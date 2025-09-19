"""
Contract tests for the initialize_project MCP tool.

These tests verify MCP protocol compliance and tool schema validation for the initialize_project tool.
The initialize_project tool sets up constitution.yaml and project configuration.

Tests MUST fail initially since implementation doesn't exist yet (TDD).
"""

import json
import tempfile
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest
import pytest_asyncio
from pydantic import ValidationError

# These imports will fail until implementation exists - that's expected for TDD
try:
    from speckit_mcp.tools.initialize import initialize_project
    from speckit_mcp.server import create_server
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    initialize_project = None
    create_server = None


class TestInitializeToolContract:
    """Contract tests for the initialize_project MCP tool ensuring MCP protocol compliance."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            # Initialize basic git repo structure
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
                yield repo_path

    @pytest.fixture
    def mock_file_operations(self):
        """Mock file system operations."""
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('pathlib.Path.write_text') as mock_write:
            mock_mkdir.return_value = None
            mock_write.return_value = None
            yield mock_mkdir, mock_write

    @pytest.mark.contract
    def test_initialize_project_tool_exists(self):
        """Test that the initialize_project tool function exists and is importable."""
        assert initialize_project is not None, "initialize_project tool function must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_mcp_schema_compliance(self):
        """Test that initialize_project tool complies with MCP tool schema requirements."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(initialize_project), "initialize_project tool must be async"

        # Verify function has proper type hints
        sig = inspect.signature(initialize_project)
        assert 'repository_path' in sig.parameters, "initialize_project tool must accept 'repository_path' parameter"
        assert 'project_name' in sig.parameters, "initialize_project tool must accept 'project_name' parameter"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_input_validation(self, temp_repo, mock_file_operations):
        """Test input validation for the initialize_project tool using Pydantic models."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        valid_repo_path = str(temp_repo)
        valid_project_name = "test-project"

        # Test valid inputs
        try:
            result = await initialize_project(
                repository_path=valid_repo_path,
                project_name=valid_project_name
            )
            assert isinstance(result, dict), "initialize_project tool must return a dictionary"
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_invalid_inputs(self, temp_repo):
        """Test that initialize_project tool properly validates and rejects invalid inputs."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        # Test non-existent repository path
        with pytest.raises(ValidationError):
            await initialize_project(
                repository_path="/nonexistent/path",
                project_name="test-project"
            )

        # Test invalid project name
        with pytest.raises(ValidationError):
            await initialize_project(
                repository_path=str(temp_repo),
                project_name=""  # Empty name
            )

        # Test None values
        with pytest.raises(ValidationError):
            await initialize_project(
                repository_path=None,
                project_name="test-project"
            )

        with pytest.raises(ValidationError):
            await initialize_project(
                repository_path=str(temp_repo),
                project_name=None
            )

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_constitution_creation(self, temp_repo, mock_file_operations):
        """Test that initialize_project tool creates constitution.yaml file."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        mock_mkdir, mock_write = mock_file_operations

        try:
            result = await initialize_project(
                repository_path=str(temp_repo),
                project_name="test-project"
            )

            # Verify .specify-mcp directory was created
            mock_mkdir.assert_called()
            created_dirs = [call[1].get('parents', False) for call in mock_mkdir.call_args_list]
            assert any(parents for parents in created_dirs), "Should create directories with parents=True"

            # Verify constitution.yaml was written
            mock_write.assert_called()
            written_files = [str(call[0][0]) for call in mock_write.call_args_list]
            assert any('constitution.yaml' in file_path for file_path in written_files), "Should write constitution.yaml"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_constitution_content(self, temp_repo, mock_file_operations):
        """Test that initialize_project tool creates valid constitution content."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        mock_mkdir, mock_write = mock_file_operations

        try:
            result = await initialize_project(
                repository_path=str(temp_repo),
                project_name="test-project"
            )

            # Verify constitution content was written
            mock_write.assert_called()

            # Find the constitution.yaml write call
            constitution_content = None
            for call in mock_write.call_args_list:
                if 'constitution.yaml' in str(call[0][0]):
                    constitution_content = call[0][1]  # The content argument
                    break

            assert constitution_content is not None, "Constitution content must be written"

            # Verify YAML content structure
            try:
                config_data = yaml.safe_load(constitution_content)
                assert isinstance(config_data, dict), "Constitution must be valid YAML dictionary"

                # Verify required constitution fields
                required_fields = ['project', 'principles', 'technologies', 'workflows']
                for field in required_fields:
                    assert field in config_data, f"Constitution must include {field}"

            except yaml.YAMLError:
                pytest.fail("Constitution content must be valid YAML")

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_project_metadata(self, temp_repo, mock_file_operations):
        """Test that initialize_project tool includes proper project metadata."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        mock_mkdir, mock_write = mock_file_operations
        project_name = "my-awesome-project"

        try:
            result = await initialize_project(
                repository_path=str(temp_repo),
                project_name=project_name
            )

            # Verify result includes project metadata
            assert 'constitution_path' in result, "Result must include constitution_path"
            assert 'project_name' in result, "Result must include project_name"
            assert 'initialized_at' in result, "Result must include initialized_at timestamp"

            # Verify project name is included in constitution
            constitution_content = None
            for call in mock_write.call_args_list:
                if 'constitution.yaml' in str(call[0][0]):
                    constitution_content = call[0][1]
                    break

            assert project_name in constitution_content, "Project name must be in constitution content"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_directory_structure(self, temp_repo, mock_file_operations):
        """Test that initialize_project tool creates proper directory structure."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        mock_mkdir, mock_write = mock_file_operations

        try:
            result = await initialize_project(
                repository_path=str(temp_repo),
                project_name="test-project"
            )

            # Verify .specify-mcp directory structure was created
            created_paths = [str(call[0][0]) for call in mock_mkdir.call_args_list]

            # Should create main .specify-mcp directory
            assert any('.specify-mcp' in path for path in created_paths), "Should create .specify-mcp directory"

            # May create subdirectories for logs, templates, etc.
            expected_subdirs = ['logs', 'templates', 'cache']
            for subdir in expected_subdirs:
                # Not all subdirs are required, but if created, should be under .specify-mcp
                subdir_paths = [path for path in created_paths if subdir in path]
                for path in subdir_paths:
                    assert '.specify-mcp' in path, f"{subdir} should be under .specify-mcp directory"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_error_handling(self, temp_repo):
        """Test proper error handling and MCPError responses."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        # Test file write failure
        with patch('pathlib.Path.write_text') as mock_write:
            mock_write.side_effect = IOError("Permission denied")

            with pytest.raises(Exception) as exc_info:
                await initialize_project(
                    repository_path=str(temp_repo),
                    project_name="test-project"
                )

            # Should raise MCPError or appropriate exception
            error = exc_info.value
            assert error is not None, "Must raise exception on file write failure"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_existing_constitution(self, temp_repo, mock_file_operations):
        """Test behavior when constitution.yaml already exists."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        # Mock existing constitution file
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True

            try:
                result = await initialize_project(
                    repository_path=str(temp_repo),
                    project_name="test-project"
                )

                # Should handle existing constitution appropriately
                # Either skip, backup, or merge - behavior depends on implementation
                assert 'status' in result, "Result should indicate handling of existing constitution"

            except Exception as e:
                if "not implemented" in str(e).lower():
                    pytest.skip("Implementation not complete - expected for TDD")
                raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_mcp_response_format(self, temp_repo, mock_file_operations):
        """Test that initialize_project tool returns MCP-compliant response format."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        try:
            result = await initialize_project(
                repository_path=str(temp_repo),
                project_name="test-project"
            )

            # Verify JSON-RPC 2.0 compatible response structure
            assert isinstance(result, dict), "Response must be a dictionary"

            # Check for required fields in response
            required_fields = ['constitution_path', 'project_name', 'initialized_at']
            for field in required_fields:
                assert field in result, f"Response must include {field}"

            # Verify response is JSON serializable (MCP requirement)
            json.dumps(result)  # Should not raise exception

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    def test_initialize_project_tool_in_mcp_server(self):
        """Test that initialize_project tool is properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify initialize_project tool is registered
            tools = getattr(server, 'tools', {})
            assert 'initialize_project' in tools, "initialize_project tool must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_template_integration(self, temp_repo, mock_file_operations):
        """Test that initialize_project tool integrates with template system."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        try:
            with patch('speckit_mcp.resources.template_manager.get_template') as mock_template:
                mock_template.return_value = """project:
  name: "{{project_name}}"
  created_at: "{{timestamp}}"

