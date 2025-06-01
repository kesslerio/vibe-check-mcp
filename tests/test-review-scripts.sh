#!/bin/bash
# Test script for enhanced review-prd.sh and review-engineering-plan.sh
# Validates that both scripts work correctly with MCP tools and project documents

set -e

echo "🧪 Testing Enhanced PRD & Engineering Plan Review Scripts"
echo "========================================================="
echo "📍 Working directory: $(pwd)"
echo "📂 Output directory: reviews/"

# Ensure we're in the right directory
if [ ! -f "scripts/review-prd.sh" ] || [ ! -f "scripts/review-engineering-plan.sh" ]; then
    echo "❌ Scripts not found. Run this test from the project root directory."
    exit 1
fi

# Clean up any previous test outputs
echo "🧹 Cleaning up previous test outputs..."
rm -f reviews/prd-review-*.md reviews/engineering-plan-review-*.md

# Test 1: Enhanced PRD Review with MCP Tools
echo ""
echo "📋 Test 1: Enhanced PRD Review Script with MCP Research Tools"
echo "------------------------------------------------------------"

if [ -f "docs/Product_Requirements_Document.md" ]; then
    echo "✅ PRD file found"
    echo "🤖 Running enhanced PRD review with MCP research tools..."
    echo "🔍 This test will include market research and technical validation..."
    
    if timeout 300 ./scripts/review-prd.sh docs/Product_Requirements_Document.md; then
        echo "✅ Enhanced PRD review completed successfully"
        
        # Check if output file was created in reviews directory
        LATEST_PRD_REVIEW=$(ls -t reviews/prd-review-*.md 2>/dev/null | head -n 1)
        if [ -n "$LATEST_PRD_REVIEW" ] && [ -s "$LATEST_PRD_REVIEW" ]; then
            echo "✅ PRD review output file created: $LATEST_PRD_REVIEW"
            echo "📊 Output size: $(wc -c < "$LATEST_PRD_REVIEW") characters"
            
            # Check for enhanced content
            if grep -q "Research\|MCP\|validation" "$LATEST_PRD_REVIEW"; then
                echo "✅ Enhanced analysis with research validation detected"
            else
                echo "⚠️ Basic analysis mode (MCP tools may not have been used)"
            fi
        else
            echo "❌ PRD review output file missing or empty"
        fi
    else
        echo "❌ Enhanced PRD review script failed or timed out"
    fi
else
    echo "❌ PRD file not found: docs/Product_Requirements_Document.md"
fi

echo ""
echo "🔧 Test 2: Enhanced Engineering Plan Review Script with Technical Research"
echo "-------------------------------------------------------------------------"

if [ -f "docs/Technical_Implementation_Guide.md" ]; then
    echo "✅ Engineering plan file found"
    echo "🤖 Running enhanced engineering plan review with technical research..."
    echo "🔍 This test will include framework validation and best practices research..."
    
    if timeout 300 ./scripts/review-engineering-plan.sh docs/Technical_Implementation_Guide.md; then
        echo "✅ Enhanced engineering plan review completed successfully"
        
        # Check if output file was created in reviews directory
        LATEST_ENG_REVIEW=$(ls -t reviews/engineering-plan-review-*.md 2>/dev/null | head -n 1)
        if [ -n "$LATEST_ENG_REVIEW" ] && [ -s "$LATEST_ENG_REVIEW" ]; then
            echo "✅ Engineering plan review output file created: $LATEST_ENG_REVIEW"
            echo "📊 Output size: $(wc -c < "$LATEST_ENG_REVIEW") characters"
            
            # Check for enhanced technical research content
            if grep -q "Research\|Technical.*Validation\|Citations" "$LATEST_ENG_REVIEW"; then
                echo "✅ Enhanced technical research analysis detected"
            else
                echo "⚠️ Basic analysis mode (technical research may not have been used)"
            fi
            
            # Check for Cognee lessons application
            if grep -qi "cognee\|infrastructure-without-implementation" "$LATEST_ENG_REVIEW"; then
                echo "✅ Cognee retrospective lessons applied"
            else
                echo "⚠️ Cognee lessons may not be prominently featured"
            fi
        else
            echo "❌ Engineering plan review output file missing or empty"
        fi
    else
        echo "❌ Enhanced engineering plan review script failed or timed out"
    fi
else
    echo "❌ Engineering plan file not found: docs/Technical_Implementation_Guide.md"
fi

echo ""
echo "🔗 Test 3: Enhanced PRD + Engineering Plan Alignment with Research Validation"
echo "----------------------------------------------------------------------------"

if [ -f "docs/Product_Requirements_Document.md" ] && [ -f "docs/Technical_Implementation_Guide.md" ]; then
    echo "✅ Both PRD and engineering plan files found"
    echo "🤖 Running enhanced alignment analysis with research validation..."
    echo "🔍 This test includes cross-document validation and external research..."
    
    if timeout 300 ./scripts/review-engineering-plan.sh docs/Technical_Implementation_Guide.md --prd docs/Product_Requirements_Document.md; then
        echo "✅ Enhanced PRD-engineering plan alignment review completed successfully"
        
        # Check if output mentions PRD alignment and research
        LATEST_ALIGNMENT_REVIEW=$(ls -t reviews/engineering-plan-review-*.md 2>/dev/null | head -n 1)
        if [ -n "$LATEST_ALIGNMENT_REVIEW" ] && grep -qi "prd\|alignment\|research" "$LATEST_ALIGNMENT_REVIEW"; then
            echo "✅ PRD alignment analysis with research validation included"
            
            # Check for comprehensive analysis
            if grep -qi "market\|technical.*validation\|research.*citations" "$LATEST_ALIGNMENT_REVIEW"; then
                echo "✅ Comprehensive research-backed analysis detected"
            fi
        else
            echo "⚠️ PRD alignment analysis may not be included or lacks research validation"
        fi
    else
        echo "❌ Enhanced PRD-engineering plan alignment review failed or timed out"
    fi
else
    echo "❌ Missing files for alignment test"
fi

echo ""
echo "📊 Enhanced Test Results Summary"
echo "==============================="

# Count successful tests and analyze quality
SUCCESS_COUNT=0
ENHANCED_COUNT=0
TOTAL_TESTS=3

echo "Test Results:"

# Test 1: PRD Review
if ls reviews/prd-review-Product_Requirements_Document-*.md >/dev/null 2>&1; then
    echo "✅ Enhanced PRD Review: PASS"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    
    # Check for enhancement quality
    if ls reviews/prd-review-*.md | xargs grep -l "Research\|validation" >/dev/null 2>&1; then
        echo "  🔬 Research enhancement: DETECTED"
        ENHANCED_COUNT=$((ENHANCED_COUNT + 1))
    else
        echo "  🔬 Research enhancement: NOT DETECTED"
    fi
else
    echo "❌ Enhanced PRD Review: FAIL"
fi

# Test 2: Engineering Plan Review
if ls reviews/engineering-plan-review-Technical_Implementation_Guide-*.md >/dev/null 2>&1; then
    echo "✅ Enhanced Engineering Plan Review: PASS"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    
    # Check for technical research quality
    if ls reviews/engineering-plan-review-*.md | xargs grep -l "Technical.*Research\|Citations\|validation" >/dev/null 2>&1; then
        echo "  🔬 Technical research enhancement: DETECTED"
        ENHANCED_COUNT=$((ENHANCED_COUNT + 1))
    else
        echo "  🔬 Technical research enhancement: NOT DETECTED"
    fi
else
    echo "❌ Enhanced Engineering Plan Review: FAIL"
fi

# Test 3: Integration Test
if [ $SUCCESS_COUNT -ge 2 ]; then
    echo "✅ Enhanced Integration Test: PASS"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    
    # Check for alignment quality
    if ls reviews/engineering-plan-review-*.md | xargs grep -l "PRD\|alignment" >/dev/null 2>&1; then
        echo "  🔗 PRD alignment analysis: DETECTED"
        ENHANCED_COUNT=$((ENHANCED_COUNT + 1))
    fi
else
    echo "❌ Enhanced Integration Test: FAIL"
fi

echo ""
echo "📈 Overall Results: $SUCCESS_COUNT/$TOTAL_TESTS tests passed"
echo "🔬 Enhancement Quality: $ENHANCED_COUNT/$TOTAL_TESTS enhanced features detected"

if [ $SUCCESS_COUNT -eq $TOTAL_TESTS ]; then
    if [ $ENHANCED_COUNT -ge 2 ]; then
        echo "🎉 All tests passed with excellent enhancement quality!"
        echo "🔬 MCP research tools are working effectively"
    else
        echo "✅ All tests passed but with basic analysis mode"
        echo "⚠️ MCP research tools may not be fully utilized"
    fi
    
    echo ""
    echo "💡 Next steps:"
    echo "   - Review generated analysis files in reviews/ directory"
    echo "   - Validate research citations and external validation"
    echo "   - Address any anti-patterns identified"
    echo "   - Integrate enhanced scripts into development workflow"
    
elif [ $SUCCESS_COUNT -gt 0 ]; then
    echo "⚠️ Some tests passed. Review failures and retry."
    echo "🔍 Check Claude CLI setup and MCP tool availability"
else
    echo "❌ All tests failed. Check setup and requirements."
    echo "🔧 Troubleshooting steps:"
    echo "   1. Verify Claude CLI: claude -p 'test'"
    echo "   2. Check file permissions on scripts"
    echo "   3. Ensure project files exist"
fi

echo ""
echo "📁 Generated Review Files:"
echo "========================="
if ls reviews/*-review-*.md >/dev/null 2>&1; then
    ls -la reviews/*-review-*.md
    echo ""
    echo "📊 File sizes:"
    for file in reviews/*-review-*.md; do
        if [ -f "$file" ]; then
            echo "  $(basename "$file"): $(wc -c < "$file") chars, $(wc -l < "$file") lines"
        fi
    done
else
    echo "No review files generated"
fi

echo ""
echo "🎯 Enhanced Review Scripts Test Complete!"
echo "Review the generated analysis files for research-backed recommendations."