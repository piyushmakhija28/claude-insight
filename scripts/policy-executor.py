#!/usr/bin/env python3
"""
Script: policy-executor.py
Version: 1.0.0
Date: 2026-02-25
Purpose: INTEGRATION BRIDGE - Executes all 34+ policies from scripts/architecture/
         Connects policy documentation (policies/*.md) to actual execution

This is the MISSING LINK that ties documentation to implementation!
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent
ARCH_DIR = SCRIPT_DIR / 'architecture'
PYTHON = sys.executable
MEMORY_BASE = Path.home() / '.claude' / 'memory'
LOG_DIR = MEMORY_BASE / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

class PolicyExecutor:
    """Orchestrates all policies from 3-level architecture"""

    def __init__(self):
        self.executed = []
        self.failed = []

    def run_policy(self, level_dir, script_name):
        """Execute single policy script with proper error reporting"""
        script = ARCH_DIR / level_dir / script_name
        if not script.exists():
            self.failed.append(f"{level_dir}/{script_name} (NOT FOUND)")
            return False

        try:
            # Windows encoding fix: use encoding='utf-8', errors='replace'
            result = subprocess.run(
                [PYTHON, str(script)],
                timeout=5,
                capture_output=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode == 0:
                self.executed.append(f"{level_dir}/{script_name}")
                return True
            else:
                error_msg = result.stderr[:100] if result.stderr else "Unknown error"
                self.failed.append(f"{level_dir}/{script_name} (exit {result.returncode}: {error_msg})")
                return False
        except subprocess.TimeoutExpired:
            self.failed.append(f"{level_dir}/{script_name} (TIMEOUT)")
            return False
        except Exception as e:
            self.failed.append(f"{level_dir}/{script_name} (ERROR: {str(e)[:50]})")
            return False

    def execute_level_1(self):
        """Execute Level 1: Sync System (6 policies)"""
        print("[LEVEL 1] SYNC SYSTEM - Loading 6 policies...", end=" ")

        policies = [
            ('01-sync-system/session-management', 'session-loader.py'),
            ('01-sync-system/context-management', 'context-monitor-v2.py'),
            ('01-sync-system/user-preferences', 'preference-auto-tracker.py'),
            ('01-sync-system/pattern-detection', 'detect-patterns.py'),
            ('01-sync-system/session-management', 'session-save-triggers.py'),
            ('01-sync-system/session-management', 'archive-old-sessions.py'),
        ]

        count = 0
        for level_dir, script in policies:
            if self.run_policy(level_dir, script):
                count += 1

        print(f"✓ {count}/6 executed")
        return count

    def execute_level_2(self):
        """Execute Level 2: Standards System (1 policy)"""
        print("[LEVEL 2] STANDARDS SYSTEM - Loading 1 policy...", end=" ")

        if self.run_policy('02-standards-system', 'standards-loader.py'):
            print("✓ 1/1 executed")
            return 1
        else:
            print("✗ 0/1 executed")
            return 0

    def execute_level_3(self):
        """Execute Level 3: Execution System (17 policies)"""
        print("[LEVEL 3] EXECUTION SYSTEM - Loading 17 policies...")

        policies = [
            # Step 3.0: Prompt Generation
            ('03-execution-system/00-prompt-generation', 'prompt-generator.py'),
            # Step 3.1: Task Breakdown
            ('03-execution-system/01-task-breakdown', 'task-auto-analyzer.py'),
            ('03-execution-system/01-task-breakdown', 'task-phase-enforcer.py'),
            # Step 3.2: Plan Mode
            ('03-execution-system/02-plan-mode', 'auto-plan-mode-suggester.py'),
            # Step 3.4: Model Selection
            ('03-execution-system/04-model-selection', 'intelligent-model-selector.py'),
            ('03-execution-system/04-model-selection', 'model-selection-enforcer.py'),
            # Step 3.5: Skill/Agent Selection
            ('03-execution-system/05-skill-agent-selection', 'auto-skill-agent-selector.py'),
            ('03-execution-system/05-skill-agent-selection', 'core-skills-enforcer.py'),
            # Step 3.6: Tool Optimization
            ('03-execution-system/06-tool-optimization', 'tool-usage-optimizer.py'),
            # Step 3.7: Failure Prevention
            ('03-execution-system/failure-prevention', 'failure-detector.py'),
            ('03-execution-system/failure-prevention', 'pre-execution-checker.py'),
            # Step 3.8-3.9: Progress Tracking
            ('03-execution-system/08-progress-tracking', 'check-incomplete-work.py'),
            # Step 3.11: Git Auto-Commit
            ('03-execution-system/09-git-commit', 'auto-commit-enforcer.py'),
        ]

        count = 0
        for level_dir, script in policies:
            if self.run_policy(level_dir, script):
                count += 1
                print(f"  ✓ {script}")

        print(f"[LEVEL 3] ✓ {count}/{len(policies)} executed")
        return count

    def execute_all(self):
        """Execute all 3 levels"""
        print("\n" + "="*70)
        print("POLICY EXECUTOR - Integrating All 34+ Policies")
        print("="*70 + "\n")

        l1 = self.execute_level_1()
        l2 = self.execute_level_2()
        l3 = self.execute_level_3()

        total = l1 + l2 + l3
        print("\n" + "="*70)
        print(f"✓ INTEGRATION COMPLETE: {total} policies executed")

        # Show failures for debugging
        if self.failed:
            print(f"\n⚠️  {len(self.failed)} policies FAILED:")
            for failed_policy in self.failed:
                print(f"   ❌ {failed_policy}")

        print("="*70 + "\n")

        return total > 0

if __name__ == '__main__':
    executor = PolicyExecutor()
    success = executor.execute_all()
    sys.exit(0 if success else 1)
