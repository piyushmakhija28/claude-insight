"""Maps observed processes onto components, which is what NFR-1 actually requires.

The revised NFR-1 criterion is per component: pass means zero processes attributable to
the plugin, not zero processes overall. Attribution is therefore the measurement, not a
presentation detail layered over it.

Three attribution bases are distinguished and always reported, because they carry
different strength:

    direct      The process's own image name, executable path or command line matched a
                component marker. Strongest.
    ancestry    The process matched nothing, but an ancestor did, so the spawn is
                charged to whichever component launched the chain. This is what catches
                a component that shells out to git or python, where the child's command
                line names only the tool.
    none        Nothing matched, anywhere up the chain. Reported as its own bucket and
                never silently discarded.

An unattributed process makes the measurement INDETERMINATE rather than a pass. The
harness cannot demonstrate that a process it failed to identify does not belong to the
plugin, and reporting a pass on that basis would be the difference between a check and
a no-op. The same applies to a process whose command line the operating system refused
to disclose, which is a real occurrence on Windows for processes owned by other users.

NOT KNOWING AND HAVING PROVED ARE DIFFERENT THINGS
--------------------------------------------------
That conservative rule was applied to every process nothing matched, which conflated two
situations that carry opposite weight. A live measurement on a working machine showed why
it matters: unrelated software -- a browser, somebody's dev server -- can never be
attributed to any declared component, so `unattributed > 0` held permanently and NFR-1
could never reach a verdict however good the measurement was.

But a process whose ancestry was walked back to something that already existed BEFORE the
measurement window opened, with every hop present and readable and no plugin marker
anywhere on the chain, has been **shown** not to descend from the plugin. That is
evidence, not ignorance.

The baseline, not "a root", is what terminates the proof, and the distinction is
load-bearing. A parent pid the backend withheld reads as absent, and a chain almost always
ends at a parent that exited and so is in no snapshot -- neither is a root, and treating
either as one would manufacture proof out of missing data. Reaching a process that
predates the window is different: NFR-1 counts what the plugin spawned DURING the window,
so a pre-existing non-plugin ancestor settles the question for everything below it.

Proof therefore requires a baseline to be supplied. Callers that pass none get no proof
and the old conservative behaviour, so nothing silently becomes provable.

The two are reported separately and only the unknown one forces INDETERMINATE. This cannot
make NFR-1 unfailable: a plugin-spawned process has a plugin ancestor by construction, so a
walk that reaches the baseline without finding one proves the process is not the plugin's.
The proof rests entirely on plugin markers being able to match at all -- see REVIEW-INDEX
correction 58 for the release in which they could not, and the tests that now pin it.
"""

from . import components

BASIS_DIRECT = "direct"
BASIS_ANCESTRY = "ancestry"
BASIS_NONE = "none"

WALK_MATCHED = "matched"
WALK_REACHED_BASELINE = "reached_baseline"
WALK_BROKEN_CHAIN = "broken_chain"
WALK_DEPTH_EXCEEDED = "depth_exceeded"
WALK_CYCLE = "cycle"
WALK_UNPROVEN = "terminated_but_a_hop_was_unreadable"

UNATTRIBUTED_KEY = "__unattributed__"
NOT_PLUGIN_DESCENDED_KEY = "__not_plugin_descended__"
NON_COMPONENT_KEYS = frozenset({UNATTRIBUTED_KEY, NOT_PLUGIN_DESCENDED_KEY})


class Attribution(object):
    """The outcome of attributing one process to one component.

    Attributes:
        record: The ProcessRecord attributed.
        component_key: Component key, or UNATTRIBUTED_KEY.
        role: The component's role, or None when unattributed.
        basis: One of BASIS_DIRECT, BASIS_ANCESTRY, BASIS_NONE.
        marker: The marker string that produced the match, or None.
        via_pid: For ancestry attribution, the ancestor pid that matched.
        reason: Short explanation, populated when attribution failed.
    """

    __slots__ = ("record", "component_key", "role", "basis", "marker", "via_pid", "reason")

    def __init__(self, record, component_key, role, basis, marker=None, via_pid=None, reason=""):
        self.record = record
        self.component_key = component_key
        self.role = role
        self.basis = basis
        self.marker = marker
        self.via_pid = via_pid
        self.reason = reason

    @property
    def is_attributed(self):
        """Return True when this process was mapped onto a known component.

        Both non-component outcomes are excluded: a process proved not to descend from
        the plugin is still not attributed to anything, it is merely no longer unknown.
        """
        return self.component_key not in NON_COMPONENT_KEYS

    def to_dict(self):
        """Return a JSON-serialisable view of this attribution."""
        return {
            "process": self.record.to_dict(),
            "component": self.component_key,
            "role": self.role,
            "basis": self.basis,
            "marker": self.marker,
            "via_pid": self.via_pid,
            "reason": self.reason,
        }


