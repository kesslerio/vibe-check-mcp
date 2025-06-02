"""
Main PR Review Orchestrator

This is the main entry point for the modularized PR review system.
It orchestrates all the extracted components to provide comprehensive PR analysis.
"""

import logging
from typing import Dict, Any

from .data_collector import PRDataCollector
from .size_classifier import PRSizeClassifier  
from .context_analyzer import ReviewContextAnalyzer
from .claude_integration import ClaudeIntegration

logger = logging.getLogger(__name__)


async def review_pull_request(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    force_re_review: bool = False,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    Comprehensive PR review with modular architecture.
    
    This is the main entry point that replaces the monolithic PRReviewTool.
    
    Args:
        pr_number: PR number to review
        repository: Repository in format "owner/repo"
        force_re_review: Force re-review mode even if not auto-detected
        analysis_mode: "comprehensive" or "quick" analysis
        detail_level: "brief", "standard", or "comprehensive"
        
    Returns:
        Complete analysis results with GitHub integration status
    """
    try:
        logger.info(f"🤖 Starting modular PR review for PR #{pr_number}")
        
        # Initialize modular components
        data_collector = PRDataCollector()
        size_classifier = PRSizeClassifier()
        context_analyzer = ReviewContextAnalyzer()
        claude_integration = ClaudeIntegration()
        
        # Phase 1: Data Collection
        logger.info("📊 Phase 1: Collecting PR data...")
        pr_data = data_collector.collect_pr_data(pr_number, repository)
        if "error" in pr_data:
            return pr_data
        
        # Phase 2: Size Classification
        logger.info("📏 Phase 2: Classifying PR size...")
        size_analysis = size_classifier.classify_pr_size(pr_data)
        
        # Phase 3: Context Analysis
        logger.info("🔄 Phase 3: Analyzing review context...")
        review_context = context_analyzer.detect_re_review(pr_data, force_re_review)
        
        # Phase 4: Analysis Generation
        logger.info(f"🔍 Phase 4: Generating analysis (Mode: {analysis_mode}, Size: {size_analysis.get('overall_size', 'Unknown')})")
        
        # Check Claude availability
        claude_available = claude_integration.check_claude_availability()
        
        if claude_available and analysis_mode == "comprehensive":
            # Use Claude for comprehensive analysis
            analysis_result = await _generate_claude_analysis(
                claude_integration, pr_data, size_analysis, review_context, detail_level, pr_number
            )
        else:
            # Use fallback analysis
            analysis_result = _generate_fallback_analysis(
                pr_data, size_analysis, review_context, detail_level
            )
        
        # Phase 5: Result Compilation
        logger.info("📋 Phase 5: Compiling final results...")
        final_result = {
            "pr_number": pr_number,
            "repository": repository,
            "analysis_mode": analysis_mode,
            "size_analysis": size_analysis,
            "review_context": review_context,
            "analysis_result": analysis_result,
            "modular_architecture": {
                "data_collector": "✅ Extracted",
                "size_classifier": "✅ Extracted", 
                "context_analyzer": "✅ Extracted",
                "claude_integration": "✅ Extracted",
                "original_file_size": "1565 lines → modular components"
            }
        }
        
        logger.info(f"✅ Modular PR review completed for PR #{pr_number}")
        return final_result
        
    except Exception as e:
        logger.error(f"❌ Modular PR review failed: {e}")
        return {
            "error": f"PR review failed: {str(e)}",
            "pr_number": pr_number,
            "repository": repository
        }


async def _generate_claude_analysis(
    claude_integration: ClaudeIntegration,
    pr_data: Dict[str, Any],
    size_analysis: Dict[str, Any], 
    review_context: Dict[str, Any],
    detail_level: str,
    pr_number: int
) -> Dict[str, Any]:
    """Generate analysis using Claude integration."""
    # Simplified prompt for now - can be enhanced with full prompt generator
    prompt_content = f"""Analyze this pull request comprehensively.

PR Details:
- Title: {pr_data['metadata']['title']}
- Author: {pr_data['metadata']['author']}
- Size: {size_analysis['overall_size']}
- Files: {size_analysis['size_reasons']}
- Re-review: {review_context['is_re_review']}

Please provide a structured analysis with:
1. Overview
2. Strengths
3. Critical Issues
4. Suggestions
5. Recommendation (APPROVE/REQUEST_CHANGES/REJECT)
"""
    
    # Simplified data content
    data_content = f"""
## PR Metadata
- **Number:** {pr_data['metadata']['number']}
- **Title:** {pr_data['metadata']['title']}
- **Author:** {pr_data['metadata']['author']}
- **Branch:** {pr_data['metadata']['head_branch']} → {pr_data['metadata']['base_branch']}
- **Files Changed:** {pr_data['statistics']['files_count']}
- **Lines:** +{pr_data['statistics']['additions']}/-{pr_data['statistics']['deletions']}

## Files Changed
{chr(10).join([f"- {f.get('path', 'unknown')}" for f in pr_data.get('files', [])[:10]])}

## Diff Sample
{pr_data.get('diff', '')[:2000]}...
"""
    
    result = await claude_integration.run_claude_analysis(
        prompt_content=prompt_content,
        data_content=data_content,
        pr_number=pr_number,
        pr_data=pr_data
    )
    
    return result or {"analysis": "Claude analysis failed", "recommendation": "MANUAL_REVIEW"}


def _generate_fallback_analysis(
    pr_data: Dict[str, Any],
    size_analysis: Dict[str, Any],
    review_context: Dict[str, Any], 
    detail_level: str
) -> Dict[str, Any]:
    """Generate fallback analysis when Claude is unavailable."""
    
    return {
        "analysis_method": "fallback",
        "overview": f"Automated analysis of PR {pr_data['metadata']['number']} - {pr_data['metadata']['title']}",
        "size_assessment": f"PR classified as {size_analysis['overall_size']} with {size_analysis['review_strategy']} strategy",
        "files_analysis": f"Modified {pr_data['statistics']['files_count']} files with {pr_data['statistics']['total_changes']} total changes",
        "re_review_status": "Re-review detected" if review_context['is_re_review'] else "First review",
        "recommendation": "MANUAL_REVIEW",
        "note": "Full analysis requires Claude CLI integration. Install Claude CLI for enhanced analysis."
    }