---
name: adaptive-skill-intelligence
description: Automatically detects when a task requires a skill or agent that doesn't exist, creates them on-the-fly, uses them during execution, and manages their lifecycle (temporary vs permanent). Prevents user from worrying about which skill/agent to use.
allowed-tools: Read,Glob,Grep,Bash,Edit,Write,Task,AskUserQuestion,TaskCreate,TaskUpdate
user-invocable: false
priority: SYSTEM-LEVEL
status: ALWAYS ACTIVE
version: 1.0.0
---

# Adaptive Skill Intelligence (Auto Skill/Agent Factory)

## Metadata
- **Skill Name**: adaptive-skill-intelligence
- **Version**: 1.0.0
- **Category**: System / Intelligence / Meta-Management
- **Priority**: SYSTEM-LEVEL (Applied DURING task analysis)
- **Status**: ALWAYS ACTIVE
- **Auto-invocation**: YES (automatic, no manual trigger needed)

---

## Purpose

This skill **intelligently manages skills and agents** by:
- ✅ Detecting when existing skills/agents can handle a task
- ✅ Identifying gaps in skill/agent coverage
- ✅ Auto-creating missing skills/agents on-the-fly
- ✅ Using created skills/agents during task execution
- ✅ Managing lifecycle: temporary vs permanent
- ✅ Cleaning up temporary skills/agents after task completion
- ✅ **NEVER** deleting pre-existing skills/agents

**Key Benefit**: User tension-free! They don't need to know which skill/agent exists or how to use it.

---

## Core Principle

**Skills and Agents Should Be Invisible to Users**:
- User describes the task → System finds/creates the right skill/agent → Task gets done
- No "which skill should I use?" questions
- No "this agent doesn't exist" errors
- Automatic skill/agent creation when needed
- Automatic cleanup of temporary resources

**Formula**:
```
Task Received
    ↓
Analyze task requirements
    ↓
Check existing skills/agents (MANDATORY - NO DUPLICATES!)
    ↓
Match found? → Use existing
    ↓
No match? → Create new (temporary or permanent)
    ↓
Use skill/agent to complete task
    ↓
Task complete → Delete temporary, Keep permanent
    ↓
Update memory registry
```

---

## When This Skill Activates

### Trigger Points

**1. Every Task (ALWAYS)**
- Triggers after context-management-core validates context
- Triggers after model-selection-core selects model
- Triggers BEFORE task-planning-intelligence
- Analyzes task to determine required skills/agents

**2. During Execution (CONDITIONAL)**
- Mid-task, new requirement emerges
- Current skill/agent insufficient
- Need specialized agent for specific subtask

**3. Skill/Agent Gap Detected**
- Task type not covered by existing skills/agents
- Specialized domain not yet handled
- New technology/framework encountered

---

## Existing Skills/Agents Discovery (MANDATORY FIRST STEP)

### Before Creating Anything, ALWAYS Check:

```bash
# 1. List all existing skills
ls -la C:\Users\techd\.claude\skills\

Current existing skills (as of 2026-01-23):
- animations-core (Frontend animations)
- context-management-core (Context handling)
- css-core (CSS management)
- docker (Docker containerization)
- java-design-patterns-core (Java patterns)
- java-spring-boot-microservices (Spring Boot microservices)
- jenkins-pipeline (CI/CD Jenkins)
- kubernetes (K8s orchestration)
- model-selection-core (Model selection)
- nosql-core (NoSQL databases)
- phased-execution-intelligence (Phase management)
- rdbms-core (RDBMS databases)
- seo-keyword-research-core (SEO keywords)
- spring-boot-design-patterns-core (Spring Boot patterns)
- task-planning-intelligence (Planning decisions)

# 2. List all existing agents
ls -la C:\Users\techd\.claude\agents\

Current existing agents (as of 2026-01-23):
- android-backend-engineer (Android backend logic)
- android-ui-designer (Android XML UI)
- angular-engineer (Angular applications)
- devops-engineer (CI/CD, deployment)
- dynamic-seo-agent (Dynamic SEO for SPAs)
- orchestrator-agent (Multi-agent coordination)
- qa-testing-agent (QA and testing)
- spring-boot-microservices (Spring Boot backend)
- static-seo-agent (Static website SEO)
- swift-backend-engineer (Swift backend)
- swiftui-designer (SwiftUI design)
- ui-ux-designer (UI/UX design)
```

