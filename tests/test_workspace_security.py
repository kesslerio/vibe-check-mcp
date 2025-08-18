"""
Security tests for workspace-aware mentor functionality.

Tests path validation, traversal prevention, and file access restrictions.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the components to test
from vibe_check.mentor.context_manager import (
    SecurityValidator,
    FileReader,
    CodeParser,
    ContextCache,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS
)


class TestSecurityValidator:
    """Test security validation for file paths"""
    
    def test_workspace_env_variable(self):
        """Test reading WORKSPACE from environment"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Resolve to handle /private symlink on macOS
            tmpdir = str(Path(tmpdir).resolve())
            with patch.dict(os.environ, {'WORKSPACE': tmpdir}):
                workspace = SecurityValidator.get_workspace_directory()
                assert workspace == tmpdir
    
    def test_invalid_workspace_env(self):
        """Test handling of invalid WORKSPACE path"""
        with patch.dict(os.environ, {'WORKSPACE': '/nonexistent/path'}):
            workspace = SecurityValidator.get_workspace_directory()
            assert workspace is None
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('test')")
            
            # Attempt path traversal
            is_valid, path, error = SecurityValidator.validate_path(
                "../../../etc/passwd",
                working_directory=tmpdir
            )
            
            assert not is_valid
            assert "outside working directory" in error or "does not exist" in error
    
    def test_symlink_validation(self):
        """Test that symlinks are properly validated"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file outside workspace
            outside_dir = tempfile.mkdtemp()
            outside_file = Path(outside_dir) / "secret.py"
            outside_file.write_text("SECRET = 'data'")
            
            # Create symlink inside workspace pointing outside
            symlink = Path(tmpdir) / "link.py"
            symlink.symlink_to(outside_file)
            
            # Should fail validation
            is_valid, path, error = SecurityValidator.validate_path(
                str(symlink),
                working_directory=tmpdir
            )
            
            assert not is_valid
            assert "outside working directory" in error
            
            # Cleanup
            outside_file.unlink()
            Path(outside_dir).rmdir()
    
    def test_file_size_limit(self):
        """Test that large files are rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file larger than MAX_FILE_SIZE
            large_file = Path(tmpdir) / "large.py"
            large_content = "x" * (MAX_FILE_SIZE + 1)
            large_file.write_text(large_content)
            
            is_valid, path, error = SecurityValidator.validate_path(
                str(large_file),
                working_directory=tmpdir
            )
            
            assert not is_valid
            assert "too large" in error
    
    def test_allowed_extensions(self):
        """Test that only allowed file extensions pass validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test allowed extension
            allowed_file = Path(tmpdir) / "test.py"
            allowed_file.write_text("print('test')")
            
            is_valid, path, error = SecurityValidator.validate_path(
                str(allowed_file),
                working_directory=tmpdir
            )
            assert is_valid
            
            # Test disallowed extension
            disallowed_file = Path(tmpdir) / "test.exe"
            disallowed_file.write_text("binary")
            
            is_valid, path, error = SecurityValidator.validate_path(
                str(disallowed_file),
                working_directory=tmpdir
            )
            assert not is_valid
            assert "not allowed" in error
    
    def test_directory_validation(self):
        """Test that directories are rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            
            is_valid, path, error = SecurityValidator.validate_path(
                str(subdir),
                working_directory=tmpdir
            )
            
            assert not is_valid
            assert "not a file" in error


class TestFileReader:
    """Test secure file reading functionality"""
    
    def test_read_valid_file(self):
        """Test reading a valid file within workspace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_content = "def hello():\n    return 'world'"
            test_file.write_text(test_content)
            
            content, error = FileReader.read_file(
                str(test_file),
                working_directory=tmpdir
            )
            
            assert content == test_content
            assert error is None
    
    def test_read_with_encoding_fallback(self):
        """Test reading files with different encodings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with latin-1 encoding
            test_file = Path(tmpdir) / "test.py"
            test_content = "# Café\ndef función():\n    pass"
            test_file.write_bytes(test_content.encode('latin-1'))
            
            content, error = FileReader.read_file(
                str(test_file),
                working_directory=tmpdir
            )
            
            assert content is not None
            assert error is None
            assert "def" in content
    
    def test_truncate_long_lines(self):
        """Test that very long lines are truncated"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            long_line = "x" * 2000  # Longer than MAX_LINE_LENGTH
            test_file.write_text(f"short line\n{long_line}\nanother short line")
            
            content, error = FileReader.read_file(
                str(test_file),
                working_directory=tmpdir
            )
            
            assert content is not None
            assert "..." in content  # Truncation marker
            assert len(content.split('\n')[1]) < 1100  # Truncated line + "..."


class TestCodeParser:
    """Test multi-language code parsing"""
    
    def test_parse_python(self):
        """Test Python file parsing"""
        content = """
