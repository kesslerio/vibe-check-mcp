import logging
from typing import Dict, Any
from ..core import mcp
from ...tools.integration_decision_check import check_official_alternatives, analyze_integration_text, ValidationError, SCORING
from ...tools.integration_pattern_analysis import (
    analyze_integration_patterns_fast, 
    quick_technology_scan, 
    analyze_effort_complexity,
    enhance_text_analysis_with_integration_patterns
)

logger = logging.getLogger(__name__)

def register_integration_decision_tools(mcp_instance):
    """Registers integration decision tools with the MCP server."""
    mcp_instance.add_tool(check_integration_alternatives)
    mcp_instance.add_tool(analyze_integration_decision_text)
    mcp_instance.add_tool(integration_decision_framework)
    mcp_instance.add_tool(integration_research_with_websearch)
    mcp_instance.add_tool(analyze_integration_patterns)
    mcp_instance.add_tool(quick_tech_scan)
    mcp_instance.add_tool(analyze_integration_effort)

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
            from ...tools.web_search_integration import search_technology_documentation
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
