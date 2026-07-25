"""Level 0 (Pre-Flight Sanity Guard) Auto-Fix System package.

Canonical location for all Level 0 (Pre-Flight Sanity Guard) node functions, merge logic,
and recovery/interactive fix nodes.

Public API:
- node_unicode_fix, node_encoding_validation, node_windows_path_check
- preflight_guard_merge_node, MAX_PREFLIGHT_ATTEMPTS
- ask_preflight_guard_fix, fix_preflight_guard_issues
"""

from .merge import MAX_PREFLIGHT_ATTEMPTS, preflight_guard_merge_node  # noqa: F401
from .nodes import node_encoding_validation, node_unicode_fix, node_windows_path_check  # noqa: F401
from .recovery import ask_preflight_guard_fix, fix_preflight_guard_issues  # noqa: F401
