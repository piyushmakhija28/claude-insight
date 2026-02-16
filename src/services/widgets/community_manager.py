"""
Community Widgets Manager
Handles widget sharing, ratings, and community marketplace
"""
import json
from datetime import datetime
from pathlib import Path
import sys

# Add path resolver for portable paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.path_resolver import get_data_dir, get_logs_dir


class CommunityWidgetsManager:
    """Manage community widget marketplace"""

    def __init__(self):
        self.data_dir = get_data_dir() / 'community'
        self.widgets_file = self.data_dir / 'widgets.json'
        self.ensure_data_files()

    def ensure_data_files(self):
        """Ensure community data files exist"""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.widgets_file.exists():
            self.widgets_file.write_text(json.dumps({
                'widgets': [],
                'last_updated': datetime.now().isoformat()
            }))

    def load_widgets(self):
        """Load all community widgets"""
        try:
            if self.widgets_file.exists():
                return json.loads(self.widgets_file.read_text())
            return {'widgets': [], 'last_updated': None}
        except Exception as e:
            print(f"Error loading community widgets: {e}")
            return {'widgets': [], 'last_updated': None}

    def save_widgets(self, data):
        """Save community widgets"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            self.widgets_file.write_text(json.dumps(data, indent=2))
            return True
        except Exception as e:
            print(f"Error saving community widgets: {e}")
            return False

    def publish_widget(self, widget_data):
        """Publish a new widget to community"""
        data = self.load_widgets()

        widget_id = f"widget_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        widget = {
            'id': widget_id,
            'name': widget_data.get('name', 'Untitled Widget'),
            'description': widget_data.get('description', ''),
            'category': widget_data.get('category', 'dashboard'),
            'version': widget_data.get('version', '1.0.0'),
            'tags': widget_data.get('tags', []),
            'author': widget_data.get('author', 'Anonymous'),
            'author_email': widget_data.get('author_email', ''),
            'widget_data': widget_data.get('widget_data', {}),
            'published_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'downloads': 0,
            'rating': 0.0,
            'reviews': 0,
            'ratings': []  # List of individual ratings
        }

        data['widgets'].append(widget)
        self.save_widgets(data)

        return widget

    def get_all_widgets(self):
        """Get all published widgets"""
        data = self.load_widgets()
        return data.get('widgets', [])

    def get_widget_by_id(self, widget_id):
        """Get a specific widget by ID"""
        data = self.load_widgets()
        widgets = data.get('widgets', [])

        for widget in widgets:
            if widget.get('id') == widget_id:
                return widget

        return None

    def increment_downloads(self, widget_id):
        """Increment download count for a widget"""
        data = self.load_widgets()
        widgets = data.get('widgets', [])

        for widget in widgets:
            if widget.get('id') == widget_id:
                widget['downloads'] = widget.get('downloads', 0) + 1
                self.save_widgets(data)
                return True

        return False

    def add_rating(self, widget_id, rating_value):
        """Add a rating to a widget"""
        if not 1 <= rating_value <= 5:
            return False

        data = self.load_widgets()
        widgets = data.get('widgets', [])

        for widget in widgets:
            if widget.get('id') == widget_id:
                ratings = widget.get('ratings', [])
                ratings.append({
                    'value': rating_value,
                    'timestamp': datetime.now().isoformat()
                })
                widget['ratings'] = ratings

                # Recalculate average rating
                avg_rating = sum(r['value'] for r in ratings) / len(ratings)
                widget['rating'] = round(avg_rating, 1)
                widget['reviews'] = len(ratings)

                self.save_widgets(data)
                return True

        return False

    def search_widgets(self, query, category=None, min_rating=0):
        """Search widgets by query, category, and rating"""
        widgets = self.get_all_widgets()
        results = []

        query_lower = query.lower() if query else ''

        for widget in widgets:
            # Filter by category
            if category and widget.get('category') != category:
                continue

            # Filter by rating
            if widget.get('rating', 0) < min_rating:
                continue

            # Filter by search query
            if query:
                matches = (
                    query_lower in widget.get('name', '').lower() or
                    query_lower in widget.get('description', '').lower() or
                    any(query_lower in tag.lower() for tag in widget.get('tags', []))
                )
                if not matches:
                    continue

            results.append(widget)

        return results

    def get_stats(self):
        """Get community marketplace statistics"""
        widgets = self.get_all_widgets()

        if not widgets:
            return {
                'total_widgets': 0,
                'total_downloads': 0,
                'total_creators': 0,
                'avg_rating': 0.0,
                'categories': {}
            }

        total_downloads = sum(w.get('downloads', 0) for w in widgets)
        ratings = [w.get('rating', 0) for w in widgets if w.get('rating', 0) > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

        authors = set(w.get('author', 'Anonymous') for w in widgets)

        categories = {}
        for widget in widgets:
            cat = widget.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total_widgets': len(widgets),
            'total_downloads': total_downloads,
            'total_creators': len(authors),
            'avg_rating': round(avg_rating, 1),
            'categories': categories
        }

    def get_popular_widgets(self, limit=10):
        """Get most popular widgets by downloads"""
        widgets = self.get_all_widgets()
        sorted_widgets = sorted(widgets, key=lambda w: w.get('downloads', 0), reverse=True)
        return sorted_widgets[:limit]

    def get_top_rated_widgets(self, limit=10):
        """Get top rated widgets"""
        widgets = self.get_all_widgets()
        # Filter widgets with at least 3 ratings
        rated_widgets = [w for w in widgets if w.get('reviews', 0) >= 3]
        sorted_widgets = sorted(rated_widgets, key=lambda w: w.get('rating', 0), reverse=True)
        return sorted_widgets[:limit]

    def get_recent_widgets(self, limit=10):
        """Get most recently published widgets"""
        widgets = self.get_all_widgets()
        sorted_widgets = sorted(widgets, key=lambda w: w.get('published_at', ''), reverse=True)
        return sorted_widgets[:limit]

    def get_widgets_by_author(self, author):
        """Get all widgets by a specific author"""
        widgets = self.get_all_widgets()
        return [w for w in widgets if w.get('author') == author]

    def delete_widget(self, widget_id):
        """Delete a widget from community (admin only)"""
        data = self.load_widgets()
        widgets = data.get('widgets', [])

        data['widgets'] = [w for w in widgets if w.get('id') != widget_id]
        return self.save_widgets(data)

    def update_widget(self, widget_id, updates):
        """Update widget information"""
        data = self.load_widgets()
        widgets = data.get('widgets', [])

        for widget in widgets:
            if widget.get('id') == widget_id:
                widget.update(updates)
                widget['updated_at'] = datetime.now().isoformat()
                self.save_widgets(data)
                return widget

        return None
