"""
Git operations module for the SpecKit MCP server.

This module provides cross-platform git operations using subprocess.run()
without shell dependencies. All operations return structured results and
handle errors gracefully.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GitOperationError(Exception):
    """Exception raised when a git operation fails."""

    def __init__(self, message: str, command: List[str], stderr: str = ""):
        """
        Initialize GitOperationError.

        Args:
            message: Human-readable error message
            command: The git command that failed
            stderr: Standard error output from git
        """
        super().__init__(message)
        self.command = command
        self.stderr = stderr


def _run_git_command(
    command: List[str],
    cwd: Optional[str] = None,
    check: bool = True
) -> Tuple[bool, str, str]:
    """
    Run a git command using subprocess.

    Args:
        command: Git command as list (e.g., ['git', 'status'])
        cwd: Working directory for command execution
        check: Whether to raise exception on non-zero exit

    Returns:
        Tuple of (success, stdout, stderr)

    Raises:
        GitOperationError: If command fails and check=True
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False  # We handle errors explicitly
        )

        success = result.returncode == 0

        if not success and check:
            raise GitOperationError(
                f"Git command failed: {' '.join(command)}",
                command,
                result.stderr
            )

        return success, result.stdout.strip(), result.stderr.strip()

    except FileNotFoundError:
        raise GitOperationError(
            "Git is not installed or not in PATH",
            command,
            "git command not found"
        )
    except GitOperationError:
        # Re-raise GitOperationError without modification
        raise
    except Exception as e:
        raise GitOperationError(
            f"Failed to execute git command: {e}",
            command,
            str(e)
        )


def is_git_repo(path: str) -> bool:
    """
    Check if a directory is a git repository.

    Args:
        path: Directory path to check

    Returns:
        True if path is within a git repository
    """
    success, _, _ = _run_git_command(
        ['git', 'rev-parse', '--git-dir'],
        cwd=path,
        check=False
    )
    return success


def get_repo_root(path: str) -> Optional[str]:
    """
    Get the root directory of the git repository.

    Args:
        path: Path within the repository

    Returns:
        Absolute path to repository root, or None if not a git repo
    """
    success, stdout, _ = _run_git_command(
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=path,
        check=False
    )

    if success and stdout:
        return str(Path(stdout).resolve())
    return None


def init_repo(path: str) -> Dict[str, any]:
    """
    Initialize a new git repository.

    Args:
        path: Directory to initialize as git repository

    Returns:
        Dictionary with operation results

    Raises:
        GitOperationError: If initialization fails
    """
    # Ensure directory exists
    repo_path = Path(path)
    repo_path.mkdir(parents=True, exist_ok=True)

    success, stdout, stderr = _run_git_command(
        ['git', 'init'],
        cwd=str(repo_path),
        check=True
    )

    return {
        'success': success,
        'repository_path': str(repo_path.resolve()),
        'message': stdout or "Initialized empty Git repository"
    }


def create_branch(
    repository_path: str,
    branch_name: str,
    from_branch: Optional[str] = None
) -> Dict[str, any]:
    """
    Create a new git branch.

    Args:
        repository_path: Path to git repository
        branch_name: Name of the new branch
        from_branch: Optional source branch (defaults to current branch)

    Returns:
        Dictionary with operation results

    Raises:
        GitOperationError: If branch creation fails
    """
    if not is_git_repo(repository_path):
        raise GitOperationError(
            f"Not a git repository: {repository_path}",
            ['git'],
            "Directory is not a git repository"
        )

    # Check if repository has any commits
    success, stdout, _ = _run_git_command(
        ['git', 'rev-list', '-n', '1', '--all'],
        cwd=repository_path,
        check=False
    )

    has_commits = success and stdout.strip()

    if has_commits:
        # Check if branch already exists
        success, stdout, _ = _run_git_command(
            ['git', 'branch', '--list', branch_name],
            cwd=repository_path,
            check=False
        )

        if success and stdout:
            raise GitOperationError(
                f"Branch already exists: {branch_name}",
                ['git', 'branch'],
                f"Branch '{branch_name}' already exists"
            )

        # Create and checkout the new branch
        command = ['git', 'checkout', '-b', branch_name]
        if from_branch:
            command.append(from_branch)
    else:
        # For empty repo, just checkout -b will work
        command = ['git', 'checkout', '-b', branch_name]

    success, stdout, stderr = _run_git_command(
        command,
        cwd=repository_path,
        check=True
    )

    return {
        'success': success,
        'branch_name': branch_name,
        'message': f"Created and switched to branch '{branch_name}'"
    }


