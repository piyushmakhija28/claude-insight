# Skill Registry System - Complete Guide

**Part of Claude Memory System v1.0.0**

---

## Overview

**Skill Registry System** provides:
- ✅ **Auto-detection** of relevant skills from user messages
- ✅ **Proactive suggestions** before starting work
- ✅ **Usage tracking** to identify most/least used skills
- ✅ **CRUD operations** for managing skills
- ✅ **Search & discovery** across all available skills

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  User Request                           │
│     "I need to add Stripe payment to my Flask app"     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              Skill Detector                             │
│  - Analyzes message for keywords                        │
│  - Matches trigger patterns                             │
│  - Calculates relevance scores                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│           Skills Registry (JSON)                        │
│  - payment-integration-python (75% match)               │
│  - payment-integration-java (40% match)                 │
│  - payment-integration-typescript (50% match)           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│          Auto-Suggestion to User                        │
│  "🔍 Relevant Skills Detected:                          │
│  1. Payment Integration - Python (75% match)            │
│     Complete payment gateway integration..."            │
└─────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Skills Registry (`skills-registry.json`)

**Central database** of all available skills.

**Structure:**
```json
{
  "version": "1.0.0",
  "skills": {
    "skill-id": {
      "name": "Skill Name",
      "file": "~/.claude/skills/skill-file.md",
      "description": "What this skill does",
      "keywords": ["keyword1", "keyword2"],
      "trigger_patterns": ["regex pattern"],
      "auto_suggest": true,
      "requires_context7": false,
      "usage_count": 0
    }
  },
  "categories": {...},
  "statistics": {...}
}
```

**Key Fields:**
- **keywords**: Simple text matching (e.g., "payment", "stripe", "python")
- **trigger_patterns**: Regex patterns (e.g., "payment.*python", "stripe.*flask")
- **auto_suggest**: Enable/disable auto-detection for this skill
- **requires_context7**: Does skill need latest documentation?
- **usage_count**: How many times skill was used

---

### 2. Skill Detector (`skill-detector.py`)

**Auto-detects relevant skills** from user messages.

**How It Works:**

```python
# Relevance Scoring Algorithm:

score = 0.0

# 1. Trigger pattern match → +0.5
if regex_matches(user_message, trigger_pattern):
    score += 0.5

# 2. Keyword matches → +0.1 per keyword (max +0.4)
for keyword in keywords:
    if keyword in user_message:
        score += 0.1  # capped at 0.4

# 3. Language match → +0.2
if language_mentioned(user_message):
    score += 0.2

# 4. Category match → +0.1
if category_mentioned(user_message):
    score += 0.1

# Max score: 1.0 (100% match)
```

**Usage:**
```bash
# Detect skills from message
python skill-detector.py "I need to add Stripe to my Flask app"

# Output:
# 🔍 Relevant Skills Detected:
# 1. Payment Integration - Python (75% match) [Context7 Required]
#    Complete payment gateway integration for Python...

# List all skills
python skill-detector.py --list

# Search for skills
python skill-detector.py --search "payment"

# Mark skill as used (updates stats)
python skill-detector.py --used "payment-integration-python"
```

---

### 3. Skill Manager (`skill-manager.py`)

**CRUD operations** for managing skills.

**Usage:**

```bash
# Add a new skill
python skill-manager.py add \
  --id "my-skill" \
  --name "My Skill" \
  --file "~/.claude/skills/my-skill.md" \
  --description "Does amazing things" \
  --language "python" \
  --category "automation" \
  --keywords "python,automation,script"

# Update a skill
python skill-manager.py update \
  --id "my-skill" \
  --keywords "python,automation,script,cli"

# Remove a skill
python skill-manager.py remove --id "my-skill"

# List all skills
python skill-manager.py list

# Show statistics
python skill-manager.py stats

# Export a skill (for sharing)
python skill-manager.py export --id "my-skill" --output skill.json

# Import a skill (from shared file)
python skill-manager.py import --file skill.json
```

---

## Integration with Claude

### Automatic Detection Flow

**STEP 1.5 in Execution Flow (After Context Validation):**

```
User: "I need to add Stripe payment to my Flask app"

↓

Claude (internally):
1. Validate context ✓
2. Run skill detector:
   python skill-detector.py "I need to add Stripe payment to my Flask app"

3. Detector finds:
   - payment-integration-python (75% match)
   - payment-integration-typescript (50% match)

4. Suggest to user:
   "🔍 I detected you're working on payment integration with Python!
    I have a payment-integration-python skill with Stripe examples.
    Want me to use it?"

5. If user agrees → Read skill file → Apply to task
```

