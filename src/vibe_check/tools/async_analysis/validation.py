"""
Input Validation for Async Analysis APIs

Comprehensive input validation and sanitization to prevent malicious requests
and ensure data integrity for the async analysis system.
"""

import re
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_value: Optional[Any] = None


class AsyncAnalysisValidator:
    """
    Validates and sanitizes inputs for async analysis APIs.
    
    Provides comprehensive validation for repository names, PR numbers,
    and other API inputs to prevent injection attacks and ensure data integrity.
    """
    
    # Repository name pattern: owner/repo (GitHub format) - stricter pattern
    REPO_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]{0,37}[a-zA-Z0-9])?/[a-zA-Z0-9]([a-zA-Z0-9._-]{0,98}[a-zA-Z0-9])?$')
    
    # Maximum lengths for safety
    MAX_REPO_LENGTH = 100
    MAX_PR_NUMBER = 999999
    MAX_JOB_ID_LENGTH = 100
    
    # Allowed characters for job IDs
    JOB_ID_PATTERN = re.compile(r'^[a-zA-Z0-9#._-]+$')
    
    @classmethod
    def validate_repository(cls, repository: str) -> ValidationResult:
        """
        Validate and sanitize repository name.
        
        Args:
            repository: Repository string in "owner/repo" format
            
        Returns:
            ValidationResult with validation status and sanitized value
        """
        if not repository or not isinstance(repository, str):
            return ValidationResult(
                is_valid=False,
                error_message="Repository name is required and must be a string"
            )
        
        # Trim whitespace
        repository = repository.strip()
        
        # Check length
        if len(repository) > cls.MAX_REPO_LENGTH:
            return ValidationResult(
                is_valid=False,
                error_message=f"Repository name too long (max {cls.MAX_REPO_LENGTH} characters)"
            )
        
        # Check for consecutive dots (not allowed in GitHub repo names)
        if '..' in repository:
            return ValidationResult(
                is_valid=False,
                error_message="Repository name cannot contain consecutive dots"
            )
        
        # Check format
        if not cls.REPO_PATTERN.match(repository):
            return ValidationResult(
                is_valid=False,
                error_message="Repository must be in 'owner/repo' format with valid characters"
            )
        
        # Additional security checks
        if cls._contains_suspicious_patterns(repository):
            return ValidationResult(
                is_valid=False,
                error_message="Repository name contains invalid characters or patterns"
            )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=repository
        )
    
    @classmethod
    def validate_pr_number(cls, pr_number: Any) -> ValidationResult:
        """
        Validate and sanitize PR number.
        
        Args:
            pr_number: PR number (int, str, or other)
            
        Returns:
            ValidationResult with validation status and sanitized value
        """
        if pr_number is None:
            return ValidationResult(
                is_valid=False,
                error_message="PR number is required"
            )
        
        # Convert to int if string
        try:
            if isinstance(pr_number, str):
                pr_number = pr_number.strip()
                pr_number = int(pr_number)
            elif not isinstance(pr_number, int):
                raise ValueError("Invalid type")
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                error_message="PR number must be a positive integer"
            )
        
        # Validate range
        if pr_number <= 0:
            return ValidationResult(
                is_valid=False,
                error_message="PR number must be positive"
            )
        
        if pr_number > cls.MAX_PR_NUMBER:
            return ValidationResult(
                is_valid=False,
                error_message=f"PR number too large (max {cls.MAX_PR_NUMBER})"
            )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=pr_number
        )
    
    @classmethod
    def validate_job_id(cls, job_id: str) -> ValidationResult:
        """
        Validate and sanitize job ID.
        
        Args:
            job_id: Async analysis job identifier
            
        Returns:
            ValidationResult with validation status and sanitized value
        """
        if not job_id or not isinstance(job_id, str):
            return ValidationResult(
                is_valid=False,
                error_message="Job ID is required and must be a string"
            )
        
        # Trim whitespace
        job_id = job_id.strip()
        
        # Check length
        if len(job_id) > cls.MAX_JOB_ID_LENGTH:
            return ValidationResult(
                is_valid=False,
                error_message=f"Job ID too long (max {cls.MAX_JOB_ID_LENGTH} characters)"
            )
        
        # Check format
        if not cls.JOB_ID_PATTERN.match(job_id):
            return ValidationResult(
                is_valid=False,
                error_message="Job ID contains invalid characters"
            )
        
        # Additional security checks
        if cls._contains_suspicious_patterns(job_id):
            return ValidationResult(
                is_valid=False,
                error_message="Job ID contains suspicious patterns"
            )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=job_id
        )
    
    @classmethod
    def validate_pr_data(cls, pr_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate PR data structure and contents.
        
        Args:
            pr_data: PR metadata dictionary
            
        Returns:
            ValidationResult with validation status and sanitized data
        """
        if not isinstance(pr_data, dict):
            return ValidationResult(
                is_valid=False,
                error_message="PR data must be a dictionary"
            )
        
        # Required fields
        required_fields = ['title', 'additions', 'deletions', 'changed_files']
        for field in required_fields:
            if field not in pr_data:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Required field '{field}' missing from PR data"
                )
        
        # Validate numeric fields
        numeric_fields = ['additions', 'deletions', 'changed_files']
        sanitized_data = pr_data.copy()
        
        for field in numeric_fields:
            value = pr_data[field]
            try:
                value = int(value) if value is not None else 0
                if value < 0:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Field '{field}' must be non-negative"
                    )
                if value > 1000000:  # Reasonable upper limit
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Field '{field}' value too large"
                    )
                sanitized_data[field] = value
            except (ValueError, TypeError):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Field '{field}' must be a non-negative integer"
                )
        
        # Validate title
        title = pr_data.get('title', '')
        if not isinstance(title, str):
            return ValidationResult(
                is_valid=False,
                error_message="PR title must be a string"
            )
        
        title = title.strip()
        if len(title) > 500:  # Reasonable limit
            title = title[:500]
        
        sanitized_data['title'] = title
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized_data
        )
    
    @classmethod
    def _contains_suspicious_patterns(cls, value: str) -> bool:
        """Check for suspicious patterns that might indicate injection attempts."""
        suspicious_patterns = [
            # SQL injection patterns
            r'(union|select|insert|update|delete|drop|create|alter)\s',
            # Script injection patterns  
            r'<script|javascript:|data:',
            # Path traversal
            r'\.\./|\.\.\\',
            # Command injection
            r'[;&|`$(){}[\]]',
            # Null bytes
            r'\x00',
        ]
        
        value_lower = value.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(
                    f"Suspicious pattern detected in input: {pattern}",
                    extra={"input_value": value[:50]}  # Log first 50 chars only
                )
                return True
        
        return False


def validate_async_analysis_request(
    pr_number: Any,
    repository: str,
    pr_data: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate complete async analysis request.
    
    Args:
        pr_number: PR number to validate
        repository: Repository name to validate
        pr_data: PR metadata to validate
        
    Returns:
        Tuple of (is_valid, result_or_error)
        - If valid: (True, {"pr_number": int, "repository": str, "pr_data": dict})
        - If invalid: (False, {"error": str, "field": str})
    """
    # Validate PR number
    pr_result = AsyncAnalysisValidator.validate_pr_number(pr_number)
    if not pr_result.is_valid:
        return False, {
            "error": pr_result.error_message,
            "field": "pr_number"
        }
    
    # Validate repository
    repo_result = AsyncAnalysisValidator.validate_repository(repository)
    if not repo_result.is_valid:
        return False, {
            "error": repo_result.error_message,
            "field": "repository"
        }
    
    # Validate PR data
    data_result = AsyncAnalysisValidator.validate_pr_data(pr_data)
    if not data_result.is_valid:
        return False, {
            "error": data_result.error_message,
            "field": "pr_data"
        }
    
    # Return sanitized values
    return True, {
        "pr_number": pr_result.sanitized_value,
        "repository": repo_result.sanitized_value,
        "pr_data": data_result.sanitized_value
    }


def validate_status_check_request(job_id: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate status check request.
    
    Args:
        job_id: Job ID to validate
        
    Returns:
        Tuple of (is_valid, result_or_error)
        - If valid: (True, {"job_id": str})
        - If invalid: (False, {"error": str})
    """
    result = AsyncAnalysisValidator.validate_job_id(job_id)
    
    if result.is_valid:
        return True, {"job_id": result.sanitized_value}
    else:
        return False, {"error": result.error_message}