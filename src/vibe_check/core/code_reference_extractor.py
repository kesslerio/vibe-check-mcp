"""
Code Reference Extractor - Minimal POC for Issue #152

Extracts code references from GitHub issue text including file paths,
function names, and stack traces. Follows mentor guidance to start
with working API calls first, then extract patterns.
"""

import re
import logging
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodeReference:
    """Represents a code reference extracted from issue text."""
    type: str  # 'file_path', 'function_name', 'line_reference', 'stack_trace'
    value: str
    line_number: Optional[int] = None
    confidence: float = 0.0
    context: str = ""


class CodeReferenceExtractor:
    """Minimal code reference extraction for GitHub issues."""
    
    def __init__(self):
        # File path patterns - start with common cases
        self.file_patterns = [
            # Standard file references
            r'`([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4})`',  # `src/file.js`
            r'(?:file|in|at)\s+([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4})',  # file src/file.js
            r'([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4}):(\d+)',  # file.js:42
            r'"([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4})"',  # "src/file.js"
        ]
        
        # Function patterns - simple cases first
        self.function_patterns = [
            r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # function processPayment
            r'([a-zA-Z_][a-zA-Z0-9_]*)\(\)',  # processPayment()
            r'`([a-zA-Z_][a-zA-Z0-9_]*)\(`',  # `processPayment(`
        ]
        
        # Stack trace patterns - start with Node.js/Python
        self.stack_trace_patterns = [
            r'at\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+\(([^)]+):(\d+):(\d+)\)',  # Node.js
            r'File\s+"([^"]+)",\s+line\s+(\d+)',  # Python
        ]
    
    def extract_references(self, text: str) -> List[CodeReference]:
        """
        Extract code references from issue text.
        
        Args:
            text: Issue body or title text
            
        Returns:
            List of extracted code references
        """
        references = []
        
        # Extract file paths
        references.extend(self._extract_file_paths(text))
        
        # Extract function references
        references.extend(self._extract_functions(text))
        
        # Extract stack traces
        references.extend(self._extract_stack_traces(text))
        
        return references
    
    def _extract_file_paths(self, text: str) -> List[CodeReference]:
        """Extract file path references."""
        references = []
        
        for pattern in self.file_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    # File path with line number
                    file_path = match.group(1)
                    line_num = int(match.group(2))
                    confidence = 0.9  # High confidence for explicit line refs
                else:
                    file_path = match.group(1)
                    line_num = None
                    confidence = 0.7  # Medium confidence for file refs
                
                # Basic validation - must have valid extension
                if '.' in file_path and len(file_path) > 3:
                    references.append(CodeReference(
                        type='file_path',
                        value=file_path,
                        line_number=line_num,
                        confidence=confidence,
                        context=match.group(0)
                    ))
        
        return references
    
    def _extract_functions(self, text: str) -> List[CodeReference]:
        """Extract function name references."""
        references = []
        
        for pattern in self.function_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                func_name = match.group(1)
                
                # Basic validation - reasonable function name
                if len(func_name) >= 3 and func_name.isidentifier():
                    confidence = 0.6  # Medium confidence for function refs
                    references.append(CodeReference(
                        type='function_name',
                        value=func_name,
                        confidence=confidence,
                        context=match.group(0)
                    ))
        
        return references
    
    def _extract_stack_traces(self, text: str) -> List[CodeReference]:
        """Extract stack trace information."""
        references = []
        
        for pattern in self.stack_trace_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                if len(match.groups()) >= 2:
                    file_path = match.group(2) if len(match.groups()) > 2 else match.group(1)
                    line_num = int(match.group(3)) if len(match.groups()) > 3 else int(match.group(2))
                    
                    references.append(CodeReference(
                        type='stack_trace',
                        value=file_path,
                        line_number=line_num,
                        confidence=0.95,  # Very high confidence for stack traces
                        context=match.group(0)
                    ))
        
        return references
    
    def get_unique_files(self, references: List[CodeReference]) -> List[str]:
        """Get unique file paths from references."""
        files = set()
        for ref in references:
            if ref.type in ['file_path', 'stack_trace']:
                files.add(ref.value)
        return list(files)
    
    def get_file_with_lines(self, references: List[CodeReference]) -> Dict[str, List[int]]:
        """Get files mapped to their referenced line numbers."""
        file_lines = {}
        for ref in references:
            if ref.type in ['file_path', 'stack_trace'] and ref.line_number:
                if ref.value not in file_lines:
                    file_lines[ref.value] = []
                file_lines[ref.value].append(ref.line_number)
        return file_lines


def extract_code_references_from_issue(issue_text: str) -> Dict[str, List[str]]:
    """
    Simple function for extracting code references - minimal POC.
    
    Args:
        issue_text: GitHub issue body text
        
    Returns:
        Dictionary with extracted references
    """
    extractor = CodeReferenceExtractor()
    references = extractor.extract_references(issue_text)
    
    return {
        'file_paths': extractor.get_unique_files(references),
        'function_names': [ref.value for ref in references if ref.type == 'function_name'],
        'file_lines': extractor.get_file_with_lines(references),
        'confidence_scores': [ref.confidence for ref in references]
    }