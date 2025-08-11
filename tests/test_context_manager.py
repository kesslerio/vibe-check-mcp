"""
Tests for the Context Manager module - Codebase-aware vibe_check_mentor

Tests security, caching, file reading, and context extraction functionality.
"""

import os
import time
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from vibe_check.mentor.context_manager import (
    SecurityValidator,
    FileReader,
    CodeParser,
    ContextCache,
    FileContext,
    SessionContext,
    get_context_cache,
    reset_context_cache,
    MAX_FILE_SIZE,
    CACHE_TTL_SECONDS
)


class TestSecurityValidator:
    """Test path validation and security features"""
    
    def test_validate_absolute_path(self, tmp_path):
        """Test validation of absolute paths"""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        # Should validate successfully
        is_valid, resolved_path, error = SecurityValidator.validate_path(str(test_file))
        assert is_valid
        assert resolved_path == str(test_file)
        assert error is None
    
    def test_validate_relative_path(self, tmp_path):
        """Test validation of relative paths with working directory"""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        # Use relative path
        is_valid, resolved_path, error = SecurityValidator.validate_path(
            "test.py", 
            working_directory=str(tmp_path)
        )
        assert is_valid
        assert Path(resolved_path) == test_file
        assert error is None
    
    def test_prevent_path_traversal(self, tmp_path):
        """Test prevention of path traversal attacks"""
        # Create a file outside the working directory
        parent_dir = tmp_path.parent
        outside_file = parent_dir / "outside.py"
        outside_file.write_text("secret")
        
        # Try to access file outside working directory using path traversal
        is_valid, resolved_path, error = SecurityValidator.validate_path(
            "../outside.py",
            working_directory=str(tmp_path)
        )
        assert not is_valid
        assert "outside working directory" in error
    
    def test_reject_non_existent_file(self):
        """Test rejection of non-existent files"""
        is_valid, resolved_path, error = SecurityValidator.validate_path("/non/existent/file.py")
        assert not is_valid
        assert "does not exist" in error
    
    def test_reject_directory(self, tmp_path):
        """Test rejection of directories (not files)"""
        is_valid, resolved_path, error = SecurityValidator.validate_path(str(tmp_path))
        assert not is_valid
        assert "not a file" in error
    
    def test_reject_invalid_extension(self, tmp_path):
        """Test rejection of files with invalid extensions"""
        test_file = tmp_path / "test.exe"
        test_file.write_text("malicious")
        
        is_valid, resolved_path, error = SecurityValidator.validate_path(str(test_file))
        assert not is_valid
        assert "not allowed" in error
    
    def test_reject_large_file(self, tmp_path):
        """Test rejection of files exceeding size limit"""
        test_file = tmp_path / "large.py"
        # Create a file larger than MAX_FILE_SIZE
        test_file.write_text("x" * (MAX_FILE_SIZE + 1))
        
        is_valid, resolved_path, error = SecurityValidator.validate_path(str(test_file))
        assert not is_valid
        assert "too large" in error


class TestFileReader:
    """Test secure file reading functionality"""
    
    def test_read_valid_file(self, tmp_path):
        """Test reading a valid file"""
        test_file = tmp_path / "test.py"
        content = "def hello():\n    print('world')"
        test_file.write_text(content)
        
        result, error = FileReader.read_file(str(test_file))
        assert result == content
        assert error is None
    
    def test_read_with_encoding_fallback(self, tmp_path):
        """Test reading files with different encodings"""
        test_file = tmp_path / "test.py"
        # Write file with latin-1 encoding
        test_file.write_bytes("café".encode('latin-1'))
        
        result, error = FileReader.read_file(str(test_file))
        assert result is not None
        assert error is None
    
    def test_truncate_long_lines(self, tmp_path):
        """Test truncation of very long lines"""
        test_file = tmp_path / "test.py"
        long_line = "x" * 2000  # Exceeds MAX_LINE_LENGTH
        test_file.write_text(f"short line\n{long_line}\nanother short line")
        
        result, error = FileReader.read_file(str(test_file))
        assert result is not None
        assert "..." in result  # Long line should be truncated
        assert error is None
    
    def test_handle_invalid_path(self):
        """Test handling of invalid file paths"""
        result, error = FileReader.read_file("/non/existent/file.py")
        assert result is None
        assert error is not None


