"""
Unit tests for configuration management module.

These tests verify ConfigManager functionality, YAML loading/saving,
configuration merging, inheritance, and Pydantic model validation.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch
import pytest
import yaml
from pydantic import ValidationError

from speckit_mcp.config.manager import ConfigurationManager, ConfigurationError
from speckit_mcp.config.models import (
    ProjectConfiguration, ProjectInfo, Principle, WorkflowConfig, GitConfig,
    WorkflowType, Task, TaskStatus, TaskCategory, WorkflowSession, SessionStatus,
    RepositoryRegistration
)


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_configuration_error_init(self):
        """Test ConfigurationError initialization."""
        error = ConfigurationError("Test configuration error")
        assert str(error) == "Test configuration error"


class TestProjectInfo:
    """Test ProjectInfo model validation."""

    def test_project_info_valid(self):
        """Test valid ProjectInfo creation."""
        info = ProjectInfo(
            name="Test Project",
            description="A test project",
            version="1.2.3"
        )
        assert info.name == "Test Project"
        assert info.description == "A test project"
        assert info.version == "1.2.3"

    def test_project_info_minimal(self):
        """Test ProjectInfo with minimal required fields."""
        info = ProjectInfo(name="MinimalProject")
        assert info.name == "MinimalProject"
        assert info.description is None
        assert info.version == "1.0.0"  # default

    def test_project_info_invalid_name(self):
        """Test ProjectInfo with invalid name."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectInfo(name="")

        errors = exc_info.value.errors()
        assert any(error['type'] == 'string_too_short' for error in errors)

    def test_project_info_invalid_version(self):
        """Test ProjectInfo with invalid version format."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectInfo(name="Test", version="invalid")

        errors = exc_info.value.errors()
        assert any(error['type'] == 'string_pattern_mismatch' for error in errors)

    def test_project_info_strip_whitespace(self):
        """Test ProjectInfo strips whitespace."""
        info = ProjectInfo(name="  Test Project  ")
        assert info.name == "Test Project"


class TestPrinciple:
    """Test Principle model validation."""

    def test_principle_valid(self):
        """Test valid Principle creation."""
        principle = Principle(
            name="Test Principle",
            description="A test principle",
            priority=5
        )
        assert principle.name == "Test Principle"
        assert principle.description == "A test principle"
        assert principle.priority == 5

    def test_principle_invalid_priority_low(self):
        """Test Principle with priority too low."""
        with pytest.raises(ValidationError) as exc_info:
            Principle(
                name="Test",
                description="Test",
                priority=0
            )

        errors = exc_info.value.errors()
        assert any(error['type'] == 'greater_than_equal' for error in errors)

    def test_principle_invalid_priority_high(self):
        """Test Principle with priority too high."""
        with pytest.raises(ValidationError) as exc_info:
            Principle(
                name="Test",
                description="Test",
                priority=11
            )

        errors = exc_info.value.errors()
        assert any(error['type'] == 'less_than_equal' for error in errors)

    def test_principle_empty_fields(self):
        """Test Principle with empty required fields."""
        with pytest.raises(ValidationError) as exc_info:
            Principle(
                name="",
                description="",
                priority=1
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Both name and description should fail


class TestWorkflowConfig:
    """Test WorkflowConfig model validation."""

    def test_workflow_config_valid(self):
        """Test valid WorkflowConfig creation."""
        config = WorkflowConfig(
            enabled=True,
            steps=["step1", "step2"],
            branch_prefix="feature/"
        )
        assert config.enabled is True
        assert config.steps == ["step1", "step2"]
        assert config.branch_prefix == "feature/"

    def test_workflow_config_defaults(self):
        """Test WorkflowConfig default values."""
        config = WorkflowConfig()
        assert config.enabled is True
        assert config.steps == []
        assert config.branch_prefix is None


class TestGitConfig:
    """Test GitConfig model validation."""

    def test_git_config_valid(self):
        """Test valid GitConfig creation."""
        config = GitConfig(
            remote_url="https://github.com/user/repo.git",
            default_branch="main"
        )
        assert config.remote_url == "https://github.com/user/repo.git"
        assert config.default_branch == "main"

    def test_git_config_defaults(self):
        """Test GitConfig default values."""
        config = GitConfig()
        assert config.remote_url is None
        assert config.default_branch == "main"


class TestProjectConfiguration:
    """Test ProjectConfiguration model validation."""

    def test_project_configuration_valid(self):
        """Test valid ProjectConfiguration creation."""
        config = ProjectConfiguration(
            project=ProjectInfo(name="Test Project"),
            principles=[
                Principle(name="Test", description="Test principle", priority=1)
            ],
            workflows={
                WorkflowType.SPECIFY: WorkflowConfig(enabled=True)
            }
        )
        assert config.project.name == "Test Project"
        assert len(config.principles) == 1
        assert WorkflowType.SPECIFY in config.workflows

    def test_project_configuration_adds_default_principles(self):
        """Test ProjectConfiguration adds default principles when none provided."""
        config = ProjectConfiguration(
            project=ProjectInfo(name="Test Project")
        )
        assert len(config.principles) >= 2
        assert any(p.name == "MCP Protocol Compliance" for p in config.principles)
        assert any(p.name == "File System Preservation" for p in config.principles)

    def test_project_configuration_adds_default_workflows(self):
        """Test ProjectConfiguration adds default workflows when none provided."""
        config = ProjectConfiguration(
            project=ProjectInfo(name="Test Project")
        )
        assert len(config.workflows) == 3
        assert WorkflowType.SPECIFY in config.workflows
        assert WorkflowType.PLAN in config.workflows
        assert WorkflowType.TASKS in config.workflows

    def test_project_configuration_invalid_workflow_type(self):
        """Test ProjectConfiguration with invalid workflow type."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectConfiguration(
                project=ProjectInfo(name="Test Project"),
                workflows={"invalid_workflow": WorkflowConfig()}
            )

        errors = exc_info.value.errors()
        # Check that validation failed for invalid workflow type
        assert len(errors) > 0
        assert any(error['type'] == 'enum' for error in errors)


