# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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