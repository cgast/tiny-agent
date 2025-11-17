# Tool Templates

This directory contains categorized tool templates that can be used with the CLI agent. Each template is a JSON file defining CLI commands that the agent can execute.

## Directory Structure

```
templates/
├── basic/              # Basic file and system operations
├── development/        # Development-related tools
├── data/              # Data processing and API tools
└── devops/            # DevOps and monitoring tools
```

## Available Templates

### Basic Tools

#### file-operations.json (7 tools)
- `list_files` - List directory contents
- `read_file` - Read file contents
- `write_file` - Write to a file
- `copy_file` - Copy files/directories
- `move_file` - Move/rename files
- `delete_file` - Delete files/directories
- `create_directory` - Create directories

#### text-processing.json (7 tools)
- `find_files` - Find files by pattern
- `search_content` - Search text in files (grep)
- `search_case_insensitive` - Case-insensitive search
- `count_lines` - Count lines in file
- `word_count` - Count words in file
- `tail_file` - Show last N lines
- `head_file` - Show first N lines

#### system-info.json (5 tools)
- `get_disk_usage` - Get directory size
- `get_disk_usage_detailed` - Detailed disk usage
- `check_file_type` - Determine file type
- `get_file_info` - Detailed file stats
- `find_large_files` - Find files by size

### Development Tools

#### git-tools.json (5 tools)
- `git_status` - Show repo status
- `git_log` - Show commit history
- `git_diff` - Show changes
- `git_branch` - List branches
- `git_show_file` - Show file from commit

#### python-tools.json (6 tools)
- `python_run_script` - Execute Python script
- `python_check_syntax` - Validate Python syntax
- `find_python_files` - Find all .py files
- `count_python_lines` - Count lines of Python code
- `find_python_imports` - List all imports
- `find_python_todos` - Find TODO comments

#### docker-tools.json (3 tools)
- `find_dockerfiles` - Find Dockerfiles
- `find_docker_compose` - Find docker-compose files
- `check_dockerfile_syntax` - Validate Dockerfile

### Data Tools

#### json-tools.json (4 tools)
- `read_json` - Pretty-print JSON
- `query_json` - Query with jq
- `validate_json` - Validate JSON syntax
- `find_json_files` - Find all JSON files

#### csv-tools.json (4 tools)
- `read_csv_head` - Show first N rows
- `count_csv_rows` - Count rows
- `find_csv_files` - Find all CSV files
- `csv_column_extract` - Extract column

#### api-tools.json (4 tools)
- `http_get` - Make GET request
- `http_get_json` - GET and format JSON
- `http_headers` - Get HTTP headers
- `download_file` - Download from URL

### DevOps Tools

#### log-analysis.json (5 tools)
- `tail_log` - Show last N log lines
- `grep_log_errors` - Find errors in logs
- `grep_log_warnings` - Find warnings in logs
- `count_log_errors` - Count error occurrences
- `find_log_files` - Find all log files

#### monitoring-tools.json (4 tools)
- `check_process` - Check if process is running
- `get_system_uptime` - Show uptime
- `check_disk_space` - Show disk usage
- `get_memory_usage` - Show memory usage

## Using Templates

### Option 1: Copy to commands.json
```bash
# Use a single template
cp templates/basic/file-operations.json commands.json

# Combine multiple templates
jq -s 'add' templates/basic/*.json > commands.json
```

### Option 2: Use with Docker
```bash
# Mount specific template
docker run --rm -it \
  -v $(pwd)/workspace:/workspace \
  -v $(pwd)/templates/development/git-tools.json:/home/agent/.agent/commands.json \
  -e OPENAI_API_KEY="your-key" \
  cli-agent:latest \
  "Show git status"

# Or update Dockerfile to copy specific template
COPY templates/development/git-tools.json /home/agent/.agent/commands.json
```

### Option 3: Merge Templates
```bash
# Merge multiple categories
jq -s 'add' \
  templates/basic/file-operations.json \
  templates/basic/text-processing.json \
  templates/development/git-tools.json \
  > commands.json
```

## Creating Custom Templates

Each tool follows this schema:

```json
{
  "name": "tool_name",
  "description": "What the tool does",
  "command": "bash_command {arg1} {arg2}",
  "parameters": {
    "type": "object",
    "properties": {
      "arg1": {
        "type": "string",
        "description": "Description of arg1"
      },
      "arg2": {
        "type": "string",
        "description": "Description of arg2"
      }
    },
    "required": ["arg1"]
  }
}
```

### Template Guidelines

1. **Command Safety**: Only include safe, read-only commands in shared templates
2. **Clear Descriptions**: Make descriptions helpful for the LLM
3. **Parameter Validation**: Use JSON Schema to validate inputs
4. **Error Handling**: Commands should handle errors gracefully
5. **Documentation**: Document what each tool does and when to use it

## Examples by Use Case

### Code Analysis
```bash
jq -s 'add' \
  templates/basic/text-processing.json \
  templates/development/python-tools.json \
  templates/development/git-tools.json \
  > commands.json
```

### Log Analysis
```bash
jq -s 'add' \
  templates/basic/text-processing.json \
  templates/devops/log-analysis.json \
  > commands.json
```

### Data Processing
```bash
jq -s 'add' \
  templates/data/json-tools.json \
  templates/data/csv-tools.json \
  templates/data/api-tools.json \
  > commands.json
```

### System Administration
```bash
jq -s 'add' \
  templates/basic/system-info.json \
  templates/devops/monitoring-tools.json \
  > commands.json
```

## Security Considerations

- **Read-only by default**: Most templates only read data
- **Destructive operations**: file-operations.json includes delete/write (use carefully)
- **API access**: api-tools.json makes external requests
- **Process access**: monitoring-tools.json accesses system processes

Always review templates before use in production environments.

## Contributing Templates

To contribute a new template:

1. Create JSON file in appropriate category
2. Follow the tool schema format
3. Test with the agent
4. Document in this README
5. Submit pull request

## Template Statistics

- **Total Tools**: 54
- **Categories**: 4 (basic, development, data, devops)
- **Template Files**: 10
- **Most Tools**: text-processing.json (7 tools)
- **Smallest**: docker-tools.json (3 tools)
