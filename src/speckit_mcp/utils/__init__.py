"""Utility functions for file operations and common tasks."""

from .file_ops import (
    FileOperationError,
    validate_path,
    safe_read,
    safe_write,
    ensure_directory,
    get_relative_path,
    safe_delete,
    safe_delete_directory,
    copy_file,
    list_files,
    get_file_info
)

__all__ = [
    'FileOperationError',
    'validate_path',
    'safe_read',
    'safe_write',
    'ensure_directory',
    'get_relative_path',
    'safe_delete',
    'safe_delete_directory',
    'copy_file',
    'list_files',
    'get_file_info'
]
