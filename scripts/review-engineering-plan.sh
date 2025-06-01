#!/bin/bash
# Engineering Plan Review Script - Technical validation with Cognee lessons
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

echo "🎯 Running Engineering Plan review with Cognee retrospective lessons..."

# Check if Claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "❌ Claude CLI not found"
    echo "Please install Claude Code CLI first: https://claude.ai/code"
    exit 1
fi

# Check if plan file exists
if [ ! -f "$PLAN_FILE" ]; then
    echo "❌ Engineering plan file not found: $PLAN_FILE"
    exit 1
fi

# Check PRD file if provided
PRD_CONTENT=""
if [ -n "$PRD_FILE" ]; then
    if [ ! -f "$PRD_FILE" ]; then
        echo "❌ PRD file not found: $PRD_FILE"
        exit 1
    fi
    PRD_CONTENT=$(head -n 50 "$PRD_FILE")
    echo "📋 PRD alignment check enabled with: $PRD_FILE"
fi

# Create reviews directory
mkdir -p reviews

# Get plan content (limit to avoid issues)
echo "📋 Reading Engineering Plan file: $PLAN_FILE"
PLAN_CONTENT=$(head -n 100 "$PLAN_FILE")
PLAN_LINES=$(echo "$PLAN_CONTENT" | wc -l)

echo "📝 Engineering plan content loaded ($PLAN_LINES lines)"

# Create output file
OUTPUT_FILE="reviews/engineering-plan-review-$(basename "$PLAN_FILE" .md)-$(date +%Y%m%d-%H%M%S).md"

# Create PRD section if provided
PRD_SECTION=""
if [ -n "$PRD_CONTENT" ]; then
    PRD_SECTION="

