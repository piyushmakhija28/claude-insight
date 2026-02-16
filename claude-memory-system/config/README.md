# ⚙️ Configuration Files

**Purpose:** JSON configuration files for system settings, preferences, and data

---

## 📋 What This Contains

All JSON configuration files:
- Runtime state files
- User preferences
- Pattern detection data
- Dashboard history
- Consultation preferences

---

## 📁 Configuration Files

### **Runtime State:**
- `.last-automation-check.json` - Last automation check timestamp
- `dashboard_history.json` - Dashboard history data

### **User Preferences:**
- `consultation-preferences.json` - User consultation preferences
- `user-preferences.json` - General user preferences (if exists)

### **Pattern Detection:**
- `cross-project-patterns.json` - Detected cross-project patterns
- `pattern-registry.json` - Pattern registry (if exists)

### **Session Data:**
- `session-index.json` - Session index (moved to sessions/ folder)

---

## 🎯 File Descriptions

### **`.last-automation-check.json`**
Tracks last automation check time:
```json
{
  "last_check": "2026-02-16T14:30:00Z",
  "status": "success",
  "daemons_checked": 9,
  "all_running": true
}
```

### **`consultation-preferences.json`**
User consultation preferences:
```json
{
  "auto_consultation": true,
  "consultation_threshold": 0.7,
  "preferred_topics": ["architecture", "security"],
  "notification_enabled": true
}
```

### **`cross-project-patterns.json`**
Detected patterns from projects:
```json
{
  "patterns": [
    {
      "pattern_id": "p001",
      "name": "Service Layer Pattern",
      "projects": ["user-service", "product-service"],
      "confidence": 0.95,
      "last_detected": "2026-02-16"
    }
  ]
}
```

### **`dashboard_history.json`**
Dashboard usage history:
```json
{
  "views": [
    {
      "timestamp": "2026-02-16T14:30:00Z",
      "duration": 120,
      "sections_viewed": ["daemons", "context", "sessions"]
    }
  ]
}
```

---

## 🔒 Security

**Important:**
- ✅ All config files are local (not synced)
- ✅ No secrets stored (secrets use Secret Manager)
- ✅ No credentials (GitHub auth via gh CLI)
- ✅ Safe to commit (no sensitive data)

---

## 🔄 Backup

**Config files are backed up:**
- Daily: Auto-backup to `~/.claude/memory/backups/config/`
- Before major changes: Manual backup
- Restore: Copy from backups folder

**Backup command:**
```bash
cp ~/.claude/memory/config/*.json ~/.claude/memory/backups/config/$(date +%Y%m%d)/
```

---

## ✅ Benefits

- **Centralized:** All configs in one place
- **Version Control:** Track config changes
- **Easy Backup:** Simple to backup/restore
- **Safe:** No sensitive data

---

**Location:** `~/.claude/memory/config/`
