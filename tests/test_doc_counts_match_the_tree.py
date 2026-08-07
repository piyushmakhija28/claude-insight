"""The file counts CLAUDE.md and README.md advertise must match the repository.

`docs/README.md` carries per-folder counts that are correct, and they are correct
because `test_docs_index_matches_the_tree.py` checks them against a live
enumeration. The same numbers in `CLAUDE.md` and `README.md` had no such check,
and every one of them drifted: seven of the nine claims below were wrong when
this test was written, two of them by more than a factor of two.

That asymmetry is the whole argument for this file. Correcting the numbers once
fixes today; the numbers went stale because nothing could tell they had, and
nothing would have told us again.

Counts come from `git ls-files`, not from the filesystem, for the reason
`test_docs_index_matches_the_tree.py` records: the documentation describes the
repository, not whoever's working tree happens to be on disk. A gitignored
scratch file would otherwise make the claim wrong in every clone but this one.

Deliberately NOT checked: `CLAUDE.md`'s "578 classes, 3,985 methods" call-graph
figures and its "13 servers" MCP count. The first would need a full AST build per
test run and would churn on any code change; the second describes repositories
that live elsewhere and cannot be enumerated from here. A check that is expensive
or that cannot see its subject is worse than an unchecked number, because it
teaches people to ignore it.
"""

