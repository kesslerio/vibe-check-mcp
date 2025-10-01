"""
Pattern handling for collaborative reasoning.

This module provides pattern detection handlers and response templates
for different anti-patterns in the collaborative reasoning system.
"""

from .handler_registry import PatternHandlerRegistry
from .handlers.infrastructure import InfrastructurePatternHandler
from .handlers.custom_solution import CustomSolutionHandler
from .handlers.product_engineer import ProductEngineerHandler
from .handlers.ai_engineer import AIEngineerHandler

__all__ = [
    "PatternHandlerRegistry",
    "InfrastructurePatternHandler",
    "CustomSolutionHandler",
    "ProductEngineerHandler",
    "AIEngineerHandler",
]
