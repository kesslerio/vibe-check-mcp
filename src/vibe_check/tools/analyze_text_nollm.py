"""
Text Analysis Tool

Provides text analysis for vibe check framework testing and demonstration.
Follows action_what naming convention: analyze_text.
"""

import logging
from typing import Dict, Any, Optional

from vibe_check.core.pattern_detector import PatternDetector
from vibe_check.core.educational_content import EducationalContentGenerator
from .contextual_documentation import AnalysisContext, get_context_manager

logger = logging.getLogger(__name__)


def _build_error_response(message: str, text: str | Any) -> Dict[str, Any]:
    """Create a structured error response with demo metadata."""

    text_length = len(text) if isinstance(text, str) else 0
    return {
        "status": "error",
        "error": message,
        "analysis_results": {
            "text_length": text_length,
            "patterns_detected": 0,
            "analysis_method": "Phase 1 validated core engine",
            "context_applied": False,
        },
        "demo_analysis": {
            "text_length": text_length,
            "patterns_detected": 0,
            "analysis_method": "Phase 1 validated core engine",
        },
        "patterns": [],
        "educational_content": {},
        "contextual_analysis": {},
        "server_status": "⚠️ FastMCP server encountered an error while analyzing",
        "accuracy_note": "Using validated detection engine (87.5% accuracy, 0% false positives)",
    }


def analyze_text_demo(
    text: str,
    detail_level: str = "standard",
    context: Optional[AnalysisContext] = None,
    use_project_context: bool = True,
    project_root: str = ".",
) -> Dict[str, Any]:
    """
    Analyze text for anti-patterns using the validated core engine with contextual awareness.

    Args:
        text: Text content to analyze for anti-patterns
        detail_level: Level of detail for educational content (brief/standard/comprehensive)
        context: Analysis context with library and project information (optional)
        use_project_context: Whether to automatically load project context (default: true)
        project_root: Root directory for project context loading (default: current directory)

    Returns:
        Dictionary containing pattern detection results and educational content with contextual recommendations
    """
    if not isinstance(text, str):
        return _build_error_response("Input text must be a string.", text)

    try:
        # Validate detail_level
        from ..core.educational_content import DetailLevel

        if isinstance(detail_level, str) and detail_level.upper() in DetailLevel.__members__:
            detail_enum = DetailLevel[detail_level.upper()]
        else:
            detail_enum = DetailLevel.STANDARD

        # Load project context if requested and not provided
        if use_project_context and context is None:
            try:
                context_manager = get_context_manager(project_root)
                context = context_manager.get_project_context()
                logger.info(
                    f"Loaded project context with {len(context.library_docs)} libraries"
                )
            except FileNotFoundError:
                logger.warning(f"Project root not found: {project_root}")
                context = None
            except PermissionError:
                logger.warning(f"Permission denied for project root: {project_root}")
                context = None
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Failed to load project context: {exc}")
                context = None

        # Initialize validated core components
        detector = PatternDetector()
        educator = EducationalContentGenerator()

        # Analyze text using proven detection algorithms
        if hasattr(detector, "detect_patterns"):
            raw_patterns = detector.detect_patterns(text)
            if isinstance(raw_patterns, list):
                patterns = raw_patterns
            elif raw_patterns is None:
                patterns = []
            else:
                patterns = [raw_patterns]
        else:
            patterns = detector.analyze_text_for_patterns(text)

        # Convert DetectionResult objects to dictionaries for JSON serialization
        patterns_dict = []
        contextual_recommendations = []

        for result in patterns:
            pattern_data: Dict[str, Any] = {
                "pattern_type": result.pattern_type,
                "detected": result.detected,
                "confidence": result.confidence,
                "evidence": result.evidence,
                "threshold": result.threshold,
            }

            # Add contextual analysis if available
            if context and result.detected:
                contextual_rec = context.get_contextual_recommendation(result.pattern_type)
                if contextual_rec != result.pattern_type:
                    pattern_data["contextual_recommendation"] = contextual_rec
                    contextual_recommendations.append(contextual_rec)

                if result.pattern_type in context.pattern_exceptions:
                    pattern_data["project_exception"] = True
                    pattern_data["exception_reason"] = context.conflict_resolution.get(
                        result.pattern_type, "Approved project exception"
                    )

            patterns_dict.append(pattern_data)

        # Generate educational content for detected patterns
        educational_content: Dict[str, Any] = {}
        if patterns and patterns[0].detected:
            first_pattern = patterns[0]

            educational_response = educator.generate_educational_response(
                pattern_type=first_pattern.pattern_type,
                confidence=first_pattern.confidence,
                evidence=first_pattern.evidence,
                detail_level=detail_enum,
            )
            from dataclasses import asdict

            educational_content = asdict(educational_response)

        detected_patterns = len([p for p in patterns if p.detected])

        # Build contextual summary
        context_summary: Dict[str, Any] = {}
        if context:
            context_summary = {
                "libraries_detected": list(context.library_docs.keys()),
                "pattern_exceptions": len(context.pattern_exceptions),
                "contextual_recommendations": contextual_recommendations,
                "project_aware": True,
            }

        response: Dict[str, Any] = {
            "status": "success",
            "analysis_results": {
                "text_length": len(text),
                "patterns_detected": detected_patterns,
                "analysis_method": "Phase 1 validated core engine with contextual awareness",
                "context_applied": context is not None,
            },
            "patterns": patterns_dict,
            "educational_content": educational_content,
            "contextual_analysis": context_summary,
            "server_status": "✅ FastMCP server operational with core engine integration",
            "accuracy_note": "Using validated detection engine (87.5% accuracy, 0% false positives) with project context",
        }

        response["demo_analysis"] = {
            "text_length": len(text),
            "patterns_detected": detected_patterns,
            "analysis_method": "Phase 1 validated core engine",
        }

        return response

    except (ValueError, TypeError) as exc:
        logger.error(f"Parameter validation failed: {exc}")
        return _build_error_response(f"Invalid parameter: {exc}", text)
    except (MemoryError, RecursionError) as exc:
        logger.error(f"Resource exhaustion error: {exc}")
        return _build_error_response(f"Resource limit exceeded: {exc}", text)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Text analysis failed: {exc}")
        error_response = _build_error_response(f"Analysis failed: {exc}", text)
        error_response["analysis_results"] = {
            "text_length": len(text) if isinstance(text, str) else 0,
            "patterns_detected": 0,
            "analysis_method": "Error occurred",
            "context_applied": False,
        }
        return error_response


def demo_analyze_text(
    text: str,
    detail_level: str = "standard",
    context: Optional[AnalysisContext] = None,
    use_project_context: bool = True,
    project_root: str = ".",
) -> Dict[str, Any]:
    """Legacy-friendly wrapper that preserves the original demo response structure."""

    return analyze_text_demo(
        text=text,
        detail_level=detail_level,
        context=context,
        use_project_context=use_project_context,
        project_root=project_root,
    )
