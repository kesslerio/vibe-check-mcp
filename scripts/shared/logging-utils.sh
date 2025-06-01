#!/bin/bash
# Shared logging utilities for review scripts
# Provides verbose logging, debug capabilities, and log management

# Set up logging environment
setup_logging() {
    local script_type="$1"  # prd, engineering-plan, pr, issue
    local identifier="$2"   # file name, PR number, issue number, etc.
    
    # Create timestamp for this run
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    
    # Set up log directory
    LOG_DIR="logs/${script_type}/${TIMESTAMP}"
    mkdir -p "$LOG_DIR"
    
    # Set up log files
    VERBOSE_LOG="${LOG_DIR}/verbose-${identifier}.log"
    DEBUG_LOG="${LOG_DIR}/debug-${identifier}.log"
    PROMPT_LOG="${LOG_DIR}/prompt-${identifier}.md"
    RESPONSE_LOG="${LOG_DIR}/response-${identifier}.md"
    ERROR_LOG="${LOG_DIR}/error-${identifier}.log"
    
    # Create log files to ensure they exist
    touch "$VERBOSE_LOG" "$DEBUG_LOG" "$PROMPT_LOG" "$RESPONSE_LOG" "$ERROR_LOG"
    
    # Export for use in calling script
    export LOG_DIR VERBOSE_LOG DEBUG_LOG PROMPT_LOG RESPONSE_LOG ERROR_LOG TIMESTAMP
    
    # Log script start
    log_info "=== Starting ${script_type} review for ${identifier} at $(date) ==="
    log_debug "Log directory: $LOG_DIR"
    log_debug "Environment: $(uname -a)"
    log_debug "Working directory: $(pwd)"
    log_debug "Script: $0 $*"
    
    # Log Claude version and MCP info for debugging
    log_debug "Claude version: $(claude --version 2>/dev/null || echo 'unknown')"
    log_debug "MCP servers will be logged in verbose output if --verbose works correctly"
}

# Logging functions
log_info() {
    local message="$1"
    # Only use tee if debug log is defined and exists
    if [ -n "$DEBUG_LOG" ] && [ -f "$DEBUG_LOG" ]; then
        echo "[$(date '+%H:%M:%S')] INFO: $message" | tee -a "$DEBUG_LOG"
    else
        echo "[$(date '+%H:%M:%S')] INFO: $message"
    fi
}

log_debug() {
    local message="$1"
    echo "[$(date '+%H:%M:%S')] DEBUG: $message" >> "$DEBUG_LOG"
}

log_error() {
    local message="$1"
    # Only use tee if both log files are defined
    if [ -n "$DEBUG_LOG" ] && [ -n "$ERROR_LOG" ]; then
        echo "[$(date '+%H:%M:%S')] ERROR: $message" | tee -a "$DEBUG_LOG" "$ERROR_LOG"
    elif [ -n "$DEBUG_LOG" ]; then
        echo "[$(date '+%H:%M:%S')] ERROR: $message" | tee -a "$DEBUG_LOG"
    else
        echo "[$(date '+%H:%M:%S')] ERROR: $message"
    fi
}

log_verbose() {
    local message="$1"
    echo "[$(date '+%H:%M:%S')] VERBOSE: $message" >> "$VERBOSE_LOG"
}

# Enhanced Claude execution with verbose logging
execute_claude_with_logging() {
    local prompt_content="$1"
    local output_file="$2"
    local description="$3"
    local use_verbose="${4:-true}"  # Default to verbose mode
    
    log_info "Starting Claude analysis: $description"
    log_debug "Output file: $output_file"
    log_debug "Prompt size: $(echo "$prompt_content" | wc -c) characters"
    log_debug "Verbose mode: $use_verbose"
    
    # Save prompt for debugging
    echo "$prompt_content" > "$PROMPT_LOG"
    log_debug "Prompt saved to: $PROMPT_LOG"
    
    # Build Claude command with proper verbose flag
    local claude_cmd="claude -p"
    if [ "$use_verbose" = "true" ]; then
        claude_cmd="$claude_cmd --verbose"
    fi
    
    # Execute Claude with verbose logging
    log_verbose "=== CLAUDE EXECUTION START ==="
    log_verbose "Command: $claude_cmd"
    log_verbose "Timestamp: $(date)"
    log_verbose "Description: $description"
    
    # Use separate files to capture stdout and stderr
    local temp_output="/tmp/claude_output_$$"
    local temp_verbose="/tmp/claude_verbose_$$"
    
    # Execute Claude command and capture verbose output to stderr
    if echo "$prompt_content" | eval "$claude_cmd" > "$temp_output" 2> "$temp_verbose"; then
        # Success case
        local output_size=$(wc -c < "$temp_output")
        log_verbose "=== CLAUDE EXECUTION SUCCESS ==="
        log_verbose "Exit code: 0"
        log_verbose "Output size: $output_size characters"
        
        # Copy output to final location
        cp "$temp_output" "$output_file"
        cp "$temp_output" "$RESPONSE_LOG"
        
        # Capture verbose output (stderr contains turn-by-turn debugging info)
        if [ -s "$temp_verbose" ]; then
            log_verbose "=== CLAUDE VERBOSE DEBUGGING OUTPUT ==="
            echo "[$(date '+%H:%M:%S')] === Claude --verbose output ===" >> "$VERBOSE_LOG"
            cat "$temp_verbose" >> "$VERBOSE_LOG"
            echo "[$(date '+%H:%M:%S')] === End Claude verbose output ===" >> "$VERBOSE_LOG"
            
            # Also log summary of verbose output to debug log
            local verbose_lines=$(wc -l < "$temp_verbose")
            log_debug "Captured $verbose_lines lines of verbose debugging output"
        else
            log_debug "No verbose output captured (may indicate --verbose not working or no debug info)"
        fi
        
        # Cleanup
        rm -f "$temp_output" "$temp_verbose"
        
        log_info "Claude analysis completed successfully (output: $output_size chars)"
        return 0
    else
        # Failure case
        local exit_code=$?
        log_error "Claude execution failed with exit code: $exit_code"
        log_verbose "=== CLAUDE EXECUTION FAILURE ==="
        log_verbose "Exit code: $exit_code"
        log_verbose "Command: $claude_cmd"
        
        # Log verbose debugging output (even on failure, may contain useful info)
        if [ -s "$temp_verbose" ]; then
            log_error "=== CLAUDE VERBOSE DEBUG OUTPUT (FAILURE) ==="
            echo "[$(date '+%H:%M:%S')] === Claude --verbose output (FAILED) ===" >> "$VERBOSE_LOG"
            cat "$temp_verbose" >> "$VERBOSE_LOG"
            [ -n "$ERROR_LOG" ] && cat "$temp_verbose" >> "$ERROR_LOG"
            echo "[$(date '+%H:%M:%S')] === End Claude verbose output (FAILED) ===" >> "$VERBOSE_LOG"
        else
            log_error "No verbose output available for debugging"
        fi
        
        # Log any partial output
        if [ -s "$temp_output" ]; then
            log_verbose "=== CLAUDE PARTIAL OUTPUT ==="
            cat "$temp_output" >> "$VERBOSE_LOG"
            # Also copy partial output for debugging
            cp "$temp_output" "$RESPONSE_LOG"
        fi
        
        # Cleanup
        rm -f "$temp_output" "$temp_verbose"
        
        return $exit_code
    fi
}

