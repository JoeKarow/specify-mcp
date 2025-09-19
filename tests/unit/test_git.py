"""
Unit tests for git operations module.

These tests use subprocess mocking to test git operations without requiring
actual git repositories. They verify command construction, error handling,
and cross-platform compatibility.
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

from speckit_mcp.git.operations import (
    GitOperationError,
    _run_git_command,
    is_git_repo,
    get_repo_root,
    init_repo,
    create_branch,
    checkout_branch,
    get_current_branch,
    get_status,
    add_files,
    commit
)


class TestGitOperationError:
    """Test GitOperationError exception."""

    def test_git_operation_error_init(self):
        """Test GitOperationError initialization."""
        command = ['git', 'status']
        stderr = 'fatal: not a git repository'
        error = GitOperationError("Test error", command, stderr)

        assert str(error) == "Test error"
        assert error.command == command
        assert error.stderr == stderr


class TestRunGitCommand:
    """Test _run_git_command helper function."""

    @patch('subprocess.run')
    def test_successful_command(self, mock_run):
        """Test successful git command execution."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='test output\n',
            stderr=''
        )

        success, stdout, stderr = _run_git_command(['git', 'status'])

        assert success is True
        assert stdout == 'test output'
        assert stderr == ''
        mock_run.assert_called_once_with(
            ['git', 'status'],
            cwd=None,
            capture_output=True,
            text=True,
            check=False
        )

    @patch('subprocess.run')
    def test_failed_command_with_check_false(self, mock_run):
        """Test failed git command with check=False."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout='',
            stderr='fatal: not a git repository'
        )

        success, stdout, stderr = _run_git_command(
            ['git', 'status'],
            check=False
        )

        assert success is False
        assert stdout == ''
        assert stderr == 'fatal: not a git repository'

    @patch('subprocess.run')
    def test_failed_command_with_check_true(self, mock_run):
        """Test failed git command with check=True raises exception."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout='',
            stderr='fatal: not a git repository'
        )

        with pytest.raises(GitOperationError) as exc_info:
            _run_git_command(['git', 'status'], check=True)

        error = exc_info.value
        assert "Git command failed: git status" in str(error)
        assert error.command == ['git', 'status']
        assert error.stderr == 'fatal: not a git repository'

    @patch('subprocess.run')
    def test_command_with_cwd(self, mock_run):
        """Test git command execution with working directory."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='',
            stderr=''
        )

        _run_git_command(['git', 'status'], cwd='/test/path')

        mock_run.assert_called_once_with(
            ['git', 'status'],
            cwd='/test/path',
            capture_output=True,
            text=True,
            check=False
        )

    @patch('subprocess.run')
    def test_git_not_found(self, mock_run):
        """Test FileNotFoundError when git is not installed."""
        mock_run.side_effect = FileNotFoundError("git not found")

        with pytest.raises(GitOperationError) as exc_info:
            _run_git_command(['git', 'status'])

        assert "Git is not installed" in str(exc_info.value)
        assert exc_info.value.stderr == "git command not found"

    @patch('subprocess.run')
    def test_unexpected_exception(self, mock_run):
        """Test handling of unexpected exceptions."""
        mock_run.side_effect = OSError("Permission denied")

        with pytest.raises(GitOperationError) as exc_info:
            _run_git_command(['git', 'status'])

        assert "Failed to execute git command" in str(exc_info.value)
        assert "Permission denied" in exc_info.value.stderr


class TestIsGitRepo:
    """Test is_git_repo function."""

    @patch('speckit_mcp.git.operations._run_git_command')
    def test_is_git_repo_true(self, mock_run):
        """Test is_git_repo returns True for valid repository."""
        mock_run.return_value = (True, '.git', '')

        result = is_git_repo('/test/repo')

        assert result is True
        mock_run.assert_called_once_with(
            ['git', 'rev-parse', '--git-dir'],
            cwd='/test/repo',
            check=False
        )

    @patch('speckit_mcp.git.operations._run_git_command')
    def test_is_git_repo_false(self, mock_run):
        """Test is_git_repo returns False for non-repository."""
        mock_run.return_value = (False, '', 'fatal: not a git repository')

        result = is_git_repo('/test/notrepo')

        assert result is False


class TestGetRepoRoot:
    """Test get_repo_root function."""

    @patch('speckit_mcp.git.operations._run_git_command')
    def test_get_repo_root_success(self, mock_run):
        """Test successful repo root retrieval."""
        mock_run.return_value = (True, '/abs/path/to/repo', '')

        result = get_repo_root('/abs/path/to/repo/subdir')

        assert result == str(Path('/abs/path/to/repo').resolve())
        mock_run.assert_called_once_with(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd='/abs/path/to/repo/subdir',
            check=False
        )

    @patch('speckit_mcp.git.operations._run_git_command')
    def test_get_repo_root_not_repo(self, mock_run):
        """Test get_repo_root returns None for non-repository."""
        mock_run.return_value = (False, '', 'fatal: not a git repository')

        result = get_repo_root('/test/notrepo')

        assert result is None

    @patch('speckit_mcp.git.operations._run_git_command')
    def test_get_repo_root_empty_output(self, mock_run):
        """Test get_repo_root with empty stdout."""
        mock_run.return_value = (True, '', '')

        result = get_repo_root('/test/path')

        assert result is None


class TestInitRepo:
    """Test init_repo function."""

    @patch('speckit_mcp.git.operations._run_git_command')
    @patch('pathlib.Path.mkdir')
    def test_init_repo_success(self, mock_mkdir, mock_run):
        """Test successful repository initialization."""
        mock_run.return_value = (True, 'Initialized empty Git repository', '')

        result = init_repo('/test/new_repo')

        # Verify directory creation
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify git init command
        mock_run.assert_called_once_with(
            ['git', 'init'],
            cwd=str(Path('/test/new_repo')),
            check=True
        )

        assert result['success'] is True
        assert 'repository_path' in result
        assert result['message'] == 'Initialized empty Git repository'

    @patch('speckit_mcp.git.operations._run_git_command')
    @patch('pathlib.Path.mkdir')
    def test_init_repo_failure(self, mock_mkdir, mock_run):
        """Test repository initialization failure."""
        mock_run.side_effect = GitOperationError(
            "Permission denied",
            ['git', 'init'],
            'permission denied'
        )

        with pytest.raises(GitOperationError):
            init_repo('/test/new_repo')


class TestCreateBranch:
    """Test create_branch function."""

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_create_branch_success_with_commits(self, mock_run, mock_is_git):
        """Test successful branch creation in repository with commits."""
        mock_is_git.return_value = True
        mock_run.side_effect = [
            # Check for commits
            (True, 'abc123', ''),
            # Check branch doesn't exist
            (True, '', ''),
            # Create and checkout branch
            (True, "Switched to a new branch 'feature-test'", '')
        ]

        result = create_branch('/test/repo', 'feature-test')

        assert result['success'] is True
        assert result['branch_name'] == 'feature-test'
        assert 'Created and switched to branch' in result['message']

        # Verify commands called
        expected_calls = [
            call(['git', 'rev-list', '-n', '1', '--all'], cwd='/test/repo', check=False),
            call(['git', 'branch', '--list', 'feature-test'], cwd='/test/repo', check=False),
            call(['git', 'checkout', '-b', 'feature-test'], cwd='/test/repo', check=True)
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_create_branch_success_empty_repo(self, mock_run, mock_is_git):
        """Test successful branch creation in empty repository."""
        mock_is_git.return_value = True
        mock_run.side_effect = [
            # No commits
            (False, '', 'fatal: your current branch does not have any commits yet'),
            # Create and checkout branch
            (True, "Switched to a new branch 'main'", '')
        ]

        result = create_branch('/test/repo', 'main')

        assert result['success'] is True
        assert result['branch_name'] == 'main'

    @patch('speckit_mcp.git.operations.is_git_repo')
    def test_create_branch_not_git_repo(self, mock_is_git):
        """Test create_branch raises error for non-git directory."""
        mock_is_git.return_value = False

        with pytest.raises(GitOperationError) as exc_info:
            create_branch('/test/notrepo', 'feature-test')

        assert "Not a git repository" in str(exc_info.value)

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_create_branch_already_exists(self, mock_run, mock_is_git):
        """Test create_branch raises error when branch already exists."""
        mock_is_git.return_value = True
        mock_run.side_effect = [
            # Check for commits
            (True, 'abc123', ''),
            # Branch exists
            (True, '  feature-test', '')
        ]

        with pytest.raises(GitOperationError) as exc_info:
            create_branch('/test/repo', 'feature-test')

        assert "Branch already exists" in str(exc_info.value)

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_create_branch_with_source_branch(self, mock_run, mock_is_git):
        """Test create_branch with source branch specification."""
        mock_is_git.return_value = True
        mock_run.side_effect = [
            # Check for commits
            (True, 'abc123', ''),
            # Check branch doesn't exist
            (True, '', ''),
            # Create and checkout branch from source
            (True, "Switched to a new branch 'feature-test'", '')
        ]

        create_branch('/test/repo', 'feature-test', 'develop')

        # Should include source branch in checkout command
        expected_final_call = call(
            ['git', 'checkout', '-b', 'feature-test', 'develop'],
            cwd='/test/repo',
            check=True
        )
        assert expected_final_call in mock_run.call_args_list


class TestCheckoutBranch:
    """Test checkout_branch function."""

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_checkout_branch_success(self, mock_run, mock_is_git):
        """Test successful branch checkout."""
        mock_is_git.return_value = True
        mock_run.return_value = (True, "Switched to branch 'main'", '')

        result = checkout_branch('/test/repo', 'main')

        assert result['success'] is True
        assert result['branch_name'] == 'main'
        assert "Switched to branch 'main'" in result['message']

        mock_run.assert_called_once_with(
            ['git', 'checkout', 'main'],
            cwd='/test/repo',
            check=True
        )

    @patch('speckit_mcp.git.operations.is_git_repo')
    def test_checkout_branch_not_git_repo(self, mock_is_git):
        """Test checkout_branch raises error for non-git directory."""
        mock_is_git.return_value = False

        with pytest.raises(GitOperationError) as exc_info:
            checkout_branch('/test/notrepo', 'main')

        assert "Not a git repository" in str(exc_info.value)


class TestGetCurrentBranch:
    """Test get_current_branch function."""

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_get_current_branch_success(self, mock_run, mock_is_git):
        """Test successful current branch retrieval."""
        mock_is_git.return_value = True
        mock_run.return_value = (True, 'main', '')

        result = get_current_branch('/test/repo')

        assert result == 'main'
        mock_run.assert_called_once_with(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd='/test/repo',
            check=False
        )

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_get_current_branch_detached_head(self, mock_run, mock_is_git):
        """Test get_current_branch with detached HEAD."""
        mock_is_git.return_value = True
        mock_run.side_effect = [
            # First call returns HEAD (detached)
            (True, 'HEAD', ''),
            # Second call with symbolic-ref
            (True, 'feature-branch', '')
        ]

        result = get_current_branch('/test/repo')

        assert result == 'feature-branch'

        expected_calls = [
            call(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd='/test/repo', check=False),
            call(['git', 'symbolic-ref', '--short', 'HEAD'], cwd='/test/repo', check=False)
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch('speckit_mcp.git.operations.is_git_repo')
    def test_get_current_branch_not_git_repo(self, mock_is_git):
        """Test get_current_branch returns None for non-git directory."""
        mock_is_git.return_value = False

        result = get_current_branch('/test/notrepo')

        assert result is None

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_get_current_branch_no_branch(self, mock_run, mock_is_git):
        """Test get_current_branch when no branch is available."""
        mock_is_git.return_value = True
        mock_run.side_effect = [
            (True, 'HEAD', ''),
            (False, '', 'fatal: ref HEAD is not a symbolic ref')
        ]

        result = get_current_branch('/test/repo')

        assert result is None


class TestGetStatus:
    """Test get_status function."""

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations.get_current_branch')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_get_status_clean_repo(self, mock_run, mock_branch, mock_is_git):
        """Test get_status for clean repository."""
        mock_is_git.return_value = True
        mock_branch.return_value = 'main'
        mock_run.return_value = (True, '', '')

        result = get_status('/test/repo')

        assert result['success'] is True
        assert result['current_branch'] == 'main'
        assert result['clean'] is True
        assert result['staged_files'] == []
        assert result['modified_files'] == []
        assert result['untracked_files'] == []

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations.get_current_branch')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_get_status_with_changes(self, mock_run, mock_branch, mock_is_git):
        """Test get_status with various file changes."""
        mock_is_git.return_value = True
        mock_branch.return_value = 'feature'
        mock_run.return_value = (True, 'M  staged_file.py\n M modified_file.py\n?? untracked_file.py', '')

        result = get_status('/test/repo')

        assert result['success'] is True
        assert result['current_branch'] == 'feature'
        assert result['clean'] is False
        assert 'staged_file.py' in result['staged_files']
        assert 'modified_file.py' in result['modified_files']
        assert 'untracked_file.py' in result['untracked_files']

    @patch('speckit_mcp.git.operations.is_git_repo')
    def test_get_status_not_git_repo(self, mock_is_git):
        """Test get_status raises error for non-git directory."""
        mock_is_git.return_value = False

        with pytest.raises(GitOperationError) as exc_info:
            get_status('/test/notrepo')

        assert "Not a git repository" in str(exc_info.value)


class TestAddFiles:
    """Test add_files function."""

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_add_files_success(self, mock_run, mock_is_git):
        """Test successful file addition."""
        mock_is_git.return_value = True
        mock_run.return_value = (True, '', '')

        files = ['file1.py', 'file2.py']
        result = add_files('/test/repo', files)

        assert result['success'] is True
        assert result['files_added'] == files
        assert 'Added 2 file(s)' in result['message']

        mock_run.assert_called_once_with(
            ['git', 'add', 'file1.py', 'file2.py'],
            cwd='/test/repo',
            check=True
        )

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_add_files_with_force(self, mock_run, mock_is_git):
        """Test add_files with force flag."""
        mock_is_git.return_value = True
        mock_run.return_value = (True, '', '')

        files = ['ignored_file.py']
        add_files('/test/repo', files, force=True)

        mock_run.assert_called_once_with(
            ['git', 'add', '--force', 'ignored_file.py'],
            cwd='/test/repo',
            check=True
        )

    @patch('speckit_mcp.git.operations.is_git_repo')
    def test_add_files_not_git_repo(self, mock_is_git):
        """Test add_files raises error for non-git directory."""
        mock_is_git.return_value = False

        with pytest.raises(GitOperationError) as exc_info:
            add_files('/test/notrepo', ['file.py'])

        assert "Not a git repository" in str(exc_info.value)

    @patch('speckit_mcp.git.operations.is_git_repo')
    def test_add_files_empty_list(self, mock_is_git):
        """Test add_files raises error for empty file list."""
        mock_is_git.return_value = True

        with pytest.raises(GitOperationError) as exc_info:
            add_files('/test/repo', [])

        assert "No files specified to add" in str(exc_info.value)


class TestCommit:
    """Test commit function."""

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations.get_status')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_commit_success(self, mock_run, mock_status, mock_is_git):
        """Test successful commit creation."""
        mock_is_git.return_value = True
        mock_status.return_value = {'staged_files': ['file.py']}
        mock_run.side_effect = [
            # Commit command
            (True, '[main abc123] Test commit', ''),
            # Get commit hash
            (True, 'abc123456789', '')
        ]

        result = commit('/test/repo', 'Test commit message')

        assert result['success'] is True
        assert result['commit_hash'] == 'abc123456789'
        assert 'Created commit' in result['message']

        expected_calls = [
            call(['git', 'commit', '-m', 'Test commit message'], cwd='/test/repo', check=True),
            call(['git', 'rev-parse', 'HEAD'], cwd='/test/repo', check=False)
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations.get_status')
    @patch('speckit_mcp.git.operations._run_git_command')
    def test_commit_with_author(self, mock_run, mock_status, mock_is_git):
        """Test commit with author specification."""
        mock_is_git.return_value = True
        mock_status.return_value = {'staged_files': ['file.py']}
        mock_run.side_effect = [
            (True, '[main abc123] Test commit', ''),
            (True, 'abc123456789', '')
        ]

        commit('/test/repo', 'Test commit', 'John Doe', 'john@example.com')

        expected_commit_call = call(
            ['git', 'commit', '-m', 'Test commit', '--author', 'John Doe <john@example.com>'],
            cwd='/test/repo',
            check=True
        )
        assert expected_commit_call in mock_run.call_args_list

    @patch('speckit_mcp.git.operations.is_git_repo')
    @patch('speckit_mcp.git.operations.get_status')
    def test_commit_no_staged_files(self, mock_status, mock_is_git):
        """Test commit when no files are staged."""
        mock_is_git.return_value = True
        mock_status.return_value = {'staged_files': []}

        result = commit('/test/repo', 'Test commit')

        assert result['success'] is False
        assert 'No changes staged' in result['message']

    @patch('speckit_mcp.git.operations.is_git_repo')
    def test_commit_not_git_repo(self, mock_is_git):
        """Test commit raises error for non-git directory."""
        mock_is_git.return_value = False

        with pytest.raises(GitOperationError) as exc_info:
            commit('/test/notrepo', 'Test commit')

        assert "Not a git repository" in str(exc_info.value)

    @patch('speckit_mcp.git.operations.is_git_repo')
    def test_commit_empty_message(self, mock_is_git):
        """Test commit raises error for empty message."""
        mock_is_git.return_value = True

        with pytest.raises(GitOperationError) as exc_info:
            commit('/test/repo', '')

        assert "Commit message cannot be empty" in str(exc_info.value)


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility aspects."""

    @patch('subprocess.run')
    def test_no_shell_usage(self, mock_run):
        """Test that git commands never use shell=True."""
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

        _run_git_command(['git', 'status'])

        # Verify shell is never used
        call_kwargs = mock_run.call_args[1]
        assert 'shell' not in call_kwargs or call_kwargs['shell'] is False

    @patch('subprocess.run')
    def test_text_mode_enabled(self, mock_run):
        """Test that text mode is always enabled for cross-platform compatibility."""
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

        _run_git_command(['git', 'status'])

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['text'] is True

    @patch('pathlib.Path.mkdir')
    def test_path_handling(self, mock_mkdir):
        """Test that Path objects are handled correctly across platforms."""
        from unittest.mock import patch

        with patch('speckit_mcp.git.operations._run_git_command') as mock_run:
            mock_run.return_value = (True, '', '')

            # Test with string path
            init_repo('/test/repo')

            # Verify Path.resolve() is used for cross-platform compatibility
            call_args = mock_run.call_args[1]
            assert 'cwd' in call_args
            # Verify mkdir was called for directory creation
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)