## PRD ALIGNMENT CHECK
**PRD Content:**
\`\`\`
$PRD_CONTENT
\`\`\`"
fi

# Comprehensive engineering plan analysis prompt with Clear-Thought integration
PROMPT="You are a senior technical architect with expertise in preventing systematic engineering failures based on the Cognee retrospective analysis.

**Enhanced Analysis Instructions:**
1. Use available MCP research tools to validate technical approaches and frameworks
2. Research best practices for proposed technologies (FastMCP, MCP protocol, etc.)
3. Look up similar technical implementations for validation
4. Provide evidence-based technical recommendations
5. Apply Cognee retrospective lessons with external research validation
6. **NEW: Use Clear-Thought MCP tools for systematic analysis:**
   - Apply sequential thinking for complex architectural decisions
   - Use mental models (First Principles, Opportunity Cost) for technology evaluation
   - Employ decision frameworks for critical technical choices
   - Leverage debugging approaches for risk assessment

**Critical Context: Known Failure Patterns**

The Cognee integration failed due to these specific patterns:
1. **Infrastructure-Without-Implementation**: Building custom HTTP servers instead of using cognee.add() → cognee.cognify() → cognee.search()
2. **Symptom-Driven Development**: Fixing effects (mock data, no integration) rather than root cause (not using basic API)
3. **Over-Engineering Bias**: Preferring custom solutions over documented API approaches
4. **Requirements-First Development**: Elaborate planning without understanding actual API capabilities

**Engineering Anti-Pattern Detection Framework:**

## 1. ARCHITECTURE WITHOUT VALIDATION ⭐⭐⭐⭐⭐
- Does the plan validate basic integrations work before complex architecture?
- Are there working POCs for core functionality?
- Is complexity justified or could simpler approaches work?
- Research the proposed technical stack for stability and best practices
- Validate complexity claims against industry standards
- Check for simpler alternatives using research tools
- **Apply First Principles thinking:** Break down proposed architecture to fundamental requirements
- **Use Decision Framework:** Evaluate technical stack choices systematically

## 2. INTEGRATION ASSUMPTION FAILURES ⭐⭐⭐⭐⭐  
- Are third-party APIs actually tested vs. assumed to work?
- Does the plan include fallback strategies for API failures?
- Are integration points validated with real data?
- Research third-party APIs and SDKs mentioned
- Validate compatibility and stability claims
- Look up common integration pitfalls
- **Apply Sequential Thinking:** Step through integration dependencies and failure points
- **Use Debugging Approach:** Anticipate and plan for integration failure modes

## 3. SCALE PREMATURE OPTIMIZATION ⭐⭐⭐⭐⭐
- Is scaling planned before basic functionality is proven?
- Are performance assumptions validated with benchmarks?
- Could MVP approach work before optimization?
- **Apply Opportunity Cost Analysis:** Evaluate scaling effort vs. core functionality delivery
- **Use Mental Models:** Assess whether scaling concerns are premature vs. necessary

## 4. TECHNOLOGY SELECTION BIAS ⭐⭐⭐⭐⭐
- Are technology choices based on proven stability vs. novelty?
- Do alternatives exist that are simpler/more established?
- Is team expertise aligned with chosen technologies?
- **Apply Decision Framework:** Systematic technology evaluation with pros/cons analysis
- **Use First Principles:** Evaluate technology choices against core requirements

## 5. RISK ASSESSMENT BLINDNESS ⭐⭐⭐⭐⭐
- Are failure modes identified and mitigated?
- Does the plan include monitoring and rollback strategies?
- Are dependencies and their failure impacts mapped?
- **Apply Debugging Approach:** Systematic identification of potential failure modes
- **Use Sequential Thinking:** Map dependency chains and cascading failure risks

**Required Output Format:**
# Engineering Plan Technical Assessment

## 🎯 **Plan Overview**
[Brief summary of what this engineering plan proposes]

## 🚨 **Anti-Pattern Risk Assessment**
[For each of the 5 categories above, provide: Rating (⭐⭐⭐⭐⭐), Risk Level (HIGH/MEDIUM/LOW), Evidence, Recommendations]

## 🔧 **Technical Validation Requirements**
[What POCs/validations are needed before proceeding]

## ⚖️ **Complexity vs. Value Analysis**
[Is the proposed complexity justified? Simpler alternatives?]

## 🛡️ **Risk Analysis & Mitigation**
[Key failure modes and how to prevent them]$(if [ -n "$PRD_CONTENT" ]; then echo "

## 🔗 **PRD Alignment Assessment**
[How well does this technical approach align with PRD requirements?]"; fi)

## 🧠 **Clear-Thought Analysis Results**
[Results from systematic thinking tools: mental models applied, decision frameworks used, sequential reasoning outcomes]

## 🔍 **Research-Backed Analysis** 
[Results from research tools about technical approaches and frameworks]

## 💡 **Key Recommendations**
[Top 3-5 actionable improvements with Cognee lessons applied]

## 📚 **Technical Research Citations**
[Sources used for validation]

## 🎯 **Systematic Analysis Summary**
[Key insights from Clear-Thought tools and how they inform the technical decision]

**Overall Assessment**: [APPROVE/NEEDS POC/NEEDS SIMPLIFICATION/REJECT]
**Infrastructure-Without-Implementation Risk**: [HIGH/MEDIUM/LOW]
**Research Confidence**: [HIGH/MEDIUM/LOW] - [validation quality]
**Clear-Thought Confidence**: [HIGH/MEDIUM/LOW] - [systematic analysis quality]
**Cognee Lessons Applied**: [Evidence of learning from retrospective]

Use star ratings and provide detailed evidence for each assessment.

**ENGINEERING PLAN TO ANALYZE:**
\`\`\`
$PLAN_CONTENT
\`\`\`$PRD_SECTION"

# Run Claude analysis
echo "🤖 Running comprehensive Claude analysis with Cognee lessons..."
if echo "$PROMPT" | claude -p > "$OUTPUT_FILE" 2>/dev/null; then
    if [ -s "$OUTPUT_FILE" ]; then
        echo "✅ Analysis complete!"
        echo ""
        echo "📊 Analysis Results:"
        echo "=================="
        cat "$OUTPUT_FILE"
        echo ""
        echo "💾 Full analysis saved to: $OUTPUT_FILE"
        
        # Check for high-risk patterns with specific messaging
        if grep -qi "infrastructure-without-implementation.*high" "$OUTPUT_FILE"; then
            echo ""
            echo "🚨 CRITICAL COGNEE-STYLE RISK DETECTED"
            echo "This plan shows infrastructure-without-implementation patterns."
            echo "Follow Cognee lessons: validate basic functionality before complex architecture."
        elif grep -qi "HIGH\\|REJECT" "$OUTPUT_FILE"; then
            echo ""
            echo "⚠️  HIGH RISK PATTERNS DETECTED"
            echo "Review recommendations before proceeding."
        elif grep -qi "APPROVE" "$OUTPUT_FILE"; then
            echo ""
            echo "✅ ENGINEERING PLAN APPROVED"
            echo "Technical approach validated with Cognee lessons."
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
echo "🎯 Engineering plan systematic review complete!"
echo "💡 Next steps:"
echo "   1. Address any HIGH risk anti-patterns identified"
echo "   2. Complete technical validation requirements"
echo "   3. Validate basic integrations per Cognee lessons"