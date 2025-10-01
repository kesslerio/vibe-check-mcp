"""
Persona data models for collaborative reasoning.

Contains the PersonaData class and related structures for representing
engineering personas in the collaborative reasoning system.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PersonaData:
    """Engineering persona definition - borrowed from Clear-Thought"""

    id: str
    name: str
    expertise: List[str]
    background: str
    perspective: str
    biases: List[str]
    communication: Dict[str, str]  # {"style": "...", "tone": "..."}
