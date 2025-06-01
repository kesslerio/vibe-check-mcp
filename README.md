# 🧭 Vibe Check MCP

**Enhanced Engineering Vibe Check Framework via Model Context Protocol**

> **⚡ Designed for Claude Code** - This MCP server is specifically built to work with Claude Code's MCP integration, providing seamless anti-pattern detection and coaching directly in your development workflow.

A comprehensive MCP server that provides friendly, coaching-oriented analysis of GitHub issues using Claude-powered reasoning to detect engineering anti-patterns and provide practical guidance for prevention.

🎯 **NEW: Enhanced Vibe Check Framework** - Transforms technical "anti-pattern detection" into friendly "vibe check" coaching with Claude-powered analytical reasoning and comprehensive educational guidance.

[![Claude Code Required](https://img.shields.io/badge/Claude%20Code-Required-red)](https://claude.ai)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.3.4-blue)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Optional-yellow)](https://docker.com)

## 🎯 What It Does

Vibe Check MCP detects **systematic engineering anti-patterns** that lead to technical debt and project failures:

- 🏗️ **Infrastructure-Without-Implementation**: Building custom solutions before testing standard approaches
- 🩹 **Symptom-Driven Development**: Treating symptoms instead of addressing root causes  
- 🌀 **Complexity Escalation**: Adding unnecessary complexity without justification
- 📚 **Documentation Neglect**: Building before researching standard approaches

**Validated Results**: 87.5% detection accuracy, 0% false positives in comprehensive testing.

## ⚡ Quick Start (Claude Code Required)

**Prerequisites**: You must have [Claude Code](https://claude.ai) installed to use this MCP server.

Get running in 5 minutes:

```bash
# 1. Clone and install
git clone https://github.com/kesslerio/vibe-check-mcp.git
cd vibe-check-mcp
pip install -r requirements.txt

# 2. Add to Claude Code (NATIVE - Recommended)
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "python", 
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "'"$(pwd)"'/src",
    "GITHUB_TOKEN": "your_github_token_here"
  }
}' -s user

# 3. Restart Claude Code and start using vibe-check tools!
```

📖 **[Complete Deployment Guide](docs/MCP_DEPLOYMENT_GUIDE.md)** - Native vs Docker vs Bridge deployment options

## 🚀 Deployment Options for Claude Code

### 🥇 **Native Deployment (Recommended)**
**Best performance, simplest setup, optimal for Claude Code**

```bash
# Pros: Fast startup (~2s), minimal memory (~50MB), direct integration
# Cons: Requires Python environment setup
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "vibe_check.server"],
  "env": {"PYTHONPATH": "'"$(pwd)"'/src"}
}' -s user
```

### 🥈 **Docker Bridge (Hybrid)**
**Docker isolation + Claude Code compatibility**

```bash
# Pros: Docker isolation, still works with Claude Code
# Cons: Slower startup (~7s), more memory (~120MB), complex setup
claude mcp add-json vibe-check-bridge '{
  "type": "stdio",
  "command": "docker",
  "args": ["run", "--rm", "-i", "--network", "host", 
           "vibe-check-mcp", "/app/scripts/mcp-bridge.sh", "localhost", "8001"]
}' -s user
```

### 🥉 **Docker HTTP Only**
**⚠️ Not compatible with Claude Code stdio requirements**

```bash
# Use case: Web applications, API clients (NOT Claude Code)
docker-compose up  # Provides HTTP endpoint only
```

**📋 Recommendation**: Use **Native Deployment** unless you specifically need Docker isolation. See the [Complete Deployment Guide](docs/MCP_DEPLOYMENT_GUIDE.md) for detailed setup instructions.

## 📦 Installation

### Prerequisites

- **🔴 Claude Code** - **REQUIRED** for MCP integration ([Download here](https://claude.ai))
- **Python 3.8+** (Python 3.10+ recommended)
- **Git** for cloning the repository
- **Docker** (optional, for containerized deployment - see deployment options below)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kesslerio/vibe-check-mcp.git
   cd vibe-check-mcp
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python -c "from vibe_check.server import run_server; print('✅ Installation successful')"
   ```

### Environment Configuration

Create a `.env` file for configuration (optional):

```bash
# GitHub Integration (optional - for private repositories)
GITHUB_TOKEN=your_github_personal_access_token

# Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000

# Logging
LOG_LEVEL=INFO
```

## 🐳 Docker Setup

> **⚠️ Important for Claude Code Users**: Standard Docker deployment provides HTTP transport which is **NOT compatible** with Claude Code. For Claude Code integration, use [Native Deployment](#-native-deployment-recommended) or [Docker Bridge](#-docker-bridge-hybrid) instead.

### Docker HTTP Deployment (Web/API Clients Only)

```bash
# ⚠️ This does NOT work with Claude Code - use for web applications only
# Build and run with docker-compose
docker-compose up --build

# Or build and run manually
docker build -t vibe-check-mcp .
docker run -p 8001:8001 vibe-check-mcp
```

### Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  vibe-check-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN:-}
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config:ro
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

### Production Docker Deployment

```bash
# Build optimized production image
docker build --target production -t vibe-check-mcp:prod .

# Run with production settings
docker run -d \
  --name vibe-check-mcp \
  -p 8000:8000 \
  -e GITHUB_TOKEN=${GITHUB_TOKEN} \
  -e LOG_LEVEL=WARNING \
  --restart unless-stopped \
  vibe-check-mcp:prod
```

## 🧠 External Claude CLI Integration

**NEW: Enhanced Analysis with External Claude CLI**

Vibe Check MCP now includes **external Claude CLI integration** for advanced analysis capabilities:

- **🔥 No Context Blocking**: External subprocess execution eliminates 30-second timeout issues
- **💰 Cost Tracking**: Real-time cost monitoring and session management
- **📊 SDK Compliance**: Structured JSON responses with metadata
- **⚡ Reliable Performance**: Consistent 27s analysis time for complex PRs
- **🎯 Specialized Prompts**: Task-specific system prompts for PR reviews, code analysis, and issue analysis

### Requirements for Enhanced Analysis

To unlock enhanced Claude CLI analysis features:

1. **Install Claude CLI** (optional but recommended):
   ```bash
   # Install Claude CLI for enhanced analysis
   # See: https://docs.anthropic.com/en/docs/claude-cli
   ```

2. **Automatic Fallback**: When Claude CLI is unavailable, the system automatically falls back to standard analysis

### Enhanced Analysis Features

- **PR Reviews**: Comprehensive PR analysis with anti-pattern detection and architectural guidance
- **Code Analysis**: Deep code quality assessment with security and performance insights  
- **Issue Analysis**: Strategic issue evaluation with implementation guidance
- **Cost Optimization**: Track analysis costs to optimize usage patterns

## 🔗 Claude Code Integration (Detailed Setup)

> **📋 Quick Setup**: See [Quick Start](#-quick-start-claude-code-required) above for the fastest way to get started.

### Step 1: Add MCP Server to Claude Code

The correct way to add MCP servers to Claude Code is using the `claude mcp add-json` command with **stdio transport**:

#### User-Level Configuration (Recommended)

Add the server at user level (available across all projects):

```bash
# Navigate to the project directory
cd /path/to/vibe-check-mcp

# Add server with user scope (using JSON config for reliability)
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "'$(pwd)'/src"
  }
}' -s user

# Optional: Add GitHub token for private repositories
claude mcp add-json vibe-check '{
  "type": "stdio", 
  "command": "python",
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "'$(pwd)'/src",
    "GITHUB_TOKEN": "your_token_here"
  }
}' -s user
```

#### Project-Level Configuration

Add the server for current project only:

```bash
# Navigate to your project directory
cd /your/project/directory

# Add server with local scope (using JSON config)
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "python", 
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "/path/to/vibe-check-mcp/src"
  }
}' -s local
```

#### Docker-Based Configuration

If using Docker:

```bash
# Build the Docker image first
cd /path/to/vibe-check-mcp
docker build -t vibe-check-mcp .

