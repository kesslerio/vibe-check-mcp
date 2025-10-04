"""
Issue Analysis Package

Modular GitHub issue analysis with pattern detection and optional Claude CLI integration.

Public API:
- analyze_issue: Main entry point for issue analysis
- analyze_issue_async: Async version of analyze_issue
- analyze_issue_legacy: Legacy compatibility function
- get_enhanced_github_analyzer: Factory for analyzer instances
- get_github_analyzer: Legacy factory (backward compat)
- EnhancedGitHubIssueAnalyzer: Main analyzer class
- GitHubIssueAnalyzer: Backward compatibility alias
"""

from .analyzer import EnhancedGitHubIssueAnalyzer, GitHubIssueAnalyzer
from .api import (
    analyze_issue,
    analyze_issue_async,
    analyze_issue_legacy,
    get_enhanced_github_analyzer,
    get_github_analyzer,
)
from .models import IssueLabel

__all__ = [
    # Main API functions
    "analyze_issue",
    "analyze_issue_async",
    "analyze_issue_legacy",
    # Factory functions
    "get_enhanced_github_analyzer",
    "get_github_analyzer",
    # Classes
    "EnhancedGitHubIssueAnalyzer",
    "GitHubIssueAnalyzer",
    "IssueLabel",
]
