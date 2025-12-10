#!/usr/bin/env python3
"""
Core agent logic - pure agentic loop without I/O dependencies.

This module contains only the reasoning, planning, and tool execution logic.
It has no direct dependencies on stdin/stdout/stderr or HTTP.
"""

import os
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

logger = logging.getLogger(__name__)


class AgentConfig:
    """Agent configuration"""

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        max_iterations: int = 10,
        command_timeout: int = 30,
        max_retries: int = 3,
        max_output_size: int = 5000,
        auto_detect_cli: bool = False,
        cli_allowlist: Optional[List[str]] = None,
        cli_blocklist: Optional[List[str]] = None,
    ):
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.max_iterations = max_iterations
        self.command_timeout = command_timeout
        self.max_retries = max_retries
        self.max_output_size = max_output_size
        self.auto_detect_cli = auto_detect_cli
        self.cli_allowlist = cli_allowlist
        self.cli_blocklist = cli_blocklist

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables"""
        from cli_commands import parse_command_list

        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4"),
            max_iterations=int(os.getenv("MAX_ITERATIONS", "10")),
            command_timeout=int(os.getenv("COMMAND_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            max_output_size=int(os.getenv("MAX_OUTPUT_SIZE", "5000")),
            auto_detect_cli=os.getenv("AUTO_DETECT_CLI", "").lower() in ("true", "1", "yes"),
            cli_allowlist=parse_command_list(os.getenv("CLI_ALLOWLIST")),
            cli_blocklist=parse_command_list(os.getenv("CLI_BLOCKLIST")),
        )


class AgentCallbacks:
    """Callbacks for agent events - allows different I/O implementations"""

    def __init__(
        self,
        on_iteration: Optional[Callable[[int, int], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
        on_tool_result: Optional[Callable[[str], None]] = None,
        on_need_input: Optional[Callable[[str], str]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_token_usage: Optional[Callable[[int, int], None]] = None,
    ):
        """
        Initialize callbacks for agent events.

        Args:
            on_iteration: Called at start of each iteration (current, max)
            on_thinking: Called when agent is thinking (content)
            on_tool_call: Called before executing tool (name, args)
            on_tool_result: Called after tool execution (result)
            on_need_input: Called when agent needs user input (question) -> response
            on_error: Called when an error occurs (error_msg)
            on_token_usage: Called with token counts (input_tokens, output_tokens)
        """
        self.on_iteration = on_iteration or (lambda i, m: None)
        self.on_thinking = on_thinking or (lambda c: None)
        self.on_tool_call = on_tool_call or (lambda n, a: None)
        self.on_tool_result = on_tool_result or (lambda r: None)
        self.on_need_input = on_need_input or (lambda q: "/quit")
        self.on_error = on_error or (lambda e: None)
        self.on_token_usage = on_token_usage or (lambda i, o: None)


class LLMResponse:
    """Wrapper for LLM response with token usage"""

    def __init__(self, message: Any, input_tokens: int = 0, output_tokens: int = 0):
        self.message = message
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

        # Proxy common attributes from the message
        self.content = getattr(message, 'content', None)
        self.tool_calls = getattr(message, 'tool_calls', None)


def call_llm(
    messages: List[Dict],
    tools: List[Dict],
    config: AgentConfig,
    retry_count: int = 0,
) -> Optional[LLMResponse]:
    """Call LLM with messages and available tools. Returns LLMResponse with token usage."""
    try:
        if config.llm_provider == "openai":
            import openai

            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable not set")

            logger.debug(f"Calling OpenAI API with model {config.llm_model}")
            response = openai.chat.completions.create(
                model=config.llm_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )

            # Extract token usage
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0

            return LLMResponse(response.choices[0].message, input_tokens, output_tokens)

        elif config.llm_provider == "anthropic":
            import anthropic

            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

            logger.debug(f"Calling Anthropic API with model {config.llm_model}")
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=config.llm_model, messages=messages, tools=tools, max_tokens=2000
            )

            # Extract token usage from Anthropic response
            usage = response.usage
            input_tokens = usage.input_tokens if usage else 0
            output_tokens = usage.output_tokens if usage else 0

            return LLMResponse(response, input_tokens, output_tokens)

        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")

    except Exception as e:
        logger.error(f"LLM call failed (attempt {retry_count + 1}/{config.max_retries}): {e}")

        if retry_count < config.max_retries:
            wait_time = 2**retry_count
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            return call_llm(messages, tools, config, retry_count + 1)
        else:
            logger.error("Max retries reached, giving up")
            raise


def load_commands(agent_dir: Path, config: Optional[AgentConfig] = None) -> tuple[List[Dict], List[Dict]]:
    """
    Load available CLI commands from .agent directory and optionally auto-detect CLI tools.

    Args:
        agent_dir: Directory containing commands.json
        config: Agent configuration (for auto-detect settings)

    Returns:
        Tuple of (tools, commands) where tools is OpenAI format and commands is raw config
    """
    tools = []
    commands = []

    # Load auto-detected CLI tools first (if enabled)
    if config and config.auto_detect_cli:
        from cli_commands import generate_cli_tools

        cli_tools, cli_commands = generate_cli_tools(
            allowlist=config.cli_allowlist,
            blocklist=config.cli_blocklist,
        )
        tools.extend(cli_tools)
        commands.extend(cli_commands)
        logger.info(f"Auto-detected {len(cli_commands)} CLI commands")

    # Load manual commands from commands.json (these take precedence)
    commands_file = agent_dir / "commands.json"
    if commands_file.exists():
        with open(commands_file) as f:
            manual_commands = json.load(f)

        # Track names to avoid duplicates (manual commands override auto-detected)
        manual_names = {cmd["name"] for cmd in manual_commands}

        # Remove auto-detected commands that have manual overrides
        if config and config.auto_detect_cli:
            tools = [t for t in tools if t["function"]["name"] not in manual_names]
            commands = [c for c in commands if c["name"] not in manual_names]

        # Add manual commands
        for cmd in manual_commands:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": cmd["name"],
                        "description": cmd["description"],
                        "parameters": cmd.get("parameters", {"type": "object", "properties": {}}),
                    },
                }
            )
            commands.append(cmd)

        logger.info(f"Loaded {len(manual_commands)} manual commands from commands.json")

    return tools, commands


def validate_arguments(cmd_config: Dict, args: Dict, config: AgentConfig) -> tuple[bool, str]:
    """Validate command arguments against parameter schema"""
    parameters = cmd_config.get("parameters", {})
    required = parameters.get("required", [])

    # Check required parameters
    for param in required:
        if param not in args or args[param] == "":
            return False, f"Missing required parameter: {param}"

    # Basic path traversal check
    in_docker = os.path.exists("/.dockerenv")
    for key, value in args.items():
        if isinstance(value, str):
            # Check for path traversal attempts
            if ".." in value:
                logger.warning(f"Path traversal attempt detected in {key}: {value}")
                return False, f"Invalid path in {key}: path traversal not allowed"

            # In Docker, restrict to /workspace only
            if in_docker and value.startswith("/") and not value.startswith("/workspace"):
                logger.warning(f"Outside workspace access in {key}: {value}")
                return False, f"Invalid path in {key}: must be within /workspace"

    return True, ""


def execute_command(cmd_config: Dict, args: Dict, config: AgentConfig) -> str:
    """Execute a CLI command with given arguments"""
    # Validate arguments
    valid, error_msg = validate_arguments(cmd_config, args, config)
    if not valid:
        logger.error(f"Argument validation failed: {error_msg}")
        return f"Validation error: {error_msg}"

    # Build command from template
    cmd_template = cmd_config["command"]
    logger.debug(f"Executing command template: {cmd_template}")

    # Simple substitution - build command as a list for subprocess
    cmd_parts = cmd_template.split()
    cmd = []
    for part in cmd_parts:
        if part.startswith("{") and part.endswith("}"):
            arg_name = part[1:-1]
            arg_value = str(args.get(arg_name, ""))
            if arg_value:
                cmd.append(arg_value)
        else:
            cmd.append(part)

    try:
        logger.debug(f"Running: {cmd}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=config.command_timeout, shell=False
        )

        # Limit output size
        output = result.stdout if result.returncode == 0 else result.stderr

        if len(output) > config.max_output_size:
            logger.warning(
                f"Output truncated from {len(output)} to {config.max_output_size} chars"
            )
            output = (
                output[: config.max_output_size]
                + f"\n... (truncated {len(output) - config.max_output_size} chars)"
            )

        if result.returncode == 0:
            logger.debug(f"Command succeeded, output length: {len(output)}")
            return output
        else:
            logger.warning(f"Command failed with code {result.returncode}")
            return f"Error (exit code {result.returncode}): {output}"

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {config.command_timeout} seconds")
        return f"Error: Command timed out after {config.command_timeout} seconds"
    except FileNotFoundError as e:
        logger.error(f"Command not found: {e}")
        return f"Error: Command not found - {str(e)}"
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return f"Error executing command: {str(e)}"


def assess_completion(messages: List[Dict], goal: str, tools: List[Dict], config: AgentConfig) -> Dict:
    """Ask the LLM to assess if the goal is complete and what to do next"""
    assessment_messages = messages + [
        {
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

IMPORTANT: If status is 'complete', you MUST include a 'result' field with the actual final answer/output.""",
        }
    ]

    try:
        response = call_llm(assessment_messages, [], config)
        if response and response.content:
            content = response.content.strip()
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
    except Exception as e:
        logger.error(f"Assessment failed: {e}")
        return {
            "status": "continue",
            "reasoning": "Assessment failed, continuing with task",
            "next_action": "Continue working on the goal",
        }

    return {
        "status": "continue",
        "reasoning": "No clear assessment, continuing",
        "next_action": "Continue working on the goal",
    }


