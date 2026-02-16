#!/usr/bin/env python3
"""
Automatic Skill & Agent Selector
Context-aware selection based on task type, complexity, and technologies
"""

import json
import yaml
from typing import Dict, List
from pathlib import Path


class AutoSkillAgentSelector:
    """
    Automatically selects skills and agents based on context
    """

    def __init__(self):
        self.registry_file = Path.home() / ".claude" / "memory" / "adaptive-skill-registry.md"

        # Available skills (from registry)
        self.available_skills = [
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

        # Available agents (from registry)
        self.available_agents = [
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
        print("\n" + "=" * 80)
        print("🎯 AUTO SKILL & AGENT SELECTION")
        print("=" * 80)

        selection = {
            'skills': [],
            'agents': [],
            'reasoning': [],
            'execution_plan': []
        }

        # Extract context
        technologies = self.extract_technologies(structured_prompt)
        complexity_score = complexity.get('score', 0)
        task_lower = task_type.lower()

        print(f"\n📊 Context Analysis:")
        print(f"   Task Type: {task_type}")
        print(f"   Complexity: {complexity_score}")
        print(f"   Technologies: {', '.join(technologies) if technologies else 'None'}")

        # Technology-based selection
        tech_matches = self.match_technologies(technologies, complexity_score)
        selection['skills'].extend(tech_matches['skills'])
        selection['agents'].extend(tech_matches['agents'])
        selection['reasoning'].extend(tech_matches['reasoning'])

        # Task type specific selection
        type_matches = self.match_task_type(task_type, complexity_score)
        for skill in type_matches['skills']:
            if skill not in selection['skills']:
                selection['skills'].append(skill)
        for agent in type_matches['agents']:
            if agent not in selection['agents']:
                selection['agents'].append(agent)
        selection['reasoning'].extend(type_matches['reasoning'])

        # Multi-service detection
        if self.is_multi_service(structured_prompt):
            if 'orchestrator-agent' not in selection['agents']:
                selection['agents'].append('orchestrator-agent')
                selection['reasoning'].append("Multi-service task → orchestrator-agent")

        # Generate execution plan
        selection['execution_plan'] = self.generate_execution_plan(selection)

        # Output
        print(f"\n{'='*80}")
        print(f"✅ SELECTION COMPLETE")
        print(f"{'='*80}")

        if selection['skills']:
            print(f"\n📚 Selected Skills ({len(selection['skills'])}):")
            for skill in selection['skills']:
                print(f"   • {skill}")

        if selection['agents']:
            print(f"\n🤖 Selected Agents ({len(selection['agents'])}):")
            for agent in selection['agents']:
                print(f"   • {agent}")

        if not selection['skills'] and not selection['agents']:
            print(f"\n✅ No additional skills/agents needed")
            print(f"   Direct execution with base knowledge")

        print(f"\n📋 Reasoning:")
        for reason in selection['reasoning']:
            print(f"   • {reason}")

        if selection['execution_plan']:
            print(f"\n🎯 Execution Plan:")
            for step in selection['execution_plan']:
                print(f"   {step}")

        print(f"\n{'='*80}\n")

        return selection

    def extract_technologies(self, prompt: Dict) -> List[str]:
        """Extract technologies from structured prompt"""
        technologies = []

        # From tech stack
        tech_stack = prompt.get('project_context', {}).get('technology_stack', [])
        for tech in tech_stack:
            technologies.append(str(tech).lower())

        # From keywords
        keywords = prompt.get('analysis', {}).get('keywords', [])
        for kw in keywords:
            technologies.append(str(kw).lower())

        return technologies

    def match_technologies(self, technologies: List[str], complexity: int) -> Dict:
        """Match technologies to skills/agents"""
        matches = {
            'skills': [],
            'agents': [],
            'reasoning': []
        }

        # Technology to resource mapping
        tech_map = {
            'spring boot': {
                'skill': 'java-spring-boot-microservices',
                'agent': 'spring-boot-microservices',
                'agent_threshold': 10
            },
            'java': {
                'skill': 'java-design-patterns-core',
                'agent': None,
                'agent_threshold': 999
            },
            'docker': {
                'skill': 'docker',
                'agent': 'devops-engineer',
                'agent_threshold': 12
            },
            'kubernetes': {
                'skill': 'kubernetes',
                'agent': 'devops-engineer',
                'agent_threshold': 12
            },
            'k8s': {
                'skill': 'kubernetes',
                'agent': 'devops-engineer',
                'agent_threshold': 12
            },
            'jenkins': {
                'skill': 'jenkins-pipeline',
                'agent': 'devops-engineer',
                'agent_threshold': 15
            },
            'postgresql': {
                'skill': 'rdbms-core',
                'agent': None,
                'agent_threshold': 999
            },
            'mysql': {
                'skill': 'rdbms-core',
                'agent': None,
                'agent_threshold': 999
            },
            'mongodb': {
                'skill': 'nosql-core',
                'agent': None,
                'agent_threshold': 999
            },
            'elasticsearch': {
                'skill': 'nosql-core',
                'agent': None,
                'agent_threshold': 999
            },
            'angular': {
                'skill': None,
                'agent': 'angular-engineer',
                'agent_threshold': 8
            },
            'android': {
                'skill': None,
                'agent': 'android-backend-engineer',
                'agent_threshold': 10
            }
        }

        for tech in technologies:
            for key, config in tech_map.items():
                if key in tech:
                    # Check if should use agent
                    if config['agent'] and complexity >= config['agent_threshold']:
                        if config['agent'] not in matches['agents']:
                            matches['agents'].append(config['agent'])
                            matches['reasoning'].append(
                                f"{key.title()} + complexity {complexity} → {config['agent']} agent"
                            )
                    # Otherwise use skill
                    elif config['skill']:
                        if config['skill'] not in matches['skills']:
                            matches['skills'].append(config['skill'])
                            matches['reasoning'].append(
                                f"{key.title()} detected → {config['skill']} skill"
                            )

        return matches

    def match_task_type(self, task_type: str, complexity: int) -> Dict:
        """Match task type to skills/agents"""
        matches = {
            'skills': [],
            'agents': [],
            'reasoning': []
        }

        task_lower = task_type.lower()

        # Task type mappings
        if 'api' in task_lower or 'microservice' in task_lower:
            if 'java' in task_lower or 'spring' in task_lower:
                if complexity >= 10:
                    matches['agents'].append('spring-boot-microservices')
                    matches['reasoning'].append(f"Task '{task_type}' + complexity → spring-boot-microservices agent")
                else:
                    matches['skills'].append('java-spring-boot-microservices')
                    matches['reasoning'].append(f"Task '{task_type}' → java-spring-boot-microservices skill")

        if 'deployment' in task_lower or 'ci/cd' in task_lower or 'pipeline' in task_lower:
            if complexity >= 12:
                matches['agents'].append('devops-engineer')
                matches['reasoning'].append(f"Task '{task_type}' → devops-engineer agent")
            else:
                matches['skills'].append('jenkins-pipeline')
                matches['reasoning'].append(f"Task '{task_type}' → jenkins-pipeline skill")

        if 'test' in task_lower and complexity >= 10:
            matches['agents'].append('qa-testing-agent')
            matches['reasoning'].append(f"Task '{task_type}' → qa-testing-agent")

        if 'ui' in task_lower or 'design' in task_lower:
            if complexity >= 12:
                matches['agents'].append('ui-ux-designer')
                matches['reasoning'].append(f"Task '{task_type}' → ui-ux-designer agent")

        return matches

    def is_multi_service(self, prompt: Dict) -> bool:
        """Check if task involves multiple services"""
        prompt_str = str(prompt).lower()

        multi_service_indicators = [
            'multiple services',
            'cross-service',
            'all services',
            'services affected',
            'multi-service'
        ]

        return any(indicator in prompt_str for indicator in multi_service_indicators)

    def generate_execution_plan(self, selection: Dict) -> List[str]:
        """Generate execution plan based on selection"""
        plan = []

        if selection['agents']:
            # Agent-based execution
            if len(selection['agents']) == 1:
                agent = selection['agents'][0]
                plan.append(f"1. Execute: Task(subagent_type='{agent}', prompt='...')")

                if selection['skills']:
                    plan.append(f"2. Skills available to agent: {', '.join(selection['skills'])}")
            else:
                # Multiple agents - need orchestrator
                plan.append(f"1. Orchestrator coordinates {len(selection['agents'])} agents")
                for i, agent in enumerate(selection['agents'], 2):
                    plan.append(f"{i}. Agent: {agent}")

        elif selection['skills']:
            # Skill-based execution (direct)
            plan.append(f"1. Direct execution with skills:")
            for skill in selection['skills']:
                plan.append(f"   - Use {skill} knowledge")

        else:
            # No skills/agents needed
            plan.append("1. Direct execution with base knowledge")

        return plan


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 4:
        print("=" * 80)
        print("Auto Skill & Agent Selector")
        print("=" * 80)
        print("\nUsage:")
        print("  python auto-skill-agent-selector.py task_type complexity.json prompt.yaml")
        print("\nExample:")
        print("  python auto-skill-agent-selector.py 'API Creation' complexity.json structured_prompt.yaml")
        sys.exit(1)

    task_type = sys.argv[1]

    with open(sys.argv[2], 'r') as f:
        complexity = json.load(f)

    with open(sys.argv[3], 'r') as f:
        prompt = yaml.safe_load(f)

    selector = AutoSkillAgentSelector()
    selection = selector.select(task_type, complexity, prompt)

    # Save output
    output_file = 'skill_agent_selection.yaml'
    with open(output_file, 'w') as f:
        yaml.dump(selection, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Selection saved to: {output_file}")


if __name__ == "__main__":
    main()