class AttributionResult(object):
    """Per-component attribution of one set of observed processes.

    Attributes:
        attributions: List of Attribution, one per observed process.
        registry: The ComponentRegistry used.
    """

    def __init__(self, attributions, registry):
        self.attributions = list(attributions)
        self.registry = registry

    def by_component(self):
        """Return a mapping of component key to the attributions charged to it."""
        buckets = {spec.key: [] for spec in self.registry}
        buckets[UNATTRIBUTED_KEY] = []
        for attribution in self.attributions:
            buckets.setdefault(attribution.component_key, []).append(attribution)
        return buckets

    def counts(self):
        """Return a mapping of component key to attributed process count."""
        return {key: len(items) for key, items in self.by_component().items()}

    def count_for_role(self, role):
        """Return how many processes were attributed to components holding a role.

        Args:
            role: One of components.VALID_ROLES.

        Returns:
            Integer count.
        """
        keys = set(self.registry.keys_with_role(role))
        return sum(1 for a in self.attributions if a.component_key in keys)

    @property
    def plugin_count(self):
        """Return the process count that decides the NFR-1 verdict."""
        return self.count_for_role(components.ROLE_PLUGIN_COUNTED)

    @property
    def excluded_count(self):
        """Return the process count charged to the single permitted exclusion."""
        return self.count_for_role(components.ROLE_PERMITTED_EXCLUSION)

    @property
    def unattributed(self):
        """Return every process whose relationship to the plugin is genuinely unknown.

        This is the bucket that forces INDETERMINATE, so it deliberately excludes
        processes proved not to descend from the plugin. Widening it back to "everything
        that matched no component" would make the verdict unreachable on any machine
        running unrelated software.
        """
        return [a for a in self.attributions if a.component_key == UNATTRIBUTED_KEY]

    @property
    def not_plugin_descended(self):
        """Return processes whose ancestry was walked to a root with no plugin on it."""
        return [a for a in self.attributions if a.component_key == NOT_PLUGIN_DESCENDED_KEY]

    @property
    def access_denied_count(self):
        """Return how many processes the operating system refused to describe."""
        return sum(1 for a in self.attributions if a.record.access_denied)

    def to_dict(self):
        """Return a JSON-serialisable summary, listing unattributed processes in full."""
        return {
            "observed_process_count": len(self.attributions),
            "counts_by_component": self.counts(),
            "plugin_attributable_count": self.plugin_count,
            "permitted_exclusion_count": self.excluded_count,
            "unattributed_count": len(self.unattributed),
            "not_plugin_descended_count": len(self.not_plugin_descended),
            "access_denied_count": self.access_denied_count,
            "unattributed_processes": [a.to_dict() for a in self.unattributed],
            "attribution_bases": {
                BASIS_DIRECT: sum(1 for a in self.attributions if a.basis == BASIS_DIRECT),
                BASIS_ANCESTRY: sum(1 for a in self.attributions if a.basis == BASIS_ANCESTRY),
                BASIS_NONE: sum(1 for a in self.attributions if a.basis == BASIS_NONE),
            },
        }


def _match_role(registry, record, role=None):
    """Return the first component that matches a record directly, optionally role-filtered.

    This is the shared primitive behind plugin-first precedence: attribute() calls it
    twice, once restricted to components.ROLE_PLUGIN_COUNTED before anything else is
    considered, and again unrestricted as part of the pre-existing first-match-wins
    fallback. A single implementation keeps both call sites honest about registration
    order rather than letting a role-filtered copy drift from the general one.

    Args:
        registry: ComponentRegistry to search, in registration order.
        record: ProcessRecord to test.
        role: Restrict the search to components carrying this role, or None to search
            every component regardless of role.

    Returns:
        Tuple of (ComponentSpec, marker), or (None, None).
    """
    for spec in registry:
        if role is not None and spec.role != role:
            continue
        marker = spec.matches(record)
        if marker is not None:
            return spec, marker
    return None, None


def _direct_match(registry, record):
    """Return the first component that matches a record directly, any role.

    Args:
        registry: ComponentRegistry to search, in registration order.
        record: ProcessRecord to test.

    Returns:
        Tuple of (ComponentSpec, marker), or (None, None).
    """
    return _match_role(registry, record)


