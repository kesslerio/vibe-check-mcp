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
    timeout_seconds: int = 90,
    model: str = "sonnet"
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
        model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
        
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
        timeout_seconds=timeout_seconds,
        model=model
    )


async def analyze_code_llm(
    code_content: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    timeout_seconds: int = 60,
    model: str = "sonnet"
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
        model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
        
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
        timeout_seconds=timeout_seconds,
        model=model
    )


async def analyze_issue_llm(
    issue_content: str,
    issue_title: str = "",
    issue_labels: Optional[List[str]] = None,
    timeout_seconds: int = 60,
    model: str = "sonnet"
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
        model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
        
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
        timeout_seconds=timeout_seconds,
        model=model
    )


async def analyze_github_issue_llm(
    issue_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    post_comment: bool = True,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard",
    timeout_seconds: int = 90,
    model: str = "sonnet"
) -> Dict[str, Any]:
    """
    🧠 Comprehensive GitHub issue vibe check using Claude CLI reasoning.
    
    This tool fetches the GitHub issue, analyzes it for anti-patterns and engineering
    guidance using Claude CLI, and optionally posts a friendly coaching comment.
    For fast direct issue analysis, use analyze_issue_nollm instead.
    
    IMPORTANT: When this tool returns a "comment_url" or "user_message" field, 
    ALWAYS include the full GitHub URL in your response to help users access 
    the posted comment directly.
    
    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        post_comment: Whether to post analysis as GitHub comment (default: True)
        analysis_mode: "quick" or "comprehensive" analysis (default: "comprehensive")
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
        timeout_seconds: Maximum time to wait for analysis (default: 90)
        model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
        
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
        
        # Enhanced prompt with integration pattern detection
        integration_context = ""
        try:
            from ..integration_pattern_analysis import quick_technology_scan
            tech_scan = quick_technology_scan(issue_context)
            if tech_scan.get("status") == "technologies_detected":
                tech_list = [t["technology"] for t in tech_scan.get("technologies", [])]
                integration_context = f"""
**Integration Technologies Detected:** {', '.join(tech_list)}
**Integration Alert:** Check for official alternatives before custom development
"""
        except Exception:
            pass  # Continue without integration context if it fails

        # Check for doom loop patterns in issue content
        doom_loop_context = ""
        try:
            from ..doom_loop_analysis import analyze_text_for_doom_loops
            doom_analysis = analyze_text_for_doom_loops(issue_context, tool_name="analyze_github_issue_llm")
            if doom_analysis.get("status") == "doom_loop_detected":
                severity = doom_analysis.get("severity", "unknown")
                doom_loop_context = f"""
**PRODUCTIVITY ALERT:** {severity.upper()} doom loop patterns detected in issue discussion
**Pattern:** {doom_analysis.get("pattern_type", "").replace('_', ' ').title()}
**Intervention Needed:** Focus on concrete next steps over endless analysis
"""
        except Exception:
            pass  # Continue without doom loop context if it fails

        vibe_prompt = f"""You are a friendly engineering coach providing a "vibe check" on this GitHub issue. Focus on preventing common engineering anti-patterns while encouraging good practices.

SPECIAL ATTENTION: This issue mentions integration technologies. Pay special attention to:
- Whether official solutions (SDKs, containers, APIs) are being considered
- Signs of custom development when standard approaches might work
- Integration complexity that could be simplified

PRODUCTIVITY FOCUS: If doom loop patterns are detected, emphasize:
- Moving from analysis to concrete action
- Setting time limits for decisions
- Implementing simplest working solution first
- Avoiding perfectionist paralysis

{detail_instruction}

{issue_context}
{integration_context}
{doom_loop_context}

Please provide a vibe check analysis in this format:

## 🎯 Vibe Check Summary
[One-sentence friendly assessment]

## 🔍 Engineering Guidance
- Research Phase: [Have we done our homework on existing solutions? Any official alternatives?]
- POC Needs: [Do we need to prove basic functionality first? Test standard approaches?]
- Complexity Check: [Is the proposed complexity justified? Could official solutions work?]
- Integration Check: [If integrating with third-party services, are we using official approaches?]

## 💡 Friendly Recommendations
[3-5 practical, encouraging recommendations - prioritize checking official solutions for any detected technologies]

## 🎓 Learning Opportunities  
[2-3 educational suggestions based on patterns detected, include integration best practices if relevant]

