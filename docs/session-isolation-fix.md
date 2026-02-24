# Multi-Window Session Isolation Fix

**Version:** 1.0.0
**Date:** 2026-02-24
**Severity:** CRITICAL - Session state conflicts between Claude Code instances
**Status:** In Progress

---

## Problem Summary

Multiple Claude Code instances running simultaneously interfere with each other:
- Window 1 sets task breakdown flag -> affects Window 2
- Window 2's tasks/flags mix with Window 1's state
- Active windows registry not populated
- Session isolation code exists but not used consistently

**Root Cause:** Most hook scripts use session-only flags (e.g., `.task-breakdown-pending-{SESSION_ID}.json`) without including PID. Same SESSION_ID across different processes = shared state.

---

## Architecture Issue

### Current (Broken)

```
Window 1 (PID 1234)                Window 2 (PID 5678)
    |                                    |
    +-- SESSION-XXXX                    +-- SESSION-XXXX (same!)
            |                                   |
            +-- .task-breakdown-pending-SESSION-XXXX.json (SHARED!)
```

### Fixed (Isolated)

```
Window 1 (PID 1234)                Window 2 (PID 5678)
    |                                    |
    +-- SESSION-XXXX-1234               +-- SESSION-XXXX-5678
            |                                   |
            +-- .task-breakdown-pending-SESSION-XXXX-1234.json (isolated)
```

---

## Files That Need Fixing

### Priority 1 (Critical Path)

| Script | Issue | Fix |
|--------|-------|-----|
| `pre-tool-enforcer.py` | Uses `.task-breakdown-pending-{SESSION}` | Add PID to flag paths |
| `post-tool-tracker.py` | Uses `.current-session.json` globally | Make window-specific |
| `3-level-flow.py` | Session flags shared across PIDs | Use window session dirs |

### Priority 2 (Supporting)

| Script | Issue | Fix |
|--------|-------|-----|
| `stop-notifier.py` | No window awareness | Add window registry check |
| `auto-fix-enforcer.py` | No isolation logic | Import isolator |

---

## Implementation Pattern

Using session-window-isolator functions:

```python
from session_window_isolator import get_window_state_file, register_window

# OLD (shared state):
flag_path = FLAG_DIR / f'.task-breakdown-pending-{session_id}.json'

# NEW (isolated state):
def get_isolated_flag_path(flag_type, session_id):
    pid = os.getpid()
    return FLAG_DIR / f'.{flag_type}-{session_id}-{pid}.json'

flag_path = get_isolated_flag_path('task-breakdown-pending', session_id)
```

---

## Testing Checklist

Before marking complete:
- [ ] 2 Claude Code windows run without state conflicts
- [ ] Tasks created in Window 1 don't affect Window 2
- [ ] Active windows registry populated
- [ ] Voice notifications work correctly per window
- [ ] No regression in single-window mode

---

## Progress

- [ ] Update pre-tool-enforcer.py
- [ ] Update 3-level-flow.py
- [ ] Update post-tool-tracker.py
- [ ] Update stop-notifier.py
- [ ] Create test-window-isolation.py
- [ ] Verify with 2 simultaneous instances
