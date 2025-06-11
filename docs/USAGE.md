# Vibe Check MCP Usage Guide

**Stop building the wrong thing before you waste months on it.**

Complete guide for using Vibe Check MCP to catch engineering anti-patterns at decision points - with crystal clear LLM vs no-LLM tool distinction for fast feedback or deep educational coaching.

## Quick Start

Once you have Vibe Check MCP configured (see [README.md](../README.md)), you can analyze content using natural language commands with two distinct approaches:

- **🚀 Fast Analysis (_nollm)**: Direct pattern detection without LLM calls
- **🧠 Deep Analysis (_llm)**: Comprehensive LLM-powered reasoning via Claude CLI

## Tool Naming Convention

All tools follow the crystal clear `_llm` / `_nollm` naming pattern:

### Fast Direct Analysis (🚀 _nollm)
- `analyze_text_nollm` - Fast pattern detection on text
- `analyze_issue_nollm` - Direct GitHub issue analysis  
- `analyze_pr_nollm` - Fast PR metrics and analysis

### LLM-Powered Analysis (🧠 _llm)
- `analyze_text_llm` - Deep Claude CLI text analysis
- `analyze_issue_llm` - Comprehensive GitHub issue reasoning
- `analyze_pr_llm` - Full Claude CLI PR review
- `analyze_code_llm` - Deep code analysis with LLM reasoning

### Integration Decision Tools (🔍 New in Issue #113)
- `check_integration_alternatives` - Official alternative check for integration decisions
- `analyze_integration_decision_text` - Text analysis for integration anti-patterns
- `integration_decision_framework` - Structured decision framework with Clear Thought integration
- `integration_research_with_websearch` - Enhanced integration research with real-time web search

### Integration Pattern Detection Tools (🚀 New in Issue #112) 
- `analyze_integration_patterns` - Fast integration pattern detection for vibe coding safety net
- `quick_tech_scan` - Ultra-fast technology scan for immediate feedback
- `analyze_integration_effort` - Integration effort-complexity analysis

### System Tools
- `claude_cli_status` - Check Claude CLI availability
- `claude_cli_diagnostics` - Diagnose Claude CLI issues
- `server_status` - MCP server status and capabilities

## Natural Language Commands

### Text Analysis

**🚀 Fast Pattern Detection**:
```
"Quick vibe check this text"
"Fast pattern analysis of this code"
"Basic analysis of this content"
```

**🧠 Deep LLM Analysis**:
```  
"Deep analyze this text with full reasoning"
"Get Claude's comprehensive analysis of this content"
"Full LLM analysis of this text"
```

### GitHub Issue Analysis

**🚀 Fast Issue Analysis**:
```
"Quick vibe check issue 42"
"Fast analysis of issue 23"
"Basic issue check 15"
```

**🧠 Deep Issue Analysis**:
```
"Deep vibe check issue 42 with full Claude analysis"
"Comprehensive LLM analysis of issue 23"
"Get Claude's detailed review of issue 15"
```

### Pull Request Analysis

**🚀 Fast PR Analysis**:
```
"Quick PR check on #44"
"Fast analysis of PR 32"
"Basic vibe check PR 18"
```

**🧠 Deep PR Analysis**:
```
"Full Claude review of PR 44"
"Comprehensive LLM analysis of PR 32"
"Deep vibe check PR 18 with Claude reasoning"
```

### Code Analysis

**🧠 Deep Code Analysis** (LLM-only):
```
"Analyze this code for anti-patterns with Claude"
"Get Claude's security review of this function"
"Deep code analysis with full LLM reasoning"
```

### Integration Decision Analysis (🔍 New)

**Official Alternative Check**:
```
"Check cognee integration alternatives"
"Validate docker vs custom approach for supabase"
"Integration decision check for claude api"
```

**Text Analysis for Integration Patterns**:
```
"Analyze this integration plan for anti-patterns"
"Check this text for custom development red flags"
"Integration vibe check of this technical document"
```

**Decision Framework Analysis**:
```
"Integration decision framework for cognee vs custom"
"Structured analysis of docker vs build approach"
"Clear thought framework for supabase integration"
```

**Web-Enhanced Research** (🌐 New):
```
"Research new-framework with web search"
"Find official deployment options for emerging-tool"
"Web search enhanced integration analysis"
```

### Integration Pattern Detection (🚀 New in Issue #112)

