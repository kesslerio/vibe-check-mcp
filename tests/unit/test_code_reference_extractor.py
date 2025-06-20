"""
Test Code Reference Extractor - Issue #152

Tests the basic functionality of extracting file references,
function names, and line numbers from GitHub issue text.
"""

import pytest
from src.vibe_check.core.code_reference_extractor import (
    CodeReferenceExtractor,
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
        assert len(file_refs) == 1
        assert file_refs[0].value == 'auth.js'
        assert file_refs[0].line_number == 156
        assert file_refs[0].confidence > 0.8  # Higher confidence for line refs
    
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
        assert len(stack_refs) == 1
        assert stack_refs[0].value == '/app/orders/processor.js'
        assert stack_refs[0].line_number == 87
        assert stack_refs[0].confidence > 0.9  # Very high for stack traces
    
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