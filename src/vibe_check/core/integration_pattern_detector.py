"""
Integration Pattern Detector for Vibe Coding Safety Net

Enhances the core pattern detection system with technology-specific recognition
and integration anti-pattern detection. Designed to prevent engineering disasters
like the Cognee case study where 2+ weeks were spent building custom solutions
instead of using official alternatives.

This module works in real-time via MCP by:
1. Analyzing text content for technology indicators
2. Detecting custom development patterns
3. Cross-referencing with known official solutions
4. Providing instant feedback with specific recommendations
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .pattern_detector import PatternDetector, DetectionResult

logger = logging.getLogger(__name__)


@dataclass
class TechnologyDetection:
    """Result of technology detection in content"""

    technology: str
    confidence: float
    indicators: List[str]
    official_solution: Optional[str] = None
    red_flags: List[str] = None


@dataclass
class IntegrationAnalysis:
    """Comprehensive integration pattern analysis result"""

    detected_technologies: List[TechnologyDetection]
    integration_anti_patterns: List[DetectionResult]
    effort_analysis: Dict[str, Any]
    recommendations: List[str]
    warning_level: str  # "none", "caution", "warning", "critical"
    research_questions: List[str]


class IntegrationPatternDetector:
    """
    Enhanced pattern detector with integration-specific capabilities.

    This detector extends the core pattern detection system to specifically
    identify third-party integration anti-patterns and provide technology-specific
    guidance to prevent unnecessary custom development.

    Real-time MCP Usage:
    - Instant technology recognition from text content
    - Immediate red flag detection for known integrations
    - Sub-second response time for development workflow integration
    - Contextual recommendations based on detected technologies
    """

    def __init__(self, patterns_file: Optional[str] = None):
        """Initialize with enhanced pattern detection capabilities"""

        # Initialize base pattern detector
        self.base_detector = PatternDetector(patterns_file=patterns_file)

        # Load integration-specific patterns
        self.integration_patterns = self._load_integration_patterns()

        # Technology detection patterns (for real-time recognition)
        self.technology_patterns = {
            "cognee": {
                "indicators": [
                    r"\bcognee\b",
                    r"cognitive\s+engine",
                    r"knowledge\s+graph\s+management",
                ],
                "context_patterns": [
                    r"cognee.*(?:integration|setup|deployment|container)",
                    r"(?:fastapi|flask|rest).*cognee",
                    r"cognee.*(?:auth|jwt|storage)",
                ],
            },
            "supabase": {
                "indicators": [
                    r"\bsupabase\b",
                    r"@supabase/supabase-js",
                    r"supabase-py",
                ],
                "context_patterns": [
                    r"supabase.*(?:auth|authentication|database|storage)",
                    r"(?:custom|manual).*supabase",
                    r"supabase.*(?:client|sdk|api)",
                ],
            },
            "openai": {
                "indicators": [r"\bopenai\b", r"gpt-[0-9]", r"openai\s+api"],
                "context_patterns": [
                    r"openai.*(?:client|api|wrapper|integration)",
                    r"(?:custom|manual).*openai",
                    r"(?:requests|urllib).*openai",
                ],
            },
            "claude": {
                "indicators": [r"\bclaude\b", r"anthropic", r"claude-[0-9]"],
                "context_patterns": [
                    r"claude.*(?:client|api|wrapper|integration)",
                    r"(?:custom|manual).*claude",
                    r"anthropic.*(?:sdk|api|client)",
                ],
            },
        }

    def analyze_integration_patterns(
        self,
        content: str,
        context: Optional[str] = None,
        include_line_analysis: bool = False,
    ) -> IntegrationAnalysis:
        """
        Comprehensive integration pattern analysis for real-time MCP usage.

        This is the main method called by MCP tools to provide instant feedback
        on integration decisions and prevent anti-patterns.

        Args:
            content: Primary text to analyze (PR description, issue content, etc.)
            context: Additional context (title, comments, file names)
            include_line_analysis: Whether to analyze code line counts

        Returns:
            IntegrationAnalysis with immediate actionable insights
        """
        logger.info("Starting real-time integration pattern analysis")

        # Combine content for analysis
        full_text = f"{content} {context or ''}"

        # Step 1: Detect technologies (instant)
        detected_technologies = self._detect_technologies(full_text)

        # Step 2: Run core pattern detection (sub-second)
        core_patterns = self.base_detector.analyze_text_for_patterns(
            content=content,
            context=context,
            focus_patterns=[
                "infrastructure_without_implementation",
                "integration_over_engineering",
            ],
        )

        # Step 3: Run integration-specific detection
        integration_patterns = self._detect_integration_patterns(
            full_text, detected_technologies
        )

        # Step 4: Effort analysis (if requested)
        effort_analysis = {}
        if include_line_analysis:
            effort_analysis = self._analyze_effort_indicators(full_text)

        # Step 5: Generate recommendations and warning level
        recommendations = self._generate_recommendations(
            detected_technologies, core_patterns + integration_patterns, effort_analysis
        )

        warning_level = self._calculate_warning_level(
            detected_technologies, core_patterns + integration_patterns
        )

        # Step 6: Generate research questions
        research_questions = self._generate_research_questions(detected_technologies)

        return IntegrationAnalysis(
            detected_technologies=detected_technologies,
            integration_anti_patterns=core_patterns + integration_patterns,
            effort_analysis=effort_analysis,
            recommendations=recommendations,
            warning_level=warning_level,
            research_questions=research_questions,
        )

    def quick_technology_check(self, content: str) -> List[str]:
        """
        Ultra-fast technology detection for immediate feedback.

        Designed for real-time MCP usage where sub-second response is critical.
        Returns list of detected technology names.
        """
        detected = []
        content_lower = content.lower()

        for tech_name, patterns in self.technology_patterns.items():
            for indicator in patterns["indicators"]:
                if re.search(indicator, content_lower, re.IGNORECASE):
                    detected.append(tech_name)
                    break  # Found this tech, move to next

        return detected

    def _detect_technologies(self, text: str) -> List[TechnologyDetection]:
        """Detect technologies mentioned in text with confidence scoring"""
        detected = []
        text_lower = text.lower()

        for tech_name, config in self.technology_patterns.items():
            confidence = 0.0
            indicators_found = []

            # Check basic indicators
            for indicator in config["indicators"]:
                if re.search(indicator, text_lower, re.IGNORECASE):
                    confidence += 0.3
                    indicators_found.append(f"mentions {tech_name}")

            # Check context patterns (higher weight)
            for pattern in config["context_patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    confidence += 0.5
                    indicators_found.append(f"{tech_name} integration context")

            # Get official solution and red flags from integration patterns
            official_solution = None
            red_flags = []
            if tech_name in self.integration_patterns.get("technologies", {}):
                tech_info = self.integration_patterns["technologies"][tech_name]
                official_solution = tech_info.get("official_solution")
                red_flags = tech_info.get("red_flags", [])

            if confidence >= 0.3:  # Threshold for detection
                detected.append(
                    TechnologyDetection(
                        technology=tech_name,
                        confidence=min(1.0, confidence),
                        indicators=indicators_found,
                        official_solution=official_solution,
                        red_flags=red_flags,
                    )
                )

        return detected

    def _detect_integration_patterns(
        self, text: str, detected_technologies: List[TechnologyDetection]
    ) -> List[DetectionResult]:
        """Detect integration-specific anti-patterns"""
        patterns = []
        text_lower = text.lower()

        # Check for integration over-engineering pattern
        if "integration_over_engineering" in self.base_detector.patterns:
            pattern_config = self.base_detector.patterns["integration_over_engineering"]
            result = self.base_detector._detect_single_pattern(text, pattern_config)

            # Enhance with technology-specific context
            if result.detected and detected_technologies:
                tech_names = [t.technology for t in detected_technologies]
                result.evidence.append(
                    f"Detected technologies: {', '.join(tech_names)}"
                )

                # Add specific red flags for detected technologies
                for tech in detected_technologies:
                    if tech.red_flags:
                        for evidence_item in result.evidence:
                            for red_flag in tech.red_flags:
                                if red_flag.lower() in evidence_item.lower():
                                    result.evidence.append(
                                        f"{tech.technology} red flag: {red_flag}"
                                    )

            if result.detected:
                patterns.append(result)

        # Additional logic for detected technologies with red flags
        if detected_technologies:
            for tech in detected_technologies:
                if tech.red_flags:
                    # Check if any red flags are mentioned in the text (with more flexible matching)
                    red_flags_found = []
                    for red_flag in tech.red_flags:
                        # More flexible matching for red flags
                        red_flag_words = red_flag.lower().split()
                        if all(word in text_lower for word in red_flag_words):
                            red_flags_found.append(red_flag)

                    if red_flags_found:
                        # Create a custom integration over-engineering detection
                        from ..core.pattern_detector import DetectionResult

                        tech_pattern = DetectionResult(
                            pattern_type="integration_over_engineering",
                            detected=True,
                            confidence=0.7,  # High confidence for explicit red flags
                            evidence=[
                                f"{tech.technology} red flag detected: {flag}"
                                for flag in red_flags_found
                            ],
                            threshold=0.5,
                            pattern_version="1.0.0",
                        )
                        patterns.append(tech_pattern)

        # Check effort-value mismatch
        if "effort_value_mismatch" in self.base_detector.patterns:
            pattern_config = self.base_detector.patterns["effort_value_mismatch"]
            result = self.base_detector._detect_single_pattern(text, pattern_config)
            if result.detected:
                patterns.append(result)

        return patterns

    def _analyze_effort_indicators(self, text: str) -> Dict[str, Any]:
        """Analyze effort indicators like line counts, time estimates"""
        effort_analysis = {
            "high_line_counts": [],
            "time_estimates": [],
            "complexity_indicators": [],
        }

        # Look for line count indicators
        line_patterns = [
            r"(\d+)\s*(?:\+|\+\+)?\s*lines",
            r"(\d+)\s*loc\b",
            r"(\d+)\s*(?:lines\s+of\s+code|LOC)",
        ]

        for pattern in line_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                line_count = int(match.group(1))
                if line_count >= 500:  # High line count threshold
                    effort_analysis["high_line_counts"].append(
                        {"count": line_count, "context": match.group(0)}
                    )

        # Look for time estimates
        time_patterns = [
            r"(\d+)\s*(?:weeks?|months?)\s*(?:of|to)\s*(?:development|work|implementation)",
            r"(?:takes?|took|spend|spent)\s*(\d+)\s*(?:weeks?|months?)",
        ]

        for pattern in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                effort_analysis["time_estimates"].append(match.group(0))

        return effort_analysis

    def _generate_recommendations(
        self,
        technologies: List[TechnologyDetection],
        patterns: List[DetectionResult],
        effort_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate specific recommendations based on detected patterns"""
        recommendations = []

        # Technology-specific recommendations
        for tech in technologies:
            if tech.official_solution:
                recommendations.append(
                    f"✅ Test official {tech.technology} solution: {tech.official_solution}"
                )

            # Red flag specific recommendations
            if tech.red_flags:
                for pattern in patterns:
                    for evidence in pattern.evidence:
                        for red_flag in tech.red_flags:
                            if red_flag.lower() in evidence.lower():
                                recommendations.append(
                                    f"🚨 Avoid {red_flag} for {tech.technology} - official alternative available"
                                )

        # Pattern-specific recommendations
        for pattern in patterns:
            if pattern.pattern_type == "integration_over_engineering":
                recommendations.append(
                    "🔍 Research official deployment options before custom development"
                )
            elif pattern.pattern_type == "effort_value_mismatch":
                recommendations.append(
                    "⚖️ Evaluate if development effort matches integration complexity"
                )

        # Effort-based recommendations
        if effort_analysis.get("high_line_counts"):
            recommendations.append(
                "📏 High line count detected - verify this complexity is necessary for integration"
            )

        if effort_analysis.get("time_estimates"):
            recommendations.append(
                "⏱️ Extended timeline detected - consider official alternatives first"
            )

        return recommendations

    def _calculate_warning_level(
        self, technologies: List[TechnologyDetection], patterns: List[DetectionResult]
    ) -> str:
        """Calculate overall warning level for integration decisions"""

        # Count high-confidence patterns
        high_confidence_patterns = [p for p in patterns if p.confidence >= 0.7]
        medium_confidence_patterns = [p for p in patterns if 0.4 <= p.confidence < 0.7]

        # Check for technologies with known red flags mentioned in text
        red_flag_count = 0
        for tech in technologies:
            if tech.red_flags:
                # Count red flags mentioned in patterns
                for pattern in patterns:
                    for evidence in pattern.evidence:
                        for red_flag in tech.red_flags:
                            if red_flag.lower() in evidence.lower():
                                red_flag_count += 1

        # Also check for technologies with official solutions (indicates potential over-engineering)
        tech_with_solutions = len([t for t in technologies if t.official_solution])

        # Determine warning level
        if len(high_confidence_patterns) >= 2 or red_flag_count >= 3:
            return "critical"
        elif len(high_confidence_patterns) >= 1 or red_flag_count >= 2:
            return "warning"
        elif (
            len(medium_confidence_patterns) >= 1
            or red_flag_count >= 1
            or tech_with_solutions >= 2
        ):
            return "caution"
        elif tech_with_solutions >= 1:
            return "caution"
        else:
            return "none"

    def _generate_research_questions(
        self, technologies: List[TechnologyDetection]
    ) -> List[str]:
        """Generate technology-specific research validation questions"""
        questions = []

        for tech in technologies:
            if tech.official_solution:
                questions.extend(
                    [
                        f"Have you tested the official {tech.technology} solution with your requirements?",
                        f"What specific features does the official {tech.technology} solution lack?",
                        f"Why is custom development necessary instead of using {tech.official_solution}?",
                    ]
                )

        # Generic integration questions
        if technologies:
            questions.extend(
                [
                    "Have you documented the decision rationale for custom vs. official approaches?",
                    "What is the long-term maintenance plan for custom integration code?",
                    "Have you estimated the total cost of ownership for custom development?",
                ]
            )

        return questions

    def _load_integration_patterns(self) -> Dict[str, Any]:
        """Load integration-specific patterns from the enhanced anti-patterns file"""
        try:
            # Load from the same file as base patterns
            patterns_path = (
                Path(__file__).parent.parent.parent.parent
                / "data"
                / "anti_patterns.json"
            )

            import json

            with open(patterns_path) as f:
                all_patterns = json.load(f)

            # Extract integration pattern data
            if "integration_over_engineering" in all_patterns:
                return all_patterns["integration_over_engineering"]
            else:
                logger.warning("Integration patterns not found in anti-patterns file")
                return {}

        except Exception as e:
            logger.error(f"Failed to load integration patterns: {e}")
            return {}

    def get_technology_coverage(self) -> List[str]:
        """Get list of technologies covered by the detector"""
        return list(self.technology_patterns.keys())

    def format_analysis_for_mcp(self, analysis: IntegrationAnalysis) -> Dict[str, Any]:
        """
        Format analysis results for MCP tool response.

        Optimized for real-time usage with clear, actionable structure.
        """
        # Technology summary
        tech_summary = []
        for tech in analysis.detected_technologies:
            tech_info = {
                "technology": tech.technology,
                "confidence": tech.confidence,
                "official_solution": tech.official_solution,
                "indicators": tech.indicators,
            }
            tech_summary.append(tech_info)

        # Pattern summary
        pattern_summary = []
        for pattern in analysis.integration_anti_patterns:
            pattern_info = {
                "pattern": pattern.pattern_type,
                "detected": pattern.detected,
                "confidence": pattern.confidence,
                "evidence": pattern.evidence,
            }
            pattern_summary.append(pattern_info)

        return {
            "status": "analysis_complete",
            "warning_level": analysis.warning_level,
            "technologies_detected": tech_summary,
            "anti_patterns_detected": pattern_summary,
            "recommendations": analysis.recommendations,
            "research_questions": analysis.research_questions,
            "effort_analysis": analysis.effort_analysis,
            "analysis_type": "integration_pattern_detection",
        }
