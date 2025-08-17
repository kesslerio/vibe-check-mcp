import logging
import re
import os
import random
import time
from typing import Dict, Any, Optional
from ....tools.analyze_text_nollm import analyze_text_demo
from ....core.business_context_extractor import BusinessContextExtractor, ContextType
from ....tools.shared.github_abstraction import get_default_github_operations
from ....tools.contextual_documentation import get_context_manager

logger = logging.getLogger(__name__)
DEFAULT_MAX_DIFF_SIZE = 50000

async def analyze_query_and_context(
    query: str,
    context: Optional[str],
    phase: str,
    mode: str,
    confidence_threshold: float
) -> Dict[str, Any]:
    """Analyzes the query and context for patterns and business context."""
    
    context_extractor = BusinessContextExtractor()
    business_context = context_extractor.extract_context(query, context, phase=phase)
    
    logger.info(f"Business context: type={business_context.primary_type.value}, confidence={business_context.confidence:.2f}")
    
    if business_context.needs_clarification and mode != "interrupt" and business_context.questions_needed:
        logger.info(f"Low confidence ({business_context.confidence:.2f}), asking clarifying questions")
        return {
            "status": "clarification_needed",
            "immediate_feedback": {
                "summary": "I need some clarification to provide the most helpful feedback",
                "confidence": business_context.confidence,
                "detected_patterns": [],
                "vibe_level": "unknown",
                "context_type": business_context.primary_type.value
            },
            "clarifying_questions": business_context.questions_needed,
            "detected_indicators": business_context.indicators,
            "session_info": {
                "session_id": f"mentor-session-{int(time.time())}-{random.randint(10000000, 99999999)}",
                "can_continue": True
            },
            "formatted_output": f"\n🤔 **I need some clarification to provide the most helpful feedback:**\n\n" +
                              "\n".join([f"• {q}" for q in business_context.questions_needed]) +
                              f"\n\n*Context indicators detected: {', '.join(business_context.indicators[:3]) if business_context.indicators else 'none'}*"
        }

    pr_diff_content = await fetch_pr_diff(query, context)
    
    project_context = None
    try:
        context_manager = get_context_manager(".")
        project_context = context_manager.get_project_context()
        logger.info(f"Loaded project context with {len(project_context.library_docs)} libraries for mentor analysis")
    except Exception as e:
        logger.warning(f"Failed to load project context for mentor: {e}")

    enhanced_text = f"{query}\n\n{context}" if context else query
    enhanced_text += pr_diff_content
    
    vibe_analysis = analyze_text_demo(
        enhanced_text, 
        detail_level="standard",
        context=project_context,
        use_project_context=True
    )
    
    patterns_raw = vibe_analysis.get("patterns", [])
    detected_patterns = patterns_raw
    
    max_confidence = 0.0
    detected_count = 0
    for pattern in patterns_raw:
        if pattern.get("detected", False):
            detected_count += 1
            confidence = pattern.get("confidence", 0.0)
            if confidence > max_confidence:
                max_confidence = confidence
    
    if business_context.is_completion_report and detected_count > 0:
        logger.info(f"Adjusting pattern confidence for completion report context (was: {max_confidence})")
        max_confidence *= 0.5
        detected_count = max(0, detected_count - 1)
        
    if detected_count == 0:
        vibe_level = "good"
        pattern_confidence = 0.0
    elif detected_count == 1 and max_confidence < 0.7:
        vibe_level = "caution"
        pattern_confidence = max_confidence
    elif detected_count >= 2 or max_confidence >= 0.7:
        vibe_level = "concerning"
        pattern_confidence = max_confidence
    else:
        vibe_level = "unknown"
        pattern_confidence = max_confidence
        
    logger.debug(f"Vibe analysis results: {detected_count} patterns detected, max confidence: {max_confidence}, vibe level: {vibe_level}")

    return {
        "vibe_level": vibe_level,
        "pattern_confidence": pattern_confidence,
        "detected_patterns": detected_patterns,
        "business_context": business_context
    }

async def fetch_pr_diff(query: str, context: Optional[str]) -> str:
    """Fetches PR diff content if a PR is mentioned in the query."""
    pr_patterns = [
        r'(?:PR|pull request)\s*#?(\d+)',
        r'#(\d+)(?:\s|$)',
        r'PR(\d+)(?:\s|$)',
        r'pr/(\d+)',
    ]
    
    pr_number = None
    for pattern in pr_patterns:
        pr_match = re.search(pattern, query, re.IGNORECASE)
        if pr_match:
            pr_number = int(pr_match.group(1))
            break
            
    if not pr_number:
        return ""

    default_repo = os.getenv('VIBE_CHECK_DEFAULT_REPO', 'kesslerio/vibe-check-mcp')
    repo_match = re.search(r'(?:repo|repository)[:=\s]+([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', f"{query} {context}", re.IGNORECASE)
    repository = repo_match.group(1) if repo_match else default_repo
    
    try:
        github_ops = get_default_github_operations()
        diff_result = github_ops.get_pull_request_diff(repository, pr_number)
        
        if diff_result.success:
            max_diff_size = int(os.getenv('VIBE_CHECK_MAX_DIFF_SIZE', str(DEFAULT_MAX_DIFF_SIZE)))
            diff_data = diff_result.data
            
            if len(diff_data) > max_diff_size:
                diff_data = diff_data[:max_diff_size] + f"\n\n[TRUNCATED: Diff too large ({len(diff_result.data)} chars). Showing first {max_diff_size} characters for performance.]"
                logger.info(f"Truncated large diff for PR #{pr_number} ({len(diff_result.data)} chars -> {max_diff_size} chars)")
            
            logger.info(f"Successfully fetched diff for PR #{pr_number} in {repository}")
            return f"\n\n**ACTUAL PR DIFF (ISSUE #151 FIX):**\n{diff_data}"
        else:
            logger.warning(f"Failed to fetch PR diff: {diff_result.error}")
            return ""
    except Exception as e:
        logger.warning(f"Error fetching PR diff: {e}")
        return ""
