"""Tests for UDM (UML Data Model) caller-supplied structured diagram data.

Covers UMLDiagramGenerator.generate_from_data() and the 11 new deterministic
renderers it dispatches to (ADR-001). Asserts three properties per type:
the renderer never reaches an LLM or the filesystem, its output is a pure
function of its input, and a payload missing its primary key raises rather
than rendering placeholder data.
"""

import sys
from pathlib import Path

import pytest

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langgraph_engine.diagrams import legacy_generator as lg  # noqa: E402

UDM_FIXTURES = {
    "class": {
        "classes": [
            {
                "name": "Verifier",
                "attributes": [{"name": "token", "type_hint": "str", "visibility": "-"}],
                "methods": [{"name": "verify", "params": ["token"], "return_type": "bool"}],
                "bases": [],
            }
        ]
    },
    "package": {
        "packages": [{"name": "L3", "contents": ["Core", "Shell"]}, {"name": "L2", "contents": []}],
        "imports": [{"from": "L2", "to": "L3", "label": "syscall_request"}],
    },
    "component": {
        "components": [
            {"name": "L3", "provides": ["authorised_operation"], "requires": ["syscall_request"]},
            {"name": "L2", "provides": ["syscall_request"], "requires": []},
        ],
        "dependencies": [{"from": "L2", "to": "L3", "label": "mediates"}],
    },
    "sequence": {
        "participants": ["L2", "L3"],
        "call_chains": [{"caller": "L2", "callee": "L3", "method": "syscall_request"}],
    },
    "state": {
        "states": ["ARMED", "TRIPPED"],
        "transitions": [{"from": "ARMED", "to": "TRIPPED", "label": "kill_signal"}],
    },
    "activity": {
        "steps": [
            {"name": "Sanitize", "type": "action"},
            {"name": "Clean?", "type": "decision"},
            {"name": "Tag", "type": "action"},
        ]
    },
    "deployment": {
        "nodes": [{"name": "Boot Node", "type": "server", "artifacts": ["Bootloader"]}],
        "connections": [],
    },
    "usecase": {
        "system_name": "Shakti-OS",
        "actors": ["Operator"],
        "use_cases": ["Kill switch"],
        "associations": [{"actor": "Operator", "use_case": "Kill switch"}],
    },
    "object": {
        "objects": [{"name": "req1", "class": "syscall_request", "values": {"op": '"open"'}}],
    },
    "communication": {
        "participants": ["L2", "L3"],
        "messages": [{"caller": "L2", "callee": "L3", "method": "syscall_request"}],
    },
    "composite": {
        "components": [{"name": "L3", "parts": ["Core", "Shell"], "ports": ["IL3Adjudicate"]}],
    },
    "interaction": {
        "steps": [{"type": "ref", "name": "Brahma"}, {"type": "decision", "name": "OK?"}],
    },
    "call_graph": {
        "methods": [{"fqn": "a.py::A.f", "name": "f", "params": [], "cyclomatic": 1, "parent_class": "a.py::A"}],
        "edges": [],
    },
}


class LLMCalled(AssertionError):
    """Raised by the detonator fixtures when a deterministic path reaches an LLM."""


@pytest.fixture
def gen(tmp_path, monkeypatch):
    """UMLDiagramGenerator whose every LLM and filesystem escape hatch detonates."""

    def _boom(*args, **kwargs):
        raise LLMCalled("deterministic path reached an LLM: args=%r kwargs=%r" % (args, kwargs))

    monkeypatch.setattr(lg.UMLDiagramGenerator, "_llm_generate", _boom)
    monkeypatch.setattr(lg.UMLDiagramGenerator, "_llm_enrich", _boom)
    monkeypatch.setattr(lg, "_llm_generate_with_system", _boom)
    return lg.UMLDiagramGenerator(str(tmp_path))


@pytest.mark.unit
@pytest.mark.parametrize("dtype", sorted(lg.UDM_PRIMARY_KEY))
def test_generate_from_data_is_deterministic_and_llm_free(gen, dtype):
    data = UDM_FIXTURES[dtype]
    out = gen.generate_from_data(dtype, data)
    assert out.strip()
    assert out == gen.generate_from_data(dtype, data), "%s: not a pure function of its input" % dtype


@pytest.mark.unit
@pytest.mark.parametrize("dtype", sorted(lg.UDM_PRIMARY_KEY))
def test_missing_primary_key_raises_instead_of_rendering_placeholder(gen, dtype):
    with pytest.raises(ValueError):
        gen.generate_from_data(dtype, {"__unrelated__": []})


