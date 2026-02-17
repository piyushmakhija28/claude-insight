# Skills Moved to Claude Global Library

**Skills and agents are no longer part of Claude Insight.**

Claude Insight is a **monitoring dashboard** for the Claude Memory System. Skills and agents are optional development tools that have been moved to a separate project for better organization.

---

## 📦 Where to Find Skills & Agents

**New Location:** Claude Global Library
**Repository:** https://github.com/piyushmakhija28/claude-global-library

---

## 🚀 How to Use Skills & Agents

### Step 1: Download Claude Global Library

```bash
git clone https://github.com/piyushmakhija28/claude-global-library.git
```

### Step 2: Copy Skills/Agents You Need

```bash
# Copy a skill
cp -r claude-global-library/skills/docker ~/.claude/skills/

# Copy an agent
cp -r claude-global-library/agents/devops-engineer ~/.claude/agents/
```

### Step 3: Use in Your Claude Projects

Skills and agents are now available in your `~/.claude/skills/` and `~/.claude/agents/` directories.

---

## 📚 Available Skills & Agents

### Skills (27 total)
- Docker, Kubernetes, Jenkins
- Java Spring Boot, Design Patterns
- RDBMS, NoSQL
- CSS, Animations
- SEO, Optimization
- And more...

### Agents (12 total)
- DevOps Engineer
- QA Testing Agent
- Spring Boot Microservices
- UI/UX Designer
- And more...

---

## 🎯 Why the Separation?

**Claude Insight** = Monitoring Dashboard
- Focus: System health, costs, analytics
- Users: Everyone who wants monitoring

**Claude Global Library** = Skills & Agents
- Focus: Development tools and patterns
- Users: Only those who need specific skills/agents

**Benefits:**
- ✅ Clear purpose for each project
- ✅ Download only what you need
- ✅ No context overload
- ✅ Better organization

---

**For monitoring:** Use Claude Insight (this project)
**For skills/agents:** Download Claude Global Library separately

**Repository:** https://github.com/piyushmakhija28/claude-global-library
