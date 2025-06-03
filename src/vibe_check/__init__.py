# -*- coding: utf-8 -*-
"""
Vibe Check MCP: Engineering Anti-Pattern Detection & Prevention

A comprehensive system for detecting and preventing engineering anti-patterns
through validated detection algorithms and educational content generation.

Phase 1: ✅ Core Detection Engine (87.5% accuracy, 0% false positives)
Phase 2: ✅ FastMCP Server Integration

Usage:
    # MCP Server
    from vibe_check.server import run_server
    run_server()
    
    # Core Detection Engine
    from vibe_check.core import PatternDetector, EducationalContentGenerator
    
    detector = PatternDetector()
    educator = EducationalContentGenerator()
"""

from .core.pattern_detector import PatternDetector
from .core.educational_content import EducationalContentGenerator
from .server import run_server
from .utils.version_utils import get_version

__version__ = get_version()
__author__ = "Vibe Check MCP Development Team"

__all__ = [
    "PatternDetector",
    "EducationalContentGenerator", 
    "run_server",
    "__version__"
]