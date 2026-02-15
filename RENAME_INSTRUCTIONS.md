# Directory Rename Instructions

## Status: ✅ File References Updated

All 28 files have been successfully renamed from "Claude Monitoring System" to "Claude Insight":
- setup.py
- run.py
- src/app.py
- All templates (17 HTML files)
- Documentation files
- Configuration files

**Committed:** Git commit `3e48a55` - refactor: Rename project from Claude Monitoring System to Claude Insight

---

## Manual Step Required: Directory Rename

The directory `claude-monitoring-system` → `claude-insight` rename needs to be done manually because the directory is currently locked by the active session.

### Option 1: Manual Rename (Recommended)

1. Close this Claude Code session
2. Navigate to parent directory:
   ```
   cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new
   ```
3. Rename the directory:
   ```bash
   mv claude-monitoring-system claude-insight
   ```
   or use Windows Explorer to rename

4. Update git remote (if needed):
   ```bash
   cd claude-insight
   git remote set-url origin https://github.com/yourusername/claude-insight.git
   ```

### Option 2: Continue Without Rename

The project will work fine with the old directory name since all internal references are updated. The directory name is just cosmetic at this point.

---

## Verification

After renaming:
```bash
cd claude-insight
python run.py
```

You should see:
```
Starting Claude Insight...
```

All references are already updated!
