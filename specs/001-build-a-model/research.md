# Research Document: MCP Server for Centralized Spec-Kit Functionality

**Date**: 2025-09-19
**Feature**: MCP Server for Centralized Spec-Kit Functionality

## Executive Summary

This research document consolidates findings for implementing a Model Context Protocol (MCP) server that centralizes GitHub's spec-kit functionality. The server will eliminate manual spec-kit installation across repositories while maintaining git-integrated workflows through Python 3.11+ with FastMCP framework.

## 1. FastMCP Framework Implementation

### Decision: FastMCP for MCP Protocol Implementation

**Rationale**: FastMCP provides native Python support for MCP protocol with automatic JSON-RPC 2.0 handling, type validation, and stdio transport out-of-the-box.

**Key Implementation Patterns**:

```python
from fastmcp import FastMCP

# Initialize server
mcp = FastMCP(name="speckit-mcp")

# Define tools for spec-kit operations
@mcp.tool()
async def specify(description: str, repository_path: str) -> dict:
    """Create feature specification from description"""
    # Implementation here
    pass

# Run stdio server
mcp.run(transport='stdio')
```

**Alternatives Considered**:

- Raw JSON-RPC implementation: More control but significant boilerplate
- HTTP-based MCP: Not suitable for CLI tool integration
- Custom protocol: Would break MCP compatibility

## 2. MCP Protocol Architecture

### Decision: Tools for Operations, Resources for Templates

**Rationale**: MCP tools handle state-changing operations (git commands, file creation), while resources serve read-only content (templates, documentation).

**Tool Examples**:

- `specify`: Create feature branch and specification
- `plan`: Generate implementation plan
- `tasks`: Create task breakdown
- `git_operation`: Execute git commands

**Resource Examples**:

- `template://spec`: Specification template
- `template://plan`: Plan template
- `context://project`: Project-specific context

**Alternatives Considered**:

- All tools approach: Would violate MCP resource semantics
- External template storage: Adds deployment complexity

## 3. Git Operations via Subprocess

### Decision: Python subprocess.run() for Git Commands

**Rationale**: Direct subprocess calls provide cross-platform compatibility without shell dependencies while maintaining security through proper input sanitization.

**Implementation Pattern**:

```python
import subprocess
import shlex
from typing import Optional

class GitOperations:
    @staticmethod
    def run_git_command(args: list, cwd: Optional[str] = None) -> tuple[bool, str]:
        """Execute git command safely"""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr
```

**Alternatives Considered**:

- GitPython library: Adds dependency, may have compatibility issues
- Shell execution: Security risk, platform-dependent
- libgit2 bindings: Complex setup, overkill for simple operations

## 4. YAML Configuration Management

### Decision: PyYAML with Pydantic Validation

**Rationale**: PyYAML provides safe parsing while Pydantic ensures schema validation and type safety for configuration files.

**Configuration Structure**:

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import yaml

class ConstitutionConfig(BaseModel):
    """Project constitution configuration"""
    project_name: str
    version: str = Field(pattern=r'^\d+\.\d+\.\d+$')
    templates: Dict[str, str] = {}
    workflows: List[str] = []

class ConfigManager:
    def load_config(self, path: str) -> ConstitutionConfig:
        with open(path) as f:
            data = yaml.safe_load(f)
        return ConstitutionConfig(**data)
```

**Alternatives Considered**:

- JSON configuration: Less human-friendly
- TOML: Limited nesting support
- INI files: Insufficient structure for complex configs

## 5. Project Structure

### Decision: Single Python Package with Embedded Resources

**Rationale**: Simplifies distribution and eliminates external file dependencies while maintaining clear module separation.

```bash
src/speckit_mcp/
├── __init__.py
├── server.py           # Main MCP server
├── tools/              # MCP tool implementations
│   ├── __init__.py
│   ├── specify.py
│   ├── plan.py
│   └── tasks.py
├── resources/          # Embedded templates
│   ├── __init__.py
│   └── templates/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── git/                # Git operations
│   ├── __init__.py
│   └── operations.py
├── config/             # Configuration management
│   ├── __init__.py
│   ├── models.py       # Pydantic models
│   └── manager.py
└── utils/              # Utilities
    ├── __init__.py
    └── file_ops.py
