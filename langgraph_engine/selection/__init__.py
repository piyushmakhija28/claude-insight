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
    explainability fields and a non-empty knowledge-graph edge path.

Windows-safe: ASCII only.
"""

from .catalogue import AgentRecord, CatalogueUnavailable, LibraryCatalogue, SkillRecord, load_catalogue
from .ids import candidate_refs, normalise_ref
from .kg_adapter import DomainKgAdapter, KgEdge, Parsed, ParseError
from .lexicon import Lexicon
from .risk import RiskSignal, TruncatedRiskSignal, probe_builder_coverage
from .selector import Degraded, EdgeStep, Match, SelectionResult, select_agents

__all__ = [
    "AgentRecord",
    "CatalogueUnavailable",
    "Degraded",
    "DomainKgAdapter",
    "EdgeStep",
    "KgEdge",
    "LibraryCatalogue",
    "Lexicon",
    "Match",
    "Parsed",
    "ParseError",
    "RiskSignal",
    "SelectionResult",
    "SkillRecord",
    "TruncatedRiskSignal",
    "candidate_refs",
    "load_catalogue",
    "normalise_ref",
    "probe_builder_coverage",
    "select_agents",
]
