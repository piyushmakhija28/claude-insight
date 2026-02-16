#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Notification Services

Tests notification services including:
- NotificationManager
- AlertSender
- AlertRoutingEngine
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestNotificationManager(unittest.TestCase):
    """Test suite for NotificationManager"""

    def setUp(self):
        """Set up test fixtures"""
        from services.notifications.notification_manager import NotificationManager
        self.manager = NotificationManager()

    def test_create_notification(self):
        """Test creating a notification"""
        notification = self.manager.create_notification(
            title='Test Alert',
            message='This is a test',
            level='info'
        )

        self.assertIsInstance(notification, dict)
        self.assertEqual(notification['title'], 'Test Alert')
        self.assertEqual(notification['level'], 'info')
        self.assertIn('id', notification)
        self.assertIn('timestamp', notification)

    def test_create_notification_different_levels(self):
        """Test creating notifications with different levels"""
        levels = ['info', 'warning', 'error', 'critical']

        for level in levels:
            notif = self.manager.create_notification(
                title=f'{level} test',
                message='Test',
                level=level
            )
            self.assertEqual(notif['level'], level)

    def test_get_notifications(self):
        """Test getting all notifications"""
        # Create some notifications
        self.manager.create_notification('Test 1', 'Message 1', 'info')
        self.manager.create_notification('Test 2', 'Message 2', 'warning')

        notifications = self.manager.get_notifications()

        self.assertIsInstance(notifications, list)
        self.assertGreaterEqual(len(notifications), 2)

    def test_get_unread_notifications(self):
        """Test getting unread notifications"""
        self.manager.create_notification('Unread', 'Message', 'info')

        unread = self.manager.get_unread_notifications()

        self.assertIsInstance(unread, list)
        self.assertGreater(len(unread), 0)

    def test_mark_as_read(self):
        """Test marking notification as read"""
        notif = self.manager.create_notification('Test', 'Message', 'info')
        notif_id = notif['id']

        result = self.manager.mark_as_read(notif_id)

        self.assertTrue(result)

    def test_clear_notifications(self):
        """Test clearing all notifications"""
        self.manager.create_notification('Test 1', 'Message 1', 'info')
        self.manager.create_notification('Test 2', 'Message 2', 'info')

        self.manager.clear_notifications()

        notifications = self.manager.get_notifications()
        self.assertEqual(len(notifications), 0)

    def test_filter_by_level(self):
        """Test filtering notifications by level"""
        self.manager.create_notification('Info', 'Message', 'info')
        self.manager.create_notification('Error', 'Message', 'error')
        self.manager.create_notification('Warning', 'Message', 'warning')

        errors = self.manager.filter_by_level('error')

        self.assertIsInstance(errors, list)
        for notif in errors:
            self.assertEqual(notif['level'], 'error')


