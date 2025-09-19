# Spec-Kit MCP Server Constitution

## Core Principles

### I. MCP Protocol Compliance

All functionality MUST be exposed through valid MCP tools and resources. No direct CLI interfaces or HTTP endpoints. Server must implement stdio protocol correctly with proper JSON-RPC 2.0 messaging.

### II. File System Preservation

Maintain existing git-integrated workflow. Continue generating files in `specs/[branch]/` structure. Preserve branch creation and semantic naming. Never break compatibility with existing spec-kit installations.

### III. Test-First Development (NON-NEGOTIABLE)

TDD mandatory: Tests written → User approved → Tests fail → Then implement. All MCP tools must have integration tests that verify actual file generation and git operations.

### IV. Structured Data Over Markdown

Replace token-inefficient markdown parsing with structured YAML/JSON. Task tracking, project state, and configuration use structured formats for better programmatic access.

### V. Simplicity and YAGNI

Start with minimal viable functionality. No premature team/enterprise features. Focus on eliminating per-repo setup burden. Add complexity only when proven necessary through real usage.

### VI. Cross-Platform Compatibility

No shell script dependencies. Use Python subprocess for git operations only. All functionality must work identically on Windows, macOS, and Linux.

## Technical Constraints

**Technology Stack**: Python 3.11+, FastMCP, PyYAML, Pydantic
**Package Management**: uv for dependencies, mise for toolchain
**Persistence**: File system only, no external databases
**Configuration**: `.specify-mcp/` directory for project-specific settings

## Development Workflow

**MCP Tool Pattern**: Each tool validates inputs → performs git/file operations → returns structured results
**Error Handling**: Graceful degradation when git operations fail or files are missing
**Logging**: Local file logging for debugging and audit trail

## Governance

Constitution supersedes implementation convenience. All features must align with core principles. Complexity additions require documented justification and user validation.

**Version**: 1.0.0 | **Ratified**: 2025-09-19 | **Last Amended**: 2025-09-19
