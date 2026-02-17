# Documentation Standards Policy

**VERSION:** 2.0.0
**STATUS:** 🟢 ACTIVE ENFORCEMENT + AUTO-CHECK
**SCOPE:** All Git Projects

---

## 🚨 MANDATORY: Auto-Check & Create Comprehensive Documentation

**NEW POLICY (v2.0.0):**

**For EVERY git repository:**
1. ✅ **Check** for README.md and CLAUDE.md
2. ✅ **Check comprehensiveness** (minimum 50 lines, required sections)
3. ✅ **Auto-create** if missing
4. ✅ **Auto-update** if not comprehensive

**Automation Script:**
```bash
# Check all git repos
python ~/.claude/memory/scripts/comprehensive-docs-checker.py /path/to/project

# Auto-create missing files
python ~/.claude/memory/scripts/comprehensive-docs-checker.py /path/to/project --auto-create

# Auto-create + Auto-update non-comprehensive files
python ~/.claude/memory/scripts/comprehensive-docs-checker.py /path/to/project --auto-create --auto-update
```

**When to Run:**
- ✅ On new git repository creation
- ✅ When user requests documentation check
- ✅ When missing documentation detected
- ✅ Periodic checks (monthly)

---

## 🎯 Core Rule: Two Markdown Files Maximum (Per Level)

**CRITICAL: 2 .md files at TWO LEVELS:**

### Level 1: Project Root
```
projectname/
├── README.md           ✅ Complete overview (ALL backend + frontend repos)
└── CLAUDE.md           ✅ Project-level instructions
```

### Level 2: Each Git Repository
```
projectname/backend/service-name/    (HAS .git)
├── README.md           ✅ Service-specific comprehensive docs
└── CLAUDE.md           ✅ Service-specific instructions

projectname/frontend/app-name/       (HAS .git)
├── README.md           ✅ Frontend app-specific docs
└── CLAUDE.md           ✅ Frontend app-specific instructions
```

### Where NOT to put .md files:
```
❌ projectname/backend/README.md              (NO .git here - not a repo)
❌ projectname/frontend/README.md             (NO .git here - not a repo)
❌ projectname/backend/service/API.md         (Extra file - should be in README.md)
❌ projectname/backend/service/STATUS.md      (Extra file - should be in README.md)
```

**❌ FORBIDDEN:**
- Multiple documentation files (API.md, Setup.md, Architecture.md, etc.)
- Status/report files (FINAL-STATUS.md, PROGRESS-REPORT.md, etc.)
- Migration guides as separate files
- Performance docs as separate files
- .md files in non-git folders (backend/, frontend/ folders)

---

## 📋 README.md Structure (MANDATORY)

### Level 1: Project Root README.md

**Project-level README.md = Overview of entire project**

```markdown
# Project Name

Brief project description

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Backend Services](#backend-services)
4. [Frontend Applications](#frontend-applications)
5. [Architecture](#architecture)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Development Guidelines](#development-guidelines)

---

## Overview

Complete project overview...

---

## Backend Services

| Service | Port | Purpose | Repo |
|---------|------|---------|------|
| product-service | 8087 | Product catalog | [Link](backend/product-service) |
| cart-service | 8093 | Shopping cart | [Link](backend/cart-service) |
...

---

## Frontend Applications

| App | Purpose | Repo |
|-----|---------|------|
| surgricalswale-ui | User interface | [Link](frontend/surgricalswale-ui) |
...

[Continue with project-level sections...]
```

### Level 2: Service/App-specific README.md

**Service-level README.md = Specific to that service/app**

```markdown
# Service Name

Brief service description

## Table of Contents

1. [Overview](#overview)
2. [API Documentation](#api-documentation)
3. [Setup Guide](#setup-guide)
4. [Configuration](#configuration)
5. [Database Schema](#database-schema)
6. [Testing](#testing)
7. [Deployment](#deployment)

---

## Overview

Service-specific overview...

---

## API Documentation

Service-specific API docs...

[Continue with service-specific sections...]
```

### Indexing Requirements:

