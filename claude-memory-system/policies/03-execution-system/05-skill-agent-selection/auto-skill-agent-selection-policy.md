# 🎯 Automatic Skill & Agent Selection Policy

**VERSION:** 2.0.0 (CONSOLIDATED)
**CREATED:** 2026-02-16
**PRIORITY:** 🔴 CRITICAL - STEP 7 (Before Execution)
**STATUS:** 🟢 ACTIVE

---

## 📋 POLICY OVERVIEW

**MANDATORY: After all preparation steps, auto-select skills/agents:**

1. ✅ **Analyze Context** - Task type, complexity, model selected
2. ✅ **Match Skills** - Find relevant skills from registry
3. ✅ **Match Agents** - Find relevant agents if needed
4. ✅ **Auto-Select** - Choose best match(es)
5. ✅ **Execute** - Invoke selected skills/agents

> **NOTE:** This policy **CONSOLIDATES** existing work:
> - `core-skills-mandate.md` - Core skills rules
> - `adaptive-skill-registry.md` - Available skills/agents
> - `SKILL-AGENT-SELECTION-FIX-REPORT.md` - Previous fixes
> - Various detector scripts
>
> **NO DUPLICATION** - References and organizes existing resources

---

## 🚨 EXECUTION ORDER

```
Step 0: Prompt Generation ✅
Step 1: Task Breakdown ✅
Step 2: Plan Mode Suggestion ✅
Step 3: Context Check ✅
Step 4: Model Selection ✅
Step 5: (Skill Detection - old position)
Step 6: Tool Optimization ✅
        ↓
🔴 STEP 7: AUTO SKILL & AGENT SELECTION (THIS POLICY)
        ↓
    All context available:
    • Task type (from Step 0)
    • Complexity (from Step 1)
    • Plan mode decision (from Step 2)
    • Selected model (from Step 4)
        ↓
    🔍 ANALYZE REQUIREMENTS:
    - What technologies? (Spring Boot, Docker, K8s, etc.)
    - What domain? (API, Auth, Database, DevOps, etc.)
    - Need agent? (Complex multi-step, or direct skill?)
        ↓
    📋 MATCH FROM REGISTRY:
    - Check existing skills (NO CREATE unless needed)
    - Check existing agents (NO CREATE unless needed)
    - Use adaptive-skill-registry.md
        ↓
    ✅ AUTO-SELECT:
    - Skills: Execute via /skill-name
    - Agents: Execute via Task(subagent_type=...)
        ↓
Step 8: Failure Prevention
Step 9: Execute (with skills/agents active)
```

---

## 📚 AVAILABLE RESOURCES (From Registry)

### **Pre-Existing Skills (From adaptive-skill-registry.md):**

```yaml
# Core System Skills (MANDATORY - Auto-applied):
- context-management-core      # ✅ Already applied in Step 3
- model-selection-core          # ✅ Already applied in Step 4
- adaptive-skill-intelligence   # ✅ This system

# Technology-Specific Skills:
- java-spring-boot-microservices  # Spring Boot projects
- spring-boot-design-patterns-core  # Design patterns
- java-design-patterns-core      # Java patterns
- docker                         # Docker/containerization
- kubernetes                     # K8s deployment
- jenkins-pipeline               # CI/CD
- rdbms-core                     # PostgreSQL/MySQL
- nosql-core                     # MongoDB/Elasticsearch
- animations-core                # UI animations
- css-core                       # CSS/styling
- seo-keyword-research-core      # SEO optimization
```

### **Pre-Existing Agents (From adaptive-skill-registry.md):**

```yaml
# Backend Engineers:
- spring-boot-microservices      # Java/Spring Boot
- swift-backend-engineer         # Swift backend
- android-backend-engineer       # Android backend

# Frontend Engineers:
- angular-engineer               # Angular apps
- android-ui-designer            # Android UI (XML)
- swiftui-designer               # SwiftUI
- ui-ux-designer                 # General UI/UX

# Specialized:
- devops-engineer                # CI/CD, deployment
- qa-testing-agent               # Testing & QA
- orchestrator-agent             # Multi-agent coordination
- dynamic-seo-agent              # Dynamic site SEO
- static-seo-agent               # Static site SEO
```

---

## 🎯 AUTO-SELECTION ALGORITHM