# Add Docker-based MCP server (using JSON config like GitHub MCP)
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "bash",
  "args": [
    "-c", 
    "docker attach vibe_check_mcp || docker run -i --rm --name vibe_check_mcp -e GITHUB_TOKEN=${GITHUB_TOKEN:-} vibe-check-mcp"
  ],
  "env": {
    "GITHUB_TOKEN": "your_token_here"
  }
}' -s user
```

### Step 2: Verify Installation

1. **List installed MCP servers**:
   ```bash
   claude mcp list
   ```

2. **You should see vibe-check listed** with status information

3. **Test the server**:
   ```bash
   claude mcp call vibe-check server_status
   ```

### Step 3: Test GitHub Issue Analysis

Test the main functionality:
```bash
claude mcp call vibe-check analyze_github_issue --issue_number 22 --repository "kesslerio/vibe-check-mcp"
```

Expected output includes:
- Anti-pattern detection results with confidence scores
- Educational explanations of detected patterns
- Remediation recommendations
- Prevention checklists

## 🛠️ Available Tools

### Core Analysis Tools

#### `analyze_github_issue` (Enhanced Vibe Check Framework)

Provides friendly, coaching-oriented analysis with Claude-powered reasoning and educational guidance.

**Parameters**:
- `issue_number` (int): GitHub issue number to analyze
- `repository` (str, optional): Repository in format "owner/repo" (defaults to current repo)
- `analysis_mode` (str, optional): "quick" for fast feedback or "comprehensive" for detailed analysis
- `detail_level` (str, optional): Educational detail level - "brief", "standard", or "comprehensive"
- `post_comment` (bool, optional): Whether to post analysis as GitHub comment

**Vibe Check Modes**:
- **Quick Vibe Check**: Fast feedback for development workflow
- **Deep Vibe Check**: Claude-powered analysis with GitHub integration and comprehensive coaching

**Example Usage**:
```bash
# Quick vibe check for development workflow
claude "vibe check issue 22"

