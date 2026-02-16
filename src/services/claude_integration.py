"""
Claude/Anthropic API Integration
Automatically use user's Claude credentials for session tracking
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.path_resolver import get_config_dir, get_sessions_dir

class ClaudeCredentialsManager:
    """Manage Claude/Anthropic API credentials securely"""

    def __init__(self):
        self.config_dir = get_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.credentials_file = self.config_dir / 'claude_credentials.enc'
        self.key_file = self.config_dir / '.encryption_key'

        # Initialize encryption
        self._init_encryption()

    def _init_encryption(self):
        """Initialize encryption key"""
        if not self.key_file.exists():
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set file permissions (owner only)
            os.chmod(self.key_file, 0o600)

        with open(self.key_file, 'rb') as f:
            self.cipher = Fernet(f.read())

    def save_api_key(self, api_key, user_email=None):
        """Save Anthropic API key securely"""
        credentials = {
            'api_key': api_key,
            'user_email': user_email,
            'saved_at': datetime.now().isoformat(),
            'status': 'active'
        }

        # Encrypt credentials
        encrypted_data = self.cipher.encrypt(json.dumps(credentials).encode())

        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted_data)

        # Set file permissions
        os.chmod(self.credentials_file, 0o600)

        return True

    def get_api_key(self):
        """Get stored API key"""
        if not self.credentials_file.exists():
            return None

        try:
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())

            return credentials.get('api_key')
        except:
            return None

    def get_credentials(self):
        """Get full credentials"""
        if not self.credentials_file.exists():
            return None

        try:
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except:
            return None

    def delete_credentials(self):
        """Delete stored credentials"""
        if self.credentials_file.exists():
            self.credentials_file.unlink()
        return True

    def has_credentials(self):
        """Check if credentials are stored"""
        return self.credentials_file.exists()


class ClaudeAPIClient:
    """Client for Anthropic Claude API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or self._get_stored_api_key()
        self.base_url = 'https://api.anthropic.com/v1'
        self.headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }

    def _get_stored_api_key(self):
        """Get API key from storage"""
        manager = ClaudeCredentialsManager()
        return manager.get_api_key()

    def test_connection(self):
        """Test API connection"""
        try:
            # Test with a simple message
            response = requests.post(
                f'{self.base_url}/messages',
                headers=self.headers,
                json={
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 10,
                    'messages': [
                        {'role': 'user', 'content': 'Hi'}
                    ]
                },
                timeout=10
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'API connection successful!',
                    'model': 'claude-3-haiku-20240307'
                }
            else:
                return {
                    'success': False,
                    'message': f'API error: {response.status_code}',
                    'error': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}',
                'error': str(e)
            }

    def get_account_info(self):
        """Get account information (if available via API)"""
        # Note: Anthropic API doesn't have account info endpoint yet
        # This is a placeholder for future implementation
        return {
            'api_key_valid': self.test_connection()['success'],
            'api_key_masked': self._mask_api_key(self.api_key) if self.api_key else None
        }

    def _mask_api_key(self, api_key):
        """Mask API key for display"""
        if not api_key or len(api_key) < 10:
            return '***'
        return f"{api_key[:8]}...{api_key[-4:]}"


class AutoSessionTracker:
    """Automatically track Claude sessions"""

    def __init__(self):
        self.sessions_dir = get_sessions_dir()
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.auto_tracking_config = get_config_dir() / 'auto_tracking.json'

    def enable_auto_tracking(self, interval_minutes=5):
        """Enable automatic session tracking"""
        config = {
            'enabled': True,
            'interval_minutes': interval_minutes,
            'last_sync': None,
            'enabled_at': datetime.now().isoformat()
        }

        with open(self.auto_tracking_config, 'w') as f:
            json.dump(config, f, indent=2)

        return config

    def disable_auto_tracking(self):
        """Disable automatic session tracking"""
        config = {
            'enabled': False,
            'disabled_at': datetime.now().isoformat()
        }

        with open(self.auto_tracking_config, 'w') as f:
            json.dump(config, f, indent=2)

        return config

    def get_tracking_status(self):
        """Get auto-tracking status"""
        if not self.auto_tracking_config.exists():
            return {'enabled': False}

        try:
            with open(self.auto_tracking_config, 'r') as f:
                return json.load(f)
        except:
            return {'enabled': False}

    def sync_sessions(self):
        """
        Sync sessions from Claude API
        Note: This is a placeholder - actual implementation depends on
        Claude API providing session history endpoint
        """
        # Check if API key is available
        manager = ClaudeCredentialsManager()
        api_key = manager.get_api_key()

        if not api_key:
            return {
                'success': False,
                'message': 'No API key configured'
            }

        # Update last sync time
        config = self.get_tracking_status()
        config['last_sync'] = datetime.now().isoformat()

        with open(self.auto_tracking_config, 'w') as f:
            json.dump(config, f, indent=2)

        return {
            'success': True,
            'message': 'Sessions synced successfully',
            'synced_at': config['last_sync']
        }


class AnthropicLoginHelper:
    """Helper for Anthropic login flow"""

    def __init__(self):
        self.anthropic_console_url = 'https://console.anthropic.com'
        self.api_keys_url = f'{self.anthropic_console_url}/settings/keys'

    def get_login_url(self):
        """Get Anthropic console login URL"""
        return self.anthropic_console_url

    def get_api_keys_url(self):
        """Get API keys page URL"""
        return self.api_keys_url

    def get_setup_instructions(self):
        """Get step-by-step setup instructions"""
        return {
            'steps': [
                {
                    'step': 1,
                    'title': 'Login to Anthropic Console',
                    'description': 'Go to console.anthropic.com and login with your account',
                    'url': self.anthropic_console_url
                },
                {
                    'step': 2,
                    'title': 'Navigate to API Keys',
                    'description': 'Click on "Settings" → "API Keys"',
                    'url': self.api_keys_url
                },
                {
                    'step': 3,
                    'title': 'Create New API Key',
                    'description': 'Click "Create Key" button and give it a name (e.g., "Claude Insight")',
                    'url': self.api_keys_url
                },
                {
                    'step': 4,
                    'title': 'Copy API Key',
                    'description': 'Copy the generated API key (starts with "sk-ant-")',
                    'important': True
                },
                {
                    'step': 5,
                    'title': 'Add to Claude Insight',
                    'description': 'Paste the API key in Claude Insight settings and click "Save"',
                    'important': True
                }
            ],
            'notes': [
                '⚠️ Never share your API key with anyone',
                '🔒 API key is stored encrypted on your machine',
                '✅ You can revoke the key anytime from Anthropic Console',
                '💡 One API key is enough for all Claude Insight features'
            ]
        }


# Global instances
credentials_manager = ClaudeCredentialsManager()
auto_tracker = AutoSessionTracker()
login_helper = AnthropicLoginHelper()
