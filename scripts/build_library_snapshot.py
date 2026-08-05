#!/usr/bin/env python3
"""Build the pinned library snapshot the plugin ships with (ADR-007, SRS FR-29).

WHY THIS EXISTS
---------------
An installed plugin runs from the plugin manager's cache directory and has no
relationship to this repository or to the sibling ``claude-global-library``
checkout. V2-016 established that experimentally: every import back into the
engine raises ``ModuleNotFoundError``. The same applies to data. The selection
package (``langgraph_engine/selection/catalogue.py``) reads four master
catalogues and one persona file per agent out of the library; on a machine with
no library checkout none of those paths exist, so selection cannot run at all.

This script copies what selection actually reads into ``plugin/snapshot/``, so
the plugin carries its own data.

WHAT IS PROJECTED AND WHY
-------------------------
The raw catalogues total 5,488,949 bytes, and three of the four individually
exceed the repository's 500 KB ``check-added-large-files`` limit
(``agents_all.json`` 840,881; ``skills_all.json`` 1,469,836;
``edges_all.json`` 3,117,619). Copying them verbatim is therefore not merely
wasteful, it is blocked.

Projection is safe because ``load_catalogue`` reads a strict subset of each
record. The fields kept below are exactly the ones it reads, and nothing else.
``edges_all.json`` is the extreme case: ``_derive_type_words`` reads that
3 MB file only to collect the distinct prefix appearing before a colon in an
endpoint identifier, so the projection keeps one representative edge per
distinct prefix. ``verify_snapshot_fidelity`` proves the projection preserves
the loader's output rather than assuming it.

SNAPSHOT LOCATION
-----------------
``plugin/snapshot/`` is deliberately NOT one of the seven convention-discovered
capability directory names (``commands``, ``agents``, ``skills``, ``hooks``,
``output-styles``, ``monitors``, ``bin``). Writing the personas to
``plugin/agents/`` instead would publish all 508 library personas as discovered
plugin subagents, which is not what the plugin offers. Discovery scans fixed
names at the plugin ROOT only, so a nested ``snapshot/agents/`` is invisible to
it, which is the property being relied on here.

Windows-safe: ASCII only. Paths are built with pathlib, never with separator
literals.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

DEV_MODE_ENV = "CLAUDE_PLUGIN_DEV_MODE"
LIBRARY_ENV = "CLAUDE_GLOBAL_LIBRARY"
LIBRARY_DIR_NAME = "claude-global-library"

MANIFEST_NAME = "snapshot.json"
MASTER_RELDIR = ("knowledge-graph", "_master")
AGENT_DIR = "agents"
AGENT_FILE = "agent.md"

AGENTS_FILE = "agents_all.json"
SKILLS_FILE = "skills_all.json"
DOMAINS_FILE = "domains_all.json"
EDGES_FILE = "edges_all.json"

AGENT_KEEP_KEYS = (
    "name",
    "primary_home_kg",
    "domain",
    "description",
    "role",
    "role_summary",
    "role_type",
    "model",
    "mandatory_skills",
    "optional_skills",
    "id",
)
SKILL_KEEP_KEYS = ("name", "primary_home_kg", "domain", "description", "id")
DOMAIN_KEEP_KEYS = ("slug", "name", "id")
EDGE_SIDE_KEYS = ("source", "target", "source_id", "target_id")

TOP_LEVEL_KEEP_KEYS = ("library_version", "kg_version", "title")

FORBIDDEN_BUNDLED_NAMES = frozenset({".mcp.json", ".lsp.json"})

DISCOVERED_CAPABILITY_NAMES = frozenset({"commands", "agents", "skills", "hooks", "output-styles", "monitors", "bin"})


class SnapshotError(Exception):
    """Base class for every failure this module raises."""


class DevModeRelease(SnapshotError):
    """Raised when a release-path operation runs with dev mode enabled.

    ADR-007 makes the pinned snapshot the source of routing data. Dev mode
    bypasses the snapshot and resolves the library from a live workspace
    checkout, so an artefact built or published under dev mode carries a
    machine-specific path that does not exist on any user's machine. The flag
    that defeats reproducibility must not be left on by accident, which is why
    this is a hard failure and not a warning.
    """


class LibraryUnavailable(SnapshotError):
    """Raised when the library checkout cannot be located or read."""


def dev_mode_enabled(env=None):
    """Report whether dev mode is enabled in the given environment.

    The flag is read from the environment ONLY. It is deliberately never read
    from a bundled configuration file, so a shipped plugin cannot be switched
    into dev mode by editing a file it carries (ADR-007 guardrail (a)).

    Args:
        env: Mapping to read from. Defaults to ``os.environ``.

    Returns:
        bool: True when the flag is present and not one of the falsey spellings.
    """
    source = os.environ if env is None else env
    raw = source.get(DEV_MODE_ENV)
    if raw is None:
        return False
    return raw.strip().lower() not in ("", "0", "false", "no", "off")


def assert_not_dev_mode(env=None, action="release"):
    """Refuse to proceed when dev mode is set in the environment.

    Args:
        env: Mapping to read from. Defaults to ``os.environ``.
        action: Name of the operation being guarded, used in the message.

    Raises:
        DevModeRelease: When the dev-mode flag is set.
    """
    if dev_mode_enabled(env):
        source = os.environ if env is None else env
        raise DevModeRelease(
            "{0} refused: {1}={2!r} is set in this environment. A dev-mode "
            "build resolves the library from a live workspace checkout instead "
            "of the pinned snapshot, so publishing one would ship routing data "
            "from an unversioned, machine-specific path (ADR-007). Unset "
            "{1} and re-run.".format(action, DEV_MODE_ENV, source.get(DEV_MODE_ENV))
        )


def locate_library_root(explicit=None, engine_root=None):
    """Resolve the claude-global-library checkout.

    Args:
        explicit: Caller-supplied path that wins when given.
        engine_root: Repository root used to find the sibling checkout.

    Returns:
        Path: The resolved library root.

    Raises:
        LibraryUnavailable: When no candidate path contains a VERSION file.
    """
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    from_env = os.environ.get(LIBRARY_ENV, "").strip()
    if from_env:
        candidates.append(Path(from_env))
    root = Path(engine_root) if engine_root else Path(__file__).resolve().parent.parent
    candidates.append(root.parent / LIBRARY_DIR_NAME)

    for candidate in candidates:
        if (candidate / "VERSION").is_file():
            return candidate.resolve()

    raise LibraryUnavailable(
        "cannot locate {0}: none of these carried a VERSION file: {1}".format(
            LIBRARY_DIR_NAME, ", ".join(str(item) for item in candidates)
        )
    )


def read_library_version(library_root):
    """Read the library's VERSION file.

    Args:
        library_root: Path of the library checkout.

    Returns:
        str: The stripped version string.

    Raises:
        LibraryUnavailable: When the file is missing or empty.
    """
    version_file = Path(library_root) / "VERSION"
    try:
        raw = version_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise LibraryUnavailable("cannot read {0}: {1}".format(version_file, exc)) from exc
    if not raw:
        raise LibraryUnavailable("{0} is empty".format(version_file))
    return raw


def _master_path(library_root, name):
    """Return the path of a master catalogue file inside the library."""
    path = Path(library_root)
    for part in MASTER_RELDIR:
        path = path / part
    return path / name


def _read_json(path):
    """Read and parse a JSON file.

    Args:
        path: Path of the file to read.

    Returns:
        The parsed payload.

    Raises:
        LibraryUnavailable: When the file is unreadable or not valid JSON.
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise LibraryUnavailable("cannot read {0}: {1}".format(path, exc)) from exc
    except ValueError as exc:
        raise LibraryUnavailable("{0} is not valid JSON: {1}".format(path, exc)) from exc


