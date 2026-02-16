# Adaptive Skill Intelligence Registry

This file tracks all skills and agents created by the `adaptive-skill-intelligence` system.

## Purpose
- Track auto-created resources (skills and agents)
- Monitor lifecycle (TEMPORARY vs PERMANENT)
- Log cleanup operations
- Prevent duplicate creation
- Maintain system health

---

## Protected Resources (NEVER DELETE)

### Pre-Existing Skills (Created before 2026-01-23)
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
- adaptive-skill-intelligence (this skill itself)

### Pre-Existing Agents (Created before 2026-01-23)
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

---

## Auto-Created Skills

| Skill Name | Created Date | Type | Status | Last Used | Description |
|------------|--------------|------|--------|-----------|-------------|
| (none yet) | - | - | - | - | - |

---

## Auto-Created Agents

| Agent Name | Created Date | Type | Status | Last Used | Description |
|------------|--------------|------|--------|-----------|-------------|
| (none yet) | - | - | - | - | - |

---

## Cleanup Log

| Resource Type | Resource Name | Deleted Date | Reason |
|---------------|---------------|--------------|--------|
| (none yet) | - | - | - |

---

## Statistics

- **Total Skills Created**: 0
- **Total Agents Created**: 0
- **Permanent Skills**: 0
- **Permanent Agents**: 0
- **Temporary Resources Cleaned**: 0
- **Last Cleanup**: Never

---

## Update Instructions

### When Creating New Resource:
```markdown
Add to "Auto-Created Skills" or "Auto-Created Agents" table:
| resource-name | YYYY-MM-DD | TEMPORARY/PERMANENT | ACTIVE | YYYY-MM-DD | description |
```

### When Deleting TEMPORARY Resource:
```markdown
Add to "Cleanup Log" table:
| Skill/Agent | resource-name | YYYY-MM-DD | reason-for-deletion |

Update "Statistics" section.
```

### When Using Existing Resource:
```markdown
Update "Last Used" column in respective table.
```

---

**Last Updated**: 2026-01-23
**Version**: 1.0.0
