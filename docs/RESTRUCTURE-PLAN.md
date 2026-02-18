# Claude Insight Restructure Plan

## Problem
- Multiple confusing folders: claude-memory-system/, memory_files/, memory-docs/, memory-scripts/
- Duplicate content everywhere
- agents/ and skills/ should be in claude-global-library
- Not clear what claude-insight actually is

## Clean Structure (What it SHOULD be)

Claude Insight = **Monitoring Dashboard for Claude Memory System**

```
claude-insight/
├── README.md                 ✅ Dashboard docs
├── CLAUDE.md                 ✅ Setup instructions
├── src/                      ✅ Dashboard backend (Python/Flask)
├── static/                   ✅ Dashboard frontend (JS/CSS)
├── templates/                ✅ Dashboard HTML templates
├── docs/                     ✅ Core memory system documentation
├── scripts/                  ✅ Core memory system scripts
├── policies/                 ✅ Core policies (consolidated)
│   ├── 01-sync-system/
│   ├── 02-standards-system/
│   └── 03-execution-system/
├── data/                     ✅ Runtime data
├── logs/                     ✅ Runtime logs
├── tests/                    ✅ Test files
├── config/                   ✅ Config files
├── requirements.txt          ✅ Python dependencies
└── .github/                  ✅ GitHub workflows
```

## To Remove (Confusing/Duplicate)
- ❌ claude-memory-system/ (duplicate)
- ❌ memory_files/ (old backup)
- ❌ memory-docs/ (duplicate of docs/)
- ❌ memory-scripts/ (duplicate of scripts/)
- ❌ agents/ (move to claude-global-library)
- ❌ skills/ (move to claude-global-library)
- ❌ archive/ (old stuff)
- ❌ 02-standards-system/ (merge into policies/)

## Actions
1. Delete confusing folders
2. Consolidate policies/
3. Keep only dashboard + core memory system
4. Clean, simple structure