Use friendly, coaching language that helps developers learn rather than intimidate. If integration technologies are detected, gently guide toward researching official solutions first."""
        
        # Run external Claude analysis
        result = await analyze_text_llm(
            content=vibe_prompt,
            task_type="issue_analysis",
            additional_context=f"Vibe check for GitHub issue {repository}#{issue_number}",
            timeout_seconds=timeout_seconds,
            model=model
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
*🤖 This vibe check was lovingly crafted by [Vibe Check MCP](https://github.com/kesslerio/vibe-check-mcp) using the Claude Code SDK. Because your code deserves better than just "looks good to me" 🚀*"""
            
            comment_result = github_ops.post_issue_comment(repository, issue_number, comment_body)
            response["comment_posted"] = comment_result.success
            
            if comment_result.success and comment_result.data.get("comment_url"):
                response["comment_url"] = comment_result.data["comment_url"]
                response["user_message"] = f"✅ Analysis posted to GitHub: {comment_result.data['comment_url']}"
                
            if not comment_result.success:
                response["comment_error"] = f"Failed to post comment: {comment_result.error}"
        
        # Sanitize any GitHub API URLs to frontend URLs
        from ..shared.github_helpers import sanitize_github_urls_in_response
        return sanitize_github_urls_in_response(response)
        
    except Exception as e:
        logger.error(f"Error in GitHub issue vibe check: {e}")
        return {
            "status": "error",
            "error": str(e),
            "issue_number": issue_number,
            "repository": repository
        }


async def analyze_github_pr_llm(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    post_comment: bool = True,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard",
    timeout_seconds: int = 120,
    model: str = "sonnet"
) -> Dict[str, Any]:
    """
    🧠 Comprehensive GitHub PR vibe check using Claude CLI reasoning.
    
    This tool fetches the GitHub PR, analyzes it for anti-patterns and engineering
    guidance using Claude CLI, and optionally posts a friendly coaching review.
    For fast direct PR analysis, use analyze_pr_nollm instead.
    
    IMPLEMENTS ISSUE #101: Intelligent pre-filtering and graceful degradation
    - Skips LLM analysis for PRs >1000 lines or >20 files
    - Falls back to fast analysis when LLM fails
    - Always returns useful response (never fails completely)
    
    IMPORTANT: When this tool returns a "comment_url" or "user_message" field, 
    ALWAYS include the full GitHub URL in your response to help users access 
    the posted review directly.
    
    Args:
        pr_number: GitHub PR number to analyze
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        post_comment: Whether to post analysis as GitHub review (default: True)
        analysis_mode: "quick" or "comprehensive" analysis (default: "comprehensive")
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
        timeout_seconds: Maximum time to wait for analysis (default: 120)
        model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
        
    Returns:
        Comprehensive Claude CLI vibe check analysis with GitHub integration
    """
    logger.info(f"Starting external GitHub PR vibe check for {repository}#{pr_number}")
    
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
        # Fetch PR data using abstraction layer
        pr_result = github_ops.get_pull_request(repository, pr_number)
        if not pr_result.success:
            return {
                "status": "error",
                "error": f"Failed to fetch PR: {pr_result.error}",
                "pr_number": pr_number,
                "repository": repository
            }
        
        pr = pr_result.data
        
        # PHASE 1 IMPLEMENTATION: Extract PR size data for intelligent filtering
        pr_size_data = {
            'number': pr.number,
            'title': pr.title,
            'additions': getattr(pr, 'additions', 0),
            'deletions': getattr(pr, 'deletions', 0), 
            'changed_files': getattr(pr, 'changed_files', 0)
        }
        
        # PHASE 1-4 IMPLEMENTATION: Complete analysis strategy with async processing
        from ...core.pr_filtering import analyze_with_fallback, should_use_llm_analysis
        from ..analyze_pr_nollm import analyze_pr_nollm
        from ..async_analysis.integration import start_async_analysis
        from ..async_analysis.config import DEFAULT_ASYNC_CONFIG
        
        # PHASE 4 CHECK: Determine if PR should use async processing
        async_config = DEFAULT_ASYNC_CONFIG
        if async_config.should_use_async_processing(pr_size_data):
            logger.info(
                f"PR {repository}#{pr_number} is massive - using async processing",
                extra={
                    "total_changes": pr_size_data.get("additions", 0) + pr_size_data.get("deletions", 0),
                    "changed_files": pr_size_data.get("changed_files", 0)
                }
            )
            
            # Start async analysis
            async_result = await start_async_analysis(
                pr_number=pr_number,
                repository=repository,
                pr_data=pr_size_data
            )
            
            # Sanitize GitHub URLs and return
            from ..shared.github_helpers import sanitize_github_urls_in_response
            return sanitize_github_urls_in_response(async_result)
        
        async def llm_analysis():
            """Perform LLM analysis for smaller PRs."""
            # Get PR diff for analysis using the fixed abstraction layer
            diff_result = github_ops.get_pull_request_diff(repository, pr_number)
            if not diff_result.success:
                raise Exception(f"Failed to fetch PR diff: {diff_result.error}")
            
            pr_diff = diff_result.data
            
            # Build comprehensive PR context
            pr_context = f"""# GitHub Pull Request Analysis
            
**PR:** {pr.title}
**Repository:** {repository}
**Author:** {pr.user_login}
**State:** {pr.state}
**Base:** {pr.base_ref} ← **Head:** {pr.head_ref}
**Labels:** {', '.join(pr.labels) if pr.labels else 'None'}

**PR Description:**
{pr.body or 'No description provided'}

**Code Changes:**
{pr_diff}
"""
            
            # Create vibe check prompt based on detail level
            detail_instructions = {
                "brief": "Provide a concise 3-section analysis with key points only.",
                "standard": "Provide a balanced analysis with practical guidance and clear recommendations.",
                "comprehensive": "Provide detailed analysis with extensive educational content, examples, and learning opportunities."
            }
            
            detail_instruction = detail_instructions.get(detail_level, detail_instructions["standard"])
            
            # Enhanced PR prompt with integration pattern detection
            pr_integration_context = ""
            try:
                from ..integration_pattern_analysis import analyze_integration_patterns_fast
                integration_analysis = analyze_integration_patterns_fast(pr_context, detail_level="brief")
                if integration_analysis.get("technologies_detected"):
                    tech_list = [t["technology"] for t in integration_analysis.get("technologies_detected", [])]
                    warning_level = integration_analysis.get("warning_level", "none")
                    pr_integration_context = f"""
**INTEGRATION ANALYSIS:**
- Technologies Detected: {', '.join(tech_list)}
- Warning Level: {warning_level}
- Integration Alert: Verify official alternatives are considered
"""
            except Exception:
                pass  # Continue without integration context if it fails

            # Check for doom loop patterns in PR content
            pr_doom_loop_context = ""
            try:
                from ..doom_loop_analysis import analyze_text_for_doom_loops
                doom_analysis = analyze_text_for_doom_loops(pr_context, tool_name="analyze_github_pr_llm")
                if doom_analysis.get("status") == "doom_loop_detected":
                    severity = doom_analysis.get("severity", "unknown")
                    pr_doom_loop_context = f"""
**PRODUCTIVITY ALERT:** {severity.upper()} analysis patterns detected in PR
**Pattern:** {doom_analysis.get("pattern_type", "").replace('_', ' ').title()}
**Focus:** Prioritize shipping working solution over perfect implementation
"""
            except Exception:
                pass  # Continue without doom loop context if it fails

            vibe_prompt = f"""You are a friendly engineering coach providing a "vibe check" on this GitHub pull request. Focus on preventing common engineering anti-patterns while encouraging good practices.

SPECIAL ATTENTION: Pay attention to integration patterns:
- Are official SDKs/containers being used instead of custom solutions?
- Is the development effort proportional to the integration complexity?
- Are there signs of reinventing existing solutions?

PRODUCTIVITY FOCUS: If analysis paralysis patterns are detected, emphasize:
- Shipping working solution over perfect implementation
- Iterative improvement over big-bang releases
- Real user feedback over theoretical optimization
- Time-boxed decisions and concrete milestones

{detail_instruction}

{pr_context}
{pr_integration_context}
{pr_doom_loop_context}

Please provide a vibe check analysis in this format:

## 🎯 PR Vibe Check Summary
[One-sentence friendly assessment of the overall PR quality]

## 🔍 Engineering Analysis
- Code Quality: [Structure, naming, organization, maintainability]
- Security & Performance: [Potential vulnerabilities, performance implications]
- Anti-Pattern Detection: [Infrastructure-without-implementation, integration over-engineering, complexity escalation]
- Integration Patterns: [If integrations present, are official solutions being used?]
- Testing & Documentation: [Test coverage, documentation updates needed]

## 💡 Friendly Recommendations
[3-5 practical, encouraging recommendations for improvement - include integration guidance if relevant]

## 🎓 Learning Opportunities  
[2-3 educational suggestions based on patterns detected, include integration best practices if applicable]

## ✅ Ready to Ship?
[Final recommendation: approve, request changes, or needs discussion]

Use friendly, coaching language that helps developers learn rather than intimidate. If integration technologies are detected, gently suggest verifying official alternatives."""
            
            # Run external Claude analysis
            result = await analyze_text_llm(
                content=vibe_prompt,
                task_type="pr_review",
                additional_context=f"Vibe check for GitHub PR {repository}#{pr_number}",
                timeout_seconds=timeout_seconds,
                model=model
            )
            
            if result.success:
                return {
                    "status": "vibe_check_complete",
                    "pr_number": pr_number,
                    "repository": repository,
                    "analysis_mode": analysis_mode,
                    "claude_analysis": result.output,
                    "github_implementation": pr_result.implementation
                }
            else:
                raise Exception(f"Claude analysis failed: {result.error}")
        
        def fast_analysis():
            """Perform fast analysis fallback."""
            return analyze_pr_nollm(
                pr_number=pr_number,
                repository=repository,
                analysis_mode="quick",
                detail_level=detail_level
            )
        
        # PHASE 1 IMPLEMENTATION: Use intelligent analysis with fallback
        analysis_result = await analyze_with_fallback(
            pr_data=pr_size_data,
            llm_analyzer_func=llm_analysis,
            fast_analyzer_func=fast_analysis
        )
        
        # Ensure we have the required fields for posting
        if 'pr_number' not in analysis_result:
            analysis_result['pr_number'] = pr_number
        if 'repository' not in analysis_result:
            analysis_result['repository'] = repository
        
        # Post review if requested and analysis succeeded
        if post_comment and analysis_result.get('claude_analysis'):
            review_body = f"""## 🎯 Comprehensive PR Vibe Check

{analysis_result['claude_analysis']}

---
*🤖 This vibe check was lovingly crafted by [Vibe Check MCP](https://github.com/kesslerio/vibe-check-mcp) using the Claude Code SDK. Because your code deserves better than just "looks good to me" 🚀*"""
            
            # For now, use create_and_submit_pull_request_review
            # TODO: Could enhance to use the abstraction layer when PR review methods are added
            try:
                from ..shared.github_helpers import get_github_client
                client = get_github_client()
                if client:
                    repo = client.get_repo(repository)
                    pr_obj = repo.get_pull(pr_number)
                    review = pr_obj.create_review(body=review_body, event="COMMENT")
                    analysis_result["comment_posted"] = True
                    
                    # Build PR review URL
                    review_url = f"https://github.com/{repository}/pull/{pr_number}#pullrequestreview-{review.id}"
                    analysis_result["comment_url"] = review_url
                    analysis_result["user_message"] = f"✅ Review posted to GitHub: {review_url}"
                else:
                    analysis_result["comment_error"] = "GitHub client not available"
            except Exception as e:
                analysis_result["comment_error"] = f"Failed to post review: {str(e)}"
        elif post_comment and not analysis_result.get('claude_analysis'):
            # Post a simpler comment for fast analysis mode
            if analysis_result.get('status') == 'large_pr_detected':
                review_body = f"""## 🎯 Large PR Analysis

{analysis_result.get('message', 'Large PR detected - providing fast analysis')}

### 📊 Size Metrics
- Files changed: {analysis_result.get('size_metrics', {}).get('changed_files', 'unknown')}
- Total changes: {analysis_result.get('size_metrics', {}).get('total_changes', 'unknown')} lines

### 💡 Recommendations
{analysis_result.get('recommendation', 'Consider splitting into smaller PRs for detailed review')}

---
*🤖 Fast analysis by [Vibe Check MCP](https://github.com/kesslerio/vibe-check-mcp) - Large PRs get pattern detection to ensure reliable response 🚀*"""
                
                try:
                    from ..shared.github_helpers import get_github_client
                    client = get_github_client()
                    if client:
                        repo = client.get_repo(repository)
                        pr_obj = repo.get_pull(pr_number)
                        review = pr_obj.create_review(body=review_body, event="COMMENT")
                        analysis_result["comment_posted"] = True
                        
                        # Build PR review URL
                        review_url = f"https://github.com/{repository}/pull/{pr_number}#pullrequestreview-{review.id}"
                        analysis_result["comment_url"] = review_url
                        analysis_result["user_message"] = f"✅ Fast analysis posted to GitHub: {review_url}"
                except Exception as e:
                    analysis_result["comment_error"] = f"Failed to post review: {str(e)}"
        
        # Sanitize any GitHub API URLs to frontend URLs
        from ..shared.github_helpers import sanitize_github_urls_in_response
        return sanitize_github_urls_in_response(analysis_result)
        
    except Exception as e:
        # PHASE 1 IMPLEMENTATION: Ultimate graceful degradation
        logger.error(f"Error in GitHub PR vibe check: {e}")
        return {
            "status": "error_fallback",
            "error": str(e),
            "pr_number": pr_number,
            "repository": repository,
            "message": "Analysis encountered errors but system ensured response",
            "note": "This implements graceful degradation from Issue #101 - system never fails completely"
        }