"""Domain knowledge-graph reader (FR-10a, ADR-015).

The 100 per-domain graphs are not schema-uniform. A census of every
``knowledge-graph/{slug}/relationships.json`` in library 29.73.0 returns six
distinct shapes, measured here rather than quoted:

======================  ====================  =========
container key           edge-type key         domains
======================  ====================  =========
bare list               ``type``              58
``edges``               ``type``              23
bare list               ``edge_type``         7
``relationships``       ``type``              7
``edges``               ``edge_type``         3
bare list               ``relationship_type`` 2
======================  ====================  =========

A reader that accepts only ``edges`` silently discards the 486 edges held by
the seven ``relationships``-container domains and reports a clean no-match.
That failure is indistinguishable from a domain that genuinely has nothing to
offer, which is the conflation this module exists to prevent. Hence the return
type: a read either yields :class:`Parsed` with at least one edge, or a typed
:class:`ParseError`. There is no third outcome and no empty-success variant.

Endpoints drift too. Some graphs write ``source``/``target``, some write
``source_id``/``target_id``, one domain writes both, and two domains identify
their nodes only by opaque domain-local codes (``A001``, ``S013``) that resolve
through that domain's own ``agents.json`` and ``skills.json``. Without that
alias step, 12 of the library's 508 agents have no resolvable edge at all and
could never be selected; with it, all 508 are reachable.

Windows-safe: ASCII only.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union

from ..library.resolver import LibrarySetupError, ResourceResolver, build_default_resolver
from .catalogue import LibraryCatalogue
from .ids import candidate_refs, normalise_ref

MALFORMED_JSON = "malformed_json"
UNRECOGNISED_CONTAINER = "unrecognised_container"
UNRECOGNISED_EDGE_TYPE_KEY = "unrecognised_edge_type_key"
UNRESOLVABLE_PATH = "unresolvable_path"

CONTAINER_BARE = "bare"
CONTAINER_EDGES = "edges"
CONTAINER_RELATIONSHIPS = "relationships"

_CONTAINER_KEYS: Tuple[str, ...] = (CONTAINER_EDGES, CONTAINER_RELATIONSHIPS)
_EDGE_TYPE_KEYS: Tuple[str, ...] = ("type", "relationship_type", "edge_type")
_SOURCE_KEYS: Tuple[str, ...] = ("source", "source_id")
_TARGET_KEYS: Tuple[str, ...] = ("target", "target_id")
_NODE_FILES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("agents.json", ("agents", "nodes")),
    ("skills.json", ("skills", "nodes")),
)


@dataclass(frozen=True)
class KgEdge:
    """One resolved knowledge-graph edge.

    Attributes:
        source: Normalised source slug, or the raw reference when it could not
            be resolved to a catalogue node.
        target: Normalised target slug, or the raw reference when unresolved.
        edge_type: Relationship type exactly as the graph records it.
        source_kind: ``"agent"``, ``"skill"``, ``"domain"`` or ``None``.
        target_kind: ``"agent"``, ``"skill"``, ``"domain"`` or ``None``.
        domain: Slug of the domain graph this edge was read from.
    """

    source: str
    target: str
    edge_type: str
    source_kind: Optional[str]
    target_kind: Optional[str]
    domain: str


@dataclass(frozen=True)
class Parsed:
    """A successfully read domain graph.

    The container form and edge-type key are carried so that observability and
    conformance tests can assert on which shape was taken, rather than only on
    the edge count.

    Attributes:
        domain: Domain slug.
        edges: Resolved edges. Guaranteed non-empty by construction.
        container_form: ``"bare"``, ``"edges"`` or ``"relationships"``.
        edge_type_key: The key the payload used to record relationship type.
        alias_count: Number of domain-local opaque identifiers resolved.
    """

    domain: str
    edges: Tuple[KgEdge, ...]
    container_form: str
    edge_type_key: str
    alias_count: int


@dataclass(frozen=True)
class ParseError:
    """A domain graph that could not be read.

    Attributes:
        domain: Domain slug.
        path: Library-relative path that was attempted.
        failure_kind: One of the four module-level failure constants.
        detail: Human-readable cause, including decoder position where known.
    """

    domain: str
    path: str
    failure_kind: str
    detail: str


DomainEdges = Union[Parsed, ParseError]


def _unwrap(payload: Any, keys: Sequence[str]) -> Optional[Sequence[Any]]:
    """Return the record list from a bare-list or single-key mapping payload.

    Returns ``None`` when no accepted shape is present, which callers must
    convert to a typed error rather than to an empty list.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return candidate
    return None


