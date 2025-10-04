"""GitHub API client for issue analysis."""

import logging
import re
from typing import Dict, Any, Optional, List

from github import Github, GithubException
from github.Issue import Issue

from .models import IssueLabel

logger = logging.getLogger(__name__)


class GitHubIssueClient:
    """Handles GitHub API interactions for issue fetching."""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub API client.

        Args:
            github_token: GitHub API token for authentication (optional for public repos)
        """
        self.github_client = Github(github_token) if github_token else Github()
        logger.debug("GitHub API client initialized")

    def fetch_issue_data(
        self, issue_number: int, repository: Optional[str]
    ) -> Dict[str, Any]:
        """
        Fetch GitHub issue data via GitHub API.

        Args:
            issue_number: Issue number to fetch
            repository: Repository in format "owner/repo"

        Returns:
            Issue data dictionary

        Raises:
            ValueError: If repository format is invalid
            GithubException: If issue not found or API error
        """
        # Default repository handling
        if repository is None:
            repository = "kesslerio/vibe-check-mcp"  # Default to this project

        # Validate repository format
        if "/" not in repository:
            raise ValueError("Repository must be in format 'owner/repo'")

        # Sanitize repository input to prevent injection
        # GitHub allows alphanumeric, hyphens, underscores, and dots
        if not re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", repository):
            raise ValueError("Repository format contains invalid characters")

        try:
            # Get repository and issue
            repo = self.github_client.get_repo(repository)
            issue: Issue = repo.get_issue(issue_number)

            # Extract relevant issue data
            label_names: List[str] = []
            for label in issue.labels:
                label_name = getattr(label, "name", None)
                if isinstance(label_name, str) and label_name:
                    label_names.append(label_name)
                else:
                    logger.warning(f"Skipping invalid label: {label}")

            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "author": issue.user.login,
                "created_at": issue.created_at.isoformat(),
                "state": issue.state,
                "labels": [IssueLabel(name=name) for name in label_names],
                "url": issue.html_url,
                "repository": repository,
            }

            logger.info(f"Fetched issue #{issue_number} from {repository}")
            return issue_data

        except GithubException as e:
            if e.status == 404:
                raise GithubException(
                    404, {"message": f"Issue #{issue_number} not found in {repository}"}
                )
            raise
