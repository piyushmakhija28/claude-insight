"""
SECURE VERSION OF app.py - FIXES ALL CRITICAL SECURITY ISSUES

This file demonstrates the security fixes needed for app.py.
Once tested, merge these changes into app.py.

CRITICAL FIXES IMPLEMENTED:
1. ✅ Removed hardcoded secret key
2. ✅ Removed hardcoded admin password
3. ✅ Added CSRF protection
4. ✅ Added rate limiting
5. ✅ Added path traversal validation
6. ✅ Added command injection prevention
7. ✅ Added security headers
8. ✅ Session regeneration on login
9. ✅ Password strength validation
10. ✅ Account lockout after failed attempts
"""

# Fix module imports - add src directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, send_file
from flask_socketio import SocketIO, emit
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from functools import wraps
import os
import csv
import io
import threading
import time
from datetime import datetime
import pyotp
import qrcode
import base64
import secrets
import json
import logging

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import security configuration
from config.security import security_config, PathValidator, FilenameValidator, CommandValidator, SecurityError
from auth.user_manager import UserManager

# Import monitoring services
from services.monitoring.metrics_collector import MetricsCollector
from services.monitoring.log_parser import LogParser
from services.monitoring.policy_checker import PolicyChecker
from services.monitoring.session_tracker import SessionTracker
from services.monitoring.memory_system_monitor import MemorySystemMonitor
from services.monitoring.performance_profiler import PerformanceProfiler
from services.monitoring.automation_tracker import AutomationTracker
from services.monitoring.skill_agent_tracker import SkillAgentTracker
from services.monitoring.optimization_tracker import OptimizationTracker
from services.monitoring.policy_execution_tracker import PolicyExecutionTracker

# Import AI services
from services.ai.anomaly_detector import AnomalyDetector
from services.ai.predictive_analytics import PredictiveAnalytics
from services.ai.bottleneck_analyzer import BottleneckAnalyzer

# Import widget services
from services.widgets.community_manager import CommunityWidgetsManager
from services.widgets.version_manager import WidgetVersionManager
from services.widgets.comments_manager import WidgetCommentsManager
from services.widgets.collaboration_manager import CollaborationSessionManager
from services.widgets.trending_calculator import TrendingCalculator

# Import notification services
from services.notifications.notification_manager import NotificationManager
from services.notifications.alert_sender import AlertSender
from services.notifications.alert_routing import AlertRoutingEngine

# Import utilities
from utils.history_tracker import HistoryTracker
from flasgger import Swagger, swag_from

# Import session search routes
from routes.session_search import session_search_bp
from routes.claude_credentials import claude_creds_bp
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Read application version
def get_version():
    """Read version from VERSION file"""
    try:
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "2.5.0"
    except:
        return "2.5.0"

APP_VERSION = get_version()

# Get project root (parent of src directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Initialize Flask with correct paths
app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / 'templates'),
    static_folder=str(PROJECT_ROOT / 'static')
)

# ============================================================
# SECURITY CONFIGURATION - CRITICAL FIXES
# ============================================================

# Apply security configuration (includes SECRET_KEY)
security_config.apply_to_flask_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[os.environ.get('RATELIMIT_DEFAULT', '200 per day;50 per hour')],
    storage_uri=os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
)

# Initialize security headers (Talisman)
# Disable in development if needed
if not security_config.development_mode and security_config.force_https:
    Talisman(
        app,
        force_https=True,
        strict_transport_security=True,
        session_cookie_secure=True,
        content_security_policy=security_config.csp_config,
        content_security_policy_nonce_in=['script-src']
    )

# Initialize User Manager (replaces hardcoded USERS dict)
user_manager = UserManager()

# Make version available to all templates
@app.context_processor
def inject_version():
    return dict(app_version=APP_VERSION)

# Register blueprints
app.register_blueprint(session_search_bp)
app.register_blueprint(claude_creds_bp)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize Swagger for API documentation
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/api/docs/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}
swagger = Swagger(app, config=swagger_config)

# Initialize utilities
metrics = MetricsCollector()
log_parser = LogParser()
policy_checker = PolicyChecker()
session_tracker = SessionTracker()
history_tracker = HistoryTracker()
notification_manager = NotificationManager()
alert_sender = AlertSender()
community_widgets_manager = CommunityWidgetsManager()
anomaly_detector = AnomalyDetector()
predictive_analytics = PredictiveAnalytics()
alert_routing = AlertRoutingEngine()
memory_system_monitor = MemorySystemMonitor()
widget_version_manager = WidgetVersionManager()
widget_comments_manager = WidgetCommentsManager()
collaboration_manager = CollaborationSessionManager()
trending_calculator = TrendingCalculator()
performance_profiler = PerformanceProfiler()
bottleneck_analyzer = BottleneckAnalyzer()
automation_tracker = AutomationTracker()
skill_agent_tracker = SkillAgentTracker()
optimization_tracker = OptimizationTracker()
policy_execution_tracker = PolicyExecutionTracker()

# ============================================================
# AUTHENTICATION - SECURE VERSION
# ============================================================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            return redirect(url_for('login'))

        username = session.get('username')
        role = user_manager.get_user_role(username)
        if role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit(os.environ.get('RATELIMIT_LOGIN', '5 per minute'))
