---
name: model-selection-core
description: Defines rules for selecting the appropriate Claude model (Haiku/Sonnet/Opus) based on task type, complexity, and intent. Ensures efficient token usage and correct reasoning depth.
allowed-tools: Read,Glob,Grep,Bash,Edit,Write,Task,AskUserQuestion
user-invocable: true
---

# Model Selection Skill Instructions (Claude Model Strategy)

### Skill Name
model-selection-core

### Description
This skill defines strict rules for selecting the appropriate Claude model based on task type, complexity, risk, and intent. It ensures efficient token usage, correct reasoning depth, and prevents misuse of heavy models for simple tasks.

This skill works alongside context-management-core and must be applied before execution begins.

---

## Available Models

- Haiku
- Sonnet (4.5)
- Opus

Each model has a specific role and must not be used outside its intended scope.

---

## Absolute Rule

### 0. Right Model Before Execution
- No task should begin without selecting the correct model
- Wrong model selection is considered a context failure
- If model choice is unclear, default to clarification, not execution

---

## Model Responsibilities

### 1. Haiku — Fast, Lightweight, Exploratory

**Primary Purpose**
- Information discovery
- Navigation
- Clarification
- Lightweight reasoning

**Use Haiku When**
- Searching files or folders
- Understanding project structure
- Quick summaries
- Yes/No or factual checks
- Clarifying missing context
- Narrowing down scope

**Do Not Use Haiku For**
- Architecture decisions
- Feature design
- Complex debugging
- Long-term planning

---

### 2. Sonnet (4.5) — Implementation & Engineering

**Primary Purpose**
- Writing production code
- Bug fixing
- Refactoring
- Applying existing skills and rules

**Use Sonnet When**
- Implementing features
- Fixing bugs with known context
- Writing backend, frontend, mobile, or DevOps code
- Applying SKILL.md instructions
- Making local engineering decisions

**Do Not Use Sonnet For**
- Ambiguous problem spaces
- High-risk architectural decisions
- Deep research or strategy

---

### 3. Opus — Deep Reasoning & Architecture

**Primary Purpose**
- High-level thinking
- Complex reasoning
- System design
- Long-term decision making

**Use Opus When**
- Planning architecture
- Resolving ambiguous requirements
- Context-heavy decision making
- Writing or modifying core system skills
- Evaluating trade-offs
- Designing workflows or agents

**Do Not Use Opus For**
- Simple searches
- File navigation
- Basic implementations
- Mechanical tasks

---

## Task-to-Model Mapping

### 4. Task Classification Mapping

| Task Type                          | Model  |
|-----------------------------------|--------|
| Context clarification             | Opus   |
| Feature vs bug decision           | Opus   |
| File search / navigation           | Haiku  |
| Folder tree understanding          | Haiku  |
| Code implementation                | Sonnet |
| Bug fix (clear scope)              | Sonnet |
| Refactor                           | Sonnet |
| Architecture / system planning     | Opus   |
| Workflow design                    | Opus   |
| Skill definition / modification    | Opus   |

---

## Multi-Stage Workflow Strategy

### 5. Progressive Model Usage (Best Practice)

Use models in sequence when needed:

1. **Haiku**
   - Gather information
   - Locate files
   - Reduce uncertainty

2. **Sonnet**
   - Implement changes
   - Write or modify code

3. **Opus**
   - Validate decisions
   - Assess long-term impact
   - Resolve ambiguity

Never skip stages when uncertainty exists.

---

## Token Efficiency Rules

### 6. Token Discipline
- Prefer the smallest capable model
- Escalate models only when required
- Do not use Opus for mechanical tasks
- Do not loop between models unnecessarily

---

## Failure Handling

### 7. If Output Quality Is Low
- Re-evaluate model choice
- Do not retry blindly with same model
- Escalate or downgrade model intentionally

---

## Integration with Context Management

### 8. Skill Dependency
- This skill depends on `context-management-core`
- If context is unclear, model selection must pause
- Context clarity takes priority over execution

---

## What Not to Do

- Do not default everything to Opus
- Do not write code with Haiku
- Do not plan architecture with Sonnet
- Do not guess model suitability
- Do not waste tokens on wrong model

---

## Output Expectations

- Correct model selection
- Efficient token usage
- Appropriate reasoning depth
- Reduced retries
- Predictable and high-quality results

---

## Skill Priority

This skill has **system-level priority**.
It must be applied before implementation-oriented skills.

---

## Skill Scope

In scope:
- Model responsibility definition
- Task-to-model mapping
- Token optimization
- Execution strategy

Out of scope:
- Code generation
- UI or backend logic
- Business rules
- Prompt writing

---

## Version
1.0.0
