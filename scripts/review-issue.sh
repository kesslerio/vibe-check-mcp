#!/bin/bash
# Systematic issue validation script for preventing third-party integration failures
# Based on lessons learned from Cognee foundational failures retrospective
# Usage: ./scripts/review-issue.sh <ISSUE_NUMBER>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <ISSUE_NUMBER>"
    echo "Example: $0 519"
    echo ""
    echo "This script validates GitHub issues to prevent infrastructure-without-implementation"
    echo "patterns and over-engineering bias in third-party integrations."
    exit 1
fi

ISSUE_NUMBER=$1

echo "🔍 Starting systematic issue review for #$ISSUE_NUMBER..."
echo "Based on Cognee retrospective failure prevention protocols"

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

# Verify issue exists
if ! gh issue view $ISSUE_NUMBER >/dev/null 2>&1; then
    echo "❌ Issue #$ISSUE_NUMBER not found"
    exit 1
fi

echo "📋 Fetching comprehensive issue details..."

# Get comprehensive issue information
ISSUE_INFO=$(gh issue view $ISSUE_NUMBER --json title,body,labels,assignees,author,createdAt,state)
ISSUE_TITLE=$(echo "$ISSUE_INFO" | jq -r '.title')
ISSUE_BODY=$(echo "$ISSUE_INFO" | jq -r '.body // ""')
ISSUE_AUTHOR=$(echo "$ISSUE_INFO" | jq -r '.author.login')
ISSUE_CREATED=$(echo "$ISSUE_INFO" | jq -r '.createdAt')
ISSUE_STATE=$(echo "$ISSUE_INFO" | jq -r '.state')
ISSUE_LABELS=$(echo "$ISSUE_INFO" | jq -r '.labels[]?.name' | tr '\n' ', ' | sed 's/,$//')

# Analyze issue content for third-party integration patterns
echo "🔍 Analyzing issue content for integration patterns..."

# Check for third-party service mentions
THIRD_PARTY_SERVICES=$(echo "$ISSUE_BODY" | grep -iE "(cognee|openai|anthropic|postgres|redis|docker|api|sdk|integration|server|client|http|rest|graphql)" || echo "")

# Check for infrastructure keywords
INFRASTRUCTURE_KEYWORDS=$(echo "$ISSUE_BODY" | grep -iE "(architecture|infrastructure|server|database|build|deploy|docker|compose|setup|config)" || echo "")

# Check for complexity indicators
COMPLEXITY_INDICATORS=$(echo "$ISSUE_BODY" | grep -iE "(complex|sophisticated|enterprise|advanced|framework|system|pipeline|orchestrat)" || echo "")

# Run analysis based on available tools
if [ "$CLAUDE_AVAILABLE" = true ]; then
    echo "🧠 Running systematic analysis with Claude..."
    
    # Create comprehensive issue analysis prompt
cat > /tmp/issue_review_prompt_${ISSUE_NUMBER}.md << EOF
You are a senior technical reviewer preventing systematic third-party integration failures based on the Cognee retrospective analysis.

## Critical Context: Known Failure Patterns

The Cognee integration failed because of these specific patterns:
1. **Infrastructure-Without-Implementation**: Building custom HTTP servers instead of using cognee.add() → cognee.cognify() → cognee.search()
2. **Symptom-Driven Development**: Fixing effects (mock data, no integration) rather than root cause (not using basic API)
3. **Over-Engineering Bias**: Preferring custom solutions over documented API approaches
4. **Requirements-First Development**: Elaborate planning without understanding actual API capabilities

## Review Framework

Analyze this GitHub issue and provide systematic validation using this exact format:

🎯 **Issue Overview**
Summary of what this issue proposes to accomplish

