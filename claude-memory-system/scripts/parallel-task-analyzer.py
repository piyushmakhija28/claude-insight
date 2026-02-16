#!/usr/bin/env python3
"""
Parallel Task Analyzer
Analyzes tasks and identifies parallelization opportunities
"""

import json
import sys
from typing import List, Dict
from pathlib import Path


def build_dependency_graph(tasks: List[Dict]) -> Dict:
    """Build dependency graph from tasks."""
    graph = {}

    for task in tasks:
        task_id = task['id']
        dependencies = task.get('blockedBy', [])
        graph[task_id] = dependencies

    return graph


def has_dependencies(task: Dict, current_group: List[Dict]) -> bool:
    """Check if task has dependencies on tasks in current group."""
    task_deps = set(task.get('blockedBy', []))
    group_ids = set(t['id'] for t in current_group)

    return bool(task_deps & group_ids)


def topological_sort(tasks: List[Dict]) -> List[Dict]:
    """Topologically sort tasks by dependencies."""
    graph = build_dependency_graph(tasks)
    task_map = {t['id']: t for t in tasks}

    visited = set()
    result = []

    def visit(task_id):
        if task_id in visited:
            return

        visited.add(task_id)

        # Visit dependencies first
        for dep in graph.get(task_id, []):
            if dep in task_map:
                visit(dep)

        if task_id in task_map:
            result.append(task_map[task_id])

    for task in tasks:
        visit(task['id'])

    return result


def analyze_tasks_for_parallelization(tasks: List[Dict]) -> List[List[Dict]]:
    """
    Analyze tasks and group them for parallel execution.

    Returns:
        List of task groups, where each group can run in parallel
    """

    if not tasks:
        return []

    # Sort tasks by dependencies (topological sort)
    sorted_tasks = topological_sort(tasks)

    # Group tasks by wave (tasks with no dependencies on each other)
    parallel_groups = []
    current_group = []
    completed_tasks = set()

    for task in sorted_tasks:
        task_deps = set(task.get('blockedBy', []))

        # Can this task run with current group?
        if task_deps.issubset(completed_tasks):
            # Check if it depends on any task in current group
            current_group_ids = set(t['id'] for t in current_group)

            if not task_deps & current_group_ids:
                # No dependency on current group - can run in parallel
                current_group.append(task)
            else:
                # Depends on current group - start new group
                if current_group:
                    parallel_groups.append(current_group)
                    completed_tasks.update(t['id'] for t in current_group)
                current_group = [task]
        else:
            # Dependencies not met - start new group
            if current_group:
                parallel_groups.append(current_group)
                completed_tasks.update(t['id'] for t in current_group)
            current_group = [task]

    # Add last group
    if current_group:
        parallel_groups.append(current_group)

    return parallel_groups


def analyze_and_save(tasks_file: str, output_file: str = None):
    """Analyze tasks and save results."""

    # Load tasks
    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    # Handle both list and dict input
    if isinstance(tasks, dict):
        tasks = tasks.get('tasks', [])

    # Analyze
    parallel_groups = analyze_tasks_for_parallelization(tasks)

    # Calculate metrics
    total_tasks = len(tasks)
    num_groups = len(parallel_groups)
    estimated_speedup = total_tasks / num_groups if num_groups > 0 else 1.0

    # Prepare results
    results = {
        "total_tasks": total_tasks,
        "parallel_groups": num_groups,
        "estimated_speedup": round(estimated_speedup, 2),
        "groups": [
            {
                "group_id": i + 1,
                "tasks_count": len(group),
                "tasks": [
                    {
                        "id": task['id'],
                        "subject": task.get('subject', 'No subject'),
                        "type": task.get('type', 'unknown')
                    }
                    for task in group
                ]
            }
            for i, group in enumerate(parallel_groups)
        ]
    }

    # Save results if output file specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        print(f"✅ Analysis saved to: {output_file}")

    return results


def print_analysis_results(results: Dict):
    """Print analysis results in a formatted way."""

    print()
    print("=" * 80)
    print("📊 PARALLEL TASK ANALYSIS RESULTS")
    print("=" * 80)
    print()
    print(f"Total tasks:         {results['total_tasks']}")
    print(f"Parallel groups:     {results['parallel_groups']}")
    print(f"Estimated speedup:   {results['estimated_speedup']}x")
    print()

    for group_info in results['groups']:
        group_id = group_info['group_id']
        tasks_count = group_info['tasks_count']

        print(f"Group {group_id} ({tasks_count} task{'s' if tasks_count > 1 else ''} in parallel):")

        for task_info in group_info['tasks']:
            task_id = task_info['id']
            subject = task_info['subject']
            task_type = task_info['type']

            print(f"  - Task {task_id}: {subject} [{task_type}]")

        print()

    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze tasks for parallelization")
    parser.add_argument("--tasks-file", required=True, help="JSON file with tasks")
    parser.add_argument("--output", help="Output file for analysis results")
    parser.add_argument("--json", action="store_true", help="Output JSON only")

    args = parser.parse_args()

    try:
        # Analyze
        results = analyze_and_save(args.tasks_file, args.output)

        # Output
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_analysis_results(results)

        sys.exit(0)

    except FileNotFoundError:
        print(f"❌ Error: Tasks file not found: {args.tasks_file}", file=sys.stderr)
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in tasks file: {str(e)}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
