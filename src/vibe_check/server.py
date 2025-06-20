"""
Vibe Check MCP FastMCP Server

Main MCP server entry point that provides anti-pattern detection capabilities
via the Model Context Protocol. Built on top of the validated Phase 1 core 
detection engine (87.5% accuracy, 0% false positives).

Usage:
    python -m vibe_check.server
    
Or programmatically:
    from vibe_check.server import run_server
    run_server()
"""

import logging
import os
import sys
import argparse
import secrets
from typing import Dict, Any, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    print("😅 FastMCP isn't vibing with us yet. Get it with: pip install fastmcp")
    sys.exit(1)

from .tools.analyze_text_nollm import analyze_text_demo
from .tools.analyze_issue_nollm import analyze_issue as analyze_github_issue_tool
from .tools.analyze_pr_nollm import analyze_pr_nollm as analyze_pr_nollm_function
from .tools.analyze_llm.tool_registry import register_llm_analysis_tools
from .tools.diagnostics_claude_cli import register_diagnostic_tools
from .tools.integration_decision_check import check_official_alternatives, analyze_integration_text, ValidationError, SCORING
from .tools.integration_pattern_analysis import (
    analyze_integration_patterns_fast, 
    quick_technology_scan, 
    analyze_effort_complexity,
    enhance_text_analysis_with_integration_patterns
)
from .tools.pr_review import review_pull_request
from .tools.vibe_mentor import get_mentor_engine, _generate_summary
from .tools.config_validation import validate_configuration, format_validation_results, log_validation_results, register_config_validation_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('vibe_check.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Vibe Check MCP")

# Register user diagnostic tools (essential for all users)
register_diagnostic_tools(mcp)

# Register configuration validation tools (Issue #98)
register_config_validation_tools(mcp)

# Register LLM-powered analysis tools
register_llm_analysis_tools(mcp)

# Temporarily disable dev tools to test if they're causing the crash
# Register development tools only when explicitly enabled via MCP config
dev_mode_override = os.getenv("VIBE_CHECK_DEV_MODE_OVERRIDE") == "true"
if dev_mode_override:
    try:
        # Import development test suite from tests directory
        import sys
        from pathlib import Path
        
        # Add tests directory to path for importing
        tests_dir = Path(__file__).parent.parent.parent / "tests"
        if str(tests_dir) not in sys.path:
            sys.path.insert(0, str(tests_dir))
        
        # Import dev tools with proper module handling
        import importlib
        register_dev_tools = None
        try:
            # Check if module is already loaded to avoid warnings
            if 'integration.claude_cli_tests' in sys.modules:
                # Use the existing module instead of reloading
                dev_tools_module = sys.modules['integration.claude_cli_tests']
                register_dev_tools = dev_tools_module.register_dev_tools
            else:
                from integration.claude_cli_tests import register_dev_tools
        except ImportError as e:
            logger.warning(f"Dev tools not available: {e}")
            # Skip dev tools registration if import fails
        
        if register_dev_tools:
            register_dev_tools(mcp)
            logger.info("🔧 Dev mode enabled: Comprehensive testing tools available")
            logger.info("   Available dev tools: test_claude_cli_integration, test_claude_cli_with_file_input,")
            logger.info("                       test_claude_cli_comprehensive, test_claude_cli_mcp_permissions")
    except ImportError as e:
        logger.warning(f"⚠️ Dev tools not available: {e}")
        logger.warning("   Set VIBE_CHECK_DEV_MODE=true and ensure tests/integration/claude_cli_tests.py exists")
else:
    logger.info("📦 User mode: Essential diagnostic tools only")
    logger.info("   Dev tools disabled to prevent import conflicts in Claude Code")
    logger.info("   To enable dev tools: set VIBE_CHECK_DEV_MODE_OVERRIDE=true")

@mcp.tool()
def analyze_text_nollm(text: str, detail_level: str = "standard") -> Dict[str, Any]:
    """
    🚀 Fast text analysis using direct pattern detection (no LLM calls).

    Direct pattern detection and anti-pattern analysis without LLM reasoning.
    Perfect for "quick vibe check", "fast pattern analysis", and development workflow.
    For comprehensive LLM-powered analysis, use analyze_text_llm instead.

    Features:
    - 🚀 Fast pattern detection on any content
    - 🎯 Direct analysis without LLM dependencies  
    - 🤝 Basic coaching recommendations
    - 📊 Pattern detection with confidence scoring

    Use this tool for: "quick vibe check this text", "fast pattern analysis", "basic text check"

    Args:
        text: Text content to analyze for anti-patterns
        detail_level: Educational detail level (brief/standard/comprehensive)
        
    Returns:
        Fast pattern detection analysis results
    """
    logger.info(f"Fast text analysis requested for {len(text)} characters")
    return analyze_text_demo(text, detail_level)

@mcp.tool()
def analyze_issue_nollm(
    issue_number: int, 
    repository: str = "kesslerio/vibe-check-mcp", 
    analysis_mode: str = "quick",
    detail_level: str = "standard",
    post_comment: bool = None
) -> Dict[str, Any]:
    """
    🚀 Fast GitHub issue analysis using direct pattern detection (no LLM calls).

    Direct GitHub issue analysis with pattern detection and GitHub API data.
    Perfect for "quick vibe check issue", "fast issue analysis", and development workflow.
    For comprehensive LLM-powered analysis, use analyze_issue_llm instead.

    Features:
    - 🚀 Fast pattern detection on GitHub issues
    - 🎯 Direct GitHub API integration
    - 🔍 Basic anti-pattern detection
    - 📊 Issue metrics and validation

    Use this tool for: "quick vibe check issue 23", "fast analysis issue 42", "basic issue check"

    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        analysis_mode: "quick" for fast pattern detection
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
        post_comment: Post analysis as GitHub comment (disabled by default for fast mode)
        
    Returns:
        Fast GitHub issue analysis with basic recommendations
    """
    # Auto-enable comment posting for comprehensive mode unless explicitly disabled
    if post_comment is None:
        post_comment = (analysis_mode == "comprehensive")
    
    logger.info(f"GitHub issue analysis ({analysis_mode}): #{issue_number} in {repository}")
    return analyze_github_issue_tool(
        issue_number=issue_number,
        repository=repository, 
        analysis_mode=analysis_mode,
        detail_level=detail_level,
        post_comment=post_comment
    )

@mcp.tool()
def analyze_pr_nollm(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    analysis_mode: str = "quick",
    detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    🚀 Fast PR analysis using direct pattern detection (no LLM calls).

    Direct PR analysis with metrics, pattern detection, and GitHub API data.
    Perfect for "quick PR check", "fast PR analysis", and development workflow.
    For comprehensive LLM-powered analysis, use analyze_pr_llm instead.

    Features:
    - 🚀 Fast PR metrics and pattern detection
    - 🎯 Direct GitHub API integration
    - 📊 PR size classification and file analysis
    - 🔍 Basic anti-pattern detection
    - 📋 Issue linkage validation

    Use this tool for: "quick PR check 44", "fast analysis PR 42", "basic PR review"

    Args:
        pr_number: PR number to analyze
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        analysis_mode: "quick" for fast analysis
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
        
    Returns:
        Fast PR analysis with basic recommendations
    """
    logger.info(f"Fast PR analysis requested: #{pr_number} in {repository} (mode: {analysis_mode})")
    return analyze_pr_nollm_function(
        pr_number=pr_number,
        repository=repository,
        analysis_mode=analysis_mode,
        detail_level=detail_level
    )

@mcp.tool()
async def review_pr_comprehensive(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    force_re_review: bool = False,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard",
    model: str = "sonnet"
) -> Dict[str, Any]:
    """
    🧠 Advanced PR review with file type analysis and model selection.
    
    Enhanced PR review tool with:
    - 📁 File type-specific analysis (TypeScript, Python, API endpoints, tests)
    - ⭐ First-time contributor awareness for encouraging feedback
    - 🔍 Security-focused review sections
    - 🧪 Test coverage analysis
    - 🎯 Model selection (sonnet/opus/haiku) for performance vs capability
    
    This is the enhanced modular PR review replacing the monolithic tool.
    
    Args:
        pr_number: PR number to review
        repository: Repository in format "owner/repo"
        force_re_review: Force re-review mode even if not auto-detected
        analysis_mode: "comprehensive" or "quick" analysis
        detail_level: "brief", "standard", or "comprehensive"
        model: Claude model - "sonnet" (default), "opus" (best), or "haiku" (fast)
        
    Returns:
        Comprehensive PR analysis with file type breakdown and recommendations
    """
    logger.info(f"🔍 Starting enhanced PR review for PR #{pr_number} with model: {model}")
    
    return await review_pull_request(
        pr_number=pr_number,
        repository=repository,
        force_re_review=force_re_review,
        analysis_mode=analysis_mode,
        detail_level=detail_level,
        model=model
    )

@mcp.tool()
def check_integration_alternatives(
    technology: str,
    custom_features: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    🔍 Official Alternative Check for Integration Decisions.
    
    Validates integration approaches against official alternatives to prevent
    unnecessary custom development. Based on real-world case studies including
    the Cognee integration failure where 2+ weeks were spent building custom
    REST servers instead of using the official Docker container.
    
    Features:
    - 🔍 Official alternative detection
    - ⚠️ Red flag identification for anti-patterns  
    - 📋 Decision framework generation
    - 🎯 Custom development justification requirements
    
    Use this tool for: "check cognee integration", "validate docker approach", "integration decision"
    
    Args:
        technology: Technology being integrated (e.g., "cognee", "supabase", "claude")
        custom_features: Comma-separated list of features being custom developed
        description: Optional description of the integration context
        
    Returns:
        Integration recommendation with research requirements and next steps
    """
    logger.info(f"Integration decision check for {technology}: {custom_features}")
    
    try:
        # Parse custom features from comma-separated string
        features_list = [f.strip() for f in custom_features.split(",") if f.strip()]
        
        # Get recommendation
        recommendation = check_official_alternatives(technology, features_list)
        
        # Convert dataclass to dict for JSON serialization
        result = {
            "status": "success",
            "technology": recommendation.technology,
            "warning_level": recommendation.warning_level,
            "official_solutions": recommendation.official_solutions,
            "custom_justification_needed": recommendation.custom_justification_needed,
            "research_required": recommendation.research_required,
            "red_flags_detected": recommendation.red_flags_detected,
            "decision_matrix": recommendation.decision_matrix,
            "next_steps": recommendation.next_steps,
            "recommendation": recommendation.recommendation,
            "description": description
        }
        
        return result
        
    except ValidationError as e:
        logger.warning(f"Input validation failed: {e}")
        return {
            "status": "error",
            "message": f"Input validation failed: {str(e)}",
            "technology": technology,
            "recommendation": "Please check your input parameters"
        }
    except Exception as e:
        logger.error(f"Integration decision check failed: {e}")
        return {
            "status": "error",
            "message": f"Integration analysis failed: {str(e)}",
            "technology": technology,
            "recommendation": "Manual research required due to analysis error"
        }

@mcp.tool()
def analyze_integration_decision_text(
    text: str,
    detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    🔍 Analyze text for integration decision anti-patterns.
    
    Scans text content for integration patterns and provides recommendations
    to prevent custom development when official alternatives exist. Detects
    technologies and custom development indicators automatically.
    
    Features:
    - 🔍 Technology detection in text
    - ⚠️ Custom development pattern identification
    - 📋 Automatic recommendation generation
    - 🎯 Integration decision guidance
    
    Use this tool for: "analyze this integration plan", "check for integration anti-patterns"
    
    Args:
        text: Text content to analyze for integration patterns
        detail_level: Educational detail level (brief/standard/comprehensive)
        
    Returns:
        Analysis of detected technologies and integration recommendations
    """
    logger.info(f"Integration decision text analysis for {len(text)} characters")
    
    try:
        analysis = analyze_integration_text(text)
        
        result = {
            "status": "success",
            "detected_technologies": analysis["detected_technologies"],
            "detected_custom_work": analysis["detected_custom_work"],
            "warning_level": analysis["warning_level"],
            "recommendations": analysis["recommendations"],
            "detail_level": detail_level,
            "text_length": len(text)
        }
        
        # Add educational content based on detail level
        if detail_level in ["standard", "comprehensive"]:
            result["educational_content"] = {
                "integration_best_practices": [
                    "Always research official deployment options first",
                    "Test official solutions with basic requirements",
                    "Document specific gaps before custom development",
                    "Consider maintenance burden of custom solutions"
                ],
                "common_anti_patterns": [
                    "Building custom REST servers when official containers exist",
                    "Manual authentication when SDKs provide it",
                    "Custom HTTP clients when official SDKs exist",
                    "Environment forcing instead of proper configuration"
                ]
            }
        
        if detail_level == "comprehensive":
            result["case_studies"] = {
                "cognee_failure": {
                    "problem": "2+ weeks spent building custom FastAPI server",
                    "solution": "cognee/cognee:main Docker container available",
                    "lesson": "Official containers often provide complete functionality"
                }
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Integration decision text analysis failed: {e}")
        return {
            "status": "error",
            "message": f"Text analysis failed: {str(e)}",
            "text_length": len(text)
        }

@mcp.tool()
def integration_decision_framework(
    technology: str,
    custom_features: str,
    decision_statement: str = "",
    analysis_type: str = "weighted-criteria"
) -> Dict[str, Any]:
    """
    🧠 Integration Decision Framework with Clear Thought Analysis.
    
    Combines integration alternative checking with Clear Thought decision framework
    to provide structured decision analysis for integration approaches. Designed
    to prevent unnecessary custom development through systematic evaluation.
    
    Features:
    - 🧠 Clear Thought decision framework integration
    - 🔍 Official alternative checking
    - ⚖️ Weighted criteria analysis
    - 📋 Structured decision documentation
    
    Use this tool for: "decide on cognee integration approach", "framework for docker vs custom"
    
    Args:
        technology: Technology being integrated (e.g., "cognee", "supabase")
        custom_features: Comma-separated list of features being custom developed
        decision_statement: Decision being made (auto-generated if empty)
        analysis_type: Type of analysis (weighted-criteria, pros-cons, risk-analysis)
        
    Returns:
        Comprehensive decision framework with recommendations and next steps
    """
    logger.info(f"Integration decision framework for {technology}: {analysis_type}")
    
    try:
        # First get the basic integration analysis
        features_list = [f.strip() for f in custom_features.split(",") if f.strip()]
        recommendation = check_official_alternatives(technology, features_list)
        
        # Generate decision statement if not provided
        if not decision_statement:
            decision_statement = f"Choose integration approach for {technology}: Official solution vs Custom development"
        
        # Create structured decision framework
        framework = {
            "status": "success",
            "decision_statement": decision_statement,
            "technology": technology,
            "analysis_type": analysis_type,
            "integration_analysis": {
                "warning_level": recommendation.warning_level,
                "official_solutions": recommendation.official_solutions,
                "red_flags_detected": recommendation.red_flags_detected,
                "research_required": recommendation.research_required
            },
            "decision_options": [
                {
                    "option": "Official Solution",
                    "description": f"Use official {technology} container/SDK",
                    "pros": [
                        "Vendor maintained and supported",
                        "Production ready and tested",
                        "Security updates included",
                        "Minimal development time",
                        "Community documentation"
                    ],
                    "cons": [
                        "Less customization control",
                        "Potential feature limitations",
                        "Dependency on vendor roadmap"
                    ],
                    "effort_score": 2,
                    "risk_score": 1,
                    "maintenance_score": 1
                },
                {
                    "option": "Custom Development",
                    "description": f"Build custom {technology} integration",
                    "pros": [
                        "Full control over implementation",
                        "Exact requirement matching",
                        "No vendor dependencies"
                    ],
                    "cons": [
                        "High development time",
                        "Ongoing maintenance burden",
                        "Security responsibility",
                        "Documentation overhead",
                        "Testing complexity"
                    ],
                    "effort_score": 8,
                    "risk_score": 6,
                    "maintenance_score": 8
                }
            ],
            "criteria_weights": {
                "development_time": 0.25,
                "maintenance_burden": 0.30,
                "reliability_support": 0.25,
                "customization_needs": 0.20
            },
            "recommendation": recommendation.recommendation,
            "next_steps": recommendation.next_steps
        }
        
        # Add analysis-specific content
        if analysis_type == "weighted-criteria":
            framework["scoring_matrix"] = SCORING
        
        elif analysis_type == "risk-analysis":
            framework["risk_assessment"] = {
                "official_solution_risks": [
                    "Vendor discontinuation (Low probability)",
                    "Feature gaps for requirements (Medium probability)",
                    "Breaking changes in updates (Low probability)"
                ],
                "custom_development_risks": [
                    "Development timeline overrun (High probability)",
                    "Security vulnerabilities (Medium probability)",
                    "Maintenance neglect over time (High probability)",
                    "Knowledge silos and team dependencies (Medium probability)"
                ]
            }
        
        # Add Clear Thought integration guidance
        framework["clear_thought_integration"] = {
            "mental_model": "first_principles",
            "reasoning_approach": "Start with the simplest solution that could work",
            "decision_trigger": f"Research official {technology} solution thoroughly before considering custom development",
            "complexity_check": "Is custom development truly necessary or driven by assumptions?",
            "validation_steps": [
                f"Test official {technology} solution with actual requirements",
                "Document specific gaps that justify custom development",
                "Estimate total cost of ownership for both approaches",
                "Consider team expertise and long-term maintenance"
            ]
        }
        
        return framework
        
    except Exception as e:
        logger.error(f"Integration decision framework failed: {e}")
        return {
            "status": "error",
            "message": f"Decision framework analysis failed: {str(e)}",
            "technology": technology,
            "recommendation": "Manual decision analysis required due to error"
        }

@mcp.tool()
def integration_research_with_websearch(
    technology: str,
    custom_features: str,
    search_depth: str = "basic"
) -> Dict[str, Any]:
    """
    🔍 Enhanced Integration Research with Real-time Web Search.
    
    Combines static knowledge base with real-time web search to research
    official alternatives for technologies. Searches for official documentation,
    Docker containers, SDKs, and deployment guides to provide up-to-date
    integration recommendations.
    
    Features:
    - 🌐 Real-time web search for official documentation
    - 🔍 Official container and SDK discovery
    - 📋 Up-to-date deployment options research
    - 🎯 Enhanced red flag detection with current information
    
    Use this tool for: "research new technology integration", "find official deployment options"
    
    Args:
        technology: Technology to research (e.g., "new-framework", "emerging-tool")
        custom_features: Comma-separated list of features being considered for custom development
        search_depth: Search depth ("basic" or "advanced")
        
    Returns:
        Enhanced integration recommendation with web-researched information
    """
    logger.info(f"Enhanced integration research for {technology} with web search")
    
    try:
        # Parse custom features
        features_list = [f.strip() for f in custom_features.split(",") if f.strip()]
        
        # Perform web search for technology information
        search_results = {}
        search_queries = [
            f"{technology} official documentation deployment",
            f"{technology} official docker container hub",
            f"{technology} official SDK API client",
            f"{technology} deployment guide best practices"
        ]
        
        enhanced_info = {
            "technology": technology,
            "search_performed": True,
            "search_queries": search_queries,
            "web_findings": {},
            "enhanced_recommendations": [],
            "confidence_level": "web-enhanced"
        }
        
        # Use available MCP tools for real web search
        try:
            from .tools.web_search_integration import search_technology_documentation
            search_results = search_technology_documentation(technology, features_list)
            enhanced_info["web_findings"] = search_results
            
        except Exception as search_error:
            logger.warning(f"Web search execution failed: {search_error}")
            enhanced_info["web_findings"]["search_error"] = str(search_error)
            # Fallback to search methodology guidance
            enhanced_info["web_findings"]["fallback_guidance"] = {
                "manual_search_required": True,
                "recommended_sources": [
                    f"https://docs.{technology.lower()}.com",
                    f"https://github.com/{technology.lower()}",
                    f"https://deepwiki.com/{technology.lower()}",  # For public GitHub repos
                    f"https://hub.docker.com/search?q={technology}",
                    "Official vendor documentation sites"
                ]
            }
        
        # Get base recommendation from static knowledge
        try:
            base_recommendation = check_official_alternatives(technology, features_list)
            enhanced_info["base_analysis"] = {
                "warning_level": base_recommendation.warning_level,
                "official_solutions": base_recommendation.official_solutions,
                "red_flags_detected": base_recommendation.red_flags_detected,
                "recommendation": base_recommendation.recommendation
            }
        except ValidationError as e:
            return {
                "status": "error",
                "message": f"Input validation failed: {str(e)}",
                "technology": technology
            }
        
        # Enhance recommendations with web search insights
        enhanced_info["enhanced_recommendations"] = [
            "Research official documentation for deployment options",
            f"Check Docker Hub for official {technology} containers",
            f"Search GitHub for official {technology} SDKs and examples",
            "Compare community solutions vs official approaches",
            "Validate custom development necessity with current options"
        ]
        
        # Provide research methodology guidance
        enhanced_info["research_methodology"] = {
            "search_strategy": [
                "Official documentation sites first",
                "Official GitHub repositories",
                "Docker Hub official images",
                "Package managers (npm, PyPI, etc.)",
                "Community discussions and comparisons"
            ],
            "validation_steps": [
                "Test official solution with basic requirements",
                "Check for recent updates and maintenance",
                "Evaluate community support and documentation quality",
                "Assess long-term vendor commitment"
            ]
        }
        
        enhanced_info["status"] = "success"
        return enhanced_info
        
    except Exception as e:
        logger.error(f"Enhanced integration research failed: {e}")
        return {
            "status": "error", 
            "message": f"Research failed: {str(e)}",
            "technology": technology,
            "recommendation": "Perform manual research using search methodology"
        }

@mcp.tool()
def analyze_integration_patterns(
    content: str,
    context: str = "",
    detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    🚀 Fast Integration Pattern Detection for Vibe Coding Safety Net.
    
    Real-time detection of integration anti-patterns to prevent engineering disasters
    like the Cognee case study. Provides instant feedback on technology usage and
    custom development decisions with sub-second response for development workflow.
    
    Features:
    - 🔍 Technology Recognition: Instant detection of Cognee, Supabase, OpenAI, Claude
    - ⚠️ Red Flag Detection: Custom development when official alternatives exist
    - 📊 Effort Analysis: High line counts for standard integrations
    - 💡 Immediate Recommendations: Official alternatives and next steps
    
    Use this tool for: "vibe check this integration plan", "analyze for integration anti-patterns"
    
    Args:
        content: Text content to analyze (PR description, issue content, code comments)
        context: Additional context (title, file names, related information)
        detail_level: Analysis detail level (brief/standard/comprehensive)
        
    Returns:
        Real-time integration pattern analysis with actionable recommendations
    """
    logger.info(f"Integration pattern analysis for {len(content)} characters")
    
    return analyze_integration_patterns_fast(
        content=content,
        context=context if context else None,
        detail_level=detail_level
    )

@mcp.tool()
def quick_tech_scan(content: str) -> Dict[str, Any]:
    """
    ⚡ Ultra-Fast Technology Scan for Immediate Feedback.
    
    Instant detection of known technologies (Cognee, Supabase, OpenAI, Claude)
    with immediate alerts about official alternatives. Designed for real-time
    development workflow integration where sub-second response is critical.
    
    Features:
    - ⚡ Sub-second response time
    - 🎯 Technology-specific official alternatives
    - 🚨 Immediate red flag alerts
    - ✅ Quick action recommendations
    
    Use this tool for: "scan for known technologies", "quick tech check", "instant integration scan"
    
    Args:
        content: Text content to scan for technology mentions
        
    Returns:
        Instant technology detection with official alternatives
    """
    logger.info("Ultra-fast technology scan requested")
    
    return quick_technology_scan(content)

@mcp.tool()
def analyze_integration_effort(
    content: str,
    lines_added: int = 0,
    lines_deleted: int = 0,
    files_changed: int = 0
) -> Dict[str, Any]:
    """
    📊 Integration Effort-Complexity Analysis.
    
    Analyzes the relationship between development effort and integration complexity
    to identify potential over-engineering. Helps prevent scenarios like the Cognee
    case study where 2000+ lines were spent on standard integrations.
    
    Features:
    - 📏 Line count analysis for integration work
    - ⚖️ Effort-value ratio assessment
    - 🎯 Technology-specific effort guidance
    - 💡 Official alternative recommendations
    
    Use this tool for: "analyze integration effort", "check development complexity", "effort-value analysis"
    
    Args:
        content: Content to analyze for effort indicators
        lines_added: Lines added in PR/change (optional)
        lines_deleted: Lines deleted in PR/change (optional)
        files_changed: Number of files modified (optional)
        
    Returns:
        Effort-complexity analysis with recommendations
    """
    logger.info("Integration effort-complexity analysis requested")
    
    pr_metrics = None
    if lines_added > 0 or lines_deleted > 0 or files_changed > 0:
        pr_metrics = {
            "additions": lines_added,
            "deletions": lines_deleted,
            "changed_files": files_changed
        }
    
    return analyze_effort_complexity(
        content=content,
        pr_metrics=pr_metrics
    )

@mcp.tool()
def analyze_doom_loops(
    content: str,
    context: str = "",
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    🔄 AI Doom Loop Detection and Analysis Paralysis Prevention.
    
    Detects when developers get stuck in unproductive AI conversation loops,
    decision paralysis, and endless analysis cycles. Provides immediate
    intervention suggestions to restore development momentum.
    
    Features:
    - 🕵️ Pattern Detection: Identifies analysis paralysis language patterns
    - ⏱️ Session Analysis: Monitors MCP session for time-sink behaviors
    - 🚨 Real-time Alerts: Warns about productivity-killing cycles
    - 💡 Intervention: Concrete steps to break out of doom loops
    
    Use this tool for: "analyze for analysis paralysis", "check for doom loops", "productivity check"
    
    Args:
        content: Text content to analyze (issue, PR, conversation)
        context: Additional context (comments, related discussions)
        analysis_type: Type of analysis (quick/standard/comprehensive)
        
    Returns:
        Doom loop analysis with intervention recommendations
    """
    logger.info(f"Doom loop analysis requested for {len(content)} characters")
    
    try:
        from .tools.doom_loop_analysis import analyze_text_for_doom_loops, get_session_health_analysis
        
        # Analyze text for doom loop patterns
        text_analysis = analyze_text_for_doom_loops(content, context, "analyze_doom_loops")
        
        # Get session health context
        session_health = get_session_health_analysis()
        
        # Combine results
        result = {
            "status": "analysis_complete",
            "text_analysis": text_analysis,
            "session_health": session_health,
            "analysis_type": "doom_loop_detection"
        }
        
        # Determine overall recommendation
        text_severity = text_analysis.get("severity", "none")
        session_severity = session_health.get("severity", "none")
        
        severity_scores = {"none": 0, "caution": 1, "warning": 2, "critical": 3, "emergency": 4}
        overall_severity = max(severity_scores.get(text_severity, 0), severity_scores.get(session_severity, 0))
        
        if overall_severity >= 3:
            result["urgent_intervention"] = {
                "message": "🚨 CRITICAL: Doom loop detected - immediate action required",
                "actions": [
                    "STOP all analysis immediately",
                    "Pick ANY viable option from current discussion",
                    "Set 10-minute implementation timer",
                    "Focus on shipping, not perfecting"
                ]
            }
        elif overall_severity >= 2:
            result["intervention_suggested"] = {
                "message": "⚠️ WARNING: Analysis paralysis patterns detected",
                "actions": [
                    "Set 15-minute decision deadline",
                    "Choose simplest working solution",
                    "Start implementation this hour"
                ]
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Doom loop analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "fallback_guidance": [
                "If stuck in analysis: Set 15-minute timer and make any decision",
                "Perfect is the enemy of done - ship something working",
                "Take 10-minute break and return with implementation focus"
            ]
        }

@mcp.tool()
def session_health_check() -> Dict[str, Any]:
    """
    🏥 MCP Session Health and Productivity Analysis.
    
    Provides comprehensive health analysis of your current MCP session to detect
    doom loops, analysis paralysis, and productivity anti-patterns. Monitors
    tool usage patterns, session duration, and decision-making cycles.
    
    Features:
    - 📊 Health Score: 0-100 productivity score for current session
    - ⏱️ Time Analysis: Session duration and time allocation patterns
    - 🔄 Pattern Detection: Repeated tool usage and topic cycling
    - 📈 Trend Analysis: Productivity trajectory and improvement suggestions
    
    Use this tool for: "check my productivity", "session health", "am I in a loop?"
    
    Returns:
        Comprehensive session health report with recommendations
    """
    logger.info("Session health check requested")
    
    try:
        from .tools.doom_loop_analysis import get_session_health_analysis
        
        health_report = get_session_health_analysis()
        
        # Add user-friendly summary
        if health_report["status"] == "no_active_session":
            return {
                "status": "no_session",
                "message": "✅ No active session - fresh start available",
                "recommendation": "Session tracking will begin with your next tool call"
            }
        
        health_score = health_report.get("health_score", 100)
        duration = health_report.get("duration_minutes", 0)
        
        # Generate health assessment
        if health_score >= 90:
            health_emoji = "🟢"
            health_status = "Excellent"
        elif health_score >= 70:
            health_emoji = "🟡"
            health_status = "Good"
        elif health_score >= 50:
            health_emoji = "🟠"
            health_status = "Caution"
        else:
            health_emoji = "🔴"
            health_status = "Critical"
        
        # Add assessment to report
        health_report["health_assessment"] = {
            "emoji": health_emoji,
            "status": health_status,
            "summary": f"{health_emoji} {health_status} ({health_score}/100) - {duration}min session"
        }
        
        return health_report
        
    except Exception as e:
        logger.error(f"Session health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Health check failed - assume session is healthy and continue working"
        }

@mcp.tool()
def productivity_intervention() -> Dict[str, Any]:
    """
    🆘 Emergency Productivity Intervention and Loop Breaking.
    
    Forces immediate productivity intervention to break out of analysis paralysis,
    doom loops, and decision cycles. Use when you recognize you're stuck or
    when other tools suggest critical intervention is needed.
    
    Features:
    - 🚨 Emergency Stop: Immediate halt to analysis and planning
    - ⚡ Action Forcing: Concrete next steps with time limits
    - 🎯 Decision Support: Simplified decision-making frameworks
    - 🔄 Momentum Reset: Fresh start with implementation focus
    
    Use this tool for: "I'm stuck", "break the loop", "emergency productivity", "force decision"
    
    Returns:
        Emergency intervention with mandatory next steps
    """
    logger.info("Productivity intervention requested")
    
    try:
        from .tools.doom_loop_analysis import force_doom_loop_intervention
        
        intervention = force_doom_loop_intervention()
        
        # Add additional emergency guidance
        intervention["emergency_protocol"] = {
            "step_1": "🛑 STOP: Close this analysis immediately",
            "step_2": "⏰ Set 5-minute timer for final decision",
            "step_3": "✅ Pick FIRST viable option from discussion",
            "step_4": "🚀 Start implementing immediately (no more planning)",
            "step_5": "📊 Validate with real usage within 1 hour"
        }
        
        intervention["mantras"] = [
            "Done is better than perfect",
            "Ship something, iterate everything",
            "Perfect is the enemy of shipped",
            "Start ugly, make it beautiful later"
        ]
        
        return intervention
        
    except Exception as e:
        logger.error(f"Productivity intervention failed: {e}")
        return {
            "status": "emergency_fallback",
            "message": "🆘 INTERVENTION ACTIVATED",
            "immediate_actions": [
                "STOP reading this - start implementing NOW",
                "Pick any solution that works",
                "Set 10-minute implementation timer",
                "Ship first, optimize later"
            ]
        }

@mcp.tool()
def reset_session_tracking() -> Dict[str, Any]:
    """
    🔄 Reset Session Tracking for Fresh Start.
    
    Resets MCP session tracking to start fresh after completing implementations,
    breaking out of doom loops, or reaching natural stopping points. Useful
    for beginning new tasks with clean productivity metrics.
    
    Features:
    - 🆕 Fresh Start: Clean session state for new tasks
    - 📊 Previous Summary: Report on completed session metrics
    - ⚡ Momentum Reset: Clear tracking for productivity restart
    - 🎯 Focus Renewal: Begin with implementation-first mindset
    
    Use this tool for: "fresh start", "reset tracking", "new session", "clean slate"
    
    Returns:
        Reset confirmation with previous session summary
    """
    logger.info("Session tracking reset requested")
    
    try:
        from .tools.doom_loop_analysis import reset_session_tracking
        
        reset_result = reset_session_tracking()
        
        # Add motivational messaging
        reset_result["fresh_start_guidance"] = {
            "mindset": "🎯 Implementation-first approach",
            "time_budget": "⏰ Time-box decisions to 15 minutes max",
            "success_metrics": "📈 Measure progress by code shipped, not analysis depth",
            "remember": "🚀 Build fast, iterate faster"
        }
        
        return reset_result
        
    except Exception as e:
        logger.error(f"Session reset failed: {e}")
        return {
            "status": "manual_reset",
            "message": "✅ Consider this a fresh start - track your own productivity",
            "guidance": "Focus on implementation over analysis for next session"
        }

def _get_phase_affirmation(phase: str, query: str) -> str:
    """Generate phase-specific affirmation when no interrupt is needed"""
    phase_affirmations = {
        "planning": [
            "Good choice - using standard tools",
            "Solid approach - keep it simple",
            "Great! Following established patterns"
        ],
        "implementation": [
            "Clean implementation - well done",
            "Following best practices - excellent",
            "Standard approach confirmed - proceed"
        ],
        "review": [
            "Implementation looks clean",
            "Matches requirements well",
            "Ready for next steps"
        ]
    }
    
    # Simple keyword matching for more specific affirmations
    if "pandas" in query.lower() or "standard" in query.lower():
        return phase_affirmations[phase][0]
    elif "official" in query.lower() or "sdk" in query.lower():
        return phase_affirmations[phase][1]
    else:
        return phase_affirmations[phase][2]

@mcp.tool()
def vibe_check_mentor(
    query: str,
    context: Optional[str] = None,
    session_id: Optional[str] = None,
    reasoning_depth: str = "standard",
    continue_session: bool = False,
    mode: str = "standard",
    phase: str = "planning",
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    🧠 Senior engineer collaborative reasoning - Get multi-perspective feedback on technical decisions.

    Interactive senior engineer mentor combining vibe-check pattern detection with collaborative reasoning.
    Multiple engineering personas analyze your technical decisions and provide structured feedback.

    Features:
    - 🧠 Multi-persona collaborative reasoning (Senior, Product, AI/ML Engineer perspectives)
    - 🎯 Automatic anti-pattern detection drives persona responses
    - 💬 Session continuity for multi-turn conversations  
    - 📊 Structured insights with consensus and disagreements
    - 🎓 Educational coaching recommendations
    - ⚡ NEW: Interrupt mode for quick focused interventions

    Modes:
    - interrupt: Quick focused intervention (<3 seconds) - single question/approval
    - standard: Normal collaborative reasoning with selected personas
    - comprehensive: Full analysis (legacy, same as reasoning_depth="comprehensive")

    Reasoning Depths (when mode="standard"):
    - quick: Senior engineer perspective only
    - standard: Senior + Product engineer perspectives  
    - comprehensive: All personas with full collaborative reasoning

    Use this tool for: "Should I build a custom auth system?", "Planning microservices architecture", 
    "What's the best approach for API integration?", "Continue previous discussion about caching"

    Args:
        query: Technical question or decision to discuss
        context: Additional context (code, architecture, requirements)
        session_id: Session ID to continue previous conversation
        reasoning_depth: Analysis depth - quick/standard/comprehensive (default: standard)
        continue_session: Whether to continue existing session (default: false)
        mode: Interaction mode - interrupt/standard (default: standard)
        phase: Development phase - planning/implementation/review (default: planning)
        confidence_threshold: Minimum confidence to trigger interrupt (default: 0.7)
        
    Returns:
        Collaborative reasoning analysis with multi-perspective insights or quick interrupt
    """
    logger.info(f"Vibe mentor activated: mode={mode}, depth={reasoning_depth}, phase={phase} for query: {query[:100]}...")
    
    try:
        # Get mentor engine instance
        engine = get_mentor_engine()
        
        # Step 1: Enhanced vibe-check pattern detection with PR diff support
        combined_text = f"{query}\n\n{context}" if context else query
        
        # FIX FOR ISSUE #151: Detect PR analysis and fetch actual diff
        pr_diff_content = ""
        import re
        import os
        
        # Enhanced PR detection regex to handle edge cases from Claude review
        pr_patterns = [
            r'(?:PR|pull request)\s*#?(\d+)',  # "PR #123" or "pull request 123"
            r'#(\d+)(?:\s|$)',                 # "#123" at word boundary
            r'PR(\d+)(?:\s|$)',                # "PR123" without space
            r'pr/(\d+)',                       # "pr/123" slash notation
        ]
        
        pr_number = None
        for pattern in pr_patterns:
            pr_match = re.search(pattern, query, re.IGNORECASE)
            if pr_match:
                pr_number = int(pr_match.group(1))
                break
        
        if pr_number:
            # Configurable repository fallback from environment or default
            default_repo = os.getenv('VIBE_CHECK_DEFAULT_REPO', 'kesslerio/vibe-check-mcp')
            repo_match = re.search(r'(?:repo|repository)[:=\s]+([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', combined_text, re.IGNORECASE)
            repository = repo_match.group(1) if repo_match else default_repo
            
            try:
                # Use GitHub abstraction layer to fetch PR diff
                from .tools.shared.github_abstraction import get_default_github_operations
                github_ops = get_default_github_operations()
                diff_result = github_ops.get_pull_request_diff(repository, pr_number)
                
                if diff_result.success:
                    # Performance limit: Truncate very large diffs to prevent timeout
                    max_diff_size = int(os.getenv('VIBE_CHECK_MAX_DIFF_SIZE', '50000'))  # 50KB default
                    diff_data = diff_result.data
                    
                    if len(diff_data) > max_diff_size:
                        diff_data = diff_data[:max_diff_size] + f"\n\n[TRUNCATED: Diff too large ({len(diff_result.data)} chars). Showing first {max_diff_size} characters for performance.]"
                        logger.info(f"Truncated large diff for PR #{pr_number} ({len(diff_result.data)} chars -> {max_diff_size} chars)")
                    
                    pr_diff_content = f"\n\n**ACTUAL PR DIFF (ISSUE #151 FIX):**\n{diff_data}"
                    logger.info(f"Successfully fetched diff for PR #{pr_number} in {repository}")
                else:
                    logger.warning(f"Failed to fetch PR diff: {diff_result.error}")
            except Exception as e:
                logger.warning(f"Error fetching PR diff: {e}")
        
        # Include PR diff in analysis if found
        enhanced_text = combined_text + pr_diff_content
        vibe_analysis = analyze_text_demo(enhanced_text, detail_level="standard")
        
        detected_patterns = vibe_analysis.get("detected_patterns", [])
        vibe_level = vibe_analysis.get("vibe_assessment", {}).get("vibe_level", "unknown")
        pattern_confidence = vibe_analysis.get("vibe_assessment", {}).get("confidence", 0)
        
        # Step 2: Handle interrupt mode for quick interventions
        if mode == "interrupt":
            # Quick pattern analysis for interrupt decision
            interrupt_needed = pattern_confidence > confidence_threshold
            
            if interrupt_needed and detected_patterns:
                # Generate focused intervention based on highest confidence pattern
                primary_pattern = detected_patterns[0]  # Already sorted by confidence
                
                # Get phase-aware question from mentor engine
                interrupt_response = engine.generate_interrupt_intervention(
                    query=query,
                    phase=phase,
                    primary_pattern=primary_pattern,
                    pattern_confidence=pattern_confidence
                )
                
                return {
                    "status": "success",
                    "mode": "interrupt",
                    "interrupt": True,
                    "question": interrupt_response["question"],
                    "severity": interrupt_response["severity"],
                    "suggestion": interrupt_response["suggestion"],
                    "session_id": session_id or f"interrupt-{secrets.token_hex(4)}",
                    "pattern_detected": primary_pattern.get("pattern_type", "unknown"),
                    "confidence": pattern_confidence,
                    "phase": phase,
                    "can_escalate": True,
                    "escalation_hint": "Use mode='standard' with same session_id for full analysis"
                }
            else:
                # No intervention needed - proceed
                return {
                    "status": "success", 
                    "mode": "interrupt",
                    "interrupt": False,
                    "proceed": True,
                    "affirmation": _get_phase_affirmation(phase, query),
                    "confidence": pattern_confidence,
                    "phase": phase
                }
        
        # Step 3: Standard mode - Create or retrieve session
        if continue_session and session_id and session_id in engine.sessions:
            session = engine.sessions[session_id]
            # Update topic for continued conversation but preserve session continuity
            session.topic = query
            logger.info(f"Continuing session {session_id} with new topic: {query}")
        else:
            # For new sessions, preserve session_id if provided for continuity
            if session_id and not continue_session:
                # User provided session_id but not continuing - this maintains ID consistency
                session = engine.create_session(topic=query, session_id=session_id)
                logger.info(f"Created new session with provided ID: {session_id}")
            else:
                # Generate new session for fresh start
                session = engine.create_session(topic=query)
                logger.info(f"Created new session with generated ID: {session.session_id}")
        
        # Step 4: Determine number of contributions based on depth
        contribution_counts = {
            "quick": 1,  # Just senior engineer
            "standard": 2,  # Senior + Product  
            "comprehensive": 3  # All personas
        }
        
        num_contributions = contribution_counts.get(reasoning_depth, 2)
        
        # Step 5: Generate contributions from personas
        for i in range(num_contributions):
            if i < len(session.personas):
                persona = session.personas[i]
                session.active_persona_id = persona.id
                
                contribution = engine.generate_contribution(
                    session=session,
                    persona=persona,
                    detected_patterns=detected_patterns,
                    context=context
                )
                
                session.contributions.append(contribution)
                
                # Advance stage after each contribution in comprehensive mode
                if reasoning_depth == "comprehensive" and i < num_contributions - 1:
                    engine.advance_stage(session)
        
        # Step 6: Synthesize insights
        synthesis = engine.synthesize_session(session)
        
        # Cleanup old sessions to prevent memory leaks
        engine.cleanup_old_sessions()
        
        # Step 7: Get coaching recommendations
        from .core.vibe_coaching import VibeCoachingFramework, CoachingTone
        coaching_framework = VibeCoachingFramework()
        coaching_recs = coaching_framework.generate_coaching_recommendations(
            vibe_level=vibe_level,
            detected_patterns=[],  # Already processed
            issue_context={"query": query},
            tone=CoachingTone.ENCOURAGING
        )
        
        # Step 8: Build response
        response = {
            "status": "success",
            "immediate_feedback": {
                "summary": _generate_summary(vibe_level, detected_patterns, synthesis),
                "confidence": vibe_analysis.get("vibe_assessment", {}).get("confidence", 0),
                "detected_patterns": [p["pattern_type"] for p in detected_patterns],
                "vibe_level": vibe_level
            },
            "collaborative_insights": {
                "consensus": synthesis["consensus_points"],
                "perspectives": {
                    contrib.persona_id: {
                        "message": contrib.content,
                        "type": contrib.type,
                        "confidence": contrib.confidence
                    }
                    for contrib in session.contributions
                },
                "key_insights": synthesis["key_insights"],
                "concerns": synthesis["primary_concerns"],
                "recommendations": synthesis["recommendations"]
            },
            "coaching_guidance": {
                "primary_recommendation": coaching_recs[0].title if coaching_recs else "Proceed with implementation",
                "action_steps": coaching_recs[0].action_items[:3] if coaching_recs else [],
                "prevention_checklist": coaching_recs[0].prevention_checklist[:3] if coaching_recs else []
            },
            "session_info": {
                "session_id": session.session_id,
                "stage": session.stage,
                "iteration": session.iteration,
                "can_continue": session.next_contribution_needed
            },
            "reasoning_depth": reasoning_depth,
            "formatted_output": engine.format_session_output(session)
        }
        
        # Log formatted output for debugging
        logger.info(response["formatted_output"])
        
        return response
        
    except Exception as e:
        logger.error(f"Vibe mentor error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Mentoring session failed: {str(e)}",
            "fallback_guidance": [
                "Start with official documentation",
                "Build a simple prototype first",
                "Get feedback early and often"
            ]
        }


@mcp.tool()
def server_status() -> Dict[str, Any]:
    """
    Get Vibe Check MCP server status and capabilities.
    
    Returns:
        Server status, core engine validation results, and available capabilities
    """
    # Check if dev mode is enabled
    dev_mode_enabled = os.getenv("VIBE_CHECK_DEV_MODE") == "true"
    
    # Core tools always available
    core_tools = [
        "analyze_text_demo - Demo anti-pattern analysis",
        "analyze_github_issue - GitHub issue analysis (Issue #22 ✅ COMPLETE)",
        "review_pull_request - Comprehensive PR review (Issue #35 ✅ COMPLETE)",
        "claude_cli_status - Essential: Check Claude CLI availability and version",
        "claude_cli_diagnostics - Essential: Diagnose Claude CLI timeout and recursion issues",
        "validate_mcp_configuration - Comprehensive Claude CLI and MCP configuration validation (Issue #98 ✅ COMPLETE)",
        "check_claude_cli_integration - Quick Claude CLI integration health check (Issue #98 ✅ COMPLETE)",
        "analyze_text_llm - Claude CLI content analysis with LLM reasoning",
        "analyze_pr_llm - Claude CLI PR review with comprehensive analysis",
        "analyze_code_llm - Claude CLI code analysis for anti-patterns",
        "analyze_issue_llm - Claude CLI issue analysis with specialized prompts",
        "analyze_github_issue_llm - GitHub issue vibe check with Claude CLI reasoning",
        "analyze_github_pr_llm - GitHub PR vibe check with comprehensive Claude CLI analysis",
        "analyze_llm_status - Status check for Claude CLI integration",
        "check_integration_alternatives - Official alternative check for integration decisions (Issue #113 ✅ COMPLETE)",
        "analyze_integration_decision_text - Text analysis for integration anti-patterns (Issue #113 ✅ COMPLETE)",
        "integration_decision_framework - Structured decision framework with Clear Thought integration (Issue #113 ✅ COMPLETE)",
        "integration_research_with_websearch - Enhanced integration research with real-time web search (Issue #113 ✅ COMPLETE)",
        "analyze_integration_patterns - Fast integration pattern detection for vibe coding safety net (Issue #112 ✅ COMPLETE)",
        "quick_tech_scan - Ultra-fast technology scan for immediate feedback (Issue #112 ✅ COMPLETE)",
        "analyze_integration_effort - Integration effort-complexity analysis (Issue #112 ✅ COMPLETE)",
        "analyze_doom_loops - AI doom loop and analysis paralysis detection (Issue #116 ⚡ NEW)",
        "session_health_check - MCP session health and productivity analysis (Issue #116 ⚡ NEW)", 
        "productivity_intervention - Emergency productivity intervention and loop breaking (Issue #116 ⚡ NEW)",
        "reset_session_tracking - Reset session tracking for fresh start (Issue #116 ⚡ NEW)",
        "vibe_check_mentor - Senior engineer collaborative reasoning with multi-persona feedback (Issue #126 🔥 LATEST)",
        "server_status - Server status and capabilities"
    ]
    
    # Development tools (environment-based)
    dev_tools = [
        "test_claude_cli_integration - Dev: Test Claude CLI integration via MCP",
        "test_claude_cli_with_file_input - Dev: Test Claude CLI with file input", 
        "test_claude_cli_comprehensive - Dev: Comprehensive test suite with multiple scenarios",
        "test_claude_cli_mcp_permissions - Dev: Test Claude CLI with MCP permissions bypass"
    ]
    
    # Build available tools list
    available_tools = core_tools[:]
    
    if dev_mode_enabled:
        available_tools.extend(dev_tools)
        tool_mode = "🔧 Development Mode (VIBE_CHECK_DEV_MODE=true)"
        tool_count = f"{len(core_tools)} core + {len(dev_tools)} dev tools"
    else:
        tool_mode = "📦 User Mode (essential tools only)"
        tool_count = f"{len(core_tools)} essential tools"
    
    return {
        "server_name": "Vibe Check MCP",
        "version": "Phase 2.2 - Testing Tools Architecture (Issue #72 ✅ COMPLETE)",
        "status": "✅ Operational",
        "tool_mode": tool_mode,
        "tool_count": tool_count,
        "architecture_improvement": {
            "issue_72_status": "✅ COMPLETE",
            "essential_diagnostics": "✅ COMPLETE - claude_cli_status, claude_cli_diagnostics",
            "environment_based_dev_tools": "✅ COMPLETE - VIBE_CHECK_DEV_MODE support", 
            "legacy_cleanup": "✅ COMPLETE - Clean tool registration architecture",
            "tool_reduction_achieved": "6 testing tools → 2 essential user diagnostics (67% reduction)"
        },
        "core_engine_status": {
            "validation_completed": True,
            "detection_accuracy": "87.5%",
            "false_positive_rate": "0%",
            "patterns_supported": 4,
            "phase_1_complete": True
        },
        "available_tools": available_tools,
        "dev_mode_instructions": {
            "enable_dev_tools": "export VIBE_CHECK_DEV_MODE=true",
            "dev_tools_location": "tests/integration/claude_cli_tests.py",
            "user_essential_tools": ["claude_cli_status", "claude_cli_diagnostics"]
        },
        "upcoming_tools": [
            "analyze_code - Code content analysis (Issue #23)", 
            "validate_integration - Integration approach validation (Issue #24)",
            "explain_pattern - Pattern education and guidance (Issue #25)"
        ],
        "anti_pattern_prevention": "✅ Successfully applied in our own development"
    }

def detect_transport_mode() -> str:
    """Auto-detect the best transport mode based on environment."""
    # Check for explicit transport override first
    transport_override = os.environ.get("MCP_TRANSPORT")
    if transport_override in ["stdio", "streamable-http"]:
        logger.info(f"Transport override found: Using '{transport_override}' from MCP_TRANSPORT env var.")
        return transport_override

    # Check if running in Docker, which strongly implies an HTTP server is needed.
    if os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER"):
        logger.info("Docker environment detected. Defaulting to 'streamable-http'.")
        return "streamable-http"
    
    # For all other cases, default to 'stdio'. This is the standard for local clients
    # like Claude Code and Cursor, which launch the MCP server as a subprocess and
    # communicate over stdin/stdout. This avoids issues where the client environment
    # is minimal and doesn't set TERM or other variables.
    logger.info("Defaulting to 'stdio' transport for local client integration.")
    return "stdio"


def run_server(transport: Optional[str] = None, host: Optional[str] = None, port: Optional[int] = None):
    """
    Start the Vibe Check MCP server with configurable transport.
    
    Args:
        transport: Override transport mode ('stdio' or 'streamable-http')
        host: Host for HTTP transport (ignored for stdio)
        port: Port for HTTP transport (ignored for stdio)
    
    Includes proper error handling and graceful startup/shutdown.
    """
    try:
        logger.info("🚀 Starting Vibe Check MCP Server...")
        
        # Configuration validation (Issue #98)
        logger.info("🔍 Validating configuration for Claude CLI and MCP integration...")
        can_start, validation_results = validate_configuration()
        
        # Log validation results
        log_validation_results(validation_results)
        
        # Check if any critical validations failed
        if not can_start:
            logger.error("❌ Critical configuration validation failed - server cannot start safely")
            print("\n" + format_validation_results(validation_results))
            sys.exit(1)
        
        # Log success
        warnings = [r for r in validation_results if not r.success and r.level.value == "warning"]
        if warnings:
            logger.warning(f"⚠️ Configuration validation completed with {len(warnings)} warnings")
        else:
            logger.info("✅ Configuration validation passed - all systems ready")
        
        # Quick engine validation
        logger.info("📊 Core detection engine: 87.5% accuracy, 0% false positives")
        logger.info("🔧 Server ready for MCP protocol connections")
        
        # Determine transport mode
        transport_mode = transport or detect_transport_mode()
        
        if transport_mode == "stdio":
            logger.info("🔗 Using stdio transport for Claude Desktop/Code integration")
            mcp.run()  # Uses stdio by default
        else:
            # HTTP transport for Docker/server deployment
            server_host = host or os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
            server_port = port or int(os.environ.get("MCP_SERVER_PORT", "8001"))
            logger.info(f"🌐 Using streamable-http transport on http://{server_host}:{server_port}/mcp")
            mcp.run(transport="streamable-http", host=server_host, port=server_port)
        
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("✅ Vibe Check MCP server shutdown complete")

def main():
    """Entry point for direct server execution with CLI argument support."""
    parser = argparse.ArgumentParser(description="Vibe Check MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "streamable-http"], 
        help="MCP transport mode (auto-detected if not specified)"
    )
    parser.add_argument(
        "--stdio", 
        action="store_const", 
        const="stdio", 
        dest="transport",
        help="Use stdio transport (shorthand for --transport stdio)"
    )
    parser.add_argument(
        "--host", 
        default=None,
        help="Host for HTTP transport (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int,
        default=None,
        help="Port for HTTP transport (default: 8001)"
    )
    
    args = parser.parse_args()
    run_server(transport=args.transport, host=args.host, port=args.port)

if __name__ == "__main__":
    main()