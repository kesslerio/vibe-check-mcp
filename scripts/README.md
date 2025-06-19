# Scripts Directory - MCP Tool Prototypes

This directory contains bash script prototypes that are being evolved into MCP tools for seamless Claude Code integration.

## 🔄 Script → MCP Tool Evolution

These scripts serve as **proof-of-concept implementations** and **feature specifications** for the corresponding MCP tools currently in development.

### Review Automation Scripts

| Script | Status | MCP Tool | GitHub Issue |
|--------|--------|----------|--------------|
| ~~`review-issue.sh`~~ | 🚀 **MIGRATED** | `analyze_github_issue_llm` | ✅ **COMPLETED** - Removed in [Issue #71](https://github.com/kesslerio/vibe-check-mcp/issues/71) |
| ~~`review-pr.sh`~~ | 🚀 **MIGRATED** | `review_pr_comprehensive` | ✅ **COMPLETED** - Removed in [Issue #71](https://github.com/kesslerio/vibe-check-mcp/issues/71) |
| `review-engineering-plan.sh` | ✅ Prototype | `review_engineering_plan` | 🔄 [Issue #36](https://github.com/kesslerio/vibe-check-mcp/issues/36) |
| `review-prd.sh` | ✅ Prototype | `review_prd` | 🔄 [Issue #37](https://github.com/kesslerio/vibe-check-mcp/issues/37) |

### Utility Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `lint-code.sh` | Code quality validation | ✅ Stable |
| ~~`triage-issue.sh`~~ | 🚀 **MIGRATED** | GitHub MCP tools | ✅ **COMPLETED** - Removed in [Issue #71](https://github.com/kesslerio/vibe-check-mcp/issues/71) |
| `shared/` | Common functions | ✅ Stable |

## 📋 Usage During Development

While MCP tools are being developed, these scripts provide **full functionality** for systematic review and validation:

### Issue Review (via MCP)
```bash
# Use Claude Code with MCP tools:
# "analyze issue 35" → analyze_github_issue_llm
```

### PR Review (via MCP)
```bash
# Use Claude Code with MCP tools:
# "review PR 38" → review_pr_comprehensive
```

### Engineering Plan Review
```bash
./scripts/review-engineering-plan.sh docs/Technical_Implementation_Guide.md --prd docs/Product_Requirements_Document.md
```

### PRD Review
```bash
./scripts/review-prd.sh docs/Product_Requirements_Document.md
```

## 🎯 MCP Integration Goals

The MCP tools will provide:

1. **Natural Language Interface**: 
   - Script: `./scripts/review-pr.sh 38`
   - MCP: `"review pull request 38"`

2. **Claude Code Integration**:
   - Direct integration with development workflow
   - No need to switch to terminal

3. **Enhanced Analysis**:
   - Integration with Clear-Thought systematic reasoning
   - Educational anti-pattern prevention
   - Structured JSON responses

4. **GitHub Integration**:
   - Automatic comment posting
   - Issue labeling
   - Status tracking

## 🔧 Development Philosophy

These scripts follow the **"API-First"** development principle from our anti-pattern prevention guidelines:

1. **Validate functionality** with bash scripts first
2. **Prove the approach** works with real data  
3. **Build MCP wrapper** over proven functionality
4. **Maintain script compatibility** during transition

This prevents the **Infrastructure-Without-Implementation** anti-pattern that led to the Cognee integration failure.

## 📚 Script Documentation

Each script includes:
- **Comprehensive help text** (`script.sh --help`)
- **Usage examples** in script headers
- **Error handling** and validation
- **Integration with Clear-Thought MCP tools** for systematic analysis

## 🚀 Migration Timeline

**Phase 2 Development** (Current):
- Scripts remain **fully functional** and **actively maintained**
- MCP tools being developed incrementally  
- **No disruption** to current workflow during transition

**Phase 3 Completion**:
- MCP tools provide **equivalent functionality**
- Scripts maintained for **CLI power users** and **CI/CD integration**
- **Both interfaces supported** long-term

## 💡 Contributing

When modifying scripts:
1. **Test thoroughly** - these are prototypes for MCP tools
2. **Document changes** - updates inform MCP tool development
3. **Maintain compatibility** - don't break existing workflows
4. **Consider MCP implications** - changes should work in both script and MCP contexts

The goal is **smooth evolution** from script prototypes to polished MCP tools without losing the proven functionality these scripts provide.