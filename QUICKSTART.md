# 🤖 CLI Agent - Quick Start Guide

## What You Have

A minimal (~150 lines) CLI agent that:
- ✅ Executes tasks by breaking them down into steps
- ✅ Uses command-line tools (ls, grep, find, etc.)
- ✅ Loops until goal is fulfilled
- ✅ Can ask you questions interactively
- ✅ Runs in isolated Docker sandbox

## Files Included

```
agent.py              - Main agent (~150 lines)
commands.json         - CLI tool definitions
Dockerfile            - Sandbox environment
docker-compose.yml    - Docker compose config
run-agent.sh          - Easy run wrapper
setup.sh              - Initial setup script
Makefile              - Make commands
env.example           - Rename to .env, add API key
dockerignore          - Rename to .dockerignore
README.md             - Full documentation
```

## Setup (2 minutes)

```bash
# 1. Initial setup
chmod +x setup.sh run-agent.sh
./setup.sh

# 2. Add your API key
cp env.example .env
nano .env  # Add OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Rename dockerignore
mv dockerignore .dockerignore

# 4. Build Docker image
make build
# OR: docker build -t cli-agent:latest .
```

## Usage

### Option 1: Make commands (easiest)
```bash
make run TASK='Find all Python files'
make run TASK='Count lines of code' DIR=./my-project
make shell  # Open shell in container
```

### Option 2: Run script
```bash
./run-agent.sh "Find all Python files"
./run-agent.sh "Search for TODO comments" ./my-project
```

### Option 3: Docker directly
```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -e OPENAI_API_KEY="your-key" \
  cli-agent:latest \
  "Your task here"
```

## Example Tasks

```bash
# File operations
make run TASK='List all Python files and their sizes'
make run TASK='Find files larger than 1MB'
make run TASK='Search for TODO comments in all code'

# Analysis
make run TASK='Count lines of code in all Python files'
make run TASK='What is the total disk usage?'
make run TASK='Find duplicate files'

# Interactive
make run TASK='Help me organize these files by type'
# Agent will ask you questions!
```

## How It Works

1. **You give a task**: `make run TASK='Find Python files'`
2. **Agent breaks it down**: Plans steps to accomplish goal
3. **Executes CLI commands**: Uses tools from commands.json
4. **Loops until done**: Keeps going until goal is met
5. **Can ask questions**: Interactive when it needs input

## Security Features

- Runs as non-root user in container
- Only workspace directory is accessible
- Can't modify agent code from inside
- No persistent state between runs
- Limited to safe CLI tools

## Customizing Tools

Edit `commands.json` to add new CLI tools:

```json
{
  "name": "your_command",
  "description": "What it does",
  "command": "bash_command {arg1} {arg2}",
  "parameters": {
    "type": "object",
    "properties": {
      "arg1": {"type": "string", "description": "..."}
    },
    "required": ["arg1"]
  }
}
```

Rebuild: `make build`

## Using Different LLMs

Edit `agent.py` and replace `call_llm()` function:

**OpenAI** (default):
```python
import openai
response = openai.chat.completions.create(...)
```

**Anthropic**:
```python
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(...)
```

**Ollama** (local):
```python
import requests
response = requests.post('http://localhost:11434/api/chat', ...)
```

## Troubleshooting

**"Docker not found"**: Install Docker Desktop
**"Permission denied"**: Run `chmod +x *.sh`
**"API key error"**: Check `.env` file has correct key
**"Command not found"**: Add tool to `commands.json`

## User Commands During Execution

- `/quit` - Stop the agent immediately
- `/done` - Mark current task as complete

## What's Next?

1. Try the example tasks above
2. Point it at your own projects
3. Add custom CLI tools in commands.json
4. Experiment with different LLMs
5. Create specialized agent configurations

## Architecture

```
User → run-agent.sh → Docker Container
                       ├── agent.py (orchestration)
                       ├── LLM (planning & decisions)
                       └── CLI tools (execution)
                       └── /workspace (your files)
```

Minimal, focused, sandboxed. 🎯