**Logging:**
```bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] skill-detection | suggested | payment-integration-python | score=0.75" >> ~/.claude/memory/logs/policy-hits.log
```

---

## Pre-Loaded Skills

### Current Skills in Registry:

1. **payment-integration-python**
   - Category: payment
   - Language: python
   - Keywords: payment, stripe, razorpay, paypal, python, flask, django, fastapi
   - Trigger: `payment.*python`, `stripe.*flask`, etc.

2. **payment-integration-java**
   - Category: payment
   - Language: java
   - Keywords: payment, stripe, spring boot, java, rest controller
   - Trigger: `payment.*java`, `stripe.*spring`

3. **payment-integration-typescript**
   - Category: payment
   - Language: typescript
   - Keywords: payment, stripe, typescript, node.js, express, nestjs
   - Trigger: `payment.*typescript`, `stripe.*express`

4. **javafx-ide-designer**
   - Category: ui
   - Language: java
   - Keywords: javafx, ide, editor, syntax highlighting, ui, gui
   - Trigger: `ide.*design`, `javafx.*ui`, `code editor.*java`

---

## Usage Examples

### Example 1: Auto-Detect Payment Skill

**User:** "I want to integrate Razorpay in my Django app"

**Claude:**
```
🔍 Relevant Skills Detected:

1. Payment Integration - Python (80% match) [Context7 Required]
   Complete payment gateway integration for Python (Flask/Django/FastAPI)
   with Stripe, Razorpay, PayPal

I can help you implement Razorpay in Django using this skill.
Shall I proceed?
```

**Logged:**
```
[2026-01-26 14:30:00] skill-detection | suggested | payment-integration-python | score=0.8
```

---

### Example 2: Auto-Detect JavaFX IDE Skill

**User:** "I need to build a code editor in JavaFX with syntax highlighting"

**Claude:**
```
🔍 Relevant Skills Detected:

1. JavaFX IDE Designer (85% match) [Context7 Required]
   Complete IDE interface design using JavaFX with editor, file tree,
   console, syntax highlighting, dark theme

This skill provides a complete IDE layout. Want me to use it?
```

---

### Example 3: No Match

**User:** "What's the weather today?"

**Claude:**
```
(No skills detected - score below 30% threshold)
(Proceed with normal response)
```

---

## Adding Your Own Skills

### Step 1: Create Skill File

```bash
# Create skill markdown file
~/.claude/skills/my-awesome-skill.md
```

### Step 2: Add to Registry

```bash
python skill-manager.py add \
  --id "my-awesome-skill" \
  --name "My Awesome Skill" \
  --file "~/.claude/skills/my-awesome-skill.md" \
  --description "Does awesome things with Python" \
  --language "python" \
  --category "automation" \
  --keywords "python,automation,cli,script"
```

### Step 3: Test Detection

```bash
python skill-detector.py "I need a Python automation script"
```

### Step 4: Use in Session

When user mentions relevant keywords, Claude will auto-suggest your skill!

---

## Best Practices

### For Skill Authors:

1. **Choose Good Keywords:**
   - Include language (python, java, typescript)
   - Include domain (payment, ui, database)
   - Include frameworks (flask, spring boot, express)
   - Include actions (integration, design, deployment)

2. **Write Clear Trigger Patterns:**
   ```
   Good: "payment.*python"  (matches "payment in python", "python payment")
   Bad:  "payment"          (too broad, matches everything)
   ```

3. **Set Auto-Suggest Wisely:**
   - `auto_suggest: true` for general-purpose skills
   - `auto_suggest: false` for highly specialized skills

4. **Mark Context7 Requirement:**
   - `requires_context7: true` if skill needs latest docs
   - This warns user to fetch documentation first

5. **Update Regularly:**
   - Keep keywords current
   - Update trigger patterns based on usage
   - Track usage stats to see if skill is discoverable

---

## Statistics Tracking

### What Gets Tracked:

- **Total skills** in registry
- **Usage count** per skill (how many times used)
- **Last used** timestamp
- **Most/least used** skills
- **Skills by language** (Python: 5, Java: 3, etc.)
- **Skills by category** (payment: 3, ui: 2, etc.)

