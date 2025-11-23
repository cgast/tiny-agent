# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Semantic versioning support
- CHANGELOG.md for version history tracking
- `/release-github` command for automated releases

## [0.3.0] - 2025-11-23

### Fixed
- Command execution issues with glob patterns and path validation

### Changed
- Improved error handling for command execution

## [0.2.0] - 2025-11-18

### Added
- Unix-style I/O support (stdout for results, stderr for progress)
- Verbosity control (quiet, normal, verbose, debug)
- HTTP GET command for fetching web content
- .env file support for configuration
- Unified agent.sh runner script
- UNIX_IO.md documentation

### Removed
- dotenv integration from core modules (simplified configuration)
- Makefile (replaced with setup.sh)

### Changed
- Updated usage instructions and configuration display
- Enhanced CLI agent setup and execution

## [0.1.0] - 2025-11-17

### Added
- Initial release
- Core agent functionality (~380 lines)
- 50+ tool templates in templates/ directory
- 4 complete examples (analyze-codebase, log-analysis, data-processing, devops-tasks)
- Docker sandbox support
- Parameter validation and security features
- Path traversal protection
- Structured logging with configurable levels
- Support for OpenAI and Anthropic LLM providers
- Comprehensive documentation (README.md, templates/README.md, examples/README.md)
- MIT License

### Architecture
- agent.py - Original monolithic implementation
- agent_core.py - Pure agent logic with callback interface
- agent_cli.py - CLI wrapper
- agent_api.py - HTTP API wrapper with Flask

[Unreleased]: https://github.com/cgast/tiny-agent/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/cgast/tiny-agent/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/cgast/tiny-agent/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/cgast/tiny-agent/releases/tag/v0.1.0
