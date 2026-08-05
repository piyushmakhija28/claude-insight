"""The docs index must describe the tree it indexes.

`docs/README.md` is the entry point `rules/11-documentation-files.md` points a
reader at, and it had rotted in two directions at once: six of its nine declared
folder counts disagreed with the tree, and **eight folders containing 63 files
were absent from it entirely** -- every one of them created during the v2.0.0
sprint by a node that added documents without touching the index.

Nothing detected that, because the index is prose. Five separate nodes each
noticed their own guide was unlisted, each reported it, and each followed the
precedent of not listing it -- so the drift compounded rather than being caught.

This test makes the index checkable. It asserts two directions, because either
one alone is satisfiable by a degenerate index:

- every folder under `docs/` holding files appears in the summary table, so a
  new folder cannot be silently omitted;
- every declared count equals the number of files actually in that folder, so a
  folder cannot be listed and then left to drift.

Counts are of ALL files, not just Markdown: `api/` holds a single YAML spec and
the index has always counted it.
"""

import io
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
INDEX = DOCS / "README.md"

TABLE_ROW = re.compile(r"\| \[`([\w.-]+)/`\]\([\w.-]+/\) \| [^|]+ \| (\d+) \|")


def declared_counts():
    """Read the folder counts the index declares.

    Returns:
        dict: Folder name (without slash) mapped to its declared file count.
    """
    text = io.open(INDEX, encoding="utf-8").read()
    return {name: int(count) for name, count in TABLE_ROW.findall(text)}


def actual_counts():
    """Count the files in every immediate subfolder of docs/.

    Returns:
        dict: Folder name mapped to its file count, excluding empty folders.
    """
    counts = {}
    for entry in sorted(os.listdir(DOCS)):
        path = DOCS / entry
        if not path.is_dir():
            continue
        files = [name for name in os.listdir(path) if (path / name).is_file()]
        if files:
            counts[entry] = len(files)
    return counts


class TestEveryFolderIsListed:
    """A folder holding files may not be missing from the index."""

    def test_no_docs_folder_is_absent_from_the_index(self):
        missing = sorted(set(actual_counts()) - set(declared_counts()))
        assert missing == [], "docs/README.md does not list: %r" % missing

    def test_the_check_can_fail(self):
        """A folder present on disk and absent from the table is caught."""
        declared = {"guides": 21}
        actual = {"guides": 21, "phase-9-invented": 3}
        assert sorted(set(actual) - set(declared)) == ["phase-9-invented"]


class TestEveryDeclaredCountIsTrue:
    """A listed folder may not drift from the number beside it."""

    def test_declared_counts_equal_the_tree(self):
        declared, actual = declared_counts(), actual_counts()
        wrong = {name: (count, actual.get(name)) for name, count in declared.items() if actual.get(name) != count}
        assert wrong == {}, "docs/README.md counts disagree with the tree: %r" % wrong

    def test_the_check_can_fail(self):
        """An off-by-one count is caught, and names both figures."""
        declared, actual = {"guides": 14}, {"guides": 21}
        wrong = {n: (c, actual.get(n)) for n, c in declared.items() if actual.get(n) != c}
        assert wrong == {"guides": (14, 21)}


class TestTheIndexIsNotDegenerate:
    """Either assertion alone is satisfiable by an index that says nothing."""

    def test_an_empty_index_fails_the_listing_direction(self):
        assert sorted(set({"guides": 21}) - set({})) == ["guides"]

    def test_the_index_actually_declares_folders(self):
        """Guards against a regex that silently matches nothing."""
        assert len(declared_counts()) >= 10