### View Statistics:

```bash
python skill-manager.py stats

# Output:
# === Skill Registry Statistics ===
# Total Skills: 4
# Version: 1.0.0
# Last Updated: 2026-01-26
#
# By Language:
#   python: 1
#   java: 2
#   typescript: 1
#
# By Category:
#   payment: 3
#   ui: 1
#
# Most Used: payment-integration-python (12 times)
```

---

## Integration Points

### 1. With Session Memory

Skill usage can be saved to session memory:

```markdown
# project-summary.md

## Skills Used:
- payment-integration-python (used for Stripe integration)
- javafx-ide-designer (used for code editor UI)
```

### 2. With Failure Learning

If skill application fails, pattern recorded:

```markdown
# failures.md

## Pattern: skill-application-error
- Skill: payment-integration-python
- Error: Missing dependency (stripe SDK)
- Prevention: Check dependencies before suggesting skill
```

### 3. With Context7

Skills marked `requires_context7: true` trigger automatic doc fetch:

```python
if skill.requires_context7:
    context7.search(f"{skill.language} {skill.keywords[0]} latest docs 2026")
```

---

## Troubleshooting

### Skill Not Detected?

1. **Check keywords:**
   ```bash
   python skill-manager.py list
   # Look at skill keywords
   ```

2. **Test pattern matching:**
   ```bash
   python skill-detector.py "your exact user message here"
   # Should show relevance score
   ```

3. **Lower threshold:**
   ```python
   # In skill-detector.py, change threshold:
   matches = detector.detect_skills(message, threshold=0.2)  # Lower = more matches
   ```

4. **Add more keywords:**
   ```bash
   python skill-manager.py update --id "my-skill" --keywords "old,keywords,new,ones"
   ```

---

### Skill Suggested Too Often?

1. **Increase threshold:**
   ```python
   matches = detector.detect_skills(message, threshold=0.5)  # Higher = fewer matches
   ```

2. **Disable auto-suggest:**
   ```bash
   python skill-manager.py update --id "my-skill" --auto-suggest false
   ```

3. **Make trigger patterns more specific:**
   ```bash
   # Change from:
   "payment"  # Too broad

   # To:
   "payment.*integration.*python"  # More specific
   ```

---

## File Locations

```
~/.claude/memory/
├── skills-registry.json           # Central registry (THIS IS THE SOURCE OF TRUTH)
├── skill-detector.py              # Auto-detection engine
├── skill-manager.py               # CRUD operations
├── SKILL-REGISTRY-SYSTEM.md       # This guide
└── logs/
    └── skill-detector.log         # Detection events log

~/.claude/skills/
├── payment-integration-python.md
├── payment-integration-java.md
├── payment-integration-typescript.md
└── javafx-ide-designer.md
```

---

## API Reference

### SkillDetector API

```python
from skill_detector import SkillDetector

detector = SkillDetector()

# Detect skills
matches = detector.detect_skills("user message", threshold=0.3)
# Returns: [{'skill_id': '...', 'name': '...', 'score': 0.75, ...}]

# Get suggestions (formatted)
suggestions = detector.suggest_skills("user message", max_suggestions=3)
# Returns: Formatted string for user

# Update usage
detector.update_usage("skill-id")

# List all
all_skills = detector.list_all_skills()

# Search
results = detector.search_skills("payment")
```

### SkillManager API

```python
from skill_manager import SkillManager

manager = SkillManager()

# Add skill
manager.add_skill("skill-id", name="...", file="...", ...)

# Update skill
manager.update_skill("skill-id", keywords=["new", "keywords"])

# Remove skill
manager.remove_skill("skill-id")

# Get skill
skill = manager.get_skill("skill-id")

# Stats
manager.show_statistics()
```

---

## Version

**Version:** 1.0.0
**Created:** 2026-01-26
**Status:** Production Ready
**Part of:** Claude Memory System

---

## Quick Commands

```bash
# Detect from message
python ~/.claude/memory/skill-detector.py "your message here"

# List all skills
python ~/.claude/memory/skill-detector.py --list

# Search skills
python ~/.claude/memory/skill-detector.py --search "keyword"

# Add new skill
python ~/.claude/memory/skill-manager.py add --id "..." --name "..." ...

# View stats
python ~/.claude/memory/skill-manager.py stats
```

---

**🚀 Skill Registry makes Claude proactive and intelligent about suggesting the right skills at the right time!**