def _entries(payload, *keys):
    """Extract the record list from a catalogue payload.

    Args:
        payload: Parsed catalogue payload, a mapping or a bare list.
        keys: Container keys to try in order.

    Returns:
        list: The records, empty when no container matched.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def _project_record(record, keep_keys):
    """Copy only the permitted keys out of one catalogue record."""
    return {key: record[key] for key in keep_keys if key in record}


def _project_container(payload, container_key, records, extra=None):
    """Rebuild a catalogue payload around projected records.

    Args:
        payload: The original payload, read for its top-level metadata.
        container_key: Key the records are stored under.
        records: The projected record list.
        extra: Additional top-level keys to merge in.

    Returns:
        dict: The projected payload.
    """
    out = {}
    if isinstance(payload, dict):
        for key in TOP_LEVEL_KEEP_KEYS:
            if key in payload:
                out[key] = payload[key]
    out[container_key] = records
    if extra:
        out.update(extra)
    return out


def project_agents(payload, dispatchable):
    """Project the agent catalogue down to the fields the loader reads.

    Args:
        payload: Parsed ``agents_all.json``.
        dispatchable: Set of agent names to retain.

    Returns:
        dict: The projected payload.
    """
    records = [
        _project_record(record, AGENT_KEEP_KEYS)
        for record in _entries(payload, "agents", "nodes")
        if isinstance(record, dict) and record.get("name") in dispatchable
    ]
    return _project_container(payload, "agents", records, {"agent_count": len(records)})


def project_skills(payload):
    """Project the skill catalogue down to the fields the loader reads."""
    records = [
        _project_record(record, SKILL_KEEP_KEYS)
        for record in _entries(payload, "skills", "nodes")
        if isinstance(record, dict)
    ]
    return _project_container(payload, "skills", records, {"skill_count": len(records)})


def project_domains(payload):
    """Project the domain catalogue down to the fields the loader reads."""
    records = [
        _project_record(record, DOMAIN_KEEP_KEYS)
        for record in _entries(payload, "domains", "nodes")
        if isinstance(record, dict)
    ]
    return _project_container(payload, "domains", records, {"domain_count": len(records)})


def _edge_prefixes(edge):
    """Return the type-word prefixes one edge record contributes."""
    found = set()
    for side in EDGE_SIDE_KEYS:
        raw = edge.get(side)
        if isinstance(raw, str) and ":" in raw:
            found.add(raw.split(":", 1)[0].strip().lower())
    return found


def project_edges(payload):
    """Keep one representative edge per distinct type-word prefix.

    ``_derive_type_words`` reads this catalogue only to collect the prefix
    appearing before a colon in an endpoint identifier. Retaining one edge per
    distinct prefix therefore yields an identical derived vocabulary at a
    fraction of the size. ``verify_snapshot_fidelity`` checks that equality
    rather than trusting this reasoning.

    Args:
        payload: Parsed ``edges_all.json``.

    Returns:
        dict: The projected payload.
    """
    seen = set()
    kept = []
    for edge in _entries(payload, "edges", "nodes"):
        if not isinstance(edge, dict):
            continue
        prefixes = _edge_prefixes(edge)
        if prefixes - seen:
            seen |= prefixes
            kept.append(_project_record(edge, EDGE_SIDE_KEYS))
    return _project_container(payload, "edges", kept, {"edge_count": len(kept)})


def derive_type_words(payload):
    """Derive the type-word vocabulary exactly as the loader does.

    Args:
        payload: Parsed edge catalogue payload.

    Returns:
        tuple: The observed type words, sorted longest-first.
    """
    words = set()
    for edge in _entries(payload, "edges", "nodes"):
        if isinstance(edge, dict):
            words |= _edge_prefixes(edge)
    return tuple(sorted(words, key=lambda word: (-len(word), word)))


def dispatchable_agents(payload, library_root):
    """Return the agent names whose persona file actually resolves.

    NOTE ON THIS DEFINITION. ADR-007 says the snapshot carries "only the
    personas for dispatchable agents, not all 508 agent directories", but no
    machine-checkable definition of "dispatchable" exists anywhere in this
    repository -- the word appears only in prose. The definition applied here
    is the one the code already enforces: ``catalogue.verify_persona`` treats an
    unresolvable persona path as a hard failure of the dispatch contract, so an
    agent is dispatchable exactly when the selector can return it AND its
    persona resolves. Measured against library 29.73.0 that set is all 508
    agents, so this predicate currently excludes nothing. It is written as a
    filter anyway so the snapshot stays correct if the catalogue ever names an
    agent whose persona is missing.

    Args:
        payload: Parsed ``agents_all.json``.
        library_root: Path of the library checkout.

    Returns:
        tuple: (kept names set, skipped names list).
    """
    root = Path(library_root)
    kept = set()
    skipped = []
    for record in _entries(payload, "agents", "nodes"):
        if not isinstance(record, dict):
            continue
        name = record.get("name")
        if not isinstance(name, str) or not name:
            continue
        if (root / AGENT_DIR / name / AGENT_FILE).is_file():
            kept.add(name)
        else:
            skipped.append(name)
    return kept, skipped


def sha256_of(path):
    """Return the hex sha256 digest of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path, payload):
    """Write a JSON payload deterministically.

    Sorted keys and a fixed separator make the output byte-identical across
    runs, which is what lets a rebuild be compared against a committed
    artefact (ADR-007 reproducibility).

    Args:
        path: Destination path.
        payload: JSON-serialisable payload.

    Returns:
        int: Bytes written.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    Path(path).write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def assert_no_bundled_server_config(snapshot_root):
    """Fail if the snapshot introduced an MCP or LSP configuration file.

    ``scripts/verify_plugin_conformance.py`` walks the WHOLE plugin tree for
    ``.mcp.json`` and treats a hit as CRITICAL under ADR-019. The snapshot
    writes library-sourced content into that tree, so it is a possible route
    for such a file to appear. Library 29.73.0 contains none, measured, but a
    later library revision could add one and it would land here silently.

    Args:
        snapshot_root: Path of the built snapshot.

    Raises:
        SnapshotError: When a forbidden file is present.
    """
    offenders = []
    for dirpath, _dirnames, filenames in os.walk(str(snapshot_root)):
        for name in filenames:
            if name.lower() in FORBIDDEN_BUNDLED_NAMES:
                offenders.append(str(Path(dirpath) / name))
    if offenders:
        raise SnapshotError(
            "snapshot would bundle server configuration, which "
            "verify_plugin_conformance rejects under ADR-019: {0}".format(", ".join(sorted(offenders)))
        )


def assert_not_discovered(snapshot_root, plugin_root):
    """Fail if the snapshot directory is itself a discovered capability name.

    Args:
        snapshot_root: Path of the built snapshot.
        plugin_root: Path of the plugin root.

    Raises:
        SnapshotError: When the snapshot sits at a discovered name.
    """
    relative = Path(snapshot_root).resolve().relative_to(Path(plugin_root).resolve())
    first = relative.parts[0] if relative.parts else ""
    if first.lower() in DISCOVERED_CAPABILITY_NAMES:
        raise SnapshotError(
            "snapshot directory {0!r} is a convention-discovered capability "
            "name; writing personas there would publish every library persona "
            "as a plugin subagent".format(first)
        )


def build_snapshot(library_root, snapshot_root, plugin_root=None, prune=True):
    """Build the pinned snapshot into ``snapshot_root``.

    Args:
        library_root: Path of the library checkout to snapshot.
        snapshot_root: Destination directory, replaced when ``prune`` is set.
        plugin_root: Plugin root used for the discovered-name assertion.
        prune: Remove any existing snapshot first.

    Returns:
        dict: The snapshot manifest that was written.

    Raises:
        LibraryUnavailable: When the library cannot be read.
        SnapshotError: When the built tree violates a plugin constraint.
    """
    library_root = Path(library_root)
    snapshot_root = Path(snapshot_root)
    if plugin_root is not None:
        assert_not_discovered(snapshot_root, plugin_root)

    library_version = read_library_version(library_root)

    agents_payload = _read_json(_master_path(library_root, AGENTS_FILE))
    skills_payload = _read_json(_master_path(library_root, SKILLS_FILE))
    domains_payload = _read_json(_master_path(library_root, DOMAINS_FILE))
    edges_payload = _read_json(_master_path(library_root, EDGES_FILE))

    kept_names, skipped_names = dispatchable_agents(agents_payload, library_root)
    if not kept_names:
        raise LibraryUnavailable(
            "no agent in the catalogue has a resolvable persona; refusing to build an empty snapshot"
        )

    if prune and snapshot_root.exists():
        shutil.rmtree(str(snapshot_root))
    snapshot_root.mkdir(parents=True, exist_ok=True)

    files = {}
    projections = (
        (AGENTS_FILE, project_agents(agents_payload, kept_names)),
        (SKILLS_FILE, project_skills(skills_payload)),
        (DOMAINS_FILE, project_domains(domains_payload)),
        (EDGES_FILE, project_edges(edges_payload)),
    )
    for name, projected in projections:
        destination = _master_path(snapshot_root, name)
        _write_json(destination, projected)
        files[str(Path(*MASTER_RELDIR) / name).replace(os.sep, "/")] = sha256_of(destination)

    persona_bytes = 0
    for name in sorted(kept_names):
        source = library_root / AGENT_DIR / name / AGENT_FILE
        destination = snapshot_root / AGENT_DIR / name / AGENT_FILE
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(source), str(destination))
        persona_bytes += destination.stat().st_size

    assert_no_bundled_server_config(snapshot_root)

    manifest = {
        "schema": 1,
        "library_version": library_version,
        "catalogue_library_version": _catalogue_version(agents_payload),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "built_in_dev_mode": dev_mode_enabled(),
        "agent_count": len(kept_names),
        "skipped_agents": sorted(skipped_names),
        "skill_count": len(_entries(skills_payload, "skills", "nodes")),
        "domain_count": len(_entries(domains_payload, "domains", "nodes")),
        "type_words": list(derive_type_words(edges_payload)),
        "files": files,
        "persona_bytes": persona_bytes,
    }
    _write_json(snapshot_root / MANIFEST_NAME, manifest)
    return manifest


def _catalogue_version(payload):
    """Read the library_version recorded inside a catalogue payload."""
    if isinstance(payload, dict):
        for key in ("library_version", "kg_version"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    return ""


def verify_snapshot_fidelity(library_root, snapshot_root):
    """Check the projection preserved everything the loader reads.

    Compares the agent, skill and domain name sets and the derived type-word
    vocabulary between the library and the snapshot. This is what turns the
    projection from an assertion into a checked property.

    Args:
        library_root: Path of the library checkout.
        snapshot_root: Path of the built snapshot.

    Returns:
        list: Human-readable mismatch descriptions, empty when faithful.
    """
    problems = []
    pairs = (
        (AGENTS_FILE, ("agents", "nodes"), "agent"),
        (SKILLS_FILE, ("skills", "nodes"), "skill"),
        (DOMAINS_FILE, ("domains", "nodes"), "domain"),
    )
    library_agents = _read_json(_master_path(library_root, AGENTS_FILE))
    kept_names, _skipped = dispatchable_agents(library_agents, library_root)

    for name, keys, label in pairs:
        source = _entries(_read_json(_master_path(library_root, name)), *keys)
        target = _entries(_read_json(_master_path(snapshot_root, name)), *keys)
        source_names = {r.get("name") or r.get("slug") for r in source if isinstance(r, dict)}
        target_names = {r.get("name") or r.get("slug") for r in target if isinstance(r, dict)}
        if label == "agent":
            source_names = source_names & kept_names
        if source_names != target_names:
            missing = sorted(x for x in source_names - target_names if x)
            extra = sorted(x for x in target_names - source_names if x)
            problems.append("{0} names differ: missing={1} extra={2}".format(label, missing[:5], extra[:5]))

    source_words = derive_type_words(_read_json(_master_path(library_root, EDGES_FILE)))
    target_words = derive_type_words(_read_json(_master_path(snapshot_root, EDGES_FILE)))
    if source_words != target_words:
        problems.append("type words differ: library={0} snapshot={1}".format(source_words, target_words))

    for name in sorted(kept_names):
        if not (Path(snapshot_root) / AGENT_DIR / name / AGENT_FILE).is_file():
            problems.append("persona missing from snapshot: {0}".format(name))
            break
    return problems


def _tree_bytes(root):
    """Return (total bytes, file count, largest file bytes) for a tree."""
    total = 0
    count = 0
    largest = 0
    for dirpath, _dirnames, filenames in os.walk(str(root)):
        for name in filenames:
            size = (Path(dirpath) / name).stat().st_size
            total += size
            count += 1
            largest = max(largest, size)
    return total, count, largest


def _parse_args(argv):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Build the pinned library snapshot the plugin ships with.")
    parser.add_argument("--library", default=None, help="Path of the claude-global-library checkout.")
    parser.add_argument("--plugin-root", default=None, help="Path of the plugin root. Defaults to <repo>/plugin.")
    parser.add_argument("--out", default=None, help="Snapshot destination. Defaults to <plugin-root>/snapshot.")
    parser.add_argument("--verify", action="store_true", help="Check projection fidelity after building.")
    parser.add_argument(
        "--release",
        action="store_true",
        help="Apply the release gate: refuse to build when {0} is set.".format(DEV_MODE_ENV),
    )
    parser.add_argument(
        "--check-dev-mode",
        action="store_true",
        help="Only assert {0} is unset, then exit. Needs no library.".format(DEV_MODE_ENV),
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Entry point.

    Returns:
        int: 0 on success, 1 on failure.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = Path(__file__).resolve().parent.parent
    plugin_root = Path(args.plugin_root) if args.plugin_root else repo_root / "plugin"
    snapshot_root = Path(args.out) if args.out else plugin_root / "snapshot"

    if args.check_dev_mode:
        try:
            assert_not_dev_mode(action="publish")
        except DevModeRelease as exc:
            print("[BLOCKED] {0}".format(exc))
            return 1
        print("[OK] {0} is not set; publishing may proceed".format(DEV_MODE_ENV))
        return 0

    try:
        if args.release:
            assert_not_dev_mode(action="snapshot build for release")
        library_root = locate_library_root(args.library, repo_root)
        manifest = build_snapshot(library_root, snapshot_root, plugin_root=plugin_root)
    except SnapshotError as exc:
        print("[FAIL] {0}".format(exc))
        return 1

    total, count, largest = _tree_bytes(snapshot_root)
    print("[OK] snapshot built: {0}".format(snapshot_root))
    print("     library VERSION      : {0}".format(manifest["library_version"]))
    print("     catalogue version    : {0}".format(manifest["catalogue_library_version"]))
    print("     agents / skills      : {0} / {1}".format(manifest["agent_count"], manifest["skill_count"]))
    print("     domains / type words : {0} / {1}".format(manifest["domain_count"], len(manifest["type_words"])))
    print("     files / bytes        : {0} / {1}".format(count, total))
    print("     largest single file  : {0} bytes".format(largest))
    if manifest["built_in_dev_mode"]:
        print("     mode                 : dev")

    if args.verify:
        problems = verify_snapshot_fidelity(library_root, snapshot_root)
        if problems:
            for problem in problems:
                print("[FAIL] fidelity: {0}".format(problem))
            return 1
        print("[OK] fidelity verified: names and type words match the library")
    return 0


if __name__ == "__main__":
    sys.exit(main())
