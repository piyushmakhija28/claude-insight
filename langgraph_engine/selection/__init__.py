"""Knowledge-graph-driven agent and skill selection (PRD FR-10 / SRS FR-22).

Every agent name, skill name and domain slug this package works with is read at
runtime from the sibling ``claude-global-library`` master catalogues. No such
name appears as a string literal anywhere in this package -- that property is
the requirement, and ``tests/test_kg_selection.py`` asserts it by parsing every
module here and intersecting its string literals against the live catalogue.

Module roles:

``ids``
    Catalogue-aware reference normalisation across the five identifier
    conventions the library uses.
``catalogue``
    The single naming authority: agents, skills and domains loaded from
    ``knowledge-graph/_master/*_all.json``, plus persona-path resolution for
    the dispatch contract.
``kg_adapter``
    ADR-015 domain reader. Three container forms, three edge-type keys, two
    endpoint-key conventions and domain-local opaque aliases. A parse failure
    is a typed error, never an empty edge list.
``lexicon``
    Inverse-document-frequency scorer built from catalogue prose, so term
    weighting is derived rather than declared.
``risk``
    The call-graph risk signal and its coverage precondition, which is what
    keeps a truncated builder off the selection path.
``selector``
    ``select_agents`` -- ranked matches, each carrying the five SRS FR-23
    explainability fields and a non-empty knowledge-graph edge path, or one of
    the three named fallback states SRS FR-24 requires. ``no_match``,
    ``low_confidence`` and ``unavailable`` stay distinct, because a caller
    deciding between widening, escalating and retrying needs to know which one
    it is.
``explainability``
    ``emit_selection`` -- the SRS FR-23 audit record. Copies the five fields
    out of an outcome and refuses, rather than padding, when one is absent.
    Reads the outcome structurally, so it imports no selector type and carries
    through outcome states it has never seen.

Windows-safe: ASCII only.
"""

from .catalogue import AgentRecord, CatalogueUnavailable, LibraryCatalogue, SkillRecord, load_catalogue
from .explainability import (
    FR23_FIELDS,
    IncompleteSelectionRecord,
    SelectionShapeChanged,
    emit_selection,
    explain_match,
    explain_selection,
)
from .ids import candidate_refs, normalise_ref
from .kg_adapter import DomainKgAdapter, KgEdge, Parsed, ParseError
from .lexicon import Lexicon
from .risk import RiskSignal, TruncatedRiskSignal, probe_builder_coverage
from .selector import (
    OUTCOME_LOW_CONFIDENCE,
    OUTCOME_NO_MATCH,
    OUTCOME_SELECTED,
    OUTCOME_UNAVAILABLE,
    REASON_OUTCOMES,
    ConfidenceFloorOutOfRange,
    Degraded,
    EdgeStep,
    Match,
    SelectionResult,
    UnmappedDegradedReason,
    outcome_for,
    select_agents,
)

__all__ = [
    "OUTCOME_LOW_CONFIDENCE",
    "OUTCOME_NO_MATCH",
    "OUTCOME_SELECTED",
    "OUTCOME_UNAVAILABLE",
    "REASON_OUTCOMES",
    "AgentRecord",
    "CatalogueUnavailable",
    "ConfidenceFloorOutOfRange",
    "Degraded",
    "DomainKgAdapter",
    "EdgeStep",
    "FR23_FIELDS",
    "IncompleteSelectionRecord",
    "KgEdge",
    "LibraryCatalogue",
    "Lexicon",
    "Match",
    "Parsed",
    "ParseError",
    "RiskSignal",
    "SelectionResult",
    "SelectionShapeChanged",
    "SkillRecord",
    "TruncatedRiskSignal",
    "UnmappedDegradedReason",
    "candidate_refs",
    "emit_selection",
    "explain_match",
    "explain_selection",
    "load_catalogue",
    "normalise_ref",
    "outcome_for",
    "probe_builder_coverage",
    "select_agents",
]
