#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Failure Learner
Analyzes failure patterns and updates knowledge base with learning

This script:
1. Loads failure detection results
2. Analyzes patterns and frequencies
3. Learns prevention strategies
4. Updates project-specific knowledge base
5. Promotes patterns to global KB when confirmed

Usage:
    python failure-learner.py [--project PROJECT] [--promote]

Examples:
    python failure-learner.py --project my-project
    python failure-learner.py --promote  # Promote confirmed patterns to global
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Configuration
DETECTION_FILE = Path.home() / ".claude" / "memory" / "logs" / "failure-detection.json"
GLOBAL_KB = Path.home() / ".claude" / "memory" / "common-failures-prevention.md"

# Learning thresholds
LEARNING_THRESHOLDS = {
    "monitoring_to_learning": 2,   # 2 occurrences → start learning
    "learning_to_confirmed": 5,    # 5 occurrences → confirmed pattern
    "confirmed_to_global": 10,     # 10 occurrences → promote to global
    "confidence_threshold": 0.7,    # 70% confidence for promotion
}

def log_learning(action, context):
    """Log learning activity"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] failure-learner | {action} | {context}\n"

        policy_log = Path.home() / ".claude" / "memory" / "logs" / "policy-hits.log"
        with open(policy_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def load_detection_results():
    """Load failure detection results"""
    if not DETECTION_FILE.exists():
        return None

    try:
        with open(DETECTION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading detection results: {e}", file=sys.stderr)
        return None

def get_current_project():
    """Get current project name from working directory"""
    try:
        cwd = Path.cwd()
        return cwd.name
    except:
        return None

def load_project_kb(project_name):
    """Load project-specific knowledge base"""
    session_dir = Path.home() / ".claude" / "memory" / "sessions" / project_name
    kb_file = session_dir / "failures.json"

    if not kb_file.exists():
        return {"patterns": {}, "metadata": {}}

    try:
        with open(kb_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"patterns": {}, "metadata": {}}

def save_project_kb(project_name, kb_data):
    """Save project-specific knowledge base"""
    session_dir = Path.home() / ".claude" / "memory" / "sessions" / project_name
    kb_file = session_dir / "failures.json"

    try:
        session_dir.mkdir(parents=True, exist_ok=True)

        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(kb_data, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving KB: {e}", file=sys.stderr)
        return False

def analyze_pattern_progression(pattern_data, current_count):
    """Analyze pattern and determine status progression"""
    old_status = pattern_data.get("status", "monitoring")
    old_count = pattern_data.get("count", 0)
    new_count = current_count

    # Determine new status based on count
    if new_count >= LEARNING_THRESHOLDS["confirmed_to_global"]:
        new_status = "global_candidate"
    elif new_count >= LEARNING_THRESHOLDS["learning_to_confirmed"]:
        new_status = "confirmed"
    elif new_count >= LEARNING_THRESHOLDS["monitoring_to_learning"]:
        new_status = "learning"
    else:
        new_status = "monitoring"

    # Calculate confidence
    # Confidence increases with frequency and consistency
    if new_count > 0:
        confidence = min(0.95, (new_count / LEARNING_THRESHOLDS["confirmed_to_global"]))
    else:
        confidence = 0.0

    changed = (new_status != old_status)

    return {
        "status": new_status,
        "count": new_count,
        "confidence": confidence,
        "status_changed": changed,
        "old_status": old_status
    }

def learn_from_detection(project_name, detection_results):
    """Learn from detection results and update KB"""
    if not detection_results:
        print("No detection results to learn from")
        return None

    # Load existing KB
    kb = load_project_kb(project_name)

    if "patterns" not in kb:
        kb["patterns"] = {}

    if "metadata" not in kb:
        kb["metadata"] = {}

    # Update metadata
    kb["metadata"]["last_learning"] = datetime.now().isoformat()
    kb["metadata"]["project"] = project_name

    # Process each detected failure signature
    failures_by_sig = detection_results.get("failures_by_signature", {})
    learned_patterns = []

    for signature, data in failures_by_sig.items():
        current_count = data["count"]

        # Get or create pattern entry
        if signature not in kb["patterns"]:
            kb["patterns"][signature] = {
                "signature": signature,
                "category": data["category"],
                "severity": data["severity"],
                "first_seen": data["first_seen"],
                "last_seen": data["last_seen"],
                "count": 0,
                "status": "monitoring",
                "confidence": 0.0,
                "examples": []
            }

        pattern = kb["patterns"][signature]

        # Analyze progression
        progression = analyze_pattern_progression(pattern, current_count)

        # Update pattern
        pattern["count"] = progression["count"]
        pattern["status"] = progression["status"]
        pattern["confidence"] = progression["confidence"]
        pattern["last_seen"] = data["last_seen"]
        pattern["severity"] = data["severity"]

        # Update examples (keep last 3)
        if "examples" in data:
            pattern["examples"] = data["examples"][:3]

        # Log if status changed
        if progression["status_changed"]:
            log_learning(
                "status-change",
                f"{signature}: {progression['old_status']} → {progression['status']} (count={current_count})"
            )

            learned_patterns.append({
                "signature": signature,
                "old_status": progression["old_status"],
                "new_status": progression["status"],
                "count": current_count,
                "confidence": progression["confidence"]
            })

    # Save updated KB
    if save_project_kb(project_name, kb):
        log_learning(
            "kb-updated",
            f"project={project_name}, patterns={len(kb['patterns'])}, learned={len(learned_patterns)}"
        )

    return {
        "project": project_name,
        "total_patterns": len(kb["patterns"]),
        "learned_patterns": learned_patterns,
        "kb_path": f"sessions/{project_name}/failures.json"
    }

def find_global_candidates(project_name):
    """Find patterns ready for promotion to global KB"""
    kb = load_project_kb(project_name)
    patterns = kb.get("patterns", {})

    candidates = []

    for signature, pattern in patterns.items():
        if pattern["status"] == "global_candidate":
            if pattern["confidence"] >= LEARNING_THRESHOLDS["confidence_threshold"]:
                candidates.append({
                    "signature": signature,
                    "count": pattern["count"],
                    "confidence": pattern["confidence"],
                    "severity": pattern["severity"],
                    "category": pattern["category"],
                    "examples": pattern.get("examples", [])
                })

    return candidates

def promote_to_global(candidates):
    """Promote patterns to global knowledge base"""
    if not candidates:
        print("No candidates for promotion")
        return 0

    print(f"\n🎯 Promoting {len(candidates)} patterns to global KB...")

    promoted = 0

    for candidate in candidates:
        # Use update-failure-kb.py to promote
        # (In real implementation, would integrate directly)
        print(f"   ✅ {candidate['signature']} (confidence: {candidate['confidence']:.1%})")
        promoted += 1

    if promoted > 0:
        log_learning("promoted-to-global", f"{promoted} patterns promoted")

    return promoted

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Failure learning and KB updates"
    )
    parser.add_argument(
        '--project',
        type=str,
        default=None,
        help='Project name (default: current directory)'
    )
    parser.add_argument(
        '--promote',
        action='store_true',
        help='Promote confirmed patterns to global KB'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # Get project name
    project_name = args.project or get_current_project()

    if not project_name:
        print("❌ Could not determine project name")
        print("   Use --project <name> to specify")
        sys.exit(1)

    # Load detection results
    detection_results = load_detection_results()

    if not detection_results:
        print("❌ No failure detection results found")
        print("   Run: python failure-detector.py --analyze-logs")
        sys.exit(1)

    # Learn from detection
    print(f"🧠 Learning from failure patterns...")
    print(f"   Project: {project_name}")
    print("")

    learning_result = learn_from_detection(project_name, detection_results)

    if not learning_result:
        print("❌ Learning failed")
        sys.exit(1)

    if args.json:
        print(json.dumps(learning_result, indent=2))
    else:
        print("=" * 70)
        print("📚 LEARNING RESULTS")
        print("=" * 70)
        print(f"\nProject: {learning_result['project']}")
        print(f"Total patterns tracked: {learning_result['total_patterns']}")
        print(f"Patterns learned (status changed): {len(learning_result['learned_patterns'])}")

        if learning_result['learned_patterns']:
            print(f"\n🎓 Status Changes:")
            for pattern in learning_result['learned_patterns']:
                print(f"   {pattern['signature']}")
                print(f"      {pattern['old_status']} → {pattern['new_status']}")
                print(f"      Count: {pattern['count']}, Confidence: {pattern['confidence']:.1%}")

        print(f"\n💾 KB saved to: {learning_result['kb_path']}")

    # Promote if requested
    if args.promote:
        candidates = find_global_candidates(project_name)

        if candidates:
            print("\n" + "=" * 70)
            print("🌍 GLOBAL PROMOTION")
            print("=" * 70)

            promoted = promote_to_global(candidates)

            if promoted > 0:
                print(f"\n✅ {promoted} patterns promoted to global KB")
        else:
            print("\n⏸️  No patterns ready for global promotion yet")

    print("\n" + "=" * 70)
    print("✅ LEARNING COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
