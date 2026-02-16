#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill/Agent Auto-Executor (Phase 4)
Automatically selects and executes skills/agents without confirmation

PHASE 4 AUTOMATION - FULL AUTO SKILL/AGENT EXECUTION
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class SkillAgentAutoExecutor:
    """
    Automatically selects and executes appropriate skills/agents
    Override on failure mechanism included
    """

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.logs_path = self.memory_path / 'logs'
        self.execution_log = self.logs_path / 'skill-agent-execution.log'

        # Skill/Agent registry (from adaptive-skill-registry.md)
        self.registry = self._load_registry()

    def _load_registry(self):
        """Load skill and agent registry"""
        return {
            'skills': {
                'java-spring-boot-microservices': {
                    'technologies': ['java', 'spring boot', 'spring', 'microservice'],
                    'complexity_min': 0,
                    'type': 'knowledge'
                },
                'docker': {
                    'technologies': ['docker', 'container', 'dockerfile'],
                    'complexity_min': 0,
                    'type': 'knowledge'
                },
                'kubernetes': {
                    'technologies': ['kubernetes', 'k8s', 'helm', 'kubectl'],
                    'complexity_min': 5,
                    'type': 'knowledge'
                },
                'rdbms-core': {
                    'technologies': ['database', 'sql', 'postgresql', 'mysql'],
                    'complexity_min': 0,
                    'type': 'knowledge'
                },
                'nosql-core': {
                    'technologies': ['mongodb', 'elasticsearch', 'nosql'],
                    'complexity_min': 0,
                    'type': 'knowledge'
                }
            },
            'agents': {
                'spring-boot-microservices': {
                    'technologies': ['java', 'spring boot', 'microservice'],
                    'complexity_min': 10,
                    'type': 'autonomous',
                    'description': 'Complex Java Spring Boot implementations'
                },
                'devops-engineer': {
                    'technologies': ['docker', 'kubernetes', 'ci/cd', 'jenkins'],
                    'complexity_min': 8,
                    'type': 'autonomous',
                    'description': 'Deployment and CI/CD'
                },
                'qa-testing-agent': {
                    'technologies': ['test', 'testing', 'junit'],
                    'complexity_min': 5,
                    'type': 'autonomous',
                    'description': 'Test implementation and validation'
                },
                'orchestrator-agent': {
                    'technologies': ['multi-service', 'microservices'],
                    'complexity_min': 15,
                    'type': 'autonomous',
                    'description': 'Multi-service coordination'
                }
            }
        }

    def match_skills(self, task_info):
        """Match appropriate skills based on task info"""
        matched_skills = []

        message = task_info.get('message', '').lower()
        complexity = task_info.get('complexity_score', 0)

        for skill_name, skill_info in self.registry['skills'].items():
            # Check technology match
            tech_match = any(tech in message for tech in skill_info['technologies'])

            # Check complexity threshold
            complexity_match = complexity >= skill_info['complexity_min']

            if tech_match and complexity_match:
                matched_skills.append({
                    'name': skill_name,
                    'type': 'skill',
                    'reason': f"Matched: {', '.join([t for t in skill_info['technologies'] if t in message])}"
                })

        return matched_skills

    def match_agents(self, task_info):
        """Match appropriate agents based on task info"""
        matched_agents = []

        message = task_info.get('message', '').lower()
        complexity = task_info.get('complexity_score', 0)
        service_count = task_info.get('service_count', 0)

        # Special case: Multi-service
        if service_count > 1:
            matched_agents.append({
                'name': 'orchestrator-agent',
                'type': 'agent',
                'reason': f'Multi-service task ({service_count} services)'
            })
            return matched_agents  # Orchestrator handles everything

        # Match individual agents
        for agent_name, agent_info in self.registry['agents'].items():
            # Skip orchestrator (already checked above)
            if agent_name == 'orchestrator-agent':
                continue

            # Check technology match
            tech_match = any(tech in message for tech in agent_info['technologies'])

            # Check complexity threshold
            complexity_match = complexity >= agent_info['complexity_min']

            if tech_match and complexity_match:
                matched_agents.append({
                    'name': agent_name,
                    'type': 'agent',
                    'reason': f"{agent_info['description']} - Matched: {', '.join([t for t in agent_info['technologies'] if t in message])}"
                })

        return matched_agents

    def decide_execution_strategy(self, complexity_score, skills, agents):
        """
        Decide execution strategy

        Rules:
        - Complexity < 10: Use skills (knowledge-based)
        - Complexity >= 10: Use agents (autonomous)
        - Multi-service: Always use orchestrator agent
        """
        if agents and complexity_score >= 10:
            return {
                'strategy': 'agent',
                'selected': agents,
                'reason': f'Complex task (score: {complexity_score}) - autonomous agent needed'
            }
        elif skills:
            return {
                'strategy': 'skill',
                'selected': skills,
                'reason': f'Moderate task (score: {complexity_score}) - skill knowledge sufficient'
            }
        else:
            return {
                'strategy': 'direct',
                'selected': [],
                'reason': 'No matching skills/agents - proceed directly'
            }

    def auto_execute(self, task_info, dry_run=False):
        """
        Main entry point - automatically select and execute
        """
        # Match skills and agents
        matched_skills = self.match_skills(task_info)
        matched_agents = self.match_agents(task_info)

        # Decide strategy
        complexity = task_info.get('complexity_score', 0)
        strategy = self.decide_execution_strategy(complexity, matched_skills, matched_agents)

        result = {
            'matched_skills': matched_skills,
            'matched_agents': matched_agents,
            'strategy': strategy['strategy'],
            'selected': strategy['selected'],
            'reason': strategy['reason'],
            'dry_run': dry_run,
            'timestamp': datetime.now().isoformat()
        }

        # Execute (if not dry run)
        if not dry_run and strategy['selected']:
            execution_results = []
            for item in strategy['selected']:
                exec_result = self.execute_item(item, task_info)
                execution_results.append(exec_result)

            result['execution_results'] = execution_results

        # Log execution
        self.log_execution(result)

        # Mark as checked in blocking enforcer
        try:
            subprocess.run(
                ['python', str(self.memory_path / 'blocking-policy-enforcer.py'),
                 '--mark-skills-agents-checked'],
                capture_output=True,
                timeout=5
            )
        except:
            pass

        return result

    def execute_item(self, item, task_info):
        """Execute a skill or agent"""
        item_type = item['type']
        item_name = item['name']

        try:
            if item_type == 'skill':
                # Execute skill (via Skill tool or direct invocation)
                result = self.execute_skill(item_name, task_info)
            else:
                # Execute agent (via Task tool)
                result = self.execute_agent(item_name, task_info)

            return {
                'name': item_name,
                'type': item_type,
                'status': 'success',
                'result': result
            }

        except Exception as e:
            return {
                'name': item_name,
                'type': item_type,
                'status': 'failure',
                'error': str(e)
            }

    def execute_skill(self, skill_name, task_info):
        """Execute a skill"""
        # In real implementation, this would invoke the skill
        # For now, just return mock result
        return f"Skill {skill_name} would be invoked here"

    def execute_agent(self, agent_name, task_info):
        """Execute an agent"""
        # In real implementation, this would spawn the agent via Task tool
        # For now, just return mock result
        return f"Agent {agent_name} would be spawned here"

    def log_execution(self, result):
        """Log execution"""
        self.logs_path.mkdir(parents=True, exist_ok=True)

        log_entry = {
            'timestamp': result['timestamp'],
            'strategy': result['strategy'],
            'selected_count': len(result['selected']),
            'dry_run': result['dry_run']
        }

        with open(self.execution_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def print_result(self, result):
        """Print formatted result"""
        print(f"\n{'='*70}")
        print(f"🤖 Skill/Agent Auto-Executor (Phase 4)")
        print(f"{'='*70}\n")

        print(f"🔍 Matched Skills ({len(result['matched_skills'])}):")
        if result['matched_skills']:
            for skill in result['matched_skills']:
                print(f"   • {skill['name']}: {skill['reason']}")
        else:
            print(f"   None")

        print(f"\n🤖 Matched Agents ({len(result['matched_agents'])}):")
        if result['matched_agents']:
            for agent in result['matched_agents']:
                print(f"   • {agent['name']}: {agent['reason']}")
        else:
            print(f"   None")

        print(f"\n✅ Strategy: {result['strategy'].upper()}")
        print(f"   Reason: {result['reason']}")

        if result['selected']:
            print(f"\n🚀 Selected for Execution:")
            for item in result['selected']:
                print(f"   • {item['name']} ({item['type']})")

        if result.get('execution_results'):
            print(f"\n📊 Execution Results:")
            for exec_result in result['execution_results']:
                status_icon = '✅' if exec_result['status'] == 'success' else '❌'
                print(f"   {status_icon} {exec_result['name']}: {exec_result['status']}")

        if result['dry_run']:
            print(f"\n⚠️  DRY RUN MODE - No actual execution")

        print(f"\n{'='*70}\n")


def main():
    """CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Skill/Agent Auto-Executor (Phase 4)')
    parser.add_argument('--task-info', required=True, help='Task information (JSON)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run - no execution')

    args = parser.parse_args()

    try:
        task_info = json.loads(args.task_info)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON task info: {args.task_info}")
        sys.exit(1)

    executor = SkillAgentAutoExecutor()
    result = executor.auto_execute(task_info, dry_run=args.dry_run)

    executor.print_result(result)

    sys.exit(0)


if __name__ == '__main__':
    main()
