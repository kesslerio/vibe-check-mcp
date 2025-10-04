"""Data models for issue analysis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IssueLabel:
    """Represents a GitHub issue label with equality and hashing support."""

    name: str

    def __eq__(self, other: object) -> bool:
        if isinstance(other, IssueLabel):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name
