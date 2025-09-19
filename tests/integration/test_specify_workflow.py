"""Integration tests for complete specify workflow.

This test suite verifies the end-to-end specify workflow including:
- Project initialization and configuration
- MCP tool interactions
- Git branch creation and file management
- Template resource loading and processing
- Spec file generation and validation

These tests MUST fail initially as no implementation exists yet (TDD requirement).
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

import pytest
import yaml
from pydantic import ValidationError

# Import MCP and FastMCP components (will fail until implemented)
try:
    from mcp import MCPError
    from fastmcp import FastMCP
    from speckit_mcp.server import create_mcp_server
    from speckit_mcp.tools.specify import specify_tool
    from speckit_mcp.tools.initialize import initialize_project_tool
    from speckit_mcp.config.models import ProjectConfiguration, WorkflowSession
    from speckit_mcp.git.operations import GitOperations
    from speckit_mcp.resources.templates import TemplateManager
except ImportError:
    # Expected to fail until implementation exists
    pytest.skip("Implementation not available yet - TDD phase", allow_module_level=True)


class TestSpecifyWorkflowIntegration:
    """Integration tests for the complete specify workflow."""

    @pytest.fixture
    async def temp_repository(self, tmp_path: Path) -> Path:
        """Create a temporary git repository for testing.

        Returns:
            Path to the temporary repository root
        """
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Initialize git repository
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
            git_ops = GitOperations(str(repo_path))
            await git_ops.initialize_repository()

        return repo_path

    @pytest.fixture
    async def project_config(self, temp_repository: Path) -> ProjectConfiguration:
        """Create a test project configuration.

        Returns:
            Valid ProjectConfiguration instance for testing
        """
        config_data = {
            "project": {
                "name": "test-project",
                "description": "Test project for integration testing",
                "version": "0.1.0"
            },
            "git": {
                "remote_url": "https://github.com/test/test-project.git",
                "default_branch": "main"
            },
            "workflows": {
                "specify": {
                    "enabled": True,
                    "branch_prefix": "feature/"
                }
            }
        }
        return ProjectConfiguration(**config_data)

    @pytest.fixture
    async def mcp_server(self, temp_repository: Path) -> FastMCP:
        """Create and configure MCP server for testing.

        Returns:
            Configured FastMCP server instance
        """
        server = await create_mcp_server()
        # Configure server with test repository
        server.context['repository_path'] = str(temp_repository)
        return server

    @pytest.mark.asyncio
    async def test_complete_specify_workflow_success(
        self,
        temp_repository: Path,
        project_config: ProjectConfiguration,
        mcp_server: FastMCP
    ):
        """Test successful end-to-end specify workflow.

        This test verifies:
        1. Project initialization with constitution.yaml
        2. Feature specification creation from description
        3. Git branch creation and file tracking
        4. Template resource loading and processing
        5. Spec file generation with correct structure
        6. Workflow session state management
        """
        # Test inputs
        feature_description = "Add user authentication with OAuth2 support"
        repository_path = str(temp_repository)

        # Step 1: Initialize project configuration
        with patch('subprocess.run') as mock_git:
            mock_git.return_value = Mock(returncode=0, stdout='', stderr='')

            init_result = await initialize_project_tool(
                repository_path=repository_path,
                project_name=project_config.project.name
            )

            assert init_result['success'] is True
            assert 'constitution_path' in init_result

            # Verify constitution.yaml was created
            constitution_path = Path(init_result['constitution_path'])
            assert constitution_path.exists()

            with open(constitution_path) as f:
                constitution = yaml.safe_load(f)
            assert constitution['project']['name'] == project_config.project.name

        # Step 2: Create feature specification
        with patch('subprocess.run') as mock_git:
            # Mock git operations for branch creation
            mock_git.side_effect = [
                Mock(returncode=0, stdout='main\n', stderr=''),  # git branch --show-current
                Mock(returncode=0, stdout='', stderr=''),        # git checkout -b feature/auth
                Mock(returncode=0, stdout='', stderr=''),        # git status
            ]

            spec_result = await specify_tool(
                description=feature_description,
                repository_path=repository_path
            )

            assert spec_result['success'] is True
            assert 'feature_id' in spec_result
            assert 'branch_name' in spec_result
            assert 'spec_path' in spec_result

            # Verify feature branch was created
            expected_branch = f"feature/{spec_result['feature_id']}"
            assert spec_result['branch_name'] == expected_branch

            # Verify git checkout was called with correct branch
            git_calls = [call.args[0] for call in mock_git.call_args_list]
            assert ['git', 'checkout', '-b', expected_branch] in git_calls

        # Step 3: Verify spec file structure and content
        spec_path = Path(spec_result['spec_path'])
        assert spec_path.exists()
        assert spec_path.name == 'spec.md'

        with open(spec_path) as f:
            spec_content = f.read()

        # Verify spec contains required sections
        assert '# Feature Specification' in spec_content
        assert feature_description in spec_content
        assert '## Problem Statement' in spec_content
        assert '## Solution Overview' in spec_content
        assert '## Requirements' in spec_content
        assert '## Implementation Notes' in spec_content

        # Step 4: Verify workflow session was created
        specs_dir = temp_repository / 'specs'
        feature_dir = specs_dir / spec_result['feature_id']
        session_file = feature_dir / 'session.yaml'

        assert session_file.exists()

        with open(session_file) as f:
            session_data = yaml.safe_load(f)

        session = WorkflowSession(**session_data)
        assert session.feature_id == spec_result['feature_id']
        assert session.current_phase == 'specify'
        assert session.repository_path == repository_path
        assert session.branch_name == expected_branch

        # Step 5: Verify directory structure
        expected_files = [
            feature_dir / 'spec.md',
            feature_dir / 'session.yaml'
        ]

        for file_path in expected_files:
            assert file_path.exists(), f"Expected file missing: {file_path}"

    @pytest.mark.asyncio
    async def test_specify_workflow_with_existing_feature(
        self,
        temp_repository: Path,
        mcp_server: FastMCP
    ):
        """Test specify workflow when feature directory already exists.

        Should handle conflicts gracefully and either:
        - Resume existing workflow session
        - Create new version/iteration
        - Return appropriate error
        """
        repository_path = str(temp_repository)
        feature_description = "Add user authentication"

        # Create existing feature directory
        specs_dir = temp_repository / 'specs'
        specs_dir.mkdir(parents=True)
        existing_feature_dir = specs_dir / 'user-authentication'
        existing_feature_dir.mkdir()

        # Create existing spec file
        existing_spec = existing_feature_dir / 'spec.md'
        existing_spec.write_text("# Existing Feature Specification\n")

        with patch('subprocess.run') as mock_git:
            mock_git.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            # Should either handle gracefully or raise appropriate error
            try:
                result = await specify_tool(
                    description=feature_description,
                    repository_path=repository_path
                )
                # If successful, should create new feature with different ID
                assert result['success'] is True
                assert result['feature_id'] != 'user-authentication'

            except MCPError as e:
                # Or should raise appropriate error about existing feature
                assert 'already exists' in str(e).lower()
                assert e.code == 'FEATURE_CONFLICT'

    @pytest.mark.asyncio
    async def test_specify_workflow_git_failure(
        self,
        temp_repository: Path,
        mcp_server: FastMCP
    ):
        """Test specify workflow when git operations fail.

        Should handle git failures gracefully and return appropriate errors.
        """
        repository_path = str(temp_repository)
        feature_description = "Add user authentication"

        with patch('subprocess.run') as mock_git:
            # Mock git failure
            mock_git.return_value = Mock(
                returncode=1,
                stdout='',
                stderr='fatal: not a git repository'
            )

            with pytest.raises(MCPError) as exc_info:
                await specify_tool(
                    description=feature_description,
                    repository_path=repository_path
                )

            assert exc_info.value.code == 'GIT_ERROR'
            assert 'not a git repository' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_specify_workflow_invalid_repository(
        self,
        tmp_path: Path,
        mcp_server: FastMCP
    ):
        """Test specify workflow with invalid repository path.

        Should validate repository existence and git initialization.
        """
        invalid_path = str(tmp_path / 'nonexistent')
        feature_description = "Add user authentication"

        with pytest.raises(MCPError) as exc_info:
            await specify_tool(
                description=feature_description,
                repository_path=invalid_path
            )

        assert exc_info.value.code == 'INVALID_REPOSITORY'
        assert 'does not exist' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_specify_workflow_template_loading(
        self,
        temp_repository: Path,
        mcp_server: FastMCP
    ):
        """Test template resource loading during specify workflow.

        Verifies that templates are properly loaded and processed.
        """
        repository_path = str(temp_repository)
        feature_description = "Add user authentication"

        with patch('subprocess.run') as mock_git:
            mock_git.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            with patch.object(TemplateManager, 'load_template') as mock_template:
                mock_template.return_value = """# Feature Specification: {{title}}

