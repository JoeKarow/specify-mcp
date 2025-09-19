"""
MCP tool for generating implementation plans from specifications.

This module implements the plan tool that analyzes specifications
and generates detailed implementation plans with tech stack and phases.
"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastmcp.exceptions import McpError

from speckit_mcp.config.manager import ConfigurationManager
from speckit_mcp.resources.template_manager import TemplateManager
from speckit_mcp.resources.models import TemplateType
from speckit_mcp.utils.file_ops import safe_read, safe_write, ensure_directory


def _extract_feature_id_from_spec(spec_path: str) -> Optional[str]:
    """
    Extract feature ID from specification file.

    Args:
        spec_path: Path to specification file

    Returns:
        Feature ID or None if not found
    """
    # Try to extract from filename first
    filename = Path(spec_path).stem
    match = re.match(r'^(\d{3})-spec', filename)
    if match:
        return match.group(1)

    # Try to extract from content
    try:
        content = safe_read(spec_path)
        # Look for "Feature ID: XXX" pattern
        match = re.search(r'\*\*Feature ID\*\*:\s*(\d{3})', content)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None


def _analyze_spec_requirements(spec_content: str) -> Dict[str, Any]:
    """
    Analyze specification content to extract requirements and complexity.

    Args:
        spec_content: Specification markdown content

    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'functional_requirements': [],
        'non_functional_requirements': [],
        'estimated_complexity': 'medium',
        'suggested_tech': [],
        'phases': []
    }

    # Extract functional requirements
    fr_pattern = r'\*\*\[FR-\d+\]\*\*\s*(.+)'
    fr_matches = re.findall(fr_pattern, spec_content)
    analysis['functional_requirements'] = fr_matches

    # Extract non-functional requirements
    nfr_pattern = r'\*\*\[NFR-\d+\]\*\*\s*(.+)'
    nfr_matches = re.findall(nfr_pattern, spec_content)
    analysis['non_functional_requirements'] = nfr_matches

    # Estimate complexity based on requirements count
    total_requirements = len(fr_matches) + len(nfr_matches)
    if total_requirements <= 3:
        analysis['estimated_complexity'] = 'low'
    elif total_requirements <= 6:
        analysis['estimated_complexity'] = 'medium'
    else:
        analysis['estimated_complexity'] = 'high'

    # Extract phases from implementation plan section
    phase_pattern = r'###\s*Phase\s*\d+:\s*(.+)'
    phase_matches = re.findall(phase_pattern, spec_content)
    analysis['phases'] = phase_matches

    # Suggest technology based on content keywords
    content_lower = spec_content.lower()
    if 'api' in content_lower or 'endpoint' in content_lower:
        analysis['suggested_tech'].append('FastAPI')
    if 'database' in content_lower or 'data model' in content_lower:
        analysis['suggested_tech'].append('PostgreSQL')
    if 'async' in content_lower or 'concurrent' in content_lower:
        analysis['suggested_tech'].append('asyncio')
    if 'test' in content_lower:
        analysis['suggested_tech'].append('pytest')

    return analysis


