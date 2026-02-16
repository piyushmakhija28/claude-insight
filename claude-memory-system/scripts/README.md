# 🔧 Scripts

**Purpose:** Shell scripts for system operations, automation, and maintenance

---

## 📋 What This Contains

All shell scripts (.sh files) for:
- System startup and initialization
- Health monitoring
- Dashboard and status
- Policy loading
- Verification and validation
- Migration and setup

---

## 📁 Script Categories

### **Startup & Initialization:**
- `startup-hook.sh` - Main startup hook (auto-runs on login)
- `startup-hook-v2.sh` - Startup hook v2
- `initialize-system.sh` - Initialize memory system
- `memory-loader.sh` - Load memory system

### **Health Monitoring:**
- `daily-health-check.sh` - Daily health check
- `weekly-health-check.sh` - Weekly health check
- `monthly-optimization.sh` - Monthly optimization
- `dashboard.sh` - System dashboard
- `dashboard-v2.sh` - Dashboard v2

### **System Verification:**
- `verify-system.sh` - Verify system health
- `verify-setup.sh` - Verify setup
- `verify-integration.sh` - Verify integration
- `check-conflicts.sh` - Check conflicts

### **Policy & Preferences:**
- `load-policies.sh` - Load all policies
- `apply-preference.sh` - Apply user preferences
- `policy-tracker.sh` - Track policy usage

### **Migration:**
- `migrate-local-claude.sh` - Migrate to local Claude

---

## 🎯 Usage

### **Run Startup Hook:**
```bash
bash ~/.claude/memory/scripts/startup-hook.sh
```

### **Check System Health:**
```bash
bash ~/.claude/memory/scripts/daily-health-check.sh
```

### **View Dashboard:**
```bash
bash ~/.claude/memory/scripts/dashboard.sh
```

### **Verify System:**
```bash
bash ~/.claude/memory/scripts/verify-system.sh
```

### **Load Policies:**
```bash
bash ~/.claude/memory/scripts/load-policies.sh
```

---

## 🔄 Auto-Execution

**Startup Hook:**
- Automatically runs on Windows login
- Location: `C:\Users\techd\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\claude-startup.bat`
- Starts all 9 daemons
- Performs system health check

**Scheduled Tasks:**
- Daily health check (runs at 9 AM daily)
- Weekly health check (runs Sunday 10 AM)
- Monthly optimization (runs 1st of month)

---

## 📝 Logging

**All scripts log to:** `~/.claude/memory/logs/scripts.log`

**View logs:**
```bash
tail -f ~/.claude/memory/logs/scripts.log
```

---

## ✅ Benefits

- **Automation:** Scripts run automatically
- **Monitoring:** Health checks keep system healthy
- **Maintenance:** Easy system maintenance
- **Verification:** Verify system integrity

---

**Location:** `~/.claude/memory/scripts/`
