"""The library catalogue -- the only naming authority on the selection path.

Loads ``knowledge-graph/_master/agents_all.json``, ``skills_all.json`` and
``domains_all.json`` through the ADR-1 resource resolver. Every agent name,
skill name and domain slug the selector can ever emit originates here, which is
what makes SRS FR-22's "zero name literals" property achievable rather than
merely aspirational.

Two facts about the catalogue were measured against library 29.73.0 and shape
the design:

* The three name spaces are disjoint -- no name is both an agent and a skill,
  and no domain slug collides with either. Node kind can therefore be decided
  by membership alone, with no reliance on an identifier prefix.
* ``path`` is present on only 295 of 508 agent records and 607 of 996 skill
  records, so it cannot be the source of the dispatch contract's persona path.
  The conventional location ``agents/{name}/agent.md`` was verified to hold for
  all 508 agents on disk, and for every record that does declare a ``path`` the
  declared value equals the conventional one. Persona paths are therefore
  derived and then confirmed against the resolver.

Windows-safe: ASCII only.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..library.resolver import LibrarySetupError, ResourceResolver, build_default_resolver
from .ids import normalise_ref

_AGENTS_RELPATH = "knowledge-graph/_master/agents_all.json"
_SKILLS_RELPATH = "knowledge-graph/_master/skills_all.json"
_DOMAINS_RELPATH = "knowledge-graph/_master/domains_all.json"
_EDGES_RELPATH = "knowledge-graph/_master/edges_all.json"

_AGENT_DIR = "agents"
_SKILL_DIR = "skills"
_AGENT_FILE = "agent.md"
_SKILL_FILE = "SKILL.md"

_KIND_AGENT = "agent"
_KIND_SKILL = "skill"
_KIND_DOMAIN = "domain"


class CatalogueUnavailable(Exception):
    """Raised when a master catalogue cannot be read or is not the expected shape.

    Deliberately not caught-and-emptied anywhere in this package: an
    unreadable catalogue must not be indistinguishable from a library that
    happens to contain no agents.
    """


@dataclass(frozen=True)
class AgentRecord:
    """One agent as the master catalogue describes it.

    Attributes:
        name: Canonical hyphenated slug, also the on-disk directory name.
        domain: Primary home knowledge graph for this agent.
        description: Catalogue prose, empty for the records that omit it.
        role: Short role line, empty for the records that omit it.
        model: Model tier recorded for the agent.
        mandatory_skills: Skill slugs the record declares as mandatory.
        optional_skills: Skill slugs the record declares as optional.
        persona_relpath: Library-relative path the persona block is lifted from.
    """

    name: str
    domain: str
    description: str
    role: str
    model: str
    mandatory_skills: Tuple[str, ...]
    optional_skills: Tuple[str, ...]
    persona_relpath: str

    @property
    def profile_text(self) -> str:
        """Return the concatenated prose used for lexical scoring."""
        return " ".join((self.name.replace("-", " "), self.role, self.description))


@dataclass(frozen=True)
class SkillRecord:
    """One skill as the master catalogue describes it.

    Attributes:
        name: Canonical hyphenated slug, also the on-disk directory name.
        domain: Primary home knowledge graph for this skill.
        description: Catalogue prose, empty for the records that omit it.
        skill_relpath: Library-relative path of the skill definition.
    """

    name: str
    domain: str
    description: str
    skill_relpath: str

    @property
    def profile_text(self) -> str:
        """Return the concatenated prose used for lexical scoring."""
        return " ".join((self.name.replace("-", " "), self.description))


@dataclass(frozen=True)
class LibraryCatalogue:
    """Immutable snapshot of the library's agents, skills and domains.

    Attributes:
        agents: Agent slug to record.
        skills: Skill slug to record.
        domains: Domain slug to human-readable domain name.
        type_words: Node-type words observed as identifier prefixes in the
            master edge file, used by reference normalisation.
        library_version: Version string the catalogues declare.
    """

    agents: Mapping[str, AgentRecord]
    skills: Mapping[str, SkillRecord]
    domains: Mapping[str, str]
    type_words: Tuple[str, ...]
    library_version: str
    _agents_by_domain: Dict[str, Tuple[str, ...]] = field(default_factory=dict, compare=False, repr=False)
    _skills_by_domain: Dict[str, Tuple[str, ...]] = field(default_factory=dict, compare=False, repr=False)

    def kind_of(self, name: str) -> Optional[str]:
        """Classify an already-normalised slug by catalogue membership.

        Args:
            name: A folded slug produced by :func:`normalise_ref`.

        Returns:
            One of ``"agent"``, ``"skill"``, ``"domain"``, or ``None`` when the
            slug names none of them. The three name spaces were verified
            disjoint, so at most one answer is ever possible.
        """
        if name in self.agents:
            return _KIND_AGENT
        if name in self.skills:
            return _KIND_SKILL
        if name in self.domains:
            return _KIND_DOMAIN
        return None

    def agents_in(self, domain: str) -> Tuple[str, ...]:
        """Return the agent slugs whose primary home graph is ``domain``."""
        return self._agents_by_domain.get(domain, ())

    def skills_in(self, domain: str) -> Tuple[str, ...]:
        """Return the skill slugs whose primary home graph is ``domain``."""
        return self._skills_by_domain.get(domain, ())

    def domain_profile_text(self, domain: str) -> str:
        """Return the prose describing a domain, for lexical domain ranking.

        Built from the domain's own slug and title plus the names of the agents
        and skills that live in it. Descriptions are excluded deliberately: at
        domain granularity they swamp the signal, and the per-agent scorer
        already reads them.
        """
        parts: List[str] = [domain.replace("-", " "), self.domains.get(domain, "")]
        parts.extend(name.replace("-", " ") for name in self.agents_in(domain))
        parts.extend(name.replace("-", " ") for name in self.skills_in(domain))
        return " ".join(parts)


def _fetch_json(resolver: ResourceResolver, relpath: str) -> Any:
    """Read and decode one master catalogue file through the resolver.

    Args:
        resolver: ADR-1 resource resolver.
        relpath: Library-relative path of the catalogue file.

    Returns:
        The decoded payload.

    Raises:
        CatalogueUnavailable: When the file cannot be resolved or is not valid
            JSON. The two causes are reported distinctly in the message.
    """
    import json

    try:
        resource = resolver.fetch_kg_file(relpath)
    except LibrarySetupError as exc:
        raise CatalogueUnavailable("cannot resolve {}: {}".format(relpath, exc)) from exc
    try:
        return json.loads(resource.content)
    except ValueError as exc:
        raise CatalogueUnavailable("malformed JSON in {}: {}".format(relpath, exc)) from exc


def _entries(payload: Any, relpath: str, *keys: str) -> Sequence[Any]:
    """Extract the record list from a catalogue payload.

    Args:
        payload: Decoded catalogue JSON.
        relpath: Library-relative path, used only for the error message.
        keys: Container keys to try, in order, when the payload is a mapping.

    Returns:
        The record list.

    Raises:
        CatalogueUnavailable: When no accepted container shape is present. An
            unrecognised shape is an error, never an empty roster.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return candidate
    raise CatalogueUnavailable("unrecognised container shape in {}".format(relpath))


