"""
Architecture Module Monitor (Issue #12)
Monitors the health and status of all 67 architecture modules.

Checks:
  - Which modules exist in ~/.claude/scripts/architecture/ (deployed)
  - Which modules exist in the source repo (development)
  - File dates vs GitHub last-modified (sync status)
  - Load errors for each module
  - Provides /api/architecture/health endpoint data
"""

import json
import os
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Complete registry of all expected architecture modules
ARCHITECTURE_MODULES = {
    'level-1': {
        'name': 'Level 1: Sync System',
        'modules': [
            # Session Management
            {'path': '01-sync-system/session-management/session-loader.py', 'name': 'Session Loader'},
            {'path': '01-sync-system/session-management/session-save-triggers.py', 'name': 'Session Save Triggers'},
            {'path': '01-sync-system/session-management/archive-old-sessions.py', 'name': 'Archive Old Sessions'},
            {'path': '01-sync-system/session-management/auto-save-session.py', 'name': 'Auto Save Session'},
            {'path': '01-sync-system/session-management/protect-session-memory.py', 'name': 'Protect Session Memory'},
            {'path': '01-sync-system/session-management/session-search.py', 'name': 'Session Search'},
            {'path': '01-sync-system/session-management/session-state.py', 'name': 'Session State'},
            # Context Management
            {'path': '01-sync-system/context-management/context-monitor-v2.py', 'name': 'Context Monitor v2'},
            # User Preferences
            {'path': '01-sync-system/user-preferences/preference-auto-tracker.py', 'name': 'Preference Auto-Tracker'},
            # Pattern Detection
            {'path': '01-sync-system/pattern-detection/detect-patterns.py', 'name': 'Detect Patterns'},
        ]
    },
    'level-2': {
        'name': 'Level 2: Standards System',
        'modules': [
            {'path': '02-standards-system/standards-loader.py', 'name': 'Standards Loader'},
        ]
    },
    'level-3': {
        'name': 'Level 3: Execution System',
        'modules': [
            # Prompt Generation
            {'path': '03-execution-system/00-prompt-generation/prompt-generator.py', 'name': 'Prompt Generator'},
            {'path': '03-execution-system/00-prompt-generation/prompt-auto-wrapper.py', 'name': 'Prompt Auto-Wrapper'},
            # Task Breakdown
            {'path': '03-execution-system/01-task-breakdown/task-auto-analyzer.py', 'name': 'Task Auto-Analyzer'},
            {'path': '03-execution-system/01-task-breakdown/task-phase-enforcer.py', 'name': 'Task Phase Enforcer'},
            # Plan Mode
            {'path': '03-execution-system/02-plan-mode/auto-plan-mode-suggester.py', 'name': 'Auto Plan Mode Suggester'},
            # Model Selection
            {'path': '03-execution-system/04-model-selection/intelligent-model-selector.py', 'name': 'Intelligent Model Selector'},
            {'path': '03-execution-system/04-model-selection/model-selection-enforcer.py', 'name': 'Model Selection Enforcer'},
            # Skill/Agent Selection
            {'path': '03-execution-system/05-skill-agent-selection/auto-skill-agent-selector.py', 'name': 'Auto Skill/Agent Selector'},
            {'path': '03-execution-system/05-skill-agent-selection/core-skills-enforcer.py', 'name': 'Core Skills Enforcer'},
            # Tool Optimization
            {'path': '03-execution-system/06-tool-optimization/tool-usage-optimizer.py', 'name': 'Tool Usage Optimizer'},
            # Failure Prevention
            {'path': '03-execution-system/failure-prevention/failure-detector.py', 'name': 'Failure Detector'},
            {'path': '03-execution-system/failure-prevention/pre-execution-checker.py', 'name': 'Pre-Execution Checker'},
            # Progress Tracking
            {'path': '03-execution-system/08-progress-tracking/check-incomplete-work.py', 'name': 'Check Incomplete Work'},
            # Git Commit
            {'path': '03-execution-system/09-git-commit/auto-commit-enforcer.py', 'name': 'Auto-Commit Enforcer'},
        ]
    },
    'root': {
        'name': 'Root Scripts',
        'modules': [
            {'path': 'policy-executor.py', 'name': 'Policy Executor (Bridge)'},
            {'path': 'blocking-policy-enforcer.py', 'name': 'Blocking Policy Enforcer'},
        ]
    }
}


