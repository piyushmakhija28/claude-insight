"""Catalogue-aware normalisation of knowledge-graph node references.

The library writes the same node five different ways. All five were measured
across the 100 domain graphs and the three master catalogues. The examples
below use a placeholder slug rather than a real library name, because a real
name written here would itself be the hardcoded knowledge SRS FR-22 removes --
and the suite's literal detector would rightly flag it:

===========================  ==================================  ==============
form                         example                             seen in
===========================  ==================================  ==============
colon + hyphenated slug      ``<kind>:some-role-name``           domain graphs
colon + underscored slug     ``<kind>:some_role_name``           master graphs
hyphen-prefixed slug         ``<kind>-some-role-name``           domain graphs
underscored, no separator    ``<kind>_some_role_name``           domain graphs
bare slug                    ``some-role-name``                  domain graphs
opaque domain-local code     ``A001`` / ``S013``                 domain graphs
===========================  ==================================  ==============

Stripping a leading type word unconditionally is WRONG and the library proves
it: 12 names -- 3 agents and 9 skills -- genuinely begin with one. Measured
against library 29.73.0, none of their stripped forms names anything else in
the catalogue, so the failure mode is not a wrong bind but a silent loss: the
reference resolves to nothing and the node vanishes from the graph, which is
indistinguishable from a genuine absence. That is the conflation ADR-015 exists
to prevent.

The fix is therefore not an ordering trick but a fallback: every plausible
reading of a reference is offered, and the catalogue decides which one is a
name. The reference exactly as written comes first because it is the most
literal reading, and a stripped form is only ever reached when the written form
is not a name the catalogue knows.

Windows-safe: ASCII only.
"""

from typing import List, Tuple

_TYPED_PREFIX_SEPARATORS: Tuple[str, ...] = (":", "-", "_")


def normalise_ref(raw: object) -> str:
    """Fold a raw reference to the library's canonical slug casing.

    Lower-cases, trims surrounding whitespace and rewrites underscores to
    hyphens. Any leading type word is left in place -- removing it is a
    separate, catalogue-checked step performed by :func:`candidate_refs`.

    Args:
        raw: A reference value taken straight from knowledge-graph JSON. Any
            non-string (including ``None``) folds to the empty string rather
            than raising, because edge payloads are third-party data.

    Returns:
        The folded slug, or ``""`` when ``raw`` carries no usable text.
    """
    if not isinstance(raw, str):
        return ""
    return raw.strip().lower().replace("_", "-")


def candidate_refs(raw: object, type_words: Tuple[str, ...]) -> List[str]:
    """Enumerate the slugs ``raw`` could denote, most literal interpretation first.

    The first entry is always the reference exactly as written (folded). Any
    further entries strip one recognised type word from the front, one per
    accepted separator. A caller resolves the list in order against the
    catalogue and takes the first hit, so a name that legitimately begins with
    a type word wins over the interpretation that would truncate it.

    Args:
        raw: A reference value taken straight from knowledge-graph JSON.
        type_words: Node-type words that may appear as a prefix, supplied by
            the caller rather than declared here so that the vocabulary stays
            data-driven.

    Returns:
        An ordered, duplicate-free list of candidate slugs. Empty when ``raw``
        carries no usable text.
    """
    folded = normalise_ref(raw)
    if not folded:
        return []

    ordered = [folded]
    for word in type_words:
        for separator in _TYPED_PREFIX_SEPARATORS:
            marker = "{}{}".format(word, separator)
            if folded.startswith(marker) and len(folded) > len(marker):
                stripped = folded[len(marker) :]
                if stripped not in ordered:
                    ordered.append(stripped)
    return ordered
