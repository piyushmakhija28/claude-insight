"""
Session ID Search Routes
Search and view sessions by ID with complete details
"""

from flask import Blueprint, request, jsonify, render_template
from pathlib import Path
import json
from datetime import datetime
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.path_resolver import get_sessions_dir, get_logs_dir

session_search_bp = Blueprint('session_search', __name__)

class SessionSearchService:
    """Service for searching and retrieving session data"""

    def __init__(self):
        self.sessions_dir = get_sessions_dir()
        self.sessions_log = get_logs_dir() / 'sessions.log'

    def search_session(self, session_id):
        """Search for a session by ID"""
        session_file = self.sessions_dir / f'{session_id}.json'

        if not session_file.exists():
            return None

        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Get session events from log
            events = self._get_session_events(session_id)

            # Calculate statistics
            stats = self._calculate_stats(session_data)

            return {
                'session_data': session_data,
                'events': events,
                'stats': stats,
                'found': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'found': False
            }

    def list_recent_sessions(self, limit=50):
        """List recent sessions"""
        if not self.sessions_dir.exists():
            return []

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
                    sessions.append({
                        'session_id': data['session_id'],
                        'start_time': data['start_time'],
                        'status': data['status'],
                        'description': data.get('description', ''),
                        'work_items_count': len(data.get('work_items', []))
                    })
            except:
                continue

        return sessions

    def search_by_date(self, date_str):
        """Search sessions by date (YYYYMMDD)"""
        if not self.sessions_dir.exists():
            return []

        pattern = f'SESSION-{date_str}-*.json'
        session_files = sorted(
            self.sessions_dir.glob(pattern),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        sessions = []
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    sessions.append(data)
            except:
                continue

        return sessions

    def _get_session_events(self, session_id):
        """Get all events for a session from log"""
        if not self.sessions_log.exists():
            return []

        events = []
        try:
            with open(self.sessions_log, 'r') as f:
                for line in f:
                    if session_id in line:
                        parts = line.strip().split(' | ')
                        if len(parts) >= 4:
                            events.append({
                                'timestamp': parts[0],
                                'session_id': parts[1],
                                'event_type': parts[2],
                                'details': parts[3] if len(parts) > 3 else ''
                            })
        except:
            pass

        return events

    def _calculate_stats(self, session_data):
        """Calculate session statistics"""
        start_time = datetime.fromisoformat(session_data['start_time'])
        end_time = datetime.fromisoformat(session_data['end_time']) if session_data.get('end_time') else datetime.now()

        duration = end_time - start_time

        work_items = session_data.get('work_items', [])
        completed = [w for w in work_items if w.get('status') == 'COMPLETED']
        in_progress = [w for w in work_items if w.get('status') == 'IN_PROGRESS']

        return {
            'duration_seconds': duration.total_seconds(),
            'duration_formatted': str(duration).split('.')[0],
            'total_work_items': len(work_items),
            'completed_work_items': len(completed),
            'in_progress_work_items': len(in_progress),
            'completion_rate': (len(completed) / len(work_items) * 100) if work_items else 0
        }

# Initialize service
session_search_service = SessionSearchService()

# Routes
@session_search_bp.route('/session-search')
def session_search_page():
    """Session search page"""
    return render_template('session_search.html')

@session_search_bp.route('/api/session/search', methods=['GET'])
def search_session():
    """
    Search for a session by ID
    ---
    parameters:
      - name: session_id
        in: query
        type: string
        required: true
        description: Session ID to search for
    responses:
      200:
        description: Session found
      404:
        description: Session not found
    """
    session_id = request.args.get('session_id', '').strip()

    if not session_id:
        return jsonify({'error': 'Session ID required'}), 400

    result = session_search_service.search_session(session_id)

    if not result or not result.get('found'):
        return jsonify({
            'found': False,
            'error': result.get('error', 'Session not found')
        }), 404

    return jsonify(result), 200

@session_search_bp.route('/api/session/list', methods=['GET'])
def list_sessions():
    """
    List recent sessions
    ---
    parameters:
      - name: limit
        in: query
        type: integer
        default: 50
        description: Number of sessions to return
    responses:
      200:
        description: List of sessions
    """
    limit = int(request.args.get('limit', 50))
    sessions = session_search_service.list_recent_sessions(limit)

    return jsonify({
        'sessions': sessions,
        'count': len(sessions)
    }), 200

@session_search_bp.route('/api/session/search-by-date', methods=['GET'])
def search_by_date():
    """
    Search sessions by date
    ---
    parameters:
      - name: date
        in: query
        type: string
        required: true
        description: Date in YYYYMMDD format
    responses:
      200:
        description: Sessions found for date
    """
    date_str = request.args.get('date', '').strip()

    if not date_str or len(date_str) != 8:
        return jsonify({'error': 'Date must be in YYYYMMDD format'}), 400

    sessions = session_search_service.search_by_date(date_str)

    return jsonify({
        'sessions': sessions,
        'count': len(sessions),
        'date': date_str
    }), 200
