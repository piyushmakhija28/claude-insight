#!/usr/bin/env python
"""
SESSION ID GENERATOR v1.0.0
============================

Generates unique session IDs for tracking purposes.
Every session and work item gets a traceable ID.

Format: SESS-YYYYMMDD-HHMMSS-XXXX
Example: SESS-20260216-143055-A7B3

Components:
- SESS = Session prefix
- YYYYMMDD = Date
- HHMMSS = Time
- XXXX = Random 4-char hash
"""

import os
import sys
import json
import hashlib
import random
import string
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

class SessionIDGenerator:
    """Generates and manages session IDs"""

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.sessions_dir = self.memory_path / 'sessions'
        self.current_session_file = self.memory_path / '.current-session.json'
        self.sessions_log = self.memory_path / 'logs' / 'sessions.log'

        # Ensure directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_log.parent.mkdir(parents=True, exist_ok=True)

    def generate_session_id(self, session_type='SESSION'):
        """Generate unique session ID"""
        now = datetime.now()

        # Format: TYPE-YYYYMMDD-HHMMSS-XXXX
        date_part = now.strftime('%Y%m%d')
        time_part = now.strftime('%H%M%S')

        # Random 4-char hash
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

        session_id = f"{session_type}-{date_part}-{time_part}-{random_chars}"

        return session_id

    def create_session(self, session_type='SESSION', description='', metadata=None):
        """Create a new session with ID and metadata"""
        session_id = self.generate_session_id(session_type)

        session_data = {
            'session_id': session_id,
            'type': session_type,
            'description': description,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'status': 'ACTIVE',
            'metadata': metadata or {},
            'tasks': [],
            'work_items': []
        }

        # Save session data
        session_file = self.sessions_dir / f'{session_id}.json'
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Update current session
        with open(self.current_session_file, 'w') as f:
            json.dump({
                'current_session_id': session_id,
                'started_at': datetime.now().isoformat()
            }, f, indent=2)

        # Log session
        self._log_session(session_id, 'CREATED', description)

        return session_id, session_data

    def get_current_session(self):
        """Get current active session ID"""
        if not self.current_session_file.exists():
            return None

        try:
            with open(self.current_session_file, 'r') as f:
                data = json.load(f)
                return data.get('current_session_id')
        except:
            return None

    def get_session_data(self, session_id):
        """Get session data by ID"""
        session_file = self.sessions_dir / f'{session_id}.json'
        if not session_file.exists():
            return None

        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except:
            return None

    def add_work_item(self, session_id, work_type, description, metadata=None):
        """Add a work item to session"""
        work_id = self.generate_session_id(work_type)

        work_item = {
            'work_id': work_id,
            'type': work_type,
            'description': description,
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'status': 'IN_PROGRESS',
            'metadata': metadata or {}
        }

        # Update session
        session_data = self.get_session_data(session_id)
        if session_data:
            session_data['work_items'].append(work_item)

            session_file = self.sessions_dir / f'{session_id}.json'
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

            self._log_session(session_id, 'WORK_ADDED', f'{work_type}: {description}')

        return work_id

    def complete_work_item(self, session_id, work_id, status='COMPLETED'):
        """Mark work item as completed"""
        session_data = self.get_session_data(session_id)
        if not session_data:
            return False

        for item in session_data['work_items']:
            if item['work_id'] == work_id:
                item['completed_at'] = datetime.now().isoformat()
                item['status'] = status
                break

        session_file = self.sessions_dir / f'{session_id}.json'
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        self._log_session(session_id, 'WORK_COMPLETED', work_id)
        return True

    def end_session(self, session_id, status='COMPLETED'):
        """End a session"""
        session_data = self.get_session_data(session_id)
        if not session_data:
            return False

        session_data['end_time'] = datetime.now().isoformat()
        session_data['status'] = status

        session_file = self.sessions_dir / f'{session_id}.json'
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Clear current session if it matches
        current = self.get_current_session()
        if current == session_id:
            if self.current_session_file.exists():
                self.current_session_file.unlink()

        self._log_session(session_id, 'ENDED', status)
        return True

    def display_session_banner(self, session_id, session_data=None):
        """Display session ID banner"""
        if not session_data:
            session_data = self.get_session_data(session_id)

        print("\n" + "="*80)
        print("[CLIPBOARD] SESSION ID FOR TRACKING")
        print("="*80)
        print(f"\n[U+1F194] Session ID: {session_id}")

        if session_data:
            print(f"[U+1F4C5] Started: {session_data['start_time'][:19]}")
            print(f"[CHART] Status: {session_data['status']}")
            if session_data.get('description'):
                print(f"[U+1F4DD] Description: {session_data['description']}")
            if session_data.get('work_items'):
                print(f"[WRENCH] Work Items: {len(session_data['work_items'])}")

        print("\n[BULB] Use this ID to track this session in logs and reports")
        print("="*80 + "\n")

    def list_recent_sessions(self, limit=10):
        """List recent sessions"""
        session_files = sorted(
            self.sessions_dir.glob('SESSION-*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        sessions = []
        for session_file in session_files[:limit]:
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    sessions.append(data)
            except:
                continue

        return sessions

    def get_session_stats(self, session_id):
        """Get session statistics"""
        session_data = self.get_session_data(session_id)
        if not session_data:
            return None

        start_time = datetime.fromisoformat(session_data['start_time'])
        end_time = datetime.fromisoformat(session_data['end_time']) if session_data.get('end_time') else datetime.now()

        duration = end_time - start_time

        work_items = session_data.get('work_items', [])
        completed_items = [w for w in work_items if w['status'] == 'COMPLETED']

        return {
            'session_id': session_id,
            'duration_seconds': duration.total_seconds(),
            'duration_formatted': str(duration).split('.')[0],
            'total_work_items': len(work_items),
            'completed_work_items': len(completed_items),
            'in_progress_work_items': len(work_items) - len(completed_items),
            'status': session_data['status']
        }

    def _log_session(self, session_id, event, details=''):
        """Log session event"""
        timestamp = datetime.now().isoformat()
        log_line = f"{timestamp} | {session_id} | {event} | {details}\n"

        with open(self.sessions_log, 'a') as f:
            f.write(log_line)


def main():
    """Main function"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Session ID Generator')
    parser.add_argument('action', choices=['create', 'current', 'display', 'list', 'stats', 'end'],
                       help='Action to perform')
    parser.add_argument('--type', default='SESSION', help='Session type')
    parser.add_argument('--description', default='', help='Session description')
    parser.add_argument('--session-id', help='Session ID (for display/stats/end)')
    parser.add_argument('--limit', type=int, default=10, help='Limit for list')

    args = parser.parse_args()

    generator = SessionIDGenerator()

    if args.action == 'create':
        session_id, session_data = generator.create_session(
            session_type=args.type,
            description=args.description
        )
        generator.display_session_banner(session_id, session_data)
        print(session_id)  # For easy capturing in scripts

    elif args.action == 'current':
        session_id = generator.get_current_session()
        if session_id:
            print(f"Current Session: {session_id}")
            generator.display_session_banner(session_id)
        else:
            print("No active session")
            sys.exit(1)

    elif args.action == 'display':
        session_id = args.session_id or generator.get_current_session()
        if session_id:
            generator.display_session_banner(session_id)
        else:
            print("No session ID provided and no active session")
            sys.exit(1)

    elif args.action == 'list':
        sessions = generator.list_recent_sessions(args.limit)
        print(f"\n[CLIPBOARD] Recent Sessions (last {args.limit}):\n")
        for session in sessions:
            status_icon = "[CHECK]" if session['status'] == 'COMPLETED' else "[CYCLE]"
            print(f"{status_icon} {session['session_id']}")
            print(f"   Started: {session['start_time'][:19]}")
            print(f"   Status: {session['status']}")
            if session.get('description'):
                print(f"   Description: {session['description']}")
            print()

    elif args.action == 'stats':
        session_id = args.session_id or generator.get_current_session()
        if not session_id:
            print("No session ID provided and no active session")
            sys.exit(1)

        stats = generator.get_session_stats(session_id)
        if stats:
            print(f"\n[CHART] Session Statistics: {session_id}\n")
            print(f"Duration: {stats['duration_formatted']}")
            print(f"Total Work Items: {stats['total_work_items']}")
            print(f"Completed: {stats['completed_work_items']}")
            print(f"In Progress: {stats['in_progress_work_items']}")
            print(f"Status: {stats['status']}")
        else:
            print(f"Session not found: {session_id}")
            sys.exit(1)

    elif args.action == 'end':
        session_id = args.session_id or generator.get_current_session()
        if not session_id:
            print("No session ID provided and no active session")
            sys.exit(1)

        if generator.end_session(session_id):
            print(f"[CHECK] Session ended: {session_id}")
        else:
            print(f"[CROSS] Failed to end session: {session_id}")
            sys.exit(1)


if __name__ == '__main__':
    main()
