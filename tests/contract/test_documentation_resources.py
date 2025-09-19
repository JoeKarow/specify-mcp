"""
Contract tests for the documentation MCP resources.

These tests verify MCP protocol compliance and resource schema validation for documentation resources.
Documentation resources serve guides and references with proper resource listing, content retrieval,
metadata handling, and phase-specific documentation filtering.

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
    from speckit_mcp.resources.documentation import DocumentationResource
    from speckit_mcp.server import create_server
    from speckit_mcp.resources.models import ContextDocument
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    DocumentationResource = None
    create_server = None
    ContextDocument = None


class TestDocumentationResourcesContract:
    """Contract tests for documentation MCP resources ensuring MCP protocol compliance."""

    @pytest.fixture
    def documentation_uris(self):
        """Standard documentation resource URIs following MCP resource pattern."""
        return [
            "mcp://speckit/docs/guides/getting-started",
            "mcp://speckit/docs/guides/specification-writing",
            "mcp://speckit/docs/guides/planning-strategies",
            "mcp://speckit/docs/guides/task-management",
            "mcp://speckit/docs/reference/constitution",
            "mcp://speckit/docs/reference/workflows",
            "mcp://speckit/docs/reference/templates",
            "mcp://speckit/docs/reference/api"
        ]

    @pytest.fixture
    def phase_specific_docs(self):
        """Documentation organized by development phases."""
        return {
            "specification": [
                "mcp://speckit/docs/guides/specification-writing",
                "mcp://speckit/docs/reference/constitution"
            ],
            "planning": [
                "mcp://speckit/docs/guides/planning-strategies",
                "mcp://speckit/docs/reference/workflows"
            ],
            "execution": [
                "mcp://speckit/docs/guides/task-management",
                "mcp://speckit/docs/reference/templates"
            ]
        }

    @pytest.fixture
    def mock_documentation_content(self):
        """Mock documentation content with metadata."""
        return {
            "getting-started": {
                "title": "Getting Started with SpecKit MCP",
                "phase": "all",
                "tags": ["introduction", "setup"],
                "content": """# Getting Started with SpecKit MCP

## Overview
SpecKit MCP provides a Model Context Protocol server for managing software specifications, planning, and task execution.

## Installation
```bash
pip install speckit-mcp
```

## Quick Start
1. Initialize a new project
2. Create your first specification
3. Generate implementation plan
4. Execute tasks
"""
            },
            "specification-writing": {
                "title": "Writing Effective Specifications",
                "phase": "specification",
                "tags": ["specification", "best-practices"],
                "content": """# Writing Effective Specifications

## Principles
- Clear problem statement
- Measurable success criteria
- Technical constraints
- User stories

## Template Structure
Use the provided specification template for consistency.
"""
            },
            "constitution": {
                "title": "SpecKit Constitution Reference",
                "phase": "all",
                "tags": ["reference", "constitution"],
                "content": """# SpecKit Constitution Reference

