#!/bin/bash
set -e

# Vibe Check MCP - Claude Code Integration Setup
# Usage: ./scripts/setup-claude-code.sh

echo "🔗 Vibe Check MCP - Claude Code Integration Setup"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get project directory
get_project_dir() {
    # Try to find project root by looking for src/vibe_check
    local current_dir="$(pwd)"
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_dir="$(dirname "$script_dir")"
    
    if [ -d "$project_dir/src/vibe_check" ]; then
        echo "$project_dir"
    elif [ -d "$current_dir/src/vibe_check" ]; then
        echo "$current_dir"
    else
        log_error "Could not find vibe-check project directory"
        log_info "Please run this script from the vibe-check-mcp directory"
        exit 1
    fi
}

# Detect Python command
detect_python() {
    if command_exists python3; then
        echo "python3"
    elif command_exists python; then
        echo "python"
    else
        log_error "Python not found"
        exit 1
    fi
}

# Setup Claude Code integration
setup_claude_code() {
    local project_dir="$1"
    local python_cmd="$2"
    
    log_info "Configuring Claude Code MCP integration..."
    
    # Check if Claude CLI is available
    if ! command_exists claude; then
        log_error "Claude CLI not found"
        log_info "Please install Claude CLI first: https://docs.anthropic.com/en/docs/claude-cli"
        exit 1
    fi
    
    log_success "Claude CLI found"
    
    # Create MCP configuration
    local config_json=$(cat <<EOF
{
  "type": "stdio",
  "command": "$python_cmd",
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "$project_dir/src"
  }
}
EOF
)
    
    log_info "Adding vibe-check MCP server to Claude Code..."
    
    # Add MCP server (remove existing first if it exists)
    claude mcp remove vibe-check -s user 2>/dev/null || true
    
    if echo "$config_json" | claude mcp add-json vibe-check --stdin -s user; then
        log_success "MCP server added successfully"
    else
        log_error "Failed to add MCP server"
        exit 1
    fi
}

# Test the integration
test_integration() {
    log_info "Testing Claude Code integration..."
    
    # List MCP servers to verify installation
    if claude mcp list | grep -q "vibe-check"; then
        log_success "vibe-check MCP server found in Claude Code configuration"
    else
        log_warning "vibe-check MCP server not found in configuration"
        return 1
    fi
    
    # Test server status
    log_info "Testing server connection..."
    if claude mcp call vibe-check server_status >/dev/null 2>&1; then
        log_success "MCP server connection test successful"
    else
        log_warning "MCP server connection test failed"
        log_info "This may be normal if the server isn't running"
    fi
}

# Show usage examples
show_usage_examples() {
    echo ""
    echo "🎉 Claude Code Integration Complete!"
    echo "===================================="
    echo ""
    echo "🚀 Usage Examples:"
    echo ""
    echo "1. Quick vibe check on text:"
    echo "   claude \"vibe check this code for anti-patterns: def process(): return fetch() and parse()\""
    echo ""
    echo "2. Analyze GitHub issue:"
    echo "   claude \"analyze issue #42 in my repo for engineering anti-patterns\""
    echo ""
    echo "3. Comprehensive PR review:"
    echo "   claude \"review PR #123 with comprehensive anti-pattern analysis\""
    echo ""
    echo "4. Check server status:"
    echo "   claude mcp call vibe-check server_status"
    echo ""
    echo "📋 Available Tools:"
    echo "- analyze_github_issue - GitHub issue vibe check with anti-pattern detection"
    echo "- analyze_text_demo - Quick anti-pattern analysis on any text"
    echo "- analyze_github_pr_llm - Comprehensive PR analysis with Claude CLI"
    echo "- analyze_code_llm - Deep code analysis with anti-pattern detection"
    echo "- server_status - Check server capabilities and status"
    echo ""
    echo "📖 For more examples, see: https://github.com/kesslerio/vibe-check-mcp#usage-examples"
    echo ""
    echo "✨ Happy vibe checking with Claude Code!"
}

# Main setup flow
main() {
    echo ""
    log_info "Starting Claude Code integration setup..."
    echo ""
    
    # Get project directory and Python command
    local project_dir=$(get_project_dir)
    local python_cmd=$(detect_python)
    
    log_info "Project directory: $project_dir"
    log_info "Python command: $python_cmd"
    echo ""
    
    # Setup integration
    setup_claude_code "$project_dir" "$python_cmd"
    echo ""
    
    # Test integration
    test_integration
    echo ""
    
    # Show usage examples
    show_usage_examples
}

# Run main function
main "$@"