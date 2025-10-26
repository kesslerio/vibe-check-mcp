"""
Secure file reading with validation and encoding detection.

Provides safe file reading with support for multiple encodings
and line length limits.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional

from .validators import SecurityValidator
from .constants import MAX_LINE_LENGTH

logger = logging.getLogger(__name__)


class FileReader:
    """Secure file reader with validation"""

    @staticmethod
    def read_file(
        file_path: str,
        working_directory: str | None = None,
        *,
        include_error: bool = False,
    ):
        """
        Securely read a file with validation.

        Returns:
            Content string when successful or None when blocked.
            If include_error=True, returns Tuple[content, error_message].
        """
        # Validate path
        is_valid, resolved_path, error = SecurityValidator.validate_path(
            file_path, working_directory
        )
        if not is_valid:
            logger.warning(f"Path validation failed: {error}")
            if include_error:
                return None, error
            return None

        try:
            # Read file with encoding detection
            path = Path(resolved_path)

            # Try UTF-8 first, then fallback to latin-1
            encodings = ["utf-8", "latin-1", "ascii"]
            content = None

            for encoding in encodings:
                try:
                    content = path.read_text(encoding=encoding)

                    # Validate content
                    lines = content.split("\n")
                    if any(len(line) > MAX_LINE_LENGTH for line in lines):
                        logger.warning(
                            f"File contains very long lines: {resolved_path}"
                        )
                        # Truncate long lines
                        lines = [
                            (
                                line[:MAX_LINE_LENGTH] + "..."
                                if len(line) > MAX_LINE_LENGTH
                                else line
                            )
                            for line in lines
                        ]
                        content = "\n".join(lines)

                    if include_error:
                        return content, None
                    return content

                except UnicodeDecodeError:
                    continue

            error_msg = (
                f"Could not decode file with any supported encoding: {resolved_path}"
            )
            if include_error:
                return None, error_msg
            return None

        except Exception as e:
            logger.error(f"Error reading file {resolved_path}: {str(e)}")
            error_msg = f"Error reading file: {str(e)}"
            if include_error:
                return None, error_msg
            return None
