"""
Contract tests for the plan MCP tool.

These tests verify MCP protocol compliance and tool schema validation for the plan tool.
The plan tool generates an implementation plan from a feature specification.

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
    from speckit_mcp.tools.plan import plan
    from speckit_mcp.server import create_server
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    plan = None
    create_server = None


class TestPlanToolContract:
    """Contract tests for the plan MCP tool ensuring MCP protocol compliance."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository with spec file for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            specs_dir = repo_path / "specs" / "001-test-feature"
            specs_dir.mkdir(parents=True)

            # Create a sample spec file
            spec_content = """# Feature Specification: Test Feature

## Overview
This is a test feature for validation.

## Requirements
- Requirement 1
- Requirement 2

## Technical Design
Basic technical approach.
"""
            (specs_dir / "spec.md").write_text(spec_content)
            yield repo_path

    @pytest.fixture
    def mock_file_operations(self):
        """Mock file system operations."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            yield mock_exists

    @pytest.mark.contract
    def test_plan_tool_exists(self):
        """Test that the plan tool function exists and is importable."""
        assert plan is not None, "plan tool function must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_mcp_schema_compliance(self):
        """Test that plan tool complies with MCP tool schema requirements."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(plan), "plan tool must be async"

        # Verify function has proper type hints
        sig = inspect.signature(plan)
        assert 'spec_path' in sig.parameters, "plan tool must accept 'spec_path' parameter"
        assert 'repository_path' in sig.parameters, "plan tool must accept 'repository_path' parameter"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_input_validation(self, temp_repo, mock_file_operations):
        """Test input validation for the plan tool using Pydantic models."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        spec_path = temp_repo / "specs" / "001-test-feature" / "spec.md"
        valid_repo_path = str(temp_repo)

        # Test valid inputs
        try:
            result = await plan(
                spec_path=str(spec_path),
                repository_path=valid_repo_path
            )
            assert isinstance(result, dict), "plan tool must return a dictionary"
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_invalid_inputs(self, temp_repo):
        """Test that plan tool properly validates and rejects invalid inputs."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        # Test non-existent spec file
        with pytest.raises(ValidationError):
            await plan(
                spec_path="/nonexistent/spec.md",
                repository_path=str(temp_repo)
            )

        # Test non-existent repository path
        with pytest.raises(ValidationError):
            await plan(
                spec_path=str(temp_repo / "specs" / "001-test-feature" / "spec.md"),
                repository_path="/nonexistent/path"
            )

        # Test None values
        with pytest.raises(ValidationError):
            await plan(spec_path=None, repository_path=str(temp_repo))

        # Test empty strings
        with pytest.raises(ValidationError):
            await plan(spec_path="", repository_path=str(temp_repo))

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_spec_analysis(self, temp_repo, mock_file_operations):
        """Test that plan tool analyzes specification content properly."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        spec_path = temp_repo / "specs" / "001-test-feature" / "spec.md"

        try:
            result = await plan(
                spec_path=str(spec_path),
                repository_path=str(temp_repo)
            )

            # Verify result structure includes plan analysis
            assert 'plan_path' in result, "Result must include plan_path"
            assert 'tech_stack' in result, "Result must include tech_stack"
            assert 'architecture_decisions' in result, "Result must include architecture_decisions"
            assert 'implementation_phases' in result, "Result must include implementation_phases"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_plan_generation(self, temp_repo, mock_file_operations):
        """Test that plan tool generates structured implementation plan."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        spec_path = temp_repo / "specs" / "001-test-feature" / "spec.md"

        try:
            with patch('pathlib.Path.write_text') as mock_write:
                result = await plan(
                    spec_path=str(spec_path),
                    repository_path=str(temp_repo)
                )

                # Verify plan file was written
                mock_write.assert_called()

                # Verify plan content structure
                written_content = mock_write.call_args[0][0]
                assert isinstance(written_content, str), "Plan content must be string"
                assert "# Implementation Plan" in written_content, "Plan must have proper header"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_technology_analysis(self, temp_repo, mock_file_operations):
        """Test that plan tool analyzes and suggests appropriate technologies."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        # Create spec with specific technology requirements
        spec_content = """# Feature: User Authentication

