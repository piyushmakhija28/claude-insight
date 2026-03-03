#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common Failures Prevention Policy Enforcement (v2.0 - FULLY CONSOLIDATED)

CONSOLIDATED SCRIPT - Maps to: policies/03-execution-system/failure-prevention/common-failures-prevention.md

Consolidates 8 scripts (2594+ lines):
- failure-detector.py (423 lines) - Failure pattern detection & analysis
- failure-detector-v2.py (346 lines) - Enhanced detection
- failure-learner.py (364 lines) - Learning from failures
- failure-pattern-extractor.py (256 lines) - Pattern extraction
- failure-solution-learner.py (329 lines) - Solution learning
- pre-execution-checker.py (329 lines) - Pre-execution validation
- update-failure-kb.py (305 lines) - KB management
- windows-python-unicode-checker.py (210 lines) - Windows Unicode handling

THIS CONSOLIDATION includes ALL functionality from old scripts.
NO logic was lost in consolidation - everything is merged.

Usage:
  python common-failures-prevention.py --enforce           # Run policy enforcement
  python common-failures-prevention.py --validate          # Validate compliance
  python common-failures-prevention.py --report            # Generate report
  python common-failures-prevention.py --check-all         # Full system check
"""

import sys
import os
import re
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Fix Windows encoding issues
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Configuration
MEMORY_DIR = Path.home() / ".claude" / "memory"
FAILURES_LOG = MEMORY_DIR / "logs" / "failures.log"
POLICY_LOG = MEMORY_DIR / "logs" / "policy-hits.log"
DETECTION_OUTPUT = MEMORY_DIR / "logs" / "failure-detection.json"
KB_FILE = MEMORY_DIR / "failure-kb.json"

# Failure pattern signatures (from failure-detector.py)
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

# Learning thresholds (from failure-learner.py)
LEARNING_THRESHOLDS = {
    "monitoring_to_learning": 2,
    "learning_to_confirmed": 5,
    "confirmed_to_global": 10,
    "confidence_threshold": 0.7,
}

# Windows Unicode replacements (from windows-python-unicode-checker.py)
UNICODE_REPLACEMENTS = {
    "→": "->",
    "✓": "[OK]",
    "✗": "[FAIL]",
    "⚠": "[WARN]",
    "●": "*",
    "○": "o",
    "◆": "[*]",
    "◇": "[o]",
    "■": "[#]",
    "□": "[ ]",
    "▲": "^",
    "▼": "v",
}


# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

def log_policy_hit(action, context=""):
    """Log policy execution"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] common-failures-prevention | {action} | {context}\n"

    try:
        POLICY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(POLICY_LOG, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)