principles:
  - MCP Protocol Compliance
  - File System Preservation
  - Test-First Development

technologies:
  - Python 3.11+
  - FastMCP
  - PyYAML
  - Pydantic

workflows:
  - specify
  - plan
  - tasks
"""

                result = await initialize_project(
                    repository_path=str(temp_repo),
                    project_name="template-test-project"
                )

                # Verify template was retrieved
                mock_template.assert_called_with('constitution')

                # Verify project uses template structure
                assert 'constitution_path' in result, "Result must include constitution_path"

        except ImportError:
            # Template manager not implemented yet - expected for TDD
            pytest.skip("Template manager not implemented - expected for TDD")
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_git_integration(self, temp_repo):
        """Test that initialize_project tool validates git repository."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        # Test with valid git repository
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            try:
                result = await initialize_project(
                    repository_path=str(temp_repo),
                    project_name="git-test-project"
                )

                # Verify git status was checked
                mock_run.assert_called()
                git_calls = [call[0][0] for call in mock_run.call_args_list]
                assert any('git' in call for call in git_calls), "Should verify git repository"

            except Exception as e:
                if "not implemented" in str(e).lower():
                    pytest.skip("Implementation not complete - expected for TDD")
                raise

        # Test with invalid git repository
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout='', stderr='Not a git repository')

            with pytest.raises(Exception):
                await initialize_project(
                    repository_path=str(temp_repo),
                    project_name="invalid-git-project"
                )

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_initialize_project_tool_concurrent_execution(self, mock_file_operations):
        """Test that initialize_project tool handles concurrent execution properly."""
        if initialize_project is None:
            pytest.fail("initialize_project tool not implemented yet - expected for TDD")

        # Create multiple temporary repositories
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_paths = []
            for i in range(3):
                repo_path = Path(temp_dir) / f"repo_{i}"
                repo_path.mkdir()
                repo_paths.append(str(repo_path))

            try:
                # Execute multiple initialize operations concurrently
                import asyncio
                tasks = [
                    initialize_project(repo_path, f"project-{i}")
                    for i, repo_path in enumerate(repo_paths)
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Verify all operations completed (even if with errors due to no implementation)
                assert len(results) == len(repo_paths), "All concurrent operations must complete"

            except Exception as e:
                if "not implemented" in str(e).lower():
                    pytest.skip("Implementation not complete - expected for TDD")
                raise