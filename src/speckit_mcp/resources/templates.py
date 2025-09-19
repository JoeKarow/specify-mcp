"""
MCP resource implementation for serving templates.

This module provides MCP resources for serving specification, plan, and task templates
with YAML front matter processing and metadata support.
"""

import logging
from typing import Dict, Any, Optional
from fastmcp.resources import Resource
from fastmcp.exceptions import McpError

from speckit_mcp.resources.template_manager import TemplateManager, TemplateError
from speckit_mcp.resources.models import TemplateType

# Set up logger for this module
logger = logging.getLogger("speckit_mcp.resources.templates")


class TemplateResources:
    """
    Manages MCP resources for templates.

    Provides access to embedded templates via MCP resource URIs,
    supporting YAML front matter extraction and variable metadata.
    """

    def __init__(self):
        """Initialize template resources with a template manager."""
        self.template_manager = TemplateManager()

    async def get_template_resource(self, template_type: str) -> Resource:
        """
        Serve a template as an MCP resource.

        Args:
            template_type: Type of template (spec, plan, tasks, constitution, research)

        Returns:
            MCP Resource with template content and metadata

        Raises:
            McpError: If template type is invalid or template cannot be loaded
        """
        # Validate template type
        logger.debug(f"Loading template resource: {template_type}")
        try:
            template_enum = TemplateType(template_type.lower())
        except ValueError:
            logger.error(f"Invalid template type requested: {template_type}")
            raise McpError(
                code=-32602,  # Invalid params
                message=f"Invalid template type: {template_type}"
            )

        # Load template
        try:
            template = self.template_manager.get_template(template_enum)
            logger.info(f"Successfully loaded template: {template.name}")
        except TemplateError as e:
            logger.error(f"Failed to load template {template_type}: {e}")
            raise McpError(
                code=-32001,  # Resource not found (custom)
                message=f"Failed to load template: {e}"
            )

        # Extract front matter for metadata
        front_matter = template.extract_front_matter() or {}

        # Build resource metadata
        metadata = {
            "name": template.name,
            "description": template.description or f"{template.name.title()} template for SpecKit",
            "version": template.version,
            "template_type": template.template_type.value,
            "variables": template.variables,
            "sections": template.sections,
            "is_embedded": template.is_embedded,
            **front_matter  # Include any additional front matter data
        }

        # Create resource URI
        uri = f"mcp://speckit/templates/{template_type}"

        # Remove front matter from content for serving
        _, body = self.template_manager.parse_front_matter(template.content)

        return Resource(
            uri=uri,
            name=f"{template.name.title()} Template",
            mimeType=template.mime_type,
            text=body,
            metadata=metadata
        )

    async def list_templates(self) -> list[Resource]:
        """
        List all available templates as MCP resources.

        Returns:
            List of MCP Resources representing available templates
        """
        resources = []
        template_list = self.template_manager.list_templates()

        for template_info in template_list:
            name = template_info['name']
            uri = f"mcp://speckit/templates/{name}"

            resources.append(Resource(
                uri=uri,
                name=f"{name.title()} Template",
                mimeType="text/markdown",
                description=template_info.get('description', f"Template for {name}"),
                metadata={
                    "template_type": template_info['type'],
                    "is_embedded": template_info['embedded']
                }
            ))

        return resources


# Create singleton instance
_template_resources = TemplateResources()


async def serve_template(uri: str) -> Resource:
    """
    Serve a template resource based on URI.

    T041: Comprehensive error handling for resource serving
    Expected URI format: mcp://speckit/templates/{template_type}

    Args:
        uri: Resource URI

    Returns:
        MCP Resource containing template

    Raises:
        McpError: If URI is invalid or template not found
    """
    logger.debug(f"Serving template resource for URI: {uri}")

    # Parse URI to extract template type
    if not uri.startswith("mcp://speckit/templates/"):
        logger.error(f"Invalid template URI format: {uri}")
        raise McpError(
            code=-32602,  # Invalid params
            message=f"Invalid template URI: {uri}"
        )

    template_type = uri.replace("mcp://speckit/templates/", "")

    if not template_type:
        # Return list of templates
        logger.info("Listing all available templates")
        templates = await _template_resources.list_templates()
        return Resource(
            uri="mcp://speckit/templates",
            name="Available Templates",
            mimeType="application/json",
            metadata={
                "templates": [
                    {
                        "uri": t.uri,
                        "name": t.name,
                        "description": t.description
                    } for t in templates
                ]
            }
        )

    logger.info(f"Fetching template: {template_type}")
    return await _template_resources.get_template_resource(template_type)


async def list_template_resources() -> list[Resource]:
    """
    List all available template resources.

    Returns:
        List of available template resources
    """
    return await _template_resources.list_templates()