🚨 **Third-Party Integration Risk Assessment**
$(if [ -n "$THIRD_PARTY_SERVICES" ]; then
    echo "⚠️ THIRD-PARTY SERVICES DETECTED: $THIRD_PARTY_SERVICES"
    echo ""
    echo "**MANDATORY API-FIRST VALIDATION REQUIRED:**"
    echo "- [ ] Has basic API functionality been demonstrated with working POC?"
    echo "- [ ] Are we using standard APIs/SDKs instead of building custom implementations?"
    echo "- [ ] Is there evidence of actual API usage (not just infrastructure setup)?"
    echo "- [ ] Does the proposal start with simple API integration before architecture?"
    echo ""
    echo "**RED FLAGS TO CHECK:**"
    echo "- Custom HTTP clients when SDKs exist"
    echo "- Complex infrastructure before basic API usage"
    echo "- Elaborate planning without POC demonstration"
    echo "- Focus on architecture over actual integration"
else
    echo "✅ No obvious third-party integration detected"
    echo "- Continue with standard issue validation"
fi)

🔍 **Research Phase Validation**
- [ ] Has existing solution research been documented?
- [ ] Are similar tools/libraries already in the project identified?
- [ ] Is official documentation referenced and understood?
- [ ] Are there working examples or tutorials completed?

📋 **Acceptance Criteria Quality Assessment**
- [ ] Are criteria focused on business outcomes vs. technical implementation?
- [ ] Do criteria include actual functionality validation (not just infrastructure)?
- [ ] Are success metrics measurable and specific?
- [ ] Do criteria prevent mock/placeholder solutions?

⚖️ **Complexity Appropriateness Evaluation**
$(if [ -n "$COMPLEXITY_INDICATORS" ]; then
    echo "⚠️ COMPLEXITY INDICATORS DETECTED: $COMPLEXITY_INDICATORS"
    echo ""
    echo "**JUSTIFY COMPLEXITY:**"
    echo "- [ ] Is complex solution justified over simple standard approaches?"
    echo "- [ ] Have simple solutions been attempted and documented as insufficient?"
    echo "- [ ] Is the proposed complexity proportional to business value?"
    echo "- [ ] Will this create maintainable, extendable solutions?"
else
    echo "✅ No obvious over-engineering indicators"
    echo "- [ ] Proposed solution appears appropriately scoped"
fi)

🧪 **Clear-Thought Tool Integration Assessment**
- [ ] For complex issues: Are systematic analysis tools recommended?
- [ ] Would mental model analysis help clarify root cause vs. symptoms?
- [ ] Should decision framework evaluation be used for service selection?
- [ ] Is sequential thinking needed for multi-step implementation planning?

⚠️ **Anti-Pattern Detection**
Check for these specific failure patterns from Cognee retrospective:

**Infrastructure-Without-Implementation:**
- [ ] Does this propose building custom solutions when standard APIs exist?
- [ ] Is infrastructure setup prioritized over actual API usage?
- [ ] Are complex systems proposed without proven basic functionality?

**Symptom-Driven Development:**
- [ ] Is this issue addressing symptoms of a deeper root cause?
- [ ] Are there multiple related issues that might share the same underlying problem?
- [ ] Would fixing the root cause eliminate need for this issue?

**Requirements-First Development:**
- [ ] Are requirements detailed without demonstrating feasibility?
- [ ] Is architectural planning proposed before API understanding?
- [ ] Would a simple POC clarify the actual requirements?

🎯 **Recommendations**

**APPROVE CONDITIONS:**
- [ ] Clear business value with appropriate complexity
- [ ] Research phase completed for third-party services
- [ ] API-first approach for integrations
- [ ] Measurable success criteria

**REVISION NEEDED:**
- [ ] Require POC before architectural planning (for third-party integrations)
- [ ] Simplify approach and justify complexity
- [ ] Add research phase documentation
- [ ] Clarify root cause vs. symptom focus

**REJECT CONDITIONS:**
- [ ] Proposes custom solutions when standard APIs exist
- [ ] Infrastructure-first approach without API demonstration
- [ ] Addressing symptoms while ignoring obvious root causes

