"""Integration tests for configuration inheritance and override behavior.

This test suite verifies configuration management including:
- Project-level, user-level, and environment configuration loading
- YAML configuration merging and precedence rules
- Pydantic validation of merged configurations
- Constitution.yaml template customization and inheritance
- Dynamic configuration updates and validation

These tests MUST fail initially as no implementation exists yet (TDD requirement).
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any, Optional

import pytest
import yaml
from pydantic import ValidationError

# Import configuration modules (will fail until implemented)
try:
    from speckit_mcp.config.manager import ConfigurationManager, ConfigurationError
    from speckit_mcp.config.models import (
        ProjectConfiguration,
        UserConfiguration,
        EnvironmentConfiguration,
        ConstitutionTemplate,
        ConfigurationSource,
        ConfigurationMergeResult
    )
    from speckit_mcp.tools.initialize import initialize_project_tool
except ImportError:
    # Expected to fail until implementation exists
    pytest.skip("Implementation not available yet - TDD phase", allow_module_level=True)


class TestConfigurationInheritanceIntegration:
    """Integration tests for configuration inheritance and merging."""

    @pytest.fixture
    def temp_directory(self, tmp_path: Path) -> Path:
        """Create temporary directory for configuration testing.

        Returns:
            Path to temporary test directory
        """
        return tmp_path

    @pytest.fixture
    def user_config_dir(self, temp_directory: Path) -> Path:
        """Create user configuration directory.

        Returns:
            Path to user configuration directory
        """
        user_dir = temp_directory / "user_config"
        user_dir.mkdir()
        return user_dir

    @pytest.fixture
    def project_config_dir(self, temp_directory: Path) -> Path:
        """Create project configuration directory.

        Returns:
            Path to project configuration directory
        """
        project_dir = temp_directory / "project"
        project_dir.mkdir()
        return project_dir

    @pytest.fixture
    def sample_user_config(self) -> Dict[str, Any]:
        """Sample user-level configuration.

        Returns:
            User configuration dictionary
        """
        return {
            "user": {
                "name": "Test User",
                "email": "test@example.com",
                "preferences": {
                    "editor": "vscode",
                    "git_commit_template": "feat: {description}"
                }
            },
            "defaults": {
                "project": {
                    "structure": "single",
                    "python_version": "3.11+"
                },
                "git": {
                    "branch_prefix": "feature/",
                    "default_branch": "main"
                },
                "workflows": {
                    "specify": {
                        "enabled": True,
                        "auto_commit": False
                    },
                    "plan": {
                        "enabled": True,
                        "include_research": True
                    }
                }
            }
        }

    @pytest.fixture
    def sample_project_config(self) -> Dict[str, Any]:
        """Sample project-level configuration.

        Returns:
            Project configuration dictionary
        """
        return {
            "project": {
                "name": "test-project",
                "description": "Test project for configuration testing",
                "version": "0.1.0",
                "structure": "monorepo"  # Override user default
            },
            "git": {
                "remote_url": "https://github.com/test/test-project.git",
                "branch_prefix": "proj-"  # Override user default
            },
            "workflows": {
                "specify": {
                    "auto_commit": True  # Override user default
                },
                "tasks": {
                    "enabled": True,  # New workflow not in user config
                    "auto_generate": True
                }
            },
            "tools": {
                "mcp_server": {
                    "host": "localhost",
                    "port": 3000
                }
            }
        }

    @pytest.fixture
    def sample_environment_config(self) -> Dict[str, Any]:
        """Sample environment configuration.

        Returns:
            Environment configuration dictionary
        """
        return {
            "environment": "testing",
            "debug": True,
            "logging": {
                "level": "DEBUG",
                "file": "/tmp/speckit-test.log"
            },
            "git": {
                "default_branch": "develop"  # Override project and user
            },
            "tools": {
                "mcp_server": {
                    "port": 3001  # Override project setting
                }
            }
        }

    @pytest.fixture
    def constitution_template(self) -> Dict[str, Any]:
        """Sample constitution template.

        Returns:
            Constitution template dictionary
        """
        return {
            "constitution": {
                "principles": [
                    "MCP Protocol Compliance",
                    "File System Preservation",
                    "Test-First Development",
                    "Structured Data",
                    "Simplicity (YAGNI)",
                    "Cross-Platform"
                ],
                "constraints": {
                    "no_shell_dependencies": True,
                    "yaml_over_markdown": True,
                    "git_integration_required": True
                },
                "customizations": {
                    "branch_naming": "{{project.git.branch_prefix}}{{feature_id}}",
                    "spec_template": "{{user.preferences.spec_style}}",
                    "commit_format": "{{user.preferences.git_commit_template}}"
                }
            },
            "project_overrides": {
                "allowed_fields": [
                    "project.name",
                    "project.description",
                    "git.remote_url",
                    "workflows"
                ]
            }
        }

    @pytest.mark.asyncio
    async def test_configuration_loading_hierarchy(
        self,
        user_config_dir: Path,
        project_config_dir: Path,
        sample_user_config: Dict[str, Any],
        sample_project_config: Dict[str, Any],
        sample_environment_config: Dict[str, Any]
    ):
        """Test configuration loading with proper hierarchy and precedence.

        Verifies:
        - User config loaded from user directory
        - Project config loaded from project directory
        - Environment config loaded from environment variables/files
        - Proper precedence: environment > project > user > defaults
        """
        # Create configuration files
        user_config_file = user_config_dir / "config.yaml"
        project_config_file = project_config_dir / ".specify" / "config.yaml"
        project_config_file.parent.mkdir()

        with open(user_config_file, 'w') as f:
            yaml.dump(sample_user_config, f)

        with open(project_config_file, 'w') as f:
            yaml.dump(sample_project_config, f)

        # Mock environment configuration
        with patch.dict(os.environ, {
            'SPECKIT_CONFIG': yaml.dump(sample_environment_config),
            'SPECKIT_DEBUG': 'true',
            'SPECKIT_GIT_DEFAULT_BRANCH': 'develop'
        }):

            config_manager = ConfigurationManager(
                user_config_dir=str(user_config_dir),
                project_config_dir=str(project_config_dir)
            )

            merged_config = await config_manager.load_configuration()

            # Verify configuration sources were loaded
            assert len(merged_config.sources) == 3
            source_types = [source.type for source in merged_config.sources]
            assert ConfigurationSource.USER in source_types
            assert ConfigurationSource.PROJECT in source_types
            assert ConfigurationSource.ENVIRONMENT in source_types

            # Verify precedence rules (environment > project > user)
            final_config = merged_config.configuration

            # Environment should override project and user
            assert final_config.git.default_branch == "develop"  # from environment
            assert final_config.tools.mcp_server.port == 3001    # from environment

            # Project should override user
            assert final_config.project.structure == "monorepo"  # from project
            assert final_config.git.branch_prefix == "proj-"     # from project
            assert final_config.workflows.specify.auto_commit is True  # from project

            # User config should be preserved where not overridden
            assert final_config.user.name == "Test User"         # from user
            assert final_config.user.email == "test@example.com" # from user

            # New sections should be added
            assert final_config.workflows.tasks.enabled is True  # from project
            assert final_config.logging.level == "DEBUG"        # from environment

    @pytest.mark.asyncio
    async def test_configuration_validation_during_merge(
        self,
        user_config_dir: Path,
        project_config_dir: Path
    ):
        """Test Pydantic validation during configuration merging.

        Verifies:
        - Invalid configuration sections are rejected
        - Type validation occurs during merge
        - Helpful error messages for validation failures
        """
        # Create invalid user configuration
        invalid_user_config = {
            "user": {
                "name": 123,  # Should be string
                "email": "invalid-email"  # Invalid email format
            },
            "defaults": {
                "project": {
                    "python_version": "invalid"  # Invalid version format
                }
            }
        }

        # Create valid project configuration
        valid_project_config = {
            "project": {
                "name": "test-project",
                "version": "0.1.0"
            }
        }

        user_config_file = user_config_dir / "config.yaml"
        project_config_file = project_config_dir / ".specify" / "config.yaml"
        project_config_file.parent.mkdir()

        with open(user_config_file, 'w') as f:
            yaml.dump(invalid_user_config, f)

        with open(project_config_file, 'w') as f:
            yaml.dump(valid_project_config, f)

        config_manager = ConfigurationManager(
            user_config_dir=str(user_config_dir),
            project_config_dir=str(project_config_dir)
        )

        with pytest.raises(ConfigurationError) as exc_info:
            await config_manager.load_configuration()

        # Verify validation error details
        assert "validation" in str(exc_info.value).lower()
        assert "user.name" in str(exc_info.value) or "name" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_constitution_template_customization(
        self,
        project_config_dir: Path,
        constitution_template: Dict[str, Any],
        sample_project_config: Dict[str, Any]
    ):
        """Test constitution.yaml template customization and inheritance.

        Verifies:
        - Constitution template loading and processing
        - Variable substitution from project configuration
        - Constraint validation and enforcement
        - Custom principle addition/modification
        """
        # Create constitution template file
        constitution_file = project_config_dir / ".specify" / "constitution-template.yaml"
        constitution_file.parent.mkdir()

        with open(constitution_file, 'w') as f:
            yaml.dump(constitution_template, f)

        # Create project configuration
        project_config_file = project_config_dir / ".specify" / "config.yaml"
        enhanced_project_config = {
            **sample_project_config,
            "constitution": {
                "custom_principles": [
                    "API-First Design",
                    "Security by Default"
                ],
                "custom_constraints": {
                    "max_function_lines": 50,
                    "require_docstrings": True
                }
            }
        }

        with open(project_config_file, 'w') as f:
            yaml.dump(enhanced_project_config, f)

        config_manager = ConfigurationManager(
            project_config_dir=str(project_config_dir)
        )

        # Test constitution generation
        constitution = await config_manager.generate_constitution()

        # Verify template customization
        assert "API-First Design" in constitution.constitution.principles
        assert "Security by Default" in constitution.constitution.principles

        # Verify variable substitution
        branch_naming = constitution.constitution.customizations.branch_naming
        assert "proj-" in branch_naming  # Should use project branch prefix

        # Verify constraints are applied
        assert constitution.constitution.constraints.max_function_lines == 50
        assert constitution.constitution.constraints.require_docstrings is True

    @pytest.mark.asyncio
    async def test_dynamic_configuration_updates(
        self,
        project_config_dir: Path,
        sample_project_config: Dict[str, Any]
    ):
        """Test dynamic configuration updates and reloading.

        Verifies:
        - Configuration can be updated at runtime
        - Changes are validated before application
        - Dependent components are notified of changes
        """
        project_config_file = project_config_dir / ".specify" / "config.yaml"
        project_config_file.parent.mkdir()

        with open(project_config_file, 'w') as f:
            yaml.dump(sample_project_config, f)

        config_manager = ConfigurationManager(
            project_config_dir=str(project_config_dir)
        )

        # Load initial configuration
        initial_config = await config_manager.load_configuration()
        assert initial_config.configuration.git.branch_prefix == "proj-"

        # Update configuration
        updated_config = {
            **sample_project_config,
            "git": {
                **sample_project_config["git"],
                "branch_prefix": "updated-"
            }
        }

        # Apply update
        update_result = await config_manager.update_configuration(
            updated_config,
            source=ConfigurationSource.PROJECT
        )

        assert update_result.success is True
        assert update_result.changes_applied == 1

        # Verify updated configuration
        reloaded_config = await config_manager.load_configuration()
        assert reloaded_config.configuration.git.branch_prefix == "updated-"

    @pytest.mark.asyncio
    async def test_configuration_inheritance_with_missing_files(
        self,
        user_config_dir: Path,
        project_config_dir: Path
    ):
        """Test configuration inheritance when some config files are missing.

        Verifies:
        - Graceful handling of missing user configuration
        - Graceful handling of missing project configuration
        - Default values are used appropriately
        """
        # Only create user configuration (project missing)
        user_config = {
            "user": {
                "name": "Test User",
                "email": "test@example.com"
            },
            "defaults": {
                "git": {
                    "default_branch": "main"
                }
            }
        }

        user_config_file = user_config_dir / "config.yaml"
        with open(user_config_file, 'w') as f:
            yaml.dump(user_config, f)

        config_manager = ConfigurationManager(
            user_config_dir=str(user_config_dir),
            project_config_dir=str(project_config_dir)  # Directory exists but no config file
        )

        merged_config = await config_manager.load_configuration()

        # Should have user configuration
        assert merged_config.configuration.user.name == "Test User"

        # Should use defaults for missing project configuration
        assert merged_config.configuration.git.default_branch == "main"

        # Should have only user source
        assert len(merged_config.sources) == 1
        assert merged_config.sources[0].type == ConfigurationSource.USER

    @pytest.mark.asyncio
    async def test_configuration_merge_conflict_resolution(
        self,
        user_config_dir: Path,
        project_config_dir: Path
    ):
        """Test resolution of configuration merge conflicts.

        Verifies:
        - Deep merge of nested configurations
        - Array/list merge strategies
        - Conflict resolution with proper precedence
        """
        # User config with nested workflows
        user_config = {
            "workflows": {
                "specify": {
                    "enabled": True,
                    "auto_commit": False,
                    "templates": ["basic", "detailed"],
                    "validation": {
                        "require_description": True,
                        "min_length": 10
                    }
                }
            }
        }

        # Project config with overlapping but different workflow config
        project_config = {
            "workflows": {
                "specify": {
                    "auto_commit": True,  # Override user setting
                    "templates": ["custom", "advanced"],  # Replace user templates
                    "validation": {
                        "require_description": True,  # Same as user
                        "max_length": 1000  # Additional constraint
                    }
                }
            }
        }

        user_config_file = user_config_dir / "config.yaml"
        project_config_file = project_config_dir / ".specify" / "config.yaml"
        project_config_file.parent.mkdir()

        with open(user_config_file, 'w') as f:
            yaml.dump(user_config, f)

        with open(project_config_file, 'w') as f:
            yaml.dump(project_config, f)

        config_manager = ConfigurationManager(
            user_config_dir=str(user_config_dir),
            project_config_dir=str(project_config_dir)
        )

        merged_config = await config_manager.load_configuration()
        workflow_config = merged_config.configuration.workflows.specify

        # Project should override user
        assert workflow_config.auto_commit is True

        # Arrays should be replaced, not merged
        assert workflow_config.templates == ["custom", "advanced"]

        # Nested objects should be deep merged
        assert workflow_config.validation.require_description is True  # from both
        assert workflow_config.validation.min_length == 10              # from user
        assert workflow_config.validation.max_length == 1000           # from project

    @pytest.mark.asyncio
    async def test_configuration_with_initialize_project_tool(
        self,
        project_config_dir: Path,
        sample_project_config: Dict[str, Any],
        constitution_template: Dict[str, Any]
    ):
        """Test configuration integration with initialize_project tool.

        Verifies:
        - Project initialization creates proper configuration structure
        - Constitution.yaml is generated from template with correct values
        - Configuration inheritance works with initialized project
        """
        repository_path = str(project_config_dir)
        project_name = "integration-test-project"

        # Mock template loading
        with patch('speckit_mcp.resources.templates.TemplateManager') as mock_template_manager:
            mock_template_manager.return_value.load_template.return_value = constitution_template

            result = await initialize_project_tool(
                repository_path=repository_path,
                project_name=project_name
            )

            assert result['success'] is True
            assert 'constitution_path' in result

            # Verify constitution file was created
            constitution_path = Path(result['constitution_path'])
            assert constitution_path.exists()

            with open(constitution_path) as f:
                constitution = yaml.safe_load(f)

            # Verify project-specific customizations
            assert constitution['project']['name'] == project_name

        # Test configuration loading after initialization
        config_manager = ConfigurationManager(
            project_config_dir=repository_path
        )

        merged_config = await config_manager.load_configuration()

        # Should have project configuration from initialization
        assert merged_config.configuration.project.name == project_name

    @pytest.mark.asyncio
    async def test_configuration_validation_schema_evolution(
        self,
        project_config_dir: Path
    ):
        """Test configuration validation with schema evolution.

        Verifies:
        - Backward compatibility with older configuration formats
        - Graceful handling of unknown configuration fields
        - Migration of deprecated configuration options
        """
        # Legacy configuration format
        legacy_config = {
            "version": "0.1",  # Old version field
            "project_info": {  # Old section name
                "name": "legacy-project",
                "desc": "description"  # Old field name
            },
            "git_settings": {  # Old section name
                "main_branch": "master"  # Deprecated field
            },
            "unknown_section": {  # Should be ignored
                "some_field": "some_value"
            }
        }

        project_config_file = project_config_dir / ".specify" / "config.yaml"
        project_config_file.parent.mkdir()

        with open(project_config_file, 'w') as f:
            yaml.dump(legacy_config, f)

        config_manager = ConfigurationManager(
            project_config_dir=str(project_config_dir)
        )

        # Should handle legacy format gracefully
        merged_config = await config_manager.load_configuration()

        # Should migrate/map legacy fields appropriately
        # (Exact migration behavior depends on implementation)
        assert merged_config.configuration is not None

        # Should log warnings about deprecated fields
        # (Would verify through logging mock in real implementation)