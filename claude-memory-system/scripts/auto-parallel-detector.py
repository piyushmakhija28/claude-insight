#!/usr/bin/env python3
"""
Auto Parallel Detector
Automatically detects if parallel execution should be used
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple


def analyze_tasks_for_parallelization(tasks: List[Dict]) -> List[List[Dict]]:
    """Analyze tasks and group them for parallel execution."""
    from parallel_task_analyzer import analyze_tasks_for_parallelization as analyze

    return analyze(tasks)


def should_use_parallel_execution(tasks: List[Dict]) -> Tuple[bool, str, float]:
    """
    Automatically detect if parallel execution should be used.

    Returns:
        (should_use: bool, reason: str, estimated_speedup: float)
    """

    # Check task count
    if len(tasks) < 3:
        return False, "Less than 3 tasks", 1.0

    # Import analyzer
    sys.path.insert(0, str(Path.home() / ".claude/memory/scripts"))
    from parallel_task_analyzer import analyze_tasks_for_parallelization

    # Analyze dependencies
    parallel_groups = analyze_tasks_for_parallelization(tasks)

    if len(parallel_groups) == 1:
        # All tasks in one group means they can all run in parallel
        if len(parallel_groups[0]) > 1:
            estimated_speedup = len(parallel_groups[0])
            return True, f"All {len(tasks)} tasks can run in parallel", estimated_speedup
        else:
            return False, "All tasks have dependencies", 1.0

    # Calculate speedup
    total_tasks = len(tasks)
    num_groups = len(parallel_groups)
    estimated_speedup = total_tasks / num_groups

    if estimated_speedup < 1.5:
        return False, f"Speedup too low: {estimated_speedup:.1f}x", estimated_speedup

    # Check if same task type (works better in parallel)
    task_types = set(t.get('type', 'unknown') for t in tasks)

    if len(task_types) == 1:
        # Homogeneous tasks - excellent for parallel
        return True, f"Homogeneous tasks ({list(task_types)[0]}), speedup: {estimated_speedup:.1f}x", estimated_speedup

    # Mixed task types - still good if speedup is significant
    if estimated_speedup >= 2.0:
        return True, f"Significant speedup: {estimated_speedup:.1f}x", estimated_speedup

    return False, "Mixed tasks with low speedup", estimated_speedup


def get_parallelization_recommendation(tasks: List[Dict]) -> Dict:
    """
    Get detailed parallelization recommendation.

    Returns:
        Recommendation dict with decision, reason, metrics, and groups
    """

    should_use, reason, speedup = should_use_parallel_execution(tasks)

    # Import analyzer
    sys.path.insert(0, str(Path.home() / ".claude/memory/scripts"))
    from parallel_task_analyzer import analyze_tasks_for_parallelization

    # Analyze task groups
    parallel_groups = analyze_tasks_for_parallelization(tasks)

    # Calculate metrics
    total_tasks = len(tasks)
    num_groups = len(parallel_groups)
    max_parallel = max(len(group) for group in parallel_groups) if parallel_groups else 0

    # Task type distribution
    task_types = {}
    for task in tasks:
        task_type = task.get('type', 'unknown')
        task_types[task_type] = task_types.get(task_type, 0) + 1

    return {
        "should_use_parallel": should_use,
        "reason": reason,
        "estimated_speedup": round(speedup, 2),
        "metrics": {
            "total_tasks": total_tasks,
            "parallel_groups": num_groups,
            "max_parallel_tasks": max_parallel,
            "task_types": task_types
        },
        "groups": [
            {
                "group_id": i + 1,
                "task_count": len(group),
                "tasks": [task['id'] for task in group]
            }
            for i, group in enumerate(parallel_groups)
        ]
    }


def print_recommendation(recommendation: Dict):
    """Print recommendation in formatted way."""

    print()
    print("=" * 80)
    print("⚡ PARALLEL EXECUTION RECOMMENDATION")
    print("=" * 80)
    print()

    should_use = recommendation["should_use_parallel"]
    reason = recommendation["reason"]
    speedup = recommendation["estimated_speedup"]

    if should_use:
        print(f"✅ RECOMMENDATION: Use Parallel Execution")
        print(f"   Reason: {reason}")
        print(f"   Estimated Speedup: {speedup}x")
    else:
        print(f"❌ RECOMMENDATION: Use Sequential Execution")
        print(f"   Reason: {reason}")

    print()

    # Print metrics
    metrics = recommendation["metrics"]
    print(f"📊 METRICS:")
    print(f"   Total Tasks:         {metrics['total_tasks']}")
    print(f"   Parallel Groups:     {metrics['parallel_groups']}")
    print(f"   Max Parallel Tasks:  {metrics['max_parallel_tasks']}")
    print()

    # Print task type distribution
    print(f"📋 TASK TYPE DISTRIBUTION:")
    for task_type, count in metrics['task_types'].items():
        print(f"   {task_type}: {count}")
    print()

    # Print groups
    if should_use:
        print(f"🔀 PARALLEL GROUPS:")
        for group in recommendation['groups']:
            group_id = group['group_id']
            task_count = group['task_count']
            tasks = group['tasks']

            print(f"   Group {group_id} ({task_count} task{'s' if task_count > 1 else ''}):")
            for task_id in tasks:
                print(f"     - {task_id}")
        print()

    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Detect parallel execution opportunities")
    parser.add_argument("--tasks-file", required=True, help="JSON file with tasks")
    parser.add_argument("--output", help="Output file for recommendation")
    parser.add_argument("--json", action="store_true", help="Output JSON only")

    args = parser.parse_args()

    try:
        # Load tasks
        with open(args.tasks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both list and dict input
        if isinstance(data, dict):
            tasks = data.get('tasks', [])
        else:
            tasks = data

        # Get recommendation
        recommendation = get_parallelization_recommendation(tasks)

        # Save if output specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(recommendation, f, indent=2)

            print(f"✅ Recommendation saved to: {args.output}")

        # Output
        if args.json:
            print(json.dumps(recommendation, indent=2))
        else:
            print_recommendation(recommendation)

        # Exit code based on recommendation
        sys.exit(0 if recommendation["should_use_parallel"] else 1)

    except FileNotFoundError:
        print(f"❌ Error: Tasks file not found: {args.tasks_file}", file=sys.stderr)
        sys.exit(2)

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in tasks file: {str(e)}", file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(2)
