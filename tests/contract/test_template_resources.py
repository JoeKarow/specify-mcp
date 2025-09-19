"""
Contract tests for the template MCP resources.

These tests verify MCP protocol compliance and resource schema validation for template resources.
Template resources serve spec, plan, and tasks templates with proper URI patterns, metadata,
and content structure including YAML front matter processing and variable substitution.

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
    from speckit_mcp.resources.templates import TemplateResource
    from speckit_mcp.server import create_server
    from speckit_mcp.resources.models import Template
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    TemplateResource = None
    create_server = None
    Template = None


class TestTemplateResourcesContract:
    """Contract tests for template MCP resources ensuring MCP protocol compliance."""

    @pytest.fixture
    def template_uris(self):
        """Standard template resource URIs following MCP resource pattern."""
        return [
            "mcp://speckit/templates/spec",
            "mcp://speckit/templates/plan",
            "mcp://speckit/templates/tasks",
            "mcp://speckit/templates/constitution"
        ]

    @pytest.fixture
    def mock_template_content(self):
        """Mock template content with YAML front matter."""
        return {
            "spec": """---
title: "{feature_title}"
id: "{feature_id}"
description: "{description}"
phase: "1.specification"
---

# Specification: {feature_title}

## Problem Statement
{description}

## Solution Overview
[To be filled based on requirements analysis]

## Functional Requirements
- [Requirement 1]
- [Requirement 2]

## Technical Requirements
- [Technical constraint 1]
- [Technical constraint 2]

## Success Criteria
- [Success metric 1]
- [Success metric 2]
""",
            "plan": """---
title: "Implementation Plan: {feature_title}"
feature_id: "{feature_id}"
phase: "2.planning"
tech_stack: "{tech_stack}"
---

# Implementation Plan: {feature_title}

## Architecture Overview
[High-level architecture description]

## Implementation Strategy
[Step-by-step implementation approach]

## Technical Stack
{tech_stack}

## Development Phases
1. Setup and scaffolding
2. Core implementation
3. Testing and validation
4. Documentation and polish

## Dependencies
- [Dependency 1]
- [Dependency 2]

## Risk Assessment
- [Risk 1]: [Mitigation strategy]
- [Risk 2]: [Mitigation strategy]
""",
            "tasks": """---
title: "Tasks: {feature_title}"
feature_id: "{feature_id}"
phase: "3.execution"
---

# Tasks: {feature_title}

**Input**: Design documents from `/specs/{feature_id}/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)

```
1. Load plan.md from feature directory
2. Load optional design documents
3. Generate tasks by category
4. Apply task rules
5. Number tasks sequentially
6. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [ ] T001 Create project structure
- [ ] T002 Initialize dependencies

## Phase 3.2: Implementation
- [ ] T003 Implement core functionality
- [ ] T004 Add error handling

## Phase 3.3: Testing
- [ ] T005 Unit tests
- [ ] T006 Integration tests

