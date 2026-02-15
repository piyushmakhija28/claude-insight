"""
Claude Monitoring System - Application Entry Point

This is the main entry point for running the Flask application.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.app import app, socketio
from src.config import get_config

if __name__ == '__main__':
    # Get configuration
    config = get_config()

    # Initialize app with config
    config.init_app(app)

    # Run application
    print("Starting Claude Monitoring System...")
    print(f"Environment: {config.__class__.__name__}")
    print(f"Debug mode: {config.DEBUG}")

    socketio.run(
        app,
        debug=config.DEBUG,
        host='0.0.0.0',
        port=5000,
        allow_unsafe_werkzeug=True  # For development only
    )
