#!/bin/bash
# PRD Review Script - Enhanced systematic validation with MCP tools
# Usage: ./scripts/review-prd.sh <PRD_FILE_PATH> [--verbose]

set -e

# Source shared utilities
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SOURCE_DIR/shared/validation-utils.sh"
source "$SOURCE_DIR/shared/logging-utils.sh"

# Parse arguments
PRD_FILE=""
VERBOSE_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE_MODE=true
            enable_verbose_mode
            shift
            ;;
        *)
            if [ -z "$PRD_FILE" ]; then
                PRD_FILE="$1"
            else
                echo "Error: Multiple PRD files specified"
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$PRD_FILE" ]; then
    echo "Usage: $0 <PRD_FILE_PATH> [--verbose]"
    echo "Example: $0 docs/Product_Requirements_Document.md"
    echo "Example: $0 docs/Product_Requirements_Document.md --verbose"
    exit 1
fi

# Set up logging
PRD_IDENTIFIER=$(basename "$PRD_FILE" .md)
setup_logging "prd" "$PRD_IDENTIFIER"

echo "🎯 Running enhanced PRD review with MCP tools for comprehensive analysis..."
$VERBOSE_MODE && echo "🔍 Verbose mode enabled - detailed logs in: $LOG_DIR"

# Test Claude CLI with logging
if ! test_claude_cli; then
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
log_info "Reading PRD file: $PRD_FILE"
PRD_SIZE=$(wc -c < "$PRD_FILE")
PRD_LINES=$(wc -l < "$PRD_FILE")

if [ "$PRD_SIZE" -eq 0 ]; then
    echo "❌ PRD file is empty"
    log_error "PRD file is empty: $PRD_FILE"
    exit 1
fi

echo "📝 PRD content loaded ($PRD_LINES lines, $PRD_SIZE chars)"
log_debug "PRD file size: $PRD_SIZE characters, $PRD_LINES lines"

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
OUTPUT_FILE="reviews/prd-review-${PRD_IDENTIFIER}-${TIMESTAMP}.md"
echo "💾 Analysis will be saved to: $OUTPUT_FILE"
log_info "Output file: $OUTPUT_FILE"

# Enhanced prompt with MCP tool integration
PROMPT="You are a senior product strategy advisor. Analyze this PRD for anti-patterns using available research tools for comprehensive analysis.

**Enhanced Analysis Instructions:**
1. Use available MCP research tools to validate claims and approaches
2. Search for similar products/solutions to inform recommendations  
3. Research best practices for identified problem areas
4. Provide evidence-based recommendations with external validation
5. **NEW: Apply Clear-Thought MCP tools for systematic product analysis:**
   - Use mental models (First Principles, Opportunity Cost, Pareto Principle) for product validation
   - Apply decision frameworks for feature prioritization and market positioning
   - Employ sequential thinking for complex product strategy evaluation
   - Use collaborative reasoning for stakeholder alignment assessment

**Anti-Patterns to Check:**
1. Solution-first requirements (tech details before user problems)
   - **Apply First Principles:** Strip away solution bias to focus on core user problems
2. Scope creep enablers (vague success criteria)
   - **Use Decision Framework:** Systematic evaluation of scope boundaries and success metrics
3. Resource reality disconnect (no feasibility validation)
   - **Apply Opportunity Cost Analysis:** Evaluate resource allocation against alternatives
4. Stakeholder assumption gaps (missing user research)
   - **Use Collaborative Reasoning:** Simulate stakeholder perspectives and identify gaps
5. Metrics manipulation (vanity metrics vs business impact)
   - **Apply Pareto Principle:** Focus on the 20% of metrics that drive 80% of business value

**Enhanced Analysis Process:**
- Research market validation for the problem domain
- Look up best practices for the proposed solution approach
- Validate technical feasibility claims
- Check for similar solutions and differentiation opportunities
- **Apply systematic thinking frameworks:**
  - Sequential thinking for complex product strategy evaluation
  - Mental model analysis for market positioning and user value
  - Decision framework assessment for feature prioritization
  - Collaborative reasoning for stakeholder alignment

