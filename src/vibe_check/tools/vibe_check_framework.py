"""
Comprehensive Vibe Check Framework

Transforms analyze_github_issue from basic keyword detection to Claude-powered 
comprehensive "vibe check" framework that provides practical engineering guidance
using sophisticated analytical reasoning.

This implements the architecture described in Issue #40 to achieve parity with
the bash script's Claude-powered analysis engine while transforming technical
"anti-pattern" language into friendly "vibe check" coaching.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import subprocess
import json
import tempfile
import os
from pathlib import Path

from github import Github, GithubException
from github.Issue import Issue

from ..core.pattern_detector import PatternDetector, DetectionResult
from ..core.educational_content import DetailLevel
from ..core.vibe_coaching import get_vibe_coaching_framework, LearningLevel, CoachingTone

logger = logging.getLogger(__name__)


class VibeCheckMode(Enum):
    """Vibe check analysis modes"""
    QUICK = "quick"
    COMPREHENSIVE = "comprehensive"


class VibeLevel(Enum):
    """Vibe assessment levels"""
    GOOD_VIBES = "good_vibes"      # ✅ Ready to go
    NEEDS_RESEARCH = "needs_research"  # 🔍 Do some homework first  
    NEEDS_POC = "needs_poc"        # 🧪 Show basic functionality
    COMPLEX_VIBES = "complex_vibes"    # ⚖️ Justify the complexity
    BAD_VIBES = "bad_vibes"        # 🚨 Infrastructure without implementation


@dataclass
class VibeCheckResult:
    """Result of comprehensive vibe check analysis"""
    vibe_level: VibeLevel
    overall_vibe: str
    friendly_summary: str
    coaching_recommendations: List[str]
    technical_analysis: Dict[str, Any]
    claude_reasoning: Optional[str] = None
    clear_thought_analysis: Optional[Dict[str, Any]] = None


class VibeCheckFramework:
    """
    Claude-powered comprehensive vibe check framework for GitHub issues.
    
    Combines sophisticated prompt-based reasoning with validated pattern detection
    to provide friendly, practical engineering guidance instead of technical jargon.
    
    Core Features:
    - Claude-powered analytical reasoning (ported from review-issue.sh)
    - Clear-Thought systematic analysis integration  
    - Friendly "vibe check" language instead of "anti-pattern detection"
    - Comprehensive issue validation framework
    - Educational coaching recommendations
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize the vibe check framework"""
        self.github_client = Github(github_token) if github_token else Github()
        self.pattern_detector = PatternDetector()
        self.claude_available = self._check_claude_availability()
        logger.info("Vibe Check Framework initialized")
    
    def check_issue_vibes(
        self,
        issue_number: int,
        repository: Optional[str] = None,
        mode: VibeCheckMode = VibeCheckMode.QUICK,
        detail_level: DetailLevel = DetailLevel.STANDARD,
        post_comment: bool = False
    ) -> VibeCheckResult:
        """
        Perform comprehensive vibe check on GitHub issue.
        
        Args:
            issue_number: GitHub issue number
            repository: Repository in format "owner/repo"
            mode: Analysis mode (quick/comprehensive)
            detail_level: Educational detail level
            post_comment: Whether to post analysis as GitHub comment
            
        Returns:
            VibeCheckResult with friendly guidance and technical analysis
        """
        try:
            # Fetch issue data
            issue_data = self._fetch_issue_data(issue_number, repository)
            
            # Phase 1: Basic pattern detection (validated engine)
            basic_patterns = self._detect_basic_patterns(issue_data, detail_level)
            
            # Phase 2: Claude-powered reasoning (if available and comprehensive mode)
            claude_analysis = None
            if mode == VibeCheckMode.COMPREHENSIVE and self.claude_available:
                claude_analysis = self._run_claude_analysis(issue_data, basic_patterns)
            
            # Phase 3: Clear-Thought systematic analysis (for complex issues)
            clear_thought_analysis = None
            if self._needs_systematic_analysis(issue_data, basic_patterns):
                clear_thought_analysis = self._run_clear_thought_analysis(issue_data, basic_patterns)
            
            # Phase 4: Generate friendly vibe check result
            vibe_result = self._generate_vibe_check_result(
                issue_data=issue_data,
                basic_patterns=basic_patterns,
                claude_analysis=claude_analysis,
                clear_thought_analysis=clear_thought_analysis,
                detail_level=detail_level
            )
            
            # Phase 5: Post GitHub comment if requested
            if post_comment and mode == VibeCheckMode.COMPREHENSIVE:
                self._post_github_comment(issue_number, repository, vibe_result)
            
            return vibe_result
            
        except Exception as e:
            logger.error(f"Vibe check failed for issue #{issue_number}: {str(e)}")
            return VibeCheckResult(
                vibe_level=VibeLevel.BAD_VIBES,
                overall_vibe="🚨 Analysis Error",
                friendly_summary=f"Oops! Something went wrong analyzing this issue: {str(e)}",
                coaching_recommendations=["Try again with a simpler analysis mode"],
                technical_analysis={"error": str(e)}
            )
    
    def _fetch_issue_data(self, issue_number: int, repository: Optional[str]) -> Dict[str, Any]:
        """Fetch GitHub issue data (same as original implementation)"""
        if repository is None:
            repository = "kesslerio/vibe-check-mcp"
        
        if "/" not in repository:
            raise ValueError("Repository must be in format 'owner/repo'")
        
        try:
            repo = self.github_client.get_repo(repository)
            issue: Issue = repo.get_issue(issue_number)
            
            return {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body or "",
                "author": issue.user.login,
                "created_at": issue.created_at.isoformat(),
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "url": issue.html_url,
                "repository": repository
            }
            
        except GithubException as e:
            if e.status == 404:
                raise GithubException(404, {"message": f"Issue #{issue_number} not found in {repository}"})
            raise
    
    def _detect_basic_patterns(self, issue_data: Dict[str, Any], detail_level: DetailLevel) -> List[DetectionResult]:
        """Run validated pattern detection engine"""
        content = issue_data["body"]
        context = f"Title: {issue_data['title']}"
        
        return self.pattern_detector.analyze_text_for_patterns(
            content=content,
            context=context,
            focus_patterns=None,
            detail_level=detail_level
        )
    
    def _check_claude_availability(self) -> bool:
        """Check if Claude CLI is available for sophisticated analysis"""
        try:
            result = subprocess.run(['claude', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _run_claude_analysis(self, issue_data: Dict[str, Any], basic_patterns: List[DetectionResult]) -> Optional[str]:
        """
        Run Claude-powered sophisticated analysis using prompts ported from review-issue.sh
        """
        try:
            # Create sophisticated analysis prompt (ported from bash script)
            prompt = self._create_sophisticated_vibe_prompt(issue_data, basic_patterns)
            
            # Write prompt to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            try:
                # Run Claude analysis using stdin approach (like working script)
                # CRITICAL: Use content as argument, not file path, to avoid hanging
                result = subprocess.run(
                    ['claude', '--dangerously-skip-permissions', '-p', prompt],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                else:
                    logger.warning(f"Claude analysis failed: {result.stderr}")
                    return None
                    
            finally:
                # Cleanup temporary file
                try:
                    os.unlink(prompt_file)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"Claude analysis error: {str(e)}")
            return None
    
    def _create_sophisticated_vibe_prompt(self, issue_data: Dict[str, Any], basic_patterns: List[DetectionResult]) -> str:
        """
        Create sophisticated vibe check prompt based on review-issue.sh framework
        but with friendly "vibe check" language instead of technical anti-pattern terms.
        """
        # Detect integration risks
        body_text = issue_data["body"].lower()
        third_party_services = self._detect_third_party_services(body_text)
        complexity_indicators = self._detect_complexity_indicators(body_text)
        infrastructure_keywords = self._detect_infrastructure_keywords(body_text)
        
        # Create pattern detection summary
        pattern_summary = "None detected"
        if basic_patterns:
            pattern_names = [p.pattern_type for p in basic_patterns if p.detected]
            if pattern_names:
                pattern_summary = ", ".join(pattern_names)
        
        prompt = f"""You are a friendly engineering coach helping developers with a "vibe check" on their GitHub issue. Your goal is to provide helpful, non-intimidating guidance that prevents common engineering pitfalls while encouraging learning and best practices.

