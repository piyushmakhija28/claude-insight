"""
Dashboard Routes Blueprint for Claude Insight

Provides routes for:
- /dashboard - Main dashboard page
- /analytics - Analytics dashboard
- /comparison - Cost comparison
- /sessions - Session tracking
- /logs - Log viewer
"""

from flask import Blueprint, render_template, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import json
from pathlib import Path

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')


def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Import here to avoid circular imports
        from flask import session, redirect, url_for
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page with real-time metrics."""
    # Widget preferences (all widgets enabled by default)
    widget_preferences = {
        'system_health': True,
        'recent_activity': True,
        'historical_charts': True,
        'context_usage': True,
        'performance_metrics': True,
    }

    # Summary statistics
    summary_stats = {
        'avg_health_score': 92,
        'trend': 'up',
        'total_errors': 0,
        'total_policy_hits': 0,
        'avg_context_usage': 42,
    }

    # Latest flow data (3-level execution status)
    flow_latest = {
        'session_id': 'SESSION-CURRENT',
        'overall_status': 'OK',
        'level_minus_1': {'status': 'PASS'},
        'level_1': {'context_pct': 42, 'status': 'OK'},
        'level_2': {'standards': 12, 'rules': 65, 'status': 'OK'},
        'level_3': {
            'status': 'OK',
            'model': 'claude-sonnet',
            'skill_agent': 'python-backend-engineer',
            'task_type': 'General',
            'tasks': 0,
            'complexity': 5,
            'execution_mode': 'sequential',
        },
    }

    # Time series data for charts
    selected_days = 7
    chart_data = []

    return render_template(
        'dashboard.html',
        widget_preferences=widget_preferences,
        summary_stats=summary_stats,
        flow_latest=flow_latest,
        selected_days=selected_days,
        chart_data=chart_data,
    )


@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Advanced analytics dashboard."""
    return render_template('analytics.html')


@dashboard_bp.route('/comparison')
@login_required
def comparison():
    """Cost comparison analysis."""
    return render_template('comparison.html')


@dashboard_bp.route('/sessions')
@login_required
def sessions():
    """Session tracking and history."""
    return render_template('sessions.html')


@dashboard_bp.route('/logs')
@login_required
def logs():
    """Real-time log viewer."""
    return render_template('logs.html')
