# Tiny Agent

> A minimal, extensible agent framework that executes tasks using command-line tools.

**Runs in a Docker sandbox** for security and isolation.

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## ⭐ Key Features

- ✅ **Minimal Core**: ~380 lines of clean, readable Python code
- ✅ **Interactive Mode**: Aider-like REPL with slash commands, history, and undo
- ✅ **Three Interfaces**: CLI, HTTP API, and Pure Core
- ✅ **Extensible**: 50+ tools in templates, 4 complete examples
- ✅ **Secure**: Sandboxed Docker execution, input validation, path traversal protection
- ✅ **Robust**: Retry logic with exponential backoff, timeout handling, comprehensive error handling
- ✅ **Observable**: Structured logging with configurable levels, token usage tracking
- ✅ **LLM Agnostic**: OpenAI, Anthropic, or bring your own
- ✅ **Unix Philosophy**: stdout for results, stderr for progress - composable with pipes
- ✅ **MIT Licensed**: Free to use and modify

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/cgast/tiny-agent.git
cd tiny-agent
./setup.sh

# 2. Set your API key
export OPENAI_API_KEY=sk-your-key-here
# OR
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# 3. Run the agent
./agent.sh "Find all Python files"

# Or run in Docker sandbox
./agent.sh --mode sandbox "Find all Python files"
```

## 📖 Table of Contents

- [Architecture](#-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
  - [CLI Usage](#cli-usage)
  - [HTTP API Usage](#http-api-usage)
  - [Programmatic Usage](#programmatic-usage)
- [Commands and Tools](#-commands-and-tools)
- [Templates and Examples](#-templates-and-examples)
- [Configuration](#-configuration)
- [Unix-Style I/O](#-unix-style-io)
- [Security](#-security)
- [Development](#-development)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## 🏗 Architecture

Tiny Agent uses a clean, modular architecture with three separate components:

```
┌──────────────────────────────────────┐
│   agent_core.py (~380 lines)         │  ← Pure agent logic
│   - LLM interaction                  │     No I/O dependencies
│   - Tool execution                   │     Callback-based
│   - Planning & reasoning             │     Easy to test
└──────────────────────────────────────┘
         ▲                    ▲
         │                    │
         │ Callbacks          │ Callbacks
         │                    │
┌────────────────┐   ┌─────────────────┐
│ agent_cli.py   │   │ agent_api.py    │
│ (~180 lines)   │   │ (~330 lines)    │
│                │   │                 │
│ CLI wrapper    │   │ HTTP API        │
│ stdin/stdout   │   │ Flask + SSE     │
└────────────────┘   └─────────────────┘
```

### Components

1. **[agent_core.py](agent_core.py)** - Pure agent logic with callback interface
   - No print statements or input() calls
   - All I/O through callbacks
   - Easy to test and reuse

2. **[agent_cli.py](agent_cli.py)** - Command-line interface
   - Unix-style I/O (results to stdout, progress to stderr)
   - Verbosity control
   - Interactive prompts

3. **[agent_api.py](agent_api.py)** - HTTP API server
   - Flask-based REST API
   - Server-Sent Events for streaming
   - Multi-session support

For detailed architecture diagrams and flow, see [.claude/reports/](.claude/reports/).

## 💾 Installation

### Requirements

- Python 3.8+
- Docker (optional, for sandbox mode)
- OpenAI or Anthropic API key

### Install

```bash
# Clone the repository
git clone https://github.com/cgast/tiny-agent.git
cd tiny-agent

# Run setup script (creates venv, installs dependencies)
./setup.sh

# Or manually
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### API Keys

```bash
# Option 1: Environment variables
export OPENAI_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4

# Option 2: .env file (create from template)
cp .env.example .env
# Edit .env and add your keys
```

## 🎯 Usage

### CLI Usage

The CLI interface is the simplest way to use Tiny Agent:

```bash
# Basic usage
./agent.sh "Find all Python files"
./agent.sh "Count lines of code in all .py files"
./agent.sh "Search for TODO comments"

# Sandbox mode (Docker)
./agent.sh --mode sandbox "Analyze this codebase"
./agent.sh -m sandbox -w ./logs "How many errors are in the logs?"

# Unix-style piping (results to stdout, progress to stderr)
./agent.sh "Get AI news from Hacker News" > news.txt
./agent.sh "List Python files" | grep "test"
./agent.sh "Calculate total" 2>/dev/null  # Quiet mode

# Verbosity control
export AGENT_VERBOSITY=quiet    # Only errors
export AGENT_VERBOSITY=normal   # Key actions (default)
export AGENT_VERBOSITY=verbose  # Include agent thoughts
export AGENT_VERBOSITY=debug    # All details

# Direct Python (without wrapper script)
source .venv/bin/activate
python agent_cli.py "Your task here"
```

See [UNIX_IO.md](UNIX_IO.md) for detailed I/O documentation.

### Interactive Mode

Start an interactive session with slash commands, command history, and more:

```bash
# Start interactive mode
./agent.sh -i
./agent.sh --interactive

# Or just run without arguments
./agent.sh
```

**Available Slash Commands:**

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/tools` | List available tools |
| `/run <cmd>` | Run a shell command and show output |
| `/clear` | Clear conversation history |
| `/undo` | Undo last file change |
| `/tokens` | Show token usage statistics |
| `/verbose [level]` | Set verbosity (quiet/normal/verbose/debug) |
| `/model [name]` | Show or change current model |
| `/status` | Show session status |
| `/history` | Show command history |
| `/quit`, `/exit` | Exit interactive mode |

**Features:**

- **Command History**: Use ↑/↓ arrows to navigate, Ctrl+R to search
- **Tab Completion**: Complete slash commands with Tab
- **Token Tracking**: See input/output token usage after each task
- **Undo Support**: Revert file changes made by the agent
- **Model Switching**: Change LLM model mid-session

**Example Session:**

```
╭─────────────────────────────────────────────────╮
│           Tiny Agent - Interactive Mode         │
│        Type /help for available commands        │
╰─────────────────────────────────────────────────╯
  Model: openai/gpt-4
  Tools: 6 loaded

tiny-agent> /tools
Available Tools:

  list_files
    List files in a directory
    Parameters: path
  ...

tiny-agent> Find all Python files in src/
🎯 Goal: Find all Python files in src/
🔧 Executing: find_files({'path': 'src', 'pattern': '*.py'})
📋 Result: src/main.py
src/utils.py
...

📊 Tokens: 1,234 (890 in / 344 out) | Calls: 2

tiny-agent> /undo
Undone: restored src/main.py to previous version

tiny-agent> /quit
Goodbye!
```

### HTTP API Usage

Run the agent as a web service:

```bash
# Start the server
python agent_api.py

# Make requests
curl -X POST http://localhost:5000/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "prompt": "List all Python files",
    "auto_respond": true
  }'
```

**Python client example:**

```python
import requests
import json

# Start agent task
response = requests.post(
    "http://localhost:5000/prompt",
    json={
        "session_id": "my-session",
        "prompt": "Find the largest Python file",
        "auto_respond": True
    },
    stream=True
)

# Handle streaming events
for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        event = json.loads(line[6:])

        if event['type'] == 'output':
            print(event['content'], end='')
        elif event['type'] == 'complete':
            print(f"\nResult: {event['content']}")
            break
        elif event['type'] == 'error':
            print(f"\nError: {event['content']}")
            break
```

**Interactive mode** (agent can ask follow-up questions):

```python
# Set auto_respond to False
response = requests.post(
    "http://localhost:5000/prompt",
    json={
        "session_id": "interactive",
        "prompt": "Analyze the codebase",
        "auto_respond": False
    },
    stream=True
)

for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        event = json.loads(line[6:])

        if event['type'] == 'question':
            # Agent is asking for input
            user_input = input(f"{event['content']}: ")

            # Send response
            requests.post(
                "http://localhost:5000/respond",
                json={
                    "session_id": "interactive",
                    "response": user_input
                }
            )
```

**API Endpoints:**

- `POST /prompt` - Start agent execution (returns SSE stream)
- `POST /respond` - Send response to waiting agent
- `GET /health` - Health check
- `GET /sessions` - List active sessions

### Programmatic Usage

Use the core agent directly in your Python code:

```python
from agent_core import agent_loop, AgentConfig, AgentCallbacks
from pathlib import Path

# Configure the agent
config = AgentConfig(
    llm_provider="openai",
    llm_model="gpt-4",
    max_iterations=10,
    command_timeout=30
)

# Define custom callbacks
def on_thinking(content: str):
    print(f"Agent is thinking: {content}")

def on_tool_call(name: str, args: dict):
    print(f"Executing tool: {name}({args})")

def on_need_input(question: str) -> str:
    return input(f"{question}: ")

callbacks = AgentCallbacks(
    on_thinking=on_thinking,
    on_tool_call=on_tool_call,
    on_need_input=on_need_input
)

# Run the agent
result = agent_loop(
    goal="Find all Python files",
    agent_dir=Path.home() / ".agent",
    config=config,
    callbacks=callbacks
)

print(f"Result: {result}")
```

## 🔧 Commands and Tools

Tools are defined in `commands.json` using JSON schema:

```json
{
  "name": "glob",
  "description": "Find files matching a pattern",
  "command": "find . -name '{pattern}' -type f",
  "parameters": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
        "description": "Glob pattern to match files"
      }
    },
    "required": ["pattern"]
  }
}
```

**Key features:**

- JSON Schema validation
- Parameter type checking
- Shell injection protection
- Path traversal prevention
- Timeout enforcement

**Creating custom tools:**

```json
{
  "name": "count_lines",
  "description": "Count lines in a file",
  "command": "wc -l {filepath}",
  "parameters": {
    "type": "object",
    "properties": {
      "filepath": {
        "type": "string",
        "description": "Path to the file"
      }
    },
    "required": ["filepath"]
  }
}
```

## 📚 Templates and Examples

### Templates

Pre-built tool collections for specific use cases:

```text
templates/
├── basic/              # File operations, text processing, system info
├── development/        # Git, Python, Docker tools
├── data/               # JSON, CSV, API tools
└── devops/             # Logging, monitoring tools
```

**Using templates:**

```bash
# Use a single template
cp templates/development/git-tools.json commands.json
./agent.sh "Show me recent commit history"

# Combine multiple templates
jq -s 'add' \
  templates/basic/file-operations.json \
  templates/development/python-tools.json \
  > commands.json
```

See [templates/README.md](templates/README.md) for all available templates.

### Examples

Complete, ready-to-use configurations:

```text
examples/
├── analyze-codebase/   # Code analysis tools
├── log-analysis/       # Log file analysis
├── data-processing/    # CSV/JSON processing
└── devops-tasks/       # DevOps automation
```

**Using examples:**

```bash
# Copy example configuration
cp examples/analyze-codebase/commands.json commands.json

# Run with example
./agent.sh "Analyze this Python project"
```

See [examples/README.md](examples/README.md) for detailed documentation.

## ⚙️ Configuration

Configuration via environment variables:

```bash
# LLM Provider (required)
OPENAI_API_KEY=sk-your-key        # For OpenAI
ANTHROPIC_API_KEY=sk-ant-your-key # For Anthropic

# LLM Settings
LLM_PROVIDER=openai        # openai or anthropic
LLM_MODEL=gpt-4            # Model to use

# Agent Behavior
MAX_ITERATIONS=10          # Max agent loop iterations
COMMAND_TIMEOUT=30         # Timeout for commands (seconds)
MAX_RETRIES=3              # LLM call retries
MAX_OUTPUT_SIZE=5000       # Output truncation size

# Logging
LOG_LEVEL=WARNING          # DEBUG, INFO, WARNING, ERROR
AGENT_VERBOSITY=normal     # quiet, normal, verbose, debug
```

**Verbosity levels:**
- `quiet` - Only critical errors
- `normal` - Key actions and results (default)
- `verbose` - Include agent thoughts
- `debug` - All logs and details

**Note:** stdout always contains only the final result, regardless of verbosity. Progress goes to stderr.

## 🔄 Unix-Style I/O

Tiny Agent follows Unix philosophy:

- **Results** → stdout
- **Progress** → stderr

This enables powerful composition:

```bash
# Save result to file (see progress on screen)
./agent.sh "Get AI news" > news.txt

