"""
Pydantic models for configuration management in the SpecKit MCP server.

This module defines the core configuration data models used throughout the application,
including project configuration, workflow sessions, tasks, and repository registration.
All models use Pydantic V2 for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.types import DirectoryPath


class WorkflowType(str, Enum):
    """Valid workflow types in the SpecKit system."""
    SPECIFY = "specify"
    PLAN = "plan"
    TASKS = "tasks"


class SessionStatus(str, Enum):
    """Valid workflow session statuses."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Valid task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskCategory(str, Enum):
    """Valid task categories."""
    TEST = "test"
    IMPLEMENT = "implement"
    DOCUMENT = "document"
    VALIDATE = "validate"


class ProjectInfo(BaseModel):
    """Project information within configuration."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    name: str = Field(..., min_length=1, description="Human-readable project name")
    description: Optional[str] = Field(None, description="Project description")
    version: str = Field("1.0.0", pattern=r"^\d+\.\d+\.\d+", description="Semantic version")


class Principle(BaseModel):
    """A constitutional principle for the project."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    name: str = Field(..., min_length=1, description="Principle name")
    description: str = Field(..., min_length=1, description="Principle description")
    priority: int = Field(..., ge=1, le=10, description="Priority (1=highest, 10=lowest)")


class WorkflowConfig(BaseModel):
    """Configuration for a specific workflow."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    enabled: bool = Field(True, description="Whether this workflow is enabled")
    steps: List[str] = Field(default_factory=list, description="Workflow execution steps")
    branch_prefix: Optional[str] = Field(None, description="Git branch prefix for this workflow")


class GitConfig(BaseModel):
    """Git-related configuration."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    remote_url: Optional[str] = Field(None, description="Git remote URL")
    default_branch: str = Field("main", description="Default branch name")


class ProjectConfiguration(BaseModel):
    """
    Project-specific configuration from .specify-mcp/constitution.yaml.

    This model represents the complete project configuration including
    identity, principles, workflows, and customization settings.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )

    # Project identity
    project: ProjectInfo = Field(..., description="Project information")

    # Constitutional principles
    principles: List[Principle] = Field(
        default_factory=list,
        description="Constitutional principles for the project"
    )

    # Git configuration
    git: Optional[GitConfig] = Field(None, description="Git configuration")

    # Workflow configuration
    workflows: Dict[WorkflowType, WorkflowConfig] = Field(
        default_factory=dict,
        description="Workflow-specific configurations"
    )

    # Template customizations
    templates: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom template overrides"
    )

    # Settings
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional project settings"
    )

    @field_validator('workflows')
    @classmethod
    def validate_workflows(cls, v):
        """Ensure all workflow keys are valid workflow types."""
        for workflow_type in v.keys():
            if isinstance(workflow_type, str):
                # Convert string to enum if needed
                try:
                    WorkflowType(workflow_type)
                except ValueError:
                    raise ValueError(f"Invalid workflow type: {workflow_type}")
        return v

    @model_validator(mode='after')
    def validate_configuration(self):
        """Validate the complete configuration."""
        # Ensure at least one principle exists
        if not self.principles:
            # Add default principles
            default_principles = [
                Principle(
                    name="MCP Protocol Compliance",
                    description="All functionality exposed through MCP tools and resources",
                    priority=1
                ),
                Principle(
                    name="File System Preservation",
                    description="Maintain git-integrated workflow without external dependencies",
                    priority=2
                )
            ]
            self.principles = default_principles

        # Ensure workflows are configured
        if not self.workflows:
            # Add default workflow configurations
            default_workflows = {
                WorkflowType.SPECIFY: WorkflowConfig(
                    enabled=True,
                    steps=["validate_repository", "create_branch", "generate_spec", "commit_changes"]
                ),
                WorkflowType.PLAN: WorkflowConfig(
                    enabled=True,
                    steps=["load_spec", "analyze_requirements", "generate_plan", "save_artifacts"]
                ),
                WorkflowType.TASKS: WorkflowConfig(
                    enabled=True,
                    steps=["load_plan", "generate_tasks", "apply_rules", "save_tasks"]
                )
            }
            self.workflows = default_workflows

        return self


class WorkflowSession(BaseModel):
    """
    Active workflow execution context.

    Represents a running workflow session with state tracking
    and execution metadata.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )

    # Identity
    session_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique session identifier")
    workflow_type: WorkflowType = Field(..., description="Type of workflow being executed")
    repository_path: str = Field(..., description="Absolute path to target repository")
    branch_name: str = Field(..., description="Feature branch name")

    # State
    status: SessionStatus = Field(SessionStatus.INITIALIZING, description="Current session status")
    current_phase: str = Field("initialize", description="Current execution phase")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    completed_at: Optional[datetime] = Field(None, description="Session completion time")

    # Context
    feature_description: str = Field(..., description="User-provided feature description")
    feature_id: Optional[str] = Field(None, description="Generated feature identifier")
    generated_artifacts: List[str] = Field(
        default_factory=list,
        description="List of created file paths"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional session metadata"
    )

    @field_validator('repository_path')
    @classmethod
    def validate_repository_path(cls, v):
        """Validate that repository path is absolute."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("Repository path must be absolute")
        return str(path)

    @field_validator('branch_name')
    @classmethod
    def validate_branch_name(cls, v):
        """Validate git branch name format."""
        if not v or not isinstance(v, str):
            raise ValueError("Branch name must be a non-empty string")

        # Basic git branch name validation
        invalid_chars = [' ', '~', '^', ':', '\\', '*', '?', '[', '@{']
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Branch name contains invalid characters: {v}")

        if v.startswith('-') or v.endswith('.'):
            raise ValueError(f"Invalid branch name format: {v}")

        return v

    @model_validator(mode='after')
    def validate_session_state(self):
        """Validate session state consistency."""
        # If status is completed, must have completion time
        if self.status == SessionStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.utcnow()

        # If status is failed, must have completion time
        if self.status == SessionStatus.FAILED and not self.completed_at:
            self.completed_at = datetime.utcnow()

        return self


class Task(BaseModel):
    """
    Structured task representation replacing markdown task lists.

    Represents an individual work item with dependencies,
    status tracking, and metadata.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    # Identity
    task_id: str = Field(..., description="Unique task identifier")
    order: int = Field(..., ge=1, description="Execution order (1-based)")

    # Content
    description: str = Field(..., min_length=1, description="Task description")
    category: TaskCategory = Field(..., description="Task category")

    # Dependencies
    depends_on: List[str] = Field(
        default_factory=list,
        description="Task IDs that must complete first"
    )
    parallel_group: Optional[str] = Field(
        None,
        description="Group ID for parallel execution"
    )

    # Status
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current task status")
    assigned_to: Optional[str] = Field(None, description="Optional assignee")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last modification time")
    specification_ref: str = Field(..., description="Reference to source specification")

    # Additional metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional task metadata"
    )

    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v):
        """Validate task ID format."""
        if not v or not isinstance(v, str):
            raise ValueError("Task ID must be a non-empty string")

        # Task IDs should follow a consistent format
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"Task ID must be alphanumeric with hyphens/underscores: {v}")

        return v

    @model_validator(mode='after')
    def validate_task_consistency(self):
        """Validate task state consistency."""
        # Update timestamp when status changes
        if hasattr(self, '_status_changed'):
            self.updated_at = datetime.utcnow()

        return self


