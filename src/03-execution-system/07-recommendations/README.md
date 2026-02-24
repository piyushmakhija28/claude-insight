# 🤖 Auto Recommendations (Step 7)

**Part of:** 🔴 Execution System

**Purpose:** Automatically recommend optimal models, skills, and agents

---

## 📋 What This Does

- Generate real-time recommendations (every 5 seconds)
- Recommend optimal Claude model (Haiku/Sonnet/Opus)
- Suggest relevant skills to use
- Suggest relevant agents for complex tasks
- Provide context status (OK/WARNING/CRITICAL)
- Show recommendations at session start

---

## 📁 Files in This Folder

### **Daemons:**
- `auto-recommendation-daemon.py` - 9th daemon (recommendations generator)

### **Detectors:**
- `skill-detector.py` - Detect relevant skills
- `skill-auto-suggester.py` - Auto-suggest skills
- `skill-manager.py` - Manage skill registry

### **Utilities:**
- `check-recommendations.py` - Check latest recommendations

---

## 🎯 Usage

### **Start Recommendations Daemon:**
```bash
nohup python auto-recommendation-daemon.py start > /dev/null 2>&1 &
```

### **Check Latest Recommendations:**
```bash
python check-recommendations.py
```

**Output:**
```json
{
  "timestamp": "2026-02-16 14:30:00",
  "model_recommendation": {
    "model": "sonnet",
    "reason": "Complex implementation task",
    "confidence": 0.9
  },
  "skill_recommendations": [
    {
      "skill": "java-spring-boot-microservices",
      "reason": "Microservice implementation detected",
      "relevance": 0.95
    },
    {
      "skill": "context-management-core",
      "reason": "Context at 72%",
      "relevance": 0.85
    }
  ],
  "agent_recommendations": [
    {
      "agent": "spring-boot-microservices",
      "reason": "Complex Spring Boot task",
      "relevance": 0.9
    }
  ],
  "context_status": {
    "usage": "72%",
    "status": "YELLOW",
    "action": "Use cache, offset/limit"
  }
}
```

---

## 📊 Recommendation Logic

### **Model Recommendation:**

| Task Type | Model | Reason |
|-----------|-------|--------|
| Simple read/search | Haiku | Fast, cheap, sufficient |
| Implementation | Sonnet | Balanced reasoning + speed |
| Architecture/planning | Opus | Deep reasoning needed |
| Plan mode | Opus | Complex planning |

### **Skill Recommendation:**

**Triggers:**
- Keywords in user message (e.g., "Spring Boot" → java-spring-boot-microservices)
- File patterns (e.g., Dockerfile → docker)
- Context (e.g., Jenkinsfile → jenkins-pipeline)
- Task type (e.g., database schema → rdbms-core)

### **Agent Recommendation:**

**Triggers:**
- Complexity >= 10 → Suggest agent over skill
- Multi-service changes → orchestrator-agent
- Testing needed → qa-testing-agent
- Backend API work → spring-boot-microservices

### **Context Status:**

| Usage | Status | Recommendation |
|-------|--------|----------------|
| < 70% | 🟢 OK | Continue normally |
| 70-84% | 🟡 WARNING | Use cache, optimization |
| 85-89% | 🟠 CRITICAL | Session state, summaries |
| 90%+ | 🔴 DANGER | Force compact/clear |

---

## 🔄 Integration with Session Start

**When session starts (session-start.sh):**
1. ✅ Start auto-recommendation daemon (if not running)
2. ✅ Check all 9 daemon PIDs
3. ✅ Show latest recommendations
4. ✅ Show context status
5. ✅ Apply recommendations BEFORE responding

**This ensures:**
- Optimal model selected
- Relevant skills loaded
- Context optimized
- User gets best experience

---

## ✅ Benefits

- **Optimal Performance:** Right model for right task
- **Token Savings:** Haiku for simple tasks (50-70% savings)
- **Quality:** Opus for complex tasks (better results)
- **Efficiency:** Skills auto-suggested (no manual search)
- **Context Safety:** Warnings before overflow

---

## 🚨 Daemon Status

**Check if daemon is running:**
```bash
python daemon-manager.py --status auto-recommendation-daemon
```

**Restart daemon:**
```bash
python auto-recommendation-daemon.py restart
```

**View logs:**
```bash
tail -f ~/.claude/memory/logs/auto-recommendation-daemon.log
```

---

**Location:** `~/.claude/memory/03-execution-system/07-recommendations/`
