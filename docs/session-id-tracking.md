# Session ID Tracking System v1.0.0

**Unique tracking IDs for every session and work item**

---

## 🎯 Purpose

Every session and work item gets a unique, traceable ID for:
- **Tracking** - Follow session activity across logs
- **Debugging** - Find exact session when issues occur
- **Analytics** - Analyze duration, completion rates
- **Reporting** - Generate session-based reports
- **Support** - Share session ID for collaboration

---

## 🆔 Session ID Format

```
SESSION-YYYYMMDD-HHMMSS-XXXX
```

**Components:**
- `SESSION` - Type prefix (can be TASK, WORK, etc.)
- `YYYYMMDD` - Date (e.g., 20260216)
- `HHMMSS` - Time (e.g., 173003)
- `XXXX` - Random 4-char hash (e.g., 09RZ)

**Example:** `SESSION-20260216-173003-09RZ`

**Benefits:**
- ✅ Unique (random hash prevents collisions)
- ✅ Sortable (date-time prefix)
- ✅ Human-readable (easy to parse)
- ✅ Traceable (shows when created)

---

## 🚀 Automatic Generation

### Session Start Integration

**Automatically generated during:**
```bash
bash ~/.claude/memory/session-start.sh
```

**Step 7/7 in session start:**
```
[7/7] Generating Session ID for tracking...

================================================================================
📋 SESSION ID FOR TRACKING
================================================================================

🆔 Session ID: SESSION-20260216-173003-09RZ
📅 Started: 2026-02-16T17:30:03
📊 Status: ACTIVE

💡 Use this ID to track this session in logs and reports
================================================================================
```

---

## 📊 Session Banner Display

**Full banner shown automatically:**

```
================================================================================
📋 SESSION ID FOR TRACKING
================================================================================

🆔 Session ID: SESSION-20260216-173003-09RZ
📅 Started: 2026-02-16T17:30:03
📊 Status: ACTIVE
📝 Description: Session started at 2026-02-16 17:30:03
🔧 Work Items: 5

💡 Use this ID to track this session in logs and reports
================================================================================
```

**Displayed:**
- Session ID
- Start timestamp
- Current status (ACTIVE/COMPLETED)
- Description (if provided)
- Work item count (if any)

---

## 🛠️ Manual Usage

### Create New Session

```bash
# With description
bash ~/.claude/memory/session-id-generator.sh create --description "Feature implementation"

# Custom type
bash ~/.claude/memory/session-id-generator.sh create --type TASK --description "Bug fix"
```

### Show Current Session

```bash
bash ~/.claude/memory/session-id-generator.sh current
```

**Output:**
```
Current Session: SESSION-20260216-173003-09RZ
[Full banner displayed]
```

### List Recent Sessions

```bash
bash ~/.claude/memory/session-id-generator.sh list

# Limit results
bash ~/.claude/memory/session-id-generator.sh list --limit 5
```

**Output:**
```
📋 Recent Sessions (last 10):

✅ SESSION-20260216-173003-09RZ
   Started: 2026-02-16T17:30:03
   Status: COMPLETED
   Description: Feature implementation

🔄 SESSION-20260216-145520-B3X7
   Started: 2026-02-16T14:55:20
   Status: ACTIVE
   Description: Bug investigation
```

### Get Session Statistics

```bash
python ~/.claude/memory/session-id-generator.py stats --session-id SESSION-20260216-173003-09RZ
```

**Output:**
```
📊 Session Statistics: SESSION-20260216-173003-09RZ

Duration: 1:25:33
Total Work Items: 8
Completed: 6
In Progress: 2
Status: ACTIVE
```

### End Session

```bash
python ~/.claude/memory/session-id-generator.py end --session-id SESSION-20260216-173003-09RZ

# Or end current session
python ~/.claude/memory/session-id-generator.py end
```

---

## 📁 Storage Structure

### Session Files

**Location:** `~/.claude/memory/sessions/`

**Format:** `SESSION-YYYYMMDD-HHMMSS-XXXX.json`

**Example:** `~/.claude/memory/sessions/SESSION-20260216-173003-09RZ.json`

**Contents:**
```json
{
  "session_id": "SESSION-20260216-173003-09RZ",
  "type": "SESSION",
  "description": "Feature implementation",
  "start_time": "2026-02-16T17:30:03.123456",
  "end_time": null,
  "status": "ACTIVE",
  "metadata": {},
  "tasks": [],
  "work_items": [
    {
      "work_id": "IMPL-20260216-173105-K2N4",
      "type": "IMPL",
      "description": "Implement authentication logic",
      "started_at": "2026-02-16T17:31:05.789012",
      "completed_at": null,
      "status": "IN_PROGRESS",
      "metadata": {}
    }
  ]
}
```

### Session Log

**Location:** `~/.claude/memory/logs/sessions.log`

**Format:** `TIMESTAMP | SESSION_ID | EVENT | DETAILS`

**Example:**
```
2026-02-16T17:30:03.123456 | SESSION-20260216-173003-09RZ | CREATED | Feature implementation
2026-02-16T17:31:05.789012 | SESSION-20260216-173003-09RZ | WORK_ADDED | IMPL: Implement authentication logic
2026-02-16T17:45:22.456789 | SESSION-20260216-173003-09RZ | WORK_COMPLETED | IMPL-20260216-173105-K2N4
2026-02-16T18:55:36.123456 | SESSION-20260216-173003-09RZ | ENDED | COMPLETED
```

