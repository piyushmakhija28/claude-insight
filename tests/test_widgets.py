#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Widget Services

Tests all widget-related services including:
- CommunityWidgetsManager
- WidgetVersionManager
- WidgetCommentsManager
- CollaborationSessionManager
- TrendingCalculator
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


class TestCommunityWidgetsManager(unittest.TestCase):
    """Test suite for CommunityWidgetsManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            from services.widgets.community_manager import CommunityWidgetsManager
            self.manager = CommunityWidgetsManager()

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_list_community_widgets_empty(self):
        """Test listing community widgets when none exist"""
        widgets = self.manager.list_community_widgets()

        self.assertIsInstance(widgets, list)

    @patch('builtins.open', create=True)
    @patch('os.listdir')
    @patch('os.path.exists', return_value=True)
    def test_list_community_widgets(self, mock_exists, mock_listdir, mock_file_open):
        """Test listing community widgets"""
        mock_listdir.return_value = ['widget1.json', 'widget2.json']

        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps({
            'id': 'widget1',
            'name': 'Test Widget',
            'author': 'test_user',
            'downloads': 100
        })
        mock_file_open.return_value.__enter__.return_value = mock_file

        widgets = self.manager.list_community_widgets()

        self.assertIsInstance(widgets, list)

    def test_install_widget_success(self):
        """Test successful widget installation"""
        widget_data = {
            'id': 'test-widget',
            'name': 'Test Widget',
            'code': 'console.log("test");'
        }

        with patch('builtins.open', create=True):
            with patch('os.makedirs'):
                result = self.manager.install_widget(widget_data)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('success', False))

    def test_uninstall_widget(self):
        """Test widget uninstallation"""
        widget_id = 'test-widget'

        with patch('os.path.exists', return_value=True):
            with patch('os.remove'):
                result = self.manager.uninstall_widget(widget_id)

        self.assertIsInstance(result, dict)

    def test_get_widget_details(self):
        """Test getting widget details"""
        widget_id = 'test-widget'

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_file_open:
                mock_file = MagicMock()
                mock_file.read.return_value = json.dumps({
                    'id': widget_id,
                    'name': 'Test Widget',
                    'version': '1.0.0'
                })
                mock_file_open.return_value.__enter__.return_value = mock_file

                details = self.manager.get_widget_details(widget_id)

        self.assertIsInstance(details, dict)
        self.assertEqual(details.get('id'), widget_id)

    def test_search_widgets(self):
        """Test searching widgets"""
        query = 'analytics'

        widgets = [
            {'name': 'Analytics Dashboard', 'tags': ['analytics']},
            {'name': 'Simple Counter', 'tags': ['simple']},
            {'name': 'Advanced Analytics', 'tags': ['analytics', 'advanced']}
        ]

        with patch.object(self.manager, 'list_community_widgets', return_value=widgets):
            results = self.manager.search_widgets(query)

        self.assertIsInstance(results, list)
        # Should find widgets matching 'analytics'
        for result in results:
            self.assertTrue(
                query.lower() in result.get('name', '').lower() or
                query.lower() in str(result.get('tags', [])).lower()
            )


class TestWidgetVersionManager(unittest.TestCase):
    """Test suite for WidgetVersionManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            from services.widgets.version_manager import WidgetVersionManager
            self.manager = WidgetVersionManager()

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_version(self):
        """Test creating a new widget version"""
        widget_id = 'test-widget'
        version_data = {
            'version': '1.0.1',
            'changes': 'Bug fixes',
            'code': 'console.log("v1.0.1");'
        }

        with patch('builtins.open', create=True):
            with patch('os.makedirs'):
                result = self.manager.create_version(widget_id, version_data)

        self.assertIsInstance(result, dict)

    def test_get_version_history(self):
        """Test getting version history"""
        widget_id = 'test-widget'

        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['1.0.0.json', '1.0.1.json']):
                with patch('builtins.open', create=True) as mock_file_open:
                    mock_file = MagicMock()
                    mock_file.read.return_value = json.dumps({
                        'version': '1.0.0',
                        'created_at': '2026-02-16T10:00:00'
                    })
                    mock_file_open.return_value.__enter__.return_value = mock_file

                    history = self.manager.get_version_history(widget_id)

        self.assertIsInstance(history, list)

    def test_rollback_version(self):
        """Test rolling back to previous version"""
        widget_id = 'test-widget'
        target_version = '1.0.0'

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True):
                with patch('shutil.copy'):
                    result = self.manager.rollback_version(widget_id, target_version)

        self.assertIsInstance(result, dict)

    def test_compare_versions(self):
        """Test comparing two versions"""
        version1 = '1.0.0'
        version2 = '1.0.1'

        comparison = self.manager.compare_versions(version1, version2)

        self.assertIsInstance(comparison, int)


