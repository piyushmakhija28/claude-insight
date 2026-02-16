# 🔄 Auto-Sync Guide - Keep Everything in Sync!

**Version:** 1.0
**Date:** 2026-02-16
**Purpose:** Ensure Claude Insight repository stays synchronized with global memory system

---

## 🎯 Why Auto-Sync?

**Claude Insight is a PUBLIC PACKAGE** that users download from GitHub.

When you create:
- ✅ A new skill → Users should get it
- ✅ A new agent → Users should get it
- ✅ A new policy → Users should get it
- ✅ Updated docs → Users should get them
- ✅ New scripts → Users should get them

**If you don't sync → Users miss out on new features!** ❌

---

## 📋 What Gets Synced?

| Type | Source Location | Destination | Trigger |
|------|-----------------|-------------|---------|
| **Skills** | `~/.claude/skills/{skill-name}/` | `claude-insight/claude-memory-system/skills/` | New skill created |
| **Agents** | `~/.claude/agents/{agent-name}/` | `claude-insight/claude-memory-system/agents/` | New agent created |
| **Policies** | `~/.claude/memory/**/*-policy.md` | `claude-insight/claude-memory-system/policies/` | New/updated policy |
| **Docs** | `~/.claude/memory/docs/*.md` | `claude-insight/claude-memory-system/docs/` | New/updated doc |
| **Scripts** | `~/.claude/memory/scripts/**/*.py` | `claude-insight/claude-memory-system/scripts/` | New script |
| **Config** | `~/.claude/memory/config/*.json` | `claude-insight/claude-memory-system/config/` | Config change |
| **CLAUDE.md** | `~/.claude/CLAUDE.md` | `claude-insight/claude-memory-system/CLAUDE.md` | Version update |
| **MASTER-README** | `~/.claude/memory/MASTER-README.md` | `claude-insight/claude-memory-system/MASTER-README.md` | Major update |

---

## 🚀 Quick Sync Commands

### Sync Everything (Full Sync)
```bash
# Run this after major changes
cd /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight

# Sync all skills
cp -r ~/.claude/skills/* claude-memory-system/skills/

# Sync all agents
cp -r ~/.claude/agents/* claude-memory-system/agents/

# Sync all policies
cp -r ~/.claude/memory/01-sync-system ~/.claude/memory/02-standards-system ~/.claude/memory/03-execution-system ~/.claude/memory/testing claude-memory-system/policies/

# Sync all docs
cp -r ~/.claude/memory/docs/* claude-memory-system/docs/

# Sync all scripts
cp -r ~/.claude/memory/scripts/* claude-memory-system/scripts/

# Sync config
cp ~/.claude/memory/config/*.json claude-memory-system/config/

# Sync main files
cp ~/.claude/CLAUDE.md claude-memory-system/
cp ~/.claude/memory/MASTER-README.md claude-memory-system/

echo "✅ Full sync completed!"
```

### Sync Single Item

**New Skill:**
```bash
cp -r ~/.claude/skills/{skill-name} /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/skills/
```

**New Agent:**
```bash
cp -r ~/.claude/agents/{agent-name} /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/agents/
```

**Updated Policy:**
```bash
cp ~/.claude/memory/**/{policy-file}.md /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/policies/
```

---

## 🤖 Automatic Sync Triggers

**Claude (AI Assistant) will automatically remind you to sync when:**

1. **New Skill Created**
   - After `/skill-builder` completes
   - After manual skill creation
   - 🔔 Reminder: "🔄 New skill created! Running auto-sync..."

2. **New Agent Created**
   - After agent builder completes
   - After manual agent creation
   - 🔔 Reminder: "🔄 New agent created! Running auto-sync..."

3. **Policy Created/Updated**
   - After policy file modification
   - After policy reorganization
   - 🔔 Reminder: "🔄 Policy updated! Running auto-sync..."

4. **Documentation Updated**
   - After major doc changes
   - After MASTER-README update
   - 🔔 Reminder: "🔄 Documentation updated! Running auto-sync..."

5. **CLAUDE.md Version Update**
   - After version bump (e.g., 2.4.0 → 2.5.0)
   - 🔔 Reminder: "🔄 CLAUDE.md updated! Running auto-sync..."

---

## ✅ Verification Steps

After syncing, always verify:

```bash
# Verify skill exists
ls /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/skills/{skill-name}

# Verify agent exists
ls /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/agents/{agent-name}

# Verify policy exists
find /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/policies -name "{policy-file}.md"

# Verify docs synced
ls /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/docs/*.md | wc -l
```