def identity_is_readable(record):
    """Return whether enough of a process's own identity was captured to judge it.

    The proof below is a statement about ANCESTRY. It says nothing about the process
    itself, so it may only be granted when the process's own identity was actually read.
    A process observed with no command line and no executable path might BE the plugin;
    granting it a clean-ancestry proof would convert a momentary failure to read into a
    finding of innocence.

    That is not hypothetical. The harness's own self-test spawns a marked child and
    requires the verdict to be FAIL. It returned PASS once, with the marked child neither
    charged to the plugin nor reported as unknown -- the shape this guard prevents.

    The image name alone is not enough. A plugin entry point runs as python.exe like
    everything else here; the marker lives in the command line or the executable path.

    Args:
        record: ProcessRecord to judge.

    Returns:
        True when the process's own identity can be assessed.
    """
    if record.access_denied:
        return False
    return bool(record.cmdline) or bool(record.exe)


def _parent_can_predate_child(parent, child):
    """Return whether a candidate parent could have spawned a child, by creation order.

    Ancestry has only a bare parent pid to follow, and operating systems reuse pids. The
    index entry for a pid may therefore be a LATER process that inherited the number
    after the real parent exited, which would send the walk up a chain that never
    existed. A process cannot be spawned by something created after it, so comparing
    creation order rejects that case.

    Returns True when the ordering cannot be compared at all, because refusing every
    unorderable hop would disable ancestry matching entirely on a backend whose creation
    tokens are not numeric. The walk records that the hop was unverified instead, which
    is what downgrades a root-reaching walk from proof to merely unmatched.

    Args:
        parent: Candidate ancestor ProcessRecord.
        child: ProcessRecord whose ppid named the candidate.

    Returns:
        Tuple of (could_be_parent, order_was_verifiable).
    """
    try:
        return float(parent.create_token) <= float(child.create_token), True
    except (TypeError, ValueError):
        return True, False


def _walk_ancestry(record, registry, index, max_ancestry_depth, role=None, baseline_pids=None):
    """Walk a process's ancestor chain looking for a component match.

    The cycle guard (seen_pids plus max_ancestry_depth) is shared by both the
    plugin-first walk and the pre-existing any-role fallback walk in attribute(), so a
    parent chain that loops back on itself terminates identically for either search.

    An ancestor the operating system refused to describe does NOT stop the walk. Its
    markers cannot be read, so it cannot produce a match, but a plugin marker may sit
    ABOVE it and finding that is the safe direction to err in -- stopping there would
    under-report the very thing NFR-1 counts. It does mean the chain can no longer prove
    anything, so it clears the provable flag and the walk continues.

    The returned outcome says WHY the walk stopped, which is what lets a caller tell a
    chain that finished cleanly without matching from one that could not be followed.
    Those two produce the same absence of a match and mean opposite things.

    Args:
        record: ProcessRecord whose ppid starts the walk.
        registry: ComponentRegistry to search at each ancestor.
        index: Mapping of pid to ProcessRecord used to resolve each ancestor.
        max_ancestry_depth: Guard against a cyclic or self-referential parent chain.
        role: Restrict matches to components carrying this role, or None for any role.
        baseline_pids: Pids observed before the measurement window opened. Reaching one
            is what allows a proof; pass None to disable proof entirely.

    Returns:
        Tuple of (ComponentSpec, marker, ancestor_pid, outcome), where outcome is one of
        the WALK_* constants. spec/marker/pid are None unless outcome is WALK_MATCHED.
    """
    seen_pids = set()
    cursor = record.ppid
    child = record
    depth = 0
    provable = True
    while True:
        if cursor is None:
            return None, None, None, WALK_BROKEN_CHAIN
        if depth >= max_ancestry_depth:
            return None, None, None, WALK_DEPTH_EXCEEDED
        if cursor in seen_pids:
            return None, None, None, WALK_CYCLE
        seen_pids.add(cursor)
        ancestor = index.get(cursor)
        if ancestor is None:
            return None, None, None, WALK_BROKEN_CHAIN
        could_be_parent, verifiable = _parent_can_predate_child(ancestor, child)
        if not could_be_parent:
            return None, None, None, WALK_BROKEN_CHAIN
        if not verifiable:
            provable = False
        if ancestor.access_denied:
            provable = False
        else:
            anc_spec, anc_marker = _match_role(registry, ancestor, role)
            if anc_spec is not None:
                return anc_spec, anc_marker, cursor, WALK_MATCHED
        if baseline_pids is not None and cursor in baseline_pids:
            return None, None, None, WALK_REACHED_BASELINE if provable else WALK_UNPROVEN
        child = ancestor
        cursor = ancestor.ppid
        depth += 1


