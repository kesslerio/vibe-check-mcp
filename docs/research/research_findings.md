# MCP Code Reviewer Research Findings

## Executive Summary

Based on comprehensive research following CLAUDE.md documentation-first protocols, this document provides technical architecture recommendations for the Engineering Anti-Patterns Prevention MCP Server project.

## 1. MCP Protocol & FastMCP Framework Analysis

### Key Findings

**MCP Protocol Specifications:**
- JSON-RPC 2.0 based protocol with well-defined tool schemas
- Tool schema requirements: `name`, `description`, `inputSchema` (JSON Schema)
- **CRITICAL**: MCP protocol does NOT support `oneOf`, `allOf`, or `anyOf` at top level of schemas
- Runtime parameter validation must be handled in code, not schemas

**FastMCP Framework (Official Python SDK):**
- Mature, official implementation: `from mcp.server.fastmcp import FastMCP`
- Decorator-based tool registration: `@mcp.tool()`
- Built-in Context object for progress tracking and resource access
- Claude Desktop integration via `mcp install server.py`
- Development workflow: `mcp dev server.py` for testing

**Recommended Architecture:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Engineering Anti-Patterns Prevention")

@mcp.tool()
def validate_issue(issue_description: str, proposed_solution: str = None) -> dict:
    """Systematic issue validation with anti-pattern detection"""
    # Implementation here
```

## 2. Python Static Analysis Libraries Research

### Core Libraries Assessment

**1. Python AST Module (Built-in)**
- **Strengths**: Standard library, NodeVisitor pattern, full syntax tree access
- **Use Case**: Custom anti-pattern detection logic, complex code analysis
- **Implementation**: Subclass `ast.NodeVisitor` for pattern matching

**2. Ruff (Recommended Primary Tool)**
- **Performance**: Extremely fast (Rust-based), 100x faster than traditional tools
- **Features**: 800+ rules, comprehensive linting, auto-fixing
- **Integration**: Easy subprocess integration, JSON output support
- **Status**: Active development, rapidly becoming Python standard

**3. Bandit (Security Analysis)**
- **Focus**: Security vulnerability detection
- **Method**: AST-based analysis with security-specific rules
- **Use Case**: Third-party integration security validation

**4. MyPy (Type Checking)**
- **Purpose**: Static type analysis, complexity indicators
- **Integration**: Can detect over-engineered type structures

**5. PyLint (Comprehensive Analysis)**
- **Features**: Code quality metrics, pattern detection
- **Drawback**: Slower than Ruff, more configuration overhead

### Recommended Stack
1. **Primary**: FastMCP + Python AST for custom anti-pattern logic
2. **Secondary**: Ruff integration for standard code quality
3. **Security**: Bandit for third-party integration validation
4. **Type Analysis**: MyPy for complexity assessment

## 3. Existing Anti-Pattern Detection Tools Analysis

### Research Findings

**Academic Tools:**
- MLScent: ML-specific anti-pattern detection using AST analysis
- TEMPY: Test smell detection for Python
- Pyscent: General Python code smell detection

**Commercial Solutions:**
- SonarQube: Comprehensive but heavyweight
- CodeClimate: Good patterns but limited customization

**Key Insight**: No existing tool addresses the specific anti-patterns from the Cognee retrospective:
- Infrastructure-without-implementation patterns
- Symptom-driven development detection
- Third-party integration over-engineering
- Documentation neglect patterns

**Opportunity**: Our MCP server fills a unique niche in preventing systematic integration failures.

## 4. Technical Architecture Recommendations

### Project Structure
```
src/
├── server.py                    # FastMCP server entry point
├── tools/
│   ├── __init__.py
│   ├── issue_validator.py       # Port review-issue.sh logic
│   ├── pr_reviewer.py           # Port review-pr.sh logic
│   ├── antipattern_detector.py  # Real-time AST analysis
│   └── integration_validator.py # Third-party validation
├── analyzers/
│   ├── __init__.py
│   ├── ast_analyzer.py          # Custom AST pattern detection
│   ├── ruff_integration.py      # Ruff subprocess integration
│   └── security_scanner.py      # Bandit integration
├── knowledge/
│   ├── antipatterns.json        # Pattern definitions from scripts
│   ├── cognee_lessons.json      # Retrospective learnings
│   └── third_party_apis.json    # Known API patterns
└── utils/
    ├── __init__.py
    ├── git_operations.py        # GitHub API integration
    └── claude_integration.py    # Optional Clear-Thought tools