class TestWidgetCommentsManager(unittest.TestCase):
    """Test suite for WidgetCommentsManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            from services.widgets.comments_manager import WidgetCommentsManager
            self.manager = WidgetCommentsManager()

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_add_comment(self):
        """Test adding a comment"""
        widget_id = 'test-widget'
        comment_data = {
            'user': 'test_user',
            'text': 'Great widget!',
            'rating': 5
        }

        with patch('builtins.open', create=True):
            with patch('os.makedirs'):
                result = self.manager.add_comment(widget_id, comment_data)

        self.assertIsInstance(result, dict)

    def test_get_comments(self):
        """Test getting comments for widget"""
        widget_id = 'test-widget'

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_file_open:
                mock_file = MagicMock()
                mock_file.read.return_value = json.dumps([
                    {'id': '1', 'text': 'Comment 1'},
                    {'id': '2', 'text': 'Comment 2'}
                ])
                mock_file_open.return_value.__enter__.return_value = mock_file

                comments = self.manager.get_comments(widget_id)

        self.assertIsInstance(comments, list)

    def test_delete_comment(self):
        """Test deleting a comment"""
        widget_id = 'test-widget'
        comment_id = 'comment-123'

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True):
                result = self.manager.delete_comment(widget_id, comment_id)

        self.assertIsInstance(result, dict)

    def test_get_average_rating(self):
        """Test calculating average rating"""
        widget_id = 'test-widget'

        comments = [
            {'rating': 5},
            {'rating': 4},
            {'rating': 5}
        ]

        with patch.object(self.manager, 'get_comments', return_value=comments):
            avg = self.manager.get_average_rating(widget_id)

        self.assertIsInstance(avg, float)
        self.assertAlmostEqual(avg, 4.666, places=2)


class TestCollaborationSessionManager(unittest.TestCase):
    """Test suite for CollaborationSessionManager"""

    def setUp(self):
        """Set up test fixtures"""
        from services.widgets.collaboration_manager import CollaborationSessionManager
        self.manager = CollaborationSessionManager()

    def test_create_session(self):
        """Test creating collaboration session"""
        widget_id = 'test-widget'
        user_id = 'user-123'

        session = self.manager.create_session(widget_id, user_id)

        self.assertIsInstance(session, dict)
        self.assertIn('session_id', session)
        self.assertEqual(session['widget_id'], widget_id)

    def test_join_session(self):
        """Test joining collaboration session"""
        widget_id = 'test-widget'
        creator = 'user-123'
        joiner = 'user-456'

        # Create session
        session = self.manager.create_session(widget_id, creator)
        session_id = session['session_id']

        # Join session
        result = self.manager.join_session(session_id, joiner)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('success', False))

    def test_leave_session(self):
        """Test leaving collaboration session"""
        widget_id = 'test-widget'
        user_id = 'user-123'

        session = self.manager.create_session(widget_id, user_id)
        session_id = session['session_id']

        result = self.manager.leave_session(session_id, user_id)

        self.assertIsInstance(result, dict)

    def test_get_active_sessions(self):
        """Test getting active sessions"""
        sessions = self.manager.get_active_sessions()

        self.assertIsInstance(sessions, list)

    def test_end_session(self):
        """Test ending collaboration session"""
        widget_id = 'test-widget'
        user_id = 'user-123'

        session = self.manager.create_session(widget_id, user_id)
        session_id = session['session_id']

        result = self.manager.end_session(session_id)

        self.assertIsInstance(result, dict)


class TestTrendingCalculator(unittest.TestCase):
    """Test suite for TrendingCalculator"""

    def setUp(self):
        """Set up test fixtures"""
        from services.widgets.trending_calculator import TrendingCalculator
        self.calculator = TrendingCalculator()

    def test_calculate_trending_score(self):
        """Test calculating trending score"""
        widget_data = {
            'downloads': 100,
            'views': 500,
            'likes': 50,
            'created_at': (datetime.now() - timedelta(days=7)).isoformat()
        }

        score = self.calculator.calculate_trending_score(widget_data)

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)

    def test_get_trending_widgets(self):
        """Test getting trending widgets"""
        widgets = [
            {
                'id': 'widget1',
                'downloads': 200,
                'views': 1000,
                'likes': 100,
                'created_at': (datetime.now() - timedelta(days=3)).isoformat()
            },
            {
                'id': 'widget2',
                'downloads': 50,
                'views': 200,
                'likes': 10,
                'created_at': (datetime.now() - timedelta(days=30)).isoformat()
            }
        ]

        trending = self.calculator.get_trending_widgets(widgets, limit=5)

        self.assertIsInstance(trending, list)
        self.assertLessEqual(len(trending), 5)

    def test_calculate_velocity(self):
        """Test calculating growth velocity"""
        data_points = [
            {'timestamp': '2026-02-10T10:00:00', 'value': 100},
            {'timestamp': '2026-02-15T10:00:00', 'value': 150},
            {'timestamp': '2026-02-16T10:00:00', 'value': 200}
        ]

        velocity = self.calculator.calculate_velocity(data_points)

        self.assertIsInstance(velocity, float)

    def test_decay_factor(self):
        """Test time decay factor calculation"""
        recent_date = datetime.now() - timedelta(days=1)
        old_date = datetime.now() - timedelta(days=30)

        recent_decay = self.calculator.calculate_decay_factor(recent_date.isoformat())
        old_decay = self.calculator.calculate_decay_factor(old_date.isoformat())

        self.assertGreater(recent_decay, old_decay)


if __name__ == '__main__':
    unittest.main()
