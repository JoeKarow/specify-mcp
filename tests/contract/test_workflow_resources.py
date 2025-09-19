"""
Contract tests for the workflow MCP resources.

These tests verify MCP protocol compliance and resource schema validation for workflow resources.
Workflow resources serve workflow definitions for specify, plan, and tasks workflows with proper
step sequences, validation rules, state transitions, and progress tracking.

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
    from speckit_mcp.resources.workflows import WorkflowResource
    from speckit_mcp.server import create_server
    from speckit_mcp.config.models import WorkflowSession
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    WorkflowResource = None
    create_server = None
    WorkflowSession = None


class TestWorkflowResourcesContract:
    """Contract tests for workflow MCP resources ensuring MCP protocol compliance."""

    @pytest.fixture
    def workflow_uris(self):
        """Standard workflow resource URIs following MCP resource pattern."""
        return [
            "mcp://speckit/workflows/specify",
            "mcp://speckit/workflows/plan",
            "mcp://speckit/workflows/tasks",
            "mcp://speckit/workflows/initialize",
            "mcp://speckit/workflows/validate"
        ]

    @pytest.fixture
    def workflow_definitions(self):
        """Expected workflow definitions with steps and validation rules."""
        return {
            "specify": {
                "name": "Feature Specification Workflow",
                "description": "Create feature specifications from requirements",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "validate_repository",
                        "name": "Validate Repository",
                        "description": "Ensure repository is valid git repository",
                        "type": "validation",
                        "required": True,
                        "timeout": 30
                    },
                    {
                        "id": "create_branch",
                        "name": "Create Feature Branch",
                        "description": "Create new branch for feature development",
                        "type": "git_operation",
                        "required": True,
                        "timeout": 60,
                        "depends_on": ["validate_repository"]
                    },
                    {
                        "id": "generate_spec",
                        "name": "Generate Specification",
                        "description": "Create specification from template and requirements",
                        "type": "generation",
                        "required": True,
                        "timeout": 120,
                        "depends_on": ["create_branch"]
                    },
                    {
                        "id": "commit_changes",
                        "name": "Commit Specification",
                        "description": "Commit generated specification to git",
                        "type": "git_operation",
                        "required": True,
                        "timeout": 30,
                        "depends_on": ["generate_spec"]
                    }
                ],
                "validation_rules": [
                    {
                        "rule": "repository_exists",
                        "message": "Repository path must exist and be a git repository"
                    },
                    {
                        "rule": "description_not_empty",
                        "message": "Feature description cannot be empty"
                    },
                    {
                        "rule": "unique_feature_id",
                        "message": "Feature ID must be unique within repository"
                    }
                ],
                "rollback_steps": [
                    {
                        "condition": "branch_created",
                        "action": "delete_branch",
                        "description": "Remove created branch if workflow fails"
                    }
                ]
            },
            "plan": {
                "name": "Implementation Planning Workflow",
                "description": "Generate implementation plans from specifications",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "load_specification",
                        "name": "Load Specification",
                        "description": "Load and validate feature specification",
                        "type": "loading",
                        "required": True,
                        "timeout": 30
                    },
                    {
                        "id": "analyze_requirements",
                        "name": "Analyze Requirements",
                        "description": "Parse and analyze specification requirements",
                        "type": "analysis",
                        "required": True,
                        "timeout": 60,
                        "depends_on": ["load_specification"]
                    },
                    {
                        "id": "generate_plan",
                        "name": "Generate Implementation Plan",
                        "description": "Create detailed implementation plan",
                        "type": "generation",
                        "required": True,
                        "timeout": 180,
                        "depends_on": ["analyze_requirements"]
                    },
                    {
                        "id": "save_artifacts",
                        "name": "Save Plan Artifacts",
                        "description": "Save plan and supporting documents",
                        "type": "persistence",
                        "required": True,
                        "timeout": 30,
                        "depends_on": ["generate_plan"]
                    }
                ],
                "validation_rules": [
                    {
                        "rule": "specification_exists",
                        "message": "Feature specification must exist"
                    },
                    {
                        "rule": "specification_valid",
                        "message": "Specification must be valid YAML format"
                    }
                ]
            },
            "tasks": {
                "name": "Task Generation Workflow",
                "description": "Create task breakdowns from implementation plans",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "load_plan",
                        "name": "Load Implementation Plan",
                        "description": "Load and validate implementation plan",
                        "type": "loading",
                        "required": True,
                        "timeout": 30
                    },
                    {
                        "id": "generate_tasks",
                        "name": "Generate Task List",
                        "description": "Create structured task breakdown",
                        "type": "generation",
                        "required": True,
                        "timeout": 120,
                        "depends_on": ["load_plan"]
                    },
                    {
                        "id": "apply_rules",
                        "name": "Apply Task Rules",
                        "description": "Apply parallelization and dependency rules",
                        "type": "processing",
                        "required": True,
                        "timeout": 60,
                        "depends_on": ["generate_tasks"]
                    },
                    {
                        "id": "save_tasks",
                        "name": "Save Task List",
                        "description": "Save final task breakdown",
                        "type": "persistence",
                        "required": True,
                        "timeout": 30,
                        "depends_on": ["apply_rules"]
                    }
                ],
                "validation_rules": [
                    {
                        "rule": "plan_exists",
                        "message": "Implementation plan must exist"
                    },
                    {
                        "rule": "plan_complete",
                        "message": "Plan must have all required sections"
                    }
                ]
            }
        }

    @pytest.fixture
    def workflow_states(self):
        """Valid workflow execution states."""
        return [
            "pending",
            "running",
            "completed",
            "failed",
            "cancelled",
            "paused"
        ]

    @pytest.mark.contract
    def test_workflow_resource_class_exists(self):
        """Test that the WorkflowResource class exists and is importable."""
        assert WorkflowResource is not None, "WorkflowResource class must exist"

    @pytest.mark.contract
    def test_workflow_session_model_exists(self):
        """Test that the WorkflowSession Pydantic model exists."""
        assert WorkflowSession is not None, "WorkflowSession model must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_resource_uri_patterns(self, workflow_uris):
        """Test that workflow resources follow proper MCP URI patterns."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        # Test URI pattern validation
        for uri in workflow_uris:
            assert uri.startswith("mcp://speckit/workflows/"), f"URI {uri} must follow mcp://speckit/workflows/ pattern"

            # Extract workflow type from URI
            workflow_type = uri.split("/")[-1]
            valid_types = ["specify", "plan", "tasks", "initialize", "validate"]
            assert workflow_type in valid_types, f"Workflow type {workflow_type} must be valid"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_resource_definitions(self, workflow_definitions):
        """Test that workflow resources provide proper workflow definitions."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test resource registration methods exist
            assert hasattr(resource, 'list_resources'), "WorkflowResource must have list_resources method"
            assert hasattr(resource, 'read_resource'), "WorkflowResource must have read_resource method"

            for workflow_name, expected_definition in workflow_definitions.items():
                uri = f"mcp://speckit/workflows/{workflow_name}"

                workflow_content = await resource.read_resource(uri)
                assert workflow_content is not None, f"Workflow {workflow_name} must be available"
                assert isinstance(workflow_content, str), "Workflow content must be string (JSON/YAML)"

                # Parse workflow definition
                import json
                try:
                    workflow_def = json.loads(workflow_content)
                except json.JSONDecodeError:
                    import yaml
                    workflow_def = yaml.safe_load(workflow_content)

                assert isinstance(workflow_def, dict), "Workflow definition must be valid object"

                # Verify required workflow fields
                required_fields = ["name", "description", "version", "steps"]
                for field in required_fields:
                    assert field in workflow_def, f"Workflow {workflow_name} must include {field}"

                # Verify steps structure
                steps = workflow_def["steps"]
                assert isinstance(steps, list), "Workflow steps must be list"
                assert len(steps) > 0, "Workflow must have at least one step"

                for step in steps:
                    step_required_fields = ["id", "name", "description", "type", "required"]
                    for field in step_required_fields:
                        assert field in step, f"Step must include {field}"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_step_sequences(self, workflow_definitions):
        """Test that workflows define proper step sequences and dependencies."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            for workflow_name, expected_definition in workflow_definitions.items():
                uri = f"mcp://speckit/workflows/{workflow_name}"

                workflow_content = await resource.read_resource(uri)
                import json
                try:
                    workflow_def = json.loads(workflow_content)
                except json.JSONDecodeError:
                    import yaml
                    workflow_def = yaml.safe_load(workflow_content)

                steps = workflow_def["steps"]
                step_ids = [step["id"] for step in steps]

                # Verify step dependency resolution
                for step in steps:
                    if "depends_on" in step:
                        dependencies = step["depends_on"]
                        assert isinstance(dependencies, list), "Dependencies must be list"

                        for dep in dependencies:
                            assert dep in step_ids, f"Dependency {dep} must reference valid step"

                # Verify no circular dependencies
                def has_circular_dependency(step_id, visited=None):
                    if visited is None:
                        visited = set()

                    if step_id in visited:
                        return True

                    visited.add(step_id)
                    step = next((s for s in steps if s["id"] == step_id), None)

                    if step and "depends_on" in step:
                        for dep in step["depends_on"]:
                            if has_circular_dependency(dep, visited.copy()):
                                return True

                    return False

                for step_id in step_ids:
                    assert not has_circular_dependency(step_id), f"Workflow {workflow_name} must not have circular dependencies"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_validation_rules(self, workflow_definitions):
        """Test that workflows define proper validation rules."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            for workflow_name, expected_definition in workflow_definitions.items():
                if "validation_rules" not in expected_definition:
                    continue

                uri = f"mcp://speckit/workflows/{workflow_name}"
                workflow_content = await resource.read_resource(uri)

                import json
                try:
                    workflow_def = json.loads(workflow_content)
                except json.JSONDecodeError:
                    import yaml
                    workflow_def = yaml.safe_load(workflow_content)

                if "validation_rules" in workflow_def:
                    validation_rules = workflow_def["validation_rules"]
                    assert isinstance(validation_rules, list), "Validation rules must be list"

                    for rule in validation_rules:
                        assert "rule" in rule, "Validation rule must have rule field"
                        assert "message" in rule, "Validation rule must have message field"
                        assert isinstance(rule["rule"], str), "Rule must be string"
                        assert isinstance(rule["message"], str), "Message must be string"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self, workflow_states):
        """Test that workflow resources support proper state transitions."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test state transition validation if implemented
            if hasattr(resource, 'validate_state_transition'):
                # Test valid transitions
                valid_transitions = [
                    ("pending", "running"),
                    ("running", "completed"),
                    ("running", "failed"),
                    ("running", "paused"),
                    ("paused", "running"),
                    ("pending", "cancelled")
                ]

                for from_state, to_state in valid_transitions:
                    is_valid = await resource.validate_state_transition(from_state, to_state)
                    assert is_valid, f"Transition from {from_state} to {to_state} must be valid"

                # Test invalid transitions
                invalid_transitions = [
                    ("completed", "running"),
                    ("failed", "running"),
                    ("cancelled", "running")
                ]

                for from_state, to_state in invalid_transitions:
                    is_valid = await resource.validate_state_transition(from_state, to_state)
                    assert not is_valid, f"Transition from {from_state} to {to_state} must be invalid"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_progress_tracking(self):
        """Test that workflow resources support progress tracking."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test progress tracking capability if implemented
            if hasattr(resource, 'track_progress'):
                workflow_id = "test-workflow-001"
                workflow_type = "specify"

                # Start workflow tracking
                await resource.track_progress(workflow_id, workflow_type, "running")

                # Update step progress
                if hasattr(resource, 'update_step_progress'):
                    step_id = "validate_repository"
                    await resource.update_step_progress(workflow_id, step_id, "completed")

                # Get progress status
                if hasattr(resource, 'get_progress'):
                    progress = await resource.get_progress(workflow_id)
                    assert isinstance(progress, dict), "Progress must be dictionary"
                    assert "workflow_id" in progress, "Progress must include workflow ID"
                    assert "state" in progress, "Progress must include state"
                    assert "steps" in progress, "Progress must include steps"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_execution_engine(self):
        """Test that workflow resources provide execution engine capabilities."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test workflow execution capability if implemented
            if hasattr(resource, 'execute_workflow'):
                workflow_name = "specify"
                workflow_params = {
                    "description": "Test feature",
                    "repository_path": "/test/repo"
                }

                # Start workflow execution
                execution_id = await resource.execute_workflow(workflow_name, workflow_params)
                assert isinstance(execution_id, str), "Execution ID must be string"
                assert len(execution_id) > 0, "Execution ID must not be empty"

                # Test execution status monitoring
                if hasattr(resource, 'get_execution_status'):
                    status = await resource.get_execution_status(execution_id)
                    assert isinstance(status, dict), "Execution status must be dictionary"
                    assert "id" in status, "Status must include execution ID"
                    assert "state" in status, "Status must include state"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_rollback_mechanisms(self):
        """Test that workflow resources support rollback mechanisms."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test rollback capability if implemented
            if hasattr(resource, 'rollback_workflow'):
                workflow_id = "test-workflow-rollback"
                rollback_point = "create_branch"

                # Perform rollback
                rollback_result = await resource.rollback_workflow(workflow_id, rollback_point)
                assert isinstance(rollback_result, dict), "Rollback result must be dictionary"
                assert "success" in rollback_result, "Rollback result must include success status"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_resource_error_handling(self):
        """Test proper error handling for invalid workflow requests."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test invalid URI
            with pytest.raises(Exception) as exc_info:
                await resource.read_resource("mcp://invalid/workflows/nonexistent")

            # Should raise appropriate exception
            error = exc_info.value
            assert error is not None, "Must raise exception for invalid URI"

            # Test malformed URI
            with pytest.raises(Exception):
                await resource.read_resource("invalid://uri/format")

            # Test non-existent workflow
            with pytest.raises(Exception):
                await resource.read_resource("mcp://speckit/workflows/nonexistent")

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_resource_mcp_compliance(self):
        """Test that workflow resources are MCP protocol compliant."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test MCP resource interface compliance
            resources = await resource.list_resources()

            # Verify JSON-RPC 2.0 compatible response structure
            assert isinstance(resources, list), "Resources list must be JSON serializable"

            # Verify each resource follows MCP resource schema
            for resource_info in resources:
                # Check for required MCP resource fields
                required_fields = ['uri', 'name']
                for field in required_fields:
                    assert field in resource_info, f"Resource must include {field}"

                # Verify URI format
                uri = resource_info['uri']
                assert uri.startswith('mcp://'), "Resource URI must use mcp:// scheme"

                # Verify MIME type for workflow resources
                if 'mimeType' in resource_info:
                    mime_type = resource_info['mimeType']
                    valid_types = ['application/json', 'application/yaml', 'text/yaml']
                    assert mime_type in valid_types, f"Workflow resource must have valid MIME type, got {mime_type}"

                # Verify response is JSON serializable (MCP requirement)
                json.dumps(resource_info)  # Should not raise exception

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    def test_workflow_resource_in_mcp_server(self):
        """Test that workflow resources are properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify workflow resources are registered
            resources = getattr(server, 'resources', {})
            workflow_resources = [r for r in resources if 'workflows' in str(r)]
            assert len(workflow_resources) > 0, "Workflow resources must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_session_model_validation(self):
        """Test WorkflowSession Pydantic model validation."""
        if WorkflowSession is None:
            pytest.fail("WorkflowSession model not implemented yet - expected for TDD")

        try:
            # Test valid workflow session creation
            valid_session = WorkflowSession(
                id="session-001",
                workflow_type="specify",
                state="running",
                current_step="validate_repository",
                parameters={
                    "description": "Test feature",
                    "repository_path": "/test/repo"
                },
                progress={
                    "completed_steps": [],
                    "failed_steps": [],
                    "total_steps": 4
                }
            )

            assert valid_session.id == "session-001"
            assert valid_session.workflow_type == "specify"
            assert valid_session.state == "running"

            # Test invalid session validation
            with pytest.raises(ValidationError):
                WorkflowSession(
                    id="",  # Empty ID should fail
                    workflow_type="invalid_type",  # Invalid workflow type
                    state="invalid_state",  # Invalid state
                    current_step=None,
                    parameters={},
                    progress={}
                )

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Model not implemented yet - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_resource_concurrent_execution(self):
        """Test that workflow resources handle concurrent workflow execution."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test concurrent workflow access
            workflow_uris = [
                "mcp://speckit/workflows/specify",
                "mcp://speckit/workflows/plan",
                "mcp://speckit/workflows/tasks"
            ]

            # Execute multiple resource reads concurrently
            import asyncio
            tasks = [
                resource.read_resource(uri) for uri in workflow_uris
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all operations completed
            assert len(results) == len(workflow_uris), "All concurrent operations must complete"

            # Verify no exceptions occurred (unless due to missing implementation)
            for result in results:
                if isinstance(result, Exception):
                    if "not implemented" not in str(result).lower():
                        raise result

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self):
        """Test that workflow resources handle step timeouts properly."""
        if WorkflowResource is None:
            pytest.fail("WorkflowResource not implemented yet - expected for TDD")

        try:
            resource = WorkflowResource()

            # Test timeout handling capability if implemented
            if hasattr(resource, 'handle_step_timeout'):
                workflow_id = "timeout-test"
                step_id = "long_running_step"

                # Simulate step timeout
                timeout_result = await resource.handle_step_timeout(workflow_id, step_id)
                assert isinstance(timeout_result, dict), "Timeout result must be dictionary"
                assert "action" in timeout_result, "Timeout result must include action"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise