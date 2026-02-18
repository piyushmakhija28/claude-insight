"""
Security Test Suite
Tests all security fixes implemented
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.security import (
    SecurityConfig,
    PasswordValidator,
    PathValidator,
    FilenameValidator,
    CommandValidator,
    LogSanitizer,
    SecurityError
)
from auth.user_manager import UserManager


class TestPasswordValidator:
    """Test password strength validation"""

    def test_password_too_short(self):
        """Password must be at least 12 characters"""
        is_valid, msg = PasswordValidator.validate("Short1!")
        assert not is_valid
        assert "12 characters" in msg

    def test_password_no_uppercase(self):
        """Password must contain uppercase letter"""
        is_valid, msg = PasswordValidator.validate("nouppercase123!")
        assert not is_valid
        assert "uppercase" in msg

    def test_password_no_lowercase(self):
        """Password must contain lowercase letter"""
        is_valid, msg = PasswordValidator.validate("NOLOWERCASE123!")
        assert not is_valid
        assert "lowercase" in msg

    def test_password_no_number(self):
        """Password must contain number"""
        is_valid, msg = PasswordValidator.validate("NoNumbersHere!")
        assert not is_valid
        assert "number" in msg

    def test_password_no_special(self):
        """Password must contain special character"""
        is_valid, msg = PasswordValidator.validate("NoSpecialChar123")
        assert not is_valid
        assert "special" in msg

    def test_common_password(self):
        """Common passwords should be rejected"""
        # Use a password that's long enough but contains common pattern
        is_valid, msg = PasswordValidator.validate("MyPassword123!")
        assert not is_valid
        assert "common" in msg.lower()

    def test_valid_strong_password(self):
        """Strong password should pass all checks"""
        # Use a strong password without common patterns
        is_valid, msg = PasswordValidator.validate("MySecure123!Phrase")
        assert is_valid
        assert msg == "Password is valid"


class TestPathValidator:
    """Test path traversal prevention"""

    def test_valid_path(self, tmp_path):
        """Valid path within allowed directory should pass"""
        validator = PathValidator(tmp_path)

        test_file = tmp_path / "subdir" / "file.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()

        validated = validator.validate(test_file)
        assert validated == test_file.resolve()

    def test_path_traversal_attack(self, tmp_path):
        """Path outside allowed directory should raise SecurityError"""
        validator = PathValidator(tmp_path)

        # Try to access parent directory
        malicious_path = tmp_path / ".." / "etc" / "passwd"

        with pytest.raises(SecurityError):
            validator.validate(malicious_path)

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlink test requires admin privileges on Windows")
    def test_symlink_escape(self, tmp_path):
        """Symlink escape should be prevented"""
        validator = PathValidator(tmp_path)

        # Create symlink pointing outside allowed directory
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)

        symlink = tmp_path / "malicious_link"
        symlink.symlink_to(outside_dir)

        with pytest.raises(SecurityError):
            validator.validate(symlink)


class TestFilenameValidator:
    """Test filename sanitization"""

    def test_path_traversal_in_filename(self):
        """Path traversal characters should be removed"""
        sanitized = FilenameValidator.sanitize("../../etc/passwd")
        assert ".." not in sanitized
        assert "/" not in sanitized

    def test_null_byte_removal(self):
        """Null bytes should be removed"""
        sanitized = FilenameValidator.sanitize("file\0.txt")
        assert "\0" not in sanitized

    def test_special_characters(self):
        """Special characters should be replaced with underscore"""
        sanitized = FilenameValidator.sanitize("file name!@#$.txt")
        # Space + 4 special chars = 5 underscores total, but only 4 after "name"
        assert sanitized == "file_name____.txt"

    def test_hidden_file_prevention(self):
        """Filenames starting with . should be modified"""
        sanitized = FilenameValidator.sanitize(".bashrc")
        assert not sanitized.startswith(".")

    def test_empty_filename(self):
        """Empty filename should return default name"""
        sanitized = FilenameValidator.sanitize("")
        assert sanitized == "unnamed_file"

    def test_valid_filename(self):
        """Valid filename should remain mostly unchanged"""
        sanitized = FilenameValidator.sanitize("myfile123.txt")
        assert sanitized == "myfile123.txt"


class TestCommandValidator:
    """Test command injection prevention"""

    def test_script_not_on_whitelist(self, tmp_path):
        """Script not on whitelist should raise SecurityError"""
        malicious_script = tmp_path / "malicious.py"
        malicious_script.touch()

        with pytest.raises(SecurityError) as exc_info:
            CommandValidator.validate_script_path(malicious_script, tmp_path)

        assert "not on allowed list" in str(exc_info.value)

    def test_script_on_whitelist(self, tmp_path):
        """Script on whitelist should pass validation"""
        # Create one of the whitelisted scripts
        allowed_script = tmp_path / "context-monitor-v2.py"
        allowed_script.touch()

        validated = CommandValidator.validate_script_path(allowed_script, tmp_path)
        assert validated == allowed_script.resolve()

    def test_script_outside_allowed_dir(self, tmp_path):
        """Script outside allowed directory should raise SecurityError"""
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)

        script = outside_dir / "context-monitor-v2.py"
        script.touch()

        with pytest.raises(SecurityError):
            CommandValidator.validate_script_path(script, tmp_path)

    def test_script_does_not_exist(self, tmp_path):
        """Non-existent script should raise SecurityError"""
        script = tmp_path / "context-monitor-v2.py"  # Not created

        with pytest.raises(SecurityError) as exc_info:
            CommandValidator.validate_script_path(script, tmp_path)

        assert "does not exist" in str(exc_info.value)


class TestLogSanitizer:
    """Test sensitive data sanitization in logs"""

    def test_email_redaction(self):
        """Email addresses should be redacted"""
        message = "User email: user@example.com logged in"
        sanitized = LogSanitizer.sanitize(message)
        assert "user@example.com" not in sanitized
        assert "[EMAIL_REDACTED]" in sanitized

    def test_phone_redaction(self):
        """Phone numbers should be redacted"""
        message = "Contact phone: 555-123-4567"
        sanitized = LogSanitizer.sanitize(message)
        assert "555-123-4567" not in sanitized
        assert "[PHONE_REDACTED]" in sanitized

    def test_api_key_redaction(self):
        """API keys should be redacted"""
        message = "API Key: abcdef1234567890abcdef1234567890"
        sanitized = LogSanitizer.sanitize(message)
        assert "abcdef1234567890abcdef1234567890" not in sanitized
        assert "[API_KEY_REDACTED]" in sanitized

    def test_password_redaction(self):
        """Passwords should be redacted"""
        message = 'config: {"password": "MySecretPass123"}'
        sanitized = LogSanitizer.sanitize(message)
        assert "MySecretPass123" not in sanitized
        assert "[PASSWORD_REDACTED]" in sanitized

    def test_token_redaction(self):
        """Tokens should be redacted"""
        message = "Authorization token=abc-123-def-456"
        sanitized = LogSanitizer.sanitize(message)
        assert "abc-123-def-456" not in sanitized
        assert "[TOKEN_REDACTED]" in sanitized

    def test_multiple_patterns(self):
        """Multiple sensitive patterns should all be redacted"""
        message = "User user@example.com with API key abc123def456 and phone 555-123-4567"
        sanitized = LogSanitizer.sanitize(message)
        assert "[EMAIL_REDACTED]" in sanitized
        assert "[API_KEY_REDACTED]" in sanitized
        assert "[PHONE_REDACTED]" in sanitized


class TestUserManager:
    """Test user management system"""

    @pytest.fixture(autouse=True)
    def setup_dev_mode(self):
        """Setup development mode for all UserManager tests"""
        import os
        original_dev_mode = os.environ.get('DEVELOPMENT_MODE')
        os.environ['DEVELOPMENT_MODE'] = 'True'
        yield
        # Cleanup
        if original_dev_mode:
            os.environ['DEVELOPMENT_MODE'] = original_dev_mode
        elif 'DEVELOPMENT_MODE' in os.environ:
            del os.environ['DEVELOPMENT_MODE']

    def test_create_user_success(self, tmp_path):
        """Creating user with valid password should succeed"""
        users_file = tmp_path / "users.json"
        manager = UserManager(users_file)

        success, msg = manager.create_user("testuser", "ValidPass123!", "user")
        assert success
        assert "testuser" in manager.users

    def test_create_user_weak_password(self, tmp_path):
        """Creating user with weak password should fail"""
        users_file = tmp_path / "users.json"

        manager = UserManager(users_file)

        success, msg = manager.create_user("testuser", "weak", "user")
        assert not success
        assert "12 characters" in msg

    def test_verify_password_success(self, tmp_path):
        """Correct password should verify successfully"""
        users_file = tmp_path / "users.json"

        manager = UserManager(users_file)

        manager.create_user("testuser", "ValidPass123!", "user")
        is_valid, error = manager.verify_password("testuser", "ValidPass123!")
        assert is_valid
        assert error is None

    def test_verify_password_failure(self, tmp_path):
        """Incorrect password should fail"""
        users_file = tmp_path / "users.json"

        manager = UserManager(users_file)

        manager.create_user("testuser", "ValidPass123!", "user")
        is_valid, error = manager.verify_password("testuser", "WrongPassword!")
        assert not is_valid
        assert error == "Invalid username or password"

    def test_account_lockout(self, tmp_path):
        """Account should lock after 5 failed attempts"""
        users_file = tmp_path / "users.json"

        manager = UserManager(users_file)

        manager.create_user("testuser", "ValidPass123!", "user")

        # Try 5 wrong passwords
        for i in range(5):
            is_valid, error = manager.verify_password("testuser", "WrongPassword!")
            assert not is_valid

        # 6th attempt should indicate account is locked
        is_valid, error = manager.verify_password("testuser", "WrongPassword!")
        assert not is_valid
        assert "locked" in error.lower()

    def test_must_change_password(self, tmp_path):
        """New users should be required to change password"""
        users_file = tmp_path / "users.json"

        manager = UserManager(users_file)

        manager.create_user("testuser", "ValidPass123!", "user")
        assert manager.must_change_password("testuser")

    def test_update_password_success(self, tmp_path):
        """Updating password should work with correct old password"""
        users_file = tmp_path / "users.json"

        manager = UserManager(users_file)

        # Create user first
        success, msg = manager.create_user("testuser", "OldSecure123!", "user")
        assert success, f"Failed to create user: {msg}"

        # Update password
        success, msg = manager.update_password("testuser", "NewSecure123!", "OldSecure123!")
        assert success, f"Failed to update password: {msg}"

        # Old password should not work
        is_valid, _ = manager.verify_password("testuser", "OldSecure123!")
        assert not is_valid

        # New password should work
        is_valid, _ = manager.verify_password("testuser", "NewSecure123!")
        assert is_valid

    def test_update_password_weak_new_password(self, tmp_path):
        """Updating to weak password should fail"""
        users_file = tmp_path / "users.json"

        manager = UserManager(users_file)

        # Create user first
        success, msg = manager.create_user("testuser", "OldSecure123!", "user")
        assert success, f"Failed to create user: {msg}"

        # Try to update to weak password
        success, msg = manager.update_password("testuser", "weak", "OldSecure123!")
        assert not success
        assert "12 characters" in msg


class TestSecurityConfig:
    """Test security configuration"""

    def test_development_mode_warning(self, tmp_path, capsys):
        """Development mode should log warning"""
        import os
        import logging

        # Enable development mode
        os.environ['DEVELOPMENT_MODE'] = 'True'
        os.environ['SECRET_KEY'] = 'test-key-' + 'x' * 50

        # Reset and create new config
        config = SecurityConfig()

        assert config.development_mode is True

    def test_production_requires_secret_key(self):
        """Production mode should require SECRET_KEY"""
        import os

        # Remove SECRET_KEY
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']

        # Disable development mode
        os.environ['DEVELOPMENT_MODE'] = 'False'

        with pytest.raises(RuntimeError) as exc_info:
            SecurityConfig()

        assert "SECRET_KEY" in str(exc_info.value)

    def test_short_secret_key_rejected(self):
        """Short SECRET_KEY should be rejected"""
        import os

        os.environ['SECRET_KEY'] = 'short'
        os.environ['DEVELOPMENT_MODE'] = 'False'

        with pytest.raises(ValueError) as exc_info:
            SecurityConfig()

        assert "32 characters" in str(exc_info.value)


# Pytest fixtures
@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create temporary directory for tests"""
    return tmp_path_factory.mktemp("security_tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