## 🎯 Issue Vibe Check Request

**Issue Information:**
- **Title:** {issue_data['title']}
- **Author:** {issue_data['author']}
- **Repository:** {issue_data['repository']}
- **Labels:** {', '.join(issue_data['labels']) if issue_data['labels'] else 'None'}

**Issue Content:**
{issue_data['body']}

## 🧠 Pattern Detection Results
- **Basic Patterns Detected:** {pattern_summary}
- **Third-Party Services Mentioned:** {', '.join(third_party_services) if third_party_services else 'None'}
- **Infrastructure Keywords:** {', '.join(infrastructure_keywords) if infrastructure_keywords else 'None'}  
- **Complexity Indicators:** {', '.join(complexity_indicators) if complexity_indicators else 'None'}

## 🔍 Vibe Check Framework

Please analyze this issue using friendly, coaching language and provide guidance in this exact format:

### 🎯 **Overall Vibe Assessment**
[Provide a one-sentence friendly assessment of the overall approach]

### 🚨 **Integration Risk Check** 
{self._generate_integration_risk_prompt(third_party_services)}

### 🔍 **Research Phase Coaching**
- Have we done our homework on existing solutions?
- Are we building on top of what's already available?
- Do we understand the basic APIs before building complex architecture?

### ⚖️ **Complexity Appropriateness Check**
{self._generate_complexity_prompt(complexity_indicators)}