```python
def auto_select_skills_and_agents(
    task_type: str,
    complexity: Dict,
    model_selection: Dict,
    structured_prompt: Dict
) -> Dict:
    """
    Automatically select skills and agents based on context
    """

    selection = {
        'skills': [],
        'agents': [],
        'reasoning': []
    }

    # Extract context
    technologies = extract_technologies(structured_prompt)
    domain = extract_domain(task_type)
    complexity_score = complexity.get('score', 0)

    # RULE 1: Technology-based skill selection
    tech_skill_map = {
        'spring boot': 'java-spring-boot-microservices',
        'java': 'java-design-patterns-core',
        'docker': 'docker',
        'kubernetes': 'kubernetes',
        'k8s': 'kubernetes',
        'jenkins': 'jenkins-pipeline',
        'postgresql': 'rdbms-core',
        'mysql': 'rdbms-core',
        'mongodb': 'nosql-core',
        'angular': None,  # Use agent instead
        'android': None,  # Use agent instead
        'css': 'css-core',
        'seo': 'seo-keyword-research-core'
    }

    for tech, skill in tech_skill_map.items():
        if tech in technologies and skill:
            if skill not in selection['skills']:
                selection['skills'].append(skill)
                selection['reasoning'].append(f"Technology '{tech}' detected → {skill}")

    # RULE 2: Agent selection (for complex or specialized tasks)
    if complexity_score >= 10 or 'multi-step' in str(structured_prompt).lower():
        # Complex task - consider agent

        domain_agent_map = {
            'spring boot': 'spring-boot-microservices',
            'java microservice': 'spring-boot-microservices',
            'android ui': 'android-ui-designer',
            'android backend': 'android-backend-engineer',
            'angular': 'angular-engineer',
            'swiftui': 'swiftui-designer',
            'swift backend': 'swift-backend-engineer',
            'ui/ux': 'ui-ux-designer',
            'devops': 'devops-engineer',
            'ci/cd': 'devops-engineer',
            'deployment': 'devops-engineer',
            'testing': 'qa-testing-agent',
            'seo dynamic': 'dynamic-seo-agent',
            'seo static': 'static-seo-agent'
        }

        for domain_key, agent in domain_agent_map.items():
            if domain_key in technologies or domain_key in domain.lower():
                if agent not in selection['agents']:
                    selection['agents'].append(agent)
                    selection['reasoning'].append(f"Domain '{domain_key}' + complexity → {agent} agent")
                    break  # Use only one primary agent

    # RULE 3: Multiple services → orchestrator
    if 'multiple services' in str(structured_prompt).lower() or \
       'cross-service' in str(structured_prompt).lower():
        if 'orchestrator-agent' not in selection['agents']:
            selection['agents'].append('orchestrator-agent')
            selection['reasoning'].append("Multi-service task → orchestrator-agent")

    # RULE 4: Skill vs Agent decision
    # If both skill and agent available for same tech:
    # - Complexity < 10: Use skill (simpler)
    # - Complexity >= 10: Use agent (autonomous)

    if complexity_score < 10 and selection['agents']:
        # Not complex enough for agent, use skill if available
        if 'spring-boot-microservices' in selection['agents']:
            if 'java-spring-boot-microservices' not in selection['skills']:
                selection['skills'].append('java-spring-boot-microservices')
                selection['reasoning'].append("Low complexity → skill instead of agent")
            selection['agents'].remove('spring-boot-microservices')

    return selection


def extract_technologies(prompt: Dict) -> List[str]:
    """Extract technologies from structured prompt"""
    tech_stack = prompt.get('project_context', {}).get('technology_stack', [])
    keywords = prompt.get('analysis', {}).get('keywords', [])

    technologies = []
    for item in tech_stack + keywords:
        technologies.append(str(item).lower())

    return technologies


def extract_domain(task_type: str) -> str:
    """Extract domain from task type"""
    return task_type.lower()
```

---

## 📊 SELECTION DECISION MATRIX

| Task Type | Technologies | Complexity | Selection | Type |
|-----------|-------------|------------|-----------|------|
| **API Creation** | Spring Boot | < 10 | java-spring-boot-microservices | Skill |
| **API Creation** | Spring Boot | >= 10 | spring-boot-microservices | Agent |
| **Authentication** | Spring Boot | Any | java-spring-boot-microservices | Skill |
| **Database** | PostgreSQL | < 10 | rdbms-core | Skill |
| **Deployment** | Docker, K8s | >= 10 | devops-engineer | Agent |
| **CI/CD** | Jenkins | Any | jenkins-pipeline | Skill |
| **UI Design** | Angular | >= 10 | angular-engineer | Agent |
| **UI Design** | Android | >= 10 | android-ui-designer | Agent |
| **Testing** | Any | >= 10 | qa-testing-agent | Agent |
| **Multi-Service** | Any | >= 15 | orchestrator-agent | Agent |

---

## 🎯 EXAMPLES

### **Example 1: Simple Spring Boot API**