def _first_present(record: Mapping[str, Any], keys: Sequence[str]) -> Optional[str]:
    """Return the first key in ``keys`` that ``record`` actually carries."""
    for key in keys:
        if key in record:
            return key
    return None


class DomainKgAdapter:
    """Reads one domain graph at a time and resolves its endpoints.

    The adapter never reaches for the master edge file to answer a per-domain
    query: ADR-015's contract is that the per-domain graphs are authoritative
    and their divergent shapes are handled, not routed around.
    """

    def __init__(self, catalogue: LibraryCatalogue, resolver: Optional[ResourceResolver] = None):
        """Bind the adapter to a catalogue and a resource resolver.

        Args:
            catalogue: Naming authority used to classify edge endpoints.
            resolver: ADR-1 resource resolver. Built from the default chain
                when omitted.
        """
        self._catalogue = catalogue
        self._resolver = resolver or build_default_resolver()
        self._cache: Dict[str, DomainEdges] = {}

    def read_domain(self, domain: str) -> DomainEdges:
        """Read and resolve one domain's relationship graph.

        Args:
            domain: Domain slug as it appears in the master domain catalogue.

        Returns:
            :class:`Parsed` with at least one edge, or :class:`ParseError`.
            Never a successful result carrying an empty edge list -- see the
            structural invariants in the module docstring.
        """
        if domain in self._cache:
            return self._cache[domain]
        result = self._read_domain_uncached(domain)
        self._cache[domain] = result
        return result

    def _read_domain_uncached(self, domain: str) -> DomainEdges:
        """Perform the four-step read for ``domain`` with no cache consultation."""
        relpath = "knowledge-graph/{}/relationships.json".format(domain)

        try:
            resource = self._resolver.fetch_kg_file(relpath)
        except LibrarySetupError as exc:
            return ParseError(domain, relpath, UNRESOLVABLE_PATH, str(exc))

        try:
            payload = json.loads(resource.content)
        except ValueError as exc:
            return ParseError(domain, relpath, MALFORMED_JSON, str(exc))

        raw_edges = _unwrap(payload, _CONTAINER_KEYS)
        if raw_edges is None:
            shape = sorted(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
            return ParseError(
                domain,
                relpath,
                UNRECOGNISED_CONTAINER,
                "no accepted container among {}; payload shape {}".format(list(_CONTAINER_KEYS) + ["bare list"], shape),
            )

        if isinstance(payload, list):
            container_form = CONTAINER_BARE
        elif isinstance(payload.get(CONTAINER_EDGES), list):
            container_form = CONTAINER_EDGES
        else:
            container_form = CONTAINER_RELATIONSHIPS

        edge_type_key = None
        for record in raw_edges:
            if isinstance(record, dict):
                edge_type_key = _first_present(record, _EDGE_TYPE_KEYS)
                if edge_type_key:
                    break
        if edge_type_key is None:
            return ParseError(
                domain,
                relpath,
                UNRECOGNISED_EDGE_TYPE_KEY,
                "no edge in {} records carries any of {}".format(len(raw_edges), list(_EDGE_TYPE_KEYS)),
            )

        aliases = self._domain_aliases(domain)
        edges, alias_hits = self._resolve_edges(domain, raw_edges, edge_type_key, aliases)

        if not edges:
            return ParseError(
                domain,
                relpath,
                UNRECOGNISED_EDGE_TYPE_KEY,
                "container '{}' held {} records but none yielded a usable endpoint pair".format(
                    container_form, len(raw_edges)
                ),
            )

        return Parsed(
            domain=domain,
            edges=tuple(edges),
            container_form=container_form,
            edge_type_key=edge_type_key,
            alias_count=alias_hits,
        )

    def _resolve_edges(
        self,
        domain: str,
        raw_edges: Sequence[Any],
        edge_type_key: str,
        aliases: Mapping[str, str],
    ) -> Tuple[list, int]:
        """Turn raw edge records into resolved :class:`KgEdge` values.

        Records missing an endpoint pair are skipped rather than fabricated; a
        domain in which every record is unusable falls through to a typed error
        in the caller.
        """
        resolved = []
        alias_hits = 0
        for record in raw_edges:
            if not isinstance(record, dict):
                continue
            source_key = _first_present(record, _SOURCE_KEYS)
            target_key = _first_present(record, _TARGET_KEYS)
            if source_key is None or target_key is None:
                continue
            edge_type = record.get(edge_type_key) or _first_value(record, _EDGE_TYPE_KEYS)
            if not isinstance(edge_type, str) or not edge_type.strip():
                continue

            source, source_kind, source_aliased = self._resolve_endpoint(record.get(source_key), aliases)
            target, target_kind, target_aliased = self._resolve_endpoint(record.get(target_key), aliases)
            if not source or not target:
                continue
            alias_hits += int(source_aliased) + int(target_aliased)

            resolved.append(
                KgEdge(
                    source=source,
                    target=target,
                    edge_type=edge_type.strip(),
                    source_kind=source_kind,
                    target_kind=target_kind,
                    domain=domain,
                )
            )
        return resolved, alias_hits

    def _resolve_endpoint(self, raw: Any, aliases: Mapping[str, str]) -> Tuple[str, Optional[str], bool]:
        """Resolve one endpoint reference to a catalogue slug and node kind.

        Resolution order is deliberate. The reference as written is checked
        first, so a skill whose real name begins with a type word is not
        truncated into a slug that matches nothing. Only then are typed
        prefixes removed, and only then is the domain-local alias table
        consulted.

        Returns:
            A ``(slug, kind, used_alias)`` triple. ``kind`` is ``None`` when the
            reference names something outside the three catalogues -- a tool,
            a regulation or a cross-domain marker -- in which case the folded
            reference is still returned so the edge remains inspectable.
        """
        for candidate in candidate_refs(raw, self._catalogue.type_words):
            kind = self._catalogue.kind_of(candidate)
            if kind is not None:
                return candidate, kind, False

        if isinstance(raw, str):
            aliased = aliases.get(raw.strip().lower())
            if aliased:
                kind = self._catalogue.kind_of(aliased)
                if kind is not None:
                    return aliased, kind, True

        folded = normalise_ref(raw)
        return folded, None, False

    def _domain_aliases(self, domain: str) -> Mapping[str, str]:
        """Build the opaque-identifier alias table for one domain.

        Two of the 100 domains identify their nodes only by codes such as
        ``A001`` and ``S013``. Those codes are meaningful solely within the
        domain's own ``agents.json`` and ``skills.json``, so the table is built
        per domain and never shared across them.

        Returns:
            A mapping from lower-cased raw identifier to catalogue slug. Empty
            when the node files are absent or unreadable, which is not an
            error: most domains use catalogue-resolvable references directly
            and need no aliases at all.
        """
        aliases: Dict[str, str] = {}
        for filename, keys in _NODE_FILES:
            relpath = "knowledge-graph/{}/{}".format(domain, filename)
            try:
                resource = self._resolver.fetch_kg_file(relpath)
                payload = json.loads(resource.content)
            except (LibrarySetupError, ValueError):
                continue
            records = _unwrap(payload, keys)
            if records is None:
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue
                raw_id = record.get("id")
                name = normalise_ref(record.get("name"))
                if isinstance(raw_id, str) and name and self._catalogue.kind_of(name) is not None:
                    aliases[raw_id.strip().lower()] = name
        return aliases


def _first_value(record: Mapping[str, Any], keys: Sequence[str]) -> Optional[Any]:
    """Return the first present value among ``keys``, or ``None``."""
    for key in keys:
        if key in record:
            return record[key]
    return None
