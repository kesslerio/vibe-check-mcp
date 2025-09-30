#!/usr/bin/env python3
"""
Token counting script for MCP tool schemas.

Uses tiktoken to accurately count tokens in all tool definitions,
helping ensure we stay within budget and prevent token bloat.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import tiktoken
except ImportError:
    print("ERROR: tiktoken not installed. Run: pip install tiktoken")
    sys.exit(1)


def count_tool_tokens():
    """Count tokens in all MCP tool schemas."""

    # Import after path is set
    from vibe_check.server.core import mcp
    from vibe_check.server.registry import register_all_tools

    # Register all tools
    register_all_tools(mcp)

    # Get tiktoken encoder - use cl100k_base which is similar to Claude's tokenizer
    enc = tiktoken.get_encoding("cl100k_base")

    # Collect tool information
    tools_data = []
    total_tokens = 0

    # Get all registered tools from FastMCP
    if hasattr(mcp, '_tool_manager') and hasattr(mcp._tool_manager, '_tools'):
        tools = mcp._tool_manager._tools

        for tool_name, tool_info in tools.items():
            # Serialize tool to JSON (this is what gets sent over MCP)
            tool_schema = {
                "name": tool_name,
                "description": getattr(tool_info, "description", ""),
                "inputSchema": getattr(tool_info, "input_schema", {})
            }

            # Convert to string and count tokens
            tool_json = json.dumps(tool_schema, separators=(',', ':'), default=str)
            token_count = len(enc.encode(tool_json))

            tools_data.append({
                "name": tool_name,
                "tokens": token_count
            })
            total_tokens += token_count

    # Sort by token count (descending)
    tools_data.sort(key=lambda x: x["tokens"], reverse=True)

    # Print results
    print("=" * 80)
    print("MCP Tool Token Count Report")
    print("=" * 80)
    print(f"\nTotal tools: {len(tools_data)}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Average tokens per tool: {total_tokens // len(tools_data) if tools_data else 0}")
    print(f"\n{'Tool Name':<50} {'Tokens':>10}")
    print("-" * 80)

    for tool in tools_data:
        print(f"{tool['name']:<50} {tool['tokens']:>10}")

    print("=" * 80)

    # Check against targets (configurable via environment variables)
    target = int(os.environ.get("TOKEN_TARGET", "10000"))
    buffer_target = int(os.environ.get("TOKEN_BUFFER_TARGET", "12000"))

    if total_tokens <= target:
        print(f"✅ SUCCESS: Within target of {target:,} tokens")
    elif total_tokens <= buffer_target:
        print(f"⚠️  WARNING: Exceeds target ({target:,}) but within buffer ({buffer_target:,})")
    else:
        print(f"❌ FAILURE: Exceeds buffer target of {buffer_target:,} tokens")
        sys.exit(1)

    return total_tokens


if __name__ == "__main__":
    try:
        count_tool_tokens()
    except Exception as e:
        print(f"Error counting tokens: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
