#!/usr/bin/env python3
"""
Version utilities for Vibe Check MCP.

Provides centralized version management, validation, and release utilities.
"""

import re
import os
from pathlib import Path
from typing import Tuple, Optional


def get_version() -> str:
    """
    Get the current version from VERSION file.

    Returns:
        Version string in semantic versioning format (major.minor.patch)
    """
    try:
        version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback version
        return "0.1.0"


def parse_semantic_version(version_str: str) -> Tuple[int, int, int]:
    """
    Parse semantic version string into major, minor, patch tuple

    Args:
        version_str: Version string in format "MAJOR.MINOR.PATCH"

    Returns:
        Tuple of (major, minor, patch) integers

    Raises:
        ValueError: If version string is invalid
    """
    if not re.match(r"^\d+\.\d+\.\d+$", version_str):
        raise ValueError(f"Invalid semantic version format: {version_str}")

    parts = version_str.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def increment_version(version: str, release_type: str) -> str:
    """
    Increment version based on release type.

    Args:
        version: Current version string
        release_type: One of 'major', 'minor', 'patch'

    Returns:
        New version string

    Raises:
        ValueError: If release_type is invalid
    """
    major, minor, patch = parse_semantic_version(version)

    if release_type == "major":
        return f"{major + 1}.0.0"
    elif release_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif release_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid release type: {release_type}")


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic version strings

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
    """
    v1_parts = parse_semantic_version(version1)
    v2_parts = parse_semantic_version(version2)

    if v1_parts < v2_parts:
        return -1
    elif v1_parts > v2_parts:
        return 1
    else:
        return 0


def is_compatible_version(
    current_version: str, required_version: str, compatibility_level: str = "minor"
) -> bool:
    """
    Check if current version is compatible with required version

    Args:
        current_version: Current version string
        required_version: Required version string
        compatibility_level: "major", "minor", or "patch"

    Returns:
        True if versions are compatible, False otherwise
    """
    current = parse_semantic_version(current_version)
    required = parse_semantic_version(required_version)

    if compatibility_level == "major":
        return current[0] == required[0]
    elif compatibility_level == "minor":
        return current[0] == required[0] and current[1] >= required[1]
    elif compatibility_level == "patch":
        return compare_versions(current_version, required_version) >= 0
    else:
        raise ValueError(f"Invalid compatibility level: {compatibility_level}")


def get_migration_path(from_version: str, to_version: str) -> Optional[str]:
    """
    Get migration guidance between versions

    Args:
        from_version: Source version
        to_version: Target version

    Returns:
        Migration guidance string or None if no migration needed
    """
    from_v = parse_semantic_version(from_version)
    to_v = parse_semantic_version(to_version)

    if from_v == to_v:
        return None

    major_diff = to_v[0] - from_v[0]
    minor_diff = to_v[1] - from_v[1]
    patch_diff = to_v[2] - from_v[2]

    if major_diff > 0:
        return f"Major version upgrade required: {from_version} -> {to_version}. Check breaking changes."
    elif minor_diff > 0:
        return f"Minor version upgrade: {from_version} -> {to_version}. New features available."
    elif patch_diff > 0:
        return f"Patch version upgrade: {from_version} -> {to_version}. Bug fixes included."
    else:
        return f"Version downgrade: {from_version} -> {to_version}. Compatibility check recommended."


# Export the current version
__version__ = get_version()
