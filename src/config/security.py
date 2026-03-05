"""Security configuration and utilities for Claude Insight.

Provides a centralised collection of security-related classes that enforce
safe defaults for the Flask application. All classes are designed to fail
loudly during startup (via logging warnings) rather than silently accepting
weak or missing configuration.

Classes:
    SecurityConfig    -- Loads and validates all security settings from
                         environment variables or a .env file. Applies them
                         to a Flask app via ``apply_to_flask_app()``.
    PasswordValidator -- Enforces password complexity rules (length,
                         character classes, common-password blacklist).
    PathValidator     -- Prevents directory traversal by ensuring all file
                         paths remain within a declared base directory.
    FilenameValidator -- Sanitises user-supplied filenames to remove
                         path components, null bytes, and unsafe characters.
    CommandValidator  -- Restricts subprocess execution to a whitelist of
                         known-safe script names within an allowed directory.
    LogSanitizer      -- Redacts sensitive patterns (passwords, tokens,
                         emails, phone numbers) from log messages.
    SecurityError     -- Exception raised by the validator classes when a
                         security constraint is violated.

Environment variables:
    SECRET_KEY              -- HMAC session signing key (min 32 chars).
    SESSION_TIMEOUT         -- Session lifetime in minutes (default 30).
    SESSION_COOKIE_SECURE   -- Require HTTPS for cookies (default True).
    SESSION_COOKIE_SAMESITE -- SameSite cookie policy (default 'Lax').
    CSRF_ENABLED            -- Enable CSRF protection (default True).
    CSRF_TIME_LIMIT         -- CSRF token lifetime in seconds (default 3600).
    FORCE_HTTPS             -- Redirect HTTP to HTTPS (default True).
    DEVELOPMENT_MODE        -- Relaxes some checks; DO NOT use in production.
"""