def attribute(records, registry, ancestry_index=None, max_ancestry_depth=12, baseline_pids=None):
    """Attribute observed processes to components.

    Plugin attribution is resolved first, against the process itself and its full
    ancestor chain, before any other component's direct match is considered. Without
    this precedence a broad marker on a lower-priority component (typically an OBSERVED
    one, since those carry no cardinality cap) can direct-match a plugin-spawned child
    before the ancestry walk that would otherwise have charged it to the plugin ever
    runs, silently making the plugin unfailable through a role nothing guards. Only
    when no plugin marker matches the process or any ancestor does the pre-existing
    first-match-wins search over every component, direct then ancestry, run.

    Args:
        records: Iterable of ProcessRecord to attribute.
        registry: ComponentRegistry defining components and roles.
        ancestry_index: Optional mapping of pid to ProcessRecord used to walk parent
            chains. Pass the full snapshot record map keyed by pid so that a child
            whose own command line names only `git` can still be charged to whichever
            component launched it.
        max_ancestry_depth: Guard against a cyclic or self-referential parent chain.
        baseline_pids: Pids present before the measurement window opened. Reaching one
            with a clean chain and no plugin marker is what proves a process does not
            descend from the plugin. Omit it and no process is ever proved, which is
            the conservative default every existing caller keeps.

    Returns:
        AttributionResult.
    """
    index = ancestry_index or {}
    results = []
    for record in records:
        plugin_spec, plugin_marker = _match_role(registry, record, components.ROLE_PLUGIN_COUNTED)
        if plugin_spec is not None:
            results.append(Attribution(record, plugin_spec.key, plugin_spec.role, BASIS_DIRECT, plugin_marker))
            continue

        plugin_anc_spec, plugin_anc_marker, plugin_anc_pid, plugin_walk = _walk_ancestry(
            record,
            registry,
            index,
            max_ancestry_depth,
            components.ROLE_PLUGIN_COUNTED,
            baseline_pids,
        )
        if plugin_anc_spec is not None:
            results.append(
                Attribution(
                    record,
                    plugin_anc_spec.key,
                    plugin_anc_spec.role,
                    BASIS_ANCESTRY,
                    plugin_anc_marker,
                    plugin_anc_pid,
                )
            )
            continue

        spec, marker = _direct_match(registry, record)
        if spec is not None:
            results.append(Attribution(record, spec.key, spec.role, BASIS_DIRECT, marker))
            continue

        anc_spec, anc_marker, anc_pid, _ = _walk_ancestry(record, registry, index, max_ancestry_depth)
        if anc_spec is not None:
            results.append(Attribution(record, anc_spec.key, anc_spec.role, BASIS_ANCESTRY, anc_marker, anc_pid))
            continue

        if record.access_denied:
            reason = (
                "operating system withheld the command line and executable path, so the "
                "process cannot be shown to not belong to the plugin"
            )
        elif plugin_walk == WALK_REACHED_BASELINE and not identity_is_readable(record):
            reason = (
                "could not be attributed: ancestry reached the baseline cleanly, but the "
                "process's own command line and executable path were both unavailable, so "
                "it cannot be shown that this process is not itself the plugin"
            )
        elif plugin_walk == WALK_REACHED_BASELINE:
            results.append(
                Attribution(
                    record,
                    NOT_PLUGIN_DESCENDED_KEY,
                    None,
                    BASIS_NONE,
                    reason=(
                        "ancestry walked back to a process that predates the measurement "
                        "window, every hop present and readable, with no plugin marker on "
                        "the chain, so the process is shown not to descend from the plugin"
                    ),
                )
            )
            continue
        else:
            reason = (
                "could not be attributed: plugin ancestry was neither established nor "
                "ruled out, because the walk ended %s" % plugin_walk
            )
        results.append(Attribution(record, UNATTRIBUTED_KEY, None, BASIS_NONE, reason=reason))
    return AttributionResult(results, registry)


def build_ancestry_index(snapshot):
    """Build a pid-keyed index for ancestry walking.

    A snapshot is keyed by (pid, create_token) so that process-identifier reuse cannot
    conflate two processes. Ancestry walking has only a bare parent pid to work with,
    so this collapses the key. Where reuse has produced two entries for one pid the
    most recently created one wins, which is the correct choice for a parent observed
    during the measurement window.

    Args:
        snapshot: Snapshot to index.

    Returns:
        Mapping of pid to ProcessRecord.
    """
    return index_from_records(snapshot.records.values())


def index_from_records(records):
    """Build a pid-keyed ancestry index from any iterable of ProcessRecord.

    The sampler observes short-lived processes that appear in neither endpoint snapshot,
    including the short-lived PARENTS of other short-lived processes. Indexing only the
    endpoints therefore left those chains broken at the first hop, which is why a live
    window reported 63 processes as unknown when all 63 carried a usable parent pid.

    Args:
        records: Iterable of ProcessRecord.

    Returns:
        Mapping of pid to ProcessRecord, most recently created winning on reuse.
    """
    index = {}
    for record in records:
        existing = index.get(record.pid)
        if existing is None or record.create_token > existing.create_token:
            index[record.pid] = record
    return index
