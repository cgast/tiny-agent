#!/usr/bin/env bash
# Unix I/O Examples for tiny-agent
# Demonstrates how to use the agent like standard Unix commands

# ============================================================================
# Basic Examples
# ============================================================================

# Get just the result
./agent.sh "What is 2+2?" 2>/dev/null

# See only progress (no result)
./agent.sh "List files" >/dev/null

# ============================================================================
# File Redirection
# ============================================================================

# Save result to file
./agent.sh "Get AI news from Hacker News" > news.txt

# Save result and logs separately
./agent.sh "Analyze code" > result.txt 2> log.txt

# Append to file
./agent.sh "Get updates" >> updates.txt

# ============================================================================
# Piping to Other Commands
# ============================================================================

# Pipe to grep
./agent.sh "List all files" | grep "\.py$"

# Pipe to wc (count lines)
./agent.sh "Find TODO comments" | wc -l

# Pipe to sort
./agent.sh "List files with sizes" | sort -n

# Pipe to head/tail
./agent.sh "Get news" | head -10

# Pipe to jq (if result is JSON)
./agent.sh "Get repo stats as JSON" | jq '.stars'

# Chain multiple pipes
./agent.sh "List Python files" | xargs wc -l | sort -n | tail -5

# ============================================================================
# Using in Scripts
# ============================================================================

# Capture result in variable
result=$(./agent.sh "Calculate total" 2>/dev/null)
echo "The answer is: $result"

# Use in conditionals
if ./agent.sh "Check if file exists: test.txt" 2>/dev/null | grep -q "exists"; then
    echo "File found"
fi

# Loop over results
./agent.sh "List all logs" 2>/dev/null | while read -r file; do
    echo "Processing: $file"
done

# ============================================================================
# Verbosity Control
# ============================================================================

# Quiet mode (minimal stderr)
./agent.sh -v quiet "Get data"

# Normal mode (default)
./agent.sh -v normal "Get data"

# Verbose mode (show agent thoughts)
./agent.sh -v verbose "Get data"

# Debug mode (all details)
./agent.sh -v debug "Get data"

# ============================================================================
# Combining with Other Unix Tools
# ============================================================================

# Use with awk
./agent.sh "List file sizes" | awk '{sum+=$1} END {print "Total:", sum}'

# Use with sed
./agent.sh "Get URLs" | sed 's/https/http/g'

# Use with cut
./agent.sh "Get CSV data" | cut -d',' -f1,3

# Use with tr (transform)
./agent.sh "Get text" | tr '[:lower:]' '[:upper:]'

# ============================================================================
# Advanced Patterns
# ============================================================================

# Tee to both file and screen
./agent.sh "Important results" 2>/dev/null | tee results.txt

# Process result with multiple tools
./agent.sh "Get stats" 2>/dev/null | jq '.data[]' | grep "important" | sort | uniq

# Compare two results
diff <(./agent.sh "Get old data" 2>/dev/null) <(./agent.sh "Get new data" 2>/dev/null)

# Parallel execution with different verbosity
./agent.sh -v quiet "Task 1" > out1.txt 2>&1 &
./agent.sh -v quiet "Task 2" > out2.txt 2>&1 &
wait

# ============================================================================
# Error Handling
# ============================================================================

# Check exit code
if ./agent.sh "Risky task" >/dev/null 2>&1; then
    echo "Success"
else
    echo "Failed with code: $?"
fi

# Redirect errors only
./agent.sh "Task" 2>&1 >/dev/null | grep "Error"

# ============================================================================
# Integration Examples
# ============================================================================

# Feed result to another command
cat input.txt | xargs -I {} ./agent.sh "Process: {}" 2>/dev/null

# Use in cron job (silent)
# 0 * * * * /path/to/agent.sh -v quiet "Hourly task" >> /var/log/agent.log 2>&1

# Use in systemd service
# ExecStart=/path/to/agent.sh "Monitor task"
# StandardOutput=file:/var/log/agent-output.log
# StandardError=file:/var/log/agent-error.log

# Use with xargs for parallel processing
echo -e "task1\ntask2\ntask3" | xargs -P 3 -I {} ./agent.sh "{}" 2>/dev/null

# ============================================================================
# Debugging
# ============================================================================

# See both streams separately on terminal
./agent.sh "Debug this" 1> >(tee stdout.log) 2> >(tee stderr.log >&2)

# Measure execution time
time ./agent.sh "Long task" 2>&1

# Add timestamps to stderr
./agent.sh "Task" 2> >(ts '[%Y-%m-%d %H:%M:%S]' >&2)