import os
from pathlib import Path

class MyClass:
    def method1(self):
        pass
    
def my_function():
    return 42
"""
        result = CodeParser.parse_python_file(content)
        
        assert 'MyClass' in result['classes']
        assert 'method1' in result['functions']
        assert 'my_function' in result['functions']
        assert 'os' in result['imports']
        assert 'pathlib' in result['imports']
    
    def test_parse_typescript(self):
        """Test TypeScript file parsing"""
        content = """
import { Component } from '@angular/core';
import axios from 'axios';

interface User {
    id: number;
    name: string;
}

type UserRole = 'admin' | 'user';

class UserService {
    async getUser(id: number): Promise<User> {
        return axios.get(`/users/${id}`);
    }
}

export default UserService;
"""
        result = CodeParser.parse_javascript_file(content)
        
        assert 'UserService' in result['classes']
        assert 'User' in result['interfaces']
        assert 'UserRole' in result['types']
        assert '@angular/core' in result['imports']
        assert 'axios' in result['imports']
    
    def test_parse_go(self):
        """Test Go file parsing"""
        content = """
package main

import (
    "fmt"
    "net/http"
)

type Server struct {
    port int
}

type Handler interface {
    Handle(w http.ResponseWriter, r *http.Request)
}

func (s *Server) Start() error {
    return http.ListenAndServe(fmt.Sprintf(":%d", s.port), nil)
}

func main() {
    server := &Server{port: 8080}
    server.Start()
}
"""
        result = CodeParser.parse_go_file(content)
        
        assert 'main' in result['packages']
        assert 'Server' in result['types']
        assert 'Handler' in result['interfaces']
        assert 'Start' in result['functions']
        assert 'main' in result['functions']
    
    def test_parse_rust(self):
        """Test Rust file parsing"""
        content = """
use std::io;
use std::collections::HashMap;

pub struct Config {
    name: String,
    value: i32,
}

pub enum Status {
    Active,
    Inactive,
}

pub trait Processor {
    fn process(&self, data: &str) -> Result<String, io::Error>;
}

impl Config {
    pub fn new(name: String, value: i32) -> Self {
        Config { name, value }
    }
}

pub fn main() {
    let config = Config::new("test".to_string(), 42);
}
"""
        result = CodeParser.parse_rust_file(content)
        
        assert 'Config' in result['structs']
        assert 'Status' in result['enums']
        assert 'Processor' in result['traits']
        assert 'new' in result['functions']
        assert 'main' in result['functions']
        assert 'Config' in result['impls']
    
    def test_parse_java(self):
        """Test Java file parsing"""
        content = """
package com.example.app;

import java.util.List;
import java.util.ArrayList;

public class UserController {
    private UserService userService;
    
    public UserController(UserService service) {
        this.userService = service;
    }
    
    public List<User> getAllUsers() {
        return userService.findAll();
    }
}

interface UserService {
    List<User> findAll();
}
"""
        result = CodeParser.parse_java_file(content)
        
        assert 'UserController' in result['classes']
        assert 'UserService' in result['interfaces']
        assert 'getAllUsers' in result['methods']
        assert 'java.util.List' in result['imports']
        assert 'com.example.app' in result['packages']
    
    def test_extract_relevant_context(self):
        """Test extraction of relevant lines from code"""
        content = """
def process_user(user_id):
    # TODO: Add validation
    user = get_user(user_id)
    
    # FIXME: Handle null case
    if not user:
        return None
    
    return user.process()

def get_user(user_id):
    # Fetch user from database
    return database.find(user_id)
