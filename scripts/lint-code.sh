#!/bin/bash
# Code linting script - passes git diff directly to Claude
# Usage: ./scripts/lint-code.sh

set -e

echo "🔍 Running Claude Code lint analysis..."

# Check if Claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "❌ Claude CLI not found"
    echo "Please install Claude Code CLI first: https://claude.ai/code"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    echo "This script needs to be run from within a git repository"
    exit 1
fi

# Get git diff
echo "📊 Getting git diff..."
GIT_DIFF=$(git diff HEAD~1..HEAD)

if [ -z "$GIT_DIFF" ]; then
    echo "ℹ️ No changes found in recent commits. Checking working directory..."
    GIT_DIFF=$(git diff)
    if [ -z "$GIT_DIFF" ]; then
        echo "ℹ️ No changes in working directory either. Checking staged changes..."
        GIT_DIFF=$(git diff --cached)
        if [ -z "$GIT_DIFF" ]; then
            echo "✅ No changes to analyze"
            exit 0
        fi
    fi
fi

echo "📝 Found changes to analyze:"
echo "$GIT_DIFF" | head -10
echo "..."

# Create output file with timestamp
OUTPUT_FILE="lint-analysis-$(date +%Y%m%d-%H%M%S).md"

# Create combined prompt with the actual diff
cat > /tmp/lint_prompt.md << EOF
You are a code linter. Please analyze the changes versus the main branch (via git diff with no arguments - you already have permission) and report any issues related to typos or style guidelines.

## Guidelines

- DO NOT run bash lint/typecheck commands on the codebase. Remember that YOU are the linter.
- Only surface issues in newly added or modified lines
- Keep the CLAUDE.md style guide in mind
- Focus on typos, style issues, and potential bugs
- When the user made an intentional change (eg. for variable naming or content tone), you should generally trust the user's intent and not report an issue
- Use Unicode ellipsis (…) instead of three dots (...) in user-facing text

## Output Format

For each issue found:

1. Filename and line number on one line
2. Description of the issue on the second line
3. Separate issues with a blank line

For example:

\`\`\`
src/commands/loadCommandsDir.ts:123
Avoid \`enum\`; use unions of string literal types instead
\`\`\`

DO NOT return any other text or explanations. If you don't find any issues, just return "No issues found".

## Git Diff to Analyze:

\`\`\`diff
$GIT_DIFF
\`\`\`
EOF

# Run Claude with the direct prompt
echo "🤖 Running Claude analysis..."
echo "Saving detailed analysis to: $OUTPUT_FILE"
claude -p "$(cat /tmp/lint_prompt.md)" | tee "$OUTPUT_FILE"

echo ""
echo "✅ Lint analysis complete!"
echo "📄 Full analysis saved to: $OUTPUT_FILE"

# Cleanup
rm /tmp/lint_prompt.md

echo ""
echo "💡 This analysis covered:"
echo "   • All changed lines in the git diff"
echo "   • Style issues (enum vs union types, ellipsis usage, etc.)"
echo "   • Code quality issues"
echo "   • Potential bugs"