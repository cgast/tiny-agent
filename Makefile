.PHONY: help setup build run clean test shell

# Default target
help:
	@echo "CLI Agent - Make Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup    - Initial setup (create .env, workspace)"
	@echo "  make build    - Build Docker image"
	@echo ""
	@echo "Run:"
	@echo "  make run      - Run agent (set TASK='your task')"
	@echo "  make shell    - Open shell in container"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean    - Remove Docker image and workspace"
	@echo "  make test     - Run test tasks"
	@echo ""
	@echo "Examples:"
	@echo "  make run TASK='Find all Python files'"
	@echo "  make run TASK='Count lines of code' DIR=./my-project"

setup:
	@./setup.sh

build:
	@echo "🔨 Building Docker image..."
	@docker build -t cli-agent:latest .
	@echo "✅ Build complete"

run:
	@if [ -z "$(TASK)" ]; then \
		echo "❌ Error: TASK not set"; \
		echo "Usage: make run TASK='your task' [DIR=./path]"; \
		exit 1; \
	fi
	@./run-agent.sh "$(TASK)" $(DIR)

shell:
	@echo "🐚 Opening shell in agent container..."
	@docker run --rm -it \
		-v $(PWD)/workspace:/workspace \
		-e OPENAI_API_KEY="$(OPENAI_API_KEY)" \
		-e ANTHROPIC_API_KEY="$(ANTHROPIC_API_KEY)" \
		cli-agent:latest \
		/bin/bash

clean:
	@echo "🧹 Cleaning up..."
	@docker rmi cli-agent:latest 2>/dev/null || true
	@rm -rf workspace/
	@echo "✅ Cleanup complete"

test:
	@echo "🧪 Running test tasks..."
	@echo ""
	@echo "Test 1: List files"
	@./run-agent.sh "List all files in the current directory"
	@echo ""
	@echo "Test 2: Find Python files"
	@./run-agent.sh "Find all Python files"
	@echo ""
	@echo "Test 3: Count files"
	@./run-agent.sh "How many files are in this directory?"