**Fast Integration Pattern Analysis**:
```
"Vibe check this integration plan for anti-patterns"
"Analyze for integration over-engineering" 
"Fast pattern detection on this PR description"
```

**Ultra-Fast Technology Scan**:
```
"Quick tech scan for known integrations"
"Scan for Cognee, Supabase, OpenAI usage"
"Instant technology detection"
```

**Effort-Complexity Analysis**:
```
"Analyze integration effort complexity"
"Check if development effort matches integration complexity"
"Effort-value analysis for this implementation"
```

## When to Use Each Tool Type

### Use Fast Analysis (_nollm) When:
- **Speed matters**: Development workflow integration
- **Quick feedback**: Basic pattern detection needed
- **Cost conscious**: Avoiding LLM API usage
- **Simple checks**: Metrics, validation, basic patterns

### Use LLM Analysis (_llm) When:
- **Depth matters**: Complex reasoning required
- **Quality focus**: Comprehensive analysis needed
- **Learning**: Educational explanations wanted
- **Complex patterns**: Sophisticated anti-pattern detection

### Use Integration Decision Tools When:
- **Planning integrations**: Before building custom solutions
- **Technology evaluation**: Comparing official vs custom approaches
- **Red flag detection**: Identifying unnecessary custom development
- **Decision documentation**: Structured integration decision frameworks

### Use Integration Pattern Detection Tools When:
- **Real-time development**: Instant feedback during coding workflow
- **PR/Issue review**: Fast pattern detection in development content
- **Technology scanning**: Quick identification of integration technologies
- **Effort validation**: Checking if development complexity matches integration needs
- **Anti-pattern prevention**: Catching integration over-engineering early

## Command Line Interface

### Direct CLI Usage

Set up a shell alias for natural command syntax:

```bash
# Add to your ~/.bashrc, ~/.zshrc, or ~/.fish_config
alias vibe='python -m vibe_check.cli'

# Fast analysis
vibe quick check issue 31
vibe fast PR 44

# Deep analysis  
vibe deep issue 31
vibe comprehensive PR 44
```

## GitHub Integration

### Issue Analysis Examples

**Fast GitHub Issue Analysis**:
```bash
# Basic pattern detection
vibe quick issue 31
vibe fast check issue 42 in facebook/react
```

**Deep GitHub Issue Analysis**:
```bash
# Comprehensive Claude-powered analysis
vibe deep issue 31
vibe comprehensive issue 42 in microsoft/typescript
```

### Pull Request Analysis Examples

**Fast PR Analysis**:
```bash
# Quick metrics and basic patterns
vibe quick PR 44
vibe fast check PR 32
```

**Deep PR Analysis**:
```bash
# Full Claude CLI review
vibe deep PR 44  
vibe comprehensive PR 32
```

## Educational Content Levels

All tools support three detail levels:

- **brief**: Concise summaries
- **standard**: Balanced detail (default)
- **comprehensive**: Full educational content

## Cost and Performance Considerations

### Fast Tools (_nollm)
- **Performance**: Sub-second response times
- **Cost**: No LLM API usage
- **Use case**: Development workflow, quick checks

### LLM Tools (_llm)  
- **Performance**: 10-60 seconds (Claude CLI execution)
- **Cost**: Uses Claude API credits via Claude CLI
- **Use case**: Comprehensive analysis, learning, complex reasoning

## Configuration

### Environment Variables

```bash
# GitHub integration (optional)
export GITHUB_TOKEN="your_github_token"

# Claude CLI configuration (for _llm tools)
export CLAUDE_CLI_NAME="claude"  # Custom CLI name if needed
```

### Claude CLI Setup

For LLM-powered tools (`_llm`), ensure Claude CLI is installed:

```bash
# Check Claude CLI status
claude --version

# Test integration
python -c "from vibe_check.server import mcp; print('✅ Ready')"
```

## Examples

### Text Analysis

```python
# Fast pattern detection
result = analyze_text_nollm("Your text here", detail_level="standard")

# Deep LLM analysis  
result = analyze_text_llm("Your text here", task_type="code_analysis")
```

### Issue Analysis

```python
# Fast issue analysis
result = analyze_issue_nollm(42, repository="owner/repo")

# Deep issue analysis
result = analyze_issue_llm(42, repository="owner/repo", post_comment=True)
```

### Pull Request Analysis

