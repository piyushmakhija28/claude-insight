#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Failure Detector
Monitors tool executions and detects failure patterns in real-time

This script:
1. Monitors logs for tool execution failures
2. Extracts failure context and patterns
3. Detects common failure signatures
4. Logs failures for learning

Usage:
    python failure-detector.py [--analyze-logs] [--tail]

Examples:
    python failure-detector.py --analyze-logs  # Analyze existing logs
    python failure-detector.py --tail          # Monitor logs in real-time
"""

import sys
import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Configuration
FAILURES_LOG = Path.home() / ".claude" / "memory" / "logs" / "failures.log"
POLICY_LOG = Path.home() / ".claude" / "memory" / "logs" / "policy-hits.log"
DETECTION_OUTPUT = Path.home() / ".claude" / "memory" / "logs" / "failure-detection.json"

# Failure pattern signatures
FAILURE_PATTERNS = {
    "encoding_error": {
        "keywords": ["UnicodeEncodeError", "charmap", "encoding", "utf-8"],
        "severity": "medium",
        "category": "encoding"
    },
    "file_not_found": {
        "keywords": ["FileNotFoundError", "No such file", "cannot find"],
        "severity": "medium",
        "category": "filesystem"
    },
    "permission_denied": {
        "keywords": ["PermissionError", "Permission denied", "Access denied"],
        "severity": "high",
        "category": "permissions"
    },
    "timeout": {
        "keywords": ["TimeoutError", "timeout", "timed out"],
        "severity": "medium",
        "category": "performance"
    },
    "import_error": {
        "keywords": ["ImportError", "ModuleNotFoundError", "No module named"],
        "severity": "high",
        "category": "dependencies"
    },
    "syntax_error": {
        "keywords": ["SyntaxError", "invalid syntax"],
        "severity": "high",
        "category": "code"
    },
    "type_error": {
        "keywords": ["TypeError", "type object"],
        "severity": "medium",
        "category": "code"
    },
    "attribute_error": {
        "keywords": ["AttributeError", "has no attribute"],
        "severity": "medium",
        "category": "code"
    },
    "value_error": {
        "keywords": ["ValueError", "invalid literal"],
        "severity": "medium",
        "category": "validation"
    },
    "key_error": {
        "keywords": ["KeyError", "key not found"],
        "severity": "medium",
        "category": "data"
    },
    "git_error": {
        "keywords": ["git error", "fatal: not a git", "git command failed"],
        "severity": "medium",
        "category": "git"
    },
    "network_error": {
        "keywords": ["ConnectionError", "Network", "Connection refused"],
        "severity": "high",
        "category": "network"
    },
}

def log_detection(action, context):
    """Log failure detection activity"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] failure-detector | {action} | {context}\n"

        policy_log = Path.home() / ".claude" / "memory" / "logs" / "policy-hits.log"
        with open(policy_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def detect_failure_signature(text):
    """Detect failure pattern from text"""
    text_lower = text.lower()

    for signature, pattern in FAILURE_PATTERNS.items():
        for keyword in pattern["keywords"]:
            if keyword.lower() in text_lower:
                return {
                    "signature": signature,
                    "severity": pattern["severity"],
                    "category": pattern["category"],
                    "matched_keyword": keyword
                }

    # Generic error detection
    if "error" in text_lower or "failed" in text_lower or "exception" in text_lower:
        return {
            "signature": "generic_error",
            "severity": "low",
            "category": "unknown",
            "matched_keyword": "error/failed/exception"
        }

    return None

def extract_failure_context(log_line):
    """Extract context from a log line"""
    try:
        # Parse log format: [timestamp] source | action | context
        if not log_line.startswith('['):
            return None

        parts = log_line.split('|', 2)
        if len(parts) < 3:
            return None

        timestamp_source = parts[0].strip()
        action = parts[1].strip()
        context = parts[2].strip()

        # Extract timestamp
        timestamp_match = re.match(r'\[([^\]]+)\]', timestamp_source)
        if not timestamp_match:
            return None

        timestamp_str = timestamp_match.group(1)
        source = timestamp_source[len(timestamp_match.group(0)):].strip()

        return {
            "timestamp": timestamp_str,
            "source": source,
            "action": action,
            "context": context,
            "full_line": log_line
        }

    except Exception as e:
        return None

def analyze_failure_log(max_lines=1000):
    """Analyze failures.log for patterns"""
    if not FAILURES_LOG.exists():
        return []

    failures = []
    cutoff_time = datetime.now() - timedelta(days=30)  # Last 30 days

    try:
        with open(FAILURES_LOG, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line in lines[-max_lines:]:
            context = extract_failure_context(line)

            if not context:
                continue

            # Parse timestamp
            try:
                log_time = datetime.strptime(context["timestamp"], "%Y-%m-%d %H:%M:%S")
                if log_time < cutoff_time:
                    continue
            except:
                pass

            # Detect failure signature
            signature = detect_failure_signature(context["context"])

            if signature:
                failure = {
                    "timestamp": context["timestamp"],
                    "source": context["source"],
                    "action": context["action"],
                    "context": context["context"],
                    "signature": signature["signature"],
                    "severity": signature["severity"],
                    "category": signature["category"],
                    "matched_keyword": signature["matched_keyword"]
                }
                failures.append(failure)

        return failures

    except Exception as e:
        print(f"Error analyzing log: {e}", file=sys.stderr)
        return []

def analyze_policy_log(max_lines=1000):
    """Analyze policy-hits.log for prevented failures"""
    if not POLICY_LOG.exists():
        return []

    prevented = []
    cutoff_time = datetime.now() - timedelta(days=30)

    try:
        with open(POLICY_LOG, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line in lines[-max_lines:]:
            # Look for prevention actions
            if "prevented" not in line.lower() and "failure-prevention" not in line.lower():
                continue

            context = extract_failure_context(line)

            if not context:
                continue

            # Parse timestamp
            try:
                log_time = datetime.strptime(context["timestamp"], "%Y-%m-%d %H:%M:%S")
                if log_time < cutoff_time:
                    continue
            except:
                pass

            prevented_item = {
                "timestamp": context["timestamp"],
                "source": context["source"],
                "action": context["action"],
                "context": context["context"]
            }
            prevented.append(prevented_item)

        return prevented

    except Exception as e:
        print(f"Error analyzing policy log: {e}", file=sys.stderr)
        return []

def aggregate_failures(failures):
    """Aggregate failures by signature"""
    aggregated = defaultdict(lambda: {
        "count": 0,
        "severity": "low",
        "category": "unknown",
        "first_seen": None,
        "last_seen": None,
        "examples": []
    })

    for failure in failures:
        sig = failure["signature"]
        agg = aggregated[sig]

        agg["count"] += 1
        agg["severity"] = failure["severity"]
        agg["category"] = failure["category"]

        if not agg["first_seen"] or failure["timestamp"] < agg["first_seen"]:
            agg["first_seen"] = failure["timestamp"]

        if not agg["last_seen"] or failure["timestamp"] > agg["last_seen"]:
            agg["last_seen"] = failure["timestamp"]

        # Keep first 3 examples
        if len(agg["examples"]) < 3:
            agg["examples"].append({
                "timestamp": failure["timestamp"],
                "context": failure["context"][:200]  # Truncate
            })

    return dict(aggregated)

def generate_report(failures, prevented):
    """Generate detection report"""
    aggregated = aggregate_failures(failures)

    report = {
        "generated": datetime.now().isoformat(),
        "summary": {
            "total_failures": len(failures),
            "unique_patterns": len(aggregated),
            "prevented_failures": len(prevented),
            "analysis_period_days": 30
        },
        "failures_by_signature": aggregated,
        "prevention_log": prevented[-10:]  # Last 10 preventions
    }

    return report

def save_detection_output(report):
    """Save detection results to JSON"""
    try:
        DETECTION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

        with open(DETECTION_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        log_detection("detection-saved", f"{report['summary']['unique_patterns']} patterns detected")

    except Exception as e:
        print(f"Error saving detection output: {e}", file=sys.stderr)

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Failure detection and pattern analysis"
    )
    parser.add_argument(
        '--analyze-logs',
        action='store_true',
        help='Analyze existing logs for failure patterns'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    parser.add_argument(
        '--tail',
        action='store_true',
        help='Monitor logs in real-time (not implemented yet)'
    )

    args = parser.parse_args()

    if args.tail:
        print("⚠️  Real-time monitoring not implemented yet")
        print("    Use --analyze-logs for batch analysis")
        return

    # Analyze logs
    print("🔍 Analyzing failure logs...")
    failures = analyze_failure_log()
    prevented = analyze_policy_log()

    if not failures and not prevented:
        print("✅ No failures detected in last 30 days")
        return

    # Generate report
    report = generate_report(failures, prevented)

    # Save to JSON file
    save_detection_output(report)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        # Print summary
        print("\n" + "=" * 70)
        print("📊 FAILURE DETECTION REPORT")
        print("=" * 70)
        print(f"\nPeriod: Last 30 days")
        print(f"Generated: {report['generated']}")

        summary = report['summary']
        print(f"\n📈 Summary:")
        print(f"   Total failures: {summary['total_failures']}")
        print(f"   Unique patterns: {summary['unique_patterns']}")
        print(f"   Prevented failures: {summary['prevented_failures']}")

        if report['failures_by_signature']:
            print(f"\n🚨 Failures by Pattern:")

            # Sort by count
            sorted_sigs = sorted(
                report['failures_by_signature'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )

            for sig, data in sorted_sigs:
                print(f"\n   {sig} ({data['severity']})")
                print(f"      Count: {data['count']}")
                print(f"      Category: {data['category']}")
                print(f"      Last seen: {data['last_seen']}")

                if data['examples']:
                    print(f"      Example: {data['examples'][0]['context'][:100]}...")

        if report['prevention_log']:
            print(f"\n✅ Recent Preventions ({len(report['prevention_log'])}):")
            for prev in report['prevention_log'][-5:]:
                print(f"   [{prev['timestamp']}] {prev['context'][:80]}...")

        print("\n" + "=" * 70)
        print(f"💾 Full report saved to: {DETECTION_OUTPUT}")
        print("=" * 70)

    log_detection("analysis-complete", f"{summary['total_failures']} failures, {summary['unique_patterns']} patterns")

if __name__ == "__main__":
    main()