@pytest.mark.unit
def test_unknown_diagram_type_raises(gen):
    with pytest.raises(ValueError):
        gen.generate_from_data("not-a-real-type", {"classes": [{"name": "X"}]})


@pytest.mark.unit
def test_class_udm_matches_classes_override(gen):
    """generate_from_data('class', ...) must produce the same output as the
    pre-existing classes= override, since it delegates to it directly."""
    data = UDM_FIXTURES["class"]
    via_dispatch = gen.generate_from_data("class", data)
    via_override = gen.generate_class_diagram(classes=data["classes"])
    assert via_dispatch == via_override


@pytest.mark.unit
def test_call_graph_udm_matches_dict_call_graph_adapter(gen):
    """generate_from_data('call_graph', ...) must match calling
    generate_call_graph_diagram with a manually-built _DictCallGraph."""
    data = UDM_FIXTURES["call_graph"]
    via_dispatch = gen.generate_from_data("call_graph", data)
    via_adapter = gen.generate_call_graph_diagram(call_graph=lg._DictCallGraph(data))
    assert via_dispatch == via_adapter


@pytest.mark.unit
def test_activity_decision_step_emits_yes_guard_not_synthetic_node(gen):
    """ADR-001 SS B.5: the Mermaid renderer expresses a decision's branch as
    a |yes| edge guard, not draw.io's synthetic '[yes] ... ok' node -- the
    two node counts differ by one per decision step until that draw.io
    defect is fixed separately."""
    out = gen.generate_from_data("activity", UDM_FIXTURES["activity"])
    assert "|yes|" in out
    assert " ok" not in out


@pytest.mark.unit
def test_interaction_closes_every_opened_if(gen):
    steps = {
        "steps": [
            {"type": "decision", "name": "A?"},
            {"type": "decision", "name": "B?"},
            {"type": "ref", "name": "Leaf"},
        ]
    }
    out = gen.generate_from_data("interaction", steps)
    assert out.count("if (") == out.count("endif") == 2
    assert out.strip().startswith("@startuml")
    assert out.strip().endswith("@enduml")


@pytest.mark.unit
def test_communication_numbering_skips_unresolvable_endpoints(gen):
    """Messages whose endpoint isn't a declared participant are dropped
    silently (matching DrawioConverter), and the counter increments only on
    an emitted edge -- so numbering stays 1..N with no gaps."""
    data = {
        "participants": ["A", "B"],
        "messages": [
            {"caller": "A", "callee": "B", "method": "m1"},
            {"caller": "A", "callee": "unknown", "method": "dropped"},
            {"caller": "B", "callee": "A", "method": "m2"},
        ],
    }
    out = gen.generate_from_data("communication", data)
    assert "1: m1" in out
    assert "2: m2" in out
    assert "dropped" not in out


@pytest.mark.unit
def test_component_requires_renders_as_dashed_edge(gen):
    """draw.io reads `requires` but never renders it; the Mermaid renderer
    must not silently drop it too (ADR-001 SS A.1 component note)."""
    out = gen.generate_from_data("component", UDM_FIXTURES["component"])
    assert "-.->|requires|" in out


@pytest.mark.unit
def test_component_diagram_groups_no_longer_drops_isolated_modules(gen):
    """Regression test for the rglob-based grouping bug: on a repo with no
    matching .py files, every module used to vanish silently. With an
    explicit `groups=` override, no filesystem scan happens and nothing is
    dropped; with groups omitted on a repo with no matching files, isolated
    modules land in 'ungrouped' instead of disappearing."""
    dep_graph = {"isolated": set(), "a": {"b"}, "b": set()}

    out_with_groups = gen.generate_component_diagram(dep_graph=dep_graph, groups={"a": "core", "b": "core"})
    assert "isolated" in out_with_groups
    assert "ungrouped" in out_with_groups

    out_no_groups = gen.generate_component_diagram(dep_graph=dep_graph)
    assert "isolated" in out_no_groups


@pytest.mark.unit
def test_deployment_infra_files_no_longer_dead_parameter(gen, tmp_path):
    """Regression test: passing infra_files used to be ignored AND skip
    auto-detection, falling through to the generic 'Python project with
    modules' fallback. Now its content is used directly."""
    f = tmp_path / "custom.yml"
    f.write_text("services:\n  api:\n    image: shakti/api\n", encoding="utf-8")

    seen_prompts = []
    gen._llm_generate = lambda prompt: seen_prompts.append(prompt) or None

    gen.generate_deployment_diagram(infra_files=[str(f)])

    assert seen_prompts, "generate_deployment_diagram never reached the LLM prompt step"
    assert "shakti/api" in seen_prompts[0], "infra_files content was not incorporated into the prompt"
