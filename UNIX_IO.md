# Unix-Style I/O Design

The agent follows standard Unix conventions for command-line tools:

## Output Channels

### stdout (File Descriptor 1)
**Purpose**: Final results only - clean, parseable, pipeable data

- Contains ONLY the answer/result to the user's query
- No progress messages, no decorations, no emojis
- Designed to be machine-readable and composable
- Can be piped to other commands or redirected to files

### stderr (File Descriptor 2)
**Purpose**: Informational and progress messages

- Progress indicators (🔧 Executing, 📋 Result, etc.)
- Status messages (🎯 Goal, ✅ Complete, etc.)
- Error messages and warnings
- Debug/verbose output
- User prompts and interaction

## Verbosity Levels

Control via `AGENT_VERBOSITY` environment variable or `--verbosity` flag:

- **quiet**: Only critical errors to stderr, results to stdout
- **normal**: Key actions and results to stderr (default)
- **verbose**: Include agent thoughts and reasoning to stderr
- **debug**: All logs and internal details to stderr

**Important**: Verbosity only affects stderr. stdout always contains just the result.

## Usage Examples

### Basic Usage
```bash
# Normal output - see progress on stderr, result on stdout
./agent.sh "Get AI news from Hacker News"
```

### Redirect Result to File
```bash
# Save result to file, see progress on terminal
./agent.sh "List all Python files" > files.txt

# Save result, hide progress
./agent.sh "List all Python files" > files.txt 2>/dev/null
```

### Pipe Result to Another Command
```bash
# Get AI news and filter with grep
./agent.sh "Get latest news" | grep "GPT"

# Count lines in result
./agent.sh "List TODO comments" | wc -l

# Chain multiple commands
./agent.sh "Find Python files" | xargs wc -l | sort -n
```

### Separate Streams
```bash
# Save result and logs separately
./agent.sh "Analyze code" > result.txt 2> log.txt

# See only result (quiet mode)
./agent.sh -v quiet "Get data"

# See detailed progress but save clean result
./agent.sh -v verbose "Get data" > output.txt
```

### Silent Operation
```bash
# Complete silence except result
./agent.sh -v quiet "Task" 2>/dev/null

# Silent result, see only errors
./agent.sh "Task" >/dev/null
```

### Composition with Other Tools
```bash
# Extract specific data from result
./agent.sh "Get repo stats" | jq '.stars'

# Process result with awk
./agent.sh "List files with sizes" | awk '{sum+=$1} END {print sum}'

# Use in shell scripts
result=$(./agent.sh "Calculate total" 2>/dev/null)
echo "The answer is: $result"
```

## Implementation Details

### Code Structure
```python
# Information to stderr
print(msg, file=sys.stderr)

# Final result to stdout
print(result, file=sys.stdout)
```

### Helper Functions
- `print_quiet()` → stderr (critical messages)
- `print_normal()` → stderr (normal verbosity)
- `print_verbose()` → stderr (verbose mode)
- `print_debug()` → stderr (debug mode)
- `print_result()` → stdout (final result only)

### Exit Codes
Following Unix conventions:
- `0` - Success
- `1` - General error
- `130` - Interrupted by user (Ctrl+C)

## Benefits

1. **Composability**: Results can be piped to other Unix tools
2. **Automation**: Scripts can capture clean results without parsing progress messages
3. **Flexibility**: Users choose what to see (progress, result, or both)
4. **Standard**: Follows established Unix philosophy and conventions
5. **Debuggability**: Progress/errors visible separately from results

## Comparison with Traditional Tools

```bash
# Like grep
grep "pattern" file.txt           # results to stdout
grep "pattern" file.txt 2>&1      # combine streams

# Like curl
curl https://api.com/data         # data to stdout
curl -v https://api.com/data      # progress to stderr

# Like find
find . -name "*.py"               # results to stdout
find . -name "*.py" 2>/dev/null   # hide permission errors

# Our agent
./agent.sh "Get data"             # result to stdout, progress to stderr
./agent.sh "Get data" 2>/dev/null # hide progress
./agent.sh "Get data" | jq        # pipe result to jq
```

## Testing I/O Separation

```bash
# Verify stdout contains only result
./agent.sh "Task" 2>/dev/null | head

# Verify stderr contains only progress
./agent.sh "Task" >/dev/null

# Confirm both work independently
./agent.sh "Task" > out.txt 2> err.txt
cat out.txt  # should be clean result
cat err.txt  # should be progress messages
```
