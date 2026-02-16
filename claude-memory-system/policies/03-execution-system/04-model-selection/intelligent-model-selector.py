#!/usr/bin/env python3
"""
Intelligent Model Selector
Selects optimal Claude model based on complexity, task type, and context
"""

import json
import yaml
from typing import Dict, List


class IntelligentModelSelector:
    def __init__(self):
        # Task type to model mapping
        self.task_type_models = {
            # Architecture & Design → OPUS
            'Architecture Design': 'OPUS',
            'System Design': 'OPUS',
            'Migration Planning': 'OPUS',
            'Refactoring Strategy': 'OPUS',

            # Implementation → SONNET
            'API Creation': 'SONNET',
            'Service Implementation': 'SONNET',
            'Business Logic': 'SONNET',
            'Integration': 'SONNET',
            'Authentication': 'SONNET',
            'Authorization': 'SONNET',

            # Simple Operations → HAIKU
            'Bug Fix': 'HAIKU',
            'Documentation': 'HAIKU',
            'Configuration': 'HAIKU',
            'Constant Addition': 'HAIKU',

            # Search & Analysis → HAIKU
            'Code Search': 'HAIKU',
            'File Reading': 'HAIKU',
            'Status Check': 'HAIKU'
        }

        # Model costs (per million tokens)
        self.model_costs = {
            'HAIKU': {'input': 0.25, 'output': 1.25},
            'SONNET': {'input': 3.00, 'output': 15.00},
            'OPUS': {'input': 15.00, 'output': 75.00}
        }

        # Estimated tokens per task
        self.tokens_per_task = {
            'HAIKU': 2000,
            'SONNET': 5000,
            'OPUS': 10000
        }

    def select_model(
        self,
        complexity: Dict,
        task_type: str,
        plan_mode_decision: Dict
    ) -> Dict:
        """
        Main model selection logic
        """
        print("=" * 80)
        print("🤖 INTELLIGENT MODEL SELECTION")
        print("=" * 80)

        selection = {
            'selected_model': None,
            'reasoning': [],
            'alternatives': [],
            'cost_estimate': {},
            'confidence': 'HIGH',
            'dynamic_upgrade': {
                'enabled': True,
                'conditions': [],
                'upgrade_to': None
            }
        }

        # Extract values
        complexity_score = complexity.get('score', 0)
        complexity_level = complexity.get('level', 'SIMPLE')
        risk_factors = complexity.get('risk_factors', [])

        print(f"\n📊 Input Analysis:")
        print(f"   Complexity: {complexity_score} ({complexity_level})")
        print(f"   Task Type: {task_type}")
        print(f"   Plan Mode: {plan_mode_decision.get('recommendation', 'NO')}")
        if risk_factors:
            print(f"   Risk Factors: {len(risk_factors)}")

        # RULE 1: Plan mode always uses OPUS
        if plan_mode_decision.get('auto_enter') or plan_mode_decision.get('in_plan_mode'):
            selection['selected_model'] = 'OPUS'
            selection['reasoning'].append('Plan mode requires OPUS for deep analysis and architectural thinking')
            selection['reasoning'].append('Critical decisions need highest capability model')

            print(f"\n🔴 PLAN MODE DETECTED → OPUS (Mandatory)")

            # After planning, execution uses SONNET
            if complexity_score >= 10:
                selection['dynamic_upgrade']['upgrade_to'] = 'SONNET'
                selection['reasoning'].append('After plan approval, switch to SONNET for execution')

        # RULE 2: Task type override
        elif task_type in self.task_type_models:
            suggested_model = self.task_type_models[task_type]

            if suggested_model == 'OPUS':
                # Always use OPUS for architecture
                selection['selected_model'] = 'OPUS'
                selection['reasoning'].append(f'Task type "{task_type}" requires OPUS')

            elif suggested_model == 'HAIKU' and complexity_score >= 10:
                # Complexity overrides simple task type
                selection['selected_model'] = 'SONNET'
                selection['reasoning'].append(f'Task type suggests HAIKU but complexity ({complexity_score}) requires SONNET')

            else:
                # Use suggested model
                selection['selected_model'] = suggested_model
                selection['reasoning'].append(f'Task type "{task_type}" matches {suggested_model} capabilities')

        # RULE 3: Complexity-based selection
        else:
            if complexity_score < 5:
                # SIMPLE
                selection['selected_model'] = 'HAIKU'
                selection['reasoning'].append(f'Low complexity ({complexity_score}) → HAIKU for speed and efficiency')

            elif complexity_score < 10:
                # MODERATE
                if task_type in ['API Creation', 'Business Logic', 'Integration']:
                    selection['selected_model'] = 'SONNET'
                    selection['reasoning'].append(f'Moderate complexity + code task → SONNET')
                else:
                    selection['selected_model'] = 'HAIKU'
                    selection['reasoning'].append(f'Moderate complexity + simple task → HAIKU')
                    selection['alternatives'].append({
                        'model': 'SONNET',
                        'reason': 'Use if task proves more complex than expected',
                        'risk': 'May need upgrade during execution'
                    })

            elif complexity_score < 20:
                # COMPLEX
                selection['selected_model'] = 'SONNET'
                selection['reasoning'].append(f'High complexity ({complexity_score}) requires SONNET reasoning')
                selection['reasoning'].append('Multiple files and complex logic coordination needed')

            else:
                # VERY_COMPLEX
                selection['selected_model'] = 'SONNET'
                selection['reasoning'].append(f'Very high complexity ({complexity_score}) requires SONNET')
                selection['reasoning'].append('Consider OPUS if architectural decisions arise')

                selection['dynamic_upgrade']['upgrade_to'] = 'OPUS'
                selection['dynamic_upgrade']['conditions'].append('Architectural issues discovered')

        # RULE 4: Risk-based adjustments
        if risk_factors:
            print(f"\n⚠️  Risk Factor Analysis:")

            security_risk = any('security' in str(f).lower() for f in risk_factors)
            multi_service_risk = any('multi-service' in str(f).lower() for f in risk_factors)

            if security_risk:
                print(f"   - Security-critical task detected")
                if selection['selected_model'] == 'HAIKU':
                    selection['selected_model'] = 'SONNET'
                    selection['reasoning'].append('🔒 Security-critical: upgraded to SONNET')

            if multi_service_risk:
                print(f"   - Multi-service impact detected")
                if selection['selected_model'] == 'HAIKU':
                    selection['selected_model'] = 'SONNET'
                    selection['reasoning'].append('🔄 Multi-service coordination: upgraded to SONNET')

        # Calculate cost estimate
        num_tasks = complexity.get('estimated_tasks', 5)
        selection['cost_estimate'] = self.estimate_cost(
            selection['selected_model'],
            num_tasks
        )

        # Set upgrade conditions
        if selection['selected_model'] != 'OPUS':
            selection['dynamic_upgrade']['conditions'].extend([
                'Build failures >= 3',
                'Test failures >= 3',
                'Security vulnerabilities found',
                'Performance issues detected'
            ])

        # Print selection
        print(f"\n{'='*80}")
        print(f"✅ SELECTED MODEL: {selection['selected_model']}")
        print(f"{'='*80}")

        print(f"\n📋 Reasoning:")
        for reason in selection['reasoning']:
            print(f"   • {reason}")

        if selection['alternatives']:
            print(f"\n⚠️  Alternatives:")
            for alt in selection['alternatives']:
                print(f"   • {alt['model']}: {alt['reason']}")

        print(f"\n💰 Cost Estimate:")
        cost = selection['cost_estimate']
        print(f"   Model: {cost['model']}")
        print(f"   Estimated Tokens: {cost['estimated_tokens']:,}")
        print(f"   Estimated Cost: ${cost['estimated_cost_usd']:.4f}")
        print(f"   Tasks: {cost['num_tasks']}")

        if selection['dynamic_upgrade']['upgrade_to']:
            print(f"\n🔄 Dynamic Upgrade:")
            print(f"   Can upgrade to: {selection['dynamic_upgrade']['upgrade_to']}")
            print(f"   Conditions:")
            for condition in selection['dynamic_upgrade']['conditions']:
                print(f"   • {condition}")

        print(f"\n{'='*80}")

        return selection

    def estimate_cost(self, model: str, num_tasks: int) -> Dict:
        """
        Estimate cost and tokens for execution
        """
        model_cost = self.model_costs[model]
        model_tokens = self.tokens_per_task[model]

        total_tokens = model_tokens * num_tasks

        # Average input/output split (60% input, 40% output)
        input_tokens = total_tokens * 0.6
        output_tokens = total_tokens * 0.4

        estimated_cost = (
            (input_tokens / 1_000_000) * model_cost['input'] +
            (output_tokens / 1_000_000) * model_cost['output']
        )

        return {
            'model': model,
            'estimated_tokens': int(total_tokens),
            'input_tokens': int(input_tokens),
            'output_tokens': int(output_tokens),
            'estimated_cost_usd': round(estimated_cost, 4),
            'num_tasks': num_tasks
        }


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 4:
        print("=" * 80)
        print("Intelligent Model Selector")
        print("=" * 80)
        print("\nUsage:")
        print("  python intelligent-model-selector.py complexity.json task_type plan_mode.json")
        print("\nExample:")
        print("  python intelligent-model-selector.py complexity.json \"API Creation\" plan_mode.json")
        print("\nInputs:")
        print("  1. complexity.json    - Output from task breakdown")
        print("  2. task_type          - Task type string")
        print("  3. plan_mode.json     - Plan mode decision output")
        sys.exit(1)

    # Load complexity analysis
    with open(sys.argv[1], 'r') as f:
        complexity = json.load(f)

    # Get task type
    task_type = sys.argv[2]

    # Load plan mode decision
    with open(sys.argv[3], 'r') as f:
        plan_mode_decision = json.load(f)

    # Select model
    selector = IntelligentModelSelector()
    selection = selector.select_model(complexity, task_type, plan_mode_decision)

    # Output as YAML
    print("\n" + "=" * 80)
    print("MODEL SELECTION OUTPUT (YAML)")
    print("=" * 80)
    print(yaml.dump(selection, default_flow_style=False, sort_keys=False))

    # Also save to file
    output_file = 'model_selection.yaml'
    with open(output_file, 'w') as f:
        yaml.dump(selection, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Saved to: {output_file}")


if __name__ == "__main__":
    main()