class RepositoryRegistration(BaseModel):
    """
    Connection between git repository and MCP server.

    Represents a registered repository with configuration
    and state tracking information.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )

    # Identity
    repository_id: str = Field(..., description="Unique repository identifier")
    repository_path: str = Field(..., description="Absolute path to repository")
    remote_url: Optional[str] = Field(None, description="Git remote URL")

    # Configuration
    config_path: str = Field(..., description="Path to .specify-mcp/constitution.yaml")
    active_branch: str = Field("main", description="Current working branch")

    # State
    is_initialized: bool = Field(False, description="Has .specify-mcp directory")
    has_legacy_speckit: bool = Field(False, description="Contains templates/ or scripts/")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last workflow execution")

    # Permissions
    read_only: bool = Field(False, description="If true, no modifications allowed")

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional repository metadata"
    )

    @field_validator('repository_path')
    @classmethod
    def validate_repository_path(cls, v):
        """Validate repository path exists and is absolute."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("Repository path must be absolute")
        return str(path)

    @field_validator('config_path')
    @classmethod
    def validate_config_path(cls, v):
        """Validate config path format."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("Config path must be absolute")

        # Config path should be within repository and have correct filename
        if not path.name == 'constitution.yaml':
            raise ValueError("Config path must point to constitution.yaml")

        return str(path)

    @field_validator('repository_id')
    @classmethod
    def validate_repository_id(cls, v):
        """Validate repository ID format."""
        if not v or not isinstance(v, str):
            raise ValueError("Repository ID must be a non-empty string")
        return v

    @model_validator(mode='after')
    def validate_repository_consistency(self):
        """Validate repository registration consistency."""
        # Config path should be within repository
        repo_path = Path(self.repository_path)
        config_path = Path(self.config_path)

        try:
            config_path.relative_to(repo_path)
        except ValueError:
            raise ValueError("Config path must be within repository path")

        return self


# Export all models
__all__ = [
    'WorkflowType',
    'SessionStatus',
    'TaskStatus',
    'TaskCategory',
    'ProjectInfo',
    'Principle',
    'WorkflowConfig',
    'GitConfig',
    'ProjectConfiguration',
    'WorkflowSession',
    'Task',
    'RepositoryRegistration'
]