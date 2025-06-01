#!/bin/bash
# Engineering Plan Review Script - Enhanced technical validation with MCP research tools
# Usage: ./scripts/review-engineering-plan.sh <PLAN_FILE_PATH> [--prd <PRD_FILE_PATH>]

set -e

# Parse arguments
PLAN_FILE=""
PRD_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --prd)
            PRD_FILE="$2"
            shift 2
            ;;
        *)
            if [ -z "$PLAN_FILE" ]; then
                PLAN_FILE="$1"
            else
                echo "Error: Multiple plan files specified"
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$PLAN_FILE" ]; then
    echo "Usage: $0 <PLAN_FILE_PATH> [--prd <PRD_FILE_PATH>]"
    echo "Examples:"
    echo "  $0 docs/Technical_Implementation_Guide.md"
    echo "  $0 docs/engineering-plan.md --prd docs/Product_Requirements_Document.md"
    exit 1
fi

echo "🎯 Running enhanced Engineering Plan review with MCP research tools..."

# Check if Claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "❌ Claude CLI not found"
    echo "Please install Claude Code CLI first: https://claude.ai/code"
    exit 1
fi

# Check if plan file exists
if [ ! -f "$PLAN_FILE" ]; then
    echo "❌ Engineering plan file not found: $PLAN_FILE"
    echo "Please provide a valid file path"
    exit 1
fi

# Check PRD file if provided
PRD_CONTENT=""
if [ -n "$PRD_FILE" ]; then
    if [ ! -f "$PRD_FILE" ]; then
        echo "❌ PRD file not found: $PRD_FILE"
        echo "Please provide a valid PRD file path or omit --prd flag"
        exit 1
    fi
    PRD_CONTENT=$(cat "$PRD_FILE")
    echo "📋 PRD alignment check enabled with: $PRD_FILE"
fi

# Create reviews directory if it doesn't exist
mkdir -p reviews

# Get plan content
echo "📋 Reading Engineering Plan file: $PLAN_FILE"
PLAN_CONTENT=$(cat "$PLAN_FILE")
PLAN_SIZE=$(echo "$PLAN_CONTENT" | wc -c)
PLAN_LINES=$(echo "$PLAN_CONTENT" | wc -l)

if [ -z "$PLAN_CONTENT" ]; then
    echo "❌ Engineering plan file is empty"
    exit 1
fi

echo "📝 Engineering plan content loaded ($PLAN_LINES lines, $PLAN_SIZE chars)"
if [ -n "$PRD_CONTENT" ]; then
    echo "📝 PRD content loaded ($(echo "$PRD_CONTENT" | wc -l) lines)"
fi

# Create output file in reviews directory
OUTPUT_FILE="reviews/engineering-plan-review-$(basename "$PLAN_FILE" .md)-$(date +%Y%m%d-%H%M%S).md"
echo "💾 Analysis will be saved to: $OUTPUT_FILE"

# Check if document is too large and create summary if needed
if [ "$PLAN_SIZE" -gt 35000 ]; then
    echo "⚠️ Warning: Engineering plan is large ($PLAN_SIZE characters)"
    echo "Creating summary for analysis..."
    PLAN_SUMMARY=$(head -n 100 "$PLAN_FILE" && echo -e "\n...\n[Document continues for $PLAN_LINES total lines]\n..." && tail -n 50 "$PLAN_FILE")
else
    PLAN_SUMMARY="$PLAN_CONTENT"
fi

# Create enhanced engineering plan review prompt
PRD_SECTION=""
if [ -n "$PRD_CONTENT" ]; then
    PRD_SECTION="## PRD CONTENT FOR ALIGNMENT CHECK:

