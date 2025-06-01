#!/bin/bash
# Shared validation utilities for review scripts
# Common functions for Claude integration and response formatting

# Check if Claude CLI is available and working
check_claude_cli() {
    if ! command -v claude &> /dev/null; then
        echo "❌ Claude CLI not found"
        echo "Please install Claude Code CLI first: https://claude.ai/code"
        return 1
    fi
    
    # Test basic Claude functionality
    if ! claude -p "test" >/dev/null 2>&1; then
        echo "❌ Claude CLI not working properly"
        echo "Please check authentication and network connection"
        return 1
    fi
    
    return 0
}

# Check if file exists and is readable
check_file() {
    local file_path="$1"
    local file_type="$2"
    
    if [ ! -f "$file_path" ]; then
        echo "❌ ${file_type} file not found: $file_path"
        return 1
    fi
    
    if [ ! -r "$file_path" ]; then
        echo "❌ ${file_type} file not readable: $file_path"
        return 1
    fi
    
    local content=$(cat "$file_path")
    if [ -z "$content" ]; then
        echo "❌ ${file_type} file is empty: $file_path"
        return 1
    fi
    
    return 0
}

# Get file size and warn if too large
check_file_size() {
    local file_path="$1"
    local max_size="${2:-30000}"  # Default 30KB limit
    
    local file_size=$(wc -c < "$file_path")
    echo "📝 File size: ${file_size} characters"
    
    if [ "$file_size" -gt "$max_size" ]; then
        echo "⚠️ Warning: File is large (${file_size} chars, limit: ${max_size})"
        echo "Claude may have difficulty processing. Consider breaking into sections."
        return 1
    fi
    
    return 0
}

# Run Claude with error handling and output validation
run_claude_analysis() {
    local prompt_file="$1"
    local output_file="$2"
    local analysis_type="$3"
    
    echo "🤖 Running Claude ${analysis_type} analysis..."
    echo "⏱️ This may take 1-3 minutes..."
    
    # Run Claude with timeout
    if timeout 300 claude -p "$(cat "$prompt_file")" > "$output_file" 2>/dev/null; then
        
        # Check if output was generated
        if [ ! -s "$output_file" ]; then
            echo "❌ Claude produced no output"
            echo "This could be due to:"
            echo "  - Document too large or complex"
            echo "  - Network connectivity issues"
            echo "  - Claude API rate limiting"
            return 1
        fi
        
        # Check if output looks valid (contains expected sections)
        if ! grep -q "Overview\|Assessment\|Recommendations" "$output_file"; then
            echo "⚠️ Warning: Claude output may be incomplete"
            echo "Review the analysis file manually"
        fi
        
        echo "✅ ${analysis_type} analysis complete!"
        return 0
        
    else
        echo "❌ Claude analysis failed or timed out"
        echo "Try:"
        echo "  1. Check network connection"
        echo "  2. Reduce document size"
        echo "  3. Try again in a few minutes"
        return 1
    fi
}

# Display analysis results with formatting
display_analysis_results() {
    local output_file="$1"
    local analysis_type="$2"
    
    echo ""
    echo "📊 ${analysis_type} Analysis Results:"
    echo "=================="
    cat "$output_file"
    echo ""
    echo "💾 Full analysis saved to: $output_file"
    
    # Check for high-risk patterns and provide specific feedback
    if grep -qi "risk.*high\|critical" "$output_file"; then
        echo ""
        echo "⚠️  HIGH RISK PATTERNS DETECTED"
        echo "This document contains patterns that could lead to significant technical debt."
        echo "Review recommendations carefully before proceeding."
        return 1
    elif grep -qi "approve" "$output_file"; then
        echo ""
        echo "✅ ANALYSIS APPROVED"
        echo "Anti-pattern analysis indicates this document is ready for next phase."
        return 0
    else
        echo ""
        echo "📋 MIXED RESULTS"
        echo "Review the detailed analysis for specific recommendations."
        return 0
    fi
}

# Extract and display key recommendations
display_key_recommendations() {
    local output_file="$1"
    
    if grep -qi "recommendations\|next steps" "$output_file"; then
        echo ""
        echo "🎯 Key Recommendations:"
        echo "======================"
        # Extract recommendations section
        grep -A 15 -i "recommendations\|💡" "$output_file" | head -n 10
    fi
}