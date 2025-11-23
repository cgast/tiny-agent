#!/usr/bin/env python3
"""
CLI wrapper for the agent - handles stdin/stdout/stderr interaction.

This is a thin wrapper around agent_core.py that provides the CLI interface.
"""

import os
import sys
import logging
from pathlib import Path
from agent_core import AgentConfig, AgentCallbacks, agent_loop

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Verbosity configuration
VERBOSITY = os.getenv("AGENT_VERBOSITY", "normal")  # quiet, normal, verbose, debug

# Configure logging level based on verbosity
verbosity_to_log_level = {
    "quiet": logging.ERROR,
    "normal": logging.WARNING,
    "verbose": logging.INFO,
    "debug": logging.DEBUG,
}
logger.setLevel(verbosity_to_log_level.get(VERBOSITY, logging.INFO))


# Output helpers following Unix conventions
# Informational output → stderr, results → stdout
def print_normal(msg: str):
    """Print to stderr in normal, verbose, debug modes"""
    if VERBOSITY in ["normal", "verbose", "debug"]:
        print(msg, file=sys.stderr)


def print_verbose(msg: str):
    """Print to stderr in verbose and debug modes"""
    if VERBOSITY in ["verbose", "debug"]:
        print(msg, file=sys.stderr)


def print_debug(msg: str):
    """Print to stderr only in debug mode"""
    if VERBOSITY == "debug":
        print(msg, file=sys.stderr)


def print_result(msg: str):
    """Print final result to stdout (for piping/redirection)"""
    print(msg, file=sys.stdout)


def create_cli_callbacks() -> AgentCallbacks:
    """Create callbacks that use CLI I/O (stdin/stdout/stderr)"""

    def on_iteration(current: int, max_iterations: int):
        """Print iteration info"""
        print_debug(f"\n--- Iteration {current}/{max_iterations} ---")

    def on_thinking(content: str):
        """Print agent's thinking"""
        print_verbose(f"\n💭 Agent: {content}")

    def on_tool_call(name: str, args: dict):
        """Print tool execution"""
        print_normal(f"🔧 Executing: {name}({args})")

    def on_tool_result(result: str):
        """Print tool result (truncated)"""
        display_result = result[:200] + "..." if len(result) > 200 else result
        print_normal(f"📋 Result: {display_result}")

    def on_need_input(question: str) -> str:
        """Ask user for input via CLI"""
        print(f"\n❓ Agent needs input: {question}", file=sys.stderr)
        print("Your response (or /quit to exit): ", end="", file=sys.stderr)
        try:
            response = input().strip()
            return response
        except (EOFError, KeyboardInterrupt):
            logger.warning("Cannot get user input or user interrupted")
            return "/quit"

    def on_error(error: str):
        """Print error"""
        print_normal(f"❌ Error: {error}")

    return AgentCallbacks(
        on_iteration=on_iteration,
        on_thinking=on_thinking,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
        on_need_input=on_need_input,
        on_error=on_error,
    )


def find_agent_dir() -> Path:
    """Find the agent directory containing commands.json"""
    current_dir = Path.cwd()
    if (current_dir / "commands.json").exists():
        return current_dir
    elif (Path.home() / ".agent").exists():
        return Path.home() / ".agent"
    else:
        raise RuntimeError(
            "commands.json not found in current directory or ~/.agent\n"
            "Run from project directory or create ~/.agent/commands.json"
        )


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        # Help goes to stderr (standard for Unix tools)
        print("Minimal CLI Agent - Autonomous task execution using command-line tools", file=sys.stderr)
        print(file=sys.stderr)
        print("NOTE: This is typically called via ./agent.sh wrapper script.", file=sys.stderr)
        print("      For full usage information, run: ./agent.sh --help", file=sys.stderr)
        print(file=sys.stderr)
        print("Direct usage: agent_cli.py '<task>'", file=sys.stderr)
        print(file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  agent_cli.py 'Find all Python files in current directory'", file=sys.stderr)
        print("  agent_cli.py 'Count lines of code in all .py files'", file=sys.stderr)
        print(file=sys.stderr)

        # Load config to show current settings
        config = AgentConfig.from_env()
        print("Current configuration:", file=sys.stderr)
        print(f"  LLM Provider: {config.llm_provider}", file=sys.stderr)
        print(f"  LLM Model: {config.llm_model}", file=sys.stderr)
        print(f"  Max Iterations: {config.max_iterations}", file=sys.stderr)
        print(f"  Verbosity: {VERBOSITY}", file=sys.stderr)
        sys.exit(0 if len(sys.argv) > 1 else 1)

    # Load configuration
    config = AgentConfig.from_env()

    # Validate API key for configured provider
    if config.llm_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        print("❌ Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        print("Please set it in your .env file or environment", file=sys.stderr)
        sys.exit(1)
    elif config.llm_provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("Please set it in your .env file or environment", file=sys.stderr)
        sys.exit(1)

    goal = sys.argv[1]

    # Find agent directory
    try:
        agent_dir = find_agent_dir()
    except RuntimeError as e:
        logger.error(str(e))
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    logger.info(f"Starting agent with goal: {goal}")
    print_normal(f"🎯 Goal: {goal}")

    # Create CLI callbacks
    callbacks = create_cli_callbacks()

    # Run agent
    try:
        result = agent_loop(goal, agent_dir, config, callbacks)

        # Output final result to stdout (clean, pipeable)
        print_result(result)

    except KeyboardInterrupt:
        logger.info("Agent interrupted by user")
        print("\n\n⚠️  Agent interrupted by user", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        logger.error(f"Agent failed with error: {e}", exc_info=True)
        print(f"\n\n❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
