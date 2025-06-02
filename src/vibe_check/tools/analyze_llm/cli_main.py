"""
CLI Main Interface for LLM Analysis Tools

Command-line interface for external Claude CLI execution and analysis tools.
Provides standalone execution capability for LLM analysis functionality.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from ..shared.claude_integration import ClaudeCliExecutor, ClaudeCliResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for external Claude CLI execution."""
    parser = argparse.ArgumentParser(
        description="External Claude CLI executor for MCP tools"
    )
    parser.add_argument(
        "--prompt", "-p",
        help="Direct prompt to send to Claude CLI"
    )
    parser.add_argument(
        "--input-file", "-f",
        help="File to analyze with Claude CLI"
    )
    parser.add_argument(
        "--task-type", "-t",
        choices=["pr_review", "code_analysis", "issue_analysis", "general"],
        default="general",
        help="Type of analysis task"
    )
    parser.add_argument(
        "--timeout", "-T",
        type=int,
        default=60,
        help="Timeout in seconds (default: 60)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for results (JSON format)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--mcp-config",
        help="Path to MCP configuration file"
    )
    parser.add_argument(
        "--permission-prompt-tool",
        help="Name of the permission tool for auto-approval"
    )
    parser.add_argument(
        "--allowedTools",
        help="Comma-separated list of allowed tools (or '*' for all)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not args.prompt and not args.input_file:
        parser.error("Either --prompt or --input-file must be specified")
    
    # Initialize executor
    executor = ClaudeCliExecutor(timeout_seconds=args.timeout)
    
    # Execute based on input type
    if args.input_file:
        # Read file and analyze
        try:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Build prompt with context and content
            prompt_parts = [f"File: {args.input_file}", f"Content to analyze:\\n{content}"]
            prompt = "\\n\\n".join(prompt_parts)
            
            result = await executor.execute_async(
                prompt=prompt,
                task_type=args.task_type
            )
        except Exception as e:
            result = ClaudeCliResult(
                success=False,
                error=f"Error reading file {args.input_file}: {str(e)}",
                exit_code=1,
                task_type=args.task_type
            )
    else:
        result = await executor.execute_async(
            prompt=args.prompt,
            task_type=args.task_type
        )
    
    # Output results
    result_dict = result.to_dict()
    
    if args.output:
        # Write to file
        with open(args.output, 'w') as f:
            json.dump(result_dict, f, indent=2)
        logger.info(f"Results written to {args.output}")
    else:
        # Print to stdout
        print(json.dumps(result_dict, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    asyncio.run(main())