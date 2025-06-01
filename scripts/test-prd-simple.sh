#!/bin/bash
# Simple PRD test without MCP tools
set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <PRD_FILE>"
    exit 1
fi

PRD_FILE="$1"
OUTPUT_FILE="reviews/simple-prd-test-$(basename "$PRD_FILE" .md)-$(date +%Y%m%d-%H%M%S).md"

echo "🧪 Testing simple PRD analysis..."
echo "📋 Input: $PRD_FILE"
echo "📄 Output: $OUTPUT_FILE"

# Create reviews directory
mkdir -p reviews

# Simple prompt without complex MCP tools
PROMPT="You are a product strategy reviewer. Analyze this PRD and provide a brief assessment.

Focus on:
1. Problem definition clarity
2. Solution approach appropriateness  
3. Success metrics specificity
4. Overall recommendation

Format your response in markdown with clear sections.

PRD Content:
\`\`\`
$(head -n 100 "$PRD_FILE")
$(if [ $(wc -l < "$PRD_FILE") -gt 100 ]; then echo "...[truncated for analysis]"; fi)
\`\`\`"

echo "🤖 Running simplified Claude analysis..."
if echo "$PROMPT" | claude -p > "$OUTPUT_FILE"; then
    if [ -s "$OUTPUT_FILE" ]; then
        echo "✅ Analysis successful!"
        echo "📊 Output preview:"
        echo "=================="
        head -n 20 "$OUTPUT_FILE"
        echo "=================="
        echo "💾 Full analysis saved to: $OUTPUT_FILE"
    else
        echo "❌ Output file is empty"
        exit 1
    fi
else
    echo "❌ Claude execution failed"
    exit 1
fi