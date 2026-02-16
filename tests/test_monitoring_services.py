#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Monitoring Services

Tests all monitoring services including:
- MetricsCollector
- LogParser
- PolicyChecker
- SessionTracker
- MemorySystemMonitor
- PerformanceProfiler
- AutomationTracker
- SkillAgentTracker
- OptimizationTracker
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestMetricsCollector(unittest.TestCase):
    """Test suite for MetricsCollector"""

    def setUp(self):
        """Set up test fixtures"""
        from services.monitoring.metrics_collector import MetricsCollector
        self.collector = MetricsCollector()

    @patch('subprocess.run')
    def test_get_system_health_success(self, mock_run):
        """Test successful system health retrieval"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'health_score': 95,
            'running': 8,
            'total_daemons': 8
        })
        mock_run.return_value = mock_result

        health = self.collector.get_system_health()

        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['health_score'], 95)
        self.assertEqual(health['running_daemons'], 8)

    @patch('subprocess.run')
    def test_get_system_health_degraded(self, mock_run):
        """Test degraded system health"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'health_score': 50,
            'running': 4,
            'total_daemons': 8
        })
        mock_run.return_value = mock_result

        health = self.collector.get_system_health()

        self.assertEqual(health['status'], 'degraded')
        self.assertLess(health['health_score'], 90)

    @patch('subprocess.run')
    def test_get_system_health_failure(self, mock_run):
        """Test system health on failure"""
        mock_run.side_effect = Exception("Command failed")

        health = self.collector.get_system_health()

        self.assertEqual(health['status'], 'unknown')
        self.assertEqual(health['health_score'], 0)

    @patch('subprocess.run')
    def test_get_daemon_status(self, mock_run):
        """Test daemon status retrieval"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'daemons': {
                'context-daemon': {'is_running': True, 'pid': 1234},
                'session-daemon': {'is_running': False, 'pid': None}
            }
        })
        mock_run.return_value = mock_result

        daemons = self.collector.get_daemon_status()

        self.assertIsInstance(daemons, list)
        self.assertGreater(len(daemons), 0)


class TestLogParser(unittest.TestCase):
    """Test suite for LogParser"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / 'test.log'

        # Create sample log file
        with open(self.log_file, 'w') as f:
            f.write('[2026-02-16 10:00:00] INFO: Test message 1\n')
            f.write('[2026-02-16 10:01:00] ERROR: Test error\n')
            f.write('[2026-02-16 10:02:00] WARNING: Test warning\n')

        with patch('utils.path_resolver.get_logs_dir', return_value=Path(self.temp_dir)):
            from services.monitoring.log_parser import LogParser
            self.parser = LogParser()

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_parse_log_line(self):
        """Test parsing single log line"""
        line = '[2026-02-16 10:00:00] INFO: Test message'
        parsed = self.parser.parse_log_line(line)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['level'], 'INFO')
        self.assertEqual(parsed['message'], 'Test message')

    def test_parse_log_line_invalid(self):
        """Test parsing invalid log line"""
        line = 'Invalid log format'
        parsed = self.parser.parse_log_line(line)

        self.assertIsNone(parsed)

    @patch('builtins.open', create=True)
    def test_get_recent_logs(self, mock_file_open):
        """Test getting recent logs"""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = [
            '[2026-02-16 10:00:00] INFO: Test 1\n',
            '[2026-02-16 10:01:00] ERROR: Test 2\n'
        ]
        mock_file_open.return_value = mock_file

        logs = self.parser.get_recent_logs(limit=10)

        self.assertIsInstance(logs, list)

    def test_filter_by_level(self):
        """Test filtering logs by level"""
        logs = [
            {'level': 'INFO', 'message': 'Test 1'},
            {'level': 'ERROR', 'message': 'Test 2'},
            {'level': 'INFO', 'message': 'Test 3'}
        ]

        filtered = self.parser.filter_by_level(logs, 'ERROR')

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['level'], 'ERROR')


