# Log Analysis Example

This example demonstrates using the agent to analyze application logs and troubleshoot issues.

## What It Does

The agent can:
- Find and analyze log files
- Count errors and warnings
- Search for specific patterns
- Identify unique IPs
- Show log time ranges
- Summarize log contents

## Tools Included

- `find_log_files` - Find all log files
- `tail_log` - Show recent log entries
- `grep_errors` - Find error messages
- `grep_warnings` - Find warnings
- `count_errors` - Count errors
- `search_pattern` - Search for patterns
- `get_log_size` - Check log file size
- `count_unique_ips` - Count unique IPs
- `get_log_timerange` - Show time range

## Usage

### Setup Test Data

```bash
# Create sample log files
mkdir -p workspace/logs

cat > workspace/logs/app.log << 'EOF'
2024-01-15 10:00:01 INFO Starting application
2024-01-15 10:00:02 INFO Connected to database
2024-01-15 10:05:23 WARN High memory usage: 85%
2024-01-15 10:10:45 ERROR Failed to connect to API: timeout
2024-01-15 10:11:12 ERROR Database connection lost
2024-01-15 10:11:13 INFO Attempting reconnection
2024-01-15 10:11:14 INFO Reconnection successful
2024-01-15 10:15:30 WARN Slow query detected: 2.5s
2024-01-15 10:20:00 ERROR Exception in handler: NullPointerException
EOF
```

### Run Analysis

```bash
# Copy commands
cp examples/log-analysis/commands.json commands.json
docker build -t cli-agent:latest .

# Analyze logs
./run-agent.sh "Analyze the logs and tell me about any errors"
```

## Example Tasks

### Error Analysis
```bash
./run-agent.sh "How many errors are in the app.log file?"
./run-agent.sh "Show me all error messages from today"
./run-agent.sh "What's the most common error?"
```

### Performance Monitoring
```bash
./run-agent.sh "Find all warnings in the logs"
./run-agent.sh "Are there any slow query warnings?"
./run-agent.sh "What's the time range of this log file?"
```

### Security Analysis
```bash
./run-agent.sh "How many unique IP addresses accessed the system?"
./run-agent.sh "Find any failed login attempts"
./run-agent.sh "Search for suspicious patterns in the logs"
```

### Comprehensive Analysis
```bash
./run-agent.sh "Analyze all logs in the directory and summarize:
1. Total number of errors and warnings
2. Most common error types
3. Time range covered
4. Any security concerns"
```

## Sample Output

```
🎯 Goal: Analyze the logs and tell me about any errors

--- Iteration 1 ---
🔧 Executing: find_log_files({'path': '/workspace/logs'})
📋 Result: /workspace/logs/app.log

--- Iteration 2 ---
🔧 Executing: count_errors({'file': '/workspace/logs/app.log'})
📋 Result: 3

--- Iteration 3 ---
🔧 Executing: grep_errors({'file': '/workspace/logs/app.log'})
📋 Result:
2024-01-15 10:10:45 ERROR Failed to connect to API: timeout
2024-01-15 10:11:12 ERROR Database connection lost
2024-01-15 10:20:00 ERROR Exception in handler: NullPointerException

--- Iteration 4 ---
🔧 Executing: get_log_timerange({'file': '/workspace/logs/app.log'})
📋 Result:
First: 2024-01-15 10:00:01 INFO Starting application
Last: 2024-01-15 10:20:00 ERROR Exception in handler: NullPointerException

✅ Final result:
Log Analysis Summary:

**Error Overview:**
- Total Errors: 3
- Total Warnings: 2
- Time Range: 2024-01-15 10:00:01 to 10:20:00 (20 minutes)

**Error Details:**
1. API Connection Timeout (10:10:45)
   - Failed to connect to external API

2. Database Connection Lost (10:11:12)
   - Connection dropped but successfully reconnected

3. NullPointerException (10:20:00)
   - Exception in request handler

**Warning Details:**
1. High memory usage (85%) at 10:05:23
2. Slow query detected (2.5s) at 10:15:30

**Recommendations:**
- Investigate API timeout issues
- Monitor database connection stability
- Fix NullPointerException in handler code
- Review memory usage patterns
- Optimize slow database queries
```

## Advanced Use Cases

### Log Aggregation

```bash
# Analyze multiple log files
./run-agent.sh "Compare errors across all log files in /workspace/logs"
```

### Time-Based Analysis

```bash
# Focus on specific timeframe
./run-agent.sh "Show me all errors that occurred between 10:00 and 11:00"
```

### Pattern Detection

```bash
# Find correlation
./run-agent.sh "Do database errors correlate with high memory usage?"
```

## Customization

### Add Custom Log Patterns

For Apache logs:
```json
{
  "name": "parse_apache_status",
  "description": "Count HTTP status codes",
  "command": "awk '{print $9}' {file} | sort | uniq -c",
  "parameters": {...}
}
```

For JSON logs:
```json
{
  "name": "query_json_logs",
  "description": "Query JSON log entries",
  "command": "grep '{pattern}' {file} | jq '{query}'",
  "parameters": {...}
}
```

### Add Alerting

```json
{
  "name": "check_error_threshold",
  "description": "Alert if errors exceed threshold",
  "command": "count=$(grep -ic 'error' {file}); if [ $count -gt {threshold} ]; then echo 'ALERT: High error count'; fi",
  "parameters": {...}
}
```

## Tips

1. **Start with overview**: "How many log files are there?" → "Which one is largest?" → "Analyze that one"
2. **Be specific**: Mention exact error types you're looking for
3. **Use time ranges**: If logs have timestamps, ask about specific periods
4. **Combine analysis**: Ask about errors AND warnings together for full picture

## Related Examples

- See `examples/devops-tasks/` for system monitoring
- See `examples/analyze-codebase/` for code-level analysis
