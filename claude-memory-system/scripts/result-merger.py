#!/usr/bin/env python3
"""
Result Merger
Intelligently merges results from parallel task executions
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def load_result(task_id: str) -> Dict:
    """Load result for a single task."""
    result_file = Path.home() / ".claude/memory/temp/parallel-results" / f"{task_id}.json"

    if result_file.exists():
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    return {"status": "failed", "error": "No result file found"}


def collect_parallel_results(task_ids: List[str]) -> Dict[str, Dict]:
    """Collect results from all parallel tasks."""
    return {task_id: load_result(task_id) for task_id in task_ids}


def merge_service_creation_results(results: Dict[str, Dict]) -> Dict:
    """Merge results from creating multiple services."""

    all_succeeded = all(r.get("status") == "success" for r in results.values())

    created_services = []
    created_files = []
    errors = []

    for task_id, result in results.items():
        if result.get("status") == "success":
            service_name = result.get("service_name", task_id)
            created_services.append(service_name)

            files = result.get("files", [])
            created_files.extend(files)
        else:
            errors.append({
                "task_id": task_id,
                "error": result.get("error", "Unknown error")
            })

    return {
        "status": "success" if all_succeeded else "partial",
        "merge_strategy": "service_creation",
        "created_services": created_services,
        "created_files": created_files,
        "total_services": len(created_services),
        "total_files": len(created_files),
        "errors": errors if errors else None
    }


def merge_file_read_results(results: Dict[str, Dict]) -> Dict:
    """Merge results from reading multiple files."""

    file_contents = {}
    errors = []

    for task_id, result in results.items():
        if result.get("status") == "success":
            file_path = result.get("file_path", task_id)
            content = result.get("content", "")
            file_contents[file_path] = content
        else:
            errors.append({
                "task_id": task_id,
                "error": result.get("error", "Unknown error")
            })

    return {
        "status": "success" if not errors else "partial",
        "merge_strategy": "file_read",
        "files": file_contents,
        "total_files": len(file_contents),
        "errors": errors if errors else None
    }


def merge_search_results(results: Dict[str, Dict]) -> Dict:
    """Merge results from multiple searches with deduplication."""

    all_matches = []
    seen = set()
    errors = []

    for task_id, result in results.items():
        if result.get("status") == "success":
            matches = result.get("matches", [])

            for match in matches:
                match_key = f"{match.get('file')}:{match.get('line')}"

                if match_key not in seen:
                    all_matches.append(match)
                    seen.add(match_key)
        else:
            errors.append({
                "task_id": task_id,
                "error": result.get("error", "Unknown error")
            })

    # Sort by relevance (if available)
    all_matches.sort(key=lambda m: m.get("relevance", 0), reverse=True)

    return {
        "status": "success" if not errors else "partial",
        "merge_strategy": "search",
        "matches": all_matches,
        "total_matches": len(all_matches),
        "unique_matches": len(seen),
        "errors": errors if errors else None
    }


def merge_test_results(results: Dict[str, Dict]) -> Dict:
    """Merge results from running tests across multiple services."""

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    test_details = []
    errors = []

    for task_id, result in results.items():
        if result.get("status") == "success":
            service_tests = result.get("test_count", 0)
            service_passed = result.get("passed", 0)
            service_failed = result.get("failed", 0)

            total_tests += service_tests
            passed_tests += service_passed
            failed_tests += service_failed

            test_details.append({
                "service": result.get("service_name", task_id),
                "tests": service_tests,
                "passed": service_passed,
                "failed": service_failed
            })
        else:
            errors.append({
                "task_id": task_id,
                "error": result.get("error", "Unknown error")
            })

    all_passed = failed_tests == 0
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    return {
        "status": "success" if all_passed and not errors else "failed",
        "merge_strategy": "test",
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "pass_rate": f"{pass_rate:.1f}%",
        "details": test_details,
        "errors": errors if errors else None
    }


def merge_build_results(results: Dict[str, Dict]) -> Dict:
    """Merge results from building multiple services."""

    all_succeeded = all(r.get("status") == "success" for r in results.values())

    built_services = []
    artifacts = []
    errors = []

    for task_id, result in results.items():
        if result.get("status") == "success":
            service_name = result.get("service_name", task_id)
            built_services.append(service_name)

            artifact_path = result.get("artifact_path")
            if artifact_path:
                artifacts.append(artifact_path)
        else:
            errors.append({
                "task_id": task_id,
                "error": result.get("error", "Unknown error")
            })

    return {
        "status": "success" if all_succeeded else "failed",
        "merge_strategy": "build",
        "built_services": built_services,
        "artifacts": artifacts,
        "total_services": len(built_services),
        "errors": errors if errors else None
    }


def merge_deployment_results(results: Dict[str, Dict]) -> Dict:
    """Merge results from deploying multiple services."""

    all_succeeded = all(r.get("status") == "success" for r in results.values())

    deployed_services = []
    endpoints = []
    errors = []

    for task_id, result in results.items():
        if result.get("status") == "success":
            service_name = result.get("service_name", task_id)
            deployed_services.append(service_name)

            endpoint = result.get("endpoint")
            if endpoint:
                endpoints.append({
                    "service": service_name,
                    "endpoint": endpoint
                })
        else:
            errors.append({
                "task_id": task_id,
                "error": result.get("error", "Unknown error")
            })

    return {
        "status": "success" if all_succeeded else "failed",
        "merge_strategy": "deployment",
        "deployed_services": deployed_services,
        "endpoints": endpoints,
        "total_services": len(deployed_services),
        "errors": errors if errors else None
    }


def determine_merge_strategy(tasks: List[Dict]) -> str:
    """Determine the appropriate merge strategy based on task types."""

    if not tasks:
        return "default"

    # Get most common task type
    task_types = [task.get("type", "unknown") for task in tasks]
    most_common = max(set(task_types), key=task_types.count)

    # Map task type to merge strategy
    strategy_map = {
        "service_creation": "service_creation",
        "file_read": "file_read",
        "search": "search",
        "testing": "test",
        "build": "build",
        "deployment": "deployment"
    }

    return strategy_map.get(most_common, "default")


def merge_parallel_results(results: Dict[str, Dict], merge_strategy: str) -> Dict:
    """
    Merge results from parallel executions.

    Args:
        results: Dict mapping task_id to result
        merge_strategy: How to merge results

    Returns:
        merged_result: Combined result
    """

    if merge_strategy == "service_creation":
        return merge_service_creation_results(results)

    elif merge_strategy == "file_read":
        return merge_file_read_results(results)

    elif merge_strategy == "search":
        return merge_search_results(results)

    elif merge_strategy == "test":
        return merge_test_results(results)

    elif merge_strategy == "build":
        return merge_build_results(results)

    elif merge_strategy == "deployment":
        return merge_deployment_results(results)

    else:
        # Default: simple aggregation
        all_succeeded = all(r.get("status") == "success" for r in results.values())

        return {
            "status": "success" if all_succeeded else "partial",
            "merge_strategy": "default",
            "task_count": len(results),
            "results": results
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Merge parallel execution results")
    parser.add_argument("--task-ids", nargs='+', required=True, help="Task IDs to merge")
    parser.add_argument("--strategy", help="Merge strategy (auto-detected if not specified)")
    parser.add_argument("--output", help="Output file for merged results")

    args = parser.parse_args()

    # Collect results
    results = collect_parallel_results(args.task_ids)

    # Determine strategy if not specified
    if not args.strategy:
        # Try to load task definitions to determine strategy
        # For now, use default
        strategy = "default"
    else:
        strategy = args.strategy

    # Merge
    merged = merge_parallel_results(results, strategy)

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2)

        print(f"✅ Merged results saved to: {args.output}")
    else:
        print(json.dumps(merged, indent=2))
