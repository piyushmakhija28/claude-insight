#!/usr/bin/env python3
"""
Refactoring script: Move Prompt Generation from 3.0 to 3.5 (after Skill Selection)

This script:
1. Keeps prompt computation early
2. Moves prompt step to trace AFTER skill selection
3. Renumbers all steps: 3.1→3.0, 3.2→3.1, etc.
4. Updates all dependencies and print statements
"""

import re
import json

def refactor_flow():
    # Read the original file
    with open('scripts/3-level-flow.py', 'r') as f:
        content = f.read()

    # Step 1: Extract prompt generation step from trace (lines 1455-1491)
    # Find and extract the entire trace.append() for LEVEL_3_STEP_3_0
    pattern_3_0 = r'trace\["pipeline"\]\.append\(\{\s*"step": "LEVEL_3_STEP_3_0".*?"passed_to_next":.*?\}\s*\}\)\s*print\(f"   \[3\.0\]'

    # This is complex - let's use a line-by-line approach instead
    lines = content.split('\n')

    # Find indices
    idx_prompt_start = None
    idx_prompt_end = None
    idx_task_start = None
    idx_skills_end = None
    idx_tool_start = None

    for i, line in enumerate(lines):
        if '"step": "LEVEL_3_STEP_3_0"' in line and 'Prompt Generation' in lines[i+1]:
            idx_prompt_start = i - 2  # Include the comment
        if idx_prompt_start and 'prev_output = {"complexity"' in line:
            idx_prompt_end = i
        if '"step": "LEVEL_3_STEP_3_1"' in line and 'Task Breakdown' in lines[i+1]:
            idx_task_start = i - 2
        if '"step": "LEVEL_3_STEP_3_5"' in line and 'Skill' in lines[i+1]:
            for j in range(i, min(i+150, len(lines))):
                if 'supp_str = f"' in lines[j]:
                    idx_skills_end = j + 1
                    break
        if '"step": "LEVEL_3_STEP_3_6"' in line and 'Tool' in lines[i+1]:
            idx_tool_start = i - 2

    print(f"Found indices:")
    print(f"  Prompt: {idx_prompt_start} - {idx_prompt_end}")
    print(f"  Task: {idx_task_start}")
    print(f"  Skills end: {idx_skills_end}")
    print(f"  Tool: {idx_tool_start}")

    if not all([idx_prompt_start, idx_prompt_end, idx_task_start, idx_skills_end, idx_tool_start]):
        print("ERROR: Could not find all required sections!")
        return False

    # Extract sections
    prompt_section = lines[idx_prompt_start:idx_prompt_end+1]
    task_to_skills = lines[idx_task_start:idx_skills_end]
    skills_to_tool = lines[idx_skills_end:idx_tool_start]
    rest = lines[idx_tool_start:]

    # Now we need to:
    # 1. Remove prompt from its original location
    # 2. Renumber 3.1->3.0, 3.2->3.1, etc.
    # 3. Insert prompt after skills (3.5)

    def renumber_step(text, old_num, new_num):
        """Renumber a step from 3.old to 3.new"""
        text = text.replace(f'LEVEL_3_STEP_3_{old_num}', f'LEVEL_3_STEP_3_{new_num}')
        text = text.replace(f'"order": {4+old_num}', f'"order": {4+new_num}')
        text = text.replace(f'[3.{old_num}]', f'[3.{new_num}]')
        return text

    # Start fresh with task section
    new_content = '\n'.join(lines[:idx_task_start])

    # Add task (renumbered as 3.0)
    task_section = '\n'.join(task_to_skills)
    task_section = renumber_step(task_section, 1, 0)
    task_section = task_section.replace('from_previous": "LEVEL_3_STEP_3_0', 'from_previous": "LEVEL_2_STANDARDS')
    new_content += '\n' + task_section

    # Add steps 2-4 (originally 3.2-3.4, now 3.1-3.3)
    for old_num in [2, 3, 4]:
        new_num = old_num - 1
        # (This gets complex, safer to do manually)

    print("\n⚠️ COMPLEX REFACTORING - Doing manually instead")
    return False

if __name__ == '__main__':
    refactor_flow()