class TestTask:
    """Test Task model validation."""

    def test_task_valid(self):
        """Test valid Task creation."""
        task = Task(
            task_id="T001",
            order=1,
            description="Test task",
            category=TaskCategory.IMPLEMENT,
            specification_ref="spec-001"
        )
        assert task.task_id == "T001"
        assert task.order == 1
        assert task.description == "Test task"
        assert task.category == TaskCategory.IMPLEMENT
        assert task.status == TaskStatus.PENDING  # default
        assert task.specification_ref == "spec-001"

    def test_task_invalid_id(self):
        """Test Task with invalid ID format."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                task_id="invalid@id",
                order=1,
                description="Test",
                category=TaskCategory.IMPLEMENT,
                specification_ref="spec-001"
            )

        errors = exc_info.value.errors()
        assert any("alphanumeric" in str(error['ctx']) for error in errors if error.get('ctx'))

    def test_task_invalid_order(self):
        """Test Task with invalid order."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                task_id="T001",
                order=0,
                description="Test",
                category=TaskCategory.IMPLEMENT,
                specification_ref="spec-001"
            )

        errors = exc_info.value.errors()
        assert any(error['type'] == 'greater_than_equal' for error in errors)


class TestWorkflowSession:
    """Test WorkflowSession model validation."""

    def test_workflow_session_valid(self):
        """Test valid WorkflowSession creation."""
        session = WorkflowSession(
            workflow_type=WorkflowType.SPECIFY,
            repository_path="/abs/path/to/repo",
            branch_name="feature-test",
            feature_description="Test feature"
        )
        assert session.workflow_type == WorkflowType.SPECIFY
        assert session.repository_path == "/abs/path/to/repo"
        assert session.branch_name == "feature-test"
        assert session.feature_description == "Test feature"
        assert session.status == SessionStatus.INITIALIZING  # default

    def test_workflow_session_invalid_path(self):
        """Test WorkflowSession with relative path."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowSession(
                workflow_type=WorkflowType.SPECIFY,
                repository_path="relative/path",
                branch_name="feature-test",
                feature_description="Test feature"
            )

        errors = exc_info.value.errors()
        assert any("absolute" in str(error['ctx']) for error in errors if error.get('ctx'))

    def test_workflow_session_invalid_branch_name(self):
        """Test WorkflowSession with invalid branch name."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowSession(
                workflow_type=WorkflowType.SPECIFY,
                repository_path="/abs/path/to/repo",
                branch_name="invalid branch name",
                feature_description="Test feature"
            )

        errors = exc_info.value.errors()
        assert any("invalid characters" in str(error['ctx']) for error in errors if error.get('ctx'))

    def test_workflow_session_completion_time(self):
        """Test WorkflowSession auto-sets completion time."""
        session = WorkflowSession(
            workflow_type=WorkflowType.SPECIFY,
            repository_path="/abs/path/to/repo",
            branch_name="feature-test",
            feature_description="Test feature",
            status=SessionStatus.COMPLETED
        )
        assert session.completed_at is not None


