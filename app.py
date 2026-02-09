"""
Claude Monitoring System
A professional dashboard for monitoring Claude Memory System v2.0
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os
from datetime import datetime
from utils.metrics import MetricsCollector
from utils.log_parser import LogParser
from utils.policy_checker import PolicyChecker
from utils.session_tracker import SessionTracker

app = Flask(__name__)
app.secret_key = 'claude-monitoring-system-secret-key-2026'

# Initialize utilities
metrics = MetricsCollector()
log_parser = LogParser()
policy_checker = PolicyChecker()
session_tracker = SessionTracker()

# Login credentials
USERNAME = 'admin'
PASSWORD = 'admin'

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Redirect to dashboard or login"""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Get all metrics
    system_health = metrics.get_system_health()
    daemon_status = metrics.get_daemon_status()
    policy_status = policy_checker.get_all_policies_status()
    recent_activity = log_parser.get_recent_activity(limit=10)

    return render_template('dashboard.html',
                         system_health=system_health,
                         daemon_status=daemon_status,
                         policy_status=policy_status,
                         recent_activity=recent_activity)

@app.route('/comparison')
@login_required
def comparison():
    """Before/After comparison page"""
    comparison_data = metrics.get_cost_comparison()
    optimization_impact = metrics.get_optimization_impact()

    return render_template('comparison.html',
                         comparison=comparison_data,
                         impact=optimization_impact)

@app.route('/policies')
@login_required
def policies():
    """Policies status page"""
    policies_data = policy_checker.get_detailed_policy_status()
    policy_history = log_parser.get_policy_history()

    return render_template('policies.html',
                         policies=policies_data,
                         history=policy_history)

@app.route('/logs')
@login_required
def logs():
    """Log analyzer page"""
    log_files = log_parser.get_available_logs()

    return render_template('logs.html',
                         log_files=log_files)

@app.route('/api/logs/analyze', methods=['POST'])
@login_required
def analyze_logs():
    """API endpoint to analyze logs"""
    data = request.get_json()
    log_file = data.get('log_file')
    search_term = data.get('search_term', '')
    log_level = data.get('log_level', 'all')

    results = log_parser.analyze_log_file(log_file, search_term, log_level)

    return jsonify(results)

@app.route('/api/metrics/live')
@login_required
def live_metrics():
    """API endpoint for live metrics"""
    live_data = {
        'health_score': metrics.get_health_score(),
        'daemon_count': metrics.get_running_daemon_count(),
        'context_usage': metrics.get_context_usage(),
        'recent_errors': log_parser.get_error_count(hours=1),
        'timestamp': datetime.now().isoformat()
    }

    return jsonify(live_data)

@app.route('/api/daemon/restart/<daemon_name>', methods=['POST'])
@login_required
def restart_daemon(daemon_name):
    """API endpoint to restart daemon"""
    try:
        result = metrics.restart_daemon(daemon_name)
        return jsonify({'success': True, 'message': f'Daemon {daemon_name} restarted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/sessions')
@login_required
def sessions():
    """Sessions tracking page"""
    current_session = session_tracker.update_session_metrics()
    sessions_history = session_tracker.get_sessions_history()
    last_session = session_tracker.get_last_session()

    # Compare current with last
    comparison = None
    if last_session:
        comparison = session_tracker.compare_sessions(last_session, current_session)

    summary = session_tracker.get_all_sessions_summary()

    return render_template('sessions.html',
                         current_session=current_session,
                         last_session=last_session,
                         sessions_history=sessions_history[-10:],  # Last 10 sessions
                         comparison=comparison,
                         summary=summary)

@app.route('/api/session/end', methods=['POST'])
@login_required
def end_session():
    """API endpoint to end current session"""
    try:
        ended_session = session_tracker.end_current_session()
        return jsonify({'success': True, 'session': ended_session})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.template_filter('format_datetime')
def format_datetime(value):
    """Format datetime for display"""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value

    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value

@app.template_filter('format_number')
def format_number(value):
    """Format numbers with commas"""
    try:
        return '{:,}'.format(int(value))
    except:
        return value

if __name__ == '__main__':
    print("""
    ============================================================
    Claude Monitoring System v2.0
    ============================================================

    Dashboard URL: http://localhost:5000
    Username: admin
    Password: admin

    Starting server...
    ============================================================
    """)

    app.run(debug=True, host='0.0.0.0', port=5000)
