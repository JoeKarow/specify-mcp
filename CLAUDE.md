# specify-mcp Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-19

## Active Technologies
- Python 3.11+ (001-build-a-model)
- FastMCP for MCP protocol implementation
- PyYAML for configuration parsing
- Pydantic for data validation
- asyncio for concurrent operations
- pytest for testing

## Project Structure
```
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
├── git/                # Git operations
│   ├── __init__.py
│   └── operations.py
├── config/             # Configuration management
│   ├── __init__.py
│   ├── models.py
│   └── manager.py
└── utils/
    ├── __init__.py
    └── file_ops.py

tests/
├── contract/           # Contract tests
├── integration/        # Integration tests
└── unit/               # Unit tests
```

## Commands
```bash
# Development setup
mise install            # Install Python 3.11+
uv pip install -e .     # Install package in dev mode

# Testing
pytest tests/           # Run all tests
pytest tests/contract/  # Run contract tests only

# Running the server
python -m speckit_mcp.server  # Start MCP server in stdio mode

# Package management
uv pip add <package>    # Add new dependency
uv pip sync             # Sync dependencies
```

## Code Style
Python: Follow PEP 8 with type hints for all functions
- Use async/await for I/O operations
- Implement proper error handling with MCPError
- Add comprehensive docstrings
- Validate inputs with Pydantic models

## Testing Requirements
- TDD mandatory: Write failing tests first
- All MCP tools must have integration tests
- Test git operations with temporary repositories
- Mock subprocess calls for unit tests
- Verify file generation and structure

## Constitutional Principles
1. **MCP Protocol Compliance**: All functionality through MCP tools/resources
2. **File System Preservation**: Maintain git-integrated workflow
3. **Test-First Development**: TDD with integration tests
4. **Structured Data**: YAML over markdown for parsing
5. **Simplicity (YAGNI)**: MVP without premature features
6. **Cross-Platform**: No shell dependencies, pure Python

## Recent Changes
- 001-build-a-model: Initial MCP server implementation with FastMCP
  - Added specify, plan, and tasks MCP tools
  - Implemented YAML-based configuration management
  - Created embedded template resource system

## Key Implementation Notes

### MCP Tools
```python
@mcp.tool()
async def specify(description: str, repository_path: str) -> dict:
    """Create feature specification from description"""
    # Validate repository
    # Create feature branch
    # Generate spec from template
    # Return results
```

### Git Operations
```python
# Use subprocess for git commands - never shell=True
result = subprocess.run(
    ['git', 'checkout', '-b', branch_name],
    cwd=repository_path,
    capture_output=True,
    text=True,
    check=True
)
```

### Configuration Loading
```python
# Always use safe_load for YAML
with open(config_path) as f:
    config = yaml.safe_load(f)
# Validate with Pydantic
validated = ProjectConfiguration(**config)
```

<!-- MANUAL ADDITIONS START -->
<!-- Add project-specific notes here -->
<!-- MANUAL ADDITIONS END -->