class TestPolicyChecker(unittest.TestCase):
    """Test suite for PolicyChecker"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        with patch('utils.path_resolver.get_data_dir', return_value=Path(self.temp_dir)):
            from services.monitoring.policy_checker import PolicyChecker
            self.checker = PolicyChecker()

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('os.listdir')
    def test_get_all_policies(self, mock_listdir):
        """Test getting all policies"""
        mock_listdir.return_value = [
            'policy-1.md',
            'policy-2.md',
            'not-a-policy.txt'
        ]

        with patch('builtins.open', create=True):
            policies = self.checker.get_all_policies()

        self.assertIsInstance(policies, list)

    def test_check_policy_status(self):
        """Test checking policy status"""
        policy_name = 'test-policy'

        with patch('os.path.exists', return_value=True):
            status = self.checker.check_policy_status(policy_name)

        self.assertIsInstance(status, dict)
        self.assertIn('exists', status)


class TestSessionTracker(unittest.TestCase):
    """Test suite for SessionTracker"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.sessions_dir = Path(self.temp_dir) / 'sessions'
        self.sessions_dir.mkdir(exist_ok=True)

        # Create sample session file
        session_file = self.sessions_dir / 'session-001.json'
        with open(session_file, 'w') as f:
            json.dump({
                'session_id': '001',
                'timestamp': '2026-02-16T10:00:00',
                'duration': 3600,
                'activities': [
                    {'type': 'read', 'timestamp': '2026-02-16T10:00:00'},
                    {'type': 'write', 'timestamp': '2026-02-16T10:05:00'}
                ]
            }, f)

        with patch('utils.path_resolver.get_data_dir', return_value=Path(self.temp_dir)):
            from services.monitoring.session_tracker import SessionTracker
            self.tracker = SessionTracker()

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_recent_sessions(self):
        """Test getting recent sessions"""
        sessions = self.tracker.get_recent_sessions(limit=10)

        self.assertIsInstance(sessions, list)

    def test_get_activity_data(self):
        """Test getting activity data"""
        activity = self.tracker.get_activity_data()

        self.assertIsInstance(activity, dict)
        self.assertIn('recent_activity', activity)

    def test_get_session_stats(self):
        """Test getting session statistics"""
        stats = self.tracker.get_session_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn('total_sessions', stats)


