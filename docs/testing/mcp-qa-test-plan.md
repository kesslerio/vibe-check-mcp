# MCP QA Test Plan: Context Loading & Context7 Integration

## Purpose

This manual E2E test plan validates the integration between:
- **Context Injection Hooks**: EnhancedClaudeCliExecutor with transparent context loading
- **Context7 MCP Integration**: Real Context7 MCP server integration with structured JSON responses

Use this checklist for production QA testing of the vibe-check MCP server.

## Pre-Test Setup

### Environment Requirements
- [ ] vibe-check-mcp server accessible (local or npm version)
- [ ] Claude CLI integration functional
- [ ] Test project with detectible libraries (FastAPI, React, etc.)

### Optional Setup
- [ ] `.vibe-check/config.json` with context loading enabled
- [ ] `.vibe-check/project-context.md` with project conventions
- [ ] WORKSPACE environment variable configured

## Test Execution Checklist

### Phase 1: Infrastructure Verification

**Objective**: Confirm MCP server operational status

- [ ] **Test 1.1**: `mcp__vibe-check-*__server_status()`
  - **Expected**: Server responds with status and tool count
  - **Pass Criteria**: No timeout, returns server info
  - **Fail Action**: Check MCP server configuration

- [ ] **Test 1.2**: `mcp__vibe-check-*__check_claude_cli_integration()`
  - **Expected**: Claude CLI availability confirmed
  - **Pass Criteria**: Returns success status
  - **Fail Action**: Run claude_cli_diagnostics tool

### Phase 2: Context Loading Components

**Objective**: Validate project context and library detection

- [ ] **Test 2.1**: `mcp__vibe-check-*__load_project_context()`
  - **Expected**: Project context loaded successfully
  - **Pass Criteria**: Returns libraries and documentation sources
  - **Fail Action**: Check .vibe-check directory structure

- [ ] **Test 2.2**: `mcp__vibe-check-*__detect_project_libraries()`
  - **Expected**: Library detection finds project dependencies
  - **Pass Criteria**: Detects 3+ libraries with >80% confidence
  - **Fail Action**: Verify project has package.json/requirements.txt

### Phase 3: Context7 MCP Integration

**Objective**: Test Context7 library resolution and documentation

- [ ] **Test 3.1**: `mcp__vibe-check-*__resolve_library_id(library_name="fastapi")`
  - **Expected**: Library resolves to Context7 ID
  - **Pass Criteria**: Returns library_id like "/tiangolo/fastapi"
  - **Fail Action**: Try different well-known library (react, nodejs)

- [ ] **Test 3.2**: `mcp__vibe-check-*__get_library_documentation(library_id="/tiangolo/fastapi")`
  - **Expected**: Documentation content retrieved
  - **Pass Criteria**: Returns documentation text with real content
  - **Fail Action**: Check Context7 service status

### Phase 4: End-to-End Integration

**Objective**: Verify combined context in analysis tools

- [ ] **Test 4.1**: `mcp__vibe-check-*__vibe_check_mentor()` with library query
  - **Query**: "Should I use [detected_library] patterns for this project?"
  - **Expected**: Response incorporates both project + library context
  - **Pass Criteria**: No errors, mentions both project and library details
  - **Fail Action**: Check logs for null handling issues

### Phase 5: Transparent Context Injection

**Objective**: Confirm context injection works in analysis tools

- [ ] **Test 5.1**: `mcp__vibe-check-*__analyze_text_nollm()` with project context
  - **Text**: "I want to build custom HTTP client instead of using [detected_library]"
  - **Parameters**: `use_project_context=true`
  - **Expected**: Analysis includes project-aware recommendations
  - **Pass Criteria**: `context_applied: true` and contextual recommendations
  - **Fail Action**: Verify project context configuration

## Success Criteria

### ✅ Full Pass
- [ ] All 7 tests pass without errors
- [ ] Context7 integration functional
- [ ] Project context loading operational
- [ ] End-to-end integration working

### 🟡 Partial Pass
- [ ] 5+ tests pass
- [ ] Core context loading functional
- [ ] Minor tool issues that don't block core functionality

### ❌ Fail
- [ ] <5 tests pass
- [ ] Core integration broken
- [ ] Multiple tool failures

## Troubleshooting Guide

### Common Issues

**Server Timeout**
- Switch between vibe-check-local and vibe-check-npm
- Check MCP server configuration
- Verify network connectivity

**Context7 Resolution Fails**
- Try different library names (fastapi, react, nodejs)
- Check Context7 service availability
- Verify library exists in Context7 catalog

**vibe_check_mentor Errors**
- Check for null handling in mentor tools
- Verify workspace configuration
- Run with minimal parameters first

**Project Context Loading Fails**
- Check .vibe-check directory exists
- Verify config.json format
- Ensure project has detectable libraries

### Debug Commands

```bash
# Check server capabilities
mcp__vibe-check-*__claude_cli_status()

# Validate configuration
mcp__vibe-check-*__validate_mcp_configuration()

# Test specific integrations
mcp__vibe-check-*__check_claude_cli_integration()
```

## Test Result Template

### Test Execution: [DATE]

**Environment**: [local/npm] vibe-check server  
**Tester**: [NAME]  
**Project**: [PROJECT_NAME]  

**Phase 1**: [ PASS / FAIL ]
- Test 1.1: [ PASS / FAIL ]
- Test 1.2: [ PASS / FAIL ]

**Phase 2**: [ PASS / FAIL ]
- Test 2.1: [ PASS / FAIL ]
- Test 2.2: [ PASS / FAIL ]

**Phase 3**: [ PASS / FAIL ]
- Test 3.1: [ PASS / FAIL ]
- Test 3.2: [ PASS / FAIL ]

**Phase 4**: [ PASS / FAIL ]
- Test 4.1: [ PASS / FAIL ]

**Phase 5**: [ PASS / FAIL ]
- Test 5.1: [ PASS / FAIL ]

**Overall Status**: [ PASS / PARTIAL / FAIL ]

**Issues Found**: 
- [List any issues]

**Recommendations**:
- [Any recommendations for improvement]

---
**Created**: 2025-08-19  
**Version**: 1.0  
**Last Updated**: 2025-08-19  
**Test Environment**: vibe-check MCP server

## Implementation Notes

### Known Issues Fixed During Creation
- **vibe_check_mentor Tool Error**: Fixed incomplete `load_workspace_context` function in `src/vibe_check/server/tools/mentor/context.py`
  - **Issue**: Missing return statement causing "cannot unpack non-iterable NoneType object" error
  - **Solution**: Added complete implementation with session_id generation and context building
  - **Files Modified**: 
    - `src/vibe_check/server/tools/mentor/context.py` - Added missing implementation
    - `src/vibe_check/server/tools/mentor/core.py` - Fixed function call signature
  - **Status**: ✅ RESOLVED - Tool now works correctly

### Validation Results (2025-08-19)
✅ **All Integration Features Confirmed Working**:
- Context7 library resolution: `/tiangolo/fastapi` 
- Project context loading: 6 libraries detected (98.3% confidence)
- Transparent context injection: `context_applied: true` in analysis tools
- vibe_check_mentor: Successfully provides collaborative reasoning output
- End-to-end integration: Both local project context AND Context7 library docs working together