**✅ MUST HAVE:**
1. **Table of Contents** - Clickable anchor links to all sections
2. **Section headers** - Proper hierarchy (##, ###, ####)
3. **Horizontal separators** - `---` between major sections
4. **Anchor links** - All ToC items must link to sections
5. **Subsection indexing** - For complex sections, add sub-ToC

**✅ BEST PRACTICES:**
- Use emoji icons for visual clarity (📋, 🔧, 🚀, etc.)
- Keep ToC at the top (after title and brief description)
- Use consistent naming (verb-noun format)
- Add "Back to Top" links for long documents
- Include status badges (✅, ❌, 🟡, etc.)

---

## 📏 Comprehensiveness Requirements (AUTO-CHECKED)

**BOTH README.md and CLAUDE.md MUST be comprehensive:**

### Minimum Requirements for README.md:

**✅ MUST HAVE (or file is marked non-comprehensive):**
1. **Minimum 50 lines** of actual content
2. **Title** (`# Project/Service Name`)
3. **Table of Contents** (with clickable links)
4. **Architecture** section (tech stack, dependencies)
5. **Getting Started** section (prerequisites, installation, running)
6. **Multiple sections** (at least 5 major sections with `##`)

**⚠️ If ANY is missing → Marked as "Not comprehensive"**

### Minimum Requirements for CLAUDE.md:

**✅ MUST HAVE (or file is marked non-comprehensive):**
1. **Minimum 50 lines** of actual content
2. **Title** (`# [Name] - Claude Code Instructions`)
3. **PROJECT OVERVIEW** section
4. **PROJECT STRUCTURE** section (directory layout)
5. **PROJECT-SPECIFIC** rules/conventions section
6. **Multiple sections** (at least 5 major sections with `##`)

**⚠️ If ANY is missing → Marked as "Not comprehensive"**

### Auto-Checker Behavior:

**On detection of non-comprehensive file:**
1. 🔍 **Check** - Identify missing sections/requirements
2. 📄 **Report** - Show what's missing
3. 🛠️ **Auto-fix** (if `--auto-update` flag used):
   - Backup original file (`.backup` extension)
   - Generate comprehensive version
   - Include all required sections
   - Preserve any custom content

**Example:**
```bash
# Check only (no changes)
python comprehensive-docs-checker.py /path/to/project

# Auto-create missing files
python comprehensive-docs-checker.py /path/to/project --auto-create

# Auto-create + Auto-update non-comprehensive files
python comprehensive-docs-checker.py /path/to/project --auto-create --auto-update
```

---

## 📝 CLAUDE.md Structure (MANDATORY)

**CLAUDE.md is for PROJECT-SPECIFIC instructions ONLY:**

```markdown
# Project: [Project Name]

## Project Information

- **Name:** [Project Name]
- **Path:** [Absolute Path]
- **Tech Stack:** [Technologies]
- **Purpose:** [Brief Purpose]

## Project-Specific Rules

1. [Custom coding conventions for this project]
2. [Project-specific build/deploy scripts]
3. [Team preferences for this project]
4. [Project-specific constants/configuration]

## File Structure

```
[Project structure tree]
```

## Custom Scripts

[Project-specific automation scripts]

## Notes

[Additional project-specific notes]
```

**❌ CLAUDE.md MUST NOT:**
- Override global policies (from ~/.claude/CLAUDE.md)
- Duplicate README.md content
- Contain general documentation
- Include API documentation
- Have setup guides (those go in README.md)

---

## 🚨 Enforcement Rules

### When Creating New Documentation:

**BEFORE creating ANY new .md file:**

```bash
# Check if content belongs in README.md
❓ Is this API documentation? → Add to README.md
❓ Is this setup guide? → Add to README.md
❓ Is this architecture info? → Add to README.md
❓ Is this status report? → Add to README.md
❓ Is this migration guide? → Add to README.md

# Only create new file if:
✅ It's project-specific CLAUDE.md instructions
```

### When Updating Documentation:

**ALWAYS update README.md with indexing:**

1. Add new section to Table of Contents
2. Add section header with anchor
3. Add content under proper section
4. Add horizontal separator
5. Test anchor links

### Consolidation Process:

**When finding multiple .md files:**

```bash
# 1. Create comprehensive README.md with ToC
# 2. Move all content from other .md files into README.md sections
# 3. Delete all other .md files (except CLAUDE.md)
# 4. Update README.md ToC with all sections
# 5. Test all anchor links
```

---

## 📊 Examples

### ❌ BAD (Multiple Files):

**Project Structure:**
```
projectname/
├── backend/
│   ├── README.md                      # ❌ No .git here!
│   └── product-service/
│       ├── .git                       # ✅ Git repo
│       ├── README.md                  # Minimal
│       ├── API-DOCUMENTATION.md       # ❌ Should be in README
│       ├── ARCHITECTURE.md            # ❌ Should be in README
│       ├── SETUP-GUIDE.md             # ❌ Should be in README
│       ├── FINAL-STATUS.md            # ❌ Should be in README
│       └── CLAUDE.md
```

### ✅ GOOD (Consolidated):

**Project Structure:**
```
projectname/
├── README.md                          # ✅ Project overview
├── CLAUDE.md                          # ✅ Project instructions
├── backend/
│   └── product-service/               # ✅ Git repo
│       ├── .git
│       ├── README.md                  # ✅ Service-specific comprehensive
│       │   ├── Overview
│       │   ├── API Documentation
│       │   ├── Setup Guide
│       │   ├── Configuration
│       │   ├── Database Schema
│       │   ├── Testing
│       │   └── Deployment
│       └── CLAUDE.md                  # ✅ Service-specific instructions
└── frontend/
    └── app-name/                      # ✅ Git repo
        ├── .git
        ├── README.md                  # ✅ App-specific comprehensive
        └── CLAUDE.md                  # ✅ App-specific instructions
```

---

## 🔧 Automated Consolidation Script

**Script:** `~/.claude/memory/scripts/consolidate-md-files.sh`

**Usage:**
```bash
# Consolidate all .md files in a project
bash ~/.claude/memory/scripts/consolidate-md-files.sh /path/to/project

# What it does:
# 1. Scans for all .md files (except README.md, CLAUDE.md)
# 2. Creates comprehensive README.md with ToC
# 3. Moves content from each file into appropriate section
# 4. Generates anchor links
# 5. Deletes consolidated files
# 6. Validates README.md structure
```

---

## 📋 Standards Integration

**This policy is loaded automatically with coding standards:**

```python
# standards-loader.py automatically loads:
✅ Java Project Structure
✅ Config Server Rules
✅ Secret Management
✅ Response Format (ApiResponseDto)
✅ API Design Standards
✅ Database Standards
✅ Error Handling
✅ Documentation Standards  ← THIS POLICY
```

---

## 🎯 Migration Checklist

**For each project with multiple .md files:**

- [ ] Create backup of all .md files
- [ ] Create comprehensive README.md structure
- [ ] Add Table of Contents with anchors
- [ ] Move content from each .md file to appropriate section
- [ ] Update CLAUDE.md (project-specific only)
- [ ] Delete all extra .md files
- [ ] Test all anchor links
- [ ] Commit changes with message: "docs: consolidate .md files into README.md"
- [ ] Verify only 2 .md files remain

---

## 🚨 Exception Handling

**The ONLY exception to 2-file rule:**

**✅ ALLOWED (but discouraged):**
- Root-level LICENSE.md
- Root-level CONTRIBUTING.md (for open-source projects)
- Root-level CODE_OF_CONDUCT.md (for open-source projects)

**❌ NOT ALLOWED:**
- Service-level additional .md files
- Documentation split across multiple files
- Status/progress reports as separate files
- Migration guides as separate files

---

## 📊 Monitoring

**Auto-detection script:** `~/.claude/memory/scripts/detect-md-violations.sh`

**Runs on:**
- Session start (daemon)
- Before git commit (hook)
- Manual invocation

**Reports:**
- Projects with >2 .md files
- Missing Table of Contents
- Broken anchor links
- Recommended consolidation actions

---

## 📖 References

**Related Policies:**
- `java-project-structure.md` - Package structure standards
- `api-design-standards.md` - API documentation format
- `git-and-context.md` - Git workflow with documentation

**Templates:**
- `~/.claude/memory/templates/README-comprehensive.md`
- `~/.claude/memory/templates/CLAUDE-project-specific.md`

---

## ✅ Summary

**Golden Rule:**
> **2 .md files at 2 LEVELS:**
> **Level 1 (Project Root):** README.md + CLAUDE.md (project overview)
> **Level 2 (Each Git Repo):** README.md + CLAUDE.md (repo-specific)

**Structure:**
```
projectname/
├── README.md               ✅ Level 1 (project overview)
├── CLAUDE.md               ✅ Level 1 (project instructions)
├── backend/                ❌ NO .md files (not a git repo)
│   ├── service1/           ✅ Level 2 (has .git)
│   │   ├── README.md       ✅ Service-specific
│   │   └── CLAUDE.md       ✅ Service-specific
│   └── service2/           ✅ Level 2 (has .git)
│       ├── README.md       ✅ Service-specific
│       └── CLAUDE.md       ✅ Service-specific
└── frontend/               ❌ NO .md files (not a git repo)
    └── app/                ✅ Level 2 (has .git)
        ├── README.md       ✅ App-specific
        └── CLAUDE.md       ✅ App-specific
```

**I MUST:**
- ✅ 2 .md files at project root (overview of all repos)
- ✅ 2 .md files per git repository (repo-specific)
- ✅ Consolidate all documentation into README.md at appropriate level
- ✅ Add proper Table of Contents with anchors
- ✅ Delete extra .md files after consolidation
- ❌ NEVER create .md files in non-git folders (backend/, frontend/)
- ❌ NEVER create multiple .md files in same folder
- ❌ NEVER split documentation across files

---

**VERSION:** 1.0.0
**CREATED:** 2026-02-17
**AUTHOR:** Claude Memory System
**STATUS:** 🟢 ACTIVE ENFORCEMENT
