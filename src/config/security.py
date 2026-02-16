"""
Security Configuration and Utilities
Provides centralized security settings and helper functions
"""

import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration with validation"""

    def __init__(self):
        self.load_config()

    def load_config(self):
        """Load and validate security configuration"""
        # Secret Key
        self.secret_key = os.environ.get('SECRET_KEY')
        if not self.secret_key:
            if os.environ.get('DEVELOPMENT_MODE', 'False') == 'True':
                logger.warning("Using generated secret key for development. DO NOT use in production!")
                self.secret_key = secrets.token_hex(32)
            else:
                raise RuntimeError(
                    "SECRET_KEY environment variable must be set in production.\n"
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )

        # Validate secret key strength
        if len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")

        # Session Configuration
        self.session_timeout = int(os.environ.get('SESSION_TIMEOUT', '30'))
        self.session_cookie_secure = os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True'
        self.session_cookie_httponly = True  # Always True
        self.session_cookie_samesite = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')

        # CSRF Configuration
        self.csrf_enabled = os.environ.get('CSRF_ENABLED', 'True') == 'True'
        self.csrf_time_limit = int(os.environ.get('CSRF_TIME_LIMIT', '3600'))

        # HTTPS Configuration
        self.force_https = os.environ.get('FORCE_HTTPS', 'True') == 'True'

        # CSP Configuration
        self.csp_config = {
            'default-src': os.environ.get('CSP_DEFAULT_SRC', "'self'").split(','),
            'script-src': os.environ.get('CSP_SCRIPT_SRC', "'self' 'unsafe-inline'").split(','),
            'style-src': os.environ.get('CSP_STYLE_SRC', "'self' 'unsafe-inline'").split(','),
        }

        # Development mode check
        self.development_mode = os.environ.get('DEVELOPMENT_MODE', 'False') == 'True'

        if self.development_mode:
            logger.warning("=" * 80)
            logger.warning("DEVELOPMENT MODE ENABLED - DO NOT USE IN PRODUCTION!")
            logger.warning("=" * 80)

    def apply_to_flask_app(self, app):
        """Apply security configuration to Flask app"""
        app.config['SECRET_KEY'] = self.secret_key
        app.config['PERMANENT_SESSION_LIFETIME'] = self.session_timeout * 60
        app.config['SESSION_COOKIE_SECURE'] = self.session_cookie_secure
        app.config['SESSION_COOKIE_HTTPONLY'] = self.session_cookie_httponly
        app.config['SESSION_COOKIE_SAMESITE'] = self.session_cookie_samesite

        # CSRF Configuration
        app.config['WTF_CSRF_ENABLED'] = self.csrf_enabled
        app.config['WTF_CSRF_TIME_LIMIT'] = self.csrf_time_limit

        return app


class PasswordValidator:
    """Password strength validation"""

    MINIMUM_LENGTH = 12

    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """
        Validate password meets complexity requirements

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < PasswordValidator.MINIMUM_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MINIMUM_LENGTH} characters"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        # Check for common passwords
        common_passwords = ['password', 'admin123', 'letmein', '123456', 'qwerty']
        if password.lower() in common_passwords:
            return False, "Password is too common. Please choose a stronger password."

        return True, "Password is valid"


class PathValidator:
    """Path validation to prevent traversal attacks"""

    def __init__(self, allowed_base_dir: Path):
        """
        Initialize path validator

        Args:
            allowed_base_dir: Base directory that all paths must be within
        """
        self.allowed_base_dir = allowed_base_dir.resolve()

    def validate(self, filepath: Path) -> Path:
        """
        Validate that path is within allowed directory

        Args:
            filepath: Path to validate

        Returns:
            Resolved path if valid

        Raises:
            SecurityError: If path is outside allowed directory
        """
        resolved_path = filepath.resolve()

        try:
            resolved_path.relative_to(self.allowed_base_dir)
        except ValueError:
            raise SecurityError(
                f"Path {filepath} is outside allowed directory {self.allowed_base_dir}"
            )

        return resolved_path


class FilenameValidator:
    """Filename validation to prevent injection attacks"""

    @staticmethod
    def sanitize(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and injection

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)

        # Remove null bytes
        filename = filename.replace('\0', '')

        # Allow only safe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Prevent hidden files
        if filename.startswith('.'):
            filename = '_' + filename[1:]

        # Ensure not empty
        if not filename:
            filename = 'unnamed_file'

        return filename


class CommandValidator:
    """Command validation to prevent injection attacks"""

    ALLOWED_SCRIPTS = {
        'pid-tracker.py',
        'context-monitor.py',
        'session-tracker.py',
        'policy-checker.py',
    }

    @staticmethod
    def validate_script_path(script_path: Path, allowed_dir: Path) -> Path:
        """
        Validate that script is in allowed directory and on whitelist

        Args:
            script_path: Path to script
            allowed_dir: Directory containing allowed scripts

        Returns:
            Validated script path

        Raises:
            SecurityError: If script is not allowed
        """
        # Check if script name is on whitelist
        script_name = script_path.name
        if script_name not in CommandValidator.ALLOWED_SCRIPTS:
            raise SecurityError(f"Script {script_name} is not on allowed list")

        # Validate path is within allowed directory
        validator = PathValidator(allowed_dir)
        validated_path = validator.validate(script_path)

        # Ensure file exists and is a file
        if not validated_path.exists():
            raise SecurityError(f"Script {script_name} does not exist")

        if not validated_path.is_file():
            raise SecurityError(f"Script {script_name} is not a file")

        return validated_path


class LogSanitizer:
    """Sanitize sensitive data from log messages"""

    PATTERNS = {
        'email': (r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]'),
        'phone': (r'\d{3}[-.]?\d{3}[-.]?\d{4}', '[PHONE_REDACTED]'),
        'api_key': (r'[A-Za-z0-9]{32,}', '[API_KEY_REDACTED]'),
        'password': (r'password["\']?\s*[:=]\s*["\']?[\w!@#$%^&*]+', 'password=[PASSWORD_REDACTED]'),
        'token': (r'token["\']?\s*[:=]\s*["\']?[\w-]+', 'token=[TOKEN_REDACTED]'),
    }

    @staticmethod
    def sanitize(message: str) -> str:
        """
        Remove sensitive data from log message

        Args:
            message: Original log message

        Returns:
            Sanitized message
        """
        sanitized = message

        for pattern_name, (pattern, replacement) in LogSanitizer.PATTERNS.items():
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized


class SecurityError(Exception):
    """Security validation error"""
    pass


# Export singleton instance
security_config = SecurityConfig()