def checkout_branch(repository_path: str, branch_name: str) -> Dict[str, any]:
    """
    Checkout an existing git branch.

    Args:
        repository_path: Path to git repository
        branch_name: Name of the branch to checkout

    Returns:
        Dictionary with operation results

    Raises:
        GitOperationError: If checkout fails
    """
    if not is_git_repo(repository_path):
        raise GitOperationError(
            f"Not a git repository: {repository_path}",
            ['git'],
            "Directory is not a git repository"
        )

    success, stdout, stderr = _run_git_command(
        ['git', 'checkout', branch_name],
        cwd=repository_path,
        check=True
    )

    return {
        'success': success,
        'branch_name': branch_name,
        'message': f"Switched to branch '{branch_name}'"
    }


def get_current_branch(repository_path: str) -> Optional[str]:
    """
    Get the name of the current git branch.

    Args:
        repository_path: Path to git repository

    Returns:
        Current branch name, or None if not on a branch
    """
    if not is_git_repo(repository_path):
        return None

    # Try to get current branch
    success, stdout, _ = _run_git_command(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        cwd=repository_path,
        check=False
    )

    if success and stdout and stdout != 'HEAD':
        return stdout

    # If HEAD, try to get branch from symbolic-ref
    success, stdout, _ = _run_git_command(
        ['git', 'symbolic-ref', '--short', 'HEAD'],
        cwd=repository_path,
        check=False
    )

    if success and stdout:
        return stdout

    return None


def get_status(repository_path: str) -> Dict[str, any]:
    """
    Get git repository status.

    Args:
        repository_path: Path to git repository

    Returns:
        Dictionary with status information

    Raises:
        GitOperationError: If status check fails
    """
    if not is_git_repo(repository_path):
        raise GitOperationError(
            f"Not a git repository: {repository_path}",
            ['git'],
            "Directory is not a git repository"
        )

    # Get branch info
    current_branch = get_current_branch(repository_path)

    # Get status
    success, stdout, stderr = _run_git_command(
        ['git', 'status', '--porcelain'],
        cwd=repository_path,
        check=True
    )

    # Parse status output
    modified_files = []
    untracked_files = []
    staged_files = []

    if stdout:
        for line in stdout.split('\n'):
            if line:
                status_code = line[:2]
                file_path = line[3:]

                if status_code[0] in ['M', 'A', 'D', 'R']:
                    staged_files.append(file_path)
                if status_code[1] == 'M':
                    modified_files.append(file_path)
                if status_code == '??':
                    untracked_files.append(file_path)

    # Check if working directory is clean
    clean = not (modified_files or untracked_files or staged_files)

    return {
        'success': True,
        'current_branch': current_branch,
        'clean': clean,
        'staged_files': staged_files,
        'modified_files': modified_files,
        'untracked_files': untracked_files
    }


def add_files(
    repository_path: str,
    file_paths: List[str],
    force: bool = False
) -> Dict[str, any]:
    """
    Add files to git staging area.

    Args:
        repository_path: Path to git repository
        file_paths: List of file paths to add (relative to repo root)
        force: Whether to force add ignored files

    Returns:
        Dictionary with operation results

    Raises:
        GitOperationError: If adding files fails
    """
    if not is_git_repo(repository_path):
        raise GitOperationError(
            f"Not a git repository: {repository_path}",
            ['git'],
            "Directory is not a git repository"
        )

    if not file_paths:
        raise GitOperationError(
            "No files specified to add",
            ['git', 'add'],
            "file_paths list is empty"
        )

    # Build command
    command = ['git', 'add']
    if force:
        command.append('--force')
    command.extend(file_paths)

    success, stdout, stderr = _run_git_command(
        command,
        cwd=repository_path,
        check=True
    )

    return {
        'success': success,
        'files_added': file_paths,
        'message': f"Added {len(file_paths)} file(s) to staging area"
    }


def commit(
    repository_path: str,
    message: str,
    author: Optional[str] = None,
    email: Optional[str] = None
) -> Dict[str, any]:
    """
    Create a git commit.

    Args:
        repository_path: Path to git repository
        message: Commit message
        author: Optional author name
        email: Optional author email

    Returns:
        Dictionary with operation results

    Raises:
        GitOperationError: If commit fails
    """
    if not is_git_repo(repository_path):
        raise GitOperationError(
            f"Not a git repository: {repository_path}",
            ['git'],
            "Directory is not a git repository"
        )

    if not message:
        raise GitOperationError(
            "Commit message cannot be empty",
            ['git', 'commit'],
            "Empty commit message"
        )

    # Check if there are changes to commit
    status = get_status(repository_path)
    if not status['staged_files']:
        return {
            'success': False,
            'message': "No changes staged for commit"
        }

    # Build command
    command = ['git', 'commit', '-m', message]

    if author and email:
        command.extend(['--author', f'{author} <{email}>'])

    success, stdout, stderr = _run_git_command(
        command,
        cwd=repository_path,
        check=True
    )

    # Get commit hash
    hash_success, commit_hash, _ = _run_git_command(
        ['git', 'rev-parse', 'HEAD'],
        cwd=repository_path,
        check=False
    )

    return {
        'success': success,
        'commit_hash': commit_hash if hash_success else None,
        'message': f"Created commit: {message[:50]}..."
    }