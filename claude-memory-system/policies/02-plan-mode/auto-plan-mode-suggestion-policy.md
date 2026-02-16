# 🎯 Automatic Plan Mode Suggestion Policy

**VERSION:** 1.0.0
**CREATED:** 2026-02-16
**PRIORITY:** 🔴 CRITICAL - STEP 2 (After Task Breakdown)
**STATUS:** 🟢 ACTIVE

---

## 📋 POLICY OVERVIEW

**MANDATORY: After Step 1 (Task Breakdown), automatically:**

1. ✅ **Analyze** complexity score from task breakdown
2. ✅ **Decide** if plan mode is needed
3. ✅ **Suggest** to user (or enforce for very complex tasks)
4. ✅ **Enter plan mode** if accepted/required
5. ✅ **Proceed directly** if not needed

---

## 🚨 EXECUTION ORDER

```
Step 0: Structured Prompt Generated ✅
        ↓
Step 1: Task Breakdown Complete ✅
        (Complexity Score Calculated)
        ↓
🔴 STEP 2: AUTO PLAN MODE SUGGESTION (THIS POLICY)
        ↓
    Analyze Complexity Score
        ↓
    Determine Plan Mode Requirement
        ↓
    ┌─────────────────────────────────┐
    │  Complexity Decision Matrix      │
    │                                  │
    │  SIMPLE (0-4):                   │
    │  ❌ No plan mode → Direct exec   │
    │                                  │
    │  MODERATE (5-9):                 │
    │  ⚠️ Optional → Ask user          │
    │                                  │
    │  COMPLEX (10-19):                │
    │  ✅ Recommended → Strong suggest │
    │                                  │
    │  VERY_COMPLEX (20+):             │
    │  🔴 MANDATORY → Must use         │
    └─────────────────────────────────┘
        ↓
    Execute Decision
        ↓
Step 3: Model Selection
Step 4: Context Check
... (continue execution)
```

---

## 🎯 COMPLEXITY DECISION MATRIX

### **SIMPLE Tasks (Score: 0-4)**

**Characteristics:**
- 1-3 files to create/modify
- Single entity
- No complex dependencies
- Standard CRUD or simple fix
- No integration points

**Decision:**
```
❌ Plan Mode: NOT NEEDED
✅ Action: Proceed directly to execution
📝 Reason: Task is straightforward, no planning overhead needed
```

**Examples:**
- "Fix a typo in README"
- "Add a simple validation rule"
- "Create a single entity"
- "Add a constant to enum"

**Output:**
```
📊 Complexity Analysis:
   Score: 3 (SIMPLE)
   Tasks: 2
   Files: 1-2

✅ DECISION: NO PLAN MODE NEEDED
   This task is straightforward and can be executed directly.

   Proceeding to execution...
```

---

### **MODERATE Tasks (Score: 5-9)**

**Characteristics:**
- 3-6 files to create/modify
- 1-2 entities
- Some dependencies
- Standard patterns available
- Minimal integration

**Decision:**
```
⚠️ Plan Mode: OPTIONAL (Ask User)
📝 Reason: Task is moderately complex, planning may help but not critical
```

**User Prompt:**
```
📊 Complexity Analysis:
   Score: 7 (MODERATE)
   Tasks: 5
   Files: 4
   Phases: None (direct execution possible)

⚠️ PLAN MODE SUGGESTION:
   This task has moderate complexity. Would you like me to:

   Option 1 (Recommended): Proceed directly
   - I can execute this using standard patterns
   - Estimated time: 5-10 minutes
   - Low risk

   Option 2: Enter plan mode first
   - Create detailed implementation plan
   - Review architecture decisions
   - Estimated time: +5 minutes for planning

   Your choice? (1/2)
```

**Examples:**
- "Create a simple CRUD API"
- "Add basic authentication"
- "Implement a new service method"
- "Add configuration for service"

---

### **COMPLEX Tasks (Score: 10-19)**

**Characteristics:**
- 7-15 files to create/modify
- 2-3 entities
- Multiple dependencies
- Cross-service integration
- Custom business logic

**Decision:**
```
✅ Plan Mode: STRONGLY RECOMMENDED
📝 Reason: Task complexity warrants upfront planning to ensure correct approach
```

