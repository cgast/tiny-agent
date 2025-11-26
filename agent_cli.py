#!/usr/bin/env python3
"""
CLI wrapper for the agent - handles stdin/stdout/stderr interaction.

This is a thin wrapper around agent_core.py that provides the CLI interface.
Supports both single-task mode and interactive mode with slash commands.
"""

import os
import sys
import json
import logging
import readline
import atexit
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from agent_core import AgentConfig, AgentCallbacks, agent_loop, load_commands

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


# =============================================================================
# Token Usage Tracking
# =============================================================================

class TokenTracker:
    """Track token usage across LLM calls"""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.session_calls = 0

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Record token usage from an LLM call"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.session_calls += 1

    def get_summary(self) -> str:
        """Get a summary of token usage"""
        total = self.total_input_tokens + self.total_output_tokens
        return f"Tokens: {total:,} ({self.total_input_tokens:,} in / {self.total_output_tokens:,} out) | Calls: {self.session_calls}"

    def reset(self):
        """Reset token counters"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.session_calls = 0


# =============================================================================
# Undo System - Track File Changes
# =============================================================================

class FileChange:
    """Represents a file change that can be undone"""

    def __init__(self, path: str, original_content: Optional[str], action: str):
        self.path = path
        self.original_content = original_content  # None if file didn't exist
        self.action = action  # 'created', 'modified', 'deleted'
        self.timestamp = datetime.now()


class UndoManager:
    """Manage file changes for undo capability"""

    def __init__(self):
        self.changes: List[FileChange] = []
        self.watching = False

    def start_watching(self, paths: List[str]):
        """Start watching files for changes - snapshot current state"""
        self.pending_snapshots: Dict[str, Optional[str]] = {}
        for path in paths:
            p = Path(path)
            if p.exists() and p.is_file():
                try:
                    self.pending_snapshots[path] = p.read_text()
                except Exception:
                    self.pending_snapshots[path] = None
            else:
                self.pending_snapshots[path] = None
        self.watching = True

    def stop_watching(self):
        """Stop watching and record any changes"""
        if not self.watching:
            return

        for path, original in self.pending_snapshots.items():
            p = Path(path)
            current_exists = p.exists() and p.is_file()

            try:
                current_content = p.read_text() if current_exists else None
            except Exception:
                current_content = None

            if original is None and current_content is not None:
                # File was created
                self.changes.append(FileChange(path, None, 'created'))
            elif original is not None and current_content is None:
                # File was deleted
                self.changes.append(FileChange(path, original, 'deleted'))
            elif original != current_content:
                # File was modified
                self.changes.append(FileChange(path, original, 'modified'))

        self.watching = False
        self.pending_snapshots = {}

    def can_undo(self) -> bool:
        """Check if there are changes to undo"""
        return len(self.changes) > 0

    def undo_last(self) -> str:
        """Undo the last file change"""
        if not self.changes:
            return "Nothing to undo"

        change = self.changes.pop()
        p = Path(change.path)

        try:
            if change.action == 'created':
                # Remove the created file
                if p.exists():
                    p.unlink()
                return f"Undone: removed created file {change.path}"

            elif change.action == 'deleted':
                # Restore the deleted file
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(change.original_content)
                return f"Undone: restored deleted file {change.path}"

            elif change.action == 'modified':
                # Restore original content
                p.write_text(change.original_content)
                return f"Undone: restored {change.path} to previous version"

        except Exception as e:
            return f"Failed to undo: {e}"

        return "Unknown change type"

    def get_pending_changes(self) -> List[str]:
        """Get list of pending undoable changes"""
        return [f"{c.action}: {c.path}" for c in self.changes]

    def clear(self):
        """Clear all change history"""
        self.changes = []


# =============================================================================
# Readline Setup - History and Completion
# =============================================================================

def setup_readline(history_file: Path):
    """Configure readline for command history and completion"""

    # Set up history file
    history_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    # Set history length
    readline.set_history_length(1000)

    # Save history on exit
    atexit.register(readline.write_history_file, history_file)

    # Configure readline behavior
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('set editing-mode emacs')


class SlashCommandCompleter:
    """Tab completion for slash commands"""

    COMMANDS = [
        '/help', '/tools', '/run', '/clear', '/undo', '/quit', '/exit',
        '/verbose', '/model', '/tokens', '/history', '/status'
    ]

    def __init__(self, tools: List[str] = None):
        self.tools = tools or []

    def complete(self, text: str, state: int) -> Optional[str]:
        """Readline completion function"""
        if text.startswith('/'):
            # Complete slash commands
            matches = [cmd for cmd in self.COMMANDS if cmd.startswith(text)]
        else:
            matches = []

        try:
            return matches[state]
        except IndexError:
            return None


# =============================================================================
# Interactive Session with Slash Commands
# =============================================================================

class InteractiveSession:
    """Interactive REPL session with slash commands"""

    def __init__(self, agent_dir: Path, config: AgentConfig):
        self.agent_dir = agent_dir
        self.config = config
        self.token_tracker = TokenTracker()
        self.undo_manager = UndoManager()
        self.conversation_history: List[Dict] = []
        self.running = True

        # Load tools for display
        self.tools, self.commands = load_commands(agent_dir)

        # Setup readline
        history_file = Path.home() / ".tiny-agent" / "history"
        setup_readline(history_file)

        # Setup tab completion
        completer = SlashCommandCompleter([cmd['name'] for cmd in self.commands])
        readline.set_completer(completer.complete)

    def print_banner(self):
        """Print welcome banner"""
        print("╭─────────────────────────────────────────────────╮", file=sys.stderr)
        print("│           Tiny Agent - Interactive Mode         │", file=sys.stderr)
        print("│        Type /help for available commands        │", file=sys.stderr)
        print("╰─────────────────────────────────────────────────╯", file=sys.stderr)
        print(f"  Model: {self.config.llm_provider}/{self.config.llm_model}", file=sys.stderr)
        print(f"  Tools: {len(self.commands)} loaded", file=sys.stderr)
        print(file=sys.stderr)

    def cmd_help(self, args: str) -> str:
        """Show help for slash commands"""
        return """
