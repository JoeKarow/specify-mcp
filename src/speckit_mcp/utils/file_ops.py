"""
File operations utilities for the SpecKit MCP server.

This module provides safe file I/O operations with path validation
to ensure operations stay within repository boundaries.
"""

import os
from pathlib import Path
from typing import Optional, Union


class FileOperationError(Exception):
    """Exception raised when file operations fail."""
    pass


def validate_path(
    file_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    must_exist: bool = False
) -> Path:
    """
    Validate that a file path is safe and within bounds.

    Args:
        file_path: Path to validate
        base_path: Optional base path to ensure file_path is within
        must_exist: Whether the path must already exist

    Returns:
        Validated absolute Path object

    Raises:
        FileOperationError: If path is invalid or outside bounds
    """
    # Convert to Path object
    path = Path(file_path)

    # Resolve to absolute path (follows symlinks)
    try:
        if path.exists():
            path = path.resolve()
        else:
            # For non-existent paths, resolve the parent and join the name
            path = path.parent.resolve() / path.name
    except (OSError, RuntimeError) as e:
        raise FileOperationError(f"Invalid path: {e}")

    # Check if path must exist
    if must_exist and not path.exists():
        raise FileOperationError(f"Path does not exist: {path}")

    # Validate against base path if provided
    if base_path:
        base = Path(base_path).resolve()

        # Ensure path is within base_path
        try:
            path.relative_to(base)
        except ValueError:
            raise FileOperationError(
                f"Path '{path}' is outside of base directory '{base}'"
            )

    # Check for dangerous path components
    path_str = str(path)
    if '..' in path.parts:
        raise FileOperationError(
            f"Path contains parent directory references: {path_str}"
        )

    return path


def safe_read(
    file_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    encoding: str = 'utf-8',
    default: Optional[str] = None
) -> str:
    """
    Safely read a file with path validation.

    Args:
        file_path: Path to file to read
        base_path: Optional base path for validation
        encoding: File encoding (default: utf-8)
        default: Default value if file doesn't exist

    Returns:
        File contents as string

    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        # Validate path
        path = validate_path(file_path, base_path, must_exist=(default is None))

        if not path.exists():
            if default is not None:
                return default
            raise FileOperationError(f"File not found: {path}")

        if not path.is_file():
            raise FileOperationError(f"Path is not a file: {path}")

        # Read file
        with open(path, 'r', encoding=encoding) as f:
            return f.read()

    except UnicodeDecodeError as e:
        raise FileOperationError(f"Could not decode file with {encoding}: {e}")
    except IOError as e:
        raise FileOperationError(f"Could not read file: {e}")


def safe_write(
    file_path: Union[str, Path],
    content: str,
    base_path: Optional[Union[str, Path]] = None,
    encoding: str = 'utf-8',
    create_parents: bool = True,
    overwrite: bool = True
) -> Path:
    """
    Safely write content to a file with path validation.

    Args:
        file_path: Path to file to write
        content: Content to write
        base_path: Optional base path for validation
        encoding: File encoding (default: utf-8)
        create_parents: Whether to create parent directories
        overwrite: Whether to overwrite existing files

    Returns:
        Path to written file

    Raises:
        FileOperationError: If file cannot be written
    """
    try:
        # Validate path
        path = validate_path(file_path, base_path, must_exist=False)

        # Check if file exists and overwrite is False
        if path.exists() and not overwrite:
            raise FileOperationError(
                f"File already exists and overwrite=False: {path}"
            )

        # Create parent directories if needed
        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)
        elif not path.parent.exists():
            raise FileOperationError(
                f"Parent directory does not exist: {path.parent}"
            )

        # Write file
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)

        return path

    except UnicodeEncodeError as e:
        raise FileOperationError(f"Could not encode content with {encoding}: {e}")
    except IOError as e:
        raise FileOperationError(f"Could not write file: {e}")


def ensure_directory(
    dir_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    mode: int = 0o755
) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to directory
        base_path: Optional base path for validation
        mode: Directory permissions (default: 0o755)

    Returns:
        Path to directory

    Raises:
        FileOperationError: If directory cannot be created
    """
    try:
        # Validate path
        path = validate_path(dir_path, base_path, must_exist=False)

        if path.exists():
            if not path.is_dir():
                raise FileOperationError(f"Path exists but is not a directory: {path}")
        else:
            # Create directory with parents
            path.mkdir(parents=True, exist_ok=True, mode=mode)

        return path

    except OSError as e:
        raise FileOperationError(f"Could not create directory: {e}")


def get_relative_path(
    file_path: Union[str, Path],
    base_path: Union[str, Path]
) -> Path:
    """
    Get the relative path from base_path to file_path.

    Args:
        file_path: Target file path
        base_path: Base path to calculate relative from

    Returns:
        Relative Path object

    Raises:
        FileOperationError: If relative path cannot be determined
    """
    try:
        file_p = Path(file_path).resolve()
        base_p = Path(base_path).resolve()

        return file_p.relative_to(base_p)

    except ValueError as e:
        raise FileOperationError(
            f"Cannot get relative path from '{base_path}' to '{file_path}': {e}"
        )


