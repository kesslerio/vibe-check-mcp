"""
Integration Decision Check Tool

Validates integration approaches against official alternatives to prevent
unnecessary custom development. Based on real-world case studies including
the Cognee integration failure where 2+ weeks were spent building custom
REST servers instead of using the official Docker container.

Features:
- Official alternative detection
- Custom development justification requirements
- Decision framework generation
- Red flag detection for anti-patterns
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Web search capabilities available via MCP tools
WEB_SEARCH_AVAILABLE = True  # We can always try MCP tools

# Configuration constants
MAX_CUSTOM_FEATURES = 20
MAX_FEATURE_LENGTH = 200
MAX_TECHNOLOGY_NAME_LENGTH = 50

# Scoring constants for decision matrix
SCORING = {
    "official_solution": {
        "development_time": 9,
        "maintenance_burden": 9,
        "reliability_support": 9,
        "customization_needs": 6,
    },
    "custom_development": {
        "development_time": 3,
        "maintenance_burden": 2,
        "reliability_support": 5,
        "customization_needs": 9,
    },
}

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def validate_inputs(technology: str, custom_features: List[str]) -> None:
    """Validate inputs for integration decision checking."""
    if not technology or not technology.strip():
        raise ValidationError("Technology name cannot be empty")

    if len(technology) > MAX_TECHNOLOGY_NAME_LENGTH:
        raise ValidationError(
            f"Technology name too long (max {MAX_TECHNOLOGY_NAME_LENGTH} chars)"
        )

    if len(custom_features) > MAX_CUSTOM_FEATURES:
        raise ValidationError(f"Too many custom features (max {MAX_CUSTOM_FEATURES})")

    for feature in custom_features:
        if len(feature) > MAX_FEATURE_LENGTH:
            raise ValidationError(
                f"Feature name too long: '{feature}' (max {MAX_FEATURE_LENGTH} chars)"
            )


def analyze_features_and_flags(
    custom_features: List[str], technology_info: Dict[str, Any]
) -> tuple:
    """Analyze custom features and detect red flags."""
    kb = IntegrationKnowledgeBase()
    red_flags_detected = kb.detect_red_flags(custom_features, technology_info)
    feature_coverage = kb.analyze_feature_coverage(custom_features, technology_info)
    warning_level = calculate_warning_level(custom_features, technology_info)

    return red_flags_detected, feature_coverage, warning_level


def build_recommendation_result(
    technology: str,
    technology_info: Dict[str, Any],
    red_flags_detected: List[str],
    warning_level: str,
    custom_features: List[str],
) -> "IntegrationRecommendation":
    """Build the final recommendation result."""
    # Analyze official solutions
    official_solutions = []
    if technology_info.get("official_container"):
        official_solutions.append(f"Docker: {technology_info['official_container']}")
    if technology_info.get("official_sdks"):
        official_solutions.extend(
            [f"SDK: {sdk}" for sdk in technology_info["official_sdks"]]
        )

    # Generate decision framework and other components
    decision_matrix = generate_decision_matrix(technology, custom_features)
    questions = generate_validation_questions(technology, custom_features)
    recommendation = generate_recommendation(
        technology, custom_features, technology_info
    )

    # Determine requirements
    research_required = bool(red_flags_detected) or warning_level in [
        "warning",
        "critical",
    ]
    custom_justification_needed = warning_level in ["caution", "warning", "critical"]

    # Generate next steps
    next_steps = []
    if research_required:
        next_steps.append(f"Test official {technology} solution with your requirements")
        if technology_info.get("documentation"):
            next_steps.append(
                f"Review documentation: {', '.join(technology_info['documentation'])}"
            )

    if red_flags_detected:
        next_steps.append(
            "Document specific gaps in official solution that justify custom development"
        )

    if custom_justification_needed:
        next_steps.append(
            "Create decision document comparing official vs custom approaches"
        )

    if not next_steps:
        next_steps.append("Proceed with integration approach comparison")

    return IntegrationRecommendation(
        technology=technology,
        warning_level=warning_level,
        official_solutions=official_solutions,
        custom_justification_needed=custom_justification_needed,
        research_required=research_required,
        red_flags_detected=red_flags_detected,
        decision_matrix=decision_matrix,
        next_steps=next_steps,
        recommendation=recommendation,
    )


@dataclass
class IntegrationRecommendation:
    """Structured recommendation for integration decisions."""

    technology: str
    warning_level: str  # "none", "caution", "warning", "critical"
    official_solutions: List[str]
    custom_justification_needed: bool
    research_required: bool
    red_flags_detected: List[str]
    decision_matrix: Dict[str, Any]
    next_steps: List[str]
    recommendation: str


class IntegrationKnowledgeBase:
    """Knowledge base for integration technologies and their official solutions."""

    def __init__(self, enable_web_search: bool = True):
        self.knowledge = self._load_knowledge_base()
        self.enable_web_search = enable_web_search and WEB_SEARCH_AVAILABLE

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load integration knowledge from data file."""
        try:
            # Path to knowledge base relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            kb_path = project_root / "data" / "integration_knowledge_base.json"

            # Security: Validate path stays within project bounds
            resolved_path = kb_path.resolve()
            project_root_resolved = project_root.resolve()
            if not str(resolved_path).startswith(str(project_root_resolved)):
                logger.error(
                    f"Knowledge base path outside project bounds: {resolved_path}"
                )
                return {}

            if kb_path.exists():
                with open(kb_path, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"Knowledge base not found at {kb_path}")
                return {}
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"File access error loading knowledge base: {e}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in knowledge base: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            return {}

    def get_technology_info(self, technology: str) -> Dict[str, Any]:
        """Get official information for a technology, enhanced with web search if available."""
        base_info = self.knowledge.get(technology.lower(), {})

        # Enhance with web search if enabled and technology not in knowledge base
        if self.enable_web_search and not base_info:
            try:
                enhanced_info = self._search_technology_info(technology)
                if enhanced_info:
                    return enhanced_info
            except Exception as e:
                logger.warning(f"Web search failed for {technology}: {e}")

        return base_info

    def _search_technology_info(self, technology: str) -> Dict[str, Any]:
        """Search for technology information using web search."""
        if not WEB_SEARCH_AVAILABLE:
            return {}

        try:
            # Search for official documentation and Docker containers
            search_queries = [
                f"{technology} official documentation deployment",
                f"{technology} official docker container",
                f"{technology} official SDK API",
                f"{technology} vs custom implementation",
            ]

            enhanced_info = {
                "features": [],
                "documentation": [],
                "red_flags": ["custom implementation"],  # Generic red flag
                "official_benefits": ["Official support", "Maintained by vendor"],
                "web_search_enhanced": True,
                "search_timestamp": "recent",
            }

            # In a real implementation, we would use web search here
            # For now, we'll return basic structure that can be populated
            logger.info(f"Web search enhancement attempted for {technology}")

            return enhanced_info

        except Exception as e:
            logger.error(f"Failed to enhance {technology} info with web search: {e}")
            return {}

    def detect_red_flags(
        self, custom_features: List[str], technology_info: Dict[str, Any]
    ) -> List[str]:
        """Detect red flags indicating unnecessary custom development."""
        detected_flags: List[str] = []
        seen_flags = set()
        flagged_features = set()
        red_flags = technology_info.get("red_flags", [])

        for feature in custom_features:
            feature_lower = feature.lower()
            for flag in red_flags:
                if flag.lower() in feature_lower:
                    message = (
                        f"Custom {feature} (official alternative available)"
                    )
                    if message not in seen_flags:
                        detected_flags.append(message)
                        seen_flags.add(message)
                        flagged_features.add(feature_lower)

        custom_indicators = technology_info.get("common_custom_indicators", [])

        for feature in custom_features:
            feature_lower = feature.lower()
            if feature_lower in flagged_features:
                continue
            for indicator in custom_indicators:
                indicator_words = indicator.lower().split()
                if all(word in feature_lower for word in indicator_words):
                    message = (
                        f"Custom {feature} (matches indicator '{indicator}' for unnecessary custom work)"
                    )
                    if message not in seen_flags:
                        detected_flags.append(message)
                        seen_flags.add(message)

        return detected_flags

    def analyze_feature_coverage(
        self, custom_features: List[str], technology_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how well official solutions cover custom features."""
        official_features = technology_info.get("features", [])
        coverage_analysis = {
            "covered_by_official": [],
            "gaps": [],
            "coverage_percentage": 0,
        }

        for custom_feature in custom_features:
            custom_lower = custom_feature.lower()
            covered = False

            for official_feature in official_features:
                if (
                    custom_lower in official_feature.lower()
                    or official_feature.lower() in custom_lower
                ):
                    coverage_analysis["covered_by_official"].append(
                        {"custom": custom_feature, "official": official_feature}
                    )
                    covered = True
                    break

            if not covered:
                coverage_analysis["gaps"].append(custom_feature)

        if custom_features:
            coverage_analysis["coverage_percentage"] = (
                len(coverage_analysis["covered_by_official"])
                / len(custom_features)
                * 100
            )

        return coverage_analysis


def calculate_warning_level(
    custom_features: List[str], technology_info: Dict[str, Any]
) -> str:
    """Calculate warning level based on red flags and feature coverage."""
    if not technology_info:
        return "caution"  # Unknown technology, proceed carefully

    if technology_info.get("web_search_enhanced"):
        # Web search fallback provides limited confidence. Treat as caution by default.
        return "caution"

    red_flags = len(
        [
            f
            for f in custom_features
            if any(
                flag.lower() in f.lower()
                for flag in technology_info.get("red_flags", [])
            )
        ]
    )

    indicator_matches = 0
    for feature in custom_features:
        feature_lower = feature.lower()
        for indicator in technology_info.get("common_custom_indicators", []):
            indicator_words = indicator.lower().split()
            if all(word in feature_lower for word in indicator_words):
                indicator_matches += 1
                break

    total_flags = red_flags + indicator_matches

    official_features = len(technology_info.get("features", []))

    if total_flags >= 3:
        return "critical"
    elif total_flags >= 2:
        return "warning"
    elif total_flags >= 1 or official_features >= 3:
        return "caution"
    else:
        return "none"


def generate_decision_matrix(
    technology: str, custom_features: List[str]
) -> Dict[str, Any]:
    """Generate decision matrix for integration choices."""
    return {
        "options": [
            {
                "name": "Official Container/SDK",
                "pros": [
                    "Maintained by vendor",
                    "Production ready",
                    "Security updates",
                ],
                "cons": ["Less customization", "Potential bloat"],
                "research_required": True,
            },
            {
                "name": "Community Solution",
                "pros": ["Community tested", "Often documented"],
                "cons": ["Maintenance burden", "Security responsibility"],
                "research_required": True,
            },
            {
                "name": "Custom Development",
                "pros": ["Full control", "Exact requirements"],
                "cons": [
                    "Development time",
                    "Maintenance burden",
                    "Security responsibility",
                ],
                "justification_required": True,
            },
        ],
        "criteria": [
            {"name": "Development Time", "weight": 0.25},
            {"name": "Maintenance Burden", "weight": 0.30},
            {"name": "Reliability/Support", "weight": 0.25},
            {"name": "Customization Needs", "weight": 0.20},
        ],
        "evaluation_questions": [
            f"Have you tested the official {technology} solution with your requirements?",
            f"What specific features does the official {technology} solution lack?",
            "Is the development time for custom solution justified by the gaps?",
            "Who will maintain the custom solution long-term?",
            "What are the security implications of custom development?",
        ],
    }


def generate_validation_questions(
    technology: str, custom_features: List[str]
) -> List[str]:
    """Generate technology-specific validation questions."""
    base_questions = [
        f"Have you reviewed the official {technology} documentation?",
        f"Have you tested the official {technology} solution with a basic setup?",
        f"What specific requirements prevent using the official {technology} approach?",
        "Have you searched for existing community solutions?",
        "Is the custom development complexity justified by the requirements?",
    ]

    # Add feature-specific questions
    if "authentication" in " ".join(custom_features).lower():
        base_questions.append(
            "Does the official solution provide authentication features?"
        )

    if "api" in " ".join(custom_features).lower():
        base_questions.append(
            "Does the official solution expose the needed API endpoints?"
        )

    if "storage" in " ".join(custom_features).lower():
        base_questions.append("How does the official solution handle data storage?")

    return base_questions


def generate_recommendation(
    technology: str, custom_features: List[str], technology_info: Dict[str, Any]
) -> str:
    """Generate specific recommendation based on analysis."""
    if not technology_info:
        return f"⚠️ Research required: Unknown technology '{technology}'. Please research official deployment options before custom development."

    red_flags = len(
        [
            f
            for f in custom_features
            if any(
                flag.lower() in f.lower()
                for flag in technology_info.get("red_flags", [])
            )
        ]
    )

    indicator_matches = 0
    for feature in custom_features:
        feature_lower = feature.lower()
        for indicator in technology_info.get("common_custom_indicators", []):
            indicator_words = indicator.lower().split()
            if all(word in feature_lower for word in indicator_words):
                indicator_matches += 1
                break

    total_flags = red_flags + indicator_matches

    official_solutions = technology_info.get(
        "official_container"
    ) or technology_info.get("official_sdks", [])

    if total_flags >= 2 and official_solutions:
        return f"🚨 STOP: Official {technology} solution likely covers your needs. Test official approach first before custom development."
    elif total_flags >= 1 and official_solutions:
        return f"⚠️ CAUTION: Official {technology} solution may cover your needs. Research and test official approach before proceeding with custom development."
    elif official_solutions:
        return f"✅ RESEARCH: Official {technology} solutions available. Compare official vs custom approaches before deciding."
    else:
        return f"📋 DOCUMENT: Limited official {technology} information available. Document research process and custom development justification."


def check_official_alternatives(
    technology: str, custom_features: List[str]
) -> IntegrationRecommendation:
    """
    Check if technology provides official solutions for custom features.

    Args:
        technology: Name of the technology (e.g., "cognee", "supabase")
        custom_features: List of features being custom developed

    Returns:
        IntegrationRecommendation with analysis and recommendations

    Raises:
        ValidationError: If inputs are invalid
    """
    # Validate inputs
    validate_inputs(technology, custom_features)

    # Get technology information
    kb = IntegrationKnowledgeBase()
    technology_info = kb.get_technology_info(technology)

    # Analyze features and detect red flags
    red_flags_detected, feature_coverage, warning_level = analyze_features_and_flags(
        custom_features, technology_info
    )

    # Build and return recommendation
    return build_recommendation_result(
        technology, technology_info, red_flags_detected, warning_level, custom_features
    )


def analyze_integration_text(text: str) -> Dict[str, Any]:
    """
    Analyze text for integration patterns and provide recommendations.

    Args:
        text: Text to analyze for integration anti-patterns

    Returns:
        Analysis results with recommendations
    """
    text_lower = text.lower()

    # Detect technologies mentioned
    kb = IntegrationKnowledgeBase()
    detected_technologies = []

    for tech in kb.knowledge.keys():
        if tech in text_lower:
            detected_technologies.append(tech)

    # Detect potential custom development indicators
    custom_indicators = [
        "custom",
        "build",
        "implement",
        "create",
        "develop",
        "write",
        "fastapi",
        "flask",
        "express",
        "server",
        "api",
        "rest",
        "authentication",
        "auth",
        "jwt",
        "storage",
        "database",
    ]

    detected_custom_work = [
        indicator for indicator in custom_indicators if indicator in text_lower
    ]

    results = {
        "detected_technologies": detected_technologies,
        "detected_custom_work": detected_custom_work,
        "recommendations": [],
        "warning_level": "none",
    }

    # Generate recommendations for each detected technology
    for tech in detected_technologies:
        if detected_custom_work:
            recommendation = check_official_alternatives(tech, detected_custom_work)
            results["recommendations"].append(
                {"technology": tech, "analysis": recommendation}
            )

            # Update warning level to highest detected
            tech_warning = recommendation.warning_level
            if tech_warning == "critical":
                results["warning_level"] = "critical"
            elif tech_warning == "warning" and results["warning_level"] != "critical":
                results["warning_level"] = "warning"
            elif tech_warning == "caution" and results["warning_level"] not in [
                "critical",
                "warning",
            ]:
                results["warning_level"] = "caution"

    return results
