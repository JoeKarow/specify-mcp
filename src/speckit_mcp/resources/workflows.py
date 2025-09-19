"""
MCP resource implementation for serving workflows.

This module provides MCP resources for serving workflow definitions,
step sequences, validation rules, and state tracking.
"""

from typing import Dict, Any, Optional, List
import json
from enum import Enum
from fastmcp import Resource
from fastmcp.exceptions import McpError


class WorkflowState(str, Enum):
    """Workflow execution states."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    """Represents a step in a workflow."""

    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        required: bool = True,
        depends_on: List[str] = None,
        validation: Dict[str, Any] = None
    ):
        """
        Initialize workflow step.

        Args:
            step_id: Unique step identifier
            name: Step name
            description: Step description
            required: Whether step is required
            depends_on: List of step IDs this depends on
            validation: Validation rules for step
        """
        self.step_id = step_id
        self.name = name
        self.description = description
        self.required = required
        self.depends_on = depends_on or []
        self.validation = validation or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "depends_on": self.depends_on,
            "validation": self.validation
        }


class WorkflowDefinition:
    """Defines a complete workflow."""

    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str,
        steps: List[WorkflowStep],
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize workflow definition.

        Args:
            workflow_id: Unique workflow identifier
            name: Workflow name
            description: Workflow description
            steps: List of workflow steps
            metadata: Additional workflow metadata
        """
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps = steps
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata
        }


