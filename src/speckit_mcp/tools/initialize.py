"""
MCP tool for initializing project configuration.

This module implements the initialize_project tool that sets up the
.specify-mcp directory structure and creates the constitution.yaml file.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastmcp.exceptions import McpError

from speckit_mcp.git.operations import (
    is_git_repo,
    init_repo,
    get_repo_root,
    add_files,
    commit
)
from speckit_mcp.config.manager import ConfigurationManager
from speckit_mcp.config.models import (
    ProjectConfiguration,
    ProjectInfo,
    Principle,
    GitConfig,
    WorkflowType,
    WorkflowConfig
)
from speckit_mcp.utils.file_ops import ensure_directory, safe_write


def _generate_project_id() -> str:
    """
    Generate a unique project identifier.

    Returns:
        Project ID string
    """
    # Use a short UUID for project identification
    return str(uuid.uuid4())[:8]


def _create_default_principles() -> list:
    """
    Create default constitutional principles.

    Returns:
        List of Principle objects
    """
    return [
        Principle(
            name="MCP Protocol Compliance",
            description="All functionality must be exposed through MCP tools and resources",
            priority=1
        ),
        Principle(
            name="File System Preservation",
            description="Maintain git-integrated workflow without external dependencies",
            priority=2
        ),
        Principle(
            name="Test-First Development",
            description="Write failing tests before implementation (TDD)",
            priority=3
        ),
        Principle(
            name="Structured Data",
            description="Use YAML over markdown for machine-parsable data",
            priority=4
        ),
        Principle(
            name="Simplicity (YAGNI)",
            description="Build MVP without premature features",
            priority=5
        ),
        Principle(
            name="Cross-Platform Support",
            description="No shell dependencies, pure Python implementation",
            priority=6
        )
    ]


def _create_default_workflows() -> Dict[WorkflowType, WorkflowConfig]:
    """
    Create default workflow configurations.

    Returns:
        Dictionary of workflow configurations
    """
    return {
        WorkflowType.SPECIFY: WorkflowConfig(
            enabled=True,
            steps=[
                "validate_repository",
                "create_branch",
                "generate_spec",
                "commit_changes"
            ],
            branch_prefix="feature/"
        ),
        WorkflowType.PLAN: WorkflowConfig(
            enabled=True,
            steps=[
                "load_spec",
                "analyze_requirements",
                "generate_plan",
                "save_artifacts"
            ]
        ),
        WorkflowType.TASKS: WorkflowConfig(
            enabled=True,
            steps=[
                "load_plan",
                "generate_tasks",
                "apply_rules",
                "save_tasks"
            ]
        )
    }


def _create_gitignore_content() -> str:
    """
    Create content for .specify-mcp/.gitignore file.

    Returns:
        Gitignore file content
    """
    return """# Temporary files
*.tmp
*.swp
*.bak
*~

# Cache and logs
cache/
logs/
*.log

# User-specific settings
user-config.yaml
local-settings.yaml

# Generated artifacts (keep these)
# specs/
# plans/
# tasks/

# Development
.env
.venv/
__pycache__/
*.pyc
"""


def _create_readme_content(project_name: str) -> str:
    """
    Create content for .specify-mcp/README.md file.

    Returns:
        README file content
    """
    return f"""# {project_name} - SpecKit MCP Configuration

This directory contains the SpecKit MCP configuration and artifacts for the project.

## Structure

```
.specify-mcp/
├── constitution.yaml    # Project configuration and principles
├── specs/               # Feature specifications
├── plans/               # Implementation plans
├── tasks/               # Task breakdowns
├── templates/           # Custom templates (optional)
└── docs/                # Additional documentation
```

## Usage

The SpecKit MCP server manages this directory automatically through MCP tools:

- `specify`: Create feature specifications
- `plan`: Generate implementation plans
- `tasks`: Create task breakdowns
- `initialize_project`: Set up project configuration
- `get_context`: Retrieve phase-specific documentation

## Configuration

Edit `constitution.yaml` to customize:
- Project metadata
- Constitutional principles
- Workflow settings
- Template overrides

## Generated Files

All generated artifacts follow the naming convention:
- Specifications: `XXX-spec.md`
- Plans: `XXX-plan.md`
- Tasks: `XXX-tasks.md` and `XXX-tasks.yaml`

