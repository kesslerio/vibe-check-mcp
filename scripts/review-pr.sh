#!/bin/bash
# Automated PR review script using claude -p with Clear-Thought integration
# Usage: ./scripts/review-pr.sh <PR_NUMBER>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <PR_NUMBER>"
    echo "Example: $0 407"
    exit 1
fi

PR_NUMBER=$1

echo "🤖 Starting automated review for PR #$PR_NUMBER..."

# Verify required tools
MISSING_TOOLS=()
for tool in gh jq; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS+=($tool)
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "❌ Required tools missing: ${MISSING_TOOLS[*]}"
    echo "Please install missing tools and try again"
    exit 1
fi

# Check for Claude CLI availability
CLAUDE_AVAILABLE=true
if ! command -v claude &> /dev/null; then
    echo "⚠️ Claude CLI not available - will use fallback analysis"
    CLAUDE_AVAILABLE=false
fi

# Verify PR exists
if ! gh pr view $PR_NUMBER >/dev/null 2>&1; then
    echo "❌ PR #$PR_NUMBER not found"
    exit 1
fi

echo "📋 Fetching comprehensive PR details..."

# Get comprehensive PR information
PR_INFO=$(gh pr view $PR_NUMBER --json title,body,files,additions,deletions,author,createdAt,baseRefName,headRefName)
PR_TITLE=$(echo "$PR_INFO" | jq -r '.title')
PR_BODY=$(echo "$PR_INFO" | jq -r '.body // ""')
PR_AUTHOR=$(echo "$PR_INFO" | jq -r '.author.login')
PR_CREATED=$(echo "$PR_INFO" | jq -r '.createdAt')
BASE_BRANCH=$(echo "$PR_INFO" | jq -r '.baseRefName')
HEAD_BRANCH=$(echo "$PR_INFO" | jq -r '.headRefName')
FILES_COUNT=$(echo "$PR_INFO" | jq -r '.files | length')
ADDITIONS=$(echo "$PR_INFO" | jq -r '.additions')
DELETIONS=$(echo "$PR_INFO" | jq -r '.deletions')

# Get all changed files
FILES_CHANGED=$(echo "$PR_INFO" | jq -r '.files[].path')

# Get file stats to determine review approach
# Check if this is a very large PR based on file count and line changes
TOTAL_CHANGES=$((ADDITIONS + DELETIONS))
echo "📊 PR Statistics: $FILES_COUNT files, +$ADDITIONS/-$DELETIONS lines (total: $TOTAL_CHANGES changes)"

# Auto-detect very large PRs to avoid hanging on diff commands
if [ $TOTAL_CHANGES -gt 10000 ] || [ $FILES_COUNT -gt 50 ]; then
    echo "⚠️ Very large PR detected based on file count/changes - using file-by-file analysis"
    DIFF_SIZE=999999
    REVIEW_TYPE="VERY_LARGE_PR"
    
    # Get file summaries for very large PRs
    FILE_STATS=$(echo "$PR_INFO" | jq -r '.files[] | "\(.path): +\(.additions)/-\(.deletions)"')
    
    # Try to get sample content from a few key files
    SAMPLE_FILES=$(echo "$PR_INFO" | jq -r '.files[0:5][] | .path')
    PR_DIFF_SAMPLE="# Very Large PR - Sample from first 5 files:\n"
    for file in $SAMPLE_FILES; do
        echo "Getting sample from $file..."
        # Get individual file diff using the files API  
        FILE_DIFF=$(gh api repos/kesslerio/ShapeScaleAI/pulls/$PR_NUMBER/files --jq ".[] | select(.filename == \"$file\") | .patch // \"File too large or binary\"" 2>/dev/null || echo "File diff unavailable")
        PR_DIFF_SAMPLE="$PR_DIFF_SAMPLE\n## $file\n\`\`\`diff\n$(echo "$FILE_DIFF" | head -20)\n\`\`\`\n"
    done