class TestAlertSender(unittest.TestCase):
    """Test suite for AlertSender"""

    def setUp(self):
        """Set up test fixtures"""
        from services.notifications.alert_sender import AlertSender
        self.sender = AlertSender()

    @patch('requests.post')
    def test_send_slack_alert_success(self, mock_post):
        """Test successful Slack alert"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        alert = {
            'title': 'Test Alert',
            'message': 'Test message',
            'level': 'warning'
        }

        config = {
            'webhook_url': 'https://hooks.slack.com/test',
            'channel': '#alerts'
        }

        result = self.sender.send_slack_alert(alert, config)

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_slack_alert_failure(self, mock_post):
        """Test failed Slack alert"""
        mock_post.side_effect = Exception("Network error")

        alert = {'title': 'Test', 'message': 'Test', 'level': 'info'}
        config = {'webhook_url': 'https://hooks.slack.com/test'}

        result = self.sender.send_slack_alert(alert, config)

        self.assertFalse(result)

    @patch('requests.post')
    def test_send_discord_alert_success(self, mock_post):
        """Test successful Discord alert"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        alert = {
            'title': 'Test Alert',
            'message': 'Test message',
            'level': 'error'
        }

        config = {
            'webhook_url': 'https://discord.com/api/webhooks/test'
        }

        result = self.sender.send_discord_alert(alert, config)

        self.assertTrue(result)

    @patch('requests.post')
    def test_send_pagerduty_alert_success(self, mock_post):
        """Test successful PagerDuty alert"""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_post.return_value = mock_response

        alert = {
            'title': 'Critical Alert',
            'message': 'System down',
            'level': 'critical'
        }

        config = {
            'integration_key': 'test-key-123'
        }

        result = self.sender.send_pagerduty_alert(alert, config)

        self.assertTrue(result)

    @patch('smtplib.SMTP')
    def test_send_email_alert_success(self, mock_smtp):
        """Test successful email alert"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        alert = {
            'title': 'Email Test',
            'message': 'Test email alert',
            'level': 'info'
        }

        config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'from_email': 'alerts@example.com',
            'to_email': 'admin@example.com',
            'password': 'secret'
        }

        result = self.sender.send_email_alert(alert, config)

        self.assertTrue(result)
        mock_server.send_message.assert_called_once()

    def test_format_slack_message(self):
        """Test formatting Slack message"""
        alert = {
            'title': 'Test Alert',
            'message': 'Test message',
            'level': 'warning',
            'timestamp': '2026-02-16T10:00:00'
        }

        formatted = self.sender.format_slack_message(alert)

        self.assertIsInstance(formatted, dict)
        self.assertIn('text', formatted)
        self.assertIn('attachments', formatted)

    def test_format_discord_embed(self):
        """Test formatting Discord embed"""
        alert = {
            'title': 'Test Alert',
            'message': 'Test message',
            'level': 'error'
        }

        embed = self.sender.format_discord_embed(alert)

        self.assertIsInstance(embed, dict)
        self.assertIn('title', embed)
        self.assertIn('description', embed)
        self.assertIn('color', embed)


class TestAlertRoutingEngine(unittest.TestCase):
    """Test suite for AlertRoutingEngine"""

    def setUp(self):
        """Set up test fixtures"""
        from services.notifications.alert_routing import AlertRoutingEngine
        self.engine = AlertRoutingEngine()

    def test_add_routing_rule(self):
        """Test adding routing rule"""
        rule = {
            'condition': {'level': 'critical'},
            'channels': ['slack', 'pagerduty', 'email']
        }

        result = self.engine.add_routing_rule(rule)

        self.assertTrue(result)

    def test_remove_routing_rule(self):
        """Test removing routing rule"""
        rule = {
            'id': 'rule-123',
            'condition': {'level': 'info'},
            'channels': ['slack']
        }

        self.engine.add_routing_rule(rule)
        result = self.engine.remove_routing_rule('rule-123')

        self.assertTrue(result)

    def test_match_conditions(self):
        """Test matching alert to conditions"""
        alert = {
            'level': 'critical',
            'source': 'system_health'
        }

        conditions = {
            'level': 'critical',
            'source': 'system_health'
        }

        matches = self.engine.match_conditions(alert, conditions)

        self.assertTrue(matches)

    def test_match_conditions_no_match(self):
        """Test alert not matching conditions"""
        alert = {
            'level': 'info',
            'source': 'logs'
        }

        conditions = {
            'level': 'critical'
        }

        matches = self.engine.match_conditions(alert, conditions)

        self.assertFalse(matches)

    @patch('services.notifications.alert_sender.AlertSender.send_slack_alert')
    def test_route_alert(self, mock_send_slack):
        """Test routing alert to appropriate channels"""
        mock_send_slack.return_value = True

        # Add routing rule
        self.engine.add_routing_rule({
            'condition': {'level': 'error'},
            'channels': ['slack']
        })

        alert = {
            'title': 'Error Alert',
            'message': 'Something went wrong',
            'level': 'error'
        }

        configs = {
            'slack': {'webhook_url': 'https://hooks.slack.com/test'}
        }

        results = self.engine.route_alert(alert, configs)

        self.assertIsInstance(results, dict)

    def test_get_routing_rules(self):
        """Test getting all routing rules"""
        self.engine.add_routing_rule({
            'condition': {'level': 'critical'},
            'channels': ['pagerduty']
        })

        rules = self.engine.get_routing_rules()

        self.assertIsInstance(rules, list)

    def test_priority_routing(self):
        """Test priority-based routing"""
        # Critical alerts should go to all channels
        critical_alert = {
            'level': 'critical',
            'priority': 'high'
        }

        # Info alerts should go to fewer channels
        info_alert = {
            'level': 'info',
            'priority': 'low'
        }

        self.engine.add_routing_rule({
            'condition': {'level': 'critical'},
            'channels': ['slack', 'pagerduty', 'email']
        })

        self.engine.add_routing_rule({
            'condition': {'level': 'info'},
            'channels': ['slack']
        })

        critical_channels = self.engine.get_matching_channels(critical_alert)
        info_channels = self.engine.get_matching_channels(info_alert)

        # Critical should have more channels than info
        self.assertGreater(len(critical_channels), len(info_channels))


class TestNotificationIntegration(unittest.TestCase):
    """Integration tests for notification system"""

    def setUp(self):
        """Set up test fixtures"""
        from services.notifications.notification_manager import NotificationManager
        from services.notifications.alert_sender import AlertSender
        from services.notifications.alert_routing import AlertRoutingEngine

        self.manager = NotificationManager()
        self.sender = AlertSender()
        self.router = AlertRoutingEngine()

    @patch('requests.post')
    def test_full_notification_flow(self, mock_post):
        """Test complete notification flow"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 1. Create notification
        notif = self.manager.create_notification(
            title='System Alert',
            message='High CPU usage detected',
            level='warning'
        )

        self.assertIsInstance(notif, dict)

        # 2. Add routing rule
        self.router.add_routing_rule({
            'condition': {'level': 'warning'},
            'channels': ['slack']
        })

        # 3. Route and send
        configs = {
            'slack': {'webhook_url': 'https://hooks.slack.com/test'}
        }

        results = self.router.route_alert(notif, configs)

        # Should complete without errors
        self.assertIsInstance(results, dict)


if __name__ == '__main__':
    unittest.main()
