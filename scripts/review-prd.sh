#!/bin/bash
# PRD Review Script - Enhanced systematic validation with MCP tools
# Usage: ./scripts/review-prd.sh <PRD_FILE_PATH>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <PRD_FILE_PATH>"
    echo "Example: $0 docs/Product_Requirements_Document.md"
    exit 1
fi

PRD_FILE=$1

echo "🎯 Running enhanced PRD review with MCP tools for comprehensive analysis..."

# Check if Claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "❌ Claude CLI not found"
    echo "Please install Claude Code CLI first: https://claude.ai/code"
    exit 1
fi

# Check if PRD file exists
if [ ! -f "$PRD_FILE" ]; then
    echo "❌ PRD file not found: $PRD_FILE"
    echo "Please provide a valid file path"
    exit 1
fi

# Create reviews directory if it doesn't exist
mkdir -p reviews

# Get PRD content and check size
echo "📋 Reading PRD file: $PRD_FILE"
PRD_SIZE=$(wc -c < "$PRD_FILE")
PRD_LINES=$(wc -l < "$PRD_FILE")

if [ "$PRD_SIZE" -eq 0 ]; then
    echo "❌ PRD file is empty"
    exit 1
fi

echo "📝 PRD content loaded ($PRD_LINES lines, $PRD_SIZE chars)"

# Check if document is too large for Claude
if [ "$PRD_SIZE" -gt 25000 ]; then
    echo "⚠️ Warning: PRD file is large ($PRD_SIZE characters)"
    echo "Breaking into summary analysis to avoid Claude limits..."
    
    # Create summary for large documents
    SUMMARY=$(head -n 50 "$PRD_FILE" && echo -e "\n...\n[Document continues for $PRD_LINES total lines]\n..." && tail -n 20 "$PRD_FILE")
else
    SUMMARY=$(cat "$PRD_FILE")
fi

# Create output file in reviews directory
OUTPUT_FILE="reviews/prd-review-$(basename "$PRD_FILE" .md)-$(date +%Y%m%d-%H%M%S).md"
echo "💾 Analysis will be saved to: $OUTPUT_FILE"

# Enhanced prompt with MCP tool integration
PROMPT="You are a senior product strategy advisor. Analyze this PRD for anti-patterns using available research tools for comprehensive analysis.

**Enhanced Analysis Instructions:**
1. Use available MCP research tools to validate claims and approaches
2. Search for similar products/solutions to inform recommendations  
3. Research best practices for identified problem areas
4. Provide evidence-based recommendations with external validation

**Anti-Patterns to Check:**
1. Solution-first requirements (tech details before user problems)
2. Scope creep enablers (vague success criteria)
3. Resource reality disconnect (no feasibility validation)
4. Stakeholder assumption gaps (missing user research)
5. Metrics manipulation (vanity metrics vs business impact)

**Enhanced Analysis Process:**
- Research market validation for the problem domain
- Look up best practices for the proposed solution approach
- Validate technical feasibility claims
- Check for similar solutions and differentiation opportunities

**Required Output Format:**
🎯 **PRD Overview**
[Brief summary]

🔍 **Market Research & Validation**
[Results from research tools about problem domain and solutions]

🚨 **Anti-Pattern Risk Assessment**
[Detected patterns with risk level HIGH/MEDIUM/LOW and research validation]

🔧 **Technical Feasibility Research**
[External validation of technical claims and approaches]

💡 **Evidence-Based Recommendations**
[Top 3 actionable improvements with research backing]

📚 **Research Citations**
[Sources and validation from research tools used]

**Overall Assessment**: [APPROVE/NEEDS REVISION/REJECT]
**Research Confidence**: [HIGH/MEDIUM/LOW] - [explanation of research validation]

**PRD Content:**
\`\`\`
$SUMMARY
\`\`\`"

# Run Claude analysis with MCP tools
echo "🤖 Running enhanced Claude analysis with MCP research tools..."
echo "🔍 This includes market research, technical validation, and best practices lookup..."

if echo "$PROMPT" | claude -p > "$OUTPUT_FILE" 2>/dev/null; then
    
    # Check if output was generated
    if [ ! -s "$OUTPUT_FILE" ]; then
        echo "❌ Claude produced no output"
        echo "Trying simplified analysis..."
        
        # Fallback: Simple prompt without MCP tools
        SIMPLE_PROMPT="Analyze this PRD for major anti-patterns. Provide summary and 3 recommendations.

PRD excerpt:
\`\`\`
$(head -n 30 "$PRD_FILE")
\`\`\`"
        
        if echo "$SIMPLE_PROMPT" | claude -p > "$OUTPUT_FILE" 2>/dev/null && [ -s "$OUTPUT_FILE" ]; then
            echo "✅ Simplified analysis complete!"
        else
            echo "❌ Claude analysis completely failed"
            echo "Manual review required"
            rm -f "$OUTPUT_FILE"
            exit 1
        fi
    else
        echo "✅ Enhanced PRD analysis complete!"
    fi
    
    echo ""
    echo "📊 Enhanced Analysis Results:"
    echo "============================"
    cat "$OUTPUT_FILE"
    echo ""
    echo "💾 Full analysis saved to: $OUTPUT_FILE"
    
    # Check for high-risk patterns
    if grep -qi "high\|critical\|reject" "$OUTPUT_FILE"; then
        echo ""
        echo "⚠️  HIGH RISK PATTERNS DETECTED"
        echo "Review research-backed recommendations before proceeding."
    elif grep -qi "approve" "$OUTPUT_FILE"; then
        echo ""
        echo "✅ PRD APPROVED WITH RESEARCH VALIDATION"
        echo "Ready for engineering planning with market confidence."
    fi
    
else
    echo "❌ Claude CLI execution failed"
    echo "Check Claude authentication and network connection"
    exit 1
fi

echo ""
echo "🎯 Enhanced PRD systematic review complete!"
echo "📄 Review the full analysis with research validation in: $OUTPUT_FILE"
echo ""
echo "💡 Next steps:"
echo "   1. Address any HIGH risk anti-patterns identified"
echo "   2. Validate market research findings"
echo "   3. Run ./scripts/review-engineering-plan.sh with MCP enhancement"
echo "   4. Consider external validation of technical feasibility claims"