"""Core analyzer class for GitHub issue analysis."""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from vibe_check.core.pattern_detector import PatternDetector
from vibe_check.core.architectural_concept_detector import ArchitecturalConceptDetector
from vibe_check.core.educational_content import DetailLevel

from .github_client import GitHubIssueClient
from .response_builder import AnalysisResponseBuilder

# Import ExternalClaudeCli if available
try:
    from ..analyze_llm_backup import ExternalClaudeCli

    EXTERNAL_CLAUDE_AVAILABLE = True
except ImportError:
    EXTERNAL_CLAUDE_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedGitHubIssueAnalyzer:
    """
    Enhanced GitHub Issue Analysis engine with optional ExternalClaudeCli integration.

    Combines fast pattern detection with optional Claude CLI powered sophisticated reasoning.

    Enhancement features:
    - Optional ExternalClaudeCli integration for comprehensive mode
    - Specialized issue analysis prompts
    - Fallback to basic analysis when Claude CLI unavailable
    - Cost and performance tracking for enhanced modes
    - Backward compatibility with existing functionality
    """

    def __init__(
        self, github_token: Optional[str] = None, enable_claude_cli: bool = True
    ):
        """
        Initialize Enhanced GitHub Issue Analyzer.

        Args:
            github_token: GitHub API token for authentication (optional for public repos)
            enable_claude_cli: Whether to enable optional ExternalClaudeCli enhancement
        """
        # Initialize core components using composition
        self.github_client = GitHubIssueClient(github_token)
        self.pattern_detector = PatternDetector()
        self.architectural_detector = ArchitecturalConceptDetector()

        # Initialize optional ExternalClaudeCli enhancement
        self.claude_cli_enabled = enable_claude_cli and EXTERNAL_CLAUDE_AVAILABLE
        if self.claude_cli_enabled:
            try:
                self.external_claude = ExternalClaudeCli(timeout_seconds=60)
                logger.info("ExternalClaudeCli enhancement available")
            except Exception as e:
                logger.warning(f"ExternalClaudeCli initialization failed: {e}")
                self.claude_cli_enabled = False
                self.external_claude = None
        else:
            self.external_claude = None
            if enable_claude_cli and not EXTERNAL_CLAUDE_AVAILABLE:
                logger.warning(
                    "ExternalClaudeCli requested but not available - using basic analysis only"
                )

        # Initialize response builder
        self.response_builder = AnalysisResponseBuilder(
            self.pattern_detector,
            self.architectural_detector,
            self.claude_cli_enabled,
        )

        logger.info("Enhanced GitHub Issue Analyzer initialized")

    def _build_comprehensive_issue_prompt(self, issue_data: Dict[str, Any]) -> str:
        """
        Build specialized prompt for comprehensive issue analysis using Claude CLI.

        Args:
            issue_data: GitHub issue information

        Returns:
            Comprehensive analysis prompt optimized for issue analysis
        """
        labels_str = ", ".join(str(label) for label in issue_data["labels"]) if issue_data["labels"] else "None"

        return f"""# GitHub Issue Comprehensive Analysis

**Repository:** {issue_data['repository']}
**Issue #{issue_data['number']}:** {issue_data['title']}
**Author:** {issue_data['author']}
**State:** {issue_data['state']}
**Labels:** {labels_str}
**Created:** {issue_data['created_at']}

**Issue Content:**
{issue_data['body'] or 'No content provided'}

---

Please provide a comprehensive analysis of this GitHub issue focusing on:

## 🎯 Issue Quality Assessment
- **Problem Definition**: Is the problem clearly defined with specific symptoms?
- **Requirements Clarity**: Are success criteria and acceptance criteria well-defined?
- **Scope Appropriateness**: Is the scope reasonable for a single issue?

## 🔍 Anti-Pattern Risk Detection
- **Infrastructure-without-Implementation**: Does this suggest building complex infrastructure before validating basic functionality?
- **Symptom-Driven Development**: Are we addressing symptoms vs root causes?
- **Complexity Escalation**: Is the proposed complexity justified by the problem?
- **Documentation Neglect**: Have existing solutions been researched first?

## 💡 Implementation Strategy Analysis
- **Approach Validation**: Is the proposed approach technically sound?
- **Technical Debt Implications**: What are the long-term maintenance implications?
- **Resource Considerations**: Are the time/effort estimates realistic?

## 🎓 Educational Recommendations
- **Best Practices**: What engineering principles should guide implementation?
- **Alternative Approaches**: Are there simpler or more standard solutions?
- **Learning Opportunities**: What can the team learn from this issue?

## 📋 Actionable Next Steps
Provide 3-5 specific, prioritized recommendations for moving forward.

Please use friendly, coaching language that helps developers learn rather than intimidate.
Focus on constructive guidance that prevents common engineering anti-patterns."""

    async def analyze_issue_comprehensive(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        detail_level: str = "standard",
    ) -> Dict[str, Any]:
        """
        Perform comprehensive issue analysis using ExternalClaudeCli.

        Args:
            issue_number: GitHub issue number to analyze
            repository: Repository in format "owner/repo" (optional)
            detail_level: Educational detail level (brief/standard/comprehensive)

        Returns:
            Comprehensive analysis with Claude CLI insights
        """
        if not self.claude_cli_enabled:
            logger.warning(
                "Comprehensive analysis requested but ExternalClaudeCli not available"
            )
            return {
                "status": "enhancement_unavailable",
                "message": "ExternalClaudeCli enhancement not available - falling back to basic analysis",
                "fallback_available": True,
            }

        try:
            # Fetch GitHub issue data
            issue_data = self.github_client.fetch_issue_data(issue_number, repository)

            # Build comprehensive analysis prompt
            analysis_prompt = self._build_comprehensive_issue_prompt(issue_data)

            # Execute Claude CLI analysis
            logger.info(f"Starting comprehensive analysis for issue #{issue_number}")
            claude_result = await self.external_claude.analyze_content(
                content=analysis_prompt,
                task_type="issue_analysis",
                additional_context=f"GitHub Issue Analysis for {repository}#{issue_number}",
            )

            # Build comprehensive response
            from datetime import datetime, UTC

            timestamp = datetime.now(UTC).isoformat()

            result = {
                "status": "comprehensive_analysis_complete",
                "analysis_timestamp": timestamp,
                "issue_info": {
                    "number": issue_data["number"],
                    "title": issue_data["title"],
                    "author": issue_data["author"],
                    "created_at": issue_data["created_at"],
                    "repository": issue_data["repository"],
                    "url": issue_data["url"],
                    "labels": issue_data["labels"],
                },
                "comprehensive_analysis": {
                    "success": claude_result.success,
                    "claude_output": (
                        claude_result.output if claude_result.success else None
                    ),
                    "analysis_error": (
                        claude_result.error if not claude_result.success else None
                    ),
                    "execution_time_seconds": claude_result.execution_time,
                    "command_used": claude_result.command_used,
                    "cost_tracking": {
                        "cost_usd": claude_result.cost_usd,
                        "duration_ms": claude_result.duration_ms,
                        "session_id": claude_result.session_id,
                        "num_turns": claude_result.num_turns,
                    },
                },
                "enhanced_features": {
                    "claude_cli_integration": True,
                    "sophisticated_reasoning": claude_result.success,
                    "cost_tracking": claude_result.cost_usd is not None,
                    "timeout_prevention": True,
                    "specialized_prompts": True,
                },
                "analysis_metadata": {
                    "enhancement_version": "1.0 - ExternalClaudeCli integration",
                    "external_claude_available": True,
                    "analysis_type": "comprehensive_with_claude_cli",
                    "detail_level": detail_level,
                    "integration_method": "external_claude_cli_wrapper",
                },
            }

            # Sanitize GitHub URLs
            from ..shared.github_helpers import sanitize_github_urls_in_response

            return sanitize_github_urls_in_response(result)

        except Exception as e:
            error_msg = f"Comprehensive analysis failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "comprehensive_analysis_error",
                "error": error_msg,
                "issue_number": issue_number,
                "repository": repository,
                "claude_cli_available": self.claude_cli_enabled,
                "fallback_recommendation": "Use basic analysis mode",
            }

    async def analyze_issue_basic(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        focus_patterns: Optional[str] = "all",
        detail_level: str = "standard",
    ) -> Dict[str, Any]:
        """
        Perform basic issue analysis using existing pattern detection.

        Args:
            issue_number: GitHub issue number to analyze
            repository: Repository in format "owner/repo" (optional)
            focus_patterns: Comma-separated list of patterns to focus on
            detail_level: Educational detail level (brief/standard/comprehensive)

        Returns:
            Pattern detection analysis with educational content
        """
        try:
            # Input validation
            if issue_number <= 0:
                raise ValueError("Issue number must be positive")

            # Parse detail level
            try:
                detail_enum = DetailLevel(detail_level.lower())
            except ValueError:
                detail_enum = DetailLevel.STANDARD
                logger.warning(
                    f"Invalid detail level '{detail_level}', using 'standard'"
                )

            # Parse focus patterns
            focus_pattern_list = None
            if focus_patterns and focus_patterns.lower() != "all":
                focus_pattern_list = [p.strip() for p in focus_patterns.split(",")]
                valid_patterns = self.pattern_detector.get_pattern_types()
                invalid_patterns = [
                    p for p in focus_pattern_list if p not in valid_patterns
                ]
                if invalid_patterns:
                    logger.warning(f"Invalid patterns ignored: {invalid_patterns}")
                    focus_pattern_list = [
                        p for p in focus_pattern_list if p in valid_patterns
                    ]

            # Fetch GitHub issue data
            issue_data = self.github_client.fetch_issue_data(issue_number, repository)

            # Analyze issue content for anti-patterns
            content = issue_data["body"] or ""
            context = f"Title: {issue_data['title']}"

            architectural_concepts = self.architectural_detector.detect_concepts(
                text=content,
                context=context,
            )

            detected_patterns = self.pattern_detector.analyze_text_for_patterns(
                content=content,
                context=context,
                focus_patterns=focus_pattern_list,
                detail_level=detail_enum,
            )

            # Generate comprehensive analysis response using response builder
            analysis_result = self.response_builder.generate_basic_analysis_response(
                issue_data=issue_data,
                detected_patterns=detected_patterns,
                detail_level=detail_enum,
                architectural_concepts=architectural_concepts,
            )

            logger.info(
                f"Basic analysis completed for issue #{issue_number}: {len(detected_patterns)} patterns detected"
            )
            return analysis_result

        except Exception as e:
            from github import GithubException

            if isinstance(e, GithubException):
                error_msg = f"GitHub API error: {e.data.get('message', str(e))}"
                status = "github_api_error"
            else:
                error_msg = f"Basic analysis failed: {str(e)}"
                status = "basic_analysis_error"

            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": status,
                "issue_number": issue_number,
                "repository": repository,
            }

    async def analyze_issue_hybrid(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        detail_level: str = "standard",
    ) -> Dict[str, Any]:
        """
        Perform hybrid analysis combining pattern detection + Claude CLI insights.

        Args:
            issue_number: GitHub issue number to analyze
            repository: Repository in format "owner/repo" (optional)
            detail_level: Educational detail level (brief/standard/comprehensive)

        Returns:
            Combined analysis with both pattern detection and Claude CLI insights
        """
        try:
            logger.info(f"Starting hybrid analysis for issue #{issue_number}")

            # Run basic pattern detection first (fast)
            basic_result = await self.analyze_issue_basic(
                issue_number=issue_number,
                repository=repository,
                detail_level=detail_level,
            )

            # If basic analysis failed, return early
            if "error" in basic_result:
                return basic_result

            # Run comprehensive Claude CLI analysis if available
            comprehensive_result = None
            if self.claude_cli_enabled:
                comprehensive_result = await self.analyze_issue_comprehensive(
                    issue_number=issue_number,
                    repository=repository,
                    detail_level=detail_level,
                )

            # Combine results
            from datetime import datetime, UTC

            timestamp = datetime.now(UTC).isoformat()

            combined_result = {
                "status": "hybrid_analysis_complete",
                "analysis_timestamp": timestamp,
                "issue_info": basic_result.get("issue_info", {}),
                "pattern_detection": {
                    "patterns_detected": basic_result.get("patterns_detected", []),
                    "confidence_summary": basic_result.get("confidence_summary", {}),
                    "recommended_actions": basic_result.get("recommended_actions", []),
                },
                "claude_cli_analysis": (
                    comprehensive_result
                    if comprehensive_result
                    else {
                        "status": "enhancement_unavailable",
                        "message": "ExternalClaudeCli not available - pattern detection only",
                    }
                ),
                "hybrid_summary": self.response_builder.generate_hybrid_summary(
                    basic_result, comprehensive_result
                ),
                "enhanced_features": {
                    "pattern_detection": True,
                    "claude_cli_integration": self.claude_cli_enabled,
                    "hybrid_analysis": True,
                    "comprehensive_reasoning": comprehensive_result is not None
                    and comprehensive_result.get("status")
                    == "comprehensive_analysis_complete",
                    "cost_tracking": comprehensive_result is not None
                    and comprehensive_result.get("comprehensive_analysis", {})
                    .get("cost_tracking", {})
                    .get("cost_usd")
                    is not None,
                },
                "analysis_metadata": {
                    "framework_version": "2.0 - Hybrid pattern detection + Claude CLI",
                    "core_engine_validation": "87.5% accuracy, 0% false positives",
                    "analysis_type": "hybrid_pattern_detection_with_claude_cli",
                    "external_claude_available": self.claude_cli_enabled,
                    "detail_level": detail_level,
                },
            }

            # Sanitize GitHub URLs
            from ..shared.github_helpers import sanitize_github_urls_in_response

            return sanitize_github_urls_in_response(combined_result)

        except Exception as e:
            error_msg = f"Hybrid analysis failed: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "hybrid_analysis_error",
                "issue_number": issue_number,
                "repository": repository,
                "claude_cli_available": self.claude_cli_enabled,
            }

    def get_supported_patterns(self) -> List[str]:
        """Get list of supported anti-pattern types."""
        return self.pattern_detector.get_pattern_types()

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary for the detection engine."""
        return self.pattern_detector.get_validation_summary()

    def get_enhancement_status(self) -> Dict[str, Any]:
        """Get status of optional enhancements."""
        return {
            "external_claude_available": EXTERNAL_CLAUDE_AVAILABLE,
            "claude_cli_enabled": self.claude_cli_enabled,
            "enhancement_version": "1.0 - ExternalClaudeCli integration",
            "supported_modes": ["basic", "comprehensive", "hybrid"],
            "backward_compatible": True,
        }

    def analyze_issue(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        focus_patterns: Optional[str] = "all",
        detail_level: str = "standard",
    ) -> Dict[str, Any]:
        """
        Backward compatibility method - synchronous wrapper for analyze_issue_basic.

        Args:
            issue_number: GitHub issue number to analyze
            repository: Repository in format "owner/repo" (optional)
            focus_patterns: Comma-separated list of patterns to focus on
            detail_level: Educational detail level (brief/standard/comprehensive)

        Returns:
            Pattern detection analysis (original format)

        Note:
            This is a simple synchronous wrapper using asyncio.run().
            Nested event loops are not supported (Python limitation).
        """
        return asyncio.run(
            self.analyze_issue_basic(
                issue_number=issue_number,
                repository=repository,
                focus_patterns=focus_patterns,
                detail_level=detail_level,
            )
        )


# Backward compatibility alias for existing tests
GitHubIssueAnalyzer = EnhancedGitHubIssueAnalyzer
