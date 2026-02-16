"""
User Management System
Replaces hardcoded credentials with secure user management
"""

import os
import json
import bcrypt
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class UserManager:
    """Secure user management system"""

    def __init__(self, users_file: Optional[Path] = None):
        """
        Initialize user manager

        Args:
            users_file: Path to users database file (defaults to data/users.json)
        """
        if users_file is None:
            data_dir = Path(__file__).parent.parent.parent / 'data'
            data_dir.mkdir(exist_ok=True)
            users_file = data_dir / 'users.json'

        self.users_file = users_file
        self.users = self._load_users()
        self.failed_attempts = {}  # Track failed login attempts
        self.lockout_duration = timedelta(minutes=15)
        self.max_failed_attempts = 5

    def _load_users(self) -> Dict[str, Any]:
        """Load users from file"""
        if not self.users_file.exists():
            # Create default admin user on first run
            return self._create_default_admin()

        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
                logger.info(f"Loaded {len(users)} users from {self.users_file}")
                return users
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return {}

    def _save_users(self):
        """Save users to file"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2)
            logger.info(f"Saved {len(self.users)} users to {self.users_file}")
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def _create_default_admin(self) -> Dict[str, Any]:
        """
        Create default admin user

        Password is read from environment variable or prompts on first run
        """
        admin_password = os.environ.get('ADMIN_PASSWORD')

        if not admin_password:
            # In production, this should fail. In development, use a secure default
            if os.environ.get('DEVELOPMENT_MODE', 'False') == 'True':
                logger.warning("=" * 80)
                logger.warning("CREATING DEFAULT ADMIN USER FOR DEVELOPMENT")
                logger.warning("Username: admin")
                logger.warning("Password: CHANGE_ME_IMMEDIATELY")
                logger.warning("YOU MUST CHANGE THIS PASSWORD IMMEDIATELY!")
                logger.warning("=" * 80)
                admin_password = "CHANGE_ME_IMMEDIATELY"
            else:
                raise RuntimeError(
                    "ADMIN_PASSWORD environment variable must be set on first run.\n"
                    "This will create the initial admin user."
                )

        users = {
            'admin': {
                'password_hash': bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                'role': 'admin',
                'created_at': datetime.now().isoformat(),
                'must_change_password': True,
                'enabled': True
            }
        }

        # Save to file
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)

        logger.info("Created default admin user")
        return users

    def verify_password(self, username: str, password: str) -> tuple[bool, Optional[str]]:
        """
        Verify username and password

        Args:
            username: Username to verify
            password: Password to verify

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if account is locked
        if self.is_account_locked(username):
            lockout_until = self.failed_attempts[username]['locked_until']
            minutes_remaining = int((lockout_until - datetime.now()).total_seconds() / 60)
            return False, f"Account locked. Try again in {minutes_remaining} minutes."

        # Check if user exists
        if username not in self.users:
            # Simulate password check to prevent timing attacks
            bcrypt.checkpw(b"dummy", bcrypt.gensalt())
            self._record_failed_attempt(username)
            return False, "Invalid username or password"

        # Check if account is enabled
        if not self.users[username].get('enabled', True):
            return False, "Account is disabled"

        # Verify password
        try:
            stored_hash = self.users[username]['password_hash'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                # Clear failed attempts on successful login
                if username in self.failed_attempts:
                    del self.failed_attempts[username]
                return True, None
            else:
                self._record_failed_attempt(username)
                return False, "Invalid username or password"
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False, "Authentication error"

    def update_password(self, username: str, new_password: str, old_password: Optional[str] = None) -> tuple[bool, str]:
        """
        Update user password

        Args:
            username: Username to update
            new_password: New password
            old_password: Current password (required unless force update)

        Returns:
            Tuple of (success, message)
        """
        if username not in self.users:
            return False, "User not found"

        # Verify old password if provided
        if old_password is not None:
            is_valid, error = self.verify_password(username, old_password)
            if not is_valid:
                return False, "Current password is incorrect"

        # Validate new password strength
        from config.security import PasswordValidator
        is_valid, message = PasswordValidator.validate(new_password)
        if not is_valid:
            return False, message

        # Update password
        try:
            self.users[username]['password_hash'] = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            self.users[username]['password_changed_at'] = datetime.now().isoformat()
            self.users[username]['must_change_password'] = False
            self._save_users()
            logger.info(f"Password updated for user: {username}")
            return True, "Password updated successfully"
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False, "Error updating password"

    def create_user(self, username: str, password: str, role: str = 'user') -> tuple[bool, str]:
        """
        Create new user

        Args:
            username: New username
            password: Initial password
            role: User role (admin or user)

        Returns:
            Tuple of (success, message)
        """
        if username in self.users:
            return False, "Username already exists"

        # Validate password
        from config.security import PasswordValidator
        is_valid, message = PasswordValidator.validate(password)
        if not is_valid:
            return False, message

        try:
            self.users[username] = {
                'password_hash': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                'role': role,
                'created_at': datetime.now().isoformat(),
                'must_change_password': True,
                'enabled': True
            }
            self._save_users()
            logger.info(f"Created new user: {username}")
            return True, "User created successfully"
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, "Error creating user"

    def must_change_password(self, username: str) -> bool:
        """Check if user must change password on next login"""
        if username not in self.users:
            return False
        return self.users[username].get('must_change_password', False)

    def get_user_role(self, username: str) -> Optional[str]:
        """Get user role"""
        if username not in self.users:
            return None
        return self.users[username].get('role', 'user')

    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                'count': 0,
                'first_attempt': datetime.now(),
                'locked_until': None
            }

        self.failed_attempts[username]['count'] += 1

        # Lock account if too many failed attempts
        if self.failed_attempts[username]['count'] >= self.max_failed_attempts:
            self.failed_attempts[username]['locked_until'] = datetime.now() + self.lockout_duration
            logger.warning(f"Account locked due to failed attempts: {username}")

    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts"""
        if username not in self.failed_attempts:
            return False

        locked_until = self.failed_attempts[username].get('locked_until')
        if locked_until is None:
            return False

        # Check if lockout has expired
        if datetime.now() >= locked_until:
            del self.failed_attempts[username]
            return False

        return True

    def enable_user(self, username: str) -> tuple[bool, str]:
        """Enable user account"""
        if username not in self.users:
            return False, "User not found"

        self.users[username]['enabled'] = True
        self._save_users()
        logger.info(f"Enabled user: {username}")
        return True, "User enabled"

    def disable_user(self, username: str) -> tuple[bool, str]:
        """Disable user account"""
        if username not in self.users:
            return False, "User not found"

        self.users[username]['enabled'] = False
        self._save_users()
        logger.info(f"Disabled user: {username}")
        return True, "User disabled"
