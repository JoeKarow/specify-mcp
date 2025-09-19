# SpecKit MCP Server

A Model Context Protocol (MCP) server that provides structured feature development workflows through git-integrated tools for creating specifications, implementation plans, and task lists.

## Overview

SpecKit MCP transforms natural language feature descriptions into structured development workflows using YAML-based templates and git branch management. It provides MCP tools for specification generation, implementation planning, and task breakdown while maintaining full integration with your existing git workflow.

## Features

### Core MCP Tools

- **`specify`** - Generate feature specifications from natural language descriptions
- **`plan`** - Create detailed implementation plans from specifications
- **`tasks`** - Break down plans into structured task lists
- **`initialize`** - Set up SpecKit configuration in existing repositories
- **`get_context`** - Retrieve project context and configuration

### MCP Resources

- **Templates** - Access specification, plan, and task templates
- **Documentation** - MCP protocol docs and usage guides
- **Configuration** - Schema definitions and default configurations
- **Workflows** - Workflow state and execution information

### Key Capabilities

- ✅ **Git Integration** - Automatic branch creation and management
- ✅ **Template System** - Customizable YAML-based templates with variable substitution
- ✅ **Configuration Management** - Project-specific settings with inheritance
- ✅ **Structured Data** - YAML over markdown for machine-parsable artifacts
- ✅ **Cross-Platform** - Pure Python implementation without shell dependencies
- ✅ **Performance Optimized** - Async operations with caching and concurrent resource loading

## Installation

### Prerequisites

- Python 3.11 or higher
- Git installed and configured
- Existing git repository (for project initialization)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/specify-mcp.git
cd specify-mcp

# Install dependencies and package in development mode
pip install -e .
```

### Verify Installation

```bash
# Test the server
python -m speckit_mcp.server
```

## Usage

### Starting the MCP Server

The SpecKit MCP server runs in stdio mode for integration with MCP clients:

```bash
python -m speckit_mcp.server
```

### MCP Client Configuration

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "speckit": {
      "command": "python",
      "args": ["-m", "speckit_mcp.server"],
      "cwd": "/path/to/specify-mcp"
    }
  }
}
```

### Initializing a Project

Set up SpecKit in an existing repository:

```bash
# Initialize SpecKit configuration
python -c "
import asyncio
from speckit_mcp.tools.initialize import initialize_project
asyncio.run(initialize_project('My Project', '/path/to/repo'))
"
```

Or use the MCP tool through your client:

```
initialize_project project_name="/path/to/repo" description="My awesome project"
```

### Creating Feature Specifications

Use the `specify` tool to generate feature specifications:

```
specify description="Add user authentication with JWT tokens" repository_path="/path/to/repo"
```

This will:
1. Create a feature branch (e.g., `001-add-user-authentication`)
2. Generate a specification file from template
3. Commit the specification to the branch

### Implementation Planning

Generate implementation plans from specifications:

```
plan spec_path="/path/to/repo/specs/001-add-user-authentication.md" repository_path="/path/to/repo"
```

### Task Breakdown

Create detailed task lists from implementation plans:

```
tasks plan_path="/path/to/repo/plans/001-add-user-authentication.md" repository_path="/path/to/repo"
```

## Configuration

### Project Constitution

SpecKit uses a `.specify-mcp/constitution.yaml` file for project-specific configuration:

```yaml
project:
  name: "My Project"
  description: "Project description"
  version: "1.0.0"

principles:
  - name: "Test-First Development"
    description: "Write tests before implementation"
    priority: 1

git:
  default_branch: "main"

workflows:
  specify:
    enabled: true
    branch_prefix: "feature/"
    steps:
      - "validate_repository"
      - "create_branch"
      - "generate_spec"
      - "commit_changes"

settings:
  auto_commit: true
  verbose_logging: false
  max_parallel_tasks: 5
```

### User Configuration

Global settings can be configured in `~/.specify-mcp/config.yaml`:

```yaml
git:
  default_branch: "main"

settings:
  verbose_logging: true
  auto_commit: true

templates:
  spec: "/path/to/custom/spec-template.md"
```

### Custom Templates

Override default templates by providing custom template files:

```yaml
# In constitution.yaml
templates:
  spec: "/path/to/custom-spec-template.md"
  plan: "/path/to/custom-plan-template.md"
  tasks: "/path/to/custom-tasks-template.md"
```

Template files use YAML front matter for metadata and Jinja2-style variables:

```markdown
---
template: spec
version: 1.0.0
variables:
  - feature_id
  - feature_name
  - description
---

# Feature Specification: {{feature_name}}

**Feature ID**: {{feature_id}}
**Date**: {{date}}

## Overview

{{description}}

## Requirements

### Functional Requirements

1. **[FR-001]** Primary functionality requirement
2. **[FR-002]** Secondary functionality requirement

## Implementation Notes

*Additional implementation details...*
```