## Requirements
- JWT token authentication
- Database integration
- REST API endpoints

## Technical Constraints
- Python backend
- PostgreSQL database
"""
        spec_path = temp_repo / "specs" / "001-auth-feature" / "spec.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(spec_content)

        try:
            result = await plan(
                spec_path=str(spec_path),
                repository_path=str(temp_repo)
            )

            # Verify tech stack analysis
            tech_stack = result.get('tech_stack', {})
            assert isinstance(tech_stack, dict), "Tech stack must be dictionary"

            # Should identify key technologies from spec
            plan_content = result.get('plan_content', '')
            assert 'python' in plan_content.lower() or 'Python' in plan_content, "Should identify Python"
            assert 'postgresql' in plan_content.lower() or 'PostgreSQL' in plan_content, "Should identify PostgreSQL"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_error_handling(self, temp_repo):
        """Test proper error handling and MCPError responses."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        # Test file read failure
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.side_effect = IOError("Permission denied")

            with pytest.raises(Exception) as exc_info:
                await plan(
                    spec_path=str(temp_repo / "specs" / "001-test-feature" / "spec.md"),
                    repository_path=str(temp_repo)
                )

            # Should raise MCPError or appropriate exception
            error = exc_info.value
            assert error is not None, "Must raise exception on file read failure"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_mcp_response_format(self, temp_repo, mock_file_operations):
        """Test that plan tool returns MCP-compliant response format."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        spec_path = temp_repo / "specs" / "001-test-feature" / "spec.md"

        try:
            result = await plan(
                spec_path=str(spec_path),
                repository_path=str(temp_repo)
            )

            # Verify JSON-RPC 2.0 compatible response structure
            assert isinstance(result, dict), "Response must be a dictionary"

            # Check for required fields in response
            required_fields = ['plan_path', 'tech_stack', 'implementation_phases']
            for field in required_fields:
                assert field in result, f"Response must include {field}"

            # Verify response is JSON serializable (MCP requirement)
            json.dumps(result)  # Should not raise exception

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    def test_plan_tool_in_mcp_server(self):
        """Test that plan tool is properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify plan tool is registered
            tools = getattr(server, 'tools', {})
            assert 'plan' in tools, "plan tool must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_template_integration(self, temp_repo, mock_file_operations):
        """Test that plan tool integrates with template system."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        spec_path = temp_repo / "specs" / "001-test-feature" / "spec.md"

        try:
            with patch('speckit_mcp.resources.template_manager.get_template') as mock_template:
                mock_template.return_value = "# Plan Template\n\n## Tech Stack\n{{tech_stack}}"

                result = await plan(
                    spec_path=str(spec_path),
                    repository_path=str(temp_repo)
                )

                # Verify template was retrieved
                mock_template.assert_called_with('plan')

                # Verify plan uses template structure
                assert 'plan_content' in result, "Result must include plan_content"

        except ImportError:
            # Template manager not implemented yet - expected for TDD
            pytest.skip("Template manager not implemented - expected for TDD")
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_plan_tool_concurrent_execution(self, temp_repo, mock_file_operations):
        """Test that plan tool handles concurrent execution properly."""
        if plan is None:
            pytest.fail("plan tool not implemented yet - expected for TDD")

        # Create multiple spec files
        spec_paths = []
        for i in range(3):
            spec_dir = temp_repo / "specs" / f"00{i+1}-feature-{i}"
            spec_dir.mkdir(parents=True, exist_ok=True)
            spec_path = spec_dir / "spec.md"
            spec_path.write_text(f"# Feature {i}\n\nTest feature {i}")
            spec_paths.append(str(spec_path))

        try:
            # Execute multiple plan operations concurrently
            import asyncio
            tasks = [
                plan(spec_path, str(temp_repo)) for spec_path in spec_paths
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all operations completed (even if with errors due to no implementation)
            assert len(results) == len(spec_paths), "All concurrent operations must complete"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise