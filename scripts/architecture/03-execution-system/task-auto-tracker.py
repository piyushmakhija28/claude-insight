#!/usr/bin/env python3
"""
Automatic Task Status Tracker
Monitors Claude's tool calls and auto-updates task status
"""

import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class TaskAutoTracker:
    """
    Automatically tracks and updates task status
    """

    def __init__(self):
        self.tasks_file = Path.home() / ".claude" / "memory" / "active_tasks.json"
        self.log_file = Path.home() / ".claude" / "memory" / "logs" / "task-tracking.log"
        self.active_tasks = self.load_tasks()
        self.tool_call_log = Path.home() / ".claude" / "memory" / "logs" / "tool-calls.log"

    def load_tasks(self) -> Dict:
        """Load active tasks"""
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        return {}

    def save_tasks(self):
        """Save tasks state"""
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tasks_file, 'w') as f:
            json.dump(self.active_tasks, f, indent=2)

    def log(self, message: str):
        """Log tracking activity"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")

    def monitor_tool_call(self, tool_name: str, tool_params: Dict, result: Any):
        """
        Monitor a tool call and auto-update related task
        """
        self.log(f"Tool call detected: {tool_name} with params: {tool_params}")

        # Find related task
        related_task = self.find_related_task(tool_name, tool_params)

        if not related_task:
            self.log("No related task found")
            return

        task_id = related_task['id']
        self.log(f"Related task: {task_id} - {related_task['subject']}")

        # Update based on tool type
        if tool_name == 'Read':
            self._handle_read(task_id, tool_params, result)

        elif tool_name == 'Write':
            self._handle_write(task_id, tool_params, result)

        elif tool_name == 'Edit':
            self._handle_edit(task_id, tool_params, result)

        elif tool_name == 'Bash':
            self._handle_bash(task_id, tool_params, result)

        elif tool_name == 'Glob':
            self._handle_glob(task_id, tool_params, result)

        elif tool_name == 'Grep':
            self._handle_grep(task_id, tool_params, result)

        # Save updated state
        self.save_tasks()

    def find_related_task(self, tool_name: str, tool_params: Dict) -> Optional[Dict]:
        """
        Find which task this tool call relates to
        """
        # Get currently in-progress tasks
        in_progress_tasks = [
            task for task in self.active_tasks.values()
            if task.get('status') == 'in_progress'
        ]

        if not in_progress_tasks:
            return None

        # Match by file path
        if tool_name in ['Read', 'Write', 'Edit']:
            file_path = tool_params.get('file_path', '')

            for task in in_progress_tasks:
                task_file = task.get('file_path', '')
                if task_file and task_file in file_path:
                    return task

        # Return first in-progress task as fallback
        return in_progress_tasks[0] if in_progress_tasks else None

    def _handle_read(self, task_id: str, params: Dict, result: Any):
        """Handle Read tool call"""
        file_path = params.get('file_path', '')
        filename = file_path.split('/')[-1]

        # Determine if reading example or target
        if any(keyword in file_path.lower() for keyword in ['example', 'user-service', 'auth-service']):
            step = f"Reading example: {filename}"
            progress_inc = 10
        else:
            step = f"Analyzing: {filename}"
            progress_inc = 5

        self.update_task_progress(
            task_id,
            current_step=step,
            progress_increment=progress_inc,
            activity=f"Read {filename}"
        )

    def _handle_write(self, task_id: str, params: Dict, result: Any):
        """Handle Write tool call"""
        file_path = params.get('file_path', '')
        filename = file_path.split('/')[-1]

        task = self.active_tasks.get(task_id)
        if not task:
            return

        # Major progress for file creation
        self.update_task_progress(
            task_id,
            current_step=f"Created {filename}",
            progress_increment=40,
            completed_items=[filename],
            activity=f"Wrote {filename}"
        )

        # Check if this completes the task
        if task.get('type') == 'file_creation':
            # If file is created, task is mostly done
            current_progress = task.get('metadata', {}).get('progress', 0)
            if current_progress + 40 >= 90:
                # Mark as near completion, verification pending
                self.update_task_progress(
                    task_id,
                    current_step="File created, pending verification",
                    progress_increment=0,
                    next_items=["Build verification", "Syntax check"]
                )

    def _handle_edit(self, task_id: str, params: Dict, result: Any):
        """Handle Edit tool call"""
        file_path = params.get('file_path', '')
        filename = file_path.split('/')[-1]

        self.update_task_progress(
            task_id,
            current_step=f"Modified {filename}",
            progress_increment=30,
            completed_items=[f"Updated {filename}"],
            activity=f"Edited {filename}"
        )

    def _handle_bash(self, task_id: str, params: Dict, result: Any):
        """Handle Bash tool call"""
        command = params.get('command', '')

        # Detect build commands
        if any(cmd in command for cmd in ['mvn clean install', 'mvn compile', 'mvn package']):
            self.update_task_progress(
                task_id,
                current_step="Building project",
                progress_increment=15,
                activity="Maven build"
            )

            # Check build result
            if result and 'BUILD SUCCESS' in str(result):
                self.update_task_progress(
                    task_id,
                    current_step="Build successful ✅",
                    progress_increment=10,
                    completed_items=["Build verification"],
                    activity="Build passed"
                )

                # Auto-complete verification tasks
                self._complete_verification_tasks("Build successful")

            elif result and 'BUILD FAILURE' in str(result):
                self.update_task_progress(
                    task_id,
                    current_step="Build failed ❌",
                    progress_increment=0,
                    blockers=["Build errors need fixing"],
                    activity="Build failed"
                )

        # Detect test commands
        elif any(cmd in command for cmd in ['mvn test', 'npm test', 'pytest']):
            self.update_task_progress(
                task_id,
                current_step="Running tests",
                progress_increment=10,
                activity="Testing"
            )

            if result and any(keyword in str(result) for keyword in ['PASS', 'SUCCESS', 'OK']):
                self.update_task_progress(
                    task_id,
                    current_step="Tests passed ✅",
                    progress_increment=15,
                    completed_items=["Tests verification"],
                    activity="Tests passed"
                )

        # Detect curl/API testing
        elif 'curl' in command:
            endpoint = self._extract_endpoint(command)
            self.update_task_progress(
                task_id,
                current_step=f"Testing endpoint: {endpoint}",
                progress_increment=10,
                activity=f"API test: {endpoint}"
            )

            # Check response
            if result and '200' in str(result):
                self.update_task_progress(
                    task_id,
                    current_step=f"Endpoint working ✅",
                    progress_increment=10,
                    completed_items=[f"{endpoint} verified"],
                    activity="API test passed"
                )

    def _handle_glob(self, task_id: str, params: Dict, result: Any):
        """Handle Glob tool call"""
        pattern = params.get('pattern', '')

        self.update_task_progress(
            task_id,
            current_step=f"Searching files: {pattern}",
            progress_increment=5,
            activity=f"File search: {pattern}"
        )

    def _handle_grep(self, task_id: str, params: Dict, result: Any):
        """Handle Grep tool call"""
        pattern = params.get('pattern', '')

        self.update_task_progress(
            task_id,
            current_step=f"Searching code: {pattern}",
            progress_increment=5,
            activity=f"Code search: {pattern}"
        )

    def update_task_progress(
        self,
        task_id: str,
        current_step: str = None,
        progress_increment: int = 0,
        completed_items: List[str] = None,
        next_items: List[str] = None,
        blockers: List[str] = None,
        activity: str = None
    ):
        """
        Update task progress with metadata
        """
        task = self.active_tasks.get(task_id)
        if not task:
            return

        metadata = task.get('metadata', {})

        # Update progress
        current_progress = metadata.get('progress', 0)
        new_progress = min(current_progress + progress_increment, 100)
        metadata['progress'] = new_progress

        # Update current step
        if current_step:
            metadata['current_step'] = current_step

        # Update completed items
        if completed_items:
            existing = metadata.get('completed_items', [])
            metadata['completed_items'] = existing + completed_items

        # Update next items
        if next_items:
            metadata['next_items'] = next_items

        # Update blockers
        if blockers:
            existing_blockers = metadata.get('blockers', [])
            metadata['blockers'] = existing_blockers + blockers

        # Add activity log
        if activity:
            activity_log = metadata.get('activity_log', [])
            activity_log.append({
                'timestamp': datetime.now().isoformat(),
                'activity': activity,
                'progress': new_progress
            })
            metadata['activity_log'] = activity_log[-20:]  # Keep last 20

        # Update timestamp
        metadata['last_updated'] = datetime.now().isoformat()

        task['metadata'] = metadata

        self.log(f"Updated task {task_id}: {current_step}, progress: {new_progress}%")

        # Auto-complete if 100%
        if new_progress >= 100:
            self.auto_complete_task(task_id)

    def auto_complete_task(self, task_id: str):
        """
        Automatically mark task as completed
        """
        task = self.active_tasks.get(task_id)
        if not task:
            return

        task['status'] = 'completed'
        task['metadata']['completed_at'] = datetime.now().isoformat()
        task['metadata']['progress'] = 100

        self.log(f"✅ Auto-completed task: {task_id} - {task['subject']}")

        # Check phase completion
        self.check_phase_completion(task)

        # Unlock dependent tasks
        self.unlock_dependent_tasks(task_id)

    def check_phase_completion(self, completed_task: Dict):
        """
        Check if all tasks in a phase are complete
        """
        phase_name = completed_task.get('phase')
        if not phase_name:
            return

        # Get all tasks in this phase
        phase_tasks = [
            task for task in self.active_tasks.values()
            if task.get('phase') == phase_name
        ]

        # Check if all complete
        all_complete = all(t.get('status') == 'completed' for t in phase_tasks)

        if all_complete:
            self.on_phase_complete(phase_name)

    def on_phase_complete(self, phase_name: str):
        """
        Handle phase completion
        """
        self.log(f"✅ PHASE COMPLETE: {phase_name}")
        print(f"\n{'='*80}")
        print(f"✅ PHASE COMPLETE: {phase_name}")
        print(f"{'='*80}\n")

        # Trigger auto-commit for phase
        # This would integrate with git-auto-commit-policy.md

    def unlock_dependent_tasks(self, completed_task_id: str):
        """
        Unlock tasks that depend on this one
        """
        completed_task = self.active_tasks.get(completed_task_id)
        if not completed_task:
            return

        completed_subject = completed_task.get('subject')

        # Find tasks that depend on this one
        for task_id, task in self.active_tasks.items():
            dependencies = task.get('dependencies', [])

            if completed_subject in dependencies:
                # Remove this dependency
                dependencies.remove(completed_subject)
                task['dependencies'] = dependencies

                # If no more dependencies, unlock
                if not dependencies:
                    task['blocked'] = False
                    self.log(f"🔓 Unlocked task: {task_id} - {task['subject']}")

    def _complete_verification_tasks(self, reason: str):
        """
        Auto-complete verification tasks when build/tests pass
        """
        for task_id, task in self.active_tasks.items():
            if task.get('type') == 'verification' and task.get('status') == 'in_progress':
                self.update_task_progress(
                    task_id,
                    current_step=f"Verified: {reason}",
                    progress_increment=100,
                    completed_items=[reason]
                )

    def _extract_endpoint(self, curl_command: str) -> str:
        """Extract API endpoint from curl command"""
        match = re.search(r'https?://[^\s]+', curl_command)
        if match:
            url = match.group(0)
            # Extract path
            parts = url.split('/')
            if len(parts) > 3:
                return '/' + '/'.join(parts[3:])
        return "unknown"


class ToolCallMonitor(FileSystemEventHandler):
    """
    Monitor tool call log file for changes
    """

    def __init__(self, tracker: TaskAutoTracker):
        self.tracker = tracker
        self.last_position = 0

    def on_modified(self, event):
        """Handle file modification"""
        if event.src_path != str(self.tracker.tool_call_log):
            return

        # Read new lines
        with open(self.tracker.tool_call_log, 'r') as f:
            f.seek(self.last_position)
            new_lines = f.readlines()
            self.last_position = f.tell()

        # Process new tool calls
        for line in new_lines:
            self.process_tool_call(line)

    def process_tool_call(self, line: str):
        """Process a tool call log entry"""
        try:
            # Parse log line (format: [timestamp] tool_name: params -> result)
            match = re.match(r'\[.*?\] (\w+): (.*?) -> (.*)', line)
            if match:
                tool_name, params_str, result_str = match.groups()

                # Parse params and result
                params = json.loads(params_str) if params_str != 'None' else {}
                result = result_str if result_str != 'None' else None

                # Monitor
                self.tracker.monitor_tool_call(tool_name, params, result)

        except Exception as e:
            self.tracker.log(f"Error processing tool call: {e}")


def start_monitoring():
    """
    Start the auto-tracker daemon
    """
    print("🤖 Starting Task Auto-Tracker...")

    tracker = TaskAutoTracker()

    # Setup file watcher
    event_handler = ToolCallMonitor(tracker)
    observer = Observer()

    watch_dir = tracker.tool_call_log.parent
    watch_dir.mkdir(parents=True, exist_ok=True)

    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()

    print(f"✅ Monitoring: {tracker.tool_call_log}")
    print("✅ Auto-tracking enabled")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Stopping Task Auto-Tracker...")

    observer.join()


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'start':
        start_monitoring()
    else:
        print("Usage:")
        print("  python task-auto-tracker.py start  # Start monitoring daemon")


if __name__ == "__main__":
    main()
