"""
Collaboration Manager
Handles real-time collaboration sessions for widget building.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import random


class CollaborationSessionManager:
    """Manages real-time collaboration sessions for widgets."""

    def __init__(self, base_dir: str = None):
        """Initialize the collaboration manager.

        Args:
            base_dir: Base directory for collaboration storage. Defaults to ~/.claude/memory/community
        """
        if base_dir is None:
            base_dir = os.path.expanduser("~/.claude/memory/community")

        self.base_dir = Path(base_dir)
        self.collab_dir = self.base_dir / "collaboration"
        self.collab_dir.mkdir(parents=True, exist_ok=True)

        self.active_sessions_file = self.collab_dir / "active_sessions.json"

        # User colors for cursor display
        self.user_colors = [
            "#FF5733", "#33FF57", "#3357FF", "#FF33F5",
            "#33FFF5", "#F5FF33", "#FF8C33", "#8C33FF"
        ]

    def _get_session_file(self, session_id: str) -> Path:
        """Get the path to a session detail file."""
        return self.collab_dir / f"{session_id}.json"

    def _atomic_write(self, filepath: Path, data: dict):
        """Atomically write JSON data to file."""
        temp_file = filepath.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(filepath)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"collab_{timestamp}_{os.urandom(3).hex()}"

    def _load_active_sessions(self) -> dict:
        """Load active sessions data."""
        if not self.active_sessions_file.exists():
            return {"sessions": []}

        with open(self.active_sessions_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_active_sessions(self, data: dict):
        """Save active sessions data."""
        self._atomic_write(self.active_sessions_file, data)

    def _assign_user_color(self, used_colors: List[str]) -> str:
        """Assign a unique color to a user.

        Args:
            used_colors: List of colors already assigned

        Returns:
            Color hex code
        """
        available = [c for c in self.user_colors if c not in used_colors]
        if available:
            return random.choice(available)
        return random.choice(self.user_colors)

    def create_session(self, widget_id: str, creator: str,
                      session_duration_hours: int = 2) -> dict:
        """Create a new collaboration session.

        Args:
            widget_id: Widget identifier
            creator: Username creating the session
            session_duration_hours: Session duration in hours

        Returns:
            New session data
        """
        session_id = self._generate_session_id()
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=session_duration_hours)

        # Assign color to creator
        user_color = self._assign_user_color([])

        session_data = {
            "session_id": session_id,
            "widget_id": widget_id,
            "creator": creator,
            "created_at": now.isoformat() + 'Z',
            "expires_at": expires_at.isoformat() + 'Z',
            "status": "active",
            "participants": [
                {
                    "user_id": creator,
                    "socket_id": None,
                    "cursor_position": None,
                    "color": user_color,
                    "joined_at": now.isoformat() + 'Z',
                    "last_activity": now.isoformat() + 'Z'
                }
            ],
            "operation_log": [],
            "locks": {}
        }

        # Save session details
        session_file = self._get_session_file(session_id)
        self._atomic_write(session_file, session_data)

        # Add to active sessions
        active_sessions = self._load_active_sessions()
        active_sessions['sessions'].append({
            "session_id": session_id,
            "widget_id": widget_id,
            "creator": creator,
            "created_at": session_data['created_at'],
            "expires_at": session_data['expires_at'],
            "status": "active",
            "participant_count": 1
        })
        self._save_active_sessions(active_sessions)

        return session_data

    def join_session(self, session_id: str, user_id: str,
                    socket_id: str) -> Optional[dict]:
        """Join an existing collaboration session.

        Args:
            session_id: Session identifier
            user_id: Username joining
            socket_id: WebSocket connection ID

        Returns:
            Updated session data or None if not found/expired
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return None

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        # Check if expired
        expires_at = datetime.fromisoformat(session_data['expires_at'].replace('Z', ''))
        if datetime.utcnow() > expires_at:
            session_data['status'] = 'expired'
            self._atomic_write(session_file, session_data)
            return None

        # Check if already in session
        existing = next((p for p in session_data['participants']
                        if p['user_id'] == user_id), None)

        if existing:
            # Update socket_id and activity
            existing['socket_id'] = socket_id
            existing['last_activity'] = datetime.utcnow().isoformat() + 'Z'
        else:
            # Assign color
            used_colors = [p['color'] for p in session_data['participants']]
            user_color = self._assign_user_color(used_colors)

            # Add new participant
            session_data['participants'].append({
                "user_id": user_id,
                "socket_id": socket_id,
                "cursor_position": None,
                "color": user_color,
                "joined_at": datetime.utcnow().isoformat() + 'Z',
                "last_activity": datetime.utcnow().isoformat() + 'Z'
            })

        # Save
        self._atomic_write(session_file, session_data)

        # Update active sessions count
        active_sessions = self._load_active_sessions()
        for s in active_sessions['sessions']:
            if s['session_id'] == session_id:
                s['participant_count'] = len(session_data['participants'])
        self._save_active_sessions(active_sessions)

        return session_data

    def leave_session(self, session_id: str, user_id: str) -> bool:
        """Leave a collaboration session.

        Args:
            session_id: Session identifier
            user_id: Username leaving

        Returns:
            True if left successfully
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return False

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        # Remove participant
        session_data['participants'] = [
            p for p in session_data['participants']
            if p['user_id'] != user_id
        ]

        # If no participants left, mark as inactive
        if not session_data['participants']:
            session_data['status'] = 'inactive'

        # Save
        self._atomic_write(session_file, session_data)

        # Update active sessions
        active_sessions = self._load_active_sessions()
        if not session_data['participants']:
            # Remove from active sessions
            active_sessions['sessions'] = [
                s for s in active_sessions['sessions']
                if s['session_id'] != session_id
            ]
        else:
            # Update count
            for s in active_sessions['sessions']:
                if s['session_id'] == session_id:
                    s['participant_count'] = len(session_data['participants'])

        self._save_active_sessions(active_sessions)

        return True

    def update_cursor(self, session_id: str, user_id: str,
                     cursor_position: dict) -> bool:
        """Update user's cursor position in session.

        Args:
            session_id: Session identifier
            user_id: Username
            cursor_position: Cursor data (line, column, editor)

        Returns:
            True if updated successfully
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return False

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        # Find participant
        participant = next((p for p in session_data['participants']
                          if p['user_id'] == user_id), None)

        if not participant:
            return False

        # Update cursor and activity
        participant['cursor_position'] = cursor_position
        participant['last_activity'] = datetime.utcnow().isoformat() + 'Z'

        # Save
        self._atomic_write(session_file, session_data)

        return True

    def log_operation(self, session_id: str, user_id: str,
                     operation: dict) -> bool:
        """Log an edit operation in the session.

        Args:
            session_id: Session identifier
            user_id: Username performing operation
            operation: Operation details (type, content, position)

        Returns:
            True if logged successfully
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return False

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        # Create operation entry
        op_entry = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "user_id": user_id,
            "operation": operation
        }

        # Add to log (keep last 100 operations)
        session_data['operation_log'].append(op_entry)
        if len(session_data['operation_log']) > 100:
            session_data['operation_log'] = session_data['operation_log'][-100:]

        # Save
        self._atomic_write(session_file, session_data)

        return True

    def request_lock(self, session_id: str, user_id: str,
                    editor: str, line_range: tuple) -> dict:
        """Request a line lock to prevent conflicts.

        Args:
            session_id: Session identifier
            user_id: Username requesting lock
            editor: Editor type (html, css, javascript)
            line_range: (start_line, end_line)

        Returns:
            Lock result (granted, denied, conflict)
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return {"granted": False, "reason": "Session not found"}

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        lock_key = f"{editor}:{line_range[0]}-{line_range[1]}"

        # Check if locked by someone else
        if lock_key in session_data['locks']:
            existing_lock = session_data['locks'][lock_key]
            if existing_lock['user_id'] != user_id:
                return {
                    "granted": False,
                    "reason": "Line locked by another user",
                    "locked_by": existing_lock['user_id']
                }

        # Grant lock
        session_data['locks'][lock_key] = {
            "user_id": user_id,
            "granted_at": datetime.utcnow().isoformat() + 'Z',
            "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat() + 'Z'
        }

        # Save
        self._atomic_write(session_file, session_data)

        return {"granted": True, "lock_key": lock_key}

    def release_lock(self, session_id: str, user_id: str, lock_key: str) -> bool:
        """Release a line lock.

        Args:
            session_id: Session identifier
            user_id: Username releasing lock
            lock_key: Lock identifier

        Returns:
            True if released successfully
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return False

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        # Check if user owns the lock
        if lock_key in session_data['locks']:
            if session_data['locks'][lock_key]['user_id'] == user_id:
                del session_data['locks'][lock_key]
                self._atomic_write(session_file, session_data)
                return True

        return False

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session details.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return None

        with open(session_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_active_sessions(self, widget_id: Optional[str] = None) -> List[dict]:
        """Get list of active sessions.

        Args:
            widget_id: Filter by widget (optional)

        Returns:
            List of active sessions
        """
        active_sessions = self._load_active_sessions()
        sessions = active_sessions.get('sessions', [])

        if widget_id:
            sessions = [s for s in sessions if s['widget_id'] == widget_id]

        # Filter out expired
        now = datetime.utcnow()
        active = []
        for s in sessions:
            expires_at = datetime.fromisoformat(s['expires_at'].replace('Z', ''))
            if now < expires_at:
                active.append(s)

        return active

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        active_sessions = self._load_active_sessions()
        now = datetime.utcnow()
        cleaned = 0

        updated_sessions = []
        for s in active_sessions.get('sessions', []):
            expires_at = datetime.fromisoformat(s['expires_at'].replace('Z', ''))
            if now < expires_at:
                updated_sessions.append(s)
            else:
                # Mark session as expired
                session_file = self._get_session_file(s['session_id'])
                if session_file.exists():
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    session_data['status'] = 'expired'
                    self._atomic_write(session_file, session_data)
                cleaned += 1

        active_sessions['sessions'] = updated_sessions
        self._save_active_sessions(active_sessions)

        return cleaned

    def remove_inactive_users(self, timeout_seconds: int = 30) -> int:
        """Remove users who haven't been active recently.

        Args:
            timeout_seconds: Inactivity timeout in seconds

        Returns:
            Number of users removed
        """
        active_sessions = self._load_active_sessions()
        now = datetime.utcnow()
        removed = 0

        for s in active_sessions.get('sessions', []):
            session_file = self._get_session_file(s['session_id'])
            if not session_file.exists():
                continue

            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Check each participant
            active_participants = []
            for p in session_data['participants']:
                last_activity = datetime.fromisoformat(p['last_activity'].replace('Z', ''))
                if (now - last_activity).total_seconds() < timeout_seconds:
                    active_participants.append(p)
                else:
                    removed += 1

            # Update if changed
            if len(active_participants) != len(session_data['participants']):
                session_data['participants'] = active_participants

                # Mark as inactive if no participants
                if not active_participants:
                    session_data['status'] = 'inactive'

                self._atomic_write(session_file, session_data)

                # Update active sessions
                s['participant_count'] = len(active_participants)

        self._save_active_sessions(active_sessions)

        return removed