class TestCodeParser:
    """Test code parsing and context extraction"""
    
    def test_parse_python_file(self):
        """Test parsing Python file structure"""
        content = """
import os
from typing import List

class MyClass:
    '''A test class'''
    
    def method1(self):
        pass
    
    def method2(self):
        pass

def standalone_function():
    '''A standalone function'''
    return 42

async def async_function():
    pass
"""
        result = CodeParser.parse_python_file(content)
        
        assert "MyClass" in result['classes']
        assert "method1" in result['functions']
        assert "method2" in result['functions']
        assert "standalone_function" in result['functions']
        assert "async_function" in result['functions']
        assert "os" in result['imports']
        assert "typing" in result['imports']
        assert 'class:MyClass' in result['docstrings']
        assert 'func:standalone_function' in result['docstrings']
    
    def test_parse_python_with_syntax_error(self):
        """Test parsing Python file with syntax errors (fallback to regex)"""
        content = """
class MyClass
    def broken_method(
        pass

def valid_function():
    return 42
"""
        result = CodeParser.parse_python_file(content)
        
        # Should still extract what it can using regex
        assert "MyClass" in result['classes']
        assert "valid_function" in result['functions']
    
    def test_parse_javascript_file(self):
        """Test parsing JavaScript/TypeScript file structure"""
        content = """
import React from 'react';
import { useState } from 'react';

export class MyComponent {
    render() {
        return null;
    }
}

const myFunction = () => {
    console.log('hello');
};

function traditionalFunction() {
    return 42;
}

export default MyComponent;
"""
        result = CodeParser.parse_javascript_file(content)
        
        assert "MyComponent" in result['classes']
        assert "myFunction" in result['functions']
        assert "traditionalFunction" in result['functions']
        assert "react" in result['imports']
        assert "MyComponent" in result['exports']
    
    def test_extract_relevant_context(self):
        """Test extraction of relevant lines from code"""
        content = """
def process_data(input_data):
    # TODO: Add validation
    result = transform(input_data)
    return result

def transform(data):
    # Process the data transformation
    return data.upper()

class DataProcessor:
    def __init__(self):
        self.data = None
    
    def process(self, input_data):
        # FIXME: Handle edge cases
        return transform(input_data)
"""
        query = "process data transformation"
        relevant = CodeParser.extract_relevant_context(content, query, 'python')
        
        # Should find mentions of query terms
        assert len(relevant['direct_mentions']) > 0
        assert any('process' in line[1].lower() for line in relevant['direct_mentions'])
        
        # Should find TODOs and FIXMEs
        assert len(relevant['potential_issues']) > 0
        assert any('TODO' in line[1] or 'FIXME' in line[1] for line in relevant['potential_issues'])


