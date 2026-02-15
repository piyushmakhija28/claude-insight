# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Claude Monitoring System v2.13** - A professional real-time analytics dashboard for monitoring the Claude Memory System v2.2.0. This Flask-based web application provides complete visibility into daemon health, policy enforcement, token consumption, anomaly detection, and performance optimization.

**Key Capabilities:**
- Real-time monitoring of 8-9 background daemons
- AI-powered anomaly detection and predictive analytics
- Custom alert routing with multi-level escalation
- Widget collaboration with real-time editing
- Community marketplace for sharing custom widgets

---

## Development Commands

### Running the Application

```bash
# Start the development server
python app.py

# Access dashboard at http://localhost:5000
# Default credentials: admin/admin
```

### Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# Required packages (14 total):
# - Flask 3.0 + Flask-SocketIO 5.3.6
# - psutil 5.9.8 (process monitoring)
# - NumPy 1.24.3 (statistical analysis)
# - Twilio 8.10.0 (SMS notifications)
# - bcrypt, openpyxl, reportlab, flasgger, etc.
```

### Deploy Memory System Files (Optional)

```bash
# Windows
xcopy /E /I /Y claude-memory-system\* %USERPROFILE%\.claude\memory\

# Linux/Mac
cp -r claude-memory-system/* ~/.claude/memory/

# Start daemons (Windows)
powershell -ExecutionPolicy Bypass -File ~/.claude/memory/setup-windows-startup.ps1

# Start daemons (Linux/Mac)
bash ~/.claude/memory/startup-hook.sh
```

---

## Architecture Overview

### Flask Application Structure

```
app.py (3,500+ lines)
├── Authentication system (bcrypt-based)
├── SocketIO for real-time updates
├── Swagger API documentation
├── 17 utility managers/collectors
└── 100+ routes (HTML + API + WebSocket)
```

### Core Components (utils/)

**Monitoring & Analytics:**
- `metrics.py` - MetricsCollector for daemon/policy/token tracking
- `log_parser.py` - Parse Memory System logs
- `policy_checker.py` - Validate policy compliance
- `session_tracker.py` - Track active sessions
- `history_tracker.py` - Historical data analysis
- `memory_system_monitor.py` - Complete Memory System integration

**AI & Intelligence:**
- `anomaly_detector.py` - ML-based anomaly detection (Isolation Forest)
- `predictive_analytics.py` - Forecasting with 5 algorithms (ARIMA, Prophet, etc.)
- `alert_routing.py` - Smart alert routing with escalation rules

**Community & Collaboration:**
- `community_widgets.py` - Widget marketplace manager
- `widget_version_manager.py` - Semantic versioning for widgets
- `widget_comments_manager.py` - Threaded discussions with @mentions
- `collaboration_manager.py` - Real-time multi-user editing
- `trending_calculator.py` - Algorithm-based widget ranking

**Notifications:**
- `notification_manager.py` - In-app notifications
- `alert_sender.py` - Email/SMS via Twilio

### Template Structure

```
templates/
├── base.html                      # Base layout with navigation
├── login.html                     # Authentication
├── dashboard.html                 # Main monitoring dashboard
├── policies.html                  # Policy compliance tracking
├── sessions.html                  # Session management
├── logs.html                      # Log viewer
├── analytics.html                 # Historical analytics
├── comparison.html                # Cross-session comparison
├── notifications.html             # Notification center
├── anomaly-detection.html         # AI anomaly detection
├── predictive-analytics.html      # Forecasting dashboard
├── alert-routing.html             # Alert configuration
├── community-marketplace.html     # Widget sharing
├── widget-builder.html            # Collaborative widget editor
├── settings.html                  # User preferences
├── 404.html / 500.html           # Error pages
```

### WebSocket Events (SocketIO)

**Real-time Updates:**
- `context_update` - Token usage changes
- `daemon_update` - Daemon status changes
- `policy_update` - Policy violations
- `alert_triggered` - New alerts
- `anomaly_detected` - Anomaly events
- `forecast_ready` - Prediction updates

**Widget Collaboration:**
- `collaboration:join` / `leave` - Session management
- `collaboration:cursor_move` - Live cursor tracking
- `collaboration:edit` - Synchronized edits
- `collaboration:lock_request` - Line locking
- `collaboration:chat` - Built-in messaging

---

## Claude Memory System Integration

The `claude-memory-system/` folder contains 139 files for the Memory System v2.2.0:

### Key Documentation

**Read `claude-memory-system/MASTER-README.md`** for complete guidance including:
- All 12 active policies (Core Skills, Model Selection, Failure Prevention, etc.)
- Java Spring Boot standards (package structure, mandatory patterns)
- Spring Boot configuration (Config Server, Secret Management)
- Token optimization strategies (15 techniques, 60-80% savings)
- Security best practices and database standards

### 8-9 Daemons Monitored

This dashboard monitors these background processes:
1. `context-daemon.py` - Monitor context usage (every 10 min)
2. `session-auto-save-daemon.py` - Auto-save sessions (every 15 min)
3. `preference-auto-tracker.py` - Learn preferences (every 20 min)
4. `skill-auto-suggester.py` - Suggest skills (every 5 min)
5. `commit-daemon.py` - Auto-commit changes (on triggers)
6. `session-pruning-daemon.py` - Clean old sessions (monthly)
7. `pattern-detection-daemon.py` - Detect patterns (monthly)
8. `failure-prevention-daemon.py` - Learn from failures (every 6 hours)
9. `token-optimization-daemon.py` - Continuous optimization (optional)

### Integration Points

The dashboard reads from these Memory System locations:
- `~/.claude/memory/logs/` - Daemon logs, policy hits, failures
- `~/.claude/memory/sessions/` - Active session data
- `~/.claude/memory/.state/` - Failure KB, preferences, patterns
- `~/.claude/memory/.pids/` - Daemon PID files

---

## Data Flow & State Management

### Metrics Collection

```python
# MetricsCollector reads from:
# 1. ~/.claude/memory/logs/policy-hits.log
# 2. ~/.claude/memory/.state/failure-kb.json
# 3. ~/.claude/memory/sessions/**/*.md
# 4. ~/.claude/memory/.pids/*.pid

