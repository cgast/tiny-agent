#!/usr/bin/env bash
# Unified agent runner - supports local and Docker execution

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Defaults
MODE="local"
WORKSPACE="."
VERBOSITY="normal"  # quiet, normal, verbose, debug
INTERACTIVE=false

# Usage
usage() {
    echo -e "${BLUE}Usage: $0 [OPTIONS] ['<task>']${NC}"
    echo ""
    echo "Options:"
    echo "  -i, --interactive            Start interactive mode with slash commands"
    echo "  -m, --mode <local|sandbox>   Execution mode (default: local)"
    echo "  -w, --workspace <path>       Workspace directory (default: .)"
    echo "  -v, --verbosity <level>      Output verbosity (default: normal)"
    echo "                               quiet   - Only final results"
    echo "                               normal  - Key actions and results"
    echo "                               verbose - Include agent thoughts"
    echo "                               debug   - All logs and details"
    echo "  -h, --help                   Show this help"
    echo ""
    echo "Interactive Mode Commands:"
    echo "  /help              Show available commands"
    echo "  /tools             List available tools"
    echo "  /clear             Clear conversation history"
    echo "  /undo              Undo last file change"
    echo "  /tokens            Show token usage"
    echo "  /model [name]      Show or change model"
    echo "  /verbose [level]   Set verbosity level"
    echo "  /status            Show session status"
    echo "  /quit              Exit interactive mode"
    echo ""
    echo "Examples:"
    echo "  $0 -i                                 Start interactive mode"
    echo "  $0 'Find all Python files'"
    echo "  $0 --mode sandbox 'Count lines of code'"
    echo "  $0 -m sandbox -w ./myproject 'Analyze this code'"
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -w|--workspace)
            WORKSPACE="$2"
            shift 2
            ;;
        -v|--verbosity)
            VERBOSITY="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            TASK="$1"
            shift
            ;;
    esac
done

# Validate: need either task or interactive mode
if [ -z "$TASK" ] && [ "$INTERACTIVE" = false ]; then
    # No task and not interactive - start interactive mode by default
    INTERACTIVE=true
fi

# Validate mode
if [ "$MODE" != "local" ] && [ "$MODE" != "sandbox" ]; then
    echo -e "${RED}Error: Invalid mode '$MODE'. Use 'local' or 'sandbox'${NC}" >&2
    exit 1
fi

# Validate verbosity
if [ "$VERBOSITY" != "quiet" ] && [ "$VERBOSITY" != "normal" ] && [ "$VERBOSITY" != "verbose" ] && [ "$VERBOSITY" != "debug" ]; then
    echo -e "${RED}Error: Invalid verbosity '$VERBOSITY'. Use 'quiet', 'normal', 'verbose', or 'debug'${NC}" >&2
    exit 1
fi

# Run local
if [ "$MODE" = "local" ]; then
    echo -e "${GREEN}🚀 Running locally...${NC}" >&2

    # Check venv
    if [ ! -d .venv ]; then
        echo -e "${YELLOW}⚠️  No .venv found. Run ./setup.sh first${NC}" >&2
        exit 1
    fi

    # Check .env
    if [ ! -f .env ]; then
        echo -e "${RED}Error: .env not found. Run ./setup.sh${NC}" >&2
        exit 1
    fi

    # Load env and run
    set -a
    source .env
    set +a
    source .venv/bin/activate

    if [ "$INTERACTIVE" = true ]; then
        echo "" >&2
        AGENT_VERBOSITY="$VERBOSITY" python3 agent_cli.py --interactive
    else
        echo -e "${BLUE}🎯 Task: $TASK${NC}" >&2
        echo "" >&2
        AGENT_VERBOSITY="$VERBOSITY" python3 agent_cli.py "$TASK"
    fi

# Run in Docker sandbox
elif [ "$MODE" = "sandbox" ]; then
    echo -e "${GREEN}🚀 Running in Docker sandbox...${NC}" >&2

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker not installed${NC}" >&2
        exit 1
    fi

    # Validate workspace
    if [ ! -d "$WORKSPACE" ]; then
        echo -e "${RED}Error: Workspace '$WORKSPACE' not found${NC}" >&2
        exit 1
    fi

    WORKSPACE_ABS=$(cd "$WORKSPACE" && pwd)

    # Build if needed
    if [[ "$(docker images -q cli-agent:latest 2> /dev/null)" == "" ]]; then
        echo -e "${GREEN}📦 Building Docker image...${NC}" >&2
        docker build -t cli-agent:latest . >&2
    fi

    # Load .env if exists
    if [ -f .env ]; then
        set -a
        source .env
        set +a
    fi

    echo -e "${BLUE}📁 Workspace: $WORKSPACE_ABS${NC}" >&2

    if [ "$INTERACTIVE" = true ]; then
        echo "" >&2
        docker run --rm -it \
            -v "$WORKSPACE_ABS:/workspace:rw" \
            -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
            -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
            -e LLM_PROVIDER="${LLM_PROVIDER}" \
            -e LLM_MODEL="${LLM_MODEL}" \
            -e LOG_LEVEL="${LOG_LEVEL}" \
            -e AGENT_VERBOSITY="${VERBOSITY}" \
            cli-agent:latest \
            --interactive
    else
        echo -e "${BLUE}🎯 Task: $TASK${NC}" >&2
        echo "" >&2
        docker run --rm -it \
            -v "$WORKSPACE_ABS:/workspace:rw" \
            -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
            -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
            -e LLM_PROVIDER="${LLM_PROVIDER}" \
            -e LLM_MODEL="${LLM_MODEL}" \
            -e LOG_LEVEL="${LOG_LEVEL}" \
            -e AGENT_VERBOSITY="${VERBOSITY}" \
            cli-agent:latest \
            "$TASK"
    fi
fi