```

**Alternatives Considered**:

- Monolithic script: Poor maintainability
- Microservices: Over-engineered for single-user tool
- Plugin architecture: Unnecessary complexity for MVP

## 6. Toolchain and Package Management

### Decision: mise for Toolchain, uv for Dependencies

**Rationale**: mise provides consistent Python version management across platforms, while uv offers fast, reliable dependency resolution.

**Setup Configuration**:

```toml
# .mise.toml
[tools]
python = "3.11"

# pyproject.toml
[project]
name = "speckit-mcp"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0.0",
    "pyyaml>=6.0",
    "pydantic>=2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Alternatives Considered**:

- Poetry: Slower dependency resolution
- pip-tools: Less modern workflow
- conda: Heavyweight for simple Python project

## 7. Concurrent Operations Handling

### Decision: asyncio with ThreadPoolExecutor for Git

**Rationale**: asyncio provides native async/await support for MCP tools while ThreadPoolExecutor handles blocking git subprocess calls.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class MCPServer:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    @mcp.tool()
    async def concurrent_specify(self, repos: List[str]) -> List[dict]:
        """Handle multiple repository specifications concurrently"""
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self.specify_sync, repo)
            for repo in repos
        ]
        return await asyncio.gather(*tasks)
```

**Alternatives Considered**:

- Threading only: Less elegant async integration
- Multiprocessing: Overhead for I/O-bound operations
- Serial execution: Poor performance for multiple repos

## 8. Error Handling and Logging

### Decision: Structured Logging to Local Files

**Rationale**: File-based logging provides audit trail without external dependencies while structured format enables parsing.

```python
import logging
from pathlib import Path

def setup_logging():
    log_dir = Path.home() / ".specify-mcp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "server.log"),
            logging.StreamHandler()  # Also output to stderr for debugging
        ]
    )
```

**Alternatives Considered**:

- Database logging: Adds complexity
- Remote logging: Privacy concerns
- No logging: Insufficient for debugging

## 9. Testing Strategy

### Decision: pytest with asyncio Support

**Rationale**: pytest provides excellent async testing support with fixtures for MCP server testing.

```python
import pytest
from fastmcp.testing import MCPTestClient

@pytest.fixture
async def mcp_client():
    from speckit_mcp.server import mcp
    async with MCPTestClient(mcp) as client:
        yield client

@pytest.mark.asyncio
async def test_specify_tool(mcp_client):
    result = await mcp_client.call_tool(
        "specify",
        {"description": "Test feature", "repository_path": "/tmp/test"}
    )
    assert result["success"]
    assert "branch" in result
```

**Alternatives Considered**:

- unittest: Less async support
- Manual integration tests: Time-consuming
- No testing: Violates TDD constitution requirement

## 10. Security Considerations

### Decision: Path Validation and Input Sanitization

**Rationale**: Prevents directory traversal and command injection while maintaining usability.

```python
import os
from pathlib import Path

def validate_repository_path(path: str) -> bool:
    """Ensure path is safe and valid repository"""
    try:
        real_path = Path(path).resolve()
        # Check if path exists and is a git repository
        git_dir = real_path / ".git"
        return real_path.exists() and git_dir.is_dir()
    except (OSError, ValueError):
        return False
```

**Alternatives Considered**:

- Containerization: Adds deployment complexity
- Strict sandboxing: May limit functionality
- No validation: Security risk

## Summary of Decisions

1. **FastMCP** for MCP protocol implementation
2. **Tools/Resources split** for operations vs templates
3. **subprocess.run()** for git operations
4. **PyYAML + Pydantic** for configuration
5. **Single package** with embedded resources
6. **mise + uv** for toolchain management
7. **asyncio + ThreadPoolExecutor** for concurrency
8. **File-based logging** with structured format
9. **pytest** for TDD implementation
10. **Path validation** for security

All decisions align with constitutional requirements: MCP compliance, file system preservation, TDD approach, structured data usage, simplicity (YAGNI), and cross-platform compatibility.

## Next Steps

With all technical decisions resolved, Phase 1 can proceed to generate:

- Data model definitions
- API contracts
- Quickstart documentation
- Agent-specific configuration files
