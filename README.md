# Minimal CLI Agent

A minimal agent that executes tasks using command-line tools, can break down tasks, loops until goal is fulfilled, and can interact with the user.

**Runs in a Docker sandbox** for security and isolation.

## Quick Start (Docker - Recommended)

1. **Setup:**
   ```bash
   # Copy .env.example to .env and add your API key
   cp .env.example .env
   nano .env  # Add your OPENAI_API_KEY or ANTHROPIC_API_KEY
   
   # Make run script executable
   chmod +x run-agent.sh
   ```

2. **Run:**
   ```bash
   # Run in current directory
   ./run-agent.sh "Find all Python files"
   
   # Run in specific directory
   ./run-agent.sh "Count lines of code" ./my-project
   ```

The agent runs in an isolated Docker container with your directory mounted as `/workspace`.

## Manual Docker Usage

```bash
# Build image
docker build -t cli-agent:latest .

# Run with current directory mounted
docker run --rm -it \
  -v $(pwd):/workspace \
  -e OPENAI_API_KEY="your-key" \
  cli-agent:latest \
  "Your task here"

# Or use docker-compose
docker-compose run agent "Your task here"
```

## Local Setup (Without Docker)

1. **Create agent directory:**
   ```bash
   mkdir -p ~/.agent
   cp commands.json ~/.agent/
   ```

2. **Configure LLM:**
   Edit `agent.py` and replace the `call_llm()` function with your LLM of choice:
   - OpenAI: `openai.chat.completions.create()`
   - Anthropic: `anthropic.messages.create()`
   - Local: ollama, llama.cpp, etc.

3. **Install dependencies:**
   ```bash
   pip install openai  # or anthropic, or whatever LLM client you use
   ```

4. **Run:**
   ```bash
   chmod +x agent.py
   ./agent.py "Find all Python files in the current directory"
   ```

## Structure

```
.
├── agent.py              # Main agent script
├── commands.json         # CLI tool definitions
├── Dockerfile            # Docker sandbox
├── docker-compose.yml    # Docker compose config
├── run-agent.sh          # Easy run script
├── .env.example          # API key template
├── .dockerignore         # Docker build exclusions
└── workspace/            # Your mounted directory (in container)
```

In container:
```
/home/agent/.agent/commands.json   # Available CLI tools
/workspace/                         # Your mounted directory
```

## Docker Security Features

- ✅ Runs as non-root user (UID 1000)
- ✅ Isolated filesystem (only workspace is accessible)
- ✅ No persistent state between runs
- ✅ Limited to basic CLI tools
- ✅ Can't modify agent code from within container

## Adding Commands

Edit `~/.agent/commands.json`:

```json
{
  "name": "your_command",
  "description": "What it does",
  "command": "bash_command {arg1} {arg2}",
  "parameters": {
    "type": "object",
    "properties": {
      "arg1": {"type": "string", "description": "..."},
      "arg2": {"type": "string", "description": "..."}
    },
    "required": ["arg1"]
  }
}
```

## Features

- ✅ Loops until task is complete
- ✅ Breaks down complex tasks
- ✅ Uses CLI commands as tools
- ✅ Interactive: can ask user questions
- ✅ User commands: `/quit`, `/done`
- ✅ ~100 lines of code

## Example Session

```
$ ./agent.py "Find large files over 1MB"

🎯 Goal: Find large files over 1MB

--- Iteration 1 ---
🔧 Executing: find_files({'path': '.', 'pattern': '*'})
📋 Result: ./file1.txt./file2.log...

--- Iteration 2 ---
🤖 Agent: I found 15 files. Should I filter by size now?
Your response: yes

--- Iteration 3 ---
🔧 Executing: get_disk_usage({'path': './file1.txt'})
...

✅ Final result:
Found 3 files over 1MB:
- file1.txt (2.3MB)
- file2.log (1.5MB)
- archive.zip (10MB)
```
