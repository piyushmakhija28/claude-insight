# Claude Insight - Security Hardening Guide

**Version:** 1.0
**Date:** 2026-02-16
**Status:** Production Ready After Implementation

---

## Table of Contents

1. [Critical Security Fixes Implemented](#critical-security-fixes-implemented)
2. [Installation & Setup](#installation--setup)
3. [Configuration](#configuration)
4. [Security Features](#security-features)
5. [Testing Security](#testing-security)
6. [Production Deployment](#production-deployment)
7. [Security Checklist](#security-checklist)
8. [Incident Response](#incident-response)

---

## Critical Security Fixes Implemented

### ✅ CRITICAL Issues Fixed

| Issue | Status | Location | Solution |
|-------|--------|----------|----------|
| Hardcoded Secret Key | ✅ FIXED | `src/config/security.py` | Environment variable with validation |
| Hardcoded Admin Password | ✅ FIXED | `src/auth/user_manager.py` | Secure user management system |
| No CSRF Protection | ✅ FIXED | `src/app_secure.py` | Flask-WTF CSRF protection |
| Command Injection | ✅ FIXED | `src/config/security.py` | Command whitelist validation |
| Path Traversal | ✅ FIXED | `src/config/security.py` | Path validation utilities |
| No Rate Limiting | ✅ FIXED | `src/app_secure.py` | Flask-Limiter on all routes |
| Weak Password Policy | ✅ FIXED | `src/config/security.py` | Password strength validation |
| Session Fixation | ✅ FIXED | `src/app_secure.py` | Session regeneration on login |
| No Security Headers | ✅ FIXED | `src/app_secure.py` | Flask-Talisman + custom headers |
| Account Lockout Missing | ✅ FIXED | `src/auth/user_manager.py` | Lockout after 5 failed attempts |

---

## Installation & Setup

### 1. Install Security Dependencies

```bash
# Backup existing requirements
cp requirements.txt requirements-old.txt

# Install security-hardened requirements
pip install -r requirements-secure.txt
```

### 2. Create Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Generate secure secret key
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" >> .env

# Edit .env and set secure values
nano .env  # or your preferred editor
```

### 3. Create Initial Admin User

**Option A: Set in Environment Variable**

```bash
# Add to .env
ADMIN_PASSWORD=YourSecurePasswordHere123!@#
```

**Option B: Interactive Setup (First Run)**

The system will prompt for admin password on first run if not set in environment.

### 4. File Structure

Ensure these new files exist:

```
claude-insight/
├── .env.example              # Template environment config
├── .env                      # YOUR actual config (git-ignored)
├── requirements-secure.txt   # Security-hardened dependencies
├── SECURITY_HARDENING_GUIDE.md  # This file
├── src/
│   ├── app_secure.py         # Secure version of app.py
│   ├── config/
│   │   └── security.py       # Security configuration & utilities
│   └── auth/
│       └── user_manager.py   # User management system
└── data/
    └── users.json            # User database (auto-created)
```

---

## Configuration

### Environment Variables Reference

#### CRITICAL Security Settings

```bash
# REQUIRED: Secret key for sessions/CSRF
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-64-character-hex-string-here

# REQUIRED: Initial admin password
# Must meet complexity requirements
ADMIN_PASSWORD=YourSecurePassword123!@#
```

#### Optional Security Settings

```bash
# Session timeout (minutes)
SESSION_TIMEOUT=30

# Session cookie security
SESSION_COOKIE_SECURE=True        # Require HTTPS
SESSION_COOKIE_HTTPONLY=True      # Prevent JavaScript access
SESSION_COOKIE_SAMESITE=Lax       # CSRF protection

# CSRF protection
CSRF_ENABLED=True
CSRF_TIME_LIMIT=3600              # 1 hour

# Rate limiting
RATELIMIT_LOGIN=5 per minute      # Login attempts
RATELIMIT_API=100 per hour        # API calls
RATELIMIT_DEFAULT=200 per day;50 per hour

# Force HTTPS (disable for local dev only)
FORCE_HTTPS=True

# Development mode (NEVER enable in production!)
DEVELOPMENT_MODE=False
```

#### Application Settings

```bash
# Flask configuration
FLASK_ENV=production              # NEVER use 'development' in production
FLASK_DEBUG=False                 # NEVER enable debug in production
FLASK_PORT=5000

# Logging
LOG_LEVEL=INFO                    # DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_TO_FILE=True
LOG_FILE_PATH=logs/app.log
LOG_MAX_BYTES=10485760            # 10MB
LOG_BACKUP_COUNT=5                # Keep 5 backup logs
```

#### External Services (Optional)

```bash
# SMTP (for email alerts)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=alerts@yourdomain.com

# Twilio (for SMS alerts)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
```

---

## Security Features

### 1. CSRF Protection

**Implementation:** Flask-WTF

**How it works:**
- CSRF tokens automatically added to all forms
- All state-changing requests (POST/PUT/DELETE) require valid token
- Tokens expire after 1 hour (configurable)

**Exempt API endpoints** (if using API keys):

```python
from flask_wtf.csrf import csrf

@app.route('/api/external-webhook', methods=['POST'])
@csrf.exempt  # Only if API key authentication is used instead
def webhook():
    # Verify API key here
    pass
```

### 2. Rate Limiting

**Implementation:** Flask-Limiter

**Default limits:**
- **Login:** 5 attempts per minute per IP
- **API endpoints:** 100 requests per hour per IP
- **Global:** 200 requests per day, 50 per hour per IP

**Custom limits** for specific routes:

```python
@app.route('/api/expensive-operation')
@limiter.limit("10 per hour")
def expensive():
    pass
```

**Bypass rate limits** (for testing only):

```python
# In .env
RATELIMIT_ENABLED=False  # NEVER in production!
```

### 3. Password Security

**Password Requirements:**
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*(),.?":{}|<>)
- Not in common password list

**Password Storage:**
- Bcrypt hashing with automatic salt
- Cost factor: 12 (default)
- Passwords NEVER stored in plain text

**Account Lockout:**
- Max 5 failed login attempts
- Lockout duration: 15 minutes
- Counter resets on successful login

### 4. Session Security

**Session Configuration:**
- Regenerated on login (prevents fixation)
- Expires on browser close (non-permanent)
- Timeout after 30 minutes of inactivity
- Secure, HttpOnly, SameSite cookies

**Session Data:**
- Minimal data stored in session
- Sensitive data never stored in session
- User role validated on each request

### 5. Path Traversal Protection

**PathValidator class** validates all file paths:

```python
from config.security import PathValidator

logs_dir = Path('/var/app/logs')
validator = PathValidator(logs_dir)

# This is safe
safe_path = validator.validate(logs_dir / 'app.log')

# This raises SecurityError
try:
    unsafe_path = validator.validate(Path('/etc/passwd'))
except SecurityError:
    # Path is outside allowed directory
    pass
```

**Filename sanitization:**

```python
from config.security import FilenameValidator

# User input: "../../etc/passwd"
safe = FilenameValidator.sanitize("../../etc/passwd")
# Result: "____etc_passwd"
```

### 6. Command Injection Protection

**CommandValidator class** whitelists allowed scripts:

```python
from config.security import CommandValidator

allowed_dir = Path('/app/scripts')

# This is safe (script on whitelist)
safe_script = CommandValidator.validate_script_path(
    allowed_dir / 'pid-tracker.py',
    allowed_dir
)

# This raises SecurityError (not on whitelist)
try:
    unsafe = CommandValidator.validate_script_path(
        allowed_dir / 'malicious.py',
        allowed_dir
    )
except SecurityError:
    pass
```

**Adding scripts to whitelist:**

Edit `src/config/security.py`:

```python
ALLOWED_SCRIPTS = {
    'pid-tracker.py',
    'context-monitor.py',
    'your-new-script.py',  # Add here
}
```

### 7. Security Headers

**Flask-Talisman** adds:
- HTTPS enforcement
- Strict-Transport-Security (HSTS)
- Content-Security-Policy (CSP)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block

**Custom headers** in `@app.after_request`:
- Cache-Control for static/API resources
- Additional security headers

### 8. Log Sanitization

**LogSanitizer class** removes sensitive data from logs:

```python
from config.security import LogSanitizer

# Original log message
message = "User email: user@example.com, API Key: abc123def456"

# Sanitized
safe = LogSanitizer.sanitize(message)
# Result: "User email: [EMAIL_REDACTED], API Key: [API_KEY_REDACTED]"
```

**Automatic sanitization** for all logs:

```python
import logging
from config.security import LogSanitizer

logger = logging.getLogger(__name__)

# Create custom formatter
class SanitizingFormatter(logging.Formatter):
    def format(self, record):
        record.msg = LogSanitizer.sanitize(str(record.msg))
        return super().format(record)

# Apply to handlers
handler = logging.StreamHandler()
handler.setFormatter(SanitizingFormatter())
logger.addHandler(handler)
```

---

## Testing Security

### 1. Security Scan

```bash
# Install security tools
pip install bandit safety

# Scan for security vulnerabilities in code
bandit -r src/ -f json -o security-scan.json

# Check dependencies for known vulnerabilities
safety check --json
```

### 2. Test CSRF Protection

```bash
# This should FAIL (no CSRF token)
curl -X POST http://localhost:5000/api/some-endpoint \
  -H "Content-Type: application/json" \
  -d '{"data":"value"}'

# Response: 400 Bad Request - CSRF token missing
```

### 3. Test Rate Limiting

```bash
# Try 6 login attempts rapidly (should block after 5)
for i in {1..6}; do
  curl -X POST http://localhost:5000/login \
    -d "username=test&password=wrong"
  echo "Attempt $i"
done

# Expected: First 5 attempts get 401, 6th gets 429 (Rate Limited)
```

### 4. Test Path Traversal Prevention

```bash
# Try to access file outside allowed directory
curl http://localhost:5000/api/logs/..%2F..%2Fetc%2Fpasswd

# Expected: 403 Forbidden or 404 Not Found
```

### 5. Test Account Lockout

```python
# Test script
from auth.user_manager import UserManager

manager = UserManager()

# Create test user
manager.create_user('testuser', 'SecurePassword123!', 'user')

# Try 6 wrong passwords
for i in range(6):
    valid, msg = manager.verify_password('testuser', 'wrong')
    print(f"Attempt {i+1}: {valid}, {msg}")

# Expected: First 5 return "Invalid", 6th returns "Account locked"
```

### 6. Test Password Strength

```python
from config.security import PasswordValidator

# Weak passwords (should FAIL)
weak_passwords = [
    'short',                    # Too short
    'NoNumbersHere!',          # No numbers
    'nonumbersorspecial123',   # No uppercase or special
    'password123',             # Common password
]

for pwd in weak_passwords:
    valid, msg = PasswordValidator.validate(pwd)
    print(f"{pwd}: {valid}, {msg}")

# Strong password (should PASS)
valid, msg = PasswordValidator.validate('MySecure123!Password')
print(f"Strong: {valid}")
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All environment variables set in `.env`
- [ ] `SECRET_KEY` is 64+ character random hex
- [ ] `ADMIN_PASSWORD` meets complexity requirements
- [ ] `FLASK_DEBUG=False`
- [ ] `FLASK_ENV=production`
- [ ] `DEVELOPMENT_MODE=False`
- [ ] `FORCE_HTTPS=True`
- [ ] SSL/TLS certificate installed
- [ ] `.env` file is git-ignored
- [ ] Security scan passed (bandit)
- [ ] Dependency vulnerabilities checked (safety)
- [ ] All tests passed
- [ ] Firewall configured
- [ ] Backup strategy in place

### Deployment Steps

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3-pip python3-venv nginx

# Create application user
sudo useradd -m -s /bin/bash claudeapp
sudo su - claudeapp
```

#### 2. Application Setup

```bash
# Clone repository
git clone https://github.com/yourusername/claude-insight.git
cd claude-insight

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-secure.txt

# Create .env file
cp .env.example .env
nano .env  # Edit with production values
```

#### 3. Generate Secrets

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')"

# Add to .env
echo "SECRET_KEY=<generated-key>" >> .env

# Set admin password
echo "ADMIN_PASSWORD=<your-secure-password>" >> .env
```

#### 4. SSL Certificate

```bash
# Using Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com
```

#### 5. Nginx Configuration

```nginx
# /etc/nginx/sites-available/claude-insight

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /home/claudeapp/claude-insight/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/claude-insight /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 6. Systemd Service

```ini
# /etc/systemd/system/claude-insight.service

[Unit]
Description=Claude Insight Dashboard
After=network.target

[Service]
Type=simple
User=claudeapp
WorkingDirectory=/home/claudeapp/claude-insight
Environment="PATH=/home/claudeapp/claude-insight/venv/bin"
ExecStart=/home/claudeapp/claude-insight/venv/bin/python src/app_secure.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable claude-insight
sudo systemctl start claude-insight

# Check status
sudo systemctl status claude-insight
```

#### 7. Firewall

```bash
# UFW firewall
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

#### 8. Monitoring

```bash
# View logs
sudo journalctl -u claude-insight -f

# Log rotation
sudo nano /etc/logrotate.d/claude-insight
```

```
/home/claudeapp/claude-insight/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 claudeapp claudeapp
}
```

---

## Security Checklist

### Daily

- [ ] Review failed login attempts
- [ ] Check for rate limit violations
- [ ] Monitor error logs for security issues
- [ ] Verify all services running

### Weekly

- [ ] Review access logs
- [ ] Check for unusual activity patterns
- [ ] Update dependencies if patches available
- [ ] Test backup restoration

### Monthly

- [ ] Full security scan (bandit)
- [ ] Dependency vulnerability scan (safety)
- [ ] Review user accounts (disable inactive)
- [ ] Update SSL certificates (if needed)
- [ ] Penetration testing
- [ ] Review and update security policies

### Quarterly

- [ ] Full security audit
- [ ] Update dependencies to latest stable
- [ ] Review and test incident response plan
- [ ] Security training for team
- [ ] Third-party security assessment

---

## Incident Response

### Security Incident Detected

#### 1. Immediate Actions

```bash
# Stop the application
sudo systemctl stop claude-insight

# Block suspicious IPs
sudo ufw deny from <IP_ADDRESS>

# Preserve evidence
sudo cp -r /home/claudeapp/claude-insight/logs /backup/incident-$(date +%Y%m%d)
```

#### 2. Investigation

```bash
# Check failed logins
grep "Failed login" logs/app.log | tail -100

# Check rate limit violations
grep "Rate limit exceeded" logs/app.log

# Check for path traversal attempts
grep "SecurityError" logs/app.log

# Check unusual file access
sudo find /home/claudeapp/claude-insight -mtime -1 -ls
```

#### 3. Remediation

```bash
# Reset all user passwords
# Rotate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Update .env with new key
nano .env

# Clear all sessions
rm -f data/sessions/*

# Restart application
sudo systemctl start claude-insight
```

#### 4. Post-Incident

- Document incident details
- Update security measures
- Notify affected users (if applicable)
- Review and update incident response plan
- Implement additional monitoring

### Breach Response

If credentials or data are compromised:

1. **Immediate:** Stop all services
2. **Notify:** Inform all users immediately
3. **Reset:** Force password reset for all users
4. **Audit:** Full system audit
5. **Report:** Report to relevant authorities if required
6. **Update:** Patch vulnerabilities
7. **Monitor:** Enhanced monitoring for 30 days

---

## Support & Questions

For security issues:
- **DO NOT** create public GitHub issues for security vulnerabilities
- Email: security@yourdomain.com
- Include: Description, steps to reproduce, impact assessment

---

**Document Version:** 1.0
**Last Updated:** 2026-02-16
**Next Review:** 2026-05-16
