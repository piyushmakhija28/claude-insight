"""Inverse-document-frequency scoring over catalogue prose.

A hand-written stopword list is a hardcoded list, and the requirement this
package implements exists to remove those. It is also fragile: the words that
carry no signal in a library of 508 agents and 996 skills are not the words
that carry no signal in English. "Engineer" appears in hundreds of records here
and discriminates nothing, while ordinary English stopword lists would keep it
and drop nothing useful.

So term weight is measured instead of declared. Every catalogue record is one
document; a term's weight is its inverse document frequency across that corpus.
Terms occurring in nearly every document approach zero weight and drop out on
their own, which is what a stopword list was trying to approximate.

Windows-safe: ASCII only.
"""

import math
import re
from typing import Dict, Iterable, Mapping, Sequence, Set

_TOKEN_RE = re.compile(r"[a-z0-9]+")

MIN_TOKEN_LENGTH = 3

BM25_K1 = 1.2
BM25_B = 0.75


def tokenize(text: str) -> Set[str]:
    """Split text into the lower-cased alphanumeric terms used for scoring.

    Args:
        text: Free text from a task description or a catalogue record.

    Returns:
        The distinct terms of at least :data:`MIN_TOKEN_LENGTH` characters.
        Term weighting, not length, does the discriminating; the length floor
        only removes fragments that carry no lexical identity at all.
    """
    if not text:
        return set()
    return {token for token in _TOKEN_RE.findall(text.lower()) if len(token) >= MIN_TOKEN_LENGTH}


class Lexicon:
    """Term weights derived from a corpus of catalogue documents."""

    def __init__(self, documents: Iterable[str]):
        """Compute inverse document frequency over ``documents``.

        Args:
            documents: One string per catalogue record. The corpus size is
                recorded so that weights can be interpreted, and an empty
                corpus yields uniform weights rather than a division error.
        """
        frequencies: Dict[str, int] = {}
        total = 0
        length_sum = 0
        for document in documents:
            total += 1
            terms = tokenize(document)
            length_sum += len(terms)
            for term in terms:
                frequencies[term] = frequencies.get(term, 0) + 1
        self._document_count = total
        self._frequencies: Mapping[str, int] = frequencies
        self._average_length = (length_sum / total) if total else 1.0

    @property
    def document_count(self) -> int:
        """Return the number of documents the weights were measured over."""
        return self._document_count

    @property
    def vocabulary_size(self) -> int:
        """Return the number of distinct terms observed in the corpus."""
        return len(self._frequencies)

    def weight(self, term: str) -> float:
        """Return the inverse document frequency weight of one term.

        A term absent from the corpus is treated as maximally rare rather than
        as weightless: an unusual word in a task description is a strong signal
        precisely because the corpus has not diluted it.
        """
        if self._document_count == 0:
            return 1.0
        occurrences = self._frequencies.get(term, 0)
        return math.log((self._document_count + 1.0) / (occurrences + 1.0))

    def median_weight(self) -> float:
        """Return the median term weight across the observed vocabulary.

        Used as the reference scale for turning a raw evidence total into an
        absolute confidence. Deriving it from the corpus rather than fixing a
        constant keeps the meaning of a given confidence stable as the library
        grows, and removes a magic number that would silently go stale.
        """
        if not self._frequencies:
            return 1.0
        weights = sorted(self.weight(term) for term in self._frequencies)
        return weights[len(weights) // 2]

    def score(self, query_terms: Set[str], document_text: str) -> float:
        """Score a document against a query, normalised for document length.

        Length normalisation is not a refinement here, it is load-bearing. The
        catalogue's record prose varies from a bare name to several hundred
        words, and an unnormalised sum of term weights hands the win to
        whichever record simply says more. Measured against the 37 sprint
        issues, the unnormalised form pulled unrelated long-description agents
        to the top of most queries. The correction is the standard Okapi BM25
        length term, with per-document term frequency collapsed to presence
        because catalogue prose repeats little.

        Args:
            query_terms: Terms from the task description, already tokenized.
            document_text: The candidate record's profile prose.

        Returns:
            The length-normalised weight of the overlap. Zero when nothing
            overlaps, which callers treat as "no lexical evidence" rather than
            as a low-confidence match.
        """
        if not query_terms:
            return 0.0
        document_terms = tokenize(document_text)
        if not document_terms:
            return 0.0
        overlap = query_terms & document_terms
        if not overlap:
            return 0.0
        normaliser = BM25_K1 * (1.0 - BM25_B + BM25_B * (len(document_terms) / (self._average_length or 1.0))) + 1.0
        saturation = (BM25_K1 + 1.0) / normaliser
        return sum(self.weight(term) for term in overlap) * saturation

    def informative_terms(self, terms: Set[str], quantile: float = 0.0) -> Set[str]:
        """Drop terms whose weight falls at or below ``quantile`` of the corpus.

        Args:
            terms: Candidate query terms.
            quantile: Fraction of the corpus weight range to discard from the
                bottom. Zero keeps everything, which is the default because
                the scorer already attenuates common terms.

        Returns:
            The retained terms.
        """
        if not terms or quantile <= 0.0:
            return set(terms)
        weights: Sequence[float] = sorted(self.weight(term) for term in terms)
        cutoff = weights[min(len(weights) - 1, int(len(weights) * quantile))]
        return {term for term in terms if self.weight(term) > cutoff}
