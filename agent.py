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
        "verbosity": os.getenv("AGENT_VERBOSITY", "normal"),  # quiet, normal, verbose, debug
    }

CONFIG = load_config()

# Configure logging level based on verbosity
verbosity_to_log_level = {
    "quiet": logging.ERROR,
    "normal": logging.WARNING,
    "verbose": logging.INFO,
    "debug": logging.DEBUG,
}
logger.setLevel(verbosity_to_log_level.get(CONFIG["verbosity"], logging.INFO))

# Output helpers with verbosity control
# Following Unix conventions: informational output goes to stderr, results to stdout
def print_quiet(msg: str):
    """Always print to stderr (even in quiet mode) - for critical info"""
    print(msg, file=sys.stderr)

def print_normal(msg: str):
    """Print to stderr in normal, verbose, debug modes"""
    if CONFIG["verbosity"] in ["normal", "verbose", "debug"]:
        print(msg, file=sys.stderr)

def print_verbose(msg: str):
    """Print to stderr in verbose and debug modes"""
    if CONFIG["verbosity"] in ["verbose", "debug"]:
        print(msg, file=sys.stderr)

def print_debug(msg: str):
    """Print to stderr only in debug mode"""
    if CONFIG["verbosity"] == "debug":
        print(msg, file=sys.stderr)

def print_separator():
    """Print section separator to stderr (not in quiet mode)"""
    if CONFIG["verbosity"] != "quiet":
        print(file=sys.stderr)

def print_result(msg: str):
    """Print final result to stdout (for piping/redirection)"""
    print(msg, file=sys.stdout)

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
    print(f"\n❓ Agent needs input: {question}", file=sys.stderr)
    print("Your response (or /quit to exit): ", end="", file=sys.stderr)
    try:
        response = input().strip()
        return response
    except EOFError:
        # Non-interactive mode or stdin closed
        logger.warning("Cannot get user input in non-interactive mode")
        return "/quit"


def assess_completion(messages: list[dict], goal: str, tools: list[dict]) -> dict:
    """Ask the LLM to assess if the goal is complete and what to do next"""
    assessment_messages = messages + [{
        "role": "user",
        "content": f"""Assess the current state:

Original goal: {goal}

Based on the conversation so far, determine:
1. Is the goal fully accomplished? (yes/no/partially)
2. What is your assessment of the current state?
3. What should happen next?
   - If complete: respond with status 'complete'
   - If you know what to do next: respond with status 'continue' and describe the next action
   - If you need clarification: respond with status 'need_input' and provide a specific question

Respond in JSON format:
{{
    "status": "complete|continue|need_input",
    "reasoning": "explanation of current state",
    "result": "the final result/answer to present to the user (if complete)",
    "next_action": "what to do next (if continue)",
    "question": "question for user (if need_input)"
}}

IMPORTANT: If status is 'complete', you MUST include a 'result' field with the actual final answer/output.
For example, if asked to list AI news, include the actual list of news items with titles and links."""
    }]

    try:
        # Call without tools for assessment
        response = call_llm(assessment_messages, [])
        if response and response.content:
            # Try to parse JSON from response
            content = response.content.strip()
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
    except Exception as e:
        logger.error(f"Assessment failed: {e}")
        # Default to continue if assessment fails
        return {
            "status": "continue",
            "reasoning": "Assessment failed, continuing with task",
            "next_action": "Continue working on the goal"
        }

    return {
        "status": "continue",
        "reasoning": "No clear assessment, continuing",
        "next_action": "Continue working on the goal"
    }


def agent_loop(goal: str, agent_dir: Path):
    """Main autonomous agent loop"""
    max_iterations = CONFIG.get("max_iterations", 10)
    logger.info(f"Starting autonomous agent loop with max {max_iterations} iterations")

    tools, commands = load_commands(agent_dir)
    cmd_map = {cmd["name"]: cmd for cmd in commands}

    logger.info(f"Loaded {len(commands)} commands")

    # Enhanced system prompt for autonomous behavior
    messages = [
        {
            "role": "system",
            "content": """You are an autonomous agent that executes tasks using CLI commands.

Your workflow:
1. Assess the task and break it down into subtasks if needed
2. Execute actions autonomously using available tools
3. After each action, evaluate if the goal is accomplished
4. Only ask the user for input if you genuinely need clarification

Important:
- Work autonomously - don't ask permission for each step
- Use tools proactively to accomplish the goal
- Think step-by-step and execute methodically
- Only stop when the goal is fully accomplished or you need user input

CRITICAL - Working with data:
- When you receive data from a tool (HTML, text, JSON, etc.), ANALYZE it directly
- You can read, parse, search and extract information from text data without additional tools
- Don't claim you "can't parse" or "don't have capability" - you're an LLM with text processing abilities
- Only use tools when you need to FETCH new data or EXECUTE commands
- If data is already available in the conversation, work with it directly

Example: If you fetch HTML content, you CAN and SHOULD search it for keywords, extract links,
find patterns, etc. without needing additional parsing tools."""
        },
        {"role": "user", "content": goal}
    ]

    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        print_debug(f"\n--- Iteration {iteration} ---")
        logger.debug(f"Iteration {iteration}/{max_iterations}")

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

            # Display agent's thinking/response
            if response.content:
                print_verbose(f"\n💭 Agent: {response.content}")

            # If no tool calls, assess what to do next
            if not response.tool_calls:
                logger.info("No tool calls, assessing completion")
                assessment = assess_completion(messages, goal, tools)

                print_verbose(f"\n🔍 Assessment: {assessment['reasoning']}")

                if assessment['status'] == 'complete':
                    logger.info("Task completed successfully")
                    # Return the actual result, fallback to reasoning if no result provided
                    return assessment.get('result', assessment['reasoning'])

                elif assessment['status'] == 'need_input':
                    # Agent needs user input
                    user_response = ask_user(assessment.get('question', 'Please provide more information:'))

                    if user_response == "/quit":
                        logger.info("User quit")
                        return "User quit"

                    messages.append({"role": "user", "content": user_response})
                    continue

                elif assessment['status'] == 'continue':
                    # Agent knows what to do next, continue autonomously
                    logger.info(f"Continuing: {assessment.get('next_action', 'Working on goal')}")
                    print_normal(f"→ Next: {assessment.get('next_action', 'Continuing...')}")
                    # Add next action as user message to guide the agent
                    messages.append({
                        "role": "user",
                        "content": f"Continue with: {assessment.get('next_action', 'Continue working on the goal')}"
                    })
                    continue

            # Execute tool calls
            if response.tool_calls:
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

                    print_normal(f"🔧 Executing: {function_name}({arguments})")
                    logger.info(f"Executing tool: {function_name}")

                    # Execute CLI command
                    if function_name in cmd_map:
                        result = execute_command(cmd_map[function_name], arguments)
                        # Show truncated result in console
                        display_result = result[:200] + "..." if len(result) > 200 else result
                        print_normal(f"📋 Result: {display_result}")
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
            logger.error(f"Unexpected error in iteration {iteration}: {e}")
            return f"Error: {str(e)}"

    logger.warning(f"Max iterations ({max_iterations}) reached")
    return f"⚠️  Max iterations ({max_iterations}) reached. Task may be incomplete."


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        # Help goes to stderr (standard for Unix tools)
        print("Minimal CLI Agent - Autonomous task execution using command-line tools", file=sys.stderr)
        print(file=sys.stderr)
        print("Usage: agent.py '<task>'", file=sys.stderr)
        print(file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  agent.py 'Find all Python files in current directory'", file=sys.stderr)
        print("  agent.py 'Count lines of code in all .py files'", file=sys.stderr)
        print("  agent.py 'Search for TODO comments'", file=sys.stderr)
        print(file=sys.stderr)
        print("Unix-style I/O:", file=sys.stderr)
        print("  stdout - Final results (pipeable, redirectable)", file=sys.stderr)
        print("  stderr - Progress and informational messages", file=sys.stderr)
        print(file=sys.stderr)
        print("  Examples:", file=sys.stderr)
        print("    ./agent.sh 'Get AI news' > results.txt       # Save results", file=sys.stderr)
        print("    ./agent.sh 'Get AI news' 2>/dev/null         # Silence progress", file=sys.stderr)
        print("    ./agent.sh 'List files' | grep '.py'         # Pipe results", file=sys.stderr)
        print(file=sys.stderr)
        print("The agent will autonomously:", file=sys.stderr)
        print("  ✓ Assess and break down your task into subtasks", file=sys.stderr)
        print("  ✓ Execute CLI commands to accomplish the goal", file=sys.stderr)
        print("  ✓ Self-evaluate progress after each action", file=sys.stderr)
        print("  ✓ Decide when the task is complete", file=sys.stderr)
        print("  ✓ Only ask for input when genuinely needed", file=sys.stderr)
        print(file=sys.stderr)
        print("User commands (when prompted):", file=sys.stderr)
        print("  /quit - Stop the agent", file=sys.stderr)
        print(file=sys.stderr)
        print("Configuration:", file=sys.stderr)
        print(f"  LLM Provider: {CONFIG['llm_provider']}", file=sys.stderr)
        print(f"  LLM Model: {CONFIG['llm_model']}", file=sys.stderr)
        print(f"  Max Iterations: {CONFIG['max_iterations']}", file=sys.stderr)
        sys.exit(0 if len(sys.argv) > 1 else 1)

    # Validate API key for configured provider
    provider = CONFIG["llm_provider"]
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        print("❌ Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        print("Please set it in your .env file or environment", file=sys.stderr)
        sys.exit(1)
    elif provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("Please set it in your .env file or environment", file=sys.stderr)
        sys.exit(1)

    goal = sys.argv[1]

    # Check for commands.json in current directory first, then ~/.agent
    current_dir = Path.cwd()
    if (current_dir / "commands.json").exists():
        agent_dir = current_dir
    elif (Path.home() / ".agent").exists():
        agent_dir = Path.home() / ".agent"
    else:
        logger.error("commands.json not found in current directory or ~/.agent")
        print("❌ Error: commands.json not found", file=sys.stderr)
        print("Run from project directory or create ~/.agent/commands.json", file=sys.stderr)
        sys.exit(1)

    logger.info(f"Starting agent with goal: {goal}")
    print_normal(f"🎯 Goal: {goal}")

    try:
        result = agent_loop(goal, agent_dir)
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