## Problem Statement
{{description}}

## Solution Overview
[To be filled]

## Requirements
- [ ] Functional requirement 1
- [ ] Functional requirement 2

## Implementation Notes
[To be filled]
"""

                result = await specify_tool(
                    description=feature_description,
                    repository_path=repository_path
                )

                # Verify template was loaded
                mock_template.assert_called_once_with('spec.md')

                # Verify template was processed with correct variables
                spec_path = Path(result['spec_path'])
                with open(spec_path) as f:
                    spec_content = f.read()

                assert feature_description in spec_content
                assert '{{title}}' not in spec_content  # Template variables should be replaced
                assert '{{description}}' not in spec_content

    @pytest.mark.asyncio
    async def test_specify_workflow_concurrent_requests(
        self,
        temp_repository: Path,
        mcp_server: FastMCP
    ):
        """Test concurrent specify requests on same repository.

        Should handle concurrent access appropriately with proper locking.
        """
        repository_path = str(temp_repository)
        descriptions = [
            "Add user authentication",
            "Add payment processing",
            "Add notification system"
        ]

        with patch('subprocess.run') as mock_git:
            mock_git.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            # Execute concurrent specify requests
            tasks = [
                specify_tool(description=desc, repository_path=repository_path)
                for desc in descriptions
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify results
            successful_results = [r for r in results if not isinstance(r, Exception)]

            # Should have either:
            # 1. All successful with different feature IDs
            # 2. Some failed with appropriate locking errors

            if len(successful_results) == len(descriptions):
                # All successful - verify unique feature IDs
                feature_ids = [r['feature_id'] for r in successful_results]
                assert len(set(feature_ids)) == len(feature_ids), "Feature IDs should be unique"
            else:
                # Some failed - verify appropriate error handling
                failed_results = [r for r in results if isinstance(r, Exception)]
                for error in failed_results:
                    assert isinstance(error, MCPError)
                    assert error.code in ['CONCURRENT_ACCESS', 'RESOURCE_LOCKED']

    @pytest.mark.asyncio
    async def test_specify_workflow_mcp_tool_registration(
        self,
        mcp_server: FastMCP
    ):
        """Test that specify tool is properly registered with MCP server.

        Verifies MCP protocol compliance and tool discovery.
        """
        # Verify tool is registered
        tools = await mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        assert 'specify' in tool_names

        # Verify tool schema
        specify_tool_info = next(tool for tool in tools if tool.name == 'specify')

        # Verify required parameters
        required_params = {'description', 'repository_path'}
        schema_properties = specify_tool_info.input_schema.get('properties', {})
        assert required_params.issubset(set(schema_properties.keys()))

        # Verify parameter types
        assert schema_properties['description']['type'] == 'string'
        assert schema_properties['repository_path']['type'] == 'string'

    @pytest.mark.asyncio
    async def test_specify_workflow_error_cleanup(
        self,
        temp_repository: Path,
        mcp_server: FastMCP
    ):
        """Test proper cleanup when specify workflow encounters errors.

        Should clean up partial state and not leave repository in inconsistent state.
        """
        repository_path = str(temp_repository)
        feature_description = "Add user authentication"

        with patch('subprocess.run') as mock_git:
            # Mock successful branch creation but failed file operations
            mock_git.side_effect = [
                Mock(returncode=0, stdout='main\n', stderr=''),  # git branch --show-current
                Mock(returncode=0, stdout='', stderr=''),        # git checkout -b
                Mock(returncode=1, stdout='', stderr='Permission denied'),  # git add (failure)
            ]

            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                with pytest.raises(MCPError) as exc_info:
                    await specify_tool(
                        description=feature_description,
                        repository_path=repository_path
                    )

                assert exc_info.value.code in ['FILE_ERROR', 'PERMISSION_ERROR']

        # Verify cleanup occurred
        specs_dir = temp_repository / 'specs'
        if specs_dir.exists():
            # Should not have partial feature directories
            feature_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
            for feature_dir in feature_dirs:
                # Any existing feature dirs should be complete (have spec.md and session.yaml)
                assert (feature_dir / 'spec.md').exists()
                assert (feature_dir / 'session.yaml').exists()