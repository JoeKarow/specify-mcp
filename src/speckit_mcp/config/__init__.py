"""Configuration management for spec-kit MCP server."""

# Import models for easy access
from .models import (
    ProjectConfiguration,
    WorkflowSession,
    Task,
    RepositoryRegistration,
    WorkflowType,
    SessionStatus,
    TaskStatus,
    TaskCategory,
    ProjectInfo,
    Principle,
    WorkflowConfig,
    GitConfig
)

# Import manager
from .manager import ConfigurationManager, ConfigurationError

__all__ = [
    # Models
    'ProjectConfiguration',
    'WorkflowSession',
    'Task',
    'RepositoryRegistration',
    'WorkflowType',
    'SessionStatus',
    'TaskStatus',
    'TaskCategory',
    'ProjectInfo',
    'Principle',
    'WorkflowConfig',
    'GitConfig',
    # Manager
    'ConfigurationManager',
    'ConfigurationError'
]
