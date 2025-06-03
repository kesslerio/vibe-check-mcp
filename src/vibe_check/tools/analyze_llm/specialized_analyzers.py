"""
Specialized LLM Analyzers

Provides specialized analysis tools for different content types including
pull requests, code, issues, and GitHub issue vibe checks.
"""

import logging
from typing import Dict, Any, Optional, List

from ..shared.claude_integration import analyze_content_async
from ..shared.github_abstraction import get_default_github_operations
from .llm_models import ExternalClaudeResponse
from .text_analyzer import analyze_text_llm

logger = logging.getLogger(__name__)


async def analyze_pr_llm(
    pr_diff: str,
    pr_description: str = "",
    file_changes: Optional[List[str]] = None,
    timeout_seconds: int = 90
) -> ExternalClaudeResponse:
    """
    🧠 Comprehensive PR review using Claude CLI reasoning.
    
    This tool provides deep PR analysis with LLM-powered reasoning including
    anti-pattern detection, security analysis, and code quality assessment.
    For fast direct PR analysis, use analyze_pr_nollm instead.
    
    Args:
        pr_diff: The full diff content of the pull request
        pr_description: Description/title of the pull request
        file_changes: List of changed files for context
        timeout_seconds: Maximum time to wait for analysis
        
    Returns:
        Comprehensive Claude CLI PR review results
    """
    logger.info("Starting external PR review")
    
    # Build context
    context_parts = []
    if pr_description:
        context_parts.append(f"PR Description: {pr_description}")
    if file_changes:
        context_parts.append(f"Changed files: {', '.join(file_changes)}")
    
    additional_context = "\n".join(context_parts) if context_parts else None
    
    return await analyze_text_llm(
        content=pr_diff,
        task_type="pr_review",
        additional_context=additional_context,
        timeout_seconds=timeout_seconds
    )


async def analyze_code_llm(
    code_content: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    timeout_seconds: int = 60
) -> ExternalClaudeResponse:
    """
    🧠 Deep code analysis using Claude CLI reasoning.
    
    This tool provides comprehensive code analysis with LLM-powered reasoning
    for anti-pattern detection, security vulnerabilities, and maintainability.
    
    Args:
        code_content: The code to analyze
        file_path: Optional file path for context
        language: Programming language for specialized analysis
        timeout_seconds: Maximum time to wait for analysis
        
    Returns:
        Detailed Claude CLI code analysis results
    """
    logger.info(f"Starting external code analysis for {language or 'unknown'} code")
    
    # Build context
    context_parts = []
    if file_path:
        context_parts.append(f"File: {file_path}")
    if language:
        context_parts.append(f"Language: {language}")
    
    additional_context = "\n".join(context_parts) if context_parts else None
    
    return await analyze_text_llm(
        content=code_content,
        task_type="code_analysis",
        additional_context=additional_context,
        timeout_seconds=timeout_seconds
    )


async def analyze_issue_llm(
    issue_content: str,
    issue_title: str = "",
    issue_labels: Optional[List[str]] = None,
    timeout_seconds: int = 60
) -> ExternalClaudeResponse:
    """
    🧠 Deep GitHub issue analysis using Claude CLI reasoning.
    
    This tool provides comprehensive issue analysis with LLM-powered reasoning
    for anti-pattern prevention, requirements quality, and implementation guidance.
    For fast direct issue analysis, use analyze_issue_nollm instead.
    
    Args:
        issue_content: The issue body/content
        issue_title: Title of the issue
        issue_labels: List of issue labels for context
        timeout_seconds: Maximum time to wait for analysis
        
    Returns:
        Comprehensive Claude CLI issue analysis with anti-pattern prevention guidance
    """
    logger.info("Starting external issue analysis")
    
    # Build context
    context_parts = []
    if issue_title:
        context_parts.append(f"Issue Title: {issue_title}")
    if issue_labels:
        context_parts.append(f"Labels: {', '.join(issue_labels)}")
    
    additional_context = "\n".join(context_parts) if context_parts else None
    
    return await analyze_text_llm(
        content=issue_content,
        task_type="issue_analysis",
        additional_context=additional_context,
        timeout_seconds=timeout_seconds
    )


