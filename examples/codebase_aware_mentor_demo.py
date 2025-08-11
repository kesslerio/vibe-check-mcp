#!/usr/bin/env python3
"""
Demo: Codebase-Aware Vibe Check Mentor

This demo shows how vibe_check_mentor can now analyze actual code files
instead of making assumptions about your implementation.

Features demonstrated:
1. Reading actual code files securely
2. Referencing specific lines and functions
3. Context persistence across multiple calls
4. Smart extraction of relevant code sections
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vibe_check.tools.vibe_mentor import get_mentor_engine
from vibe_check.mentor.context_manager import get_context_cache


def create_sample_files(temp_dir):
    """Create sample code files for demonstration"""
    
    # Sample Python file with potential issues
    api_client = temp_dir / "api_client.py"
    api_client.write_text("""
import requests
import json
from typing import Optional, Dict, Any

class CustomAPIClient:
    '''Custom HTTP client for our API instead of using official SDK'''
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
    def _create_session(self):
        # TODO: Add retry logic
        # FIXME: No connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def fetch_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        '''Fetch data from API endpoint'''
        if not self.session:
            self._create_session()
        
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params)
        
        # No error handling!
        return response.json()
    
    def post_data(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        '''Post data to API endpoint'''
        if not self.session:
            self._create_session()
        
        url = f"{self.base_url}/{endpoint}"
        response = self.session.post(url, json=data)
        
        return response.json()

# Usage
client = CustomAPIClient("api_key_123", "https://api.example.com")
result = client.fetch_data("users")
""")
    
    # Sample auth implementation
    auth_system = temp_dir / "auth_system.py"
    auth_system.write_text("""
import hashlib
import secrets
from datetime import datetime, timedelta

class CustomAuthSystem:
    '''Yet another custom authentication system'''
    
    def __init__(self):
        self.users = {}
        self.sessions = {}
        
    def hash_password(self, password: str) -> str:
        # Using MD5 - security issue!
        return hashlib.md5(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str):
        '''Create a new user'''
        if username in self.users:
            raise ValueError("User already exists")
        
        self.users[username] = {
            'password_hash': self.hash_password(password),
            'created_at': datetime.now()
        }
    
    def authenticate(self, username: str, password: str) -> str:
        '''Authenticate user and return session token'''
        if username not in self.users:
            return None
        
        if self.users[username]['password_hash'] == self.hash_password(password):
            token = secrets.token_hex(16)
            self.sessions[token] = {
                'username': username,
                'expires_at': datetime.now() + timedelta(hours=1)
            }
            return token
        
        return None
    
    def validate_token(self, token: str) -> bool:
        '''Check if token is valid'''
        if token not in self.sessions:
            return False
        
        # No expiry check!
        return True
""")
    
    return [str(api_client), str(auth_system)]


def demo_basic_analysis():
    """Demo: Basic analysis without file context"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Analysis (Without File Context)")
    print("="*60)
    
    engine = get_mentor_engine()
    
    # Create a session and ask about API integration
    session = engine.create_session(
        topic="Should I build a custom HTTP client for the API?",
        session_id="demo-basic"
    )
    
    # Simulate pattern detection
    detected_patterns = [
        {
            "pattern_type": "infrastructure_without_implementation",
            "confidence": 0.85,
            "description": "Building custom HTTP client instead of using SDK"
        }
    ]
    
    # Get contribution from senior engineer persona
    contribution = engine.generate_contribution(
        session=session,
        persona=session.personas[0],  # Senior engineer
        detected_patterns=detected_patterns,
        context="We need to integrate with a third-party API"
    )
    
    print(f"\nPersona: {session.personas[0].name}")
    print(f"Response Type: {contribution.type}")
    print(f"Confidence: {contribution.confidence}")
    print(f"\nAdvice:\n{contribution.content}")


def demo_codebase_aware():
    """Demo: Analysis with actual code files"""
    print("\n" + "="*60)
    print("DEMO 2: Codebase-Aware Analysis (With Actual Files)")
    print("="*60)
    
    # Create temporary directory with sample files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_paths = create_sample_files(temp_path)
        
        print(f"\nCreated sample files:")
        for fp in file_paths:
            print(f"  - {Path(fp).name}")
        
        # Get context cache and mentor engine
        cache = get_context_cache()
        engine = get_mentor_engine()
        
        # Load files into context
        session_id = "demo-codebase-aware"
        file_contexts, errors = cache.add_files_to_session(
            session_id=session_id,
            file_paths=file_paths,
            working_directory=temp_dir,
            query="API client implementation authentication"
        )
        
        print(f"\nLoaded {len(file_contexts)} files successfully")
        
        # Show what was extracted
        for fc in file_contexts:
            print(f"\n  File: {Path(fc.path).name}")
            print(f"    - Classes: {', '.join(fc.classes)}")
            print(f"    - Functions: {', '.join(fc.functions[:5])}")
            if fc.relevant_lines.get('potential_issues'):
                print(f"    - Issues found: {len(fc.relevant_lines['potential_issues'])}")
                for line_num, line in fc.relevant_lines['potential_issues'][:2]:
                    print(f"      Line {line_num}: {line.strip()}")
        
        # Create session with topic
        session = engine.create_session(
            topic="Review our custom API client and auth system implementation",
            session_id=session_id
        )
        
        # Detect patterns in the actual code
        detected_patterns = [
            {
                "pattern_type": "infrastructure_without_implementation",
                "confidence": 0.95,
                "description": "Custom HTTP client (CustomAPIClient) instead of official SDK",
                "file": "api_client.py",
                "line": 6
            },
            {
                "pattern_type": "security_vulnerability",
                "confidence": 0.99,
                "description": "Using MD5 for password hashing",
                "file": "auth_system.py",
                "line": 14
            }
        ]
        
        # Generate contribution with file context
        print("\n" + "-"*60)
        print("Senior Engineer Analysis (With Code Context):")
        print("-"*60)
        
        contribution = engine.generate_contribution(
            session=session,
            persona=session.personas[0],  # Senior engineer
            detected_patterns=detected_patterns,
            context="Review implementation for production readiness",
            file_contexts=file_contexts
        )
        
        print(f"\nResponse Type: {contribution.type}")
        print(f"Confidence: {contribution.confidence}")
        print(f"\nAdvice:\n{contribution.content}")
        
        # The response should now reference specific code!
        if "CustomAPIClient" in contribution.content or "MD5" in contribution.content:
            print("\n✅ Success: The mentor referenced actual code from the files!")
        else:
            print("\n⚠️  The mentor provided generic advice without code references")


def demo_session_persistence():
    """Demo: Context persistence across multiple calls"""
    print("\n" + "="*60)
    print("DEMO 3: Session Persistence (Multiple Calls)")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_paths = create_sample_files(temp_path)
        
        cache = get_context_cache()
        engine = get_mentor_engine()
        session_id = "demo-persistence"
        
        # First call - load files
        print("\nFirst call: Loading files...")
        file_contexts, _ = cache.add_files_to_session(
            session_id=session_id,
            file_paths=file_paths,
            working_directory=temp_dir,
            query="API implementation"
        )
        print(f"Loaded {len(file_contexts)} files")
        
        # Check cache stats
        stats = cache.get_stats()
        print(f"\nCache stats after first call:")
        print(f"  - Sessions: {stats['sessions']}")
        print(f"  - Total files: {stats['total_files']}")
        print(f"  - Total size: {stats['total_size_mb']} MB")
        
        # Second call - files should be cached
        print("\nSecond call: Using cached context...")
        session_context = cache.get_session_context(session_id)
        if session_context:
            print(f"✅ Session found with {len(session_context.files)} cached files")
            
            # Try to add same files again - should use cache
            file_contexts2, _ = cache.add_files_to_session(
                session_id=session_id,
                file_paths=file_paths,
                working_directory=temp_dir,
                query="authentication security"
            )
            print(f"Files returned from cache: {len(file_contexts2)}")
        else:
            print("❌ Session not found in cache")
        
        # Clean up
        cache.clear_session(session_id)
        print("\n✅ Session cleared from cache")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("CODEBASE-AWARE VIBE CHECK MENTOR DEMO")
    print("="*60)
    print("\nThis demo shows the new codebase-aware features:")
    print("1. Secure file reading with path validation")
    print("2. Smart context extraction from code")
    print("3. Session-based caching for performance")
    print("4. Referencing actual code in responses")
    
    # Run demos
    demo_basic_analysis()
    demo_codebase_aware()
    demo_session_persistence()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nThe vibe_check_mentor now:")
    print("✅ Reads actual code files securely")
    print("✅ References specific lines and functions")
    print("✅ Maintains context across multiple calls")
    print("✅ Provides code-specific recommendations")
    print("\nUsage in MCP:")
    print('vibe_check_mentor(')
    print('    query="Should I use this custom auth?",')
    print('    file_paths=["auth_system.py", "api_client.py"],')
    print('    working_directory="/path/to/project"')
    print(')')


if __name__ == "__main__":
    main()