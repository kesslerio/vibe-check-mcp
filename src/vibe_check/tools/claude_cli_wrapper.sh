#!/bin/bash
# Claude CLI wrapper for complete MCP isolation
# This script provides a clean execution environment for Claude CLI calls
# that prevents recursion detection when called from MCP servers

set -e

# Default values
TIMEOUT=60
TASK_TYPE="general"
VERBOSE=false
OUTPUT_FILE=""
TEMP_DIR="/tmp"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prompt)
            PROMPT="$2"
            shift 2
            ;;
        --task-type)
            TASK_TYPE="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --input-file)
            INPUT_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$PROMPT" ] && [ -z "$INPUT_FILE" ]; then
    echo "Error: Either --prompt or --input-file must be specified"
    exit 1
fi

# Create completely isolated environment
# Remove ALL Claude/MCP related environment variables
unset CLAUDE_CODE_MODE
unset CLAUDE_CLI_SESSION
unset MCP_SERVER
unset CLAUDECODE
unset CLAUDE_EXTERNAL_EXECUTION
unset CLAUDE_MCP_ISOLATED
unset CLAUDE_TASK_ID
unset ANTHROPIC_MCP_SERVER

# Build clean environment array
CLEAN_ENV_VARS=(
    "PATH=$PATH"
    "HOME=$HOME"
    "USER=$USER"
    "SHELL=$SHELL"
)

# Preserve Anthropic API key if it exists
if [ -n "$ANTHROPIC_API_KEY" ]; then
    CLEAN_ENV_VARS+=("ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY")
fi

# Set up task-specific prompting
case $TASK_TYPE in
    "code_analysis")
        TASK_INSTRUCTION="You are an expert code analyst. Review this code for potential issues, anti-patterns, security vulnerabilities, and provide improvement suggestions:"
        ;;
    "pr_review")
        TASK_INSTRUCTION="You are a senior software engineer conducting a code review. Analyze this pull request for code quality, security, and best practices:"
        ;;
    "issue_analysis")
        TASK_INSTRUCTION="You are a technical product manager. Analyze this GitHub issue for quality, clarity, and implementation considerations:"
        ;;
    *)
        TASK_INSTRUCTION="Please analyze the following:"
        ;;
esac

# Build the full prompt
if [ -n "$INPUT_FILE" ]; then
    if [ ! -f "$INPUT_FILE" ]; then
        echo "Error: Input file '$INPUT_FILE' not found"
        exit 1
    fi
    FILE_CONTENT=$(cat "$INPUT_FILE")
    FULL_PROMPT="$TASK_INSTRUCTION

File: $INPUT_FILE

$FILE_CONTENT"
else
    FULL_PROMPT="$TASK_INSTRUCTION

$PROMPT"
fi

# Generate unique identifiers for this execution
EXECUTION_ID="claude_$(date +%s)_$$"
PROMPT_FILE="$TEMP_DIR/${EXECUTION_ID}_prompt.txt"
OUTPUT_TEMP="$TEMP_DIR/${EXECUTION_ID}_output.txt"
ERROR_TEMP="$TEMP_DIR/${EXECUTION_ID}_error.txt"

# Write prompt to temporary file to avoid command line length issues
echo "$FULL_PROMPT" > "$PROMPT_FILE"

if [ "$VERBOSE" = true ]; then
    echo "Executing Claude CLI with complete environment isolation..."
    echo "Task Type: $TASK_TYPE"
    echo "Timeout: $TIMEOUT seconds"
    echo "Prompt file: $PROMPT_FILE"
    echo "Environment variables being passed:"
    printf '%s\n' "${CLEAN_ENV_VARS[@]}"
fi

# Execute Claude CLI in completely isolated environment using timeout
START_TIME=$(date +%s)
EXIT_CODE=0

# Use env -i to start with completely clean environment, then add only what we need
timeout "$TIMEOUT" env -i "${CLEAN_ENV_VARS[@]}" claude -p --dangerously-skip-permissions "$(cat "$PROMPT_FILE")" > "$OUTPUT_TEMP" 2> "$ERROR_TEMP" || EXIT_CODE=$?

END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))

# Check for timeout (exit code 124)
if [ $EXIT_CODE -eq 124 ]; then
    ERROR_MESSAGE="Claude CLI timed out after ${TIMEOUT} seconds"
    if [ "$VERBOSE" = true ]; then
        echo "Error: $ERROR_MESSAGE"
    fi
    
    # Generate timeout result JSON
    cat > "$OUTPUT_TEMP" << EOF
{
  "success": false,
  "output": null,
  "error": "$ERROR_MESSAGE",
  "exit_code": 124,
  "execution_time_seconds": $EXECUTION_TIME,
  "command_used": "claude -p --dangerously-skip-permissions (isolated)",
  "task_type": "$TASK_TYPE",
  "timestamp": $(date +%s),
  "isolation_method": "shell_wrapper"
}
EOF
elif [ $EXIT_CODE -eq 0 ]; then
    # Success case - generate success result JSON
    OUTPUT_CONTENT=$(cat "$OUTPUT_TEMP" | jq -R -s '.')
    cat > "$OUTPUT_TEMP" << EOF
{
  "success": true,
  "output": $OUTPUT_CONTENT,
  "error": null,
  "exit_code": 0,
  "execution_time_seconds": $EXECUTION_TIME,
  "command_used": "claude -p --dangerously-skip-permissions (isolated)",
  "task_type": "$TASK_TYPE",
  "timestamp": $(date +%s),
  "isolation_method": "shell_wrapper"
}
EOF
else
    # Error case - generate error result JSON
    ERROR_CONTENT=$(cat "$ERROR_TEMP" | jq -R -s '.')
    cat > "$OUTPUT_TEMP" << EOF
{
  "success": false,
  "output": null,
  "error": $ERROR_CONTENT,
  "exit_code": $EXIT_CODE,
  "execution_time_seconds": $EXECUTION_TIME,
  "command_used": "claude -p --dangerously-skip-permissions (isolated)",
  "task_type": "$TASK_TYPE",
  "timestamp": $(date +%s),
  "isolation_method": "shell_wrapper"
}
EOF
fi

# Output results
if [ -n "$OUTPUT_FILE" ]; then
    cp "$OUTPUT_TEMP" "$OUTPUT_FILE"
    if [ "$VERBOSE" = true ]; then
        echo "Results written to: $OUTPUT_FILE"
    fi
else
    cat "$OUTPUT_TEMP"
fi

# Cleanup temporary files
rm -f "$PROMPT_FILE" "$ERROR_TEMP"
if [ -z "$OUTPUT_FILE" ]; then
    rm -f "$OUTPUT_TEMP"
fi

if [ "$VERBOSE" = true ]; then
    echo "Execution completed in ${EXECUTION_TIME} seconds with exit code $EXIT_CODE"
fi

exit $EXIT_CODE 