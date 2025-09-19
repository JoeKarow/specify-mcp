"""
Configuration management for the SpecKit MCP server.

This module handles loading, saving, and managing project configurations
using YAML safe_load and Pydantic models for validation.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import ValidationError

from .models import ProjectConfiguration, ProjectInfo, Principle, WorkflowConfig, WorkflowType, GitConfig


class ConfigurationError(Exception):
    """Exception raised when configuration operations fail."""
    pass


class ConfigurationManager:
    """
    Manages project configuration with support for inheritance and validation.

    This class handles loading configurations from multiple sources (defaults,
    user, project) and merging them with proper precedence.
    """

    def __init__(self, repository_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            repository_path: Optional path to the repository root
        """
        self.repository_path = Path(repository_path) if repository_path else Path.cwd()
        self.config_dir = self.repository_path / '.specify-mcp'
        self.constitution_path = self.config_dir / 'constitution.yaml'

        # Cache for loaded configuration
        self._cached_config: Optional[ProjectConfiguration] = None

    def _get_default_configuration(self) -> Dict[str, Any]:
        """
        Get the default configuration.

        Returns:
            Dictionary with default configuration values
        """
        return {
            'project': {
                'name': self.repository_path.name,
                'description': 'SpecKit MCP managed project',
                'version': '1.0.0'
            },
            'principles': [
                {
                    'name': 'MCP Protocol Compliance',
                    'description': 'All functionality exposed through MCP tools and resources',
                    'priority': 1
                },
                {
                    'name': 'File System Preservation',
                    'description': 'Maintain git-integrated workflow without external dependencies',
                    'priority': 2
                },
                {
                    'name': 'Test-First Development',
                    'description': 'Write failing tests before implementation (TDD)',
                    'priority': 3
                },
                {
                    'name': 'Structured Data',
                    'description': 'YAML over markdown for machine-parsable data',
                    'priority': 4
                },
                {
                    'name': 'Simplicity',
                    'description': 'YAGNI - build MVP without premature features',
                    'priority': 5
                },
                {
                    'name': 'Cross-Platform',
                    'description': 'No shell dependencies, pure Python implementation',
                    'priority': 6
                }
            ],
            'git': {
                'default_branch': 'main'
            },
            'workflows': {
                'specify': {
                    'enabled': True,
                    'steps': [
                        'validate_repository',
                        'create_branch',
                        'generate_spec',
                        'commit_changes'
                    ],
                    'branch_prefix': 'feature/'
                },
                'plan': {
                    'enabled': True,
                    'steps': [
                        'load_spec',
                        'analyze_requirements',
                        'generate_plan',
                        'save_artifacts'
                    ]
                },
                'tasks': {
                    'enabled': True,
                    'steps': [
                        'load_plan',
                        'generate_tasks',
                        'apply_rules',
                        'save_tasks'
                    ]
                }
            },
            'templates': {},
            'settings': {
                'auto_commit': True,
                'verbose_logging': False,
                'max_parallel_tasks': 5
            }
        }

    def _get_user_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Get user-level configuration from ~/.specify-mcp/config.yaml.

        Returns:
            Dictionary with user configuration or None if not found
        """
        user_config_path = Path.home() / '.specify-mcp' / 'config.yaml'

        if not user_config_path.exists():
            return None

        try:
            with open(user_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, IOError) as e:
            # Log warning but don't fail
            print(f"Warning: Could not load user configuration: {e}")
            return None

    def _merge_configurations(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries with override taking precedence.

        Args:
            base: Base configuration dictionary
            override: Configuration to override base values

        Returns:
            Merged configuration dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configurations(result[key], value)
            else:
                # Override the value
                result[key] = value

        return result

    def load_configuration(self, force_reload: bool = False) -> ProjectConfiguration:
        """
        Load project configuration with inheritance (defaults -> user -> project).

        Args:
            force_reload: Whether to bypass cache and reload from disk

        Returns:
            Validated ProjectConfiguration object

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not force_reload and self._cached_config is not None:
            return self._cached_config

        # Start with defaults
        config_dict = self._get_default_configuration()

        # Merge user configuration if available
        user_config = self._get_user_configuration()
        if user_config:
            config_dict = self._merge_configurations(config_dict, user_config)

        # Merge project configuration if available
        if self.constitution_path.exists():
            try:
                with open(self.constitution_path, 'r', encoding='utf-8') as f:
                    project_config = yaml.safe_load(f) or {}
                    config_dict = self._merge_configurations(config_dict, project_config)
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in constitution.yaml: {e}")
            except IOError as e:
                raise ConfigurationError(f"Could not read constitution.yaml: {e}")

        # Validate and create ProjectConfiguration
        try:
            self._cached_config = ProjectConfiguration(**config_dict)
            return self._cached_config
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}")

    def save_configuration(
        self,
        config: ProjectConfiguration,
        path: Optional[Path] = None
    ) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: ProjectConfiguration object to save
            path: Optional path to save to (defaults to constitution.yaml)

        Raises:
            ConfigurationError: If save operation fails
        """
        save_path = path or self.constitution_path

        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary, excluding defaults
        config_dict = config.model_dump(exclude_defaults=False, exclude_unset=False)

        # Clean up the dictionary for YAML serialization
        config_dict = self._clean_for_yaml(config_dict)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    config_dict,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=120
                )

            # Clear cache after saving
            self._cached_config = None

        except IOError as e:
            raise ConfigurationError(f"Could not save configuration: {e}")

    def _clean_for_yaml(self, data: Any) -> Any:
        """
        Clean data for YAML serialization.

        Args:
            data: Data to clean

        Returns:
            Cleaned data suitable for YAML
        """
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Convert enum keys to strings
                if hasattr(key, 'value'):
                    key = key.value
                cleaned[key] = self._clean_for_yaml(value)
            return cleaned
        elif isinstance(data, list):
            return [self._clean_for_yaml(item) for item in data]
        elif hasattr(data, 'value'):  # Enum
            return data.value
        else:
            return data

    def create_constitution(
        self,
        project_name: str,
        description: Optional[str] = None,
        principles: Optional[list] = None
    ) -> ProjectConfiguration:
        """
        Create a new constitution.yaml file with initial configuration.

        Args:
            project_name: Name of the project
            description: Optional project description
            principles: Optional list of constitutional principles

        Returns:
            Created ProjectConfiguration object

        Raises:
            ConfigurationError: If constitution already exists
        """
        if self.constitution_path.exists():
            raise ConfigurationError(
                f"Constitution already exists at {self.constitution_path}"
            )

        # Build configuration
        config_dict = self._get_default_configuration()

        # Override with provided values
        config_dict['project']['name'] = project_name
        if description:
            config_dict['project']['description'] = description
        if principles:
            config_dict['principles'] = principles

        # Validate and save
        try:
            config = ProjectConfiguration(**config_dict)
            self.save_configuration(config)
            return config
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}")

    def update_constitution(
        self,
        updates: Dict[str, Any],
        merge: bool = True
    ) -> ProjectConfiguration:
        """
        Update the existing constitution with new values.

        Args:
            updates: Dictionary of updates to apply
            merge: Whether to merge with existing or replace

        Returns:
            Updated ProjectConfiguration object

        Raises:
            ConfigurationError: If update fails
        """
        if merge:
            # Load existing configuration
            current_config = self.load_configuration(force_reload=True)
            current_dict = current_config.model_dump(
                exclude_defaults=False,
                exclude_unset=False
            )

            # Merge updates
            updated_dict = self._merge_configurations(current_dict, updates)
        else:
            # Use updates directly
            updated_dict = updates

        # Validate and save
        try:
            config = ProjectConfiguration(**updated_dict)
            self.save_configuration(config)
            return config
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration update: {e}")

    def validate_configuration_file(self, file_path: str) -> bool:
        """
        Validate a configuration file without loading it.

        Args:
            file_path: Path to configuration file to validate

        Returns:
            True if configuration is valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)

            ProjectConfiguration(**config_dict)
            return True

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML: {e}")
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}")
        except IOError as e:
            raise ConfigurationError(f"Could not read file: {e}")

    def get_workflow_config(self, workflow_type: WorkflowType) -> Optional[WorkflowConfig]:
        """
        Get configuration for a specific workflow.

        Args:
            workflow_type: The workflow type to get configuration for

        Returns:
            WorkflowConfig object or None if not configured
        """
        config = self.load_configuration()
        return config.workflows.get(workflow_type)

    def is_workflow_enabled(self, workflow_type: WorkflowType) -> bool:
        """
        Check if a workflow is enabled.

        Args:
            workflow_type: The workflow type to check

        Returns:
            True if workflow is enabled
        """
        workflow_config = self.get_workflow_config(workflow_type)
        return workflow_config.enabled if workflow_config else False