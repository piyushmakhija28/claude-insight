"""
Trending Calculator
Calculates trending and featured widgets based on activity and ratings.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import math


class TrendingCalculator:
    """Calculates trending scores and manages featured widgets."""

    def __init__(self, base_dir: str = None, widgets_file: str = None):
        """Initialize the trending calculator.

        Args:
            base_dir: Base directory for storage. Defaults to ~/.claude/memory/community
            widgets_file: Path to widgets.json file
        """
        if base_dir is None:
            base_dir = os.path.expanduser("~/.claude/memory/community")

        self.base_dir = Path(base_dir)
        self.featured_dir = self.base_dir / "featured"
        self.featured_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.featured_dir / "trending_cache.json"

        if widgets_file is None:
            self.widgets_file = self.base_dir / "widgets.json"
        else:
            self.widgets_file = Path(widgets_file)

        # Scoring weights
        self.weights = {
            "downloads": 0.40,
            "rating": 0.30,
            "comments": 0.20,
            "recency": 0.10
        }

        # Cache duration
        self.cache_duration_minutes = 60

    def _atomic_write(self, filepath: Path, data: dict):
        """Atomically write JSON data to file."""
        temp_file = filepath.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(filepath)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e

    def _load_widgets(self) -> List[dict]:
        """Load all widgets."""
        if not self.widgets_file.exists():
            return []

        with open(self.widgets_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get('widgets', [])

    def _calculate_recency_score(self, created_at: str) -> float:
        """Calculate recency score (0-1) based on widget age.

        Args:
            created_at: ISO timestamp of creation

        Returns:
            Score between 0 and 1 (1 = very recent, 0 = very old)
        """
        created = datetime.fromisoformat(created_at.replace('Z', ''))
        now = datetime.utcnow()
        age_days = (now - created).total_seconds() / 86400

        # Exponential decay: score = e^(-age/30)
        # After 30 days, score is ~0.37
        # After 90 days, score is ~0.05
        return math.exp(-age_days / 30)

    def _calculate_download_score(self, downloads: int) -> float:
        """Calculate normalized download score (0-1).

        Args:
            downloads: Number of downloads

        Returns:
            Score between 0 and 1
        """
        # Logarithmic scaling: log(downloads + 1) / log(1001)
        # 0 downloads = 0
        # 100 downloads = 0.67
        # 1000 downloads = 1.0
        if downloads <= 0:
            return 0.0

        return min(1.0, math.log(downloads + 1) / math.log(1001))

    def _calculate_rating_score(self, rating: float, rating_count: int) -> float:
        """Calculate weighted rating score (0-1).

        Args:
            rating: Average rating (1-5)
            rating_count: Number of ratings

        Returns:
            Score between 0 and 1
        """
        if rating_count == 0:
            return 0.0

        # Normalize rating to 0-1
        normalized_rating = (rating - 1) / 4

        # Weight by confidence (more ratings = higher confidence)
        # Confidence factor: min(rating_count / 10, 1)
        confidence = min(rating_count / 10, 1.0)

        return normalized_rating * confidence

    def _calculate_comment_score(self, comment_count: int) -> float:
        """Calculate normalized comment activity score (0-1).

        Args:
            comment_count: Number of comments

        Returns:
            Score between 0 and 1
        """
        # Logarithmic scaling: log(comments + 1) / log(101)
        # 0 comments = 0
        # 10 comments = 0.52
        # 100 comments = 1.0
        if comment_count <= 0:
            return 0.0

        return min(1.0, math.log(comment_count + 1) / math.log(101))

    def calculate_trending_score(self, widget: dict) -> dict:
        """Calculate overall trending score for a widget.

        Args:
            widget: Widget data

        Returns:
            Scoring breakdown
        """
        # Extract metrics
        downloads = widget.get('download_count', 0)
        rating = widget.get('rating', 0)
        rating_count = widget.get('rating_count', 0)
        comment_count = widget.get('comment_count', 0)
        created_at = widget.get('created_at', datetime.utcnow().isoformat() + 'Z')

        # Calculate component scores
        download_score = self._calculate_download_score(downloads)
        rating_score = self._calculate_rating_score(rating, rating_count)
        comment_score = self._calculate_comment_score(comment_count)
        recency_score = self._calculate_recency_score(created_at)

        # Calculate weighted total
        total_score = (
            download_score * self.weights['downloads'] +
            rating_score * self.weights['rating'] +
            comment_score * self.weights['comments'] +
            recency_score * self.weights['recency']
        ) * 100  # Scale to 0-100

        return {
            "total_score": round(total_score, 2),
            "download_score": round(download_score, 3),
            "rating_score": round(rating_score, 3),
            "comment_score": round(comment_score, 3),
            "recency_score": round(recency_score, 3),
            "downloads": downloads,
            "rating_weighted": rating,
            "comment_activity": comment_count
        }

    def calculate_trending(self, time_period_days: int = 1) -> List[dict]:
        """Calculate trending widgets for a time period.

        Args:
            time_period_days: Number of days to consider (1, 7, 30)

        Returns:
            List of trending widgets with scores
        """
        widgets = self._load_widgets()

        if not widgets:
            return []

        # Filter by time period
        cutoff = datetime.utcnow() - timedelta(days=time_period_days)
        recent_widgets = []

        for widget in widgets:
            created_at = datetime.fromisoformat(widget.get('created_at', '').replace('Z', ''))
            if created_at >= cutoff:
                recent_widgets.append(widget)

        # Calculate scores
        trending = []
        for widget in recent_widgets:
            score_data = self.calculate_trending_score(widget)

            trending.append({
                "widget_id": widget['id'],
                "name": widget['name'],
                "author": widget['author'],
                "score": score_data['total_score'],
                "metrics": score_data,
                "created_at": widget['created_at']
            })

        # Sort by score (descending)
        trending = sorted(trending, key=lambda x: x['score'], reverse=True)

        # Add rank and trend indicator
        for idx, item in enumerate(trending):
            item['rank'] = idx + 1

            # Trend indicator (simplified)
            if item['metrics']['recency_score'] > 0.8:
                item['trend'] = 'rising'
            elif item['metrics']['recency_score'] < 0.3:
                item['trend'] = 'declining'
            else:
                item['trend'] = 'stable'

        return trending

    def get_trending_cached(self, time_period_days: int = 1,
                           force_refresh: bool = False) -> List[dict]:
        """Get trending widgets with caching.

        Args:
            time_period_days: Number of days (1, 7, 30)
            force_refresh: Force recalculation

        Returns:
            List of trending widgets
        """
        period_key = f"trending_{time_period_days}d"

        # Check cache
        if not force_refresh and self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            last_calculated = datetime.fromisoformat(
                cache_data.get('last_calculated', '').replace('Z', '')
            )
            age_minutes = (datetime.utcnow() - last_calculated).total_seconds() / 60

            # Use cache if fresh
            if age_minutes < self.cache_duration_minutes:
                if period_key in cache_data:
                    return cache_data[period_key]

        # Calculate fresh
        trending = self.calculate_trending(time_period_days)

        # Update cache
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        else:
            cache_data = {}

        cache_data['last_calculated'] = datetime.utcnow().isoformat() + 'Z'
        cache_data['cache_duration_minutes'] = self.cache_duration_minutes
        cache_data[period_key] = trending

        self._atomic_write(self.cache_file, cache_data)

        return trending

    def get_featured_widgets(self) -> List[dict]:
        """Get manually featured widgets.

        Returns:
            List of featured widgets
        """
        if not self.cache_file.exists():
            return []

        with open(self.cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        return cache_data.get('featured', [])

    def add_featured(self, widget_id: str, featured_by: str = "admin") -> bool:
        """Add a widget to featured list (admin only).

        Args:
            widget_id: Widget identifier
            featured_by: Username featuring the widget

        Returns:
            True if added successfully
        """
        # Load widget data
        widgets = self._load_widgets()
        widget = next((w for w in widgets if w['id'] == widget_id), None)

        if not widget:
            return False

        # Load cache
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        else:
            cache_data = {
                'last_calculated': datetime.utcnow().isoformat() + 'Z',
                'featured': []
            }

        # Check if already featured
        featured = cache_data.get('featured', [])
        if any(f['widget_id'] == widget_id for f in featured):
            return False

        # Add to featured
        featured.append({
            "widget_id": widget_id,
            "name": widget['name'],
            "author": widget['author'],
            "featured_at": datetime.utcnow().isoformat() + 'Z',
            "featured_by": featured_by
        })

        cache_data['featured'] = featured
        self._atomic_write(self.cache_file, cache_data)

        return True

    def remove_featured(self, widget_id: str) -> bool:
        """Remove a widget from featured list.

        Args:
            widget_id: Widget identifier

        Returns:
            True if removed successfully
        """
        if not self.cache_file.exists():
            return False

        with open(self.cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        featured = cache_data.get('featured', [])
        original_count = len(featured)

        # Remove widget
        cache_data['featured'] = [
            f for f in featured
            if f['widget_id'] != widget_id
        ]

        if len(cache_data['featured']) < original_count:
            self._atomic_write(self.cache_file, cache_data)
            return True

        return False

    def invalidate_cache(self):
        """Invalidate trending cache to force recalculation."""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Keep featured, remove trending data
            cache_data = {
                'last_calculated': datetime.utcnow().isoformat() + 'Z',
                'featured': cache_data.get('featured', [])
            }

            self._atomic_write(self.cache_file, cache_data)