```python
# Fast PR analysis
result = analyze_pr_nollm(44, repository="owner/repo")

# Deep PR analysis  
result = analyze_pr_llm("PR diff content", pr_description="Feature: New login")
```

## Integration Decision Tools - Detailed Guide

### Overview

The integration decision tools (Issue #113) prevent unnecessary custom development by checking for official alternatives before building custom solutions. Based on real-world case studies like the Cognee integration failure where 2+ weeks were spent building custom REST servers instead of using the official Docker container.

### Tool 1: check_integration_alternatives

**Purpose**: Check if a technology provides official solutions for your custom features.

**Sample Prompts**:
```
"Check cognee integration with custom REST server, JWT authentication"
"Validate supabase approach for custom auth, manual database"
"Integration check for docker with custom container management"
```

**Real-World Example**:
```python
# Cognee Case Study Scenario
check_integration_alternatives(
    technology="cognee",
    custom_features="custom REST server, JWT authentication, storage management",
    description="Building custom Cognee integration for our application"
)
```

**Expected Response**:
```json
{
  "status": "success",
  "technology": "cognee",
  "warning_level": "warning",
  "official_solutions": ["Docker: cognee/cognee:main"],
  "red_flags_detected": ["Custom custom REST server (official alternative available)"],
  "research_required": true,
  "custom_justification_needed": true,
  "recommendation": "🚨 STOP: Official cognee solution likely covers your needs. Test official approach first before custom development.",
  "next_steps": [
    "Test official cognee solution with your requirements",
    "Review documentation: https://cognee.ai/docs",
    "Document specific gaps in official solution that justify custom development"
  ]
}
```

### Tool 2: analyze_integration_decision_text

**Purpose**: Analyze text content for integration anti-patterns and provide recommendations.

**Sample Prompts**:
```
"Analyze this integration plan for anti-patterns"
"Check this technical document for custom development red flags"
"Integration vibe check of this architecture proposal"
```

**Real-World Example**:
```python
text = """
We're planning to build a custom FastAPI server for Cognee integration.
The server will handle JWT authentication and manage storage configurations.
We'll also need custom Supabase authentication instead of using their SDK.
"""

analyze_integration_decision_text(text, detail_level="comprehensive")
```

**Expected Response**:
```json
{
  "status": "success",
  "detected_technologies": ["cognee", "supabase"],
  "detected_custom_work": ["custom", "fastapi", "authentication", "storage"],
  "warning_level": "warning",
  "recommendations": [
    {
      "technology": "cognee",
      "analysis": {
        "warning_level": "warning",
        "official_solutions": ["Docker: cognee/cognee:main"],
        "recommendation": "⚠️ CAUTION: Official cognee solution may cover your needs."
      }
    }
  ],
  "educational_content": {
    "integration_best_practices": [
      "Always research official deployment options first",
      "Test official solutions with basic requirements"
    ],
    "common_anti_patterns": [
      "Building custom REST servers when official containers exist",
      "Manual authentication when SDKs provide it"
    ]
  },
  "case_studies": {
    "cognee_failure": {
      "problem": "2+ weeks spent building custom FastAPI server",
      "solution": "cognee/cognee:main Docker container available",
      "lesson": "Official containers often provide complete functionality"
    }
  }
}
```

### Tool 3: integration_decision_framework

**Purpose**: Provide structured decision framework with Clear Thought analysis for integration approaches.

**Sample Prompts**:
```
"Integration decision framework for cognee vs custom"
"Structured analysis of docker vs build approach for supabase"
"Clear thought framework for claude api integration"
```

**Real-World Example**:
```python
integration_decision_framework(
    technology="cognee",
    custom_features="REST API, authentication, storage",
    decision_statement="Choose between official Cognee container vs custom development",
    analysis_type="weighted-criteria"
)
```

**Expected Response**:
```json
{
  "status": "success",
  "decision_statement": "Choose between official Cognee container vs custom development",
  "technology": "cognee",
  "analysis_type": "weighted-criteria",
  "integration_analysis": {
    "warning_level": "warning",
    "official_solutions": ["Docker: cognee/cognee:main"],
    "red_flags_detected": ["Custom REST API (official alternative available)"]
  },
  "decision_options": [
    {
      "option": "Official Solution",
      "pros": ["Vendor maintained and supported", "Production ready and tested"],
      "cons": ["Less customization control", "Potential feature limitations"],
      "effort_score": 2,
      "risk_score": 1,
      "maintenance_score": 1
    },
    {
      "option": "Custom Development",
      "pros": ["Full control over implementation", "Exact requirement matching"],
      "cons": ["High development time", "Ongoing maintenance burden"],
      "effort_score": 8,
      "risk_score": 6,
      "maintenance_score": 8
    }
  ],
  "scoring_matrix": {
    "official_solution": {
      "development_time": 9,
      "maintenance_burden": 9,
      "reliability_support": 9,
      "customization_needs": 6
    },
    "custom_development": {
      "development_time": 3,
      "maintenance_burden": 2,
      "reliability_support": 5,
      "customization_needs": 9
    }
  },
  "clear_thought_integration": {
    "mental_model": "first_principles",
    "reasoning_approach": "Start with the simplest solution that could work",
    "validation_steps": [
      "Test official cognee solution with actual requirements",
      "Document specific gaps that justify custom development",
      "Estimate total cost of ownership for both approaches"
    ]
  }
}
```

### Common Use Cases

#### 1. Pre-Development Integration Check
```bash
# Before starting integration work
vibe check cognee integration alternatives
```

#### 2. Architecture Review
```bash
# Review technical documents for integration anti-patterns
vibe analyze integration plan for red flags
```

#### 3. Decision Documentation
```bash
# Generate structured decision framework
vibe integration framework cognee vs custom
```

#### 4. Team Education
```bash
# Comprehensive analysis with case studies
vibe analyze integration text comprehensive
```

### Supported Technologies

The tool includes knowledge for popular technologies:
- **Cognee**: Official Docker container, REST API, authentication
- **Supabase**: Official SDKs, authentication, database, storage
- **Claude**: Official SDK, chat completions, function calling
- **OpenAI**: Official SDK, completions, embeddings
- **GitHub**: Official SDKs, repository management, APIs
- **Docker**: Official SDK, container management
- **Kubernetes**: Official client, pod/service management

### Warning Levels

- **🚨 Critical**: 3+ red flags detected, immediate action required
- **⚠️ Warning**: 2+ red flags detected, careful evaluation needed
- **🔍 Caution**: 1 red flag or many official features available
- **✅ None**: No red flags detected, proceed with comparison

### Red Flags Detected

Common patterns that trigger warnings:
- **Custom REST server** when official containers exist
- **Manual authentication** when SDKs provide it
- **Custom HTTP clients** when official SDKs exist
- **Environment forcing** instead of proper configuration
- **Manual API calls** when official clients available

## 🌐 Web Search Integration Architecture

### How Integration Analysis Works

The integration decision tools use a **hybrid approach** combining static knowledge with real-time web search:

#### **1. Static Knowledge Base** (`data/integration_knowledge_base.json`)
- **Pre-curated data** for popular technologies (Cognee, Supabase, Claude, etc.)
- **Instant response** for known technologies
- **Comprehensive red flag patterns** based on real-world case studies
- **Performance**: Sub-second analysis for known technologies

#### **2. Web Search Enhancement** (`integration_research_with_websearch`)
- **Real-time research** for unknown or emerging technologies
- **Official documentation discovery** via targeted search queries
- **Docker Hub container detection** with official image verification
- **SDK and API client discovery** across package managers
- **Performance**: 10-30 seconds for comprehensive web research

### Search Strategy & Methodology

#### **Automated Search Queries**:
```bash
# Official Documentation Discovery
"{technology} official documentation deployment"
"{technology} site:docs.* OR site:github.com"

# Container & Deployment Options
"{technology} official docker container site:hub.docker.com"
"{technology} deployment guide best practices"

# SDK & API Discovery
"{technology} official SDK OR client library"
"{technology} site:npmjs.com OR site:pypi.org"
"{technology} site:deepwiki.com"  # For public GitHub repos

# Comparison Research
"{technology} vs custom implementation"
"{technology} official vs community solutions"
```

#### **Search Sources Prioritized**:
1. **Official Documentation Sites** (`docs.*`, vendor sites)
2. **Official GitHub Repositories** (`github.com/[vendor]`)
3. **DeepWiki Documentation** (`deepwiki.com` - excellent for public GitHub repo understanding)
4. **Docker Hub Official Images** (`hub.docker.com`)
5. **Package Managers** (npm, PyPI, Maven, etc.)
6. **Community Discussions** (Stack Overflow, Reddit)

#### **Validation Process**:
1. **Authenticity Verification**: Official vendor endorsement check
2. **Maintenance Status**: Recent updates and active development
3. **Community Support**: Documentation quality and usage patterns
4. **Production Readiness**: Stability and enterprise adoption

### Tool Selection Guide

#### **Use Static Analysis** (`check_integration_alternatives`) When:
- ✅ **Known technologies** in the knowledge base
- ✅ **Fast decisions** required in development workflow
- ✅ **Offline environment** or limited internet access
- ✅ **Cost-conscious** scenarios avoiding web search API calls

#### **Use Web-Enhanced Research** (`integration_research_with_websearch`) When:
- 🌐 **New or emerging technologies** not in knowledge base
- 🌐 **Comprehensive research** needed for critical decisions
- 🌐 **Up-to-date information** required for rapidly evolving tools
- 🌐 **Unknown vendor landscape** requiring discovery

### Example: New Technology Research

```python
# Research a new technology with web search
integration_research_with_websearch(
    technology="newtech-framework",
    custom_features="REST API, authentication, data processing",
    search_depth="advanced"
)
```

**Expected Web Search Process**:
1. **Documentation Search**: `newtech-framework official documentation deployment`
2. **Container Discovery**: `newtech-framework official docker container site:hub.docker.com`
3. **SDK Research**: `newtech-framework official SDK OR client library`
4. **Comparison Analysis**: `newtech-framework vs custom implementation`

**Enhanced Response Includes**:
- **Search queries executed** and results found
- **Official documentation links** discovered
- **Container availability** on Docker Hub
- **SDK options** across different languages
- **Research methodology** for manual validation
- **Confidence level** based on search results quality

### Web Search Limitations & Fallbacks

#### **Rate Limiting & Reliability**:
- **Graceful degradation** to static knowledge base if web search fails
- **Timeout handling** with fallback recommendations
- **Search result validation** to avoid false positives

#### **Search Quality Indicators**:
- **High Confidence**: Official vendor sites, GitHub orgs, Docker Hub verified
- **Medium Confidence**: Well-documented community projects
- **Low Confidence**: Limited or conflicting information found
- **Manual Research Required**: No clear official alternatives found

### Privacy & Performance Considerations

#### **Data Handling**:
- **No persistent storage** of search results
- **Query anonymization** where possible
- **Minimal data collection** focused on technical information

#### **Performance Optimization**:
- **Parallel search execution** for multiple queries
- **Result caching** for recent searches (session-based)
- **Intelligent query selection** based on technology patterns

This hybrid approach ensures you get **instant feedback** for known technologies while enabling **comprehensive research** for new or emerging tools, preventing both the Cognee-style failures (missing obvious official solutions) and the opposite problem (building custom solutions for truly novel technologies without alternatives).

## 🚀 Integration Pattern Detection Tools - Real-Time Vibe Coding Safety Net

### Overview

The Integration Pattern Detection tools (Issue #112) provide real-time anti-pattern detection specifically designed to prevent engineering disasters like the Cognee case study. These tools work seamlessly via MCP to catch integration over-engineering before it happens.

**Key Innovation**: Unlike traditional code analysis that happens after development, these tools provide **instant feedback during the planning and development process**, preventing unnecessary custom development before it starts.

### Real-Time MCP Usage

#### How the Tools Work in Real-Time:

1. **Sub-Second Technology Recognition**: Instantly detects Cognee, Supabase, OpenAI, Claude mentions
2. **Immediate Red Flag Detection**: Flags custom development when official alternatives exist  
3. **Instant Recommendations**: Provides specific next steps with official alternatives
4. **Seamless Workflow Integration**: Works with any MCP-compatible development environment

#### Tool 1: analyze_integration_patterns

**Purpose**: Comprehensive real-time integration pattern analysis with sub-second response.

**Sample Prompts**:
```
"Vibe check this integration plan for anti-patterns"
"Analyze this PR description for integration over-engineering"
"Fast pattern detection on this technical document"
```

**Real-World Example**:
```python
# Input: PR description mentioning custom Cognee development
analyze_integration_patterns(
    content="""
    We're building a custom FastAPI server for Cognee integration.
    The server will handle JWT authentication and manage storage configurations.
    This is part of our 2000+ line integration implementation.
    """,
    detail_level="standard"
)
```

**Expected Response**:
```json
{
  "status": "analysis_complete",
  "warning_level": "critical",
  "technologies_detected": [
    {
      "technology": "cognee",
      "confidence": 0.9,
      "official_solution": "cognee/cognee:main Docker container with built-in REST API",
      "indicators": ["mentions cognee", "cognee integration context"]
    }
  ],
  "anti_patterns_detected": [
    {
      "pattern": "integration_over_engineering",
      "detected": true,
      "confidence": 0.8,
      "evidence": ["custom server for managed service", "custom integration for known tech"]
    }
  ],
  "recommendations": [
    "🚨 Avoid custom REST server for cognee - official alternative available",
    "✅ Test official cognee solution: cognee/cognee:main Docker container",
    "📏 High line count detected - verify this complexity is necessary for integration"
  ],
  "research_questions": [
    "Have you tested the official cognee solution with your requirements?",
    "What specific features does the official cognee solution lack?",
    "Why is custom development necessary instead of using cognee/cognee:main Docker container?"
  ]
}
```

#### Tool 2: quick_tech_scan

**Purpose**: Ultra-fast technology detection for immediate alerts (sub-100ms response).

**Sample Prompts**:
```
"Quick tech scan for known integrations"
"Scan for Cognee, Supabase, OpenAI usage"
"Instant technology detection"
```

**Real-World Example**:
```python
# Ultra-fast scan during code review
quick_tech_scan("Using Supabase for auth and Cognee for knowledge management")
```

**Expected Response**:
```json
{
  "status": "technologies_detected", 
  "technologies": [
    {
      "technology": "supabase",
      "confidence": 0.8,
      "official_solution": "Supabase official SDKs (@supabase/supabase-js, supabase-py)",
      "immediate_action": "✅ Check official supabase solution before custom development",
      "red_flags": ["custom auth", "manual database"],
      "warning": "⚠️ Avoid custom custom auth - official alternative available"
    },
    {
      "technology": "cognee", 
      "confidence": 0.7,
      "official_solution": "cognee/cognee:main Docker container",
      "immediate_action": "✅ Check official cognee solution before custom development"
    }
  ],
  "warning_level": "caution",
  "quick_recommendations": [
    "Research supabase official solution",
    "Research cognee official solution"
  ]
}
```

#### Tool 3: analyze_integration_effort

**Purpose**: Effort-complexity analysis to identify potential over-engineering.

**Sample Prompts**:
```
"Analyze integration effort complexity"
"Check if development effort matches integration complexity"
"Effort-value analysis for this implementation"
```

**Real-World Example**:
```python
# PR with high line count for integration
analyze_integration_effort(
    content="Custom Cognee integration with FastAPI and JWT",
    lines_added=1800,
    lines_deleted=200, 
    files_changed=15
)
```

**Expected Response**:
```json
{
  "status": "effort_analysis_complete",
  "detected_technologies": ["cognee"],
  "pr_metrics": {
    "additions": 1800,
    "deletions": 200,
    "changed_files": 15
  },
  "complexity_assessment": "high",
  "warning": "🚨 2000 lines for integration - verify necessity",
  "technology_effort_analysis": [
    {
      "technology": "cognee",
      "official_solution": "cognee/cognee:main Docker container",
      "effort_question": "Is custom development effort justified vs cognee/cognee:main Docker container?",
      "recommendation": "Test cognee/cognee:main Docker container with realistic requirements first"
    }
  ],
  "recommendations": [
    "✅ Test official cognee solution: cognee/cognee:main Docker container",
    "📏 High line count detected - verify this complexity is necessary for integration",
    "⏱️ Extended timeline detected - consider official alternatives first"
  ]
}
```

### Performance Characteristics

#### Real-Time Performance Metrics:
- **quick_tech_scan**: <100ms response time
- **analyze_integration_patterns**: <500ms for standard analysis  
- **analyze_integration_effort**: <300ms with PR metrics
- **Technology Recognition**: Instant detection of 7+ technologies
- **Concurrent Usage**: Supports multiple simultaneous MCP calls

#### Workflow Integration:
```bash
# Development workflow examples
vibe analyze integration patterns "Building custom Cognee server"
vibe quick tech scan "PR: Add Supabase integration" 
vibe effort analysis "Custom auth implementation - 1500 lines"
```

### Supported Technologies & Red Flags

#### Technologies Covered:
- **Cognee**: Docker container, REST API, JWT authentication
- **Supabase**: Official SDKs, authentication, database
- **OpenAI**: Python SDK, API clients, embeddings
- **Claude**: Anthropic SDK, messages API, function calling
- **GitHub**: Official SDKs, repository management
- **Docker**: Official SDK, container management
- **Kubernetes**: Official client, pod/service management

#### Red Flag Patterns Detected:
- **Custom REST servers** when official containers exist
- **Manual authentication** when SDKs provide it  
- **Custom HTTP clients** when official SDKs exist
- **Environment forcing** instead of proper configuration
- **Manual API calls** when official clients available
- **High line counts** for standard integrations (>1000 lines)
- **Extended timelines** for simple integrations (weeks/months)

### Real-World Impact & Case Studies

#### Cognee Case Study Prevention:
**Problem Prevented**: 2+ weeks spent building custom FastAPI server
**Detection**: `analyze_integration_patterns` flags custom REST server red flag
**Solution Suggested**: cognee/cognee:main Docker container with built-in REST API
**Time Saved**: 2-3 weeks of development effort

#### Example Detection Flow:
1. **Developer writes**: "Building custom Cognee REST server with JWT"
2. **MCP tool detects**: Technology=Cognee, Red Flag=custom REST server  
3. **Instant feedback**: "🚨 Official cognee/cognee:main container available"
4. **Next step**: Test official solution before custom development
5. **Outcome**: Prevents unnecessary 2000+ line implementation

### Integration with Existing Tools

#### Enhanced LLM Analysis:
The integration pattern detection automatically enhances existing LLM-powered tools:

- **analyze_github_issue_llm**: Now includes integration pattern context
- **analyze_github_pr_llm**: Automatically flags integration anti-patterns
- **Text analysis tools**: Enhanced with technology-specific guidance

#### Backward Compatibility:
All existing tools continue to work unchanged while gaining integration pattern awareness.

### Common Usage Scenarios

#### 1. Pre-Development Planning
```bash
# Before starting integration work
vibe analyze integration patterns "Planning Cognee integration for knowledge management"
```

#### 2. Code Review Enhancement  
```bash
# During PR review
vibe quick tech scan "PR: Custom Supabase authentication implementation"
```

#### 3. Architecture Decision Validation
```bash
# Validating technical decisions
vibe effort analysis "2000+ line custom integration vs official SDK"
```

#### 4. Team Education & Learning
```bash
# Comprehensive analysis with case studies
vibe analyze integration patterns "Custom vs official approaches" --detail comprehensive
```

### Best Practices for Real-Time Usage

#### 1. **Immediate Feedback Loop**:
- Use `quick_tech_scan` for instant technology detection
- Apply `analyze_integration_patterns` for detailed analysis
- Leverage recommendations for next steps

#### 2. **Development Workflow Integration**:
- Scan PR descriptions before implementation starts
- Analyze issue content during planning phase
- Validate architecture decisions with effort analysis

#### 3. **Team Adoption Strategy**:
- Start with quick scans to build awareness
- Gradually introduce comprehensive analysis
- Use educational content for team learning

#### 4. **Cost-Effective Usage**:
- Integration pattern detection has no LLM costs
- Sub-second response times for development workflow
- Prevents costly over-engineering cycles

The Integration Pattern Detection tools represent a fundamental shift from reactive code review to **proactive architectural guidance**, catching integration anti-patterns at the decision point rather than after implementation is complete.

## Troubleshooting

### Fast Tools Not Working
- Check GitHub token for issue/PR analysis
- Verify repository access permissions

### LLM Tools Not Working
- Run `claude_cli_status` to check Claude CLI
- Run `claude_cli_diagnostics` for timeout issues
- Ensure Claude CLI is in PATH or set CLAUDE_CLI_NAME

### Import Errors
- Check PYTHONPATH includes src directory
- Verify all dependencies installed: `pip install -r requirements.txt`

## Best Practices

1. **Start Fast**: Use `_nollm` tools for quick development feedback
2. **Go Deep**: Use `_llm` tools for comprehensive analysis and learning
3. **Combine Approaches**: Fast tools for triage, LLM tools for deep dives
4. **Cost Awareness**: `_llm` tools consume API credits, use mindfully
5. **Educational Value**: Use comprehensive detail level for learning

The crystal clear `_llm` / `_nollm` naming makes it instantly obvious which tools use LLM reasoning and which provide fast direct analysis.