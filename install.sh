#!/bin/bash
set -e

# Vibe Check MCP - One-Command Installation Script
# Usage: curl -fsSL https://raw.githubusercontent.com/kesslerio/vibe-check-mcp/main/install.sh | bash

echo "🎯 Vibe Check MCP Installation Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/kesslerio/vibe-check-mcp.git"
INSTALL_DIR="$HOME/.vibe-check-mcp"
PYTHON_MIN_VERSION="3.8"

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

# Check Python version
check_python() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        log_error "Python not found. Please install Python 3.8+ first."
        exit 1
    fi
    
    local python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    local required_version="$PYTHON_MIN_VERSION"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
        log_success "Python $python_version found"
        return 0
    else
        log_error "Python $python_version found, but $PYTHON_MIN_VERSION+ required"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    check_python
    
    # Check pip
    if ! command_exists pip3 && ! command_exists pip; then
        log_error "pip not found. Please install pip first."
        exit 1
    fi
    log_success "pip found"
    
    # Check git
    if ! command_exists git; then
        log_error "git not found. Please install git first."
        exit 1
    fi
    log_success "git found"
    
    # Check Claude CLI (optional)
    if command_exists claude; then
        log_success "Claude CLI found - enhanced analysis features will be available"
    else
        log_warning "Claude CLI not found - install later for enhanced analysis features"
        log_info "Claude CLI installation: https://docs.anthropic.com/en/docs/claude-cli"
    fi
}

# Install vibe-check-mcp
install_vibe_check() {
    log_info "Installing Vibe Check MCP..."
    
    # Remove existing installation
    if [ -d "$INSTALL_DIR" ]; then
        log_info "Removing existing installation..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Clone repository
    log_info "Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    if command_exists pip3; then
        pip3 install -r requirements.txt
    else
        pip install -r requirements.txt
    fi
    
    log_success "Vibe Check MCP installed successfully"
}

# Setup Claude Code integration
setup_claude_code() {
    log_info "Setting up Claude Code integration..."
    
    if ! command_exists claude; then
        log_warning "Claude CLI not found - skipping Claude Code integration"
        log_info "Install Claude CLI later and run: $INSTALL_DIR/scripts/setup-claude-code.sh"
        return
    fi
    
    # Add MCP server to Claude Code
    local config_json=$(cat <<EOF
{
  "type": "stdio",
  "command": "$PYTHON_CMD",
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "$INSTALL_DIR/src"
  }
}
EOF
)
    
    log_info "Adding vibe-check MCP server to Claude Code..."
    echo "$config_json" | claude mcp add-json vibe-check --stdin -s user
    
    if [ $? -eq 0 ]; then
        log_success "Claude Code integration configured"
    else
        log_warning "Claude Code integration failed - you can set it up manually later"
    fi
}

# Create convenience scripts
create_scripts() {
    log_info "Creating convenience scripts..."
    
    # Create CLI wrapper script
    local cli_script="$HOME/.local/bin/vibe-check"
    mkdir -p "$(dirname "$cli_script")"
    
    cat > "$cli_script" << EOF
#!/bin/bash
# Vibe Check MCP CLI Wrapper
cd "$INSTALL_DIR"
PYTHONPATH="$INSTALL_DIR/src" $PYTHON_CMD -m vibe_check.cli "\$@"
EOF
    chmod +x "$cli_script"
    
    # Create CLAUDE.md sample
    if [ ! -f "CLAUDE.md" ] && [ -f "$INSTALL_DIR/CLAUDE.md.sample" ]; then
        log_info "Creating sample CLAUDE.md in current directory..."
        cp "$INSTALL_DIR/CLAUDE.md.sample" ./CLAUDE.md.sample
        log_info "Customize ./CLAUDE.md.sample and rename to CLAUDE.md for your project"
    fi
    
    log_success "Convenience scripts created"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    cd "$INSTALL_DIR"
    if PYTHONPATH="$INSTALL_DIR/src" $PYTHON_CMD -c "from vibe_check.server import run_server; print('✅ Installation verified')"; then
        log_success "Installation verification successful"
    else
        log_error "Installation verification failed"
        exit 1
    fi
}

# Show next steps
show_next_steps() {
    echo ""
    echo "🎉 Installation Complete!"
    echo "======================="
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. 🔧 Test the installation:"
    echo "   cd $INSTALL_DIR && PYTHONPATH=src python -m vibe_check.server --help"
    echo ""
    
    if command_exists claude; then
        echo "2. ✅ Claude Code integration is ready!"
        echo "   Try: claude \"vibe check this issue for anti-patterns\""
        echo ""
    else
        echo "2. 📥 Install Claude CLI for enhanced features:"
        echo "   https://docs.anthropic.com/en/docs/claude-cli"
        echo "   Then run: $INSTALL_DIR/scripts/setup-claude-code.sh"
        echo ""
    fi
    
    echo "3. 📝 Customize CLAUDE.md for your project:"
    echo "   cp $INSTALL_DIR/CLAUDE.md.sample ./CLAUDE.md"
    echo "   # Edit CLAUDE.md with your project's engineering guidelines"
    echo ""
    
    echo "4. 🚀 Start using vibe-check tools:"
    echo "   # Quick vibe check on GitHub issue"
    echo "   # Comprehensive PR analysis with anti-pattern detection"
    echo "   # Code quality assessment with engineering guidance"
    echo ""
    
    echo "📖 Documentation: https://github.com/kesslerio/vibe-check-mcp"
    echo "🐛 Issues: https://github.com/kesslerio/vibe-check-mcp/issues"
    echo ""
    echo "✨ Happy vibe checking!"
}

# Main installation flow
main() {
    echo ""
    log_info "Starting Vibe Check MCP installation..."
    echo ""
    
    check_prerequisites
    echo ""
    
    install_vibe_check
    echo ""
    
    setup_claude_code
    echo ""
    
    create_scripts
    echo ""
    
    verify_installation
    echo ""
    
    show_next_steps
}

# Run main function
main "$@"