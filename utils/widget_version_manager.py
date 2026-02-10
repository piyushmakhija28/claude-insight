"""
Widget Version Manager
Handles versioning, diff generation, and rollback for community widgets.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import difflib
import re


class WidgetVersionManager:
    """Manages widget versions with semantic versioning and diff tracking."""

    def __init__(self, base_dir: str = None):
        """Initialize the version manager.

        Args:
            base_dir: Base directory for version storage. Defaults to ~/.claude/memory/community
        """
        if base_dir is None:
            base_dir = os.path.expanduser("~/.claude/memory/community")

        self.base_dir = Path(base_dir)
        self.versions_dir = self.base_dir / "widget_versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def _get_version_file(self, widget_id: str) -> Path:
        """Get the path to the version metadata file."""
        return self.versions_dir / f"{widget_id}_versions.json"

    def _get_snapshot_file(self, widget_id: str, version: str) -> Path:
        """Get the path to a version snapshot file."""
        return self.versions_dir / f"{widget_id}_v{version.replace('.', '_')}.json"

    def _atomic_write(self, filepath: Path, data: dict):
        """Atomically write JSON data to file."""
        temp_file = filepath.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(filepath)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e

    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse semantic version string into (major, minor, patch)."""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")
        return tuple(map(int, match.groups()))

    def _increment_version(self, current: str, version_type: str) -> str:
        """Increment version based on type (major, minor, patch)."""
        major, minor, patch = self._parse_version(current)

        if version_type == 'major':
            return f"{major + 1}.0.0"
        elif version_type == 'minor':
            return f"{major}.{minor + 1}.0"
        elif version_type == 'patch':
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid version type: {version_type}")

    def initialize_versioning(self, widget_id: str, widget_data: dict,
                            created_by: str = "admin") -> dict:
        """Initialize version control for a widget.

        Args:
            widget_id: Widget identifier
            widget_data: Current widget data
            created_by: User who created the version

        Returns:
            Version metadata
        """
        version_file = self._get_version_file(widget_id)

        # Check if already initialized
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Create initial version
        initial_version = "1.0.0"
        timestamp = datetime.utcnow().isoformat() + 'Z'

        version_metadata = {
            "widget_id": widget_id,
            "current_version": initial_version,
            "versions": [
                {
                    "version": initial_version,
                    "version_type": "major",
                    "created_at": timestamp,
                    "created_by": created_by,
                    "commit_message": "Initial version",
                    "snapshot_file": f"{widget_id}_v1_0_0.json",
                    "parent_version": None,
                    "diff": {
                        "added_lines": 0,
                        "removed_lines": 0,
                        "modified_components": []
                    }
                }
            ]
        }

        # Save version metadata
        self._atomic_write(version_file, version_metadata)

        # Save snapshot
        snapshot_file = self._get_snapshot_file(widget_id, initial_version)
        self._atomic_write(snapshot_file, widget_data)

        return version_metadata

    def create_version(self, widget_id: str, widget_data: dict,
                      version_type: str = 'patch',
                      commit_message: str = "",
                      created_by: str = "admin") -> dict:
        """Create a new version of the widget.

        Args:
            widget_id: Widget identifier
            widget_data: New widget data
            version_type: 'major', 'minor', or 'patch'
            commit_message: Description of changes
            created_by: User creating the version

        Returns:
            New version metadata
        """
        version_file = self._get_version_file(widget_id)

        # Initialize if needed
        if not version_file.exists():
            self.initialize_versioning(widget_id, widget_data, created_by)
            return self.get_current_version(widget_id)

        # Load existing versions
        with open(version_file, 'r', encoding='utf-8') as f:
            version_data = json.load(f)

        # Calculate new version
        current_version = version_data['current_version']
        new_version = self._increment_version(current_version, version_type)

        # Load previous snapshot for diff
        prev_snapshot_file = self._get_snapshot_file(widget_id, current_version)
        with open(prev_snapshot_file, 'r', encoding='utf-8') as f:
            prev_data = json.load(f)

        # Generate diff
        diff_info = self._generate_diff(prev_data, widget_data)

        # Create version entry
        timestamp = datetime.utcnow().isoformat() + 'Z'
        version_entry = {
            "version": new_version,
            "version_type": version_type,
            "created_at": timestamp,
            "created_by": created_by,
            "commit_message": commit_message or f"{version_type.capitalize()} update",
            "snapshot_file": f"{widget_id}_v{new_version.replace('.', '_')}.json",
            "parent_version": current_version,
            "diff": diff_info
        }

        # Update version metadata
        version_data['current_version'] = new_version
        version_data['versions'].append(version_entry)
        self._atomic_write(version_file, version_data)

        # Save new snapshot
        snapshot_file = self._get_snapshot_file(widget_id, new_version)
        self._atomic_write(snapshot_file, widget_data)

        return version_entry

    def _generate_diff(self, old_data: dict, new_data: dict) -> dict:
        """Generate diff between two widget versions.

        Args:
            old_data: Previous widget data
            new_data: New widget data

        Returns:
            Diff information
        """
        # Convert to JSON strings for line-by-line comparison
        old_json = json.dumps(old_data, indent=2, sort_keys=True).splitlines()
        new_json = json.dumps(new_data, indent=2, sort_keys=True).splitlines()

        # Generate unified diff
        differ = difflib.unified_diff(old_json, new_json, lineterm='')
        diff_lines = list(differ)

        # Count changes
        added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

        # Detect modified components
        modified_components = []

        # Check HTML changes
        if old_data.get('html_content') != new_data.get('html_content'):
            modified_components.append('html')

        # Check CSS changes
        if old_data.get('css_content') != new_data.get('css_content'):
            modified_components.append('css')

        # Check JS changes
        if old_data.get('js_content') != new_data.get('js_content'):
            modified_components.append('javascript')

        # Check metadata changes
        if old_data.get('name') != new_data.get('name') or \
           old_data.get('description') != new_data.get('description'):
            modified_components.append('metadata')

        return {
            "added_lines": added,
            "removed_lines": removed,
            "modified_components": modified_components
        }

    def get_version_list(self, widget_id: str, limit: int = 50,
                        offset: int = 0) -> List[dict]:
        """Get list of all versions for a widget.

        Args:
            widget_id: Widget identifier
            limit: Maximum number of versions to return
            offset: Number of versions to skip

        Returns:
            List of version metadata (newest first)
        """
        version_file = self._get_version_file(widget_id)

        if not version_file.exists():
            return []

        with open(version_file, 'r', encoding='utf-8') as f:
            version_data = json.load(f)

        versions = version_data.get('versions', [])
        # Reverse to get newest first
        versions = list(reversed(versions))

        return versions[offset:offset + limit]

    def get_version(self, widget_id: str, version: str) -> Optional[dict]:
        """Get specific version data.

        Args:
            widget_id: Widget identifier
            version: Version string (e.g., "1.2.3")

        Returns:
            Widget data for that version, or None if not found
        """
        snapshot_file = self._get_snapshot_file(widget_id, version)

        if not snapshot_file.exists():
            return None

        with open(snapshot_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_current_version(self, widget_id: str) -> Optional[dict]:
        """Get current version metadata.

        Args:
            widget_id: Widget identifier

        Returns:
            Current version metadata
        """
        version_file = self._get_version_file(widget_id)

        if not version_file.exists():
            return None

        with open(version_file, 'r', encoding='utf-8') as f:
            version_data = json.load(f)

        current = version_data['current_version']
        versions = version_data['versions']

        for v in reversed(versions):
            if v['version'] == current:
                return v

        return None

    def get_diff(self, widget_id: str, from_version: str,
                to_version: str) -> dict:
        """Get diff between two versions.

        Args:
            widget_id: Widget identifier
            from_version: Source version
            to_version: Target version

        Returns:
            Detailed diff information
        """
        old_data = self.get_version(widget_id, from_version)
        new_data = self.get_version(widget_id, to_version)

        if not old_data or not new_data:
            return {"error": "Version not found"}

        # Generate unified diff for each component
        diff_result = {
            "from_version": from_version,
            "to_version": to_version,
            "summary": self._generate_diff(old_data, new_data),
            "diffs": {}
        }

        # HTML diff
        if old_data.get('html_content') != new_data.get('html_content'):
            html_diff = list(difflib.unified_diff(
                old_data.get('html_content', '').splitlines(),
                new_data.get('html_content', '').splitlines(),
                lineterm='',
                fromfile=f'v{from_version} (HTML)',
                tofile=f'v{to_version} (HTML)'
            ))
            diff_result['diffs']['html'] = html_diff

        # CSS diff
        if old_data.get('css_content') != new_data.get('css_content'):
            css_diff = list(difflib.unified_diff(
                old_data.get('css_content', '').splitlines(),
                new_data.get('css_content', '').splitlines(),
                lineterm='',
                fromfile=f'v{from_version} (CSS)',
                tofile=f'v{to_version} (CSS)'
            ))
            diff_result['diffs']['css'] = css_diff

        # JS diff
        if old_data.get('js_content') != new_data.get('js_content'):
            js_diff = list(difflib.unified_diff(
                old_data.get('js_content', '').splitlines(),
                new_data.get('js_content', '').splitlines(),
                lineterm='',
                fromfile=f'v{from_version} (JavaScript)',
                tofile=f'v{to_version} (JavaScript)'
            ))
            diff_result['diffs']['javascript'] = js_diff

        return diff_result

    def rollback_version(self, widget_id: str, target_version: str,
                        created_by: str = "admin") -> dict:
        """Rollback widget to a previous version.

        Args:
            widget_id: Widget identifier
            target_version: Version to rollback to
            created_by: User performing rollback

        Returns:
            New version metadata (created from rollback)
        """
        # Get target version data
        target_data = self.get_version(widget_id, target_version)
        if not target_data:
            raise ValueError(f"Target version {target_version} not found")

        # Create backup of current version
        version_file = self._get_version_file(widget_id)
        if version_file.exists():
            backup_file = version_file.with_suffix('.backup')
            shutil.copy2(version_file, backup_file)

        # Create new version with rollback data
        commit_message = f"Rollback to version {target_version}"
        return self.create_version(
            widget_id=widget_id,
            widget_data=target_data,
            version_type='patch',
            commit_message=commit_message,
            created_by=created_by
        )

    def delete_version(self, widget_id: str, version: str) -> bool:
        """Delete a specific version (not current).

        Args:
            widget_id: Widget identifier
            version: Version to delete

        Returns:
            True if deleted successfully
        """
        version_file = self._get_version_file(widget_id)

        if not version_file.exists():
            return False

        with open(version_file, 'r', encoding='utf-8') as f:
            version_data = json.load(f)

        # Cannot delete current version
        if version_data['current_version'] == version:
            raise ValueError("Cannot delete current version")

        # Remove version entry
        version_data['versions'] = [
            v for v in version_data['versions']
            if v['version'] != version
        ]

        # Save updated metadata
        self._atomic_write(version_file, version_data)

        # Delete snapshot file
        snapshot_file = self._get_snapshot_file(widget_id, version)
        if snapshot_file.exists():
            snapshot_file.unlink()

        return True