class WorkflowResources:
    """
    Manages MCP resources for workflows.

    Provides access to workflow definitions, step sequences,
    validation rules, and state tracking via MCP resource URIs.
    """

    def __init__(self):
        """Initialize workflow resources."""
        self.workflows = self._load_workflow_definitions()

    def _load_workflow_definitions(self) -> Dict[str, WorkflowDefinition]:
        """
        Load workflow definitions.

        Returns:
            Dictionary mapping workflow IDs to WorkflowDefinition instances
        """
        workflows = {}

        # Specify workflow
        workflows['specify'] = WorkflowDefinition(
            workflow_id='specify',
            name='Specification Workflow',
            description='Create feature specifications from descriptions',
            steps=[
                WorkflowStep(
                    step_id='validate_repo',
                    name='Validate Repository',
                    description='Ensure repository is valid git repo',
                    validation={
                        'is_git_repo': True,
                        'has_write_access': True
                    }
                ),
                WorkflowStep(
                    step_id='parse_description',
                    name='Parse Description',
                    description='Extract feature information from description',
                    validation={
                        'min_length': 20,
                        'max_length': 1000
                    }
                ),
                WorkflowStep(
                    step_id='generate_feature_id',
                    name='Generate Feature ID',
                    description='Create unique feature identifier',
                    validation={
                        'format': '^[0-9]{3}$'
                    }
                ),
                WorkflowStep(
                    step_id='create_branch',
                    name='Create Feature Branch',
                    description='Create git branch for feature',
                    depends_on=['validate_repo'],
                    validation={
                        'branch_pattern': '^feature/[a-z0-9-]+$'
                    }
                ),
                WorkflowStep(
                    step_id='load_template',
                    name='Load Specification Template',
                    description='Load and prepare specification template',
                    validation={
                        'template_exists': True
                    }
                ),
                WorkflowStep(
                    step_id='substitute_variables',
                    name='Substitute Template Variables',
                    description='Replace template variables with values',
                    depends_on=['load_template'],
                    validation={
                        'all_variables_replaced': True
                    }
                ),
                WorkflowStep(
                    step_id='write_spec',
                    name='Write Specification File',
                    description='Save specification to repository',
                    depends_on=['substitute_variables', 'create_branch'],
                    validation={
                        'file_created': True,
                        'valid_markdown': True
                    }
                ),
                WorkflowStep(
                    step_id='commit_spec',
                    name='Commit Specification',
                    description='Commit specification to git',
                    depends_on=['write_spec'],
                    validation={
                        'commit_created': True,
                        'commit_message_valid': True
                    }
                )
            ],
            metadata={
                'requires_git': True,
                'creates_branch': True,
                'output_type': 'specification',
                'typical_duration': '2-5 minutes'
            }
        )

        # Plan workflow
        workflows['plan'] = WorkflowDefinition(
            workflow_id='plan',
            name='Planning Workflow',
            description='Generate implementation plans from specifications',
            steps=[
                WorkflowStep(
                    step_id='validate_spec',
                    name='Validate Specification',
                    description='Ensure specification exists and is valid',
                    validation={
                        'file_exists': True,
                        'has_requirements': True
                    }
                ),
                WorkflowStep(
                    step_id='parse_spec',
                    name='Parse Specification',
                    description='Extract requirements and constraints',
                    depends_on=['validate_spec'],
                    validation={
                        'requirements_extracted': True
                    }
                ),
                WorkflowStep(
                    step_id='analyze_requirements',
                    name='Analyze Requirements',
                    description='Analyze technical requirements and dependencies',
                    depends_on=['parse_spec'],
                    validation={
                        'complexity_assessed': True
                    }
                ),
                WorkflowStep(
                    step_id='design_architecture',
                    name='Design Architecture',
                    description='Create high-level architecture design',
                    depends_on=['analyze_requirements'],
                    validation={
                        'components_defined': True,
                        'interfaces_specified': True
                    }
                ),
                WorkflowStep(
                    step_id='load_plan_template',
                    name='Load Plan Template',
                    description='Load and prepare plan template',
                    validation={
                        'template_exists': True
                    }
                ),
                WorkflowStep(
                    step_id='generate_plan',
                    name='Generate Implementation Plan',
                    description='Create detailed implementation plan',
                    depends_on=['design_architecture', 'load_plan_template'],
                    validation={
                        'phases_defined': True,
                        'deliverables_specified': True
                    }
                ),
                WorkflowStep(
                    step_id='assess_risks',
                    name='Assess Risks',
                    description='Identify and document risks',
                    depends_on=['generate_plan'],
                    required=False,
                    validation={
                        'risks_documented': True
                    }
                ),
                WorkflowStep(
                    step_id='write_plan',
                    name='Write Plan File',
                    description='Save plan to repository',
                    depends_on=['generate_plan'],
                    validation={
                        'file_created': True,
                        'valid_markdown': True
                    }
                ),
                WorkflowStep(
                    step_id='commit_plan',
                    name='Commit Plan',
                    description='Commit plan to git',
                    depends_on=['write_plan'],
                    validation={
                        'commit_created': True
                    }
                )
            ],
            metadata={
                'requires_spec': True,
                'creates_branch': False,
                'output_type': 'plan',
                'typical_duration': '5-10 minutes'
            }
        )

        # Tasks workflow
        workflows['tasks'] = WorkflowDefinition(
            workflow_id='tasks',
            name='Task Breakdown Workflow',
            description='Create task breakdowns from implementation plans',
            steps=[
                WorkflowStep(
                    step_id='validate_plan',
                    name='Validate Plan',
                    description='Ensure plan exists and is valid',
                    validation={
                        'file_exists': True,
                        'has_phases': True
                    }
                ),
                WorkflowStep(
                    step_id='parse_plan',
                    name='Parse Plan',
                    description='Extract phases and deliverables',
                    depends_on=['validate_plan'],
                    validation={
                        'phases_extracted': True
                    }
                ),
                WorkflowStep(
                    step_id='identify_tasks',
                    name='Identify Tasks',
                    description='Break down phases into individual tasks',
                    depends_on=['parse_plan'],
                    validation={
                        'min_tasks': 5,
                        'max_tasks': 100
                    }
                ),
                WorkflowStep(
                    step_id='map_dependencies',
                    name='Map Dependencies',
                    description='Identify task dependencies and order',
                    depends_on=['identify_tasks'],
                    validation={
                        'no_circular_deps': True,
                        'all_tasks_reachable': True
                    }
                ),
                WorkflowStep(
                    step_id='identify_parallel',
                    name='Identify Parallel Tasks',
                    description='Find tasks that can run in parallel',
                    depends_on=['map_dependencies'],
                    validation={
                        'parallel_groups_valid': True
                    }
                ),
                WorkflowStep(
                    step_id='apply_tdd_rules',
                    name='Apply TDD Rules',
                    description='Ensure tests come before implementation',
                    depends_on=['identify_tasks'],
                    validation={
                        'tests_first': True
                    }
                ),
                WorkflowStep(
                    step_id='estimate_duration',
                    name='Estimate Duration',
                    description='Calculate time estimates for tasks',
                    depends_on=['identify_tasks'],
                    required=False,
                    validation={
                        'estimates_reasonable': True
                    }
                ),
                WorkflowStep(
                    step_id='load_tasks_template',
                    name='Load Tasks Template',
                    description='Load and prepare tasks template',
                    validation={
                        'template_exists': True
                    }
                ),
                WorkflowStep(
                    step_id='generate_tasks',
                    name='Generate Task Breakdown',
                    description='Create formatted task list',
                    depends_on=['identify_parallel', 'apply_tdd_rules', 'load_tasks_template'],
                    validation={
                        'all_phases_covered': True
                    }
                ),
                WorkflowStep(
                    step_id='write_tasks',
                    name='Write Tasks File',
                    description='Save tasks to repository',
                    depends_on=['generate_tasks'],
                    validation={
                        'file_created': True,
                        'valid_markdown': True
                    }
                ),
                WorkflowStep(
                    step_id='commit_tasks',
                    name='Commit Tasks',
                    description='Commit tasks to git',
                    depends_on=['write_tasks'],
                    validation={
                        'commit_created': True
                    }
                )
            ],
            metadata={
                'requires_plan': True,
                'creates_branch': False,
                'output_type': 'tasks',
                'typical_duration': '3-7 minutes',
                'supports_parallel': True
            }
        )

        # Initialize workflow
        workflows['initialize'] = WorkflowDefinition(
            workflow_id='initialize',
            name='Project Initialization Workflow',
            description='Initialize a new SpecKit project',
            steps=[
                WorkflowStep(
                    step_id='validate_directory',
                    name='Validate Directory',
                    description='Ensure directory is suitable for initialization',
                    validation={
                        'directory_exists': True,
                        'has_write_permission': True
                    }
                ),
                WorkflowStep(
                    step_id='check_git',
                    name='Check Git Repository',
                    description='Verify git repository status',
                    validation={
                        'is_git_repo': False  # Should NOT already be initialized
                    }
                ),
                WorkflowStep(
                    step_id='create_structure',
                    name='Create Project Structure',
                    description='Create necessary directories',
                    depends_on=['validate_directory'],
                    validation={
                        'directories_created': True
                    }
                ),
                WorkflowStep(
                    step_id='generate_constitution',
                    name='Generate Constitution',
                    description='Create project constitution file',
                    depends_on=['create_structure'],
                    validation={
                        'file_created': True
                    }
                ),
                WorkflowStep(
                    step_id='create_gitignore',
                    name='Create .gitignore',
                    description='Add appropriate .gitignore file',
                    depends_on=['create_structure'],
                    required=False,
                    validation={
                        'file_created': True
                    }
                ),
                WorkflowStep(
                    step_id='init_git',
                    name='Initialize Git',
                    description='Initialize git repository',
                    depends_on=['check_git', 'create_structure'],
                    validation={
                        'repo_initialized': True
                    }
                ),
                WorkflowStep(
                    step_id='initial_commit',
                    name='Create Initial Commit',
                    description='Commit initial project files',
                    depends_on=['generate_constitution', 'init_git'],
                    validation={
                        'commit_created': True
                    }
                )
            ],
            metadata={
                'creates_repo': True,
                'one_time_only': True,
                'output_type': 'project',
                'typical_duration': '1-2 minutes'
            }
        )

        return workflows

    async def get_workflow_resource(self, workflow_name: str) -> Resource:
        """
        Serve a workflow definition as an MCP resource.

        Args:
            workflow_name: Name of the workflow

        Returns:
            MCP Resource with workflow definition

        Raises:
            McpError: If workflow not found
        """
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            raise McpError(f"Workflow not found: {workflow_name}")

        uri = f"mcp://speckit/workflows/{workflow_name}"

        # Build step sequence for display
        step_sequence = []
        for step in workflow.steps:
            step_info = {
                "id": step.step_id,
                "name": step.name,
                "description": step.description,
                "required": step.required,
                "depends_on": step.depends_on
            }
            if step.validation:
                step_info["validation"] = step.validation
            step_sequence.append(step_info)

        # Build metadata
        metadata = {
            "workflow_id": workflow.workflow_id,
            "description": workflow.description,
            "total_steps": len(workflow.steps),
            "required_steps": sum(1 for s in workflow.steps if s.required),
            "optional_steps": sum(1 for s in workflow.steps if not s.required),
            "steps": step_sequence,
            **workflow.metadata
        }

        # Generate workflow documentation
        content = self._generate_workflow_documentation(workflow)

        return Resource(
            uri=uri,
            name=workflow.name,
            mimeType="text/markdown",
            text=content,
            metadata=metadata
        )

    def _generate_workflow_documentation(self, workflow: WorkflowDefinition) -> str:
        """
        Generate markdown documentation for a workflow.

        Args:
            workflow: Workflow definition

        Returns:
            Markdown documentation
        """
        lines = []

        # Header
        lines.append(f"# {workflow.name}")
        lines.append("")
        lines.append(f"**ID**: {workflow.workflow_id}")
        lines.append(f"**Description**: {workflow.description}")
        lines.append("")

        # Metadata
        if workflow.metadata:
            lines.append("## Metadata")
            lines.append("")
            for key, value in workflow.metadata.items():
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
            lines.append("")

        # Steps
        lines.append("## Workflow Steps")
        lines.append("")
        lines.append(f"Total steps: {len(workflow.steps)} ({sum(1 for s in workflow.steps if s.required)} required, {sum(1 for s in workflow.steps if not s.required)} optional)")
        lines.append("")

        for i, step in enumerate(workflow.steps, 1):
            req_marker = "" if step.required else " (Optional)"
            lines.append(f"### {i}. {step.name}{req_marker}")
            lines.append("")
            lines.append(f"**ID**: `{step.step_id}`")
            lines.append(f"**Description**: {step.description}")

            if step.depends_on:
                lines.append(f"**Depends on**: {', '.join(f'`{d}`' for d in step.depends_on)}")

            if step.validation:
                lines.append("")
                lines.append("**Validation Rules**:")
                for rule, value in step.validation.items():
                    lines.append(f"- {rule}: {value}")

            lines.append("")

        # Step sequence diagram
        lines.append("## Execution Flow")
        lines.append("")
        lines.append("```")

        # Build dependency graph
        for step in workflow.steps:
            if not step.depends_on:
                lines.append(f"START → {step.step_id}")
            else:
                for dep in step.depends_on:
                    lines.append(f"{dep} → {step.step_id}")

        # Find terminal steps
        terminal_steps = []
        for step in workflow.steps:
            is_terminal = True
            for other_step in workflow.steps:
                if step.step_id in other_step.depends_on:
                    is_terminal = False
                    break
            if is_terminal:
                terminal_steps.append(step.step_id)

        for terminal in terminal_steps:
            lines.append(f"{terminal} → END")

        lines.append("```")
        lines.append("")

        # Validation summary
        lines.append("## Validation Summary")
        lines.append("")
        lines.append("This workflow validates:")
        lines.append("")

        all_validations = {}
        for step in workflow.steps:
            if step.validation:
                all_validations.update(step.validation)

        for rule, value in all_validations.items():
            lines.append(f"- **{rule.replace('_', ' ').title()}**: {value}")

        return "\n".join(lines)

    async def get_workflow_state(self, workflow_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the current state of a workflow execution.

        Args:
            workflow_name: Name of the workflow
            context: Execution context with completed steps

        Returns:
            Workflow state information
        """
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            raise McpError(f"Workflow not found: {workflow_name}")

        completed_steps = context.get('completed_steps', [])
        failed_steps = context.get('failed_steps', [])

        # Calculate state
        total_steps = len(workflow.steps)
        required_steps = [s for s in workflow.steps if s.required]
        completed_count = len(completed_steps)
        failed_count = len(failed_steps)

        if failed_count > 0:
            state = WorkflowState.FAILED
        elif completed_count == 0:
            state = WorkflowState.NOT_STARTED
        elif completed_count < len(required_steps):
            state = WorkflowState.IN_PROGRESS
        else:
            state = WorkflowState.COMPLETED

        # Find next steps
        next_steps = []
        for step in workflow.steps:
            if step.step_id in completed_steps or step.step_id in failed_steps:
                continue

            # Check if dependencies are met
            deps_met = all(dep in completed_steps for dep in step.depends_on)
            if deps_met:
                next_steps.append(step.step_id)

        # Calculate progress
        progress_percentage = (completed_count / total_steps) * 100 if total_steps > 0 else 0

        return {
            "workflow_id": workflow.workflow_id,
            "state": state.value,
            "progress": {
                "total_steps": total_steps,
                "completed_steps": completed_count,
                "failed_steps": failed_count,
                "percentage": round(progress_percentage, 1)
            },
            "next_steps": next_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps
        }

    async def list_workflows(self) -> List[Resource]:
        """
        List all available workflow resources.

        Returns:
            List of workflow resources
        """
        resources = []

        for workflow_name, workflow in self.workflows.items():
            uri = f"mcp://speckit/workflows/{workflow_name}"

            resources.append(Resource(
                uri=uri,
                name=workflow.name,
                mimeType="application/json",
                description=workflow.description,
                metadata={
                    "workflow_id": workflow.workflow_id,
                    "total_steps": len(workflow.steps),
                    "creates_branch": workflow.metadata.get('creates_branch', False),
                    "output_type": workflow.metadata.get('output_type')
                }
            ))

        return resources


# Create singleton instance
_workflow_resources = WorkflowResources()


async def serve_workflow(uri: str) -> Resource:
    """
    Serve a workflow resource based on URI.

    Expected URI format: mcp://speckit/workflows/{workflow_name}

    Args:
        uri: Resource URI

    Returns:
        MCP Resource containing workflow definition

    Raises:
        McpError: If URI is invalid or workflow not found
    """
    if not uri.startswith("mcp://speckit/workflows/"):
        raise McpError(f"Invalid workflow URI: {uri}")

    workflow_name = uri.replace("mcp://speckit/workflows/", "")

    if not workflow_name:
        # List all workflows
        workflows = await _workflow_resources.list_workflows()
        return Resource(
            uri="mcp://speckit/workflows",
            name="Available Workflows",
            mimeType="application/json",
            metadata={
                "workflows": [
                    {
                        "uri": w.uri,
                        "name": w.name,
                        "description": w.description
                    } for w in workflows
                ]
            }
        )

    return await _workflow_resources.get_workflow_resource(workflow_name)


async def list_workflow_resources() -> List[Resource]:
    """
    List all available workflow resources.

    Returns:
        List of available workflow resources
    """
    return await _workflow_resources.list_workflows()