### 🧪 **Success Criteria Vibe Check**
- Are the acceptance criteria focused on real user value?
- Can we tell when we're actually done (no fake success)?
- Are we measuring the right things?

### 💡 **Friendly Recommendations**

**If Good Vibes (✅):**
- "Looks great! This has a solid plan and appropriate scope."
- "The research phase is well thought out."
- "Clear success criteria - we'll know when this works."

**If Needs Research (🔍):**
- "Let's do some homework first - what solutions already exist?"
- "Have we checked the official docs and tutorials?"
- "A quick POC might clarify what we actually need."

**If Needs POC (🧪):**
- "Show us the basic functionality first before building complex stuff."
- "Let's prove the API works with real data."
- "Start simple, then add complexity only if needed."

**If Complex Vibes (⚖️):**
- "This feels pretty complex - have we tried the simple approach first?"
- "Can we break this down into smaller, more manageable pieces?"
- "What's the simplest thing that could possibly work?"

**If Bad Vibes (🚨):**
- "Hold up! This looks like building infrastructure without proving basic functionality."
- "Are we solving the right problem or just the symptoms?"
- "Let's step back and understand the root cause first."

### 🎓 **Learning Opportunities**
[Provide 2-3 specific learning suggestions based on the patterns detected]

### 🎯 **Next Steps Recommendation**
[Choose one: GOOD VIBES / NEEDS RESEARCH / NEEDS POC / COMPLEX VIBES / BAD VIBES]

Remember: Use encouraging, friendly language that helps developers learn rather than technical jargon that might intimidate. Focus on practical guidance and prevention of common pitfalls."""

        return prompt
    
    def _detect_third_party_services(self, text: str) -> List[str]:
        """Detect mentions of third-party services"""
        services = []
        service_keywords = [
            "cognee", "openai", "anthropic", "postgres", "redis", "docker",
            "api", "sdk", "integration", "server", "client", "http", "rest", "graphql"
        ]
        
        for keyword in service_keywords:
            if keyword in text:
                services.append(keyword)
        
        return services
    
    def _detect_infrastructure_keywords(self, text: str) -> List[str]:
        """Detect infrastructure-related keywords"""
        keywords = []
        infra_terms = [
            "architecture", "infrastructure", "server", "database", "build", 
            "deploy", "docker", "compose", "setup", "config"
        ]
        
        for term in infra_terms:
            if term in text:
                keywords.append(term)
        
        return keywords
    
    def _detect_complexity_indicators(self, text: str) -> List[str]:
        """Detect complexity indicators"""
        indicators = []
        complexity_terms = [
            "complex", "sophisticated", "enterprise", "advanced", "framework",
            "system", "pipeline", "orchestrat"
        ]
        
        for term in complexity_terms:
            if term in text:
                indicators.append(term)
        
        return indicators
    
    def _generate_integration_risk_prompt(self, third_party_services: List[str]) -> str:
        """Generate integration risk assessment prompt"""
        if not third_party_services:
            return """✅ **No obvious third-party integration detected**
