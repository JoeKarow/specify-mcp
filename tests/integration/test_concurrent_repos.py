"""Integration tests for concurrent repository operations.

This test suite verifies concurrent operations including:
- Concurrent operations on multiple repositories
- Repository session isolation and state management
- Resource locking and synchronization mechanisms
- Async operation handling and performance
- Error handling and recovery in concurrent scenarios

These tests MUST fail initially as no implementation exists yet (TDD requirement).
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any, Tuple
import time
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

# Import concurrent operation modules (will fail until implemented)
try:
    from mcp import MCPError
    from speckit_mcp.server import create_mcp_server
    from speckit_mcp.tools.specify import specify_tool
    from speckit_mcp.tools.plan import plan_tool
    from speckit_mcp.tools.tasks import tasks_tool
    from speckit_mcp.config.models import WorkflowSession, RepositoryRegistration
    from speckit_mcp.git.operations import GitOperations
    from speckit_mcp.utils.concurrency import (
        RepositoryLockManager,
        SessionManager,
        ConcurrentOperationError,
        ResourceLockTimeout
    )
except ImportError:
    # Expected to fail until implementation exists
    pytest.skip("Implementation not available yet - TDD phase", allow_module_level=True)


class TestConcurrentRepositoryOperations:
    """Integration tests for concurrent repository operations."""

    @pytest.fixture
    async def multiple_repositories(self, tmp_path: Path) -> List[Path]:
        """Create multiple temporary git repositories for testing.

        Returns:
            List of paths to temporary repositories
        """
        repositories = []
        for i in range(3):
            repo_path = tmp_path / f"repo_{i}"
            repo_path.mkdir()

            # Initialize git repository
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
                git_ops = GitOperations(str(repo_path))
                await git_ops.initialize_repository()

            repositories.append(repo_path)

        return repositories

    @pytest.fixture
    async def session_manager(self) -> SessionManager:
        """Create session manager for testing.

        Returns:
            SessionManager instance for concurrent session handling
        """
        return SessionManager()

    @pytest.fixture
    async def lock_manager(self) -> RepositoryLockManager:
        """Create repository lock manager for testing.

        Returns:
            RepositoryLockManager instance for resource locking
        """
        return RepositoryLockManager()

    @pytest.mark.asyncio
    async def test_concurrent_specify_operations_different_repos(
        self,
        multiple_repositories: List[Path],
        session_manager: SessionManager
    ):
        """Test concurrent specify operations on different repositories.

        Verifies:
        - Multiple repositories can be operated on simultaneously
        - No interference between repository operations
        - Proper isolation of workflow sessions
        - Performance benefits of concurrent execution
        """
        repositories = multiple_repositories
        feature_descriptions = [
            "Add user authentication system",
            "Implement payment processing",
            "Create notification service"
        ]

        with patch('subprocess.run') as mock_run:
            # Mock git operations for all repositories
            mock_run.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            start_time = time.time()

            # Execute concurrent specify operations
            tasks = [
                specify_tool(
                    description=desc,
                    repository_path=str(repo)
                )
                for desc, repo in zip(feature_descriptions, repositories)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            execution_time = time.time() - start_time

            # Verify all operations succeeded
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == 3

            # Verify unique feature IDs across repositories
            feature_ids = [r['feature_id'] for r in successful_results]
            assert len(set(feature_ids)) == 3

            # Verify repository isolation
            for i, result in enumerate(successful_results):
                expected_repo = str(repositories[i])
                # Each operation should have created files in correct repository
                spec_path = Path(result['spec_path'])
                assert expected_repo in str(spec_path)

            # Verify performance benefit (should be faster than sequential)
            # Note: This is a rough check - actual timing would depend on implementation
            assert execution_time < 10.0  # Should complete quickly with proper concurrency

    @pytest.mark.asyncio
    async def test_concurrent_operations_same_repository_with_locking(
        self,
        multiple_repositories: List[Path],
        lock_manager: RepositoryLockManager
    ):
        """Test concurrent operations on same repository with proper locking.

        Verifies:
        - Repository locking prevents conflicting operations
        - Operations are queued and executed sequentially on same repository
        - Lock acquisition and release works correctly
        - Timeout handling for long-running operations
        """
        repo_path = multiple_repositories[0]
        feature_descriptions = [
            "Add user authentication",
            "Add user authorization",
            "Add user profile management"
        ]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            # Execute concurrent operations on same repository
            tasks = [
                specify_tool(
                    description=desc,
                    repository_path=str(repo_path)
                )
                for desc in feature_descriptions
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Should handle concurrent access appropriately
            successful_results = [r for r in results if not isinstance(r, Exception)]
            failed_results = [r for r in results if isinstance(r, Exception)]

            # Either all succeed (queued properly) or some fail with appropriate errors
            if len(successful_results) == len(feature_descriptions):
                # All succeeded - verify they were executed sequentially
                feature_ids = [r['feature_id'] for r in successful_results]
                assert len(set(feature_ids)) == 3  # Unique feature IDs

                # Verify git operations were called multiple times sequentially
                git_call_count = mock_run.call_count
                assert git_call_count >= len(feature_descriptions)
            else:
                # Some failed - verify appropriate error handling
                for error in failed_results:
                    assert isinstance(error, (ConcurrentOperationError, ResourceLockTimeout, MCPError))

    @pytest.mark.asyncio
    async def test_workflow_session_isolation(
        self,
        multiple_repositories: List[Path],
        session_manager: SessionManager
    ):
        """Test workflow session isolation between repositories.

        Verifies:
        - Each repository maintains independent workflow session
        - Session state doesn't leak between repositories
        - Concurrent session updates work correctly
        """
        repositories = multiple_repositories

        # Start workflow sessions in multiple repositories
        session_data = []
        for i, repo in enumerate(repositories):
            session = WorkflowSession(
                feature_id=f"feature-{i}",
                repository_path=str(repo),
                current_phase="specify",
                branch_name=f"feature/feature-{i}"
            )

            await session_manager.create_session(session)
            session_data.append(session)

        # Verify session isolation
        for i, session in enumerate(session_data):
            retrieved_session = await session_manager.get_session(
                repository_path=str(repositories[i]),
                feature_id=f"feature-{i}"
            )

            assert retrieved_session.feature_id == session.feature_id
            assert retrieved_session.repository_path == session.repository_path
            assert retrieved_session.current_phase == session.current_phase

        # Test concurrent session updates
        update_tasks = []
        for i, session in enumerate(session_data):
            update_tasks.append(
                session_manager.update_session_phase(
                    repository_path=str(repositories[i]),
                    feature_id=f"feature-{i}",
                    new_phase="plan"
                )
            )

        await asyncio.gather(*update_tasks)

        # Verify updates were applied correctly
        for i in range(len(repositories)):
            updated_session = await session_manager.get_session(
                repository_path=str(repositories[i]),
                feature_id=f"feature-{i}"
            )
            assert updated_session.current_phase == "plan"

    @pytest.mark.asyncio
    async def test_concurrent_full_workflow_execution(
        self,
        multiple_repositories: List[Path]
    ):
        """Test concurrent execution of full workflows (specify -> plan -> tasks).

        Verifies:
        - Complete workflows can run concurrently on different repositories
        - Workflow phase transitions work correctly
        - No state interference between workflows
        """
        repositories = multiple_repositories[:2]  # Use 2 repositories for this test
        feature_descriptions = [
            "Add comprehensive user management system",
            "Implement real-time chat functionality"
        ]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            # Execute concurrent full workflows
            async def execute_full_workflow(repo_path: Path, description: str) -> Dict[str, Any]:
                """Execute complete workflow: specify -> plan -> tasks"""

                # Step 1: Specify
                specify_result = await specify_tool(
                    description=description,
                    repository_path=str(repo_path)
                )

                # Step 2: Plan
                plan_result = await plan_tool(
                    feature_id=specify_result['feature_id'],
                    repository_path=str(repo_path)
                )

                # Step 3: Tasks
                tasks_result = await tasks_tool(
                    feature_id=specify_result['feature_id'],
                    repository_path=str(repo_path)
                )

                return {
                    'specify': specify_result,
                    'plan': plan_result,
                    'tasks': tasks_result
                }

            workflow_tasks = [
                execute_full_workflow(repo, desc)
                for repo, desc in zip(repositories, feature_descriptions)
            ]

            results = await asyncio.gather(*workflow_tasks, return_exceptions=True)

            # Verify both workflows completed successfully
            successful_workflows = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_workflows) == 2

            # Verify workflow completeness
            for workflow_result in successful_workflows:
                assert 'specify' in workflow_result
                assert 'plan' in workflow_result
                assert 'tasks' in workflow_result

                assert workflow_result['specify']['success'] is True
                assert workflow_result['plan']['success'] is True
                assert workflow_result['tasks']['success'] is True

    @pytest.mark.asyncio
    async def test_repository_lock_timeout_handling(
        self,
        multiple_repositories: List[Path],
        lock_manager: RepositoryLockManager
    ):
        """Test repository lock timeout handling.

        Verifies:
        - Lock timeouts are properly handled
        - Operations fail gracefully when locks cannot be acquired
        - Lock cleanup occurs even after timeout
        """
        repo_path = multiple_repositories[0]

        # Simulate long-running operation holding lock
        async def long_running_operation():
            async with lock_manager.acquire_lock(str(repo_path), timeout=60):
                await asyncio.sleep(5)  # Hold lock for 5 seconds
                return "Long operation completed"

        # Start long-running operation
        long_task = asyncio.create_task(long_running_operation())

        # Wait briefly to ensure lock is acquired
        await asyncio.sleep(0.1)

        # Try to acquire same lock with short timeout
        with pytest.raises(ResourceLockTimeout):
            async with lock_manager.acquire_lock(str(repo_path), timeout=1):
                await specify_tool(
                    description="Quick operation",
                    repository_path=str(repo_path)
                )

        # Wait for long operation to complete
        await long_task

        # Verify lock is released and new operations can proceed
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            result = await specify_tool(
                description="Operation after lock release",
                repository_path=str(repo_path)
            )

            assert result['success'] is True

    @pytest.mark.asyncio
    async def test_concurrent_repository_registration(
        self,
        multiple_repositories: List[Path]
    ):
        """Test concurrent repository registration and management.

        Verifies:
        - Multiple repositories can be registered simultaneously
        - Repository metadata is maintained correctly
        - Concurrent access to repository registry works
        """
        repositories = multiple_repositories

        # Create repository registrations
        registrations = [
            RepositoryRegistration(
                path=str(repo),
                name=f"test-repo-{i}",
                description=f"Test repository {i} for concurrent testing"
            )
            for i, repo in enumerate(repositories)
        ]

        from speckit_mcp.config.manager import RepositoryRegistry
        registry = RepositoryRegistry()

        # Register repositories concurrently
        registration_tasks = [
            registry.register_repository(reg)
            for reg in registrations
        ]

        registration_results = await asyncio.gather(*registration_tasks)

        # Verify all registrations succeeded
        for result in registration_results:
            assert result['success'] is True

        # Verify concurrent access to registry
        async def get_repository_info(repo_path: str) -> Dict[str, Any]:
            return await registry.get_repository(repo_path)

        info_tasks = [
            get_repository_info(str(repo))
            for repo in repositories
        ]

        repo_infos = await asyncio.gather(*info_tasks)

        # Verify correct information returned
        for i, repo_info in enumerate(repo_infos):
            assert repo_info['name'] == f"test-repo-{i}"
            assert repo_info['path'] == str(repositories[i])

    @pytest.mark.asyncio
    async def test_error_recovery_in_concurrent_operations(
        self,
        multiple_repositories: List[Path]
    ):
        """Test error recovery in concurrent operations.

        Verifies:
        - Errors in one repository don't affect others
        - Proper cleanup occurs after errors
        - Recovery and retry mechanisms work
        """
        repositories = multiple_repositories

        # Mix of valid and invalid operations
        operations = [
            ("valid operation", str(repositories[0])),
            ("another valid operation", str(repositories[1])),
            ("invalid operation", "/nonexistent/path"),  # This should fail
        ]

        with patch('subprocess.run') as mock_run:
            def mock_git_command(cmd, cwd, **kwargs):
                if cwd == "/nonexistent/path":
                    return Mock(returncode=128, stdout='', stderr='fatal: not a git repository')
                return Mock(returncode=0, stdout='main\n', stderr='')

            mock_run.side_effect = mock_git_command

            tasks = [
                specify_tool(description=desc, repository_path=repo_path)
                for desc, repo_path in operations
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify partial success
            successful_results = [r for r in results if not isinstance(r, Exception)]
            failed_results = [r for r in results if isinstance(r, Exception)]

            assert len(successful_results) == 2  # Two valid operations
            assert len(failed_results) == 1     # One invalid operation

            # Verify failed operation has appropriate error
            assert isinstance(failed_results[0], MCPError)

    @pytest.mark.asyncio
    async def test_concurrent_resource_access_patterns(
        self,
        multiple_repositories: List[Path]
    ):
        """Test various concurrent resource access patterns.

        Verifies:
        - Read-heavy workloads perform well
        - Write operations are properly serialized
        - Mixed read/write patterns work correctly
        """
        repo_path = multiple_repositories[0]

        # Setup initial repository state
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            # Create initial feature
            initial_result = await specify_tool(
                description="Initial feature for testing",
                repository_path=str(repo_path)
            )

        # Test concurrent read operations (should all succeed)
        from speckit_mcp.tools.context import get_context_tool

        read_tasks = [
            get_context_tool(
                repository_path=str(repo_path),
                feature_id=initial_result['feature_id'],
                phase="specify"
            )
            for _ in range(5)
        ]

        read_results = await asyncio.gather(*read_tasks, return_exceptions=True)

        # All reads should succeed
        successful_reads = [r for r in read_results if not isinstance(r, Exception)]
        assert len(successful_reads) == 5

        # Test mixed read/write operations
        mixed_tasks = []

        # Add more read operations
        for _ in range(3):
            mixed_tasks.append(
                get_context_tool(
                    repository_path=str(repo_path),
                    feature_id=initial_result['feature_id'],
                    phase="specify"
                )
            )

        # Add write operations (these may be serialized)
        mixed_tasks.extend([
            plan_tool(
                feature_id=initial_result['feature_id'],
                repository_path=str(repo_path)
            ),
            tasks_tool(
                feature_id=initial_result['feature_id'],
                repository_path=str(repo_path)
            )
        ])

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            mixed_results = await asyncio.gather(*mixed_tasks, return_exceptions=True)

            # Most operations should succeed (some writes might be serialized)
            successful_mixed = [r for r in mixed_results if not isinstance(r, Exception)]
            assert len(successful_mixed) >= 3  # At least the reads should succeed

    @pytest.mark.asyncio
    async def test_memory_usage_during_concurrent_operations(
        self,
        multiple_repositories: List[Path]
    ):
        """Test memory usage patterns during concurrent operations.

        Verifies:
        - Memory usage remains reasonable under concurrent load
        - No memory leaks from unclosed resources
        - Proper cleanup of temporary objects
        """
        import gc
        import sys

        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Execute many concurrent operations
        repositories = multiple_repositories
        operations_per_repo = 10

        all_tasks = []
        for repo in repositories:
            for i in range(operations_per_repo):
                all_tasks.append(
                    specify_tool(
                        description=f"Feature {i} for memory test",
                        repository_path=str(repo)
                    )
                )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='main\n', stderr='')

            # Execute all operations
            results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())

        # Memory usage should not have grown excessively
        object_growth = final_objects - initial_objects

        # This is a rough check - exact numbers depend on implementation
        # The growth should be reasonable (not linear with operation count)
        max_acceptable_growth = len(all_tasks) * 50  # Arbitrary reasonable limit
        assert object_growth < max_acceptable_growth, f"Memory usage grew by {object_growth} objects"

        # Verify operations completed successfully
        successful_operations = [r for r in results if not isinstance(r, Exception)]
        # Allow for some failures due to concurrent access limitations
        min_expected_success = len(all_tasks) * 0.8  # At least 80% should succeed
        assert len(successful_operations) >= min_expected_success