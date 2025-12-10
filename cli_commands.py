#!/usr/bin/env python3
"""
Auto-detect CLI commands module.

Provides automatic detection of available CLI commands in the environment,
with curated descriptions and safety classifications.
"""

import os
import shutil
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Curated registry of known CLI commands with descriptions and safety info
# Commands marked safe=True are allowed by default
# Commands marked docker_only=True are only allowed in Docker environments
KNOWN_CLI_COMMANDS: Dict[str, Dict] = {
    # File operations - safe
    "ls": {
        "description": "List directory contents",
        "safe": True,
    },
    "cat": {
        "description": "Display file contents",
        "safe": True,
    },
    "head": {
        "description": "Show first lines of a file",
        "safe": True,
    },
    "tail": {
        "description": "Show last lines of a file",
        "safe": True,
    },
    "wc": {
        "description": "Count lines, words, and characters in files",
        "safe": True,
    },
    "file": {
        "description": "Determine file type",
        "safe": True,
    },
    "stat": {
        "description": "Display file status and metadata",
        "safe": True,
    },
    "du": {
        "description": "Estimate file and directory disk usage",
        "safe": True,
    },
    "df": {
        "description": "Show disk space usage",
        "safe": True,
    },
    "tree": {
        "description": "Display directory tree structure",
        "safe": True,
    },
    "find": {
        "description": "Find files by name, type, or attributes",
        "safe": True,
    },
    "locate": {
        "description": "Find files by name using database",
        "safe": True,
    },
    "which": {
        "description": "Show full path of commands",
        "safe": True,
    },
    "whereis": {
        "description": "Locate binary, source, and manual files",
        "safe": True,
    },
    "realpath": {
        "description": "Resolve absolute path",
        "safe": True,
    },
    "basename": {
        "description": "Strip directory from filename",
        "safe": True,
    },
    "dirname": {
        "description": "Strip filename from path",
        "safe": True,
    },

    # Text processing - safe
    "grep": {
        "description": "Search text patterns in files",
        "safe": True,
    },
    "egrep": {
        "description": "Search extended regex patterns in files",
        "safe": True,
    },
    "fgrep": {
        "description": "Search fixed string patterns in files",
        "safe": True,
    },
    "awk": {
        "description": "Pattern scanning and text processing",
        "safe": True,
    },
    "sed": {
        "description": "Stream editor for text transformation",
        "safe": True,
    },
    "cut": {
        "description": "Remove sections from lines",
        "safe": True,
    },
    "sort": {
        "description": "Sort lines of text",
        "safe": True,
    },
    "uniq": {
        "description": "Filter or report repeated lines",
        "safe": True,
    },
    "tr": {
        "description": "Translate or delete characters",
        "safe": True,
    },
    "tee": {
        "description": "Read from stdin and write to stdout and files",
        "safe": True,
    },
    "xargs": {
        "description": "Build and execute commands from stdin",
        "safe": True,
    },
    "diff": {
        "description": "Compare files line by line",
        "safe": True,
    },
    "comm": {
        "description": "Compare two sorted files line by line",
        "safe": True,
    },
    "paste": {
        "description": "Merge lines of files",
        "safe": True,
    },
    "join": {
        "description": "Join lines of two files on a common field",
        "safe": True,
    },
    "nl": {
        "description": "Number lines of files",
        "safe": True,
    },
    "fmt": {
        "description": "Simple text formatter",
        "safe": True,
    },
    "fold": {
        "description": "Wrap lines to specified width",
        "safe": True,
    },
    "expand": {
        "description": "Convert tabs to spaces",
        "safe": True,
    },
    "unexpand": {
        "description": "Convert spaces to tabs",
        "safe": True,
    },
    "column": {
        "description": "Format input into columns",
        "safe": True,
    },
    "rev": {
        "description": "Reverse lines character-wise",
        "safe": True,
    },
    "tac": {
        "description": "Display file in reverse line order",
        "safe": True,
    },

    # Data formats - safe
    "jq": {
        "description": "JSON processor and query tool",
        "safe": True,
    },
    "yq": {
        "description": "YAML/JSON/XML processor",
        "safe": True,
    },
    "xmllint": {
        "description": "XML parser and validator",
        "safe": True,
    },
    "csvtool": {
        "description": "CSV file manipulation",
        "safe": True,
    },

    # Compression - safe for reading
    "gzip": {
        "description": "Compress or decompress files",
        "safe": True,
    },
    "gunzip": {
        "description": "Decompress gzip files",
        "safe": True,
    },
    "zcat": {
        "description": "View compressed file contents",
        "safe": True,
    },
    "bzip2": {
        "description": "Compress or decompress files",
        "safe": True,
    },
    "bunzip2": {
        "description": "Decompress bzip2 files",
        "safe": True,
    },
    "bzcat": {
        "description": "View bzip2 compressed file contents",
        "safe": True,
    },
    "xz": {
        "description": "Compress or decompress files",
        "safe": True,
    },
    "unxz": {
        "description": "Decompress xz files",
        "safe": True,
    },
    "xzcat": {
        "description": "View xz compressed file contents",
        "safe": True,
    },
    "tar": {
        "description": "Archive files (tar)",
        "safe": True,
    },
    "zip": {
        "description": "Package and compress files",
        "safe": True,
    },
    "unzip": {
        "description": "Extract zip archives",
        "safe": True,
    },

    # System info - safe
    "date": {
        "description": "Display current date and time",
        "safe": True,
    },
    "cal": {
        "description": "Display calendar",
        "safe": True,
    },
    "uptime": {
        "description": "Show system uptime",
        "safe": True,
    },
    "hostname": {
        "description": "Show or set system hostname",
        "safe": True,
    },
    "uname": {
        "description": "Print system information",
        "safe": True,
    },
    "whoami": {
        "description": "Print current username",
        "safe": True,
    },
    "id": {
        "description": "Print user and group IDs",
        "safe": True,
    },
    "groups": {
        "description": "Print group memberships",
        "safe": True,
    },
    "env": {
        "description": "Print environment variables",
        "safe": True,
    },
    "printenv": {
        "description": "Print environment variables",
        "safe": True,
    },
    "pwd": {
        "description": "Print working directory",
        "safe": True,
    },
    "free": {
        "description": "Display memory usage",
        "safe": True,
    },
    "vmstat": {
        "description": "Report virtual memory statistics",
        "safe": True,
    },
    "iostat": {
        "description": "Report I/O statistics",
        "safe": True,
    },
    "lscpu": {
        "description": "Display CPU architecture information",
        "safe": True,
    },
    "lsblk": {
        "description": "List block devices",
        "safe": True,
    },
    "lsusb": {
        "description": "List USB devices",
        "safe": True,
    },
    "lspci": {
        "description": "List PCI devices",
        "safe": True,
    },

    # Process info - safe (read-only)
    "ps": {
        "description": "Report process status",
        "safe": True,
    },
    "top": {
        "description": "Display running processes (use -b for batch mode)",
        "safe": True,
    },
    "htop": {
        "description": "Interactive process viewer",
        "safe": True,
    },
    "pgrep": {
        "description": "Find processes by name",
        "safe": True,
    },
    "pidof": {
        "description": "Find process ID by name",
        "safe": True,
    },
    "pstree": {
        "description": "Display process tree",
        "safe": True,
    },
    "lsof": {
        "description": "List open files",
        "safe": True,
    },

    # Network diagnostics - safe
    "ping": {
        "description": "Send ICMP echo requests to hosts",
        "safe": True,
    },
    "curl": {
        "description": "Transfer data from URLs",
        "safe": True,
    },
    "wget": {
        "description": "Download files from web",
        "safe": True,
    },
    "dig": {
        "description": "DNS lookup utility",
        "safe": True,
    },
    "nslookup": {
        "description": "Query DNS servers",
        "safe": True,
    },
    "host": {
        "description": "DNS lookup utility",
        "safe": True,
    },
    "traceroute": {
        "description": "Trace packet route to host",
        "safe": True,
    },
    "netstat": {
        "description": "Network statistics",
        "safe": True,
    },
    "ss": {
        "description": "Socket statistics",
        "safe": True,
    },
    "ip": {
        "description": "Show/manipulate routing and network devices",
        "safe": True,
    },
    "ifconfig": {
        "description": "Configure network interfaces",
        "safe": True,
    },
    "arp": {
        "description": "Display ARP table",
        "safe": True,
    },

    # Development tools - safe
    "git": {
        "description": "Version control system",
        "safe": True,
    },
    "python": {
        "description": "Python interpreter",
        "safe": True,
    },
    "python3": {
        "description": "Python 3 interpreter",
        "safe": True,
    },
    "pip": {
        "description": "Python package installer",
        "safe": True,
    },
    "pip3": {
        "description": "Python 3 package installer",
        "safe": True,
    },
    "node": {
        "description": "Node.js JavaScript runtime",
        "safe": True,
    },
    "npm": {
        "description": "Node.js package manager",
        "safe": True,
    },
    "npx": {
        "description": "Execute npm packages",
        "safe": True,
    },
    "yarn": {
        "description": "JavaScript package manager",
        "safe": True,
    },
    "ruby": {
        "description": "Ruby interpreter",
        "safe": True,
    },
    "gem": {
        "description": "Ruby package manager",
        "safe": True,
    },
    "go": {
        "description": "Go programming language",
        "safe": True,
    },
    "rustc": {
        "description": "Rust compiler",
        "safe": True,
    },
    "cargo": {
        "description": "Rust package manager",
        "safe": True,
    },
    "make": {
        "description": "Build automation tool",
        "safe": True,
    },
    "cmake": {
        "description": "Cross-platform build system",
        "safe": True,
    },
    "gcc": {
        "description": "GNU C compiler",
        "safe": True,
    },
    "g++": {
        "description": "GNU C++ compiler",
        "safe": True,
    },
    "clang": {
        "description": "LLVM C compiler",
        "safe": True,
    },
    "javac": {
        "description": "Java compiler",
        "safe": True,
    },
    "java": {
        "description": "Java runtime",
        "safe": True,
    },

    # Docker - safe in controlled environments
    "docker": {
        "description": "Container management",
        "safe": True,
    },
    "docker-compose": {
        "description": "Multi-container Docker applications",
        "safe": True,
    },
    "kubectl": {
        "description": "Kubernetes command-line tool",
        "safe": True,
    },

    # File modification - docker only (more permissive in sandbox)
    "cp": {
        "description": "Copy files and directories",
        "safe": False,
        "docker_only": True,
    },
    "mv": {
        "description": "Move or rename files",
        "safe": False,
        "docker_only": True,
    },
    "mkdir": {
        "description": "Create directories",
        "safe": False,
        "docker_only": True,
    },
    "touch": {
        "description": "Create empty file or update timestamp",
        "safe": False,
        "docker_only": True,
    },
    "ln": {
        "description": "Create links between files",
        "safe": False,
        "docker_only": True,
    },
    "rmdir": {
        "description": "Remove empty directories",
        "safe": False,
        "docker_only": True,
    },

    # Dangerous commands - never auto-detected (require explicit definition)
    "rm": {
        "description": "Remove files (DANGEROUS)",
        "safe": False,
        "docker_only": False,
        "blocked": True,
    },
    "sudo": {
        "description": "Execute as superuser (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
    "su": {
        "description": "Switch user (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
    "chmod": {
        "description": "Change file permissions",
        "safe": False,
        "blocked": True,
    },
    "chown": {
        "description": "Change file ownership",
        "safe": False,
        "blocked": True,
    },
    "dd": {
        "description": "Low-level data copy (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
    "mkfs": {
        "description": "Create filesystem (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
    "fdisk": {
        "description": "Partition table manipulator (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
    "kill": {
        "description": "Send signal to process",
        "safe": False,
        "blocked": True,
    },
    "killall": {
        "description": "Kill processes by name",
        "safe": False,
        "blocked": True,
    },
    "pkill": {
        "description": "Kill processes by pattern",
        "safe": False,
        "blocked": True,
    },
    "reboot": {
        "description": "Reboot system (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
    "shutdown": {
        "description": "Shutdown system (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
    "poweroff": {
        "description": "Power off system (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
    "halt": {
        "description": "Halt system (DANGEROUS)",
        "safe": False,
        "blocked": True,
    },
}

# Default blocklist - these commands are never auto-detected
DEFAULT_BLOCKLIST = {
    "rm", "sudo", "su", "chmod", "chown", "dd", "mkfs", "fdisk",
    "kill", "killall", "pkill", "reboot", "shutdown", "poweroff", "halt",
    "passwd", "useradd", "userdel", "groupadd", "groupdel",
    "iptables", "ip6tables", "nft", "firewall-cmd",
    "systemctl", "service", "init",
}


def is_in_docker() -> bool:
    """Check if running inside a Docker container"""
    return os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")


def get_available_commands(
    allowlist: Optional[List[str]] = None,
    blocklist: Optional[List[str]] = None,
    include_docker_only: Optional[bool] = None,
) -> Dict[str, Dict]:
    """
    Get available CLI commands based on what's installed and allowed.

    Args:
        allowlist: If provided, only these commands are considered
        blocklist: Commands to exclude (merged with DEFAULT_BLOCKLIST)
        include_docker_only: Include docker-only commands. Auto-detected if None.

    Returns:
        Dict of command name -> command info for available commands
    """
    if include_docker_only is None:
        include_docker_only = is_in_docker()

    # Merge blocklists
    effective_blocklist = DEFAULT_BLOCKLIST.copy()
    if blocklist:
        effective_blocklist.update(blocklist)

    available = {}

    # Determine which commands to check
    commands_to_check = allowlist if allowlist else list(KNOWN_CLI_COMMANDS.keys())

    for cmd_name in commands_to_check:
        # Skip if blocklisted
        if cmd_name in effective_blocklist:
            logger.debug(f"Skipping blocklisted command: {cmd_name}")
            continue

        # Get command info
        cmd_info = KNOWN_CLI_COMMANDS.get(cmd_name)
        if not cmd_info:
            # Unknown command - skip unless explicitly allowlisted
            if allowlist and cmd_name in allowlist:
                # Create basic entry for explicitly allowed unknown command
                cmd_info = {
                    "description": f"Execute {cmd_name} command",
                    "safe": False,
                    "docker_only": True,
                }
            else:
                continue

        # Check if blocked
        if cmd_info.get("blocked"):
            logger.debug(f"Skipping blocked command: {cmd_name}")
            continue

        # Check docker_only restriction
        if cmd_info.get("docker_only") and not include_docker_only:
            logger.debug(f"Skipping docker-only command outside Docker: {cmd_name}")
            continue

        # Check if safe or in Docker
        if not cmd_info.get("safe") and not include_docker_only:
            logger.debug(f"Skipping unsafe command outside Docker: {cmd_name}")
            continue

        # Check if command exists in PATH
        if shutil.which(cmd_name):
            available[cmd_name] = cmd_info
            logger.debug(f"Found available command: {cmd_name}")
        else:
            logger.debug(f"Command not found in PATH: {cmd_name}")

    return available


def generate_cli_tools(
    allowlist: Optional[List[str]] = None,
    blocklist: Optional[List[str]] = None,
    include_docker_only: Optional[bool] = None,
) -> tuple[List[Dict], List[Dict]]:
    """
    Generate tool definitions for available CLI commands.

    Args:
        allowlist: If provided, only these commands are considered
        blocklist: Commands to exclude
        include_docker_only: Include docker-only commands. Auto-detected if None.

    Returns:
        Tuple of (tools, commands) where:
        - tools: List of OpenAI-format tool definitions
        - commands: List of command configurations for execution
    """
    available = get_available_commands(allowlist, blocklist, include_docker_only)

    tools = []
    commands = []

    for cmd_name, cmd_info in sorted(available.items()):
        # Create command configuration
        cmd_config = {
            "name": f"cli_{cmd_name}",
            "description": cmd_info["description"],
            "command": f"{cmd_name} {{args}}",
            "auto_detected": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "args": {
                        "type": "string",
                        "description": f"Arguments to pass to {cmd_name}. Can include flags and parameters.",
                    }
                },
                "required": [],
            },
        }
        commands.append(cmd_config)

        # Create OpenAI-format tool
        tools.append({
            "type": "function",
            "function": {
                "name": cmd_config["name"],
                "description": cmd_config["description"],
                "parameters": cmd_config["parameters"],
            },
        })

    logger.info(f"Generated {len(tools)} auto-detected CLI tools")
    return tools, commands


def parse_command_list(env_value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated command list from environment variable"""
    if not env_value:
        return None
    return [cmd.strip() for cmd in env_value.split(",") if cmd.strip()]
