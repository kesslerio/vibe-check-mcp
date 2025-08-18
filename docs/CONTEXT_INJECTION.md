# Context Injection Hooks for Consistent Analysis Awareness

This document describes the enhanced context injection system that provides automatic project-specific context to all vibe check analysis tools.

## Overview

The context injection system automatically enhances Claude CLI prompts with:
- **Project-specific context** from `.vibe-check/project-context.md`
- **Library documentation** from Context 7 integration
- **Pattern exceptions** from `.vibe-check/pattern-exceptions.json`
- **Team conventions** and architectural decisions

## Quick Start

### 1. Enable Context Injection

Create or update `.vibe-check/config.json`:

```json
{
  "context_loading": {
    "enabled": true,
    "cache_duration_minutes": 60,
    "library_detection": {
      "languages": ["python", "javascript", "typescript"],
      "depth": "imports_only",
      "max_files_to_scan": 1000
    }
  }
}
```

### 2. Create Project Context

Create `.vibe-check/project-context.md`:

```markdown
# Your Project Context

## Team Conventions
- Use pytest for testing with >90% coverage
- Follow PEP 8 for Python, Prettier for TypeScript
- Conventional commit format required

## Approved Pattern Exceptions
- Custom auth system required for GDPR compliance
- Legacy React class components allowed during migration

## Technology Constraints
- Python 3.11+ required
- FastAPI for all new APIs
- React 18+ with hooks pattern
```

### 3. Configure Pattern Exceptions

Update `.vibe-check/pattern-exceptions.json`:

```json
{
  "approved_patterns": [
    "custom-auth-required-for-compliance",
    "legacy-components-in-maintenance-mode"
  ],
  "reasoning": {
    "custom-auth-required-for-compliance": "GDPR requirements mandate custom authentication flow",
    "legacy-components-in-maintenance-mode": "Gradual migration strategy approved by architecture team"
  }
}
```

## How It Works

### Automatic Context Injection

The `EnhancedClaudeCliExecutor` automatically:

1. **Detects Configuration**: Checks if `.vibe-check/config.json` enables context loading
2. **Loads Context Files**: Reads project-context.md and pattern-exceptions.json
3. **Detects Libraries**: Scans project files for library imports and versions
4. **Fetches Documentation**: Gets relevant library docs via Context 7 integration
5. **Enhances Prompts**: Injects context into Claude CLI prompts transparently

### Context Injection Flow

```
User Request → EnhancedClaudeCliExecutor → Context Loading → Enhanced Prompt → Claude CLI
                        ↓
            Project Context + Library Docs + Pattern Exceptions
```

## Configuration Reference

### context_loading Section

```json
{
  "context_loading": {
    "enabled": true,                    // Enable/disable context injection
    "cache_duration_minutes": 60,      // Cache TTL for loaded context
    "library_detection": {
      "languages": ["python", "js"],   // Languages to scan for imports
      "depth": "imports_only",          // "imports_only" or "full_dependency_tree"
      "max_files_to_scan": 1000,      // Performance limit
      "timeout_seconds": 30            // Scan timeout
    },
    "project_docs": {
      "paths": ["docs/", "README.md"], // Documentation paths to include
      "max_file_size_kb": 500         // Size limit per file
    }
  }
}
```

### Library-Specific Overrides

```json
{
  "libraries": {
    "react": {
      "version": "18.x",
      "patterns": ["hooks-preferred", "functional-components"],
      "exceptions": ["legacy-class-components-in-tests"]
    },
    "fastapi": {
      "version": "0.100+", 
      "patterns": ["dependency-injection", "async-preferred"],
      "architecture": "microservices"
    }
  }
}
```

## Usage Examples

### Code Analysis with Context

```python
from vibe_check.tools.shared.enhanced_claude_integration import EnhancedClaudeCliExecutor

# Context is automatically injected
executor = EnhancedClaudeCliExecutor()
result = executor.execute_sync("Analyze this React component", "code_analysis")
```

The analysis will automatically include:
- Your project's React conventions (hooks-preferred)
- Latest React 18 documentation from Context 7
- Approved exceptions (legacy components during migration)

### PR Review with Context

```python
# Existing tools automatically get enhanced context
analyze_pr_result = analyze_github_pr_llm(pr_number=42)
```

The PR review will consider:
- Your team's coding standards
- Library-specific best practices
- Approved architectural patterns

## Project Context Template

Create comprehensive project context in `.vibe-check/project-context.md`:

```markdown
# Project Name - Vibe Check Context

## Team Conventions

### Code Style
- **Python**: Black + isort, type hints required
- **JavaScript/TypeScript**: Prettier + ESLint
- **Testing**: Jest for frontend, pytest for backend
- **Documentation**: JSDoc for public APIs

### Architecture Decisions
- **Authentication**: Custom JWT (GDPR compliance)
- **Database**: PostgreSQL with async SQLAlchemy
- **Caching**: Redis for session management
- **API Design**: OpenAPI spec-first development

## Approved Pattern Exceptions

### Legacy System Integration
- **Custom HTTP clients** approved for legacy SOAP services
- **Synchronous database calls** allowed in migration scripts
- **Class-based React components** in legacy feature modules

### Performance Optimizations
- **Direct SQL queries** approved for reporting features
- **Cache-aside pattern** for frequently accessed data

## Technology Constraints

### Required Versions
- Node.js 18+ for frontend development
- Python 3.11+ for backend services
- PostgreSQL 14+ with specific extensions

### Approved Libraries
- **Frontend**: React 18+, TypeScript 4.5+, Vite
- **Backend**: FastAPI 0.100+, SQLAlchemy 2.0+
- **Testing**: pytest, Jest, Playwright for E2E

## Integration Patterns

### External Services
- **Payment Processing**: Stripe SDK (not custom integration)
- **Email**: SendGrid API with official Python client
- **Logging**: Structured logging with correlation IDs

### Internal Services
- **Message Queue**: RabbitMQ with pika client
- **File Storage**: AWS S3 with boto3
- **Monitoring**: Prometheus + Grafana stack

## Business Context

### Domain-Specific Rules
- **Financial data**: PCI DSS compliance required
- **User data**: GDPR privacy by design
- **Audit trail**: Immutable logs for all transactions

### Success Metrics
- **Performance**: 99.9% uptime, <200ms API response
- **Quality**: >95% test coverage, zero critical security issues
- **User Experience**: <2s page load times
```

## Advanced Features

### Caching and Performance

Context loading is optimized with:
- **TTL-based caching** (default 5 minutes)
- **Lazy loading** of expensive operations
- **Parallel context loading** from multiple sources
- **Size limits** to prevent memory issues

### Graceful Degradation

The system continues working even when:
- Configuration files are missing or invalid
- Context 7 API is unavailable
- File permissions prevent reading context files
- Network timeouts occur during library detection

### Context Scoping

Different scopes provide different context levels:
- **Repository**: Full project context + all libraries
- **PR**: Changed files context + relevant libraries
- **File**: File-specific context + imported libraries
- **Code**: Snippet context + detected dependencies

## Troubleshooting

### Context Not Loading

1. **Check Configuration**:
   ```bash
   cat .vibe-check/config.json | jq '.context_loading.enabled'
   ```

2. **Verify File Permissions**:
   ```bash
   ls -la .vibe-check/
   ```

3. **Test Context Loading**:
   ```python
   from vibe_check.tools.contextual_documentation import get_context_manager
   manager = get_context_manager(".")
   context = manager.get_project_context()
   ```

### Performance Issues

1. **Reduce Scope**:
   - Lower `max_files_to_scan`
   - Increase `cache_duration_minutes`
   - Use `"depth": "imports_only"`

2. **Monitor Cache**:
   ```python
   executor = EnhancedClaudeCliExecutor()
   print(f"Cache hits: {executor._cache_hits}")
   ```

### Library Detection Problems

1. **Check Supported Languages**:
   ```json
   {
     "library_detection": {
       "languages": ["python", "javascript", "typescript"]
     }
   }
   ```

2. **Verify Import Patterns**:
   - Python: `import library` or `from library import`
   - JavaScript: `import {} from 'library'` or `require('library')`

## Migration Guide

### From ClaudeCliExecutor to EnhancedClaudeCliExecutor

**Before:**
```python
from vibe_check.tools.shared.claude_integration import ClaudeCliExecutor

executor = ClaudeCliExecutor()
```

**After:**
```python
from vibe_check.tools.shared.enhanced_claude_integration import EnhancedClaudeCliExecutor

executor = EnhancedClaudeCliExecutor()
```

All existing methods and behavior remain the same - context injection is completely transparent.

### Enabling Context for Existing Projects

1. **Create minimal configuration**:
   ```json
   {
     "context_loading": {
       "enabled": true
     }
   }
   ```

2. **Add basic project context**:
   ```markdown
   # Project Context
   
   ## Key Conventions
   - List your main coding standards
   
   ## Known Exceptions
   - Document approved deviations
   ```

3. **Test with existing tools** - no code changes needed

## Best Practices

### Project Context Content

- **Be specific**: Instead of "use best practices", specify exact patterns
- **Document exceptions**: Explain why deviations are approved
- **Keep current**: Update context as standards evolve
- **Focus on decisions**: Include architectural choices and rationale

### Configuration Management

- **Version control**: Commit `.vibe-check/` directory
- **Team consensus**: Review context changes in PRs
- **Environment-specific**: Use different configs for dev/staging/prod
- **Regular updates**: Review quarterly as project evolves

### Performance Optimization

- **Monitor impact**: Track analysis speed with/without context
- **Tune cache duration**: Balance freshness vs performance
- **Limit scope**: Focus on actively developed parts of codebase
- **Profile regularly**: Check memory usage and load times

## Integration with Existing Tools

All existing vibe check tools automatically benefit from context injection:

- `analyze_github_pr_llm()` - PR reviews with project awareness
- `analyze_github_issue_llm()` - Issue analysis with conventions
- `vibe_check_mentor()` - Collaborative reasoning with context
- `analyze_code_llm()` - Code analysis with library knowledge

No code changes required - enhanced context is injected transparently.

## Future Enhancements

Planned improvements:

- **Git context**: Include recent commits and branch context
- **Team member context**: Developer-specific patterns and preferences  
- **Deployment context**: Environment-specific configuration awareness
- **Metrics integration**: Performance and quality trend context
- **Custom context sources**: Plugin system for domain-specific context

## Support

For issues or questions:

1. Check existing GitHub issues: [kesslerio/vibe-check-mcp](https://github.com/kesslerio/vibe-check-mcp/issues)
2. Create new issue with `area:context-injection` label
3. Include configuration files and error messages
4. Test with context injection disabled to isolate issues