### ⚠️ CRITICAL RULES:
1. **ALWAYS** check existing skills/agents BEFORE creating new ones
2. **NEVER** create duplicates
3. **NEVER** delete pre-existing skills/agents (created before this session)
4. **ONLY** create if genuinely needed and no existing match
5. **PREFER** using existing over creating new

---

## Task-to-Skill/Agent Mapping Strategy

### Step 1: Analyze Task Type

**Categories:**
- Frontend (React, Angular, HTML/CSS, UI/UX)
- Backend (Java, Spring Boot, Node.js, APIs, databases)
- Mobile (Android, iOS, SwiftUI)
- DevOps (Docker, K8s, Jenkins, deployment)
- Testing (QA, unit tests, integration tests)
- Design (UI/UX, animations, SEO)
- Database (SQL, NoSQL, schema design)
- Architecture (Microservices, patterns, design)

### Step 2: Match Against Existing Resources

**Matching Logic:**
```python
def find_skill_or_agent(task):
    # Extract task keywords
    keywords = extract_keywords(task)
    domain = identify_domain(task)

    # Search existing skills
    existing_skills = scan_skills_directory()
    for skill in existing_skills:
        if skill.covers(keywords, domain):
            return skill  # ✅ Use existing

    # Search existing agents
    existing_agents = scan_agents_directory()
    for agent in existing_agents:
        if agent.handles(keywords, domain):
            return agent  # ✅ Use existing

    # No match found
    return None  # ⚠️ Create new
```

### Step 3: Create New (Only If No Match)

**Decision Tree:**
```
No existing match?
    ↓
Is this a one-time specialized task? → Create TEMPORARY skill/agent
    ↓
Is this a recurring domain/technology? → Create PERMANENT skill/agent
    ↓
Is this a complex workflow? → Create AGENT
    ↓
Is this a reusable pattern? → Create SKILL
```

---

## Creation Strategy

### When to Create a SKILL vs AGENT

**Create a SKILL when:**
- Task involves reusable patterns/rules
- Applies to many tasks (e.g., error handling, logging)
- Provides guidelines/best practices
- Enhances existing capabilities (e.g., optimization)
- Cross-domain applicability
- Examples: caching-strategy, error-handling-core, logging-best-practices

**Create an AGENT when:**
- Task requires specialized domain expertise
- Involves multi-step execution workflow
- Needs dedicated tools/context
- Specific technology stack (e.g., Vue.js, Flutter)
- Complex implementation logic
- Examples: vue-engineer, flutter-ui-designer, python-backend-engineer

### Temporary vs Permanent Decision

**Create TEMPORARY (delete after task):**
- Very niche, one-time use case
- Highly specific to current project only
- No reusability beyond this task
- Experimental/exploratory
- Examples: "parse-legacy-xml-format", "migrate-old-db-schema"

**Create PERMANENT (keep forever):**
- General-purpose technology/framework
- Likely to be used in future projects
- Common industry tool/pattern
- Fills important gap in coverage
- Examples: "nextjs-engineer", "graphql-api-designer", "redis-caching-strategy"

### Naming Convention

**Skills:**
- Format: `{domain}-{purpose}-{type}`
- Examples:
  - `frontend-performance-optimization`
  - `backend-api-security-core`
  - `database-migration-strategy`

**Agents:**
- Format: `{technology}-{role}`
- Examples:
  - `nextjs-engineer`
  - `flutter-ui-designer`
  - `python-backend-engineer`

---

## Auto-Creation Workflow

### Creating a New Skill

```bash
# 1. Create directory
mkdir -p C:\Users\techd\.claude\skills\{skill-name}\

# 2. Create skill.md file
cat > C:\Users\techd\.claude\skills\{skill-name}\skill.md << 'EOF'
---
name: {skill-name}
description: {clear description}
allowed-tools: Read,Glob,Grep,Bash,Edit,Write,Task
user-invocable: true/false
priority: NORMAL/SYSTEM-LEVEL
status: ACTIVE/TEMPORARY
version: 1.0.0
created-by: adaptive-skill-intelligence
created-at: {timestamp}
lifecycle: TEMPORARY/PERMANENT
---

# {Skill Name}

## Purpose
{What problem does this solve}

## When to Use
{Trigger conditions}

## How It Works
{Implementation details}

## Examples
{Usage examples}

## Status
- Version: 1.0.0
- Created: {timestamp}
- Type: {TEMPORARY/PERMANENT}
EOF

# 3. Mark as TEMPORARY or PERMANENT in metadata
echo "lifecycle: {TEMPORARY/PERMANENT}" >> metadata
```

### Creating a New Agent

