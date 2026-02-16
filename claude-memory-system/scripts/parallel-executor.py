#!/usr/bin/env python3
"""
Parallel Task Executor
Executes multiple tasks in parallel using subagents
"""

import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


def execute_task_with_subagent(task_id, subagent_type, prompt, background=False):
    """Execute a single task using a subagent."""

    # Prepare task execution
    task_start = datetime.now()

    print(f"🚀 Launching Task {task_id} with {subagent_type} agent...")

    # Build subagent command (Note: This is a placeholder - actual implementation
    # would use Claude Code's Task tool)
    cmd = [
        "python",
        str(Path.home() / ".claude/memory/scripts/mock-subagent-executor.py"),
        f"--task-id={task_id}",
        f"--subagent={subagent_type}",
        f"--prompt={prompt}"
    ]

    if background:
        cmd.append("--background")

    try:
        # Execute
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        task_end = datetime.now()
        duration = (task_end - task_start).total_seconds()

        # Save result
        result_data = {
            "task_id": task_id,
            "subagent": subagent_type,
            "status": "success" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "duration": duration,
            "start_time": task_start.isoformat(),
            "end_time": task_end.isoformat()
        }

        # Save to file
        result_file = Path.home() / ".claude/memory/temp/parallel-results" / f"{task_id}.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)

        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        if result.returncode == 0:
            print(f"✅ Task {task_id} completed in {duration:.1f}s")
        else:
            print(f"❌ Task {task_id} failed after {duration:.1f}s")

        return result.returncode

    except subprocess.TimeoutExpired:
        print(f"⏱️ Task {task_id} timed out after 10 minutes")
        return 1

    except Exception as e:
        print(f"❌ Task {task_id} error: {str(e)}")
        return 1


def execute_parallel_tasks(tasks):
    """Execute multiple tasks in parallel."""
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {
            executor.submit(
                execute_task_with_subagent,
                task['id'],
                task.get('subagent_type', 'general-purpose'),
                task.get('prompt', ''),
                task.get('background', False)
            ): task
            for task in tasks
        }

        results = {}
        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            try:
                exit_code = future.result()
                results[task['id']] = exit_code
            except Exception as e:
                print(f"❌ Task {task['id']} raised exception: {str(e)}")
                results[task['id']] = 1

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute task with subagent")
    parser.add_argument("--task-id", required=True, help="Task ID")
    parser.add_argument("--subagent", required=True, help="Subagent type")
    parser.add_argument("--prompt", required=True, help="Task prompt")
    parser.add_argument("--background", action="store_true", help="Run in background")

    args = parser.parse_args()

    exit_code = execute_task_with_subagent(
        args.task_id,
        args.subagent,
        args.prompt,
        args.background
    )

    sys.exit(exit_code)