# Real-time updates via SocketIO every 10-30 seconds
```

### Alert Routing Engine

```python
# AlertRoutingEngine supports:
# - Priority-based routing (low/medium/high/critical)
# - Multi-channel delivery (email, SMS, in-app, webhook)
# - Time-based rules (business hours, timezone-aware)
# - Escalation policies (retry intervals, backup contacts)
# - Filter criteria (daemon types, severity, keywords)
```

### Anomaly Detection

```python
# AnomalyDetector uses:
# - Isolation Forest for pattern detection
# - Statistical analysis (Z-score, IQR)
# - Historical baseline comparison
# - Configurable sensitivity (low/medium/high)
```

### Predictive Analytics

```python
# PredictiveAnalytics includes 5 algorithms:
# 1. Linear Regression (baseline trends)
# 2. ARIMA (time series forecasting)
# 3. Prophet (seasonal patterns)
# 4. Exponential Smoothing (weighted averages)
# 5. Moving Average (simple trends)
```

---

## API Endpoints

### Authentication
- `POST /login` - User login
- `GET /logout` - User logout
- `POST /api/change-password` - Update password

### Monitoring
- `GET /` - Main dashboard
- `GET /policies` - Policy compliance
- `GET /sessions` - Session tracker
- `GET /logs` - Log viewer
- `GET /analytics` - Historical analytics

### Data Export
- `GET /export/sessions` - Export sessions to CSV
- `GET /export/metrics` - Export metrics to CSV
- `GET /export/logs` - Export logs to CSV

### AI Features
- `GET /anomaly-detection` - Anomaly dashboard
- `POST /api/anomaly/detect` - Run detection
- `GET /predictive-analytics` - Forecasting dashboard
- `POST /api/forecast/generate` - Generate predictions

### Alert Management
- `GET /alert-routing` - Alert configuration
- `POST /api/alerts/routes` - Create routing rule
- `PUT /api/alerts/routes/<id>` - Update rule
- `DELETE /api/alerts/routes/<id>` - Delete rule

### Widget Marketplace (v2.13)
- `GET /community-marketplace` - Browse widgets
- `GET /api/widgets` - List all widgets
- `POST /api/widgets` - Create widget
- `GET /api/widgets/<id>` - Get widget details
- `PUT /api/widgets/<id>` - Update widget
- `DELETE /api/widgets/<id>` - Delete widget

### Widget Versioning
- `GET /api/widgets/<id>/versions` - Version history
- `POST /api/widgets/<id>/versions` - Create version
- `GET /api/widgets/<id>/versions/<version>` - Get specific version
- `POST /api/widgets/<id>/rollback/<version>` - Rollback to version

### Widget Comments
- `GET /api/widgets/<id>/comments` - Get comments
- `POST /api/widgets/<id>/comments` - Add comment
- `POST /api/widgets/<id>/comments/<cid>/reply` - Reply to comment
- `PUT /api/widgets/<id>/comments/<cid>` - Edit comment
- `DELETE /api/widgets/<id>/comments/<cid>` - Delete comment
- `POST /api/widgets/<id>/comments/<cid>/react` - Add reaction

### Collaboration
- `POST /api/widgets/<id>/collaborate/join` - Join session
- `POST /api/widgets/<id>/collaborate/leave` - Leave session
- `GET /api/widgets/<id>/collaborate/participants` - Active users

### Trending & Featured
- `GET /api/widgets/trending` - Trending widgets (24h/7d/30d)
- `GET /api/widgets/featured` - Featured carousel
- `POST /api/widgets/<id>/download` - Increment download count

---

## Important Development Notes

### Authentication Flow

```python
# app.py uses session-based auth with bcrypt
# Default user: admin/admin
# User data stored in USERS dict (in-memory)
# Decorate protected routes with @login_required

