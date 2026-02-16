"""
Output formatting for tiny-agent.

Uses ASCII art (circles, lines, arrows) to show execution flow
and ANSI color codes to differentiate output types.

Color support is auto-detected from the terminal.
Disable with NO_COLOR=1, force with FORCE_COLOR=1.
"""

import os
import sys


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    if os.getenv("NO_COLOR"):
        return False
    if os.getenv("FORCE_COLOR"):
        return True
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()


# ---------------------------------------------------------------------------
# ANSI escape codes (empty strings when color is not supported)
# ---------------------------------------------------------------------------

_c = _supports_color()

RESET   = "\033[0m"   if _c else ""
BOLD    = "\033[1m"   if _c else ""
DIM     = "\033[2m"   if _c else ""
RED     = "\033[31m"  if _c else ""
GREEN   = "\033[32m"  if _c else ""
YELLOW  = "\033[33m"  if _c else ""
BLUE    = "\033[34m"  if _c else ""
MAGENTA = "\033[35m"  if _c else ""
CYAN    = "\033[36m"  if _c else ""


# ---------------------------------------------------------------------------
# Unicode flow symbols
# ---------------------------------------------------------------------------

SYM_GOAL     = "●"       # start / goal
SYM_DONE     = "✔"       # success / completion
SYM_ERROR    = "✖"       # error
SYM_WARN     = "⚠"       # warning
SYM_QUESTION = "?"       # needs user input
SYM_THINK    = "···"     # thinking / assessment
SYM_INFO     = "ℹ"       # informational
SYM_OK       = "✔"       # pass / success marker
SYM_FAIL     = "✖"       # fail marker

FLOW   = " │"            # vertical flow line
ARROW  = " ├╌╌"          # branch for tool calls
INDENT = " │   "         # indented result line


# ---------------------------------------------------------------------------
# Colored formatters (for terminal / stderr output)
# ---------------------------------------------------------------------------

def fmt_goal(text: str) -> str:
    return f"{CYAN}{BOLD}{SYM_GOAL} Goal:{RESET} {CYAN}{text}{RESET}"


def fmt_thinking(text: str) -> str:
    return f"{DIM}{FLOW}  {SYM_THINK} {text}{RESET}"


def fmt_tool_call(name: str, args) -> str:
    return f"{DIM}{ARROW}{RESET} {YELLOW}{name}{RESET}({DIM}{args}{RESET})"


def fmt_tool_result(text: str) -> str:
    lines = text.split("\n")
    indented = f"\n{DIM}{INDENT}{RESET}{GREEN}".join(lines)
    return f"{DIM}{INDENT}{RESET}{GREEN}{indented}{RESET}"


def fmt_input(text: str) -> str:
    return f"{MAGENTA}{BOLD}\n{FLOW}\n {SYM_QUESTION} {text}{RESET}"


def fmt_error(text: str) -> str:
    return f"{RED}{BOLD} {SYM_ERROR} Error:{RESET} {RED}{text}{RESET}"


def fmt_warning(text: str) -> str:
    return f"{YELLOW}{BOLD} {SYM_WARN}{RESET} {YELLOW}{text}{RESET}"


def fmt_done(text: str) -> str:
    return f"{GREEN}{BOLD} {SYM_DONE} Done:{RESET} {GREEN}{text}{RESET}"


def fmt_result() -> str:
    return f"\n{GREEN}{BOLD} {SYM_DONE} Result:{RESET}"


def fmt_stats(text: str) -> str:
    return f"{DIM} --- {text}{RESET}"


def fmt_iteration(current: int, max_iter: int) -> str:
    return f"{DIM}\n --- iteration {current}/{max_iter} ---{RESET}"


def fmt_ok(text: str) -> str:
    return f"{GREEN}{SYM_OK}{RESET} {text}"


def fmt_fail(text: str) -> str:
    return f"{RED}{SYM_FAIL}{RESET} {text}"


def fmt_info(text: str) -> str:
    return f"{CYAN}{SYM_INFO}{RESET} {text}"


def fmt_flow() -> str:
    return f"{DIM}{FLOW}{RESET}"


def fmt_next(text: str) -> str:
    return f"{DIM}{FLOW}  ╌╌▸{RESET} {text}"


def fmt_banner(model: str, tools_count: int, max_iter: int, threshold: str) -> str:
    w = 49
    top    = f"{CYAN}╭{'─' * w}╮{RESET}"
    mid    = f"{CYAN}│{RESET}{{:^{w}}}{CYAN}│{RESET}"
    bottom = f"{CYAN}╰{'─' * w}╯{RESET}"
    return "\n".join([
        top,
        mid.format(f"{BOLD}Tiny Agent - Interactive Mode{RESET}"),
        mid.format("Type /help for available commands"),
        bottom,
        f"  {DIM}Model:{RESET} {model}",
        f"  {DIM}Tools:{RESET} {tools_count} loaded",
        f"  {DIM}Max Iterations:{RESET} {max_iter}",
        f"  {DIM}Completion Threshold:{RESET} {threshold}",
    ])


# ---------------------------------------------------------------------------
# Plain formatters (no color, for API / non-terminal output)
# ---------------------------------------------------------------------------

def plain_goal(text: str) -> str:
    return f"{SYM_GOAL} Goal: {text}"


def plain_thinking(text: str) -> str:
    return f"{FLOW}  {SYM_THINK} {text}"


def plain_tool_call(name: str, args) -> str:
    return f"{ARROW} {name}({args})"


def plain_tool_result(text: str) -> str:
    return f"{INDENT}{text}"


def plain_input(text: str) -> str:
    return f" {SYM_QUESTION} {text}"


def plain_error(text: str) -> str:
    return f" {SYM_ERROR} Error: {text}"


def plain_warning(text: str) -> str:
    return f" {SYM_WARN} {text}"


def plain_done(text: str) -> str:
    return f" {SYM_DONE} Done: {text}"


def plain_ok(text: str) -> str:
    return f"{SYM_OK} {text}"


def plain_fail(text: str) -> str:
    return f"{SYM_FAIL} {text}"
