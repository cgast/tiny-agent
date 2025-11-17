#!/usr/bin/env python3
"""Minimal CLI Agent - executes tasks using command-line tools"""

import os
import json
import subprocess
import sys
from pathlib import Path

# Simple LLM interface (use any LLM)
def call_llm(messages: list[dict], tools: list[dict]) -> dict:
    """Call LLM with messages and available tools. Returns response with potential tool_calls."""
    # This is a placeholder - replace with actual LLM call (OpenAI, Anthropic, etc.)
    import openai
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    return response.choices[0].message


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


def execute_command(cmd_config: dict, args: dict) -> str:
    """Execute a CLI command with given arguments"""
    # Build command from template
    cmd_template = cmd_config["command"]
    
    # Simple substitution
    cmd_parts = cmd_template.split()
    cmd = []
    for part in cmd_parts:
        if part.startswith("{") and part.endswith("}"):
            arg_name = part[1:-1]
            cmd.append(str(args.get(arg_name, "")))
        else:
            cmd.append(part)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def ask_user(question: str) -> str:
    """Ask user a question and get response"""
    print(f"\n🤖 Agent: {question}")
    print("Your response (or /quit to exit, /done to finish): ", end="")
    response = input().strip()
    return response


def agent_loop(goal: str, agent_dir: Path, max_iterations: int = 10):
    """Main agent loop"""
    tools, commands = load_commands(agent_dir)
    cmd_map = {cmd["name"]: cmd for cmd in commands}
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can execute CLI commands and ask the user questions when needed. Break down tasks and execute them step by step."},
        {"role": "user", "content": goal}
    ]
    
    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")
        
        # Call LLM
        response = call_llm(messages, tools)
        
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
                        return "User quit"
                    elif user_response == "/done":
                        return response.content
                    
                    messages.append({"role": "user", "content": user_response})
                    continue
            
            # Task complete
            return response.content
        
        # Execute tool calls
        for tool_call in response.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"🔧 Executing: {function_name}({arguments})")
            
            # Execute CLI command
            if function_name in cmd_map:
                result = execute_command(cmd_map[function_name], arguments)
                print(f"📋 Result: {result[:200]}...")
            else:
                result = f"Unknown command: {function_name}"
            
            # Add result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": result
            })
    
    return "Max iterations reached"


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
        sys.exit(0 if len(sys.argv) > 1 else 1)
    
    goal = sys.argv[1]
    agent_dir = Path.home() / ".agent"
    
    if not agent_dir.exists():
        print(f"Error: Agent directory not found at {agent_dir}")
        print("Create it with commands.json")
        sys.exit(1)
    
    print(f"🎯 Goal: {goal}")
    result = agent_loop(goal, agent_dir)
    print(f"\n✅ Final result:\n{result}")


if __name__ == "__main__":
    main()
