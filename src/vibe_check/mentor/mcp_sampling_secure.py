"""
MCP Sampling Integration for Dynamic Response Generation - SECURE VERSION
This module implements security fixes for Issue #194

Security Features:
- Jinja2 safe template rendering (prevents injection)
- Pydantic input validation models
- File access controls with allowlist/denylist
- Rate limiting with token bucket algorithm
- Enhanced secrets scanning
"""

import logging
import json
import html
import re
import string
import time
import asyncio
import hashlib
import os
from pathlib import Path
from collections import OrderedDict, deque
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

# Pydantic for input validation
from pydantic import BaseModel, Field, field_validator, model_validator

# Jinja2 for safe template rendering
from jinja2 import Environment, BaseLoader, TemplateSyntaxError, select_autoescape
from jinja2.sandbox import SandboxedEnvironment

# MIME type detection for enhanced security
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

# Import MCP types for sampling
try:
    from mcp.types import (
        TextContent,
        ImageContent,
        SamplingMessage
    )
except ImportError:
    # Fallback definitions for development
    TextContent = Dict[str, Any]
    ImageContent = Dict[str, Any]
    SamplingMessage = Dict[str, Any]

logger = logging.getLogger(__name__)


# ============================================================================
# SECURITY: Input Validation Models using Pydantic
# ============================================================================

class QueryInput(BaseModel):
    """Validated query input model"""
    query: str = Field(..., min_length=1, max_length=5000)
    intent: Optional[str] = Field(None, max_length=100)
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate query for injection patterns"""
        injection_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',  # Event handlers
            r'eval\(',
            r'exec\(',
            r'__import__',
            r'globals\(',
            r'locals\(',
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Potential injection pattern detected: {pattern}")
        
        return v


class FilePathInput(BaseModel):
    """Validated file path input"""
    path: str = Field(..., max_length=500)
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        """Validate file path for traversal attacks"""
        # Normalize path
        normalized = os.path.normpath(v)
        
        # Check for path traversal
        if '..' in normalized or normalized.startswith('/etc/') or normalized.startswith('/proc/'):
            raise ValueError("Path traversal or restricted path detected")
        
        # Check for null bytes
        if '\x00' in v:
            raise ValueError("Null byte in path")
        
        return normalized


class WorkspaceDataInput(BaseModel):
    """Validated workspace data input"""
    files: Optional[List[str]] = Field(default=None, max_length=100)
    code: Optional[str] = Field(default=None, max_length=50000)
    language: Optional[str] = Field(default=None, max_length=50)
    frameworks: Optional[List[str]] = Field(default=None, max_length=20)
    imports: Optional[List[str]] = Field(default=None, max_length=100)
    file_path: Optional[str] = Field(default=None, max_length=500)
    
    @field_validator('files', 'frameworks', 'imports')
    @classmethod
    def validate_list_items(cls, v):
        """Validate list items for length"""
        if v is not None:
            for item in v:
                if isinstance(item, str) and len(item) > 200:
                    raise ValueError("List item too long")
        return v


# ============================================================================
# SECURITY: Rate Limiting with Token Bucket Algorithm
# ============================================================================

class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float, refill_period: float = 1.0):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Number of tokens added per period
            refill_period: Time period in seconds for refill
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket
        
        Returns:
            True if tokens were consumed, False if rate limit exceeded
        """
        async with self._lock:
            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_refill
            tokens_to_add = (elapsed / self.refill_period) * self.refill_rate
            
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            # Try to consume
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def get_wait_time(self) -> float:
        """Get time to wait before next token is available"""
        async with self._lock:
            if self.tokens >= 1:
                return 0.0
            
            tokens_needed = 1 - self.tokens
            wait_time = (tokens_needed / self.refill_rate) * self.refill_period
            return wait_time


