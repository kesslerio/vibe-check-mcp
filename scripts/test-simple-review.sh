#!/bin/bash
# Simple test script to validate Claude integration
set -e

echo "🧪 Testing simple Claude integration..."

# Simple prompt without MCP tools
SIMPLE_PROMPT="You are a code reviewer. Analyze this simple test and respond with 'TEST SUCCESSFUL' if you can process this request.

Test content: This is a basic functionality test."

echo "📝 Running simple test..."
if echo "$SIMPLE_PROMPT" | claude -p --verbose > /tmp/test_output.txt 2> /tmp/test_verbose.txt; then
    echo "✅ Claude execution successful"
    echo "📄 Response:"
    cat /tmp/test_output.txt
    echo ""
    echo "🔍 Verbose output:"
    cat /tmp/test_verbose.txt
else
    echo "❌ Claude execution failed"
    echo "Error output:"
    cat /tmp/test_verbose.txt
    exit 1
fi

echo ""
echo "🎯 Test complete - Claude is working properly"