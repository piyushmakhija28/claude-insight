"""Selection explainability emission (PRD FR-11 / SRS FR-23).

SRS FR-23 requires that, for every agent the selector picks, five fields are
emitted: the agent name, its source domain, the matched skills, the
knowledge-graph edge path and the confidence score. This module turns a
selection outcome into audit records carrying exactly those fields, and refuses
to emit a record it cannot fill from the outcome itself.

**Nothing here invents a value.** Every emitted field is copied from the
selection outcome. A field that is absent, blank, empty or numerically
meaningless raises rather than being filled with a placeholder. That refusal is
the point of the requirement: five fields that are always present because four
of them are padded would satisfy a shallow check while destroying the
explainability the requirement exists to provide.

**Nothing here imports the selector.** The outcome is read structurally -- as a
mapping, or through the object's own ``to_dict`` -- so this module carries no
compile-time dependency on the shape of a match or on the vocabulary of
outcomes that carry no match. A selection that names no agent emits no agent
record and passes its own explanation through verbatim, whatever that
explanation is called; an outcome state this module has never seen survives
into the audit record unread rather than being dropped or renamed. The one
structural claim made about the outcome is that it reports its matches under
:data:`MATCHES_KEY`; if that key disappears, :class:`SelectionShapeChanged` is
raised, because silently emitting zero agent records for a renamed key would
forge a clean audit of a run that selected agents.

A sixth field, :data:`DISPATCH_FIELD`, is required alongside the five. Library
agents are not registered subagent types: a run spawns a generic subagent with
the persona block lifted from that path, so a record naming an agent without it
is an explanation of something that cannot be executed.

Windows-safe: ASCII only.
"""

import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

REQUIREMENT = "SRS FR-23"

FIELD_AGENT = "agent"
FIELD_DOMAIN = "domain"
FIELD_MATCHED_SKILLS = "matched_skills"
FIELD_EDGE_PATH = "edge_path"
FIELD_CONFIDENCE = "confidence"

FR23_FIELDS: Tuple[str, ...] = (
    FIELD_AGENT,
    FIELD_DOMAIN,
    FIELD_MATCHED_SKILLS,
    FIELD_EDGE_PATH,
    FIELD_CONFIDENCE,
)

DISPATCH_FIELD = "persona_relpath"
REQUIRED_FIELDS: Tuple[str, ...] = FR23_FIELDS + (DISPATCH_FIELD,)

MATCHES_KEY = "matches"

RECORD_REQUIREMENT_KEY = "requirement"
RECORD_FIELDS_KEY = "explainability_fields"
RECORD_COUNT_KEY = "selected_agent_count"
RECORD_AGENTS_KEY = "selected_agents"
RECORD_OUTCOME_KEY = "outcome"

LOG_MARKER = "selection.explainability"

CONFIDENCE_FLOOR_EXCLUSIVE = 0.0
CONFIDENCE_CEILING = 1.0

PATH_SEPARATOR = "/"
PARENT_SEGMENT = ".."


class IncompleteSelectionRecord(ValueError):
    """Raised when a selected agent cannot be explained from the outcome alone.

    Carrying the offending position and field name makes the refusal
    actionable: the caller learns which selected agent was unexplainable and in
    which of the required fields, rather than receiving a record that looks
    complete.

    Attributes:
        field: The required field that could not be filled.
        position: Zero-based index of the offending match within the outcome.
        reason: Why the value was rejected.
    """

    def __init__(self, field: str, position: int, reason: str):
        """Store the offending field, position and reason, and build the message."""
        self.field = field
        self.position = position
        self.reason = reason
        super().__init__("match {}: field '{}' {}".format(position, field, reason))


class SelectionShapeChanged(IncompleteSelectionRecord):
    """Raised when the outcome does not report its matches where expected.

    Distinct from a merely incomplete record because the remedy is different: a
    missing :data:`MATCHES_KEY` means the outcome's own shape moved, and the
    only safe response is to stop rather than to report an empty selection that
    the outcome never claimed.
    """


def _as_mapping(value: object, position: int, field: str) -> Mapping[str, Any]:
    """Return ``value`` as a read-only mapping without importing its type.

    Args:
        value: A mapping, or any object exposing a callable ``to_dict``.
        position: Index used in the error message when the value is neither.
        field: Field name used in the error message.

    Returns:
        The mapping form of ``value``.

    Raises:
        IncompleteSelectionRecord: When ``value`` offers neither form.
    """
    if isinstance(value, Mapping):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        produced = to_dict()
        if isinstance(produced, Mapping):
            return produced
    raise IncompleteSelectionRecord(field, position, "is neither a mapping nor an object offering to_dict()")


def _require_text(field: str, value: object, position: int) -> str:
    """Return ``value`` as non-blank text or refuse the record.

    Raises:
        IncompleteSelectionRecord: When the value is absent, not text or blank.
    """
    if not isinstance(value, str) or not value.strip():
        raise IncompleteSelectionRecord(field, position, "is absent, not text, or blank")
    return value


