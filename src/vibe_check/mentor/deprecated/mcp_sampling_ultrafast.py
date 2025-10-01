"""
MCP Sampling Security - ULTRA-FAST VERSION (<10% overhead)
Achieves minimal overhead through aggressive optimization

Key strategies:
1. No regex in hot path - use simple string operations
2. Early exits on common cases
3. Minimal allocations
4. Inline simple checks
"""

import time
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

# Single global rate limiter instance to avoid allocation
_global_rate_limiter_tokens = 10
_global_rate_limiter_last = time.time()
_global_rate_limiter_lock = asyncio.Lock()

# Pre-computed constants
DANGEROUS_STRINGS = frozenset(
    [
        "<script",
        "javascript:",
        "eval(",
        "exec(",
        "__import__",
        "drop table",
        "delete from",
        "; --",
    ]
)
SECRET_INDICATORS = frozenset(
    ["api", "key", "secret", "token", "password", "bearer", "ghp_"]
)
RESTRICTED_PATHS = frozenset(["/etc/", "/proc/", "/sys/", "/dev/", ".ssh/", ".aws/"])
ALLOWED_EXTENSIONS = frozenset(
    [
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".json",
        ".yaml",
        ".yml",
        ".md",
        ".txt",
    ]
)


def validate_query_ultrafast(
    query: str, intent: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Ultra-fast query validation with minimal overhead
    Returns: (is_valid, sanitized_data)
    """
    # Fast type check
    if not isinstance(query, str) or not query:
        return False, {}

    # Fast length check
    length = len(query)
    if length == 0 or length > 5000:
        return False, {}

    # Ultra-fast dangerous content check (no regex)
    query_lower = query.lower()
    for danger in DANGEROUS_STRINGS:
        if danger in query_lower:
            return False, {}

    return True, {"query": query, "intent": intent}


def validate_workspace_ultrafast(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Ultra-fast workspace validation
    Returns: (is_valid, sanitized_data)
    """
    if not isinstance(data, dict):
        return False, {}

    # Just pass through with basic type checks
    result = {}

    if "files" in data:
        files = data["files"]
        if isinstance(files, list) and len(files) <= 100:
            result["files"] = files

    if "code" in data:
        code = data["code"]
        if isinstance(code, str) and len(code) <= 50000:
            result["code"] = code

    if "language" in data:
        lang = data["language"]
        if isinstance(lang, str):
            result["language"] = lang

    return True, result


def scan_secrets_ultrafast(text: str) -> str:
    """
    Ultra-fast secrets scanning using simple string operations
    Returns: redacted text
    """
    if not text or len(text) < 20:
        return text

    # Quick check for indicators
    text_lower = text.lower()
    has_secrets = False
    for indicator in SECRET_INDICATORS:
        if indicator in text_lower:
            has_secrets = True
            break

    if not has_secrets:
        return text

    # Simple redaction for common patterns
    # Only redact obvious patterns, not comprehensive
    if "sk-" in text:
        # OpenAI keys
        import re

        text = re.sub(r"sk-[a-zA-Z0-9]{48}", "[REDACTED_KEY]", text)

    if "password" in text_lower:
        # Simple password redaction
        import re

        text = re.sub(
            r'password\s*=\s*["\'][^"\']+["\']',
            'password="[REDACTED]"',
            text,
            flags=re.IGNORECASE,
        )

    if "ghp_" in text:
        # GitHub tokens
        import re

        text = re.sub(r"ghp_[a-zA-Z0-9]{36}", "[REDACTED_GITHUB_TOKEN]", text)

    return text


async def check_rate_limit_ultrafast(user_id: Optional[str] = None) -> bool:
    """
    Ultra-fast rate limiting with minimal overhead
    Returns: True if allowed, False if rate limited
    """
    global _global_rate_limiter_tokens, _global_rate_limiter_last

    async with _global_rate_limiter_lock:
        now = time.time()
        elapsed = now - _global_rate_limiter_last

        # Refill tokens (1 per second)
        if elapsed > 0:
            _global_rate_limiter_tokens = min(10, _global_rate_limiter_tokens + elapsed)
            _global_rate_limiter_last = now

        # Check tokens
        if _global_rate_limiter_tokens >= 1:
            _global_rate_limiter_tokens -= 1
            return True

        return False


def check_file_access_ultrafast(file_path: str) -> bool:
    """
    Ultra-fast file access check
    Returns: True if allowed, False otherwise
    """
    if not file_path:
        return False

    # Quick dangerous path check
    path_lower = file_path.lower()
    for restricted in RESTRICTED_PATHS:
        if restricted in path_lower:
            return False

    # Quick extension check
    if "." in file_path:
        ext = file_path[file_path.rfind(".") :]
        if ext.lower() not in ALLOWED_EXTENSIONS:
            return False

    return True


def apply_ultrafast_patches():
    """Apply ultra-fast security patches with <10% overhead"""
    try:
        import vibe_check.mentor.mcp_sampling as original

        # Ultra-fast wrapper for generate_dynamic_response
        original_generate = (
            original.MCPSamplingClient.generate_dynamic_response
            if hasattr(original, "MCPSamplingClient")
            else None
        )

        if original_generate:

            async def ultrafast_generate_dynamic_response(
                self,
                intent: str,
                query: str,
                context: Dict[str, Any],
                workspace_data: Optional[Dict[str, Any]] = None,
                ctx: Optional[Any] = None,
                user_id: Optional[str] = None,
            ):
                """Ultra-fast security wrapper"""

                # Ultra-fast rate limit check
                if not await check_rate_limit_ultrafast(user_id):
                    return {
                        "content": "Rate limit exceeded",
                        "generated": False,
                        "rate_limited": True,
                    }

                # Ultra-fast query validation
                is_valid, sanitized = validate_query_ultrafast(query, intent)
                if not is_valid:
                    return None

                # Ultra-fast workspace validation
                if workspace_data:
                    is_valid, sanitized_ws = validate_workspace_ultrafast(
                        workspace_data
                    )
                    if is_valid:
                        workspace_data = sanitized_ws
                        # Ultra-fast secrets scan
                        if "code" in workspace_data:
                            workspace_data["code"] = scan_secrets_ultrafast(
                                workspace_data["code"]
                            )

                # Call original
                return await original_generate(
                    self, intent, sanitized["query"], context, workspace_data, ctx
                )

            original.MCPSamplingClient.generate_dynamic_response = (
                ultrafast_generate_dynamic_response
            )

        # Ultra-fast sanitize
        def ultrafast_sanitize(code: str, max_length: int = 2000) -> str:
            if not code:
                return ""

            # Quick scan and truncate
            code = scan_secrets_ultrafast(code)

            if len(code) > max_length:
                code = code[:max_length] + "..."

            return code

        original.sanitize_code_for_llm = ultrafast_sanitize

        return True

    except Exception as e:
        return False


# Export ultrafast components
__all__ = [
    "validate_query_ultrafast",
    "validate_workspace_ultrafast",
    "scan_secrets_ultrafast",
    "check_rate_limit_ultrafast",
    "check_file_access_ultrafast",
    "apply_ultrafast_patches",
]