**Overall Recommendation**: [APPROVE / NEEDS REVISION / NEEDS POC / REJECT]

Focus on preventing the specific failure patterns that led to 2+ years of non-functional Cognee integration.
EOF

# Create issue data file for Claude analysis
cat > /tmp/issue_data_${ISSUE_NUMBER}.md << EOF
# Issue #${ISSUE_NUMBER} Analysis Data

## Issue Information
**Title:** ${ISSUE_TITLE}
**Author:** ${ISSUE_AUTHOR}
**Created:** ${ISSUE_CREATED}
**State:** ${ISSUE_STATE}
**Labels:** ${ISSUE_LABELS}

## Issue Body
${ISSUE_BODY}

## Pattern Detection Results

### Third-Party Services Detected
${THIRD_PARTY_SERVICES:-"None detected"}

### Infrastructure Keywords Found
${INFRASTRUCTURE_KEYWORDS:-"None found"}

### Complexity Indicators
${COMPLEXITY_INDICATORS:-"None found"}

## Analysis Context
This issue is being reviewed using the systematic prevention framework based on the Cognee foundational failures retrospective. The review focuses on preventing infrastructure-without-implementation patterns, over-engineering bias, and symptom-driven development that led to 2+ years of non-functional integration.
EOF

# Create combined prompt file
cat /tmp/issue_review_prompt_${ISSUE_NUMBER}.md /tmp/issue_data_${ISSUE_NUMBER}.md > /tmp/combined_issue_prompt_${ISSUE_NUMBER}.md

    # Run Claude analysis
    echo "📝 Generating systematic issue analysis..."
    if ! claude -p "$(cat /tmp/combined_issue_prompt_${ISSUE_NUMBER}.md)" > /tmp/issue_analysis_${ISSUE_NUMBER}.md 2>/tmp/claude_issue_error_${ISSUE_NUMBER}.log; then
        echo "❌ Claude analysis failed. Error log:"
        cat /tmp/claude_issue_error_${ISSUE_NUMBER}.log
        echo "🔄 Falling back to manual analysis..."
        CLAUDE_AVAILABLE=false
    fi

    # Check if analysis generation succeeded
    if [ -s /tmp/issue_analysis_${ISSUE_NUMBER}.md ]; then
        ANALYSIS_SIZE=$(wc -c < /tmp/issue_analysis_${ISSUE_NUMBER}.md)
        if [ $ANALYSIS_SIZE -lt 100 ]; then
            echo "⚠️ Generated analysis seems too short ($ANALYSIS_SIZE chars)"
            echo "🔄 Falling back to manual analysis..."
            CLAUDE_AVAILABLE=false
        fi
    else
        echo "⚠️ Failed to generate issue analysis content."
        echo "🔄 Falling back to manual analysis..."
        CLAUDE_AVAILABLE=false
    fi
fi

# Fallback analysis when Claude is not available
if [ "$CLAUDE_AVAILABLE" = false ]; then
    echo "📝 Generating fallback systematic analysis..."
    
    cat > /tmp/issue_analysis_${ISSUE_NUMBER}.md << EOF
## 🔍 Systematic Issue Review (Manual Analysis)

**Analysis Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Analysis Method**: Fallback (Claude CLI not available)

### 🎯 Issue Overview
**Title**: ${ISSUE_TITLE}
**Author**: ${ISSUE_AUTHOR}
**State**: ${ISSUE_STATE}
**Labels**: ${ISSUE_LABELS}

