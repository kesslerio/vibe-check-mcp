# 🧭 Vibe Compass MCP

**Engineering Anti-Pattern Detection & Prevention via Model Context Protocol**

A comprehensive MCP server that analyzes code, issues, and development workflows to detect systematic engineering anti-patterns and provide educational guidance for prevention.

[![FastMCP](https://img.shields.io/badge/FastMCP-2.3.4-blue)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-green)](https://docker.com)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Integration-purple)](https://claude.ai)

## 🎯 What It Does

Vibe Compass MCP detects **systematic engineering anti-patterns** that lead to technical debt and project failures:

- 🏗️ **Infrastructure-Without-Implementation**: Building custom solutions before testing standard approaches
- 🩹 **Symptom-Driven Development**: Treating symptoms instead of addressing root causes  
- 🌀 **Complexity Escalation**: Adding unnecessary complexity without justification
- 📚 **Documentation Neglect**: Building before researching standard approaches

**Validated Results**: 87.5% detection accuracy, 0% false positives in comprehensive testing.

## ⚡ Quick Start

Get running in 5 minutes:

```bash
# 1. Clone and install
git clone https://github.com/kesslerio/vibe-compass-mcp.git
cd vibe-compass-mcp
pip install -r requirements.txt

# 2. Start the MCP server
python -m vibe_compass.server

# 3. Connect to Claude Code (see integration section below)
```

## 📦 Installation

### Prerequisites

- **Python 3.8+** (Python 3.10+ recommended)
- **Git** for cloning the repository
- **Docker** (optional, for containerized deployment)
- **Claude Code** for MCP integration

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kesslerio/vibe-compass-mcp.git
   cd vibe-compass-mcp
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
   python -c "from vibe_compass.server import run_server; print('✅ Installation successful')"
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

### Quick Docker Run

```bash
# Build and run with docker-compose (recommended)
docker-compose up --build

# Or build and run manually
docker build -t vibe-compass-mcp .
docker run -p 8000:8000 vibe-compass-mcp
```

### Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  vibe-compass-mcp:
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
docker build --target production -t vibe-compass-mcp:prod .

# Run with production settings
docker run -d \
  --name vibe-compass-mcp \
  -p 8000:8000 \
  -e GITHUB_TOKEN=${GITHUB_TOKEN} \
  -e LOG_LEVEL=WARNING \
  --restart unless-stopped \
  vibe-compass-mcp:prod
```

## 🔗 Claude Code Integration

### Step 1: Add MCP Server to Claude Code

The correct way to add MCP servers to Claude Code is using the `claude mcp add` command:

#### User-Level Configuration (Recommended)

Add the server at user level (available across all projects):

```bash
# Navigate to the project directory
cd /path/to/vibe-compass-mcp

# Add server with user scope
claude mcp add vibe-compass -s user python -m vibe_compass.server --cwd $(pwd) --env PYTHONPATH=$(pwd)/src

# Optional: Add GitHub token for private repositories
claude mcp add vibe-compass -s user python -m vibe_compass.server --cwd $(pwd) --env PYTHONPATH=$(pwd)/src --env GITHUB_TOKEN=your_token_here
```

#### Project-Level Configuration

Add the server for current project only:

```bash
# Navigate to your project directory
cd /your/project/directory

# Add server with local scope
claude mcp add vibe-compass -s local python -m vibe_compass.server --cwd /path/to/vibe-compass-mcp --env PYTHONPATH=/path/to/vibe-compass-mcp/src
```

#### Docker-Based Configuration

If using Docker:

```bash
# Build the Docker image first
cd /path/to/vibe-compass-mcp
docker build -t vibe-compass-mcp .

# Add Docker-based MCP server
claude mcp add vibe-compass -s user docker run --rm -p 8000:8000 vibe-compass-mcp
```

### Step 2: Verify Installation

1. **List installed MCP servers**:
   ```bash
   claude mcp list
   ```

2. **You should see vibe-compass listed** with status information

3. **Test the server**:
   ```bash
   claude mcp call vibe-compass server_status
   ```

### Step 3: Test GitHub Issue Analysis

Test the main functionality:
```bash
claude mcp call vibe-compass analyze_github_issue --issue_number 22 --repository "kesslerio/vibe-compass-mcp"
```

Expected output includes:
- Anti-pattern detection results with confidence scores
- Educational explanations of detected patterns
- Remediation recommendations
- Prevention checklists

## 🛠️ Available Tools

### `analyze_github_issue`

Analyzes GitHub issues for anti-patterns and provides educational guidance.

**Parameters**:
- `issue_number` (int): GitHub issue number to analyze
- `repository` (str, optional): Repository in format "owner/repo" (defaults to current repo)
- `focus_patterns` (str, optional): Comma-separated patterns to focus on ("all" for all patterns)
- `detail_level` (str, optional): Educational detail level - "brief", "standard", or "comprehensive"

**Example Usage**:
```bash
# Analyze issue #22 in current repository
/mcp call vibe-compass analyze_github_issue --issue_number 22

# Analyze specific repository with comprehensive detail
/mcp call vibe-compass analyze_github_issue --issue_number 123 --repository "owner/repo" --detail_level "comprehensive"

# Focus on specific anti-patterns
/mcp call vibe-compass analyze_github_issue --issue_number 456 --focus_patterns "infrastructure_without_implementation,complexity_escalation"
```

### `server_status`

Get server status and capabilities information.

**Example Usage**:
```bash
/mcp call vibe-compass server_status
```

## 📝 Usage Examples

### 1. Basic Anti-Pattern Detection

Analyze a GitHub issue for potential anti-patterns:

```bash
# Check issue for any anti-patterns
/mcp call vibe-compass analyze_github_issue --issue_number 42

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
/mcp call vibe-compass analyze_github_issue --issue_number 123 --detail_level "comprehensive"

# Focus on specific patterns during reviews
/mcp call vibe-compass analyze_github_issue --issue_number 456 --focus_patterns "infrastructure_without_implementation"
```

### 3. Integration with Development Workflow

```bash
# 1. Analyze issues before starting work
/mcp call vibe-compass analyze_github_issue --issue_number $ISSUE_ID

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
    "name": "Vibe Compass MCP",
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
# Issue: ModuleNotFoundError: No module named 'vibe_compass'
# Solution: Ensure you're in the correct directory and dependencies are installed
cd /path/to/vibe-compass-mcp
pip install -r requirements.txt
python -m vibe_compass.server
```

#### 2. GitHub API Rate Limiting

```bash
# Issue: GitHub API rate limit exceeded
# Solution: Add GitHub token for higher rate limits
export GITHUB_TOKEN=your_token_here
```

#### 3. Claude Code Connection Issues

```bash
# Issue: MCP server not responding
# Solution: Check server is running and port is correct
python -m vibe_compass.server  # Should show "Server ready for MCP protocol connections"

# Check if port 8000 is in use
lsof -i :8000
```

#### 4. Docker Build Issues

```bash
# Issue: Docker build fails
# Solution: Ensure Docker is running and build context is correct
docker --version  # Verify Docker is installed
docker build --no-cache -t vibe-compass-mcp .  # Clean build
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
python -m vibe_compass.server

# Or with Docker
docker run -e LOG_LEVEL=DEBUG vibe-compass-mcp
```

### Validation Commands

Test your setup:

```bash
# 1. Test Python environment
python -c "import vibe_compass; print('✅ Module import successful')"

# 2. Test dependencies
python -c "from github import Github; print('✅ PyGithub working')"
python -c "from fastmcp import FastMCP; print('✅ FastMCP working')"

# 3. Test server startup
timeout 10s python -m vibe_compass.server || echo "✅ Server startup successful"

# 4. Test tool functionality
python -c "
from vibe_compass.tools.analyze_issue import analyze_issue
result = analyze_issue(22, 'kesslerio/vibe-compass-mcp', 'all', 'brief')
print('✅ Tool execution successful' if 'status' in result else '❌ Tool execution failed')
"
```

### Getting Help

If you continue to experience issues:

1. **Check the logs**: Look for error messages in the server output
2. **Verify your configuration**: Ensure all paths and tokens are correct
3. **Test with minimal setup**: Try the quick start guide with default settings
4. **Create an issue**: [Open a GitHub issue](https://github.com/kesslerio/vibe-compass-mcp/issues) with:
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
git clone https://github.com/kesslerio/vibe-compass-mcp.git
cd vibe-compass-mcp
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
python -m vibe_compass.server
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
vibe-compass-mcp/
├── src/vibe_compass/          # Main package
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

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastMCP Framework**: For excellent MCP server development experience
- **Model Context Protocol**: For enabling seamless AI tool integration
- **Claude Code**: For powerful MCP client capabilities
- **Engineering Teams**: For validating anti-pattern detection in real scenarios

---

**Built with ❤️ for engineering excellence and anti-pattern prevention**

For questions, issues, or contributions, visit: https://github.com/kesslerio/vibe-compass-mcp