- Standard development process applies
- Continue with regular issue validation"""
        
        return f"""⚠️ **Third-party services detected:** {', '.join(third_party_services)}

**Key Questions:**
- Are we using the basic APIs before building custom infrastructure?
- Do we have a working POC that proves basic functionality?
- Are we avoiding the "infrastructure-without-implementation" trap?
- Have we checked if simpler standard approaches work first?

**Red Flags to Check:**
- Custom HTTP servers when SDKs exist
- Complex architecture before basic API usage
- Elaborate planning without demonstrated API calls"""
    
    def _generate_complexity_prompt(self, complexity_indicators: List[str]) -> str:
        """Generate complexity appropriateness prompt"""
        if not complexity_indicators:
            return """✅ **No obvious over-engineering indicators**
- Proposed solution appears appropriately scoped
- Continue with standard complexity validation"""
        
        return f"""⚠️ **Complexity indicators detected:** {', '.join(complexity_indicators)}

**Complexity Check Questions:**
- Is this complexity justified over simple standard approaches?
- Have we tried the simple solution first and found it insufficient?
- Are we building something proportional to the business value?
- Will this create maintainable, understandable code?"""
    
    def _needs_systematic_analysis(self, issue_data: Dict[str, Any], basic_patterns: List[DetectionResult]) -> bool:
        """Determine if issue needs Clear-Thought systematic analysis"""
        # Complex issues with multiple patterns
        if len(basic_patterns) > 2:
            return True
        
        # High-confidence problematic patterns
        high_confidence_patterns = [p for p in basic_patterns if p.confidence > 0.8]
        if high_confidence_patterns:
            return True
        
        # Issues with complexity indicators
        body_text = issue_data["body"].lower()
        complexity_indicators = self._detect_complexity_indicators(body_text)
        if len(complexity_indicators) > 2:
            return True
        
        return False
    
    def _run_clear_thought_analysis(self, issue_data: Dict[str, Any], basic_patterns: List[DetectionResult]) -> Optional[Dict[str, Any]]:
        """
        Recommend Clear-Thought MCP tools for systematic analysis.
        
        Since MCP servers cannot directly call other MCP tools, this function
        analyzes the issue and recommends specific Clear-Thought tools that
        the MCP client (Claude Code) should call for enhanced analysis.
        
        This implements client-side orchestration pattern for MCP tool integration.
        """
        try:
            recommended_tools = []
            analysis_reasoning = []
            
            # Analyze issue complexity and recommend appropriate mental models
            if self._needs_first_principles_analysis(issue_data, basic_patterns):
                recommended_tools.append({
                    "tool": "mcp__clear-thought-server__mentalmodel",
                    "args": {
                        "modelName": "First Principles",
                        "problem": f"Engineering Issue Analysis: {issue_data['title']}\n\nDescription: {issue_data['body'][:300]}..."
                    },
                    "reasoning": "Complex patterns detected - fundamental analysis needed to avoid over-engineering",
                    "when_to_use": "Before implementation to question assumptions and complexity"
                })
                analysis_reasoning.append("First Principles analysis recommended for complexity validation")
            
            # Recommend decision framework for service selection
            if self._needs_decision_framework(issue_data, basic_patterns):
                recommended_tools.append({
                    "tool": "mcp__clear-thought-server__decisionframework",
                    "args": {
                        "decisionStatement": "Third-Party Integration Approach Selection",
                        "options": [
                            "API-first: Start with basic SDK usage and real data",
                            "Custom Implementation: Build infrastructure and abstractions",
                            "Research Phase: Study existing solutions before implementation"
                        ],
                        "analysisType": "Engineering Decision"
                    },
                    "reasoning": "Multiple implementation approaches available - systematic evaluation needed",
                    "when_to_use": "When choosing between different technical approaches"
                })
                analysis_reasoning.append("Decision framework recommended for systematic approach selection")
            
            # Recommend programming paradigm analysis for architecture decisions
            if self._needs_programming_paradigm_analysis(issue_data, basic_patterns):
                recommended_tools.append({
                    "tool": "mcp__clear-thought-server__programmingparadigm",
                    "args": {
                        "paradigmName": "API Integration Pattern",
                        "problem": f"Integration challenge: {issue_data['title']}"
                    },
                    "reasoning": "Integration patterns need systematic architectural analysis",
                    "when_to_use": "For designing clean, maintainable integration architecture"
                })
                analysis_reasoning.append("Programming paradigm analysis recommended for integration architecture")
            
            # Recommend sequential thinking for complex multi-step issues
            if self._needs_sequential_thinking(issue_data, basic_patterns):
                recommended_tools.append({
                    "tool": "mcp__clear-thought-server__sequentialthinking",
                    "args": {
                        "thought": "Breaking down complex issue into systematic validation steps",
                        "thoughtNumber": 1,
                        "totalThoughts": 5,
                        "nextThoughtNeeded": True
                    },
                    "reasoning": "Multi-step issue requires systematic step-by-step analysis",
                    "when_to_use": "For complex issues with multiple interconnected components"
                })
                analysis_reasoning.append("Sequential thinking recommended for systematic breakdown")
            
            # Return recommendations if any tools are suggested
            if recommended_tools:
                return {
                    "analysis_type": "clear_thought_recommendations",
                    "integration_pattern": "client_orchestrated",
                    "recommended_tools": recommended_tools,
                    "analysis_reasoning": analysis_reasoning,
                    "usage_instructions": [
                        "Run the recommended Clear-Thought tools using Claude Code MCP integration",
                        "Combine results with vibe check analysis for comprehensive guidance",
                        "Apply systematic thinking to prevent engineering anti-patterns"
                    ],
                    "benefits": [
                        "Systematic analysis prevents cognitive biases",
                        "Mental models provide structured thinking frameworks",
                        "Decision frameworks ensure comprehensive option evaluation"
                    ]
                }
            else:
                return {
                    "analysis_type": "clear_thought_not_needed",
                    "reasoning": "Issue appears straightforward - basic vibe check is sufficient"
                }
                
        except Exception as e:
            logger.error(f"Clear-Thought analysis recommendation failed: {str(e)}")
            return {
                "analysis_type": "clear_thought_error",
                "error": str(e),
                "fallback": "Use basic vibe check analysis"
            }
    
    def _needs_first_principles_analysis(self, issue_data: Dict[str, Any], basic_patterns: List[DetectionResult]) -> bool:
        """Determine if First Principles mental model analysis would be helpful"""
        # Complex infrastructure patterns
        infrastructure_patterns = [p for p in basic_patterns if "infrastructure" in p.pattern_type.lower()]
        if infrastructure_patterns:
            return True
        
        # High complexity indicators
        body_text = issue_data["body"].lower()
        complexity_indicators = self._detect_complexity_indicators(body_text)
        if len(complexity_indicators) > 2:
            return True
        
        # Multiple third-party services mentioned
        third_party_services = self._detect_third_party_services(body_text)
        if len(third_party_services) > 2:
            return True
        
        return False
    
    def _needs_decision_framework(self, issue_data: Dict[str, Any], basic_patterns: List[DetectionResult]) -> bool:
        """Determine if decision framework analysis would be helpful"""
        body_text = issue_data["body"].lower()
        
        # Multiple implementation options mentioned
        option_keywords = ["option", "approach", "method", "way", "solution", "alternative"]
        option_mentions = sum(1 for keyword in option_keywords if keyword in body_text)
        if option_mentions > 2:
            return True
        
        # Third-party integration decisions
        third_party_services = self._detect_third_party_services(body_text)
        if third_party_services:
            return True
        
        # Architecture decision indicators
        architecture_keywords = ["architecture", "design", "pattern", "structure"]
        if any(keyword in body_text for keyword in architecture_keywords):
            return True
        
        return False
    
    def _needs_programming_paradigm_analysis(self, issue_data: Dict[str, Any], basic_patterns: List[DetectionResult]) -> bool:
        """Determine if programming paradigm analysis would be helpful"""
        body_text = issue_data["body"].lower()
        
        # Integration architecture patterns
        integration_keywords = ["integration", "api", "sdk", "client", "server"]
        if any(keyword in body_text for keyword in integration_keywords):
            return True
        
        # Code organization patterns
        organization_keywords = ["module", "class", "function", "component", "service"]
        organization_mentions = sum(1 for keyword in organization_keywords if keyword in body_text)
        if organization_mentions > 1:
            return True
        
        return False
    
    def _needs_sequential_thinking(self, issue_data: Dict[str, Any], basic_patterns: List[DetectionResult]) -> bool:
        """Determine if sequential thinking analysis would be helpful"""
        # Multiple detected patterns suggest complex issue
        if len(basic_patterns) > 2:
            return True
        
        # Multi-step implementation indicators
        body_text = issue_data["body"].lower()
        step_keywords = ["step", "phase", "stage", "first", "then", "next", "finally"]
        step_mentions = sum(1 for keyword in step_keywords if keyword in body_text)
        if step_mentions > 3:
            return True
        
        # Acceptance criteria with multiple items
        if "acceptance criteria" in body_text or "- [ ]" in issue_data["body"]:
            criteria_count = issue_data["body"].count("- [ ]")
            if criteria_count > 4:
                return True
        
        return False
    
    def _generate_vibe_check_result(
        self,
        issue_data: Dict[str, Any],
        basic_patterns: List[DetectionResult],
        claude_analysis: Optional[str],
        clear_thought_analysis: Optional[Dict[str, Any]],
        detail_level: DetailLevel
    ) -> VibeCheckResult:
        """Generate final friendly vibe check result"""
        
        # Determine overall vibe level based on analysis
        vibe_level = self._determine_vibe_level(issue_data, basic_patterns, claude_analysis)
        
        # Generate friendly summary
        friendly_summary = self._generate_friendly_summary(vibe_level, basic_patterns, issue_data)
        
        # Generate coaching recommendations
        coaching_recommendations = self._generate_coaching_recommendations(
            vibe_level, basic_patterns, claude_analysis, clear_thought_analysis
        )
        
        # Generate overall vibe assessment
        overall_vibe = self._generate_overall_vibe(vibe_level)
        
        # Compile technical analysis for transparency
        technical_analysis = {
            "detected_patterns": [
                {
                    "type": p.pattern_type,
                    "confidence": p.confidence,
                    "detected": p.detected,
                    "evidence": p.evidence
                }
                for p in basic_patterns
            ],
            "integration_analysis": {
                "third_party_services": self._detect_third_party_services(issue_data["body"].lower()),
                "infrastructure_keywords": self._detect_infrastructure_keywords(issue_data["body"].lower()),
                "complexity_indicators": self._detect_complexity_indicators(issue_data["body"].lower())
            },
            "analysis_metadata": {
                "claude_analysis_available": claude_analysis is not None,
                "clear_thought_analysis_available": clear_thought_analysis is not None,
                "detail_level": detail_level.value
            }
        }
        
        return VibeCheckResult(
            vibe_level=vibe_level,
            overall_vibe=overall_vibe,
            friendly_summary=friendly_summary,
            coaching_recommendations=coaching_recommendations,
            technical_analysis=technical_analysis,
            claude_reasoning=claude_analysis,
            clear_thought_analysis=clear_thought_analysis
        )
    
    def _determine_vibe_level(
        self,
        issue_data: Dict[str, Any],
        basic_patterns: List[DetectionResult],
        claude_analysis: Optional[str]
    ) -> VibeLevel:
        """Determine the overall vibe level based on analysis results"""
        
        # Check for high-confidence bad patterns
        high_confidence_bad = [p for p in basic_patterns 
                              if p.detected and p.confidence > 0.8 
                              and "infrastructure_without_implementation" in p.pattern_type]
        
        if high_confidence_bad:
            return VibeLevel.BAD_VIBES
        
        # Check for third-party integration without API evidence
        body_text = issue_data["body"].lower()
        third_party_services = self._detect_third_party_services(body_text)
        
        if third_party_services and not ("api" in body_text or "poc" in body_text or "example" in body_text):
            return VibeLevel.NEEDS_POC
        
        # Check for complexity without justification
        complexity_indicators = self._detect_complexity_indicators(body_text)
        if len(complexity_indicators) > 2:
            return VibeLevel.COMPLEX_VIBES
        
        # Check for missing research phase
        if third_party_services and not ("documentation" in body_text or "research" in body_text):
            return VibeLevel.NEEDS_RESEARCH
        
        # Default to good vibes if no major issues
        return VibeLevel.GOOD_VIBES
    
    def _generate_friendly_summary(
        self,
        vibe_level: VibeLevel,
        basic_patterns: List[DetectionResult],
        issue_data: Dict[str, Any]
    ) -> str:
        """Generate friendly, encouraging summary message"""
        
        summaries = {
            VibeLevel.GOOD_VIBES: "✅ This looks like a solid plan! The approach seems well thought out and appropriately scoped.",
            
            VibeLevel.NEEDS_RESEARCH: "🔍 Let's do some homework first! This would benefit from researching existing solutions and checking official documentation before diving in.",
            
            VibeLevel.NEEDS_POC: "🧪 Show us it works first! Let's prove the basic functionality with a simple proof-of-concept before building complex architecture.",
            
            VibeLevel.COMPLEX_VIBES: "⚖️ This feels pretty complex! Have we considered if there's a simpler approach that could achieve the same goals?",
            
            VibeLevel.BAD_VIBES: "🚨 Hold up! This looks like it might be building infrastructure without proving the basic functionality works first. Let's step back and start with the fundamentals."
        }
        
        return summaries[vibe_level]
    
    def _generate_coaching_recommendations(
        self,
        vibe_level: VibeLevel,
        basic_patterns: List[DetectionResult],
        claude_analysis: Optional[str],
        clear_thought_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate comprehensive coaching recommendations using enhanced coaching framework"""
        
        try:
            # Get coaching framework
            coaching_framework = get_vibe_coaching_framework()
            
            # Create issue context for coaching
            issue_context = {
                "vibe_level": vibe_level.value,
                "pattern_count": len(basic_patterns),
                "has_claude_analysis": claude_analysis is not None,
                "has_clear_thought": clear_thought_analysis is not None
            }
            
            # Generate comprehensive coaching recommendations
            coaching_recommendations = coaching_framework.generate_coaching_recommendations(
                vibe_level=vibe_level.value,
                detected_patterns=basic_patterns,
                issue_context=issue_context,
                detail_level=DetailLevel.STANDARD,
                learning_level=LearningLevel.INTERMEDIATE,
                tone=CoachingTone.ENCOURAGING
            )
            
            # Convert coaching recommendations to simple list format for compatibility
            simple_recommendations = []
            
            for coaching in coaching_recommendations:
                # Add main coaching title and description
                simple_recommendations.append(f"{coaching.title}: {coaching.description}")
                
                # Add top action items with emojis
                for action in coaching.action_items[:3]:  # Top 3 action items
                    simple_recommendations.append(f"• {action}")
                
                # Add learning opportunity if available
                if coaching.real_world_example:
                    simple_recommendations.append(f"💡 Real-world insight: {coaching.real_world_example[:100]}...")
            
            # Add Clear-Thought specific recommendations if available
            if clear_thought_analysis and "recommendations" in clear_thought_analysis:
                simple_recommendations.append("🧠 Enhanced Analysis Available:")
                simple_recommendations.extend(clear_thought_analysis["recommendations"])
            
            return simple_recommendations
            
        except Exception as e:
            logger.error(f"Enhanced coaching generation failed: {str(e)}")
            
            # Fallback to simple recommendations
            return self._generate_fallback_recommendations(vibe_level, clear_thought_analysis)
    
    def _generate_fallback_recommendations(
        self,
        vibe_level: VibeLevel,
        clear_thought_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Fallback simple recommendations if enhanced coaching fails"""
        
        fallback_recommendations = {
            VibeLevel.GOOD_VIBES: [
                "🎯 Proceed with implementation following the plan",
                "📋 Use the acceptance criteria to track progress",
                "✅ Consider adding tests to validate functionality",
                "🔄 Remember to iterate and improve based on feedback"
            ],
            
            VibeLevel.NEEDS_RESEARCH: [
                "📚 Check official documentation and tutorials first",
                "🔍 Search for existing solutions and libraries",
                "💡 Look for working examples in similar projects",
                "📝 Document your research findings before coding",
                "🎯 Update the issue with research results"
            ],
            
            VibeLevel.NEEDS_POC: [
                "🧪 Create a minimal proof-of-concept with real data",
                "🔗 Test basic API calls and core functionality",
                "📊 Validate key assumptions with working code",
                "📝 Document what works and what doesn't",
                "🏗️ Only then plan the full architecture"
            ],
            
            VibeLevel.COMPLEX_VIBES: [
                "🤔 Question if this complexity is really necessary",
                "💡 Try the simplest approach that could work first",
                "📝 Document why simple solutions aren't sufficient",
                "⚖️ Ensure complexity is proportional to business value",
                "🔧 Consider breaking into smaller, manageable pieces"
            ],
            
            VibeLevel.BAD_VIBES: [
                "🛑 Stop building infrastructure and start with basic API usage",
                "🎯 Focus on proving core functionality first",
                "📚 Read the official docs and follow standard patterns",
                "🧪 Create a working example before any architecture",
                "🔄 Come back to this issue after basic functionality works"
            ]
        }
        
        base_recommendations = fallback_recommendations[vibe_level]
        
        # Add Clear-Thought specific recommendations if available
        if clear_thought_analysis and "recommendations" in clear_thought_analysis:
            base_recommendations.extend(clear_thought_analysis["recommendations"])
        
        return base_recommendations
    
    def _generate_overall_vibe(self, vibe_level: VibeLevel) -> str:
        """Generate overall vibe emoji and text"""
        vibes = {
            VibeLevel.GOOD_VIBES: "✅ Good Vibes",
            VibeLevel.NEEDS_RESEARCH: "🔍 Research Vibes",
            VibeLevel.NEEDS_POC: "🧪 POC Vibes",
            VibeLevel.COMPLEX_VIBES: "⚖️ Complex Vibes",
            VibeLevel.BAD_VIBES: "🚨 Bad Vibes"
        }
        return vibes[vibe_level]
    
    def _post_github_comment(self, issue_number: int, repository: str, vibe_result: VibeCheckResult) -> None:
        """Post vibe check result as GitHub comment"""
        try:
            repo = self.github_client.get_repo(repository)
            issue = repo.get_issue(issue_number)
            
            # Format comment
            comment_body = self._format_github_comment(vibe_result)
            
            # Post comment
            issue.create_comment(comment_body)
            logger.info(f"Posted vibe check comment to issue #{issue_number}")
            
        except Exception as e:
            logger.error(f"Failed to post GitHub comment: {str(e)}")
    
    def _format_github_comment(self, vibe_result: VibeCheckResult) -> str:
        """Format vibe check result as GitHub comment"""
        return f"""## 🎯 Comprehensive Vibe Check

**Overall Vibe:** {vibe_result.overall_vibe}

### 💫 Vibe Summary
{vibe_result.friendly_summary}

### 🎓 Coaching Recommendations
{chr(10).join(f"- {rec}" for rec in vibe_result.coaching_recommendations)}

### 🔍 Technical Analysis Summary
- **Patterns Detected:** {len(vibe_result.technical_analysis['detected_patterns'])}
- **Claude Analysis:** {'✅ Available' if vibe_result.claude_reasoning else '❌ Not available'}
- **Clear-Thought Analysis:** {'✅ Applied' if vibe_result.clear_thought_analysis else '❌ Not needed'}

---
*This vibe check was generated by the enhanced Vibe Check MCP framework using Claude-powered analytical reasoning and validated pattern detection.*"""
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


# Global framework instance
_vibe_check_framework = None


def get_vibe_check_framework(github_token: Optional[str] = None) -> VibeCheckFramework:
    """Get or create vibe check framework instance"""
    global _vibe_check_framework
    if _vibe_check_framework is None:
        _vibe_check_framework = VibeCheckFramework(github_token)
    return _vibe_check_framework