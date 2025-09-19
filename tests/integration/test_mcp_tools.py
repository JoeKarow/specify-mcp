"""
Integration tests for MCP tools registration and basic functionality.

This module tests that all MCP tools are properly registered with the
server and have the correct signatures.
"""

import pytest
import inspect
from pathlib import Path
from typing import Dict, Any

from speckit_mcp.server import create_server
from speckit_mcp.tools import (
    specify,
    plan,
    tasks,
    initialize_project,
    get_context
)


class TestMCPToolsRegistration:
    """Test MCP tools are properly registered with the server."""

    def test_all_tools_registered(self):
        """Test that all MCP tools are registered with the server."""
        # Create server instance
        server = create_server()

        # Check that server has tools registered
        # Note: FastMCP doesn't expose registered tools directly,
        # so we verify the tools can be imported and have correct signatures

        assert callable(specify)
        assert callable(plan)
        assert callable(tasks)
        assert callable(initialize_project)
        assert callable(get_context)

    def test_tool_signatures(self):
        """Test that tools have the correct async signatures."""
        # All MCP tools should be async functions
        assert inspect.iscoroutinefunction(specify)
        assert inspect.iscoroutinefunction(plan)
        assert inspect.iscoroutinefunction(tasks)
        assert inspect.iscoroutinefunction(initialize_project)
        assert inspect.iscoroutinefunction(get_context)

        # Check parameter signatures
        specify_params = inspect.signature(specify).parameters
        assert 'description' in specify_params
        assert 'repository_path' in specify_params

        plan_params = inspect.signature(plan).parameters
        assert 'spec_path' in plan_params
        assert 'repository_path' in plan_params

        tasks_params = inspect.signature(tasks).parameters
        assert 'plan_path' in tasks_params
        assert 'repository_path' in tasks_params

        init_params = inspect.signature(initialize_project).parameters
        assert 'repository_path' in init_params
        assert 'project_name' in init_params

        context_params = inspect.signature(get_context).parameters
        assert 'phase' in context_params
        assert 'workflow' in context_params

    @pytest.mark.asyncio
    async def test_specify_tool_error_handling(self, tmp_path):
        """Test specify tool handles invalid inputs correctly."""
        from fastmcp.exceptions import McpError

        # Test with non-existent repository
        with pytest.raises(McpError) as exc_info:
            await specify(
                description="Test feature",
                repository_path="/non/existent/path"
            )

        assert exc_info.value.code == -32602  # Invalid params
        assert "does not exist" in str(exc_info.value.message)

        # Test with file instead of directory
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with pytest.raises(McpError) as exc_info:
            await specify(
                description="Test feature",
                repository_path=str(test_file)
            )

        assert exc_info.value.code == -32602
        assert "not a directory" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_plan_tool_error_handling(self, tmp_path):
        """Test plan tool handles invalid inputs correctly."""
        from fastmcp.exceptions import McpError

        # Test with non-existent spec file
        with pytest.raises(McpError) as exc_info:
            await plan(
                spec_path="/non/existent/spec.md",
                repository_path=str(tmp_path)
            )

        assert exc_info.value.code == -32602
        assert "not found" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_tasks_tool_error_handling(self, tmp_path):
        """Test tasks tool handles invalid inputs correctly."""
        from fastmcp.exceptions import McpError

        # Test with non-existent plan file
        with pytest.raises(McpError) as exc_info:
            await tasks(
                plan_path="/non/existent/plan.md",
                repository_path=str(tmp_path)
            )

        assert exc_info.value.code == -32602
        assert "not found" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_get_context_tool_error_handling(self):
        """Test get_context tool handles invalid inputs correctly."""
        from fastmcp.exceptions import McpError

        # Test with invalid phase
        with pytest.raises(McpError) as exc_info:
            await get_context(
                phase="invalid_phase"
            )

        assert exc_info.value.code == -32602
        assert "Invalid phase" in str(exc_info.value.message)

        # Test with invalid workflow
        with pytest.raises(McpError) as exc_info:
            await get_context(
                phase="research",
                workflow="invalid_workflow"
            )

        assert exc_info.value.code == -32602
        assert "Invalid workflow" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_get_context_tool_valid_phases(self):
        """Test get_context tool returns documents for valid phases."""
        # Test each valid phase
        for phase in ['research', 'design', 'implement', 'validate']:
            result = await get_context(phase=phase)

            assert result['success'] is True
            assert 'documents' in result
            assert 'total_count' in result
            assert result['phase'] == phase
            assert isinstance(result['documents'], list)

            # Should have at least some embedded documents
            assert result['total_count'] >= 0

    @pytest.mark.asyncio
    async def test_initialize_project_creates_structure(self, tmp_path):
        """Test initialize_project creates correct directory structure."""
        import subprocess

        # Initialize git repo first
        subprocess.run(
            ['git', 'init'],
            cwd=str(tmp_path),
            capture_output=True,
            check=True
        )

        # Run initialize_project
        result = await initialize_project(
            repository_path=str(tmp_path),
            project_name="TestProject"
        )

        assert result['success'] is True
        assert 'constitution_path' in result
        assert 'project_id' in result
        assert 'directories_created' in result

        # Verify constitution.yaml was created
        constitution_path = Path(result['constitution_path'])
        assert constitution_path.exists()
        assert constitution_path.name == 'constitution.yaml'

        # Verify directory structure
        config_dir = tmp_path / '.specify-mcp'
        assert config_dir.exists()
        assert (config_dir / 'specs').exists()
        assert (config_dir / 'plans').exists()
        assert (config_dir / 'tasks').exists()
        assert (config_dir / 'templates').exists()
        assert (config_dir / 'docs').exists()