Where `XXX` is a unique feature identifier.
"""


async def initialize_project(
    repository_path: str,
    project_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize project with SpecKit MCP configuration.

    This MCP tool creates the .specify-mcp directory structure and
    initializes the constitution.yaml configuration file.

    Args:
        repository_path: Path to git repository
        project_name: Optional project name (defaults to directory name)

    Returns:
        Dictionary containing:
            - success: Whether the operation succeeded
            - constitution_path: Path to created constitution.yaml
            - project_id: Generated project identifier
            - directories_created: List of created directories
            - message: Status message

    Raises:
        McpError: If initialization fails or project already initialized
    """
    try:
        # Validate repository path
        repo_path = Path(repository_path)
        if not repo_path.exists():
            raise McpError(
                code=-32602,  # Invalid params
                message=f"Repository path does not exist: {repository_path}"
            )

        if not repo_path.is_dir():
            raise McpError(
                code=-32602,
                message=f"Repository path is not a directory: {repository_path}"
            )

        # Initialize git repo if needed
        if not is_git_repo(str(repo_path)):
            init_result = init_repo(str(repo_path))
            if not init_result.get('success'):
                raise McpError(
                    code=-32603,
                    message=f"Failed to initialize git repository: {init_result.get('message')}"
                )

        # Get repository root
        repo_root = get_repo_root(str(repo_path))
        if not repo_root:
            repo_root = str(repo_path)

        # Check if already initialized
        config_dir = Path(repo_root) / '.specify-mcp'
        constitution_path = config_dir / 'constitution.yaml'

        if constitution_path.exists():
            raise McpError(
                code=-32603,
                message=f"Project already initialized. Constitution exists at: {constitution_path}"
            )

        # Use provided project name or derive from directory
        if not project_name:
            project_name = Path(repo_root).name

        # Generate project ID
        project_id = _generate_project_id()

        # Create directory structure
        directories = [
            config_dir,
            config_dir / 'specs',
            config_dir / 'plans',
            config_dir / 'tasks',
            config_dir / 'templates',
            config_dir / 'docs'
        ]

        directories_created = []
        for directory in directories:
            ensure_directory(directory)
            directories_created.append(str(directory))

        # Create project configuration
        project_config = ProjectConfiguration(
            project=ProjectInfo(
                name=project_name,
                description=f"{project_name} - Managed by SpecKit MCP",
                version="1.0.0"
            ),
            principles=_create_default_principles(),
            git=GitConfig(
                default_branch="main"
            ),
            workflows=_create_default_workflows(),
            templates={},
            settings={
                'auto_commit': True,
                'verbose_logging': False,
                'max_parallel_tasks': 5,
                'project_id': project_id
            }
        )

        # Save configuration using ConfigurationManager
        config_manager = ConfigurationManager(repo_root)
        config_manager.save_configuration(project_config)

        # Create .gitignore file
        gitignore_path = config_dir / '.gitignore'
        safe_write(
            gitignore_path,
            _create_gitignore_content(),
            base_path=repo_root
        )

        # Create README file
        readme_path = config_dir / 'README.md'
        safe_write(
            readme_path,
            _create_readme_content(project_name),
            base_path=repo_root
        )

        # Create initial template examples
        spec_template_path = config_dir / 'templates' / 'custom-spec.md.example'
        safe_write(
            spec_template_path,
            """---
template: spec
version: 1.0.0
variables:
  - feature_id
  - feature_name
  - description
---

# Custom Specification Template

This is an example custom template. Copy and modify as needed.

Feature: {{feature_name}}
ID: {{feature_id}}
""",
            base_path=repo_root
        )

        # Auto-commit the initialization
        if project_config.settings.get('auto_commit', True):
            # Add all created files
            files_to_add = [
                '.specify-mcp/constitution.yaml',
                '.specify-mcp/.gitignore',
                '.specify-mcp/README.md',
                '.specify-mcp/templates/custom-spec.md.example'
            ]

            add_result = add_files(repo_root, files_to_add)

            if add_result.get('success'):
                # Create initial commit
                commit_message = f"chore: Initialize SpecKit MCP configuration for {project_name}"
                commit_result = commit(repo_root, commit_message)

                if not commit_result.get('success'):
                    # Log warning but don't fail
                    print(f"Warning: Could not commit initialization: {commit_result.get('message')}")

        return {
            'success': True,
            'constitution_path': str(constitution_path),
            'project_id': project_id,
            'directories_created': directories_created,
            'project_name': project_name,
            'message': f"Successfully initialized SpecKit MCP for project '{project_name}'"
        }

    except McpError:
        # Re-raise MCP errors as-is
        raise
    except Exception as e:
        # Wrap other exceptions in McpError
        raise McpError(
            code=-32603,  # Internal error
            message=f"Project initialization failed: {str(e)}",
            data={"error_type": type(e).__name__}
        )