# Code Analysis Example

This example demonstrates using the agent to analyze a codebase and generate insights.

## What It Does

The agent can:
- Count lines of code by language
- Find TODO/FIXME comments
- List all imports/dependencies
- Analyze project structure
- Show git history
- Identify code smells

## Tools Included

- `find_files_by_extension` - Find files by extension
- `count_lines_by_extension` - Count lines of code
- `find_todos` - Find TODO/FIXME comments
- `find_imports` - List all imports
- `list_files` - List directory contents
- `read_file` - Read file contents
- `git_log` - Show commit history
- `get_directory_structure` - Show file tree

## Usage

### Using Docker

```bash
# Build the image with this example
docker build -t cli-agent:codebase-analyzer .

# Run analysis on your project
docker run --rm -it \
  -v /path/to/your/project:/workspace \
  -v $(pwd)/examples/analyze-codebase/commands.json:/home/agent/.agent/commands.json \
  -e OPENAI_API_KEY="your-key" \
  cli-agent:latest \
  "Analyze this codebase and give me a summary"
```

### Using run-agent.sh

```bash
# Copy commands to default location
cp examples/analyze-codebase/commands.json commands.json

# Rebuild Docker image
docker build -t cli-agent:latest .

# Run on a project
./run-agent.sh "Analyze this Python project" /path/to/project
```

## Example Tasks

### Basic Analysis
```bash
./run-agent.sh "How many lines of Python code are in this project?"
./run-agent.sh "What is the project structure?"
./run-agent.sh "List all Python files"
```

### Code Quality
```bash
./run-agent.sh "Find all TODO comments"
./run-agent.sh "What are the main dependencies?"
./run-agent.sh "Show me the recent commit history"
```

### Comprehensive Analysis
```bash
./run-agent.sh "Analyze this codebase and tell me:
1. Total lines of code by language
2. Number of files
3. All TODO/FIXME comments
4. Main dependencies
5. Recent changes"
```

## Sample Output

```
🎯 Goal: Analyze this codebase and give me a summary

--- Iteration 1 ---
🔧 Executing: list_files({'path': '.'})
📋 Result: Found 12 files and 3 directories

--- Iteration 2 ---
🔧 Executing: find_files_by_extension({'path': '.', 'extension': 'py'})
📋 Result: ./agent.py ./tests/test_agent.py ...

--- Iteration 3 ---
🔧 Executing: count_lines_by_extension({'path': '.', 'extension': 'py'})
📋 Result: 450 total lines of Python code

--- Iteration 4 ---
🔧 Executing: find_todos({'path': '.'})
📋 Result: Found 5 TODO comments...

✅ Final result:
Codebase Analysis Summary:

**Project Statistics:**
- Total Python files: 8
- Total lines of code: 450
- Directories: 3

**Code Quality:**
- TODO comments: 5
- FIXME comments: 2
- Main files: agent.py (189 lines), tests/test_agent.py (156 lines)

**Dependencies:**
- openai
- anthropic

**Recent Activity:**
- 2 commits in last week
- Last commit: "Add input validation"

**Recommendations:**
- Address 5 TODO items
- Consider adding more test coverage
- Good code organization with clear separation
```

## Customization

### Add Language-Specific Analysis

For JavaScript:
```json
{
  "name": "find_npm_packages",
  "description": "List npm dependencies",
  "command": "cat {path}/package.json | jq '.dependencies'",
  "parameters": {...}
}
```

For Go:
```json
{
  "name": "find_go_modules",
  "description": "List Go modules",
  "command": "cat {path}/go.mod",
  "parameters": {...}
}
```

### Add Security Scanning

```json
{
  "name": "find_secrets",
  "description": "Search for potential secrets",
  "command": "grep -rn 'password\\|secret\\|api_key' {path}",
  "parameters": {...}
}
```

## Tips

1. **Start broad, then drill down**: Ask for general analysis first, then specific details
2. **Be specific with paths**: Use `.` for current directory, or full paths
3. **Combine multiple questions**: The agent can handle complex multi-part queries
4. **Interactive mode**: The agent will ask clarifying questions if needed

## Related Examples

- See `examples/devops-tasks/` for CI/CD analysis
- See `examples/log-analysis/` for analyzing application logs
