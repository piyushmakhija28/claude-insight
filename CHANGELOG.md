# Changelog

All notable changes to Claude Insight will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Migrated to semantic versioning (MAJOR.MINOR.PATCH)
- Improved version management workflow

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
