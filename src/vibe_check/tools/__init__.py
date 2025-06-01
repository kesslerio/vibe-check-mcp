"""
Vibe Check MCP MCP Tools

This module contains the MCP tool implementations that wrap the core 
anti-pattern detection engine for use via the Model Context Protocol.

All tools maintain the validated 87.5% detection accuracy from Phase 1.
"""

from .demo_tool import demo_analyze_text

__all__ = ["demo_analyze_text"]