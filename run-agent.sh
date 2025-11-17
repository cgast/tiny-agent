#!/bin/bash
# Wrapper script to run CLI agent in Docker sandbox

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if task is provided
if [ $# -eq 0 ]; then
    echo -e "${BLUE}Usage: $0 '<task>' [workspace-dir]${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 'Find all Python files'"
    echo "  $0 'Count lines of code' ./my-project"
    echo ""
    echo "The agent runs in a Docker sandbox with mounted workspace."
    exit 1
fi

TASK="$1"
WORKSPACE="${2:-.}"  # Default to current directory

# Check if workspace exists
if [ ! -d "$WORKSPACE" ]; then
    echo -e "${RED}Error: Workspace directory '$WORKSPACE' does not exist${NC}"
    exit 1
fi

# Get absolute path
WORKSPACE_ABS=$(cd "$WORKSPACE" && pwd)

echo -e "${GREEN}🚀 Starting CLI Agent in sandbox...${NC}"
echo -e "${BLUE}📁 Workspace: $WORKSPACE_ABS${NC}"
echo -e "${BLUE}🎯 Task: $TASK${NC}"
echo ""

# Build image if it doesn't exist
if [[ "$(docker images -q cli-agent:latest 2> /dev/null)" == "" ]]; then
    echo -e "${GREEN}📦 Building Docker image...${NC}"
    docker build -t cli-agent:latest .
fi

# Run agent in container
docker run --rm -it \
    -v "$WORKSPACE_ABS:/workspace:rw" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
    cli-agent:latest \
    "$TASK"