class TestContextCache:
    """Test session-based context caching"""
    
    def test_create_session(self):
        """Test creating a new session"""
        cache = ContextCache()
        session = cache.get_or_create_session("test-session", "/test/dir")
        
        assert session.session_id == "test-session"
        assert session.working_directory == "/test/dir"
        assert len(session.files) == 0
        assert session.total_size == 0
    
    def test_retrieve_existing_session(self):
        """Test retrieving an existing session"""
        cache = ContextCache()
        session1 = cache.get_or_create_session("test-session")
        session2 = cache.get_or_create_session("test-session")
        
        assert session1 is session2
    
    def test_add_files_to_session(self, tmp_path):
        """Test adding files to a session"""
        cache = ContextCache()
        
        # Create test files
        file1 = tmp_path / "file1.py"
        file1.write_text("def function1(): pass")
        file2 = tmp_path / "file2.py"
        file2.write_text("class MyClass: pass")
        
        # Add files to session
        contexts, errors = cache.add_files_to_session(
            "test-session",
            [str(file1), str(file2)],
            working_directory=str(tmp_path),
            query="function class"
        )
        
        assert len(contexts) == 2
        assert len(errors) == 0
        assert contexts[0].functions == ["function1"]
        assert contexts[1].classes == ["MyClass"]
    
    def test_file_caching(self, tmp_path):
        """Test that files are cached and not re-read"""
        cache = ContextCache()
        
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")
        
        # Add file to session
        contexts1, _ = cache.add_files_to_session(
            "test-session",
            [str(test_file)],
            working_directory=str(tmp_path)
        )
        
        # Modify file on disk
        test_file.write_text("modified content")
        
        # Add same file again - should return cached version
        contexts2, _ = cache.add_files_to_session(
            "test-session",
            [str(test_file)],
            working_directory=str(tmp_path)
        )
        
        assert contexts1[0].content == contexts2[0].content
        assert contexts1[0].content == "original content"
    
    def test_session_expiry(self):
        """Test that expired sessions are cleaned up"""
        cache = ContextCache()
        
        # Create session
        session = cache.get_or_create_session("test-session")
        
        # Mock time to simulate expiry
        with patch('time.time', return_value=time.time() + CACHE_TTL_SECONDS + 1):
            assert session.is_expired()
            
            # Try to get session - should return None
            retrieved = cache.get_session_context("test-session")
            assert retrieved is None
    
    def test_max_files_limit(self, tmp_path):
        """Test enforcement of maximum files limit"""
        cache = ContextCache()
        
        # Create more files than allowed
        files = []
        for i in range(15):  # More than MAX_FILES
            file = tmp_path / f"file{i}.py"
            file.write_text(f"# File {i}")
            files.append(str(file))
        
        contexts, errors = cache.add_files_to_session(
            "test-session",
            files,
            working_directory=str(tmp_path)
        )
        
        # Should only load up to MAX_FILES
        assert len(contexts) <= 10  # MAX_FILES
        assert len(errors) > 0
        assert "Too many files" in errors[0]
    
    def test_total_size_limit(self, tmp_path):
        """Test enforcement of total size limit"""
        cache = ContextCache()
        
        # Create multiple files that total over 5MB when encoded
        # Each file should be under 1MB individually but together exceed 5MB
        files = []
        for i in range(6):
            large_file = tmp_path / f"large{i}.py"
            # Create ~900KB of actual content (under 1MB limit)
            lines = ["x" * 100 for _ in range(9000)]  # ~900KB of content
            large_file.write_text("\n".join(lines))
            files.append(str(large_file))
        
        contexts, errors = cache.add_files_to_session(
            "test-session",
            files,
            working_directory=str(tmp_path)
        )
        
        # Should stop before exceeding total size limit (5MB)
        # 6 files * 900KB = 5.4MB, so should only load 5 files
        assert len(contexts) <= 5  # At most 5 files
        if len(contexts) < 6:
            assert len(errors) > 0
            assert any("size limit" in e for e in errors)
    
    def test_cache_stats(self, tmp_path):
        """Test cache statistics"""
        cache = ContextCache()
        
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("content")
        
        # Add to multiple sessions with working directory
        cache.add_files_to_session("session1", [str(test_file)], working_directory=str(tmp_path))
        cache.add_files_to_session("session2", [str(test_file)], working_directory=str(tmp_path))
        
        stats = cache.get_stats()
        assert stats['sessions'] == 2
        assert stats['total_files'] == 2
        assert stats['total_size_bytes'] > 0
    
    def test_clear_session(self):
        """Test clearing a specific session"""
        cache = ContextCache()
        cache.get_or_create_session("session1")
        cache.get_or_create_session("session2")
        
        cache.clear_session("session1")
        
        assert cache.get_session_context("session1") is None
        assert cache.get_session_context("session2") is not None
    
    def test_clear_all(self):
        """Test clearing all sessions"""
        cache = ContextCache()
        cache.get_or_create_session("session1")
        cache.get_or_create_session("session2")
        
        cache.clear_all()
        
        assert cache.get_session_context("session1") is None
        assert cache.get_session_context("session2") is None


class TestGlobalCache:
    """Test global cache instance management"""
    
    def test_get_context_cache_singleton(self):
        """Test that get_context_cache returns singleton"""
        cache1 = get_context_cache()
        cache2 = get_context_cache()
        assert cache1 is cache2
    
    def test_reset_context_cache(self):
        """Test resetting the global cache"""
        cache1 = get_context_cache()
        cache1.get_or_create_session("test")
        
        reset_context_cache()
        
        cache2 = get_context_cache()
        assert cache1 is not cache2
        assert cache2.get_session_context("test") is None


class TestIntegration:
    """Integration tests for the complete flow"""
    
    def test_complete_flow(self, tmp_path):
        """Test the complete flow from file reading to context extraction"""
        # Create a test Python file with various elements
        test_file = tmp_path / "example.py"
        test_file.write_text("""
import requests
from typing import Optional

class APIClient:
    '''Client for external API'''
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def fetch_data(self, endpoint: str) -> dict:
        # TODO: Add retry logic
        response = requests.get(endpoint)
        return response.json()

def process_api_response(data: dict) -> Optional[str]:
    '''Process API response data'''
    if 'result' in data:
        return data['result']
    return None
""")
        
        # Initialize cache and add file
        cache = get_context_cache()
        contexts, errors = cache.add_files_to_session(
            "integration-test",
            [str(test_file)],
            working_directory=str(tmp_path),
            query="API fetch data"
        )
        
        # Verify results
        assert len(contexts) == 1
        assert len(errors) == 0
        
        file_context = contexts[0]
        assert "APIClient" in file_context.classes
        assert "fetch_data" in file_context.functions
        assert "process_api_response" in file_context.functions
        assert "requests" in file_context.imports
        
        # Check relevant lines were extracted
        assert len(file_context.relevant_lines['direct_mentions']) > 0
        assert len(file_context.relevant_lines['potential_issues']) > 0  # Should find TODO
        
        # Verify session persistence
        session = cache.get_session_context("integration-test")
        assert session is not None
        assert len(session.files) == 1
        
        # Clean up
        reset_context_cache()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])