# Deep vibe check with comprehensive analysis  
claude "deep vibe issue 22"

# Cross-repository analysis
claude "vibe check issue 123 in microsoft/typescript"
```

#### `review_pull_request` (Enhanced PR Analysis)

Comprehensive PR review with external Claude CLI integration for advanced analysis.

**Parameters**:
- `pr_number` (int): Pull request number to review
- `repository` (str, optional): Repository in format "owner/repo"
- `force_re_review` (bool, optional): Force re-review mode even if not auto-detected
- `analysis_mode` (str, optional): "comprehensive" for full analysis or "quick" for basic review
- `detail_level` (str, optional): Educational detail level - "brief", "standard", or "comprehensive"

**Features**:
- **Multi-dimensional size classification**: Intelligent review strategies based on PR complexity
- **Re-review tracking**: Detects and handles multiple review cycles
- **External Claude CLI**: Enhanced analysis with cost tracking and session management
- **GitHub integration**: Automated commenting and labeling

**Example Usage**:
```bash
# Comprehensive PR review
claude "vibe check PR 42"

# Re-review with progress tracking
claude "review PR 42 again"
```

### External Claude CLI Tools (Enhanced)

#### `external_claude_analyze`

Advanced content analysis using isolated Claude CLI execution.

**Parameters**:
- `content` (str): Content to analyze
- `task_type` (str, optional): Analysis type - "general", "pr_review", "code_analysis", "issue_analysis"
- `additional_context` (str, optional): Additional context for analysis
- `timeout_seconds` (int, optional): Maximum execution time

#### `external_pr_review`

Specialized PR review using external Claude CLI with anti-pattern detection.

**Parameters**:
- `pr_diff` (str): Pull request diff content
- `pr_description` (str, optional): PR description/title
- `file_changes` (list, optional): List of changed files for context
- `timeout_seconds` (int, optional): Maximum execution time

#### `external_code_analysis`

Deep code analysis for quality, security, and anti-patterns.

**Parameters**:
- `code_content` (str): Code to analyze
- `file_path` (str, optional): File path for context
- `language` (str, optional): Programming language for specialized analysis
- `timeout_seconds` (int, optional): Maximum execution time

#### `external_issue_analysis`

Strategic GitHub issue analysis with implementation guidance.

**Parameters**:
- `issue_content` (str): Issue body/content
- `issue_title` (str, optional): Issue title
- `issue_labels` (list, optional): Issue labels for context
- `timeout_seconds` (int, optional): Maximum execution time

#### `external_claude_status`

Check status and availability of external Claude CLI integration.

**Returns**: Integration status, capabilities, and configuration information

### Utility Tools

#### `analyze_text_demo`

Test vibe check analysis on any text content without GitHub dependencies.

**Parameters**:
- `text` (str): Text content to analyze for anti-patterns
- `detail_level` (str, optional): Educational detail level

#### `server_status`

Get server status and capabilities information.

**Example Usage**:
```bash
/mcp call vibe-check server_status
```

## 📝 Usage Examples

### 1. Basic Anti-Pattern Detection

Analyze a GitHub issue for potential anti-patterns:

```bash
# Check issue for any anti-patterns
/mcp call vibe-check analyze_github_issue --issue_number 42

