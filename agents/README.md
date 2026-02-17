# Agents Moved to Claude Global Library

**Agents are no longer part of Claude Insight.**

Claude Insight is a **monitoring dashboard** for the Claude Memory System. Agents are autonomous assistants that have been moved to a separate project for better organization.

---

## 📦 Where to Find Agents

**New Location:** Claude Global Library
**Repository:** https://github.com/piyushmakhija28/claude-global-library

---

## 🤖 Available Agents

**Backend Development:**
- Spring Boot Microservices
- Android Backend Engineer
- Swift Backend Engineer

**Frontend/UI Development:**
- Angular Engineer
- UI/UX Designer
- Android UI Designer
- SwiftUI Designer

**DevOps & Quality:**
- DevOps Engineer
- QA Testing Agent

**SEO:**
- Dynamic SEO Agent
- Static SEO Agent

**Orchestration:**
- Orchestrator Agent

---

## 🚀 How to Use Agents

### Step 1: Download Claude Global Library

```bash
git clone https://github.com/piyushmakhija28/claude-global-library.git
```

### Step 2: Copy Agents You Need

```bash
# Copy an agent
cp -r claude-global-library/agents/devops-engineer ~/.claude/agents/
cp -r claude-global-library/agents/qa-testing-agent ~/.claude/agents/
```

### Step 3: Launch Agents via Task Tool

```python
Task(
    subagent_type="devops-engineer",
    prompt="Deploy my app to Kubernetes"
)
```

---

**Repository:** https://github.com/piyushmakhija28/claude-global-library
