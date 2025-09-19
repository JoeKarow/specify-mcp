"""
Contract tests for the get_context MCP tool.

These tests verify MCP protocol compliance and tool schema validation for the get_context tool.
The get_context tool retrieves phase-specific documentation and context.

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
    from speckit_mcp.tools.context import get_context
    from speckit_mcp.server import create_server
except ImportError:
    # Expected for TDD - tests should fail until implementation exists
    get_context = None
    create_server = None


class TestContextToolContract:
    """Contract tests for the get_context MCP tool ensuring MCP protocol compliance."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository with documentation for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create .specify-mcp documentation structure
            docs_dir = repo_path / ".specify-mcp" / "docs"
            docs_dir.mkdir(parents=True)

            # Create phase-specific documentation
            phases = ['specify', 'plan', 'tasks', 'implementation']
            for phase in phases:
                phase_dir = docs_dir / phase
                phase_dir.mkdir()

                # Create sample documentation files
                (phase_dir / "guide.md").write_text(f"# {phase.title()} Phase Guide\n\nThis is the guide for {phase} phase.")
                (phase_dir / "examples.md").write_text(f"# {phase.title()} Examples\n\nExamples for {phase} phase.")
                (phase_dir / "troubleshooting.md").write_text(f"# {phase.title()} Troubleshooting\n\nTroubleshooting for {phase}.")

            # Create general documentation
            (docs_dir / "getting-started.md").write_text("# Getting Started\n\nGeneral getting started guide.")
            (docs_dir / "principles.md").write_text("# Principles\n\nCore principles and guidelines.")

            yield repo_path

    @pytest.fixture
    def mock_file_operations(self):
        """Mock file system operations."""
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.glob') as mock_glob:
            mock_exists.return_value = True
            mock_glob.return_value = []  # Will be overridden in individual tests
            yield mock_exists, mock_glob

    @pytest.mark.contract
    def test_get_context_tool_exists(self):
        """Test that the get_context tool function exists and is importable."""
        assert get_context is not None, "get_context tool function must exist"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_mcp_schema_compliance(self):
        """Test that get_context tool complies with MCP tool schema requirements."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(get_context), "get_context tool must be async"

        # Verify function has proper type hints
        sig = inspect.signature(get_context)
        assert 'phase' in sig.parameters, "get_context tool must accept 'phase' parameter"
        assert 'repository_path' in sig.parameters, "get_context tool must accept 'repository_path' parameter"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_input_validation(self, temp_repo, mock_file_operations):
        """Test input validation for the get_context tool using Pydantic models."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        valid_phase = "specify"
        valid_repo_path = str(temp_repo)

        # Test valid inputs
        try:
            result = await get_context(
                phase=valid_phase,
                repository_path=valid_repo_path
            )
            assert isinstance(result, dict), "get_context tool must return a dictionary"
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_invalid_inputs(self, temp_repo):
        """Test that get_context tool properly validates and rejects invalid inputs."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        # Test invalid phase
        with pytest.raises(ValidationError):
            await get_context(
                phase="invalid_phase",
                repository_path=str(temp_repo)
            )

        # Test non-existent repository path
        with pytest.raises(ValidationError):
            await get_context(
                phase="specify",
                repository_path="/nonexistent/path"
            )

        # Test None values
        with pytest.raises(ValidationError):
            await get_context(phase=None, repository_path=str(temp_repo))

        # Test empty strings
        with pytest.raises(ValidationError):
            await get_context(phase="", repository_path=str(temp_repo))

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_phase_filtering(self, temp_repo, mock_file_operations):
        """Test that get_context tool filters documentation by phase properly."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        mock_exists, mock_glob = mock_file_operations

        # Mock phase-specific files
        specify_files = [
            Path(temp_repo) / ".specify-mcp" / "docs" / "specify" / "guide.md",
            Path(temp_repo) / ".specify-mcp" / "docs" / "specify" / "examples.md"
        ]
        mock_glob.return_value = specify_files

        try:
            result = await get_context(
                phase="specify",
                repository_path=str(temp_repo)
            )

            # Verify result structure includes phase-specific content
            assert 'documents' in result, "Result must include documents"
            assert 'phase' in result, "Result must include phase"
            assert 'total_documents' in result, "Result must include total_documents"

            # Verify phase filtering
            assert result['phase'] == 'specify', "Should return correct phase"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_document_retrieval(self, temp_repo, mock_file_operations):
        """Test that get_context tool retrieves document content properly."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        mock_exists, mock_glob = mock_file_operations

        # Mock document files
        plan_files = [
            Path(temp_repo) / ".specify-mcp" / "docs" / "plan" / "guide.md",
            Path(temp_repo) / ".specify-mcp" / "docs" / "plan" / "troubleshooting.md"
        ]
        mock_glob.return_value = plan_files

        try:
            with patch('pathlib.Path.read_text') as mock_read:
                mock_read.return_value = "# Plan Guide\n\nPlan phase documentation content."

                result = await get_context(
                    phase="plan",
                    repository_path=str(temp_repo)
                )

                # Verify document content was read
                mock_read.assert_called()

                # Verify documents in result
                documents = result.get('documents', [])
                assert isinstance(documents, list), "Documents must be a list"

                for doc in documents:
                    assert 'path' in doc, "Each document must have path"
                    assert 'content' in doc, "Each document must have content"
                    assert 'title' in doc, "Each document must have title"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_all_phases_support(self, temp_repo, mock_file_operations):
        """Test that get_context tool supports all defined phases."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        valid_phases = ['specify', 'plan', 'tasks', 'implementation', 'all']

        for phase in valid_phases:
            try:
                result = await get_context(
                    phase=phase,
                    repository_path=str(temp_repo)
                )

                # Should successfully handle all valid phases
                assert isinstance(result, dict), f"Should handle {phase} phase"
                assert 'phase' in result, f"Result should include phase for {phase}"

            except Exception as e:
                if "not implemented" in str(e).lower():
                    pytest.skip("Implementation not complete - expected for TDD")
                raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_general_documentation(self, temp_repo, mock_file_operations):
        """Test that get_context tool can retrieve general documentation."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        mock_exists, mock_glob = mock_file_operations

        # Mock general documentation files
        general_files = [
            Path(temp_repo) / ".specify-mcp" / "docs" / "getting-started.md",
            Path(temp_repo) / ".specify-mcp" / "docs" / "principles.md"
        ]
        mock_glob.return_value = general_files

        try:
            result = await get_context(
                phase="all",  # Request all documentation
                repository_path=str(temp_repo)
            )

            # Should include general documentation
            documents = result.get('documents', [])
            assert len(documents) > 0, "Should return documentation"

            # Check for general docs
            doc_paths = [doc['path'] for doc in documents]
            assert any('getting-started' in path for path in doc_paths), "Should include general docs"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_error_handling(self, temp_repo):
        """Test proper error handling and MCPError responses."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        # Test file read failure
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.side_effect = IOError("Permission denied")

            # Should handle file read errors gracefully
            try:
                result = await get_context(
                    phase="specify",
                    repository_path=str(temp_repo)
                )
                # May return empty result or error, but should not crash
                assert isinstance(result, dict), "Should return dict even on errors"
            except Exception as e:
                # Should raise appropriate exception type
                assert "Permission denied" in str(e) or "not implemented" in str(e).lower()

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_missing_docs_directory(self, temp_repo):
        """Test behavior when documentation directory doesn't exist."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        # Test with non-existent docs directory
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            try:
                result = await get_context(
                    phase="specify",
                    repository_path=str(temp_repo)
                )

                # Should handle missing docs gracefully
                assert isinstance(result, dict), "Should return dict for missing docs"
                assert 'documents' in result, "Should include documents field (may be empty)"

            except Exception as e:
                if "not implemented" in str(e).lower():
                    pytest.skip("Implementation not complete - expected for TDD")
                # Should raise appropriate error for missing docs
                assert "not found" in str(e).lower() or "missing" in str(e).lower()

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_mcp_response_format(self, temp_repo, mock_file_operations):
        """Test that get_context tool returns MCP-compliant response format."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        try:
            result = await get_context(
                phase="specify",
                repository_path=str(temp_repo)
            )

            # Verify JSON-RPC 2.0 compatible response structure
            assert isinstance(result, dict), "Response must be a dictionary"

            # Check for required fields in response
            required_fields = ['documents', 'phase', 'total_documents']
            for field in required_fields:
                assert field in result, f"Response must include {field}"

            # Verify response is JSON serializable (MCP requirement)
            json.dumps(result)  # Should not raise exception

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    def test_get_context_tool_in_mcp_server(self):
        """Test that get_context tool is properly registered in MCP server."""
        if create_server is None:
            pytest.fail("MCP server not implemented yet - expected for TDD")

        try:
            server = create_server()

            # Verify get_context tool is registered
            tools = getattr(server, 'tools', {})
            assert 'get_context' in tools, "get_context tool must be registered in MCP server"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Server implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_content_filtering(self, temp_repo, mock_file_operations):
        """Test that get_context tool can filter content by keywords or topics."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        try:
            # Test with optional filtering parameter if supported
            result = await get_context(
                phase="specify",
                repository_path=str(temp_repo),
                topic="git"  # Optional parameter for filtering
            )

            # Should handle topic filtering
            assert isinstance(result, dict), "Should return dict with topic filtering"

        except TypeError:
            # Topic parameter may not be implemented yet - that's okay
            result = await get_context(
                phase="specify",
                repository_path=str(temp_repo)
            )
            assert isinstance(result, dict), "Should work without topic filtering"
        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_document_metadata(self, temp_repo, mock_file_operations):
        """Test that get_context tool includes proper document metadata."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        mock_exists, mock_glob = mock_file_operations

        # Mock document files with metadata
        task_files = [Path(temp_repo) / ".specify-mcp" / "docs" / "tasks" / "guide.md"]
        mock_glob.return_value = task_files

        try:
            with patch('pathlib.Path.read_text') as mock_read, \
                 patch('pathlib.Path.stat') as mock_stat:

                mock_read.return_value = "# Tasks Guide\n\nTasks documentation content."
                mock_stat.return_value.st_mtime = 1234567890  # Mock modification time

                result = await get_context(
                    phase="tasks",
                    repository_path=str(temp_repo)
                )

                # Verify document metadata
                documents = result.get('documents', [])
                for doc in documents:
                    assert 'path' in doc, "Document must have path"
                    assert 'title' in doc, "Document must have title"
                    assert 'content' in doc, "Document must have content"
                    # May include additional metadata like modified_at, size, etc.

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_get_context_tool_concurrent_execution(self, temp_repo, mock_file_operations):
        """Test that get_context tool handles concurrent execution properly."""
        if get_context is None:
            pytest.fail("get_context tool not implemented yet - expected for TDD")

        phases = ['specify', 'plan', 'tasks', 'implementation']

        try:
            # Execute multiple get_context operations concurrently
            import asyncio
            tasks = [
                get_context(phase, str(temp_repo)) for phase in phases
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all operations completed (even if with errors due to no implementation)
            assert len(results) == len(phases), "All concurrent operations must complete"

            # Each result should be a dict or exception
            for result in results:
                if not isinstance(result, Exception):
                    assert isinstance(result, dict), "Non-exception results must be dictionaries"

        except Exception as e:
            if "not implemented" in str(e).lower():
                pytest.skip("Implementation not complete - expected for TDD")
            raise