**User Prompt:**
```
📊 Complexity Analysis:
   Score: 15 (COMPLEX)
   Tasks: 12
   Files: 10
   Phases: 4
   Dependencies: Multiple cross-file dependencies

✅ PLAN MODE RECOMMENDED:
   This task has significant complexity. I strongly recommend plan mode to:

   Benefits:
   ✅ Design implementation strategy upfront
   ✅ Identify potential issues early
   ✅ Ensure architectural alignment
   ✅ Review approach before coding
   ✅ Reduce rework risk

   Recommendation: ENTER PLAN MODE
   - Time: +10 minutes for planning
   - Risk reduction: High
   - Quality improvement: Significant

   Proceed with plan mode? (Yes/No)
   (You can skip, but it's recommended)
```

**Examples:**
- "Create complete CRUD API with validation"
- "Add JWT authentication to service"
- "Implement order processing workflow"
- "Create multi-service integration"

---

### **VERY COMPLEX Tasks (Score: 20+)**

**Characteristics:**
- 15+ files to create/modify
- 3+ entities
- Complex dependencies
- Multi-service integration
- Custom architecture needed
- High risk of mistakes

**Decision:**
```
🔴 Plan Mode: MANDATORY
📝 Reason: Task is too complex to execute safely without planning
```

**User Notification:**
```
📊 Complexity Analysis:
   Score: 24 (VERY COMPLEX)
   Tasks: 18
   Files: 15+
   Phases: 5+
   Dependencies: Complex cross-service dependencies
   Risk: HIGH

🔴 PLAN MODE REQUIRED:
   This task is very complex and REQUIRES planning before execution.

   Why mandatory:
   🔴 High risk of incorrect approach without planning
   🔴 Multiple architectural decisions needed
   🔴 Cross-service impacts require careful design
   🔴 Potential for significant rework if rushed

   I will now enter plan mode to:
   1. Explore codebase thoroughly
   2. Design implementation strategy
   3. Identify all dependencies
   4. Create detailed execution plan
   5. Get your approval before coding

   Entering plan mode automatically...
   [EnterPlanMode tool called]
```

**Examples:**
- "Implement complete authentication system"
- "Migrate database schema across all services"
- "Create new microservice with full integration"
- "Implement event-driven architecture"
- "Major refactoring across multiple services"

---

## 🔧 DECISION ALGORITHM

```python
def should_use_plan_mode(complexity_analysis: Dict) -> Dict:
    """
    Determine if plan mode should be used
    """
    score = complexity_analysis.get('score', 0)
    level = complexity_analysis.get('level', 'SIMPLE')

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
        'risks_without_planning': []
    }

    if score < 5:
        # SIMPLE: No plan mode needed
        decision['plan_mode_required'] = False
        decision['reasoning'] = 'Task is straightforward, direct execution is efficient'
        decision['auto_enter'] = False

    elif score < 10:
        # MODERATE: Optional, ask user
        decision['plan_mode_optional'] = True
        decision['should_ask_user'] = True
        decision['reasoning'] = 'Task has moderate complexity, planning may help but not critical'
        decision['benefits'] = [
            'Clearer implementation strategy',
            'Upfront identification of potential issues'
        ]

    elif score < 20:
        # COMPLEX: Strongly recommended
        decision['plan_mode_recommended'] = True
        decision['should_ask_user'] = True
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
        # VERY COMPLEX: Mandatory
        decision['plan_mode_required'] = True
        decision['auto_enter'] = True
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


def format_suggestion(decision: Dict, complexity: Dict) -> str:
    """
    Format the suggestion message for user
    """
    score = decision['score']
    level = decision['level']

    output = f"""
{'='*80}
📊 COMPLEXITY ANALYSIS
{'='*80}

Score: {score} ({level})
Tasks: {complexity.get('estimated_tasks', 'Unknown')}
Files: {len(complexity.get('files_to_create', [])) + len(complexity.get('files_to_modify', []))}
Phases: {len(complexity.get('phases', []))}

"""

    if decision['auto_enter']:
        # VERY COMPLEX - Auto-enter
        output += f"""
🔴 PLAN MODE: REQUIRED (MANDATORY)
{'='*80}

{decision['reasoning']}

Why this is mandatory:
"""
        for risk in decision['risks_without_planning']:
            output += f"\n{risk}"

        output += f"""

I will now enter plan mode to create a detailed implementation plan.
This will ensure we approach this correctly and avoid costly mistakes.

Entering plan mode...
"""

    elif decision['plan_mode_recommended']:
        # COMPLEX - Strongly recommended
        output += f"""
✅ PLAN MODE: STRONGLY RECOMMENDED
{'='*80}

{decision['reasoning']}

Benefits of planning:
"""
        for benefit in decision['benefits']:
            output += f"\n✅ {benefit}"

        output += "\n\nRisks without planning:"
        for risk in decision['risks_without_planning']:
            output += f"\n⚠️ {risk}"

        output += """

Would you like me to enter plan mode? (Recommended: Yes)
- Yes: I'll create a detailed plan for your approval
- No: I'll proceed directly (higher risk)

Your choice?
"""

    elif decision['plan_mode_optional']:
        # MODERATE - Optional
        output += f"""
⚠️ PLAN MODE: OPTIONAL
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

Your choice? (1 = Direct, 2 = Plan)
"""

    else:
        # SIMPLE - No plan mode
        output += f"""
✅ NO PLAN MODE NEEDED
{'='*80}

{decision['reasoning']}

Proceeding directly to execution...
"""

    output += f"\n{'='*80}\n"

    return output
```

---

## 🎯 INTEGRATION WITH EnterPlanMode

### **Automatic Triggering:**

```python
def execute_plan_mode_decision(decision: Dict, complexity: Dict):
    """
    Execute the plan mode decision
    """
    if decision['auto_enter']:
        # VERY COMPLEX: Auto-enter plan mode
        print("🔴 Entering plan mode automatically...")

        # Call EnterPlanMode tool
        result = EnterPlanMode()

        # Claude will now be in plan mode
        # Follow plan mode workflow
        return result

    elif decision['should_ask_user']:
        # MODERATE/COMPLEX: Ask user
        message = format_suggestion(decision, complexity)
        print(message)

        # Wait for user response
        # If user says yes, call EnterPlanMode
        # If user says no, proceed to execution

    else:
        # SIMPLE: Proceed directly
        print("✅ Proceeding directly to execution...")
        # Continue to Step 3 (Model Selection)
```

---

## 📊 RISK ASSESSMENT

### **Additional Factors to Consider:**

```python
def calculate_risk_factors(structured_prompt: Dict, complexity: Dict) -> Dict:
    """
    Calculate additional risk factors beyond complexity score
    """
    risks = {
        'score': 0,
        'factors': []
    }

    # Factor 1: Multi-service impact
    if 'multiple services' in str(structured_prompt).lower():
        risks['score'] += 5
        risks['factors'].append('Multi-service impact detected')

    # Factor 2: Database changes
    if any(kw in str(structured_prompt).lower() for kw in ['database', 'migration', 'schema']):
        risks['score'] += 5
        risks['factors'].append('Database changes involved')

    # Factor 3: Security/Auth
    if any(kw in str(structured_prompt).lower() for kw in ['auth', 'security', 'jwt', 'permission']):
        risks['score'] += 3
        risks['factors'].append('Security-critical changes')

    # Factor 4: External integrations
    if any(kw in str(structured_prompt).lower() for kw in ['integration', 'api call', 'external']):
        risks['score'] += 3
        risks['factors'].append('External integration complexity')

    # Factor 5: No similar examples found
    if not structured_prompt.get('examples_from_codebase'):
        risks['score'] += 4
        risks['factors'].append('No similar examples in codebase')

    # Factor 6: Uncertainties flagged
    if structured_prompt.get('uncertainties'):
        risks['score'] += 2
        risks['factors'].append('Uncertainties identified in requirements')

    return risks


def adjust_complexity_with_risks(complexity: Dict, risks: Dict) -> Dict:
    """
    Adjust complexity score based on additional risk factors
    """
    original_score = complexity['score']
    risk_score = risks['score']
    adjusted_score = original_score + risk_score

    complexity['original_score'] = original_score
    complexity['risk_adjustment'] = risk_score
    complexity['score'] = adjusted_score
    complexity['level'] = get_complexity_level(adjusted_score)
    complexity['risk_factors'] = risks['factors']

    return complexity
```

---

## 🎯 COMPLETE DECISION FLOW

```
Task Breakdown Complete
    ↓
Calculate Base Complexity Score
    ↓
Assess Additional Risk Factors
    ↓
Adjust Complexity Score
    ↓
┌─────────────────────────────────────┐
│  Score < 5 (SIMPLE)                 │
│  ❌ No plan mode                    │
│  ✅ Proceed to execution            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Score 5-9 (MODERATE)               │
│  ⚠️ Ask user preference             │
│  Option 1: Direct execution         │
│  Option 2: Plan mode                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Score 10-19 (COMPLEX)              │
│  ✅ Strongly recommend plan mode    │
│  Show benefits & risks              │
│  Ask user approval                  │
│  - Yes → EnterPlanMode              │
│  - No → Warn + Proceed              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Score 20+ (VERY COMPLEX)           │
│  🔴 MANDATORY plan mode             │
│  Auto-call EnterPlanMode            │
│  No option to skip                  │
└─────────────────────────────────────┘
```

---

## 📝 EXAMPLE OUTPUTS

### **Example 1: SIMPLE Task**

```
User: "Add a constant to UserRole enum"

Step 0: Prompt Generation ✅
Step 1: Task Breakdown ✅
    Score: 2 (SIMPLE)
    Tasks: 1
    Files: 1

Step 2: Plan Mode Suggestion
────────────────────────────────────────────
📊 COMPLEXITY ANALYSIS

Score: 2 (SIMPLE)
Tasks: 1
Files: 1
Phases: 0

✅ NO PLAN MODE NEEDED
────────────────────────────────────────────

This task is straightforward, direct execution
is efficient.

Proceeding directly to execution...

Step 3: Model Selection → Haiku (simple task)
Step 4: Execution...
```

---

### **Example 2: MODERATE Task**

```
User: "Create Product entity with repository"

Step 0: Prompt Generation ✅
Step 1: Task Breakdown ✅
    Score: 7 (MODERATE)
    Tasks: 4
    Files: 3

Step 2: Plan Mode Suggestion
────────────────────────────────────────────
📊 COMPLEXITY ANALYSIS

Score: 7 (MODERATE)
Tasks: 4
Files: 3 (Product.java, ProductRepository.java, ProductDto.java)
Phases: 2

⚠️ PLAN MODE: OPTIONAL
────────────────────────────────────────────

Task has moderate complexity, planning may help
but not critical.

Option 1 (Recommended): Proceed directly
- Can execute using standard patterns from UserService
- Estimated time: 5 minutes
- Risk: Low

Option 2: Enter plan mode
- Create detailed implementation plan
- Review approach first
- Estimated time: +5 minutes for planning

Your choice? (1 = Direct, 2 = Plan)
```

---

### **Example 3: COMPLEX Task**

```
User: "Create complete Product API with CRUD and validation"

Step 0: Prompt Generation ✅
Step 1: Task Breakdown ✅
    Base Score: 15
    Risk Factors:
    - Multi-file creation (7 files)
    - Complex validation logic
    Adjusted Score: 18 (COMPLEX)

Step 2: Plan Mode Suggestion
────────────────────────────────────────────
📊 COMPLEXITY ANALYSIS

Score: 18 (COMPLEX)
Tasks: 13
Files: 7
Phases: 4
Risk Factors:
  - Complex validation logic
  - Multi-file dependencies

✅ PLAN MODE: STRONGLY RECOMMENDED
────────────────────────────────────────────

Task complexity warrants upfront planning.

Benefits of planning:
✅ Design implementation strategy before coding
✅ Identify architectural issues early
✅ Ensure alignment with existing patterns
✅ Reduce risk of rework
✅ Better quality outcome

Risks without planning:
⚠️ May choose suboptimal validation approach
⚠️ Could miss important dependencies
⚠️ Higher chance of rework
⚠️ Potential architectural misalignment

Would you like me to enter plan mode? (Recommended: Yes)
- Yes: I'll create a detailed plan for your approval
- No: I'll proceed directly (higher risk)

Your choice?
```

---

### **Example 4: VERY COMPLEX Task**

