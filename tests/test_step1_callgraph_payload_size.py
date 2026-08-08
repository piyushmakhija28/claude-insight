"""Step 1's call-graph argument must fit in a Windows command line.

The payload is passed to prompt_gen_expert_caller as a command-line argument. On
this repository the ungated lists serialise to 1,031,711 characters -- 5,527
affected methods and 940 danger zones -- against a Windows CreateProcess limit of
32,767. Every Step 1 run on Windows therefore died with WinError 206, fell back
to the raw task, and left orchestration_prompt empty. Steps 2 and 3 then skipped
issue and branch creation, and the run reported OK having done nothing.

That failure was silent for a month. It is the reason these tests assert on the
SIZE of what is sent rather than only on the content: a correctness test would
have passed throughout, because the values were right and merely undeliverable.

The receiver already truncated affected_methods to ten, so capping the sender
changes nothing about the rendered prompt for that list. danger_zones it rendered
in full, so the totals are sent alongside the sample and _render_sample states
what was omitted -- a truncation the reader cannot see is worse than none, since
the prompt then asserts something false about the codebase.
"""

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from langgraph_engine.sdlc_pipeline.architecture.prompt_gen_expert_caller import _render_sample  # noqa: E402

WINDOWS_CMDLINE_LIMIT = 32767

# Shaped like the real thing on this repository, big enough that an uncapped
# payload cannot fit. Built rather than measured so the test does not depend on
# how large the repository happens to be on the day it runs.
MANY_METHODS = ["langgraph_engine.module_%d.Class%d.method_%d" % (i, i, i) for i in range(5527)]
MANY_ZONES = ["langgraph_engine/danger/zone_%d.py" % i for i in range(940)]


def _build_payload(danger_zones, affected_methods, sample=10):
    """Build the argument exactly as step1_task_analysis_node builds it."""
    return json.dumps(
        {
            "risk_level": "high",
            "danger_zones": danger_zones[:sample],
            "danger_zones_total": len(danger_zones),
            "affected_methods": affected_methods[:sample],
            "affected_methods_total": len(affected_methods),
        }
    )


class TestThePayloadFitsInACommandLine:
    """The size property the outage was caused by."""

    def test_a_large_graph_still_fits(self):
        payload = _build_payload(MANY_ZONES, MANY_METHODS)
        assert len(payload) < WINDOWS_CMDLINE_LIMIT, "payload is %d chars, over the %d Windows limit" % (
            len(payload),
            WINDOWS_CMDLINE_LIMIT,
        )

    def test_the_uncapped_payload_would_not_fit(self):
        """The half that proves the cap is what makes the difference.

        Without this, the test above passes on any repository small enough to fit
        anyway, and would have passed throughout the outage.
        """
        uncapped = json.dumps({"risk_level": "high", "danger_zones": MANY_ZONES, "affected_methods": MANY_METHODS})
        assert len(uncapped) > WINDOWS_CMDLINE_LIMIT

    def test_the_totals_survive_the_cap(self):
        """A sample without its total cannot be reported honestly downstream."""
        payload = json.loads(_build_payload(MANY_ZONES, MANY_METHODS))
        assert payload["danger_zones_total"] == 940
        assert payload["affected_methods_total"] == 5527
        assert len(payload["danger_zones"]) == 10
        assert len(payload["affected_methods"]) == 10


class TestTheRenderedSampleDeclaresWhatItOmitted:
    """A cap the reader cannot see makes the prompt assert something false."""

    def test_a_truncated_list_states_the_true_total(self):
        rendered = _render_sample(MANY_ZONES[:10], total=940)
        assert "showing 10 of 940" in rendered

    def test_a_complete_list_carries_no_suffix(self):
        """The half that fails if the suffix were unconditional."""
        rendered = _render_sample(["a", "b"], total=2)
        assert rendered == "a, b"
        assert "showing" not in rendered

    def test_an_absent_total_is_treated_as_complete(self):
        """An older caller sends no total; it must not be reported as truncated."""
        rendered = _render_sample(["a", "b"], total=None)
        assert rendered == "a, b"
        assert "showing" not in rendered

    def test_an_empty_list_renders_as_none(self):
        assert _render_sample([], total=0) == "none"
        assert _render_sample(None, total=None) == "none"


class TestEntriesAreDictsNotStrings:
    """The second bug, which the first one hid.

    The analyser yields dicts carrying fqn / callers_count / risk. The previous
    code joined them directly, which raises TypeError on a dict. It never
    surfaced because the argument carrying them blew the Windows command-line
    limit and the caller died before reaching the join -- so fixing only the size
    would have swapped a WinError for a TypeError.
    """

    def test_a_dict_entry_renders_its_fqn(self):
        entries = [{"fqn": "pkg.mod.Class.method", "callers_count": 42, "risk": "high"}]
        assert _render_sample(entries, total=1) == "pkg.mod.Class.method"

    def test_the_old_join_would_have_raised_on_these(self):
        """Pins why this is a separate defect rather than a style preference."""
        entries = [{"fqn": "pkg.mod.Class.method", "callers_count": 42}]
        try:
            ", ".join(entries)
        except TypeError:
            return
        raise AssertionError("joining dicts must raise TypeError, or this test proves nothing")

    def test_a_plain_string_entry_still_works(self):
        """Older callers, and hot_nodes, may still send strings."""
        assert _render_sample(["a.b.c"], total=1) == "a.b.c"

    def test_an_unexpected_shape_degrades_instead_of_raising(self):
        """Prompt assembly must not die because an entry grew a new shape."""
        assert _render_sample([{"unexpected": 1}], total=1) != ""


class TestTheNodeSendsTheCappedShape:
    """The cap must live in the node, not only in this test's helper."""

    def test_the_node_source_caps_both_lists_and_sends_totals(self):
        source = (_PROJECT_ROOT / "langgraph_engine" / "sdlc_pipeline" / "nodes" / "task_orchestration.py").read_text(
            encoding="utf-8"
        )
        assert "danger_zones_total" in source, "the node must send the danger_zones total"
        assert "affected_methods_total" in source, "the node must send the affected_methods total"
        assert "_CG_SAMPLE" in source, "the node must cap the lists before serialising"