else
    # Handle GitHub API diff size limits (20K lines max) for smaller PRs
    echo "🔍 Attempting to get PR diff (with 15s timeout)..."
    DIFF_OUTPUT=$(timeout 15s gh pr diff $PR_NUMBER 2>&1)
    DIFF_EXIT_CODE=$?
    
    # Check if timeout occurred or API limit hit
    if [ $DIFF_EXIT_CODE -eq 124 ]; then
        echo "⚠️ Timeout: PR diff took longer than 15 seconds - treating as very large PR"
        DIFF_SIZE=999999
        REVIEW_TYPE="VERY_LARGE_PR"
        FILE_STATS=$(echo "$PR_INFO" | jq -r '.files[] | "\(.path): +\(.additions)/-\(.deletions)"')
        PR_DIFF_SAMPLE="# Timeout occurred while fetching diff - file-level analysis only"
    elif [ $DIFF_EXIT_CODE -ne 0 ] && echo "$DIFF_OUTPUT" | grep -q "diff exceeded the maximum number of lines"; then
        echo "⚠️ GitHub API limit: diff exceeds 20K line limit - using file-by-file analysis"
        DIFF_SIZE=999999
        REVIEW_TYPE="VERY_LARGE_PR"
        FILE_STATS=$(echo "$PR_INFO" | jq -r '.files[] | "\(.path): +\(.additions)/-\(.deletions)"')
        PR_DIFF_SAMPLE="# GitHub API limit exceeded - file-level analysis only"
    else
        DIFF_SIZE=$(echo "$DIFF_OUTPUT" | wc -c)
        echo "📊 Diff size: $DIFF_SIZE characters"
        
        # Determine review approach based on size
        if [ $DIFF_SIZE -gt 100000 ]; then
            echo "⚠️ Large PR detected - using focused review approach"
            FILE_STATS=$(echo "$PR_INFO" | jq -r '.files[] | "\(.path): +\(.additions)/-\(.deletions)"')
            PR_DIFF_SAMPLE=$(echo "$DIFF_OUTPUT" | grep -E "^(diff|@@|\+\+\+|---|\+[^+]|\-[^-])" | head -200)
            REVIEW_TYPE="LARGE_PR_SUMMARY"
        else
            echo "📝 Small/Medium PR - using detailed review approach"
            PR_DIFF="$DIFF_OUTPUT"
            REVIEW_TYPE="FULL_ANALYSIS"
        fi
    fi
fi

# Get linked issues from PR body
LINKED_ISSUES=$(echo "$PR_BODY" | grep -oE "(Fixes|Closes|Resolves) #[0-9]+" | grep -oE "[0-9]+" || echo "")

echo "🔍 Running comprehensive analysis with issue validation ($REVIEW_TYPE)..."

