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
from .feedback_categorizer import FeedbackCategorizer
from .chunked_analyzer import ChunkedAnalyzer, analyze_pr_with_chunking
from .file_type_analyzer import FileTypeAnalyzer
from ..shared.pr_classifier import classify_pr_size, PrSizeCategory, should_use_chunked_analysis
from ..mcp_protocol_handler import get_mcp_handler, analyze_with_token_limit_bypass

logger = logging.getLogger(__name__)


async def review_pull_request(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    force_re_review: bool = False,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard",
    model: str = "sonnet"  # New parameter for model selection
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
        model: Claude model to use - "sonnet" (default), "opus", or "haiku"
        
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
        file_type_analyzer = FileTypeAnalyzer()
        
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
        
        # Phase 3.5: File Type Analysis
        logger.info("📁 Phase 3.5: Analyzing file types...")
        file_type_analysis = file_type_analyzer.analyze_files(pr_data.get('files', []))
        
        # Phase 4: Intelligent Analysis Strategy Selection
        logger.info(f"🔍 Phase 4: Selecting analysis strategy (Mode: {analysis_mode}, Size: {size_analysis.get('overall_size', 'Unknown')})")
        
        # Enhanced PR classification for chunked analysis
        enhanced_pr_metrics = classify_pr_size(pr_data.get('metadata', {}))
        
        # Check Claude availability
        claude_available = claude_integration.check_claude_availability()
        
        if claude_available and analysis_mode == "comprehensive":
            # Determine analysis strategy based on PR size
            if enhanced_pr_metrics.size_category == PrSizeCategory.MEDIUM:
                logger.info("📊 Using chunked analysis for medium-sized PR")
                analysis_result = await _generate_chunked_analysis(
                    pr_data, enhanced_pr_metrics, review_context, detail_level, pr_number
                )
            elif enhanced_pr_metrics.size_category == PrSizeCategory.SMALL:
                logger.info("🎯 Using full LLM analysis for small PR")
                analysis_result = await _generate_claude_analysis(
                    claude_integration, pr_data, size_analysis, review_context, 
                    detail_level, pr_number, model, file_type_analysis
                )
            else:  # LARGE
                logger.info("⚡ Using pattern detection for large PR")
                analysis_result = _generate_large_pr_analysis(
                    pr_data, enhanced_pr_metrics, review_context, detail_level
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
            "model_used": model,
            "size_analysis": size_analysis,
            "review_context": review_context,
            "file_type_analysis": file_type_analysis,
            "analysis_result": analysis_result,
            "enhanced_pr_metrics": {
                "size_category": enhanced_pr_metrics.size_category.value,
                "analysis_strategy": enhanced_pr_metrics.analysis_strategy,
                "total_changes": enhanced_pr_metrics.total_changes,
                "changed_files": enhanced_pr_metrics.changed_files,
                "estimated_chunks": enhanced_pr_metrics.estimated_chunks
            },
            "modular_architecture": {
                "data_collector": "✅ Extracted",
                "size_classifier": "✅ Extracted", 
                "context_analyzer": "✅ Extracted",
                "claude_integration": "✅ Extracted",
                "chunked_analyzer": "✅ Phase 3 - Issue #103",
                "pr_classifier": "✅ Phase 3 - Issue #103",
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
    pr_number: int,
    model: str = "sonnet",
    file_type_analysis: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate analysis using Claude integration."""
    # Check if author is a first-time contributor
    author_association = pr_data.get('metadata', {}).get('author_association', 'NONE')
    is_first_time_contributor = author_association in ['FIRST_TIME_CONTRIBUTOR', 'NONE']
    
    # Generate file type-specific prompt section
    file_type_prompt = ""
    if file_type_analysis:
        file_type_prompt = file_type_analyzer.generate_file_type_prompt(file_type_analysis)
    
    # Enhanced prompt following CLAUDE.md PR review guidelines
    author_context = ""
    if is_first_time_contributor:
        author_context = "\n⭐ FIRST-TIME CONTRIBUTOR: Please be encouraging and provide detailed explanations for any suggestions. Welcome them to the project!\n"
    
    prompt_content = f"""Analyze this pull request with focus on code quality, security, performance, and test coverage.
{author_context}
PR Details:
- Title: {pr_data['metadata']['title']}
- Author: {pr_data['metadata']['author']} ({author_association})
- Size: {size_analysis['overall_size']}
- Files: {size_analysis['size_reasons']}
- Re-review: {review_context['is_re_review']}

Please provide analysis with categorized feedback:

## Overview
Brief summary of changes and overall assessment.

## Code Quality and Best Practices
Review code structure, patterns, and adherence to project standards.

## Security Analysis
Identify any security vulnerabilities, exposed secrets, or unsafe practices.

## Performance Considerations
Analyze performance implications and optimization opportunities.

## Test Coverage
Evaluate test completeness, edge cases, and test quality.

{file_type_prompt}

## Strengths  
Positive aspects of the implementation.

## Categorized Feedback

### ⚠️ CRITICAL Issues (Fix before merge)
Issues that MUST be addressed before merging:
- Security vulnerabilities or critical bugs
- Missing issue linkage (Fixes #XX)
- Breaking functionality
- Simple fixes that don't change scope

### 📋 IMPORTANT Suggestions (Consider follow-up)
Good ideas that could be follow-up issues:
- Performance improvements requiring analysis
- Documentation enhancements not critical to current functionality
- Refactoring suggestions that don't affect core functionality
Note: Check if issues already exist before creating new ones.

### 💡 NICE-TO-HAVE (Consider but likely ignore)
Minor improvements with unclear value:
- Subjective style preferences already covered by linting
- Minor optimizations with unclear value
- Features that may never be needed (YAGNI principle)

### ❌ OVERENGINEERING Concerns (Reject)
Recommendations that add unnecessary complexity:
- Premature optimization
- Over-abstraction for current use case
- Violates KISS principle

## Final Recommendation
APPROVE/REQUEST_CHANGES/REJECT with clear rationale.
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
    
    # USE TOKEN LIMIT BYPASS: Intelligent handling of large prompts
    try:
        logger.info("🔄 Using intelligent token limit bypass for PR analysis")
        
        # Use the MCP token limit handler for intelligent mode selection
        bypass_result = await analyze_with_token_limit_bypass(
            prompt=prompt_content,
            data=data_content,
            context={
                "pr_number": pr_number,
                "pr_data": pr_data,
                "model": model,
                "analysis_type": "pr_review"
            }
        )
        
        if bypass_result["success"]:
            logger.info(f"✅ Token limit bypass successful using {bypass_result.get('method', 'unknown')} method")
            
            # Parse the analysis result for compatibility with existing code
            analysis_text = bypass_result["analysis"]
            
            # Try to parse it using the existing Claude integration parser
            parsed_result = claude_integration._parse_claude_output(analysis_text, pr_number)
            
            # Add bypass metadata
            if parsed_result:
                parsed_result["analysis_method"] = bypass_result.get("method", "token_bypass")
                parsed_result["token_count"] = bypass_result.get("token_count", 0)
                parsed_result["processing_metadata"] = bypass_result.get("processing_metadata", {})
                return parsed_result
            else:
                # Fallback: return raw analysis if parsing fails
                return {
                    "analysis": analysis_text,
                    "analysis_method": bypass_result.get("method", "token_bypass"),
                    "token_count": bypass_result.get("token_count", 0),
                    "recommendation": "MANUAL_REVIEW",
                    "processing_metadata": bypass_result.get("processing_metadata", {})
                }
        else:
            logger.warning(f"⚠️ Token limit bypass failed: {bypass_result.get('error', 'Unknown error')}")
            
            # Fallback to original Claude integration
            logger.info("🔄 Falling back to original Claude integration")
            result = await claude_integration.run_claude_analysis(
                prompt_content=prompt_content,
                data_content=data_content,
                pr_number=pr_number,
                pr_data=pr_data,
                model=model
            )
            
            return result or {"analysis": "Claude analysis failed", "recommendation": "MANUAL_REVIEW"}
            
    except Exception as e:
        logger.error(f"❌ Token limit bypass failed with exception: {e}")
        
        # Fallback to original Claude integration
        logger.info("🔄 Falling back to original Claude integration after bypass failure")
        result = await claude_integration.run_claude_analysis(
            prompt_content=prompt_content,
            data_content=data_content,
            pr_number=pr_number,
            pr_data=pr_data,
            model=model
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


async def _generate_chunked_analysis(
    pr_data: Dict[str, Any],
    pr_metrics,  # PrSizeMetrics
    review_context: Dict[str, Any],
    detail_level: str,
    pr_number: int
) -> Dict[str, Any]:
    """Generate analysis using chunked approach for medium-sized PRs."""
    
    try:
        # Extract file data for chunking
        pr_files = pr_data.get('files', [])
        
        if not pr_files:
            return {
                "analysis_method": "chunked_analysis_failed",
                "error": "No file data available for chunked analysis",
                "recommendation": "MANUAL_REVIEW",
                "fallback_reason": "Missing file data"
            }
        
        # Perform chunked analysis
        chunked_result = await analyze_pr_with_chunking(
            pr_data=pr_data.get('metadata', {}),
            pr_files=pr_files
        )
        
        # Convert chunked result to standard analysis format
        return {
            "analysis_method": "chunked_llm_analysis",
            "overview": chunked_result.overall_assessment,
            "patterns_detected": chunked_result.patterns_detected,
            "recommendations": chunked_result.recommendations,
            "chunk_analysis": {
                "total_chunks": chunked_result.total_chunks,
                "successful_chunks": chunked_result.successful_chunks,
                "failed_chunks": chunked_result.failed_chunks,
                "success_rate": chunked_result.successful_chunks / max(chunked_result.total_chunks, 1),
                "chunk_summaries": chunked_result.chunk_summaries
            },
            "size_metrics": {
                "category": pr_metrics.size_category.value,
                "total_changes": pr_metrics.total_changes,
                "changed_files": pr_metrics.changed_files,
                "estimated_chunks": pr_metrics.estimated_chunks
            },
            "performance": {
                "total_duration": chunked_result.total_duration,
                "avg_chunk_duration": chunked_result.total_duration / max(chunked_result.total_chunks, 1)
            },
            "recommendation": _determine_chunked_recommendation(chunked_result),
            "status": chunked_result.status
        }
        
    except Exception as e:
        logger.error(f"Chunked analysis failed: {e}")
        return {
            "analysis_method": "chunked_analysis_failed",
            "error": f"Chunked analysis error: {str(e)}",
            "recommendation": "MANUAL_REVIEW",
            "fallback_reason": "Chunked analysis failure"
        }


def _generate_large_pr_analysis(
    pr_data: Dict[str, Any],
    pr_metrics,  # PrSizeMetrics
    review_context: Dict[str, Any],
    detail_level: str
) -> Dict[str, Any]:
    """Generate basic pattern detection analysis for large PRs."""
    
    # Basic analysis for large PRs that are too big for LLM analysis
    files_count = pr_metrics.changed_files
    total_changes = pr_metrics.total_changes
    
    # Simple pattern detection based on file changes
    patterns = []
    recommendations = []
    
    # Check for common patterns
    if files_count > 50:
        patterns.append("Large-scale refactoring detected")
        recommendations.append("Consider breaking into smaller, focused PRs")
    
    if total_changes > 2000:
        patterns.append("Major code changes detected")
        recommendations.append("Ensure comprehensive testing and staged deployment")
    
    if pr_metrics.has_large_files:
        patterns.append(f"Large files detected (max {pr_metrics.largest_file_changes} lines)")
        recommendations.append("Review large file changes carefully for maintainability")
    
    # File diversity analysis
    if pr_metrics.file_diversity_score > 0.8:
        patterns.append("High file diversity - changes span multiple components")
        recommendations.append("Verify changes are cohesive and properly coordinated")
    
    return {
        "analysis_method": "pattern_detection_only",
        "overview": f"Large PR analysis: {total_changes} lines across {files_count} files. "
                   f"Too large for detailed LLM analysis - using pattern detection only.",
        "patterns_detected": [{"pattern": p, "category": "size_analysis", "confidence": "high"} for p in patterns],
        "recommendations": recommendations,
        "size_metrics": {
            "category": pr_metrics.size_category.value,
            "total_changes": total_changes,
            "changed_files": files_count,
            "lines_per_file_avg": pr_metrics.lines_per_file_avg,
            "file_diversity_score": pr_metrics.file_diversity_score
        },
        "limitation_notice": (
            "This PR is too large for detailed LLM analysis. "
            "Consider using chunked analysis by breaking into smaller PRs, "
            "or use manual review for comprehensive assessment."
        ),
        "recommendation": "MANUAL_REVIEW" if total_changes > 3000 else "APPROVE_WITH_CAUTION",
        "status": "pattern_analysis_complete"
    }


def _determine_chunked_recommendation(chunked_result) -> str:
    """Determine recommendation based on chunked analysis results."""
    
    success_rate = chunked_result.successful_chunks / max(chunked_result.total_chunks, 1)
    
    # If most chunks failed, recommend manual review
    if success_rate < 0.5:
        return "MANUAL_REVIEW"
    
    # Count critical issues from patterns
    critical_patterns = [
        p for p in chunked_result.patterns_detected 
        if isinstance(p, dict) and p.get('category') in ['security', 'bug_risk']
    ]
    
    # If critical issues found, request changes
    if critical_patterns:
        return "REQUEST_CHANGES"
    
    # Check for significant issues in recommendations
    critical_recommendations = [
        r for r in chunked_result.recommendations
        if any(word in r.lower() for word in ['security', 'bug', 'error', 'critical', 'fix'])
    ]
    
    if critical_recommendations:
        return "REQUEST_CHANGES"
    
    # Default to approval for successful chunked analysis
    return "APPROVE"