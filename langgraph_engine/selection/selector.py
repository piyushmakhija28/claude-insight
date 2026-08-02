"""Knowledge-graph-driven agent selection (PRD FR-10 / SRS FR-22).

``select_agents`` ranks library agents for a task description by querying the
per-domain knowledge graphs. Two properties are structural rather than
incidental, and both are asserted by the accompanying suite:

**No agent or skill name is a literal here.** Candidates are discovered by
reading edges; their names arrive as data from the master catalogue. Nothing in
this module can name an agent, so nothing here can prefer one by name.

**Every emitted match carries a non-empty edge path.** Candidacy is derived
from knowledge-graph edges -- an agent that no edge mentions is never a
candidate in the first place. An empty edge path is therefore unreachable
rather than merely improbable, which is what SRS FR-23 requires of the field
and what FR-11 means by "an empty edge path is a bug, not a low-confidence
result".

The five SRS FR-23 explainability fields live on :class:`Match`: agent name,
source domain, matched skills, knowledge-graph edge path and confidence score.
:meth:`SelectionResult.to_dict` emits them, so the downstream explainability
requirement is a serialisation concern and not a second selection pass.

The dispatch contract is satisfied by :attr:`Match.persona_relpath`. Library
agents are not registered subagent types; a run spawns a generic subagent with
the persona block lifted from that path, and a selection that did not record
the path would not be executable.

**A call ends in one of four named states** (SRS FR-24), reported by
:attr:`SelectionResult.outcome` so that a caller switches on one field rather
than pattern-matching a reason string:

``selected``
    Ranked matches were produced and are safe to dispatch.
``low_confidence``
    Candidates were found and every one scored below the floor. They are
    carried on :attr:`Degraded.near_misses` with their evidence intact, so the
    caller can widen the search or escalate to a human with something to show,
    but they are deliberately absent from :attr:`SelectionResult.matches` -- a
    caller that ignores the outcome cannot dispatch one by accident.
``no_match``
    The corpus offered nothing: no scorable query terms, no lexical signal, or
    no graph edge naming a catalogue agent. There are no near misses because
    there were no candidates.
``unavailable``
    Every candidate domain graph failed to parse. Nothing was looked at, which
    is a retryable infrastructure failure rather than a verdict on the library.

The distinction between the last three is the point of the requirement.
Collapsing them into one degraded path discards exactly the information a
caller needs to choose between retrying, widening and escalating.

**On the floor's value.** It was measured, and the measurement is the reason it
was left where it is. Top-1 confidence was taken over all 37 sprint issue
titles and over a set of tasks the library plainly cannot serve. The real
titles span 0.685 to 0.863; the unservable tasks that produce any candidate at
all reach 0.714. The populations overlap, so no absolute floor separates them.
Four alternative discriminators -- query-term coverage, weight-normalised
coverage, top-to-median margin, and pool spread -- were measured on the same
two populations and every one of them overlapped more, not less. Most
unservable tasks are caught earlier and more cleanly, by having no lexical
overlap with the corpus at all, which is the ``no_match`` path rather than this
one.

A floor placed just under the real minimum would catch most of the remainder,
but it would sit 0.035 above nothing at all, measured on one sprint of one
project, and any vocabulary drift would start degrading real work. The default
is therefore unchanged and deliberately permissive, the floor actually applied
is recorded on every degraded result so a rejection can be re-examined, and the
value is a per-call parameter because the evidence does not pick one number for
every deployment. What this state guarantees is not that a bad match is always
caught -- lexical retrieval cannot promise that -- but that when one is caught
it is never returned as a silent pick.

Windows-safe: ASCII only.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .catalogue import AgentRecord, LibraryCatalogue
from .kg_adapter import DomainKgAdapter, KgEdge, Parsed, ParseError
from .lexicon import Lexicon, tokenize
from .risk import RiskSignal

REASON_NO_QUERY_TERMS = "no_usable_query_terms"
REASON_NO_DOMAIN_SIGNAL = "no_domain_lexical_signal"
REASON_KG_UNREADABLE = "kg_unreadable_for_every_candidate_domain"
REASON_NO_KG_EVIDENCE = "no_agent_with_kg_evidence"
REASON_BELOW_THRESHOLD = "all_candidates_below_confidence_threshold"

OUTCOME_SELECTED = "selected"
OUTCOME_LOW_CONFIDENCE = "low_confidence"
OUTCOME_NO_MATCH = "no_match"
OUTCOME_UNAVAILABLE = "unavailable"

REASON_OUTCOMES: Dict[str, str] = {
    REASON_NO_QUERY_TERMS: OUTCOME_NO_MATCH,
    REASON_NO_DOMAIN_SIGNAL: OUTCOME_NO_MATCH,
    REASON_NO_KG_EVIDENCE: OUTCOME_NO_MATCH,
    REASON_KG_UNREADABLE: OUTCOME_UNAVAILABLE,
    REASON_BELOW_THRESHOLD: OUTCOME_LOW_CONFIDENCE,
}

KIND_AGENT = "agent"
KIND_SKILL = "skill"
KIND_DOMAIN = "domain"

COMPLEXITY_MIN = 1
COMPLEXITY_MAX = 25

DEFAULT_DOMAIN_FANOUT = 5
DEFAULT_LIMIT = 5
RETRIEVAL_DEPTH = 40
MAX_EDGE_PATH_STEPS = 6
MAX_MATCHED_SKILLS = 6

WEIGHT_AGENT_PROSE = 1.0
WEIGHT_LINKED_SKILL = 0.6
WEIGHT_DOMAIN = 0.25

BASE_CONFIDENCE_FLOOR = 0.45
HIGH_RISK_CONFIDENCE_FLOOR = 0.55
RISK_HIGH = "high"


class UnmappedDegradedReason(KeyError):
    """Raised when a degraded reason has no declared outcome state.

    Every reason must name the state it belongs to. Defaulting an unrecognised
    reason to one of the states would silently mislabel it, which is the same
    class of failure -- an outcome the caller cannot trust -- that this module's
    state separation exists to remove.
    """


def outcome_for(reason: str) -> str:
    """Return the caller-facing outcome state that ``reason`` belongs to.

    Args:
        reason: One of the module-level ``REASON_*`` constants.

    Returns:
        The matching ``OUTCOME_*`` constant.

    Raises:
        UnmappedDegradedReason: When ``reason`` is not in
            :data:`REASON_OUTCOMES`.
    """
    try:
        return REASON_OUTCOMES[reason]
    except KeyError:
        raise UnmappedDegradedReason(
            "degraded reason '{}' declares no outcome state; add it to REASON_OUTCOMES".format(reason)
        ) from None


class ComplexityOutOfRange(ValueError):
    """Raised when the caller passes a complexity outside the 1-25 band.

    ``combined_complexity_score`` is on a 1-25 scale. Passing a 1-10 score is a
    silent mis-scaling that would bias every threshold, so it is rejected
    rather than clamped.
    """


class ConfidenceFloorOutOfRange(ValueError):
    """Raised when the caller passes a confidence floor outside 0-1.

    Confidence is an absolute score in ``[0, 1)``. A floor expressed as a
    percentage would silently reject every candidate, producing a plausible
    low-confidence outcome from a unit error rather than from the evidence.
    """


@dataclass(frozen=True)
class EdgeStep:
    """One hop of a knowledge-graph edge path.

    Attributes:
        source: Normalised source slug.
        edge_type: Relationship type exactly as the domain graph records it.
        target: Normalised target slug.
        domain: Domain graph the hop was read from.
    """

    source: str
    edge_type: str
    target: str
    domain: str

    def to_dict(self) -> Dict[str, str]:
        """Return the hop as a serialisable mapping."""
        return {
            "source": self.source,
            "edge_type": self.edge_type,
            "target": self.target,
            "domain": self.domain,
        }


@dataclass(frozen=True)
class Match:
    """One selected agent and the evidence behind it.

    The first five attributes are the SRS FR-23 explainability fields.

    Attributes:
        agent: Agent slug, sourced from the master catalogue.
        domain: Domain graph that supplied the supporting edges.
        matched_skills: Skills the graph links to this agent, ranked by their
            relevance to the task.
        edge_path: Supporting edges. Non-empty by construction.
        confidence: Absolute score in ``[0, 1)``, not a within-pool rank.
        persona_relpath: Library-relative path the persona block is lifted
            from, required by the dispatch contract.
        model: Model tier the catalogue records for this agent.
    """

    agent: str
    domain: str
    matched_skills: Tuple[str, ...]
    edge_path: Tuple[EdgeStep, ...]
    confidence: float
    persona_relpath: str
    model: str

    def to_dict(self) -> Dict[str, Any]:
        """Return the match as a serialisable mapping, FR-23 fields first."""
        return {
            "agent": self.agent,
            "domain": self.domain,
            "matched_skills": list(self.matched_skills),
            "edge_path": [step.to_dict() for step in self.edge_path],
            "confidence": round(self.confidence, 4),
            "persona_relpath": self.persona_relpath,
            "model": self.model,
        }


@dataclass(frozen=True)
class Degraded:
    """The explicit fallback outcome: why nothing was selected, and what was near.

    ``outcome`` is the field a caller switches on. ``reason`` narrows it to the
    specific condition, and the two are kept consistent by :func:`outcome_for`
    rather than by convention.

    ``near_misses`` is what separates a low-confidence outcome from a no-match
    outcome in substance rather than only in label. A low-confidence result had
    candidates and carries them, each with the evidence that earned it, so the
    caller can widen the search or hand a human something concrete. A no-match
    result had none to carry. Reading this field is therefore an independent
    check on the state, which is why the accompanying suite asserts both.

    Attributes:
        reason: One of the module-level ``REASON_*`` constants.
        detail: Human-readable elaboration naming what was tried.
        considered_domains: Domains that were read before giving up.
        outcome: One of the module-level ``OUTCOME_*`` constants.
        near_misses: Candidates that were found and rejected, best first.
            Populated only for the low-confidence outcome, and deliberately not
            surfaced as matches -- a caller that ignores ``outcome`` must not be
            able to dispatch one of these by accident.
        best_confidence: Confidence of the best rejected candidate, or ``0.0``
            when there were no candidates at all.
        applied_floor: The floor that was in force for this call, recorded so
            that a rejection can be re-examined without re-deriving it.
    """

    reason: str
    detail: str
    considered_domains: Tuple[str, ...] = ()
    outcome: str = OUTCOME_NO_MATCH
    near_misses: Tuple[Match, ...] = ()
    best_confidence: float = 0.0
    applied_floor: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Return the degraded outcome as a serialisable mapping."""
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "detail": self.detail,
            "considered_domains": list(self.considered_domains),
            "near_misses": [match.to_dict() for match in self.near_misses],
            "best_confidence": round(self.best_confidence, 4),
            "applied_floor": round(self.applied_floor, 4),
        }


@dataclass(frozen=True)
class SelectionResult:
    """Outcome of one selection call.

    Exactly one of ``matches`` and ``degraded`` is populated. An empty
    ``matches`` with no ``degraded`` is not a state this module can produce --
    an unexplained empty result is the failure SRS FR-24 exists to forbid.

    :attr:`outcome` names which of the four states the call ended in.

    Attributes:
        task: The task description that was scored.
        matches: Ranked matches, best first. Empty unless the outcome is
            ``selected``; rejected candidates live on ``degraded.near_misses``
            instead, so they cannot be mistaken for a pick.
        degraded: Populated only when nothing was selected.
        considered_domains: Domains ranked in and read.
        parse_errors: Typed adapter failures encountered while reading them.
        risk: The risk signal the call ran against.
        library_version: Version the master catalogues declared.
    """

    task: str
    matches: Tuple[Match, ...]
    degraded: Optional[Degraded]
    considered_domains: Tuple[str, ...]
    parse_errors: Tuple[ParseError, ...]
    risk: RiskSignal
    library_version: str

    @property
    def outcome(self) -> str:
        """Return the state this call ended in, as an ``OUTCOME_*`` constant.

        This is the single field a caller should branch on. A selection that
        produced matches is ``selected``; anything else reports the degraded
        outcome's own state, so "nothing came back" is never ambiguous.
        """
        return self.degraded.outcome if self.degraded else OUTCOME_SELECTED

    def to_dict(self) -> Dict[str, Any]:
        """Return the whole result as a serialisable mapping."""
        return {
            "task": self.task,
            "outcome": self.outcome,
            "matches": [match.to_dict() for match in self.matches],
            "degraded": self.degraded.to_dict() if self.degraded else None,
            "considered_domains": list(self.considered_domains),
            "parse_errors": [
                {
                    "domain": error.domain,
                    "path": error.path,
                    "failure_kind": error.failure_kind,
                    "detail": error.detail,
                }
                for error in self.parse_errors
            ],
            "risk": {
                "risk_level": self.risk.risk_level,
                "danger_zone_count": self.risk.danger_zone_count,
                "coverage_complete": self.risk.coverage_complete,
                "source": self.risk.source,
            },
            "library_version": self.library_version,
        }


