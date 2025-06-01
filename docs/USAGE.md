# Vibe Check MCP Usage Guide

Complete guide for using the enhanced Vibe Check MCP framework with Claude Code CLI for comprehensive engineering vibe checks and friendly coaching guidance.

## Quick Start

Once you have Vibe Check MCP configured (see [README.md](../README.md)), you can analyze GitHub issues using natural language commands.

## Command Line Interface

### Direct CLI Usage

Set up a shell alias for natural command syntax:

```bash
# Add to your ~/.bashrc, ~/.zshrc, or ~/.fish_config
alias vibe='python -m vibe_check.cli'

# Now you can use:
vibe check issue 31
deep vibe issue 31
vibe check issue 31 in microsoft/typescript
```

### Natural Language Commands

**Quick Analysis**:
```bash
vibe check issue 31
vibe check issue 42 in facebook/react
```

**Deep Analysis** (comprehensive mode with educational content):
```bash
deep vibe issue 31
deep vibe issue 42 in microsoft/typescript
```

## GitHub Issue Vibe Check Analysis

The enhanced Vibe Check MCP provides friendly, coaching-oriented analysis with Claude-powered reasoning and educational guidance.

### Two Analysis Modes

**🚀 Quick Vibe Check** (fast feedback for development workflow):
```
vibe check issue 23
analyze issue 23
quick vibe on issue 23
```

**🧠 Deep Vibe Check** (Claude-powered analysis with GitHub integration):
```
deep vibe issue 23
analyze issue 23 comprehensively  
do a deep vibe check on issue 23
thorough vibe analysis of issue 23
```

### Advanced Usage

**Cross-Repository Analysis**:
```
analyze issue 42 in microsoft/typescript
check issue 156 in facebook/react for anti-patterns
```

**Detail Level Control**:
```
analyze issue 23 with brief details
analyze issue 23 with comprehensive educational content
do a detailed analysis of issue 23
```

**GitHub Integration Control**:
```
analyze issue 23 comprehensively but don't post a comment
analyze issue 23 in comprehensive mode without GitHub integration
```

## Natural Language Prompting

Vibe Check MCP responds to natural language. Here are various ways to trigger analysis:

### Quick Analysis Triggers
- "vibe check issue 23"
- "analyze issue 23"
- "check issue 23 for patterns"  
- "quick review of issue 23"
- "scan issue 23"

### Deep Analysis Triggers (Comprehensive Mode)
- "deep vibe issue 23"
- "analyze issue 23 comprehensively"
- "do a deep vibe check on issue 23"
- "thoroughly analyze issue 23"
- "systematic deep review of issue 23"

### Repository Specification
- "vibe check issue 23 in owner/repo"
- "deep vibe issue 23 in microsoft/typescript"  
- "vibe check issue 42 in facebook/react"

### Educational Content Control
- "analyze issue 23 with brief explanations"
- "analyze issue 23 with detailed educational content"
- "analyze issue 23 with comprehensive learning materials"

## Understanding the Enhanced Vibe Check Output

### Quick Vibe Check Output
```json
{
  "status": "vibe_check_complete",
  "vibe_check": {
    "overall_vibe": "⚖️ Complex Vibes",
    "vibe_level": "complex_vibes",
    "friendly_summary": "⚖️ This feels pretty complex! Have we considered if there's a simpler approach that could achieve the same goals?",
    "coaching_recommendations": [
      "🤔 Question if this complexity is really necessary",
      "💡 Try the simplest approach that could work first",
      "📝 Document why simple solutions aren't sufficient"
    ]
  },
  "enhanced_features": {
    "claude_reasoning": false,
    "clear_thought_analysis": false,
    "comprehensive_validation": false,
    "educational_coaching": true,
    "friendly_language": true
  }
}
```

