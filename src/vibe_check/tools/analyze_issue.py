"""
Enhanced GitHub Issue Analysis with ExternalClaudeCli Integration

Implements comprehensive GitHub issue analysis combining:
1. Fast pattern detection (existing vibe check framework)
2. Optional Claude CLI powered sophisticated reasoning (new enhancement)

This enhanced version provides backward compatible analysis while optionally
leveraging the proven ExternalClaudeCli wrapper for comprehensive mode analysis.

Issue #65 implementation: Migrate analyze_issue.py to use ExternalClaudeCli wrapper.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from github import Github, GithubException
from github.Issue import Issue

from ..core.pattern_detector import PatternDetector, DetectionResult
from ..core.educational_content import DetailLevel
from .legacy.vibe_check_framework import VibeCheckFramework, VibeCheckMode, get_vibe_check_framework

# Import the proven ExternalClaudeCli wrapper from analyze_llm_backup.py
try:
    from .analyze_llm_backup import ExternalClaudeCli, ClaudeCliResult
    EXTERNAL_CLAUDE_AVAILABLE = True
except ImportError:
    EXTERNAL_CLAUDE_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class EnhancedGitHubIssueAnalyzer:
    """
    Enhanced GitHub Issue Analysis engine with optional ExternalClaudeCli integration.
    
    Combines fast pattern detection (87.5% accuracy) with optional Claude CLI powered
    sophisticated reasoning for comprehensive mode analysis.
    
    Enhancement features:
    - Optional ExternalClaudeCli integration for comprehensive mode
    - Specialized issue analysis prompts
    - Fallback to basic analysis when Claude CLI unavailable
    - Cost and performance tracking for enhanced modes
    - Backward compatibility with existing analyze_issue_nollm functionality
    """
    
    def __init__(self, github_token: Optional[str] = None, enable_claude_cli: bool = True):
        """
        Initialize Enhanced GitHub Issue Analyzer.
        
        Args:
            github_token: GitHub API token for authentication (optional for public repos)
            enable_claude_cli: Whether to enable optional ExternalClaudeCli enhancement
        """
        self.github_client = Github(github_token) if github_token else Github()
        self.pattern_detector = PatternDetector()
        
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
                logger.warning("ExternalClaudeCli requested but not available - using basic analysis only")
        
        logger.info("Enhanced GitHub Issue Analyzer initialized")
    
    def _build_comprehensive_issue_prompt(self, issue_data: Dict[str, Any]) -> str:
        """
        Build specialized prompt for comprehensive issue analysis using Claude CLI.
        
        Args:
            issue_data: GitHub issue information
            
        Returns:
            Comprehensive analysis prompt optimized for issue analysis
        """
        return f"""# GitHub Issue Comprehensive Analysis

**Repository:** {issue_data['repository']}
**Issue #{issue_data['number']}:** {issue_data['title']}
**Author:** {issue_data['author']}
**State:** {issue_data['state']}
**Labels:** {', '.join(issue_data['labels']) if issue_data['labels'] else 'None'}
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
        detail_level: str = "standard"
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
            logger.warning("Comprehensive analysis requested but ExternalClaudeCli not available")
            return {
                "status": "enhancement_unavailable",
                "message": "ExternalClaudeCli enhancement not available - falling back to basic analysis",
                "fallback_available": True
            }
        
        try:
            # Fetch GitHub issue data
            issue_data = self._fetch_issue_data(issue_number, repository)
            
            # Build comprehensive analysis prompt
            analysis_prompt = self._build_comprehensive_issue_prompt(issue_data)
            
            # Execute Claude CLI analysis
            logger.info(f"Starting comprehensive analysis for issue #{issue_number}")
            claude_result = await self.external_claude.analyze_content(
                content=analysis_prompt,
                task_type="issue_analysis",
                additional_context=f"GitHub Issue Analysis for {repository}#{issue_number}"
            )
            
            # Build comprehensive response
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            result = {
                "status": "comprehensive_analysis_complete",
                "analysis_timestamp": timestamp,
                
                # Issue information
                "issue_info": {
                    "number": issue_data["number"],
                    "title": issue_data["title"],
                    "author": issue_data["author"],
                    "created_at": issue_data["created_at"],
                    "repository": issue_data["repository"],
                    "url": issue_data["url"],
                    "labels": issue_data["labels"]
                },
                
                # Claude CLI comprehensive analysis
                "comprehensive_analysis": {
                    "success": claude_result.success,
                    "claude_output": claude_result.output if claude_result.success else None,
                    "analysis_error": claude_result.error if not claude_result.success else None,
                    "execution_time_seconds": claude_result.execution_time,
                    "command_used": claude_result.command_used,
                    "cost_tracking": {
                        "cost_usd": claude_result.cost_usd,
                        "duration_ms": claude_result.duration_ms,
                        "session_id": claude_result.session_id,
                        "num_turns": claude_result.num_turns
                    }
                },
                
                # Enhanced capabilities metadata
                "enhanced_features": {
                    "claude_cli_integration": True,
                    "sophisticated_reasoning": claude_result.success,
                    "cost_tracking": claude_result.cost_usd is not None,
                    "timeout_prevention": True,
                    "specialized_prompts": True
                },
                
                # Analysis metadata
                "analysis_metadata": {
                    "enhancement_version": "1.0 - ExternalClaudeCli integration",
                    "external_claude_available": True,
                    "analysis_type": "comprehensive_with_claude_cli",
                    "detail_level": detail_level,
                    "integration_method": "external_claude_cli_wrapper"
                }
            }
            
            # Sanitize GitHub URLs
            from .shared.github_helpers import sanitize_github_urls_in_response
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
                "fallback_recommendation": "Use basic analysis mode"
            }
    
    def analyze_issue_basic(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        focus_patterns: Optional[str] = "all",
        detail_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Perform basic issue analysis using existing pattern detection (backward compatible).
        
        This is the original analyze_issue_nollm functionality preserved for compatibility.
        
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
                logger.warning(f"Invalid detail level '{detail_level}', using 'standard'")
            
            # Parse focus patterns
            focus_pattern_list = None
            if focus_patterns and focus_patterns.lower() != "all":
                focus_pattern_list = [p.strip() for p in focus_patterns.split(",")]
                # Validate pattern names
                valid_patterns = self.pattern_detector.get_pattern_types()
                invalid_patterns = [p for p in focus_pattern_list if p not in valid_patterns]
                if invalid_patterns:
                    logger.warning(f"Invalid patterns ignored: {invalid_patterns}")
                    focus_pattern_list = [p for p in focus_pattern_list if p in valid_patterns]
            
            # Fetch GitHub issue data
            issue_data = self._fetch_issue_data(issue_number, repository)
            
            # Analyze issue content for anti-patterns
            content = issue_data["body"] or ""
            context = f"Title: {issue_data['title']}"
            
            detected_patterns = self.pattern_detector.analyze_text_for_patterns(
                content=content,
                context=context,
                focus_patterns=focus_pattern_list,
                detail_level=detail_enum
            )
            
            # Generate comprehensive analysis response
            analysis_result = self._generate_basic_analysis_response(
                issue_data=issue_data,
                detected_patterns=detected_patterns,
                detail_level=detail_enum
            )
            
            logger.info(f"Basic analysis completed for issue #{issue_number}: {len(detected_patterns)} patterns detected")
            return analysis_result
            
        except GithubException as e:
            error_msg = f"GitHub API error: {e.data.get('message', str(e))}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "github_api_error",
                "issue_number": issue_number,
                "repository": repository
            }
            
        except Exception as e:
            error_msg = f"Basic analysis failed: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "basic_analysis_error", 
                "issue_number": issue_number,
                "repository": repository
            }
    
    async def analyze_issue_hybrid(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        detail_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Perform hybrid analysis combining pattern detection + Claude CLI insights.
        
        This provides the best of both worlds: fast pattern detection for immediate
        feedback combined with sophisticated Claude CLI reasoning for deep insights.
        
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
            basic_result = self.analyze_issue_basic(
                issue_number=issue_number,
                repository=repository,
                detail_level=detail_level
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
                    detail_level=detail_level
                )
            
            # Combine results
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            combined_result = {
                "status": "hybrid_analysis_complete",
                "analysis_timestamp": timestamp,
                
                # Issue information (from basic analysis)
                "issue_info": basic_result.get("issue_info", {}),
                
                # Pattern detection results
                "pattern_detection": {
                    "patterns_detected": basic_result.get("patterns_detected", []),
                    "confidence_summary": basic_result.get("confidence_summary", {}),
                    "recommended_actions": basic_result.get("recommended_actions", [])
                },
                
                # Claude CLI comprehensive analysis (if available)
                "claude_cli_analysis": comprehensive_result if comprehensive_result else {
                    "status": "enhancement_unavailable",
                    "message": "ExternalClaudeCli not available - pattern detection only"
                },
                
                # Hybrid analysis summary
                "hybrid_summary": self._generate_hybrid_summary(basic_result, comprehensive_result),
                
                # Enhanced capabilities
                "enhanced_features": {
                    "pattern_detection": True,
                    "claude_cli_integration": self.claude_cli_enabled,
                    "hybrid_analysis": True,
                    "comprehensive_reasoning": comprehensive_result is not None and comprehensive_result.get("status") == "comprehensive_analysis_complete",
                    "cost_tracking": comprehensive_result is not None and comprehensive_result.get("comprehensive_analysis", {}).get("cost_tracking", {}).get("cost_usd") is not None
                },
                
                # Analysis metadata
                "analysis_metadata": {
                    "framework_version": "2.0 - Hybrid pattern detection + Claude CLI",
                    "core_engine_validation": "87.5% accuracy, 0% false positives",
                    "analysis_type": "hybrid_pattern_detection_with_claude_cli",
                    "external_claude_available": self.claude_cli_enabled,
                    "detail_level": detail_level
                }
            }
            
            # Sanitize GitHub URLs
            from .shared.github_helpers import sanitize_github_urls_in_response
            return sanitize_github_urls_in_response(combined_result)
            
        except Exception as e:
            error_msg = f"Hybrid analysis failed: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "hybrid_analysis_error",
                "issue_number": issue_number,
                "repository": repository,
                "claude_cli_available": self.claude_cli_enabled
            }
    
    def _fetch_issue_data(self, issue_number: int, repository: Optional[str]) -> Dict[str, Any]:
        """
        Fetch GitHub issue data via GitHub API.
        
        Args:
            issue_number: Issue number to fetch
            repository: Repository in format "owner/repo"
            
        Returns:
            Issue data dictionary
            
        Raises:
            ValueError: If repository format is invalid
            GithubException: If issue not found or API error
        """
        # Default repository handling
        if repository is None:
            repository = "kesslerio/vibe-check-mcp"  # Default to this project
        
        # Validate repository format
        if "/" not in repository:
            raise ValueError("Repository must be in format 'owner/repo'")
        
        try:
            # Get repository and issue
            repo = self.github_client.get_repo(repository)
            issue: Issue = repo.get_issue(issue_number)
            
            # Extract relevant issue data
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "author": issue.user.login,
                "created_at": issue.created_at.isoformat(),
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "url": issue.html_url,
                "repository": repository
            }
            
            logger.info(f"Fetched issue #{issue_number} from {repository}")
            return issue_data
            
        except GithubException as e:
            if e.status == 404:
                raise GithubException(404, {"message": f"Issue #{issue_number} not found in {repository}"})
            raise
    
    def _generate_basic_analysis_response(
        self,
        issue_data: Dict[str, Any],
        detected_patterns: List[DetectionResult],
        detail_level: DetailLevel
    ) -> Dict[str, Any]:
        """
        Generate basic analysis response with educational content (backward compatible).
        
        This preserves the exact functionality from analyze_issue_nollm.py.
        """
        # Generate confidence summary
        if detected_patterns:
            avg_confidence = sum(p.confidence for p in detected_patterns) / len(detected_patterns)
            max_confidence = max(p.confidence for p in detected_patterns)
            confidence_summary = {
                "total_patterns_detected": len(detected_patterns),
                "average_confidence": round(avg_confidence, 3),
                "highest_confidence": round(max_confidence, 3),
                "patterns_by_confidence": [
                    {
                        "pattern": p.pattern_type,
                        "confidence": round(p.confidence, 3),
                        "severity": "HIGH" if p.confidence >= 0.8 else "MEDIUM" if p.confidence >= 0.6 else "LOW"
                    }
                    for p in sorted(detected_patterns, key=lambda x: x.confidence, reverse=True)
                ]
            }
        else:
            confidence_summary = {
                "total_patterns_detected": 0,
                "average_confidence": 0.0,
                "highest_confidence": 0.0,
                "patterns_by_confidence": []
            }
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(detected_patterns, detail_level)
        
        # Format detected patterns for response
        patterns_detected = []
        for pattern in detected_patterns:
            pattern_data = {
                "pattern_type": pattern.pattern_type,
                "confidence": round(pattern.confidence, 3),
                "detected": pattern.detected,
                "evidence": pattern.evidence,
                "threshold": pattern.threshold,
                "educational_content": pattern.educational_content
            }
            patterns_detected.append(pattern_data)
        
        # Build comprehensive response
        analysis_response = {
            "status": "basic_analysis_complete",
            "analysis_timestamp": self._get_timestamp(),
            
            # Issue information
            "issue_info": {
                "number": issue_data["number"],
                "title": issue_data["title"],
                "author": issue_data["author"],
                "created_at": issue_data["created_at"],
                "repository": issue_data["repository"],
                "url": issue_data["url"],
                "labels": issue_data["labels"]
            },
            
            # Pattern detection results
            "patterns_detected": patterns_detected,
            "confidence_summary": confidence_summary,
            
            # Educational and actionable content
            "recommended_actions": recommended_actions,
            
            # Analysis metadata
            "analysis_metadata": {
                "core_engine_validation": "87.5% accuracy, 0% false positives",
                "detail_level": detail_level.value,
                "patterns_analyzed": self.pattern_detector.get_pattern_types(),
                "detection_method": "Phase 1 validated algorithms",
                "external_claude_available": self.claude_cli_enabled
            }
        }
        
        return analysis_response
    
    def _generate_hybrid_summary(
        self,
        basic_result: Dict[str, Any],
        comprehensive_result: Optional[Dict[str, Any]]
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
            "claude_cli_status": "not_available"
        }
        
        if comprehensive_result and comprehensive_result.get("status") == "comprehensive_analysis_complete":
            claude_analysis = comprehensive_result.get("comprehensive_analysis", {})
            if claude_analysis.get("success"):
                summary.update({
                    "claude_cli_status": "analysis_complete",
                    "claude_cli_execution_time": f"{claude_analysis.get('execution_time_seconds', 0):.2f}s",
                    "combined_analysis": "Pattern detection provides immediate feedback, Claude CLI provides deep insights",
                    "cost_tracking": claude_analysis.get("cost_tracking", {})
                })
            else:
                summary["claude_cli_status"] = f"analysis_failed: {claude_analysis.get('analysis_error', 'unknown error')}"
        elif comprehensive_result and comprehensive_result.get("status") == "enhancement_unavailable":
            summary["claude_cli_status"] = "enhancement_unavailable"
        
        return summary
    
    def _generate_recommended_actions(
        self,
        detected_patterns: List[DetectionResult],
        detail_level: DetailLevel
    ) -> List[str]:
        """Generate prioritized recommended actions based on detected patterns"""
        
        if not detected_patterns:
            actions = [
                "✅ No anti-patterns detected in this issue",
                "Continue with standard engineering practices"
            ]
            
            # Add Claude CLI recommendation if available
            if self.claude_cli_enabled:
                actions.append("💡 Consider using comprehensive analysis mode for detailed insights")
            else:
                actions.append("📚 Consider enabling ExternalClaudeCli for enhanced analysis capabilities")
            
            return actions
        
        actions = []
        
        # Sort patterns by confidence for prioritized recommendations
        sorted_patterns = sorted(detected_patterns, key=lambda x: x.confidence, reverse=True)
        
        for i, pattern in enumerate(sorted_patterns[:3]):  # Top 3 most confident patterns
            if pattern.confidence >= 0.8:
                priority = "🚨 CRITICAL"
            elif pattern.confidence >= 0.6:
                priority = "⚠️ HIGH PRIORITY"
            else:
                priority = "💡 CONSIDER"
            
            pattern_name = pattern.educational_content.get("pattern_name", pattern.pattern_type) if pattern.educational_content else pattern.pattern_type
            actions.append(f"{priority}: Address {pattern_name} pattern (confidence: {pattern.confidence:.0%})")
            
            # Add specific immediate actions from educational content
            if pattern.educational_content and "immediate_actions" in pattern.educational_content:
                immediate_actions = pattern.educational_content["immediate_actions"]
                if immediate_actions and isinstance(immediate_actions, list):
                    actions.extend(immediate_actions[:2])  # Add top 2 immediate actions
        
        # Add general recommendations
        if len(detected_patterns) > 1:
            actions.append("📋 Review all detected patterns before proceeding with implementation")
        
        actions.append("📚 Use provided educational content to understand why these patterns are problematic")
        
        # Add Claude CLI recommendation if available
        if self.claude_cli_enabled:
            actions.append("🧠 Consider using comprehensive or hybrid analysis mode for detailed insights")
        
        actions.append("✅ Apply prevention checklists for future work")
        
        return actions
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported anti-pattern types"""
        return self.pattern_detector.get_pattern_types()
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary for the detection engine"""
        return self.pattern_detector.get_validation_summary()
    
    def get_enhancement_status(self) -> Dict[str, Any]:
        """Get status of optional enhancements"""
        return {
            "external_claude_available": EXTERNAL_CLAUDE_AVAILABLE,
            "claude_cli_enabled": self.claude_cli_enabled,
            "enhancement_version": "1.0 - ExternalClaudeCli integration",
            "supported_modes": ["basic", "comprehensive", "hybrid"],
            "backward_compatible": True
        }
    
    def analyze_issue(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        focus_patterns: Optional[str] = "all",
        detail_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Backward compatibility method - delegates to analyze_issue_basic.
        
        This method preserves the exact interface from the original GitHubIssueAnalyzer
        for backward compatibility with existing tests and code.
        
        Args:
            issue_number: GitHub issue number to analyze
            repository: Repository in format "owner/repo" (optional)
            focus_patterns: Comma-separated list of patterns to focus on
            detail_level: Educational detail level (brief/standard/comprehensive)
            
        Returns:
            Pattern detection analysis (original format)
        """
        return self.analyze_issue_basic(
            issue_number=issue_number,
            repository=repository,
            focus_patterns=focus_patterns,
            detail_level=detail_level
        )


# Backward compatibility alias for existing tests
GitHubIssueAnalyzer = EnhancedGitHubIssueAnalyzer

# Initialize global analyzer instance
_enhanced_github_analyzer = None


def get_enhanced_github_analyzer(github_token: Optional[str] = None, enable_claude_cli: bool = True) -> EnhancedGitHubIssueAnalyzer:
    """Get or create enhanced GitHub analyzer instance"""
    global _enhanced_github_analyzer
    if _enhanced_github_analyzer is None:
        _enhanced_github_analyzer = EnhancedGitHubIssueAnalyzer(github_token, enable_claude_cli)
    return _enhanced_github_analyzer


def get_github_analyzer(github_token: Optional[str] = None) -> EnhancedGitHubIssueAnalyzer:
    """Get or create GitHub analyzer instance (backward compatibility)"""
    return get_enhanced_github_analyzer(github_token, enable_claude_cli=False)


async def analyze_issue(
    issue_number: int,
    repository: Optional[str] = None,
    analysis_mode: str = "hybrid",
    detail_level: str = "standard",
    post_comment: bool = False
) -> Dict[str, Any]:
    """
    Enhanced GitHub issue analysis with optional ExternalClaudeCli integration.
    
    This enhanced version provides multiple analysis modes:
    - "basic": Fast pattern detection only (backward compatible)
    - "comprehensive": Claude CLI powered sophisticated reasoning
    - "hybrid": Combined pattern detection + Claude CLI insights (recommended)
    
    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo" (optional, defaults to current repo)
        analysis_mode: Analysis mode - "basic", "comprehensive", or "hybrid" (default: "hybrid")
        detail_level: Educational detail level - "brief"/"standard"/"comprehensive" (default: "standard")
        post_comment: Whether to post analysis as GitHub comment (future enhancement)
        
    Returns:
        Comprehensive issue analysis with optional Claude CLI enhancement
        
    Example:
        # Fast pattern detection only (backward compatible)
        result = await analyze_issue(22, analysis_mode="basic")
        
        # Comprehensive Claude CLI analysis
        result = await analyze_issue(123, "owner/repo", "comprehensive")
        
        # Hybrid analysis (recommended) - combines both approaches
        result = await analyze_issue(456, analysis_mode="hybrid")
    """
    try:
        # Get enhanced analyzer
        analyzer = get_enhanced_github_analyzer()
        
        # Parse analysis mode
        mode = analysis_mode.lower()
        if mode not in ["basic", "comprehensive", "hybrid"]:
            logger.warning(f"Invalid analysis mode '{analysis_mode}', using 'hybrid'")
            mode = "hybrid"
        
        # Execute analysis based on mode
        if mode == "basic":
            logger.info(f"Running basic pattern detection analysis for issue #{issue_number}")
            result = analyzer.analyze_issue_basic(
                issue_number=issue_number,
                repository=repository,
                detail_level=detail_level
            )
        elif mode == "comprehensive":
            logger.info(f"Running comprehensive Claude CLI analysis for issue #{issue_number}")
            result = await analyzer.analyze_issue_comprehensive(
                issue_number=issue_number,
                repository=repository,
                detail_level=detail_level
            )
        else:  # hybrid
            logger.info(f"Running hybrid analysis for issue #{issue_number}")
            result = await analyzer.analyze_issue_hybrid(
                issue_number=issue_number,
                repository=repository,
                detail_level=detail_level
            )
        
        # Add enhancement metadata
        result["enhanced_analysis"] = {
            "analysis_mode": mode,
            "external_claude_available": EXTERNAL_CLAUDE_AVAILABLE,
            "claude_cli_enabled": analyzer.claude_cli_enabled,
            "enhancement_version": "1.0 - Issue #65 implementation",
            "backward_compatible": True
        }
        
        # Future enhancement: post_comment functionality
        if post_comment:
            logger.info("Comment posting not yet implemented - future enhancement")
            result["comment_posting"] = {
                "requested": True,
                "status": "not_implemented",
                "note": "Future enhancement - will integrate with vibe check framework"
            }
        
        return result
        
    except Exception as e:
        error_msg = f"Enhanced issue analysis failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": error_msg,
            "status": "enhanced_analysis_error",
            "issue_number": issue_number,
            "repository": repository,
            "analysis_mode": analysis_mode,
            "external_claude_available": EXTERNAL_CLAUDE_AVAILABLE,
            "fallback_recommendation": "Try basic analysis mode"
        }


# Backward compatibility function (preserves exact analyze_issue_nollm interface)
def analyze_issue_legacy(
    issue_number: int,
    repository: Optional[str] = None,
    analysis_mode: str = "quick",
    detail_level: str = "standard",
    post_comment: bool = False
) -> Dict[str, Any]:
    """
    Legacy analyze_issue function for backward compatibility.
    
    This function provides the exact same interface as the original analyze_issue_nollm
    function while using the enhanced analyzer underneath.
    
    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo"
        analysis_mode: Analysis mode - "quick" or "comprehensive"
        detail_level: Educational detail level
        post_comment: Whether to post analysis as GitHub comment
        
    Returns:
        Analysis results compatible with original analyze_issue_nollm
    """
    try:
        # Map legacy modes to enhanced modes
        enhanced_mode = "basic" if analysis_mode.lower() == "quick" else "hybrid"
        
        # Get enhanced analyzer with Claude CLI disabled for legacy mode
        analyzer = get_enhanced_github_analyzer(enable_claude_cli=False)
        
        # Run basic analysis for full backward compatibility
        result = analyzer.analyze_issue_basic(
            issue_number=issue_number,
            repository=repository,
            detail_level=detail_level
        )
        
        # Legacy vibe check integration (if post_comment is requested)
        if post_comment:
            try:
                from .legacy.vibe_check_framework import get_vibe_check_framework, VibeCheckMode
                framework = get_vibe_check_framework()
                detail_enum = DetailLevel(detail_level.lower()) if detail_level.lower() in ["brief", "standard", "comprehensive"] else DetailLevel.STANDARD
                mode = VibeCheckMode.COMPREHENSIVE if analysis_mode.lower() == "comprehensive" else VibeCheckMode.QUICK
                
                vibe_result = framework.check_issue_vibes(
                    issue_number=issue_number,
                    repository=repository,
                    mode=mode,
                    detail_level=detail_enum,
                    post_comment=post_comment
                )
                
                # Add vibe check results
                result["vibe_check"] = {
                    "overall_vibe": vibe_result.overall_vibe,
                    "vibe_level": vibe_result.vibe_level.value,
                    "friendly_summary": vibe_result.friendly_summary,
                    "coaching_recommendations": vibe_result.coaching_recommendations
                }
                
            except Exception as e:
                logger.warning(f"Vibe check integration failed: {e}")
                result["vibe_check_error"] = str(e)
        
        return result
        
    except Exception as e:
        error_msg = f"Legacy vibe check failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": error_msg,
            "status": "legacy_analysis_error",
            "issue_number": issue_number,
            "repository": repository,
            "friendly_error": "🚨 Oops! Something went wrong with the analysis. Try again with a simpler analysis mode."
        }