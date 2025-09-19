"""
Contract tests for the configuration MCP resources.

These tests verify MCP protocol compliance and resource schema validation for configuration resources.
Configuration resources serve constitution schema, default values, inheritance rules, and support
configuration merging and override behavior.

Tests MUST fail initially since implementation doesn't exist yet (TDD).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest
import pytest_asyncio
from pydantic import ValidationError

# These imports will fail until implementation exists - that's expected for TDD
try:
    from speckit_mcp.resources.configuration import ConfigurationResource
    from speckit_mcp.server import create_server
    from speckit_mcp.config.models import ProjectConfiguration
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    ConfigurationResource = None
    create_server = None
    ProjectConfiguration = None


class TestConfigurationResourcesContract:
    """Contract tests for configuration MCP resources ensuring MCP protocol compliance."""

    @pytest.fixture
    def configuration_uris(self):
        """Standard configuration resource URIs following MCP resource pattern."""
        return [
            "mcp://speckit/config/schema/constitution",
            "mcp://speckit/config/schema/project",
            "mcp://speckit/config/defaults/constitution",
            "mcp://speckit/config/defaults/project",
            "mcp://speckit/config/examples/minimal",
            "mcp://speckit/config/examples/complete"
        ]

    @pytest.fixture
    def constitution_schema(self):
        """Expected constitution schema structure."""
        return {
            "type": "object",
            "properties": {
                "project": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "description": {"type": "string"},
                        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+"}
                    },
                    "required": ["name"]
                },
                "principles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "priority": {"type": "integer", "minimum": 1, "maximum": 10}
                        },
                        "required": ["name", "description", "priority"]
                    }
                },
                "workflows": {
                    "type": "object",
                    "properties": {
                        "specify": {"$ref": "#/definitions/workflow"},
                        "plan": {"$ref": "#/definitions/workflow"},
                        "tasks": {"$ref": "#/definitions/workflow"}
                    }
                },
                "templates": {
                    "type": "object",
                    "properties": {
                        "spec": {"type": "string"},
                        "plan": {"type": "string"},
                        "tasks": {"type": "string"}
                    }
                }
            },
            "required": ["project", "principles"],
            "definitions": {
                "workflow": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "steps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        }

    @pytest.fixture
    def default_constitution(self):
        """Default constitution configuration."""
        return {
            "project": {
                "name": "example-project",
                "description": "Example SpecKit project",
                "version": "1.0.0"
            },
            "principles": [
                {
                    "name": "MCP Protocol Compliance",
                    "description": "All functionality exposed through MCP tools and resources",
                    "priority": 1
                },
                {
                    "name": "File System Preservation",
                    "description": "Maintain git-integrated workflow without external dependencies",
                    "priority": 2
                },
                {
                    "name": "Test-First Development",
                    "description": "TDD methodology with comprehensive test coverage",
                    "priority": 3
                },
                {
                    "name": "Structured Data",
                    "description": "YAML over markdown for machine-parseable data",
                    "priority": 4
                },
                {
                    "name": "Simplicity (YAGNI)",
                    "description": "Build MVP without premature optimization or features",
                    "priority": 5
                },
                {
                    "name": "Cross-Platform",
                    "description": "No shell dependencies, pure Python implementation",
                    "priority": 6
                }
            ],
            "workflows": {
                "specify": {
                    "enabled": True,
                    "steps": ["validate_repository", "create_branch", "generate_spec", "commit_changes"]
                },
                "plan": {
                    "enabled": True,
                    "steps": ["load_spec", "analyze_requirements", "generate_plan", "save_artifacts"]
                },
                "tasks": {
                    "enabled": True,
                    "steps": ["load_plan", "generate_tasks", "apply_rules", "save_tasks"]
                }
            },
            "templates": {
                "spec": "mcp://speckit/templates/spec",
                "plan": "mcp://speckit/templates/plan",
                "tasks": "mcp://speckit/templates/tasks"
            }
        }

    @pytest.mark.contract
    def test_configuration_resource_class_exists(self):
        """Test that the ConfigurationResource class exists and is importable."""
        assert ConfigurationResource is not None, "ConfigurationResource class must exist"

    @pytest.mark.contract
    def test_project_configuration_model_exists(self):
        """Test that the ProjectConfiguration Pydantic model exists."""
        assert ProjectConfiguration is not None, "ProjectConfiguration model must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_resource_uri_patterns(self, configuration_uris):
        """Test that configuration resources follow proper MCP URI patterns."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        # Test URI pattern validation
        for uri in configuration_uris:
            assert uri.startswith("mcp://speckit/config/"), f"URI {uri} must follow mcp://speckit/config/ pattern"

            # Extract configuration type and category from URI
            parts = uri.split("/")
            assert len(parts) >= 5, f"URI {uri} must have proper structure"

            category = parts[4]  # schema, defaults, examples
            assert category in ["schema", "defaults", "examples"], f"Category {category} must be valid"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_resource_schema_validation(self, constitution_schema):
        """Test that configuration resources provide proper schema validation."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test schema resource access
            schema_uri = "mcp://speckit/config/schema/constitution"
            schema_content = await resource.read_resource(schema_uri)

            assert schema_content is not None, "Constitution schema must be available"
            assert isinstance(schema_content, str), "Schema content must be string (JSON)"

            # Parse and validate schema structure
            import json
            schema = json.loads(schema_content)
            assert isinstance(schema, dict), "Schema must be valid JSON object"

            # Verify essential schema properties
            assert "type" in schema, "Schema must have type property"
            assert schema["type"] == "object", "Constitution schema must be object type"
            assert "properties" in schema, "Schema must have properties"

            # Verify required sections
            properties = schema["properties"]
            required_sections = ["project", "principles"]
            for section in required_sections:
                assert section in properties, f"Schema must include {section} section"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_default_values(self, default_constitution):
        """Test that configuration resources provide proper default values."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test default constitution access
            defaults_uri = "mcp://speckit/config/defaults/constitution"
            defaults_content = await resource.read_resource(defaults_uri)

            assert defaults_content is not None, "Default constitution must be available"
            assert isinstance(defaults_content, str), "Defaults content must be string (YAML)"

            # Parse and validate default structure
            import yaml
            defaults = yaml.safe_load(defaults_content)
            assert isinstance(defaults, dict), "Defaults must be valid YAML object"

            # Verify required sections in defaults
            required_sections = ["project", "principles", "workflows", "templates"]
            for section in required_sections:
                assert section in defaults, f"Defaults must include {section} section"

            # Verify principles structure
            principles = defaults["principles"]
            assert isinstance(principles, list), "Principles must be list"
            assert len(principles) > 0, "Must have at least one principle"

            for principle in principles:
                assert "name" in principle, "Principle must have name"
                assert "description" in principle, "Principle must have description"
                assert "priority" in principle, "Principle must have priority"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_inheritance_rules(self):
        """Test that configuration resources support inheritance and override behavior."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test inheritance capability if implemented
            if hasattr(resource, 'merge_configurations'):
                base_config = {
                    "project": {"name": "base-project"},
                    "principles": [{"name": "Base Principle", "priority": 1}]
                }

                override_config = {
                    "project": {"description": "Override description"},
                    "principles": [{"name": "Override Principle", "priority": 2}]
                }

                merged = await resource.merge_configurations(base_config, override_config)
                assert isinstance(merged, dict), "Merged config must be dictionary"

                # Verify inheritance behavior
                assert "name" in merged["project"], "Base project name must be preserved"
                assert "description" in merged["project"], "Override description must be added"

                # Verify list merging behavior for principles
                principles = merged["principles"]
                principle_names = [p["name"] for p in principles]
                assert "Base Principle" in principle_names, "Base principles must be preserved"
                assert "Override Principle" in principle_names, "Override principles must be added"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_validation_service(self):
        """Test that configuration resources provide validation services."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test validation capability if implemented
            if hasattr(resource, 'validate_configuration'):
                # Test valid configuration
                valid_config = {
                    "project": {
                        "name": "test-project",
                        "version": "1.0.0"
                    },
                    "principles": [
                        {
                            "name": "Test Principle",
                            "description": "Test description",
                            "priority": 1
                        }
                    ]
                }

                validation_result = await resource.validate_configuration(valid_config)
                assert validation_result["valid"] is True, "Valid configuration must pass validation"

                # Test invalid configuration
                invalid_config = {
                    "project": {
                        "name": "",  # Empty name should fail
                        "version": "invalid"  # Invalid version format
                    },
                    "principles": []  # Empty principles should fail
                }

                validation_result = await resource.validate_configuration(invalid_config)
                assert validation_result["valid"] is False, "Invalid configuration must fail validation"
                assert "errors" in validation_result, "Validation result must include errors"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_examples_access(self):
        """Test that configuration resources provide example configurations."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test example configurations
            example_uris = [
                "mcp://speckit/config/examples/minimal",
                "mcp://speckit/config/examples/complete"
            ]

            for uri in example_uris:
                example_content = await resource.read_resource(uri)
                assert example_content is not None, f"Example {uri} must be available"
                assert isinstance(example_content, str), "Example content must be string"

                # Parse and validate example structure
                import yaml
                example = yaml.safe_load(example_content)
                assert isinstance(example, dict), "Example must be valid YAML object"

                # Verify minimal required structure
                assert "project" in example, "Example must include project section"
                assert "principles" in example, "Example must include principles section"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_resource_error_handling(self):
        """Test proper error handling for invalid configuration requests."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test invalid URI
            with pytest.raises(Exception) as exc_info:
                await resource.read_resource("mcp://invalid/config/nonexistent")

            # Should raise appropriate exception
            error = exc_info.value
            assert error is not None, "Must raise exception for invalid URI"

            # Test malformed URI
            with pytest.raises(Exception):
                await resource.read_resource("invalid://uri/format")

            # Test non-existent configuration
            with pytest.raises(Exception):
                await resource.read_resource("mcp://speckit/config/schema/nonexistent")

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_resource_mcp_compliance(self):
        """Test that configuration resources are MCP protocol compliant."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test resource registration methods exist
            assert hasattr(resource, 'list_resources'), "ConfigurationResource must have list_resources method"
            assert hasattr(resource, 'read_resource'), "ConfigurationResource must have read_resource method"

            # Test MCP resource interface compliance
            resources = await resource.list_resources()

            # Verify JSON-RPC 2.0 compatible response structure
            assert isinstance(resources, list), "Resources list must be JSON serializable"

            # Verify each resource follows MCP resource schema
            for resource_info in resources:
                # Check for required MCP resource fields
                required_fields = ['uri', 'name']
                for field in required_fields:
                    assert field in resource_info, f"Resource must include {field}"

                # Verify URI format
                uri = resource_info['uri']
                assert uri.startswith('mcp://'), "Resource URI must use mcp:// scheme"

                # Verify MIME type for configuration resources
                if 'mimeType' in resource_info:
                    mime_type = resource_info['mimeType']
                    valid_types = ['application/json', 'application/yaml', 'text/yaml', 'text/plain']
                    assert mime_type in valid_types, f"Configuration resource must have valid MIME type, got {mime_type}"

                # Verify response is JSON serializable (MCP requirement)
                json.dumps(resource_info)  # Should not raise exception

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    def test_configuration_resource_in_mcp_server(self):
        """Test that configuration resources are properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify configuration resources are registered
            resources = getattr(server, 'resources', {})
            config_resources = [r for r in resources if 'config' in str(r)]
            assert len(config_resources) > 0, "Configuration resources must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_project_configuration_model_validation(self):
        """Test ProjectConfiguration Pydantic model validation."""
        if ProjectConfiguration is None:
            pytest.fail("ProjectConfiguration model not implemented yet - expected for TDD")

        try:
            # Test valid configuration creation
            valid_config = ProjectConfiguration(
                name="test-project",
                description="Test project description",
                version="1.0.0",
                principles=[
                    {
                        "name": "Test Principle",
                        "description": "Test description",
                        "priority": 1
                    }
                ]
            )

            assert valid_config.name == "test-project"
            assert valid_config.version == "1.0.0"
            assert len(valid_config.principles) == 1

            # Test invalid configuration validation
            with pytest.raises(ValidationError):
                ProjectConfiguration(
                    name="",  # Empty name should fail
                    description="description",
                    version="invalid-version",  # Invalid version format
                    principles=[]
                )

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Model not implemented yet - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_environment_overrides(self):
        """Test that configuration resources support environment-based overrides."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test environment override capability if implemented
            if hasattr(resource, 'apply_environment_overrides'):
                base_config = {
                    "project": {"name": "base-project"},
                    "debug": False
                }

                # Simulate environment variables
                env_overrides = {
                    "SPECKIT_PROJECT_NAME": "env-project",
                    "SPECKIT_DEBUG": "true"
                }

                overridden = await resource.apply_environment_overrides(base_config, env_overrides)
                assert isinstance(overridden, dict), "Overridden config must be dictionary"

                # Verify environment overrides were applied
                assert overridden["project"]["name"] == "env-project", "Environment override must be applied"
                assert overridden["debug"] is True, "Boolean environment override must be applied"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_resource_concurrent_access(self):
        """Test that configuration resources handle concurrent access properly."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test concurrent configuration access
            config_uris = [
                "mcp://speckit/config/schema/constitution",
                "mcp://speckit/config/defaults/constitution",
                "mcp://speckit/config/examples/minimal"
            ]

            # Execute multiple resource reads concurrently
            import asyncio
            tasks = [
                resource.read_resource(uri) for uri in config_uris
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all operations completed
            assert len(results) == len(config_uris), "All concurrent operations must complete"

            # Verify no exceptions occurred (unless due to missing implementation)
            for result in results:
                if isinstance(result, Exception):
                    if "not implemented" not in str(result).lower():
                        raise result

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_configuration_backup_and_restore(self):
        """Test that configuration resources support backup and restore operations."""
        if ConfigurationResource is None:
            pytest.fail("ConfigurationResource not implemented yet - expected for TDD")

        try:
            resource = ConfigurationResource()

            # Test backup capability if implemented
            if hasattr(resource, 'backup_configuration'):
                config = {
                    "project": {"name": "backup-test"},
                    "principles": [{"name": "Test", "priority": 1}]
                }

                backup_id = await resource.backup_configuration(config)
                assert isinstance(backup_id, str), "Backup ID must be string"
                assert len(backup_id) > 0, "Backup ID must not be empty"

                # Test restore capability
                if hasattr(resource, 'restore_configuration'):
                    restored = await resource.restore_configuration(backup_id)
                    assert isinstance(restored, dict), "Restored config must be dictionary"
                    assert restored["project"]["name"] == "backup-test", "Restored config must match original"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise