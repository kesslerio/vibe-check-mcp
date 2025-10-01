"""
Response generation for collaborative reasoning.

This module provides response coordination and generation functionality
for different engineering personas in the collaborative reasoning system.
"""

from .coordinator import ResponseCoordinator
from .generators.senior_engineer import SeniorEngineerGenerator
from .generators.product_engineer import ProductEngineerGenerator
from .generators.ai_engineer import AIEngineerGenerator
from .formatters.console import ConsoleFormatter

__all__ = [
    "ResponseCoordinator",
    "SeniorEngineerGenerator",
    "ProductEngineerGenerator",
    "AIEngineerGenerator",
    "ConsoleFormatter",
]