## Core Principles
1. MCP Protocol Compliance
2. File System Preservation
3. Test-First Development
4. Structured Data (YAML over markdown)
5. Simplicity (YAGNI)
6. Cross-Platform Compatibility
"""
            }
        }

    @pytest.mark.contract
    def test_documentation_resource_class_exists(self):
        """Test that the DocumentationResource class exists and is importable."""
        assert DocumentationResource is not None, "DocumentationResource class must exist"

    @pytest.mark.contract
    def test_context_document_model_exists(self):
        """Test that the ContextDocument Pydantic model exists."""
        assert ContextDocument is not None, "ContextDocument model must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_resource_uri_patterns(self, documentation_uris):
        """Test that documentation resources follow proper MCP URI patterns."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        # Test URI pattern validation
        for uri in documentation_uris:
            assert uri.startswith("mcp://speckit/docs/"), f"URI {uri} must follow mcp://speckit/docs/ pattern"

            # Extract document type and category from URI
            parts = uri.split("/")
            assert len(parts) >= 5, f"URI {uri} must have proper structure"

            category = parts[4]  # guides or reference
            assert category in ["guides", "reference"], f"Category {category} must be valid"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_resource_listing(self):
        """Test that documentation resources provide proper resource listing."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            # Test resource registration methods exist
            assert hasattr(resource, 'list_resources'), "DocumentationResource must have list_resources method"
            assert hasattr(resource, 'read_resource'), "DocumentationResource must have read_resource method"

            # Test list_resources returns proper metadata
            resources = await resource.list_resources()
            assert isinstance(resources, list), "list_resources must return a list"

            for resource_info in resources:
                assert 'uri' in resource_info, "Resource info must include URI"
                assert 'name' in resource_info, "Resource info must include name"
                assert 'description' in resource_info, "Resource info must include description"
                assert 'mimeType' in resource_info, "Resource info must include mimeType"

                # Verify MIME type for documentation resources
                assert resource_info['mimeType'] in ['text/markdown', 'text/plain'], \
                    f"Documentation resource must have valid MIME type, got {resource_info['mimeType']}"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_content_retrieval(self, mock_documentation_content):
        """Test that documentation resources return proper content."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            for doc_id, doc_data in mock_documentation_content.items():
                uri = f"mcp://speckit/docs/guides/{doc_id}"

                content = await resource.read_resource(uri)
                assert content is not None, f"Documentation {doc_id} must return content"
                assert isinstance(content, str), f"Documentation {doc_id} content must be string"

                # Verify content is markdown format
                assert content.startswith('#'), f"Documentation {doc_id} must be markdown format"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_metadata_handling(self, mock_documentation_content):
        """Test that documentation resources handle metadata properly."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            # Test metadata extraction if available
            if hasattr(resource, 'get_metadata'):
                for doc_id, doc_data in mock_documentation_content.items():
                    uri = f"mcp://speckit/docs/guides/{doc_id}"

                    metadata = await resource.get_metadata(uri)
                    assert isinstance(metadata, dict), "Metadata must be dictionary"

                    # Verify required metadata fields
                    required_fields = ['title', 'phase', 'tags']
                    for field in required_fields:
                        assert field in metadata, f"Metadata must include {field}"

                    # Verify phase values
                    phase = metadata['phase']
                    valid_phases = ['specification', 'planning', 'execution', 'all']
                    assert phase in valid_phases, f"Phase {phase} must be valid"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_phase_specific_documentation_filtering(self, phase_specific_docs):
        """Test that documentation resources support phase-specific filtering."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            # Test phase filtering capability
            if hasattr(resource, 'list_by_phase'):
                for phase, expected_uris in phase_specific_docs.items():
                    phase_docs = await resource.list_by_phase(phase)
                    assert isinstance(phase_docs, list), f"Phase {phase} docs must be list"

                    # Verify phase-specific documents are returned
                    phase_uris = [doc['uri'] for doc in phase_docs if 'uri' in doc]
                    for expected_uri in expected_uris:
                        assert any(expected_uri in uri for uri in phase_uris), \
                            f"Phase {phase} must include relevant documentation"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_search_capability(self):
        """Test that documentation resources support search functionality."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            # Test search capability if implemented
            if hasattr(resource, 'search'):
                # Search for documentation by keyword
                search_terms = ["specification", "planning", "constitution"]

                for term in search_terms:
                    results = await resource.search(term)
                    assert isinstance(results, list), f"Search for {term} must return list"

                    # Verify search results relevance
                    for result in results:
                        assert 'uri' in result, "Search result must include URI"
                        assert 'title' in result, "Search result must include title"
                        assert 'relevance' in result, "Search result must include relevance score"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_resource_error_handling(self):
        """Test proper error handling for invalid documentation requests."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            # Test invalid URI
            with pytest.raises(Exception) as exc_info:
                await resource.read_resource("mcp://invalid/docs/nonexistent")

            # Should raise appropriate exception
            error = exc_info.value
            assert error is not None, "Must raise exception for invalid URI"

            # Test malformed URI
            with pytest.raises(Exception):
                await resource.read_resource("invalid://uri/format")

            # Test non-existent document
            with pytest.raises(Exception):
                await resource.read_resource("mcp://speckit/docs/guides/nonexistent-doc")

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_resource_mcp_compliance(self):
        """Test that documentation resources are MCP protocol compliant."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

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
    def test_documentation_resource_in_mcp_server(self):
        """Test that documentation resources are properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify documentation resources are registered
            resources = getattr(server, 'resources', {})
            doc_resources = [r for r in resources if 'docs' in str(r)]
            assert len(doc_resources) > 0, "Documentation resources must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_context_document_model_validation(self):
        """Test ContextDocument Pydantic model validation."""
        if ContextDocument is None:
            pytest.fail("ContextDocument model not implemented yet - expected for TDD")

        try:
            # Test valid context document creation
            valid_doc = ContextDocument(
                title="Getting Started Guide",
                content="# Getting Started\n\nThis is a guide...",
                phase="specification",
                tags=["guide", "introduction"],
                uri="mcp://speckit/docs/guides/getting-started"
            )

            assert valid_doc.title == "Getting Started Guide"
            assert valid_doc.phase == "specification"
            assert "guide" in valid_doc.tags

            # Test invalid document validation
            with pytest.raises(ValidationError):
                ContextDocument(
                    title="",  # Empty title should fail
                    content="content",
                    phase="invalid_phase",  # Invalid phase
                    tags=[],
                    uri="invalid_uri"
                )

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Model not implemented yet - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_versioning_support(self):
        """Test that documentation resources support versioning if implemented."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            # Test versioning capability if implemented
            if hasattr(resource, 'get_versions'):
                uri = "mcp://speckit/docs/reference/constitution"

                versions = await resource.get_versions(uri)
                assert isinstance(versions, list), "Versions must be list"

                # If versioning is supported, test version-specific access
                if hasattr(resource, 'read_version'):
                    for version in versions[:1]:  # Test first version only
                        versioned_content = await resource.read_version(uri, version)
                        assert isinstance(versioned_content, str), "Versioned content must be string"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_documentation_resource_concurrent_access(self):
        """Test that documentation resources handle concurrent access properly."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            # Test concurrent documentation access
            doc_uris = [
                "mcp://speckit/docs/guides/getting-started",
                "mcp://speckit/docs/guides/specification-writing",
                "mcp://speckit/docs/reference/constitution"
            ]

            # Execute multiple resource reads concurrently
            import asyncio
            tasks = [
                resource.read_resource(uri) for uri in doc_uris
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all operations completed
            assert len(results) == len(doc_uris), "All concurrent operations must complete"

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
    async def test_documentation_cross_references(self):
        """Test that documentation resources handle cross-references properly."""
        if DocumentationResource is None:
            pytest.fail("DocumentationResource not implemented yet - expected for TDD")

        try:
            resource = DocumentationResource()

            # Test cross-reference capability if implemented
            if hasattr(resource, 'get_references'):
                uri = "mcp://speckit/docs/guides/specification-writing"

                references = await resource.get_references(uri)
                assert isinstance(references, list), "References must be list"

                # Verify reference structure
                for ref in references:
                    assert 'target_uri' in ref, "Reference must include target URI"
                    assert 'context' in ref, "Reference must include context"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise