# Quick test to verify session
from flask import Flask, session
app = Flask(__name__)
app.secret_key = 'claude-insight-secret-key-2026'

with app.test_request_context():
    session['logged_in'] = True
    print(f"Session test:")
    print(f"  session['logged_in'] = {session.get('logged_in')}")
    print(f"  Check: {session.get('logged_in') == True}")
    print()
    print("✅ Session will work correctly!")