## Project Structure

```
src/speckit_mcp/
├── __init__.py
├── server.py              # Main MCP server
├── tools/                 # MCP tool implementations
│   ├── __init__.py
│   ├── specify.py         # Feature specification tool
│   ├── plan.py           # Implementation planning tool
│   ├── tasks.py          # Task breakdown tool
│   ├── initialize.py     # Project initialization
│   └── context.py        # Context retrieval
├── resources/            # MCP resource providers
│   ├── __init__.py
│   ├── templates.py      # Template resources
│   ├── documentation.py # Documentation resources
│   ├── configuration.py # Configuration resources
│   ├── workflows.py      # Workflow resources
│   ├── template_manager.py # Template loading/caching
│   └── models.py         # Resource data models
├── config/               # Configuration management
│   ├── __init__.py
│   ├── models.py         # Pydantic configuration models
│   └── manager.py        # Configuration loading/saving
├── git/                  # Git operations
│   ├── __init__.py
│   └── operations.py     # Git command wrappers
└── utils/
    ├── __init__.py
    └── file_ops.py       # File system utilities

tests/
├── contract/             # Contract tests for MCP compliance
├── integration/          # Integration tests
└── unit/                 # Unit tests
```

## Development

### Development Setup

```bash
# Install development dependencies
mise install              # Install Python 3.11+
uv pip install -e .       # Install package in development mode
uv pip install pytest pytest-asyncio pytest-mock  # Testing dependencies
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test types
pytest tests/unit/         # Unit tests only
pytest tests/integration/  # Integration tests only
pytest tests/contract/     # Contract tests only

# Run with coverage
pytest tests/ --cov=src/speckit_mcp --cov-report=html
```

### Testing Philosophy

SpecKit follows Test-Driven Development (TDD) principles:

1. **Unit Tests** - Test individual functions with mocked dependencies
2. **Integration Tests** - Test MCP tool workflows with temporary repositories
3. **Contract Tests** - Verify MCP protocol compliance

### Code Style

- **Python**: Follow PEP 8 with type hints for all functions
- **Async/Await**: Use for I/O operations and MCP tool implementations
- **Error Handling**: Implement proper error handling with MCPError
- **Documentation**: Add comprehensive docstrings for all public functions
- **Validation**: Use Pydantic models for input validation

### Git Workflow

```bash
# Feature development
git checkout -b feature/new-capability
# ... make changes ...
pytest tests/  # Ensure tests pass
git commit -m "feat: add new capability"
git push origin feature/new-capability
# Create pull request
```

## Architecture

### MCP Protocol Implementation

SpecKit implements the Model Context Protocol using FastMCP:

- **Tools** - Expose workflow operations (specify, plan, tasks)
- **Resources** - Provide access to templates, documentation, and configuration
- **Server** - Manages tool registration and request handling

### Data Flow

1. **User Input** → Natural language feature description
2. **Specification** → Generated from template with extracted requirements
3. **Planning** → Implementation plan with phases and dependencies
4. **Tasks** → Granular task breakdown with assignees and dependencies
5. **Git Integration** → Branch management and commit automation

### Template System

- **YAML Front Matter** - Metadata and variable definitions
- **Jinja2 Variables** - Dynamic content substitution
- **Embedded Templates** - Default templates included in package
- **Custom Override** - Project-specific template customization
- **Caching** - Performance optimization for frequently accessed templates

## Contributing

### Guidelines

1. **TDD Required** - Write failing tests before implementation
2. **MCP Compliance** - All functionality must be exposed through MCP tools/resources
3. **Git Integration** - Maintain git-integrated workflow
4. **Documentation** - Update README and docstrings for new features
5. **Performance** - Consider async operations and caching for I/O

### Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Implement changes with tests
4. Ensure all tests pass: `pytest tests/`
5. Update documentation as needed
6. Submit pull request with clear description

### Issue Reporting

When reporting issues, include:

- SpecKit version
- Python version
- Operating system
- MCP client being used
- Minimal reproduction steps
- Expected vs actual behavior

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: Check the `/docs` resource in your MCP client
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Use GitHub Discussions for questions and ideas

## Changelog

### v1.0.0 (Current)

- ✅ Core MCP tools (specify, plan, tasks, initialize, get_context)
- ✅ MCP resources (templates, documentation, configuration, workflows)
- ✅ Git integration with branch management
- ✅ YAML-based template system with caching
- ✅ Configuration management with inheritance
- ✅ Cross-platform compatibility
- ✅ Performance optimizations with async operations
- ✅ Comprehensive test suite (unit, integration, contract)

## Related Projects

- **FastMCP** - MCP server framework used by SpecKit
- **Model Context Protocol** - Protocol specification for AI assistant integration
- **Claude Desktop** - MCP client for Claude AI assistant