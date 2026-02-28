"""Configuration Management for Claude Insight"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data directory resolution (where dashboard stores its data)
# Priority: env var > ~/.claude/memory (legacy) > ./data (portable)
_data_dir_override = os.environ.get('CLAUDE_INSIGHT_DATA_DIR')
if _data_dir_override:
    MEMORY_SYSTEM_DIR = Path(_data_dir_override)
elif (Path.home() / '.claude' / 'memory').exists():
    MEMORY_SYSTEM_DIR = Path.home() / '.claude' / 'memory'
else:
    MEMORY_SYSTEM_DIR = BASE_DIR / 'data'

# Flask Configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Memory System Paths (MEMORY_SYSTEM_DIR is already the data root — no double nesting)
    MEMORY_DIR = MEMORY_SYSTEM_DIR
    LOGS_DIR = MEMORY_DIR / 'logs'
    SESSIONS_DIR = MEMORY_DIR / 'sessions'
    DOCS_DIR = MEMORY_DIR / 'docs'

    # File Storage
    MEMORY_FILES_DIR = BASE_DIR / 'memory_files'

    # Monitoring Settings
    METRICS_RETENTION_DAYS = 30
    LOG_RETENTION_DAYS = 90
    SESSION_RETENTION_DAYS = 180

    # Alert Thresholds
    CONTEXT_WARNING_THRESHOLD = 70
    CONTEXT_CRITICAL_THRESHOLD = 85
    CONTEXT_DANGER_THRESHOLD = 90

    # Widget Settings
    TRENDING_WINDOW_HOURS = 24
    FEATURED_WIDGET_COUNT = 10

    # WebSocket Settings
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_LOGGER = False
    SOCKETIO_ENGINEIO_LOGGER = False

    # Notification Settings
    NOTIFICATION_BATCH_SIZE = 50
    NOTIFICATION_RETRY_ATTEMPTS = 3

    # AI/ML Settings
    ANOMALY_DETECTION_ENABLED = True
    PREDICTIVE_ANALYTICS_ENABLED = True
    MODEL_UPDATE_INTERVAL_HOURS = 6

    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        os.makedirs(Config.MEMORY_FILES_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        os.makedirs(Config.SESSIONS_DIR, exist_ok=True)
        os.makedirs(Config.DOCS_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