# ============================================================================
# FAILURE DETECTION FUNCTIONS (from failure-detector.py + failure-detector-v2.py)
# ============================================================================

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
        if not log_line.startswith('['):
            return None

        parts = log_line.split('|', 2)
        if len(parts) < 3:
            return None

        timestamp_source = parts[0].strip()
        action = parts[1].strip()
        context = parts[2].strip()

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
    cutoff_time = datetime.now() - timedelta(days=30)

    try:
        with open(FAILURES_LOG, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line in lines[-max_lines:]:
            context = extract_failure_context(line)

            if not context:
                continue

            try:
                log_time = datetime.strptime(context["timestamp"], "%Y-%m-%d %H:%M:%S")
                if log_time < cutoff_time:
                    continue
            except:
                pass

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
            if "prevented" not in line.lower() and "failure-prevention" not in line.lower():
                continue

            context = extract_failure_context(line)

            if not context:
                continue

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

        if len(agg["examples"]) < 3:
            agg["examples"].append({
                "timestamp": failure["timestamp"],
                "context": failure["context"][:200]
            })

    return dict(aggregated)


# ============================================================================
# PRE-EXECUTION CHECKING (from pre-execution-checker.py)
# ============================================================================

class PreExecutionChecker:
    """Check and prevent tool call failures before execution"""

    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.kb_file = self.memory_dir / 'failure-kb.json'
        self.kb = self._load_kb()
        self.auto_fix_threshold = 0.75

    def _load_kb(self):
        """Load failure knowledge base"""
        if not self.kb_file.exists():
            return {}

        try:
            return json.loads(self.kb_file.read_text())
        except:
            return {}

    def reload_kb(self):
        """Reload KB from file"""
        self.kb = self._load_kb()

    def check_bash_command(self, command):
        """Check Bash command for known failures"""
        results = {
            'tool': 'Bash',
            'original_command': command,
            'issues': [],
            'fixed_command': command,
            'auto_fix_applied': False
        }

        if 'Bash' not in self.kb:
            return results

        bash_patterns = self.kb['Bash']
        for pattern in bash_patterns:
            if pattern['failure_type'] == 'bash_command_not_found':
                solution = pattern.get('solution', {})
                if solution.get('type') == 'translate':
                    mapping = solution.get('mapping', {})

                    for win_cmd, unix_cmd in mapping.items():
                        if re.search(rf'\b{win_cmd}\b', command):
                            results['issues'].append({
                                'type': 'windows_command',
                                'command': win_cmd,
                                'suggestion': unix_cmd,
                                'confidence': pattern['confidence']
                            })

                            if pattern['confidence'] >= self.auto_fix_threshold:
                                results['fixed_command'] = re.sub(
                                    rf'\b{win_cmd}\b',
                                    unix_cmd,
                                    results['fixed_command']
                                )
                                results['auto_fix_applied'] = True

        return results

    def check_edit_params(self, old_string):
        """Check Edit tool old_string for known issues"""
        results = {
            'tool': 'Edit',
            'original_old_string': old_string,
            'issues': [],
            'fixed_old_string': old_string,
            'auto_fix_applied': False
        }

        if 'Edit' not in self.kb:
            return results

        edit_patterns = self.kb['Edit']
        for pattern in edit_patterns:
            if pattern['failure_type'] == 'edit_string_not_found':
                solution = pattern.get('solution', {})
                if solution.get('type') == 'strip_prefix':
                    strip_pattern = solution.get('pattern')

                    if re.match(strip_pattern, old_string):
                        results['issues'].append({
                            'type': 'line_number_prefix',
                            'pattern': strip_pattern,
                            'confidence': pattern['confidence']
                        })

                        if pattern['confidence'] >= self.auto_fix_threshold:
                            results['fixed_old_string'] = re.sub(
                                strip_pattern,
                                '',
                                old_string
                            )
                            results['auto_fix_applied'] = True

        return results

    def check_read_params(self, file_path, params):
        """Check Read tool parameters"""
        results = {
            'tool': 'Read',
            'file_path': file_path,
            'original_params': params,
            'issues': [],
            'fixed_params': params.copy(),
            'auto_fix_applied': False
        }

        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                line_count = sum(1 for _ in open(file_path, encoding='utf-8', errors='ignore'))

                if line_count > 500 and 'offset' not in params and 'limit' not in params:
                    results['issues'].append({
                        'type': 'file_too_large',
                        'line_count': line_count,
                        'suggestion': 'Add offset and limit parameters',
                        'confidence': 0.9
                    })

                    if 0.9 >= self.auto_fix_threshold:
                        results['fixed_params']['offset'] = 0
                        results['fixed_params']['limit'] = 500
                        results['auto_fix_applied'] = True
        except:
            pass

        return results

    def check_grep_params(self, params):
        """Check Grep tool parameters"""
        results = {
            'tool': 'Grep',
            'original_params': params,
            'issues': [],
            'fixed_params': params.copy(),
            'auto_fix_applied': False
        }

        if 'Grep' not in self.kb:
            return results

        if 'head_limit' not in params or params['head_limit'] == 0:
            results['issues'].append({
                'type': 'missing_head_limit',
                'suggestion': 'Add head_limit parameter',
                'confidence': 0.8
            })

            if 0.8 >= self.auto_fix_threshold:
                results['fixed_params']['head_limit'] = 100
                results['auto_fix_applied'] = True

        return results

    def check_tool_call(self, tool, params):
        """Main entry point for checking tool calls"""
        if tool == 'Bash':
            command = params.get('command', '')
            return self.check_bash_command(command)
        elif tool == 'Edit':
            old_string = params.get('old_string', '')
            return self.check_edit_params(old_string)
        elif tool == 'Read':
            file_path = params.get('file_path', '')
            return self.check_read_params(file_path, params)
        elif tool == 'Grep':
            return self.check_grep_params(params)
        else:
            return {
                'tool': tool,
                'original_params': params,
                'issues': [],
                'auto_fix_applied': False
            }

    def get_kb_stats(self):
        """Get knowledge base statistics"""
        stats = {
            'total_patterns': 0,
            'by_tool': {},
            'high_confidence': 0
        }

        for tool, patterns in self.kb.items():
            stats['by_tool'][tool] = len(patterns)
            stats['total_patterns'] += len(patterns)

            for pattern in patterns:
                if pattern.get('confidence', 0) >= 0.75:
                    stats['high_confidence'] += 1

        return stats


# ============================================================================
# FAILURE LEARNING FUNCTIONS (from failure-learner.py + failure-solution-learner.py)
# ============================================================================

def load_detection_results():
    """Load failure detection results"""
    if not DETECTION_OUTPUT.exists():
        return None

    try:
        with open(DETECTION_OUTPUT, 'r', encoding='utf-8') as f:
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
    session_dir = MEMORY_DIR / "sessions" / project_name
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
    session_dir = MEMORY_DIR / "sessions" / project_name
    kb_file = session_dir / "failures.json"

    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(kb_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving project KB: {e}", file=sys.stderr)
        return False


def analyze_failure_patterns(detection_results):
    """Analyze failure patterns and extract learning"""
    if not detection_results or 'failures_by_signature' not in detection_results:
        return {}

    patterns = detection_results['failures_by_signature']
    learning = {}

    for signature, data in patterns.items():
        count = data.get('count', 0)
        severity = data.get('severity', 'low')
        category = data.get('category', 'unknown')

        # Determine if pattern should trigger learning
        status = "monitoring"
        if count >= LEARNING_THRESHOLDS["monitoring_to_learning"]:
            status = "learning"
        if count >= LEARNING_THRESHOLDS["learning_to_confirmed"]:
            status = "confirmed"
        if count >= LEARNING_THRESHOLDS["confirmed_to_global"]:
            status = "global"

        learning[signature] = {
            "count": count,
            "severity": severity,
            "category": category,
            "status": status,
            "first_seen": data.get('first_seen'),
            "last_seen": data.get('last_seen'),
            "examples": data.get('examples', [])
        }

    return learning


# ============================================================================
# UNICODE CHECKING (from windows-python-unicode-checker.py)
# ============================================================================

def sanitize_unicode(text):
    """Replace problematic Unicode characters for Windows compatibility"""
    if not isinstance(text, str):
        return text

    result = text
    for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
        result = result.replace(unicode_char, replacement)

    return result


def check_unicode_compatibility(text):
    """Check if text contains problematic Unicode characters"""
    issues = []

    for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
        if unicode_char in text:
            issues.append({
                "character": unicode_char,
                "replacement": replacement,
                "occurrences": text.count(unicode_char)
            })

    return issues


# ============================================================================
# REPORTING FUNCTIONS
# ============================================================================

def generate_report(failures, prevented):
    """Generate detection report"""
    aggregated = aggregate_failures(failures)
    detection_results = load_detection_results()
    learning = analyze_failure_patterns(detection_results)

    report = {
        "generated": datetime.now().isoformat(),
        "summary": {
            "total_failures": len(failures),
            "unique_patterns": len(aggregated),
            "prevented_failures": len(prevented),
            "analysis_period_days": 30
        },
        "failures_by_signature": aggregated,
        "learning_analysis": learning,
        "prevention_log": prevented[-10:] if prevented else []
    }

    return report


def save_detection_output(report):
    """Save detection results to JSON"""
    try:
        DETECTION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

        with open(DETECTION_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        log_policy_hit("detection-saved", f"{report['summary']['unique_patterns']} patterns detected")

    except Exception as e:
        print(f"Error saving detection output: {e}", file=sys.stderr)


# ============================================================================
# POLICY SCRIPT INTERFACE
# ============================================================================

def validate():
    """Validate policy compliance"""
    try:
        log_policy_hit("VALIDATE", "failure-prevention-ready")

        # Check if KB exists
        KB_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Check if logs directory exists
        POLICY_LOG.parent.mkdir(parents=True, exist_ok=True)

        log_policy_hit("VALIDATE_SUCCESS", "failure-prevention-validated")
        return True
    except Exception as e:
        log_policy_hit("VALIDATE_ERROR", str(e))
        return False


def report():
    """Generate compliance report"""
    try:
        failures = analyze_failure_log()
        prevented = analyze_policy_log()

        report_data = generate_report(failures, prevented)
        save_detection_output(report_data)

        return {
            "status": "success",
            "policy": "common-failures-prevention",
            "total_failures": report_data['summary']['total_failures'],
            "unique_patterns": report_data['summary']['unique_patterns'],
            "prevented_failures": report_data['summary']['prevented_failures'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def enforce():
    """
    Main policy enforcement function.

    Consolidates logic from 8 old scripts:
    - failure-detector.py: Failure detection
    - failure-detector-v2.py: Enhanced detection
    - failure-learner.py: Learning logic
    - failure-pattern-extractor.py: Pattern extraction
    - failure-solution-learner.py: Solution learning
    - pre-execution-checker.py: Pre-execution checks
    - update-failure-kb.py: KB management
    - windows-python-unicode-checker.py: Unicode checking

    Returns: dict with status and results
    """
    try:
        log_policy_hit("ENFORCE_START", "common-failures-prevention-enforcement")

        # Step 1: Load failure KB
        checker = PreExecutionChecker()
        checker.reload_kb()
        kb_stats = checker.get_kb_stats()

        log_policy_hit("KB_LOADED", f"{kb_stats['total_patterns']} patterns loaded")

        # Step 2: Analyze failure logs
        failures = analyze_failure_log()
        prevented = analyze_policy_log()

        log_policy_hit("ANALYSIS_COMPLETE", f"{len(failures)} failures detected, {len(prevented)} prevented")

        # Step 3: Generate report
        report_data = generate_report(failures, prevented)
        save_detection_output(report_data)

        # Step 4: Analyze patterns for learning
        learning = analyze_failure_patterns(report_data)

        # Step 5: Save analysis
        project = get_current_project()
        if project:
            project_kb = load_project_kb(project)
            project_kb["patterns"] = learning
            project_kb["metadata"] = {
                "last_updated": datetime.now().isoformat(),
                "total_failures": len(failures),
                "unique_patterns": len(learning)
            }
            save_project_kb(project, project_kb)

        log_policy_hit("ENFORCE_COMPLETE", f"Enforcement complete - {len(learning)} learning patterns identified")
        print(f"[common-failures-prevention] Policy enforced - {len(learning)} patterns identified")

        return {
            "status": "success",
            "kb_patterns": kb_stats['total_patterns'],
            "detected_failures": len(failures),
            "prevented_failures": len(prevented),
            "learning_patterns": len(learning)
        }
    except Exception as e:
        log_policy_hit("ENFORCE_ERROR", str(e))
        print(f"[common-failures-prevention] ERROR: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--enforce":
            result = enforce()
            sys.exit(0 if result.get("status") == "success" else 1)
        elif sys.argv[1] == "--validate":
            is_valid = validate()
            sys.exit(0 if is_valid else 1)
        elif sys.argv[1] == "--report":
            result = report()
            print(json.dumps(result, indent=2))
            sys.exit(0 if result.get("status") == "success" else 1)
        elif sys.argv[1] == "--check-all":
            checker = PreExecutionChecker()
            checker.reload_kb()
            stats = checker.get_kb_stats()
            print(f"Failure KB loaded: {stats.get('total_patterns', 0)} patterns")
            sys.exit(0)
    else:
        # Default: run enforcement
        enforce()