```bash
# 1. Create directory
mkdir -p C:\Users\techd\.claude\agents\{agent-name}\

# 2. Create agent.md file
cat > C:\Users\techd\.claude\agents\{agent-name}\{agent-name}.md << 'EOF'
---
name: {agent-name}
description: {clear description}
tools: Read, Glob, Grep, Bash, Edit, Write, WebFetch, WebSearch
model: sonnet
created-by: adaptive-skill-intelligence
created-at: {timestamp}
lifecycle: TEMPORARY/PERMANENT
---

# {Agent Name}

## Role
{What this agent does}

## Responsibilities
{What it handles}

## Tools
{Available tools}

## When to Use
{Use cases}

## Version
1.0.0 (Created: {timestamp}, Type: {TEMPORARY/PERMANENT})
EOF
```

---

## Lifecycle Management

### Tracking Created Skills/Agents

**Registry File**: `C:\Users\techd\.claude\memory\adaptive-skill-registry.md`

```markdown
# Adaptive Skill Intelligence Registry

## Auto-Created Skills

| Skill Name | Created | Type | Status | Last Used |
|------------|---------|------|--------|-----------|
| example-skill | 2026-01-23 | PERMANENT | ACTIVE | 2026-01-23 |

## Auto-Created Agents

| Agent Name | Created | Type | Status | Last Used |
|------------|---------|------|--------|-----------|
| example-agent | 2026-01-23 | TEMPORARY | ACTIVE | 2026-01-23 |

## Cleanup Log

| Resource | Deleted | Reason |
|----------|---------|--------|
| temp-parser | 2026-01-23 | Task completed, one-time use |
```

### Cleanup Process (TEMPORARY Only)

**When to Delete:**
- Task is completed
- Resource marked as TEMPORARY
- Not used in last session
- No future utility

**Cleanup Steps:**
```bash
# 1. Verify it's TEMPORARY (NEVER delete PERMANENT or pre-existing)
grep "lifecycle: TEMPORARY" skill.md || agent.md

# 2. Check creation timestamp (only delete self-created)
grep "created-by: adaptive-skill-intelligence" skill.md || agent.md

# 3. Delete directory
rm -rf C:\Users\techd\.claude\skills\{temp-skill}
rm -rf C:\Users\techd\.claude\agents\{temp-agent}

# 4. Log cleanup
echo "Deleted {resource} - Reason: Task complete, TEMPORARY" >> registry
```

### ⚠️ NEVER DELETE:
- Pre-existing skills/agents (created before 2026-01-23 or without "created-by: adaptive-skill-intelligence")
- Skills/agents marked as PERMANENT
- Skills/agents used in last 7 days
- Core system skills (context-management, model-selection, etc.)

---

## Integration with Existing Skills

### Execution Flow (Updated)

```
User Request
    ↓
1. context-management-core (FIRST)
   ↓ Validate context, classify task
   ↓
2. model-selection-core (SECOND)
   ↓ Select appropriate model
   ↓
3. adaptive-skill-intelligence (THIRD) ← NEW!
   ↓ Check existing skills/agents
   ↓ Create new if needed (temporary or permanent)
   ↓ Select best skill/agent for task
   ↓
4. task-planning-intelligence (FOURTH)
   ↓ Calculate complexity score
   ↓ Decide: Direct vs Planning vs Ask
   ↓
5. phased-execution-intelligence (FIFTH)
   ↓ Calculate task size score
   ↓ Decide: Single vs Multi-phase
   ↓
6. Implementation (SIXTH)
   ↓ Use selected/created skill/agent
   ↓ Complete task
   ↓
7. Cleanup (SEVENTH)
   ↓ Delete TEMPORARY skills/agents
   ↓ Update registry
```

### Priority Hierarchy (Updated)

1. **HIGHEST**: Context validation (context-management-core)
2. **SYSTEM-LEVEL**: Model selection (model-selection-core)
3. **SYSTEM-LEVEL**: Skill/Agent Intelligence (adaptive-skill-intelligence) ← NEW
4. **SYSTEM-LEVEL**: Planning intelligence (task-planning-intelligence)
5. **SYSTEM-LEVEL**: Phase intelligence (phased-execution-intelligence)
6. **NORMAL**: Implementation skills/agents

---

## Decision Examples

### Example 1: Existing Skill Matches

```
User: "Optimize database queries in PostgreSQL"

Analysis:
- Domain: Backend, Database
- Check existing: rdbms-core skill exists ✅
- Action: Use existing rdbms-core skill
- Create new: NO
```

### Example 2: Existing Agent Matches

