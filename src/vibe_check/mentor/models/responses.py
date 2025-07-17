"""
Response-related data models.

Contains data structures for handling disagreements and response types
in the collaborative reasoning system.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class DisagreementData:
    """Structured disagreement between personas"""

    topic: str
    positions: List[
        Dict[str, Any]
    ]  # [{"personaId": "...", "position": "...", "arguments": [...]}]