def build_lexicon(catalogue: LibraryCatalogue) -> Lexicon:
    """Build the term-weight model from every catalogue record's prose.

    Args:
        catalogue: The loaded library catalogue.

    Returns:
        A :class:`Lexicon` whose corpus is one document per agent and per
        skill, so weights reflect this library rather than English at large.
    """
    documents: List[str] = [record.profile_text for record in catalogue.agents.values()]
    documents.extend(record.profile_text for record in catalogue.skills.values())
    return Lexicon(documents)


def _rank_domains(
    catalogue: LibraryCatalogue,
    lexicon: Lexicon,
    query_terms: "set",
    fanout: int,
) -> List[Tuple[str, float]]:
    """Choose which domain graphs to read, by voting from record-level scores.

    Scoring a domain on its own aggregate prose was measured to lose the right
    domain behind larger, wordier ones: a domain profile is a bag of a hundred
    records, and the term that identifies the task drowns in it. Individual
    records are scored instead, and each strong record votes for the domain it
    lives in. Recall is a record-level question, so it is answered at record
    level.

    This is retrieval, not selection. Nothing is selected here -- the shortlist
    only decides which graphs get read, and an agent still becomes a candidate
    only by appearing in an edge.

    Returns:
        Up to ``fanout`` ``(domain, score)`` pairs with a positive vote total,
        best first. Ties break on domain slug so the ranking is deterministic.
    """
    votes: Dict[str, float] = {}

    def cast(records, count: int) -> None:
        scored = []
        for record in records:
            score = lexicon.score(query_terms, record.profile_text)
            if score > 0.0 and record.domain in catalogue.domains:
                scored.append((record.domain, score))
        scored.sort(key=lambda pair: -pair[1])
        for domain_slug, score in scored[:count]:
            votes[domain_slug] = votes.get(domain_slug, 0.0) + score

    cast(catalogue.agents.values(), RETRIEVAL_DEPTH)
    cast(catalogue.skills.values(), RETRIEVAL_DEPTH)

    ranked = sorted(votes.items(), key=lambda pair: (-pair[1], pair[0]))
    return ranked[:fanout]


