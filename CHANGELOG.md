# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2025-10-22

### Added
- **Tool Architecture Optimization** (#237): Environment-based tool gating for cleaner UX
  - Production mode: 30 tools (default) - 30% reduction from 43 tools
  - Diagnostics mode: +11 tools with `VIBE_CHECK_DIAGNOSTICS=true`
  - Development mode: +2 tools with `VIBE_CHECK_DEV_MODE=true`
  - Tool descriptions now prefixed with `[DIAGNOSTIC]` and `[DEV]` for clarity
  - `skip_production` parameter for maintainable tool registration
  - Comprehensive test suite with 11 tests validating all modes

- **Context7 MCP Server Integration** (#220, #217): Hybrid documentation approach
  - Direct library documentation access via Context7 MCP server
  - Intelligent caching with TTL support and memory limits
  - Circuit breaker pattern for graceful degradation
  - Rate limiting (100 requests/minute) and timeout protection
  - Fallback to web search when Context7 unavailable
  - Support for 9 popular libraries (React, TypeScript, FastAPI, etc.)

- **Context Injection Hooks** (#218): Automatic project context loading
  - Detects project libraries and technologies automatically
  - Injects relevant documentation into analysis workflows
  - Supports GitHub issue/PR analysis with project-aware context
  - Configurable context injection for all analysis tools

- **Telemetry System** (#209): Basic metrics collection for MCP sampling
  - Tracks request patterns and response times
  - Session-based analytics for usage insights
  - Privacy-preserving metric aggregation
  - Foundation for future performance optimization

- **Claude Code GitHub Workflow** (#231): Automated code review integration
  - GitHub Actions workflow for automated vibe checks
  - PR comment integration with analysis results
  - Configurable review triggers and thresholds

- **Test Factory Pattern** (#224): Dependency injection for testing
  - Simplified test setup with `create_mentor_engine()`
  - Mock-friendly architecture for unit testing
  - Reduces test boilerplate by 60%

### Performance
- **Token Optimization** (#236): Reduced MCP tool token consumption by 86.7%
  - Before: ~35,000 tokens for tool descriptions
  - After: ~4,700 tokens for tool descriptions
  - Achieved through schema optimization and description compression
  - Saves ~$0.42 per 1000 requests with Claude Sonnet

- **Tool Count Reduction** (#237): 30% fewer default tools
  - Production: 30 tools (down from 43)
  - Token savings: ~650 tokens per request
  - Cleaner tool discovery for end users
  - Professional appearance (no internal test tools exposed)

### Fixed
- **MCP stdio Import Failures** (#239, #234, #232): P0 Critical Bug
  - Converted all relative imports to absolute imports
  - Fixed module import failures in MCP stdio mode
  - Prevented `ModuleNotFoundError` in Claude Code integration
  - Affected modules: GitHub integration, PR review, LLM analysis

- **Claude CLI Diagnostics** (#243): MCP stdio mode integration
  - Enhanced diagnostic tools for Claude CLI troubleshooting
  - Fixed timeout detection in MCP stdio environments
  - Improved error messages for recursion detection
  - Added environment variable guidance

- **Read-Only Filesystem** (b531b0a): MCP stdio compatibility
  - Handles read-only filesystems in MCP stdio mode
  - Graceful fallback when temporary directories unavailable
  - Prevents crashes in restricted environments

- **Workflow Syntax Errors** (#242, #241): GitHub Actions fixes
  - Removed invalid EOF syntax from YAML workflows
  - Fixed issue validation workflow failures
  - Improved CI/CD reliability

- **Test Suite Fixes** (#216, #215, #213, #208): 100% pass rate achieved
  - Fixed async/sync mismatch in mentor calls
  - Removed unexpected `ctx` parameter from generate_contribution
  - Resolved test collection errors after server.py refactor
  - All tests now passing consistently

- **PR Review Quality** (#227): Reduced superfluous recommendations
  - Improved pattern detection to avoid false positives
  - Better context understanding for review comments
  - More actionable, less generic suggestions

### Changed
- **Tool Registration Architecture**: Refactored for maintainability
  - Added `skip_production` parameter to registration functions
  - Prevents double-registration in development mode
  - Maintains encapsulation (tools managed by their modules)
  - Self-documenting code with explicit parameters

- **Documentation Accuracy**: All tool counts verified at runtime
  - System module: 2 tools (was documented as 1)
  - Project context: 4 tools (was documented as 3)
  - Diagnostic tools: 11 total (was documented as 13)
  - Inline comments now match actual behavior

### Technical Improvements
- **Import Strategy**: All relative imports converted to absolute
  - Prevents MCP stdio import failures
  - Improves module resolution reliability
  - Better compatibility with different execution contexts

- **Environment Variables**: New configuration options
  - `VIBE_CHECK_DIAGNOSTICS`: Enable 11 diagnostic tools
  - `VIBE_CHECK_DEV_MODE`: Enable 2 development tools
  - `VIBE_CHECK_DEV_MODE_OVERRIDE`: Enable comprehensive test suite

- **Code Quality**: Enhanced maintainability
  - Reduced coupling between registry and tool modules
  - Consistent registration patterns across all modules
  - Comprehensive test coverage for all modes
  - Runtime-verified documentation

### Security
- **Context7 Integration**: Secure documentation access
  - Rate limiting to prevent abuse
  - Timeout protection against hanging requests
  - Circuit breaker for service degradation
  - Memory limits to prevent resource exhaustion

### Documentation
- **README.md**: Added tool architecture configuration section
  - Environment variable usage guide
  - Benefits of environment-based gating
  - Tool count breakdown by mode

- **Test Documentation**: Comprehensive test suite documentation
  - 11 tests for tool architecture validation
  - Tests for production, diagnostics, dev, and combined modes
  - Backward compatibility verification

### Breaking Changes
None - All changes are backward compatible. Tools remain available via environment variables.

### Migration Guide
For users upgrading from v0.5.1:
- No action required - default behavior unchanged
- To enable diagnostics: `export VIBE_CHECK_DIAGNOSTICS=true`
- To enable dev tools: `export VIBE_CHECK_DEV_MODE=true`
- All 43 original tools still available via environment variables

## [0.5.1] - 2025-08-12

### Added
- **MCP Sampling Integration** (#189): Dynamic response generation for vibe_check_mentor
  - Native MCP protocol support for LLM completions without API keys
  - Hybrid routing between static (fast) and dynamic (flexible) responses
  - Response caching with TTL support for performance optimization
  - Circuit breaker pattern for graceful degradation
  - Comprehensive security measures (secret redaction, rate limiting, injection prevention)

### Technical Improvements
- **Hybrid Router**: Intelligent routing based on confidence scoring
  - High confidence queries use static responses (<100ms)
  - Low confidence queries trigger dynamic generation (~2000ms)
  - Configurable confidence threshold (default 0.7)
  - Cache hit optimization reduces latency by 85%

- **Security Enhancements**:
  - Automatic secret detection and redaction (API keys, passwords, tokens)
  - Prompt injection prevention with pattern matching
  - Path validation to prevent symlink attacks
  - Rate limiting (10 requests/minute per session)
  - 30-second timeout protection with fallback

- **Performance Metrics**:
  - P95 latency: ~2000ms for dynamic generation
  - Static response: <100ms
  - Cache hit rate: 20% (with optimization opportunities)
  - Circuit breaker recovery: 60 seconds

### Changed
- vibe_check_mentor now accepts `ctx` parameter for MCP sampling
- Enhanced path validation with symlink prevention
- Improved error handling with graceful fallback to static responses

### Documentation
- Added comprehensive MCP_SAMPLING.md technical documentation
- Updated vibe_check_mentor API reference with ctx parameter
- Added troubleshooting guide for common issues
- Performance tuning recommendations

## [0.4.6] - 2025-07-16

### Fixed
- **vibe_check_mentor Phase Parameter**: Fixed redundant clarifying questions when phase is explicitly set (#173, #174)
  - When `phase="planning"` is set, bypasses "Are you planning to implement this?" questions
  - Treats explicit phase as high-confidence signal (0.8)
  - Supports phases: planning, implementation, coding, development, review
  
### Improvements
- Added debug logging when no explicit phase is provided
- Enhanced docstring with clear example of phase bypass behavior
- Better user experience for architectural planning discussions

## [0.4.5] - 2025-07-16

### Added
- **Context-Aware Processing**: New BusinessContextExtractor intelligently distinguishes between completion reports, review requests, and planning discussions (#167)
- **Clarifying Questions**: vibe_check_mentor now asks intelligent questions when confidence is low/medium instead of making assumptions
- **Large Prompt Handling**: Zen-style simple solution for MCP's 25K token limit - automatically handles large PRs by asking Claude to save to file (#164, #165)
- **Code-Aware Analysis**: GitHub issue and PR analysis now fetches and analyzes actual code, not just descriptions (#151, #152, #154)
- **Architecture-Aware Detection**: Detects architectural concepts (auth, payment, API, etc.) from natural language and provides targeted analysis (#155, #158)

### Fixed
- **vibe_check_mentor Generic Advice**: Fixed critical bug where mentor provided template responses instead of contextual analysis (#167, #163)
  - Pattern detection now runs after context understanding
  - Reduced false positives by 50% for completion reports
  - Added negative indicators to anti_patterns.json
- **Pattern Detection Failures**: Fixed field name mismatch causing confidence: 0 failures (#163, #166)
  - Corrected "detected_patterns" vs "patterns" field access
  - Added missing ConfidenceScores.MEDIUM constant
- **Immediate Feedback Bug**: Fixed mentor always reporting "No concerning patterns" even when personas raised valid concerns (#156, #159)
  - Enhanced _generate_summary() to consider collaborative reasoning insights
  - Improved session management to maintain continuity
- **PR Analysis Bug**: Fixed critical issue where PR reviews only analyzed titles/descriptions, never the actual diff (#151, #153)

### Improvements
- **Enhanced Anti-Pattern Detection**: Added comprehensive negative indicators with weights to prevent false triggers
  - Completion indicators (weight -0.8)
  - Review indicators (weight -0.6)
  - Process descriptors (weight -0.4)
- **Better Error Handling**: Added try-except blocks for regex pattern failures with proper logging
- **Code Quality**: Added ConfidenceThresholds class to replace magic numbers throughout codebase
- **Session Management**: Fixed new session IDs being generated mid-conversation
- **Debug Logging**: Enhanced pattern detection visibility for troubleshooting

## [0.4.0] - 2025-06-19

### Added
- **Complete Strategy Pattern Architecture**: Configuration-driven response system replacing 375+ lines of hardcoded logic
- **Enhanced 2025 Technology Support**: Comprehensive LLM pricing, framework comparisons, and AI tool recommendations
- **YAML Configuration System**: All technology patterns and pricing data externalized to `tech_patterns.yaml`
- **Budget LLM Support**: DeepSeek R1 ($0.14/$2.19), GPT-4.1 nano ($0.075/$0.30), Claude 3.5 Haiku, Llama 4
- **Framework Comparisons**: Astro vs Next.js, Bun vs Node.js, LangChain vs LlamaIndex with specific use case advice
- **Database Rankings**: Vector DBs (Milvus > Weaviate ≈ Qdrant) and Graph DBs (FalkorDB vs Neo4j) with performance data
- **Comprehensive Test Suite**: 18 pytest tests with performance regression detection

### Changed  
- **MAJOR REFACTORING**: 413-line `generate_senior_engineer_response` method reduced to 25 lines using strategy pattern
- **File Size Reduction**: `vibe_mentor_enhanced.py` reduced from 1000+ lines to 588 lines (-40%)
- **Architecture**: Response generation centralized in priority-based strategy pattern
- **Configuration Management**: Singleton config loader with staleness detection and fallback handling
- **Constants**: Added `MAX_FEATURES=5`, `MAX_DECISION_POINTS=3` replacing magic numbers

### Fixed
- **Performance**: O(n*m) → O(1) pattern matching with compiled regex patterns  
- **Security**: ReDoS attack prevention with input validation and length limits
- **Code Quality**: All of Claude's code review issues addressed (duplicate logic, magic numbers, method complexity)
- **Error Handling**: Comprehensive try-catch blocks with meaningful fallback responses

### Performance
- **Context Extraction**: < 0.1s for large input processing
- **Strategy Selection**: < 0.5s for 1000 response generations
- **Pattern Matching**: LRU cache with compiled regex for O(1) lookup performance

### Technical Debt Eliminated
- Removed duplicate LLM comparison logic scattered across multiple methods
- Eliminated hardcoded responses (lines 356-649) in favor of configuration
- Consolidated helper methods (`_handle_llm_comparisons`, `_handle_framework_comparisons`) into strategy pattern
- Fixed all magic numbers with proper constants

### Testing
- Added comprehensive unit tests for strategy pattern components
- Performance regression tests to prevent O(n*m) issues
- Integration tests for end-to-end query flows
- Fallback configuration testing for error resilience

## [0.3.0] - 2025-06-19

### Added
- Model parameter support for Claude model selection (#125)
- Interrupt mode to vibe_check_mentor for quick interventions (#136)
- Security enhancements with comprehensive testing
- Enhanced PR review with file type analysis and model selection
- Improved issue analysis framework with logging enhancements

### Fixed
- Syntax errors in analyze_issue_nollm module
- String formatting issues in test files
- Try-except block structure in analysis workflows

### Security
- Added model parameter validation and comprehensive testing
- Enhanced security patterns in PR review workflows

## [0.2.0] - 2025-01-06

### Added
- AI Doom Loop Detection and Analysis Paralysis Prevention (Issue #116) (#122)
- Official Alternative Check for Integration Decisions (Issue #113)
- Async analysis system improvements (Issue #110) (#111)
- Claude PR Assistant workflow (#119)
- Chunked analysis for medium-sized PRs (Issue #103) (#108)
- Circuit breaker pattern for Claude CLI reliability (Issue #102)
- Async processing queue for massive PRs (Issue #104) (#109)
- CLAUDE.md.sample with doom loop instructions
- Extended technology coverage future roadmap documentation

### Fixed
- Correct test expectations for Supabase integration pattern detection (#120)

### Changed
- Centralized version management system with VERSION file
- Release automation script (scripts/release.sh)
- Version utilities in src/vibe_check/utils/version_utils.py
- Comprehensive versioning guidelines in CLAUDE.md
- CONTRIBUTING.md with detailed contribution guidelines
- Clear "Who is it for" section targeting decision makers at all levels
- Updated LICENSE from MIT to Apache 2.0
- Refactored version management to use centralized VERSION file
- **BREAKING**: Renamed docs/Product_Requirements_Document.md → docs/PRD.md
- **BREAKING**: Renamed docs/Technical_Implementation_Guide.md → docs/TECHNICAL.md
- Completely revamped README.md with prevention-focused value proposition
- Updated messaging to emphasize educational coaching and systematic failure prevention
- Improved tool descriptions with specific use cases and real-world impact data

## [0.1.0] - 2025-01-06

### Added
- Initial release of Vibe Check MCP
- Core anti-pattern detection engine with 87.5% accuracy
- FastMCP server integration for MCP protocol support
- Educational coaching system for engineering guidance
- GitHub integration for issues and PRs analysis
- Comprehensive pattern detection for engineering anti-patterns
- Documentation and technical implementation guides
- Test coverage with pytest framework
- Code quality tools (black, mypy, pylint, bandit)

### Features
- **Pattern Detection**: Detects engineering anti-patterns in code, issues, and PRs
- **Educational Content**: Provides coaching and guidance for better engineering practices
- **GitHub Integration**: Analyzes GitHub issues and pull requests
- **MCP Server**: Fully compatible with Model Context Protocol
- **Extensible Architecture**: Plugin-based pattern detection system

### Dependencies
- fastmcp>=2.5.2 (MCP protocol support)
- anthropic>=0.40.0 (AI integration)
- PyGithub>=2.1.1 (GitHub API)
- pytest>=7.4.3 (testing framework)
- And other quality assurance tools

[Unreleased]: https://github.com/kesslerio/vibe-check-mcp/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/kesslerio/vibe-check-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kesslerio/vibe-check-mcp/releases/tag/v0.1.0