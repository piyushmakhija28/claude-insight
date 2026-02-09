# Skill Registry - Quick Start Guide

**Get started with auto-skill detection in 3 minutes!**

---

## What Is This?

**Skill Registry** makes Claude **proactively suggest relevant skills** when you ask for help.

**Example:**
```
You: "I need to add Stripe payment to my Flask app"

Claude: "=== Relevant Skills Detected ===
         1. Payment Integration - Python (90% match)
         Want me to use this skill?"
```

**No more:**
- ❌ Forgetting which skills exist
- ❌ Searching through documentation
- ❌ Manually requesting skills

**Instead:**
- ✅ Claude auto-detects what you need
- ✅ Suggests best match with score
- ✅ Applies skill immediately if you agree

---

## How It Works (Behind the Scenes)

```
Your Request
    ↓
Skill Detector analyzes keywords
    ↓
Matches against registry (4 skills currently)
    ↓
Returns top matches with relevance scores
    ↓
Claude suggests to you
    ↓
You approve → Skill applied!
```

---

## Current Available Skills

### 1. Payment Integration - Python
**When to use:** Python payment gateway integration
**Covers:** Stripe, Razorpay, PayPal, Flask/Django/FastAPI
**Trigger words:** payment, stripe, razorpay, python, flask, django

### 2. Payment Integration - Java
**When to use:** Java Spring Boot payment integration
**Covers:** Stripe, Razorpay, PayPal, REST controllers
**Trigger words:** payment, stripe, java, spring boot

### 3. Payment Integration - TypeScript
**When to use:** Node.js payment integration
**Covers:** Stripe, Razorpay, PayPal, Express/NestJS
**Trigger words:** payment, stripe, typescript, node, express

### 4. JavaFX IDE Designer
**When to use:** Building IDE/code editor with JavaFX
**Covers:** Editor, file tree, console, syntax highlighting, dark theme
**Trigger words:** javafx, ide, editor, code editor, ui

---

## Quick Test

Try these commands to see it in action:

### Test 1: Payment Detection
```bash
python ~/.claude/memory/skill-detector.py "I need to add Stripe to my Flask app"
```

**Expected:**
```
=== Relevant Skills Detected ===
1. Payment Integration - Python (90% match) [Context7 Required]
```

### Test 2: JavaFX Detection
```bash
python ~/.claude/memory/skill-detector.py "I want to build an IDE with JavaFX"
```

**Expected:**
```
=== Relevant Skills Detected ===
1. JavaFX IDE Designer (100% match) [Context7 Required]
```

### Test 3: List All Skills
```bash
python ~/.claude/memory/skill-detector.py --list
```

**Expected:**
```
=== Available Skills ===
• Payment Integration - Python
• Payment Integration - Java
• Payment Integration - TypeScript
• JavaFX IDE Designer
Total Skills: 4
```

---

## Using in Claude Sessions

### Automatic (Recommended!)

Just ask Claude normally:

```
You: "I need to integrate Razorpay in my Django project"

Claude: (internally runs skill detector)
        "I detected a relevant skill: Payment Integration - Python
         This covers Razorpay integration for Django. Use it?"

You: "Yes"

Claude: (reads skill file and applies it)
```

### Manual (If Needed)

You can also explicitly request:

```
You: "Search for payment skills"

Claude: (runs: python skill-detector.py --search "payment")
        Shows all payment-related skills
```

---

## Adding Your Own Skills

### Step 1: Create Skill File

Create a markdown file in `~/.claude/skills/`:

```bash
~/.claude/skills/my-skill.md
```

### Step 2: Register It

```bash
python ~/.claude/memory/skill-manager.py add \
  --id "my-skill" \
  --name "My Awesome Skill" \
  --file "~/.claude/skills/my-skill.md" \
  --description "What it does" \
  --language "python" \
  --category "automation" \
  --keywords "python,cli,automation"
```

### Step 3: Test Detection

```bash
python ~/.claude/memory/skill-detector.py "python automation script"
```

Should detect your new skill!

---

## Understanding Match Scores

**How relevance is calculated:**

```
Score Breakdown (max 100%):

+50% = Trigger pattern match
       Example: "payment.*python" matches "payment in python"

+40% = Keyword matches (10% per keyword, max 4)
       Example: "stripe", "python", "flask", "payment" all found

+20% = Language mentioned
       Example: "python" found in message

+10% = Category mentioned
       Example: "payment" category mentioned

────────────────────────────────
 100% = Perfect match!
```

