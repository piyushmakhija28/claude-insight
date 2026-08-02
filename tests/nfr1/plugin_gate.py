"""Structural gates over the plugin tree that decide NFR-1 independently of counting.

Acceptance criterion 6 is not a process-count criterion. A .mcp.json at the plugin root
containing any server entry fails NFR-1 outright, whatever the process count says,
because plugin_schema_spike.md item 5 MEASURED that plugin-registered stdio servers
spawn eagerly on plugin enable with zero tool calls made. The gate therefore runs before
and independently of any measurement.

A source discrepancy is reported rather than resolved by picking a side:

    The binding acceptance criterion (issue V2-003, prd-v2.md section 5 NFR-1 row,
    SRS.md NFR-7 acceptance row) fails on "a .mcp.json containing any server entry".
    The prd-v2.md section 7 Gherkin is stricter and says the plugin "ships NO .mcp.json
    at all".

An empty .mcp.json satisfies the first and violates the second. This module fails on the
binding criterion and warns on the stricter Gherkin, and names both, so the discrepancy
reaches a human instead of being silently absorbed.

The gate returns NOT_MEASURABLE when the plugin root does not exist. It never returns
PASS for an absent plugin. A structural check that passes because the artifact under
test is missing is the purest form of a check that cannot fail.
"""

import json
import os

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_WARN = "WARN"
STATUS_NOT_MEASURABLE = "NOT_MEASURABLE"

SERVER_KEYS = ("mcpServers", "servers", "mcp_servers")


class GateResult(object):
    """The outcome of one structural gate.

    Attributes:
        gate: Gate identifier.
        status: One of STATUS_PASS, STATUS_FAIL, STATUS_WARN, STATUS_NOT_MEASURABLE.
        detail: Human-readable explanation.
        evidence: Structured supporting data.
        authority: The requirement or ADR this gate enforces.
    """

    __slots__ = ("gate", "status", "detail", "evidence", "authority")

    def __init__(self, gate, status, detail, evidence=None, authority=""):
        self.gate = gate
        self.status = status
        self.detail = detail
        self.evidence = evidence or {}
        self.authority = authority

    @property
    def is_blocking_failure(self):
        """Return True when this result alone fails NFR-1."""
        return self.status == STATUS_FAIL

    def to_dict(self):
        """Return a JSON-serialisable view of this result."""
        return {
            "gate": self.gate,
            "status": self.status,
            "detail": self.detail,
            "evidence": self.evidence,
            "authority": self.authority,
        }