def _agent_edges(edges: Sequence[KgEdge]) -> Dict[str, List[KgEdge]]:
    """Group edges by the agent endpoint they touch.

    An edge is attributed to every agent it mentions on either side, so an
    agent named only as a delegation target is still discoverable.
    """
    grouped: Dict[str, List[KgEdge]] = {}
    for edge in edges:
        if edge.source_kind == KIND_AGENT:
            grouped.setdefault(edge.source, []).append(edge)
        if edge.target_kind == KIND_AGENT and edge.target != edge.source:
            grouped.setdefault(edge.target, []).append(edge)
    return grouped


def _linked_skills(agent: str, edges: Sequence[KgEdge]) -> List[str]:
    """Return the distinct skill slugs the graph links to ``agent``.

    Edge type is not consulted. The library records agent-to-skill association
    under at least five different type names, and enumerating them is exactly
    the hardcoded list this requirement removes -- so the relationship is
    identified by what the endpoints resolve to, which is measured, rather than
    by what the edge calls itself, which is inconsistent.
    """
    skills: List[str] = []
    for edge in edges:
        if edge.source == agent and edge.target_kind == KIND_SKILL:
            candidate = edge.target
        elif edge.target == agent and edge.source_kind == KIND_SKILL:
            candidate = edge.source
        else:
            continue
        if candidate not in skills:
            skills.append(candidate)
    return skills


