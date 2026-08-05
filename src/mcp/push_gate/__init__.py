"""Version-push gate as an MCP-reachable capability (PRD FR-23 / SRS FR-35).

The package holds two files and no third-party dependency:

- ``push_gate_policy`` -- the two rules, ported from
  ``hooks/pre_tool_enforcer/policies/push_gate.py`` so the guarantee survives
  that hook's deletion (PRD FR-4).
- ``server`` -- a stdio JSON-RPC 2.0 server exposing the rules as the named
  tool ``check_push_allowed``.

Nothing here is imported by the plugin. The plugin runs from the plugin
manager's cache and cannot reach this repository; it only writes the absolute
path of ``server.py`` into user-scope settings, and Claude Code spawns that path
directly.
"""