async def analyze_github_issue_llm(
    issue_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    post_comment: bool = True,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard",
    timeout_seconds: int = 90
) -> Dict[str, Any]:
    """
    🧠 Comprehensive GitHub issue vibe check using Claude CLI reasoning.
    
    This tool fetches the GitHub issue, analyzes it for anti-patterns and engineering
    guidance using Claude CLI, and optionally posts a friendly coaching comment.
    For fast direct issue analysis, use analyze_issue_nollm instead.
    
    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        post_comment: Whether to post analysis as GitHub comment (default: True)
        analysis_mode: "quick" or "comprehensive" analysis (default: "comprehensive")
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
        timeout_seconds: Maximum time to wait for analysis (default: 90)
        
    Returns:
        Comprehensive Claude CLI vibe check analysis with GitHub integration
    """
    logger.info(f"Starting external GitHub issue vibe check for {repository}#{issue_number}")
    
    # Use the GitHub abstraction layer
    github_ops = get_default_github_operations()
    
    # Check authentication first
    auth_result = github_ops.check_authentication()
    if not auth_result.success:
        return {
            "status": "error",
            "error": "GitHub authentication not available",
            "solution": auth_result.error or "Check GitHub authentication"
        }
    
    try:
        # Fetch issue data using abstraction layer
        issue_result = github_ops.get_issue(repository, issue_number)
        if not issue_result.success:
            return {
                "status": "error",
                "error": f"Failed to fetch issue: {issue_result.error}",
                "issue_number": issue_number,
                "repository": repository
            }
        
        issue = issue_result.data
        
        # Build comprehensive issue context
        issue_context = f"""# GitHub Issue Analysis
        
**Issue:** {issue.title}
**Repository:** {repository}
**Author:** {issue.user_login}
**State:** {issue.state}
**Labels:** {', '.join(issue.labels) if issue.labels else 'None'}

**Issue Content:**
{issue.body or 'No content provided'}
"""
        
        # Create vibe check prompt based on detail level
        detail_instructions = {
            "brief": "Provide a concise 3-section analysis with key points only.",
            "standard": "Provide a balanced analysis with practical guidance and clear recommendations.",
            "comprehensive": "Provide detailed analysis with extensive educational content, examples, and learning opportunities."
        }
        
        detail_instruction = detail_instructions.get(detail_level, detail_instructions["standard"])
        
        vibe_prompt = f"""You are a friendly engineering coach providing a "vibe check" on this GitHub issue. Focus on preventing common engineering anti-patterns while encouraging good practices.

{detail_instruction}

{issue_context}

Please provide a vibe check analysis in this format:

## 🎯 Vibe Check Summary
[One-sentence friendly assessment]

## 🔍 Engineering Guidance
- Research Phase: [Have we done our homework on existing solutions?]
- POC Needs: [Do we need to prove basic functionality first?]
- Complexity Check: [Is the proposed complexity justified?]

## 💡 Friendly Recommendations
[3-5 practical, encouraging recommendations]

## 🎓 Learning Opportunities  
[2-3 educational suggestions based on patterns detected]

Use friendly, coaching language that helps developers learn rather than intimidate."""
        
        # Run external Claude analysis
        result = await analyze_text_llm(
            content=vibe_prompt,
            task_type="issue_analysis",
            additional_context=f"Vibe check for GitHub issue {repository}#{issue_number}",
            timeout_seconds=timeout_seconds
        )
        
        # Build response
        response = {
            "status": "vibe_check_complete",
            "issue_number": issue_number,
            "repository": repository,
            "analysis_mode": analysis_mode,
            "claude_analysis": result.output if result.success else None,
            "analysis_error": result.error if not result.success else None,
            "comment_posted": False,
            "github_implementation": issue_result.implementation
        }
        
        # Post comment if requested and analysis succeeded
        if post_comment and result.success and result.output:
            comment_body = f"""## 🎯 Comprehensive Vibe Check

{result.output}

---
*This vibe check was generated by the Vibe Check MCP framework using external Claude CLI for enhanced analysis.*"""
            
            comment_result = github_ops.post_issue_comment(repository, issue_number, comment_body)
            response["comment_posted"] = comment_result.success
            
            if not comment_result.success:
                response["comment_error"] = f"Failed to post comment: {comment_result.error}"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in GitHub issue vibe check: {e}")
        return {
            "status": "error",
            "error": str(e),
            "issue_number": issue_number,
            "repository": repository
        }