```

### Dependency Stack
```txt
# Core MCP
mcp>=1.0.0

# Static Analysis
ruff>=0.5.0
bandit[toml]>=1.7.0
mypy>=1.0.0

# GitHub Integration  
PyGithub>=2.0.0
requests>=2.28.0

# Utilities
pydantic>=2.0.0
click>=8.0.0
```

### Key Design Decisions

**1. AST-First Approach**
- Use Python's `ast` module for sophisticated pattern detection
- Implement custom `NodeVisitor` subclasses for each anti-pattern
- Leverage AST for contextual analysis beyond simple regex patterns

**2. Hybrid Analysis Strategy**
- Custom AST analysis for specific anti-patterns (infrastructure-without-implementation)
- Ruff integration for standard code quality metrics
- Bandit for security validation of third-party integrations

**3. Knowledge Base Design**
- JSON-based pattern definitions extracted from existing scripts
- Extensible architecture for adding new anti-patterns
- Case study integration (Cognee lessons) for context

**4. MCP Tool Design**
- Follow FastMCP decorator patterns for clean tool definitions
- Implement proper JSON Schema validation (avoiding unsupported features)
- Return structured data with confidence scores and remediation suggestions

## 5. Implementation Priorities

### Phase 1: Foundation (Immediate)
1. Set up FastMCP server with basic tool registration
2. Port `validate_issue` logic from `review-issue.sh` (400+ lines)
3. Implement basic AST analysis for third-party service detection
4. Create knowledge base from existing script patterns

### Phase 2: Core Analysis (Next)
1. Implement comprehensive anti-pattern detection using AST
2. Integrate Ruff for standard code quality metrics
3. Add Bandit security analysis for third-party integrations
4. Port `review_pull_request` from `review-pr.sh`

### Phase 3: Advanced Features (Later)
1. Real-time code analysis capabilities
2. Codebase auditing tools
3. Integration with Clear-Thought MCP tools
4. Performance optimization and monitoring

## 6. Risk Assessment & Mitigation

### Technical Risks
1. **MCP Schema Limitations**: Avoid oneOf/allOf at root level
2. **Performance**: AST analysis can be slow - implement caching
3. **Maintenance**: Keep up with FastMCP API changes

### Mitigation Strategies
1. **Schema Design**: Use runtime validation instead of complex schemas
2. **Performance**: Implement incremental analysis and result caching
3. **Framework Updates**: Pin versions, test compatibility regularly

## 7. Success Metrics

### Technical Metrics
- Tool response time <2 seconds for typical analysis
- 95%+ accuracy in detecting known anti-patterns from scripts
- Zero false positives on infrastructure-without-implementation detection

### Business Impact
- Prevention of 2+ year technical debt scenarios (like Cognee)
- Measurable reduction in over-engineered solutions
- Team adoption for daily development workflow

## Conclusion

The research validates the project's technical feasibility and identifies a clear implementation path. The combination of FastMCP framework, Python AST analysis, and modern static analysis tools provides a robust foundation for systematic anti-pattern prevention.

**Recommended Next Steps:**
1. Update issue #1 with detailed technical specifications
2. Begin Phase 1 implementation with FastMCP server setup
3. Port existing script logic incrementally with proper testing
4. Design extensible architecture for future anti-pattern additions

**Key Success Factor**: Maintain focus on the specific anti-patterns that caused the Cognee integration failures, rather than building a generic code quality tool.