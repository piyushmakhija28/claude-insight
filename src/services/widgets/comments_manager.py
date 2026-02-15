"""
Widget Comments Manager
Handles comments, threading, mentions, and reactions for community widgets.
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class WidgetCommentsManager:
    """Manages comments, threads, mentions, and reactions for widgets."""

    def __init__(self, base_dir: str = None):
        """Initialize the comments manager.

        Args:
            base_dir: Base directory for comments storage. Defaults to ~/.claude/memory/community
        """
        if base_dir is None:
            base_dir = os.path.expanduser("~/.claude/memory/community")

        self.base_dir = Path(base_dir)
        self.comments_dir = self.base_dir / "widget_comments"
        self.comments_dir.mkdir(parents=True, exist_ok=True)

    def _get_comments_file(self, widget_id: str) -> Path:
        """Get the path to the comments file for a widget."""
        return self.comments_dir / f"{widget_id}_comments.json"

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

    def _generate_comment_id(self) -> str:
        """Generate unique comment ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"comment_{timestamp}_{os.urandom(2).hex()}"

    def _generate_thread_id(self) -> str:
        """Generate unique thread ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"thread_{timestamp}_{os.urandom(2).hex()}"

    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from comment content.

        Args:
            content: Comment text

        Returns:
            List of mentioned usernames
        """
        # Match @username patterns (alphanumeric, underscore, hyphen)
        mentions = re.findall(r'@([\w-]+)', content)
        return list(set(mentions))  # Remove duplicates

    def _sanitize_content(self, content: str) -> str:
        """Sanitize comment content to prevent XSS.

        Args:
            content: Raw comment text

        Returns:
            Sanitized content
        """
        # Basic HTML escaping
        content = content.replace('&', '&amp;')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        content = content.replace('"', '&quot;')
        content = content.replace("'", '&#x27;')

        # Limit length
        max_length = 5000
        if len(content) > max_length:
            content = content[:max_length]

        return content

    def initialize_comments(self, widget_id: str) -> dict:
        """Initialize comments structure for a widget.

        Args:
            widget_id: Widget identifier

        Returns:
            Initial comments data
        """
        comments_file = self._get_comments_file(widget_id)

        if comments_file.exists():
            with open(comments_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        comments_data = {
            "widget_id": widget_id,
            "total_comments": 0,
            "comments": []
        }

        self._atomic_write(comments_file, comments_data)
        return comments_data

    def add_comment(self, widget_id: str, author: str, content: str,
                   parent_comment_id: Optional[str] = None,
                   thread_id: Optional[str] = None) -> dict:
        """Add a comment to a widget.

        Args:
            widget_id: Widget identifier
            author: Comment author username
            content: Comment text
            parent_comment_id: Parent comment ID (for replies)
            thread_id: Thread ID (auto-assigned if not provided)

        Returns:
            New comment data
        """
        comments_file = self._get_comments_file(widget_id)

        # Load or initialize
        if comments_file.exists():
            with open(comments_file, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)
        else:
            comments_data = self.initialize_comments(widget_id)

        # Sanitize content
        content = self._sanitize_content(content)

        # Extract mentions
        mentions = self._extract_mentions(content)

        # Generate IDs
        comment_id = self._generate_comment_id()

        # Determine thread_id
        if parent_comment_id:
            # Find parent's thread_id
            parent = next((c for c in comments_data['comments']
                         if c['id'] == parent_comment_id), None)
            if parent:
                thread_id = parent['thread_id']
            else:
                thread_id = thread_id or self._generate_thread_id()
        else:
            thread_id = thread_id or self._generate_thread_id()

        # Create comment
        timestamp = datetime.utcnow().isoformat() + 'Z'
        comment = {
            "id": comment_id,
            "thread_id": thread_id,
            "parent_comment_id": parent_comment_id,
            "author": author,
            "content": content,
            "created_at": timestamp,
            "updated_at": timestamp,
            "mentions": mentions,
            "reactions": {},
            "status": "visible"
        }

        # Add to comments list
        comments_data['comments'].append(comment)
        comments_data['total_comments'] = len(comments_data['comments'])

        # Save
        self._atomic_write(comments_file, comments_data)

        return comment

    def get_comments(self, widget_id: str, limit: int = 50,
                    offset: int = 0, thread_id: Optional[str] = None) -> List[dict]:
        """Get comments for a widget.

        Args:
            widget_id: Widget identifier
            limit: Maximum number of comments to return
            offset: Number of comments to skip
            thread_id: Filter by thread (optional)

        Returns:
            List of comments (newest first)
        """
        comments_file = self._get_comments_file(widget_id)

        if not comments_file.exists():
            return []

        with open(comments_file, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        comments = comments_data.get('comments', [])

        # Filter by thread if specified
        if thread_id:
            comments = [c for c in comments if c['thread_id'] == thread_id]

        # Filter out deleted comments
        comments = [c for c in comments if c['status'] != 'deleted']

        # Sort by created_at (newest first)
        comments = sorted(comments, key=lambda c: c['created_at'], reverse=True)

        return comments[offset:offset + limit]

    def get_comment(self, widget_id: str, comment_id: str) -> Optional[dict]:
        """Get a specific comment.

        Args:
            widget_id: Widget identifier
            comment_id: Comment identifier

        Returns:
            Comment data or None if not found
        """
        comments_file = self._get_comments_file(widget_id)

        if not comments_file.exists():
            return None

        with open(comments_file, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        comments = comments_data.get('comments', [])
        return next((c for c in comments if c['id'] == comment_id), None)

    def update_comment(self, widget_id: str, comment_id: str,
                      author: str, new_content: str) -> Optional[dict]:
        """Update a comment (only by author).

        Args:
            widget_id: Widget identifier
            comment_id: Comment identifier
            author: Username attempting update
            new_content: New comment text

        Returns:
            Updated comment data or None if not found/unauthorized
        """
        comments_file = self._get_comments_file(widget_id)

        if not comments_file.exists():
            return None

        with open(comments_file, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        # Find comment
        comment = next((c for c in comments_data['comments']
                       if c['id'] == comment_id), None)

        if not comment:
            return None

        # Verify author
        if comment['author'] != author:
            raise PermissionError("Only comment author can edit")

        # Update content
        comment['content'] = self._sanitize_content(new_content)
        comment['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        comment['mentions'] = self._extract_mentions(new_content)

        # Save
        self._atomic_write(comments_file, comments_data)

        return comment

    def delete_comment(self, widget_id: str, comment_id: str,
                      author: str, is_admin: bool = False) -> bool:
        """Delete a comment (author or admin only).

        Args:
            widget_id: Widget identifier
            comment_id: Comment identifier
            author: Username attempting deletion
            is_admin: Whether user is admin

        Returns:
            True if deleted successfully
        """
        comments_file = self._get_comments_file(widget_id)

        if not comments_file.exists():
            return False

        with open(comments_file, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        # Find comment
        comment = next((c for c in comments_data['comments']
                       if c['id'] == comment_id), None)

        if not comment:
            return False

        # Verify permission
        if comment['author'] != author and not is_admin:
            raise PermissionError("Only comment author or admin can delete")

        # Soft delete
        comment['status'] = 'deleted'
        comment['updated_at'] = datetime.utcnow().isoformat() + 'Z'

        # Save
        self._atomic_write(comments_file, comments_data)

        return True

    def add_reaction(self, widget_id: str, comment_id: str,
                    user: str, reaction_type: str) -> Optional[dict]:
        """Add a reaction to a comment.

        Args:
            widget_id: Widget identifier
            comment_id: Comment identifier
            user: Username adding reaction
            reaction_type: Type of reaction (e.g., 'thumbs_up', 'heart')

        Returns:
            Updated comment data or None if not found
        """
        comments_file = self._get_comments_file(widget_id)

        if not comments_file.exists():
            return None

        with open(comments_file, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        # Find comment
        comment = next((c for c in comments_data['comments']
                       if c['id'] == comment_id), None)

        if not comment:
            return None

        # Add reaction
        if reaction_type not in comment['reactions']:
            comment['reactions'][reaction_type] = 0

        comment['reactions'][reaction_type] += 1

        # Save
        self._atomic_write(comments_file, comments_data)

        return comment

    def get_thread(self, widget_id: str, thread_id: str) -> List[dict]:
        """Get all comments in a thread.

        Args:
            widget_id: Widget identifier
            thread_id: Thread identifier

        Returns:
            List of comments in thread (chronological order)
        """
        comments_file = self._get_comments_file(widget_id)

        if not comments_file.exists():
            return []

        with open(comments_file, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        comments = comments_data.get('comments', [])

        # Filter by thread and status
        thread_comments = [
            c for c in comments
            if c['thread_id'] == thread_id and c['status'] != 'deleted'
        ]

        # Sort chronologically
        thread_comments = sorted(thread_comments, key=lambda c: c['created_at'])

        return thread_comments

    def get_user_mentions(self, username: str, limit: int = 20) -> List[dict]:
        """Get all comments where a user was mentioned.

        Args:
            username: Username to search for
            limit: Maximum number of mentions to return

        Returns:
            List of comments with mentions
        """
        mentions = []

        # Scan all comment files
        for comments_file in self.comments_dir.glob("*_comments.json"):
            with open(comments_file, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)

            for comment in comments_data.get('comments', []):
                if username in comment.get('mentions', []) and \
                   comment['status'] != 'deleted':
                    comment['widget_id'] = comments_data['widget_id']
                    mentions.append(comment)

        # Sort by created_at (newest first)
        mentions = sorted(mentions, key=lambda c: c['created_at'], reverse=True)

        return mentions[:limit]

    def get_comment_count(self, widget_id: str) -> int:
        """Get total comment count for a widget.

        Args:
            widget_id: Widget identifier

        Returns:
            Number of visible comments
        """
        comments_file = self._get_comments_file(widget_id)

        if not comments_file.exists():
            return 0

        with open(comments_file, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        comments = comments_data.get('comments', [])
        visible = [c for c in comments if c['status'] != 'deleted']

        return len(visible)