def agent_loop(
    goal: str,
    agent_dir: Path,
    config: Optional[AgentConfig] = None,
    callbacks: Optional[AgentCallbacks] = None,
) -> str:
    """
    Main autonomous agent loop - pure logic without I/O dependencies.

    Args:
        goal: The task/goal for the agent to accomplish
        agent_dir: Directory containing commands.json
        config: Agent configuration (uses defaults if None)
        callbacks: Callbacks for events (uses no-op defaults if None)

    Returns:
        Final result string
    """
    config = config or AgentConfig.from_env()
    callbacks = callbacks or AgentCallbacks()

    logger.info(f"Starting agent loop with max {config.max_iterations} iterations")

    tools, commands = load_commands(agent_dir, config)
    cmd_map = {cmd["name"]: cmd for cmd in commands}

    logger.info(f"Loaded {len(commands)} commands")

    # System prompt
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
- If data is already available in the conversation, work with it directly""",
        },
        {"role": "user", "content": goal},
    ]

    iteration = 0
    while iteration < config.max_iterations:
        iteration += 1
        callbacks.on_iteration(iteration, config.max_iterations)
        logger.debug(f"Iteration {iteration}/{config.max_iterations}")

        try:
            # Call LLM
            response = call_llm(messages, tools, config)

            if response is None:
                logger.error("LLM returned None, aborting")
                return "Error: LLM call failed after retries"

            # Report token usage
            callbacks.on_token_usage(response.input_tokens, response.output_tokens)

            # Add to messages
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": response.tool_calls if hasattr(response, "tool_calls") else None,
                }
            )

            # Display agent's thinking
            if response.content:
                callbacks.on_thinking(response.content)

            # If no tool calls, assess what to do next
            if not response.tool_calls:
                logger.info("No tool calls, assessing completion")
                assessment = assess_completion(messages, goal, tools, config)

                callbacks.on_thinking(f"Assessment: {assessment['reasoning']}")

                if assessment["status"] == "complete":
                    logger.info("Task completed successfully")
                    return assessment.get("result", assessment["reasoning"])

                elif assessment["status"] == "need_input":
                    # Agent needs user input
                    user_response = callbacks.on_need_input(
                        assessment.get("question", "Please provide more information:")
                    )

                    if user_response == "/quit":
                        logger.info("User quit")
                        return "User quit"

                    messages.append({"role": "user", "content": user_response})
                    continue

                elif assessment["status"] == "continue":
                    # Agent knows what to do next
                    logger.info(f"Continuing: {assessment.get('next_action', 'Working on goal')}")
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Continue with: {assessment.get('next_action', 'Continue working on the goal')}",
                        }
                    )
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
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": result,
                            }
                        )
                        continue

                    callbacks.on_tool_call(function_name, arguments)
                    logger.info(f"Executing tool: {function_name}")

                    # Execute CLI command
                    if function_name in cmd_map:
                        result = execute_command(cmd_map[function_name], arguments, config)
                        callbacks.on_tool_result(result)
                    else:
                        logger.warning(f"Unknown command requested: {function_name}")
                        result = f"Unknown command: {function_name}"
                        callbacks.on_error(result)

                    # Add result to messages
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": result,
                        }
                    )

        except KeyboardInterrupt:
            logger.info("User interrupted execution")
            return "User interrupted"
        except Exception as e:
            logger.error(f"Unexpected error in iteration {iteration}: {e}")
            callbacks.on_error(str(e))
            return f"Error: {str(e)}"

    logger.warning(f"Max iterations ({config.max_iterations}) reached")
    return f"⚠️  Max iterations ({config.max_iterations}) reached. Task may be incomplete."
