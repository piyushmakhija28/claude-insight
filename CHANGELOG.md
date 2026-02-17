# Changelog

All notable changes to Claude Insight will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [3.3.0] - 2026-02-18

### Added
- **Comprehensive Documentation Policy v2.0**
  - Added `scripts/comprehensive-docs-checker.py` - Auto-check, auto-create, and auto-update documentation
  - Minimum 50 lines requirement with required sections
  - Auto-creates missing README.md and CLAUDE.md in all git repos
  - Auto-updates non-comprehensive files (preserves .backup)
  - Flexible section matching (PROJECT/SERVICE/APPLICATION OVERVIEW accepted)

- **3-Level Flow Display System**
  - Added `test-complete-execution-flow.sh` - Complete 3-level architecture test
  - Shows all 17 steps (Level -1, Level 1, Level 2, Level 3 with 12 execution steps)
  - Mandatory display before every request for transparency
  - User-configurable TRACE_MODE flag

- **True Automation System**
  - Added `auto-enforce-all-policies.sh` - All-in-one automatic policy enforcement
  - Added `install-auto-hooks.sh` - Auto-hooks installer for pre-request execution
  - Policies now run automatically before every request (no manual intervention)
  - Blocking mode: policies must pass before response

- **Per-Request Policy Enforcement**
  - Added `per-request-enforcer.py` - Continuous policy enforcement system
  - Policies run before EVERY user request (not just session start)
  - Per-request state tracking with completion markers
  - Final check before responding to user

### Changed
- **Documentation Standards** - Updated to v2.0.0 with auto-enforcement
- **Auto-Fix Enforcement** - Enhanced with more comprehensive checks
- **Production Infrastructure** - New documentation for VPS/K8s/Three-Tier Routing

### Documentation
- Updated `docs/documentation-standards.md` to v2.0.0
- Added `docs/production-infrastructure.md` with VPS setup details
- Updated `docs/auto-fix-enforcement.md` with latest policies

---

## [2.7.0] - 2026-02-17

### Added
- **Complete Daemon Management System**
  - Added `daemon-manager.py` - Comprehensive daemon lifecycle management for all 10 daemons
  - Added `health-monitor-daemon.py` - Auto-restart monitor for dead daemons (checks every 5 min)
  - Added `daemon-logger.py` - Centralized daemon logging system
  - Added `pid-tracker.py` - Process ID tracking and management
  - All utilities added to `src/utils/` for easy access

- **Enhanced Daemon Support**
  - Now manages 10 core daemons (upgraded from 8-9)
  - Added `token-optimization-daemon` - Auto-optimizes context when >85%
  - Added `health-monitor-daemon` - Auto-restarts dead daemons
  - Removed non-existent `auto-recommendation-daemon`

- **Cross-Platform Daemon Management**
  - Windows, Linux, Mac support
  - Auto-start on system login
  - JSON status API for dashboard integration
  - Real-time daemon health monitoring

### Changed
- **daemon-manager.py** - Updated with correct subdirectory paths for all daemon scripts
- **health-monitor-daemon.py** - Fixed import paths to use `utilities/` subdirectory
- All daemon scripts now properly reference their actual locations
- Documentation updated with complete daemon system details

### Fixed
- Fixed daemon-manager.py looking for scripts in wrong directories
- Fixed health-monitor-daemon.py import errors (daemon-logger.py, pid-tracker.py, daemon-manager.py)
- Fixed missing daemon paths causing startup failures
- All 10 daemons now start and run correctly with auto-restart capability

### Documentation
- Updated README.md with daemon management system details
- Updated CLAUDE.md with complete daemon information
- Added daemon utilities documentation
- Added changelog entry for v2.7.0

---

## [2.5.2] - 2026-02-16

### Bug
- Bug fixes and minor improvements

---

## [2.5.1] - 2026-02-16

### Added
- **Automatic Versioning System**
  - VERSION file for semantic versioning
  - Version display in navbar
  - `bump-version.py` script for version management
  - `bump-version.sh` wrapper with auto-commit, tag, push, release
  - Automatic GitHub release creation using gh CLI

- **Portability Improvements**
  - PathResolver utility for smart path detection
  - Support for both Global mode (`~/.claude/memory`) and Local mode (`./data/`)
  - Auto-creation of local data directory structure
  - Batch path fixer script (`fix-paths.py`)

### Changed
- Updated 18 service files to use PathResolver instead of hardcoded paths
- Repository description updated to reflect v2.5+ features
- Removed GitHub Actions dependency (using gh CLI directly)

### Fixed
- Fixed all hardcoded `~/.claude/memory` paths for portability
- Fixed session-start.sh daemon status checking using daemon-manager.py
- Fixed Unicode encoding errors in various scripts

---

## [2.5.0] - 2026-02-15

### Added
- **Claude/Anthropic API Integration**
  - Secure credential storage with Fernet encryption
  - API key validation and connection testing
  - Auto-tracking enable/disable with configurable intervals
  - Manual session sync capability
  - Setup instructions with Anthropic Console links

- **Session Search Feature**
  - Search sessions by ID
  - Search sessions by date
  - View complete session details ("chittha")
  - Session timeline visualization
  - Work items tracking

### Changed
- Updated navigation with Session Search and Claude API links
- Added cryptography, requests, and pyotp dependencies

---

## [2.4.0] - 2026-02-15

### Added
- Migration Skill & Migration Expert Agent
- GitHub CLI (`gh`) mandatory enforcement for all GitHub operations

---

## [2.3.0] - 2026-02-10

### Changed
- Restored active enforcement mode
- Enhanced policy execution

---

## [2.2.0] - 2026-02-09

### Added
- Initial Claude Memory System integration
- Real-time monitoring capabilities
- Cost comparison features
- Session tracking

---

## Links

- [Repository](https://github.com/piyushmakhija28/claude-insight)
- [Issues](https://github.com/piyushmakhija28/claude-insight/issues)
- [Releases](https://github.com/piyushmakhija28/claude-insight/releases)

---

**Legend:**
- `Added` - New features
- `Changed` - Changes in existing functionality
- `Deprecated` - Soon-to-be removed features
- `Removed` - Removed features
- `Fixed` - Bug fixes
- `Security` - Security improvements
