#!/bin/bash
# PRD Review Script - Basic anti-pattern detection
# Usage: ./scripts/review-prd.sh <PRD_FILE_PATH>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <PRD_FILE_PATH>"
    echo "Example: $0 docs/Product_Requirements_Document.md"
    exit 1
fi

PRD_FILE=$1

echo "🎯 Running PRD review with anti-pattern detection..."

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

# Get PRD content (limit to 100 lines to avoid hanging)
echo "📋 Reading PRD file: $PRD_FILE"
PRD_CONTENT=$(head -n 100 "$PRD_FILE")
PRD_LINES=$(echo "$PRD_CONTENT" | wc -l)

echo "📝 PRD content loaded ($PRD_LINES lines)"

# Create output file
OUTPUT_FILE="reviews/prd-review-$(basename "$PRD_FILE" .md)-$(date +%Y%m%d-%H%M%S).md"

# Rich prompt with systematic thinking integration
PROMPT="You are a senior product strategy advisor. Analyze this PRD comprehensively for anti-patterns and strategic quality using systematic thinking approaches.

**Enhanced Analysis Instructions:**
1. Use available MCP research tools to validate claims and approaches
2. Search for similar products/solutions to inform recommendations  
3. Research best practices for identified problem areas
4. **Apply Clear-Thought systematic analysis:**
   - Use mental models (First Principles, Opportunity Cost, Pareto Principle) for product validation
   - Apply decision frameworks for feature prioritization and market positioning
   - Employ sequential thinking for complex product strategy evaluation
   - Use collaborative reasoning for stakeholder alignment assessment

**Focus Areas:**
1. **Problem Definition Clarity** - How well-defined and validated is the problem?
2. **Solution Approach Appropriateness** - Does the solution fit the problem and market?
3. **Success Metrics Specificity** - Are success criteria measurable and realistic?
4. **Overall Strategic Assessment** - Is this a sound product strategy?

**Anti-Pattern Detection with Systematic Thinking:**
1. **Solution-first requirements** (tech details before user problems)
   - **Apply First Principles:** Strip away solution bias to focus on core user problems
2. **Scope creep enablers** (vague success criteria)
   - **Use Decision Framework:** Systematic evaluation of scope boundaries and success metrics
3. **Resource reality disconnect** (no feasibility validation)
   - **Apply Opportunity Cost Analysis:** Evaluate resource allocation against alternatives
4. **Stakeholder assumption gaps** (missing user research)
   - **Use Collaborative Reasoning:** Simulate stakeholder perspectives and identify gaps
5. **Metrics manipulation** (vanity metrics vs business impact)
   - **Apply Pareto Principle:** Focus on the 20% of metrics that drive 80% of business value

**Required Output Format:**
# PRD Strategic Assessment: [Product Name]

## 1. Problem Definition Clarity ⭐⭐⭐⭐⭐

**Strengths:**
[Detailed analysis with evidence]

**Evidence of strong/weak problem definition:**
[Specific examples from PRD]

## 2. Solution Approach Appropriateness ⭐⭐⭐⭐⚡

**Strengths:**
[Detailed analysis]

**Potential concerns:**
[Issues and risks]

## 3. Success Metrics Specificity ⭐⭐⭐⚡⚡

**Strengths:**
[What's well defined]

**Weaknesses:**
[Missing or vague metrics]

**Suggested additions needed:**
[Specific metric recommendations]

## 4. Overall Recommendation ⭐⭐⭐⭐⚡

### ✅ **[PROCEED/NEEDS REVISION/REJECT]** with strategic adjustments

**Key Strengths:**
[Major positives]

**Critical Success Factors:**
[What needs to happen]

**Risk Mitigation:**
[How to reduce risks]

## 🧠 **Clear-Thought Analysis Results**
[Results from systematic thinking: mental models applied, decision frameworks used, collaborative reasoning insights]

## 🔍 **Market Research & Validation** 
[Results from research tools about problem domain and solutions]

## 🎯 **Systematic Thinking Summary**
[Key insights from Clear-Thought tools and how they validate/challenge the PRD approach]

**Recommendation**: [Detailed strategic assessment]
**Research Confidence**: [HIGH/MEDIUM/LOW] - [explanation of research validation]
**Clear-Thought Confidence**: [HIGH/MEDIUM/LOW] - [systematic analysis validation]

Format your response in markdown with clear sections and use star ratings (⭐) for each area.

**PRD Content:**
\`\`\`
$PRD_CONTENT
\`\`\`"

# Run Claude analysis
echo "🤖 Running Claude analysis..."
if echo "$PROMPT" | claude -p > "$OUTPUT_FILE" 2>/dev/null; then
    if [ -s "$OUTPUT_FILE" ]; then
        echo "✅ Analysis complete!"
        echo ""
        echo "📊 Analysis Results:"
        echo "=================="
        cat "$OUTPUT_FILE"
        echo ""
        echo "💾 Full analysis saved to: $OUTPUT_FILE"
        
        # Check for high-risk patterns
        if grep -qi "HIGH\\|REJECT" "$OUTPUT_FILE"; then
            echo ""
            echo "⚠️  HIGH RISK PATTERNS DETECTED"
            echo "Review systematic analysis recommendations before proceeding."
        elif grep -qi "APPROVE" "$OUTPUT_FILE"; then
            echo ""
            echo "✅ PRD APPROVED WITH SYSTEMATIC VALIDATION"
            echo "Ready for engineering planning with research confidence."
        fi
    else
        echo "❌ Claude produced no output"
        exit 1
    fi
else
    echo "❌ Claude analysis failed"
    echo "Check Claude authentication and try again"
    exit 1
fi

echo ""
echo "🎯 Enhanced PRD systematic review complete!"
echo "💡 Next steps:"
echo "   1. Address any HIGH risk anti-patterns identified"
echo "   2. Validate market research findings"
echo "   3. Apply systematic thinking insights to planning"
echo "   4. Run ./scripts/review-engineering-plan.sh for technical validation"