"""
File Type Analyzer for PR Reviews

Provides file type-specific analysis guidelines and prompts based on the
Claude GitHub action patterns. Each file type has specific review criteria.
"""

from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileTypeAnalyzer:
    """
    Analyzes files by type and provides specific review guidelines.
    
    Based on Claude GitHub action best practices for different file types.
    """
    
    # File type detection patterns
    FILE_TYPE_PATTERNS = {
        'typescript': ['.ts', '.tsx'],
        'javascript': ['.js', '.jsx'],
        'python': ['.py'],
        'api': ['api.py', 'routes.py', 'endpoints.py', 'views.py', 'controller.py'],
        'react': ['.tsx', '.jsx', 'Component.tsx', 'Component.jsx'],
        'test': ['test_', '_test.', '.test.', '.spec.', 'test/', 'tests/'],
        'config': ['.json', '.yaml', '.yml', '.toml', '.ini', '.env'],
        'documentation': ['.md', '.rst', '.txt', 'README', 'CHANGELOG'],
        'sql': ['.sql'],
        'style': ['.css', '.scss', '.sass', '.less'],
    }
    
    # Specific review guidelines per file type
    REVIEW_GUIDELINES = {
        'typescript': {
            'focus_areas': [
                'Type safety and proper interface usage',
                'Avoid using "any" type without justification',
                'Proper error type definitions',
                'Consistent type exports and imports'
            ],
            'common_issues': [
                'Missing type definitions',
                'Implicit any types',
                'Type assertions without validation',
                'Inconsistent interface naming'
            ]
        },
        'javascript': {
            'focus_areas': [
                'Modern ES6+ syntax usage',
                'Proper error handling',
                'Async/await vs promises consistency',
                'Module import/export patterns'
            ],
            'common_issues': [
                'Callback hell',
                'Missing error handling',
                'Var usage instead of let/const',
                'Inconsistent code style'
            ]
        },
        'python': {
            'focus_areas': [
                'Type hints usage',
                'Proper exception handling',
                'PEP 8 compliance',
                'Docstring completeness'
            ],
            'common_issues': [
                'Missing type hints',
                'Broad exception catching',
                'Mutable default arguments',
                'Missing docstrings'
            ]
        },
        'api': {
            'focus_areas': [
                'Security and authentication',
                'Input validation and sanitization',
                'Error handling and status codes',
                'Rate limiting considerations',
                'API versioning strategy'
            ],
            'common_issues': [
                'Missing input validation',
                'Exposing sensitive data',
                'Improper error responses',
                'SQL injection vulnerabilities',
                'Missing rate limiting'
            ]
        },
        'react': {
            'focus_areas': [
                'Performance optimizations (memoization, lazy loading)',
                'Accessibility (ARIA labels, keyboard navigation)',
                'Component composition and reusability',
                'State management patterns',
                'Hook usage best practices'
            ],
            'common_issues': [
                'Missing key props in lists',
                'Unnecessary re-renders',
                'Direct DOM manipulation',
                'Missing accessibility attributes',
                'useEffect dependency issues'
            ]
        },
        'test': {
            'focus_areas': [
                'Test coverage completeness',
                'Edge case handling',
                'Test isolation and independence',
                'Meaningful test descriptions',
                'Mock usage appropriateness'
            ],
            'common_issues': [
                'Missing edge case tests',
                'Flaky tests',
                'Over-mocking',
                'Poor test descriptions',
                'Testing implementation details'
            ]
        },
        'config': {
            'focus_areas': [
                'Security (no exposed secrets)',
                'Environment-specific settings',
                'Validation of config values',
                'Documentation of settings'
            ],
            'common_issues': [
                'Hardcoded secrets',
                'Missing environment variables',
                'Invalid JSON/YAML syntax',
                'Undocumented configuration'
            ]
        },
        'sql': {
            'focus_areas': [
                'Query performance and indexing',
                'SQL injection prevention',
                'Transaction handling',
                'Migration reversibility'
            ],
            'common_issues': [
                'Missing indexes',
                'N+1 query problems',
                'Unsafe string concatenation',
                'Non-reversible migrations'
            ]
        }
    }
    
    def analyze_files(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze files and group by type with specific guidelines.
        
        Args:
            files: List of file dictionaries from PR data
            
        Returns:
            Analysis results with file type breakdown and guidelines
        """
        file_type_groups = self._group_files_by_type(files)
        
        analysis = {
            'file_types_found': list(file_type_groups.keys()),
            'type_specific_analysis': {},
            'review_focus_summary': [],
            'priority_checks': []
        }
        
        for file_type, file_list in file_type_groups.items():
            guidelines = self.REVIEW_GUIDELINES.get(file_type, {})
            
            # Extract filenames with logging for fallbacks
            files = []
            for f in file_list:
                filename = f.get('filename')
                if not filename:
                    filename = f.get('name', 'unknown')
                    if filename != 'unknown':
                        logger.debug(f"Using 'name' fallback for file: {filename}")
                    else:
                        logger.debug("No filename or name found, using 'unknown'")
                files.append(filename)
            
            analysis['type_specific_analysis'][file_type] = {
                'files': files,
                'count': len(file_list),
                'focus_areas': guidelines.get('focus_areas', []),
                'common_issues': guidelines.get('common_issues', [])
            }
            
            # Add to review focus summary
            if guidelines.get('focus_areas'):
                analysis['review_focus_summary'].extend([
                    f"{file_type.upper()}: {area}" 
                    for area in guidelines['focus_areas'][:2]  # Top 2 focus areas
                ])
            
            # Identify priority checks
            if file_type in ['api', 'config', 'sql']:
                # Extract filenames with logging for security-sensitive files
                security_files = []
                for f in file_list:
                    filename = f.get('filename')
                    if not filename:
                        filename = f.get('name', 'unknown')
                        logger.debug(f"Using fallback filename for security-sensitive file: {filename}")
                    security_files.append(filename)
                
                analysis['priority_checks'].append({
                    'type': file_type,
                    'reason': 'Security-sensitive file type',
                    'files': security_files
                })
        
        return analysis
    
    def _group_files_by_type(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Group files by their detected type."""
        file_groups = {}
        
        for file_data in files:
            filename = file_data.get('filename', '')
            file_type = self._detect_file_type(filename)
            
            if file_type not in file_groups:
                file_groups[file_type] = []
            file_groups[file_type].append(file_data)
        
        return file_groups
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type based on filename patterns."""
        path = Path(filename)
        filename_lower = filename.lower()
        
        # Check each file type pattern
        for file_type, patterns in self.FILE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern.startswith('.'):
                    # Extension match
                    if path.suffix == pattern:
                        return file_type
                elif '/' in pattern:
                    # Path contains match
                    if pattern in filename_lower:
                        return file_type
                else:
                    # Filename contains match
                    if pattern in path.name.lower():
                        return file_type
        
        # No match found in patterns, return 'other'
        return 'other'
    
    def generate_file_type_prompt(self, file_type_analysis: Dict[str, Any]) -> str:
        """Generate file type-specific review prompt section."""
        if not file_type_analysis['type_specific_analysis']:
            return ""
        
        prompt_parts = ["## File Type-Specific Review Focus\n"]
        
        for file_type, details in file_type_analysis['type_specific_analysis'].items():
            if details['count'] == 0:
                continue
                
            prompt_parts.append(f"\n### {file_type.upper()} Files ({details['count']} files)")
            
            if details['focus_areas']:
                prompt_parts.append("Focus on:")
                for area in details['focus_areas']:
                    prompt_parts.append(f"- {area}")
            
            if details['common_issues']:
                prompt_parts.append("\nWatch for:")
                for issue in details['common_issues'][:3]:  # Top 3 issues
                    prompt_parts.append(f"- {issue}")
        
        if file_type_analysis['priority_checks']:
            prompt_parts.append("\n### ⚠️ Priority Security Checks")
            for check in file_type_analysis['priority_checks']:
                prompt_parts.append(f"- {check['type'].upper()}: {check['reason']}")
                for filename in check['files'][:3]:  # Show first 3 files
                    prompt_parts.append(f"  - {filename}")
        
        return '\n'.join(prompt_parts)