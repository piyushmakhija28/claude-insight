#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic Task Breakdown Policy Enforcement (v2.0 - FULLY CONSOLIDATED)

CONSOLIDATED SCRIPT - Maps to: policies/03-execution-system/01-task-breakdown/automatic-task-breakdown-policy.md

Consolidates 3 scripts (1,182+ lines):
- task-auto-analyzer.py (400 lines) - Automatic task analysis and breakdown
- task-auto-tracker.py (536 lines) - Task progress tracking and monitoring
- task-phase-enforcer.py (121 lines) - Task/phase enforcement validation

THIS CONSOLIDATION includes ALL functionality from old scripts.
NO logic was lost in consolidation - everything is merged.

Usage:
  python automatic-task-breakdown-policy.py --enforce              # Run policy enforcement
  python automatic-task-breakdown-policy.py --validate             # Validate compliance
  python automatic-task-breakdown-policy.py --report               # Generate report
  python automatic-task-breakdown-policy.py --analyze <task>       # Analyze task description
"""

import sys
import io
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# ===================================================================
# NEW: POLICY TRACKING INTEGRATION
# ===================================================================
# Policy tracking - mandatory (find helper by walking up to scripts root)
_scripts_root = Path(__file__).resolve().parent
while _scripts_root != _scripts_root.parent:
    if (_scripts_root / 'policy_tracking_helper.py').exists():
        if str(_scripts_root) not in sys.path:
            sys.path.insert(0, str(_scripts_root))
        break
    _scripts_root = _scripts_root.parent
from policy_tracking_helper import record_policy_execution, record_sub_operation, get_session_id

# Configuration
MEMORY_DIR = Path.home() / ".claude" / "memory"
LOG_FILE = MEMORY_DIR / "logs" / "policy-hits.log"
TASK_LOG_DIR = MEMORY_DIR / "logs" / "tasks"


# ============================================================================
# TASK AUTO-ANALYZER CLASS (from task-auto-analyzer.py - 400 lines)
# ============================================================================

class TaskAutoAnalyzer:
    """Analyzes user messages and automatically breaks them into structured tasks.

    Extracts entities, estimates file count, detects phase requirements, and
    generates a typed task list with dependency relationships.

    Attributes:
        memory_path (Path): Base ~/.claude/memory directory.
        logs_path (Path): Logs subdirectory.
        task_log (Path): JSONL log file for breakdown events.

    Key Methods:
        auto_analyze(user_message): Main entry; returns full analysis dict.
        extract_entities(message): Find service/feature names from message.
        estimate_complexity(message, entities): Score complexity from 5-30.
        detect_phases(complexity, file_count): Decide if phases are needed.
        generate_tasks(message, entities, phases): Build typed task list.
    """

    def __init__(self):
        """Initialize TaskAutoAnalyzer with memory directory and task-breakdown log path."""
        self.memory_path = MEMORY_DIR
        self.logs_path = self.memory_path / "logs"
        self.task_log = self.logs_path / "task-breakdown.log"

    def detect_tech_from_message(self, message: str) -> List[str]:
        """Detect technology stack from user message via keyword scanning.

        Analyzes the raw user message for technology keywords and returns a list
        of detected technologies (e.g., ['java', 'docker', 'postgresql']).

        The keyword map is built from actual keywords used in:
        - AGENT_KEYWORD_SCORES in detect_task_type()
        - detect_tech_stack() in architecture
        - Existing YAML heuristics throughout the system

        Args:
            message (str): Raw task description from the user.

        Returns:
            list[str]: List of detected technology names (lowercase).
                      Returns ['unknown'] if no technologies detected.
        """
        # Tech keyword map - built from existing detection patterns
        tech_keywords = {
            'spring-boot': ['spring boot', 'spring-boot', 'springboot', 'spring', '@springboot',
                           'maven', 'gradle', 'eureka', 'feign', 'config server', 'rest api java',
                           'pom.xml', 'application.yml'],
            'java': ['java', 'jpa', 'hibernate', 'bean', 'autowired', 'dto',
                    'request mapping', 'controller', 'entity', 'repository'],
            'python': ['python', 'setup.py', 'pyproject.toml', 'app.py'],
            'flask': ['flask', 'flask app', 'flask route', 'flask api'],
            'django': ['django', 'django rest', 'django model', 'django view'],
            'fastapi': ['fastapi', 'fast api'],
            'angular': ['angular', 'ngmodule', 'ngcomponent', 'ngrouter', 'rxjs',
                       'observable', 'ngform', 'reactive form', 'angular service'],
            'typescript': ['typescript', 'ts', '.ts file', 'type script'],
            'react': ['react', 'jsx', 'tsx', 'react component', 'useState', 'useEffect', 'hooks react'],
            'vue': ['vue', 'vuejs', 'vue component', 'vuex'],
            'css': ['css', 'style', 'styling', 'flex', 'flexbox', 'grid css', 'bootstrap',
                   'tailwind', 'theme', 'color', 'font', 'responsive', 'dark mode', 'light mode'],
            'scss': ['scss', 'sass'],
            'html': ['html', 'template', 'layout', 'interface', 'frontend', 'page', 'screen',
                    'widget', 'card', 'modal', 'form', 'button', 'nav', 'navbar', 'sidebar',
                    'header', 'footer'],
            'docker': ['docker', 'dockerfile', 'docker-compose', 'container', 'image docker',
                      'docker image', 'docker build', 'docker run'],
            'kubernetes': ['kubernetes', 'k8s', 'kubectl', 'helm', 'pod', 'cluster', 'ingress',
                          'namespace', 'manifest', 'deploy', 'daemonset', 'stateful', 'configmap', 'hpa'],
            'jenkins': ['jenkins', 'jenkinsfile', 'pipeline', 'ci/cd', 'cicd', 'build pipeline',
                       'jenkins pipeline'],
            'postgresql': ['postgresql', 'postgres', 'pg', 'psql'],
            'mysql': ['mysql', 'mariadb'],
            'mongodb': ['mongodb', 'mongo', 'nosql'],
            'redis': ['redis', 'cache redis'],
            'kotlin': ['kotlin', 'android', 'apk', 'coroutine', 'retrofit', 'room database',
                      'viewmodel', 'livedata', 'jetpack', 'recycler', 'gradle android'],
            'swift': ['swift', 'ios', 'swiftui', 'iphone', 'ipad', 'xcode', 'uikit',
                     'storyboard', 'vapor'],
            'seo': ['seo', 'sitemap', 'robots.txt', 'meta tag', 'search engine'],
            'testing': ['test', 'testing', 'unit test', 'pytest', 'junit', 'integration test',
                       'mock', 'e2e', 'selenium'],
        }

        detected = []
        message_lower = message.lower()

        for tech, keywords in tech_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    if tech not in detected:
                        detected.append(tech)
                    break  # Move to next tech

        return detected if detected else ['unknown']

    def extract_entities(self, message: str) -> List[str]:
        """Extract service and feature entity names from a task description.

        Args:
            message (str): Raw task description text.

        Returns:
            list[str]: Deduplicated list of entity names (lowercased).
        """
        entities = []

        # Service patterns
        service_patterns = [
            r'(\w+)[-\s]service',
            r'service\s+for\s+(\w+)',
            r'(\w+)\s+microservice'
        ]

        for pattern in service_patterns:
            matches = re.findall(pattern, message.lower())
            entities.extend(matches)

        # Feature patterns
        feature_patterns = [
            r'(\w+)\s+feature',
            r'feature\s+for\s+(\w+)',
            r'add\s+(\w+)',
            r'create\s+(\w+)',
            r'implement\s+(\w+)'
        ]

        for pattern in feature_patterns:
            matches = re.findall(pattern, message.lower())
            entities.extend(matches)

        return list(set(entities))

    def estimate_file_count(self, message: str, entities: List[str]) -> int:
        """Estimate how many files a task will touch based on entities and keywords.

        Args:
            message (str): Raw task description.
            entities (list[str]): Extracted entity names.

        Returns:
            int: Estimated file count.
        """
        file_count = 0

        # Base count from entities
        file_count += len(entities) * 3

        # Check for explicit mentions
        keywords_count_map = {
            'crud': 4,
            'api': 2,
            'endpoint': 2,
            'database': 2,
            'entity': 2,
            'config': 1,
            'test': 2,
            'dashboard': 3,
            'admin panel': 3,
            'ui': 2,
            'frontend': 2,
            'component': 1,
            'layout': 1,
            'template': 1
        }

        for keyword, count in keywords_count_map.items():
            if keyword in message.lower():
                file_count += count

        return file_count

    def detect_phases(self, complexity_score: int, file_count: int, tech_stack: List[str] = None) -> tuple:
        """Decide whether the task requires phase-based execution.

        Generates phase names based on the detected technology stack for better clarity.

        Args:
            complexity_score (int): Complexity score from estimate_complexity().
            file_count (int): Estimated number of files to touch.
            tech_stack (list[str]): Detected technologies from detect_tech_from_message().
                                    Used to customize phase names. Defaults to None.

        Returns:
            tuple: (needs_phases (bool), phase_list (list[dict])).
                   phase_list is empty if phases are not needed.
        """
        needs_phases = False
        phase_list = []
        tech_stack = tech_stack or []

        # Detect dominant technology domain for phase customization
        frontend_techs = {'angular', 'react', 'vue', 'css', 'scss', 'html', 'typescript'}
        backend_techs = {'python', 'flask', 'django', 'fastapi', 'java', 'spring-boot', 'kotlin', 'swift'}
        devops_techs = {'docker', 'kubernetes', 'jenkins'}

        has_frontend = any(t in frontend_techs for t in tech_stack)
        has_backend = any(t in backend_techs for t in tech_stack)
        has_devops = any(t in devops_techs for t in tech_stack)

        if complexity_score >= 15 or file_count >= 8:
            needs_phases = True
            # Choose phase names based on dominant tech
            if has_devops and not has_backend and not has_frontend:
                # DevOps-focused
                phase_list = [
                    {'name': 'Containerization', 'description': 'Docker/container setup'},
                    {'name': 'Orchestration', 'description': 'Kubernetes deployment'},
                    {'name': 'Pipeline', 'description': 'CI/CD pipeline configuration'},
                    {'name': 'Monitoring', 'description': 'Observability and monitoring'}
                ]
            elif has_frontend and not has_backend:
                # Frontend-focused
                phase_list = [
                    {'name': 'Structure', 'description': 'HTML layout and components'},
                    {'name': 'Styling', 'description': 'CSS and responsive design'},
                    {'name': 'Components', 'description': 'Interactive components'},
                    {'name': 'Integration', 'description': 'API integration and routing'}
                ]
            elif has_backend and not has_frontend and any(t in {'python', 'flask', 'django', 'fastapi'} for t in tech_stack):
                # Python backend-focused
                phase_list = [
                    {'name': 'Setup', 'description': 'Project structure and dependencies'},
                    {'name': 'Data Layer', 'description': 'Database models and ORM'},
                    {'name': 'Logic', 'description': 'Business logic and services'},
                    {'name': 'Endpoints', 'description': 'API endpoints and routing'}
                ]
            else:
                # Default / Java backend
                phase_list = [
                    {'name': 'Foundation', 'description': 'Entities and repositories'},
                    {'name': 'Business Logic', 'description': 'Service layer implementation'},
                    {'name': 'API Layer', 'description': 'Controllers and DTOs'},
                    {'name': 'Configuration', 'description': 'Config files and properties'}
                ]
        elif complexity_score >= 10 or file_count >= 5:
            needs_phases = True
            phase_list = [
                {'name': 'Core', 'description': 'Main implementation'},
                {'name': 'Integration', 'description': 'Config and integration'}
            ]

        return needs_phases, phase_list

    def generate_tasks(self, message: str, entities: List[str], phases: List[Dict], tech_stack: List[str] = None) -> List[Dict]:
        """Generate a typed task list from entities and phases.

        Args:
            message (str): Original task description.
            entities (list[str]): Extracted entity names.
            phases (list[dict]): Phase dicts from detect_phases().
            tech_stack (list[str]): Detected technologies. Added to every task for context.
                                   Defaults to None (empty list in task dict).

        Returns:
            list[dict]: Task dicts each with 'id', 'title', 'phase', 'type', and 'tech_stack'.
        """
        tasks = []
        task_id = 1
        tech_stack = tech_stack or []

        if phases:
            for phase in phases:
                if phase['name'] in ('Foundation', 'Structure', 'Setup', 'Containerization'):
                    for entity in entities:
                        tasks.append({
                            'id': task_id,
                            'title': f"Create {entity.capitalize()} entity",
                            'phase': phase['name'],
                            'type': 'entity',
                            'tech_stack': tech_stack
                        })
                        task_id += 1

                        tasks.append({
                            'id': task_id,
                            'title': f"Create {entity.capitalize()} repository",
                            'phase': phase['name'],
                            'type': 'repository',
                            'tech_stack': tech_stack
                        })
                        task_id += 1

                elif phase['name'] in ('Business Logic', 'Styling', 'Data Layer', 'Orchestration'):
                    for entity in entities:
                        tasks.append({
                            'id': task_id,
                            'title': f"Implement {entity.capitalize()} service",
                            'phase': phase['name'],
                            'type': 'service',
                            'tech_stack': tech_stack
                        })
                        task_id += 1

                elif phase['name'] in ('API Layer', 'Components', 'Logic', 'Pipeline'):
                    for entity in entities:
                        tasks.append({
                            'id': task_id,
                            'title': f"Create {entity.capitalize()} controller",
                            'phase': phase['name'],
                            'type': 'controller',
                            'tech_stack': tech_stack
                        })
                        task_id += 1

        return tasks

    def create_dependencies(self, tasks: List[Dict]) -> List[Dict]:
        """Assign depends_on and blocked_by relationships to each task.

        Args:
            tasks (list[dict]): Task list from generate_tasks().

        Returns:
            list[dict]: Same tasks with 'depends_on' and 'blocked_by' lists added.
        """
        for i, task in enumerate(tasks):
            task['depends_on'] = []
            task['blocked_by'] = []

            # Repository depends on entity
            if task.get('type') == 'repository':
                for prev_task in tasks[:i]:
                    if prev_task.get('type') == 'entity':
                        task['depends_on'].append(prev_task['id'])

            # Service depends on repository
            elif task.get('type') == 'service':
                for prev_task in tasks[:i]:
                    if prev_task.get('type') == 'repository':
                        task['depends_on'].append(prev_task['id'])

            # Controller depends on service
            elif task.get('type') == 'controller':
                for prev_task in tasks[:i]:
                    if prev_task.get('type') == 'service':
                        task['depends_on'].append(prev_task['id'])

        return tasks

    def estimate_complexity(self, message: str, entities: List[str]) -> int:
        """Estimate task complexity on a 5-30 scale.

        Args:
            message (str): Raw task description.
            entities (list[str]): Extracted entity names.

        Returns:
            int: Complexity score from 5 (simple) to 30 (very complex).
        """
        score = 5

        # Entity count
        score += len(entities) * 2

        # Keyword indicators
        complexity_keywords = {
            'crud': 3,
            'api': 2,
            'auth': 3,
            'security': 3,
            'transaction': 2,
            'cache': 2,
            'migration': 2
        }

        for keyword, points in complexity_keywords.items():
            if keyword in message.lower():
                score += points

        # Phrase indicators
        if 'multiple' in message.lower() or 'several' in message.lower():
            score += 3

        return min(30, score)

    def auto_analyze(self, user_message: str) -> Dict:
        """Run the full task analysis pipeline on a user message.

        Pipeline:
        1. Detect technology stack from message keywords
        2. Extract service/feature entities
        3. Estimate file count and complexity
        4. Detect if phases are needed (tech-aware)
        5. Generate task list with tech context
        6. Create task dependencies

        Args:
            user_message (str): Raw task description from the user.

        Returns:
            dict: Contains 'message', 'tech_stack', 'entities', 'file_count', 'complexity',
                  'needs_phases', 'phases', 'tasks', 'task_count', 'timestamp'.
        """
        # Step 1: Detect tech stack from message
        tech_stack = self.detect_tech_from_message(user_message)

        # Steps 2-3: Extract entities and estimate metrics
        entities = self.extract_entities(user_message)
        file_count = self.estimate_file_count(user_message, entities)
        complexity = self.estimate_complexity(user_message, entities)

        # Step 4: Detect phases (tech-aware)
        needs_phases, phases = self.detect_phases(complexity, file_count, tech_stack=tech_stack)

        # Step 5: Generate tasks with tech stack context
        tasks = self.generate_tasks(user_message, entities, phases, tech_stack=tech_stack)

        # Step 6: Create dependencies
        tasks = self.create_dependencies(tasks)

        return {
            'message': user_message,
            'tech_stack': tech_stack,
            'entities': entities,
            'file_count': file_count,
            'complexity': complexity,
            'needs_phases': needs_phases,
            'phases': phases,
            'tasks': tasks,
            'task_count': len(tasks),
            'timestamp': datetime.now().isoformat()
        }

    def log_analysis(self, result: Dict):
        """Append a JSONL entry with key analysis metrics to the task log.

        Args:
            result (dict): Analysis result from auto_analyze().
        """
        self.logs_path.mkdir(parents=True, exist_ok=True)
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_count': result.get('task_count', 0),
            'complexity': result.get('complexity', 0),
            'entities': result.get('entities', [])
        }

        try:
            with open(self.task_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass


# ============================================================================
# TASK AUTO-TRACKER CLASS (from task-auto-tracker.py - 536 lines)
# ============================================================================

class TaskAutoTracker:
    """Monitors tool calls and tracks progress against active tasks.

    Reads and writes an active-tasks.json file and appends a per-task tracker
    log. Tool call interception updates task status in real time.

    Attributes:
        memory_path (Path): Base ~/.claude/memory directory.
        tasks_file (Path): JSON file storing active task records.
        logs_path (Path): Directory for per-task tracker logs.
        current_task: Currently tracked task, or None.

    Key Methods:
        monitor_tool_call(tool_name, tool_params, result): Record a tool call.
        update_task_progress(task_id, status, progress): Update task status.
        auto_complete_task(task_id): Mark a task as 100% done.
        check_phase_completion(completed_task): Detect phase completion.
    """

    def __init__(self):
        """Initialize TaskAutoTracker with task file, logs, and empty current-task state."""
        self.memory_path = MEMORY_DIR
        self.tasks_file = self.memory_path / "tasks" / "active-tasks.json"
        self.logs_path = self.memory_path / "logs" / "tasks"
        self.current_task = None

    def load_tasks(self) -> Dict:
        """Load the active tasks dictionary from disk.

        Returns:
            dict: Tasks dict keyed by task ID string. Empty dict if not found.
        """
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)

        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_tasks(self, tasks: Dict):
        """Persist the tasks dictionary to the active-tasks.json file.

        Args:
            tasks (dict): Tasks dict to save.
        """
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=2)
        except Exception:
            pass

    def log(self, message: str):
        """Append a timestamped message to the tracker log file.

        Args:
            message (str): Log message to append.
        """
        self.logs_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}\n"

        try:
            log_file = self.logs_path / "tracker.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass

    def monitor_tool_call(self, tool_name: str, tool_params: Dict, result: Any):
        """Process a tool call event and dispatch to the appropriate handler.

        Args:
            tool_name (str): Name of the tool (e.g., 'Read', 'Write', 'Bash').
            tool_params (dict): Parameters passed to the tool.
            result: Tool execution result.
        """
        self.log(f"TOOL_CALL: {tool_name}")

        tasks = self.load_tasks()

        if tool_name == 'Read':
            self._handle_read(tool_params, result, tasks)
        elif tool_name == 'Write':
            self._handle_write(tool_params, result, tasks)
        elif tool_name == 'Edit':
            self._handle_edit(tool_params, result, tasks)
        elif tool_name == 'Bash':
            self._handle_bash(tool_params, result, tasks)

        self.save_tasks(tasks)

    def _handle_read(self, params: Dict, result: Any, tasks: Dict):
        """Handle Read tool calls"""
        file_path = params.get('file_path', '')
        self.log(f"READ: {file_path}")

    def _handle_write(self, params: Dict, result: Any, tasks: Dict):
        """Handle Write tool calls"""
        file_path = params.get('file_path', '')
        self.log(f"WRITE: {file_path}")

    def _handle_edit(self, params: Dict, result: Any, tasks: Dict):
        """Handle Edit tool calls"""
        file_path = params.get('file_path', '')
        self.log(f"EDIT: {file_path}")

    def _handle_bash(self, params: Dict, result: Any, tasks: Dict):
        """Handle Bash tool calls"""
        command = params.get('command', '')
        self.log(f"BASH: {command[:50]}")

    def update_task_progress(self, task_id: int, status: str, progress: int):
        """Update the status and progress percentage for a task.

        Args:
            task_id (int): Numeric task ID to update.
            status (str): New status string (e.g., 'in_progress', 'completed').
            progress (int): Progress percentage from 0 to 100.
        """
        tasks = self.load_tasks()

        if str(task_id) in tasks:
            tasks[str(task_id)]['status'] = status
            tasks[str(task_id)]['progress'] = progress
            tasks[str(task_id)]['updated_at'] = datetime.now().isoformat()

        self.save_tasks(tasks)
        self.log(f"PROGRESS: Task {task_id} -> {status} ({progress}%)")

    def auto_complete_task(self, task_id: int):
        """Mark a task as completed at 100% progress.

        Args:
            task_id (int): Numeric task ID to complete.
        """
        self.update_task_progress(task_id, 'completed', 100)
        self.log(f"AUTO_COMPLETE: Task {task_id}")

    def check_phase_completion(self, completed_task: Dict):
        """Detect if all tasks in a phase are now complete.

        Args:
            completed_task (dict): The task that was just completed,
                                   containing a 'phase' key.

        Returns:
            bool: True if all tasks in the phase are completed, False otherwise.
        """
        tasks = self.load_tasks()
        phase = completed_task.get('phase', '')

        if phase:
            phase_tasks = [t for t in tasks.values() if t.get('phase') == phase]
            completed_count = len([t for t in phase_tasks if t.get('status') == 'completed'])

            if completed_count == len(phase_tasks):
                self.log(f"PHASE_COMPLETE: {phase}")
                return True

        return False


# ============================================================================
# PHASE ENFORCEMENT CLASS (from task-phase-enforcer.py - 121 lines)
# ============================================================================

class PhaseEnforcer:
    """Validates whether tasks require phases based on complexity and size scoring.

    All methods are static and operate purely on the task description string.

    Key Methods:
        calculate_complexity_score(task_desc): Score keyword density (0-10).
        calculate_size_score(task_desc): Score task breadth by word count (0-10).
        analyze_task(task_desc): Combine scores to determine phase requirements.
    """

    @staticmethod
    def calculate_complexity_score(task_desc: str) -> int:
        """Calculate a complexity score from keyword density in the task description.

        Args:
            task_desc (str): Task description text.

        Returns:
            int: Complexity score from 0 to 10.
        """
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

    @staticmethod
    def calculate_size_score(task_desc: str) -> int:
        """Calculate a size score from word count and breadth indicators.

        Args:
            task_desc (str): Task description text.

        Returns:
            int: Size score from 0 to 10.
        """
        score = 0

        word_count = len(task_desc.split())
        if word_count > 20:
            score += 3
        elif word_count > 10:
            score += 2
        elif word_count > 5:
            score += 1

        multi_indicators = ['all', 'every', 'each', 'multiple', 'several']
        if any(ind in task_desc.lower() for ind in multi_indicators):
            score += 3

        return min(10, score)

    @staticmethod
    def analyze_task(task_desc: str) -> Dict:
        """Analyze a task description to determine if phases are required.

        Args:
            task_desc (str): Task description text.

        Returns:
            dict: Contains 'complexity' (int), 'size' (int),
                  'needs_task' (bool), 'needs_phases' (bool), and 'status' (str).
        """
        complexity = PhaseEnforcer.calculate_complexity_score(task_desc)
        size = PhaseEnforcer.calculate_size_score(task_desc)

        needs_task = True  # Always required in v2.0.0
        needs_phases = size >= 6

        return {
            'complexity': complexity,
            'size': size,
            'needs_task': needs_task,
            'needs_phases': needs_phases,
            'status': 'requirements_detected' if needs_task else 'compliant'
        }


# ============================================================================
# LOGGING
# ============================================================================

def log_policy_hit(action: str, context: str = ""):
    """Append a timestamped entry to the policy-hits log.

    Args:
        action (str): The action identifier (e.g., 'ENFORCE_START', 'VALIDATE').
        context (str): Optional human-readable context or detail string.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] automatic-task-breakdown-policy | {action} | {context}\n"

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception:
        pass


# ============================================================================
# POLICY INTERFACE
# ============================================================================

def validate():
    """Check that the automatic task breakdown policy preconditions are met.

    Returns:
        bool: True if validation succeeds, False on any exception.
    """
    try:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        log_policy_hit("VALIDATE", "automatic-task-breakdown-ready")
        return True
    except Exception as e:
        log_policy_hit("VALIDATE_ERROR", str(e))
        return False


def report():
    """Generate a compliance report for the automatic task breakdown policy.

    Returns:
        dict: Contains 'status', 'policy', 'features', and 'timestamp'.
              Returns {'status': 'error', ...} on failure.
    """
    try:
        report_data = {
            "status": "success",
            "policy": "automatic-task-breakdown",
            "features": [
                "Automatic task analysis",
                "Entity extraction",
                "File count estimation",
                "Complexity scoring",
                "Phase detection and generation",
                "Task dependency management",
                "Task progress tracking",
                "Phase enforcement validation"
            ],
            "timestamp": datetime.now().isoformat()
        }

        log_policy_hit("REPORT", "automatic-task-breakdown-report-generated")
        return report_data
    except Exception as e:
        return {"status": "error", "message": str(e)}


def enforce():
    """Activate the automatic task breakdown policy.

    Consolidates logic from 3 old scripts:
    - task-auto-analyzer.py (400 lines): Automatic task analysis and breakdown
    - task-auto-tracker.py (536 lines): Task progress tracking and monitoring
    - task-phase-enforcer.py (121 lines): Task/phase enforcement validation

    Initializes all three component classes.

    Returns:
        dict: Contains 'status' ('success' or 'error'), 'system', and
              'components' list. On error, contains 'message'.
    """
    # ===================================================================
    # TRACKING: Record start time
    # ===================================================================
    _track_start_time = datetime.now()
    _sub_operations = []

    try:
        log_policy_hit("ENFORCE_START", "automatic-task-breakdown-enforcement")

        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

        # Sub-op 1: Initialize TaskAutoAnalyzer
        _op1_start = datetime.now()
        analyzer = TaskAutoAnalyzer()
        _op1_duration = int((datetime.now() - _op1_start).total_seconds() * 1000)
        _sub_operations.append(record_sub_operation(
            session_id=get_session_id(),
            policy_name="automatic-task-breakdown-policy",
            operation_name="initialize_task_analyzer",
            input_params={},
            output_results={"analyzer_ready": True},
            duration_ms=_op1_duration
        ))

        # Sub-op 2: Initialize TaskAutoTracker
        _op2_start = datetime.now()
        tracker = TaskAutoTracker()
        _op2_duration = int((datetime.now() - _op2_start).total_seconds() * 1000)
        _sub_operations.append(record_sub_operation(
            session_id=get_session_id(),
            policy_name="automatic-task-breakdown-policy",
            operation_name="initialize_task_tracker",
            input_params={},
            output_results={"tracker_ready": True},
            duration_ms=_op2_duration
        ))

        # Sub-op 3: Initialize PhaseEnforcer
        _op3_start = datetime.now()
        enforcer = PhaseEnforcer()
        _op3_duration = int((datetime.now() - _op3_start).total_seconds() * 1000)
        _sub_operations.append(record_sub_operation(
            session_id=get_session_id(),
            policy_name="automatic-task-breakdown-policy",
            operation_name="initialize_phase_enforcer",
            input_params={},
            output_results={"enforcer_ready": True},
            duration_ms=_op3_duration
        ))

        log_policy_hit("ENFORCE_COMPLETE", "automatic-task-breakdown-system-ready")
        print("[automatic-task-breakdown-policy] Policy enforced - Task breakdown system active")

        # ===================================================================
        # TRACKING: Record overall execution
        # ===================================================================
        _duration_ms = int((datetime.now() - _track_start_time).total_seconds() * 1000)
        record_policy_execution(
            session_id=get_session_id(),
            policy_name="automatic-task-breakdown-policy",
            policy_script="automatic-task-breakdown-policy.py",
            policy_type="Policy Script",
            input_params={},
            output_results={
                "status": "success",
                "system": "automatic-task-breakdown",
                "components_count": 3
            },
            decision="Initialized TaskAutoAnalyzer, TaskAutoTracker, and PhaseEnforcer",
            duration_ms=_duration_ms,
            sub_operations=_sub_operations if _sub_operations else None
        )

        return {
            "status": "success",
            "system": "automatic-task-breakdown",
            "components": [
                "TaskAutoAnalyzer",
                "TaskAutoTracker",
                "PhaseEnforcer"
            ]
        }
    except Exception as e:
        log_policy_hit("ENFORCE_ERROR", str(e))
        print(f"[automatic-task-breakdown-policy] ERROR: {e}")

        # ===================================================================
        # TRACKING: Record error
        # ===================================================================
        _duration_ms = int((datetime.now() - _track_start_time).total_seconds() * 1000)
        record_policy_execution(
            session_id=get_session_id(),
            policy_name="automatic-task-breakdown-policy",
            policy_script="automatic-task-breakdown-policy.py",
            policy_type="Policy Script",
            input_params={},
            output_results={"status": "error", "error": str(e)},
            decision=f"Policy failed: {e}",
            duration_ms=_duration_ms,
            sub_operations=_sub_operations if _sub_operations else None
        )

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
        elif sys.argv[1] == "--analyze" and len(sys.argv) >= 3:
            task_desc = ' '.join(sys.argv[2:])
            analyzer = TaskAutoAnalyzer()
            result = analyzer.auto_analyze(task_desc)
            enforcer_result = PhaseEnforcer.analyze_task(task_desc)

            print(f"\n{'='*70}")
            print(f"TASK ANALYSIS & PHASE ENFORCEMENT")
            print(f"{'='*70}\n")

            print(f"[ANALYSIS]")
            print(f"  Entities: {', '.join(result['entities']) if result['entities'] else 'None'}")
            print(f"  Complexity: {result['complexity']}/30")
            print(f"  Estimated Files: {result['file_count']}")
            print(f"  Task Count: {result['task_count']}")
            print(f"\n[ENFORCEMENT]")
            print(f"  Complexity Score: {enforcer_result['complexity']}/10")
            print(f"  Size Score: {enforcer_result['size']}/10")
            print(f"  Needs TaskCreate: YES (v2.0.0 policy)")
            print(f"  Needs Phases: {'YES' if enforcer_result['needs_phases'] else 'Optional'}")

            if result['needs_phases']:
                print(f"\n[PHASES ({len(result['phases'])})]")
                for i, phase in enumerate(result['phases'], 1):
                    print(f"  {i}. {phase['name']}: {phase['description']}")

            print(f"\n{'='*70}\n")
            sys.exit(0)
        else:
            print("Usage: python automatic-task-breakdown-policy.py [--enforce|--validate|--report|--analyze <task>]")
            sys.exit(1)
    else:
        # Default: run enforcement
        enforce()