# Check if output file is valid
validate_output() {
    local output_file="$1"
    local min_size="${2:-50}"  # Minimum expected size in characters
    
    if [ ! -f "$output_file" ]; then
        log_error "Output file does not exist: $output_file"
        return 1
    fi
    
    if [ ! -s "$output_file" ]; then
        log_error "Output file is empty: $output_file"
        return 1
    fi
    
    local file_size=$(wc -c < "$output_file")
    if [ "$file_size" -lt "$min_size" ]; then
        log_error "Output file too small ($file_size chars, expected >= $min_size): $output_file"
        return 1
    fi
    
    log_info "Output validation passed: $file_size characters"
    return 0
}

# Clean up old logs (keep last 10 runs per script type)
cleanup_old_logs() {
    local script_type="$1"
    local keep_count="${2:-10}"
    
    log_debug "Cleaning up old logs for $script_type (keeping last $keep_count)"
    
    if [ -d "logs/$script_type" ]; then
        # Find timestamp directories and remove oldest ones
        cd "logs/$script_type" || return
        ls -1 | grep -E '^20[0-9]{6}-[0-9]{6}$' | sort | head -n -"$keep_count" | xargs rm -rf
        cd - > /dev/null || return
    fi
}

# Print log summary at end of script
print_log_summary() {
    local script_type="$1"
    local identifier="$2"
    
    echo ""
    echo "🔍 Debug Information:"
    echo "===================="
    echo "📁 Log Directory: $LOG_DIR"
    echo "📋 Debug Log: $DEBUG_LOG"
    echo "📝 Prompt Used: $PROMPT_LOG" 
    echo "📄 Claude Response: $RESPONSE_LOG"
    echo "🔍 Verbose Log (--verbose output): $VERBOSE_LOG"
    [ -f "$ERROR_LOG" ] && echo "❌ Error Log: $ERROR_LOG"
    echo ""
    echo "💡 For debugging Claude issues:"
    echo "   - Check turn-by-turn verbose: cat '$VERBOSE_LOG'"
    echo "   - Review exact prompt sent: cat '$PROMPT_LOG'"
    echo "   - Examine Claude response: cat '$RESPONSE_LOG'"
    [ -f "$ERROR_LOG" ] && echo "   - Check error details: cat '$ERROR_LOG'"
    echo ""
    echo "🛠️  Debugging tips:"
    echo "   - The verbose log shows Claude's internal turn-by-turn processing"
    echo "   - Look for MCP tool usage and any errors in the verbose output"
    echo "   - Compare prompt vs response to identify content/format issues"
    if [ -f "$ERROR_LOG" ]; then
        echo "   - Error log contains stderr output and failure details"
    fi
    echo ""
}

# Function to check if verbose mode is enabled
is_verbose_mode() {
    [[ "${VERBOSE:-}" == "true" || "${DEBUG:-}" == "true" ]]
}

# Function to enable verbose mode
enable_verbose_mode() {
    export VERBOSE=true
    log_info "Verbose mode enabled"
}

# Function to test Claude CLI availability with logging
test_claude_cli() {
    log_debug "Testing Claude CLI availability"
    
    if ! command -v claude &> /dev/null; then
        log_error "Claude CLI not found in PATH"
        echo "❌ Claude CLI not found"
        echo "Please install Claude Code CLI first: https://claude.ai/code"
        return 1
    fi
    
    local claude_path=$(which claude)
    log_debug "Claude CLI found: $claude_path"
    
    # Test Claude with a simple command (avoid --help as it may not work with pipes)
    echo "🔍 Testing Claude CLI..."
    if echo "test" | claude -p "respond with 'ok'" > /dev/null 2>&1; then
        log_debug "Claude CLI test successful"
        log_debug "Claude version: $(claude --version 2>/dev/null || echo 'version unknown')"
        return 0
    else
        log_error "Claude CLI test failed"
        echo "⚠️ Claude CLI found but not responding correctly"
        echo "Check Claude authentication and network connection"
        echo "Try running: claude -p 'test' manually to diagnose"
        return 1
    fi
}