```
User: "Design a new login screen in Android XML"

Analysis:
- Domain: Mobile, Android, UI
- Check existing: android-ui-designer agent exists ✅
- Action: Use existing android-ui-designer agent
- Create new: NO
```

### Example 3: Create New PERMANENT Agent

```
User: "Build a Next.js application with server-side rendering"

Analysis:
- Domain: Frontend, Next.js
- Check existing: No Next.js specialist ❌
- Technology: Next.js (popular, future use likely)
- Decision: Create PERMANENT agent "nextjs-engineer"
- Action:
  1. Create nextjs-engineer agent
  2. Mark as PERMANENT
  3. Use for current task
  4. Keep for future
```

### Example 4: Create New TEMPORARY Skill

```
User: "Parse this legacy XML format specific to old system"

Analysis:
- Domain: Data parsing
- Check existing: No XML legacy parser ❌
- Use case: One-time migration
- Reusability: Low (very specific format)
- Decision: Create TEMPORARY skill "legacy-xml-parser"
- Action:
  1. Create legacy-xml-parser skill
  2. Mark as TEMPORARY
  3. Use for current task
  4. Delete after task complete
```

### Example 5: Multiple Agents Coordinated

```
User: "Build full-stack app: Spring Boot backend + Angular frontend"

Analysis:
- Domain: Multi-domain (Backend + Frontend)
- Check existing:
  - spring-boot-microservices agent exists ✅
  - angular-engineer agent exists ✅
  - orchestrator-agent exists ✅
- Action: Use orchestrator-agent to coordinate existing agents
- Create new: NO
```

---

## User Communication Templates

### Template 1: Using Existing Resource
```
"I'll use the existing {skill/agent name} to handle this task."
[Proceed with task]
```

### Template 2: Creating PERMANENT Resource
```
"This requires {technology/domain} expertise. Creating a permanent
{skill/agent name} for this and future tasks."
[Create + Use + Keep]
```

### Template 3: Creating TEMPORARY Resource
```
"This is a specialized one-time task. Creating a temporary
{skill/agent name} for this specific need."
[Create + Use + Will delete after completion]
```

### Template 4: Cleanup Notification
```
"Task complete. Cleaning up temporary resources:
- Deleted: {temp-skill/agent-name} (no longer needed)
- Kept: {permanent-skill/agent-name} (for future use)"
```

---

## Memory Update Workflow

### Update core-skills-mandate.md

After creating PERMANENT skill/agent:

```bash
# Add to C:\Users\techd\.claude\memory\core-skills-mandate.md

## Available Skills (Updated)
...
- {new-skill-name}: {description}

## Available Agents (Updated)
...
- {new-agent-name}: {description}
```

### Update Registry

```bash
# Update C:\Users\techd\.claude\memory\adaptive-skill-registry.md

| {resource-name} | {date} | {TEMP/PERM} | ACTIVE | {date} |
```

---

## Anti-Patterns (What NOT to Do)

### ❌ WRONG: Create without checking existing
```
User: "Setup Docker container"
Action: Create new docker-setup skill
❌ WRONG! docker skill already exists!
```

### ❌ WRONG: Delete pre-existing skills/agents
```
Action: Clean up unused skills
→ Delete java-design-patterns-core
❌ WRONG! This is pre-existing, never delete!
```

### ❌ WRONG: Create duplicate
```
User: "Design UI in Angular"
Action: Create angular-ui-designer
❌ WRONG! angular-engineer already exists!
```

### ❌ WRONG: Mark common tech as TEMPORARY
```
User: "Build GraphQL API"
Action: Create graphql-api-designer as TEMPORARY
❌ WRONG! GraphQL is common, should be PERMANENT!
```

### ✅ CORRECT: Check first, create only if needed
```
User: "Setup Docker container"
Analysis:
- Check existing: docker skill found ✅
Action: Use existing docker skill
✅ CORRECT!
```

---

## Quick Decision Flowchart

