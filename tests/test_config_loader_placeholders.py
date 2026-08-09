"""An unfilled config template must not be injected as if it were a credential.

The shipped workflow-config.json carries `"github": {"token": "YOUR_GITHUB_TOKEN"}`.
load_workflow_config injected that string into GITHUB_TOKEN, and one placeholder
then defeated BOTH GitHub backends at once: the MCP client authenticated with it
and got 401 Bad credentials, and the gh CLI fallback also lost, because gh prefers
an environment token over its own keyring and reported itself unauthenticated.

`gh auth login` therefore appeared to do nothing. Step 2 fell back to "no GitHub
backend available" on every run, and the pipeline could not create an issue or a
branch on a machine that was, by every other measure, correctly authenticated.
Injecting nothing leaves the keyring reachable, which is the working path.

The predicate is deliberately narrow, and half of these tests exist to hold it
that way. A false positive rejects a real secret and breaks a setup that was
working -- worse than the bug it guards against -- so nothing is matched on
length, entropy or character class.
"""

import json
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from langgraph_engine.core import config_loader  # noqa: E402
from langgraph_engine.core.config_loader import _is_placeholder, load_workflow_config  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Reset the env vars and the module's config cache before each test.

    _load_raw memoises into _CONFIG_CACHE on first read, after which the `path`
    argument is silently ignored. Without this reset the first test to run would
    pin the real ~/.claude/workflow-config.json for every test after it, and the
    suite would be asserting against the developer's own machine -- which is how
    a green suite ends up proving nothing.
    """
    for var in ("GITHUB_TOKEN", "GITHUB_DEFAULT_LABEL", "CLAUDE_GITHUB_OWNER", "JIRA_API_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(config_loader, "_CONFIG_CACHE", None)


def _write_config(tmp_path, payload):
    """Write a workflow-config.json and return its path."""
    path = tmp_path / "workflow-config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestThePlaceholderIsNotInjected:
    """The exact failure that cost a day."""

    def test_the_shipped_github_placeholder_is_skipped(self, tmp_path):
        path = _write_config(tmp_path, {"github": {"token": "YOUR_GITHUB_TOKEN"}})
        injected = load_workflow_config(path)
        assert "GITHUB_TOKEN" not in injected
        assert "GITHUB_TOKEN" not in __import__("os").environ

    def test_a_real_looking_token_is_still_injected(self, tmp_path):
        """The half that fails if the predicate became greedy.

        Without this, a predicate that rejected everything would satisfy the test
        above -- and would break every correctly configured machine instead.
        """
        path = _write_config(tmp_path, {"github": {"token": "ghp_16CharsOrMoreOfRealLookingSecret"}})
        injected = load_workflow_config(path)
        assert injected.get("GITHUB_TOKEN") == "ghp_16CharsOrMoreOfRealLookingSecret"

    def test_other_real_values_survive_alongside_a_skipped_one(self, tmp_path):
        """One placeholder must not suppress the rest of the file."""
        path = _write_config(
            tmp_path,
            {"github": {"token": "YOUR_GITHUB_TOKEN", "owner": "techdeveloper-org", "default_label": "feature"}},
        )
        injected = load_workflow_config(path)
        assert "GITHUB_TOKEN" not in injected
        assert injected.get("CLAUDE_GITHUB_OWNER") == "techdeveloper-org"
        assert injected.get("GITHUB_DEFAULT_LABEL") == "feature"


class TestTheSkipIsAnnounced:
    """A value silently ignored is indistinguishable from one never read."""

    def test_the_skip_is_reported(self, tmp_path, capsys):
        path = _write_config(tmp_path, {"github": {"token": "YOUR_GITHUB_TOKEN"}})
        load_workflow_config(path)
        assert "github.token" in capsys.readouterr().err

    def test_nothing_is_reported_when_nothing_was_skipped(self, tmp_path, capsys):
        """The half that fails if the notice were unconditional."""
        path = _write_config(tmp_path, {"github": {"owner": "techdeveloper-org"}})
        load_workflow_config(path)
        assert "config_loader" not in capsys.readouterr().err


class TestThePredicateIsNarrow:
    """A false positive breaks a working setup, so the shapes are enumerated."""

    @pytest.mark.parametrize(
        "value",
        [
            "YOUR_GITHUB_TOKEN",
            "your-api-key",
            "<your-token-here>",
            "CHANGEME",
            "change_me",
            "REPLACE_ME",
            "TODO",
            "xxxxxxxx",
            "",
            "   ",
        ],
    )
    def test_template_shapes_are_placeholders(self, value):
        assert _is_placeholder(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "ghp_realLookingToken1234567890",
            "gho_anotherRealShape",
            "github_pat_11ABCDEF",
            "techdeveloper-org",
            "feature",
            "sk-ant-api03-abcdef",
            "yourcompany-prod-key",  # starts with "your" but not "your_" or "your-"
            "0123456789abcdef",
        ],
    )
    def test_real_values_are_not_placeholders(self, value):
        assert _is_placeholder(value) is False

    def test_a_non_string_is_not_a_placeholder(self):
        """Config values may be bools or numbers; those are not templates."""
        assert _is_placeholder(True) is False
        assert _is_placeholder(0) is False


class TestExistingBehaviourIsUnchanged:
    """The no-override rule and missing-file handling must not have moved."""

    def test_an_existing_env_var_still_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_GITHUB_OWNER", "already-set")
        path = _write_config(tmp_path, {"github": {"owner": "from-config"}})
        injected = load_workflow_config(path)
        assert "CLAUDE_GITHUB_OWNER" not in injected
        assert __import__("os").environ["CLAUDE_GITHUB_OWNER"] == "already-set"

    def test_a_missing_file_returns_empty(self, tmp_path):
        assert load_workflow_config(tmp_path / "absent.json") == {}
