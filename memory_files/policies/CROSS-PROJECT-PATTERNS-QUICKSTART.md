# Cross-Project Pattern Detection - Quick Start Guide

## 🎯 What is This?

**Learn from your work across ALL projects!**

This system analyzes your completed projects and detects patterns in:
- Technologies you consistently use
- Architecture choices you make
- Workflows you follow

Then it suggests these patterns when you start new work!

---

## 📚 Quick Commands

### 1. Detect Patterns (Run Monthly)

```bash
python ~/.claude/memory/detect-patterns.py
```

**What it does:**
- Scans all your projects
- Finds common technologies/approaches
- Detects patterns (3+ projects)
- Saves patterns for future use

**Output:**
```
🔍 Analyzing 8 projects for patterns...

✅ Pattern detected: JWT (authentication)
   Confidence: 75%
   Found in: 6 projects

✅ Pattern detected: POSTGRESQL (databases)
   Confidence: 62%
   Found in: 5 projects

📊 Summary:
   Projects analyzed: 8
   Patterns detected: 12
```

---

### 2. View Detected Patterns

```bash
python ~/.claude/memory/detect-patterns.py --show
```

**What it shows:**
- All detected patterns
- Confidence levels
- Which projects use them

**Output:**
```
🎯 Cross-Project Patterns Detected
======================================================================

📁 AUTHENTICATION
  ✓ JWT
    Confidence: [███████   ] 75%
    Found in 6 projects: app1, app2, app3...

📁 DATABASES
  ✓ POSTGRESQL
    Confidence: [██████    ] 62%
    Found in 5 projects: app1, app3, app5...
```

---

### 3. Get Pattern Suggestions

```bash
python ~/.claude/memory/apply-patterns.py <topic>
```

**Examples:**
```bash
# Authentication patterns
python ~/.claude/memory/apply-patterns.py authentication

# Database patterns
python ~/.claude/memory/apply-patterns.py database

# API patterns
python ~/.claude/memory/apply-patterns.py "rest api"

# Language patterns
python ~/.claude/memory/apply-patterns.py language

# Frontend patterns
python ~/.claude/memory/apply-patterns.py frontend
```

**Output:**
```
💡 Based on your past projects, here are relevant patterns:
======================================================================

1. JWT (STRONG PATTERN)
   Confidence: [███████   ] 75%
   Used in: 6 of your projects

   💡 Suggestion: Consider using JWT authentication
      You've successfully used this in 6 projects
```

---

## 🎯 How It Works

### Step 1: Analysis (Monthly)

```
Your Projects:
├── project-1 (JWT, PostgreSQL, React)
├── project-2 (JWT, PostgreSQL, Angular)
├── project-3 (JWT, MongoDB, React)
├── project-4 (Session, PostgreSQL, Vue)
├── project-5 (JWT, PostgreSQL, React)
└── project-6 (JWT, PostgreSQL, React)

Pattern Detection:
✅ JWT → 5/6 projects (83% confidence) = STRONG PATTERN
✅ PostgreSQL → 5/6 projects (83% confidence) = STRONG PATTERN
✅ React → 4/6 projects (67% confidence) = MODERATE PATTERN
❌ MongoDB → 1/6 projects (17% confidence) = NO PATTERN
```

---

### Step 2: Application (When Working)

```
User: "I need authentication for my new app"

Claude checks:
  python apply-patterns.py authentication
  Result: JWT (83% confidence)

Claude suggests:
  "You consistently use JWT authentication across
   5 of your 6 projects. Should I implement JWT?"
```

---

## 🔥 Real-World Examples

### Example 1: Authentication Choice

**Your History:**
- 6 projects total
- 5 use JWT authentication
- 1 uses session authentication

**When you start new project:**
```bash
$ python apply-patterns.py authentication

💡 JWT (STRONG PATTERN)
   Confidence: 83%
   Suggestion: Use JWT authentication (you've used it in 5 projects)
```

**Result:** You see your own pattern and can choose to follow it (or not!)

---

### Example 2: Database Choice

**Your History:**
- 8 projects total
- 5 use PostgreSQL
- 3 use MongoDB

**When you need a database:**
```bash
$ python apply-patterns.py database

1. POSTGRESQL (MODERATE PATTERN)
   Confidence: 62%
   Used in: 5 projects

2. MONGODB (WEAK)
   Confidence: 37%
   Used in: 3 projects
```

**Result:** See your preferences, make informed decision!

---

### Example 3: Frontend Framework

**Your History:**
- 6 projects with frontend
- 4 use React
- 2 use Angular

**When building UI:**
```bash
$ python apply-patterns.py frontend

1. REACT (MODERATE PATTERN)
   Confidence: 67%
   Used in: 4 projects

2. ANGULAR (WEAK)
   Confidence: 33%
   Used in: 2 projects
```

**Result:** React is your stronger pattern!

---

## 📊 Confidence Levels

### STRONG (80-100%)
```
Pattern: [████████  ] 85%
Meaning: You use this in 85% of projects
Action: Strong recommendation
```

