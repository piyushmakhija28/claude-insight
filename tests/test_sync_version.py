"""Tests for scripts/tools/sync-version.py and the release helper's root resolution.

Guards the three defects from issue #248, each of which was silent:

1. ``PROJECT_ROOT`` resolved to ``scripts/`` instead of the repo root, so every
   target path was wrong and the script reported success while propagating nothing.
2. Any argument was written straight into VERSION, so ``--help`` set the project
   version to the literal string ``--help``.
3. Targets were rewritten with ``Path.write_text``, which on Windows converts the
   committed LF files to CRLF and turns a two-line bump into a whole-file diff.

Windows-safe: ASCII only, no Unicode characters.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC_SCRIPT = REPO_ROOT / "scripts" / "tools" / "sync-version.py"
RELEASE_SCRIPT = REPO_ROOT / "scripts" / "tools" / "release.py"
VERSION_FILE = REPO_ROOT / "VERSION"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _run(*args):
    """Run sync-version.py with the given arguments.

    Args:
        *args: Command-line arguments to pass.

    Returns:
        subprocess.CompletedProcess: Captured result.
    """
    return subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )


@pytest.fixture
def version_guard():
    """Restore the VERSION file byte-for-byte after a test.

    Yields:
        bytes: The original file contents.
    """
    original = VERSION_FILE.read_bytes()
    yield original
    VERSION_FILE.write_bytes(original)


class TestProjectRootResolution:
    """The scripts must resolve the repo root, not scripts/."""

    def test_sync_script_resolves_repo_root(self):
        """PROJECT_ROOT must be three parents up from scripts/tools/<file>.py."""
        source = SYNC_SCRIPT.read_text(encoding="utf-8")
        assert "PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent" in source

    def test_release_script_resolves_repo_root(self):
        source = RELEASE_SCRIPT.read_text(encoding="utf-8")
        assert "PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent" in source

    def test_no_stray_version_file_under_scripts(self):
        """scripts/VERSION is the tell-tale artifact of the wrong root."""
        assert not (REPO_ROOT / "scripts" / "VERSION").exists()

    def test_every_declared_target_exists(self):
        """A missing target means the layout moved and TARGETS is stale."""
        result = _run("--dry-run")
        assert "[MISSING]" not in result.stdout, result.stdout
        assert result.returncode == 0, result.stdout + result.stderr


class TestArgumentValidation:
    """A bad argument must never reach the VERSION file."""

    @pytest.mark.parametrize("bad", ["--help", "-h", "not-a-version", "1.2", "v1.2.3", "1.2.3.4", ""])
    def test_bad_argument_leaves_version_untouched(self, bad, version_guard):
        _run(bad)
        assert VERSION_FILE.read_bytes() == version_guard

    def test_help_exits_zero_and_prints_usage(self):
        result = _run("--help")
        assert result.returncode == 0
        assert "usage:" in result.stdout

    def test_non_semver_argument_exits_nonzero(self, version_guard):
        result = _run("not-a-version")
        assert result.returncode != 0
        assert "Not a valid version" in result.stderr

    def test_valid_version_is_accepted_in_dry_run(self, version_guard):
        result = _run("--dry-run", "9.9.9")
        assert result.returncode == 0
        assert VERSION_FILE.read_bytes() == version_guard, "dry run must not write"


class TestLineEndingPreservation:
    """Propagation must not rewrite a file's line terminators."""

    TARGETS = ("README.md", "CLAUDE.md", "SRS.md", "langgraph_engine/__init__.py")

    def test_sync_preserves_each_target_line_endings(self):
        before = {}
        for name in self.TARGETS:
            data = (REPO_ROOT / name).read_bytes()
            before[name] = (data.count(b"\r\n"), data.count(b"\n") - data.count(b"\r\n"))

        result = _run()
        assert result.returncode == 0, result.stdout + result.stderr

        for name in self.TARGETS:
            data = (REPO_ROOT / name).read_bytes()
            after = (data.count(b"\r\n"), data.count(b"\n") - data.count(b"\r\n"))
            assert after == before[name], "{} line endings changed: {} -> {}".format(name, before[name], after)

    def test_script_does_not_use_text_mode_writes(self):
        """Path.write_text is what flipped LF to CRLF; it must stay out."""
        source = SYNC_SCRIPT.read_text(encoding="utf-8")
        offenders = [line.strip() for line in source.splitlines() if ".write_text(" in line]
        assert offenders == [], offenders


class TestVersionConsistency:
    """After a sync every hand-written reference must match VERSION."""

    def test_all_references_match_version_file(self):
        _run()
        version = VERSION_FILE.read_bytes().decode("utf-8").strip()
        assert SEMVER_RE.match(version), version

        checks = (
            ("README.md", r"\*\*Version:\*\*\s*([\d.]+)"),
            ("CLAUDE.md", r"\*\*Version:\*\*\s*([\d.]+)"),
            ("SRS.md", r"\*\*Version:\*\*\s*([\d.]+)"),
            ("langgraph_engine/__init__.py", r'__version__\s*=\s*["\']([\d.]+)["\']'),
        )
        for name, pattern in checks:
            text = (REPO_ROOT / name).read_text(encoding="utf-8")
            match = re.search(pattern, text)
            assert match is not None, "no version reference found in {}".format(name)
            assert match.group(1) == version, "{} says {}, VERSION says {}".format(name, match.group(1), version)


def test_dead_bump_version_shell_script_is_gone():
    """bump-version.sh called two scripts and two app files that never existed."""
    assert not (REPO_ROOT / "scripts" / "tools" / "bump-version.sh").exists()