\`\`\`
$(echo "$PRD_CONTENT" | head -n 50)
$(if [ $(echo "$PRD_CONTENT" | wc -l) -gt 50 ]; then echo "...[PRD continues]"; fi)
\`\`\`"
fi

PROMPT="You are a senior technical architect with expertise in preventing systematic engineering failures.

**Enhanced Analysis Instructions:**
1. Use available MCP research tools to validate technical approaches and frameworks
2. Research best practices for proposed technologies (FastMCP, MCP protocol, etc.)
3. Look up similar technical implementations for validation
4. Provide evidence-based technical recommendations
5. Apply Cognee retrospective lessons with external research validation

**Engineering Anti-Pattern Detection Framework:**

### 1. ARCHITECTURE WITHOUT VALIDATION
- Research the proposed technical stack for stability and best practices
- Validate complexity claims against industry standards
- Check for simpler alternatives using research tools

### 2. INTEGRATION ASSUMPTION FAILURES  
- Research third-party APIs and SDKs mentioned
- Validate compatibility and stability claims
- Look up common integration pitfalls

### 3. SCALE PREMATURE OPTIMIZATION
- Research performance benchmarks for proposed approaches
- Validate scaling claims with external data
- Check industry standards for similar applications

### 4. TECHNOLOGY SELECTION BIAS
- Research proposed technologies for production readiness
- Look up alternatives and comparative analysis
- Validate team skill requirements

### 5. RISK ASSESSMENT BLINDNESS
- Research failure modes for proposed architecture
- Look up monitoring and observability best practices
- Validate backup and recovery approaches

## COGNEE RETROSPECTIVE LESSONS WITH RESEARCH VALIDATION

**Infrastructure-Without-Implementation Prevention:**
- Research if basic integrations work as claimed
- Validate that standard approaches exist for proposed custom solutions
- Look up documentation quality for proposed APIs
- Research complexity vs. benefit trade-offs

**Required Output Format:**

🎯 **Engineering Plan Overview**
[Brief summary]

🔍 **Technical Research & Validation**
[Results from researching proposed technologies and approaches]

🚨 **Anti-Pattern Risk Assessment**  
[Detected patterns with research-backed evidence]

🔧 **Technical Validation Requirements**
[Research-informed POCs needed]

⚖️ **Complexity vs. Industry Standards**
[Research comparison of proposed complexity]

🛡️ **Risk Analysis with External Validation**
[Research-backed failure modes and mitigation]

$(if [ -n "$PRD_CONTENT" ]; then echo "🔗 **PRD Alignment with Research**
[Technical approach vs. PRD with external validation]"; fi)

💡 **Research-Backed Recommendations**
[Evidence-based improvements with citations]

📚 **Technical Research Citations**
[Sources used for validation]

**Overall Assessment**: [APPROVE/NEEDS POC/NEEDS SIMPLIFICATION/REJECT]
**Infrastructure-Without-Implementation Risk**: [HIGH/MEDIUM/LOW]
**Research Confidence**: [HIGH/MEDIUM/LOW] - [validation quality]

## ENGINEERING PLAN TO ANALYZE:

\`\`\`
$PLAN_SUMMARY
\`\`\`

$PRD_SECTION"

# Run Claude analysis with MCP research tools
echo "🤖 Running enhanced Claude analysis with technical research..."
echo "🔍 This includes framework validation, best practices research, and technical feasibility..."

if echo "$PROMPT" | claude -p > "$OUTPUT_FILE" 2>/dev/null; then
    
    # Check if output was generated
    if [ ! -s "$OUTPUT_FILE" ]; then
        echo "❌ Claude produced no output"
        echo "Document may be too complex. Trying simplified analysis..."
        
        # Fallback: Simplified prompt
        SIMPLE_PROMPT="Analyze this engineering plan for anti-patterns. Focus on infrastructure-without-implementation risks from Cognee lessons.

Plan excerpt:
\`\`\`
$(head -n 50 "$PLAN_FILE")
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
        echo "✅ Enhanced engineering plan analysis complete!"
    fi
    
    echo ""
    echo "📊 Enhanced Analysis Results:"
    echo "============================"
    cat "$OUTPUT_FILE"
    echo ""
    echo "💾 Full analysis saved to: $OUTPUT_FILE"
    
    # Check for high-risk patterns with specific messaging
    if grep -qi "infrastructure-without-implementation.*high\|infrastructure-without-implementation.*critical" "$OUTPUT_FILE"; then
        echo ""
        echo "🚨 CRITICAL COGNEE-STYLE RISK DETECTED"
        echo "This plan shows research-validated infrastructure-without-implementation patterns."
        echo "Follow Cognee lessons: validate basic functionality before complex architecture."
    elif grep -qi "high\|critical\|reject" "$OUTPUT_FILE"; then
        echo ""
        echo "⚠️  HIGH RISK PATTERNS DETECTED"
        echo "Research validation shows significant technical debt risk."
        echo "Review evidence-based recommendations before proceeding."
    elif grep -qi "approve" "$OUTPUT_FILE"; then
        echo ""
        echo "✅ ENGINEERING PLAN APPROVED WITH RESEARCH VALIDATION"
        echo "Technical research supports the proposed approach."
    fi
    
else
    echo "❌ Claude CLI execution failed"
    echo "Check Claude authentication and network connection"
    exit 1
fi

# Extract key recommendations if present
if grep -qi "recommendations\|💡" "$OUTPUT_FILE"; then
    echo ""
    echo "🎯 Research-Backed Key Recommendations:"
    echo "======================================"
    grep -A 10 -i "recommendations\|💡" "$OUTPUT_FILE" | head -n 10
fi

echo ""
echo "🎯 Enhanced engineering plan systematic review complete!"
echo "📄 Review the research-validated analysis in: $OUTPUT_FILE"
echo ""
echo "💡 Next steps:"
echo "   1. Address any research-validated HIGH risk anti-patterns"
echo "   2. Complete technical validation requirements with external sources"
echo "   3. Validate basic integrations per Cognee lessons"
echo "   4. Consider research citations for implementation decisions"
echo "   5. Use ./scripts/review-issue.sh for implementation validation"