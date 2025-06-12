# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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