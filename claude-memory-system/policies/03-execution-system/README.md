# 🔴 EXECUTION SYSTEM (Implementation Layer)

**PURPOSE:** Execute tasks following loaded standards from Rules/Standards System

---

## 📊 What This System Does

**Executes 11 Steps in Order:**

1. **Prompt Generation** - Convert natural language to structured prompt
2. **Task Breakdown** - Divide into phases and tasks
3. **Plan Mode Suggestion** - Auto-suggest plan mode based on complexity
4. **Model Selection** - Choose Haiku/Sonnet/Opus intelligently
5. **Skill/Agent Selection** - Auto-select skills and agents
6. **Tool Optimization** - Optimize tools for 60-85% token savings
7. **Auto Recommendations** - Real-time model/skill/agent recommendations
8. **Progress Tracking** - Auto-track task progress with granular updates
9. **Execution** - Generate code following loaded standards
10. **Git Auto-Commit** - Auto-commit on phase/task completion
11. **Session Save** - Save session with unique ID

**OUTPUT:** Code generated with 100% standards compliance

---

## 📁 Sub-Folders (Organized by Step)

```
03-execution-system/
├── 00-prompt-generation/        🔴 Step 0: Structured prompts
│   ├── prompt-generation-policy.md
│   ├── anti-hallucination-enforcement.md
│   └── prompt-generator.py
│
├── 01-task-breakdown/           🎯 Step 1: Phases & tasks
│   ├── automatic-task-breakdown-policy.md
│   ├── task-auto-tracker.py
│   └── task-phase-enforcer.py
│
├── 02-plan-mode/                🎯 Step 2: Plan mode decision
│   ├── auto-plan-mode-suggestion-policy.md
│   └── auto-plan-mode-suggester.py
│
├── 04-model-selection/          🤖 Step 4: Haiku/Sonnet/Opus
│   ├── intelligent-model-selection-policy.md
│   ├── intelligent-model-selector.py
│   ├── model-selection-enforcement.md
│   ├── model-selection-enforcer.py
│   └── model-selection-monitor.py
│
├── 05-skill-agent-selection/    🤖 Step 5: Skills & agents
│   ├── auto-skill-agent-selection-policy.md
│   ├── auto-skill-agent-selector.py
│   ├── adaptive-skill-registry.md
│   ├── core-skills-mandate.md
│   ├── core-skills-enforcer.py
│   └── auto-register-skills.py
│
├── 06-tool-optimization/        ⚡ Step 6: Token savings
│   ├── tool-usage-optimization-policy.md
│   ├── tool-usage-optimizer.py
│   ├── auto-tool-wrapper.py
│   ├── smart-read.py
│   ├── ast-code-navigator.py
│   └── token-optimization-daemon.py
│
├── 07-recommendations/          🤖 Step 7: Auto recommendations
│   ├── README.md
│   ├── auto-recommendation-daemon.py
│   ├── check-recommendations.py
│   ├── skill-detector.py
│   ├── skill-auto-suggester.py
│   └── skill-manager.py
│
├── 08-progress-tracking/        📊 Step 8: Progress tracking
│   ├── README.md
│   ├── task-phase-enforcement-policy.md
│   ├── task-progress-tracking-policy.md
│   └── check-incomplete-work.py
│
├── 09-git-commit/               📤 Step 9: Auto-commit
│   ├── git-auto-commit-policy.md
│   ├── auto-commit.py
│   ├── auto-commit-detector.py
│   ├── auto-commit-enforcer.py
│   ├── commit-daemon.py
│   └── trigger-auto-commit.py
│
└── failure-prevention/          🛡️ Failure prevention
    ├── common-failures-prevention.md
    ├── failure-detector.py
    ├── failure-detector-v2.py
    ├── failure-kb.json
    ├── failure-learner.py
    ├── failure-pattern-extractor.py
    ├── failure-prevention-daemon.py
    ├── failure-solution-learner.py
    ├── pre-execution-checker.py
    └── update-failure-kb.py
```