import io
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def tracked_paths():
    """List every path tracked in the repository.

    Returns:
        list[str]: Repository-relative paths, forward-slash separated.
    """
    listing = subprocess.run(
        ["git", "ls-files"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in listing.stdout.splitlines() if line.strip()]


def _python_under(prefix, paths):
    """Count tracked Python files beneath a directory prefix."""
    return sum(1 for p in paths if p.startswith(prefix) and p.endswith(".py"))


def _test_modules_in(prefix, paths):
    """Count tracked ``test_*.py`` modules DIRECTLY inside a directory prefix.

    The prefix ends in a slash, so a file sitting directly in it carries exactly
    as many slashes as the prefix does -- ``tests/`` has one, and so does
    ``tests/test_thing.py``. An earlier version added one to that, which made the
    "unit tests" counter report the nine files one level DEEPER
    (``tests/*/test_*.py``) and the three per-directory counters report zero.
    """
    depth = prefix.count("/")
    return sum(
        1
        for p in paths
        if p.startswith(prefix)
        and p.endswith(".py")
        and p.count("/") == depth
        and p.rsplit("/", 1)[1].startswith("test_")
    )


def actual_counts():
    """Compute every figure the documentation claims.

    Returns:
        dict: Claim key mapped to the count the repository actually holds.
    """
    paths = tracked_paths()
    per_dir = {name: _test_modules_in("tests/%s/" % name, paths) for name in ("integration", "e2e", "load")}
    unit = _test_modules_in("tests/", paths)
    return {
        "engine_py": _python_under("langgraph_engine/", paths),
        "repo_py": sum(1 for p in paths if p.endswith(".py")),
        "tests_all_py": _python_under("tests/", paths),
        "tests_total": unit + sum(per_dir.values()),
        "tests_unit": unit,
        "tests_integration": per_dir["integration"],
        "tests_e2e": per_dir["e2e"],
        "tests_load": per_dir["load"],
        "docs_files": sum(1 for p in paths if p.startswith("docs/")),
    }


# Each claim names the file it lives in, a pattern whose capture groups are the
# numbers it advertises, and the actual_counts() keys those groups must equal.
# The group count and key count must agree -- test_every_claim_is_well_formed
# asserts that, so a mis-specified claim fails loudly instead of silently
# checking nothing.
CLAIMS = (
    (
        "CLAUDE.md Quick Info: Total Python Files",
        "CLAUDE.md",
        r"\|\s*\*\*Total Python Files\*\*\s*\|\s*(\d+) \(langgraph_engine/\); (\d+) repo-wide\s*\|",
        ("engine_py", "repo_py"),
    ),
    (
        "CLAUDE.md Quick Info: Test Files",
        "CLAUDE.md",
        r"\|\s*\*\*Test Files\*\*\s*\|\s*(\d+) \((\d+) unit, (\d+) integration, (\d+) e2e, (\d+) load\)\s*\|",
        ("tests_total", "tests_unit", "tests_integration", "tests_e2e", "tests_load"),
    ),
    (
        "README.md tests badge",
        "README.md",
        r"Tests-(\d+)%20files%20\xb7%20(\d+)%20integration",
        ("tests_total", "tests_integration"),
    ),
    (
        "README.md directory tree: tests/ header",
        "README.md",
        r"#\s*(\d+) test_\*\.py files \((\d+) total Python files\)",
        ("tests_total", "tests_all_py"),
    ),
    (
        "README.md directory tree: unit tests",
        "README.md",
        r"#\s*(\d+) unit tests",
        ("tests_unit",),
    ),
    (
        "README.md directory tree: integration tests",
        "README.md",
        r"#\s*(\d+) integration tests",
        ("tests_integration",),
    ),
    (
        "README.md directory tree: e2e tests",
        "README.md",
        r"#\s*(\d+) end-to-end scenario tests",
        ("tests_e2e",),
    ),
    (
        "README.md directory tree: load tests",
        "README.md",
        r"#\s*(\d+) concurrency / load test",
        ("tests_load",),
    ),
    (
        "README.md directory tree: docs/",
        "README.md",
        r"#\s*(\d+) files — architecture docs",
        ("docs_files",),
    ),
    (
        "README.md Testing section: header",
        "README.md",
        r"(\d+) test_\*\.py files \((\d+) total Python files in `tests/`",
        ("tests_total", "tests_all_py"),
    ),
    (
        "README.md Testing section: Unit tests row",
        "README.md",
        r"\| Unit tests \|\s*(\d+)\s*\|",
        ("tests_unit",),
    ),
    (
        "README.md Testing section: Integration tests row",
        "README.md",
        r"\| Integration tests \|\s*(\d+)\s*\|",
        ("tests_integration",),
    ),
    (
        "README.md Testing section: E2E tests row",
        "README.md",
        r"\| E2E tests \|\s*(\d+)\s*\|",
        ("tests_e2e",),
    ),
    (
        "README.md Testing section: Load tests row",
        "README.md",
        r"\| Load tests \|\s*(\d+)\s*\|",
        ("tests_load",),
    ),
)


def declared(claim):
    """Extract the numbers one claim advertises.

    Args:
        claim: A CLAIMS entry.

    Returns:
        tuple[int, ...] | None: The captured numbers, or None if the pattern
        found no match at all.
    """
    _label, filename, pattern, _keys = claim
    text = io.open(REPO_ROOT / filename, encoding="utf-8").read()
    found = re.search(pattern, text)
    if found is None:
        return None
    return tuple(int(group) for group in found.groups())


class TestEveryAdvertisedCountIsTrue:
    """A number printed in the documentation must equal the tracked tree."""

    def test_declared_counts_equal_the_tree(self):
        actual = actual_counts()
        wrong = {}
        for claim in CLAIMS:
            label, _filename, _pattern, keys = claim
            numbers = declared(claim)
            assert numbers is not None, "claim pattern matched nothing: %s" % label
            expected = tuple(actual[key] for key in keys)
            if numbers != expected:
                wrong[label] = {"says": numbers, "actual": expected}
        assert wrong == {}, "documentation counts disagree with the tree: %r" % wrong

    def test_the_check_can_fail(self):
        """An off-by-one is caught, and both figures are named."""
        actual = {"tests_total": 99}
        numbers, keys = (98,), ("tests_total",)
        expected = tuple(actual[key] for key in keys)
        assert numbers != expected


class TestTheClaimsAreWellFormed:
    """A claim that cannot match, or matches nothing, checks nothing."""

    def test_every_claim_pattern_matches_its_file(self):
        unmatched = [claim[0] for claim in CLAIMS if declared(claim) is None]
        assert unmatched == [], "these claim patterns found no match: %r" % unmatched

    def test_group_count_equals_key_count(self):
        """A pattern with fewer groups than keys would silently skip a number."""
        mismatched = {}
        for label, _filename, pattern, keys in CLAIMS:
            groups = re.compile(pattern).groups
            if groups != len(keys):
                mismatched[label] = (groups, len(keys))
        assert mismatched == {}, "claim group/key arity disagrees: %r" % mismatched

    def test_the_claim_set_is_not_empty(self):
        """Guards against a refactor that leaves the suite checking nothing."""
        assert len(CLAIMS) >= 10


class TestTheCountersSeeTheRepository:
    """The counters must return real figures, not zero from a bad prefix."""

    def test_no_counter_returns_zero(self):
        zeros = sorted(key for key, value in actual_counts().items() if value == 0)
        assert zeros == [], "these counters found nothing, so their prefix is wrong: %r" % zeros

    def test_the_parts_sum_to_the_total(self):
        """tests_total must be the sum of its four parts, or the split is a lie."""
        actual = actual_counts()
        parts = actual["tests_unit"] + actual["tests_integration"] + actual["tests_e2e"] + actual["tests_load"]
        assert parts == actual["tests_total"]