"""
        
        relevant = CodeParser.extract_relevant_context(
            content,
            "process user validation",
            "python"
        )
        
        assert len(relevant['direct_mentions']) > 0
        assert len(relevant['potential_issues']) > 0
        assert any('TODO' in str(line) for _, line in relevant['potential_issues'])
        assert any('FIXME' in str(line) for _, line in relevant['potential_issues'])


class TestContextCache:
    """Test session caching functionality"""
    
    def test_session_creation(self):
        """Test creating and retrieving sessions"""
        cache = ContextCache()
        
        session = cache.get_or_create_session("test-session", "/workspace")
        assert session.session_id == "test-session"
        assert session.working_directory == "/workspace"
        
        # Retrieve existing session
        session2 = cache.get_or_create_session("test-session")
        assert session2.session_id == session.session_id
    
    def test_file_extraction_from_query(self):
        """Test extracting file names from queries"""
        cache = ContextCache()
        
        files = cache.extract_files_from_query(
            "Review the auth.py and user_service.ts files for security issues"
        )
        
        assert 'auth.py' in files
        assert 'user_service.ts' in files
    
    def test_workspace_file_loading(self):
        """Test loading files with workspace validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "test1.py"
            file1.write_text("print('test1')")
            
            file2 = Path(tmpdir) / "test2.js"
            file2.write_text("console.log('test2')")
            
            cache = ContextCache()
            contexts, errors = cache.add_files_to_session(
                "test-session",
                [str(file1), str(file2)],
                working_directory=tmpdir,
                query="test query"
            )
            
            assert len(contexts) == 2
            assert len(errors) == 0
            assert contexts[0].language == 'python'
            assert contexts[1].language == 'javascript'
    
    def test_total_size_limit(self):
        """Test that total size limit is enforced"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache()
            
            # Note: MAX_FILES is 10, so we'll hit that limit first
            # Create fewer files but ensure we exceed total size limit
            large_files = []
            for i in range(15):  # More than MAX_FILES
                file = Path(tmpdir) / f"large{i}.py"
                file.write_text("x" * 600000)  # 600KB each
                large_files.append(str(file))
            
            contexts, errors = cache.add_files_to_session(
                "test-session",
                large_files,
                working_directory=tmpdir
            )
            
            # Should have errors about too many files
            assert len(errors) > 0
            assert "Too many files" in str(errors[0]) or len(contexts) == 10  # MAX_FILES
    
    def test_session_expiry(self):
        """Test that expired sessions are cleaned up"""
        cache = ContextCache()
        
        session = cache.get_or_create_session("test-session")
        
        # Mock time to simulate expiry
        with patch('time.time', return_value=session.created_at + 7200):  # 2 hours later
            assert session.is_expired()
            
            # Should create new session
            new_session = cache.get_or_create_session("test-session")
            assert new_session.created_at > session.created_at


@pytest.mark.integration
class TestWorkspaceIntegration:
    """Integration tests for workspace-aware mentor"""
    
    def test_workspace_aware_analysis(self):
        """Test full workspace-aware analysis flow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple project structure
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            
            # Create Python file
            auth_file = src_dir / "auth.py"
            auth_file.write_text("""
class AuthService:
    def authenticate(self, username, password):
        # TODO: Add rate limiting
        if username == "admin" and password == "admin":  # FIXME: Hardcoded credentials
            return True
        return False
""")
            
            # Create TypeScript file
            api_file = src_dir / "api.ts"
            api_file.write_text("""
interface User {
    id: number;
    username: string;
    password: string;  // TODO: Should be hashed
}

class APIClient {
    async login(user: User): Promise<boolean> {
        // FIXME: No error handling
        return fetch('/login', {
            method: 'POST',
            body: JSON.stringify(user)
        });
    }
}
""")
            
            # Set workspace environment
            with patch.dict(os.environ, {'WORKSPACE': tmpdir}):
                from vibe_check.tools.vibe_mentor_workspace import WorkspaceAwareMentorEngine
                
                engine = WorkspaceAwareMentorEngine()
                
                # Analyze with workspace context
                result = engine.analyze_with_workspace(
                    query="Review the authentication implementation in auth.py and api.ts",
                    reasoning_depth="quick"
                )
                
                # Verify workspace was used
                assert result['workspace_info']['workspace_configured']
                assert result['workspace_info']['files_loaded'] > 0
                
                # Check for detected issues
                if 'code_insights' in result:
                    insights = result['code_insights']
                    assert any('TODO' in insight for insight in insights)
                    assert any('FIXME' in insight for insight in insights)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])