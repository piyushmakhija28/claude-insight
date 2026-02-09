# Global User Preferences - Quick Start Guide

## 🎯 What is This?

**Claude remembers your repeated choices across all projects!**

After you make the same choice 3 times, Claude saves it as a global preference and stops asking you the same question.

---

## 📚 Example: Testing Preference

### First 3 Times (Learning Phase)

**Session 1:**
```
You: "Implement user login"
Claude: "Skip tests? (Recommended)"
You: "Yes"
Claude: [Records: 1/3]
```

**Session 2:**
```
You: "Add password reset"
Claude: "Skip tests? (Recommended)"
You: "Yes"
Claude: [Records: 2/3]
```

**Session 3:**
```
You: "Implement logout"
Claude: "Skip tests? (Recommended)"
You: "Yes"
Claude: [Learns: testing = skip ✅]
```

### 4th Time Onwards (Auto-Apply Phase)

**Session 4:**
```
You: "Add profile page"
Claude: "Skipping tests (based on your preference)"
       [Proceeds without asking]
```

**You can always override:**
```
You: "Actually, write tests this time"
Claude: "Got it! Writing tests for profile page."
```

---

## 🗂️ What Gets Tracked?

### Technology Preferences
- **api_style**: REST, GraphQL, gRPC
- **testing**: skip, full_coverage, unit_only
- **ui_theme**: dark, light, auto
- **auth_method**: JWT, OAuth, session
- **database**: postgres, mysql, mongodb

### Language Preferences
- **backend**: python, java, node, go
- **frontend**: react, angular, vue
- **scripting**: python, bash, powershell

### Workflow Preferences
- **commit_style**: conventional, descriptive, simple
- **plan_mode**: always_ask, auto_enter, skip
- **phased_execution**: preferred, ask, avoid
- **documentation**: minimal, comprehensive, inline

---

## 🔧 View Your Preferences

```bash
python ~/.claude/memory/load-preferences.py
```

**Output:**
```
🎯 Global User Preferences
============================================================

📱 Technology Preferences:
  ✓ api_style: REST
  ✓ testing: skip
  - ui_theme: (not set)

💻 Language Preferences:
  ✓ backend: python
  ✓ frontend: typescript

⚙️  Workflow Preferences:
  ✓ commit_style: conventional
  ✓ plan_mode: always_ask

📊 Statistics:
  Total preferences learned: 5
  Learning threshold: 3
```

---

## 🛠️ Advanced: Manual Management

### Check Specific Preference
```bash
python ~/.claude/memory/load-preferences.py testing
# Output: skip
```

### Check If Preference Exists
```bash
python ~/.claude/memory/load-preferences.py --has api_style
# Output: yes
```

### Reset a Preference
Edit `~/.claude/memory/user-preferences.json`:
```json
{
  "technology_preferences": {
    "testing": null  // Reset to null
  }
}
```

### Change Learning Threshold
```json
{
  "metadata": {
    "learning_threshold": 5  // Require 5 observations instead of 3
  }
}
```

---

## 🔒 Privacy

**100% LOCAL!**
- All preferences stored in: `~/.claude/memory/user-preferences.json`
- No API calls, no cloud storage
- Complete control over your data

---

## 📊 Monitoring

### View Learning History
```bash
tail -f ~/.claude/memory/logs/policy-hits.log | grep user-preferences
```

**Example output:**
```
[2026-01-26 20:03:29] user-preferences | tracked | testing=skip | count=1/3
[2026-01-26 20:03:45] user-preferences | tracked | testing=skip | count=2/3
[2026-01-26 20:03:53] user-preferences | learned | testing=skip | threshold_reached
[2026-01-26 20:15:22] user-preferences | applied | testing=skip
```

---

## ❓ FAQ

### Q: Can I override a preference?
**A:** Yes! Just tell Claude explicitly:
```
"Actually, write tests this time"
"Use GraphQL instead"
"Enter plan mode for this one"
```

### Q: How do I delete all preferences?
**A:** Delete the file:
```bash
rm ~/.claude/memory/user-preferences.json
```
Then recreate it:
```bash
python ~/.claude/memory/track-preference.py testing skip  # Will error
# Follow instructions to recreate structure
```

### Q: Can I add custom preference categories?
**A:** Yes! Edit `user-preferences.json` and add to both:
- Top-level category (e.g., `technology_preferences`)
- `learning_data` section

### Q: Does this work across all projects?
**A:** YES! These are GLOBAL preferences. They apply to ALL projects on your machine.

---

## 🎉 Benefits

### Before (Without Preferences):
```
Session 1: "Skip tests?" → You: "Yes"
Session 2: "Skip tests?" → You: "Yes"
Session 3: "Skip tests?" → You: "Yes"
Session 4: "Skip tests?" → You: "Yes"  😫 (Repetitive!)
```

### After (With Preferences):
```
Session 1: "Skip tests?" → You: "Yes" [1/3]
Session 2: "Skip tests?" → You: "Yes" [2/3]
Session 3: "Skip tests?" → You: "Yes" [Learned! ✅]
Session 4: "Skipping tests (based on your preference)" 🎯 (Automatic!)
```

**Result:** Faster workflows, less repetition, Claude knows you better!

---

**Status:** ACTIVE | **Version:** 1.0 | **Location:** `~/.claude/memory/user-preferences.json`