**Threshold:** Only skills scoring 30%+ are suggested.

---

## Pro Tips

### Tip 1: Use Specific Keywords

```
Less specific: "I need to add payments"
→ Might match multiple skills

More specific: "I need to integrate Stripe in my Flask app"
→ Higher score, better match
```

### Tip 2: Mention the Language

```
"I need payment integration"        → All 3 payment skills match
"I need payment integration Python" → Python skill scores highest
```

### Tip 3: Check What Triggered

```bash
# If unexpected skill suggested, check its keywords:
python ~/.claude/memory/skill-manager.py list
# Then adjust your request phrasing
```

---

## Troubleshooting

### Skill Not Detected?

**Possible reasons:**
1. **Score below 30% threshold**
   - Try using more specific keywords
   - Mention the language/framework

2. **Auto-suggest disabled**
   - Check: `auto_suggest: true` in registry

3. **Wrong keywords**
   - Add more relevant keywords to skill

**Solution:**
```bash
# Check current keywords
python ~/.claude/memory/skill-detector.py --list

# Update keywords
python ~/.claude/memory/skill-manager.py update \
  --id "skill-id" \
  --keywords "new,keywords,here"
```

---

### Too Many Skills Suggested?

**Problem:** Every request triggers skill suggestions

**Solution:**
1. **Increase threshold** (in skill-detector.py line 87):
   ```python
   matches = self.detect_skills(user_message, threshold=0.5)  # Higher = fewer
   ```

2. **Disable auto-suggest** for specific skills:
   ```bash
   python ~/.claude/memory/skill-manager.py update \
     --id "chatty-skill" \
     --auto-suggest false
   ```

---

## Files & Locations

```
~/.claude/memory/
├── skills-registry.json           # Central registry (4 skills currently)
├── skill-detector.py              # Detection engine
├── skill-manager.py               # CRUD operations
├── SKILL-REGISTRY-SYSTEM.md       # Full documentation
└── SKILL-REGISTRY-QUICK-START.md  # This file

~/.claude/skills/
├── payment-integration-python.md
├── payment-integration-java.md
├── payment-integration-typescript.md
└── javafx-ide-designer.md
```

---

## Stats & Usage Tracking

### View Statistics

```bash
python ~/.claude/memory/skill-manager.py stats
```

**Output:**
```
Total Skills: 4
By Language: python (1), java (2), typescript (1)
By Category: payment (3), ui (1)
Most Used: payment-integration-python (12 times)
```

### Mark Skill as Used

(Automatic when Claude applies a skill, but you can also manually track:)

```bash
python ~/.claude/memory/skill-detector.py --used "payment-integration-python"
```

---

## Integration with Other Systems

### With Session Memory

When Claude uses a skill, it's saved to session memory:

```markdown
# ~/.claude/memory/sessions/my-project/project-summary.md

## Skills Used:
- payment-integration-python (Stripe integration)
```

### With Failure Learning

If skill fails, pattern is learned:

```markdown
# ~/.claude/memory/sessions/my-project/failures.md

## Pattern: missing-dependency
- Skill: payment-integration-python
- Issue: Stripe SDK not installed
- Prevention: Check dependencies first
```

### With Context7

Skills marked `requires_context7: true` trigger automatic doc fetches before application.

---

## Next Steps

1. ✅ **Test the system:**
   ```bash
   python ~/.claude/memory/skill-detector.py "your test message"
   ```

2. ✅ **Try in a session:**
   Ask Claude for help with payment or JavaFX tasks

3. ✅ **Add your own skills:**
   Follow "Adding Your Own Skills" section

4. ✅ **Monitor usage:**
   ```bash
   python ~/.claude/memory/skill-manager.py stats
   ```

5. ✅ **Read full docs (if needed):**
   ```bash
   ~/.claude/memory/SKILL-REGISTRY-SYSTEM.md
   ```

---

## Summary

**Skill Registry System:**
- ✅ Auto-detects relevant skills from your messages
- ✅ Suggests best matches with relevance scores
- ✅ Currently includes 4 production-ready skills
- ✅ Easy to add your own skills
- ✅ Integrated with session memory & failure learning
- ✅ Tracks usage statistics

**Result:** Claude becomes proactive and intelligent about skill suggestions! 🚀

---

**Version:** 1.0.0 | **Status:** Production Ready | **Updated:** 2026-01-26
