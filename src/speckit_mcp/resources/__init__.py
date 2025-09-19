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

__all__ = [
    'Template',
    'ContextDocument',
    'TemplateType',
    'DocumentType',
    'DevelopmentPhase',
    'DocumentVisibility'
]
