# Parallel Mode Hook Optimization

**Version:** 1.0.0
**Last Updated:** 2026-02-24
**Purpose:** Reduce hook overhead by 80-90% when running 2+ parallel agents

---

## Problem

When running parallel agents with the `Task` tool:
- **Pre-execution:** UserPromptSubmit hooks take 45s (clear-session: 15s + 3-level-flow: 30s)
- **Per tool call:** PreToolUse + PostToolUse hooks take 20s combined (10s each)
- **With 5 parallel agents:** 100+ seconds of hook overhead

**Result:** Agents appear slow even though actual work is fast.

---

## Solution: Parallel Mode Manager

Three new scripts auto-detect and optimize hook behavior:

### 1. `parallel-mode-manager.py`
Detects when 2+ agents are running by analyzing tool-tracker.jsonl:
- Counts `Task` tool calls in the last 5 minutes
- Returns `'parallel'` if ≥2 active tasks, `'normal'` otherwise
- Auto-expires parallel mode after 10 minutes

### 2. `parallel-mode-enforcer.py`
Lightweight UserPromptSubmit hook wrapper:
- Calls `parallel-mode-manager.py` to detect mode
- Always runs session handler (fast)
- Skips verbose 3-level-flow.py output if in parallel mode
- Shows minimal status: `[PARALLEL] Lightweight mode active...`

### 3. `switch-hook-mode.py`
CLI tool to manually switch between hook modes:

```bash
# Check current mode
python ~/.claude/memory/current/switch-hook-mode.py

# Switch to lightweight (reduced timeouts)
python ~/.claude/memory/current/switch-hook-mode.py lightweight

# Switch back to normal
python ~/.claude/memory/current/switch-hook-mode.py normal

# Auto-detect and switch
python ~/.claude/memory/current/switch-hook-mode.py auto
```

---

## Hook Timeout Comparison

| Hook | Normal Mode | Lightweight Mode |
|------|------------|-----------------|
| clear-session-handler | 15s | 10s |
| 3-level-flow --summary | 30s | **SKIPPED** |
| pre-tool-enforcer | 10s | 5s |
| post-tool-tracker | 10s | 5s |
| stop-notifier | 60s | 30s |
| **Total per prompt** | **45s** | **15s** |
| **Total per tool call** | **20s** | **10s** |

---

## How to Use

### Auto-Detection (Recommended)

The system detects parallel execution automatically:

1. When you run 2+ agents with `Task(run_in_background=true)`, the manager detects this
2. On next prompt, `parallel-mode-enforcer.py` switches to lightweight hooks
3. Hook timeouts drop to 50% of normal
4. When agents complete, mode returns to normal

**No action required - happens automatically.**

### Manual Control

For testing or forcing a specific mode:

```bash
# Immediately switch to lightweight
python ~/.claude/memory/current/switch-hook-mode.py lightweight

# Run your parallel agents
# (agents will be faster)

# Restore normal mode
python ~/.claude/memory/current/switch-hook-mode.py normal
```

---

## Performance Impact

### Example: 5 parallel tasks

**Before optimization:**
- Pre-work: 45s
- Per agent: 5 × (10s + 10s) = 100s
- **Total: 145s overhead**

**After optimization (parallel mode):**
- Pre-work: 15s
- Per agent: 5 × (5s + 5s) = 50s
- **Total: 65s overhead**
- **Improvement: 55% faster** (80s saved)

---

## Implementation Details

### Parallel Mode Flag

File: `~/.claude/.parallel-mode-active.json`

```json
{
  "active": true,
  "started": "2026-02-24T14:30:00",
  "expires": "2026-02-24T14:40:00",
  "task_count": 3
}
```

Auto-cleaned if expired.

### Hook Mode File

File: `~/.claude/.hook-mode.json`

Stores current mode (`normal` or `lightweight`):

```json
{
  "mode": "lightweight"
}
```

### Configuration Files

- `settings.json` (normal mode): Full 3-level-flow.py, full timeouts
- Generated at runtime (lightweight mode): Parallel-mode-enforcer replaces 3-level-flow

---

## Troubleshooting

### Parallel mode not activating?

Check task tracking:
```bash
tail -20 ~/.claude/memory/logs/tool-tracker.jsonl
```

Look for `"tool": "Task"` entries with recent timestamps.

### Mode stuck in lightweight?

Check expiry:
```bash
cat ~/.claude/.parallel-mode-active.json
```

Manually reset:
```bash
python ~/.claude/memory/current/switch-hook-mode.py normal
```

### Hooks still slow?

1. Check which hooks are running:
   ```bash
   cat ~/.claude/settings.json | jq '.hooks'
   ```

2. Verify you're in lightweight mode:
   ```bash
   cat ~/.claude/.hook-mode.json
   ```

3. Force regenerate:
   ```bash
   python ~/.claude/memory/current/switch-hook-mode.py lightweight
   ```

---

## Technical Details

### Task Detection Algorithm

`parallel-mode-manager.py` counts active tasks by:
1. Reading `~/.claude/memory/logs/tool-tracker.jsonl`
2. Finding `"tool": "Task"` entries with `"status": "start"`
3. Filtering to last 5 minutes: `now() - timedelta(minutes=5)`
4. Returning count ≥2 → parallel mode enabled

### Lightweight Hook Chain

1. **UserPromptSubmit** hook calls `parallel-mode-enforcer.py`
2. Enforcer runs `parallel-mode-manager.py` → gets mode
3. If `mode == 'normal'`: Run full 3-level-flow.py trace
4. If `mode == 'parallel'`: Skip trace, show minimal status
5. Continue with other hooks (pre-tool, post-tool) with reduced timeouts

### Auto-Expiry

Parallel mode expires after 10 minutes to prevent stuck state:
- Tasks take max ~10 mins typically
- After expiry, next prompt returns to normal mode
- Can be manually reset anytime

---

## Future Enhancements

1. **Adaptive timeouts** - Increase/decrease based on actual tool latency
2. **Per-agent mode** - Different timeouts for different agent types
3. **Metrics dashboard** - Show hook performance statistics
4. **Progressive enablement** - Auto-enable at 3+ agents (not just 2+)
