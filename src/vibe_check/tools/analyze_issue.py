"""
Backward Compatibility Shim for analyze_issue

This module maintains backward compatibility by re-exporting the issue analysis
functionality from the refactored issue_analysis package.

All new code should import from vibe_check.tools.issue_analysis instead.
This module exists solely to preserve existing import paths.

Issue #276: Refactored from 1,352-line monolithic file into modular package.
"""

# Re-export all public API from the issue_analysis package
from .issue_analysis import (
    analyze_issue,
    analyze_issue_async,
    analyze_issue_legacy,
    get_enhanced_github_analyzer,
    get_github_analyzer,
    EnhancedGitHubIssueAnalyzer,
    GitHubIssueAnalyzer,
    IssueLabel,
)

# Re-export ExternalClaudeCli and ClaudeCliResult from analyze_llm_backup
# These were previously imported in analyze_issue.py for Claude CLI integration
from .analyze_llm_backup import ExternalClaudeCli, ClaudeCliResult

__all__ = [
    "analyze_issue",
    "analyze_issue_async",
    "analyze_issue_legacy",
    "get_enhanced_github_analyzer",
    "get_github_analyzer",
    "EnhancedGitHubIssueAnalyzer",
    "GitHubIssueAnalyzer",
    "IssueLabel",
    "ExternalClaudeCli",
    "ClaudeCliResult",
]
