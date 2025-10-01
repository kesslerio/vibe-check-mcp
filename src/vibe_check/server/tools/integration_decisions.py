import logging
from typing import Dict, Any
from vibe_check.server.core import mcp
from vibe_check.tools.integration_decision_check import check_official_alternatives, analyze_integration_text, ValidationError, SCORING
from vibe_check.tools.integration_pattern_analysis import (
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
    Official alternative check for integration decisions.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
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
    Analyze text for integration decision anti-patterns.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
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
    Integration decision framework with systematic evaluation.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
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
    Enhanced integration research with real-time web search.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
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
    Fast integration pattern detection for vibe coding safety net.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
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
    Ultra-fast technology scan for immediate feedback.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
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
    Integration effort-complexity analysis.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
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
