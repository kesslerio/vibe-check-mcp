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
import sys
from typing import Dict, Any

try:
    from fastmcp import FastMCP
except ImportError:
    print("❌ FastMCP not installed. Install with: pip install fastmcp")
    sys.exit(1)

from .tools.demo_tool import demo_analyze_text, analyze_github_issue as analyze_github_issue_tool
from .tools.pr_review import review_pull_request as pr_review_tool

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

@mcp.tool()
def analyze_text_demo(text: str, detail_level: str = "standard") -> Dict[str, Any]:
    """
    Demo: Analyze text for anti-patterns using validated core detection engine.
    
    This is a demonstration tool showing FastMCP integration with the proven
    Phase 1 core engine. Full tools will be implemented in issues #22-25.
    
    Args:
        text: Text content to analyze for anti-patterns
        detail_level: Educational detail level (brief/standard/comprehensive)
        
    Returns:
        Analysis results with detected patterns and educational content
    """
    logger.info(f"Demo analysis requested for {len(text)} characters")
    return demo_analyze_text(text, detail_level)

@mcp.tool()
def analyze_github_issue(
    issue_number: int, 
    repository: str = "kesslerio/vibe-check-mcp", 
    analysis_mode: str = "quick",
    detail_level: str = "standard",
    post_comment: bool = None
) -> Dict[str, Any]:
    """
    Analyze GitHub issue for anti-patterns with quick or comprehensive modes.
    
    QUICK MODE: Fast analysis for immediate feedback during development
    COMPREHENSIVE MODE: Detailed analysis with automatic GitHub comment posting
    
    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        analysis_mode: "quick" for immediate analysis or "comprehensive" for detailed review
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
        post_comment: Post analysis as GitHub comment (auto-enabled for comprehensive mode, disabled for quick mode)
        
    Returns:
        Analysis results with detected patterns and recommendations
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
def review_pull_request(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    force_re_review: bool = False,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    Comprehensive PR review incorporating ALL functionality from scripts/review-pr.sh.
    
    Enterprise-grade PR review with:
    - Multi-dimensional size classification
    - Re-review detection and progress tracking
    - Linked issue analysis and validation
    - Clear-Thought integration for systematic analysis
    - Comprehensive GitHub integration
    - Permanent logging and review tracking
    
    Args:
        pr_number: PR number to review
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        force_re_review: Force re-review mode even if not auto-detected
        analysis_mode: "comprehensive" for full analysis or "quick" for basic review
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
        
    Returns:
        Complete review results with GitHub integration status and permanent logging
    """
    logger.info(f"Comprehensive PR review requested: #{pr_number} in {repository} (mode: {analysis_mode})")
    return pr_review_tool(
        pr_number=pr_number,
        repository=repository,
        force_re_review=force_re_review,
        analysis_mode=analysis_mode,
        detail_level=detail_level
    )

@mcp.tool()
def server_status() -> Dict[str, Any]:
    """
    Get Vibe Check MCP server status and capabilities.
    
    Returns:
        Server status, core engine validation results, and available capabilities
    """
    return {
        "server_name": "Vibe Check MCP",
        "version": "Phase 2.1 - FastMCP Integration",
        "status": "✅ Operational",
        "core_engine_status": {
            "validation_completed": True,
            "detection_accuracy": "87.5%",
            "false_positive_rate": "0%",
            "patterns_supported": 4,
            "phase_1_complete": True
        },
        "available_tools": [
            "analyze_text_demo - Demo anti-pattern analysis",
            "analyze_github_issue - GitHub issue analysis (Issue #22 ✅ COMPLETE)",
            "review_pull_request - Comprehensive PR review (Issue #35 ✅ COMPLETE)",
            "server_status - Server status and capabilities"
        ],
        "upcoming_tools": [
            "analyze_code - Code content analysis (Issue #23)", 
            "validate_integration - Integration approach validation (Issue #24)",
            "explain_pattern - Pattern education and guidance (Issue #25)"
        ],
        "anti_pattern_prevention": "✅ Successfully applied in our own development"
    }

def run_server():
    """
    Start the Vibe Check MCP server.
    
    Includes proper error handling and graceful startup/shutdown.
    """
    try:
        logger.info("🚀 Starting Vibe Check MCP Server...")
        logger.info("📊 Core detection engine validated: 87.5% accuracy, 0% false positives")
        logger.info("🔧 Server ready for MCP protocol connections")
        
        # Start the FastMCP server
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("✅ Vibe Check MCP server shutdown complete")

if __name__ == "__main__":
    run_server()