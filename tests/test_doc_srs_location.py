"""Tests that the SRS is generated where every other part of the system reads it.

`DocumentationGenerator` used to create the SRS at
`docs/SYSTEM_REQUIREMENTS_SPECIFICATION.md`, a path that exists nowhere in this repo,
while `documentation_manager` reads the project-root `SRS.md` and both rules/11
(permitted root documentation files) and rules/44 (SRS lifecycle) place it at the
root. A fresh project therefore got one SRS created in `docs/` that nothing ever
read, and the root `SRS.md` the manager appends requirements to was never generated.

Windows-safe: ASCII only, no Unicode characters.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "langgraph_engine" / "sdlc_pipeline" / "documentation_generator.py"
MANAGER = REPO_ROOT / "langgraph_engine" / "sdlc_pipeline" / "documentation_manager.py"


def _generator_source():
    """Read the generator module source.

    Returns:
        str: File contents.
    """
    return GENERATOR.read_text(encoding="utf-8")


class TestGeneratorTargetsRootSrs:
    """The generator must write the SRS to the project root."""

    def test_srs_is_generated_at_the_repo_root(self):
        source = _generator_source()
        assert '("SRS.md", self.update_or_create_sra)' in source

    def test_no_longer_targets_the_docs_path(self):
        source = _generator_source()
        assert '("docs/SYSTEM_REQUIREMENTS_SPECIFICATION.md"' not in source

    def test_generated_target_matches_what_the_manager_reads(self):
        """Generator and manager must agree on the same file."""
        manager = MANAGER.read_text(encoding="utf-8")
        match = re.search(r"_SRS_ALTERNATES\s*=\s*\[(.*?)\]", manager, re.DOTALL)
        assert match is not None, "_SRS_ALTERNATES not found in documentation_manager"
        first_alternate = re.findall(r'"([^"]+)"', match.group(1))[0]
        assert first_alternate == "SRS.md"
        assert '("{}", self.update_or_create_sra)'.format(first_alternate) in _generator_source()

    def test_docs_srs_path_does_not_exist_in_this_repo(self):
        """The old target was never a real location."""
        assert not (REPO_ROOT / "docs" / "SYSTEM_REQUIREMENTS_SPECIFICATION.md").exists()
        assert (REPO_ROOT / "SRS.md").exists()


class TestRootDocumentationGovernance:
    """rules/11 permits exactly five documentation files at the repo root."""

    PERMITTED = {"SRS.md", "README.md", "CLAUDE.md", "CHANGELOG.md"}

    def test_only_permitted_markdown_files_are_tracked_at_the_root(self):
        import subprocess

        result = subprocess.run(
            ["git", "ls-files", "--", "*.md"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        root_markdown = {line for line in result.stdout.split() if "/" not in line}
        unexpected = root_markdown - self.PERMITTED
        assert unexpected == set(), "unexpected root markdown files: {}".format(sorted(unexpected))
