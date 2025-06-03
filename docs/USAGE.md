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