"""
Path Resolver for Claude Insight
Ensures portability - works with or without ~/.claude/ installed
"""

from pathlib import Path
import os


class PathResolver:
    """
    Resolves paths for Claude Insight data storage

    Priority:
    1. If ~/.claude/memory exists (user has Claude Memory System) → use it
    2. Otherwise → use ./data/ within claude-insight (portable mode)
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.global_memory = Path.home() / '.claude' / 'memory'

        # Check if global memory exists
        self.has_global_memory = self.global_memory.exists()

        # Use global if available, otherwise local
        if self.has_global_memory:
            self.base_dir = self.global_memory
            self.mode = "GLOBAL"
        else:
            self.base_dir = self.project_root / 'data'
            self.mode = "LOCAL"
            self._ensure_local_structure()

    def _ensure_local_structure(self):
        """Create local data directory structure"""
        dirs = [
            self.base_dir / 'sessions',
            self.base_dir / 'logs',
            self.base_dir / 'config',
            self.base_dir / 'anomalies',
            self.base_dir / 'forecasts',
            self.base_dir / 'performance',
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get_sessions_dir(self):
        """Get sessions directory"""
        return self.base_dir / 'sessions'

    def get_logs_dir(self):
        """Get logs directory"""
        return self.base_dir / 'logs'

    def get_config_dir(self):
        """Get config directory"""
        return self.base_dir / 'config'

    def get_data_dir(self, subdir=None):
        """Get data directory (optionally with subdirectory)"""
        if subdir:
            return self.base_dir / subdir
        return self.base_dir

    def get_file(self, *parts):
        """Get file path within data directory"""
        return self.base_dir.joinpath(*parts)

    def is_global_mode(self):
        """Check if using global ~/.claude/memory"""
        return self.mode == "GLOBAL"

    def is_local_mode(self):
        """Check if using local ./data/"""
        return self.mode == "LOCAL"

    def get_mode_info(self):
        """Get current mode information"""
        return {
            'mode': self.mode,
            'base_dir': str(self.base_dir),
            'has_global_memory': self.has_global_memory
        }


# Global instance
path_resolver = PathResolver()


# Convenience functions
def get_sessions_dir():
    return path_resolver.get_sessions_dir()


def get_logs_dir():
    return path_resolver.get_logs_dir()


def get_config_dir():
    return path_resolver.get_config_dir()


def get_data_dir(subdir=None):
    return path_resolver.get_data_dir(subdir)


def get_file(*parts):
    return path_resolver.get_file(*parts)


def is_global_mode():
    return path_resolver.is_global_mode()


def is_local_mode():
    return path_resolver.is_local_mode()


def get_mode_info():
    return path_resolver.get_mode_info()