Available Commands:
  /help              Show this help message
  /tools             List available tools
  /run <cmd>         Run a shell command and show output
  /clear             Clear conversation history
  /undo              Undo last file change
  /tokens            Show token usage statistics
  /verbose [level]   Set verbosity (quiet/normal/verbose/debug)
  /model [name]      Show or change current model
  /status            Show session status
  /history           Show command history
  /quit, /exit       Exit interactive mode

Tips:
  • Use ↑/↓ arrows to navigate command history
  • Use Ctrl+R to search history
  • Tab completes slash commands
  • Enter a task description to run the agent
"""

    def cmd_tools(self, args: str) -> str:
        """List available tools"""
        if not self.commands:
            return "No tools loaded. Check commands.json"

        lines = ["Available Tools:", ""]
        for cmd in self.commands:
            params = cmd.get('parameters', {}).get('properties', {})
            param_str = ', '.join(params.keys()) if params else 'none'
            lines.append(f"  {cmd['name']}")
            lines.append(f"    {cmd['description']}")
            lines.append(f"    Parameters: {param_str}")
            lines.append("")

        return '\n'.join(lines)

    def cmd_run(self, args: str) -> str:
        """Run a shell command and show output"""
        import subprocess

        if not args:
            return "Usage: /run <command>\nExample: /run ls -la"

        try:
            result = subprocess.run(
                args,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            if not output:
                output = "(no output)"

            # Truncate if too long
            if len(output) > 2000:
                output = output[:2000] + "\n... (truncated)"

            status = "✓" if result.returncode == 0 else f"✗ (exit {result.returncode})"
            return f"{status} {args}\n{output}"

        except subprocess.TimeoutExpired:
            return f"✗ Command timed out after 30s: {args}"
        except Exception as e:
            return f"✗ Error running command: {e}"

    def cmd_clear(self, args: str) -> str:
        """Clear conversation history"""
        self.conversation_history = []
        return "Conversation history cleared"

    def cmd_undo(self, args: str) -> str:
        """Undo last file change"""
        if not self.undo_manager.can_undo():
            return "Nothing to undo"
        return self.undo_manager.undo_last()

    def cmd_tokens(self, args: str) -> str:
        """Show token usage statistics"""
        return self.token_tracker.get_summary()

    def cmd_verbose(self, args: str) -> str:
        """Set or show verbosity level"""
        global VERBOSITY
        levels = ['quiet', 'normal', 'verbose', 'debug']

        if not args:
            return f"Current verbosity: {VERBOSITY}"

        if args in levels:
            VERBOSITY = args
            return f"Verbosity set to: {VERBOSITY}"
        else:
            return f"Invalid level. Choose from: {', '.join(levels)}"

    def cmd_model(self, args: str) -> str:
        """Show or change model"""
        if not args:
            return f"Current model: {self.config.llm_provider}/{self.config.llm_model}"

        # Parse provider/model or just model
        if '/' in args:
            provider, model = args.split('/', 1)
            self.config.llm_provider = provider
            self.config.llm_model = model
        else:
            self.config.llm_model = args

        return f"Model changed to: {self.config.llm_provider}/{self.config.llm_model}"

    def cmd_status(self, args: str) -> str:
        """Show session status"""
        changes = self.undo_manager.get_pending_changes()
        changes_str = '\n    '.join(changes) if changes else 'none'

        return f"""
Session Status:
  Model: {self.config.llm_provider}/{self.config.llm_model}
  {self.token_tracker.get_summary()}
  History: {len(self.conversation_history)} messages
  Undoable changes: {len(self.undo_manager.changes)}
    {changes_str}
  Verbosity: {VERBOSITY}
  Working directory: {os.getcwd()}
"""

    def cmd_history(self, args: str) -> str:
        """Show command history"""
        history_len = readline.get_current_history_length()
        lines = ["Recent Commands:", ""]

        start = max(1, history_len - 20)
        for i in range(start, history_len + 1):
            item = readline.get_history_item(i)
            if item:
                lines.append(f"  {i}: {item}")

        return '\n'.join(lines)

    def cmd_quit(self, args: str) -> str:
        """Exit interactive mode"""
        self.running = False
        return "Goodbye!"

    def handle_slash_command(self, user_input: str) -> Optional[str]:
        """Parse and execute slash command, return result or None if not a command"""
        if not user_input.startswith('/'):
            return None

        parts = user_input[1:].split(None, 1)
        cmd_name = parts[0].lower() if parts else ''
        cmd_args = parts[1] if len(parts) > 1 else ''

        commands = {
            'help': self.cmd_help,
            'tools': self.cmd_tools,
            'run': self.cmd_run,
            'clear': self.cmd_clear,
            'undo': self.cmd_undo,
            'tokens': self.cmd_tokens,
            'verbose': self.cmd_verbose,
            'model': self.cmd_model,
            'status': self.cmd_status,
            'history': self.cmd_history,
            'quit': self.cmd_quit,
            'exit': self.cmd_quit,
        }

        if cmd_name in commands:
            return commands[cmd_name](cmd_args)
        else:
            return f"Unknown command: /{cmd_name}. Type /help for available commands."

    def run_task(self, goal: str):
        """Run the agent on a task"""
        print_normal(f"🎯 Goal: {goal}")

        # Track files that might be modified
        # For simplicity, watch common files in current directory
        watched_files = []
        for pattern in ['*.py', '*.json', '*.txt', '*.md', '*.yaml', '*.yml']:
            watched_files.extend([str(p) for p in Path('.').glob(pattern)])
        self.undo_manager.start_watching(watched_files)

        # Create callbacks with token tracking
        callbacks = create_cli_callbacks_with_tracking(self.token_tracker)

        try:
            result = agent_loop(goal, self.agent_dir, self.config, callbacks)

            # Show result
            print_result(result)

            # Show token usage
            print_normal(f"\n📊 {self.token_tracker.get_summary()}")

        except KeyboardInterrupt:
            print("\n⚠️  Task interrupted", file=sys.stderr)
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
        finally:
            self.undo_manager.stop_watching()

    def run(self):
        """Main interactive loop"""
        self.print_banner()

        while self.running:
            try:
                user_input = input("tiny-agent> ").strip()

                if not user_input:
                    continue

                # Check for slash command
                result = self.handle_slash_command(user_input)
                if result is not None:
                    print(result, file=sys.stderr)
                    continue

                # Otherwise, treat as a task
                self.run_task(user_input)

            except EOFError:
                print("\nGoodbye!", file=sys.stderr)
                break
            except KeyboardInterrupt:
                print("\nUse /quit to exit", file=sys.stderr)
                continue


def create_cli_callbacks_with_tracking(token_tracker: TokenTracker) -> AgentCallbacks:
    """Create callbacks that track token usage"""
    base_callbacks = create_cli_callbacks()

    def on_token_usage(input_tokens: int, output_tokens: int):
        """Track token usage from LLM calls"""
        token_tracker.add_usage(input_tokens, output_tokens)

    return AgentCallbacks(
        on_iteration=base_callbacks.on_iteration,
        on_thinking=base_callbacks.on_thinking,
        on_tool_call=base_callbacks.on_tool_call,
        on_tool_result=base_callbacks.on_tool_result,
        on_need_input=base_callbacks.on_need_input,
        on_error=base_callbacks.on_error,
        on_token_usage=on_token_usage,
    )


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
    # Parse arguments
    interactive_mode = False
    goal = None

    args = sys.argv[1:]

    # Check for interactive flag
    if "--interactive" in args or "-i" in args:
        interactive_mode = True
        args = [a for a in args if a not in ["--interactive", "-i"]]

    # Check for help
    if "--help" in args or "-h" in args:
        print("Tiny Agent - Autonomous task execution using command-line tools", file=sys.stderr)
        print(file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  agent_cli.py '<task>'           Run a single task", file=sys.stderr)
        print("  agent_cli.py --interactive      Start interactive mode", file=sys.stderr)
        print("  agent_cli.py -i                 Start interactive mode (short)", file=sys.stderr)
        print(file=sys.stderr)
        print("Interactive Mode Commands:", file=sys.stderr)
        print("  /help              Show available commands", file=sys.stderr)
        print("  /tools             List available tools", file=sys.stderr)
        print("  /clear             Clear conversation history", file=sys.stderr)
        print("  /undo              Undo last file change", file=sys.stderr)
        print("  /tokens            Show token usage", file=sys.stderr)
        print("  /model [name]      Show or change model", file=sys.stderr)
        print("  /verbose [level]   Set verbosity level", file=sys.stderr)
        print("  /quit              Exit interactive mode", file=sys.stderr)
        print(file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  agent_cli.py 'Find all Python files'", file=sys.stderr)
        print("  agent_cli.py -i", file=sys.stderr)
        print(file=sys.stderr)

        config = AgentConfig.from_env()
        print("Current configuration:", file=sys.stderr)
        print(f"  LLM Provider: {config.llm_provider}", file=sys.stderr)
        print(f"  LLM Model: {config.llm_model}", file=sys.stderr)
        print(f"  Max Iterations: {config.max_iterations}", file=sys.stderr)
        print(f"  Verbosity: {VERBOSITY}", file=sys.stderr)
        sys.exit(0)

    # If no args, start interactive mode
    if not args:
        interactive_mode = True
    else:
        goal = args[0]

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

    # Find agent directory
    try:
        agent_dir = find_agent_dir()
    except RuntimeError as e:
        logger.error(str(e))
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    # Interactive mode
    if interactive_mode:
        try:
            session = InteractiveSession(agent_dir, config)
            session.run()
        except Exception as e:
            logger.error(f"Interactive session failed: {e}", exc_info=True)
            print(f"\n❌ Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
        return

    # Single task mode
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