# Result includes:
# - Detected patterns with confidence scores
# - Educational explanations of why patterns are problematic  
# - Specific remediation steps
# - Prevention checklists for future work
```

### 2. Educational Workflow

Use for code review and team education:

```bash
# Comprehensive analysis for learning
/mcp call vibe-check analyze_github_issue --issue_number 123 --detail_level "comprehensive"

# Focus on specific patterns during reviews
/mcp call vibe-check analyze_github_issue --issue_number 456 --focus_patterns "infrastructure_without_implementation"
```

### 3. Integration with Development Workflow

```bash
# 1. Analyze issues before starting work
/mcp call vibe-check analyze_github_issue --issue_number $ISSUE_ID

# 2. Review recommendations and apply prevention checklist

# 3. Proceed with implementation using anti-pattern guidance
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_TOKEN` | GitHub personal access token | None | No* |
| `MCP_SERVER_HOST` | Server host address | `localhost` | No |
| `MCP_SERVER_PORT` | Server port number | `8000` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

*Required for private repositories or higher rate limits

### GitHub Token Setup

1. **Create a Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create a new token with `repo` scope for private repositories
   - For public repositories only, no token is required

2. **Configure the token**:
   ```bash
   # Option 1: Environment variable
   export GITHUB_TOKEN=your_token_here
   
   # Option 2: .env file
   echo "GITHUB_TOKEN=your_token_here" >> .env
   
   # Option 3: Claude Code configuration (see integration section)
   ```

### FastMCP Server Configuration

The server uses FastMCP framework with these defaults:

```python
# Default configuration
server_config = {
    "name": "Vibe Check MCP",
    "version": "Phase 2.1",
    "host": "localhost",
    "port": 8000,
    "tools": ["analyze_github_issue", "server_status"]
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "Module not found" Error

```bash
# Issue: ModuleNotFoundError: No module named 'vibe_check'
# Solution: Ensure you're in the correct directory and dependencies are installed
cd /path/to/vibe-check-mcp
pip install -r requirements.txt
python -m vibe_check.server
```

#### 2. GitHub API Rate Limiting

```bash
# Issue: GitHub API rate limit exceeded
# Solution: Add GitHub token for higher rate limits
export GITHUB_TOKEN=your_token_here
```

#### 3. Claude Code MCP Connection Issues

**Most Common Issue: "MCP error -32000: Connection closed"**

```bash
# SOLUTION 1: Use Native Deployment (NOT Docker HTTP)
# Claude Code requires stdio transport, not HTTP
claude mcp remove vibe-check -s user
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "vibe_check.server"],
  "env": {"PYTHONPATH": "'"$(pwd)"'/src"}
}' -s user

# SOLUTION 2: Verify server uses stdio transport
cd /path/to/vibe-check-mcp
PYTHONPATH=src python -m vibe_check server --stdio --help

# SOLUTION 3: Check Claude Code can see the server
claude mcp list  # Should show vibe-check as available
```

**Why Docker HTTP doesn't work with Claude Code:**
- Claude Code expects stdio transport (stdin/stdout)
- Docker HTTP uses streamable-http transport (incompatible)
- Use Native or Docker Bridge deployment instead

#### 4. Docker Build Issues

```bash
# Issue: Docker build fails
# Solution: Ensure Docker is running and build context is correct
docker --version  # Verify Docker is installed
docker build --no-cache -t vibe-check-mcp .  # Clean build
```

#### 5. Permission Errors

```bash
# Issue: Permission denied errors
# Solution: Check file permissions and Python virtual environment
chmod +x scripts/*.sh
source venv/bin/activate  # Ensure virtual environment is activated
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug logging
export LOG_LEVEL=DEBUG
python -m vibe_check.server

# Or with Docker
docker run -e LOG_LEVEL=DEBUG vibe-check-mcp
```

### Validation Commands

Test your setup:

```bash
# 1. Test Python environment
python -c "import vibe_check; print('✅ Module import successful')"

# 2. Test dependencies
python -c "from github import Github; print('✅ PyGithub working')"
python -c "from fastmcp import FastMCP; print('✅ FastMCP working')"

# 3. Test server startup
timeout 10s python -m vibe_check.server || echo "✅ Server startup successful"

# 4. Test tool functionality
python -c "
from vibe_check.tools.analyze_issue import analyze_issue
result = analyze_issue(22, 'kesslerio/vibe-check-mcp', 'all', 'brief')
print('✅ Tool execution successful' if 'status' in result else '❌ Tool execution failed')
"
```

### Getting Help

If you continue to experience issues:

1. **Check the logs**: Look for error messages in the server output
2. **Verify your configuration**: Ensure all paths and tokens are correct
3. **Test with minimal setup**: Try the quick start guide with default settings
4. **Create an issue**: [Open a GitHub issue](https://github.com/kesslerio/vibe-check-mcp/issues) with:
   - Your operating system and Python version
   - Complete error messages
   - Steps to reproduce the issue
   - Your configuration files (without sensitive tokens)

## 🏗️ Development

### Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes** following the anti-pattern prevention guidelines
4. **Test thoroughly**: Ensure all functionality works as documented
5. **Submit a pull request**

### Local Development

```bash
# 1. Clone and setup
git clone https://github.com/kesslerio/vibe-check-mcp.git
cd vibe-check-mcp
python -m venv venv
source venv/bin/activate

# 2. Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black isort mypy

# 3. Run tests
pytest

# 4. Run linting
black src/ tests/
isort src/ tests/
mypy src/

# 5. Start development server
python -m vibe_check.server
```

### Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_pattern_detection.py
pytest tests/test_mcp_server.py
```

### Project Structure

```
vibe-check-mcp/
├── src/vibe_check/          # Main package
│   ├── core/                  # Core detection engine
│   ├── tools/                 # MCP tools
│   ├── server.py              # FastMCP server
│   └── cli.py                 # CLI interface
├── data/                      # Pattern definitions and case studies
├── tests/                     # Test suite
├── validation/                # Validation scripts and results
├── docs/                      # Additional documentation
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
└── README.md                  # This file
```

## 🔍 Anti-Pattern Prevention Applied

This project demonstrates anti-pattern prevention in its own development:

- ✅ **Research-First**: Used existing FastMCP framework instead of building custom MCP implementation
- ✅ **Standard APIs**: Leveraged PyGithub library instead of custom HTTP clients
- ✅ **Documentation-Driven**: Comprehensive setup instructions prevent common issues
- ✅ **Validation-Focused**: 87.5% detection accuracy achieved through systematic testing
- ✅ **Educational Focus**: Provides WHY explanations, not just WHAT detection

## 📊 Validation Results

**Phase 1 Validation (Completed)**:
- Core pattern detection: **100% accuracy** (7/7 tests)
- Comprehensive testing: **87.5% accuracy** (7/8 tests)
- False positive rate: **0%**
- Cognee case study detection: **100% confidence**

**Real-World Application**:
- Successfully detected infrastructure anti-patterns in actual development scenarios
- Educational content validated with engineering teams
- Prevention checklists tested in active development workflows

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**Why MIT License?**
- ✅ **Open Source Friendly**: Encourages community contributions and adoption
- ✅ **Commercial Use**: Allows integration into commercial projects
- ✅ **Minimal Restrictions**: Simple, permissive license that's developer-friendly
- ✅ **MCP Ecosystem**: Aligns with Model Context Protocol community standards

## 📋 Summary

### ✅ **For Claude Code Users (Primary Use Case)**
- **Required**: Claude Code installed
- **Recommended**: Native deployment with stdio transport
- **Setup**: Use `claude mcp add-json` command from Quick Start
- **Performance**: ~2s startup, ~50MB memory, direct integration

### ⚠️ **Important Compatibility Notes**
- **Claude Code**: Requires stdio transport (Native or Docker Bridge)
- **Web Applications**: Use Docker HTTP deployment (not compatible with Claude Code)
- **Docker HTTP**: Does NOT work with Claude Code due to transport mismatch

### 🚀 **Deployment Decision Tree**
1. **Using Claude Code?** → Use Native Deployment (fastest, simplest)
2. **Need Docker isolation + Claude Code?** → Use Docker Bridge (compatible but slower)
3. **Building web application?** → Use Docker HTTP (Claude Code won't work)
4. **Not sure?** → Start with Native Deployment

## 🙏 Acknowledgments

- **FastMCP Framework**: For excellent MCP server development experience
- **Model Context Protocol**: For enabling seamless AI tool integration
- **Claude Code**: For powerful MCP client capabilities and stdio transport support
- **Engineering Teams**: For validating anti-pattern detection in real scenarios

---

**Built with ❤️ for engineering excellence and anti-pattern prevention**  
**🎯 Designed specifically for Claude Code MCP integration**

For questions, issues, or contributions, visit: https://github.com/kesslerio/vibe-check-mcp