**Required Output Format:**
🎯 **PRD Overview**
[Brief summary]

🔍 **Market Research & Validation**
[Results from research tools about problem domain and solutions]

🚨 **Anti-Pattern Risk Assessment**
[Detected patterns with risk level HIGH/MEDIUM/LOW and research validation]

🔧 **Technical Feasibility Research**
[External validation of technical claims and approaches]

🧠 **Clear-Thought Analysis Results**
[Results from systematic thinking: mental models applied, decision frameworks used, collaborative reasoning insights]

💡 **Evidence-Based Recommendations**
[Top 3 actionable improvements with research backing and systematic thinking validation]

📚 **Research Citations**
[Sources and validation from research tools used]

🎯 **Systematic Thinking Summary**
[Key insights from Clear-Thought tools and how they validate/challenge the PRD approach]

**Overall Assessment**: [APPROVE/NEEDS REVISION/REJECT]
**Research Confidence**: [HIGH/MEDIUM/LOW] - [explanation of research validation]
**Clear-Thought Confidence**: [HIGH/MEDIUM/LOW] - [systematic analysis validation]

**PRD Content:**
\`\`\`
$SUMMARY
\`\`\`"

# Run Claude analysis with MCP tools and enhanced logging
echo "🤖 Running enhanced Claude analysis with MCP research tools..."
echo "🔍 This includes market research, technical validation, and best practices lookup..."
$VERBOSE_MODE && echo "📝 Detailed analysis logs will be captured for debugging"

log_info "Starting Claude analysis with enhanced MCP tools"
if execute_claude_with_logging "$PROMPT" "$OUTPUT_FILE" "PRD analysis with MCP research tools"; then
    
    # Validate output
    if validate_output "$OUTPUT_FILE" 100; then
        echo "✅ Enhanced PRD analysis complete!"
        log_info "Analysis completed successfully"
    else
        echo "⚠️ Primary analysis had issues, trying simplified analysis..."
        log_info "Falling back to simplified analysis"
        
        # Fallback: Simple prompt without MCP tools
        SIMPLE_PROMPT="Analyze this PRD for major anti-patterns. Provide summary and 3 recommendations.

PRD excerpt:
\`\`\`
$(head -n 30 "$PRD_FILE")
\`\`\`"
        
        if execute_claude_with_logging "$SIMPLE_PROMPT" "$OUTPUT_FILE" "Simplified PRD analysis"; then
            if validate_output "$OUTPUT_FILE" 50; then
                echo "✅ Simplified analysis complete!"
                log_info "Fallback analysis completed successfully"
            else
                echo "❌ Even simplified analysis failed"
                log_error "Both primary and fallback analysis failed"
                echo "Manual review required - check logs for details"
                print_log_summary "prd" "$PRD_IDENTIFIER"
                exit 1
            fi
        else
            echo "❌ Claude analysis completely failed"
            log_error "Complete analysis failure"
            echo "Manual review required - check logs for details"
            print_log_summary "prd" "$PRD_IDENTIFIER"
            exit 1
        fi
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
    log_error "Claude CLI execution failed"
    echo "Check Claude authentication and network connection"
    echo "Detailed error information available in logs"
    print_log_summary "prd" "$PRD_IDENTIFIER"
    exit 1
fi

# Clean up old logs
cleanup_old_logs "prd" 10

echo ""
echo "🎯 Enhanced PRD systematic review complete!"
echo "📄 Review the full analysis with research validation in: $OUTPUT_FILE"
echo ""
echo "💡 Next steps:"
echo "   1. Address any HIGH risk anti-patterns identified"
echo "   2. Validate market research findings"
echo "   3. Run ./scripts/review-engineering-plan.sh with MCP enhancement"
echo "   4. Consider external validation of technical feasibility claims"

# Print debug information if verbose mode or if there were issues
if $VERBOSE_MODE || [ -f "$ERROR_LOG" ]; then
    print_log_summary "prd" "$PRD_IDENTIFIER"
fi

log_info "PRD review script completed successfully"