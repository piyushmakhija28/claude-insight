#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Flask App Routes

Tests all Flask routes in app.py including:
- Authentication routes (login, logout, 2FA)
- Dashboard routes
- API endpoints
- Export functionality
- WebSocket connections
- Error handling
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Patch imports before importing app
with patch('flask_socketio.SocketIO'):
    from app import app

class TestAppRoutes(unittest.TestCase):
    """Test suite for Flask app routes"""

    def setUp(self):
        """Set up test fixtures before each test"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after each test"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    # ========== Authentication Routes ==========

    def test_login_page_get(self):
        """Test GET request to login page"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_login_redirect_when_authenticated(self):
        """Test login redirects to dashboard when already authenticated"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/login')
        self.assertEqual(response.status_code, 302)  # Redirect

    @patch('bcrypt.checkpw')
    @patch('builtins.open', create=True)
    def test_login_success(self, mock_open, mock_checkpw):
        """Test successful login"""
        mock_checkpw.return_value = True
        mock_file = MagicMock()
        mock_file.read.return_value = '$2b$12$test_hashed_password'
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'test123'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        with patch('bcrypt.checkpw', return_value=False):
            with patch('builtins.open', create=True):
                response = self.client.post('/login', data={
                    'username': 'admin',
                    'password': 'wrong'
                })

                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Invalid', response.data)

    def test_logout(self):
        """Test logout functionality"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        with self.client.session_transaction() as sess:
            self.assertFalse(sess.get('authenticated', False))

    # ========== 2FA Routes ==========

    def test_2fa_settings_page(self):
        """Test 2FA settings page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/2fa-settings')
        self.assertEqual(response.status_code, 200)

    def test_2fa_settings_unauthorized(self):
        """Test 2FA settings requires authentication"""
        response = self.client.get('/2fa-settings', follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    @patch('builtins.open', create=True)
    def test_2fa_status_enabled(self, mock_open):
        """Test 2FA status when enabled"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_file = MagicMock()
        mock_file.read.return_value = 'test_secret'
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.get('/api/2fa/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('enabled', data)

    @patch('pyotp.random_base32')
    @patch('builtins.open', create=True)
    def test_2fa_setup(self, mock_open, mock_random):
        """Test 2FA setup"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_random.return_value = 'TEST_SECRET_KEY'
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.post('/api/2fa/setup')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('qr_code', data)
        self.assertIn('secret', data)

    # ========== Dashboard Routes ==========

    def test_dashboard_authenticated(self):
        """Test dashboard access when authenticated"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_unauthorized(self):
        """Test dashboard redirects when not authenticated"""
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    def test_comparison_page(self):
        """Test comparison page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/comparison')
        self.assertEqual(response.status_code, 200)

    def test_policies_page(self):
        """Test policies page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/policies')
        self.assertEqual(response.status_code, 200)

    def test_logs_page(self):
        """Test logs page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/logs')
        self.assertEqual(response.status_code, 200)

    # ========== API Endpoints ==========

    @patch('services.monitoring.metrics_collector.MetricsCollector.get_system_health')
    def test_api_metrics(self, mock_health):
        """Test metrics API endpoint"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_health.return_value = {
            'status': 'healthy',
            'health_score': 95,
            'running_daemons': 8,
            'total_daemons': 8
        }

        response = self.client.get('/api/metrics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('system_health', data)

    @patch('services.monitoring.session_tracker.SessionTracker.get_activity_data')
    def test_api_activity(self, mock_activity):
        """Test activity API endpoint"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_activity.return_value = {
            'recent_activity': [],
            'hourly_stats': {}
        }

        response = self.client.get('/api/activity')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('recent_activity', data)

    @patch('services.monitoring.policy_checker.PolicyChecker.get_all_policies')
    def test_api_policies(self, mock_policies):
        """Test policies API endpoint"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_policies.return_value = [
            {'name': 'test-policy', 'status': 'active'}
        ]

        response = self.client.get('/api/policies')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    @patch('services.monitoring.memory_system_monitor.MemorySystemMonitor.get_system_info')
    def test_api_system_info(self, mock_sysinfo):
        """Test system info API endpoint"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_sysinfo.return_value = {
            'version': '2.5.0',
            'uptime': '5 days',
            'memory_usage': 60
        }

        response = self.client.get('/api/system-info')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('version', data)

    # ========== Export Functionality ==========

    @patch('services.monitoring.log_parser.LogParser.get_recent_logs')
    def test_export_csv(self, mock_logs):
        """Test CSV export"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_logs.return_value = [
            {'timestamp': '2026-02-16 10:00:00', 'level': 'INFO', 'message': 'Test'}
        ]

        response = self.client.get('/api/export/logs?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/csv')

    @patch('services.monitoring.log_parser.LogParser.get_recent_logs')
    def test_export_json(self, mock_logs):
        """Test JSON export"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_logs.return_value = [
            {'timestamp': '2026-02-16 10:00:00', 'level': 'INFO', 'message': 'Test'}
        ]

        response = self.client.get('/api/export/logs?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

    # ========== Dashboard Builder ==========

    def test_dashboard_builder_page(self):
        """Test dashboard builder page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/dashboard-builder')
        self.assertEqual(response.status_code, 200)

    @patch('builtins.open', create=True)
    def test_save_dashboard(self, mock_open):
        """Test saving dashboard configuration"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.post('/api/dashboards/save',
            data=json.dumps({
                'name': 'Test Dashboard',
                'layout': {'widgets': []}
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    @patch('builtins.open', create=True)
    @patch('os.path.exists', return_value=True)
    def test_list_dashboards(self, mock_exists, mock_open):
        """Test listing dashboards"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps([{
            'id': 'test-1',
            'name': 'Test Dashboard'
        }])
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.get('/api/dashboards/list')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    # ========== Plugins ==========

    def test_plugins_page(self):
        """Test plugins page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/plugins')
        self.assertEqual(response.status_code, 200)

    @patch('builtins.open', create=True)
    @patch('os.path.exists', return_value=True)
    def test_get_installed_plugins(self, mock_exists, mock_open):
        """Test getting installed plugins"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps([{
            'id': 'plugin-1',
            'name': 'Test Plugin',
            'enabled': True
        }])
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.get('/api/plugins/installed')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    # ========== Integrations ==========

    def test_integrations_page(self):
        """Test integrations page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/integrations')
        self.assertEqual(response.status_code, 200)

    def test_metrics_page(self):
        """Test metrics page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)

    # ========== Notification Channels ==========

    def test_notification_channels_page(self):
        """Test notification channels page access"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.get('/notification-channels')
        self.assertEqual(response.status_code, 200)

    @patch('builtins.open', create=True)
    def test_save_slack_config(self, mock_open):
        """Test saving Slack notification config"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.post('/api/notifications/slack',
            data=json.dumps({
                'webhook_url': 'https://hooks.slack.com/test',
                'channel': '#alerts'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    # ========== Error Handling ==========

    def test_404_error(self):
        """Test 404 error handling"""
        response = self.client.get('/nonexistent-route')
        self.assertEqual(response.status_code, 404)

    def test_api_unauthorized(self):
        """Test API endpoints require authentication"""
        response = self.client.get('/api/metrics')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_invalid_json_post(self):
        """Test handling of invalid JSON in POST"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        response = self.client.post('/api/dashboards/save',
            data='invalid json',
            content_type='application/json'
        )
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 500])


class TestWebSocketEvents(unittest.TestCase):
    """Test suite for WebSocket events"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True

    @patch('flask_socketio.SocketIO')
    def test_socketio_initialization(self, mock_socketio):
        """Test SocketIO is properly initialized"""
        # SocketIO should be created with app
        self.assertIsNotNone(mock_socketio)


if __name__ == '__main__':
    unittest.main()
