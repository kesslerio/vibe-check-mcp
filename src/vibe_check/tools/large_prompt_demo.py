"""
Large Prompt Demo Tool

Demonstrates the Zen-style large prompt handling approach.
Serves as a proof of concept for issue #164.
"""

import logging
from typing import Dict, Any, Optional, List

from .large_prompt_handler import handle_large_prompt

logger = logging.getLogger(__name__)


def demo_large_prompt_analysis(
    content: str, files: Optional[List[str]] = None, detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    Demo tool showing large prompt handling in action.

    This tool demonstrates the Zen-style approach:
    1. Check if content is too large (>50K chars)
    2. If so, ask Claude to save to file and resubmit
    3. If files provided, read from them
    4. Process the content normally

    Args:
        content: The content to analyze
        files: Optional list of file paths from Claude
        detail_level: Analysis detail level

    Returns:
        Analysis result or file mode instructions
    """
    try:
        # Use the simple large prompt handler
        result = handle_large_prompt(content, files)

        if result["status"] == "prompt_too_large":
            # Return instructions for file mode
            return {
                "success": True,
                "mode": "file_mode_requested",
                "message": result["message"],
                "instructions": result["instructions"],
                "character_count": result["character_count"],
                "limit": result["limit"],
                "analysis": "⚠️ Content too large - please save to file and resubmit",
                "next_steps": [
                    "Save your content to a temporary file (e.g., /tmp/prompt.txt)",
                    "Re-run this tool with the file path included",
                    "The analysis will then process the full content",
                ],
            }

        elif result["status"] == "file_mode_success":
            # Process content from file
            file_content = result["content"]
            return {
                "success": True,
                "mode": "file_mode_processing",
                "source_file": result["source"],
                "character_count": result["character_count"],
                "analysis": f"✅ Successfully loaded {result['character_count']:,} characters from file",
                "content_preview": (
                    file_content[:500] + "..."
                    if len(file_content) > 500
                    else file_content
                ),
                "demo_result": "This would normally be processed by your analysis logic",
                "zen_style_benefits": [
                    "No complex token counting needed",
                    "Claude handles the file operations",
                    "Simple character-based thresholds work great",
                    "Minimal code complexity",
                ],
            }

        else:
            # Normal processing for small content
            return {
                "success": True,
                "mode": "normal_processing",
                "character_count": result["character_count"],
                "analysis": f"✅ Processing {result['character_count']:,} character content normally",
                "content_preview": (
                    content[:200] + "..." if len(content) > 200 else content
                ),
                "demo_result": "This would be your normal analysis logic for smaller content",
            }

    except Exception as e:
        logger.error(f"Large prompt demo failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "analysis": "❌ Demo failed - check logs for details",
        }
