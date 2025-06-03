# Technical Architecture Guide
## Vibe Check MCP: Anti-Pattern Detection System

**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Technical architecture documentation for engineering anti-pattern detection and educational coaching platform  
**Architecture**: Independent FastMCP Server with dual-mode analysis

---

## Executive Summary

This document outlines the technical architecture of Vibe Check MCP, a proven anti-pattern detection system that prevents systematic engineering failures through real-time pattern detection and educational coaching. The system is built as an independent FastMCP server designed for seamless integration with Claude Code workflows.

**Core Architecture Principles:**
- **Validation-First Development**: Proven detection algorithms before infrastructure building
- **Educational Focus**: Explain WHY patterns are problematic with real-world case studies  
- **Dual-Mode Analysis**: Fast pattern detection + Deep Claude-powered reasoning
- **MCP-Native Design**: Built specifically for Model Context Protocol integration

---

## System Architecture

### High-Level Architecture
```
Vibe Check MCP - Independent MCP Server Architecture
┌─────────────────────────────────────────────────────────────┐
│                    MCP Protocol Layer                      │
│  • Standardized tool/resource interfaces                   │
│  • JSON-RPC communication with Claude Code                 │
│  • Client-agnostic connectivity                            │
├─────────────────────────────────────────────────────────────┤
│                    FastMCP Server Core                     │
│  ┌─────────────────┬─────────────────┬───────────────────┐  │
│  │   MCP Tools     │ Educational     │   CLI Interface  │  │
│  │                 │ Content Engine  │                   │  │
│  │  • analyze_issue│ • WHY explanations│ • Fallback mode│  │
│  │  • analyze_code │ • HOW remediation │ • Power users  │  │
│  │  • analyze_text │ • Case studies   │ • Testing      │  │
│  │  • server_status│ • Confidence     │ • Development  │  │
│  └─────────────────┴─────────────────┴───────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Anti-Pattern Detection Engine           │
│  • Python AST analysis for structural patterns             │
│  • Regex-based pattern matching for text analysis          │
│  • Context-aware analysis with confidence scoring          │
│  • Knowledge base integration for case studies             │
├─────────────────────────────────────────────────────────────┤
│                    Integration Services                     │
│  • GitHub API client for issue/PR analysis                 │
│  • External Claude CLI integration for deep reasoning      │
│  • Configuration management system                         │
│  • Error handling and graceful degradation                 │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. MCP Protocol Layer
- **FastMCP Framework**: Provides MCP protocol compliance and tool registration
- **JSON-RPC Communication**: Standard protocol for Claude Code integration
- **Tool Schema Definition**: Structured interfaces for all analysis tools
- **Error Handling**: Graceful degradation with helpful error messages

#### 2. Core Analysis Engine
- **PatternDetector**: Main detection engine using AST analysis and regex patterns
- **EducationalContentGenerator**: Multi-level educational responses with case studies
- **ConfidenceScorer**: Weighted confidence calculation for pattern detection
- **KnowledgeBase**: Structured storage of patterns, case studies, and educational content

#### 3. Integration Services
- **GitHub Integration**: API client for fetching issues, PRs, and posting comments
- **External Claude CLI**: Integration for deep LLM-powered analysis
- **Configuration Management**: Environment-based configuration with secure defaults

---

## Core Detection Engine

### Pattern Detection Architecture

```python
# Core detection workflow
class PatternDetector:
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.confidence_scorer = ConfidenceScorer()
        self.patterns = self.load_anti_patterns()
    
    def analyze(self, content: str, context: str) -> List[DetectedPattern]:
        """Main analysis pipeline"""
        detected_patterns = []
        
        for pattern_id, pattern_config in self.patterns.items():
            detection_result = self._detect_pattern(
                content=content,
                pattern_config=pattern_config,
                context=context
            )
            
            if detection_result.detected:
                detected_patterns.append(detection_result)
        
        return self._rank_by_confidence(detected_patterns)
