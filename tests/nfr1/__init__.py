"""Per-component process-count measurement harness for PRD NFR-1 / SRS NFR-7.

This package builds the measurement apparatus required by GitHub issue V2-003. It
observes; it never modifies the components it measures.

NFR-1's original acceptance criterion ("delta = 0 processes attributable to
claude-workflow-engine") could not pass as worded, because the retained user-level
Stop hook is itself engine code and fires every response turn. The criterion was
revised to require PER-COMPONENT ATTRIBUTION: pass means zero processes attributable
to the PLUGIN specifically, with exactly one permitted exclusion (the retained
user-level Stop and Notification hooks, which the plugin never owned, per ADR-010).
Making that attribution measurable is the whole purpose of this package.

Build status: the harness is BUILT. The NFR-1 measurement it performs CANNOT yet be
executed, because it requires a plugin to install (issue V2-015) and the hook
registrations to be deleted (issue V2-027). Neither exists. Calling the harness
against the current tree yields a NOT_MEASURABLE verdict by design, never a PASS.

Modules:
    process_probe    OS process enumeration, Windows-native, psutil or PowerShell CIM.
    components       Component registry and attribution roles; Stop-hook spawn floor.
    attribution      Maps observed processes onto components, including by ancestry.
    plugin_gate      Structural ADR-019 / ADR-010 gates over the plugin tree.
    harness          Measurement session, turn-boundary guard, cold/warm verdict.
    cli              Runnable entry point emitting a JSON report.
"""

__all__ = [
    "attribution",
    "cli",
    "components",
    "harness",
    "plugin_gate",
    "process_probe",
]
