# Project-Specific Context for Vibe Check Analysis

This file provides project-specific context to enhance anti-pattern detection and code analysis recommendations. The vibe check tools will automatically include this context when analyzing code, PRs, and issues.

## Team Conventions

### Code Style
- **Python**: Black + isort formatting, PEP 8 compliance required
- **Documentation**: Type hints mandatory for all public functions  
- **Testing**: pytest with >90% coverage requirement
- **Commits**: Conventional commit format required

### Architecture Decisions
- **MCP Integration**: FastMCP framework for all MCP tools
- **Error Handling**: Circuit breaker pattern for external service calls
- **Performance**: Response time <3 seconds for analysis tools
- **Security**: Input validation required for all user-provided data

## Approved Pattern Exceptions

### Custom Integration Approaches
- **Claude CLI Integration**: Custom wrapper with timeout and isolation required for recursion prevention
- **Context Loading**: File-based context preferred over dynamic API calls for reliability
- **Circuit Breaker**: Custom implementation approved for MCP-specific requirements

### Legacy Code Patterns
- **Gradual Migration**: Mixed patterns allowed during transition to enhanced architecture
- **Backward Compatibility**: Existing ClaudeCliExecutor usage maintained alongside enhanced version

## Technology Constraints

### Development Stack
- **Python**: 3.11+ required for all new code
- **FastMCP**: 0.9.0+ for MCP server implementation
- **Testing**: pytest + coverage for comprehensive test coverage
- **Documentation**: Sphinx for API documentation

### Infrastructure Requirements
- **Claude CLI**: External CLI integration with proper isolation
- **Context 7**: Optional integration for library documentation
- **Redis**: Optional caching for performance optimization

## Integration Patterns

### Analysis Tool Design
- **Context Injection**: Automatic via EnhancedClaudeCliExecutor inheritance
- **Configuration**: .vibe-check/config.json for project-specific settings
- **Caching**: TTL-based caching for context loading performance

### Anti-Pattern Prevention
- **Integration Decisions**: Always check official alternatives before custom development
- **Complexity Management**: Keep files <700 lines, functions <40 lines
- **Documentation First**: Research official docs before building workarounds

## Project-Specific Patterns

### MCP Tool Development
- Use FastMCP decorators for tool registration
- Implement proper error handling with graceful degradation
- Follow security best practices for input validation

### Context Management
- Lazy loading preferred for performance
- Graceful fallback when context unavailable
- Caching with reasonable TTL (5-60 minutes)

## Business Context

### Project Mission
Prevent engineering disasters through intelligent anti-pattern detection and contextual code analysis. Focus on practical, actionable recommendations that improve code quality without adding unnecessary complexity.

### Success Metrics
- Reduced time spent on integration decisions
- Fewer custom implementations when official alternatives exist
- Improved consistency of code analysis recommendations
- Higher confidence in architectural decisions

## Notes for Analysis Tools

When analyzing code in this project:
1. **Context Awareness**: Consider project-specific patterns and exceptions
2. **Integration Focus**: Always suggest official alternatives over custom development
3. **Practical Recommendations**: Provide actionable, specific guidance
4. **Complexity Balance**: Favor simplicity over architectural purity

This context helps ensure that vibe check analysis is tailored to our specific project needs and architectural decisions.