```

### Pattern Definition Structure

```json
{
  "infrastructure_without_implementation": {
    "name": "Infrastructure Without Implementation",
    "description": "Building custom solutions before testing standard approaches",
    "severity": "high",
    "detection_threshold": 0.6,
    "indicators": [
      {
        "regex": "(?i)custom\\s+(http|api)\\s+client",
        "weight": 0.4,
        "description": "Custom HTTP client mentioned"
      },
      {
        "regex": "(?i)build\\s+(from\\s+)?scratch",
        "weight": 0.3,
        "description": "Building from scratch mentioned"
      }
    ],
    "educational_content": {
      "why_problematic": "Building custom infrastructure before validating standard approaches led to wasted development time in the Cognee case study.",
      "case_study": "cognee_integration_failure",
      "prevention_checklist": [
        "Research official SDK documentation",
        "Test basic integration with 10 lines of code",
        "Document why standard approach is insufficient"
      ]
    }
  }
}
```

### Confidence Scoring Algorithm

```python
class ConfidenceScorer:
    def calculate_confidence(self, indicators_found: List[Indicator]) -> float:
        """Calculate weighted confidence score"""
        total_weight = sum(indicator.weight for indicator in indicators_found)
        
        # Apply diminishing returns for multiple weak indicators
        if len(indicators_found) > 3:
            total_weight *= 0.9
        
        # Context-specific adjustments
        if self._has_contradictory_evidence(indicators_found):
            total_weight *= 0.7
        
        return min(total_weight, 1.0)
```

---

## MCP Tools Implementation

### Tool Registry Pattern

```python
# FastMCP tool registration
from fastmcp import FastMCP

mcp = FastMCP("Vibe Check MCP")

@mcp.tool()
def analyze_github_issue(
    issue_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    analysis_mode: str = "quick",
    post_comment: bool = False,
    detail_level: str = "standard"
) -> dict:
    """
    Analyze GitHub issue for engineering anti-patterns.
    
    Supports dual-mode operation:
    - quick: Fast pattern detection without LLM calls
    - comprehensive: Deep Claude CLI analysis with educational content
    """
```

### Dual-Mode Analysis Architecture

```python
class DualModeAnalyzer:
    def __init__(self):
        self.fast_analyzer = FastPatternAnalyzer()
        self.deep_analyzer = ExternalClaudeAnalyzer()
    
    def analyze(self, content: str, mode: str) -> AnalysisResult:
        if mode == "quick":
            return self.fast_analyzer.analyze(content)
        elif mode == "comprehensive":
            return self.deep_analyzer.analyze(content)
        else:
            raise ValueError(f"Unknown analysis mode: {mode}")
```

### Tool Schema Design

```json
{
  "type": "object",
  "properties": {
    "issue_number": {
      "type": "integer",
      "description": "GitHub issue number to analyze"
    },
    "analysis_mode": {
      "type": "string",
      "enum": ["quick", "comprehensive"],
      "description": "Analysis depth - quick for fast feedback, comprehensive for deep reasoning"
    },
    "detail_level": {
      "type": "string", 
      "enum": ["brief", "standard", "comprehensive"],
      "description": "Educational content detail level"
    }
  },
  "required": ["issue_number"]
}
```

---

## Educational Content System

### Content Generation Pipeline

```python
class EducationalContentGenerator:
    def generate_response(
        self, 
        patterns: List[DetectedPattern],
        detail_level: str = "standard"
    ) -> EducationalResponse:
        """Generate multi-level educational content"""
        
        if not patterns:
            return self._generate_positive_feedback()
        
        primary_pattern = max(patterns, key=lambda p: p.confidence)
        
        content = {
            "summary": self._generate_summary(patterns),
            "primary_concern": self._explain_pattern(primary_pattern),
            "why_problematic": self._get_why_explanation(primary_pattern),
            "case_study": self._get_case_study(primary_pattern),
            "prevention_checklist": self._get_prevention_steps(primary_pattern),
            "alternative_approaches": self._get_alternatives(primary_pattern)
        }
        
        return self._format_by_detail_level(content, detail_level)
```

### Case Study Integration

```python
class CaseStudyManager:
    def get_case_study(self, pattern_type: str) -> CaseStudy:
        """Retrieve relevant real-world case study"""
        case_studies = {
            "infrastructure_without_implementation": {
                "title": "Cognee Integration Learning Experience", 
                "timeline": "Several days of development time",
                "root_cause": "Built custom HTTP servers instead of using cognee.add() → cognee.cognify() → cognee.search()",
                "impact": "Delayed integration due to unnecessary complexity",
                "lesson": "Always test standard API approaches with minimal POC before building custom infrastructure"
            }
        }
        
        return case_studies.get(pattern_type, self._get_default_case_study())
