"""
Pydantic models for resource management in the SpecKit MCP server.

This module defines the data models for templates and context documents used
by the MCP resource system. All models use Pydantic V2 for validation and serialization.
"""

import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TemplateType(str, Enum):
    """Valid template types in the SpecKit system."""
    SPEC = "spec"
    PLAN = "plan"
    TASKS = "tasks"
    CONSTITUTION = "constitution"
    RESEARCH = "research"


class DocumentType(str, Enum):
    """Valid document types for context documents."""
    CONSTITUTION = "constitution"
    QUICKSTART = "quickstart"
    API = "api"
    GUIDE = "guide"


class DevelopmentPhase(str, Enum):
    """Valid development phases."""
    RESEARCH = "research"
    DESIGN = "design"
    IMPLEMENT = "implement"
    VALIDATE = "validate"


class DocumentVisibility(str, Enum):
    """Document visibility levels."""
    ALWAYS = "always"
    PHASE_SPECIFIC = "phase-specific"
    ON_DEMAND = "on-demand"


class Template(BaseModel):
    """
    Reusable template for specifications, plans, and tasks.

    Represents a template document with content, metadata, and variable
    substitution capabilities.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )

    # Identity
    name: str = Field(..., min_length=1, description="Template name identifier")
    template_type: TemplateType = Field(..., description="Type of template")
    version: str = Field("1.0.0", description="Template version")

    # Content
    content: str = Field(..., min_length=1, description="Template content (markdown)")
    variables: List[str] = Field(
        default_factory=list,
        description="Required template variables"
    )
    sections: List[str] = Field(
        default_factory=list,
        description="Template section names"
    )

    # Metadata
    description: Optional[str] = Field(None, description="Template description")
    author: Optional[str] = Field(None, description="Template author")
    mime_type: str = Field("text/markdown", description="Content MIME type")
    is_embedded: bool = Field(True, description="True if bundled with server")
    source_path: Optional[str] = Field(None, description="Path if custom template")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Additional metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional template metadata"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate template name format."""
        if not v or not isinstance(v, str):
            raise ValueError("Template name must be a non-empty string")

        # Template names should be valid identifiers
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', v):
            raise ValueError("Template name must be alphanumeric with hyphens/underscores")

        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate template content is valid markdown."""
        if not v or not isinstance(v, str):
            raise ValueError("Template content must be a non-empty string")

        # Basic markdown validation - check for YAML front matter if present
        if v.startswith('---'):
            parts = v.split('---', 2)
            if len(parts) < 3:
                raise ValueError("Invalid YAML front matter format")

            front_matter = parts[1].strip()
            if front_matter:
                try:
                    import yaml
                    yaml.safe_load(front_matter)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML front matter: {e}")

        return v

    @field_validator('variables')
    @classmethod
    def validate_variables(cls, v):
        """Validate template variables follow {{variable}} pattern."""
        if not isinstance(v, list):
            raise ValueError("Variables must be a list")

        # Validate variable names are valid identifiers
        for var in v:
            if not isinstance(var, str):
                raise ValueError("Variable names must be strings")
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', var):
                raise ValueError(f"Invalid variable name: {var}")

        return v

    @field_validator('mime_type')
    @classmethod
    def validate_mime_type(cls, v):
        """Validate MIME type is appropriate for templates."""
        valid_types = [
            'text/markdown',
            'text/plain',
            'application/x-template',
            'text/yaml',
            'application/yaml'
        ]

        if v not in valid_types:
            raise ValueError(f"Invalid MIME type for template: {v}")

        return v

    @field_validator('source_path')
    @classmethod
    def validate_source_path(cls, v):
        """Validate source path if provided."""
        if v is not None:
            path = Path(v)
            if not path.is_absolute():
                raise ValueError("Source path must be absolute")

        return v

    @model_validator(mode='after')
    def validate_template_consistency(self):
        """Validate template consistency."""
        # Extract variables from content if not explicitly provided
        if not self.variables and self.content:
            # Find {{variable}} patterns in content
            variable_pattern = r'\{\{(\w+)\}\}'
            found_variables = re.findall(variable_pattern, self.content)
            if found_variables:
                self.variables = list(set(found_variables))

        # Extract sections from markdown content
        if not self.sections and self.content:
            # Find markdown headers
            header_pattern = r'^#+\s+(.+)$'
            sections = re.findall(header_pattern, self.content, re.MULTILINE)
            if sections:
                self.sections = sections

        # Embedded templates should not have source_path
        if self.is_embedded and self.source_path:
            raise ValueError("Embedded templates cannot have source_path")

        # Custom templates should have source_path
        if not self.is_embedded and not self.source_path:
            raise ValueError("Custom templates must have source_path")

        return self

    def substitute_variables(self, variables: Dict[str, str]) -> str:
        """
        Substitute variables in template content.

        Args:
            variables: Dictionary of variable name to value mappings

        Returns:
            Template content with variables substituted

        Raises:
            ValueError: If required variables are missing
        """
        content = self.content

        # Check for missing required variables
        missing_vars = set(self.variables) - set(variables.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")

        # Substitute variables
        for var_name, var_value in variables.items():
            pattern = f'{{{{{var_name}}}}}'
            content = content.replace(pattern, str(var_value))

        return content

    def extract_front_matter(self) -> Optional[Dict[str, Any]]:
        """
        Extract YAML front matter from template content.

        Returns:
            Dictionary of front matter data or None if no front matter
        """
        if not self.content.startswith('---'):
            return None

        parts = self.content.split('---', 2)
        if len(parts) < 3:
            return None

        front_matter = parts[1].strip()
        if not front_matter:
            return None

        try:
            import yaml
            return yaml.safe_load(front_matter)
        except yaml.YAMLError:
            return None


class ContextDocument(BaseModel):
    """
    Phase-specific documentation served to users.

    Represents documentation that provides context and guidance
    during different development phases.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    # Identity
    document_id: str = Field(..., description="Unique document identifier")
    document_type: DocumentType = Field(..., description="Type of document")
    title: str = Field(..., min_length=1, description="Document title")

    # Relevance
    phase: DevelopmentPhase = Field(..., description="Associated development phase")
    workflow: str = Field(..., description="Associated workflow type")

    # Content
    content: str = Field(..., min_length=1, description="Document content (markdown)")
    summary: Optional[str] = Field(None, description="Brief document summary")

    # Access control
    visibility: DocumentVisibility = Field(
        DocumentVisibility.ALWAYS,
        description="When document should be visible"
    )
    priority: int = Field(
        1,
        ge=1,
        le=10,
        description="Display priority (1=highest, 10=lowest)"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Document tags for categorization"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional document metadata"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        """Validate document ID format."""
        if not v or not isinstance(v, str):
            raise ValueError("Document ID must be a non-empty string")

        # Document IDs should be valid identifiers
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', v):
            raise ValueError("Document ID must be alphanumeric with hyphens/underscores")

        return v

    @field_validator('workflow')
    @classmethod
    def validate_workflow(cls, v):
        """Validate workflow type."""
        valid_workflows = ['specify', 'plan', 'tasks', 'all']
        if v not in valid_workflows:
            raise ValueError(f"Invalid workflow type: {v}")
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate document content is valid markdown."""
        if not v or not isinstance(v, str):
            raise ValueError("Document content must be a non-empty string")

        # Basic markdown validation
        # Could add more sophisticated validation here
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate document tags."""
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")

        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Tag must be a string")
            if not tag.strip():
                raise ValueError("Tag cannot be empty")

        return v

    @model_validator(mode='after')
    def validate_document_consistency(self):
        """Validate document consistency."""
        # Generate summary from content if not provided
        if not self.summary and self.content:
            # Extract first paragraph as summary
            lines = self.content.split('\n')
            first_paragraph = []

            for line in lines:
                line = line.strip()
                if not line:
                    if first_paragraph:
                        break
                    continue

                # Skip markdown headers
                if line.startswith('#'):
                    continue

                first_paragraph.append(line)

            if first_paragraph:
                summary = ' '.join(first_paragraph)
                # Limit summary length
                if len(summary) > 200:
                    summary = summary[:197] + '...'
                self.summary = summary

        return self

    def is_visible_for_phase(self, current_phase: DevelopmentPhase) -> bool:
        """
        Check if document should be visible for the given phase.

        Args:
            current_phase: The current development phase

        Returns:
            True if document should be visible
        """
        if self.visibility == DocumentVisibility.ALWAYS:
            return True

        if self.visibility == DocumentVisibility.PHASE_SPECIFIC:
            return self.phase == current_phase

        # ON_DEMAND visibility requires explicit request
        return False

    def matches_workflow(self, workflow_type: str) -> bool:
        """
        Check if document is relevant for the given workflow.

        Args:
            workflow_type: The workflow type to check against

        Returns:
            True if document is relevant for the workflow
        """
        return self.workflow == 'all' or self.workflow == workflow_type


# Export all models
__all__ = [
    'TemplateType',
    'DocumentType',
    'DevelopmentPhase',
    'DocumentVisibility',
    'Template',
    'ContextDocument'
]