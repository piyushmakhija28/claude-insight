"""
Claude Monitoring System
A professional dashboard for monitoring Claude Memory System v2.0
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from functools import wraps
import os
import csv
import io
from datetime import datetime
from utils.metrics import MetricsCollector
from utils.log_parser import LogParser
from utils.policy_checker import PolicyChecker
from utils.session_tracker import SessionTracker
from utils.history_tracker import HistoryTracker

app = Flask(__name__)
app.secret_key = 'claude-monitoring-system-secret-key-2026'

# Initialize utilities
metrics = MetricsCollector()
log_parser = LogParser()
policy_checker = PolicyChecker()
session_tracker = SessionTracker()
history_tracker = HistoryTracker()

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
    # Get time range from query parameter (default: 7 days)
    days = request.args.get('days', 7, type=int)
    # Validate days parameter
    if days not in [7, 30, 60, 90]:
        days = 7

    # Get widget preferences from session (default: all enabled)
    widget_prefs = session.get('widget_preferences', {
        'system_health': True,
        'daemon_status': True,
        'policy_status': True,
        'recent_activity': True,
        'historical_charts': True,
        'recent_errors': True
    })

    # Get all metrics
    system_health = metrics.get_system_health()
    daemon_status = metrics.get_daemon_status()
    policy_status = policy_checker.get_all_policies_status()
    recent_activity = log_parser.get_recent_activity(limit=10)

    # Add daily metric snapshot
    try:
        # Get detailed policy status (returns dict)
        policy_status_dict = policy_checker.get_detailed_policy_status()

        current_metrics = {
            'health_score': system_health.get('health_score', 0),
            'errors_24h': log_parser.get_error_count(hours=24),
            'policy_hits': policy_status_dict.get('active_policies', 0),
            'context_usage': system_health.get('context_usage', 0),
            'tokens_used': 0,  # Would come from session tracker
            'daemons_running': len([d for d in daemon_status if d.get('status') == 'running']),
            'daemons_total': len(daemon_status)
        }
        history_tracker.add_daily_metric(current_metrics)
    except Exception as e:
        print(f"Error adding daily metric: {e}")
        import traceback
        traceback.print_exc()

    # Get historical data for selected time range
    chart_data = history_tracker.get_chart_data(days=days)
    summary_stats = history_tracker.get_summary_stats(days=days)

    return render_template('dashboard.html',
                         system_health=system_health,
                         daemon_status=daemon_status,
                         policy_status=policy_status,
                         recent_activity=recent_activity,
                         chart_data=chart_data,
                         summary_stats=summary_stats,
                         selected_days=days,
                         widget_preferences=widget_prefs)

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

@app.route('/api/metrics')
@login_required
def api_metrics():
    """API endpoint for dashboard metrics - REAL DATA from Claude Memory System"""
    try:
        system_health = metrics.get_system_health()
        daemon_status = metrics.get_daemon_status()
        # Use get_detailed_policy_status() which returns a dict
        policy_status = policy_checker.get_detailed_policy_status()

        # daemon_status is a list from get_daemon_status
        daemons_running = len([d for d in daemon_status if isinstance(d, dict) and d.get('status') == 'running'])
        daemons_total = len(daemon_status) if daemon_status else 8

        health_score = system_health.get('health_score', system_health.get('score', 0))

        return jsonify({
            'success': True,
            'health_score': health_score,
            'daemons_running': daemons_running,
            'daemons_total': daemons_total,
            'active_policies': policy_status.get('active_policies', 0),
            'policy_hits': 0,  # Will track from logs later
            'context_usage': system_health.get('context_usage', 0),
            'memory_usage': system_health.get('memory_usage', 0),
            'labels': ['Now'],
            'health_scores': [health_score],
            'policy_hits_data': [0]
        })
    except Exception as e:
        print(f"Error in api_metrics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/activity')
@login_required
def api_activity():
    """API endpoint for recent activity"""
    try:
        recent_activity = log_parser.get_recent_activity(limit=10)
        return jsonify({
            'success': True,
            'activities': recent_activity
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/policies')
@login_required
def api_policies():
    """API endpoint for policy status - REAL DATA"""
    try:
        policies_data = policy_checker.get_detailed_policy_status()

        # Ensure policies is an array for dashboard
        if isinstance(policies_data, dict):
            # Convert dict to array of policy objects
            policies_array = []
            for key, value in policies_data.items():
                if isinstance(value, dict):
                    policies_array.append({
                        'name': key.replace('_', ' ').title(),
                        **value
                    })
                else:
                    # Simple key-value pair
                    policies_array.append({
                        'name': key.replace('_', ' ').title(),
                        'status': 'active',
                        'value': value
                    })
            policies_data = policies_array

        return jsonify({
            'success': True,
            'policies': policies_data
        })
    except Exception as e:
        print(f"Error in api_policies: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system-info')
@login_required
def api_system_info():
    """API endpoint for system information - REAL DATA"""
    try:
        system_health = metrics.get_system_health()
        daemon_status = metrics.get_daemon_status()

        daemons_running = len([d for d in daemon_status if d.get('status') == 'running'])
        daemons_total = len(daemon_status)
        health_score = system_health.get('health_score', system_health.get('score', 0))

        return jsonify({
            'success': True,
            'system_info': {
                'status': 'Operational' if health_score >= 90 else ('Healthy' if health_score >= 70 else 'Degraded'),
                'health_score': health_score,
                'memory_usage': system_health.get('memory_usage', 0),
                'context_usage': system_health.get('context_usage', 0),
                'daemons_running': daemons_running,
                'daemons_total': daemons_total,
                'uptime': system_health.get('uptime', 'Active'),
                'last_check': datetime.now().isoformat()
            }
        })
    except Exception as e:
        print(f"Error in api_system_info: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recent-errors')
@login_required
def api_recent_errors():
    """API endpoint for recent errors"""
    try:
        errors = log_parser.get_recent_errors(limit=5)
        return jsonify({
            'success': True,
            'errors': errors
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/comparison')
@login_required
def api_comparison():
    """API endpoint for comparison data"""
    try:
        comparison_data = metrics.get_cost_comparison()
        optimization_impact = metrics.get_optimization_impact()

        return jsonify({
            'success': True,
            'comparison': comparison_data,
            'impact': optimization_impact
        })
    except Exception as e:
        print(f"Error in api_comparison: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/api/export/sessions')
@login_required
def export_sessions():
    """Export session history to CSV"""
    try:
        sessions_history = session_tracker.get_sessions_history()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['Session ID', 'Start Time', 'End Time', 'Duration (min)', 'Commands', 'Tokens Used', 'Cost ($)', 'Status'])

        # Write data
        for sess in sessions_history:
            writer.writerow([
                sess.get('session_id', 'N/A'),
                sess.get('start_time', 'N/A'),
                sess.get('end_time', 'N/A'),
                sess.get('duration_minutes', 0),
                sess.get('commands_executed', 0),
                sess.get('tokens_used', 0),
                sess.get('estimated_cost', 0),
                sess.get('status', 'N/A')
            ])

        # Create response
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=claude_sessions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return response
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/export/metrics')
@login_required
def export_metrics():
    """Export current metrics to CSV"""
    try:
        system_health = metrics.get_system_health()
        daemon_status = metrics.get_daemon_status()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['Metric', 'Value', 'Status', 'Timestamp'])

        # Write system health data
        writer.writerow(['Health Score', system_health.get('health_score', 0), 'N/A', datetime.now().isoformat()])
        writer.writerow(['Memory Usage', system_health.get('memory_usage', 0), 'N/A', datetime.now().isoformat()])
        writer.writerow(['Active Daemons', len([d for d in daemon_status if d.get('status') == 'running']), 'N/A', datetime.now().isoformat()])
        writer.writerow(['Total Daemons', len(daemon_status), 'N/A', datetime.now().isoformat()])

        # Write daemon status
        writer.writerow([])
        writer.writerow(['Daemon Name', 'Status', 'PID', 'Uptime'])
        for daemon in daemon_status:
            writer.writerow([
                daemon.get('name', 'N/A'),
                daemon.get('status', 'N/A'),
                daemon.get('pid', 'N/A'),
                daemon.get('uptime', 'N/A')
            ])

        # Create response
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=claude_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return response
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/export/logs')
@login_required
def export_logs():
    """Export logs to CSV"""
    try:
        recent_activity = log_parser.get_recent_activity(limit=1000)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['Timestamp', 'Level', 'Policy', 'Action', 'Message'])

        # Write log data
        for activity in recent_activity:
            writer.writerow([
                activity.get('timestamp', 'N/A'),
                activity.get('level', 'N/A'),
                activity.get('policy', 'N/A'),
                activity.get('action', 'N/A'),
                activity.get('message', 'N/A')
            ])

        # Create response
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=claude_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return response
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/widget-preferences', methods=['GET', 'POST'])
@login_required
def widget_preferences():
    """Get or update widget preferences"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            session['widget_preferences'] = data.get('preferences', {})
            return jsonify({'success': True, 'message': 'Preferences saved'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        # GET request - return current preferences
        prefs = session.get('widget_preferences', {
            'system_health': True,
            'daemon_status': True,
            'policy_status': True,
            'recent_activity': True,
            'historical_charts': True,
            'recent_errors': True
        })
        return jsonify({'success': True, 'preferences': prefs})

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

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
