"""
MCP tool for generating task breakdowns from implementation plans.

This module implements the tasks tool that creates structured task
YAML files with dependencies, parallel groups, and categories.
"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastmcp.exceptions import McpError

from speckit_mcp.config.manager import ConfigurationManager
from speckit_mcp.config.models import Task, TaskStatus, TaskCategory
from speckit_mcp.resources.template_manager import TemplateManager
from speckit_mcp.resources.models import TemplateType
from speckit_mcp.utils.file_ops import safe_read, safe_write, ensure_directory


def _extract_feature_id_from_plan(plan_path: str) -> Optional[str]:
    """
    Extract feature ID from plan file.

    Args:
        plan_path: Path to plan file

    Returns:
        Feature ID or None if not found
    """
    # Try to extract from filename first
    filename = Path(plan_path).stem
    match = re.match(r'^(\d{3})-plan', filename)
    if match:
        return match.group(1)

    # Try to extract from content
    try:
        content = safe_read(plan_path)
        # Look for "Feature ID: XXX" pattern
        match = re.search(r'\*\*Feature ID\*\*:\s*(\d{3})', content)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None


def _parse_plan_phases(plan_content: str) -> List[Dict[str, Any]]:
    """
    Parse implementation phases from plan content.

    Args:
        plan_content: Plan markdown content

    Returns:
        List of phase dictionaries
    """
    phases = []

    # Look for phase sections
    phase_pattern = r'###\s*Phase\s*\d+:\s*(.+?)(?:\((.+?)\))?'
    phase_matches = re.findall(phase_pattern, plan_content)

    for match in phase_matches:
        phase_name = match[0].strip()
        duration = match[1].strip() if len(match) > 1 else None

        phases.append({
            'name': phase_name,
            'duration': duration or 'TBD',
            'tasks': []
        })

    return phases


def _generate_tasks_for_phase(
    phase_name: str,
    feature_id: str,
    task_start_id: int
) -> List[Task]:
    """
    Generate tasks for a specific phase.

    Args:
        phase_name: Name of the phase
        feature_id: Feature identifier
        task_start_id: Starting task ID number

    Returns:
        List of Task objects
    """
    tasks = []
    phase_lower = phase_name.lower()

    # Determine tasks based on phase type
    if 'foundation' in phase_lower or 'setup' in phase_lower:
        task_specs = [
            ('Initialize project structure', TaskCategory.IMPLEMENT),
            ('Configure dependencies', TaskCategory.IMPLEMENT),
            ('Set up development environment', TaskCategory.IMPLEMENT),
            ('Create core data models', TaskCategory.IMPLEMENT),
            ('Write unit tests for models', TaskCategory.TEST)
        ]
    elif 'research' in phase_lower or 'design' in phase_lower:
        task_specs = [
            ('Research technical requirements', TaskCategory.DOCUMENT),
            ('Design system architecture', TaskCategory.DOCUMENT),
            ('Create API specifications', TaskCategory.DOCUMENT),
            ('Review and validate design', TaskCategory.VALIDATE)
        ]
    elif 'implement' in phase_lower or 'core' in phase_lower:
        task_specs = [
            ('Write failing tests (TDD)', TaskCategory.TEST),
            ('Implement core business logic', TaskCategory.IMPLEMENT),
            ('Create API endpoints', TaskCategory.IMPLEMENT),
            ('Add error handling', TaskCategory.IMPLEMENT),
            ('Write integration tests', TaskCategory.TEST)
        ]
    elif 'integration' in phase_lower:
        task_specs = [
            ('Connect system components', TaskCategory.IMPLEMENT),
            ('Verify data flow', TaskCategory.VALIDATE),
            ('Test end-to-end workflows', TaskCategory.TEST),
            ('Handle edge cases', TaskCategory.IMPLEMENT)
        ]
    elif 'test' in phase_lower or 'polish' in phase_lower:
        task_specs = [
            ('Complete test coverage', TaskCategory.TEST),
            ('Optimize performance', TaskCategory.IMPLEMENT),
            ('Write documentation', TaskCategory.DOCUMENT),
            ('Final validation', TaskCategory.VALIDATE)
        ]
    else:
        # Default tasks for unknown phase
        task_specs = [
            (f'Complete {phase_name} tasks', TaskCategory.IMPLEMENT),
            (f'Test {phase_name} implementation', TaskCategory.TEST),
            (f'Document {phase_name} work', TaskCategory.DOCUMENT)
        ]

    # Create Task objects
    for i, (description, category) in enumerate(task_specs):
        task_id = f"T{task_start_id + i:03d}"

        # Determine dependencies
        depends_on = []
        if category == TaskCategory.TEST and i > 0:
            # Tests depend on implementation
            depends_on.append(f"T{task_start_id + i - 1:03d}")
        elif i > 0 and 'validate' in description.lower():
            # Validation depends on previous tasks
            depends_on.append(f"T{task_start_id + i - 1:03d}")

        task = Task(
            task_id=task_id,
            order=task_start_id + i,
            description=description,
            category=category,
            depends_on=depends_on,
            parallel_group=f"phase_{phase_name.replace(' ', '_').lower()}" if category == TaskCategory.TEST else None,
            status=TaskStatus.PENDING,
            specification_ref=f"{feature_id}-spec.md"
        )

        tasks.append(task)

    return tasks


def _identify_parallel_groups(tasks: List[Task]) -> List[str]:
    """
    Identify groups of tasks that can be executed in parallel.

    Args:
        tasks: List of Task objects

    Returns:
        List of parallel group identifiers
    """
    groups = set()

    for task in tasks:
        if task.parallel_group:
            groups.add(task.parallel_group)

    # Also identify tasks with no dependencies as a parallel group
    independent_tasks = [
        t for t in tasks
        if not t.depends_on and not t.parallel_group
    ]

    if len(independent_tasks) > 1:
        groups.add('independent')
        for task in independent_tasks:
            task.parallel_group = 'independent'

    return list(groups)


async def tasks(plan_path: str, repository_path: str) -> Dict[str, Any]:
    """
    Create task breakdown from implementation plan.

    This MCP tool parses an implementation plan and generates a structured
    task YAML file with dependencies, parallel execution groups, and categories.

    Args:
        plan_path: Path to plan file
        repository_path: Path to git repository

    Returns:
        Dictionary containing:
            - success: Whether the operation succeeded
            - tasks_path: Path to generated tasks file
            - task_count: Total number of tasks generated
            - parallel_groups: List of parallel execution groups
            - categories: Task categories distribution
            - message: Status message

    Raises:
        McpError: If plan file not found or task generation fails
    """
    try:
        # Validate paths
        plan_file = Path(plan_path)
        if not plan_file.exists():
            raise McpError(
                code=-32602,  # Invalid params
                message=f"Plan file not found: {plan_path}"
            )

        repo_path = Path(repository_path)
        if not repo_path.exists():
            raise McpError(
                code=-32602,
                message=f"Repository path does not exist: {repository_path}"
            )

        # Load configuration
        config_manager = ConfigurationManager(str(repo_path))
        config = config_manager.load_configuration()

        # Check if tasks workflow is enabled
        workflow_config = config.workflows.get('tasks')
        if not workflow_config or not workflow_config.enabled:
            raise McpError(
                code=-32603,  # Internal error
                message="Tasks workflow is not enabled in configuration"
            )

        # Read plan content
        plan_content = safe_read(plan_file)

        # Extract feature ID
        feature_id = _extract_feature_id_from_plan(str(plan_file))
        if not feature_id:
            # Generate a default ID if not found
            feature_id = datetime.now().strftime('%m%d')

        # Extract feature name from plan content
        feature_name_match = re.search(r'#\s*Implementation Plan:\s*(.+)', plan_content)
        feature_name = feature_name_match.group(1) if feature_name_match else f"Feature {feature_id}"

        # Parse phases from plan
        phases = _parse_plan_phases(plan_content)
        if not phases:
            # Create default phases if none found
            phases = [
                {'name': 'Setup', 'duration': '1 day'},
                {'name': 'Implementation', 'duration': '3 days'},
                {'name': 'Testing', 'duration': '1 day'}
            ]

        # Generate tasks for each phase
        all_tasks = []
        task_id_counter = 1

        for phase in phases:
            phase_tasks = _generate_tasks_for_phase(
                phase['name'],
                feature_id,
                task_id_counter
            )
            all_tasks.extend(phase_tasks)
            task_id_counter += len(phase_tasks)

        # Identify parallel groups
        parallel_groups = _identify_parallel_groups(all_tasks)

        # Calculate category distribution
        categories = {}
        for task in all_tasks:
            category = task.category.value
            categories[category] = categories.get(category, 0) + 1

        # Generate tasks markdown from template
        template_manager = TemplateManager()
        template = template_manager.get_template(TemplateType.TASKS)

        # Prepare variables for template substitution
        variables = {
            'feature_id': feature_id,
            'feature_name': feature_name,
            'plan_path': str(plan_file),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'task_count': len(all_tasks),
            'parallel_groups': len(parallel_groups),
            'estimated_duration': f"{len(phases) * 2} days"  # Rough estimate
        }

        # Substitute variables in template
        tasks_content = template_manager.substitute_variables(template, variables)

        # Create tasks directory
        tasks_dir = repo_path / '.specify-mcp' / 'tasks'
        ensure_directory(tasks_dir)

        # Write tasks markdown file
        tasks_md_filename = f"{feature_id}-tasks.md"
        tasks_md_path = tasks_dir / tasks_md_filename

        written_md_path = safe_write(
            tasks_md_path,
            tasks_content,
            base_path=str(repo_path),
            overwrite=True
        )

        # Also create a structured YAML file with task data
        tasks_data = {
            'feature_id': feature_id,
            'feature_name': feature_name,
            'generated_at': datetime.now().isoformat(),
            'total_tasks': len(all_tasks),
            'parallel_groups': parallel_groups,
            'categories': categories,
            'tasks': [
                {
                    'id': task.task_id,
                    'order': task.order,
                    'description': task.description,
                    'category': task.category.value,
                    'status': task.status.value,
                    'depends_on': task.depends_on,
                    'parallel_group': task.parallel_group
                }
                for task in all_tasks
            ]
        }

        # Write YAML file
        tasks_yaml_filename = f"{feature_id}-tasks.yaml"
        tasks_yaml_path = tasks_dir / tasks_yaml_filename

        with open(tasks_yaml_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                tasks_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )

        # Auto-commit if enabled
        if config.settings.get('auto_commit', True):
            from speckit_mcp.git.operations import add_files, commit

            # Add both files to git
            files_to_add = [
                str(written_md_path.relative_to(repo_path)),
                str(tasks_yaml_path.relative_to(repo_path))
            ]

            add_result = add_files(str(repo_path), files_to_add)

            if add_result.get('success'):
                # Commit the changes
                commit_message = f"docs: Add task breakdown for {feature_id}"
                commit(str(repo_path), commit_message)

        return {
            'success': True,
            'tasks_path': str(written_md_path),
            'tasks_yaml_path': str(tasks_yaml_path),
            'task_count': len(all_tasks),
            'parallel_groups': parallel_groups,
            'categories': categories,
            'message': f"Generated {len(all_tasks)} tasks for feature {feature_id}"
        }

    except McpError:
        # Re-raise MCP errors as-is
        raise
    except Exception as e:
        # Wrap other exceptions in McpError
        raise McpError(
            code=-32603,  # Internal error
            message=f"Task generation failed: {str(e)}",
            data={"error_type": type(e).__name__}
        )