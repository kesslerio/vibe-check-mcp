import sys
print(f"DEBUG SYS.PATH: {sys.path}")

import asyncio
import json
import logging
from fastmcp import FastMCP, McpTool, McpToolContext, McpToolSchema

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ClaudeAutoPermissionTool")

class AutoApproveToolInput(McpToolSchema):
    tool_name: str
    input: dict # Passthrough for the original tool's input

class AutoApproveTool(McpTool[AutoApproveToolInput, dict]):
    name = "approve" # Will be prefixed by server's prefix
    description = "Automatically approves any tool permission request from the Claude CLI."
    schema = AutoApproveToolInput

    async def run(self, ctx: McpToolContext, params: AutoApproveToolInput) -> dict:
        logger.info(f"Auto-approving tool: {params.tool_name} with input: {params.input}")
        approval_response = {
            "behavior": "allow",
            "updatedInput": params.input  # Pass back the original input
        }
        # The Claude CLI --permission-prompt-tool expects the MCP tool to return
        # a JSON-stringified payload of the approval_response structure.
        # FastMCP will automatically JSON-serialize the dictionary returned by this run method.
        # So, we should return the approval_response dictionary directly.
        return approval_response

async def run_server():
    mcp = FastMCP(
        title="Claude Auto Permission MCP Server",
        description="Provides a tool to automatically approve Claude CLI tool permissions.",
        prefix="claude_permission_server", # Changed prefix
        host="127.0.0.1",
        port=39999  # Using a distinct port
    )
    mcp.add_tool(AutoApproveTool())
    logger.info("Starting Claude Auto Permission MCP Server on port 39999...")
    await mcp.serve()

if __name__ == "__main__":
    # This script will now run as a standalone MCP server for the permission tool.
    # The claude CLI will be configured to talk to this server for permissions.
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Claude Auto Permission MCP Server stopped.") 