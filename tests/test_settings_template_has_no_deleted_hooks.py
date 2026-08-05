"""The bootstrap template must not re-register the hooks v2.0.0 deleted.

`scripts/settings-config.json` is the template `~/.claude/settings.json` is
created from, and both `setup-global-claude.ps1` and `setup-global-claude.sh`
copy it over an existing settings file wholesale rather than merging into it.
So a machine bootstrapped from this template gets exactly whatever it declares.

Until this test existed, that template still registered `UserPromptSubmit`,
`PreToolUse` and `PostToolUse` -- the three registrations PRD FR-4 / SRS FR-13
and FR-15 removed. Nothing detected it: the hook-deletion issue's own criterion
asserts against the LIVE settings file rather than the template, the sibling
issue that needed `UserPromptSubmit` gone was forbidden from touching settings
and deferred, and the push-gate CI assertion reasons only about `PreToolUse` and
the MCP gate. **The most likely way the migration gets undone was also the way
least likely to be noticed.**

`Stop` is asserted to REMAIN. It is a retained user-level registration the
plugin never owned, and dropping it would be a different regression in the
opposite direction -- which is why the two assertions are paired rather than a
single "no hooks" check.
"""

import io
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "scripts" / "settings-config.json"

DELETED_HOOK_EVENTS = ("UserPromptSubmit", "PreToolUse", "PostToolUse")
RETAINED_HOOK_EVENTS = ("Stop",)


def load_template():
    """Read the bootstrap template.

    Returns:
        dict: The parsed template.
    """
    return json.loads(io.open(TEMPLATE, encoding="utf-8").read())


def deleted_events_present(document):
    """List the deleted hook events a settings document still registers.

    Args:
        document: A parsed settings or template document.

    Returns:
        list: Event names in DELETED_HOOK_EVENTS present in the document.
    """
    hooks = document.get("hooks", {})
    return [event for event in DELETED_HOOK_EVENTS if event in hooks]


class TestTemplateDropsTheDeletedHooks:
    """The three registrations v2.0.0 removed must not reappear here."""

    def test_no_deleted_hook_event_is_registered(self):
        present = deleted_events_present(load_template())
        assert present == [], "bootstrap template re-registers deleted hooks: %r" % present

    def test_the_check_can_fail(self):
        """A template carrying one of the three is rejected, naming it."""
        planted = {"hooks": {"Stop": [], "PreToolUse": [{"hooks": []}]}}
        assert deleted_events_present(planted) == ["PreToolUse"]

    def test_the_check_is_not_vacuous(self):
        """All three are detected, not just the first."""
        planted = {"hooks": {event: [] for event in DELETED_HOOK_EVENTS}}
        assert deleted_events_present(planted) == list(DELETED_HOOK_EVENTS)


class TestTemplateKeepsWhatWasRetained:
    """Paired with the above so a blanket hook purge fails too."""

    def test_retained_hook_events_are_still_registered(self):
        hooks = load_template().get("hooks", {})
        missing = [event for event in RETAINED_HOOK_EVENTS if event not in hooks]
        assert missing == [], "bootstrap template dropped retained hooks: %r" % missing

    def test_a_template_with_no_hooks_at_all_fails_this_direction(self):
        """Specificity: removing everything is a regression, not a pass."""
        empty = {"hooks": {}}
        missing = [event for event in RETAINED_HOOK_EVENTS if event not in empty["hooks"]]
        assert missing == list(RETAINED_HOOK_EVENTS)


class TestTemplateIsWellFormed:
    """The template is copied verbatim onto a live settings file."""

    def test_template_parses_as_json(self):
        assert isinstance(load_template(), dict)

    def test_template_is_ascii_only(self):
        raw = io.open(TEMPLATE, "rb").read()
        assert not [byte for byte in raw if byte > 127]