### Deep Vibe Check Output
```json
{
  "status": "vibe_check_complete",
  "vibe_check": {
    "overall_vibe": "🔍 Research Vibes",
    "vibe_level": "needs_research", 
    "friendly_summary": "🔍 Let's do some homework first! This would benefit from researching existing solutions and checking official documentation before diving in.",
    "coaching_recommendations": [
      "🔍 Time to Do Some Homework!: Great question! Let's do some research first to build on what already exists instead of reinventing wheels.",
      "• Search for existing solutions and libraries in this domain",
      "• Read official documentation and getting-started guides",
      "• Find working examples and tutorials",
      "💡 Real-world insight: Before building a custom authentication system, developers typically research existing solutions like Auth0, Firebase Auth, or Supabase Auth..."
    ]
  },
  "technical_analysis": {
    "detected_patterns": [
      {
        "type": "infrastructure_without_implementation", 
        "confidence": 0.85,
        "detected": true,
        "evidence": "Custom solution mentioned without API research"
      }
    ],
    "integration_analysis": {
      "third_party_services": ["api", "integration"],
      "complexity_indicators": ["complex", "architecture"]
    }
  },
  "enhanced_features": {
    "claude_reasoning": true,
    "clear_thought_analysis": true,
    "comprehensive_validation": true,
    "educational_coaching": true,
    "friendly_language": true
  }
}
```

## GitHub Integration

### Enhanced GitHub Comment Posting

When you use **deep vibe check mode**, the enhanced Vibe Check framework automatically posts a friendly, coaching-oriented comment to the GitHub issue.

**Enhanced Comment Format**:
```markdown
## 🎯 Deep Vibe Check

**Overall Vibe:** 🔍 Research Vibes

### 💫 Vibe Summary
🔍 Let's do some homework first! This would benefit from researching existing solutions and checking official documentation before diving in.

### 🎓 Coaching Recommendations
- 🔍 Time to Do Some Homework!: Great question! Let's do some research first to build on what already exists instead of reinventing wheels.
- • Search for existing solutions and libraries in this domain
- • Read official documentation and getting-started guides
- • Find working examples and tutorials
- 💡 Real-world insight: Before building a custom authentication system, developers typically research existing solutions like Auth0, Firebase Auth, or Supabase Auth...
- 🤝 Collaboration and Feedback: Great engineering happens in teams! Here's how to leverage collective wisdom.

### 🔍 Technical Analysis Summary
- **Patterns Detected:** 1
- **Claude Analysis:** ✅ Available
- **Clear-Thought Analysis:** ✅ Applied

---
*This vibe check was generated by the enhanced Vibe Check MCP framework using Claude-powered analytical reasoning and validated pattern detection.*
```

### Issue Labeling

Deep vibe check analysis automatically adds helpful labels to issues and provides comprehensive coaching in the comments.

## 🎯 The Five Vibe Levels

The enhanced framework assesses issues across 5 friendly vibe levels:

### ✅ **Good Vibes**
- **What it means**: "This looks like a solid plan! The approach seems well thought out and appropriately scoped."
- **When you see this**: Issue has clear requirements, appropriate complexity, good research
- **What to do**: Proceed with implementation following the plan

### 🔍 **Research Vibes** 
- **What it means**: "Let's do some homework first! This would benefit from researching existing solutions."
- **When you see this**: Missing research phase, no existing solution analysis
- **What to do**: Check documentation, find working examples, research existing tools

### 🧪 **POC Vibes**
- **What it means**: "Show us it works first! Let's prove the basic functionality with a simple proof-of-concept."
- **When you see this**: Third-party integration without basic API validation
- **What to do**: Create minimal POC, test basic functionality, validate assumptions

### ⚖️ **Complex Vibes**
- **What it means**: "This feels pretty complex! Have we considered if there's a simpler approach?"
- **When you see this**: High complexity indicators, over-engineering patterns
- **What to do**: Question necessity, try simple approaches first, justify complexity

### 🚨 **Bad Vibes**
- **What it means**: "Hold up! This looks like building infrastructure without proving the basics work."
- **When you see this**: Infrastructure-without-implementation patterns detected
- **What to do**: Stop and start with basic API usage, focus on fundamentals

## Best Practices