def safe_delete(
    file_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    must_exist: bool = True
) -> bool:
    """
    Safely delete a file with path validation.

    Args:
        file_path: Path to file to delete
        base_path: Optional base path for validation
        must_exist: Whether to raise error if file doesn't exist

    Returns:
        True if file was deleted, False if it didn't exist

    Raises:
        FileOperationError: If file cannot be deleted
    """
    try:
        # Validate path
        path = validate_path(file_path, base_path, must_exist=False)

        if not path.exists():
            if must_exist:
                raise FileOperationError(f"File not found: {path}")
            return False

        if path.is_dir():
            raise FileOperationError(
                f"Path is a directory, use safe_delete_directory: {path}"
            )

        # Delete the file
        path.unlink()
        return True

    except OSError as e:
        raise FileOperationError(f"Could not delete file: {e}")


def safe_delete_directory(
    dir_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    recursive: bool = False,
    must_exist: bool = True
) -> bool:
    """
    Safely delete a directory with path validation.

    Args:
        dir_path: Path to directory to delete
        base_path: Optional base path for validation
        recursive: Whether to delete non-empty directories
        must_exist: Whether to raise error if directory doesn't exist

    Returns:
        True if directory was deleted, False if it didn't exist

    Raises:
        FileOperationError: If directory cannot be deleted
    """
    try:
        # Validate path
        path = validate_path(dir_path, base_path, must_exist=False)

        if not path.exists():
            if must_exist:
                raise FileOperationError(f"Directory not found: {path}")
            return False

        if not path.is_dir():
            raise FileOperationError(f"Path is not a directory: {path}")

        if recursive:
            # Recursively delete directory and contents
            import shutil
            shutil.rmtree(path)
        else:
            # Only delete if empty
            path.rmdir()

        return True

    except OSError as e:
        if not recursive and "not empty" in str(e).lower():
            raise FileOperationError(
                f"Directory not empty (use recursive=True): {path}"
            )
        raise FileOperationError(f"Could not delete directory: {e}")


def copy_file(
    source_path: Union[str, Path],
    dest_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    overwrite: bool = False
) -> Path:
    """
    Safely copy a file with path validation.

    Args:
        source_path: Source file path
        dest_path: Destination file path
        base_path: Optional base path for validation
        overwrite: Whether to overwrite existing destination

    Returns:
        Path to copied file

    Raises:
        FileOperationError: If file cannot be copied
    """
    try:
        # Validate paths
        source = validate_path(source_path, base_path, must_exist=True)
        dest = validate_path(dest_path, base_path, must_exist=False)

        if not source.is_file():
            raise FileOperationError(f"Source is not a file: {source}")

        if dest.exists() and not overwrite:
            raise FileOperationError(
                f"Destination already exists and overwrite=False: {dest}"
            )

        # Ensure destination directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        import shutil
        shutil.copy2(source, dest)

        return dest

    except IOError as e:
        raise FileOperationError(f"Could not copy file: {e}")


def list_files(
    dir_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    pattern: str = "*",
    recursive: bool = False
) -> list[Path]:
    """
    Safely list files in a directory with pattern matching.

    Args:
        dir_path: Directory to list files from
        base_path: Optional base path for validation
        pattern: Glob pattern for filtering (default: "*")
        recursive: Whether to search recursively

    Returns:
        List of Path objects matching the pattern

    Raises:
        FileOperationError: If directory cannot be listed
    """
    try:
        # Validate path
        path = validate_path(dir_path, base_path, must_exist=True)

        if not path.is_dir():
            raise FileOperationError(f"Path is not a directory: {path}")

        # List files
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        # Filter to only files (not directories)
        return [f for f in files if f.is_file()]

    except OSError as e:
        raise FileOperationError(f"Could not list files: {e}")


def get_file_info(
    file_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None
) -> dict:
    """
    Get information about a file.

    Args:
        file_path: Path to file
        base_path: Optional base path for validation

    Returns:
        Dictionary with file information

    Raises:
        FileOperationError: If file information cannot be retrieved
    """
    try:
        # Validate path
        path = validate_path(file_path, base_path, must_exist=True)

        stat = path.stat()

        return {
            'path': str(path),
            'name': path.name,
            'size': stat.st_size,
            'is_file': path.is_file(),
            'is_dir': path.is_dir(),
            'is_symlink': path.is_symlink(),
            'modified_time': stat.st_mtime,
            'created_time': stat.st_ctime,
            'permissions': oct(stat.st_mode)[-3:]
        }

    except OSError as e:
        raise FileOperationError(f"Could not get file info: {e}")