def _rank_skills(
    catalogue: LibraryCatalogue,
    lexicon: Lexicon,
    query_terms: "set",
    skills: Sequence[str],
) -> List[Tuple[str, float]]:
    """Rank an agent's linked skills by lexical relevance to the task."""
    scored = []
    for skill in skills:
        record = catalogue.skills.get(skill)
        text = record.profile_text if record else skill.replace("-", " ")
        scored.append((skill, lexicon.score(query_terms, text)))
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored


def _build_edge_path(agent: str, edges: Sequence[KgEdge], preferred_targets: Sequence[str]) -> Tuple[EdgeStep, ...]:
    """Assemble the supporting edge path for one agent.

    Edges touching a skill the task actually matched come first, then the
    agent's domain-membership edge, then whatever else the graph records. The
    ordering makes the path read as evidence rather than as a dump.

    Returns:
        Up to :data:`MAX_EDGE_PATH_STEPS` hops. Non-empty whenever ``edges`` is
        non-empty, which the caller guarantees.
    """
    preferred = set(preferred_targets)

    def rank(edge: KgEdge) -> Tuple[int, str, str]:
        other = edge.target if edge.source == agent else edge.source
        if other in preferred:
            bucket = 0
        elif edge.target_kind == KIND_DOMAIN or edge.source_kind == KIND_DOMAIN:
            bucket = 1
        elif edge.target_kind == KIND_SKILL or edge.source_kind == KIND_SKILL:
            bucket = 2
        else:
            bucket = 3
        return (bucket, edge.edge_type, other)

    ordered = sorted(edges, key=rank)
    return tuple(
        EdgeStep(source=edge.source, edge_type=edge.edge_type, target=edge.target, domain=edge.domain)
        for edge in ordered[:MAX_EDGE_PATH_STEPS]
    )


def _confidence(raw_score: float, scale: float) -> float:
    """Map a raw score onto an absolute ``[0, 1)`` confidence.

    The transform saturates rather than normalising within the candidate pool.
    Pool normalisation would hand the best of a bad field a confidence of 1.0,
    which is precisely the silent-default failure SRS FR-24 forbids: the top
    candidate for a task the library cannot serve must score low, not first.

    Args:
        raw_score: Weighted evidence total for one candidate.
        scale: Corpus-derived reference weight. One hit on a term of median
            rarity yields a confidence of ``0.5``.

    Returns:
        The saturated confidence.
    """
    if raw_score <= 0.0 or scale <= 0.0:
        return 0.0
    return raw_score / (raw_score + scale)


