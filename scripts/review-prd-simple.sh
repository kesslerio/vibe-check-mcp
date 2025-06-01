#!/bin/bash
# Simple PRD Review Script - Basic anti-pattern detection without MCP tools
# Usage: ./scripts/review-prd-simple.sh <PRD_FILE_PATH>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <PRD_FILE_PATH>"
    echo "Example: $0 docs/Product_Requirements_Document.md"
    exit 1
fi

PRD_FILE=$1

echo "🎯 Running basic PRD review..."

# Check if Claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "❌ Claude CLI not found"
    echo "Please install Claude Code CLI first: https://claude.ai/code"
    exit 1
fi

# Check if PRD file exists
if [ ! -f "$PRD_FILE" ]; then
    echo "❌ PRD file not found: $PRD_FILE"
    exit 1
fi

# Create reviews directory
mkdir -p reviews

# Get PRD content (limit to avoid hanging)
echo "📋 Reading PRD file: $PRD_FILE"
PRD_CONTENT=$(head -n 150 "$PRD_FILE")
PRD_SIZE=$(echo "$PRD_CONTENT" | wc -c)

echo "📝 PRD content loaded ($(echo "$PRD_CONTENT" | wc -l) lines, $PRD_SIZE chars)"

# Create output file
OUTPUT_FILE="reviews/prd-simple-$(basename "$PRD_FILE" .md)-$(date +%Y%m%d-%H%M%S).md"

# Simple, focused prompt without MCP tools
PROMPT="You are a product strategy reviewer. Analyze this PRD for common anti-patterns.

**Anti-Patterns to Check:**
1. Solution-first requirements (tech details before user problems)
2. Scope creep enablers (vague success criteria)  
3. Resource reality disconnect (no feasibility validation)
4. Stakeholder assumption gaps (missing user research)
5. Metrics manipulation (vanity metrics vs business impact)

**Format:** Brief markdown with sections for each anti-pattern risk level (HIGH/MEDIUM/LOW) and 3 key recommendations.

**PRD Content:**
\`\`\`
$PRD_CONTENT
\`\`\`"

# Run Claude with simple command and timeout
echo "🤖 Running basic Claude analysis..."
if echo "$PROMPT" | claude -p > "$OUTPUT_FILE" 2>/dev/null; then
    if [ -s "$OUTPUT_FILE" ]; then
        echo "✅ Basic analysis complete!"
        echo ""
        echo "📊 Analysis Results:"
        echo "=================="
        cat "$OUTPUT_FILE"
        echo ""
        echo "💾 Full analysis saved to: $OUTPUT_FILE"
    else
        echo "❌ Claude produced no output"
        exit 1
    fi
else
    echo "❌ Claude analysis failed or timed out"
    echo "Check Claude authentication and try again"
    exit 1
fi

echo ""
echo "🎯 Basic PRD review complete!"
echo "💡 For enhanced analysis with research tools, use: ./scripts/review-prd.sh"