def _determine_phases(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Determine implementation phases based on complexity.

    Args:
        analysis: Specification analysis results

    Returns:
        List of phase dictionaries
    """
    complexity = analysis.get('estimated_complexity', 'medium')

    if complexity == 'low':
        return [
            {'name': 'Foundation', 'duration': '1 day', 'description': 'Setup and core models'},
            {'name': 'Implementation', 'duration': '1 day', 'description': 'Main features'},
            {'name': 'Polish', 'duration': '1 day', 'description': 'Testing and docs'}
        ]
    elif complexity == 'medium':
        return [
            {'name': 'Foundation', 'duration': '2 days', 'description': 'Project setup and core models'},
            {'name': 'Implementation', 'duration': '3 days', 'description': 'Main features and integration'},
            {'name': 'Testing & Polish', 'duration': '2 days', 'description': 'Complete testing and documentation'}
        ]
    else:  # high complexity
        return [
            {'name': 'Research & Design', 'duration': '2 days', 'description': 'Architecture and design'},
            {'name': 'Foundation', 'duration': '3 days', 'description': 'Core infrastructure and models'},
            {'name': 'Implementation', 'duration': '5 days', 'description': 'Feature implementation'},
            {'name': 'Integration', 'duration': '3 days', 'description': 'System integration'},
            {'name': 'Testing & Polish', 'duration': '3 days', 'description': 'Comprehensive testing and docs'}
        ]


async def plan(spec_path: str, repository_path: str) -> Dict[str, Any]:
    """
    Generate implementation plan from specification.

    This MCP tool analyzes a specification file and generates a detailed
    implementation plan with tech stack, phases, and complexity estimates.

    Args:
        spec_path: Path to specification file
        repository_path: Path to git repository

    Returns:
        Dictionary containing:
            - success: Whether the operation succeeded
            - plan_path: Path to generated plan file
            - phases: List of implementation phases
            - estimated_complexity: Complexity estimate (low/medium/high)
            - tech_stack: Suggested technology stack
            - message: Status message

    Raises:
        McpError: If spec file not found or plan generation fails
    """
    try:
        # Validate paths
        spec_file = Path(spec_path)
        if not spec_file.exists():
            raise McpError(
                code=-32602,  # Invalid params
                message=f"Specification file not found: {spec_path}"
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

        # Check if plan workflow is enabled
        workflow_config = config.workflows.get('plan')
        if not workflow_config or not workflow_config.enabled:
            raise McpError(
                code=-32603,  # Internal error
                message="Plan workflow is not enabled in configuration"
            )

        # Read specification content
        spec_content = safe_read(spec_file)

        # Extract feature ID
        feature_id = _extract_feature_id_from_spec(str(spec_file))
        if not feature_id:
            # Generate a default ID if not found
            feature_id = datetime.now().strftime('%m%d')

        # Extract feature name from spec content
        feature_name_match = re.search(r'#\s*Feature Specification:\s*(.+)', spec_content)
        feature_name = feature_name_match.group(1) if feature_name_match else f"Feature {feature_id}"

        # Analyze specification
        analysis = _analyze_spec_requirements(spec_content)

        # Determine implementation phases
        phases = _determine_phases(analysis)

        # Generate plan from template
        template_manager = TemplateManager()
        template = template_manager.get_template(TemplateType.PLAN)

        # Prepare variables for template substitution
        variables = {
            'feature_id': feature_id,
            'feature_name': feature_name,
            'spec_path': str(spec_file),
            'date': datetime.now().strftime('%Y-%m-%d')
        }

        # Substitute variables in template
        plan_content = template_manager.substitute_variables(template, variables)

        # Create plans directory
        plans_dir = repo_path / '.specify-mcp' / 'plans'
        ensure_directory(plans_dir)

        # Write plan file
        plan_filename = f"{feature_id}-plan.md"
        plan_path = plans_dir / plan_filename

        written_path = safe_write(
            plan_path,
            plan_content,
            base_path=str(repo_path),
            overwrite=True  # Allow overwriting existing plans
        )

        # Prepare tech stack list
        tech_stack = analysis.get('suggested_tech', [])
        if not tech_stack:
            # Default tech stack
            tech_stack = ['Python 3.11+', 'FastMCP', 'pytest', 'PyYAML']

        # Auto-commit if enabled
        if config.settings.get('auto_commit', True):
            from speckit_mcp.git.operations import add_files, commit

            # Add the plan file to git
            add_result = add_files(
                str(repo_path),
                [str(written_path.relative_to(repo_path))]
            )

            if add_result.get('success'):
                # Commit the changes
                commit_message = f"docs: Add implementation plan for {feature_id}"
                commit(str(repo_path), commit_message)

        return {
            'success': True,
            'plan_path': str(written_path),
            'phases': phases,
            'estimated_complexity': analysis['estimated_complexity'],
            'tech_stack': tech_stack,
            'requirements_count': len(analysis['functional_requirements']) + len(analysis['non_functional_requirements']),
            'message': f"Generated implementation plan for feature {feature_id}"
        }

    except McpError:
        # Re-raise MCP errors as-is
        raise
    except Exception as e:
        # Wrap other exceptions in McpError
        raise McpError(
            code=-32603,  # Internal error
            message=f"Plan generation failed: {str(e)}",
            data={"error_type": type(e).__name__}
        )