def select_agents(
    task: str,
    *,
    catalogue: LibraryCatalogue,
    adapter: DomainKgAdapter,
    risk: RiskSignal,
    lexicon: Optional[Lexicon] = None,
    domain: Optional[str] = None,
    complexity: int = COMPLEXITY_MIN,
    limit: int = DEFAULT_LIMIT,
    domain_fanout: int = DEFAULT_DOMAIN_FANOUT,
    accept_partial_coverage: bool = False,
    confidence_floor: Optional[float] = None,
) -> SelectionResult:
    """Select agents for ``task`` by querying the library knowledge graph.

    Args:
        task: Free-text task description.
        catalogue: Loaded master catalogue, the only source of names.
        adapter: Domain graph reader.
        risk: Call-graph risk signal. Its coverage precondition is enforced
            before any scoring happens.
        lexicon: Prebuilt term-weight model. Built from ``catalogue`` when
            omitted; supply one to avoid rebuilding across repeated calls.
        domain: Optional caller-supplied domain to score alone, bypassing
            lexical domain ranking.
        complexity: ``combined_complexity_score`` on its native 1-25 scale.
        limit: Maximum number of matches to return.
        domain_fanout: Number of top-ranked domains to read.
        accept_partial_coverage: Explicit acceptance of a truncated risk
            signal, recorded by the caller rather than inferred here.
        confidence_floor: Overrides the risk-derived floor below which a
            candidate is reported as a near miss instead of a match. The
            default is deployment-independent and conservative; a caller that
            has measured its own tolerance can raise it, and the floor actually
            applied is recorded on the result either way.

    Returns:
        A :class:`SelectionResult` carrying either ranked matches or an
        explicit degraded outcome, never both and never neither.

    Raises:
        ComplexityOutOfRange: When ``complexity`` is outside 1-25.
        ConfidenceFloorOutOfRange: When ``confidence_floor`` is outside 0-1.
        TruncatedRiskSignal: When ``risk`` is not coverage-complete and
            ``accept_partial_coverage`` is false.
    """
    if not COMPLEXITY_MIN <= complexity <= COMPLEXITY_MAX:
        raise ComplexityOutOfRange(
            "complexity {} is outside the {}-{} band; combined_complexity_score is not a 1-10 score".format(
                complexity, COMPLEXITY_MIN, COMPLEXITY_MAX
            )
        )
    if confidence_floor is not None and not 0.0 <= confidence_floor <= 1.0:
        raise ConfidenceFloorOutOfRange(
            "confidence_floor {} is outside 0.0-1.0; confidence is an absolute score, not a percentage".format(
                confidence_floor
            )
        )
    risk.require_coverage(accept_partial_coverage)

    lexicon = lexicon or build_lexicon(catalogue)
    query_terms = tokenize(task)

    def degraded(
        reason: str,
        detail: str,
        domains: Sequence[str] = (),
        *,
        errors: Sequence[ParseError] = (),
        near_misses: Sequence[Match] = (),
        best_confidence: float = 0.0,
        applied_floor: float = 0.0,
    ) -> SelectionResult:
        """Build the one degraded result shape, with its outcome state derived.

        Every degraded exit routes through here so that the outcome can never
        drift from the reason: it is looked up, not restated at each site.
        """
        return SelectionResult(
            task=task,
            matches=(),
            degraded=Degraded(
                reason=reason,
                detail=detail,
                considered_domains=tuple(domains),
                outcome=outcome_for(reason),
                near_misses=tuple(near_misses),
                best_confidence=best_confidence,
                applied_floor=applied_floor,
            ),
            considered_domains=tuple(domains),
            parse_errors=tuple(errors),
            risk=risk,
            library_version=catalogue.library_version,
        )

    if not query_terms:
        return degraded(REASON_NO_QUERY_TERMS, "task description yielded no scorable terms")

    if domain:
        if domain not in catalogue.domains:
            return degraded(
                REASON_NO_DOMAIN_SIGNAL, "caller-supplied domain '{}' is not in the catalogue".format(domain)
            )
        ranked_domains = [(domain, lexicon.score(query_terms, catalogue.domain_profile_text(domain)))]
    else:
        ranked_domains = _rank_domains(catalogue, lexicon, query_terms, domain_fanout)

    if not ranked_domains:
        return degraded(
            REASON_NO_DOMAIN_SIGNAL,
            "no domain profile shares a term with the task across {} domains".format(len(catalogue.domains)),
        )

    domain_scores = dict(ranked_domains)
    considered = tuple(name for name, _ in ranked_domains)

    parse_errors: List[ParseError] = []
    parsed_domains: List[Parsed] = []
    for name, _ in ranked_domains:
        result = adapter.read_domain(name)
        if isinstance(result, ParseError):
            parse_errors.append(result)
        else:
            parsed_domains.append(result)

    if not parsed_domains:
        return degraded(
            REASON_KG_UNREADABLE,
            "every one of {} candidate domains failed to parse: {}".format(
                len(parse_errors),
                ", ".join("{}={}".format(error.domain, error.failure_kind) for error in parse_errors),
            ),
            considered,
            errors=parse_errors,
        )

    scale = _corpus_scale(lexicon)
    if confidence_floor is not None:
        floor = confidence_floor
    else:
        floor = HIGH_RISK_CONFIDENCE_FLOOR if risk.risk_level == RISK_HIGH else BASE_CONFIDENCE_FLOOR

    best: Dict[str, Tuple[float, Match]] = {}
    candidate_count = 0
    for parsed in parsed_domains:
        grouped = _agent_edges(parsed.edges)
        for agent_name, edges in grouped.items():
            record = catalogue.agents.get(agent_name)
            if record is None:
                continue
            candidate_count += 1
            match, raw = _score_candidate(
                record=record,
                edges=edges,
                domain=parsed.domain,
                domain_score=domain_scores.get(parsed.domain, 0.0),
                catalogue=catalogue,
                lexicon=lexicon,
                query_terms=query_terms,
                scale=scale,
            )
            previous = best.get(agent_name)
            if previous is None or raw > previous[0]:
                best[agent_name] = (raw, match)

    if not best:
        return degraded(
            REASON_NO_KG_EVIDENCE,
            "{} domain graphs parsed but named no catalogue agent".format(len(parsed_domains)),
            considered,
            errors=parse_errors,
        )

    ranked = sorted(best.values(), key=lambda pair: (-pair[0], pair[1].agent))
    matches = tuple(match for _, match in ranked if match.confidence >= floor)[:limit]

    if not matches:
        near = tuple(match for _, match in ranked)[:limit]
        _require_edge_paths(near)
        return degraded(
            REASON_BELOW_THRESHOLD,
            "best of {} candidates scored {:.3f}, below the {:.2f} floor for risk_level={}; "
            "{} near miss(es) carried for widening or escalation, none dispatchable".format(
                candidate_count, near[0].confidence, floor, risk.risk_level, len(near)
            ),
            considered,
            errors=parse_errors,
            near_misses=near,
            best_confidence=near[0].confidence,
            applied_floor=floor,
        )

    _require_edge_paths(matches)

    return SelectionResult(
        task=task,
        matches=matches,
        degraded=None,
        considered_domains=considered,
        parse_errors=tuple(parse_errors),
        risk=risk,
        library_version=catalogue.library_version,
    )