# Pipe result to another command
./agent.sh "List Python files" | grep "test"
./agent.sh "Get TODO comments" | wc -l

# Silent operation (result only)
result=$(./agent.sh "Calculate total" 2>/dev/null)

# Separate result and logs
./agent.sh "Analyze code" > result.txt 2> log.txt

# Chain with Unix tools
./agent.sh "Get stats" | jq '.count' | bc
```

See [UNIX_IO.md](UNIX_IO.md) for detailed documentation and examples.

## 🔒 Security

### Docker Sandbox

- Runs as non-root user (UID 1000)
- Isolated filesystem (only /workspace accessible)
- No persistent state between runs
- Limited to safe CLI tools
- Can't modify agent code from within container

### Agent Security

- Input validation against parameter schemas
- Path traversal protection
- Shell injection prevention with `shlex.quote`
- Command timeout enforcement
- Output size limits
- Explicit `shell=False` in subprocess calls

### Best Practices

- Always use Docker sandbox for untrusted tasks
- Review commands.json before use
- Set appropriate timeout values
- Monitor agent logs
- Use minimal tool sets (principle of least privilege)

## 🛠 Development

### Project Structure

```text
tiny-agent/
├── agent_core.py          # Core agent logic (~380 lines)
├── agent_cli.py           # CLI wrapper (~180 lines)
├── agent_api.py           # HTTP API (~330 lines)
├── version.py             # Version information
├── commands.json          # Default tool definitions
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Package configuration
│
├── templates/             # 50+ reusable tool templates
│   ├── basic/
│   ├── development/
│   ├── data/
│   └── devops/
│
├── examples/              # 4 complete use cases
│   ├── analyze-codebase/
│   ├── log-analysis/
│   ├── data-processing/
│   └── devops-tasks/
│
├── .claude/
│   ├── commands/          # Custom slash commands
│   │   └── release-github.md
│   └── reports/           # Refactoring reports
│
├── Dockerfile             # Docker sandbox
├── docker-compose.yml     # Docker Compose config
├── setup.sh               # Automated setup script
├── agent.sh               # Unified runner (local/sandbox)
├── CHANGELOG.md           # Version history
└── README.md              # This file
```

### Running Tests

```bash
# Run agent tests
./agent.sh "List all files in the current directory"
./agent.sh "Find all Python files"

# Run API tests
python agent_api.py &  # Start server
python test_agent_api.py

# Run in Docker
docker build -t tiny-agent:latest .
docker run --rm \
  -v $(pwd)/workspace:/workspace \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  tiny-agent:latest \
  "List files"
```

### Building Docker Image

```bash
# Build
docker build -t tiny-agent:latest .

# Run
docker run --rm -it \
  -v $(pwd)/workspace:/workspace \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  tiny-agent:latest \
  "Your task here"

# Shell into container
docker run --rm -it \
  -v $(pwd)/workspace:/workspace \
  tiny-agent:latest \
  /bin/bash
```

### Creating a Release

Use the `/release-github` command in Claude Code for guided release process:

- Version bumping
- CHANGELOG.md updates
- Git tagging
- GitHub release creation

See [.claude/commands/release-github.md](.claude/commands/release-github.md) for details.

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[UNIX_IO.md](UNIX_IO.md)** - Detailed I/O documentation and examples
- **[templates/README.md](templates/README.md)** - Template documentation
- **[examples/README.md](examples/README.md)** - Example use cases
- **[.claude/reports/](.claude/reports/)** - Refactoring and implementation reports

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. Additional templates for specific domains
2. More complete examples
3. Support for additional LLM providers
4. Test coverage
5. Documentation improvements

**Process:**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- OpenAI API / Anthropic API for LLM capabilities
- Docker for sandboxed execution
- Flask for HTTP API
- Python standard library for core functionality

## 📊 Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

**Current version:** 0.3.0

```bash
# Check version
python version.py
```

---

**Keep the core minimal, extend with templates and examples.** 🎯

For questions or issues, please open an issue on GitHub.