def _text(record: Mapping[str, Any], *keys: str) -> str:
    """Return the first non-empty string among ``keys``, or the empty string."""
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _slug_tuple(record: Mapping[str, Any], key: str) -> Tuple[str, ...]:
    """Return the normalised slugs held under ``key``, dropping non-strings."""
    raw = record.get(key)
    if not isinstance(raw, list):
        return ()
    return tuple(normalise_ref(item) for item in raw if isinstance(item, str) and item.strip())


def _derive_type_words(resolver: ResourceResolver) -> Tuple[str, ...]:
    """Derive the node-type prefix vocabulary from the master edge file.

    The vocabulary is read out of the data rather than declared, so a new node
    kind appearing upstream is picked up without a code change. Every prefix
    that occurs before a colon in a master edge endpoint is a type word.

    Args:
        resolver: ADR-1 resource resolver.

    Returns:
        The observed type words, sorted longest-first so that a longer prefix
        is tried before a shorter one that is its prefix. Falls back to the
        prefixes declared on catalogue record identifiers when the master edge
        file cannot be read, which is a strictly smaller but still valid
        vocabulary.
    """
    words = set()
    try:
        payload = _fetch_json(resolver, _EDGES_RELPATH)
        for edge in _entries(payload, _EDGES_RELPATH, "edges"):
            if not isinstance(edge, dict):
                continue
            for side in ("source", "target", "source_id", "target_id"):
                raw = edge.get(side)
                if isinstance(raw, str) and ":" in raw:
                    words.add(raw.split(":", 1)[0].strip().lower())
    except CatalogueUnavailable:
        words = set()
    return tuple(sorted(words, key=lambda word: (-len(word), word)))