```
                    User Task Received
                           ↓
              [Context & Model validated]
                           ↓
            ┌──────────────────────────────┐
            │  Extract Task Requirements   │
            │  (domain, tech, complexity)  │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │  Scan Existing Skills        │
            │  C:\Users\techd\.claude\skills\ │
            └──────────────────────────────┘
                           ↓
                    Match found?
              ┌────────────┴────────────┐
              ↓ YES                     ↓ NO
    ┌─────────────────┐      ┌──────────────────┐
    │ Use Existing    │      │ Scan Agents      │
    │ Skill           │      │ C:\...\agents\   │
    └─────────────────┘      └──────────────────┘
              ↓                         ↓
         Execute Task            Match found?
                           ┌────────────┴────────────┐
                           ↓ YES                     ↓ NO
                  ┌─────────────────┐    ┌──────────────────┐
                  │ Use Existing    │    │ Analyze Need     │
                  │ Agent           │    │ Skill vs Agent?  │
                  └─────────────────┘    └──────────────────┘
                           ↓                         ↓
                      Execute Task        ┌──────────┴──────────┐
                                          ↓ SKILL               ↓ AGENT
                                 ┌─────────────────┐  ┌─────────────────┐
                                 │ Temp or Perm?   │  │ Temp or Perm?   │
                                 └─────────────────┘  └─────────────────┘
                                          ↓                      ↓
                                 ┌─────────────────┐  ┌─────────────────┐
                                 │ Create Skill    │  │ Create Agent    │
                                 │ Mark lifecycle  │  │ Mark lifecycle  │
                                 └─────────────────┘  └─────────────────┘
                                          ↓                      ↓
                                 ┌─────────────────────────────────────┐
                                 │      Use Created Resource          │
                                 └─────────────────────────────────────┘
                                                    ↓
                                          Execute Task
                                                    ↓
                                          Task Complete
                                                    ↓
                                 ┌─────────────────────────────────────┐
                                 │  Cleanup TEMPORARY Resources       │
                                 │  Keep PERMANENT Resources          │
                                 │  Update Registry                   │
                                 └─────────────────────────────────────┘
```

---

## Pre-Existing Resources Protection

### Never Touch List (as of 2026-01-23)

**Skills (PROTECTED):**
- animations-core
- context-management-core
- css-core
- docker
- java-design-patterns-core
- java-spring-boot-microservices
- jenkins-pipeline
- kubernetes
- model-selection-core
- nosql-core
- phased-execution-intelligence
- rdbms-core
- seo-keyword-research-core
- spring-boot-design-patterns-core
- task-planning-intelligence

**Agents (PROTECTED):**
- android-backend-engineer
- android-ui-designer
- angular-engineer
- devops-engineer
- dynamic-seo-agent
- orchestrator-agent
- qa-testing-agent
- spring-boot-microservices
- static-seo-agent
- swift-backend-engineer
- swiftui-designer
- ui-ux-designer

### Verification Before Deletion

```python
def safe_to_delete(resource_path):
    # Read metadata
    metadata = read_metadata(resource_path)

    # Check 1: Is it TEMPORARY?
    if metadata.lifecycle != "TEMPORARY":
        return False  # PERMANENT or undefined = DO NOT DELETE

    # Check 2: Created by this system?
    if metadata.created_by != "adaptive-skill-intelligence":
        return False  # Pre-existing = DO NOT DELETE

    # Check 3: Recent activity?
    if metadata.last_used > 7_days_ago:
        return False  # Recently used = DO NOT DELETE

    return True  # Safe to delete
```

---

## Monitoring & Learning

### Track Patterns

Keep mental note of:
- **Creation frequency**: How often are new resources created?
- **Permanent vs Temporary ratio**: Are we creating too many permanent resources?
- **Reuse rate**: Are created resources being reused?
- **Gap patterns**: What domains need new skills/agents most?

### Continuous Improvement

If patterns emerge:
- **High creation rate** → Existing resources may need expansion
- **Low reuse of PERMANENT** → May need stricter permanent criteria
- **Repeated TEMPORARY for same domain** → Consider creating PERMANENT
- **Resource bloat** → Review and consolidate similar resources

---

## Status

**Version**: 1.0.0
**Status**: ACTIVE (Automatic enforcement)
**Created**: 2026-01-23
**Integration**: Works with all core skills (context, model-selection, planning, phased)

---

## Summary (TL;DR)

**What**: Automatically detects, creates, and manages skills/agents as needed
**How**: Check existing → Create if needed → Mark lifecycle → Use → Cleanup temporary
**When**: After context & model selection, before planning
**Why**: User stays tension-free, doesn't need to know which skill/agent to use

**Key Rules**:
- ALWAYS check existing first (NO DUPLICATES!)
- Create PERMANENT for common tech, TEMPORARY for one-time
- NEVER delete pre-existing resources
- Update registry for all changes
- Cleanup TEMPORARY after task completion

**Benefits**:
- Zero user mental overhead
- Automatic resource management
- No "skill not found" errors
- Clean system (no resource bloat)
- Smart lifecycle management

---

**Remember**: "Rehem kar le" on pre-existing skills/agents! 😄