### When to Use Quick Vibe Check
- **Development workflow**: Fast feedback during issue planning
- **Daily standup prep**: Quick assessment before discussing issues
- **Issue triage**: Rapid scanning of multiple issues for risk assessment
- **Personal development**: Understanding your own engineering approach

### When to Use Deep Vibe Check  
- **Team code reviews**: When you want to share analysis with team members
- **Educational moments**: When you want full coaching content and learning opportunities
- **Issue documentation**: Creating permanent record of engineering guidance
- **Mentoring sessions**: Teaching junior developers about engineering best practices
- **Pre-implementation validation**: Before starting complex or risky work

### Repository Context

If you're working within a repository, Vibe Check will default to analyzing issues in that repository:

```bash
# In /path/to/my-project
cd /path/to/my-project
claude -p "analyze issue 23"  # Analyzes issue 23 in current repo
```

For cross-repository analysis, always specify the repository:
```
analyze issue 23 in microsoft/typescript
```

## Ensuring Tool Selection

### When Vibe Check Isn't Selected Automatically

Sometimes Claude may not automatically choose the Vibe Check tool for analysis. Here's how to ensure it gets used:

**Explicit Tool References**:
```
use Vibe Check to analyze issue 35
analyze issue 35 with Vibe Check
Vibe Check: check issue 35 for anti-patterns
```

**Anti-Pattern Keywords** (triggers tool selection):
```
analyze issue 35 for anti-patterns
check issue 35 for patterns
scan issue 35 for engineering anti-patterns
anti-pattern analysis of issue 35
```

**Specific Mode Requests**:
```
run comprehensive anti-pattern analysis on issue 35
do a quick vibe check on issue 35  
systematic pattern analysis of issue 35
```

