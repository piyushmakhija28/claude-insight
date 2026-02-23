# Session Management Guide
Session ID tracking, chaining, and lifecycle management.

---

## 🆔 SESSION ID TRACKING (MANDATORY)

**Every session and work item gets a unique tracking ID!**

### **Format:**
```
SESSION-YYYYMMDD-HHMMSS-XXXX
```

**Example:** `SESSION-20260216-173003-09RZ`

### **When Generated:**
- ✅ **Session start** - Automatically during session-start.sh
- ✅ **Work item start** - When starting any major task
- ✅ **On request** - Anytime user asks

### **Mandatory Display:**

**I MUST show Session ID after:**
1. Running session-start.sh
2. Starting any new work/task
3. User explicitly requests it

**Format to show:**
```
🆔 Session ID: SESSION-20260216-173003-09RZ
```

### **Session ID Banner:**

Full banner displayed automatically:
```
================================================================================
📋 SESSION ID FOR TRACKING
================================================================================

🆔 Session ID: SESSION-20260216-173003-09RZ
📅 Started: 2026-02-16T17:30:03
📊 Status: ACTIVE
📝 Description: Session started at 2026-02-16 17:30:03

💡 Use this ID to track this session in logs and reports
================================================================================
```

### **Usage:**

**Generate new session:**
```bash
bash ~/.claude/memory/session-id-generator.sh create --description "Your description"
```

**Show current session:**
```bash
bash ~/.claude/memory/session-id-generator.sh current
```

**List recent sessions:**
```bash
bash ~/.claude/memory/session-id-generator.sh list
```

**Get session stats:**
```bash
python ~/.claude/memory/session-id-generator.py stats --session-id SESSION-20260216-173003-09RZ
```

### **Tracking Benefits:**

1. **📊 Session Logs** - Track all activity by session ID
2. **🔍 Debugging** - Find exact session when issues occur
3. **📈 Analytics** - Analyze session duration, work items
4. **🤝 Collaboration** - Share session ID for support
5. **📝 Reporting** - Generate reports by session

### **Session Data Stored:**

**Location:** `~/.claude/memory/sessions/SESSION-*.json`

**Contains:**
- Session ID and timestamps
- Work items and their status
- Session metadata
- Duration and completion stats

**Log:** `~/.claude/memory/logs/sessions.log`

### **Enforcement:**

**I MUST:**
- ✅ Generate session ID on session start
- ✅ Display session ID banner to user
- ✅ Provide session ID for tracking
- ✅ Log all session events
- ❌ NEVER skip showing session ID

---

## 🔗 SESSION CHAINING POLICY (v1.0.0)

**Sessions are linked in a chain. Each session knows its parent, children, related sessions, and tags.**

### How It Works:

**On /clear (automatic via clear-session-handler.py):**
- Old session is closed
- New session is created
- New session is linked to old session as parent -> child
- Chain: `SESSION-A -> SESSION-B -> SESSION-C` (A is grandparent, B is parent, C is current)

**On every request (automatic via 3-level-flow.py):**
- Auto-extract tags from: prompt keywords, task type, skill, project directory
- Tags stored in chain-index.json
- Sessions with 2+ shared tags are auto-related
- Chain context displayed in flow output when ancestors/related exist

### Data Model:
```
chain-index.json:
  sessions:
    SESSION-ID:
      parent: SESSION-PARENT-ID
      children: [SESSION-CHILD-IDs]
      related: [SESSION-IDs]          # by explicit link or shared tags
      tags: [spring-boot, docker, ...] # auto-extracted
      project: techdeveloper-scheduler
      skill: java-spring-boot-microservices
      task_type: Implementation
      summary: "what was done"
      last_prompt: "user's last message"
  tag_index:
    spring-boot: [SESSION-IDs]
    docker: [SESSION-IDs]
```

### CLI Commands:
```bash
# Link sessions (auto-called by clear-session-handler.py)
python session-chain-manager.py link --child NEW --parent OLD

# Auto-tag (auto-called by 3-level-flow.py)
python session-chain-manager.py auto-tag --session ID --prompt "..." --skill "..."

# Get chain context
python session-chain-manager.py context --session ID

# Search by tag
python session-chain-manager.py search --tag "spring-boot"

# Get full chain (ancestors + descendants)
python session-chain-manager.py chain --session ID
```

### How This Helps Me (Claude):
- **Context continuity:** Know what was worked on in previous sessions
- **Related sessions:** Find sessions about the same project/topic
- **Tag search:** "Show me all spring-boot sessions" or "sessions about docker"
- **Ancestor chain:** Walk up the chain to understand the full workflow
- **Auto-relate:** Sessions with 2+ shared tags are automatically linked

### Script Location:
`~/.claude/memory/current/session-chain-manager.py` (v1.0.0)
