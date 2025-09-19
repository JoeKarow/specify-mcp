"""MCP resource implementations for templates and documentation."""

# Import models for easy access
from .models import (
    Template,
    ContextDocument,
    TemplateType,
    DocumentType,
    DevelopmentPhase,
    DocumentVisibility
)

# Import template manager
from .template_manager import TemplateManager, TemplateError

__all__ = [
    # Models
    'Template',
    'ContextDocument',
    'TemplateType',
    'DocumentType',
    'DevelopmentPhase',
    'DocumentVisibility',
    # Manager
    'TemplateManager',
    'TemplateError'
]