### MODERATE (60-79%)
```
Pattern: [██████    ] 65%
Meaning: You use this in 65% of projects
Action: Solid suggestion
```

### WEAK (50-59%)
```
Pattern: [█████     ] 55%
Meaning: You use this in 55% of projects
Action: Mild suggestion
```

### BELOW 50%
```
Not considered a pattern - no clear preference
```

---

## ⚙️ Pattern Categories

### What Gets Detected:

**1. Languages**
- Python, JavaScript, TypeScript, Java, Go, etc.

**2. Frontend Frameworks**
- React, Angular, Vue, Svelte

**3. Databases**
- PostgreSQL, MySQL, MongoDB, Redis

**4. Authentication**
- JWT, OAuth, Session, Basic Auth

**5. API Style**
- REST, GraphQL, gRPC

**6. Testing**
- Unit tests, Integration tests, TDD

**7. DevOps**
- Docker, Kubernetes, CI/CD tools

---

## 🔄 Typical Workflow

### Month 1: First Detection

```bash
# After completing 3+ projects
$ python ~/.claude/memory/detect-patterns.py

📊 Summary:
   Projects analyzed: 4
   Patterns detected: 5
```

---

### Month 2: Use Patterns

```bash
# Starting new work on authentication
$ python ~/.claude/memory/apply-patterns.py authentication

💡 JWT (MODERATE PATTERN)
   Confidence: 75%
   You've used this in 3 of 4 projects
```

**You:** "Yes, use JWT!" (or "No, try OAuth this time")

---

### Month 3: Re-detect

```bash
# After completing more work
$ python ~/.claude/memory/detect-patterns.py

📊 Summary:
   Projects analyzed: 7
   Patterns detected: 8

# Patterns get stronger with more data!
```

---

## ⚠️ Important Notes

### This is NOT:
❌ Forcing you to repeat old approaches
❌ Limiting your technology choices
❌ Preventing experimentation

### This IS:
✅ Showing you your own patterns
✅ Helping maintain consistency (when desired)
✅ Informed decision-making
✅ Learning from your own experience

### Remember:
**Patterns are suggestions, not rules!**

You can always:
- Choose different technologies
- Try new approaches
- Experiment freely

---

## 📅 Maintenance Schedule

### Monthly (Recommended)

```bash
# First Sunday of each month
python ~/.claude/memory/detect-patterns.py
```

---

### After Major Projects

```bash
# Completed a big project?
# New patterns may have emerged!
python ~/.claude/memory/detect-patterns.py
```

---

### Before Starting New Work

```bash
# Get pattern suggestions
python ~/.claude/memory/apply-patterns.py <topic>
```

---

## 🎯 Benefits

### 1. Self-Awareness
**See your own working patterns clearly**

### 2. Consistency
**Maintain similar approaches across projects (when desired)**

### 3. Speed
**Leverage proven solutions you've used before**

### 4. Learning
**Understand your own preferences and evolution**

### 5. Decisions
**Make informed choices based on your experience**

---

## 📊 Example Session

```bash
# Step 1: Run monthly detection
$ python detect-patterns.py

✅ JWT detected (6 projects, 75%)
✅ PostgreSQL detected (5 projects, 62%)
✅ React detected (4 projects, 50%)

# Step 2: Start new project
$ python apply-patterns.py authentication

💡 JWT (STRONG PATTERN - 75%)
   Use JWT? Yes/No

# Step 3: Make decision
You: "Yes, use JWT!" (pattern followed)
OR
You: "No, try OAuth this time!" (pattern ignored - that's OK!)

# Pattern system adapts to your actual work
```

---

## 🛠️ Troubleshooting

### Issue: No Patterns Detected

**Cause:** Less than 3 projects analyzed

**Solution:** Normal - need 3+ projects for pattern detection

---

### Issue: Patterns Seem Wrong

**Cause:** Old sessions with different approaches

**Solution:** Re-run detection after completing current work:
```bash
python detect-patterns.py
```

---

### Issue: Want Stricter Patterns

**Cause:** Too many weak patterns

**Solution:** Edit threshold in `cross-project-patterns.json`:
```json
{
  "metadata": {
    "detection_threshold": 4  // Require 4+ projects instead of 3
  }
}
```

---

## 📁 Files & Locations

**Pattern Storage:**
```
~/.claude/memory/cross-project-patterns.json
```

**Detection Script:**
```
~/.claude/memory/detect-patterns.py
```

**Application Script:**
```
~/.claude/memory/apply-patterns.py
```

**View Patterns:**
```bash
cat ~/.claude/memory/cross-project-patterns.json
# OR
python detect-patterns.py --show
```

---

## 🎉 Summary

**What it does:**
- Detects patterns across all your projects
- Shows your consistent technology choices
- Suggests approaches based on your history

**When to use:**
- Run detection: Monthly
- Apply patterns: When starting new work
- Review patterns: Anytime

**Key principle:**
**Learn from yourself, but stay flexible!**

---

**Status:** ✅ READY TO USE | **Location:** `~/.claude/memory/detect-patterns.py`