```

---

## External Claude CLI Integration

### Architecture for Deep Analysis

```python
class ExternalClaudeIntegration:
    def __init__(self):
        self.claude_cli_name = os.getenv("CLAUDE_CLI_NAME", "claude")
        self.timeout_seconds = 60
        
    def analyze_with_claude(
        self, 
        content: str, 
        task_type: str = "general"
    ) -> str:
        """Execute Claude CLI for deep reasoning"""
        
        system_prompt = self._get_system_prompt(task_type)
        
        try:
            result = subprocess.run([
                self.claude_cli_name, 
                "-p", 
                f"{system_prompt}\n\nAnalyze this content:\n{content}"
            ], 
            capture_output=True, 
            text=True, 
            timeout=self.timeout_seconds
            )
            
            if result.returncode == 0:
                return self._parse_claude_response(result.stdout)
            else:
                raise ClaudeIntegrationError(f"Claude CLI failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise ClaudeIntegrationError("Claude CLI timeout - see diagnostics")
```

### System Prompts for Specialized Analysis

```python
def _get_system_prompt(self, task_type: str) -> str:
    """Get specialized system prompt for analysis type"""
    prompts = {
        "code_analysis": """
        You are an expert software architect focused on anti-pattern detection.
        Analyze the provided code for these specific patterns:
        1. Infrastructure Without Implementation - custom solutions vs standard APIs
        2. Complexity Escalation - unnecessary abstraction layers
        3. Symptom-Driven Development - treating symptoms vs root causes
        
        Provide educational explanations with real-world consequences.
        """,
        
        "issue_analysis": """
        You are an engineering coach specializing in preventing systematic failures.
        Review this GitHub issue for planning anti-patterns that lead to technical debt.
        Focus on the Cognee case study lessons about validating standard approaches first.
        """,
        
        "pr_review": """
        You are a senior technical reviewer with expertise in anti-pattern prevention.
        Review this PR for patterns that compound into long-term maintenance issues.
        Provide constructive coaching with specific improvement suggestions.
        """
    }
    
    return prompts.get(task_type, prompts["code_analysis"])
```

---

## Performance & Scalability

### Caching Strategy

```python
class AnalysisCache:
    def __init__(self, ttl_hours: int = 1):
        self.cache_dir = Path("~/.vibe-check/cache").expanduser()
        self.ttl = timedelta(hours=ttl_hours)
    
    def get_cached_result(self, content_hash: str) -> Optional[dict]:
        """Retrieve cached analysis if still valid"""
        cache_file = self.cache_dir / f"{content_hash}.json"
        
        if not cache_file.exists():
            return None
            
        cached_data = json.loads(cache_file.read_text())
        cache_time = datetime.fromisoformat(cached_data["timestamp"])
        
        if datetime.now() - cache_time > self.ttl:
            cache_file.unlink()  # Remove expired cache
            return None
            
        return cached_data["result"]
```

### Async Analysis Pipeline

```python
class AsyncAnalyzer:
    async def analyze_multiple_items(
        self, 
        items: List[AnalysisItem]
    ) -> List[AnalysisResult]:
        """Analyze multiple items concurrently"""
        
        semaphore = asyncio.Semaphore(3)  # Limit concurrent analyses
        
        async def analyze_with_limit(item):
            async with semaphore:
                return await self._analyze_single_item(item)
        
        tasks = [analyze_with_limit(item) for item in items]
        return await asyncio.gather(*tasks)
```

---

## Testing Strategy

### Test Architecture

```python
# Core detection testing
class TestPatternDetection:
    def test_infrastructure_pattern_detection(self):
        """Test detection of infrastructure-without-implementation"""
        detector = PatternDetector()
        
        # Known anti-pattern content
        issue_content = """
        We need to integrate with Stripe API for payments.
        I'm planning to build a custom HTTP client since their SDK 
        might be limiting for our use case.
        """
        
        patterns = detector.analyze_issue_content(
            title="Custom Stripe Integration",
            body=issue_content
        )
        
        assert len(patterns) > 0
        assert patterns[0]["type"] == "infrastructure_without_implementation"
        assert patterns[0]["confidence"] > 0.7

    def test_no_false_positives(self):
        """Ensure good practices don't trigger false positives"""
        detector = PatternDetector()
        
        # Good practice content
        good_content = """
        We need to integrate with Stripe for payments.
        I've reviewed their official Python SDK documentation
        and will use stripe.Customer.create() and stripe.PaymentIntent.confirm()
        as recommended in their quickstart guide.
        """
        
        patterns = detector.analyze_issue_content(
            title="Stripe Integration Using Official SDK", 
            body=good_content
        )
        
        # Should not detect any anti-patterns
        assert len(patterns) == 0
```

### Integration Testing

```python
@pytest.mark.integration
class TestMCPIntegration:
    def test_analyze_github_issue_tool(self):
        """Test the full MCP tool pipeline"""
        result = analyze_github_issue(
            issue_number=1,
            repository="kesslerio/vibe-check-mcp-test",
            analysis_mode="quick"
        )
        
        assert "analysis_mode" in result
        assert "patterns_detected" in result  
        assert "educational_content" in result
        assert isinstance(result["patterns_detected"], list)
```

---

## Security & Privacy

### Data Handling Principles

```python
class PrivacyManager:
    """Ensure user data privacy and security"""
    
    @staticmethod
    def sanitize_content(content: str) -> str:
        """Remove potentially sensitive information"""
        patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b(?:\d[ -]*?){13,16}\b',  # Credit card numbers
            r'\b[A-Za-z0-9]{20,}\b'      # API keys/tokens (basic heuristic)
        ]
        
        sanitized = content
        for pattern in patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        
        return sanitized
    
    @staticmethod
    def validate_github_permissions(token: str, repository: str) -> bool:
        """Validate minimal required GitHub permissions"""
        # Implementation for permission validation
        pass
```

### Local Processing

- **No External Data Transmission**: Analysis happens locally except for user-initiated GitHub API calls
- **Configurable Privacy**: Users control what data is processed and cached
- **Secure Defaults**: No sensitive data logging or external analytics
- **Token Management**: Users provide their own GitHub tokens with minimal required permissions

---

## Deployment Architecture

### MCP Server Configuration

```json
{
  "vibe-check": {
    "type": "stdio",
    "command": "python",
    "args": ["-m", "vibe_check.server"],
    "env": {
      "PYTHONPATH": "/path/to/vibe-check-mcp/src",
      "GITHUB_TOKEN": "${GITHUB_TOKEN}",
      "VIBE_CHECK_DEV_MODE": "false"
    }
  }
}
```

### Environment Configuration

```python
class Config:
    """Environment-based configuration"""
    
    # GitHub Integration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    DEFAULT_REPOSITORY = os.getenv("VIBE_CHECK_DEFAULT_REPO", "kesslerio/vibe-check-mcp")
    
    # Claude CLI Integration  
    CLAUDE_CLI_NAME = os.getenv("CLAUDE_CLI_NAME", "claude")
    CLAUDE_CLI_TIMEOUT = int(os.getenv("CLAUDE_CLI_TIMEOUT", "60"))
    
    # Analysis Configuration
    CACHE_TTL_HOURS = int(os.getenv("VIBE_CHECK_CACHE_TTL", "1"))
    DEV_MODE = os.getenv("VIBE_CHECK_DEV_MODE", "false").lower() == "true"
    
    # Paths
    CACHE_DIR = Path(os.getenv("VIBE_CHECK_CACHE_DIR", "~/.vibe-check/cache"))
    DATA_DIR = Path(os.getenv("VIBE_CHECK_DATA_DIR", "./data"))
```

---

## Monitoring & Observability

### Local Analytics

```python
class LocalMetrics:
    """Local performance monitoring without external transmission"""
    
    def log_analysis_performance(
        self, 
        tool_name: str, 
        duration: float, 
        patterns_found: int,
        success: bool
    ):
        """Log performance metrics for optimization"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "duration_seconds": duration,
            "patterns_detected": patterns_found,
            "success": success
        }
        
        self._append_to_metrics_log(metrics)
    
    def get_performance_summary(self, days: int = 7) -> dict:
        """Get performance summary for troubleshooting"""
        # Implementation for metrics aggregation
        pass
```

### Health Checks

```python
@mcp.tool()
def server_status() -> dict:
    """Get comprehensive server status and capabilities"""
    return {
        "status": "healthy",
        "version": get_version(),
        "capabilities": {
            "github_integration": bool(Config.GITHUB_TOKEN),
            "claude_cli_integration": check_claude_cli_available(),
            "pattern_detection": True,
            "educational_content": True
        },
        "performance": {
            "cache_size": get_cache_size(),
            "patterns_loaded": len(get_loaded_patterns()),
            "uptime_seconds": get_uptime()
        }
    }
```

---

## Future Architecture Considerations

### Extensibility

- **Plugin Architecture**: Support for custom pattern definitions
- **Language Support**: Modular language analyzers for JavaScript, Go, Rust
- **Integration Points**: Webhooks for CI/CD pipeline integration
- **Community Patterns**: Framework for community-contributed patterns

### Scalability

- **Distributed Analysis**: Support for analyzing large codebases
- **Caching Optimization**: Intelligent cache invalidation and compression  
- **Resource Management**: Memory-efficient analysis for large files
- **Async Processing**: Non-blocking analysis pipeline for responsiveness

This technical architecture provides the foundation for a robust, scalable, and maintainable anti-pattern detection system that integrates seamlessly with Claude Code workflows while maintaining strong privacy and performance characteristics.