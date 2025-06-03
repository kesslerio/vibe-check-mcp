#!/bin/bash
# Vibe Check CLI Helper - Safe On-Demand Usage
# Prevents recursion by temporarily adding/removing vibe-check from MCP config

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "Commands:"
    echo "  enable    - Add vibe-check to MCP config"
    echo "  disable   - Remove vibe-check from MCP config"
    echo "  status    - Check if vibe-check is enabled"
    echo "  safe-run  - Run vibe-check tool safely (auto enable/disable)"
    echo ""
    echo "Examples:"
    echo "  $0 enable"
    echo "  $0 safe-run analyze_github_issue_llm 95"
    echo "  $0 disable"
}

enable_vibe_check() {
    echo -e "${YELLOW}🔧 Adding vibe-check to MCP config...${NC}"
    
    cd "$PROJECT_DIR"
    claude mcp add-json vibe-check '{
        "type": "stdio",
        "command": "'"$PROJECT_DIR/clean_env/bin/python"'",
        "args": ["-m", "vibe_check.server"],
        "env": {
            "PYTHONPATH": "'"$PROJECT_DIR/src"'",
            "GITHUB_TOKEN": "'"${GITHUB_TOKEN:-}"'"
        }
    }' -s user 2>/dev/null || true
    
    echo -e "${GREEN}✅ Vibe-check enabled${NC}"
}

disable_vibe_check() {
    echo -e "${YELLOW}🔧 Removing vibe-check from MCP config...${NC}"
    
    cd "$PROJECT_DIR"
    claude mcp remove vibe-check 2>/dev/null || true
    
    echo -e "${GREEN}✅ Vibe-check disabled (recursion prevention active)${NC}"
}

check_status() {
    cd "$PROJECT_DIR"
    if claude mcp list | grep -q "vibe-check:"; then
        echo -e "${YELLOW}⚠️  Vibe-check is ENABLED (recursion risk)${NC}"
        return 0
    else
        echo -e "${GREEN}✅ Vibe-check is DISABLED (safe)${NC}"
        return 1
    fi
}

safe_run() {
    local tool_name="$1"
    shift
    local args="$@"
    
    echo -e "${GREEN}🚀 Safe vibe-check execution starting...${NC}"
    
    # Enable vibe-check
    enable_vibe_check
    
    # Run the tool
    echo -e "${YELLOW}▶️  Running: $tool_name $args${NC}"
    
    # Use Claude CLI to run the vibe-check tool
    cd "$PROJECT_DIR"
    claude -p "Use the $tool_name tool with these parameters: $args" || {
        echo -e "${RED}❌ Tool execution failed${NC}"
    }
    
    # Always disable after use
    disable_vibe_check
    
    echo -e "${GREEN}🏁 Safe execution completed${NC}"
}

case "${1:-}" in
    enable)
        enable_vibe_check
        ;;
    disable)
        disable_vibe_check
        ;;
    status)
        check_status
        ;;
    safe-run)
        if [ $# -lt 2 ]; then
            echo -e "${RED}Error: safe-run requires tool name and parameters${NC}"
            usage
            exit 1
        fi
        shift
        safe_run "$@"
        ;;
    *)
        usage
        exit 1
        ;;
esac