**Total: 10 sub-folders, 50+ files organized by step**

---

## 🔗 Dependencies

**Depends on:**
1. Sync System (Context + Session loaded)
2. Rules/Standards System (Standards loaded)

**Provides:**
- Generated code following standards
- Auto-tracked progress
- Auto-committed changes
- Saved sessions

---

## ⚙️ Integration

**Position in Flow:**
```
🔵 SYNC SYSTEM (Context + Session)
        ↓
🟢 RULES/STANDARDS SYSTEM (Load standards)
        ↓
🔴 EXECUTION SYSTEM (THIS) - Execute with standards
```

---

## 🎯 Usage Examples

### **Step 0: Generate Structured Prompt**
```bash
python prompt-generator.py "Create Product API"
```

### **Step 1: Break into Tasks**
```bash
python task-auto-tracker.py --analyze "Create Product API"
```

### **Step 2: Check Plan Mode**
```bash
python auto-plan-mode-suggester.py --complexity 15 --task "Create Product API"
```

### **Step 4: Select Model**
```bash
python intelligent-model-selector.py --complexity 15 --task "API Creation" --plan-mode NO
```

### **Step 5: Select Skills/Agents**
```bash
python auto-skill-agent-selector.py --technologies "Spring Boot,JWT" --complexity 15
```

### **Step 6: Optimize Tools**
```bash
python tool-usage-optimizer.py Read read_params.json context.json
```

### **Step 9: Auto-Commit**
```bash
python auto-commit-enforcer.py --enforce-now
```

---

## ✅ Key Features

### **Anti-Hallucination (Step 0):**
- Think → Gather Info → Verify
- Answer based on FOUND info only
- Flag uncertainties

### **Auto Task Breakdown (Step 1):**
- Calculate complexity score
- Divide into phases if complex
- Auto-create all tasks
- Auto-detect dependencies
- Auto-track progress

### **Intelligent Model Selection (Step 4):**
- Plan mode → OPUS
- Complex → SONNET
- Simple → HAIKU
- Security → Upgrade to SONNET

### **Auto Skill/Agent Selection (Step 5):**
- Complexity < 10 → Skill
- Complexity >= 10 → Agent
- Technology-based matching

### **Tool Optimization (Step 6):**
- Read: offset/limit for >500 lines
- Grep: head_limit always
- Tree: Understand structure first
- 60-85% token savings

### **Auto Recommendations (Step 7):**
- Real-time recommendations (every 5s)
- Optimal model selection
- Skill/agent suggestions
- Context status monitoring
- Applied at session start

### **Progress Tracking (Step 8):**
- BLOCKING enforcement (complexity-based)
- Granular progress updates
- Task/phase creation required
- Metadata tracking
- Integration with git auto-commit

### **Git Auto-Commit (Step 9):**
- Task complete → Commit + Push
- Phase complete → Commit + Push + PR
- All repos scanned
- Auto-commit message

---

## 📊 Execution Flow

```
User Request
    ↓
Step 0: Prompt Generation (structured prompt)
    ↓
Step 1: Task Breakdown (phases + tasks)
    ↓
Step 2: Plan Mode Decision (complexity-based)
    ↓
Step 3: Context Check (token management)
    ↓
Step 4: Model Selection (Haiku/Sonnet/Opus)
    ↓
Step 5: Skill/Agent Selection (auto-choose)
    ↓
Step 6: Tool Optimization (token savings)
    ↓
Step 7: Auto Recommendations (real-time)
    ↓
Step 8: Progress Tracking (BLOCKING enforcement)
    ↓
Step 9: EXECUTION (with loaded standards) ✅
    ↓
Step 10: Git Auto-Commit (on completion)
    ↓
Step 11: Session Save (with ID)
    ↓
✅ Complete!
```

---

**STATUS:** 🟢 ACTIVE
**PRIORITY:** 🟡 NORMAL (Runs after Sync + Standards)
