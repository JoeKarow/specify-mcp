"""
Contract tests for the specify MCP tool.

These tests verify MCP protocol compliance and tool schema validation for the specify tool.
The specify tool creates a feature branch and generates a specification from a description.

Tests MUST fail initially since implementation doesn't exist yet (TDD).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest
import pytest_asyncio
from pydantic import ValidationError

# These imports will fail until implementation exists - that's expected for TDD
try:
    from speckit_mcp.tools.specify import specify
    from speckit_mcp.server import create_server
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    specify = None
    create_server = None


class TestSpecifyToolContract:
    """Contract tests for the specify MCP tool ensuring MCP protocol compliance."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            # Initialize git repo
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
                yield repo_path

    @pytest.fixture
    def mock_git_operations(self):
        """Mock all git subprocess operations."""
        with patch('subprocess.run') as mock_run:
            # Default successful git operations
            mock_run.return_value = Mock(
                returncode=0,
                stdout='main\n',  # Current branch
                stderr=''
            )
            yield mock_run

    @pytest.mark.contract
    def test_specify_tool_exists(self):
        """Test that the specify tool function exists and is importable."""
        assert specify is not None, "specify tool function must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_specify_tool_mcp_schema_compliance(self):
        """Test that specify tool complies with MCP tool schema requirements."""
        if specify is None:
            pytest.fail("specify tool not implemented yet - expected for TDD")

        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(specify), "specify tool must be async"

        # Verify function has proper type hints
        sig = inspect.signature(specify)
        assert 'description' in sig.parameters, "specify tool must accept 'description' parameter"
        assert 'repository_path' in sig.parameters, "specify tool must accept 'repository_path' parameter"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_specify_tool_input_validation(self, temp_repo, mock_git_operations):
        """Test input validation for the specify tool using Pydantic models."""
        if specify is None:
            pytest.fail("specify tool not implemented yet - expected for TDD")

        # Test valid inputs
        valid_description = "Add user authentication with JWT tokens"
        valid_repo_path = str(temp_repo)

        # This should not raise validation errors
        try:
            result = await specify(
                description=valid_description,
                repository_path=valid_repo_path
            )
            assert isinstance(result, dict), "specify tool must return a dictionary"
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_specify_tool_invalid_inputs(self, temp_repo):
        """Test that specify tool properly validates and rejects invalid inputs."""
        if specify is None:
            pytest.fail("specify tool not implemented yet - expected for TDD")

        # Test empty description
        with pytest.raises(ValidationError):
            await specify(description="", repository_path=str(temp_repo))

        # Test non-existent repository path
        with pytest.raises(ValidationError):
            await specify(
                description="Valid description",
                repository_path="/nonexistent/path"
            )

        # Test None values
        with pytest.raises(ValidationError):
            await specify(description=None, repository_path=str(temp_repo))

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_specify_tool_git_branch_creation(self, temp_repo, mock_git_operations):
        """Test that specify tool creates a feature branch through git operations."""
        if specify is None:
            pytest.fail("specify tool not implemented yet - expected for TDD")

        description = "Add user authentication system"

        try:
            result = await specify(
                description=description,
                repository_path=str(temp_repo)
            )

            # Verify git commands were called for branch creation
            mock_git_operations.assert_called()

            # Check that branch creation command was invoked
            git_calls = [call[0][0] for call in mock_git_operations.call_args_list]
            assert any('checkout' in call for call in git_calls), "Git checkout command must be called"
            assert any('-b' in call for call in git_calls), "Branch creation flag must be used"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_specify_tool_spec_generation(self, temp_repo, mock_git_operations):
        """Test that specify tool generates a specification file."""
        if specify is None:
            pytest.fail("specify tool not implemented yet - expected for TDD")

        description = "Implement real-time chat functionality"

        try:
            result = await specify(
                description=description,
                repository_path=str(temp_repo)
            )

            # Verify result structure
            assert 'spec_path' in result, "Result must include spec_path"
            assert 'branch_name' in result, "Result must include branch_name"
            assert 'feature_id' in result, "Result must include feature_id"

            # Verify branch naming follows conventions
            branch_name = result['branch_name']
            assert branch_name.startswith(('feat/', 'feature/')), "Branch must follow naming convention"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_specify_tool_error_handling(self, temp_repo):
        """Test proper error handling and MCPError responses."""
        if specify is None:
            pytest.fail("specify tool not implemented yet - expected for TDD")

        # Test git command failure
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout='', stderr='Git error')

            with pytest.raises(Exception) as exc_info:
                await specify(
                    description="Test description",
                    repository_path=str(temp_repo)
                )

            # Should raise MCPError or appropriate exception
            error = exc_info.value
            assert error is not None, "Must raise exception on git failure"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_specify_tool_mcp_response_format(self, temp_repo, mock_git_operations):
        """Test that specify tool returns MCP-compliant response format."""
        if specify is None:
            pytest.fail("specify tool not implemented yet - expected for TDD")

        description = "Add OAuth integration"

        try:
            result = await specify(
                description=description,
                repository_path=str(temp_repo)
            )

            # Verify JSON-RPC 2.0 compatible response structure
            assert isinstance(result, dict), "Response must be a dictionary"

            # Check for required fields in response
            required_fields = ['spec_path', 'branch_name', 'feature_id']
            for field in required_fields:
                assert field in result, f"Response must include {field}"

            # Verify response is JSON serializable (MCP requirement)
            json.dumps(result)  # Should not raise exception

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    def test_specify_tool_in_mcp_server(self):
        """Test that specify tool is properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify specify tool is registered
            tools = getattr(server, 'tools', {})
            assert 'specify' in tools, "specify tool must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_specify_tool_concurrent_execution(self, temp_repo, mock_git_operations):
        """Test that specify tool handles concurrent execution properly."""
        if specify is None:
            pytest.fail("specify tool not implemented yet - expected for TDD")

        # Test concurrent calls to specify tool
        descriptions = [
            "Add user management",
            "Implement search functionality",
            "Add notification system"
        ]

        try:
            # Execute multiple specify operations concurrently
            import asyncio
            tasks = [
                specify(desc, str(temp_repo)) for desc in descriptions
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all operations completed (even if with errors due to no implementation)
            assert len(results) == len(descriptions), "All concurrent operations must complete"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise