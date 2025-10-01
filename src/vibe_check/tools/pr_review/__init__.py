"""
Modular PR Review Tool

This module provides a modularized pull request review system that
breaks down the large monolithic PRReviewTool into focused components.

Architecture:
- main.py: Main orchestrator and entry point
- data_collector.py: GitHub data collection and API interactions
- size_classifier.py: Multi-dimensional PR size classification
- context_analyzer.py: Review context and re-review detection
- prompt_generator.py: Claude prompt creation and formatting
- claude_integration.py: External Claude CLI integration
- fallback_analyzer.py: Non-Claude analysis methods
- github_integration.py: GitHub API operations and posting
- output_formatter.py: Result formatting and comment generation
- utils.py: Shared utilities and helper functions

This modular design ensures each component is <700 lines and has a single responsibility.
"""

from .main import review_pull_request

__all__ = ["review_pull_request"]
