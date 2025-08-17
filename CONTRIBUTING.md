# Contributing to Vibe Check MCP

Thank you for your interest in contributing to Vibe Check MCP! This guide will help you get started with contributing to our engineering anti-pattern detection and educational coaching platform.

## 🎯 Project Vision

Vibe Check MCP prevents systematic engineering failures through real-time anti-pattern detection and educational coaching. We transform hard-won lessons from real-world failures into actionable prevention guidance.

## 🚀 Quick Start for Contributors

### Prerequisites

- Python 3.8+ with pip
- Git
- GitHub account
- [Claude Code](https://claude.ai) (recommended for testing MCP integration)

### Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/vibe-check-mcp.git
cd vibe-check-mcp

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
export GITHUB_TOKEN="your_github_token"  # For GitHub integration testing
export VIBE_CHECK_DEV_MODE="true"       # Enable dev tools

# 5. Run tests to verify setup
pytest

# 6. Start the MCP server for testing
PYTHONPATH=src python -m vibe_check server
```

## 🏗️ Project Structure

```
vibe-check-mcp/
├── src/vibe_check/          # Main package
│   ├── core/                # Pattern detection engine
│   ├── tools/               # MCP tools implementation
│   │   ├── analyze_*_llm.py    # LLM-powered analysis tools
│   │   └── analyze_*_nollm.py  # Fast direct analysis tools
│   ├── utils/               # Utilities and helpers
│   └── server/             # Modular FastMCP server
│       ├── main.py         # Entry point
│       ├── core.py         # FastMCP initialization
│       ├── transport.py    # Transport detection
│       ├── registry.py     # Tool registration
│       └── tools/          # Tool implementations
├── docs/                   # Documentation
│   ├── PRD.md             # Product Requirements
│   ├── TECHNICAL.md       # Technical Implementation
│   └── USAGE.md           # Usage examples
├── tests/                  # Test suite
├── scripts/               # Automation scripts
└── validation/           # Pattern validation
```

## 🛠️ Development Workflow

### 1. Branch Strategy

- `main` - Production-ready code
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates

### 2. Making Changes

```bash
# Create feature branch
git checkout -b feature/new-anti-pattern-detection

# Make your changes following the coding standards below
# Run tests frequently
pytest

# Run linting and type checking
black src/ tests/
mypy src/
pylint src/

# Commit with clear messages
git commit -m "Add: Detection for over-engineering anti-pattern

- Implement AST analysis for unnecessary abstraction layers
- Add educational content for complexity escalation  
- Include test cases and validation data
- Update pattern definitions JSON"
```

### 3. Testing Requirements

All contributions must include:

- **Unit tests** for new functionality
- **Integration tests** for MCP tools
- **Pattern validation** for new anti-pattern detection
- **Documentation updates** for new features

```bash
# Run full test suite
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Test MCP integration
PYTHONPATH=src python -c "from vibe_check.server import app; print('✅ MCP server loads')"
```

## 📋 Contribution Types

### 🎯 High-Priority Contributions

1. **New Anti-Pattern Detection**
   - Add detection algorithms for new engineering anti-patterns
   - Include real-world case studies and educational content
   - Validate with test cases and false positive checks

2. **Educational Content**
   - Improve explanations of why patterns are problematic
   - Add case studies from real engineering failures
   - Enhance coaching recommendations

3. **MCP Tool Enhancements**
   - Improve existing tools (analyze_issue, analyze_pr, etc.)
   - Add new MCP tools for different analysis types
   - Optimize performance and response times

### 🛠️ Technical Contributions

1. **Performance Improvements**
   - Optimize pattern detection algorithms
   - Improve MCP server response times
   - Reduce memory usage and startup time

2. **Integration Enhancements**
   - Improve GitHub API integration
   - Add support for other platforms (GitLab, etc.)
   - Enhance Claude Code MCP integration

3. **Developer Experience**
   - Improve error messages and debugging
   - Add more comprehensive logging
   - Enhance development tooling

## 📝 Coding Standards

### Python Style

- **PEP 8** compliance with Black formatting (88 character lines)
- **Type hints** mandatory for all functions
- **Docstrings** required for public functions
- **Import organization**: Standard → Third-party → Local

### Code Organization

- **Functions**: Maximum 40 lines (Single Responsibility Principle)
- **Files**: Maximum 700 lines (consider splitting if larger)
- **Classes**: Prefer functions over classes unless state management needed
- **Error handling**: Specific try/catch with detailed error messages

### Example Code Structure

```python
from typing import Dict, List, Optional
from pathlib import Path

def detect_infrastructure_pattern(
    code_content: str,
    context: Optional[Dict[str, str]] = None
) -> Dict[str, float]:
    """
    Detect infrastructure-without-implementation anti-pattern.
    
    Args:
        code_content: Source code to analyze
        context: Optional context for analysis
        
    Returns:
        Dictionary with confidence scores for detected patterns
        
    Raises:
        ValueError: If code_content is empty or invalid
    """
    if not code_content.strip():
        raise ValueError("Code content cannot be empty")
    
    # Implementation here...
    return {"infrastructure_without_implementation": 0.85}
```

### MCP Tool Standards

- **Clear tool descriptions** in schema
- **Structured error responses** with helpful messages
- **No oneOf/allOf/anyOf** at root level (MCP protocol limitation)
- **Educational output format** for all responses

## 🧪 Testing Guidelines

### Test Structure

```python
import pytest
from vibe_check.core.pattern_detector import PatternDetector

class TestPatternDetector:
    def test_infrastructure_pattern_detection(self):
        """Test detection of infrastructure-without-implementation pattern."""
        detector = PatternDetector()
        
        # Test case with known anti-pattern
        code_with_pattern = """
        # Custom HTTP client instead of using SDK
        class CustomAPIClient:
            def __init__(self):
                self.session = requests.Session()
        """
        
        result = detector.analyze(code_with_pattern)
        
        assert result.patterns_detected > 0
        assert "infrastructure_without_implementation" in result.anti_patterns
        assert result.anti_patterns["infrastructure_without_implementation"].confidence > 0.7

    def test_no_false_positives(self):
        """Ensure good code doesn't trigger false positives."""
        detector = PatternDetector()
        
        # Good code using standard SDK
        good_code = """
        import stripe
        stripe.api_key = "sk_test_..."
        stripe.Customer.create(email="test@example.com")
        """
        
        result = detector.analyze(good_code)
        
        # Should not detect anti-patterns in good code
        assert result.patterns_detected == 0
```

### Integration Tests

```python
@pytest.mark.integration
def test_analyze_github_issue_tool():
    """Test the analyze_github_issue MCP tool."""
    from vibe_check.tools.analyze_issue_llm import analyze_github_issue_llm
    
    # Test with a real GitHub issue (use test repository)
    result = analyze_github_issue_llm(
        issue_number=1,
        repository="kesslerio/vibe-check-mcp-test",
        analysis_mode="quick"
    )
    
    assert result["analysis_mode"] == "quick"
    assert "patterns_detected" in result
    assert isinstance(result["recommendations"], dict)
```

## 📚 Documentation Standards

### Code Documentation

- **Docstrings**: Google style for all public functions
- **Type hints**: Complete type annotations
- **Examples**: Include usage examples in docstrings
- **Error conditions**: Document when functions raise exceptions

### User Documentation

- **Clear examples**: Show actual usage patterns
- **Error scenarios**: Document common error cases and solutions
- **Configuration**: Explain all environment variables and options
- **Troubleshooting**: Include common issues and solutions

## 🔍 Anti-Pattern Detection Contributions

### Adding New Patterns

1. **Research the pattern**: Document real-world examples and impacts
2. **Create detection algorithm**: Implement the detection logic
3. **Add educational content**: Explain why it's problematic and how to fix
4. **Write comprehensive tests**: Include positive and negative test cases
5. **Validate accuracy**: Ensure low false positive rate

### Pattern Definition Format

```python
PATTERN_DEFINITION = {
    "id": "new_anti_pattern",
    "name": "Descriptive Pattern Name",
    "description": "Clear description of what this pattern is",
    "why_problematic": "Explanation of why this causes problems",
    "detection_method": "ast|regex|heuristic",
    "confidence_threshold": 0.7,
    "case_studies": [
        {
            "title": "Real-world failure example",
            "impact": "Quantified impact (time, cost, etc.)",
            "lesson": "What to do instead"
        }
    ],
    "prevention_checklist": [
        "Specific action to prevent this pattern",
        "Another preventive measure"
    ]
}
```

## 🚀 Release Process

We use automated releases with semantic versioning:

1. **Make your changes** on a feature branch
2. **Ensure all tests pass** and code quality checks pass
3. **Submit a pull request** with clear description
4. **Address review feedback** from maintainers
5. **Merge to main** triggers automated release process

### Commit Message Format

```
Type: Brief description of change

- Detailed explanation of what changed
- Why the change was necessary
- Any breaking changes or migration notes

Closes #issue-number
```

Types: `Add`, `Fix`, `Update`, `Remove`, `Refactor`, `Docs`, `Test`

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful** and inclusive in all interactions
- **Focus on the code** and technical merit of contributions
- **Help others learn** through constructive feedback
- **Assume good intentions** and ask for clarification when needed

### Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check docs/ directory for detailed guides

### Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes for significant contributions
- Documentation acknowledgments

## 📊 Quality Standards

All contributions must meet:

- **✅ Tests pass**: `pytest` runs without failures
- **✅ Type checking**: `mypy src/` passes
- **✅ Code style**: `black` and `pylint` compliance
- **✅ Documentation**: Updated for new features
- **✅ Performance**: No significant performance regressions

## 🎯 Getting Started

Ready to contribute? Here are some good first issues:

1. **Add test cases** for existing anti-pattern detection
2. **Improve error messages** in MCP tools
3. **Add educational content** for existing patterns
4. **Fix documentation typos** or improve examples
5. **Optimize performance** of pattern detection algorithms

Look for issues labeled `good-first-issue` or `help-wanted` in the GitHub repository.

Thank you for contributing to Vibe Check MCP! Together, we can help developers avoid systematic engineering failures and build better software.