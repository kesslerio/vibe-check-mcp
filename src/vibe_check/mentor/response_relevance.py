"""
Utilities for validating relevance of mentor responses against query context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set


@dataclass(frozen=True)
class RelevanceResult:
    """Captured scoring details for relevance evaluations."""

    score: float
    matched_terms: Sequence[str]
    considered_terms: Sequence[str]
    passed: bool

    @property
    def has_matches(self) -> bool:
        return bool(self.matched_terms)


class ResponseRelevanceValidator:
    """Scores whether a static response references the important query context."""

    # Keep the stop word list intentionally small to avoid shipping an external dependency.
    _STOP_WORDS: Set[str] = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "have",
        "if",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "so",
        "that",
        "the",
        "their",
        "then",
        "there",
        "this",
        "to",
        "was",
        "we",
        "will",
        "with",
    }

    def __init__(self, minimum_score: float = 0.2, minimum_matches: int = 1) -> None:
        self.minimum_score = minimum_score
        self.minimum_matches = minimum_matches

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9\-/]+", text.lower())

    def _extract_terms(self, query: str, context: Dict[str, object]) -> List[str]:
        terms: List[str] = []

        terms.extend(self._tokenize(query))

        technologies = context.get("technologies")
        if isinstance(technologies, Iterable):
            for tech in technologies:
                if isinstance(tech, str):
                    terms.extend(self._tokenize(tech))

        for key in ("decision_points", "specific_features", "problem_type"):
            values = context.get(key)
            if isinstance(values, str):
                terms.extend(self._tokenize(values))
            elif isinstance(values, Iterable):
                for value in values:
                    if isinstance(value, str):
                        terms.extend(self._tokenize(value))

        unique_terms = []
        seen: Set[str] = set()
        for term in terms:
            if term in self._STOP_WORDS or len(term) < 3:
                continue
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        return unique_terms

    def score(
        self, query: str, response: str, context: Dict[str, object]
    ) -> RelevanceResult:
        terms = self._extract_terms(query, context)
        if not terms:
            # Without any meaningful terms, default to success to avoid over-blocking.
            return RelevanceResult(
                score=1.0, matched_terms=[], considered_terms=[], passed=True
            )

        response_tokens = set(self._tokenize(response))
        matched_terms = [term for term in terms if term in response_tokens]

        score = len(matched_terms) / float(len(terms))
        passed = (
            score >= self.minimum_score and len(matched_terms) >= self.minimum_matches
        )
        return RelevanceResult(
            score=score,
            matched_terms=matched_terms,
            considered_terms=terms,
            passed=passed,
        )