def _type_words_from_ids(*payloads: Sequence[Any]) -> Tuple[str, ...]:
    """Derive type words from catalogue record identifiers as a fallback."""
    words = set()
    for records in payloads:
        for record in records:
            if not isinstance(record, dict):
                continue
            raw = record.get("id")
            if isinstance(raw, str) and ":" in raw:
                words.add(raw.split(":", 1)[0].strip().lower())
    return tuple(sorted(words, key=lambda word: (-len(word), word)))


def load_catalogue(resolver: Optional[ResourceResolver] = None) -> LibraryCatalogue:
    """Load the three master catalogues into an immutable snapshot.

    Args:
        resolver: ADR-1 resource resolver. Built from the default chain when
            omitted.

    Returns:
        A populated :class:`LibraryCatalogue`.

    Raises:
        CatalogueUnavailable: When any catalogue is unreadable, malformed, or
            carries an unrecognised container shape.
    """
    resolver = resolver or build_default_resolver()

    agent_payload = _fetch_json(resolver, _AGENTS_RELPATH)
    skill_payload = _fetch_json(resolver, _SKILLS_RELPATH)
    domain_payload = _fetch_json(resolver, _DOMAINS_RELPATH)

    agent_records = _entries(agent_payload, _AGENTS_RELPATH, "agents", "nodes")
    skill_records = _entries(skill_payload, _SKILLS_RELPATH, "skills", "nodes")
    domain_records = _entries(domain_payload, _DOMAINS_RELPATH, "domains", "nodes")

    agents: Dict[str, AgentRecord] = {}
    agents_by_domain: Dict[str, List[str]] = {}
    for record in agent_records:
        if not isinstance(record, dict):
            continue
        name = normalise_ref(record.get("name"))
        if not name:
            continue
        domain = normalise_ref(record.get("primary_home_kg") or record.get("domain"))
        agents[name] = AgentRecord(
            name=name,
            domain=domain,
            description=_text(record, "description"),
            role=_text(record, "role", "role_summary", "role_type"),
            model=_text(record, "model"),
            mandatory_skills=_slug_tuple(record, "mandatory_skills"),
            optional_skills=_slug_tuple(record, "optional_skills"),
            persona_relpath="{}/{}/{}".format(_AGENT_DIR, name, _AGENT_FILE),
        )
        agents_by_domain.setdefault(domain, []).append(name)

    skills: Dict[str, SkillRecord] = {}
    skills_by_domain: Dict[str, List[str]] = {}
    for record in skill_records:
        if not isinstance(record, dict):
            continue
        name = normalise_ref(record.get("name"))
        if not name:
            continue
        domain = normalise_ref(record.get("primary_home_kg") or record.get("domain"))
        skills[name] = SkillRecord(
            name=name,
            domain=domain,
            description=_text(record, "description"),
            skill_relpath="{}/{}/{}".format(_SKILL_DIR, name, _SKILL_FILE),
        )
        skills_by_domain.setdefault(domain, []).append(name)

    domains: Dict[str, str] = {}
    for record in domain_records:
        if not isinstance(record, dict):
            continue
        slug = normalise_ref(record.get("slug") or record.get("name"))
        if not slug:
            continue
        domains[slug] = _text(record, "name")

    if not agents or not skills or not domains:
        raise CatalogueUnavailable(
            "master catalogues resolved but yielded agents={} skills={} domains={}".format(
                len(agents), len(skills), len(domains)
            )
        )

    type_words = _derive_type_words(resolver) or _type_words_from_ids(agent_records, skill_records)

    version = ""
    if isinstance(agent_payload, dict):
        version = _text(agent_payload, "library_version", "kg_version")

    return LibraryCatalogue(
        agents=agents,
        skills=skills,
        domains=domains,
        type_words=type_words,
        library_version=version,
        _agents_by_domain={key: tuple(value) for key, value in agents_by_domain.items()},
        _skills_by_domain={key: tuple(value) for key, value in skills_by_domain.items()},
    )


def verify_persona(resolver: ResourceResolver, record: AgentRecord) -> str:
    """Confirm an agent's persona file resolves, and return its path.

    The dispatch contract requires that a selection record the path its
    persona block is lifted from; a path that does not resolve makes the
    selection unexecutable, so this is checked rather than assumed.

    Args:
        resolver: ADR-1 resource resolver.
        record: The agent whose persona path is being confirmed.

    Returns:
        ``record.persona_relpath`` when the file resolves.

    Raises:
        CatalogueUnavailable: When the persona file cannot be resolved.
    """
    try:
        resolver.fetch_agent(record.name)
    except LibrarySetupError as exc:
        raise CatalogueUnavailable("persona unavailable for agent '{}': {}".format(record.name, exc)) from exc
    return record.persona_relpath