def login():
    """
    Secure login endpoint

    SECURITY FIXES:
    - Rate limiting to prevent brute force
    - Session regeneration to prevent fixation
    - Account lockout after failed attempts
    - Secure password validation
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Verify credentials
        is_valid, error_message = user_manager.verify_password(username, password)

        if is_valid:
            # SECURITY FIX: Regenerate session to prevent fixation
            session.clear()
            session['logged_in'] = True
            session['username'] = username
            session.permanent = False  # Session expires on browser close

            logger.info(f"Successful login: {username}")

            # Check if password must be changed
            if user_manager.must_change_password(username):
                return redirect(url_for('change_password_required'))

            return redirect(url_for('dashboard'))
        else:
            logger.warning(f"Failed login attempt for: {username}")
            return render_template('login.html', error=error_message or 'Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Secure logout"""
    username = session.get('username', 'unknown')
    session.clear()
    logger.info(f"User logged out: {username}")
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password_required():
    """Force password change for new users or compromised accounts"""
    username = session.get('username')

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate passwords match
        if new_password != confirm_password:
            return render_template('change_password.html',
                                 error='New passwords do not match',
                                 required=True)

        # Update password
        success, message = user_manager.update_password(username, new_password, current_password)

        if success:
            logger.info(f"Password changed for user: {username}")
            return redirect(url_for('dashboard'))
        else:
            return render_template('change_password.html',
                                 error=message,
                                 required=True)

    return render_template('change_password.html', required=True)

# ============================================================
# EXAMPLE: SECURE FILE DOWNLOAD WITH PATH VALIDATION
# ============================================================

@app.route('/api/logs/<log_name>/download')
@login_required
def download_log_secure(log_name):
    """
    Secure log file download

    SECURITY FIXES:
    - Filename sanitization
    - Path traversal prevention
    - Path validation
    """
    try:
        # Get logs directory
        logs_dir = PROJECT_ROOT / 'logs'

        # SECURITY FIX: Sanitize filename
        safe_filename = FilenameValidator.sanitize(log_name)

        # SECURITY FIX: Validate path is within logs directory
        path_validator = PathValidator(logs_dir)
        log_path = path_validator.validate(logs_dir / safe_filename)

        # Check file exists
        if not log_path.exists():
            return jsonify({'error': 'Log file not found'}), 404

        return send_file(log_path, as_attachment=True, download_name=safe_filename)

    except SecurityError as e:
        logger.error(f"Security error in log download: {e}")
        return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        logger.error(f"Error downloading log: {e}")
        return jsonify({'error': 'Internal error'}), 500

# ============================================================
# EXAMPLE: SECURE SUBPROCESS EXECUTION
# ============================================================

def run_script_secure(script_name: str, args: list = None):
    """
    Securely execute allowed scripts

    SECURITY FIXES:
    - Script whitelist validation
    - Path validation
    - Argument sanitization
    - Timeout enforcement
    """
    try:
        import subprocess

        # Get memory scripts directory
        memory_dir = Path.home() / '.claude' / 'memory'

        # SECURITY FIX: Validate script is allowed
        script_path = CommandValidator.validate_script_path(
            memory_dir / script_name,
            memory_dir
        )

        # Build command
        cmd = ['python', str(script_path)]
        if args:
            # Validate arguments (whitelist approach)
            allowed_args = ['--health', '--status', '--check']
            for arg in args:
                if arg not in allowed_args:
                    raise SecurityError(f"Argument not allowed: {arg}")
            cmd.extend(args)

        # Execute with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,  # Don't raise on non-zero exit
            cwd=str(memory_dir)
        )

        return result

    except SecurityError as e:
        logger.error(f"Security error executing script: {e}")
        raise
    except subprocess.TimeoutExpired:
        logger.error(f"Script timeout: {script_name}")
        raise
    except Exception as e:
        logger.error(f"Error executing script: {e}")
        raise

# ============================================================
# SECURITY HEADERS (Additional middleware)
# ============================================================

@app.after_request
def security_headers(response):
    """Add additional security headers"""

    # HTTP Caching
    if request.path.startswith('/static/'):
        # Cache static files for 1 year
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
    elif request.path.startswith('/api/'):
        # Don't cache API responses
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True

    # Additional security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    return response

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    logger.warning(f"Rate limit exceeded: {request.remote_addr}")
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@app.errorhandler(403)
def forbidden_handler(e):
    """Handle forbidden access"""
    return jsonify({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource.'
    }), 403

@app.errorhandler(404)
def not_found_handler(e):
    """Handle not found"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found.'
    }), 404

@app.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server error"""
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred.'
    }), 500

# ============================================================
# NOTE: Add remaining routes from original app.py here
# Copy all routes but apply security fixes as needed
# ============================================================

if __name__ == '__main__':
    # Log startup information
    logger.info("=" * 80)
    logger.info(f"Claude Insight v{APP_VERSION} - SECURE VERSION")
    logger.info(f"Development Mode: {security_config.development_mode}")
    logger.info(f"CSRF Protection: {security_config.csrf_enabled}")
    logger.info(f"Force HTTPS: {security_config.force_https}")
    logger.info("=" * 80)

    # Run server
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False') == 'True'

    socketio.run(app, debug=debug, host='0.0.0.0', port=port)
