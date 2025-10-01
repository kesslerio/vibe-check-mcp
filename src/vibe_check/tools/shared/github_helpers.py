"""
GitHub Helper Functions

Consolidated GitHub integration utilities shared across vibe check tools.
Provides authentication, API access, and comment posting functionality.
"""

import logging
import os
import subprocess
from typing import Optional, Any

logger = logging.getLogger(__name__)

# GitHub integration
try:
    from github import Github, GithubException

    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


def get_github_token() -> Optional[str]:
    """
    Get GitHub token from environment or gh CLI.

    Tries multiple sources in order:
    1. GITHUB_PERSONAL_ACCESS_TOKEN environment variable
    2. GITHUB_TOKEN environment variable
    3. gh CLI auth token command

    Returns:
        GitHub token string if available, None otherwise
    """
    # Try environment variable first
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get(
        "GITHUB_TOKEN"
    )
    if token:
        return token

    # Fallback to gh CLI
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.warning(f"Could not get GitHub token from gh CLI: {e}")

    return None


def post_github_comment(
    issue_number: int, repository: str, comment_body: str
) -> tuple[bool, Optional[str]]:
    """
    Post comment to GitHub issue using proper authentication.

    Args:
        issue_number: GitHub issue number to comment on
        repository: Repository in format "owner/repo"
        comment_body: Content of the comment to post

    Returns:
        Tuple of (success: bool, comment_url: Optional[str])
    """
    if not GITHUB_AVAILABLE:
        logger.error("GitHub library not available for posting comments")
        return False, None

    token = get_github_token()
    if not token:
        logger.error("No GitHub token available for posting comments")
        return False, None

    try:
        github_client = Github(token)
        repo = github_client.get_repo(repository)
        issue = repo.get_issue(issue_number)
        comment = issue.create_comment(comment_body)

        # Build comment URL
        comment_url = f"https://github.com/{repository}/issues/{issue_number}#issuecomment-{comment.id}"

        logger.info(
            f"Successfully posted comment to {repository}#{issue_number}: {comment_url}"
        )
        return True, comment_url
    except Exception as e:
        logger.error(f"Failed to post GitHub comment: {e}")
        return False, None


def get_github_client() -> Optional[Github]:
    """
    Get authenticated GitHub client.

    Returns:
        Authenticated Github client if available, None otherwise
    """
    if not GITHUB_AVAILABLE:
        logger.error("GitHub library not available")
        return None

    token = get_github_token()
    if not token:
        logger.error("No GitHub token available")
        return None

    try:
        return Github(token)
    except Exception as e:
        logger.error(f"Failed to create GitHub client: {e}")
        return None


def check_github_authentication() -> dict:
    """
    Check GitHub authentication status and provide helpful error messages.

    Returns:
        Dictionary with status information and error details if applicable
    """
    if not GITHUB_AVAILABLE:
        return {
            "authenticated": False,
            "error": "GitHub library not available",
            "solution": "Install PyGithub: pip install PyGithub",
        }

    token = get_github_token()
    if not token:
        return {
            "authenticated": False,
            "error": "No GitHub token available",
            "solution": "Set GITHUB_PERSONAL_ACCESS_TOKEN environment variable or run 'gh auth login'",
        }

    try:
        client = Github(token)
        user = client.get_user()
        return {
            "authenticated": True,
            "username": user.login,
            "token_source": (
                "GITHUB_PERSONAL_ACCESS_TOKEN"
                if os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
                else "gh CLI"
            ),
        }
    except Exception as e:
        return {
            "authenticated": False,
            "error": f"GitHub authentication failed: {str(e)}",
            "solution": "Check token validity or run 'gh auth refresh'",
        }


def convert_api_url_to_frontend(url: str) -> str:
    """
    Convert GitHub API URLs to user-facing frontend URLs.

    Args:
        url: GitHub URL (API or frontend)

    Returns:
        Frontend GitHub URL
    """
    if not url:
        return url

    # Convert API URLs to frontend URLs
    if "api.github.com" in url:
        # Convert issue API URLs: https://api.github.com/repos/owner/repo/issues/123
        # To frontend URLs: https://github.com/owner/repo/issues/123
        if "/repos/" in url and "/issues/" in url:
            # Extract parts: https://api.github.com/repos/owner/repo/issues/123
            parts = url.replace("https://api.github.com/repos/", "").split("/")
            if len(parts) >= 4 and parts[2] == "issues":
                owner, repo, _, issue_num = parts[:4]
                return f"https://github.com/{owner}/{repo}/issues/{issue_num}"

        # Convert PR API URLs: https://api.github.com/repos/owner/repo/pulls/123
        # To frontend URLs: https://github.com/owner/repo/pull/123
        elif "/repos/" in url and "/pulls/" in url:
            parts = url.replace("https://api.github.com/repos/", "").split("/")
            if len(parts) >= 4 and parts[2] == "pulls":
                owner, repo, _, pr_num = parts[:4]
                return f"https://github.com/{owner}/{repo}/pull/{pr_num}"

    # Return as-is if already a frontend URL or unrecognized format
    return url


def sanitize_github_urls_in_response(data: Any) -> Any:
    """
    Recursively convert any GitHub API URLs to frontend URLs in response data.

    Args:
        data: Response data (dict, list, or primitive)

    Returns:
        Data with API URLs converted to frontend URLs
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Convert URL fields
            if key.endswith("_url") or key == "url":
                if isinstance(value, str):
                    result[key] = convert_api_url_to_frontend(value)
                else:
                    result[key] = value
            else:
                result[key] = sanitize_github_urls_in_response(value)
        return result
    elif isinstance(data, list):
        return [sanitize_github_urls_in_response(item) for item in data]
    else:
        return data