@login_required
def protected_route():
    username = session.get('username')
    # Route logic
```

### Real-Time Updates

```python
# Background thread broadcasts updates every 10-30 seconds
# Start with: threading.Thread(target=broadcast_updates, daemon=True).start()
# Clients receive via SocketIO: socket.on('context_update', callback)
```

### Widget Collaboration Sessions

```python
# CollaborationSessionManager tracks:
# - Active participants (username, color, cursor position)
# - Line locks (automatic 5-minute timeout)
# - Operation history (edits, saves, commits)
# - Session lifecycle (2-hour auto-cleanup)

# WebSocket events:
# - join/leave: User presence
# - cursor_move: Live cursor tracking
# - edit: Synchronized code changes
# - lock_request: Prevent conflicts
# - chat: Built-in messaging
```

### Trending Algorithm

```python
# TrendingCalculator scoring:
# - 40% Downloads (usage metric)
# - 30% Ratings (quality metric)
# - 20% Comments (engagement metric)
# - 10% Recency (time decay, exponential)

# Cached for 60 minutes for performance
# Supports multiple time periods: 24h, 7d, 30d
```

---

## Configuration

### Application Settings (app.py)

```python
app.secret_key = 'claude-monitoring-system-secret-key-2026'
# Change in production!

# SocketIO config
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Swagger API docs available at: /api/docs
```

### User Preferences (settings.html)

Users can configure:
- Auto-refresh intervals (10s - 300s)
- Theme (6 themes: Light, Dark, etc.)
- Default dashboard page
- Display density (comfortable/compact)
- Data retention periods
- Export formats (CSV/JSON/Excel/PDF)
- Debug mode toggle

---

## Memory System Integration Points

### Reading Daemon Status

```python
# Check PID files in ~/.claude/memory/.pids/
# Parse logs from ~/.claude/memory/logs/daemons/
# Memory System Monitor utility handles this automatically
```

### Policy Compliance Tracking

```python
# Read ~/.claude/memory/logs/policy-hits.log
# Format: [timestamp] policy_name | action | context
# PolicyChecker parses and validates against 12 policies
```

### Session Memory Access

```python
# Read from ~/.claude/memory/sessions/<project>/
# Files: project-summary.md, session-*.md
# SessionTracker provides aggregated view
```

### Failure Prevention KB

```python
# Read ~/.claude/memory/.state/failure-kb.json
# Contains learned failure patterns with confidence scores
# Used for anomaly detection and predictive analytics
```

---

## Version History Context

**v2.13 (Feb 2026):** Widget Collaboration Edition
- Real-time multi-user widget editing
- Version control with semantic versioning
- Threaded comments with @mentions
- Featured & trending widgets

**v2.12 (Feb 2026):** Memory System Integration
- Complete Memory System v2.2.0 integration
- All 12 policies explained
- Java Spring Boot standards documented

**v2.11 (Feb 2026):** Alert Routing Edition
- Custom alert routing engine
- Multi-level escalation policies
- Time-based and filter-based rules

**v2.10 (Feb 2026):** Forecasting Edition
- 5 predictive algorithms
- Context/token forecasting
- Capacity planning insights

**v2.9 (Feb 2026):** AI Detection Edition
- ML-based anomaly detection
- Statistical analysis
- Pattern recognition

---

## When Working on This Codebase

### Adding New Monitoring Features

1. Create utility class in `utils/` (e.g., `new_monitor.py`)
2. Initialize in `app.py`: `new_monitor = NewMonitor()`
3. Add route handler with `@login_required` decorator
4. Create template in `templates/`
5. Add navigation link in `base.html`
6. Implement SocketIO events if real-time updates needed

### Extending Widget Collaboration

1. Widget data stored in `~/.claude/memory/community/widgets.json`
2. Version history in `~/.claude/memory/community/versions/`
3. Comments in `~/.claude/memory/community/comments/`
4. Collaboration sessions managed in-memory (not persisted)

### API Documentation

- All API endpoints auto-documented via Swagger/Flasgger
- Access at `/api/docs` when app is running
- Use `@swag_from()` decorator for YAML/JSON specs

### Security Considerations

- All passwords hashed with bcrypt
- Session-based authentication
- XSS protection (Jinja2 auto-escaping)
- Input sanitization for widget content
- CORS configured for SocketIO
- Rate limiting should be added for production

---

## Claude Memory System Policies

When working with Memory System files (`claude-memory-system/`):

1. **Never modify daemon scripts** - these run in background
2. **Policy files are read-only** - documentation only
3. **All documentation in MASTER-README.md** - single source of truth
4. **Java standards in docs/** - Spring Boot patterns and conventions
5. **Scripts in root** - automation and monitoring utilities

**For complete Memory System guidance, always reference:**
`claude-memory-system/MASTER-README.md` (2,891 lines, fully indexed)

---

## Project Structure Summary

```
claude-monitoring-system/
├── app.py                         # Main Flask application (3,500+ lines)
├── requirements.txt               # Python dependencies (14 packages)
├── verify_enhancements.py         # Enhancement validation script
│
├── utils/                         # Core monitoring utilities (17 files)
│   ├── metrics.py                 # MetricsCollector
│   ├── memory_system_monitor.py   # Memory System integration
│   ├── anomaly_detector.py        # AI anomaly detection
│   ├── predictive_analytics.py    # Forecasting engine
│   ├── alert_routing.py           # Alert routing engine
│   ├── collaboration_manager.py   # Real-time editing
│   └── ... (11 more utilities)
│
├── templates/                     # HTML templates (17 files)
│   ├── base.html                  # Base layout
│   ├── dashboard.html             # Main dashboard
│   ├── widget-builder.html        # Collaborative editor
│   └── ... (14 more templates)
│
├── static/                        # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── img/
│
├── claude-memory-system/          # Memory System v2.2.0 (139 files)
│   ├── MASTER-README.md           # Complete guide (2,891 lines)
│   ├── docs/                      # Java standards (10 files)
│   ├── policies/                  # 12 policy files
│   ├── *.py                       # 81 automation scripts
│   └── *-daemon.py                # 8-9 background daemons
│
└── memory_files/                  # Memory System file storage
```

---

This CLAUDE.md provides the essential context for working effectively in this codebase. For complete Memory System documentation, always reference `claude-memory-system/MASTER-README.md`.
