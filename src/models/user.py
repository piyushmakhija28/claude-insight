"""User Model for Authentication and Authorization"""

from datetime import datetime
from typing import Dict, List, Optional


class User:
    """User model for the monitoring system"""

    def __init__(
        self,
        username: str,
        email: str,
        user_id: Optional[str] = None,
        role: str = 'user',
        created_at: Optional[datetime] = None,
        last_login: Optional[datetime] = None,
        preferences: Optional[Dict] = None,
        is_active: bool = True
    ):
        self.user_id = user_id or self._generate_id()
        self.username = username
        self.email = email
        self.role = role
        self.created_at = created_at or datetime.now()
        self.last_login = last_login
        self.preferences = preferences or {}
        self.is_active = is_active

    @staticmethod
    def _generate_id() -> str:
        """Generate unique user ID"""
        import uuid
        return str(uuid.uuid4())

    def to_dict(self) -> Dict:
        """Convert user to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferences': self.preferences,
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary"""
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        last_login = datetime.fromisoformat(data['last_login']) if data.get('last_login') else None

        return cls(
            user_id=data.get('user_id'),
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'user'),
            created_at=created_at,
            last_login=last_login,
            preferences=data.get('preferences', {}),
            is_active=data.get('is_active', True)
        )

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now()

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        # Role-based permissions
        permissions_map = {
            'admin': ['read', 'write', 'delete', 'manage_users', 'configure_system'],
            'developer': ['read', 'write', 'create_widgets'],
            'user': ['read']
        }
        return permission in permissions_map.get(self.role, [])

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