class TestMemorySystemMonitor(unittest.TestCase):
    """Test suite for MemorySystemMonitor"""

    def setUp(self):
        """Set up test fixtures"""
        from services.monitoring.memory_system_monitor import MemorySystemMonitor
        self.monitor = MemorySystemMonitor()

    @patch('subprocess.run')
    def test_get_system_info(self, mock_run):
        """Test getting system information"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Version: 2.5.0\nUptime: 5 days"
        mock_run.return_value = mock_result

        info = self.monitor.get_system_info()

        self.assertIsInstance(info, dict)

    def test_get_context_usage(self):
        """Test getting context usage"""
        usage = self.monitor.get_context_usage()

        self.assertIsInstance(usage, dict)
        self.assertIn('current', usage)
        self.assertIn('max', usage)

    def test_get_memory_usage(self):
        """Test getting memory usage"""
        usage = self.monitor.get_memory_usage()

        self.assertIsInstance(usage, dict)


class TestPerformanceProfiler(unittest.TestCase):
    """Test suite for PerformanceProfiler"""

    def setUp(self):
        """Set up test fixtures"""
        from services.monitoring.performance_profiler import PerformanceProfiler
        self.profiler = PerformanceProfiler()

    def test_record_metric(self):
        """Test recording a performance metric"""
        self.profiler.record_metric('test_operation', 123.45)

        # Should not raise exception
        self.assertTrue(True)

    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        self.profiler.record_metric('op1', 100)
        self.profiler.record_metric('op1', 200)
        self.profiler.record_metric('op2', 50)

        summary = self.profiler.get_metrics_summary()

        self.assertIsInstance(summary, dict)

    def test_get_slowest_operations(self):
        """Test getting slowest operations"""
        self.profiler.record_metric('fast', 10)
        self.profiler.record_metric('slow', 1000)
        self.profiler.record_metric('medium', 100)

        slowest = self.profiler.get_slowest_operations(limit=2)

        self.assertIsInstance(slowest, list)
        self.assertLessEqual(len(slowest), 2)


class TestAutomationTracker(unittest.TestCase):
    """Test suite for AutomationTracker"""

    def setUp(self):
        """Set up test fixtures"""
        from services.monitoring.automation_tracker import AutomationTracker
        self.tracker = AutomationTracker()

    def test_track_automation(self):
        """Test tracking automation event"""
        self.tracker.track_automation(
            automation_type='auto_commit',
            status='success',
            details={'files': 5}
        )

        # Should not raise exception
        self.assertTrue(True)

    def test_get_automation_stats(self):
        """Test getting automation statistics"""
        self.tracker.track_automation('auto_commit', 'success', {})
        self.tracker.track_automation('auto_save', 'success', {})

        stats = self.tracker.get_automation_stats()

        self.assertIsInstance(stats, dict)

    def test_get_recent_automations(self):
        """Test getting recent automations"""
        self.tracker.track_automation('test', 'success', {})

        recent = self.tracker.get_recent_automations(limit=10)

        self.assertIsInstance(recent, list)


class TestSkillAgentTracker(unittest.TestCase):
    """Test suite for SkillAgentTracker"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        with patch('utils.path_resolver.get_data_dir', return_value=Path(self.temp_dir)):
            from services.monitoring.skill_agent_tracker import SkillAgentTracker
            self.tracker = SkillAgentTracker()

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('os.path.exists', return_value=True)
    @patch('os.listdir')
    def test_get_installed_skills(self, mock_listdir, mock_exists):
        """Test getting installed skills"""
        mock_listdir.return_value = ['skill1', 'skill2']

        skills = self.tracker.get_installed_skills()

        self.assertIsInstance(skills, list)

    @patch('os.path.exists', return_value=True)
    @patch('os.listdir')
    def test_get_installed_agents(self, mock_listdir, mock_exists):
        """Test getting installed agents"""
        mock_listdir.return_value = ['agent1', 'agent2']

        agents = self.tracker.get_installed_agents()

        self.assertIsInstance(agents, list)

    def test_get_skill_usage_stats(self):
        """Test getting skill usage statistics"""
        stats = self.tracker.get_skill_usage_stats()

        self.assertIsInstance(stats, dict)


class TestOptimizationTracker(unittest.TestCase):
    """Test suite for OptimizationTracker"""

    def setUp(self):
        """Set up test fixtures"""
        from services.monitoring.optimization_tracker import OptimizationTracker
        self.tracker = OptimizationTracker()

    def test_track_optimization(self):
        """Test tracking optimization"""
        self.tracker.track_optimization(
            optimization_type='cache_hit',
            tokens_saved=500,
            details={'strategy': 'file_cache'}
        )

        # Should not raise exception
        self.assertTrue(True)

    def test_get_optimization_stats(self):
        """Test getting optimization statistics"""
        self.tracker.track_optimization('cache_hit', 100, {})
        self.tracker.track_optimization('cache_hit', 200, {})

        stats = self.tracker.get_optimization_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn('total_tokens_saved', stats)

    def test_get_optimization_breakdown(self):
        """Test getting optimization breakdown by type"""
        self.tracker.track_optimization('cache_hit', 100, {})
        self.tracker.track_optimization('offset_limit', 50, {})

        breakdown = self.tracker.get_optimization_breakdown()

        self.assertIsInstance(breakdown, dict)


if __name__ == '__main__':
    unittest.main()
