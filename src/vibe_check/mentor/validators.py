"""
Security validators for file path and access control.

Provides path validation, security checks, and workspace management.
"""

import os
import re
import logging
from pathlib import Path
from typing import Tuple, Optional

from .constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Validates file paths for security"""

    @staticmethod
    def get_workspace_directory() -> Optional[str]:
        """
        Get the configured workspace directory from environment variable.

        Returns:
            Workspace directory path or None if not configured
        """
        workspace = os.environ.get("WORKSPACE")
        if workspace:
            workspace_path = Path(workspace).resolve()
            if workspace_path.exists() and workspace_path.is_dir():
                logger.info(f"Using configured WORKSPACE: {workspace_path}")
                return str(workspace_path)
            else:
                logger.warning(
                    f"WORKSPACE environment variable points to invalid directory: {workspace}"
                )
        return None

    @staticmethod
    def validate_path(
        file_path: str, working_directory: str | None = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a file path for security issues.
        Uses WORKSPACE environment variable if set, otherwise uses provided working_directory.

        Returns:
            Tuple of (is_valid, resolved_path, error_message)
        """
        try:
            # Prefer WORKSPACE environment variable over provided working_directory
            workspace = SecurityValidator.get_workspace_directory()
            if workspace:
                working_directory = workspace

            # Handle explicit Windows drive references on non-Windows systems
            if os.name != "nt" and re.match(r"^[a-zA-Z]:\\", file_path):
                return (
                    False,
                    file_path,
                    "File is outside working directory",
                )

            # Convert to Path object
            path = Path(file_path).expanduser()

            # If relative, make it relative to working directory
            if not path.is_absolute():
                if working_directory:
                    base_dir = Path(working_directory).resolve()
                    path = (base_dir / path).resolve()
                else:
                    path = path.resolve()
            else:
                path = path.resolve()

            # Prevent path traversal - ensure file is within working directory if specified
            if working_directory:
                base_dir = Path(working_directory).resolve()
                try:
                    # Check if the resolved path is within the base directory
                    path.relative_to(base_dir)
                except ValueError:
                    # If specified, file must be within working directory
                    return (
                        False,
                        str(path),
                        f"File is outside working directory: {path}",
                    )

            # Check if file exists
            if not path.exists():
                return False, str(path), f"File does not exist: {path}"

            # Check if it's a file (not directory)
            if not path.is_file():
                return False, str(path), f"Path is not a file: {path}"

            # Check file extension
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                return False, str(path), f"File type not allowed: {path.suffix}"

            # Check file size
            file_size = path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                return (
                    False,
                    str(path),
                    f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})",
                )

            return True, str(path), None

        except Exception as e:
            return False, str(file_path), f"Error validating path: {str(e)}"
