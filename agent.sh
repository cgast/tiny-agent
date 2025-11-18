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

# Usage
usage() {
    echo -e "${BLUE}Usage: $0 [OPTIONS] '<task>'${NC}"
    echo ""
    echo "Options:"
    echo "  -m, --mode <local|sandbox>   Execution mode (default: local)"
    echo "  -w, --workspace <path>       Workspace directory (default: .)"
    echo "  -h, --help                   Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 'Find all Python files'"
    echo "  $0 --mode sandbox 'Count lines of code'"
    echo "  $0 -m sandbox -w ./myproject 'Analyze this code'"
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -w|--workspace)
            WORKSPACE="$2"
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

# Validate task
if [ -z "$TASK" ]; then
    echo -e "${RED}Error: No task provided${NC}"
    usage
fi

# Validate mode
if [ "$MODE" != "local" ] && [ "$MODE" != "sandbox" ]; then
    echo -e "${RED}Error: Invalid mode '$MODE'. Use 'local' or 'sandbox'${NC}"
    exit 1
fi

# Run local
if [ "$MODE" = "local" ]; then
    echo -e "${GREEN}🚀 Running locally...${NC}"

    # Check venv
    if [ ! -d .venv ]; then
        echo -e "${YELLOW}⚠️  No .venv found. Run ./setup.sh first${NC}"
        exit 1
    fi

    # Check .env
    if [ ! -f .env ]; then
        echo -e "${RED}Error: .env not found. Run ./setup.sh${NC}"
        exit 1
    fi

    # Load env and run
    set -a
    source .env
    set +a
    source .venv/bin/activate

    echo -e "${BLUE}🎯 Task: $TASK${NC}"
    echo ""
    python3 agent.py "$TASK"

# Run in Docker sandbox
elif [ "$MODE" = "sandbox" ]; then
    echo -e "${GREEN}🚀 Running in Docker sandbox...${NC}"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker not installed${NC}"
        exit 1
    fi

    # Validate workspace
    if [ ! -d "$WORKSPACE" ]; then
        echo -e "${RED}Error: Workspace '$WORKSPACE' not found${NC}"
        exit 1
    fi

    WORKSPACE_ABS=$(cd "$WORKSPACE" && pwd)

    # Build if needed
    if [[ "$(docker images -q cli-agent:latest 2> /dev/null)" == "" ]]; then
        echo -e "${GREEN}📦 Building Docker image...${NC}"
        docker build -t cli-agent:latest .
    fi

    # Load .env if exists
    if [ -f .env ]; then
        set -a
        source .env
        set +a
    fi

    echo -e "${BLUE}📁 Workspace: $WORKSPACE_ABS${NC}"
    echo -e "${BLUE}🎯 Task: $TASK${NC}"
    echo ""

    # Run
    docker run --rm -it \
        -v "$WORKSPACE_ABS:/workspace:rw" \
        -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
        -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
        -e LLM_PROVIDER="${LLM_PROVIDER}" \
        -e LLM_MODEL="${LLM_MODEL}" \
        -e LOG_LEVEL="${LOG_LEVEL}" \
        cli-agent:latest \
        "$TASK"
fi
