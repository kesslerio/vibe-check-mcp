"""Response building for issue analysis results."""

import logging
from datetime import UTC, datetime
from typing import Dict, Any, List, Optional

from vibe_check.core.pattern_detector import DetectionResult
from vibe_check.core.architectural_concept_detector import (
    ArchitecturalConceptDetector,
    ConceptDetectionResult,
)
from vibe_check.core.educational_content import DetailLevel
from vibe_check.core.pattern_detector import PatternDetector

logger = logging.getLogger(__name__)


class AnalysisResponseBuilder:
    """Builds formatted response objects for issue analysis results."""

    def __init__(
        self,
        pattern_detector: PatternDetector,
        architectural_detector: ArchitecturalConceptDetector,
        claude_cli_enabled: bool = False,
    ):
        """
        Initialize response builder.

        Args:
            pattern_detector: Pattern detector instance for metadata
            architectural_detector: Architectural concept detector instance
            claude_cli_enabled: Whether Claude CLI enhancement is enabled
        """
        self.pattern_detector = pattern_detector
        self.architectural_detector = architectural_detector
        self.claude_cli_enabled = claude_cli_enabled

    def generate_basic_analysis_response(
        self,
        issue_data: Dict[str, Any],
        detected_patterns: List[DetectionResult],
        detail_level: DetailLevel,
        architectural_concepts: ConceptDetectionResult,
    ) -> Dict[str, Any]:
        """
        Generate basic analysis response with educational content.

        Args:
            issue_data: GitHub issue information
            detected_patterns: List of detected anti-patterns
            detail_level: Educational detail level
            architectural_concepts: Detected architectural concepts

        Returns:
            Formatted analysis response
        """
        # Generate confidence summary
        confidence_summary = self._build_confidence_summary(detected_patterns)

        # Generate recommended actions
        recommended_actions = self.generate_recommended_actions(
            detected_patterns, detail_level
        )

        # Format detected patterns for response
        patterns_detected = [
            {
                "pattern_type": pattern.pattern_type,
                "confidence": round(pattern.confidence, 3),
                "detected": pattern.detected,
                "evidence": pattern.evidence,
                "threshold": pattern.threshold,
                "educational_content": pattern.educational_content,
            }
            for pattern in detected_patterns
        ]

        architectural_analysis = self.format_architectural_concepts(
            architectural_concepts,
            issue_data["repository"],
        )

        # Build comprehensive response
        return {
            "status": "basic_analysis_complete",
            "analysis_timestamp": self._get_timestamp(),
            "issue_info": {
                "number": issue_data["number"],
                "title": issue_data["title"],
                "body": issue_data["body"],
                "author": issue_data["author"],
                "created_at": issue_data["created_at"],
                "state": issue_data["state"],
                "repository": issue_data["repository"],
                "url": issue_data["url"],
                "labels": issue_data["labels"],
            },
            "patterns_detected": patterns_detected,
            "confidence_summary": confidence_summary,
            "architectural_concepts": architectural_analysis,
            "recommended_actions": recommended_actions,
            "analysis_metadata": {
                "core_engine_validation": "87.5% accuracy, 0% false positives",
                "detail_level": detail_level.value,
                "patterns_analyzed": self.pattern_detector.get_pattern_types(),
                "detection_method": "Phase 1 validated algorithms",
                "external_claude_available": self.claude_cli_enabled,
            },
        }

    def generate_hybrid_summary(
        self,
        basic_result: Dict[str, Any],
        comprehensive_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate summary combining basic pattern detection with Claude CLI insights.

        Args:
            basic_result: Results from pattern detection analysis
            comprehensive_result: Results from Claude CLI analysis (if available)

        Returns:
            Combined analysis summary
        """
        summary = {
            "pattern_detection_summary": f"{basic_result.get('confidence_summary', {}).get('total_patterns_detected', 0)} patterns detected",
            "claude_cli_status": "not_available",
        }

        if (
            comprehensive_result
            and comprehensive_result.get("status") == "comprehensive_analysis_complete"
        ):
            claude_analysis = comprehensive_result.get("comprehensive_analysis", {})
            if claude_analysis.get("success"):
                summary.update(
                    {
                        "claude_cli_status": "analysis_complete",
                        "claude_cli_execution_time": f"{claude_analysis.get('execution_time_seconds', 0):.2f}s",
                        "combined_analysis": "Pattern detection provides immediate feedback, Claude CLI provides deep insights",
                        "cost_tracking": claude_analysis.get("cost_tracking", {}),
                    }
                )
            else:
                summary["claude_cli_status"] = (
                    f"analysis_failed: {claude_analysis.get('analysis_error', 'unknown error')}"
                )
        elif (
            comprehensive_result
            and comprehensive_result.get("status") == "enhancement_unavailable"
        ):
            summary["claude_cli_status"] = "enhancement_unavailable"

        return summary

    def generate_recommended_actions(
        self, detected_patterns: List[DetectionResult], detail_level: DetailLevel
    ) -> List[str]:
        """
        Generate prioritized recommended actions based on detected patterns.

        Args:
            detected_patterns: List of detected patterns
            detail_level: Detail level for recommendations

        Returns:
            List of recommended actions
        """
        if not detected_patterns:
            actions = [
                "✅ No anti-patterns detected in this issue",
                "Continue with standard engineering practices",
            ]

            if self.claude_cli_enabled:
                actions.append(
                    "💡 Consider using comprehensive analysis mode for detailed insights"
                )
            else:
                actions.append(
                    "📚 Consider enabling ExternalClaudeCli for enhanced analysis capabilities"
                )

            return actions

        actions = []

        # Sort patterns by confidence for prioritized recommendations
        sorted_patterns = sorted(
            detected_patterns, key=lambda x: x.confidence, reverse=True
        )

        for pattern in sorted_patterns[:3]:  # Top 3 most confident patterns
            if pattern.confidence >= 0.8:
                priority = "🚨 CRITICAL"
            elif pattern.confidence >= 0.6:
                priority = "⚠️ HIGH PRIORITY"
            else:
                priority = "💡 CONSIDER"

            pattern_name = (
                pattern.educational_content.get("pattern_name", pattern.pattern_type)
                if pattern.educational_content
                else pattern.pattern_type
            )
            actions.append(
                f"{priority}: Address {pattern_name} pattern (confidence: {pattern.confidence:.0%})"
            )

            # Add specific immediate actions from educational content
            if (
                pattern.educational_content
                and "immediate_actions" in pattern.educational_content
            ):
                immediate_actions = pattern.educational_content["immediate_actions"]
                if immediate_actions and isinstance(immediate_actions, list):
                    actions.extend(immediate_actions[:2])

        # Add general recommendations
        if len(detected_patterns) > 1:
            actions.append(
                "📋 Review all detected patterns before proceeding with implementation"
            )

        actions.append(
            "📚 Use provided educational content to understand why these patterns are problematic"
        )

        if self.claude_cli_enabled:
            actions.append(
                "🧠 Consider using comprehensive or hybrid analysis mode for detailed insights"
            )

        actions.append("✅ Apply prevention checklists for future work")

        return actions

    def format_architectural_concepts(
        self, concepts: ConceptDetectionResult, repository: str
    ) -> Dict[str, Any]:
        """
        Format architectural concept detection results for responses.

        Args:
            concepts: Detected architectural concepts
            repository: Repository name for context

        Returns:
            Formatted architectural analysis
        """
        if not concepts or not concepts.detected_concepts:
            return {
                "detected": False,
                "concepts": [],
                "search_guidance": [],
                "analysis_mode": "general",
            }

        sorted_concepts = sorted(
            concepts.detected_concepts, key=lambda item: item.confidence, reverse=True
        )

        formatted_concepts: List[Dict[str, Any]] = []
        for concept in sorted_concepts:
            guidance = self.architectural_detector.get_file_discovery_guidance(
                concept, repository
            )
            formatted_concepts.append(
                {
                    "name": concept.concept_name,
                    "confidence": round(concept.confidence, 3),
                    "keywords_found": concept.keywords_found,
                    "file_discovery": {
                        "patterns": concept.file_patterns,
                        "common_files": concept.common_files,
                        "github_queries": guidance["github_search_queries"][:3],
                    },
                }
            )

        context = self.architectural_detector.generate_analysis_context(concepts)

        return {
            "detected": True,
            "primary_concept": context.get("primary_concept"),
            "concepts": formatted_concepts,
            "search_guidance": context.get("search_guidance", {}),
            "analysis_mode": context.get("analysis_mode", "general"),
            "architectural_recommendations": context.get("recommendations", []),
        }

    def _build_confidence_summary(
        self, detected_patterns: List[DetectionResult]
    ) -> Dict[str, Any]:
        """Build confidence summary from detected patterns."""
        if detected_patterns:
            avg_confidence = sum(p.confidence for p in detected_patterns) / len(
                detected_patterns
            )
            max_confidence = max(p.confidence for p in detected_patterns)
            return {
                "total_patterns_detected": len(detected_patterns),
                "average_confidence": round(avg_confidence, 3),
                "highest_confidence": round(max_confidence, 3),
                "patterns_by_confidence": [
                    {
                        "pattern": p.pattern_type,
                        "confidence": round(p.confidence, 3),
                        "severity": (
                            "HIGH"
                            if p.confidence >= 0.8
                            else "MEDIUM" if p.confidence >= 0.6 else "LOW"
                        ),
                    }
                    for p in sorted(
                        detected_patterns, key=lambda x: x.confidence, reverse=True
                    )
                ],
            }
        else:
            return {
                "total_patterns_detected": 0,
                "average_confidence": 0.0,
                "highest_confidence": 0.0,
                "patterns_by_confidence": [],
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(UTC).isoformat()
