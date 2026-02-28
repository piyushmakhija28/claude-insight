"""
Configuration module — security + app settings
"""
import os
from pathlib import Path

from .security import (
    SecurityConfig,
    PasswordValidator,
    PathValidator,
    FilenameValidator,
    CommandValidator,
    LogSanitizer,
    SecurityError
)

# ── App Configuration (previously in standalone config.py) ──────────────────

BASE_DIR = Path(__file__).parent.parent.parent

# Data directory resolution (where dashboard stores its data)
# Priority: env var > ~/.claude/memory (legacy) > ./data (portable)
_data_dir_override = os.environ.get('CLAUDE_INSIGHT_DATA_DIR')
if _data_dir_override:
    MEMORY_SYSTEM_DIR = Path(_data_dir_override)
elif (Path.home() / '.claude' / 'memory').exists():
    MEMORY_SYSTEM_DIR = Path.home() / '.claude' / 'memory'
else:
    MEMORY_SYSTEM_DIR = BASE_DIR / 'data'


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    MEMORY_DIR = MEMORY_SYSTEM_DIR
    LOGS_DIR = MEMORY_DIR / 'logs'
    SESSIONS_DIR = MEMORY_DIR / 'sessions'
    DOCS_DIR = MEMORY_DIR / 'docs'

    MEMORY_FILES_DIR = BASE_DIR / 'memory_files'

    METRICS_RETENTION_DAYS = 30
    LOG_RETENTION_DAYS = 90
    SESSION_RETENTION_DAYS = 180

    CONTEXT_WARNING_THRESHOLD = 70
    CONTEXT_CRITICAL_THRESHOLD = 85
    CONTEXT_DANGER_THRESHOLD = 90

    TRENDING_WINDOW_HOURS = 24
    FEATURED_WIDGET_COUNT = 10

    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_LOGGER = False
    SOCKETIO_ENGINEIO_LOGGER = False

    NOTIFICATION_BATCH_SIZE = 50
    NOTIFICATION_RETRY_ATTEMPTS = 3

    ANOMALY_DETECTION_ENABLED = True
    PREDICTIVE_ANALYTICS_ENABLED = True
    MODEL_UPDATE_INTERVAL_HOURS = 6

    DEBUG = False
    TESTING = False

    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        os.makedirs(Config.MEMORY_FILES_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        os.makedirs(Config.SESSIONS_DIR, exist_ok=True)
        os.makedirs(Config.DOCS_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY')


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True


_config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return _config_map.get(env, _config_map['default'])


__all__ = [
    'SecurityConfig',
    'PasswordValidator',
    'PathValidator',
    'FilenameValidator',
    'CommandValidator',
    'LogSanitizer',
    'SecurityError',
    'Config',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestingConfig',
    'get_config',
    'MEMORY_SYSTEM_DIR',
    'BASE_DIR',
]
