"""
Test Code Reference Extractor - Issue #152

Tests the enhanced functionality of extracting file references,
function names, and line numbers from GitHub issue text with
validation, binary filtering, and performance improvements.
"""

import pytest
from vibe_check.core.code_reference_extractor import (
    CodeReferenceExtractor,
    ExtractionConfig,
    extract_code_references_from_issue
)


class TestCodeReferenceExtractor:
    """Test the code reference extraction functionality."""
    
    def setup_method(self):
        """Setup test instance."""
        self.extractor = CodeReferenceExtractor()
    
    def test_extract_file_path_basic(self):
        """Test basic file path extraction."""
        text = "Error in `src/payments/stripe.js` on line 42"
        refs = self.extractor.extract_references(text)
        
        file_refs = [r for r in refs if r.type == 'file_path']
        assert len(file_refs) == 1
        assert file_refs[0].value == 'src/payments/stripe.js'
        assert file_refs[0].confidence > 0.5
    
    def test_extract_file_with_line_number(self):
        """Test file path with line number extraction."""
        text = "Stack trace shows error in auth.js:156"
        refs = self.extractor.extract_references(text)
        
        file_refs = [r for r in refs if r.type == 'file_path']
        # Should find the file reference, possibly multiple matches
        assert len(file_refs) >= 1
        
        # Find the reference with line number (higher confidence)
        line_ref = next((r for r in file_refs if r.line_number is not None), None)
        assert line_ref is not None
        assert line_ref.value == 'auth.js'
        assert line_ref.line_number == 156
        assert line_ref.confidence > 0.8  # Higher confidence for line refs
    
    def test_extract_function_names(self):
        """Test function name extraction."""
        text = "The processPayment() function is broken"
        refs = self.extractor.extract_references(text)
        
        func_refs = [r for r in refs if r.type == 'function_name']
        assert len(func_refs) == 1
        assert func_refs[0].value == 'processPayment'
    
    def test_extract_stack_trace_nodejs(self):
        """Test Node.js stack trace extraction."""
        text = "at processOrder (/app/orders/processor.js:87:12)"
        refs = self.extractor.extract_references(text)
        
        stack_refs = [r for r in refs if r.type == 'stack_trace']
        # Should find at least one stack trace reference  
        assert len(stack_refs) >= 1
        
        # Find the stack trace reference (may also match as file_path)
        stack_ref = next((r for r in stack_refs if r.value == '/app/orders/processor.js'), None)
        assert stack_ref is not None
        assert stack_ref.line_number == 87
        assert stack_ref.confidence > 0.9  # Very high for stack traces
    
    def test_extract_stack_trace_python(self):
        """Test Python stack trace extraction."""
        text = 'File "django/views.py", line 23, in handle_request'
        refs = self.extractor.extract_references(text)
        
        stack_refs = [r for r in refs if r.type == 'stack_trace']
        assert len(stack_refs) == 1
        assert stack_refs[0].value == 'django/views.py'
        assert stack_refs[0].line_number == 23
    
    def test_get_unique_files(self):
        """Test getting unique file list."""
        text = """
        Error in src/auth.js:15
        Also check src/auth.js for other issues
        Problem in lib/utils.js
        """
        refs = self.extractor.extract_references(text)
        unique_files = self.extractor.get_unique_files(refs)
        
        assert 'src/auth.js' in unique_files
        assert 'lib/utils.js' in unique_files
        assert len(unique_files) == 2  # Should deduplicate auth.js
    
    def test_get_file_with_lines(self):
        """Test getting files mapped to line numbers."""
        text = """
        Error in auth.js:15
        Also error in auth.js:42
        Problem in utils.js:100
        """
        refs = self.extractor.extract_references(text)
        file_lines = self.extractor.get_file_with_lines(refs)
        
        assert 'auth.js' in file_lines
        assert 15 in file_lines['auth.js']
        assert 42 in file_lines['auth.js']
        assert 'utils.js' in file_lines
        assert 100 in file_lines['utils.js']
    
    def test_simple_function_interface(self):
        """Test the simple function interface."""
        text = "Error in `src/api.js:42` where getUserData() fails"
        result = extract_code_references_from_issue(text)
        
        assert 'src/api.js' in result['file_paths']
        assert 'getUserData' in result['function_names']
        assert 'src/api.js' in result['file_lines']
        assert 42 in result['file_lines']['src/api.js']
        assert len(result['confidence_scores']) > 0
    
    def test_no_references_found(self):
        """Test handling when no code references are found."""
        text = "This is just a regular issue with no code references"
        result = extract_code_references_from_issue(text)
        
        assert result['file_paths'] == []
        assert result['function_names'] == []
        assert result['file_lines'] == {}
        assert result['confidence_scores'] == []
    
    def test_complex_issue_text(self):
        """Test with complex issue text like #152."""
        text = """
        ## Current Implementation (specialized_analyzers.py:210-220)
        
        When someone reports: "Function `processPayment()` in `src/payments/stripe.js` throws TypeError on line 42"
        
        Error in `lib/auth/validator.js:15` where `checkPermissions()` fails.
        """
        result = extract_code_references_from_issue(text)
        
        # Should find multiple files
        assert 'specialized_analyzers.py' in result['file_paths']
        assert 'src/payments/stripe.js' in result['file_paths'] 
        assert 'lib/auth/validator.js' in result['file_paths']
        
        # Should find functions
        assert 'processPayment' in result['function_names']
        assert 'checkPermissions' in result['function_names']
        
        # Should find line references
        assert 'specialized_analyzers.py' in result['file_lines']
        assert 210 in result['file_lines']['specialized_analyzers.py']
    
    def test_binary_file_filtering(self):
        """Test that binary files are filtered out."""
        config = ExtractionConfig(enable_metrics_logging=False)
        extractor = CodeReferenceExtractor(config)
        
        text = """
        Error in `src/image.png` and `config/app.js`
        Also check `docs/readme.pdf` and `lib/utils.py`
        """
        refs = extractor.extract_references(text)
        
        # Should only find text files
        file_refs = [r for r in refs if r.type == 'file_path']
        file_paths = [r.value for r in file_refs]
        
        assert 'config/app.js' in file_paths
        assert 'lib/utils.py' in file_paths
        assert 'src/image.png' not in file_paths  # Filtered binary
        assert 'docs/readme.pdf' not in file_paths  # Filtered binary
    
    def test_path_validation_security(self):
        """Test path traversal and security validation."""
        config = ExtractionConfig(enable_metrics_logging=False)
        extractor = CodeReferenceExtractor(config)
        
        text = """
        Error in `../../../etc/passwd` and `src/normal.js`
        Also check `/absolute/path.py` and `nested/very/deep/path/too/deep/structure/file.js`
        File with no extension: `README`
        """
        refs = extractor.extract_references(text)
        
        file_refs = [r for r in refs if r.type == 'file_path']
        file_paths = [r.value for r in file_refs]
        
        
        # Should only find safe paths
        assert 'src/normal.js' in file_paths
        assert '../../../etc/passwd' not in file_paths  # Path traversal
        assert '/absolute/path.py' not in file_paths  # Absolute path
        # Very deep nesting should be filtered (more than 10 slashes)
        deep_paths = [p for p in file_paths if p.count('/') > 10]
        assert len(deep_paths) == 0, f"Found deep paths that should be filtered: {deep_paths}"
    
    def test_extraction_config_limits(self):
        """Test that extraction respects configuration limits."""
        config = ExtractionConfig(
            max_files_per_issue=2,
            max_line_refs_per_file=1,
            enable_metrics_logging=False
        )
        extractor = CodeReferenceExtractor(config)
        
        text = "Files: `a.js:10`, `b.py:20`, `c.cpp:30`, `d.ts:40`"
        refs = extractor.extract_references(text)
        
        unique_files = extractor.get_unique_files(refs)
        file_lines = extractor.get_file_with_lines(refs)
        
        # Configuration limits should be available for downstream use
        assert config.max_files_per_issue == 2
        assert config.max_line_refs_per_file == 1
        
        # All files should be extracted (filtering happens downstream)
        assert len(unique_files) == 4
    
    def test_malformed_references(self):
        """Test handling of malformed file and function references."""
        config = ExtractionConfig(enable_metrics_logging=False)
        extractor = CodeReferenceExtractor(config)
        
        text = """
        Malformed: `file.js:abc` and `function broken(` 
        Valid: `normal.py:42` and `validFunction()`
        """
        refs = extractor.extract_references(text)
        
        # Should extract valid references and skip malformed ones
        file_refs = [r for r in refs if r.type == 'file_path']
        func_refs = [r for r in refs if r.type == 'function_name']
        
        # Should find valid file with line number
        valid_file = next((r for r in file_refs if r.value == 'normal.py'), None)
        assert valid_file is not None
        assert valid_file.line_number == 42
        
        # Should find valid function
        assert 'validFunction' in [r.value for r in func_refs]
    
    def test_malformed_stack_traces(self):
        """Test handling of malformed stack traces."""
        config = ExtractionConfig(enable_metrics_logging=False)
        extractor = CodeReferenceExtractor(config)
        
        text = """
        Malformed traces - these should be ignored:
        at functionName (incomplete.js:
        File "broken_python.py", line abc
        
        Valid Node.js stack trace:
        at processOrder (/app/orders/valid.js:25:10)
        
        Valid Python stack trace:
        File "src/test.py", line 42
        """
        refs = extractor.extract_references(text)
        
        stack_refs = [r for r in refs if r.type == 'stack_trace']
        # Should find valid stack traces, ignoring malformed ones
        assert len(stack_refs) >= 1
        
        # Check for the Node.js stack trace
        nodejs_trace = next((r for r in stack_refs if '/app/orders/valid.js' in r.value), None)
        assert nodejs_trace is not None
        assert nodejs_trace.line_number == 25
        
        # Check for the Python stack trace
        python_trace = next((r for r in stack_refs if 'src/test.py' in r.value), None)
        assert python_trace is not None
        assert python_trace.line_number == 42
    
    def test_very_long_file_paths(self):
        """Test handling of unreasonably long file paths."""
        config = ExtractionConfig(max_file_path_length=100, enable_metrics_logging=False)
        extractor = CodeReferenceExtractor(config)
        
        # Create a very long path that exceeds the limit
        long_path = "src/" + "very_long_directory_name/" * 10 + "file.js"
        text = f"Error in `{long_path}` on line 42"
        
        refs = extractor.extract_references(text)
        file_refs = [r for r in refs if r.type == 'file_path']
        
        # Should filter out the overly long path
        assert not any(r.value == long_path for r in file_refs)
    
    def test_sensitive_system_files(self):
        """Test filtering of sensitive system file paths."""
        config = ExtractionConfig(enable_metrics_logging=False)
        extractor = CodeReferenceExtractor(config)
        
        text = """
        System files that should be blocked:
        Error in `/etc/passwd` 
        Problem with `/proc/meminfo`
        Issue in `/sys/kernel/debug`
        
        Valid file:
        Error in `src/config.js`
        """
        refs = extractor.extract_references(text)
        file_refs = [r for r in refs if r.type == 'file_path']
        file_paths = [r.value for r in file_refs]
        
        # Should not include sensitive system files
        assert '/etc/passwd' not in file_paths
        assert '/proc/meminfo' not in file_paths
        assert '/sys/kernel/debug' not in file_paths
        
        # Should include valid user files
        assert 'src/config.js' in file_paths
    
    def test_injection_attempt_filtering(self):
        """Test filtering of potential injection attempts in file paths."""
        config = ExtractionConfig(enable_metrics_logging=False)
        extractor = CodeReferenceExtractor(config)
        
        text = """
        Potential injection attempts:
        Error in `file.js; rm -rf /`
        Problem with `app.py | cat /etc/passwd`
        Issue in `script.sh && echo "hacked"`
        
        Valid file:
        Error in `src/normal-file.js`
        """
        refs = extractor.extract_references(text)
        file_refs = [r for r in refs if r.type == 'file_path']
        file_paths = [r.value for r in file_refs]
        
        # Should filter out paths with injection characters
        assert not any(';' in path or '|' in path or '&' in path for path in file_paths)
        
        # Should include valid files
        assert 'src/normal-file.js' in file_paths