import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration with validation.

    Loads all security settings at construction time by calling
    ``load_config()``. Settings are sourced from environment variables
    first, then from a ``.env`` file in the project root, and finally
    from safe defaults where applicable.

    Attributes:
        secret_key: HMAC key for signing Flask sessions.
        session_timeout: Session lifetime in minutes.
        session_cookie_secure: Whether to set the Secure cookie flag.
        session_cookie_httponly: Always True (HttpOnly flag always set).
        session_cookie_samesite: SameSite cookie policy string.
        csrf_enabled: Whether CSRF protection is active.
        csrf_time_limit: CSRF token validity window in seconds.
        force_https: Whether to redirect HTTP requests to HTTPS.
        csp_config: Content Security Policy directives dict.
        development_mode: Whether relaxed development checks are active.

    Example::

        from src.config.security import SecurityConfig
        sec = SecurityConfig()
        sec.apply_to_flask_app(app)
    """

    def __init__(self):
        """Initialise and validate security configuration from environment."""
        self.load_config()

    def load_config(self) -> None:
        """Load and validate all security configuration values.

        Resolution order for ``SECRET_KEY``:
            1. ``SECRET_KEY`` environment variable.
            2. ``SECRET_KEY`` key in a ``.env`` file at the project root.
            3. Ephemeral random 32-byte hex key (warns, not suitable for
               multi-process or persistent-session deployments).

        Keys shorter than 32 characters are rejected and replaced with a
        freshly generated secure key, with a warning logged.
        """
        # Secret Key — try env var first, then .env file, then generate fallback
        self.secret_key = os.environ.get('SECRET_KEY')

        # Try loading from .env file if not in environment
        if not self.secret_key:
            self.secret_key = self._read_env_file_key('SECRET_KEY')

        if not self.secret_key:
            logger.warning("SECRET_KEY not set — generating ephemeral key. Set SECRET_KEY env var for persistence.")
            self.secret_key = secrets.token_hex(32)

        # Validate secret key strength
        if len(self.secret_key) < 32:
            logger.warning("SECRET_KEY too short, generating a secure one")
            self.secret_key = secrets.token_hex(32)

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

    @staticmethod
    def _read_env_file_key(key):
        """Read a single key value from the .env file in the project root.

        Parses key=value lines, skipping blanks and comments. Returns the
        first matching value found.

        Args:
            key (str): Environment variable name to look up.

        Returns:
            str or None: The value string if found, or None if the file does
                not exist, the key is not present, or a read error occurs.
        """
        try:
            env_path = Path(__file__).parent.parent.parent / '.env'
            if env_path.exists():
                for line in env_path.read_text(encoding='utf-8').splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() == key:
                            return v.strip()
        except Exception:
            pass
        return None

    def apply_to_flask_app(self, app):
        """Apply security configuration to a Flask application instance.

        Sets ``app.config`` keys for secret key, session cookies, and CSRF
        protection. Must be called after ``app`` is created but before the
        first request is handled.

        Args:
            app: The Flask application instance to configure.

        Returns:
            The configured Flask application instance (for chaining).
        """
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
    """Enforce password complexity requirements.

    Validates that passwords meet minimum length, character class diversity,
    and are not in the common-password blacklist.

    Class Attributes:
        MINIMUM_LENGTH (int): Minimum required password length (default 12).
    """

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

        # Check for common passwords (case-insensitive, substring match)
        common_passwords = ['password', 'admin', 'letmein', '123456', 'qwerty', 'welcome', 'passw0rd']
        password_lower = password.lower()
        for common in common_passwords:
            if common in password_lower:
                return False, "Password contains common patterns. Please choose a stronger password."

        return True, "Password is valid"


class PathValidator:
    """Prevent directory traversal attacks by constraining file access to a base directory.

    All paths submitted to validate() are resolved to absolute form and checked
    against the allowed_base_dir. Raises SecurityError for any path that escapes
    the declared directory.

    Attributes:
        allowed_base_dir (Path): Resolved absolute base directory. All validated
            paths must be descendants of this directory.
    """

    def __init__(self, allowed_base_dir: Path):
        """Initialize PathValidator with the permitted base directory.

        Args:
            allowed_base_dir (Path): Directory that all validated paths must
                reside within. The path is resolved to its canonical absolute
                form on initialization.
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
    """Command validation to prevent injection attacks.

    Restricts subprocess execution to a whitelist of known-safe script
    names and enforces that those scripts reside within a declared allowed
    directory. This prevents arbitrary code execution via crafted paths.

    Class attributes:
        ALLOWED_SCRIPTS: Set of filenames (basename only) that may be
            executed. Any other script name raises ``SecurityError``.
    """

    ALLOWED_SCRIPTS = {
        'context-monitor-v2.py',
        'blocking-policy-enforcer.py',
        'per-request-enforcer.py',
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
    """Sanitise sensitive data from log messages before they are persisted.

    Applies a sequence of regex substitutions to replace API keys,
    passwords, tokens, email addresses, and phone numbers with
    redaction placeholders. Patterns are applied in declaration order;
    more specific patterns are listed before general ones to avoid
    partial matches masking full replacements.

    Class attributes:
        PATTERNS: List of ``(name, regex_pattern, replacement)`` tuples
            applied in order by ``sanitize()``.
    """

    # Order matters: More specific patterns should come before general ones
    PATTERNS = [
        ('api_key', r'(?:api[_\s-]?key[:\s=]+\s*)([A-Za-z0-9]{12,})', r'[API_KEY_REDACTED]'),
        ('password', r'password["\']?\s*[:=]\s*["\']?[\w!@#$%^&*]+', 'password=[PASSWORD_REDACTED]'),
        ('token', r'token["\']?\s*[:=]\s*["\']?[\w-]+', 'token=[TOKEN_REDACTED]'),
        ('email', r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]'),
        ('phone', r'\d{3}[-.]?\d{3}[-.]?\d{4}', '[PHONE_REDACTED]'),
    ]

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

        for pattern_name, pattern, replacement in LogSanitizer.PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized


class SecurityError(Exception):
    """Exception raised when a security constraint is violated.

    Raised by ``PathValidator``, ``CommandValidator``, and any other
    validator that detects an unsafe operation. Callers should catch
    this exception and return an appropriate HTTP 400/403 response
    rather than propagating it to the user as a 500 error.
    """


# Export singleton instance
security_config = SecurityConfig()
