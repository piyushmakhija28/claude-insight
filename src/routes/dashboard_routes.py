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
    return render_template('dashboard.html')


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
