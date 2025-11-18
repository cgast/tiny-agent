#!/usr/bin/env python3
"""Minimal CLI Agent - executes tasks using command-line tools"""

import os
import json
import subprocess
import sys
import time
import logging
import shlex
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, environment variables must be set manually
    pass

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
def load_config() -> dict:
    """Load configuration from environment variables (set in .env file)"""
    return {
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "llm_model": os.getenv("LLM_MODEL", "gpt-4"),
        "max_iterations": int(os.getenv("MAX_ITERATIONS", "10")),
        "command_timeout": int(os.getenv("COMMAND_TIMEOUT", "30")),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "max_output_size": int(os.getenv("MAX_OUTPUT_SIZE", "5000")),
    }

CONFIG = load_config()

# Simple LLM interface (use any LLM)
def call_llm(messages: list[dict], tools: list[dict], retry_count: int = 0) -> Optional[dict]:
    """Call LLM with messages and available tools. Returns response with potential tool_calls."""
    max_retries = CONFIG.get("max_retries", 3)

    try:
        if CONFIG["llm_provider"] == "openai":
            import openai

            # Validate API key
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable not set")

            logger.debug(f"Calling OpenAI API with model {CONFIG['llm_model']}")
            response = openai.chat.completions.create(
                model=CONFIG["llm_model"],
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            return response.choices[0].message

        elif CONFIG["llm_provider"] == "anthropic":
            import anthropic

            # Validate API key
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

            logger.debug(f"Calling Anthropic API with model {CONFIG['llm_model']}")
            # Note: Anthropic API differs - this is simplified
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=CONFIG.get("llm_model", "claude-3-opus-20240229"),
                messages=messages,
                tools=tools,
                max_tokens=2000
            )

            return response
        else:
            raise ValueError(f"Unsupported LLM provider: {CONFIG['llm_provider']}")

    except Exception as e:
        logger.error(f"LLM call failed (attempt {retry_count + 1}/{max_retries}): {e}")

        # Retry with exponential backoff
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # 1s, 2s, 4s
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            return call_llm(messages, tools, retry_count + 1)
        else:
            logger.error("Max retries reached, giving up")
            raise


def load_commands(agent_dir: Path) -> list[dict]:
    """Load available CLI commands from .agent directory"""
    commands_file = agent_dir / "commands.json"
    if not commands_file.exists():
        return []
    
    with open(commands_file) as f:
        commands = json.load(f)
    
    # Convert to OpenAI tool format
    tools = []
    for cmd in commands:
        tools.append({
            "type": "function",
            "function": {
                "name": cmd["name"],
                "description": cmd["description"],
                "parameters": cmd.get("parameters", {"type": "object", "properties": {}})
            }
        })
    
    return tools, commands


def validate_arguments(cmd_config: dict, args: dict) -> tuple[bool, str]:
    """Validate command arguments against parameter schema"""
    parameters = cmd_config.get("parameters", {})
    required = parameters.get("required", [])

    # Check required parameters
    for param in required:
        if param not in args or args[param] == "":
            return False, f"Missing required parameter: {param}"

    # Basic path traversal check
    for key, value in args.items():
        if isinstance(value, str):
            # Check for path traversal attempts
            if ".." in value or value.startswith("/"):
                logger.warning(f"Potential path traversal detected in {key}: {value}")
                # Allow absolute paths for workspace, but log them
                if not value.startswith("/workspace"):
                    return False, f"Invalid path in {key}: {value}"

    return True, ""

def execute_command(cmd_config: dict, args: dict) -> str:
    """Execute a CLI command with given arguments"""
    # Validate arguments
    valid, error_msg = validate_arguments(cmd_config, args)
    if not valid:
        logger.error(f"Argument validation failed: {error_msg}")
        return f"Validation error: {error_msg}"

    # Build command from template
    cmd_template = cmd_config["command"]
    logger.debug(f"Executing command template: {cmd_template}")

    # Simple substitution
    cmd_parts = cmd_template.split()
    cmd = []
    for part in cmd_parts:
        if part.startswith("{") and part.endswith("}"):
            arg_name = part[1:-1]
            arg_value = str(args.get(arg_name, ""))
            # Use shlex.quote for safe argument handling
            cmd.append(shlex.quote(arg_value) if arg_value else "")
        else:
            cmd.append(part)

    try:
        timeout = CONFIG.get("command_timeout", 30)
        logger.debug(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False  # Explicitly disable shell for security
        )

        # Limit output size
        max_size = CONFIG.get("max_output_size", 5000)
        output = result.stdout if result.returncode == 0 else result.stderr

        if len(output) > max_size:
            logger.warning(f"Output truncated from {len(output)} to {max_size} chars")
            output = output[:max_size] + f"\n... (truncated {len(output) - max_size} chars)"

        if result.returncode == 0:
            logger.debug(f"Command succeeded, output length: {len(output)}")
            return output
        else:
            logger.warning(f"Command failed with code {result.returncode}")
            return f"Error (exit code {result.returncode}): {output}"

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds")
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError as e:
        logger.error(f"Command not found: {e}")
        return f"Error: Command not found - {str(e)}"
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return f"Error executing command: {str(e)}"


def ask_user(question: str) -> str:
    """Ask user a question and get response"""
    print(f"\n🤖 Agent: {question}")
    print("Your response (or /quit to exit, /done to finish): ", end="")
    response = input().strip()
    return response


def agent_loop(goal: str, agent_dir: Path):
    """Main agent loop"""
    max_iterations = CONFIG.get("max_iterations", 10)
    logger.info(f"Starting agent loop with max {max_iterations} iterations")

    tools, commands = load_commands(agent_dir)
    cmd_map = {cmd["name"]: cmd for cmd in commands}

    logger.info(f"Loaded {len(commands)} commands")

    messages = [
        {"role": "system", "content": "You are a helpful assistant that can execute CLI commands and ask the user questions when needed. Break down tasks and execute them step by step."},
        {"role": "user", "content": goal}
    ]

    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")
        logger.debug(f"Iteration {iteration + 1}/{max_iterations}")

        try:
            # Call LLM
            response = call_llm(messages, tools)

            if response is None:
                logger.error("LLM returned None, aborting")
                return "Error: LLM call failed after retries"

            # Add to messages
            messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": response.tool_calls if hasattr(response, 'tool_calls') else None
            })

            # If no tool calls, check if agent wants to ask user something or is done
            if not response.tool_calls:
                if response.content:
                    print(f"\n🤖 Agent: {response.content}")

                    # Check if asking a question
                    if "?" in response.content:
                        user_response = ask_user("Please respond:")

                        if user_response == "/quit":
                            logger.info("User quit")
                            return "User quit"
                        elif user_response == "/done":
                            logger.info("User marked as done")
                            return response.content

                        messages.append({"role": "user", "content": user_response})
                        continue

                # Task complete
                logger.info("Task completed successfully")
                return response.content

            # Execute tool calls
            for tool_call in response.tool_calls:
                function_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse arguments: {e}")
                    result = f"Error: Invalid JSON arguments - {str(e)}"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result
                    })
                    continue

                print(f"🔧 Executing: {function_name}({arguments})")
                logger.info(f"Executing tool: {function_name}")

                # Execute CLI command
                if function_name in cmd_map:
                    result = execute_command(cmd_map[function_name], arguments)
                    # Show truncated result in console
                    display_result = result[:200] + "..." if len(result) > 200 else result
                    print(f"📋 Result: {display_result}")
                else:
                    logger.warning(f"Unknown command requested: {function_name}")
                    result = f"Unknown command: {function_name}"

                # Add result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": result
                })

        except KeyboardInterrupt:
            logger.info("User interrupted execution")
            return "User interrupted"
        except Exception as e:
            logger.error(f"Unexpected error in iteration {iteration + 1}: {e}")
            return f"Error: {str(e)}"

    logger.warning(f"Max iterations ({max_iterations}) reached")
    return f"Max iterations ({max_iterations}) reached"


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        print("Minimal CLI Agent - Execute tasks using command-line tools")
        print()
        print("Usage: agent.py '<task>'")
        print()
        print("Examples:")
        print("  agent.py 'Find all Python files in current directory'")
        print("  agent.py 'Count lines of code in all .py files'")
        print("  agent.py 'Search for TODO comments'")
        print()
        print("The agent will:")
        print("  - Break down your task into steps")
        print("  - Execute CLI commands to accomplish the task")
        print("  - Loop until the goal is fulfilled")
        print("  - Ask you questions if needed")
        print()
        print("User commands during execution:")
        print("  /quit - Stop the agent")
        print("  /done - Mark task as complete")
        print()
        print("Configuration:")
        print(f"  LLM Provider: {CONFIG['llm_provider']}")
        print(f"  LLM Model: {CONFIG['llm_model']}")
        print(f"  Max Iterations: {CONFIG['max_iterations']}")
        sys.exit(0 if len(sys.argv) > 1 else 1)

    # Validate API key for configured provider
    provider = CONFIG["llm_provider"]
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set it in your .env file or environment")
        sys.exit(1)
    elif provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it in your .env file or environment")
        sys.exit(1)

    goal = sys.argv[1]
    agent_dir = Path.home() / ".agent"

    if not agent_dir.exists():
        logger.error(f"Agent directory not found at {agent_dir}")
        print(f"❌ Error: Agent directory not found at {agent_dir}")
        print("Create it with commands.json")
        sys.exit(1)

    logger.info(f"Starting agent with goal: {goal}")
    print(f"🎯 Goal: {goal}")

    try:
        result = agent_loop(goal, agent_dir)
        print(f"\n✅ Final result:\n{result}")
    except KeyboardInterrupt:
        logger.info("Agent interrupted by user")
        print("\n\n⚠️  Agent interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Agent failed with error: {e}", exc_info=True)
        print(f"\n\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
