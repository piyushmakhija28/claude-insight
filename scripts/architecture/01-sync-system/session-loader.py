#!/usr/bin/env python3
"""
Session Loader
Load session by ID for context reuse
"""

import json
import sys
from pathlib import Path
from datetime import datetime


class SessionLoader:
    def __init__(self):
        self.memory_dir = Path.home() / ".claude" / "memory"
        self.sessions_dir = self.memory_dir / "sessions"
        self.index_file = self.sessions_dir / "session-index.json"

    def load_session(self, session_id: str) -> dict:
        """Load session by ID"""

        print(f"\n{'='*70}")
        print(f"🔍 LOADING SESSION: {session_id}")
        print(f"{'='*70}\n")

        # Check if index exists
        if not self.index_file.exists():
            print(f"❌ Session index not found: {self.index_file}")
            print(f"   No sessions have been saved yet.")
            return None

        # Read index
        with open(self.index_file, 'r') as f:
            index = json.load(f)

        # Find session
        session = next((s for s in index['sessions'] if s['session_id'] == session_id), None)

        if not session:
            print(f"❌ Session {session_id} not found")
            print(f"\nAvailable sessions:")
            for s in index['sessions'][-5:]:  # Show last 5
                print(f"   • {s['session_id']} - {s['purpose']}")
            return None

        # Load session file
        session_file = self.memory_dir / session['file_path']

        if not session_file.exists():
            print(f"❌ Session file not found: {session_file}")
            return None

        with open(session_file, 'r') as f:
            content = f.read()

        # Display session info
        print(f"✅ Session Loaded Successfully!")
        print(f"\n{'='*70}")
        print(f"📊 SESSION INFO")
        print(f"{'='*70}")
        print(f"   ID:       {session['session_id']}")
        print(f"   Date:     {session['timestamp']}")
        print(f"   Project:  {session['project']}")
        print(f"   Purpose:  {session['purpose']}")
        print(f"   Tags:     {', '.join(session.get('tags', []))}")
        print(f"   Duration: {session.get('duration_minutes', 'N/A')} minutes")
        print(f"   Files:    {session.get('files_modified', 0)} modified")
        print(f"   Status:   {session.get('status', 'unknown')}")
        print(f"{'='*70}\n")

        # Display content
        print(f"📄 SESSION CONTENT:\n")
        print(content)

        return {
            'metadata': session,
            'content': content
        }

    def list_recent(self, limit: int = 10):
        """List recent sessions"""

        if not self.index_file.exists():
            print("❌ No sessions found")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)

        sessions = sorted(
            index['sessions'],
            key=lambda s: s['timestamp'],
            reverse=True
        )[:limit]

        print(f"\n{'='*70}")
        print(f"📋 RECENT SESSIONS (Last {limit})")
        print(f"{'='*70}\n")

        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session['session_id']}")
            print(f"   Date:    {session['timestamp']}")
            print(f"   Project: {session['project']}")
            print(f"   Purpose: {session['purpose']}")
            print(f"   Tags:    {', '.join(session.get('tags', []))}")
            print()

    def session_info(self, session_id: str):
        """Show session info without full content"""

        if not self.index_file.exists():
            print("❌ Session index not found")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)

        session = next((s for s in index['sessions'] if s['session_id'] == session_id), None)

        if not session:
            print(f"❌ Session {session_id} not found")
            return

        print(f"\n{'='*70}")
        print(f"📊 SESSION INFO: {session_id}")
        print(f"{'='*70}")
        print(f"   Timestamp:      {session['timestamp']}")
        print(f"   Project:        {session['project']}")
        print(f"   Purpose:        {session['purpose']}")
        print(f"   Tags:           {', '.join(session.get('tags', []))}")
        print(f"   Duration:       {session.get('duration_minutes', 'N/A')} minutes")
        print(f"   Files Modified: {session.get('files_modified', 0)}")
        print(f"   Status:         {session.get('status', 'unknown')}")
        print(f"   File Path:      {session['file_path']}")
        print(f"{'='*70}\n")


def main():
    """CLI interface"""

    if len(sys.argv) < 2:
        print("=" * 70)
        print("Session Loader")
        print("=" * 70)
        print("\nUsage:")
        print("  python session-loader.py COMMAND [OPTIONS]")
        print("\nCommands:")
        print("  load SESSION_ID       - Load session by ID")
        print("  info SESSION_ID       - Show session info")
        print("  list [LIMIT]          - List recent sessions (default: 10)")
        print("\nExamples:")
        print("  python session-loader.py load 20260216-1430-a3f7")
        print("  python session-loader.py info 20260216-1430-a3f7")
        print("  python session-loader.py list 20")
        sys.exit(1)

    command = sys.argv[1]
    loader = SessionLoader()

    if command == "load":
        if len(sys.argv) < 3:
            print("❌ Error: SESSION_ID required")
            print("Usage: python session-loader.py load SESSION_ID")
            sys.exit(1)
        session_id = sys.argv[2]
        loader.load_session(session_id)

    elif command == "info":
        if len(sys.argv) < 3:
            print("❌ Error: SESSION_ID required")
            print("Usage: python session-loader.py info SESSION_ID")
            sys.exit(1)
        session_id = sys.argv[2]
        loader.session_info(session_id)

    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        loader.list_recent(limit)

    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: load, info, list")
        sys.exit(1)


if __name__ == "__main__":
    main()