**Expected Results:**
- ✅ File/directory exists → Sync successful!
- ❌ File not found → Retry sync command

---

## 📝 Manual Sync Checklist

Use this checklist when syncing manually:

```
□ Sync all skills (28+ skills)
□ Sync all agents (12+ agents)
□ Sync all policies (18+ policies)
□ Sync all docs (50+ files)
□ Sync all scripts (81+ files)
□ Sync config files
□ Sync CLAUDE.md
□ Sync MASTER-README.md
□ Verify all files copied
□ Update version in README.md (if needed)
□ Commit changes to Git
□ Push to GitHub
```

---

## 🔄 Sync Frequency

| Item | Frequency | When |
|------|-----------|------|
| **Skills** | On creation | Immediately after skill builder |
| **Agents** | On creation | Immediately after agent creation |
| **Policies** | On major update | After policy restructuring |
| **Docs** | Weekly | After documentation updates |
| **Scripts** | On creation | After new script added |
| **Config** | As needed | After config changes |
| **Main files** | On version update | After CLAUDE.md version bump |

---

## 🚨 Important Notes

### 1. Don't Forget to Sync!
**Problem:** You create amazing new skill/agent/policy but forget to sync
**Result:** Users download old version, miss new features
**Solution:** Follow auto-sync reminders!

### 2. Sync Before Committing
**Always sync BEFORE committing to Git:**
```bash
# 1. Make changes in global memory
# 2. Sync to claude-insight
# 3. Then commit
cd /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight
git add .
git commit -m "feat: Add new skill/agent/policy"
git push
```

### 3. Full Sync Weekly
**Best Practice:** Run full sync every week to catch missed files
```bash
# Every Sunday evening
bash full-sync.sh  # Or run manual commands above
```

---

## 📂 Directory Structure After Sync

```
claude-insight/claude-memory-system/
├── CLAUDE.md (synced from ~/.claude/)
├── MASTER-README.md (synced from ~/.claude/memory/)
│
├── skills/ (synced from ~/.claude/skills/)
│   ├── adaptive-skill-intelligence/
│   ├── docker/
│   ├── java-spring-boot-microservices/
│   └── ... (28+ skills)
│
├── agents/ (synced from ~/.claude/agents/)
│   ├── android-backend-engineer/
│   ├── spring-boot-microservices/
│   ├── orchestrator-agent/
│   └── ... (12+ agents)
│
├── policies/ (synced from ~/.claude/memory/)
│   ├── 01-sync-system/
│   ├── 02-standards-system/
│   ├── 03-execution-system/
│   └── testing/
│
├── docs/ (synced from ~/.claude/memory/docs/)
│   ├── ADVANCED-TOKEN-OPTIMIZATION.md
│   ├── java-project-structure.md
│   └── ... (50+ docs)
│
├── scripts/ (synced from ~/.claude/memory/scripts/)
│   ├── automation/
│   ├── daemons/
│   └── ... (81+ scripts)
│
└── config/ (synced from ~/.claude/memory/config/)
    ├── skills-registry.json
    ├── user-preferences.json
    └── ... (6+ configs)
```

---

## 🎯 Success Criteria

**You know sync is working when:**
1. ✅ All new skills appear in claude-insight
2. ✅ All new agents appear in claude-insight
3. ✅ All policy updates reflect in claude-insight
4. ✅ Documentation stays current
5. ✅ Users get latest features on download
6. ✅ No "file not found" issues reported
7. ✅ GitHub repo shows recent commits

---

## 🐛 Troubleshooting

### Issue: Sync command fails
**Solution:**
```bash
# Check if destination exists
mkdir -p /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/skills
mkdir -p /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/agents

# Try sync again
cp -r ~/.claude/skills/* /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/skills/
```

### Issue: File not copied
**Solution:**
```bash
# Check if source exists
ls ~/.claude/skills/{skill-name}

# If exists, retry copy with verbose
cp -rv ~/.claude/skills/{skill-name} /c/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-insight/claude-memory-system/skills/
```

### Issue: Partial sync
**Solution:**
Run full sync command to ensure everything is copied.

---

## 📞 Questions?

**Need help with sync?**
- Check this guide first
- Verify paths are correct
- Ensure source files exist
- Run full sync as fallback

---

**🎉 Keep Everything in Sync - Keep Users Happy!** 🚀

**Remember:** Every time you create something new in the global memory system, it should be synced to Claude Insight so users get the complete, up-to-date package!