```yaml
Input:
  task_type: "API Creation"
  technologies: ["Spring Boot 3.2.0", "PostgreSQL"]
  complexity_score: 7

Selection:
  skills:
    - java-spring-boot-microservices
    - rdbms-core
  agents: []

Reasoning:
  - "Spring Boot detected → java-spring-boot-microservices"
  - "PostgreSQL detected → rdbms-core"
  - "Complexity < 10 → skill (not agent)"

Execution:
  # Execute skills directly, no agent needed
```

---

### **Example 2: Complex Multi-Service**

```yaml
Input:
  task_type: "Authentication"
  technologies: ["Spring Boot", "JWT", "Multi-service"]
  complexity_score: 18

Selection:
  skills: []
  agents:
    - spring-boot-microservices
    - orchestrator-agent

Reasoning:
  - "Spring Boot + complexity 18 → spring-boot-microservices agent"
  - "Multi-service detected → orchestrator-agent"

Execution:
  Task(subagent_type="orchestrator-agent", prompt="...")
  # Orchestrator will coordinate with spring-boot-microservices agent
```

---

### **Example 3: DevOps Deployment**

```yaml
Input:
  task_type: "Deployment"
  technologies: ["Docker", "Kubernetes", "Jenkins"]
  complexity_score: 15

Selection:
  skills:
    - docker
    - kubernetes
    - jenkins-pipeline
  agents:
    - devops-engineer

Reasoning:
  - "Docker detected → docker skill"
  - "Kubernetes detected → kubernetes skill"
  - "Jenkins detected → jenkins-pipeline skill"
  - "Deployment + complexity 15 → devops-engineer agent"

Execution:
  # Skills provide knowledge
  # Agent handles autonomous deployment
  Task(subagent_type="devops-engineer", prompt="...")
```

---

### **Example 4: Simple Bug Fix**

```yaml
Input:
  task_type: "Bug Fix"
  technologies: ["Spring Boot"]
  complexity_score: 2

Selection:
  skills:
    - java-spring-boot-microservices
  agents: []

Reasoning:
  - "Spring Boot detected → java-spring-boot-microservices"
  - "Complexity 2 → too simple for agent"

Execution:
  # Use skill knowledge, direct execution (no agent)
```

---

## 🔧 IMPLEMENTATION SCRIPT

**File:** `~/.claude/memory/auto-skill-agent-selector.py`