class RateLimiter:
    """Rate limiter for MCP operations"""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_capacity: int = 10,
        per_user: bool = True,
        max_buckets: int = 1000,  # configurable threshold for cleanup
        retain_buckets: int = 500  # how many buckets to keep during cleanup
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_capacity = burst_capacity
        self.per_user = per_user
        self.max_buckets = max_buckets
        self.retain_buckets = retain_buckets
        self.buckets: Dict[str, TokenBucket] = {}
        self._cleanup_interval = 300  # Clean up old buckets every 5 minutes
        self._last_cleanup = time.time()
    
    def _get_bucket_key(self, user_id: Optional[str] = None) -> str:
        """Get bucket key for rate limiting"""
        if self.per_user and user_id:
            return f"user:{user_id}"
        return "global"
    
    async def check_rate_limit(self, user_id: Optional[str] = None, tokens: int = 1) -> Tuple[bool, Optional[float]]:
        """
        Check if request is within rate limit
        
        Returns:
            Tuple of (allowed, wait_time_seconds)
        """
        # Clean up old buckets periodically
        if time.time() - self._last_cleanup > self._cleanup_interval:
            self._cleanup_old_buckets()
        
        key = self._get_bucket_key(user_id)
        
        if key not in self.buckets:
            # Create new bucket
            refill_rate = self.requests_per_minute / 60.0  # Per second
            self.buckets[key] = TokenBucket(
                capacity=self.burst_capacity,
                refill_rate=refill_rate,
                refill_period=1.0
            )
        
        bucket = self.buckets[key]
        allowed = await bucket.consume(tokens)
        
        if not allowed:
            wait_time = await bucket.get_wait_time()
            return False, wait_time
        
        return True, None
    
    def _cleanup_old_buckets(self):
        """Remove inactive buckets to prevent memory leak"""
        # Use configurable thresholds for cleanup
        if len(self.buckets) > self.max_buckets:
            # Keep only the most recent buckets based on retain_buckets setting
            keys = list(self.buckets.keys())
            buckets_to_remove = len(keys) - self.retain_buckets
            for key in keys[:buckets_to_remove]:
                del self.buckets[key]
            
            # Log cleanup for monitoring
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Rate limiter cleanup: removed {buckets_to_remove} old buckets, "
                       f"retained {self.retain_buckets} active buckets")
        
        self._last_cleanup = time.time()


# ============================================================================
# SECURITY: File Access Controls
# ============================================================================