### Current Session Marker

**Location:** `~/.claude/memory/.current-session.json`

**Contents:**
```json
{
  "current_session_id": "SESSION-20260216-173003-09RZ",
  "started_at": "2026-02-16T17:30:03.123456"
}
```

---

## 🔧 Python API

### Import

```python
from session_id_generator import SessionIDGenerator

generator = SessionIDGenerator()
```

### Create Session

```python
session_id, session_data = generator.create_session(
    session_type='SESSION',
    description='Feature implementation',
    metadata={'project': 'my-project', 'priority': 'high'}
)

print(f"Created: {session_id}")
generator.display_session_banner(session_id)
```

### Add Work Item

```python
work_id = generator.add_work_item(
    session_id='SESSION-20260216-173003-09RZ',
    work_type='IMPL',
    description='Implement authentication logic',
    metadata={'file': 'auth.py'}
)

print(f"Work item created: {work_id}")
```

### Complete Work Item

```python
generator.complete_work_item(
    session_id='SESSION-20260216-173003-09RZ',
    work_id='IMPL-20260216-173105-K2N4',
    status='COMPLETED'
)
```

### End Session

```python
generator.end_session(
    session_id='SESSION-20260216-173003-09RZ',
    status='COMPLETED'
)
```

### Get Statistics

```python
stats = generator.get_session_stats('SESSION-20260216-173003-09RZ')
print(f"Duration: {stats['duration_formatted']}")
print(f"Completed: {stats['completed_work_items']}/{stats['total_work_items']}")
```

---

## 🎯 Use Cases

### 1. Session Tracking

Track all activity in a session:
```bash
# Start session
SESSION_ID=$(bash ~/.claude/memory/session-id-generator.sh create --description "Bug fix session")

# Do work...

# Check stats
python ~/.claude/memory/session-id-generator.py stats --session-id $SESSION_ID

# End session
python ~/.claude/memory/session-id-generator.py end --session-id $SESSION_ID
```

### 2. Debugging

Find session where error occurred:
```bash
# Search logs for session ID
grep "SESSION-20260216-173003-09RZ" ~/.claude/memory/logs/sessions.log

# Get full session data
cat ~/.claude/memory/sessions/SESSION-20260216-173003-09RZ.json | jq
```

### 3. Analytics

Analyze session patterns:
```bash
# List all sessions
bash ~/.claude/memory/session-id-generator.sh list --limit 50

# Calculate average duration
for session in ~/.claude/memory/sessions/SESSION-*.json; do
    python ~/.claude/memory/session-id-generator.py stats --session-id $(basename $session .json)
done
```

### 4. Collaboration

Share session ID with team:
```
"Check session SESSION-20260216-173003-09RZ for the implementation details"
```

---

## 🚨 Mandatory Requirements

**I MUST:**

1. **Generate session ID** on every session start
2. **Display session ID banner** to user
3. **Provide session ID** for tracking
4. **Log all session events** to sessions.log
5. **NEVER skip** showing session ID

**Format to show user:**
```
🆔 Session ID: SESSION-20260216-173003-09RZ
```

---

## 📊 Session Lifecycle

```
1. CREATE
   ↓
   [Session ID generated]
   ↓
   [Session file created]
   ↓
   [Marked as current]
   ↓
   [Banner displayed to user] ← MANDATORY

2. ACTIVE
   ↓
   [Work items added]
   ↓
   [Progress tracked]
   ↓
   [Events logged]

3. END
   ↓
   [Session marked completed]
   ↓
   [Final stats calculated]
   ↓
   [Current session cleared]
```

---

## 🔍 Troubleshooting

### Session ID Not Generated

**Check:**
1. Script exists: `ls ~/.claude/memory/session-id-generator.py`
2. Python works: `python --version`
3. Permissions: `chmod +x ~/.claude/memory/session-id-generator.py`

**Manually generate:**
```bash
export PYTHONIOENCODING=utf-8
python ~/.claude/memory/session-id-generator.py create
```

### Cannot Find Session

**Check:**
1. Session file exists: `ls ~/.claude/memory/sessions/SESSION-*.json`
2. Correct session ID format
3. Session log: `tail ~/.claude/memory/logs/sessions.log`

**List all sessions:**
```bash
bash ~/.claude/memory/session-id-generator.sh list
```

### Duplicate Session IDs

**Extremely rare** (random 4-char hash prevents collisions)

**If occurs:**
- Check system clock
- Verify random generator working
- Check for manual ID creation

---

## 🔮 Future Enhancements

- [ ] Session tagging system
- [ ] Session search by description/metadata
- [ ] Session export (PDF/CSV reports)
- [ ] Session sharing/collaboration
- [ ] Session templates
- [ ] Automatic session grouping
- [ ] Session performance analytics
- [ ] Integration with dashboard

---

**Created:** 2026-02-16
**Version:** 1.0.0
**Status:** 🟢 Active
**Mandatory:** Yes (show session ID to user)