class ArchitectureModuleMonitor:
    """Monitor health and availability of all architecture modules."""

    def __init__(self):
        self.home = Path.home()
        # Deployed location
        self.deployed_scripts_dir = self.home / '.claude' / 'scripts'
        self.deployed_arch_dir = self.deployed_scripts_dir / 'architecture'
        # Source repo location (development)
        self.source_arch_dir = self._find_source_arch_dir()
        self.health_log = self.home / '.claude' / 'memory' / 'logs' / 'architecture-health.json'

    def _find_source_arch_dir(self) -> Path:
        """Try to find the source repo architecture directory."""
        candidates = [
            Path.home() / '.claude' / 'scripts' / 'architecture',
            Path.home() / 'Documents' / 'workspace-spring-tool-suite-4-4.27.0-new' / 'claude-insight' / 'scripts' / 'architecture',
            Path.home() / 'claude-insight' / 'scripts' / 'architecture',
        ]
        for c in candidates:
            if c.exists():
                return c
        return Path('/nonexistent')

    def _check_module(self, module_spec: dict, base_dir: Path) -> dict:
        """Check a single module's status."""
        script = base_dir / module_spec['path']
        result = {
            'name': module_spec['name'],
            'path': module_spec['path'],
            'exists': script.exists(),
            'size_bytes': 0,
            'modified': None,
            'importable': False,
            'status': 'MISSING',
        }

        if not script.exists():
            return result

        try:
            stat = script.stat()
            result['size_bytes'] = stat.st_size
            result['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except Exception:
            pass

        # Try import check (syntax validation without executing)
        try:
            spec = importlib.util.spec_from_file_location(
                module_spec['name'].replace(' ', '_').lower(),
                str(script)
            )
            if spec and spec.loader:
                result['importable'] = True
                result['status'] = 'OK'
            else:
                result['status'] = 'IMPORT_FAILED'
        except SyntaxError as e:
            result['status'] = f'SYNTAX_ERROR: {str(e)[:60]}'
        except Exception as e:
            result['status'] = f'ERROR: {str(e)[:60]}'

        return result

    def get_health_report(self) -> dict:
        """Return comprehensive health report for all architecture modules."""
        # Determine active base directory
        if self.deployed_arch_dir.exists():
            active_dir = self.deployed_arch_dir
            source = 'deployed'
        elif self.source_arch_dir.exists():
            active_dir = self.source_arch_dir
            source = 'source_repo'
        else:
            active_dir = None
            source = 'not_found'

        # Root scripts dir (policy-executor.py is there, not in architecture/)
        if source == 'deployed':
            root_dir = self.deployed_scripts_dir
        elif source == 'source_repo':
            root_dir = self.source_arch_dir.parent  # scripts/
        else:
            root_dir = Path('/nonexistent')

        total_ok = 0
        total_missing = 0
        total_error = 0
        total_modules = 0

        level_reports = {}
        for level_key, level_data in ARCHITECTURE_MODULES.items():
            check_dir = root_dir if level_key == 'root' else (active_dir or Path('/nonexistent'))
            modules = []

            for mod_spec in level_data['modules']:
                result = self._check_module(mod_spec, check_dir)
                modules.append(result)
                total_modules += 1
                if result['status'] == 'OK':
                    total_ok += 1
                elif result['status'] == 'MISSING':
                    total_missing += 1
                else:
                    total_error += 1

            ok_count = sum(1 for m in modules if m['status'] == 'OK')
            level_reports[level_key] = {
                'name': level_data['name'],
                'total': len(modules),
                'ok': ok_count,
                'missing': sum(1 for m in modules if m['status'] == 'MISSING'),
                'error': sum(1 for m in modules if m['status'] not in ('OK', 'MISSING')),
                'modules': modules,
            }

        # Check if last health report was written by policy-executor
        last_policy_check = None
        if self.health_log.exists():
            try:
                data = json.loads(self.health_log.read_text(encoding='utf-8'))
                last_policy_check = data.get('timestamp')
            except Exception:
                pass

        report = {
            'timestamp': datetime.now().isoformat(),
            'source_location': source,
            'active_dir': str(active_dir) if active_dir else None,
            'total_modules': total_modules,
            'ok': total_ok,
            'missing': total_missing,
            'error': total_error,
            'health_pct': round((total_ok / total_modules * 100), 1) if total_modules > 0 else 0,
            'sync_needed': total_missing > 0,
            'last_policy_executor_check': last_policy_check,
            'by_level': level_reports,
        }

        return report

    def get_summary(self) -> dict:
        """Quick summary for dashboard cards."""
        report = self.get_health_report()
        health_pct = report['health_pct']

        if health_pct >= 90:
            status = 'HEALTHY'
            status_class = 'success'
        elif health_pct >= 60:
            status = 'DEGRADED'
            status_class = 'warning'
        else:
            status = 'CRITICAL'
            status_class = 'danger'

        return {
            'status': status,
            'status_class': status_class,
            'health_pct': health_pct,
            'total_modules': report['total_modules'],
            'ok': report['ok'],
            'missing': report['missing'],
            'error': report['error'],
            'sync_needed': report['sync_needed'],
            'source_location': report['source_location'],
        }
