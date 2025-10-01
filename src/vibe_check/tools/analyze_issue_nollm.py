"""
Enhanced GitHub Issue Analysis MCP Tool

Implements FastMCP tool for comprehensive "vibe check" analysis of GitHub issues
using Claude-powered analytical reasoning and validated pattern detection.

Transforms from basic "anti-pattern detection" to friendly "vibe check" framework
that provides practical engineering guidance and coaching.

Issue #40 implementation: Claude-powered comprehensive vibe check framework.
"""

import logging
from typing import Dict, Any, Optional, List
from github import Github, GithubException
from github.Issue import Issue

from vibe_check.core.pattern_detector import PatternDetector, DetectionResult
from vibe_check.core.educational_content import DetailLevel
from vibe_check.core.vibe_config import get_vibe_config, vibe_message, vibe_error
from vibe_check.core.architectural_concept_detector import ArchitecturalConceptDetector, ConceptDetectionResult
from .legacy.vibe_check_framework import VibeCheckFramework, VibeCheckMode, get_vibe_check_framework
from vibe_check.utils.logging_framework import get_vibe_logger, create_migration_logger

# Configure logging - maintain backward compatibility
logger = logging.getLogger(__name__)
vibe_logger = get_vibe_logger("issue_analyzer")


class GitHubIssueAnalyzer:
    """
    GitHub Issue Analysis engine that integrates GitHub API with anti-pattern detection.
    
    Uses the validated Phase 1 core detection engine (87.5% accuracy) to analyze
    GitHub issues for systematic engineering anti-patterns.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub Issue Analyzer.
        
        Args:
            github_token: GitHub API token for authentication (optional for public repos)
        """
        self.github_client = Github(github_token) if github_token else Github()
        self.pattern_detector = PatternDetector()
        self.architectural_detector = ArchitecturalConceptDetector()
        self.vibe_logger = get_vibe_logger("issue_analyzer")
        
        # User-friendly initialization
        self.vibe_logger.progress("Initializing GitHub Issue Analyzer", "🤖")
        logger.info("GitHub Issue Analyzer initialized")
    
    def analyze_issue(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        focus_patterns: Optional[str] = "all",
        detail_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Analyze GitHub issue for anti-patterns using validated detection engine.
        
        Args:
            issue_number: GitHub issue number to analyze
            repository: Repository in format "owner/repo" (optional, uses current repo context)
            focus_patterns: Comma-separated list of patterns to focus on ("all" for all patterns)
            detail_level: Educational detail level (brief/standard/comprehensive)
            
        Returns:
            Comprehensive analysis with detected patterns and educational content
            
        Raises:
            ValueError: For invalid parameters
            GithubException: For GitHub API errors
        """
        # Use rich progress tracking for the entire analysis
        with self.vibe_logger.operation(f"vibe check for issue #{issue_number}", 5):
            try:
                # Step 1: Input validation
                self.vibe_logger.step("Validating input parameters")
                if issue_number <= 0:
                    raise ValueError("Issue number must be positive")
                
                # Parse detail level
                try:
                    detail_enum = DetailLevel(detail_level.lower())
                except ValueError:
                    detail_enum = DetailLevel.STANDARD
                    self.vibe_logger.warning(f"Invalid detail level '{detail_level}', using 'standard'")
                
                # Parse focus patterns
                focus_pattern_list = None
                if focus_patterns and focus_patterns.lower() != "all":
                    focus_pattern_list = [p.strip() for p in focus_patterns.split(",")]
                    # Validate pattern names
                    valid_patterns = self.pattern_detector.get_pattern_types()
                    invalid_patterns = [p for p in focus_pattern_list if p not in valid_patterns]
                    if invalid_patterns:
                        self.vibe_logger.warning(f"Invalid patterns ignored: {invalid_patterns}")
                        focus_pattern_list = [p for p in focus_pattern_list if p in valid_patterns]
                
                # Step 2: Fetch GitHub issue data
                self.vibe_logger.step("Fetching GitHub issue data")
                issue_data = self._fetch_issue_data(issue_number, repository)
                
                # Step 3: Run architectural concept detection
                self.vibe_logger.step("Detecting architectural concepts")
                content = issue_data["body"] or ""
                context = f"Title: {issue_data['title']}"
                
                architectural_concepts = self.architectural_detector.detect_concepts(
                    text=content,
                    context=context
                )
                
                # Step 4: Run pattern detection
                self.vibe_logger.step("Running pattern detection")
                detected_patterns = self.pattern_detector.analyze_text_for_patterns(
                    content=content,
                    context=context,
                    focus_patterns=focus_pattern_list,
                    detail_level=detail_enum
                )
                
                # Step 5: Generate analysis response
                self.vibe_logger.step("Generating analysis report")
                analysis_result = self._generate_analysis_response(
                    issue_data=issue_data,
                    detected_patterns=detected_patterns,
                    architectural_concepts=architectural_concepts,
                    detail_level=detail_enum
                )
                
                # Step 5: Finalize results
                self.vibe_logger.step("Finalizing results")
                
                # Display results summary
                self.vibe_logger.stats("Analysis Results", {
                    "patterns_detected": len(detected_patterns),
                    "issue_number": issue_number,
                    "detail_level": detail_level
                })
                
                if detected_patterns:
                    # Validate confidence values before comparison
                    valid_confidences = []
                    for p in detected_patterns:
                        if hasattr(p, 'confidence') and isinstance(p.confidence, (int, float)):
                            valid_confidences.append(max(0.0, min(1.0, float(p.confidence))))
                    
                    if valid_confidences:
                        max_confidence = max(valid_confidences)
                        if max_confidence >= 0.8:
                            vibe_emoji = "🚨"
                            vibe_text = "Bad Vibes"
                        elif max_confidence >= 0.6:
                            vibe_emoji = "⚠️"
                            vibe_text = "Mixed Vibes"
                        else:
                            vibe_emoji = "💡"
                            vibe_text = "Minor Concerns"
                    else:
                        vibe_emoji = "❓"
                        vibe_text = "Unknown Confidence"
                else:
                    vibe_emoji = "✅"
                    vibe_text = "Good Vibes"
                
                self.vibe_logger.success(f"Vibe check complete! Overall vibe: {vibe_emoji} {vibe_text}")
                logger.info(f"Analysis completed for issue #{issue_number}: {len(detected_patterns)} patterns detected")
                return analysis_result
            
            except Exception as e:
                self.vibe_logger.error(f"Analysis failed: {str(e)}")
                logger.error(f"Error analyzing issue #{issue_number}: {e}")
                raise
    
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
        # Default repository handling (could be enhanced with config)
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
            
            self.vibe_logger.info(f"Retrieved issue #{issue_number}: '{issue.title}'", "📄")
            logger.info(f"Fetched issue #{issue_number} from {repository}")
            return issue_data
            
        except GithubException as e:
            if e.status == 404:
                raise GithubException(404, {"message": f"Issue #{issue_number} not found in {repository}"})
            raise
    
    def _generate_analysis_response(
        self,
        issue_data: Dict[str, Any],
        detected_patterns: List[DetectionResult],
        architectural_concepts: ConceptDetectionResult,
        detail_level: DetailLevel
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis response with educational content and architectural concepts.
        
        Args:
            issue_data: GitHub issue information
            detected_patterns: List of detected anti-patterns
            architectural_concepts: Detected architectural concepts
            detail_level: Educational detail level
            
        Returns:
            Comprehensive analysis response
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
        
        # Generate recommended actions (enhanced with architectural context)
        recommended_actions = self._generate_recommended_actions(
            detected_patterns, 
            detail_level,
            architectural_concepts
        )
        
        # Format architectural concepts for response
        architectural_analysis = self._format_architectural_concepts(architectural_concepts, issue_data["repository"])
        
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
            "status": "analysis_complete",
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
            
            # Architectural concept analysis
            "architectural_concepts": architectural_analysis,
            
            # Educational and actionable content
            "recommended_actions": recommended_actions,
            
            # Analysis metadata
            "analysis_metadata": {
                "core_engine_validation": "87.5% accuracy, 0% false positives",
                "detail_level": detail_level.value,
                "patterns_analyzed": self.pattern_detector.get_pattern_types(),
                "detection_method": "Phase 1 validated algorithms"
            }
        }
        
        return analysis_response
    
    def _format_architectural_concepts(
        self, 
        concepts: ConceptDetectionResult, 
        repository: str
    ) -> Dict[str, Any]:
        """Format architectural concepts for response"""
        if not concepts.detected_concepts:
            return {
                "detected": False,
                "concepts": [],
                "search_guidance": [],
                "analysis_mode": "general"
            }
        
        # Sort concepts by confidence
        sorted_concepts = sorted(
            concepts.detected_concepts,
            key=lambda x: x.confidence,
            reverse=True
        )
        
        formatted_concepts = []
        for concept in sorted_concepts:
            guidance = self.architectural_detector.get_file_discovery_guidance(concept, repository)
            
            formatted_concepts.append({
                "name": concept.concept_name,
                "confidence": round(concept.confidence, 3),
                "keywords_found": concept.keywords_found,
                "file_discovery": {
                    "patterns": concept.file_patterns,
                    "common_files": concept.common_files,
                    "github_queries": guidance["github_search_queries"][:3]  # Limit to top 3
                },
                "recommendations": self.architectural_detector._get_concept_specific_recommendations(concept)
            })
        
        # Generate analysis context
        analysis_context = self.architectural_detector.generate_analysis_context(concepts)
        
        return {
            "detected": True,
            "primary_concept": analysis_context.get("primary_concept"),
            "concepts": formatted_concepts,
            "search_guidance": {
                "github_queries": concepts.github_search_queries[:5],  # Top 5 queries
                "file_patterns": analysis_context.get("search_guidance", {}).get("file_patterns", []),
                "common_files": analysis_context.get("search_guidance", {}).get("common_files", [])
            },
            "analysis_mode": analysis_context.get("analysis_mode", "general"),
            "architectural_recommendations": analysis_context.get("recommendations", [])
        }
    
    def _generate_recommended_actions(
        self,
        detected_patterns: List[DetectionResult],
        detail_level: DetailLevel,
        architectural_concepts: Optional[ConceptDetectionResult] = None
    ) -> List[str]:
        """Generate prioritized recommended actions based on detected patterns and architectural concepts"""
        
        if not detected_patterns:
            vibe_config = get_vibe_config()
            base_actions = [
                vibe_message('no_patterns'),
                "Keep those good vibes rolling with solid engineering",
                "Consider using this vibe check for other issues or code reviews"
            ]
            
            # Add architectural guidance even if no patterns detected
            if architectural_concepts and architectural_concepts.detected_concepts:
                primary_concept = architectural_concepts.detected_concepts[0]
                base_actions.insert(1, 
                    f"🏗️ Detected {primary_concept.concept_name} architectural focus - "
                    f"consider checking {', '.join(primary_concept.common_files[:2])} files"
                )
            
            return base_actions
        
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
        
        # Add architectural guidance if concepts detected
        if architectural_concepts and architectural_concepts.detected_concepts:
            primary_concept = architectural_concepts.detected_concepts[0]
            actions.append(
                f"🏗️ Focus on {primary_concept.concept_name} architecture - "
                f"search for files matching: {', '.join(primary_concept.file_patterns[:2])}"
            )
        
        # Add general recommendations
        if len(detected_patterns) > 1:
            actions.append("🔍 Check out all these vibe patterns before diving in")
        
        actions.append("📖 Dig into the learning stuff to see why these patterns kill the vibe")
        actions.append("✨ Use these vibe-check checklists to keep future work smooth")
        
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


# Initialize global analyzer instance
_github_analyzer = None


def get_github_analyzer(github_token: Optional[str] = None) -> GitHubIssueAnalyzer:
    """Get or create GitHub analyzer instance"""
    global _github_analyzer
    if _github_analyzer is None:
        _github_analyzer = GitHubIssueAnalyzer(github_token)
    return _github_analyzer


def analyze_issue(
    issue_number: int,
    repository: Optional[str] = None,
    analysis_mode: str = "quick",
    detail_level: str = "standard",
    post_comment: bool = False
) -> Dict[str, Any]:
    """
    Enhanced FastMCP tool: Comprehensive vibe check for GitHub issues.
    
    Transforms from basic anti-pattern detection to Claude-powered friendly vibe check
    that provides practical engineering guidance and coaching.
    
    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo" (optional, defaults to current repo)
        analysis_mode: Analysis mode - "quick" for fast feedback or "comprehensive" for detailed analysis
        detail_level: Educational detail level - "brief"/"standard"/"comprehensive" (default: "standard")
        post_comment: Whether to post analysis as GitHub comment (auto-enabled for comprehensive mode)
        
    Returns:
        Comprehensive vibe check with friendly guidance, coaching recommendations, and technical analysis
        
    Example:
        # Quick vibe check for development workflow  
        result = analyze_issue(22, analysis_mode="quick")
        
        # Comprehensive analysis with GitHub comment
        result = analyze_issue(123, "owner/repo", "comprehensive", "comprehensive", True)
    """
    try:
        # Initialize VibeLogger for this analysis
        analysis_logger = get_vibe_logger(f"vibe_check_issue_{issue_number}")
        analysis_logger.progress(f"Starting vibe check for issue #{issue_number}", "🤖")
        
        # Parse analysis mode
        mode = VibeCheckMode.COMPREHENSIVE if analysis_mode.lower() == "comprehensive" else VibeCheckMode.QUICK
        
        # Parse detail level
        try:
            detail_enum = DetailLevel(detail_level.lower())
        except ValueError:
            detail_enum = DetailLevel.STANDARD
            analysis_logger.warning(f"Invalid detail level '{detail_level}', using 'standard'")
        
        # Auto-enable comment posting for comprehensive mode (unless explicitly disabled)
        if mode == VibeCheckMode.COMPREHENSIVE and post_comment is None:
            post_comment = True
        
        analysis_logger.info(f"Analysis mode: {mode.value}, Detail level: {detail_enum.value}", "⚙️")
        
        # Get vibe check framework
        framework = get_vibe_check_framework()
        
        # Run comprehensive vibe check
        with analysis_logger.operation(f"vibe check analysis ({mode.value} mode)", 3):
            analysis_logger.step("Initializing vibe check framework")
            
            analysis_logger.step("Running comprehensive analysis")
            vibe_result = framework.check_issue_vibes(
                issue_number=issue_number,
                repository=repository,
                mode=mode,
                detail_level=detail_enum,
                post_comment=post_comment
            )
            
            analysis_logger.step("Preparing response")
        
        # Convert to MCP tool response format
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        result = {
            "status": "vibe_check_complete",
            "analysis_timestamp": timestamp,
            
            # Friendly vibe check results
            "vibe_check": {
                "overall_vibe": vibe_result.overall_vibe,
                "vibe_level": vibe_result.vibe_level.value,
                "friendly_summary": vibe_result.friendly_summary,
                "coaching_recommendations": vibe_result.coaching_recommendations
            },
            
            # Issue information  
            "issue_info": {
                "number": issue_number,
                "repository": repository or "kesslerio/vibe-check-mcp",
                "analysis_mode": mode.value,
                "detail_level": detail_enum.value,
                "comment_posted": post_comment
            },
            
            # Technical analysis (for transparency)
            "technical_analysis": vibe_result.technical_analysis,
            
            # Enhanced capabilities
            "enhanced_features": {
                "claude_reasoning": vibe_result.claude_reasoning is not None,
                "clear_thought_analysis": vibe_result.clear_thought_analysis is not None,
                "comprehensive_validation": mode == VibeCheckMode.COMPREHENSIVE,
                "educational_coaching": True,
                "friendly_language": True
            },
            
            # Analysis metadata
            "analysis_metadata": {
                "framework_version": "2.0 - Claude-powered vibe check",
                "core_engine_validation": "87.5% accuracy, 0% false positives",
                "analysis_type": "comprehensive_vibe_check",
                "language_style": "friendly_coaching"
            }
        }
        
        # Display final results
        analysis_logger.stats("Vibe Check Results", {
            "overall_vibe": vibe_result.overall_vibe,
            "vibe_level": vibe_result.vibe_level.value,
            "mode": mode.value
        })
        
        analysis_logger.success(f"Vibe check complete! Overall: {vibe_result.overall_vibe}")
        
        # Sanitize any GitHub API URLs to frontend URLs
        from .shared.github_helpers import sanitize_github_urls_in_response
        return sanitize_github_urls_in_response(result)
        
    except Exception as e:
        error_msg = f"Vibe check failed: {str(e)}"
        vibe_logger.error(error_msg, exception=e)
        logger.error(error_msg)
        return {
            "error": error_msg,
            "status": "vibe_check_error",
            "issue_number": issue_number,
            "repository": repository,
            "friendly_error": "🚨 Oops! Something went wrong with the vibe check. Try again with a simpler analysis mode."
        }