def _require_edge_paths(candidates: Sequence[Match]) -> None:
    """Enforce the non-empty edge path invariant on anything leaving the module.

    Applied to near misses as well as to matches. A rejected candidate is still
    handed to a caller as the evidence behind an escalation, so one that cited
    no edge would be exactly as unusable there as it would be as a match.

    Raises:
        AssertionError: When any candidate carries an empty edge path.
    """
    for candidate in candidates:
        if not candidate.edge_path:
            raise AssertionError(
                "invariant breach: candidate for '{}' carries an empty edge path".format(candidate.agent)
            )


def _score_candidate(
    *,
    record: AgentRecord,
    edges: Sequence[KgEdge],
    domain: str,
    domain_score: float,
    catalogue: LibraryCatalogue,
    lexicon: Lexicon,
    query_terms: "set",
    scale: float,
) -> Tuple[Match, float]:
    """Score one agent within one domain and build its match record.

    Returns:
        The :class:`Match` and its raw pre-saturation score, which the caller
        uses for ranking so that ordering is not flattened by the transform.
    """
    prose_score = lexicon.score(query_terms, record.profile_text)
    ranked_skills = _rank_skills(catalogue, lexicon, query_terms, _linked_skills(record.name, edges))
    top_skill_score = ranked_skills[0][1] if ranked_skills else 0.0

    raw = WEIGHT_AGENT_PROSE * prose_score + WEIGHT_LINKED_SKILL * top_skill_score + WEIGHT_DOMAIN * domain_score

    matched_skills = tuple(name for name, score in ranked_skills if score > 0.0)[:MAX_MATCHED_SKILLS]
    if not matched_skills:
        matched_skills = tuple(name for name, _ in ranked_skills)[:MAX_MATCHED_SKILLS]

    match = Match(
        agent=record.name,
        domain=domain,
        matched_skills=matched_skills,
        edge_path=_build_edge_path(record.name, edges, matched_skills),
        confidence=_confidence(raw, scale),
        persona_relpath=record.persona_relpath,
        model=record.model,
    )
    return match, raw


def _corpus_scale(lexicon: Lexicon) -> float:
    """Return the reference weight a single median-rarity term hit is worth.

    Derived from the corpus so that confidence means the same thing across
    libraries of different sizes, and so that no scale constant has to be
    guessed and then quietly go stale.
    """
    return lexicon.median_weight()


def selection_to_mapping(result: SelectionResult) -> Mapping[str, Any]:
    """Return ``result`` as a plain mapping, for logging and state storage."""
    return result.to_dict()