class TestRepositoryRegistration:
    """Test RepositoryRegistration model validation."""

    def test_repository_registration_valid(self):
        """Test valid RepositoryRegistration creation."""
        registration = RepositoryRegistration(
            repository_id="repo-001",
            repository_path="/abs/path/to/repo",
            config_path="/abs/path/to/repo/.specify-mcp/constitution.yaml"
        )
        assert registration.repository_id == "repo-001"
        assert registration.repository_path == "/abs/path/to/repo"
        assert registration.config_path.endswith("constitution.yaml")

    def test_repository_registration_invalid_config_path(self):
        """Test RepositoryRegistration with invalid config path."""
        with pytest.raises(ValidationError) as exc_info:
            RepositoryRegistration(
                repository_id="repo-001",
                repository_path="/abs/path/to/repo",
                config_path="/abs/path/to/repo/wrong-file.yaml"
            )

        errors = exc_info.value.errors()
        assert any("constitution.yaml" in str(error['ctx']) for error in errors if error.get('ctx'))

    def test_repository_registration_config_outside_repo(self):
        """Test RepositoryRegistration with config path outside repository."""
        with pytest.raises(ValidationError) as exc_info:
            RepositoryRegistration(
                repository_id="repo-001",
                repository_path="/abs/path/to/repo",
                config_path="/different/path/constitution.yaml"
            )

        errors = exc_info.value.errors()
        assert any("within repository" in str(error['ctx']) for error in errors if error.get('ctx'))


