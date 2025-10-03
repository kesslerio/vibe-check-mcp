"""Severity level helpers for normalized mentor outputs."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Dict


SEVERITY_MAPPING: Dict[str, str]


class SeverityLevel(str, Enum):
    """Normalized severity levels surfaced to users."""

    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"


SEVERITY_MAPPING = {
    "minor": SeverityLevel.CAUTION.value,
    "moderate": SeverityLevel.WARNING.value,
    "major": SeverityLevel.CRITICAL.value,
}


class SeverityMapping:
    """Utility for normalizing severity values from various sources."""

    DEFAULT_LEVEL: SeverityLevel = SeverityLevel.WARNING
    _PRIMARY_MAPPING: Dict[str, SeverityLevel] = {
        key: SeverityLevel(value)
        for key, value in (
            ("minor", SEVERITY_MAPPING["minor"]),
            ("moderate", SEVERITY_MAPPING["moderate"]),
            ("major", SEVERITY_MAPPING["major"]),
        )
    }
    _ALIASES: Dict[str, str] = {
        "low": "minor",
        "caution": "minor",
        "medium": "moderate",
        "warning": "moderate",
        "severe": "major",
        "high": "major",
        "critical": "major",
    }

    @classmethod
    @lru_cache(maxsize=32)
    def resolve(cls, value: str | SeverityLevel | None) -> SeverityLevel:
        """Map arbitrary severity strings onto normalized levels."""

        if not value:
            return cls.DEFAULT_LEVEL

        if isinstance(value, SeverityLevel):
            return value

        normalized = value.strip().lower()
        if normalized in cls._PRIMARY_MAPPING:
            return cls._PRIMARY_MAPPING[normalized]

        canonical = cls._ALIASES.get(normalized)
        if canonical:
            return cls._PRIMARY_MAPPING[canonical]

        return cls.DEFAULT_LEVEL


def normalize_severity(value: str | SeverityLevel | None) -> str:
    """Normalize severity string to the canonical level name."""

    return SeverityMapping.resolve(value).value


__all__ = [
    "SeverityLevel",
    "SeverityMapping",
    "normalize_severity",
    "SEVERITY_MAPPING",
]