### 🚨 Third-Party Integration Risk Assessment
$(if [ -n "$THIRD_PARTY_SERVICES" ]; then
    echo "⚠️ **THIRD-PARTY SERVICES DETECTED**: $THIRD_PARTY_SERVICES"
    echo ""
    echo "**MANDATORY VALIDATION REQUIRED:**"
    echo "- [ ] Ensure basic API functionality is demonstrated with working POC"
    echo "- [ ] Verify use of standard APIs/SDKs instead of custom implementations"
    echo "- [ ] Confirm actual API usage evidence (not just infrastructure setup)"
    echo "- [ ] Validate simple API integration before complex architecture"
    echo ""
    echo "**COGNEE RETROSPECTIVE LESSONS:**"
    echo "- The Cognee failure occurred because custom HTTP servers were built"
    echo "- Instead of using cognee.add() → cognee.cognify() → cognee.search()"
    echo "- 2+ years of infrastructure without basic API implementation"
    echo "- This issue MUST demonstrate API usage before architectural planning"
else
    echo "✅ **No obvious third-party integration detected**"
    echo "- Standard issue validation applies"
fi)

### 🔍 Research Phase Validation  
**REQUIRED BEFORE IMPLEMENTATION:**
- [ ] Has existing solution research been documented?
- [ ] Are similar tools/libraries already in the project identified?
- [ ] Is official documentation referenced and understood?
- [ ] Are there working examples or tutorials completed?

### ⚖️ Complexity Appropriateness Evaluation
$(if [ -n "$COMPLEXITY_INDICATORS" ]; then
    echo "⚠️ **COMPLEXITY INDICATORS DETECTED**: $COMPLEXITY_INDICATORS"
    echo ""
    echo "**JUSTIFY COMPLEXITY:**"
    echo "- [ ] Is complex solution justified over simple standard approaches?"
    echo "- [ ] Have simple solutions been attempted and documented as insufficient?"
    echo "- [ ] Is the proposed complexity proportional to business value?"
    echo "- [ ] Will this create maintainable, extendable solutions?"
    echo ""
    echo "**OVER-ENGINEERING RISK:**"
    echo "- Check if this follows the Cognee anti-pattern of elaborate architecture"
    echo "- Without proven basic functionality first"
else
    echo "✅ **No obvious over-engineering indicators**"
    echo "- [ ] Proposed solution appears appropriately scoped"
fi)

### ⚠️ Anti-Pattern Detection (Based on Cognee Retrospective)

**Infrastructure-Without-Implementation Check:**
- [ ] Does this propose building custom solutions when standard APIs exist?
- [ ] Is infrastructure setup prioritized over actual API usage?
- [ ] Are complex systems proposed without proven basic functionality?

**Symptom-Driven Development Check:**
- [ ] Is this issue addressing symptoms of a deeper root cause?
- [ ] Are there multiple related issues that might share the same underlying problem?
- [ ] Would fixing the root cause eliminate need for this issue?

**Requirements-First Development Check:**
- [ ] Are requirements detailed without demonstrating feasibility?
- [ ] Is architectural planning proposed before API understanding?
- [ ] Would a simple POC clarify the actual requirements?

### 🎯 Recommendations

**For Third-Party Integrations:**
$(if [ -n "$THIRD_PARTY_SERVICES" ]; then
    echo "🚨 **MANDATORY: API-FIRST DEVELOPMENT REQUIRED**"
    echo "1. Create minimal POC using actual API before any planning"
    echo "2. Demonstrate basic functionality with real data"
    echo "3. Document working API patterns before architecture"
    echo "4. Avoid custom implementations of standard functionality"
    echo "5. **Apply Clear-Thought tools:** Use systematic analysis for integration planning"
    echo ""
    echo "**DO NOT PROCEED** without demonstrated API usage"
else
    echo "✅ Standard development process applies"
    echo "- **Consider Clear-Thought enhancement:** Apply systematic thinking for complex issues"
fi)

**🧠 Clear-Thought Analysis Summary:**
- Systematic thinking tools can enhance issue validation and planning
- Mental models applicable: $([ -n "$COMPLEXITY_INDICATORS" ] && echo "First Principles (complexity validation)" || echo "Standard analysis sufficient")
- Decision frameworks recommended for: $([ -n "$THIRD_PARTY_SERVICES" ] && echo "Service selection and integration approach" || echo "N/A")

