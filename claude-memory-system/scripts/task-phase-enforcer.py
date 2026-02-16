#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task & Phase Enforcement Script
Validates compliance with task/phase breakdown requirements
"""

import sys
import os
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def log_policy_hit(action, context):
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] task-phase-enforcer | {action} | {context}\n"
    
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception:
        pass

def calculate_complexity_score(task_desc):
    score = 0
    requirements_keywords = ['and', 'also', 'plus', 'additionally', 'all']
    req_count = sum(1 for kw in requirements_keywords if kw in task_desc.lower())
    score += min(3, req_count)
    
    domains = ['backend', 'frontend', 'database', 'api', 'ui', 'docker', 'kubernetes']
    domain_count = sum(1 for domain in domains if domain in task_desc.lower())
    score += min(2, domain_count)
    
    file_keywords = ['update', 'create', 'modify', 'edit', 'change', 'fix', 'add']
    if any(kw in task_desc.lower() for kw in file_keywords):
        score += 2
    
    multi_keywords = ['all', 'every', 'each', 'multiple', 'several']
    if any(kw in task_desc.lower() for kw in multi_keywords):
        score += 2
    
    complex_keywords = ['comprehensive', 'complete', 'full', 'entire', 'complex']
    if any(kw in task_desc.lower() for kw in complex_keywords):
        score += 1
    
    return min(10, score)

def calculate_size_score(task_desc):
    score = 0
    word_count = len(task_desc.split())
    if word_count > 20:
        score += 3
    elif word_count > 10:
        score += 2
    elif word_count > 5:
        score += 1
    
    multi_indicators = ['all', 'every', 'each', '10', 'multiple', 'several']
    if any(ind in task_desc.lower() for ind in multi_indicators):
        score += 3
    
    return min(10, score)

def analyze_task(task_desc):
    print("\n" + "="*70)
    print("TASK/PHASE ENFORCEMENT CHECK")
    print("="*70 + "\n")
    
    print(f"Request: {task_desc}\n")
    
    complexity = calculate_complexity_score(task_desc)
    size = calculate_size_score(task_desc)
    
    print("Analysis:")
    print(f"  Complexity Score: {complexity}/10")
    print(f"  Size Score: {size}/10\n")
    
    needs_task = complexity >= 3
    needs_phases = size >= 6
    
    print("Requirements:")
    print(f"  TaskCreate: {'REQUIRED' if needs_task else 'Optional'}")
    print(f"  Phased Execution: {'REQUIRED' if needs_phases else 'Optional'}")
    print()
    
    if not needs_task and not needs_phases:
        print("Status: ✅ COMPLIANT - Can proceed")
        log_policy_hit("compliant", f"task={task_desc[:50]}")
        return 0
    else:
        print("Status: ⚠️  REQUIREMENTS DETECTED")
        if needs_task:
            print("  → Must use TaskCreate before starting")
        if needs_phases:
            print("  → Must define phases (score >= 6)")
        log_policy_hit("requirements-detected", f"task={task_desc[:50]}")
        return 0
    
    print("="*70 + "\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Task/Phase enforcement")
    parser.add_argument('--analyze', type=str, help='Analyze task description')
    args = parser.parse_args()
    
    if args.analyze:
        return analyze_task(args.analyze)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
