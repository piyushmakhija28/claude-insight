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
"""

from . import components

BASIS_DIRECT = "direct"
BASIS_ANCESTRY = "ancestry"
BASIS_NONE = "none"

UNATTRIBUTED_KEY = "__unattributed__"


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
        """Return True when this process was mapped onto a known component."""
        return self.component_key != UNATTRIBUTED_KEY

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
        """Return every attribution that could not be mapped to a component."""
        return [a for a in self.attributions if not a.is_attributed]

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
            "access_denied_count": self.access_denied_count,
            "unattributed_processes": [a.to_dict() for a in self.unattributed],
            "attribution_bases": {
                BASIS_DIRECT: sum(1 for a in self.attributions if a.basis == BASIS_DIRECT),
                BASIS_ANCESTRY: sum(1 for a in self.attributions if a.basis == BASIS_ANCESTRY),
                BASIS_NONE: sum(1 for a in self.attributions if a.basis == BASIS_NONE),
            },
        }


def _direct_match(registry, record):
    """Return the first component that matches a record directly.

    Args:
        registry: ComponentRegistry to search, in registration order.
        record: ProcessRecord to test.

    Returns:
        Tuple of (ComponentSpec, marker), or (None, None).
    """
    for spec in registry:
        marker = spec.matches(record)
        if marker is not None:
            return spec, marker
    return None, None


def attribute(records, registry, ancestry_index=None, max_ancestry_depth=12):
    """Attribute observed processes to components.

    Args:
        records: Iterable of ProcessRecord to attribute.
        registry: ComponentRegistry defining components and roles.
        ancestry_index: Optional mapping of pid to ProcessRecord used to walk parent
            chains. Pass the full snapshot record map keyed by pid so that a child
            whose own command line names only `git` can still be charged to whichever
            component launched it.
        max_ancestry_depth: Guard against a cyclic or self-referential parent chain.

    Returns:
        AttributionResult.
    """
    index = ancestry_index or {}
    results = []
    for record in records:
        spec, marker = _direct_match(registry, record)
        if spec is not None:
            results.append(Attribution(record, spec.key, spec.role, BASIS_DIRECT, marker))
            continue

        attributed = None
        seen_pids = set()
        cursor = record.ppid
        depth = 0
        while cursor is not None and depth < max_ancestry_depth and cursor not in seen_pids:
            seen_pids.add(cursor)
            ancestor = index.get(cursor)
            if ancestor is None:
                break
            anc_spec, anc_marker = _direct_match(registry, ancestor)
            if anc_spec is not None:
                attributed = Attribution(record, anc_spec.key, anc_spec.role, BASIS_ANCESTRY, anc_marker, cursor)
                break
            cursor = ancestor.ppid
            depth += 1

        if attributed is not None:
            results.append(attributed)
            continue

        if record.access_denied:
            reason = (
                "operating system withheld the command line and executable path, so the "
                "process cannot be shown to not belong to the plugin"
            )
        else:
            reason = "no component marker matched the process or any ancestor"
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
    index = {}
    for record in snapshot.records.values():
        existing = index.get(record.pid)
        if existing is None or record.create_token > existing.create_token:
            index[record.pid] = record
    return index
