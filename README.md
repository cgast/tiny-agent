# Minimal CLI Agent

A minimal (~380 lines) agent that executes tasks using command-line tools, can break down tasks, loops until goal is fulfilled, and can interact with the user.

**Runs in a Docker sandbox** for security and isolation.

## ⭐ Key Features

- ✅ **Minimal Core**: ~380 lines of clean, readable Python code
- ✅ **Extensible**: 50+ tools in templates, 4 complete examples
- ✅ **Secure**: Sandboxed Docker execution, input validation, path traversal protection
- ✅ **Robust**: Retry logic with exponential backoff, timeout handling, comprehensive error handling
- ✅ **Configurable**: Environment variables and config.yaml support
- ✅ **Observable**: Structured logging with configurable levels
- ✅ **LLM Agnostic**: OpenAI, Anthropic, or bring your own
- ✅ **MIT Licensed**: Free to use and modify

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone and setup
git clone <repo-url>
cd tiny-agent

# 2. Setup environment
cp env.example .env
nano .env  # Add your OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Build and run
chmod +x run-agent.sh
docker build -t cli-agent:latest .
./run-agent.sh "Find all Python files"
```

### Using Make

```bash
make setup  # Initial setup
make build  # Build Docker image
make run TASK='Find all Python files'
```

## 📁 Project Structure

```
tiny-agent/
├── agent.py                 # Core agent (~380 lines)
├── commands.json            # Default tool definitions
├── config.yaml.example      # Configuration template
├── env.example              # Environment variables template
│
├── templates/               # ⭐ 50+ reusable tool templates
│   ├── basic/              # File operations, text processing, system info
│   ├── development/        # Git, Python, Docker tools
│   ├── data/               # JSON, CSV, API tools
│   ├── devops/             # Logging, monitoring tools
│   └── README.md           # Template documentation
│
├── examples/                # ⭐ 4 complete use cases
│   ├── analyze-codebase/   # Code analysis
│   ├── log-analysis/       # Log file analysis
│   ├── data-processing/    # CSV/JSON processing
│   ├── devops-tasks/       # DevOps automation
│   └── README.md           # Examples documentation
│
├── Dockerfile               # Docker sandbox
├── docker-compose.yml       # Docker Compose config
├── run-agent.sh             # Convenient wrapper script
├── Makefile                 # Make commands
└── README.md                # This file
```

## 🎯 Usage Examples

### Basic Tasks

```bash
# File operations
./run-agent.sh "Find all Python files"
./run-agent.sh "Count lines of code in all .py files"
./run-agent.sh "Search for TODO comments"

# Data analysis
./run-agent.sh "Summarize the sales.csv data"
./run-agent.sh "How many errors are in the logs?"

# Code analysis
./run-agent.sh "Analyze this codebase and give me a summary"
```

### Using Templates

Templates provide reusable tool sets for specific use cases:

```bash
# Use a specific template
cp templates/development/git-tools.json commands.json
docker build -t cli-agent:latest .
./run-agent.sh "Show me the recent commit history"

# Combine multiple templates
jq -s 'add' \
  templates/basic/file-operations.json \
  templates/development/python-tools.json \
  > commands.json
```

See [templates/README.md](templates/README.md) for all available templates.

### Using Examples

Examples provide complete, ready-to-use configurations:

```bash
# Use the code analysis example
cp examples/analyze-codebase/commands.json commands.json
docker build -t cli-agent:latest .
./run-agent.sh "Analyze this Python project"

# Use the log analysis example
cp examples/log-analysis/commands.json commands.json
docker build -t cli-agent:latest .
./run-agent.sh "Find all errors in the logs" ./logs
```

See [examples/README.md](examples/README.md) for all available examples.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp env.example .env
```

Required variables:
```bash
# Choose your LLM provider
OPENAI_API_KEY=sk-your-key        # For OpenAI
ANTHROPIC_API_KEY=sk-ant-your-key # For Anthropic
```

Optional configuration (override config.yaml):
```bash
LLM_PROVIDER=openai     # openai or anthropic
LLM_MODEL=gpt-4         # Model to use
MAX_ITERATIONS=10       # Max agent loop iterations
COMMAND_TIMEOUT=30      # Timeout for commands (seconds)
MAX_RETRIES=3           # LLM call retries
MAX_OUTPUT_SIZE=5000    # Output truncation size
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
```

### Configuration File

Copy and customize the config file:

```bash
cp config.yaml.example config.yaml
```

See [config.yaml.example](config.yaml.example) for all options.

## 🔧 Advanced Usage

### Custom Tool Development

Create your own tools in `commands.json`:

```json
{
  "name": "your_tool",
  "description": "What your tool does",
  "command": "bash_command {arg1} {arg2}",
  "parameters": {
    "type": "object",
    "properties": {
      "arg1": {
        "type": "string",
        "description": "Description for arg1"
      }
    },
    "required": ["arg1"]
  }
}
```

### Running Without Docker

```bash
# 1. Setup
mkdir -p ~/.agent
cp commands.json ~/.agent/
pip install openai  # or anthropic

# 2. Configure
export OPENAI_API_KEY="your-key"

# 3. Run
./agent.py "Your task here"
```

### Different LLM Providers

The agent supports multiple LLM providers:

**OpenAI (default):**
```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export OPENAI_API_KEY=your-key
```

**Anthropic:**
```bash
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3-opus-20240229
export ANTHROPIC_API_KEY=your-key
```

**Custom providers:** Edit the `call_llm()` function in `agent.py`.

## 🔒 Security Features

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

## 📊 Improvements Over Original

| Feature | Original | Enhanced |
|---------|----------|----------|
| Code Size | ~190 lines | ~380 lines (with features) |
| Error Handling | Basic | Comprehensive with retries |
| Validation | None | Full parameter validation |
| Security | Basic | Path traversal protection, input sanitization |
| Configuration | Hardcoded | Environment + config.yaml |
| Logging | print() only | Structured logging with levels |
| Templates | 5 tools | 50+ tools in templates |
| Examples | None | 4 complete examples |
| Documentation | Basic | Complete with guides |
| License | None | MIT License |

## 🛠️ Development

### Project Commands

```bash
make help     # Show all commands
make setup    # Initial project setup
make build    # Build Docker image
make run      # Run agent (set TASK)
make shell    # Open shell in container
make clean    # Clean up Docker image
make test     # Run test tasks
```

### Logging

Set log level for debugging:

```bash
export LOG_LEVEL=DEBUG
./run-agent.sh "Your task"
```

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`

## 📚 Documentation

- [Templates Guide](templates/README.md) - 50+ reusable tool templates
- [Examples Guide](examples/README.md) - 4 complete use cases
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [LICENSE](LICENSE) - MIT License

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. Additional templates for specific domains
2. More complete examples
3. Support for additional LLM providers
4. Test coverage
5. Documentation improvements

## 🐛 Troubleshooting

**"API key error"**
- Check `.env` file has the correct key
- Ensure key matches your LLM provider

**"Command not found"**
- Add the tool to `commands.json`
- Or use a template from `templates/`

**"Docker permission denied"**
- Run `chmod +x run-agent.sh`
- Check Docker is installed and running

**"Validation error: Invalid path"**
- Paths must be within `/workspace` in Docker
- Or use relative paths starting with `.`

**Agent loops forever**
- Increase `MAX_ITERATIONS` if needed
- Check if task is clearly defined
- Use `/quit` to stop manually

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- OpenAI API / Anthropic API for LLM capabilities
- Docker for sandboxed execution
- Python standard library for core functionality

---

**Keep the core minimal, extend with templates and examples.** 🎯