class TestConfigurationManager:
    """Test ConfigurationManager functionality."""

    def test_configuration_manager_init(self):
        """Test ConfigurationManager initialization."""
        manager = ConfigurationManager("/test/repo")
        assert manager.repository_path == Path("/test/repo")
        assert manager.config_dir == Path("/test/repo/.specify-mcp")
        assert manager.constitution_path == Path("/test/repo/.specify-mcp/constitution.yaml")

    def test_configuration_manager_default_path(self):
        """Test ConfigurationManager with default path."""
        with patch('pathlib.Path.cwd', return_value=Path("/current/dir")):
            manager = ConfigurationManager()
            assert manager.repository_path == Path("/current/dir")

    def test_get_default_configuration(self):
        """Test _get_default_configuration method."""
        manager = ConfigurationManager("/test/repo")
        defaults = manager._get_default_configuration()

        assert 'project' in defaults
        assert 'principles' in defaults
        assert 'workflows' in defaults
        assert 'git' in defaults
        assert defaults['project']['name'] == "repo"  # from path name

    @patch('pathlib.Path.home')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_get_user_configuration_exists(self, mock_yaml, mock_file, mock_home):
        """Test _get_user_configuration when file exists."""
        mock_home.return_value = Path("/home/user")
        mock_yaml.return_value = {"settings": {"verbose_logging": True}}

        with patch('pathlib.Path.exists', return_value=True):
            manager = ConfigurationManager("/test/repo")
            user_config = manager._get_user_configuration()

        assert user_config == {"settings": {"verbose_logging": True}}
        mock_file.assert_called_once()

    @patch('pathlib.Path.home')
    def test_get_user_configuration_not_exists(self, mock_home):
        """Test _get_user_configuration when file doesn't exist."""
        mock_home.return_value = Path("/home/user")

        with patch('pathlib.Path.exists', return_value=False):
            manager = ConfigurationManager("/test/repo")
            user_config = manager._get_user_configuration()

        assert user_config is None

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('pathlib.Path.home')
    def test_get_user_configuration_yaml_error(self, mock_home, mock_yaml, mock_file):
        """Test _get_user_configuration with YAML error."""
        mock_home.return_value = Path("/home/user")
        mock_yaml.side_effect = yaml.YAMLError("Invalid YAML")

        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.print') as mock_print:
                manager = ConfigurationManager("/test/repo")
                user_config = manager._get_user_configuration()

        assert user_config is None
        mock_print.assert_called_once()

    def test_merge_configurations_simple(self):
        """Test _merge_configurations with simple values."""
        manager = ConfigurationManager("/test/repo")
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        result = manager._merge_configurations(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_configurations_nested(self):
        """Test _merge_configurations with nested dictionaries."""
        manager = ConfigurationManager("/test/repo")
        base = {"nested": {"a": 1, "b": 2}, "simple": "value"}
        override = {"nested": {"b": 3, "c": 4}}

        result = manager._merge_configurations(base, override)

        assert result == {
            "nested": {"a": 1, "b": 3, "c": 4},
            "simple": "value"
        }

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_configuration_success(self, mock_yaml, mock_file):
        """Test successful configuration loading."""
        # Mock project config file
        mock_yaml.return_value = {
            "project": {"name": "Test Project"},
            "settings": {"custom": "value"}
        }

        manager = ConfigurationManager("/test/repo")

        with patch('pathlib.Path.exists', return_value=True):
            config = manager.load_configuration()

        assert isinstance(config, ProjectConfiguration)
        assert config.project.name == "Test Project"
        # Should be cached
        assert manager._cached_config is not None

    def test_load_configuration_cached(self):
        """Test configuration loading uses cache."""
        manager = ConfigurationManager("/test/repo")
        cached_config = ProjectConfiguration(
            project=ProjectInfo(name="Cached Project")
        )
        manager._cached_config = cached_config

        config = manager.load_configuration()

        assert config is cached_config

    def test_load_configuration_force_reload(self):
        """Test configuration loading bypasses cache with force_reload."""
        manager = ConfigurationManager("/test/repo")
        manager._cached_config = ProjectConfiguration(
            project=ProjectInfo(name="Cached Project")
        )

        with patch('pathlib.Path.exists', return_value=False):
            config = manager.load_configuration(force_reload=True)

        # Should get new config, not cached
        assert config.project.name != "Cached Project"

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_configuration_yaml_error(self, mock_yaml, mock_file):
        """Test configuration loading with YAML error."""
        mock_yaml.side_effect = yaml.YAMLError("Invalid YAML")

        manager = ConfigurationManager("/test/repo")

        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ConfigurationError) as exc_info:
                manager.load_configuration()

        assert "Invalid YAML" in str(exc_info.value)

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_dump')
    def test_save_configuration_success(self, mock_yaml_dump, mock_file):
        """Test successful configuration saving."""
        config = ProjectConfiguration(
            project=ProjectInfo(name="Test Project")
        )

        manager = ConfigurationManager("/test/repo")

        with patch('pathlib.Path.mkdir') as mock_mkdir:
            manager.save_configuration(config)

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_yaml_dump.assert_called_once()
        # Cache should be cleared
        assert manager._cached_config is None

    @patch('builtins.open')
    def test_save_configuration_io_error(self, mock_file):
        """Test configuration saving with IO error."""
        mock_file.side_effect = IOError("Permission denied")
        config = ProjectConfiguration(
            project=ProjectInfo(name="Test Project")
        )

        manager = ConfigurationManager("/test/repo")

        with patch('pathlib.Path.mkdir'):
            with pytest.raises(ConfigurationError) as exc_info:
                manager.save_configuration(config)

        assert "Could not save configuration" in str(exc_info.value)

    def test_clean_for_yaml_enum(self):
        """Test _clean_for_yaml with enum values."""
        manager = ConfigurationManager("/test/repo")

        # Mock enum with value attribute
        mock_enum = Mock()
        mock_enum.value = "enum_value"

        data = {"enum_key": mock_enum, "normal": "value"}
        result = manager._clean_for_yaml(data)

        assert result == {"enum_key": "enum_value", "normal": "value"}

    def test_clean_for_yaml_nested(self):
        """Test _clean_for_yaml with nested structures."""
        manager = ConfigurationManager("/test/repo")

        mock_enum = Mock()
        mock_enum.value = "nested_enum"

        data = {
            "list": [mock_enum, "string"],
            "dict": {"nested_enum": mock_enum}
        }
        result = manager._clean_for_yaml(data)

        assert result == {
            "list": ["nested_enum", "string"],
            "dict": {"nested_enum": "nested_enum"}
        }

    def test_create_constitution_success(self):
        """Test successful constitution creation."""
        manager = ConfigurationManager("/test/repo")

        with patch('pathlib.Path.exists', return_value=False):
            with patch.object(manager, 'save_configuration') as mock_save:
                config = manager.create_constitution(
                    "New Project",
                    "A new project",
                    [{"name": "Custom", "description": "Custom principle", "priority": 1}]
                )

        assert config.project.name == "New Project"
        assert config.project.description == "A new project"
        mock_save.assert_called_once()

    def test_create_constitution_already_exists(self):
        """Test constitution creation when file already exists."""
        manager = ConfigurationManager("/test/repo")

        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ConfigurationError) as exc_info:
                manager.create_constitution("Test Project")

        assert "Constitution already exists" in str(exc_info.value)

    def test_update_constitution_merge(self):
        """Test constitution update with merge."""
        manager = ConfigurationManager("/test/repo")
        existing_config = ProjectConfiguration(
            project=ProjectInfo(name="Existing Project")
        )

        with patch.object(manager, 'load_configuration', return_value=existing_config):
            with patch.object(manager, 'save_configuration') as mock_save:
                updates = {"project": {"description": "Updated description"}}
                config = manager.update_constitution(updates, merge=True)

        assert config.project.name == "Existing Project"
        assert config.project.description == "Updated description"
        mock_save.assert_called_once()

    def test_update_constitution_replace(self):
        """Test constitution update with replace."""
        manager = ConfigurationManager("/test/repo")

        with patch.object(manager, 'save_configuration') as mock_save:
            updates = {
                "project": {"name": "New Project"},
                "principles": [],
                "workflows": {}
            }
            config = manager.update_constitution(updates, merge=False)

        assert config.project.name == "New Project"
        mock_save.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_validate_configuration_file_valid(self, mock_yaml, mock_file):
        """Test configuration file validation with valid file."""
        mock_yaml.return_value = {
            "project": {"name": "Valid Project"}
        }

        manager = ConfigurationManager("/test/repo")
        result = manager.validate_configuration_file("/test/config.yaml")

        assert result is True

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_validate_configuration_file_invalid(self, mock_yaml, mock_file):
        """Test configuration file validation with invalid file."""
        mock_yaml.return_value = {
            "project": {"name": ""}  # Invalid: empty name
        }

        manager = ConfigurationManager("/test/repo")

        with pytest.raises(ConfigurationError) as exc_info:
            manager.validate_configuration_file("/test/config.yaml")

        assert "Invalid configuration" in str(exc_info.value)

    def test_get_workflow_config_exists(self):
        """Test get_workflow_config for existing workflow."""
        manager = ConfigurationManager("/test/repo")
        config = ProjectConfiguration(
            project=ProjectInfo(name="Test"),
            workflows={
                WorkflowType.SPECIFY: WorkflowConfig(enabled=False)
            }
        )

        with patch.object(manager, 'load_configuration', return_value=config):
            workflow_config = manager.get_workflow_config(WorkflowType.SPECIFY)

        assert workflow_config is not None
        assert workflow_config.enabled is False

    def test_get_workflow_config_not_exists(self):
        """Test get_workflow_config for non-existing workflow."""
        manager = ConfigurationManager("/test/repo")
        # Create config without the specific workflow but with defaults
        config = ProjectConfiguration(
            project=ProjectInfo(name="Test")
        )
        # Remove the default workflow we're testing for
        config.workflows.pop(WorkflowType.SPECIFY, None)

        with patch.object(manager, 'load_configuration', return_value=config):
            workflow_config = manager.get_workflow_config(WorkflowType.SPECIFY)

        assert workflow_config is None

    def test_is_workflow_enabled_true(self):
        """Test is_workflow_enabled returns True for enabled workflow."""
        manager = ConfigurationManager("/test/repo")

        with patch.object(manager, 'get_workflow_config') as mock_get:
            mock_get.return_value = WorkflowConfig(enabled=True)
            result = manager.is_workflow_enabled(WorkflowType.SPECIFY)

        assert result is True

    def test_is_workflow_enabled_false(self):
        """Test is_workflow_enabled returns False for disabled workflow."""
        manager = ConfigurationManager("/test/repo")

        with patch.object(manager, 'get_workflow_config') as mock_get:
            mock_get.return_value = WorkflowConfig(enabled=False)
            result = manager.is_workflow_enabled(WorkflowType.SPECIFY)

        assert result is False

    def test_is_workflow_enabled_not_configured(self):
        """Test is_workflow_enabled returns False for non-configured workflow."""
        manager = ConfigurationManager("/test/repo")

        with patch.object(manager, 'get_workflow_config') as mock_get:
            mock_get.return_value = None
            result = manager.is_workflow_enabled(WorkflowType.SPECIFY)

        assert result is False