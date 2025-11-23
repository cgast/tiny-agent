"""Version information for tiny-agent."""

__version__ = "0.3.0"
__version_info__ = tuple(int(i) for i in __version__.split("."))

# Version history
VERSION_HISTORY = {
    "0.3.0": "2025-11-23 - Bug fixes for command execution",
    "0.2.0": "2025-11-18 - Unix-style I/O, verbosity control",
    "0.1.0": "2025-11-17 - Initial release",
}


def get_version() -> str:
    """Get the current version string."""
    return __version__


def get_version_info() -> tuple:
    """Get the version as a tuple of integers."""
    return __version_info__


def print_version():
    """Print version information."""
    print(f"tiny-agent v{__version__}")
    print(f"\nVersion History:")
    for version, description in sorted(VERSION_HISTORY.items(), reverse=True):
        print(f"  {version}: {description}")


if __name__ == "__main__":
    print_version()
