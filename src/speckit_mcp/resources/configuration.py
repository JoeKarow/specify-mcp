"""
MCP resource implementation for serving configuration.

This module provides MCP resources for serving configuration schemas,
defaults, and validation rules.
"""

from typing import Dict, Any, Optional, List
import json
from fastmcp import Resource
from fastmcp.exceptions import McpError

from speckit_mcp.config.models import (
    ProjectConfiguration,
    WorkflowConfiguration,
    WorkflowType,
    TemplateConfiguration,
    RulesConfiguration
)


class ConfigurationResources:
    """
    Manages MCP resources for configuration.

    Provides access to configuration schemas, defaults, and validation rules
    via MCP resource URIs.
    """

    def __init__(self):
        """Initialize configuration resources."""
        self.schemas = self._load_configuration_schemas()
        self.defaults = self._load_default_configurations()

    def _load_configuration_schemas(self) -> Dict[str, Any]:
        """
        Load configuration schemas.

        Returns:
            Dictionary of configuration schemas
        """
        schemas = {}

        # Project configuration schema
        schemas['project'] = {
            "type": "object",
            "title": "Project Configuration Schema",
            "description": "Schema for SpecKit project configuration",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name of the project",
                    "minLength": 1
                },
                "description": {
                    "type": "string",
                    "description": "Project description"
                },
                "version": {
                    "type": "string",
                    "description": "Project version",
                    "pattern": "^\\d+\\.\\d+\\.\\d+$"
                },
                "constitution": {
                    "$ref": "#/definitions/constitution"
                },
                "workflows": {
                    "type": "object",
                    "properties": {
                        "specify": {"$ref": "#/definitions/workflow"},
                        "plan": {"$ref": "#/definitions/workflow"},
                        "tasks": {"$ref": "#/definitions/workflow"}
                    }
                }
            },
            "required": ["project_name"],
            "definitions": {
                "constitution": {
                    "type": "object",
                    "properties": {
                        "principles": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "priority": {"type": "integer", "minimum": 1}
                                },
                                "required": ["name", "description"]
                            }
                        },
                        "rules": {
                            "$ref": "#/definitions/rules"
                        }
                    }
                },
                "workflow": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "auto_commit": {"type": "boolean"},
                        "template": {"$ref": "#/definitions/template"}
                    }
                },
                "template": {
                    "type": "object",
                    "properties": {
                        "use_custom": {"type": "boolean"},
                        "custom_path": {"type": "string"},
                        "variables": {
                            "type": "object",
                            "additionalProperties": {"type": "string"}
                        }
                    }
                },
                "rules": {
                    "type": "object",
                    "properties": {
                        "require_tests_first": {"type": "boolean"},
                        "max_file_size_kb": {"type": "integer", "minimum": 1},
                        "allowed_file_types": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "branch_naming_pattern": {"type": "string"}
                    }
                }
            }
        }

        # Workflow configuration schema
        schemas['workflow'] = {
            "type": "object",
            "title": "Workflow Configuration Schema",
            "description": "Schema for individual workflow configuration",
            "properties": {
                "workflow_type": {
                    "type": "string",
                    "enum": ["specify", "plan", "tasks"],
                    "description": "Type of workflow"
                },
                "enabled": {
                    "type": "boolean",
                    "description": "Whether workflow is enabled",
                    "default": True
                },
                "auto_commit": {
                    "type": "boolean",
                    "description": "Auto-commit changes",
                    "default": True
                },
                "create_branch": {
                    "type": "boolean",
                    "description": "Create feature branch",
                    "default": True
                },
                "branch_prefix": {
                    "type": "string",
                    "description": "Branch name prefix",
                    "default": "feature"
                },
                "commit_message_template": {
                    "type": "string",
                    "description": "Template for commit messages"
                },
                "template": {
                    "$ref": "#/definitions/template"
                }
            },
            "required": ["workflow_type"],
            "definitions": {
                "template": {
                    "type": "object",
                    "properties": {
                        "use_custom": {"type": "boolean"},
                        "custom_path": {"type": "string"},
                        "variables": {
                            "type": "object",
                            "additionalProperties": {"type": "string"}
                        }
                    }
                }
            }
        }

        # Rules configuration schema
        schemas['rules'] = {
            "type": "object",
            "title": "Rules Configuration Schema",
            "description": "Schema for validation and workflow rules",
            "properties": {
                "require_tests_first": {
                    "type": "boolean",
                    "description": "Require tests before implementation",
                    "default": True
                },
                "require_documentation": {
                    "type": "boolean",
                    "description": "Require documentation",
                    "default": True
                },
                "max_file_size_kb": {
                    "type": "integer",
                    "description": "Maximum file size in KB",
                    "minimum": 1,
                    "default": 1000
                },
                "max_files_per_commit": {
                    "type": "integer",
                    "description": "Maximum files per commit",
                    "minimum": 1,
                    "default": 50
                },
                "allowed_file_types": {
                    "type": "array",
                    "description": "Allowed file extensions",
                    "items": {"type": "string"},
                    "default": [".md", ".yaml", ".yml", ".json", ".py", ".js", ".ts", ".go", ".rs"]
                },
                "branch_naming_pattern": {
                    "type": "string",
                    "description": "Regex pattern for branch names",
                    "default": "^(feature|fix|docs|refactor)/[a-z0-9-]+$"
                },
                "commit_message_pattern": {
                    "type": "string",
                    "description": "Regex pattern for commit messages",
                    "default": "^(feat|fix|docs|refactor|test|chore)(\\(.+\\))?:\\s.+"
                }
            }
        }

        # Template configuration schema
        schemas['template'] = {
            "type": "object",
            "title": "Template Configuration Schema",
            "description": "Schema for template configuration",
            "properties": {
                "use_custom": {
                    "type": "boolean",
                    "description": "Use custom template",
                    "default": False
                },
                "custom_path": {
                    "type": "string",
                    "description": "Path to custom template file"
                },
                "template_type": {
                    "type": "string",
                    "enum": ["spec", "plan", "tasks", "constitution", "research"],
                    "description": "Type of template"
                },
                "variables": {
                    "type": "object",
                    "description": "Template variables",
                    "additionalProperties": {"type": "string"}
                },
                "cache_enabled": {
                    "type": "boolean",
                    "description": "Enable template caching",
                    "default": True
                }
            }
        }

        return schemas

    def _load_default_configurations(self) -> Dict[str, Any]:
        """
        Load default configuration values.

        Returns:
            Dictionary of default configurations
        """
        defaults = {}

        # Default project configuration
        defaults['project'] = {
            "project_name": "my-project",
            "description": "A SpecKit managed project",
            "version": "0.1.0",
            "constitution": {
                "principles": [
                    {
                        "name": "MCP Protocol Compliance",
                        "description": "All functionality through MCP tools/resources",
                        "priority": 1
                    },
                    {
                        "name": "File System Preservation",
                        "description": "Maintain git-integrated workflow",
                        "priority": 2
                    },
                    {
                        "name": "Test-First Development",
                        "description": "TDD with failing tests first",
                        "priority": 3
                    },
                    {
                        "name": "Structured Data",
                        "description": "YAML over markdown for parsing",
                        "priority": 4
                    },
                    {
                        "name": "Simplicity",
                        "description": "MVP without premature features",
                        "priority": 5
                    },
                    {
                        "name": "Cross-Platform",
                        "description": "Pure Python, no shell dependencies",
                        "priority": 6
                    }
                ],
                "rules": {
                    "require_tests_first": True,
                    "require_documentation": True,
                    "max_file_size_kb": 1000,
                    "allowed_file_types": [".md", ".yaml", ".yml", ".json", ".py"],
                    "branch_naming_pattern": "^(feature|fix|docs)/[a-z0-9-]+$"
                }
            },
            "workflows": {
                "specify": {
                    "enabled": True,
                    "auto_commit": True,
                    "create_branch": True,
                    "branch_prefix": "feature",
                    "template": {
                        "use_custom": False
                    }
                },
                "plan": {
                    "enabled": True,
                    "auto_commit": True,
                    "template": {
                        "use_custom": False
                    }
                },
                "tasks": {
                    "enabled": True,
                    "auto_commit": True,
                    "template": {
                        "use_custom": False
                    }
                }
            },
            "settings": {
                "auto_save": True,
                "verbose_logging": False,
                "max_parallel_tasks": 5,
                "cache_templates": True,
                "validate_on_save": True
            }
        }

        # Default workflow configurations
        defaults['workflow_specify'] = {
            "workflow_type": "specify",
            "enabled": True,
            "auto_commit": True,
            "create_branch": True,
            "branch_prefix": "feature",
            "commit_message_template": "feat: Add specification for {{feature_name}}",
            "template": {
                "use_custom": False,
                "variables": {}
            }
        }

        defaults['workflow_plan'] = {
            "workflow_type": "plan",
            "enabled": True,
            "auto_commit": True,
            "create_branch": False,
            "commit_message_template": "docs: Add implementation plan for {{feature_name}}",
            "template": {
                "use_custom": False,
                "variables": {}
            }
        }

        defaults['workflow_tasks'] = {
            "workflow_type": "tasks",
            "enabled": True,
            "auto_commit": True,
            "create_branch": False,
            "commit_message_template": "docs: Add task breakdown for {{feature_name}}",
            "template": {
                "use_custom": False,
                "variables": {}
            }
        }

        # Default rules configuration
        defaults['rules'] = {
            "require_tests_first": True,
            "require_documentation": True,
            "max_file_size_kb": 1000,
            "max_files_per_commit": 50,
            "allowed_file_types": [".md", ".yaml", ".yml", ".json", ".py", ".js", ".ts"],
            "branch_naming_pattern": "^(feature|fix|docs|refactor)/[a-z0-9-]+$",
            "commit_message_pattern": "^(feat|fix|docs|refactor|test|chore)(\\(.+\\))?:\\s.+"
        }

        return defaults

    async def get_schema_resource(self, schema_name: str) -> Resource:
        """
        Serve a configuration schema as an MCP resource.

        Args:
            schema_name: Name of the schema (project, workflow, rules, template)

        Returns:
            MCP Resource with schema content

        Raises:
            McpError: If schema not found
        """
        schema = self.schemas.get(schema_name)
        if not schema:
            raise McpError(f"Schema not found: {schema_name}")

        uri = f"mcp://speckit/config/schema/{schema_name}"

        return Resource(
            uri=uri,
            name=f"{schema_name.title()} Configuration Schema",
            mimeType="application/json",
            text=json.dumps(schema, indent=2),
            metadata={
                "schema_type": schema_name,
                "title": schema.get("title"),
                "description": schema.get("description")
            }
        )

    async def get_defaults_resource(self, config_name: Optional[str] = None) -> Resource:
        """
        Serve default configuration as an MCP resource.

        Args:
            config_name: Optional specific configuration name

        Returns:
            MCP Resource with default configuration

        Raises:
            McpError: If configuration not found
        """
        if config_name:
            config = self.defaults.get(config_name)
            if not config:
                raise McpError(f"Default configuration not found: {config_name}")

            uri = f"mcp://speckit/config/defaults/{config_name}"
            name = f"Default {config_name.replace('_', ' ').title()} Configuration"
            content = config
        else:
            uri = "mcp://speckit/config/defaults"
            name = "Default Configurations"
            content = self.defaults

        return Resource(
            uri=uri,
            name=name,
            mimeType="application/json",
            text=json.dumps(content, indent=2),
            metadata={
                "config_type": config_name or "all",
                "includes_defaults": True
            }
        )

    async def get_constitution_template(self) -> Resource:
        """
        Serve the constitution template as an MCP resource.

        Returns:
            MCP Resource with constitution template
        """
        constitution_content = """---
project_name: {{project_name}}
description: {{description}}
version: 1.0.0
---

# {{project_name}} Constitution

## Project Information

**Name**: {{project_name}}
**Description**: {{description}}
**Version**: {{version}}
**Generated**: {{date}}

## Constitutional Principles

### 1. MCP Protocol Compliance
All functionality must be exposed through MCP tools and resources.
**Priority**: 1
**Rationale**: Ensures consistent interface and integration with AI assistants.

### 2. File System Preservation
Maintain git-integrated workflow without external dependencies.
**Priority**: 2
**Rationale**: Keeps all project artifacts versioned and trackable.

### 3. Test-First Development
Write failing tests before implementation (TDD).
**Priority**: 3
**Rationale**: Ensures robust, well-tested code with clear requirements.

### 4. Structured Data
Use YAML over markdown for machine-parsable data.
**Priority**: 4
**Rationale**: Enables better tooling and automation.

### 5. Simplicity (YAGNI)
Build MVP without premature features.
**Priority**: 5
**Rationale**: Reduces complexity and maintenance burden.

### 6. Cross-Platform Support
No shell dependencies, pure Python implementation.
**Priority**: 6
**Rationale**: Maximizes portability across different systems.

## Workflow Configuration

### Specify Workflow
- **Enabled**: true
- **Auto-commit**: true
- **Create branch**: true
- **Branch prefix**: feature/

### Plan Workflow
- **Enabled**: true
- **Auto-commit**: true
- **Create branch**: false

### Tasks Workflow
- **Enabled**: true
- **Auto-commit**: true
- **Create branch**: false

## Validation Rules

### Code Quality
- Require tests before implementation
- Maintain minimum 80% test coverage
- Follow PEP 8 style guidelines
- Document all public APIs

### Git Workflow
- Branch naming: `^(feature|fix|docs)/[a-z0-9-]+$`
- Commit messages: Conventional Commits format
- Maximum files per commit: 50
- Maximum file size: 1000 KB

### File Management
- Allowed file types: .md, .yaml, .yml, .json, .py
- Required documentation for all features
- Specifications in specs/ directory
- Plans in plans/ directory
- Tasks in tasks/ directory

## Development Settings

- **Auto-save**: enabled
- **Verbose logging**: disabled
- **Max parallel tasks**: 5
- **Template caching**: enabled
- **Validation on save**: enabled

## Amendment Process

This constitution can be amended by:
1. Creating a proposal in specs/amendments/
2. Getting team consensus
3. Updating this document
4. Committing with message: `docs: Amend constitution - [description]`

---
*This constitution defines the core principles and rules for the {{project_name}} project.*"""

        uri = "mcp://speckit/config/constitution"

        return Resource(
            uri=uri,
            name="Constitution Template",
            mimeType="text/markdown",
            text=constitution_content,
            metadata={
                "template_type": "constitution",
                "variables": ["project_name", "description", "version", "date"],
                "purpose": "Project constitution and configuration"
            }
        )

    async def list_schemas(self) -> List[Resource]:
        """
        List available configuration schemas.

        Returns:
            List of schema resources
        """
        resources = []

        for schema_name in self.schemas.keys():
            schema = self.schemas[schema_name]
            uri = f"mcp://speckit/config/schema/{schema_name}"

            resources.append(Resource(
                uri=uri,
                name=f"{schema_name.title()} Schema",
                mimeType="application/json",
                description=schema.get("description", f"Schema for {schema_name} configuration"),
                metadata={
                    "schema_type": schema_name,
                    "title": schema.get("title")
                }
            ))

        return resources

    async def list_defaults(self) -> List[Resource]:
        """
        List available default configurations.

        Returns:
            List of default configuration resources
        """
        resources = []

        for config_name in self.defaults.keys():
            uri = f"mcp://speckit/config/defaults/{config_name}"

            resources.append(Resource(
                uri=uri,
                name=f"Default {config_name.replace('_', ' ').title()}",
                mimeType="application/json",
                description=f"Default configuration for {config_name}",
                metadata={
                    "config_type": config_name
                }
            ))

        return resources