```
User: "Implement JWT authentication across all services with role-based access control"

Step 0: Prompt Generation ✅
Step 1: Task Breakdown ✅
    Base Score: 22
    Risk Factors:
    - Multi-service impact (+5)
    - Security-critical (+3)
    - No similar examples (+4)
    Adjusted Score: 34 (VERY COMPLEX)

Step 2: Plan Mode Suggestion
────────────────────────────────────────────
📊 COMPLEXITY ANALYSIS

Score: 34 (VERY COMPLEX)
Tasks: 25+
Files: 15+
Phases: 6
Services Affected: 4 (auth, user, product, gateway)

Risk Factors:
  ⚠️ Multi-service impact detected
  ⚠️ Security-critical changes
  ⚠️ No similar examples in codebase

🔴 PLAN MODE: REQUIRED (MANDATORY)
────────────────────────────────────────────

Task is too complex to execute safely without
planning.

Why this is mandatory:
🔴 HIGH: Wrong architectural decisions possible
🔴 HIGH: Missed critical security considerations
🔴 HIGH: Breaking changes to all services
🔴 HIGH: Major rework risk
🔴 HIGH: Potential production security issues

I will now enter plan mode to create a detailed
implementation plan. This will ensure we:
1. Design secure authentication architecture
2. Identify all cross-service impacts
3. Plan migration strategy for existing services
4. Create rollback plan
5. Review security best practices

Entering plan mode automatically...
────────────────────────────────────────────

[EnterPlanMode tool called]

I'm now in plan mode. I'll explore the codebase
thoroughly and design the implementation approach.
```

---

## 🔧 IMPLEMENTATION SCRIPT

**File:** `~/.claude/memory/auto-plan-mode-suggester.py`

```python
#!/usr/bin/env python3
"""
Automatic Plan Mode Suggestion
Based on complexity analysis
"""

import json
from typing import Dict


def should_use_plan_mode(complexity_analysis: Dict, structured_prompt: Dict) -> Dict:
    """
    Main function: Determine if plan mode should be used
    """
    # Calculate base complexity
    score = complexity_analysis.get('score', 0)

    # Calculate additional risks
    risks = calculate_risk_factors(structured_prompt, complexity_analysis)

    # Adjust complexity score
    adjusted_complexity = adjust_complexity_with_risks(complexity_analysis, risks)

    # Make decision
    decision = make_decision(adjusted_complexity)

    return decision


def main():
    """CLI interface"""
    import sys
    import yaml

    if len(sys.argv) < 3:
        print("Usage: python auto-plan-mode-suggester.py complexity.json prompt.yaml")
        sys.exit(1)

    # Load inputs
    with open(sys.argv[1], 'r') as f:
        complexity = json.load(f)

    with open(sys.argv[2], 'r') as f:
        prompt = yaml.safe_load(f)

    # Make decision
    decision = should_use_plan_mode(complexity, prompt)

    # Output
    message = format_suggestion(decision, complexity)
    print(message)

    # Return decision as JSON
    print("\nDECISION:")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
```

---

## 📊 METRICS & LEARNING

### **Track Decision Accuracy:**

```python
# After task completion, evaluate if plan mode decision was correct

def evaluate_plan_mode_decision(
    decision: Dict,
    actual_outcome: Dict
) -> Dict:
    """
    Evaluate if the plan mode decision was correct
    """
    evaluation = {
        'decision_was_correct': False,
        'reasoning': ''
    }

    used_plan_mode = actual_outcome.get('used_plan_mode', False)
    had_rework = actual_outcome.get('had_rework', False)
    had_architectural_issues = actual_outcome.get('had_architectural_issues', False)

    if decision['auto_enter'] and used_plan_mode:
        # Required plan mode and used it
        if not had_rework and not had_architectural_issues:
            evaluation['decision_was_correct'] = True
            evaluation['reasoning'] = 'Plan mode prevented issues'
        else:
            evaluation['decision_was_correct'] = True
            evaluation['reasoning'] = 'Plan mode identified issues early'

    elif decision['plan_mode_recommended'] and not used_plan_mode:
        # Recommended but user skipped
        if had_rework or had_architectural_issues:
            evaluation['decision_was_correct'] = True
            evaluation['reasoning'] = 'Recommendation was correct, issues occurred'
        else:
            evaluation['decision_was_correct'] = False
            evaluation['reasoning'] = 'Task was simpler than estimated'

    return evaluation
```

---

**VERSION:** 1.0.0
**CREATED:** 2026-02-16
**LOCATION:** `~/.claude/memory/auto-plan-mode-suggestion-policy.md`
**SCRIPT:** `~/.claude/memory/auto-plan-mode-suggester.py`
