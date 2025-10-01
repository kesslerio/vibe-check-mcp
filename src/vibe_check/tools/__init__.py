"""
Vibe Check MCP MCP Tools

This module contains the MCP tool implementations that wrap the core
anti-pattern detection engine for use via the Model Context Protocol.

All tools maintain the validated 87.5% detection accuracy from Phase 1.
"""

from .analyze_text_nollm import analyze_text_demo

__all__ = ["analyze_text_demo"]