def check_mcp_manifest(plugin_root):
    """Apply acceptance criterion 6 to the plugin root.

    Args:
        plugin_root: Path to the installed plugin root, or None.

    Returns:
        GateResult. FAIL when a .mcp.json declares one or more servers. WARN when a
        .mcp.json exists but declares none, because the section 7 Gherkin forbids the
        file existing at all while the binding criterion tolerates it. PASS when no
        .mcp.json exists. NOT_MEASURABLE when the plugin root does not exist.
    """
    authority = "ADR-019; issue V2-003 AC 6; prd-v2.md section 5 NFR-1 row; SRS.md NFR-7"
    if not plugin_root or not os.path.isdir(str(plugin_root)):
        return GateResult(
            gate="adr019_no_bundled_mcp",
            status=STATUS_NOT_MEASURABLE,
            detail=(
                "plugin root %r does not exist, so criterion 6 cannot be evaluated. "
                "Deferred until the plugin manifest exists (issue V2-015). This is not "
                "a pass." % (str(plugin_root) if plugin_root else None)
            ),
            evidence={"plugin_root": str(plugin_root) if plugin_root else None},
            authority=authority,
        )

    manifest_path = os.path.join(str(plugin_root), ".mcp.json")
    if not os.path.exists(manifest_path):
        return GateResult(
            gate="adr019_no_bundled_mcp",
            status=STATUS_PASS,
            detail="no .mcp.json at the plugin root; zero bundled MCP servers",
            evidence={"manifest_path": manifest_path, "exists": False},
            authority=authority,
        )

    try:
        with open(manifest_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        return GateResult(
            gate="adr019_no_bundled_mcp",
            status=STATUS_FAIL,
            detail=(
                "a .mcp.json exists at the plugin root but could not be read or parsed "
                "(%s). An unreadable manifest cannot be shown to declare zero servers, "
                "and criterion 6 fails closed." % exc
            ),
            evidence={"manifest_path": manifest_path, "exists": True},
            authority=authority,
        )

    declared = {}
    if isinstance(payload, dict):
        for key in SERVER_KEYS:
            block = payload.get(key)
            if isinstance(block, dict):
                declared.update(block)
            elif isinstance(block, list):
                for index, item in enumerate(block):
                    declared["%s[%d]" % (key, index)] = item

    if declared:
        return GateResult(
            gate="adr019_no_bundled_mcp",
            status=STATUS_FAIL,
            detail=(
                "a .mcp.json at the plugin root declares %d server entr%s. Criterion 6 "
                "fails outright regardless of the process count, because bundled stdio "
                "servers were MEASURED to spawn eagerly on plugin enable with zero tool "
                "calls made." % (len(declared), "y" if len(declared) == 1 else "ies")
            ),
            evidence={
                "manifest_path": manifest_path,
                "server_names": sorted(declared.keys()),
                "server_count": len(declared),
            },
            authority=authority,
        )

    return GateResult(
        gate="adr019_no_bundled_mcp",
        status=STATUS_WARN,
        detail=(
            "a .mcp.json exists at the plugin root but declares no servers. The binding "
            "acceptance criterion tolerates this, because it fails only on a manifest "
            "containing server entries. The prd-v2.md section 7 Gherkin is stricter and "
            "requires the plugin to ship NO .mcp.json at all. The two sources disagree; "
            "this is reported rather than silently resolved."
        ),
        evidence={"manifest_path": manifest_path, "server_count": 0},
        authority=authority,
    )


def check_no_bundled_hooks(plugin_root):
    """Check ADR-010 conformance: no hooks directory and no hooks.json in the plugin.

    This gate is AUXILIARY. It is not one of issue V2-003's six acceptance criteria; it
    belongs to ADR-010 conformance and is owned by the plugin build. It is evaluated
    here because a bundled hook merges into the user's configuration on enable and
    spawns without invocation, which is the precise failure NFR-1 exists to detect, so
    a per-component process harness that ignored it would under-report.

    Args:
        plugin_root: Path to the installed plugin root, or None.

    Returns:
        GateResult, marked auxiliary in its evidence.
    """
    authority = "ADR-010 (SETTLED, NON-NEGOTIABLE); hld.md section 9 fitness function 2"
    evidence = {"auxiliary": True, "not_part_of_v2_003_acceptance_criteria": True}

    if not plugin_root or not os.path.isdir(str(plugin_root)):
        evidence["plugin_root"] = str(plugin_root) if plugin_root else None
        return GateResult(
            gate="adr010_no_bundled_hooks",
            status=STATUS_NOT_MEASURABLE,
            detail=(
                "plugin root does not exist; ADR-010 conformance cannot be evaluated. "
                "Deferred until issue V2-015. This is not a pass."
            ),
            evidence=evidence,
            authority=authority,
        )

    offenders = []
    hooks_dir = os.path.join(str(plugin_root), "hooks")
    if os.path.isdir(hooks_dir):
        offenders.append(hooks_dir)
    for dirpath, dirnames, filenames in os.walk(str(plugin_root)):
        if ".git" in dirnames:
            dirnames.remove(".git")
        if "hooks.json" in filenames:
            offenders.append(os.path.join(dirpath, "hooks.json"))

    evidence["offenders"] = offenders
    if offenders:
        return GateResult(
            gate="adr010_no_bundled_hooks",
            status=STATUS_FAIL,
            detail=(
                "the plugin tree contains %d hook artefact(s). ADR-010 forbids any "
                "hooks/ directory or hooks.json, at CRITICAL." % len(offenders)
            ),
            evidence=evidence,
            authority=authority,
        )
    return GateResult(
        gate="adr010_no_bundled_hooks",
        status=STATUS_PASS,
        detail="no hooks/ directory and no hooks.json anywhere in the plugin tree",
        evidence=evidence,
        authority=authority,
    )


def run_structural_gates(plugin_root):
    """Run every structural gate and summarise.

    Args:
        plugin_root: Path to the installed plugin root, or None.

    Returns:
        Dict with the individual gate results and an overall status. The overall status
        is FAIL if any gate fails, NOT_MEASURABLE if any gate could not be evaluated,
        and PASS only when every gate produced a pass or a warning.
    """
    results = [check_mcp_manifest(plugin_root), check_no_bundled_hooks(plugin_root)]
    if any(r.status == STATUS_FAIL for r in results):
        overall = STATUS_FAIL
    elif any(r.status == STATUS_NOT_MEASURABLE for r in results):
        overall = STATUS_NOT_MEASURABLE
    else:
        overall = STATUS_PASS
    return {
        "overall": overall,
        "gates": [r.to_dict() for r in results],
        "blocking_failures": [r.gate for r in results if r.is_blocking_failure],
    }