def _require_sequence(field: str, value: object, position: int) -> List[Any]:
    """Return ``value`` as a non-empty list or refuse the record.

    Text is rejected rather than iterated. A bare string in a field that holds a
    collection is the shape a placeholder takes, and iterating it would emit a
    sequence of characters that reads as evidence.

    Raises:
        IncompleteSelectionRecord: When the value is not a non-empty sequence.
    """
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise IncompleteSelectionRecord(field, position, "is not a list of entries")
    if not value:
        raise IncompleteSelectionRecord(field, position, "is empty")
    return list(value)


def _entry_is_populated(entry: object) -> bool:
    """Return whether one entry of a collection field carries content."""
    if entry is None:
        return False
    if isinstance(entry, str):
        return bool(entry.strip())
    if isinstance(entry, (Mapping, list, tuple, set, bytes)):
        return len(entry) > 0
    return True


def _require_confidence(field: str, value: object, position: int) -> float:
    """Return ``value`` as a usable confidence or refuse the record.

    Zero is rejected as vigorously as absence. The scoring transform returns
    exactly zero when a candidate has no supporting evidence at all, so a zero
    confidence on a selected agent is not a low score but a missing one.

    Raises:
        IncompleteSelectionRecord: When the value is not a real number inside
            the exclusive-zero-to-one band.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IncompleteSelectionRecord(field, position, "is absent or not a number")
    number = float(value)
    if number != number:
        raise IncompleteSelectionRecord(field, position, "is not a real number")
    if number <= CONFIDENCE_FLOOR_EXCLUSIVE or number > CONFIDENCE_CEILING:
        detail = "is {} and so falls outside the {}-to-{} band".format(
            number, CONFIDENCE_FLOOR_EXCLUSIVE, CONFIDENCE_CEILING
        )
        raise IncompleteSelectionRecord(field, position, detail)
    return number


def _require_dispatchable_path(value: object, agent: str, position: int) -> str:
    """Return the persona path or refuse the record.

    The path is checked for the three properties that make a selection
    executable: it is library-relative, it names a location rather than a bare
    token, and it belongs to the agent the record names. A record failing any
    of them explains a spawn that a run cannot perform.

    Raises:
        IncompleteSelectionRecord: When the path is blank, absolute, escaping,
            separator-free, or attributed to a different agent.
    """
    path = _require_text(DISPATCH_FIELD, value, position)
    if path.startswith(PATH_SEPARATOR) or path.startswith(chr(92)) or ":" in path:
        raise IncompleteSelectionRecord(DISPATCH_FIELD, position, "is not library-relative")
    segments = path.replace(chr(92), PATH_SEPARATOR).split(PATH_SEPARATOR)
    if PARENT_SEGMENT in segments:
        raise IncompleteSelectionRecord(DISPATCH_FIELD, position, "escapes the library root")
    if len(segments) < 2:
        raise IncompleteSelectionRecord(DISPATCH_FIELD, position, "names no location inside the library")
    if agent not in segments:
        raise IncompleteSelectionRecord(DISPATCH_FIELD, position, "does not belong to the agent the record names")
    return path


def _normalise_edge_path(value: object, position: int) -> List[Mapping[str, Any]]:
    """Return the edge path as a list of populated, serialisable hops.

    Raises:
        IncompleteSelectionRecord: When the path is not a non-empty list, or
            any hop is empty or offers no mapping form.
    """
    steps = _require_sequence(FIELD_EDGE_PATH, value, position)
    hops: List[Mapping[str, Any]] = []
    for step in steps:
        if not _entry_is_populated(step):
            raise IncompleteSelectionRecord(FIELD_EDGE_PATH, position, "contains an empty hop")
        hops.append(step if isinstance(step, Mapping) else _as_mapping(step, position, FIELD_EDGE_PATH))
    return hops


def explain_match(match: object, position: int = 0) -> Dict[str, Any]:
    """Return the audit record for one selected agent.

    The five requirement fields come first and are validated; the dispatch path
    follows; anything else the match carries is passed through afterwards,
    unread and unrenamed, so a field added to the match later reaches the audit
    log without this module being taught its name.

    Args:
        match: One selected agent, as a mapping or an object offering
            ``to_dict``.
        position: Zero-based index within the outcome, used in error messages.

    Returns:
        The record, requirement fields first.

    Raises:
        IncompleteSelectionRecord: When any required field is absent, blank,
            empty or unusable. Nothing is emitted in that case.
    """
    payload = _as_mapping(match, position, MATCHES_KEY)

    agent = _require_text(FIELD_AGENT, payload.get(FIELD_AGENT), position)
    domain = _require_text(FIELD_DOMAIN, payload.get(FIELD_DOMAIN), position)

    skills = _require_sequence(FIELD_MATCHED_SKILLS, payload.get(FIELD_MATCHED_SKILLS), position)
    for skill in skills:
        if not isinstance(skill, str) or not skill.strip():
            raise IncompleteSelectionRecord(FIELD_MATCHED_SKILLS, position, "contains a blank or non-text entry")

    steps = _normalise_edge_path(payload.get(FIELD_EDGE_PATH), position)
    confidence = _require_confidence(FIELD_CONFIDENCE, payload.get(FIELD_CONFIDENCE), position)
    persona = _require_dispatchable_path(payload.get(DISPATCH_FIELD), agent, position)

    record: Dict[str, Any] = {
        FIELD_AGENT: agent,
        FIELD_DOMAIN: domain,
        FIELD_MATCHED_SKILLS: list(skills),
        FIELD_EDGE_PATH: steps,
        FIELD_CONFIDENCE: confidence,
        DISPATCH_FIELD: persona,
    }
    for key, value in payload.items():
        if key not in record:
            record[key] = value
    return record


def explain_selection(result: object) -> Dict[str, Any]:
    """Return the audit record for one whole selection outcome.

    Args:
        result: A selection outcome, as a mapping or an object offering
            ``to_dict``.

    Returns:
        A record carrying one entry per selected agent under
        :data:`RECORD_AGENTS_KEY`, and everything else the outcome holds
        untouched under :data:`RECORD_OUTCOME_KEY`. An outcome that selected no
        agent yields an empty list rather than a padded entry.

    Raises:
        SelectionShapeChanged: When the outcome reports no matches key at all.
        IncompleteSelectionRecord: When any selected agent cannot be explained.
    """
    payload = _as_mapping(result, 0, MATCHES_KEY)
    if MATCHES_KEY not in payload:
        raise SelectionShapeChanged(MATCHES_KEY, 0, "is absent from the selection outcome")

    raw_matches = payload[MATCHES_KEY]
    if raw_matches is None:
        raw_matches = []
    if isinstance(raw_matches, (str, bytes)) or not isinstance(raw_matches, (list, tuple)):
        raise SelectionShapeChanged(MATCHES_KEY, 0, "is not a list of matches")

    agents = [explain_match(match, position) for position, match in enumerate(raw_matches)]

    return {
        RECORD_REQUIREMENT_KEY: REQUIREMENT,
        RECORD_FIELDS_KEY: list(FR23_FIELDS),
        RECORD_COUNT_KEY: len(agents),
        RECORD_AGENTS_KEY: agents,
        RECORD_OUTCOME_KEY: {key: value for key, value in payload.items() if key != MATCHES_KEY},
    }


def selection_log_lines(record: Mapping[str, Any]) -> List[str]:
    """Return the log lines for an audit record, one per selected agent.

    The first line summarises the outcome so a selection that named no agent
    still leaves a trace; each subsequent line carries one agent's requirement
    fields as single-line JSON, so a run log can be checked field by field
    without reconstructing the pipeline.

    Args:
        record: A record produced by :func:`explain_selection`.

    Returns:
        The lines, summary first.
    """
    summary = {
        RECORD_REQUIREMENT_KEY: record.get(RECORD_REQUIREMENT_KEY),
        RECORD_COUNT_KEY: record.get(RECORD_COUNT_KEY),
        RECORD_OUTCOME_KEY: record.get(RECORD_OUTCOME_KEY),
    }
    lines = ["{} {}".format(LOG_MARKER, json.dumps(summary, sort_keys=True, default=str))]
    for agent_record in record.get(RECORD_AGENTS_KEY, ()):
        lines.append("{} {}".format(LOG_MARKER, json.dumps(agent_record, sort_keys=True, default=str)))
    return lines


def emit_selection(result: object, logger: Optional[Any] = None) -> Dict[str, Any]:
    """Build and log the audit record for one selection outcome.

    Args:
        result: A selection outcome, as a mapping or an object offering
            ``to_dict``.
        logger: Destination for the lines. The engine logger is resolved
            lazily when omitted, so importing this module costs nothing.

    Returns:
        The record :func:`explain_selection` produced.

    Raises:
        SelectionShapeChanged: When the outcome reports no matches key.
        IncompleteSelectionRecord: When any selected agent cannot be explained.
            Nothing is logged in that case -- the record is built in full
            before the first line is written, so a run never leaves behind a
            partial explanation of a selection it then refused.
    """
    record = explain_selection(result)
    sink = logger if logger is not None else _default_logger()
    for line in selection_log_lines(record):
        sink.info(line)
    return record


def _default_logger() -> Any:
    """Return the engine logger, falling back to the standard library."""
    try:
        from ..core import get_logger

        return get_logger(__name__)
    except Exception:
        import logging

        return logging.getLogger(__name__)


def iter_selected_agents(record: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    """Yield the per-agent records inside an audit record."""
    return tuple(record.get(RECORD_AGENTS_KEY, ()))
