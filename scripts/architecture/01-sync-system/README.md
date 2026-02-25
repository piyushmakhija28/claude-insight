# 🔵 SYNC SYSTEM (Foundation Layer)

**PURPOSE:** Load context and session history BEFORE execution

---

## 📊 What This System Does

1. **Context Management:**
   - Load project README.md
   - Load service .md files
   - Understand current codebase structure
   - Know where files are located
   - Smart caching and cleanup

2. **Session Management:**
   - Load previous sessions by ID
   - Know what was done before
   - Track historical decisions
   - Auto-save sessions with unique IDs

3. **User Preferences:**
   - Learn user coding preferences
   - Remember architectural choices
   - Apply preferences automatically
   - Reduce re-explanations

4. **Pattern Detection:**
   - Detect patterns from existing code
   - Replicate patterns across services
   - Ensure consistency
   - Enable "do it like service X"

**OUTPUT:** Complete understanding (Current state + History + Preferences + Patterns)

---

## 📁 Sub-Folders

```
01-sync-system/
├── session-management/      📦 Session with unique IDs
│   ├── README.md               (13 files total)
│   ├── session-memory-policy.md
│   ├── session-loader.py
│   ├── session-search.py
│   └── ... (session-related files)
│
├── context-management/      📖 Context optimization
│   ├── README.md               (14 files total)
│   ├── context-daemon.py
│   ├── context-monitor-v2.py
│   ├── smart-cleanup.py
│   ├── tiered-cache.py
│   └── ... (context-related files)
│
├── user-preferences/        🎯 User preference tracking
│   ├── README.md               (5 files total)
│   ├── user-preferences-policy.md
│   ├── preference-auto-tracker.py
│   ├── load-preferences.py
│   └── ... (preference-related files)
│
└── pattern-detection/       🔍 Pattern detection & replication
    ├── README.md               (4 files total)
    ├── cross-project-patterns-policy.md
    ├── pattern-detection-daemon.py
    ├── detect-patterns.py
    └── apply-patterns.py
```

**Total: 4 sub-folders, 36 files organized by category**

**See each sub-folder's README for detailed file list.**

---

## 🔗 Dependencies

**This system runs FIRST - no dependencies**

---

## 🎯 Usage

```bash
# Load previous session
python session-loader.py load SESSION_ID

# Search sessions
python session-search.py --tags authentication jwt

# Start session monitoring
bash session-start.sh
```

---

## ⚙️ Integration

**Position in Flow:**
```
🔵 SYNC SYSTEM (THIS) - Foundation
        ↓
🟢 RULES/STANDARDS SYSTEM
        ↓
🔴 EXECUTION SYSTEM
```

---

**STATUS:** 🟢 ACTIVE
**PRIORITY:** 🔴 CRITICAL (Must run first)