# Create singleton instance
_configuration_resources = ConfigurationResources()


async def serve_configuration(uri: str) -> Resource:
    """
    Serve a configuration resource based on URI.

    Expected URI formats:
    - mcp://speckit/config/schema/{name}
    - mcp://speckit/config/defaults/{name}
    - mcp://speckit/config/constitution

    Args:
        uri: Resource URI

    Returns:
        MCP Resource containing configuration

    Raises:
        McpError: If URI is invalid or resource not found
    """
    if not uri.startswith("mcp://speckit/config/"):
        raise McpError(f"Invalid configuration URI: {uri}")

    path = uri.replace("mcp://speckit/config/", "")

    if path == "constitution":
        return await _configuration_resources.get_constitution_template()

    parts = path.split("/")

    if len(parts) == 1:
        # List resources in category
        if parts[0] == "schema":
            schemas = await _configuration_resources.list_schemas()
            return Resource(
                uri="mcp://speckit/config/schema",
                name="Configuration Schemas",
                mimeType="application/json",
                metadata={
                    "schemas": [
                        {
                            "uri": s.uri,
                            "name": s.name,
                            "description": s.description
                        } for s in schemas
                    ]
                }
            )
        elif parts[0] == "defaults":
            return await _configuration_resources.get_defaults_resource()

    elif len(parts) == 2:
        category = parts[0]
        name = parts[1]

        if category == "schema":
            return await _configuration_resources.get_schema_resource(name)
        elif category == "defaults":
            return await _configuration_resources.get_defaults_resource(name)

    raise McpError(f"Invalid configuration URI: {uri}")


async def list_configuration_resources() -> List[Resource]:
    """
    List all available configuration resources.

    Returns:
        List of available configuration resources
    """
    resources = []
    resources.extend(await _configuration_resources.list_schemas())
    resources.extend(await _configuration_resources.list_defaults())

    # Add constitution template
    resources.append(Resource(
        uri="mcp://speckit/config/constitution",
        name="Constitution Template",
        mimeType="text/markdown",
        description="Project constitution template"
    ))

    return resources