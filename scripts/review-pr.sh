#!/bin/bash
# Automated PR review script using claude -p with Clear-Thought integration
# Usage: ./scripts/review-pr.sh <PR_NUMBER>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <PR_NUMBER> [--re-review]"
    echo "Examples:"
    echo "  $0 407              # First review or auto-detect re-review"
    echo "  $0 407 --re-review  # Force re-review mode"
    exit 1
fi

PR_NUMBER=$1
FORCE_RE_REVIEW=false

# Parse additional arguments
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --re-review)
            FORCE_RE_REVIEW=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

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

# Create reviews directory structure
mkdir -p reviews/pr-reviews

# Multi-dimensional PR size classification
SIZE_BY_LINES="SMALL"
SIZE_BY_FILES="SMALL"
SIZE_BY_CHARS="SMALL"
SIZE_REASONS=()

# Classify by line changes
if [ $TOTAL_CHANGES -le 500 ]; then
    SIZE_BY_LINES="SMALL"
elif [ $TOTAL_CHANGES -le 1500 ]; then
    SIZE_BY_LINES="MEDIUM"
    SIZE_REASONS+=("$TOTAL_CHANGES line changes (Medium)")
elif [ $TOTAL_CHANGES -le 5000 ]; then
    SIZE_BY_LINES="LARGE"
    SIZE_REASONS+=("$TOTAL_CHANGES line changes (Large)")
else
    SIZE_BY_LINES="VERY_LARGE"
    SIZE_REASONS+=("$TOTAL_CHANGES line changes (Very Large)")
fi

# Classify by file count
if [ $FILES_COUNT -le 3 ]; then
    SIZE_BY_FILES="SMALL"
elif [ $FILES_COUNT -le 8 ]; then
    SIZE_BY_FILES="MEDIUM"
    SIZE_REASONS+=("$FILES_COUNT files (Medium)")
elif [ $FILES_COUNT -le 20 ]; then
    SIZE_BY_FILES="LARGE"
    SIZE_REASONS+=("$FILES_COUNT files (Large)")
else
    SIZE_BY_FILES="VERY_LARGE"
    SIZE_REASONS+=("$FILES_COUNT files (Very Large)")
fi

# Auto-detect very large PRs to avoid hanging on diff commands
if [ $TOTAL_CHANGES -gt 10000 ] || [ $FILES_COUNT -gt 50 ]; then
    echo "⚠️ Very large PR detected: ${SIZE_REASONS[*]} - using file-by-file analysis"
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
        
        # Classify by character size
        if [ $DIFF_SIZE -gt 100000 ]; then
            SIZE_BY_CHARS="VERY_LARGE"
            SIZE_REASONS+=("$DIFF_SIZE char diff (Very Large)")
        elif [ $DIFF_SIZE -gt 50000 ]; then
            SIZE_BY_CHARS="LARGE"
            SIZE_REASONS+=("$DIFF_SIZE char diff (Large)")
        fi
        
        # Determine overall size (highest category wins)
        OVERALL_SIZE="SMALL"
        for size in "$SIZE_BY_LINES" "$SIZE_BY_FILES" "$SIZE_BY_CHARS"; do
            case $size in
                "VERY_LARGE") OVERALL_SIZE="VERY_LARGE"; break ;;
                "LARGE") OVERALL_SIZE="LARGE" ;;
                "MEDIUM") if [ "$OVERALL_SIZE" != "LARGE" ]; then OVERALL_SIZE="MEDIUM"; fi ;;
            esac
        done
        
        # Determine review approach based on overall size
        if [ "$OVERALL_SIZE" = "VERY_LARGE" ] || [ $DIFF_SIZE -gt 100000 ]; then
            echo "⚠️ Very Large PR detected: ${SIZE_REASONS[*]} - using focused review approach"
            FILE_STATS=$(echo "$PR_INFO" | jq -r '.files[] | "\(.path): +\(.additions)/-\(.deletions)"')
            PR_DIFF_SAMPLE=$(echo "$DIFF_OUTPUT" | grep -E "^(diff|@@|\+\+\+|---|\+[^+]|\-[^-])" | head -200)
            REVIEW_TYPE="LARGE_PR_SUMMARY"
        elif [ "$OVERALL_SIZE" = "LARGE" ] || [ $DIFF_SIZE -gt 50000 ]; then
            echo "⚠️ Large PR detected: ${SIZE_REASONS[*]} - using focused review approach"
            FILE_STATS=$(echo "$PR_INFO" | jq -r '.files[] | "\(.path): +\(.additions)/-\(.deletions)"')
            PR_DIFF_SAMPLE=$(echo "$DIFF_OUTPUT" | grep -E "^(diff|@@|\+\+\+|---|\+[^+]|\-[^-])" | head -200)
            REVIEW_TYPE="LARGE_PR_SUMMARY"
        else
            if [ ${#SIZE_REASONS[@]} -gt 0 ]; then
                echo "📝 ${OVERALL_SIZE} PR detected: ${SIZE_REASONS[*]} - using detailed review approach"
            else
                echo "📝 Small PR - using detailed review approach"
            fi
            PR_DIFF="$DIFF_OUTPUT"
            REVIEW_TYPE="FULL_ANALYSIS"
        fi
    fi
fi

# Get linked issues from PR body
LINKED_ISSUES=$(echo "$PR_BODY" | grep -oE "(Fixes|Closes|Resolves) #[0-9]+" | grep -oE "[0-9]+" || echo "")

# Get existing PR comments for analysis
echo "📝 Fetching existing PR comments..."
EXISTING_COMMENTS=$(gh pr view $PR_NUMBER --json comments --jq '.comments[] | "**@" + .author.login + "** (" + .createdAt + "): " + .body' 2>/dev/null || echo "No comments found")

# Detect if this is a re-review (auto-detect or forced)
IS_RE_REVIEW=false
PREVIOUS_AUTOMATED_REVIEWS=""
REVIEW_COUNT=0

if [ "$FORCE_RE_REVIEW" = true ] || echo "$EXISTING_COMMENTS" | grep -q "🎯.*Overview\|## 🎯\|🔍.*Analysis\|⚠️.*Critical Issues\|💡.*Suggestions\|Automated PR Review\|🔍 Automated PR Review\|## 🤖 Enhanced PR Review"; then
    IS_RE_REVIEW=true
    echo "🔄 Re-review mode detected"
    
    # Extract previous automated review comments
    PREVIOUS_AUTOMATED_REVIEWS=$(echo "$EXISTING_COMMENTS" | grep -A 50 -B 2 "🎯.*Overview\|## 🎯\|🔍.*Analysis\|⚠️.*Critical Issues\|💡.*Suggestions\|Automated PR Review\|🔍 Automated PR Review\|## 🤖 Enhanced PR Review" || echo "Previous automated reviews found but could not extract details")
    
    # Count previous reviews (look for comprehensive review patterns)
    REVIEW_COUNT=$(echo "$EXISTING_COMMENTS" | grep -c "🎯.*Overview\|💡.*Suggestions\|⚠️.*Critical Issues" || echo "0")
    echo "📊 Previous automated reviews: $REVIEW_COUNT"
else
    echo "✨ First automated review for this PR"
fi

# Get issue details if linked issues exist
ISSUE_ANALYSIS=""
if [ -n "$LINKED_ISSUES" ]; then
    echo "🔗 Analyzing linked issues: #$LINKED_ISSUES"
    for issue_num in $LINKED_ISSUES; do
        echo "🔍 Fetching issue #$issue_num details..."
        ISSUE_DATA=$(gh issue view $issue_num --json title,body,labels 2>/dev/null || echo "Issue not found")
        if [ "$ISSUE_DATA" != "Issue not found" ]; then
            ISSUE_TITLE_LINKED=$(echo "$ISSUE_DATA" | jq -r '.title')
            ISSUE_BODY_LINKED=$(echo "$ISSUE_DATA" | jq -r '.body // ""')
            ISSUE_LABELS_LINKED=$(echo "$ISSUE_DATA" | jq -r '.labels[]?.name' | tr '\n' ', ' | sed 's/,$//')
            
            ISSUE_ANALYSIS="$ISSUE_ANALYSIS

## Issue #$issue_num Analysis
**Title:** $ISSUE_TITLE_LINKED
**Labels:** $ISSUE_LABELS_LINKED
**Body:** 
$ISSUE_BODY_LINKED
"
        else
            ISSUE_ANALYSIS="$ISSUE_ANALYSIS

## Issue #$issue_num Analysis
**Status:** Issue not found or inaccessible
"
        fi
    done
fi

echo "🔍 Running comprehensive analysis with comment and issue validation ($REVIEW_TYPE)..."

# Create comprehensive review prompt with re-review context
cat > /tmp/pr_review_prompt_${PR_NUMBER}.md << EOF
You are an expert code reviewer with focus on systematic prevention of third-party integration failures. Apply project conventions from CLAUDE.md, .cursor/rules/*, or .windsurfrules (if available).

$(if [ "$IS_RE_REVIEW" = true ]; then
    echo "**🔄 RE-REVIEW MODE** - This is review #$((REVIEW_COUNT + 1)) for this PR"
    echo "**Previous Review Context:**"
    echo "- Focus on changes since last review"
    echo "- Identify what issues have been resolved vs. still pending"
    echo "- Avoid repeating previously identified issues that haven't changed"
    echo "- Provide incremental analysis focusing on new developments"
    echo ""
    echo "**Enhanced Re-Review Instructions:**"
    echo "1. Compare current state against previous automated review findings"
    echo "2. Highlight what has been addressed from previous feedback"
    echo "3. Focus analysis on new changes and unresolved issues"
    echo "4. Provide progress assessment on previous recommendations"
else
    echo "**✨ FIRST REVIEW** - Comprehensive initial analysis"
    echo ""
    echo "**Enhanced Review Instructions:**"
fi)
1. Use available MCP GitHub tools for comprehensive PR analysis
2. Apply Clear-Thought MCP tools for systematic code review
3. Leverage research tools for validation of technical approaches
4. Employ debugging approaches for identifying potential issues

Perform a comprehensive review of this Pull Request and provide output in the exact format below:

🎯 **Overview**
Brief summary of what this PR accomplishes and its scope

$(if [ "$IS_RE_REVIEW" = true ]; then
    echo "🔄 **Re-Review Analysis** (Review #$((REVIEW_COUNT + 1)))"
    echo "**Previous Review Summary:**"
    echo "- [ ] Identify key issues flagged in previous automated review(s)"
    echo "- [ ] Assess what has been resolved since last review"
    echo "- [ ] Highlight new changes that need analysis"
    echo "- [ ] Provide progress assessment: IMPROVED/UNCHANGED/REGRESSED"
    echo "- [ ] Focus on incremental changes vs. comprehensive re-analysis"
    echo ""
fi)

🔗 **Issue Linkage Validation**
$(if [ -n "$LINKED_ISSUES" ]; then
    echo "- Linked Issues: #$LINKED_ISSUES"
    echo "- [ ] Verify PR addresses the core problem described in linked issue(s)"
    echo "- [ ] Check if acceptance criteria from issue are met"
    echo "- [ ] Validate that solution approach aligns with issue requirements"
    echo "- [ ] Apply Clear-Thought decision framework to assess PR-issue alignment"
    echo "- [ ] Ensure all issue requirements are addressed by this PR"
    echo ""
    echo "**Linked Issue Analysis Available Below** - Use this to validate alignment"
else
    echo "⚠️ NO LINKED ISSUES DETECTED - This PR should reference specific issues it addresses"
    echo "- [ ] PR should link to relevant issues using 'Fixes #XXX' syntax"
    echo "- [ ] Changes should be traceable to documented requirements"
    echo "- [ ] Use MCP GitHub search to find related issues if needed"
fi)

📝 **Previous Review Comments Analysis**
$(if [ "$EXISTING_COMMENTS" != "No comments found" ]; then
    echo "- [ ] Analyze existing review feedback and concerns raised"
    echo "- [ ] Verify that previous review issues have been addressed"
    echo "- [ ] Check if changes align with reviewer suggestions"
    echo "- [ ] Identify any unresolved review topics that need follow-up"
    echo "- [ ] Apply Clear-Thought collaborative reasoning to assess reviewer consensus"
    echo ""
    echo "**Previous Comments Available Below** - Address any unresolved feedback"
else
    echo "✅ This is the first review of this PR"
    echo "- [ ] Provide comprehensive initial review"
    echo "- [ ] Set clear expectations for any needed changes"
fi)

🚫 **Third-Party Integration & Complexity Assessment**
- [ ] If this involves third-party services: Does it follow API-first development protocol from CLAUDE.md?
- [ ] Are we using standard APIs/SDKs instead of building custom implementations?
- [ ] **Assess (not necessarily block):** Infrastructure-without-implementation patterns
- [ ] **Consider:** Is custom code justified and well-documented for its purpose?
- [ ] **Advisory:** Working POC validation for complex third-party integrations
- [ ] **Apply Clear-Thought debugging approach:** Systematic analysis of complexity trade-offs
- [ ] **Use MCP research tools:** Validate third-party service integration approaches

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
- Missing issue linkage or requirement validation
- **Clear-Thought analysis:** Systematic identification of failure modes and risks

💡 **Complexity & Architecture Considerations**
- Over-engineering patterns or unnecessary complexity (advisory, not necessarily blocking)
- Infrastructure complexity vs. benefit trade-offs
- Optional vs. required dependencies assessment
- User experience and setup complexity considerations
- Alternative implementation approaches worth considering

💡 **Enhancement Suggestions**
- Code improvements and optimizations
- Best practice recommendations
- Performance considerations
- Architecture improvements
- Simplification opportunities (where beneficial, not dogmatic)
- Optional dependency management strategies
- User experience improvements
- **Research-backed recommendations:** External validation of suggested approaches
- **Clear-Thought insights:** Systematic thinking results informing suggestions

🧪 **Testing Requirements**
- What needs testing before merge
- Specific test scenarios to validate
- Integration test considerations
- Third-party service validation if applicable
- **Clear-Thought testing strategy:** Systematic approach to test coverage and validation

📋 **Action Items**
- [ ] **Required changes for approval** (critical issues only)
- [ ] Issue linkage corrections needed
- [ ] **Recommended improvements** (suggestions, not requirements)
- [ ] **Advisory considerations** (complexity trade-offs to consider)
- [ ] Documentation updates needed
- [ ] Third-party integration validation if applicable
- [ ] **Optional dependency management** (make MCP servers optional where feasible)
- [ ] **MCP GitHub follow-up:** Use GitHub tools for any additional PR interactions needed

🧠 **Clear-Thought Analysis Summary**
[Key insights from systematic thinking tools and how they inform the review]

🔍 **MCP Tools Usage Summary**
[GitHub tools used, research validation performed, systematic analysis applied]

**Recommendation**: [APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]
**Analysis Confidence**: [HIGH/MEDIUM/LOW] - [systematic validation quality]

**Review Philosophy**: 
- Distinguish between critical issues (must fix) and advisory considerations (worth considering)
- Recognize that complexity may be justified for specific purposes (logging, better analysis, etc.)
- Focus on helping vs. blocking: provide options and considerations rather than dogmatic requirements
- Validate third-party integrations but recognize their value when well-implemented
- Consider user experience: optional dependencies and graceful degradation where possible

**CRITICAL: Code Analysis Guidelines**
- **ONLY analyze the changed files in this PR diff** - do not count unrelated repository files
- **Focus on NET changes**: If files were deleted and replaced, analyze the complexity reduction vs. addition
- **Understand refactoring**: File deletions followed by simpler replacements represent complexity reduction
- **PR Statistics Context**: +${ADDITIONS}/-${DELETIONS} lines may include large deletions of over-engineered code
- **Validate Claims**: When author claims complexity reduction, look for evidence in deleted vs. added files
- **Files Changed**: ${FILES_COUNT} files (focus analysis only on these files, not entire repository)

Focus on project conventions from CLAUDE.md/.cursor/rules/.windsurfrules, balanced assessment of complexity trade-offs, and actionable feedback enhanced by MCP tool capabilities.
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

## Previous Review Comments
$EXISTING_COMMENTS

$(if [ "$IS_RE_REVIEW" = true ]; then
    echo "## Previous Automated Reviews (For Re-Review Analysis)"
    echo "**Review Count**: $REVIEW_COUNT previous automated reviews"
    echo "**Previous Automated Review Details**:"
    echo "$PREVIOUS_AUTOMATED_REVIEWS"
    echo ""
    echo "**Re-Review Focus**: Compare current state against previous findings and assess progress"
fi)

$ISSUE_ANALYSIS
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

## Previous Review Comments
$EXISTING_COMMENTS

$(if [ "$IS_RE_REVIEW" = true ]; then
    echo "## Previous Automated Reviews (For Re-Review Analysis)"
    echo "**Review Count**: $REVIEW_COUNT previous automated reviews"
    echo "**Previous Automated Review Details**:"
    echo "$PREVIOUS_AUTOMATED_REVIEWS"
    echo ""
    echo "**Re-Review Focus**: Compare current state against previous findings and assess progress"
fi)

$ISSUE_ANALYSIS
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

## Previous Review Comments
$EXISTING_COMMENTS

$(if [ "$IS_RE_REVIEW" = true ]; then
    echo "## Previous Automated Reviews (For Re-Review Analysis)"
    echo "**Review Count**: $REVIEW_COUNT previous automated reviews"
    echo "**Previous Automated Review Details**:"
    echo "$PREVIOUS_AUTOMATED_REVIEWS"
    echo ""
    echo "**Re-Review Focus**: Compare current state against previous findings and assess progress"
fi)

$ISSUE_ANALYSIS
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

# Add re-review header if this is a re-review
if [ "$IS_RE_REVIEW" = true ]; then
    # Create enhanced header for re-review
    cat > /tmp/review_header_${PR_NUMBER}.md << EOF
## 🔄 **Automated PR Re-Review #$((REVIEW_COUNT + 1))**

**Previous Reviews**: $REVIEW_COUNT automated review(s) completed
**Re-Review Focus**: Changes since last review, progress assessment, new issues
**Analysis Date**: $(date '+%Y-%m-%d %H:%M:%S')

---

EOF
    # Combine header with review content
    cat /tmp/review_header_${PR_NUMBER}.md /tmp/review_output_${PR_NUMBER}.md > /tmp/final_review_${PR_NUMBER}.md
    REVIEW_FILE="/tmp/final_review_${PR_NUMBER}.md"
else
    REVIEW_FILE="/tmp/review_output_${PR_NUMBER}.md"
fi

# Save review to permanent log file
REVIEW_LOG_FILE="reviews/pr-reviews/pr-${PR_NUMBER}-review-$(date +%Y%m%d-%H%M%S).md"
cp "$REVIEW_FILE" "$REVIEW_LOG_FILE"

# Post review as comment
gh pr comment $PR_NUMBER --body-file "$REVIEW_FILE"

# Add appropriate labels
gh pr edit $PR_NUMBER --add-label "automated-review" 2>/dev/null || true
if [ "$IS_RE_REVIEW" = true ]; then
    gh pr edit $PR_NUMBER --add-label "re-reviewed" 2>/dev/null || true
fi

if [ "$IS_RE_REVIEW" = true ]; then
    echo "✅ Re-review #$((REVIEW_COUNT + 1)) completed and posted to PR #$PR_NUMBER"
else
    echo "✅ Initial review completed and posted to PR #$PR_NUMBER"
fi
echo "🔗 View at: $(gh pr view $PR_NUMBER --json url -q .url)"

# File preservation summary
echo "📁 Review files saved:"
echo "💾 Permanent log: $REVIEW_LOG_FILE"
echo "🔍 Debug files preserved:"
echo "- Prompt: /tmp/pr_review_prompt_${PR_NUMBER}.md"
echo "- Data: /tmp/pr_data_${PR_NUMBER}.md"
echo "- Combined: /tmp/combined_prompt_${PR_NUMBER}.md"
echo "- Output: /tmp/review_output_${PR_NUMBER}.md"
if [ "$IS_RE_REVIEW" = true ]; then
    echo "- Re-review header: /tmp/review_header_${PR_NUMBER}.md"
    echo "- Final review: /tmp/final_review_${PR_NUMBER}.md"
fi
echo "- Error log: /tmp/claude_error_${PR_NUMBER}.log"

echo ""
if [ "$IS_RE_REVIEW" = true ]; then
    echo "💡 Re-review analysis completed with context from $REVIEW_COUNT previous review(s)"
else
    echo "💡 Full detailed analysis completed using claude -p"
fi