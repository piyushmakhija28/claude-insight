"""
Notification Manager
Handles browser push notifications and notification history
"""
import json
from datetime import datetime
from pathlib import Path


class NotificationManager:
    """Manage browser notifications and history"""

    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.notifications_file = self.memory_dir / 'notifications_history.json'
        self.ensure_notifications_file()

    def ensure_notifications_file(self):
        """Ensure notifications history file exists"""
        if not self.notifications_file.exists():
            self.notifications_file.parent.mkdir(parents=True, exist_ok=True)
            self.notifications_file.write_text(json.dumps({
                'notifications': [],
                'last_updated': datetime.now().isoformat()
            }))

    def load_notifications(self):
        """Load notification history"""
        try:
            if self.notifications_file.exists():
                return json.loads(self.notifications_file.read_text())
            return {'notifications': [], 'last_updated': None}
        except Exception as e:
            print(f"Error loading notifications: {e}")
            return {'notifications': [], 'last_updated': None}

    def save_notifications(self, data):
        """Save notification history"""
        try:
            self.notifications_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving notifications: {e}")

    def add_notification(self, notification_type, title, message, severity='info', data=None):
        """Add a notification to history"""
        history = self.load_notifications()

        notification = {
            'id': f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'type': notification_type,
            'title': title,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'data': data or {}
        }

        history['notifications'].insert(0, notification)

        # Keep only last 500 notifications
        history['notifications'] = history['notifications'][:500]
        history['last_updated'] = datetime.now().isoformat()

        self.save_notifications(history)
        return notification

    def mark_as_read(self, notification_id):
        """Mark notification as read"""
        history = self.load_notifications()

        for notif in history['notifications']:
            if notif.get('id') == notification_id:
                notif['read'] = True
                break

        self.save_notifications(history)

    def mark_all_as_read(self):
        """Mark all notifications as read"""
        history = self.load_notifications()

        for notif in history['notifications']:
            notif['read'] = True

        self.save_notifications(history)

    def get_unread_count(self):
        """Get count of unread notifications"""
        history = self.load_notifications()
        return len([n for n in history['notifications'] if not n.get('read', False)])

    def get_recent_notifications(self, limit=50):
        """Get recent notifications"""
        history = self.load_notifications()
        return history['notifications'][:limit]

    def get_notification_trends(self, days=30):
        """Get notification trends for the last N days"""
        history = self.load_notifications()
        notifications = history['notifications']

        # Filter by date range
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        filtered = [n for n in notifications if datetime.fromisoformat(n['timestamp']) > cutoff_date]

        # Count by type
        type_counts = {}
        severity_counts = {}
        daily_counts = {}

        for notif in filtered:
            # Count by type
            notif_type = notif.get('type', 'unknown')
            type_counts[notif_type] = type_counts.get(notif_type, 0) + 1

            # Count by severity
            severity = notif.get('severity', 'info')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Count by day
            date = notif['timestamp'][:10]
            daily_counts[date] = daily_counts.get(date, 0) + 1

        return {
            'total_count': len(filtered),
            'by_type': type_counts,
            'by_severity': severity_counts,
            'by_day': daily_counts,
            'most_frequent_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        }

    def delete_old_notifications(self, days=90):
        """Delete notifications older than N days"""
        history = self.load_notifications()

        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        filtered = [n for n in history['notifications']
                    if datetime.fromisoformat(n['timestamp']) > cutoff_date]

        history['notifications'] = filtered
        self.save_notifications(history)

        return len(history['notifications']) - len(filtered)  # Number deleted
