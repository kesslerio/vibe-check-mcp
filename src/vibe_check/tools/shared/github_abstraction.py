"""
GitHub Operations Abstraction Layer

Provides a unified interface for GitHub operations that can be implemented
using either PyGithub library or GitHub MCP server. This supports the
architectural audit in issue #90 and allows flexible switching between
implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitHubIssue:
    """Standardized GitHub issue representation."""
    number: int
    title: str
    body: Optional[str]
    state: str
    user_login: str
    labels: List[str]
    repository: str
    html_url: str
    created_at: str
    updated_at: str


@dataclass
class GitHubPullRequest:
    """Standardized GitHub pull request representation."""
    number: int
    title: str
    body: Optional[str]
    state: str
    user_login: str
    labels: List[str]
    repository: str
    html_url: str
    head_ref: str
    base_ref: str
    diff_url: str
    created_at: str
    updated_at: str


@dataclass
class GitHubOperationResult:
    """Result of a GitHub operation with metadata."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    implementation: str = ""  # "pygithub" or "mcp"
    execution_time: float = 0.0


class GitHubOperations(ABC):
    """
    Abstract interface for GitHub operations.
    
    This interface can be implemented using either PyGithub library or
    GitHub MCP server, allowing flexible switching based on performance
    and integration requirements.
    """
    
    @abstractmethod
    def get_issue(self, repository: str, issue_number: int) -> GitHubOperationResult:
        """
        Fetch a GitHub issue.
        
        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number to fetch
            
        Returns:
            GitHubOperationResult with GitHubIssue data or error
        """
        pass
    
    @abstractmethod
    def get_pull_request(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """
        Fetch a GitHub pull request.
        
        Args:
            repository: Repository in format "owner/repo"
            pr_number: PR number to fetch
            
        Returns:
            GitHubOperationResult with GitHubPullRequest data or error
        """
        pass
    
    @abstractmethod
    def post_issue_comment(
        self, 
        repository: str, 
        issue_number: int, 
        comment_body: str
    ) -> GitHubOperationResult:
        """
        Post a comment to a GitHub issue.
        
        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number to comment on
            comment_body: Content of the comment
            
        Returns:
            GitHubOperationResult with success status or error
        """
        pass
    
    @abstractmethod
    def get_pull_request_diff(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """
        Get the diff content of a pull request.
        
        Args:
            repository: Repository in format "owner/repo"
            pr_number: PR number to get diff for
            
        Returns:
            GitHubOperationResult with diff content or error
        """
        pass
    
    @abstractmethod
    def get_pull_request_files(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """
        Get the list of files changed in a pull request.
        
        Args:
            repository: Repository in format "owner/repo"
            pr_number: PR number to get files for
            
        Returns:
            GitHubOperationResult with list of file names or error
        """
        pass
    
    @abstractmethod
    def check_authentication(self) -> GitHubOperationResult:
        """
        Check GitHub authentication status.
        
        Returns:
            GitHubOperationResult with authentication info or error
        """
        pass


class PyGitHubImplementation(GitHubOperations):
    """Implementation using PyGithub library."""
    
    def __init__(self):
        self.implementation_name = "pygithub"
        # Import here to avoid requiring PyGithub if not used
        try:
            from .github_helpers import get_github_client, GITHUB_AVAILABLE
            self.get_client = get_github_client
            self.available = GITHUB_AVAILABLE
        except ImportError:
            self.available = False
            logger.error("PyGithub not available")
    
    def get_issue(self, repository: str, issue_number: int) -> GitHubOperationResult:
        """Fetch issue using PyGithub."""
        if not self.available:
            return GitHubOperationResult(
                success=False,
                error="PyGithub not available",
                implementation=self.implementation_name
            )
        
        import time
        start_time = time.time()
        
        try:
            client = self.get_client()
            if not client:
                return GitHubOperationResult(
                    success=False,
                    error="GitHub authentication failed",
                    implementation=self.implementation_name
                )
            
            repo = client.get_repo(repository)
            issue = repo.get_issue(issue_number)
            
            github_issue = GitHubIssue(
                number=issue.number,
                title=issue.title,
                body=issue.body,
                state=issue.state,
                user_login=issue.user.login,
                labels=[label.name for label in issue.labels],
                repository=repository,
                html_url=issue.html_url,
                created_at=issue.created_at.isoformat(),
                updated_at=issue.updated_at.isoformat()
            )
            
            return GitHubOperationResult(
                success=True,
                data=github_issue,
                implementation=self.implementation_name,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return GitHubOperationResult(
                success=False,
                error=str(e),
                implementation=self.implementation_name,
                execution_time=time.time() - start_time
            )
    
    def get_pull_request(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """Fetch PR using PyGithub."""
        if not self.available:
            return GitHubOperationResult(
                success=False,
                error="PyGithub not available",
                implementation=self.implementation_name
            )
        
        import time
        start_time = time.time()
        
        try:
            client = self.get_client()
            if not client:
                return GitHubOperationResult(
                    success=False,
                    error="GitHub authentication failed",
                    implementation=self.implementation_name
                )
            
            repo = client.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            github_pr = GitHubPullRequest(
                number=pr.number,
                title=pr.title,
                body=pr.body,
                state=pr.state,
                user_login=pr.user.login,
                labels=[label.name for label in pr.labels],
                repository=repository,
                html_url=pr.html_url,
                head_ref=pr.head.ref,
                base_ref=pr.base.ref,
                diff_url=pr.diff_url,
                created_at=pr.created_at.isoformat(),
                updated_at=pr.updated_at.isoformat()
            )
            
            return GitHubOperationResult(
                success=True,
                data=github_pr,
                implementation=self.implementation_name,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return GitHubOperationResult(
                success=False,
                error=str(e),
                implementation=self.implementation_name,
                execution_time=time.time() - start_time
            )
    
    def post_issue_comment(
        self, 
        repository: str, 
        issue_number: int, 
        comment_body: str
    ) -> GitHubOperationResult:
        """Post comment using PyGithub."""
        if not self.available:
            return GitHubOperationResult(
                success=False,
                error="PyGithub not available",
                implementation=self.implementation_name
            )
        
        import time
        start_time = time.time()
        
        try:
            from .github_helpers import post_github_comment
            success = post_github_comment(issue_number, repository, comment_body)
            
            return GitHubOperationResult(
                success=success,
                data={"comment_posted": success},
                implementation=self.implementation_name,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return GitHubOperationResult(
                success=False,
                error=str(e),
                implementation=self.implementation_name,
                execution_time=time.time() - start_time
            )
    
    def get_pull_request_diff(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """Get PR diff using PyGithub."""
        if not self.available:
            return GitHubOperationResult(
                success=False,
                error="PyGithub not available",
                implementation=self.implementation_name
            )
        
        import time
        start_time = time.time()
        
        try:
            client = self.get_client()
            if not client:
                return GitHubOperationResult(
                    success=False,
                    error="GitHub authentication failed",
                    implementation=self.implementation_name
                )
            
            repo = client.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            # Get the diff URL and fetch it with authentication
            import requests
            from .github_helpers import get_github_token
            
            token = get_github_token()
            if not token:
                return GitHubOperationResult(
                    success=False,
                    error="No GitHub token available for diff fetching",
                    implementation=self.implementation_name,
                    execution_time=time.time() - start_time
                )
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3.diff'
            }
            
            diff_response = requests.get(pr.diff_url, headers=headers)
            if diff_response.status_code == 200:
                diff_content = diff_response.text
                
                return GitHubOperationResult(
                    success=True,
                    data=diff_content,
                    implementation=self.implementation_name,
                    execution_time=time.time() - start_time
                )
            else:
                return GitHubOperationResult(
                    success=False,
                    error=f"Failed to fetch diff: HTTP {diff_response.status_code}",
                    implementation=self.implementation_name,
                    execution_time=time.time() - start_time
                )
            
        except Exception as e:
            return GitHubOperationResult(
                success=False,
                error=str(e),
                implementation=self.implementation_name,
                execution_time=time.time() - start_time
            )
    
    def get_pull_request_files(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """Get PR files using PyGithub."""
        return GitHubOperationResult(
            success=False,
            error="Not implemented yet", 
            implementation=self.implementation_name
        )
    
    def check_authentication(self) -> GitHubOperationResult:
        """Check auth using PyGithub."""
        try:
            from .github_helpers import check_github_authentication
            auth_status = check_github_authentication()
            
            return GitHubOperationResult(
                success=auth_status.get("authenticated", False),
                data=auth_status,
                implementation=self.implementation_name
            )
            
        except Exception as e:
            return GitHubOperationResult(
                success=False,
                error=str(e),
                implementation=self.implementation_name
            )


class GitHubMCPImplementation(GitHubOperations):
    """Implementation using GitHub MCP server."""
    
    def __init__(self):
        self.implementation_name = "mcp"
        # This would be implemented to use MCP server tools
        # For now, showing structure
    
    def get_issue(self, repository: str, issue_number: int) -> GitHubOperationResult:
        """Fetch issue using MCP server."""
        return GitHubOperationResult(
            success=False,
            error="MCP implementation not ready yet",
            implementation=self.implementation_name
        )
    
    def get_pull_request(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """Fetch PR using MCP server."""
        return GitHubOperationResult(
            success=False,
            error="MCP implementation not ready yet",
            implementation=self.implementation_name
        )
    
    def post_issue_comment(
        self, 
        repository: str, 
        issue_number: int, 
        comment_body: str
    ) -> GitHubOperationResult:
        """Post comment using MCP server."""
        return GitHubOperationResult(
            success=False,
            error="MCP implementation not ready yet",
            implementation=self.implementation_name
        )
    
    def get_pull_request_diff(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """Get PR diff using MCP server."""
        return GitHubOperationResult(
            success=False,
            error="MCP implementation not ready yet",
            implementation=self.implementation_name
        )
    
    def get_pull_request_files(self, repository: str, pr_number: int) -> GitHubOperationResult:
        """Get PR files using MCP server."""
        return GitHubOperationResult(
            success=False,
            error="MCP implementation not ready yet",
            implementation=self.implementation_name
        )
    
    def check_authentication(self) -> GitHubOperationResult:
        """Check auth using MCP server."""
        return GitHubOperationResult(
            success=False,
            error="MCP implementation not ready yet",
            implementation=self.implementation_name
        )


# Factory function for creating GitHub operations
def create_github_operations(implementation: str = "pygithub") -> GitHubOperations:
    """
    Factory function to create GitHub operations implementation.
    
    Args:
        implementation: Either "pygithub" or "mcp"
        
    Returns:
        GitHubOperations implementation instance
    """
    if implementation == "pygithub":
        return PyGitHubImplementation()
    elif implementation == "mcp":
        return GitHubMCPImplementation()
    else:
        raise ValueError(f"Unknown implementation: {implementation}")


# Convenience function for default implementation
def get_default_github_operations() -> GitHubOperations:
    """
    Get the default GitHub operations implementation.
    
    Can be configured via environment variable GITHUB_IMPLEMENTATION
    or defaults to PyGithub for now.
    """
    import os
    implementation = os.environ.get("GITHUB_IMPLEMENTATION", "pygithub")
    return create_github_operations(implementation)