> **📝 Note**: "Vibe check" phrasing works well and may become the official tool name ([see Issue #39](https://github.com/kesslerio/vibe-check-mcp/issues/39)).

### Tool Selection Debugging

**Check Available Tools**:
```
what MCP tools are available?
list Vibe Check capabilities
show me the Vibe Check server status
```

**Verify Tool Registration**:
If Vibe Check isn't available, check your MCP configuration:
```bash
claude mcp list | grep vibe
```

**Force Tool Usage**:
When Claude uses other tools instead, explicitly request:
```
instead, use the Vibe Check analyze_github_issue tool
please use vibe-check:analyze_github_issue for this
```

## Troubleshooting

### Common Issues

**"Vibe Check tool not found"**:
- Check MCP server registration: `claude mcp list`
- Verify server is running: `claude mcp status vibe-check`
- Re-add server if needed (see [README.md](../README.md))

**"Failed to fetch issue"**:
- Check that the issue number exists
- Verify repository name format (owner/repo)
- Ensure GitHub CLI (`gh`) is authenticated

**"GitHub comment posting failed"**:
- Verify you have write access to the repository
- Check that GitHub token is properly configured
- Ensure GitHub CLI is authenticated with sufficient permissions

**"No patterns detected"**:
- This is actually good! It means no anti-patterns were found
- Try comprehensive mode for more detailed analysis
- Check that the issue content contains sufficient detail

**"PR review uses GitHub MCP instead of vibe-check"** (should be resolved with routing optimizations):
- ✅ Try natural language first: "vibe check PR 44" should now work
- ✅ Include pattern keywords: "analyze PR 44 for patterns"
- 🔄 If still routing incorrectly, use explicit: "use vibe-check to review PR 44"
- 📝 Report persistent routing issues for further optimization

**"Claude doesn't use Vibe Check automatically"**:
- Use more specific language (see "Ensuring Tool Selection" above)
- Include "anti-pattern" or "Vibe Check" in your prompt
- Be explicit: "use Vibe Check to analyze..."

### Authentication Setup

Ensure GitHub CLI is properly authenticated:
```bash
gh auth status
gh auth login  # If not authenticated
```

## Advanced Features

### Pattern-Specific Analysis
```
analyze issue 23 focusing on infrastructure patterns
check issue 23 for complexity escalation
scan issue 23 for documentation neglect patterns
```

### Educational Mode
```
explain the infrastructure-without-implementation pattern
teach me about complexity escalation  
what are the main anti-patterns to avoid?
```

## PR Review Usage

The enhanced Vibe Check MCP now includes comprehensive PR review capabilities with Claude CLI integration.

### Natural Language Commands

**Basic PR Review**:
```
review pull request 42
vibe check PR 42
analyze PR 44 comprehensively
```

**Explicit Tool Usage** (recommended for consistent routing):
```
use vibe-check to review PR 44
analyze PR 44 with vibe-check
vibe-check: comprehensive PR review of 44
```

### Command Routing Notes

✅ **Routing Optimization**: Tool descriptions have been optimized with "vibe check" keywords to improve natural language routing.

**Natural language commands that should work**:
- `vibe check PR 44` ✅ (optimized routing)
- `vibe check issue 23` ✅ (optimized routing)  
- `analyze PR 44 for patterns` ✅ (optimized routing)

**If routing issues persist, use explicit tool references**:
- `use vibe-check to review PR 44` ✅ (guaranteed)
- `vibe-check: analyze PR 44 comprehensively` ✅ (guaranteed)
- `analyze PR 44 with the vibe-check tool` ✅ (guaranteed)

### PR Review Features

**🧠 Enhanced Claude CLI Analysis**:
- Comprehensive technical review with sophisticated reasoning
- Anti-pattern detection and prevention guidance
- Security analysis and architectural review
- Real-time output streaming for large PRs

**📊 Multi-Dimensional Analysis**:
- PR size classification (Small/Medium/Large/Very Large)
- Re-review detection and progress tracking
- Linked issue validation and requirement alignment
- Previous review comment analysis

**🔍 Comprehensive Coverage**:
- Code quality and architecture assessment
- Third-party integration validation
- Testing requirements analysis
- Action items with priority classification

### Enhanced Analysis Output

When using explicit vibe-check tool calls, you'll receive:

```json
{
  "pr_number": 44,
  "analysis": {
    "claude_analysis": "Full Claude CLI enhanced review...",
    "analysis_method": "claude-cli",
    "timestamp": "2025-06-01T12:37:36"
  },
  "github_integration": {
    "comment_posted": true,
    "labels_added": ["automated-review"]
  },
  "review_context": {
    "is_re_review": false,
    "review_count": 0
  }
}
```

### GitHub Integration

**Automatic Features**:
- Posts comprehensive review comment to PR
- Adds `automated-review` label
- Tracks re-review status with `re-reviewed` label
- Validates issue linkage and acceptance criteria

**Re-Review Support**:
- Detects previous automated reviews
- Focuses on changes since last review
- Provides progress assessment
- Avoids repeating resolved issues

### Security and Performance

**Claude CLI Integration**:
- Uses `--dangerously-skip-permissions` flag for subprocess execution
- Real-time output streaming for observability
- Automatic fallback to standard analysis if Claude CLI unavailable
- Comprehensive timeout and error handling

**Performance Optimizations**:
- Large PR detection with summary analysis approach
- Diff pattern extraction for very large changes
- Intelligent content sampling for massive PRs

### ✅ Verified Working

**Recent Testing**:
- PR #44: 6 files, +3734/-0 lines - Full Claude CLI analysis successful
- PR #48: 3 files, +28/-0 lines - Instant response with comprehensive review
- Enhanced analysis provides 8000+ character detailed reviews
- Real-time output streaming working correctly

## Upcoming Features

The following tools are planned for Phase 2 expansion:

- **Code Analysis**: `analyze this code for patterns`
- **Integration Validation**: `validate Stripe integration approach`
- **Engineering Plan Review**: `review engineering plan docs/plan.md`
- **PRD Review**: `review PRD docs/requirements.md`

## Getting Help

- **Server Status**: Ask "what's the Vibe Check server status?"
- **Available Tools**: Ask "what can Vibe Check do?"
- **Pattern Information**: Ask "explain [pattern-name] pattern"

For more help, see:
- [Installation Guide](../README.md)
- [Technical Implementation](Technical_Implementation_Guide.md)
- [Product Requirements](Product_Requirements_Document.md)