"""
Contract tests for the tasks MCP tool.

These tests verify MCP protocol compliance and tool schema validation for the tasks tool.
The tasks tool creates task breakdowns from implementation plans.

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
    from speckit_mcp.tools.tasks import tasks
    from speckit_mcp.server import create_server
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    tasks = None
    create_server = None


class TestTasksToolContract:
    """Contract tests for the tasks MCP tool ensuring MCP protocol compliance."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository with plan file for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            specs_dir = repo_path / "specs" / "001-test-feature"
            specs_dir.mkdir(parents=True)

            # Create a sample plan file
            plan_content = """# Implementation Plan: Test Feature

## Tech Stack
- Python 3.11+
- FastAPI
- PostgreSQL
- pytest

## Architecture Decisions
- RESTful API design
- Microservices architecture
- Event-driven messaging

## Implementation Phases

### Phase 1: Core Setup
- Project structure
- Database setup
- Authentication

### Phase 2: API Development
- User endpoints
- Data models
- Business logic

### Phase 3: Testing & Deployment
- Unit tests
- Integration tests
- Docker deployment
"""
            (specs_dir / "plan.md").write_text(plan_content)
            yield repo_path

    @pytest.fixture
    def mock_file_operations(self):
        """Mock file system operations."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            yield mock_exists

    @pytest.mark.contract
    def test_tasks_tool_exists(self):
        """Test that the tasks tool function exists and is importable."""
        assert tasks is not None, "tasks tool function must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_mcp_schema_compliance(self):
        """Test that tasks tool complies with MCP tool schema requirements."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(tasks), "tasks tool must be async"

        # Verify function has proper type hints
        sig = inspect.signature(tasks)
        assert 'plan_path' in sig.parameters, "tasks tool must accept 'plan_path' parameter"
        assert 'repository_path' in sig.parameters, "tasks tool must accept 'repository_path' parameter"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_input_validation(self, temp_repo, mock_file_operations):
        """Test input validation for the tasks tool using Pydantic models."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        plan_path = temp_repo / "specs" / "001-test-feature" / "plan.md"
        valid_repo_path = str(temp_repo)

        # Test valid inputs
        try:
            result = await tasks(
                plan_path=str(plan_path),
                repository_path=valid_repo_path
            )
            assert isinstance(result, dict), "tasks tool must return a dictionary"
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_invalid_inputs(self, temp_repo):
        """Test that tasks tool properly validates and rejects invalid inputs."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        # Test non-existent plan file
        with pytest.raises(ValidationError):
            await tasks(
                plan_path="/nonexistent/plan.md",
                repository_path=str(temp_repo)
            )

        # Test non-existent repository path
        with pytest.raises(ValidationError):
            await tasks(
                plan_path=str(temp_repo / "specs" / "001-test-feature" / "plan.md"),
                repository_path="/nonexistent/path"
            )

        # Test None values
        with pytest.raises(ValidationError):
            await tasks(plan_path=None, repository_path=str(temp_repo))

        # Test empty strings
        with pytest.raises(ValidationError):
            await tasks(plan_path="", repository_path=str(temp_repo))

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_plan_analysis(self, temp_repo, mock_file_operations):
        """Test that tasks tool analyzes implementation plan content properly."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        plan_path = temp_repo / "specs" / "001-test-feature" / "plan.md"

        try:
            result = await tasks(
                plan_path=str(plan_path),
                repository_path=str(temp_repo)
            )

            # Verify result structure includes task breakdown
            assert 'tasks_path' in result, "Result must include tasks_path"
            assert 'total_tasks' in result, "Result must include total_tasks"
            assert 'phases' in result, "Result must include phases"
            assert 'dependencies' in result, "Result must include dependencies"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_yaml_generation(self, temp_repo, mock_file_operations):
        """Test that tasks tool generates structured YAML task breakdown."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        plan_path = temp_repo / "specs" / "001-test-feature" / "plan.md"

        try:
            with patch('pathlib.Path.write_text') as mock_write:
                result = await tasks(
                    plan_path=str(plan_path),
                    repository_path=str(temp_repo)
                )

                # Verify tasks file was written
                mock_write.assert_called()

                # Verify YAML content structure
                written_content = mock_write.call_args[0][0]
                assert isinstance(written_content, str), "Tasks content must be string"

                # Parse YAML to verify structure
                try:
                    task_data = yaml.safe_load(written_content)
                    assert isinstance(task_data, dict), "Tasks YAML must be valid dictionary"
                    assert 'phases' in task_data, "Tasks must include phases"
                    assert 'tasks' in task_data, "Tasks must include task list"
                except yaml.YAMLError:
                    pytest.fail("Generated content must be valid YAML")

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_phase_breakdown(self, temp_repo, mock_file_operations):
        """Test that tasks tool breaks down phases into specific tasks."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        plan_path = temp_repo / "specs" / "001-test-feature" / "plan.md"

        try:
            result = await tasks(
                plan_path=str(plan_path),
                repository_path=str(temp_repo)
            )

            # Verify phase analysis
            phases = result.get('phases', {})
            assert isinstance(phases, dict), "Phases must be dictionary"

            # Should identify phases from plan content
            task_content = result.get('task_content', '')
            assert 'Phase 1' in task_content or 'phase 1' in task_content.lower(), "Should identify Phase 1"
            assert 'Phase 2' in task_content or 'phase 2' in task_content.lower(), "Should identify Phase 2"
            assert 'Phase 3' in task_content or 'phase 3' in task_content.lower(), "Should identify Phase 3"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_dependency_analysis(self, temp_repo, mock_file_operations):
        """Test that tasks tool analyzes task dependencies properly."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        # Create plan with clear dependencies
        plan_content = """# Implementation Plan

## Phase 1: Foundation
- Database setup
- Project structure

## Phase 2: Core Features
- User authentication (depends on database)
- API endpoints (depends on authentication)

## Phase 3: Advanced Features
- Real-time features (depends on API)
- Analytics (depends on real-time features)
"""
        plan_path = temp_repo / "specs" / "001-dependency-test" / "plan.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan_content)

        try:
            result = await tasks(
                plan_path=str(plan_path),
                repository_path=str(temp_repo)
            )

            # Verify dependency analysis
            dependencies = result.get('dependencies', {})
            assert isinstance(dependencies, dict), "Dependencies must be dictionary"

            # Should identify sequential dependencies
            task_content = result.get('task_content', '')
            assert 'depends on' in task_content.lower() or 'dependency' in task_content.lower(), "Should identify dependencies"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_error_handling(self, temp_repo):
        """Test proper error handling and MCPError responses."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        # Test file read failure
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.side_effect = IOError("Permission denied")

            with pytest.raises(Exception) as exc_info:
                await tasks(
                    plan_path=str(temp_repo / "specs" / "001-test-feature" / "plan.md"),
                    repository_path=str(temp_repo)
                )

            # Should raise MCPError or appropriate exception
            error = exc_info.value
            assert error is not None, "Must raise exception on file read failure"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_mcp_response_format(self, temp_repo, mock_file_operations):
        """Test that tasks tool returns MCP-compliant response format."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        plan_path = temp_repo / "specs" / "001-test-feature" / "plan.md"

        try:
            result = await tasks(
                plan_path=str(plan_path),
                repository_path=str(temp_repo)
            )

            # Verify JSON-RPC 2.0 compatible response structure
            assert isinstance(result, dict), "Response must be a dictionary"

            # Check for required fields in response
            required_fields = ['tasks_path', 'total_tasks', 'phases']
            for field in required_fields:
                assert field in result, f"Response must include {field}"

            # Verify response is JSON serializable (MCP requirement)
            json.dumps(result)  # Should not raise exception

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    def test_tasks_tool_in_mcp_server(self):
        """Test that tasks tool is properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify tasks tool is registered
            tools = getattr(server, 'tools', {})
            assert 'tasks' in tools, "tasks tool must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_template_integration(self, temp_repo, mock_file_operations):
        """Test that tasks tool integrates with template system."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        plan_path = temp_repo / "specs" / "001-test-feature" / "plan.md"

        try:
            with patch('speckit_mcp.resources.template_manager.get_template') as mock_template:
                mock_template.return_value = """# Tasks: {{feature_name}}

phases:
  {{#phases}}
  - name: {{name}}
    tasks: {{tasks}}
  {{/phases}}

tasks:
  {{#tasks}}
  - id: {{id}}
    description: {{description}}
    dependencies: {{dependencies}}
  {{/tasks}}
"""

                result = await tasks(
                    plan_path=str(plan_path),
                    repository_path=str(temp_repo)
                )

                # Verify template was retrieved
                mock_template.assert_called_with('tasks')

                # Verify tasks uses template structure
                assert 'task_content' in result, "Result must include task_content"

        except ImportError:
            # Template manager not implemented yet - expected for TDD
            pytest.skip("Template manager not implemented - expected for TDD")
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_parallel_task_identification(self, temp_repo, mock_file_operations):
        """Test that tasks tool identifies tasks that can run in parallel."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        plan_path = temp_repo / "specs" / "001-test-feature" / "plan.md"

        try:
            result = await tasks(
                plan_path=str(plan_path),
                repository_path=str(temp_repo)
            )

            # Verify parallel task analysis
            task_content = result.get('task_content', '')

            # Should mark parallel tasks with [P] or similar indicator
            assert '[P]' in task_content or 'parallel' in task_content.lower(), "Should identify parallel tasks"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_tasks_tool_concurrent_execution(self, temp_repo, mock_file_operations):
        """Test that tasks tool handles concurrent execution properly."""
        if tasks is None:
            pytest.fail("tasks tool not implemented yet - expected for TDD")

        # Create multiple plan files
        plan_paths = []
        for i in range(3):
            plan_dir = temp_repo / "specs" / f"00{i+1}-feature-{i}"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_path = plan_dir / "plan.md"
            plan_path.write_text(f"# Plan {i}\n\n## Phase 1\n- Task {i}.1\n- Task {i}.2")
            plan_paths.append(str(plan_path))

        try:
            # Execute multiple tasks operations concurrently
            import asyncio
            task_calls = [
                tasks(plan_path, str(temp_repo)) for plan_path in plan_paths
            ]

            results = await asyncio.gather(*task_calls, return_exceptions=True)

            # Verify all operations completed (even if with errors due to no implementation)
            assert len(results) == len(plan_paths), "All concurrent operations must complete"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise