# -*- coding: utf-8 -*-
"""
Vibe Check MCP - Your AI coding safety net with senior engineer collaborative reasoning.

Because getting 90% done and then stuck for weeks sucks.

This is an MCP (Model Context Protocol) server that provides anti-pattern detection
and senior engineer mentoring for AI-assisted coding projects.

Key Features:
- Senior engineer collaborative reasoning with interrupt mode
- Fast pattern detection without external API calls  
- Deep analysis with Claude-powered reasoning
- Educational explanations and real-world case studies
- Native MCP protocol integration with sub-millisecond components

For more information, visit: https://github.com/kesslerio/vibe-check-mcp
"""

# CRITICAL: Fix environment variables before any fastmcp imports
import os
# Handle LOG_LEVEL that causes pydantic validation errors in FastMCP
_original_log_level = os.environ.get('LOG_LEVEL', None)
if _original_log_level and _original_log_level.lower() in ['debug', 'info', 'warning', 'error', 'critical']:
    if _original_log_level.lower() == 'error':
        # Convert lowercase 'error' to uppercase 'ERROR' for FastMCP validation
        os.environ['LOG_LEVEL'] = 'ERROR'
    elif _original_log_level != _original_log_level.upper():
        os.environ['LOG_LEVEL'] = _original_log_level.upper()

# Import main server functions for easy access
from .server import run_server
from .core.pattern_detector import PatternDetector
from .core.educational_content import EducationalContentGenerator
from .utils.version_utils import get_version

__version__ = get_version()
__author__ = "Vibe Check MCP Development Team"
__email__ = "hello@kessler.io"

__all__ = [
    "PatternDetector",
    "EducationalContentGenerator", 
    "run_server",
    "__version__"
]