# Create comprehensive review prompt with issue validation
cat > /tmp/pr_review_prompt_${PR_NUMBER}.md << EOF
You are an expert code reviewer with focus on systematic prevention of third-party integration failures. Apply project conventions from CLAUDE.md, .cursor/rules/*, or .windsurfrules (if available).

**Enhanced Review Instructions:**
1. Use available MCP GitHub tools for comprehensive PR analysis
2. Apply Clear-Thought MCP tools for systematic code review
3. Leverage research tools for validation of technical approaches
4. Employ debugging approaches for identifying potential issues

Perform a comprehensive review of this Pull Request and provide output in the exact format below:

🎯 **Overview**
Brief summary of what this PR accomplishes and its scope

🔗 **Issue Linkage Validation**
$(if [ -n "$LINKED_ISSUES" ]; then
    echo "- Linked Issues: #$LINKED_ISSUES"
    echo "- [ ] Use MCP GitHub tools to fetch and validate linked issue details"
    echo "- [ ] Verify PR addresses the core problem described in linked issue(s)"
    echo "- [ ] Check if acceptance criteria from issue are met"
    echo "- [ ] Validate that solution approach aligns with issue requirements"
    echo "- [ ] Apply Clear-Thought decision framework to assess PR-issue alignment"
else
    echo "⚠️ NO LINKED ISSUES DETECTED - This PR should reference specific issues it addresses"
    echo "- [ ] PR should link to relevant issues using 'Fixes #XXX' syntax"
    echo "- [ ] Changes should be traceable to documented requirements"
    echo "- [ ] Use MCP GitHub search to find related issues if needed"
fi)

🚫 **Third-Party Integration & Over-Engineering Check**
- [ ] If this involves third-party services: Does it follow API-first development protocol from CLAUDE.md?
- [ ] Are we using standard APIs/SDKs instead of building custom implementations?
- [ ] Check for infrastructure-without-implementation patterns (custom solutions when standard approaches exist)
- [ ] Validate that any custom code is justified over documented standard approaches
- [ ] Ensure working POC was demonstrated before complex architecture
- [ ] **Apply Clear-Thought debugging approach:** Systematic analysis of integration complexity
- [ ] **Use MCP research tools:** Validate third-party service best practices

✅ **Strengths** 
- Key positive aspects and good practices followed
- Well-implemented features and patterns
- Good code quality and architecture decisions
- Adherence to CLAUDE.md guidelines
- **Clear-Thought validation:** Systematic reasoning supporting good practices

⚠️ **Critical Issues**
- Bugs or problems that must be fixed before merge
- Breaking changes or compatibility issues
- Security vulnerabilities or concerns
- Over-engineering patterns or unnecessary complexity
- Missing issue linkage or requirement validation
- **Clear-Thought analysis:** Systematic identification of failure modes and risks

💡 **Suggestions**
- Code improvements and optimizations
- Best practice recommendations
- Performance considerations
- Architecture improvements
- Simplification opportunities
- **Research-backed recommendations:** External validation of suggested approaches
- **Clear-Thought insights:** Systematic thinking results informing suggestions

🧪 **Testing Requirements**
- What needs testing before merge
- Specific test scenarios to validate
- Integration test considerations
- Third-party service validation if applicable
- **Clear-Thought testing strategy:** Systematic approach to test coverage and validation

📋 **Action Items**
- [ ] Required changes for approval
- [ ] Issue linkage corrections needed
- [ ] Recommended improvements
- [ ] Documentation updates needed
- [ ] Third-party integration validation if applicable
- [ ] **MCP GitHub follow-up:** Use GitHub tools for any additional PR interactions needed

🧠 **Clear-Thought Analysis Summary**
[Key insights from systematic thinking tools and how they inform the review]

🔍 **MCP Tools Usage Summary**
[GitHub tools used, research validation performed, systematic analysis applied]

**Recommendation**: [APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]
**Analysis Confidence**: [HIGH/MEDIUM/LOW] - [systematic validation quality]

Focus on project conventions from CLAUDE.md/.cursor/rules/.windsurfrules, systematic prevention of integration failures, and actionable feedback enhanced by MCP tool capabilities.
EOF

# Create data file for claude -p
if [ "$REVIEW_TYPE" = "VERY_LARGE_PR" ]; then
cat > /tmp/pr_data_${PR_NUMBER}.md << EOF
# PR #${PR_NUMBER} Review Data (Very Large PR - File Summary Analysis)

## PR Information
**Title:** ${PR_TITLE}
**Author:** ${PR_AUTHOR}
**Created:** ${PR_CREATED}
**Branch:** ${HEAD_BRANCH} → ${BASE_BRANCH}
**Files Changed:** ${FILES_COUNT}
**Lines:** +${ADDITIONS}/-${DELETIONS}

**Description:**
${PR_BODY}

**File Change Summary:**
${FILE_STATS}

**Sample Code Changes (First 5 files with 20-line previews):**
$(echo -e "$PR_DIFF_SAMPLE")

**Note:** This PR exceeds normal size limits. Review focuses on file-level changes, architecture patterns, and high-level impact assessment rather than detailed line-by-line analysis.

**Review Strategy:**
- Focus on architectural changes and patterns
- Identify potential breaking changes or compatibility issues  
- Assess security implications of large-scale changes
- Recommend testing strategies for comprehensive changes
- Highlight areas that need careful manual review
EOF
elif [ "$REVIEW_TYPE" = "LARGE_PR_SUMMARY" ]; then
cat > /tmp/pr_data_${PR_NUMBER}.md << EOF
# PR #${PR_NUMBER} Review Data (Large PR - Summary Analysis)

## PR Information
**Title:** ${PR_TITLE}
**Author:** ${PR_AUTHOR}
**Created:** ${PR_CREATED}
**Branch:** ${HEAD_BRANCH} → ${BASE_BRANCH}
**Files Changed:** ${FILES_COUNT}
**Lines:** +${ADDITIONS}/-${DELETIONS}

**Description:**
${PR_BODY}

**File Change Summary:**
${FILE_STATS}

**Key Diff Patterns (Sample - 200 lines):**
\`\`\`diff
${PR_DIFF_SAMPLE}
\`\`\`

**Note:** This is a large PR (${DIFF_SIZE} chars). Review focuses on architecture, patterns, and high-level changes rather than line-by-line analysis.
EOF
else
cat > /tmp/pr_data_${PR_NUMBER}.md << EOF
# PR #${PR_NUMBER} Review Data

## PR Information
**Title:** ${PR_TITLE}
**Author:** ${PR_AUTHOR}
**Created:** ${PR_CREATED}
**Branch:** ${HEAD_BRANCH} → ${BASE_BRANCH}
**Files Changed:** ${FILES_COUNT}
**Lines:** +${ADDITIONS}/-${DELETIONS}

**Description:**
${PR_BODY}

**Files Modified:**
${FILES_CHANGED}

**Complete Diff:**
\`\`\`diff
${PR_DIFF}
\`\`\`
EOF
fi

# Create combined prompt file to avoid stdin redirection issues
cat /tmp/pr_review_prompt_${PR_NUMBER}.md /tmp/pr_data_${PR_NUMBER}.md > /tmp/combined_prompt_${PR_NUMBER}.md

# Generate review based on available tools
if [ "$CLAUDE_AVAILABLE" = true ]; then
    # Run claude with the combined prompt
    echo "📝 Generating review with Claude..."
    if ! claude -p "$(cat /tmp/combined_prompt_${PR_NUMBER}.md)" > /tmp/review_output_${PR_NUMBER}.md 2>/tmp/claude_error_${PR_NUMBER}.log; then
        echo "❌ Claude command failed. Error log:"
        cat /tmp/claude_error_${PR_NUMBER}.log
        echo "🔄 Falling back to manual analysis..."
        CLAUDE_AVAILABLE=false
    fi

    # Check if review generation succeeded
    if [ -s /tmp/review_output_${PR_NUMBER}.md ]; then
        EXTRACTED_SIZE=$(wc -c < /tmp/review_output_${PR_NUMBER}.md)
        if [ $EXTRACTED_SIZE -lt 50 ]; then
            echo "⚠️ Generated review content seems too short ($EXTRACTED_SIZE chars)"
            echo "🔄 Falling back to manual analysis..."
            CLAUDE_AVAILABLE=false
        fi
    else
        echo "⚠️ Failed to generate review content."
        echo "🔄 Falling back to manual analysis..."
        CLAUDE_AVAILABLE=false
    fi
fi

# Fallback analysis when Claude is not available
if [ "$CLAUDE_AVAILABLE" = false ]; then
    echo "📝 Generating fallback PR analysis..."
    
    cat > /tmp/review_output_${PR_NUMBER}.md << EOF
## 🔍 Automated PR Review (Fallback Analysis)

**Analysis Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Analysis Method**: Fallback (Claude CLI not available)

### 🎯 Overview
**Title**: ${PR_TITLE}
**Author**: ${PR_AUTHOR}
**Files Changed**: ${FILES_COUNT}
**Lines**: +${ADDITIONS}/-${DELETIONS}

This PR modifies ${FILES_COUNT} files with ${TOTAL_CHANGES} total changes.

### 🔗 Issue Linkage Validation
$(if [ -n "$LINKED_ISSUES" ]; then
    echo "✅ **Linked Issues Found**: #$LINKED_ISSUES"
    echo "- [ ] Manual verification required: Does PR address the core problem in linked issue(s)?"
    echo "- [ ] Manual verification required: Are acceptance criteria from issue met?"
    echo "- [ ] Manual verification required: Does solution approach align with issue requirements?"
else
    echo "⚠️ **NO LINKED ISSUES DETECTED**"
    echo "- [ ] This PR should reference specific issues it addresses using 'Fixes #XXX' syntax"
    echo "- [ ] Changes should be traceable to documented requirements"
    echo "- [ ] Consider adding issue linkage to improve traceability"
fi)

### 🚫 Third-Party Integration & Over-Engineering Check
**Manual Review Required:**
- [ ] If this involves third-party services: Does it follow API-first development protocol?
- [ ] Are we using standard APIs/SDKs instead of building custom implementations?
- [ ] Check for infrastructure-without-implementation patterns
- [ ] Validate that any custom code is justified over documented standard approaches
- [ ] Ensure working POC was demonstrated before complex architecture

**Files to Review for Third-Party Patterns:**
$(echo "$FILES_CHANGED" | grep -E "\.(py|js|ts|sh|yml|yaml|json)$" | head -10)

### ✅ Strengths
**Automated Analysis Limited - Manual Review Recommended:**
- [ ] Code quality assessment needed
- [ ] Architecture impact evaluation required  
- [ ] Security review needed for sensitive changes
- [ ] Performance impact assessment if applicable

### ⚠️ Critical Issues  
**Manual Validation Required:**
- [ ] Check for bugs or problems that must be fixed before merge
- [ ] Validate no breaking changes or compatibility issues
- [ ] Security vulnerability scan needed
- [ ] Over-engineering pattern detection required
- [ ] Missing issue linkage validation needed

### 💡 Suggestions
**Recommended Manual Reviews:**
- [ ] Code improvements and optimizations assessment
- [ ] Best practice compliance check
- [ ] Performance considerations evaluation
- [ ] Architecture improvements analysis
- [ ] Simplification opportunities identification

### 🧪 Testing Requirements
**Manual Verification Needed:**
- [ ] Validate testing strategy before merge
- [ ] Verify test scenarios cover changes
- [ ] Integration test considerations review
- [ ] Third-party service validation if applicable

### 📋 Action Items
**Required Manual Review:**
- [ ] Detailed code review by team member
- [ ] Issue linkage verification if missing
- [ ] Third-party integration validation if applicable
- [ ] Documentation updates assessment
- [ ] Security and performance review

**Recommendation**: **MANUAL REVIEW REQUIRED**

This automated fallback analysis provides basic validation but cannot replace human review. 
Please ensure a team member conducts thorough code review focusing on:
1. Code quality and architecture impact
2. Security and performance implications  
3. Third-party integration best practices
4. Issue linkage and requirement fulfillment

For enhanced automated analysis, ensure Claude CLI is available in the environment.

---
*This review was generated using fallback patterns. For comprehensive automated analysis, install Claude CLI.*
EOF
fi

echo "📝 Posting review to PR..."

# Post review as comment
gh pr comment $PR_NUMBER --body-file /tmp/review_output_${PR_NUMBER}.md

# Add automated review label
gh pr edit $PR_NUMBER --add-label "automated-review" 2>/dev/null || true

echo "✅ Review completed and posted to PR #$PR_NUMBER"
echo "🔗 View at: $(gh pr view $PR_NUMBER --json url -q .url)"

# Cleanup (preserve for debugging)
echo "🔍 Debug files preserved:"
echo "- Prompt: /tmp/pr_review_prompt_${PR_NUMBER}.md"
echo "- Data: /tmp/pr_data_${PR_NUMBER}.md"
echo "- Combined: /tmp/combined_prompt_${PR_NUMBER}.md"
echo "- Output: /tmp/review_output_${PR_NUMBER}.md"
echo "- Error log: /tmp/claude_error_${PR_NUMBER}.log"
# rm /tmp/pr_review_prompt_${PR_NUMBER}.md /tmp/pr_data_${PR_NUMBER}.md /tmp/review_output_${PR_NUMBER}.md /tmp/claude_error_${PR_NUMBER}.log

echo ""
echo "💡 Full detailed analysis completed using claude -p"