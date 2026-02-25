#!/usr/bin/env python3
"""
Automatic Plan Mode Suggester
Analyzes complexity and suggests whether to use plan mode
"""

import json
import yaml
from typing import Dict, List
from datetime import datetime


class AutoPlanModeSuggester:
    def __init__(self):
        self.decision_log = []

    def should_use_plan_mode(
        self,
        complexity_analysis: Dict,
        structured_prompt: Dict
    ) -> Dict:
        """
        Main decision function
        """
        print("=" * 80)
        print("🎯 AUTO PLAN MODE SUGGESTION")
        print("=" * 80)

        # Step 1: Get base complexity
        base_score = complexity_analysis.get('score', 0)
        print(f"\n📊 Base Complexity Score: {base_score}")

        # Step 2: Calculate additional risk factors
        risks = self.calculate_risk_factors(structured_prompt, complexity_analysis)
        print(f"\n⚠️  Risk Adjustment: +{risks['score']}")
        if risks['factors']:
            print(f"   Risk Factors:")
            for factor in risks['factors']:
                print(f"   - {factor}")

        # Step 3: Adjust complexity
        adjusted_complexity = self.adjust_complexity_with_risks(
            complexity_analysis.copy(),
            risks
        )
        adjusted_score = adjusted_complexity['score']
        level = adjusted_complexity['level']

        print(f"\n📈 Adjusted Complexity: {adjusted_score} ({level})")

        # Step 4: Make decision
        decision = self.make_decision(adjusted_complexity)

        # Step 5: Format output
        message = self.format_suggestion(decision, adjusted_complexity)
        print(f"\n{message}")

        # Log decision
        self.log_decision(decision, adjusted_complexity)

        return decision

    def calculate_risk_factors(
        self,
        structured_prompt: Dict,
        complexity: Dict
    ) -> Dict:
        """
        Calculate additional risk factors beyond base complexity
        """
        risks = {
            'score': 0,
            'factors': []
        }

        prompt_str = str(structured_prompt).lower()

        # Factor 1: Multi-service impact
        if any(kw in prompt_str for kw in ['multiple services', 'all services', 'cross-service']):
            risks['score'] += 5
            risks['factors'].append('Multi-service impact detected')

        # Factor 2: Database changes
        if any(kw in prompt_str for kw in ['database', 'migration', 'schema', 'alter table']):
            risks['score'] += 5
            risks['factors'].append('Database changes involved')

        # Factor 3: Security/Auth
        if any(kw in prompt_str for kw in ['auth', 'security', 'jwt', 'permission', 'role']):
            risks['score'] += 3
            risks['factors'].append('Security-critical changes')

        # Factor 4: External integrations
        if any(kw in prompt_str for kw in ['integration', 'api call', 'external', 'third-party']):
            risks['score'] += 3
            risks['factors'].append('External integration complexity')

        # Factor 5: No similar examples found
        examples = structured_prompt.get('examples_from_codebase', [])
        if not examples or len(examples) == 0:
            risks['score'] += 4
            risks['factors'].append('No similar examples in codebase')

        # Factor 6: Uncertainties flagged
        metadata = structured_prompt.get('metadata', {})
        if metadata.get('uncertainties') or metadata.get('assumptions'):
            risks['score'] += 2
            risks['factors'].append('Uncertainties identified in requirements')

        # Factor 7: Performance critical
        if any(kw in prompt_str for kw in ['performance', 'optimize', 'scalability']):
            risks['score'] += 2
            risks['factors'].append('Performance-critical implementation')

        # Factor 8: Breaking changes
        if any(kw in prompt_str for kw in ['breaking', 'major change', 'refactor']):
            risks['score'] += 4
            risks['factors'].append('Potential breaking changes')

        return risks

    def adjust_complexity_with_risks(
        self,
        complexity: Dict,
        risks: Dict
    ) -> Dict:
        """
        Adjust complexity score based on risk factors
        """
        original_score = complexity['score']
        risk_score = risks['score']
        adjusted_score = original_score + risk_score

        complexity['original_score'] = original_score
        complexity['risk_adjustment'] = risk_score
        complexity['score'] = adjusted_score
        complexity['level'] = self.get_complexity_level(adjusted_score)
        complexity['risk_factors'] = risks['factors']

        return complexity

    def get_complexity_level(self, score: int) -> str:
        """Get complexity level from score"""
        if score < 5:
            return 'SIMPLE'
        elif score < 10:
            return 'MODERATE'
        elif score < 20:
            return 'COMPLEX'
        else:
            return 'VERY_COMPLEX'

    def make_decision(self, complexity: Dict) -> Dict:
        """
        Make plan mode decision based on complexity
        """
        score = complexity.get('score', 0)
        level = complexity.get('level', 'SIMPLE')

        decision = {
            'score': score,
            'level': level,
            'plan_mode_required': False,
            'plan_mode_recommended': False,
            'plan_mode_optional': False,
            'should_ask_user': False,
            'auto_enter': False,
            'reasoning': '',
            'benefits': [],
            'risks_without_planning': [],
            'recommendation': ''
        }

        if score < 5:
            # SIMPLE
            decision['recommendation'] = 'NO_PLAN_MODE'
            decision['reasoning'] = 'Task is straightforward, direct execution is efficient'

        elif score < 10:
            # MODERATE
            decision['plan_mode_optional'] = True
            decision['should_ask_user'] = True
            decision['recommendation'] = 'OPTIONAL'
            decision['reasoning'] = 'Task has moderate complexity, planning may help but not critical'
            decision['benefits'] = [
                'Clearer implementation strategy',
                'Upfront identification of potential issues'
            ]

        elif score < 20:
            # COMPLEX
            decision['plan_mode_recommended'] = True
            decision['should_ask_user'] = True
            decision['recommendation'] = 'RECOMMENDED'
            decision['reasoning'] = 'Task complexity warrants upfront planning'
            decision['benefits'] = [
                'Design implementation strategy before coding',
                'Identify architectural issues early',
                'Ensure alignment with existing patterns',
                'Reduce risk of rework',
                'Better quality outcome'
            ]
            decision['risks_without_planning'] = [
                'May choose suboptimal approach',
                'Could miss important dependencies',
                'Higher chance of rework',
                'Potential architectural misalignment'
            ]

        else:
            # VERY COMPLEX
            decision['plan_mode_required'] = True
            decision['auto_enter'] = True
            decision['recommendation'] = 'REQUIRED'
            decision['reasoning'] = 'Task is too complex to execute safely without planning'
            decision['benefits'] = [
                'CRITICAL: Prevents incorrect architectural approach',
                'CRITICAL: Identifies all cross-service impacts',
                'CRITICAL: Ensures thorough dependency analysis',
                'CRITICAL: Significantly reduces rework risk'
            ]
            decision['risks_without_planning'] = [
                '🔴 HIGH: Wrong architectural decisions',
                '🔴 HIGH: Missed critical dependencies',
                '🔴 HIGH: Breaking changes to other services',
                '🔴 HIGH: Major rework required',
                '🔴 HIGH: Production issues'
            ]

        return decision

    def format_suggestion(self, decision: Dict, complexity: Dict) -> str:
        """
        Format the suggestion message
        """
        score = decision['score']
        level = decision['level']

        output = f"""
{'='*80}
📊 COMPLEXITY ANALYSIS COMPLETE
{'='*80}

Score: {score} ({level})
Tasks: {complexity.get('estimated_tasks', 'Unknown')}
Files: {complexity.get('file_count', 'Unknown')}
Phases: {len(complexity.get('phases', []))}
"""

        if complexity.get('risk_factors'):
            output += f"\nRisk Factors:"
            for factor in complexity['risk_factors']:
                output += f"\n  ⚠️  {factor}"

        output += "\n"

        if decision['auto_enter']:
            # VERY COMPLEX
            output += f"""
{'='*80}
🔴 PLAN MODE: REQUIRED (MANDATORY)
{'='*80}

{decision['reasoning']}

Why this is mandatory:
"""
            for risk in decision['risks_without_planning']:
                output += f"{risk}\n"

            output += """
I will now enter plan mode to create a detailed implementation plan.
This will ensure we approach this correctly and avoid costly mistakes.

✅ ACTION: Entering plan mode automatically...
"""

        elif decision['plan_mode_recommended']:
            # COMPLEX
            output += f"""
{'='*80}
✅ PLAN MODE: STRONGLY RECOMMENDED
{'='*80}

{decision['reasoning']}

Benefits of planning:
"""
            for benefit in decision['benefits']:
                output += f"✅ {benefit}\n"

            output += "\nRisks without planning:"
            for risk in decision['risks_without_planning']:
                output += f"⚠️  {risk}\n"

            output += """
⚠️  RECOMMENDATION: Enter plan mode (STRONGLY SUGGESTED)

Would you like me to enter plan mode?
- Yes: I'll create a detailed plan for your approval (Recommended)
- No: I'll proceed directly (higher risk, not recommended)
"""

        elif decision['plan_mode_optional']:
            # MODERATE
            output += f"""
{'='*80}
⚠️  PLAN MODE: OPTIONAL
{'='*80}

{decision['reasoning']}

Option 1 (Recommended): Proceed directly
- Can execute using standard patterns
- Estimated time: Faster
- Risk: Low

Option 2: Enter plan mode
- Create detailed implementation plan
- Review approach first
- Estimated time: +5-10 minutes for planning

💡 RECOMMENDATION: Option 1 (Proceed directly)
"""

        else:
            # SIMPLE
            output += f"""
{'='*80}
✅ NO PLAN MODE NEEDED
{'='*80}

{decision['reasoning']}

✅ ACTION: Proceeding directly to execution...
"""

        output += f"{'='*80}\n"

        return output

    def log_decision(self, decision: Dict, complexity: Dict):
        """
        Log decision for future learning
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'score': decision['score'],
            'level': decision['level'],
            'recommendation': decision['recommendation'],
            'complexity_details': complexity
        }

        self.decision_log.append(log_entry)


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python auto-plan-mode-suggester.py complexity.json structured_prompt.yaml")
        print("\nExample:")
        print("  python auto-plan-mode-suggester.py task_breakdown.json structured_prompt.yaml")
        sys.exit(1)

    # Load complexity analysis
    with open(sys.argv[1], 'r') as f:
        complexity = json.load(f)

    # Load structured prompt
    with open(sys.argv[2], 'r') as f:
        structured_prompt = yaml.safe_load(f)

    # Make decision
    suggester = AutoPlanModeSuggester()
    decision = suggester.should_use_plan_mode(complexity, structured_prompt)

    # Output decision as JSON
    print("\n" + "=" * 80)
    print("DECISION OUTPUT (JSON)")
    print("=" * 80)
    print(json.dumps(decision, indent=2))

    # Return exit code based on decision
    if decision['auto_enter']:
        sys.exit(2)  # Auto-enter plan mode
    elif decision['should_ask_user']:
        sys.exit(1)  # Ask user
    else:
        sys.exit(0)  # No plan mode needed


if __name__ == "__main__":
    main()
