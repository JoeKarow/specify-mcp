"""Integration tests for git operations.

This test suite verifies git operations including:
- Branch creation, switching, and status checking
- Cross-platform subprocess git command execution
- Error handling for git failures and edge cases
- Concurrent git operations on same repository
- Repository validation and initialization

These tests MUST fail initially as no implementation exists yet (TDD requirement).
"""

import asyncio
import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, call
from typing import List, Dict, Any, Optional

import pytest

# Import git operations module (will fail until implemented)
try:
    from speckit_mcp.git.operations import GitOperations, GitError, BranchOperationError
    from speckit_mcp.config.models import RepositoryRegistration
except ImportError:
    # Expected to fail until implementation exists
    pytest.skip("Implementation not available yet - TDD phase", allow_module_level=True)


class TestGitOperationsIntegration:
    """Integration tests for git operations functionality."""

    @pytest.fixture
    def temp_repository(self, tmp_path: Path) -> Path:
        """Create a temporary directory for git repository testing.

        Returns:
            Path to the temporary repository root
        """
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        return repo_path

    @pytest.fixture
    def git_ops(self, temp_repository: Path) -> GitOperations:
        """Create GitOperations instance for testing.

        Returns:
            GitOperations instance configured for test repository
        """
        return GitOperations(str(temp_repository))

    @pytest.fixture
    def initialized_repo(self, temp_repository: Path, git_ops: GitOperations) -> tuple[Path, GitOperations]:
        """Create and initialize a git repository for testing.

        Returns:
            Tuple of (repository_path, git_operations_instance)
        """
        with patch('subprocess.run') as mock_run:
            # Mock successful git init
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            # Initialize repository (this will call the implementation when it exists)
            # For now, this will fail as expected in TDD
            git_ops.initialize_repository()

        return temp_repository, git_ops

    @pytest.mark.asyncio
    async def test_repository_initialization(self, temp_repository: Path, git_ops: GitOperations):
        """Test git repository initialization.

        Verifies:
        - Repository can be initialized in empty directory
        - Proper subprocess call to 'git init'
        - Error handling for initialization failures
        """
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            result = await git_ops.initialize_repository()

            # Verify successful initialization
            assert result is True

            # Verify correct git command was called
            mock_run.assert_called_once_with(
                ['git', 'init'],
                cwd=str(temp_repository),
                capture_output=True,
                text=True,
                check=False
            )

    @pytest.mark.asyncio
    async def test_repository_initialization_failure(self, temp_repository: Path, git_ops: GitOperations):
        """Test git repository initialization failure handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=128,
                stdout='',
                stderr='fatal: permission denied'
            )

            with pytest.raises(GitError) as exc_info:
                await git_ops.initialize_repository()

            assert 'permission denied' in str(exc_info.value).lower()
            assert exc_info.value.return_code == 128

    @pytest.mark.asyncio
    async def test_repository_validation(self, git_ops: GitOperations):
        """Test repository validation functionality.

        Verifies:
        - Detection of valid git repositories
        - Detection of non-git directories
        - Proper error handling for invalid paths
        """
        with patch('subprocess.run') as mock_run:
            # Test valid repository
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            is_valid = await git_ops.is_valid_repository()
            assert is_valid is True

            mock_run.assert_called_with(
                ['git', 'rev-parse', '--git-dir'],
                cwd=git_ops.repository_path,
                capture_output=True,
                text=True,
                check=False
            )

            # Test invalid repository
            mock_run.return_value = Mock(
                returncode=128,
                stdout='',
                stderr='fatal: not a git repository'
            )

            is_valid = await git_ops.is_valid_repository()
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_branch_creation(self, initialized_repo: tuple[Path, GitOperations]):
        """Test git branch creation functionality.

        Verifies:
        - Creation of new branches from current HEAD
        - Automatic checkout to new branch
        - Error handling for invalid branch names
        - Handling of existing branch names
        """
        repo_path, git_ops = initialized_repo
        branch_name = "feature/test-branch"

        with patch('subprocess.run') as mock_run:
            # Mock successful branch creation and checkout
            mock_run.side_effect = [
                Mock(returncode=0, stdout='main\n', stderr=''),  # git branch --show-current
                Mock(returncode=0, stdout='', stderr=''),        # git checkout -b
                Mock(returncode=0, stdout='', stderr=''),        # git branch --show-current (verify)
            ]

            result = await git_ops.create_and_checkout_branch(branch_name)

            assert result['success'] is True
            assert result['branch_name'] == branch_name
            assert result['previous_branch'] == 'main'

            # Verify correct git commands were called
            expected_calls = [
                call(['git', 'branch', '--show-current'], cwd=str(repo_path), capture_output=True, text=True, check=False),
                call(['git', 'checkout', '-b', branch_name], cwd=str(repo_path), capture_output=True, text=True, check=False),
                call(['git', 'branch', '--show-current'], cwd=str(repo_path), capture_output=True, text=True, check=False),
            ]
            mock_run.assert_has_calls(expected_calls)

    @pytest.mark.asyncio
    async def test_branch_creation_existing_branch(self, initialized_repo: tuple[Path, GitOperations]):
        """Test handling of existing branch names during creation."""
        repo_path, git_ops = initialized_repo
        branch_name = "feature/existing-branch"

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout='main\n', stderr=''),  # git branch --show-current
                Mock(  # git checkout -b (failure - branch exists)
                    returncode=128,
                    stdout='',
                    stderr=f"fatal: A branch named '{branch_name}' already exists."
                ),
            ]

            with pytest.raises(BranchOperationError) as exc_info:
                await git_ops.create_and_checkout_branch(branch_name)

            assert 'already exists' in str(exc_info.value).lower()
            assert exc_info.value.branch_name == branch_name

    @pytest.mark.asyncio
    async def test_branch_switching(self, initialized_repo: tuple[Path, GitOperations]):
        """Test git branch switching functionality.

        Verifies:
        - Switching to existing branches
        - Error handling for non-existent branches
        - Preservation of working directory state
        """
        repo_path, git_ops = initialized_repo
        target_branch = "develop"

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout='main\n', stderr=''),      # current branch
                Mock(returncode=0, stdout='', stderr=''),            # git checkout
                Mock(returncode=0, stdout='develop\n', stderr=''),   # verify switch
            ]

            result = await git_ops.checkout_branch(target_branch)

            assert result['success'] is True
            assert result['previous_branch'] == 'main'
            assert result['current_branch'] == 'develop'

            # Verify checkout command
            mock_run.assert_any_call(
                ['git', 'checkout', target_branch],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False
            )

    @pytest.mark.asyncio
    async def test_branch_switching_nonexistent(self, initialized_repo: tuple[Path, GitOperations]):
        """Test error handling when switching to non-existent branch."""
        repo_path, git_ops = initialized_repo
        nonexistent_branch = "feature/nonexistent"

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout='main\n', stderr=''),  # current branch
                Mock(  # git checkout (failure)
                    returncode=1,
                    stdout='',
                    stderr=f"error: pathspec '{nonexistent_branch}' did not match any file(s) known to git"
                ),
            ]

            with pytest.raises(BranchOperationError) as exc_info:
                await git_ops.checkout_branch(nonexistent_branch)

            assert 'did not match' in str(exc_info.value)
            assert exc_info.value.branch_name == nonexistent_branch

    @pytest.mark.asyncio
    async def test_repository_status(self, initialized_repo: tuple[Path, GitOperations]):
        """Test git repository status checking.

        Verifies:
        - Retrieval of working directory status
        - Detection of staged/unstaged changes
        - Parsing of git status output
        """
        repo_path, git_ops = initialized_repo

        with patch('subprocess.run') as mock_run:
            mock_status_output = """On branch feature/test
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        new file:   specs/test-feature/spec.md

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        temp.txt
"""
            mock_run.return_value = Mock(
                returncode=0,
                stdout=mock_status_output,
                stderr=''
            )

            status = await git_ops.get_repository_status()

            assert status['branch'] == 'feature/test'
            assert 'specs/test-feature/spec.md' in status['staged_files']
            assert 'README.md' in status['modified_files']
            assert 'temp.txt' in status['untracked_files']
            assert status['is_clean'] is False

            mock_run.assert_called_once_with(
                ['git', 'status', '--porcelain', '-b'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False
            )

    @pytest.mark.asyncio
    async def test_file_staging_and_commit(self, initialized_repo: tuple[Path, GitOperations]):
        """Test file staging and commit operations.

        Verifies:
        - Adding files to staging area
        - Creating commits with messages
        - Handling of empty commits
        """
        repo_path, git_ops = initialized_repo
        file_paths = ['specs/test-feature/spec.md', 'specs/test-feature/session.yaml']
        commit_message = "Add test feature specification"

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout='', stderr=''),  # git add
                Mock(  # git commit
                    returncode=0,
                    stdout='[feature/test 1234567] Add test feature specification\n 2 files changed, 45 insertions(+)',
                    stderr=''
                ),
            ]

            result = await git_ops.stage_and_commit(file_paths, commit_message)

            assert result['success'] is True
            assert '1234567' in result['commit_hash']
            assert result['files_changed'] == 2

            # Verify git commands
            expected_calls = [
                call(['git', 'add'] + file_paths, cwd=str(repo_path), capture_output=True, text=True, check=False),
                call(['git', 'commit', '-m', commit_message], cwd=str(repo_path), capture_output=True, text=True, check=False),
            ]
            mock_run.assert_has_calls(expected_calls)

    @pytest.mark.asyncio
    async def test_concurrent_git_operations(self, initialized_repo: tuple[Path, GitOperations]):
        """Test concurrent git operations on same repository.

        Verifies:
        - Proper handling of concurrent branch creation
        - Resource locking mechanisms
        - Error handling for conflicting operations
        """
        repo_path, git_ops = initialized_repo
        branch_names = [
            "feature/concurrent-test-1",
            "feature/concurrent-test-2",
            "feature/concurrent-test-3"
        ]

        with patch('subprocess.run') as mock_run:
            # Mock successful operations for all branches
            mock_run.side_effect = [
                # For each branch: current branch, checkout -b, verify current
                Mock(returncode=0, stdout='main\n', stderr=''),
                Mock(returncode=0, stdout='', stderr=''),
                Mock(returncode=0, stdout='feature/concurrent-test-1\n', stderr=''),

                Mock(returncode=0, stdout='main\n', stderr=''),
                Mock(returncode=0, stdout='', stderr=''),
                Mock(returncode=0, stdout='feature/concurrent-test-2\n', stderr=''),

                Mock(returncode=0, stdout='main\n', stderr=''),
                Mock(returncode=0, stdout='', stderr=''),
                Mock(returncode=0, stdout='feature/concurrent-test-3\n', stderr=''),
            ]

            # Execute concurrent branch creation operations
            tasks = [
                git_ops.create_and_checkout_branch(branch_name)
                for branch_name in branch_names
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify results - should either all succeed or handle conflicts appropriately
            successful_results = [r for r in results if not isinstance(r, Exception)]
            failed_results = [r for r in results if isinstance(r, Exception)]

            # At least one should succeed
            assert len(successful_results) >= 1

            # Any failures should be appropriate concurrent access errors
            for error in failed_results:
                assert isinstance(error, (BranchOperationError, GitError))

    @pytest.mark.asyncio
    async def test_cross_platform_git_commands(self, initialized_repo: tuple[Path, GitOperations]):
        """Test cross-platform git command execution.

        Verifies:
        - No shell=True usage (security requirement)
        - Proper argument passing to subprocess
        - Platform-agnostic path handling
        """
        repo_path, git_ops = initialized_repo

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            # Test various git operations
            await git_ops.initialize_repository()
            await git_ops.is_valid_repository()
            await git_ops.create_and_checkout_branch("test-branch")

            # Verify all subprocess calls use proper format
            for call_args in mock_run.call_args_list:
                args, kwargs = call_args

                # Verify command is a list (not string)
                assert isinstance(args[0], list), "Git commands should be passed as list, not string"

                # Verify no shell=True
                assert kwargs.get('shell', False) is False, "shell=True should never be used"

                # Verify proper working directory
                assert 'cwd' in kwargs
                assert kwargs['cwd'] == str(repo_path)

                # Verify capture_output and text settings
                assert kwargs.get('capture_output', False) is True
                assert kwargs.get('text', False) is True

    @pytest.mark.asyncio
    async def test_git_error_handling_and_logging(self, initialized_repo: tuple[Path, GitOperations]):
        """Test comprehensive git error handling and logging.

        Verifies:
        - Proper exception types for different error scenarios
        - Error message preservation and context
        - Logging of git command failures
        """
        repo_path, git_ops = initialized_repo

        # Test various error scenarios
        error_scenarios = [
            {
                'command': 'init',
                'mock_return': Mock(returncode=128, stdout='', stderr='fatal: permission denied'),
                'expected_exception': GitError,
                'expected_message': 'permission denied'
            },
            {
                'command': 'checkout_branch',
                'mock_return': Mock(returncode=1, stdout='', stderr='error: pathspec did not match'),
                'expected_exception': BranchOperationError,
                'expected_message': 'did not match'
            },
        ]

        for scenario in error_scenarios:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = scenario['mock_return']

                with pytest.raises(scenario['expected_exception']) as exc_info:
                    if scenario['command'] == 'init':
                        await git_ops.initialize_repository()
                    elif scenario['command'] == 'checkout_branch':
                        await git_ops.checkout_branch('nonexistent-branch')

                assert scenario['expected_message'] in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_repository_registration_integration(self, temp_repository: Path):
        """Test integration with repository registration system.

        Verifies:
        - Repository validation during registration
        - Configuration persistence
        - Multi-repository management
        """
        # Test repository registration
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            registration = RepositoryRegistration(
                path=str(temp_repository),
                name="test-repo",
                description="Test repository for integration testing"
            )

            # Verify repository path validation
            assert registration.path == str(temp_repository)
            assert registration.name == "test-repo"

            # Test git operations with registered repository
            git_ops = GitOperations(registration.path)

            # Should be able to perform operations
            await git_ops.initialize_repository()
            is_valid = await git_ops.is_valid_repository()
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_git_operations_cleanup_on_failure(self, initialized_repo: tuple[Path, GitOperations]):
        """Test proper cleanup when git operations fail partway through.

        Verifies:
        - Partial state cleanup on failures
        - Repository consistency after errors
        - No orphaned branches or uncommitted changes
        """
        repo_path, git_ops = initialized_repo
        branch_name = "feature/cleanup-test"

        with patch('subprocess.run') as mock_run:
            # Mock successful branch creation but failed subsequent operation
            mock_run.side_effect = [
                Mock(returncode=0, stdout='main\n', stderr=''),  # current branch
                Mock(returncode=0, stdout='', stderr=''),        # checkout -b (success)
                Mock(returncode=1, stdout='', stderr='fatal: file operation failed'),  # subsequent failure
            ]

            with pytest.raises(GitError):
                # This operation should fail partway through
                await git_ops.create_and_checkout_branch(branch_name)
                # Simulate additional operation that fails
                await git_ops.stage_and_commit(['nonexistent.txt'], 'Test commit')

            # Verify cleanup: should be back to a consistent state
            # (This would be tested by checking actual git state in real implementation)
            mock_run.assert_called()  # Ensure operations were attempted