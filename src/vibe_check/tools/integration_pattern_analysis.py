"""
Integration Pattern Analysis MCP Tools

Real-time MCP tools for detecting integration anti-patterns and providing
immediate feedback during development workflow. These tools are designed to
prevent engineering disasters like the Cognee case study by catching
integration over-engineering before it happens.

MCP Real-Time Usage:
- Sub-second technology recognition
- Instant red flag detection
- Immediate actionable recommendations
- Seamless integration with development workflow
"""

import logging
import threading
from typing import Dict, Any, List, Optional

from vibe_check.core.integration_pattern_detector import IntegrationPatternDetector

logger = logging.getLogger(__name__)

# Global detector instance for performance (MCP tools need fast response)
_integration_detector = None
_detector_lock = threading.Lock()


def get_integration_detector() -> IntegrationPatternDetector:
    """Get or create the global integration pattern detector instance (thread-safe)"""
    global _integration_detector
    if _integration_detector is None:
        with _detector_lock:
            # Double-check locking pattern
            if _integration_detector is None:
                _integration_detector = IntegrationPatternDetector()
    return _integration_detector


def reset_integration_detector():
    """Reset the global detector instance (for testing purposes)"""
    global _integration_detector
    with _detector_lock:
        _integration_detector = None


def analyze_integration_patterns_fast(
    content: str, context: Optional[str] = None, detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    🚀 Fast integration pattern detection for real-time MCP usage.

    This tool provides instant feedback on integration decisions to prevent
    common anti-patterns like building custom solutions when official
    alternatives exist. Optimized for sub-second response in development workflow.

    Features:
    - Real-time technology recognition (Cognee, Supabase, OpenAI, Claude)
    - Instant red flag detection for custom development
    - Immediate recommendations with official alternatives
    - Integration complexity analysis

    Args:
        content: Text content to analyze (PR description, issue content, etc.)
        context: Additional context (title, comments, file names)
        detail_level: Analysis detail level (brief/standard/comprehensive)

    Returns:
        Instant integration pattern analysis with actionable recommendations
    """
    logger.info(
        f"Fast integration pattern analysis requested for {len(content)} characters"
    )

    try:
        detector = get_integration_detector()

        # Perform comprehensive analysis
        analysis = detector.analyze_integration_patterns(
            content=content,
            context=context,
            include_line_analysis=(detail_level == "comprehensive"),
        )

        # Format for MCP response
        result = detector.format_analysis_for_mcp(analysis)

        # Add educational content based on detail level
        if detail_level in ["standard", "comprehensive"]:
            result["educational_content"] = _get_educational_content(
                analysis, detail_level
            )

        # Add real-world examples if comprehensive
        if detail_level == "comprehensive":
            result["case_studies"] = _get_case_studies(analysis)

        return result

    except Exception as e:
        logger.error(f"Integration pattern analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Integration analysis failed but provided fallback guidance",
            "fallback_guidance": [
                "Research official documentation before building custom solutions",
                "Test standard approaches with basic requirements first",
                "Document specific gaps that justify custom development",
            ],
        }


def quick_technology_scan(content: str) -> Dict[str, Any]:
    """
    ⚡ Ultra-fast technology detection for immediate feedback.

    Designed for real-time development workflow integration where instant
    feedback is critical. Provides immediate alerts when known technologies
    are detected that have official solutions.

    Args:
        content: Text content to scan for technology mentions

    Returns:
        Instant technology detection results with official alternatives
    """
    logger.info("Quick technology scan requested")

    try:
        detector = get_integration_detector()

        # Ultra-fast detection
        detected_techs = detector.quick_technology_check(content)

        if not detected_techs:
            return {
                "status": "no_technologies_detected",
                "technologies": [],
                "message": "No known integration technologies detected",
            }

        # Get detailed info for detected technologies
        analysis = detector.analyze_integration_patterns(
            content, include_line_analysis=False
        )
        tech_details = []

        for tech in analysis.detected_technologies:
            tech_info = {
                "technology": tech.technology,
                "confidence": tech.confidence,
                "official_solution": tech.official_solution,
                "immediate_action": f"✅ Check official {tech.technology} solution before custom development",
            }

            if tech.red_flags:
                tech_info["red_flags"] = tech.red_flags
                tech_info["warning"] = (
                    f"⚠️ Avoid custom {tech.red_flags[0]} - official alternative available"
                )

            tech_details.append(tech_info)

        return {
            "status": "technologies_detected",
            "technologies": tech_details,
            "warning_level": analysis.warning_level,
            "quick_recommendations": [
                f"Research {tech.technology} official solution"
                for tech in analysis.detected_technologies
                if tech.official_solution
            ],
        }

    except Exception as e:
        logger.error(f"Quick technology scan failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Technology scan failed - manual check recommended",
        }


def analyze_effort_complexity(
    content: str, pr_metrics: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    📊 Effort-complexity analysis for integration decisions.

    Analyzes the relationship between development effort and integration
    complexity to identify potential over-engineering. Helps prevent
    scenarios like the Cognee case study (2000+ lines for standard integration).

    Args:
        content: Content to analyze for effort indicators
        pr_metrics: Optional PR metrics (lines changed, files modified)

    Returns:
        Effort-complexity analysis with recommendations
    """
    logger.info("Effort-complexity analysis requested")

    try:
        detector = get_integration_detector()

        # Full analysis with effort focus
        analysis = detector.analyze_integration_patterns(
            content=content, include_line_analysis=True
        )

        effort_summary = {
            "status": "effort_analysis_complete",
            "detected_technologies": [
                t.technology for t in analysis.detected_technologies
            ],
            "effort_indicators": analysis.effort_analysis,
            "complexity_assessment": "unknown",
        }

        # Add PR metrics if provided
        if pr_metrics:
            effort_summary["pr_metrics"] = pr_metrics

            # Analyze effort-value ratio
            total_changes = pr_metrics.get("additions", 0) + pr_metrics.get(
                "deletions", 0
            )
            files_changed = pr_metrics.get("changed_files", 0)

            if total_changes > 1000 and analysis.detected_technologies:
                effort_summary["complexity_assessment"] = "high"
                effort_summary["warning"] = (
                    f"🚨 {total_changes} lines for integration - verify necessity"
                )
            elif total_changes > 500 and analysis.detected_technologies:
                effort_summary["complexity_assessment"] = "medium"
                effort_summary["caution"] = (
                    f"⚠️ {total_changes} lines for integration - check official alternatives"
                )
            else:
                effort_summary["complexity_assessment"] = "reasonable"

        # Technology-specific effort analysis
        tech_effort_analysis = []
        for tech in analysis.detected_technologies:
            if tech.official_solution:
                tech_analysis = {
                    "technology": tech.technology,
                    "official_solution": tech.official_solution,
                    "effort_question": f"Is custom development effort justified vs {tech.official_solution}?",
                    "recommendation": f"Test {tech.official_solution} with realistic requirements first",
                }
                tech_effort_analysis.append(tech_analysis)

        effort_summary["technology_effort_analysis"] = tech_effort_analysis
        effort_summary["recommendations"] = analysis.recommendations

        return effort_summary

    except Exception as e:
        logger.error(f"Effort-complexity analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Effort analysis failed - manual assessment recommended",
        }


def _get_educational_content(analysis, detail_level: str) -> Dict[str, Any]:
    """Generate educational content based on detected patterns"""
    content = {
        "integration_best_practices": [
            "Research official deployment options first",
            "Test standard approaches with realistic data",
            "Document specific gaps before custom development",
            "Consider maintenance burden of custom solutions",
        ]
    }

    if analysis.detected_technologies:
        content["technology_guidance"] = {}
        for tech in analysis.detected_technologies:
            if tech.official_solution:
                content["technology_guidance"][tech.technology] = {
                    "official_solution": tech.official_solution,
                    "first_step": f"Test {tech.official_solution} with your requirements",
                    "documentation": f"Review official {tech.technology} documentation",
                }

    if detail_level == "comprehensive":
        content["common_anti_patterns"] = [
            "Building custom REST servers when official containers exist",
            "Manual authentication when SDKs provide it",
            "Custom HTTP clients when official SDKs exist",
            "Environment forcing instead of proper configuration",
        ]

    return content


def _get_case_studies(analysis) -> Dict[str, Any]:
    """Get relevant case studies based on detected patterns"""
    case_studies = {}

    # Add Cognee case study if relevant
    for tech in analysis.detected_technologies:
        if tech.technology == "cognee":
            case_studies["cognee_failure"] = {
                "problem": "2+ weeks spent building custom FastAPI server for Cognee",
                "solution": "cognee/cognee:main Docker container provides complete REST API",
                "lesson": "Official containers often provide complete functionality",
                "prevention": "Test official solutions with realistic requirements first",
            }

    # Add generic integration failure patterns
    if any(
        p.pattern_type == "integration_over_engineering"
        for p in analysis.integration_anti_patterns
    ):
        case_studies["over_engineering_pattern"] = {
            "pattern": "Building custom infrastructure when standard options exist",
            "symptoms": "High development time for standard integrations",
            "solution": "Research and test official alternatives first",
            "prevention": "Always check vendor solutions before custom development",
        }

    return case_studies


# Integration with existing text analysis tools
def enhance_text_analysis_with_integration_patterns(
    existing_analysis: Dict[str, Any], content: str, context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhance existing text analysis results with integration pattern detection.

    This function can be used to augment other analysis tools with integration-specific
    insights without duplicating the full analysis.
    """
    try:
        detector = get_integration_detector()

        # Quick integration check
        integration_analysis = detector.analyze_integration_patterns(
            content=content, context=context, include_line_analysis=False
        )

        # Add integration insights to existing analysis
        enhanced_analysis = existing_analysis.copy()
        enhanced_analysis["integration_insights"] = {
            "technologies_detected": [
                t.technology for t in integration_analysis.detected_technologies
            ],
            "integration_warning_level": integration_analysis.warning_level,
            "integration_recommendations": integration_analysis.recommendations[
                :3
            ],  # Top 3
            "has_integration_anti_patterns": len(
                integration_analysis.integration_anti_patterns
            )
            > 0,
        }

        return enhanced_analysis

    except Exception as e:
        logger.error(f"Integration enhancement failed: {e}")
        return existing_analysis  # Return original if enhancement fails