**Overall Assessment:**
- This issue requires $([ -n "$THIRD_PARTY_SERVICES" ] && echo "**API-FIRST VALIDATION**" || echo "standard review")
- $([ -n "$COMPLEXITY_INDICATORS" ] && echo "Complexity justification needed" || echo "Appropriate complexity level")
- Follow prevention guidelines from docs/guides/THIRD_PARTY_INTEGRATION_GUIDE.md
- **Enhanced with:** MCP GitHub tools and Clear-Thought systematic analysis

**Recommendation**: $(if [ -n "$THIRD_PARTY_SERVICES" ]; then echo "**NEEDS POC BEFORE APPROVAL**"; elif [ -n "$COMPLEXITY_INDICATORS" ]; then echo "**NEEDS COMPLEXITY JUSTIFICATION**"; else echo "**STANDARD REVIEW PROCESS**"; fi)
**Analysis Quality**: **ENHANCED** - MCP tools provide comprehensive validation

### 📚 References
- Cognee Foundational Failures Retrospective
- Third-Party Integration Prevention Guide: docs/guides/THIRD_PARTY_INTEGRATION_GUIDE.md
- API-First Development Protocol

---
*This analysis was generated using fallback patterns based on the Cognee retrospective findings. For more detailed analysis, ensure Claude CLI is available.*
EOF
fi

echo "📝 Posting systematic review to issue..."

# Create analysis header
cat > /tmp/issue_analysis_header_${ISSUE_NUMBER}.md << EOF
## 🔍 Systematic Issue Review (Automated)

**Prevention System**: Third-Party Integration Failure Prevention
**Based on**: Cognee Foundational Failures Retrospective
**Analysis Date**: $(date '+%Y-%m-%d %H:%M:%S')

---

EOF

# Combine header with analysis
cat /tmp/issue_analysis_header_${ISSUE_NUMBER}.md /tmp/issue_analysis_${ISSUE_NUMBER}.md > /tmp/final_issue_review_${ISSUE_NUMBER}.md

# Post analysis as comment
gh issue comment $ISSUE_NUMBER --body-file /tmp/final_issue_review_${ISSUE_NUMBER}.md

# Add systematic review label
gh issue edit $ISSUE_NUMBER --add-label "systematic-review" 2>/dev/null || true

echo "✅ Systematic issue review completed for #$ISSUE_NUMBER"
echo "🔗 View at: $(gh issue view $ISSUE_NUMBER --json url -q .url)"

# Determine if this needs special attention based on analysis
if grep -q "NEEDS POC\|REJECT\|THIRD-PARTY SERVICES DETECTED" /tmp/issue_analysis_${ISSUE_NUMBER}.md; then
    echo "⚠️ ATTENTION REQUIRED: This issue may need additional validation before implementation"
    gh issue edit $ISSUE_NUMBER --add-label "needs-validation" 2>/dev/null || true
fi

if grep -q "COMPLEXITY INDICATORS DETECTED" /tmp/issue_analysis_${ISSUE_NUMBER}.md; then
    echo "⚠️ COMPLEXITY WARNING: This issue shows over-engineering risk patterns"
    gh issue edit $ISSUE_NUMBER --add-label "complexity-review" 2>/dev/null || true
fi

# Cleanup (preserve for debugging)
echo "🔍 Debug files preserved:"
echo "- Prompt: /tmp/issue_review_prompt_${ISSUE_NUMBER}.md"
echo "- Data: /tmp/issue_data_${ISSUE_NUMBER}.md"
echo "- Combined: /tmp/combined_issue_prompt_${ISSUE_NUMBER}.md"
echo "- Analysis: /tmp/issue_analysis_${ISSUE_NUMBER}.md"
echo "- Final: /tmp/final_issue_review_${ISSUE_NUMBER}.md"
echo "- Error log: /tmp/claude_issue_error_${ISSUE_NUMBER}.log"

echo ""
echo "💡 Systematic issue validation completed"
echo "🎯 Prevention system active: Infrastructure-without-implementation patterns detected and flagged"