#!/usr/bin/env python
"""
Claude Insight Server Startup Script
Starts Flask app with SocketIO on port 5000
"""

import os
import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

# Change to project root
os.chdir(project_root)

print(f"[INFO] Starting Claude Insight from: {project_root}")
print(f"[INFO] Server will be available at: http://localhost:5000")
print(f"[INFO] Press Ctrl+C to stop")
print("-" * 60)

# Import and run Flask app
try:
    from app import app, socketio

    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )
except Exception as e:
    print(f"[ERROR] Failed to start server: {e}")
    sys.exit(1)