class FileAccessController:
    """Controls file access with allowlist/denylist"""
    
    # Default restricted paths
    RESTRICTED_PATHS = {
        '/etc/', '/proc/', '/sys/', '/dev/',
        '~/.ssh/', '~/.aws/', '~/.config/',
        '.git/config', '.env', 'secrets.', 'credentials.',
        'private_key', 'id_rsa', 'id_dsa', 'id_ecdsa',
        '.key', '.pem', '.p12', '.pfx',
        'shadow', 'passwd', 'sudoers'
    }
    
    # Default allowed extensions
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.clj', '.ex', '.exs', '.ml', '.mli',
        '.json', '.yaml', '.yml', '.toml', '.xml', '.html', '.css',
        '.md', '.txt', '.rst', '.sql', '.sh', '.bash', '.zsh'
    }
    
    # Allowed MIME types for enhanced security
    ALLOWED_MIME_TYPES = {
        # Text files
        'text/plain', 'text/x-python', 'text/javascript', 'text/x-typescript',
        'text/x-java-source', 'text/x-go', 'text/x-rust', 'text/x-c',
        'text/x-c++', 'text/x-csharp', 'text/x-ruby', 'text/x-php',
        'text/x-swift', 'text/x-kotlin', 'text/x-scala', 'text/x-clojure',
        'text/x-elixir', 'text/x-ocaml', 'text/html', 'text/css',
        'text/markdown', 'text/x-rst', 'text/x-sql', 'text/x-shellscript',
        # Structured data
        'application/json', 'application/yaml', 'text/yaml',
        'application/toml', 'application/xml', 'text/xml',
        # Configuration files
        'application/x-yaml', 'text/x-yaml', 'text/x-toml',
        # Documentation
        'text/x-markdown', 'application/rtf'
    }
    
    def __init__(
        self,
        allowed_paths: Optional[Set[str]] = None,
        restricted_paths: Optional[Set[str]] = None,
        allowed_extensions: Optional[Set[str]] = None,
        allowed_mime_types: Optional[Set[str]] = None,
        enable_mime_validation: bool = True
    ):
        self.allowed_paths = allowed_paths or set()
        self.restricted_paths = self.RESTRICTED_PATHS | (restricted_paths or set())
        self.allowed_extensions = self.ALLOWED_EXTENSIONS | (allowed_extensions or set())
        self.allowed_mime_types = self.ALLOWED_MIME_TYPES | (allowed_mime_types or set())
        self.enable_mime_validation = enable_mime_validation and MAGIC_AVAILABLE
    
    def _validate_mime_type(self, file_path: Path) -> Tuple[bool, str]:
        """Validate file MIME type for enhanced security"""
        if not self.enable_mime_validation:
            return True, "MIME validation disabled"
        
        try:
            # Get MIME type using python-magic
            mime_type = magic.from_file(str(file_path), mime=True)
            
            if mime_type in self.allowed_mime_types:
                return True, f"MIME type allowed: {mime_type}"
            else:
                return False, f"MIME type not allowed: {mime_type}"
                
        except Exception as e:
            # Log error but don't fail completely
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"MIME type detection failed for {file_path}: {e}")
            # Fall back to extension-based validation only
            return True, f"MIME validation failed, using extension only: {e}"
    
    def is_allowed(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if file access is allowed
        
        Returns:
            Tuple of (allowed, reason)
        """
        try:
            # Validate input
            validated = FilePathInput(path=file_path)
            normalized_path = validated.path
        except Exception as e:
            return False, f"Invalid path: {e}"
        
        # Convert to Path object
        path = Path(normalized_path)
        
        # Check if path exists (prevent information disclosure)
        if not path.exists():
            return False, "Path does not exist"
        
        # Check if it's a file (not directory)
        if not path.is_file():
            return False, "Not a file"
        
        # Check file size (prevent DoS)
        max_size = 10 * 1024 * 1024  # 10MB
        if path.stat().st_size > max_size:
            return False, f"File too large (max {max_size} bytes)"
        
        # Check against restricted paths
        path_str = str(path.resolve())
        for restricted in self.restricted_paths:
            if restricted in path_str.lower():
                return False, f"Restricted path pattern: {restricted}"
        
        # Check extension
        if path.suffix.lower() not in self.allowed_extensions:
            return False, f"File type not allowed: {path.suffix}"
        
        # Check if in allowed paths (if specified)
        if self.allowed_paths:
            allowed = False
            for allowed_path in self.allowed_paths:
                if path_str.startswith(allowed_path):
                    allowed = True
                    break
            
            if not allowed:
                return False, "Path not in allowed directories"
        
        # Enhanced security: Validate MIME type
        mime_allowed, mime_reason = self._validate_mime_type(path)
        if not mime_allowed:
            return False, f"MIME type validation failed: {mime_reason}"
        
        return True, f"Access allowed - {mime_reason}"


# ============================================================================
# SECURITY: Safe Template Rendering with Jinja2
# ============================================================================

class SafeTemplateRenderer:
    """Safe template rendering using Jinja2 sandbox"""
    
    def __init__(self):
        # Use sandboxed environment for safety
        self.env = SandboxedEnvironment(
            loader=BaseLoader(),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add safe filters
        self.env.filters['sanitize'] = self._sanitize_filter
        self.env.filters['truncate_safe'] = self._truncate_safe
    
    @staticmethod
    def _sanitize_filter(text: str) -> str:
        """Sanitize text for safe display"""
        if not text:
            return ""
        
        # HTML escape
        text = html.escape(text)
        
        # Remove potential command injection patterns
        patterns = [
            (r'\$\([^)]+\)', '[COMMAND]'),  # Command substitution
            (r'`[^`]+`', '[COMMAND]'),      # Backtick command
            (r'<\?[^>]+\?>', '[PHP]'),      # PHP tags
            (r'<%[^>]+%>', '[ASP]'),        # ASP tags
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    @staticmethod
    def _truncate_safe(text: str, length: int = 1000) -> str:
        """Safely truncate text at word boundaries"""
        if not text or len(text) <= length:
            return text
        
        # Find last space before limit
        truncated = text[:length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def render(self, template_str: str, variables: Dict[str, Any]) -> str:
        """
        Safely render a template with variables
        
        Args:
            template_str: Jinja2 template string
            variables: Variables to render
            
        Returns:
            Rendered template
            
        Raises:
            TemplateSyntaxError: If template syntax is invalid
        """
        try:
            # Validate all input variables
            safe_vars = {}
            for key, value in variables.items():
                # Sanitize string values
                if isinstance(value, str):
                    safe_vars[key] = self._sanitize_filter(value)
                # Limit list sizes
                elif isinstance(value, list):
                    safe_vars[key] = value[:100]  # Max 100 items
                # Pass through safe types
                elif isinstance(value, (int, float, bool, type(None))):
                    safe_vars[key] = value
                # Convert complex types to string
                else:
                    safe_vars[key] = self._sanitize_filter(str(value))
            
            # Create and render template
            template = self.env.from_string(template_str)
            return template.render(**safe_vars)
            
        except TemplateSyntaxError as e:
            # Enhanced logging with template context
            logger.error(
                f"Template syntax error: {e}\n"
                f"Template content (first 200 chars): {template_str[:200]}\n"
                f"Variables provided: {list(variables.keys())}"
            )
            raise
        except Exception as e:
            # Enhanced logging with full context for debugging
            logger.error(
                f"Template rendering error: {e}\n"
                f"Template content (first 200 chars): {template_str[:200]}\n"
                f"Variables: {list(variables.keys())}\n"
                f"Error type: {type(e).__name__}\n"
                f"Error details: {str(e)}"
            )
            # Return more informative error message while still being safe
            return f"[Template Error: {type(e).__name__}]"


# ============================================================================
# Enhanced Secrets Scanner
# ============================================================================

class EnhancedSecretsScanner:
    """Enhanced scanner for secrets and sensitive data"""
    
    # Comprehensive secret patterns
    SECRET_PATTERNS = [
        # API Keys
        (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'API_KEY'),
        (r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'SECRET_KEY'),
        
        # Passwords
        (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\\s]{8,})["\']?', 'PASSWORD'),
        
        # Tokens
        (r'(?i)(auth[_-]?token|token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 'AUTH_TOKEN'),
        (r'(?i)bearer\s+([a-zA-Z0-9_\-\.]+)', 'BEARER_TOKEN'),
        
        # AWS
        (r'AKIA[0-9A-Z]{16}', 'AWS_ACCESS_KEY'),
        (r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?', 'AWS_SECRET_KEY'),
        
        # Private Keys
        (r'-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----', 'PRIVATE_KEY'),
        
        # Service-specific
        (r'sk-[a-zA-Z0-9]{48}', 'OPENAI_API_KEY'),
        (r'ghp_[a-zA-Z0-9]{36}', 'GITHUB_TOKEN'),
        (r'ghs_[a-zA-Z0-9]{36}', 'GITHUB_SECRET'),
        (r'(?i)slack[_-]?token\s*[:=]\s*["\']?xox[baprs]-[a-zA-Z0-9\-]+["\']?', 'SLACK_TOKEN'),
        
        # Database URLs
        (r'(?i)(postgres|mysql|mongodb|redis)://[^\\s]+@[^\\s]+', 'DATABASE_URL'),
        
        # JWT
        (r'eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+', 'JWT_TOKEN'),
        
        # Credit Cards (PCI compliance)
        (r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b', 'CREDIT_CARD'),
        
        # SSN (US)
        (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
    ]
    
    @classmethod
    def scan_and_redact(cls, text: str, context: str = "unknown") -> Tuple[str, List[Dict[str, Any]]]:
        """
        Scan text for secrets and redact them
        
        Args:
            text: Text to scan
            context: Context for logging (e.g., "user_input", "file_content")
            
        Returns:
            Tuple of (redacted_text, found_secrets)
        """
        if not text:
            return "", []
        
        redacted_text = text
        found_secrets = []
        
        for pattern, secret_type in cls.SECRET_PATTERNS:
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            
            for match in matches:
                secret_value = match.group(0)
                
                # Create hash for logging (don't log actual secret)
                secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()[:8]
                
                # Redact based on type
                if secret_type == 'CREDIT_CARD':
                    # Keep last 4 digits for credit cards
                    redacted = f"[REDACTED_CC_****{secret_value[-4:]}]"
                else:
                    redacted = f"[REDACTED_{secret_type}_{secret_hash}]"
                
                redacted_text = redacted_text.replace(secret_value, redacted)
                
                found_secrets.append({
                    'type': secret_type,
                    'hash': secret_hash,
                    'location': match.start(),
                    'length': len(secret_value),
                    'context': context
                })
        
        if found_secrets:
            logger.warning(
                f"[SECURITY] Detected and redacted {len(found_secrets)} potential secrets in {context}: "
                f"{', '.join(set(s['type'] for s in found_secrets))}"
            )
        
        return redacted_text, found_secrets
    
    @classmethod
    def validate_safe(cls, text: str) -> Tuple[bool, List[str]]:
        """
        Check if text is safe (no secrets detected)
        
        Returns:
            Tuple of (is_safe, detected_types)
        """
        detected_types = []
        
        for pattern, secret_type in cls.SECRET_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                detected_types.append(secret_type)
        
        return len(detected_types) == 0, detected_types


def sanitize_code_for_llm(code: str, max_length: int = 2000) -> str:
    """Sanitize code before sending to LLM to prevent injection attacks"""
    if not code:
        return ""
    
    # First, scan and redact secrets
    code, _ = EnhancedSecretsScanner.scan_and_redact(code, "code_content")
    
    # Remove potential prompt injection patterns
    injection_patterns = [
        r'#\s*ignore\s+all\s+previous',
        r'#\s*system\s*:',
        r'#\s*assistant\s*:',
        r'#\s*user\s*:',
        r'/\*\s*SYSTEM\s*\*/',
        r'""".*?ignore.*?instructions.*?"""',
        r"'''.*?ignore.*?instructions.*?'''",
        r'<\|.*?\|>',  # Special tokens
        r'\[\[.*?\]\]',  # Potential control sequences
    ]
    
    sanitized = code
    for pattern in injection_patterns:
        sanitized = re.sub(
            pattern, 
            '# [REDACTED - POTENTIAL INJECTION]', 
            sanitized, 
            flags=re.IGNORECASE | re.DOTALL
        )
    
    # Escape HTML entities to prevent rendering issues
    sanitized = html.escape(sanitized)
    
    # Truncate safely at word boundaries
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(' ', 1)[0] + '...'
    
    return sanitized


# Export the main classes
__all__ = [
    'QueryInput',
    'FilePathInput', 
    'WorkspaceDataInput',
    'TokenBucket',
    'RateLimiter',
    'FileAccessController',
    'SafeTemplateRenderer',
    'EnhancedSecretsScanner',
    'sanitize_code_for_llm'
]