"""
MCP tool for creating feature specifications.

This module implements the specify tool that creates feature branches,
generates specifications from templates, and manages the spec workflow.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from fastmcp.exceptions import McpError

from speckit_mcp.git.operations import (
    is_git_repo,
    get_repo_root,
    create_branch,
    add_files,
    commit,
    get_current_branch
)
from speckit_mcp.config.manager import ConfigurationManager
from speckit_mcp.resources.template_manager import TemplateManager
from speckit_mcp.resources.models import TemplateType
from speckit_mcp.utils.file_ops import safe_write, ensure_directory


def _generate_feature_id() -> str:
    """
    Generate a unique feature ID based on timestamp.

    Returns:
        Feature ID in format XXX where XXX is a 3-digit number
    """
    # Use timestamp-based ID for uniqueness
    timestamp = datetime.now()
    # Create ID from timestamp components
    id_num = (timestamp.month * 100 + timestamp.day) % 1000
    return f"{id_num:03d}"


def _slugify(text: str) -> str:
    """
    Convert text to a valid git branch slug.

    Args:
        text: Text to slugify

    Returns:
        Slugified text suitable for branch names
    """
    # Convert to lowercase
    text = text.lower()

    # Replace spaces and punctuation with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)

    # Remove leading/trailing hyphens
    text = text.strip('-')

    # Limit length
    if len(text) > 50:
        text = text[:50].rstrip('-')

    return text


async def specify(description: str, repository_path: str) -> Dict[str, Any]:
    """
    Create feature specification from description.

    This MCP tool creates a feature branch, generates a specification
    from a template, and commits the changes to the repository.

    Args:
        description: Natural language feature description
        repository_path: Path to git repository

    Returns:
        Dictionary containing:
            - success: Whether the operation succeeded
            - branch_name: Created feature branch name
            - spec_path: Path to generated specification file
            - feature_id: Generated feature identifier
            - message: Status message

    Raises:
        McpError: If repository validation fails or spec generation fails
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

        # Check if it's a git repository
        if not is_git_repo(str(repo_path)):
            raise McpError(
                code=-32602,
                message=f"Not a git repository: {repository_path}"
            )

        # Get repository root
        repo_root = get_repo_root(str(repo_path))
        if not repo_root:
            repo_root = str(repo_path)

        # Load configuration
        config_manager = ConfigurationManager(repo_root)
        config = config_manager.load_configuration()

        # Check if specify workflow is enabled
        workflow_config = config.workflows.get('specify')
        if not workflow_config or not workflow_config.enabled:
            raise McpError(
                code=-32603,  # Internal error
                message="Specify workflow is not enabled in configuration"
            )

        # Generate feature ID and branch name
        feature_id = _generate_feature_id()
        feature_slug = _slugify(description[:50])  # Use first 50 chars for slug

        # Use branch prefix from config or default
        branch_prefix = workflow_config.branch_prefix or "feature/"
        branch_name = f"{branch_prefix}{feature_id}-{feature_slug}"

        # Create feature branch
        branch_result = create_branch(repo_root, branch_name)
        if not branch_result.get('success'):
            raise McpError(
                code=-32603,
                message=f"Failed to create branch: {branch_result.get('message', 'Unknown error')}"
            )

        # Create specs directory
        specs_dir = Path(repo_root) / '.specify-mcp' / 'specs'
        ensure_directory(specs_dir)

        # Generate specification from template
        template_manager = TemplateManager()
        template = template_manager.get_template(TemplateType.SPEC)

        # Prepare variables for template substitution
        variables = {
            'feature_id': feature_id,
            'feature_name': description,
            'description': description,
            'repository_path': repo_root,
            'date': datetime.now().strftime('%Y-%m-%d')
        }

        # Substitute variables in template
        spec_content = template_manager.substitute_variables(template, variables)

        # Write specification file
        spec_filename = f"{feature_id}-spec.md"
        spec_path = specs_dir / spec_filename

        written_path = safe_write(
            spec_path,
            spec_content,
            base_path=repo_root,
            overwrite=False
        )

        # Add and commit the specification
        if config.settings.get('auto_commit', True):
            # Add the spec file to git
            add_result = add_files(
                repo_root,
                [str(written_path.relative_to(repo_root))]
            )

            if add_result.get('success'):
                # Commit the changes
                commit_message = f"feat: Add specification for {feature_id} - {feature_slug}"
                commit_result = commit(repo_root, commit_message)

                if not commit_result.get('success'):
                    # Log warning but don't fail the operation
                    print(f"Warning: Could not commit specification: {commit_result.get('message')}")

        return {
            'success': True,
            'branch_name': branch_name,
            'spec_path': str(written_path),
            'feature_id': feature_id,
            'message': f"Created specification for feature {feature_id} in branch {branch_name}"
        }

    except McpError:
        # Re-raise MCP errors as-is
        raise
    except Exception as e:
        # Wrap other exceptions in McpError
        raise McpError(
            code=-32603,  # Internal error
            message=f"Specification generation failed: {str(e)}",
            data={"error_type": type(e).__name__}
        )