```python
#!/usr/bin/env python3
"""
Automatic Skill & Agent Selector
Analyzes context and selects appropriate skills/agents
"""

import json
import yaml
from typing import Dict, List


class AutoSkillAgentSelector:
    def __init__(self):
        # Load available resources from registry
        self.available_skills = self.load_skills()
        self.available_agents = self.load_agents()

    def load_skills(self) -> List[str]:
        """Load available skills from registry"""
        return [
            'context-management-core',
            'model-selection-core',
            'java-spring-boot-microservices',
            'spring-boot-design-patterns-core',
            'java-design-patterns-core',
            'docker',
            'kubernetes',
            'jenkins-pipeline',
            'rdbms-core',
            'nosql-core',
            'css-core',
            'animations-core',
            'seo-keyword-research-core'
        ]

    def load_agents(self) -> List[str]:
        """Load available agents from registry"""
        return [
            'spring-boot-microservices',
            'android-backend-engineer',
            'android-ui-designer',
            'angular-engineer',
            'devops-engineer',
            'dynamic-seo-agent',
            'orchestrator-agent',
            'qa-testing-agent',
            'static-seo-agent',
            'swift-backend-engineer',
            'swiftui-designer',
            'ui-ux-designer'
        ]

    def select(
        self,
        task_type: str,
        complexity: Dict,
        structured_prompt: Dict
    ) -> Dict:
        """
        Main selection logic
        """
        print("=" * 80)
        print("🎯 AUTO SKILL & AGENT SELECTION")
        print("=" * 80)

        selection = {
            'skills': [],
            'agents': [],
            'reasoning': []
        }

        # Extract context
        technologies = self.extract_technologies(structured_prompt)
        complexity_score = complexity.get('score', 0)

        print(f"\n📊 Context:")
        print(f"   Task Type: {task_type}")
        print(f"   Complexity: {complexity_score}")
        print(f"   Technologies: {technologies}")

        # Technology-based selection
        tech_matches = self.match_technologies(technologies, complexity_score)
        selection['skills'].extend(tech_matches['skills'])
        selection['agents'].extend(tech_matches['agents'])
        selection['reasoning'].extend(tech_matches['reasoning'])

        # Domain-based selection
        domain_matches = self.match_domain(task_type, complexity_score)
        for agent in domain_matches['agents']:
            if agent not in selection['agents']:
                selection['agents'].append(agent)
        selection['reasoning'].extend(domain_matches['reasoning'])

        # Output
        print(f"\n{'='*80}")
        print(f"✅ SELECTION COMPLETE")
        print(f"{'='*80}")

        if selection['skills']:
            print(f"\n📚 Selected Skills:")
            for skill in selection['skills']:
                print(f"   • {skill}")

        if selection['agents']:
            print(f"\n🤖 Selected Agents:")
            for agent in selection['agents']:
                print(f"   • {agent}")

        print(f"\n📋 Reasoning:")
        for reason in selection['reasoning']:
            print(f"   • {reason}")

        print(f"\n{'='*80}\n")

        return selection

    def extract_technologies(self, prompt: Dict) -> List[str]:
        """Extract technologies from prompt"""
        tech_stack = prompt.get('project_context', {}).get('technology_stack', [])
        keywords = prompt.get('analysis', {}).get('keywords', [])

        technologies = []
        for item in tech_stack + keywords:
            technologies.append(str(item).lower())

        return technologies

    def match_technologies(self, technologies: List[str], complexity: int) -> Dict:
        """Match technologies to skills/agents"""
        matches = {
            'skills': [],
            'agents': [],
            'reasoning': []
        }

        tech_map = {
            'spring boot': {
                'skill': 'java-spring-boot-microservices',
                'agent': 'spring-boot-microservices',
                'threshold': 10
            },
            'docker': {
                'skill': 'docker',
                'agent': 'devops-engineer',
                'threshold': 15
            },
            'kubernetes': {
                'skill': 'kubernetes',
                'agent': 'devops-engineer',
                'threshold': 15
            },
            'postgresql': {
                'skill': 'rdbms-core',
                'agent': None,
                'threshold': 999
            },
            'mongodb': {
                'skill': 'nosql-core',
                'agent': None,
                'threshold': 999
            }
        }

        for tech in technologies:
            for key, config in tech_map.items():
                if key in tech:
                    if complexity < config['threshold']:
                        # Use skill
                        if config['skill'] and config['skill'] not in matches['skills']:
                            matches['skills'].append(config['skill'])
                            matches['reasoning'].append(f"{key.title()} detected → {config['skill']} skill")
                    else:
                        # Use agent
                        if config['agent'] and config['agent'] not in matches['agents']:
                            matches['agents'].append(config['agent'])
                            matches['reasoning'].append(f"{key.title()} + complexity → {config['agent']} agent")

        return matches

    def match_domain(self, task_type: str, complexity: int) -> Dict:
        """Match task type to agents"""
        matches = {
            'agents': [],
            'reasoning': []
        }

        # Domain matching only for complex tasks
        if complexity >= 12:
            domain_map = {
                'deployment': 'devops-engineer',
                'ci/cd': 'devops-engineer',
                'testing': 'qa-testing-agent',
                'ui design': 'ui-ux-designer'
            }

            task_lower = task_type.lower()
            for domain, agent in domain_map.items():
                if domain in task_lower:
                    if agent not in matches['agents']:
                        matches['agents'].append(agent)
                        matches['reasoning'].append(f"Task type '{task_type}' → {agent} agent")

        return matches


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 4:
        print("Usage: python auto-skill-agent-selector.py task_type complexity.json prompt.yaml")
        sys.exit(1)

    task_type = sys.argv[1]

    with open(sys.argv[2], 'r') as f:
        complexity = json.load(f)

    with open(sys.argv[3], 'r') as f:
        prompt = yaml.safe_load(f)

    selector = AutoSkillAgentSelector()
    selection = selector.select(task_type, complexity, prompt)

    print(yaml.dump(selection, default_flow_style=False))


if __name__ == "__main__":
    main()
```

---

## ✅ CONSOLIDATION SUMMARY

**This Policy:**
- ✅ References existing `adaptive-skill-registry.md`
- ✅ Uses existing skills and agents (NO CREATE)
- ✅ Consolidates `core-skills-mandate.md` rules
- ✅ Fixes issues from `SKILL-AGENT-SELECTION-FIX-REPORT.md`
- ✅ Makes it formal Step 7 in execution flow
- ✅ Auto-selection based on ALL available context

**NO DUPLICATION:**
- References registry, doesn't duplicate it
- Uses existing skills/agents
- Organizes scattered knowledge

**NEW CONTRIBUTION:**
- Formal step in execution flow
- Context-aware selection (uses Steps 0-6 data)
- Auto-selection algorithm
- Integration with new pipeline

---

**VERSION:** 2.0.0 (CONSOLIDATED)
**CREATED:** 2026-02-16
**LOCATION:** `~/.claude/memory/auto-skill-agent-selection-policy.md`
**SCRIPT:** `~/.claude/memory/auto-skill-agent-selector.py`
**REFERENCES:** adaptive-skill-registry.md, core-skills-mandate.md