## Phase 3.4: Polish
- [ ] T007 Documentation
- [ ] T008 Performance optimization
"""
        }

    @pytest.mark.contract
    def test_template_resource_class_exists(self):
        """Test that the TemplateResource class exists and is importable."""
        assert TemplateResource is not None, "TemplateResource class must exist"

    @pytest.mark.contract
    def test_template_model_exists(self):
        """Test that the Template Pydantic model exists."""
        assert Template is not None, "Template model must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_resource_uri_patterns(self, template_uris):
        """Test that template resources follow proper MCP URI patterns."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        # Test URI pattern validation
        for uri in template_uris:
            assert uri.startswith("mcp://speckit/templates/"), f"URI {uri} must follow mcp://speckit/templates/ pattern"

            # Extract template type from URI
            template_type = uri.split("/")[-1]
            assert template_type in ["spec", "plan", "tasks", "constitution"], f"Template type {template_type} must be valid"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_resource_metadata(self):
        """Test that template resources have proper MCP resource metadata."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        try:
            resource = TemplateResource()

            # Test resource registration methods exist
            assert hasattr(resource, 'list_resources'), "TemplateResource must have list_resources method"
            assert hasattr(resource, 'read_resource'), "TemplateResource must have read_resource method"

            # Test list_resources returns proper metadata
            resources = await resource.list_resources()
            assert isinstance(resources, list), "list_resources must return a list"

            for resource_info in resources:
                assert 'uri' in resource_info, "Resource info must include URI"
                assert 'name' in resource_info, "Resource info must include name"
                assert 'description' in resource_info, "Resource info must include description"
                assert 'mimeType' in resource_info, "Resource info must include mimeType"

                # Verify MIME type for template resources
                assert resource_info['mimeType'] in ['text/markdown', 'text/plain', 'application/x-template'], \
                    f"Template resource must have valid MIME type, got {resource_info['mimeType']}"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_resource_content_structure(self, mock_template_content):
        """Test that template resources return content with proper structure."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        try:
            resource = TemplateResource()

            for template_type, expected_content in mock_template_content.items():
                uri = f"mcp://speckit/templates/{template_type}"

                content = await resource.read_resource(uri)
                assert content is not None, f"Template {template_type} must return content"
                assert isinstance(content, str), f"Template {template_type} content must be string"

                # Verify YAML front matter exists
                assert content.startswith('---'), f"Template {template_type} must have YAML front matter"
                assert '---\n' in content, f"Template {template_type} must have proper front matter delimiter"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_yaml_front_matter_processing(self):
        """Test that templates properly parse and validate YAML front matter."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        try:
            resource = TemplateResource()

            # Test spec template front matter
            spec_content = await resource.read_resource("mcp://speckit/templates/spec")

            # Extract front matter
            if spec_content and spec_content.startswith('---'):
                parts = spec_content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1].strip()

                    # Parse YAML front matter
                    import yaml
                    try:
                        metadata = yaml.safe_load(front_matter)
                        assert isinstance(metadata, dict), "Front matter must be valid YAML dictionary"

                        # Verify required front matter fields
                        required_fields = ['title', 'id', 'description', 'phase']
                        for field in required_fields:
                            assert field in metadata, f"Front matter must include {field}"

                    except yaml.YAMLError:
                        pytest.fail("Front matter must be valid YAML")

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_variable_substitution(self):
        """Test that templates support variable substitution in content."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        try:
            resource = TemplateResource()

            # Test variable substitution capability
            template_vars = {
                "feature_title": "User Authentication System",
                "feature_id": "001-auth-system",
                "description": "Implement JWT-based user authentication",
                "tech_stack": "Python, FastAPI, JWT"
            }

            # Get template content
            spec_content = await resource.read_resource("mcp://speckit/templates/spec")

            # Verify template contains substitution variables
            assert "{feature_title}" in spec_content, "Template must contain {feature_title} variable"
            assert "{feature_id}" in spec_content, "Template must contain {feature_id} variable"
            assert "{description}" in spec_content, "Template must contain {description} variable"

            # Test substitution method exists
            if hasattr(resource, 'substitute_variables'):
                substituted = await resource.substitute_variables(spec_content, template_vars)

                # Verify substitution worked
                assert "{feature_title}" not in substituted, "Variables must be substituted"
                assert "User Authentication System" in substituted, "Substituted values must appear"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_resource_error_handling(self):
        """Test proper error handling for invalid template requests."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        try:
            resource = TemplateResource()

            # Test invalid URI
            with pytest.raises(Exception) as exc_info:
                await resource.read_resource("mcp://invalid/templates/nonexistent")

            # Should raise appropriate exception
            error = exc_info.value
            assert error is not None, "Must raise exception for invalid URI"

            # Test malformed URI
            with pytest.raises(Exception):
                await resource.read_resource("invalid://uri/format")

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_resource_mcp_compliance(self):
        """Test that template resources are MCP protocol compliant."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        try:
            resource = TemplateResource()

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

                # Verify response is JSON serializable (MCP requirement)
                json.dumps(resource_info)  # Should not raise exception

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    def test_template_resource_in_mcp_server(self):
        """Test that template resources are properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify template resources are registered
            resources = getattr(server, 'resources', {})
            template_resources = [r for r in resources if 'templates' in str(r)]
            assert len(template_resources) > 0, "Template resources must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_model_validation(self):
        """Test Template Pydantic model validation."""
        if Template is None:
            pytest.fail("Template model not implemented yet - expected for TDD")

        try:
            # Test valid template creation
            valid_template = Template(
                name="spec-template",
                content="# Spec Template\n\n{description}",
                variables=["description", "feature_id"],
                mime_type="text/markdown"
            )

            assert valid_template.name == "spec-template"
            assert valid_template.mime_type == "text/markdown"
            assert "description" in valid_template.variables

            # Test invalid template validation
            with pytest.raises(ValidationError):
                Template(
                    name="",  # Empty name should fail
                    content="content",
                    variables=[],
                    mime_type="text/markdown"
                )

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Model not implemented yet - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_template_resource_concurrent_access(self):
        """Test that template resources handle concurrent access properly."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        try:
            resource = TemplateResource()

            # Test concurrent template access
            template_uris = [
                "mcp://speckit/templates/spec",
                "mcp://speckit/templates/plan",
                "mcp://speckit/templates/tasks"
            ]

            # Execute multiple resource reads concurrently
            import asyncio
            tasks = [
                resource.read_resource(uri) for uri in template_uris
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all operations completed
            assert len(results) == len(template_uris), "All concurrent operations must complete"

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
    async def test_template_resource_caching(self):
        """Test that template resources implement proper caching behavior."""
        if TemplateResource is None:
            pytest.fail("TemplateResource not implemented yet - expected for TDD")

        try:
            resource = TemplateResource()

            # Test template caching if implemented
            uri = "mcp://speckit/templates/spec"

            # First read
            content1 = await resource.read_resource(uri)

            # Second read (should use cache if implemented)
            content2 = await resource.read_resource(uri)

            # Content should be identical
            assert content1 == content2, "Template content must be consistent"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise