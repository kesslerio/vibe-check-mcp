#!/bin/bash
# Issue triage script - passes issue data directly to Claude
# Usage: ./scripts/triage-issue.sh <ISSUE_NUMBER>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <ISSUE_NUMBER>"
    echo "Example: $0 123"
    exit 1
fi

ISSUE_NUMBER=$1

echo "🎯 Running Claude issue triage for issue #$ISSUE_NUMBER..."

# Check if Claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "❌ Claude CLI not found"
    echo "Please install Claude Code CLI first: https://claude.ai/code"
    exit 1
fi

# Check if GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found"
    echo "Please install GitHub CLI first: https://cli.github.com/"
    exit 1
fi

# Verify the issue exists and get its data
echo "📋 Fetching issue data..."
if ! ISSUE_DATA=$(gh issue view $ISSUE_NUMBER --json title,body,labels,author,createdAt,state 2>/dev/null); then
    echo "❌ Issue #$ISSUE_NUMBER not found"
    echo "Make sure the issue number is correct and you have access to the repository"
    exit 1
fi

# Extract issue information
ISSUE_TITLE=$(echo "$ISSUE_DATA" | jq -r '.title')
ISSUE_BODY=$(echo "$ISSUE_DATA" | jq -r '.body // ""')
ISSUE_AUTHOR=$(echo "$ISSUE_DATA" | jq -r '.author.login')
ISSUE_CREATED=$(echo "$ISSUE_DATA" | jq -r '.createdAt')
ISSUE_STATE=$(echo "$ISSUE_DATA" | jq -r '.state')
EXISTING_LABELS=$(echo "$ISSUE_DATA" | jq -r '.labels[]?.name // empty' | tr '\n' ', ' | sed 's/,$//')

# Get available labels
echo "🏷️ Fetching available labels..."
AVAILABLE_LABELS=$(gh label list --json name,description | jq -r '.[] | "\(.name): \(.description // "No description")"')

echo "📝 Issue data collected:"
echo "   Title: $ISSUE_TITLE"
echo "   Author: $ISSUE_AUTHOR"
echo "   State: $ISSUE_STATE"
echo "   Existing labels: ${EXISTING_LABELS:-"None"}"

# Create output file with timestamp
OUTPUT_FILE="triage-analysis-issue-${ISSUE_NUMBER}-$(date +%Y%m%d-%H%M%S).md"

# Create combined prompt with the actual issue data
cat > /tmp/triage_prompt.md << EOF
You're an issue triage assistant for GitHub issues. Your task is to analyze the issue and select appropriate labels from the provided list.

IMPORTANT: Don't post any comments or messages to the issue. Your only action should be to apply labels.

Issue Information:
- REPO: Current repository
- ISSUE_NUMBER: $ISSUE_NUMBER

## Guidelines

- DO NOT post any comments explaining your decision
- DO NOT communicate directly with users
- Your ONLY action should be to apply labels using mcp__github__update_issue
- It's okay to not add any labels if none are clearly applicable
- Be thorough in your analysis

## Available Labels:
$AVAILABLE_LABELS

## Issue Details:
**Title:** $ISSUE_TITLE
**Author:** $ISSUE_AUTHOR  
**Created:** $ISSUE_CREATED
**Current State:** $ISSUE_STATE
**Existing Labels:** ${EXISTING_LABELS:-"None"}

**Description:**
$ISSUE_BODY

## Task Overview

1. Analyze the issue content, considering:
   - The issue title and description
   - The type of issue (bug report, feature request, question, etc.)
   - Technical areas mentioned
   - Severity or priority indicators
   - User impact
   - Components affected

2. Select appropriate labels from the available labels list:
   - Choose labels that accurately reflect the issue's nature
   - Be specific but comprehensive
   - Select priority labels if you can determine urgency (high-priority, med-priority, or low-priority)
   - Consider platform labels (android, ios) if applicable
   - Look for potential duplicates if you notice similar patterns

3. Provide your analysis in this format:

## 🎯 Issue Analysis

**Issue Type:** [bug/feature/enhancement/question/documentation/etc.]
**Priority:** [high/medium/low]
**Complexity:** [simple/moderate/complex]

## 🏷️ Recommended Labels

**Primary Labels:**
- [label-name]: [reason for this label]
- [label-name]: [reason for this label]

**Additional Labels:**
- [label-name]: [reason for this label]

## 📊 Analysis Summary

**Technical Areas:** [list relevant areas]
**User Impact:** [describe impact]
**Estimated Effort:** [rough estimate if applicable]

## 🔧 Suggested Actions

**Commands to run:**
\`\`\`bash
gh issue edit $ISSUE_NUMBER --add-label "label1,label2,label3"
\`\`\`

**Notes:** [any additional observations]

## IMPORTANT GUIDELINES:
- Be thorough in your analysis
- Only select labels from the provided list above
- DO NOT post any comments to the issue
- Your ONLY action should be to apply labels using mcp__github__update_issue
- It's okay to not add any labels if none are clearly applicable
EOF

# Run Claude with the direct prompt
echo "🤖 Running Claude analysis..."
echo "Saving detailed analysis to: $OUTPUT_FILE"
claude -p "$(cat /tmp/triage_prompt.md)" | tee "$OUTPUT_FILE"

# Extract suggested labels and ask if user wants to apply them
if grep -q "gh issue edit.*--add-label" "$OUTPUT_FILE"; then
    SUGGESTED_LABELS=$(grep "gh issue edit.*--add-label" "$OUTPUT_FILE" | sed 's/.*--add-label "//' | sed 's/".*//')
    echo ""
    echo "🏷️ Suggested labels found: $SUGGESTED_LABELS"
    echo ""
    read -p "Apply these labels? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Applying labels..."
        if gh issue edit $ISSUE_NUMBER --add-label "$SUGGESTED_LABELS"; then
            echo "✅ Labels applied successfully"
        else
            echo "❌ Failed to apply labels"
        fi
    else
        echo "Labels not applied. You can apply them manually with:"
        echo "gh issue edit $ISSUE_NUMBER --add-label \"$SUGGESTED_LABELS\""
    fi
fi

echo ""
echo "✅ Triage analysis complete!"
echo "📄 Full analysis saved to: $OUTPUT_FILE"

# Cleanup
rm /tmp/triage_prompt.md

echo "🔗 View issue: $(gh issue view $ISSUE_NUMBER --json url -q .url)"