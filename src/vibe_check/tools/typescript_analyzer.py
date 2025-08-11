"""
TypeScript-specific analysis for vibe_check_mentor
Provides real code analysis for TypeScript 'any' warnings and type safety issues
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TypeScriptAnalysis:
    """Analysis results for TypeScript code"""
    any_count: int = 0
    unknown_count: int = 0
    test_file_anys: int = 0
    production_anys: int = 0
    api_boundary_anys: int = 0
    simple_anys: int = 0  # Easy to fix (e.g., any[])
    complex_anys: int = 0  # Requires type guards
    sample_usages: List[str] = None
    risk_assessment: str = "low"
    
    def __post_init__(self):
        if self.sample_usages is None:
            self.sample_usages = []


class TypeScriptAnyAnalyzer:
    """Analyzes TypeScript files for 'any' usage patterns"""
    
    # Patterns for detecting different any usage types
    ANY_PATTERNS = {
        'explicit_any': re.compile(r':\s*any(?:\[\])?(?:\s|$|,|\)|>)'),
        'as_any': re.compile(r'\bas\s+any\b'),
        'any_array': re.compile(r':\s*any\[\]'),
        'any_in_generics': re.compile(r'<[^>]*any[^>]*>'),
        'eslint_disable': re.compile(r'@typescript-eslint/no-explicit-any'),
        'unknown': re.compile(r':\s*unknown(?:\[\])?(?:\s|$|,|\)|>)'),
        'type_guard': re.compile(r'if\s*\([^)]*typeof|instanceof|in\s+[^)]*\)'),
    }
    
    API_INDICATORS = ['fetch', 'axios', 'request', 'response', 'api', 'endpoint', 'payload']
    TEST_INDICATORS = ['.test.ts', '.spec.ts', '__tests__', 'test/', 'tests/']
    
    @classmethod
    def analyze_file(cls, file_path: Path) -> Dict[str, Any]:
        """Analyze a single TypeScript file for any usage"""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Count different types of any usage
            any_matches = cls.ANY_PATTERNS['explicit_any'].findall(content)
            as_any_matches = cls.ANY_PATTERNS['as_any'].findall(content)
            unknown_matches = cls.ANY_PATTERNS['unknown'].findall(content)
            
            # Check if it's a test file
            is_test = any(indicator in str(file_path).lower() for indicator in cls.TEST_INDICATORS)
            
            # Check for API boundaries
            is_api = any(indicator in content.lower() for indicator in cls.API_INDICATORS)
            
            # Get sample usages with line numbers
            samples = []
            for i, line in enumerate(lines, 1):
                if 'any' in line and not line.strip().startswith('//'):
                    samples.append(f"Line {i}: {line.strip()[:100]}")
                    if len(samples) >= 3:  # Limit samples
                        break
            
            return {
                'file': str(file_path),
                'any_count': len(any_matches) + len(as_any_matches),
                'unknown_count': len(unknown_matches),
                'is_test': is_test,
                'is_api': is_api,
                'samples': samples,
                'has_type_guards': bool(cls.ANY_PATTERNS['type_guard'].search(content))
            }
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return {}
    
    @classmethod
    def analyze_directory(cls, directory: Path, max_files: int = 10) -> TypeScriptAnalysis:
        """Analyze TypeScript files in a directory"""
        analysis = TypeScriptAnalysis()
        
        # Find TypeScript files
        ts_files = list(directory.rglob("*.ts"))
        tsx_files = list(directory.rglob("*.tsx"))
        all_files = ts_files + tsx_files
        
        if not all_files:
            logger.info("No TypeScript files found in directory")
            return analysis
        
        # Sample files for analysis (limit for performance)
        files_to_analyze = all_files[:max_files]
        logger.info(f"Analyzing {len(files_to_analyze)} TypeScript files")
        
        for file_path in files_to_analyze:
            file_analysis = cls.analyze_file(file_path)
            if not file_analysis:
                continue
                
            analysis.any_count += file_analysis.get('any_count', 0)
            analysis.unknown_count += file_analysis.get('unknown_count', 0)
            
            if file_analysis.get('is_test'):
                analysis.test_file_anys += file_analysis.get('any_count', 0)
            else:
                analysis.production_anys += file_analysis.get('any_count', 0)
            
            if file_analysis.get('is_api'):
                analysis.api_boundary_anys += file_analysis.get('any_count', 0)
            
            # Collect samples
            analysis.sample_usages.extend(file_analysis.get('samples', [])[:2])
        
        # Risk assessment
        if analysis.production_anys > 50:
            analysis.risk_assessment = "high"
        elif analysis.api_boundary_anys > 20:
            analysis.risk_assessment = "medium-high"
        elif analysis.production_anys > 20:
            analysis.risk_assessment = "medium"
        else:
            analysis.risk_assessment = "low"
        
        # Simple vs complex (heuristic)
        analysis.simple_anys = analysis.test_file_anys  # Test files usually simpler
        analysis.complex_anys = analysis.api_boundary_anys  # API boundaries usually complex
        
        return analysis


def generate_typescript_specific_advice(
    analysis: TypeScriptAnalysis,
    query: str,
    target_reduction: int = 500
) -> Dict[str, Tuple[str, str, float]]:
    """Generate TypeScript-specific advice based on actual code analysis"""
    
    advice = {}
    
    # Senior Engineer perspective with real data
    if analysis.production_anys > analysis.test_file_anys:
        senior_msg = (
            f"Based on actual analysis: You have {analysis.production_anys} 'any' in production vs "
            f"{analysis.test_file_anys} in tests. **Start with test files** - they're safer to modify. "
            f"For production code with {analysis.api_boundary_anys} API boundary 'any' types, use "
            f"ts-migrate to add $TSFixMe markers first. This preserves functionality while marking "
            f"technical debt. Never use eslint --fix on API boundaries - it WILL break runtime code."
        )
    else:
        senior_msg = (
            f"Good news: Most of your {analysis.any_count} 'any' warnings are in test files. "
            f"Use eslint-filtered-fix on test/**/*.ts first - safe and quick wins. "
            f"For the {analysis.production_anys} production 'any' types, manual review is essential. "
            f"Each any→unknown conversion needs type guards, especially at API boundaries."
        )
    
    advice['senior_engineer'] = ('insight', senior_msg, 0.95)
    
    # Product Engineer with timeline focus
    reduction_needed = analysis.any_count - target_reduction
    weekly_target = reduction_needed // 12  # 3 months = ~12 weeks
    
    product_msg = (
        f"Timeline reality check: You need to fix {reduction_needed} warnings in 3 months = "
        f"~{weekly_target} per week. With {analysis.test_file_anys} in tests, you can safely "
        f"auto-fix ~{analysis.test_file_anys // 3} this week. That's {(analysis.test_file_anys // 3) / weekly_target:.0%} "
        f"of your weekly target with minimal risk. Focus on velocity in safe areas first, "
        f"then tackle the {analysis.complex_anys} complex cases manually."
    )
    
    advice['product_engineer'] = ('suggestion', product_msg, 0.90)
    
    # AI Engineer with tooling recommendations
    if analysis.sample_usages:
        samples_text = "\n".join(analysis.sample_usages[:3])
        ai_msg = (
            f"Looking at your actual 'any' usage:\n{samples_text}\n\n"
            f"AI-powered approach: 1) Use TypeStat for safe automated inference, "
            f"2) Generate types from runtime JSON with quicktype.io, "
            f"3) Use Copilot to suggest type definitions based on usage context. "
            f"Risk level: {analysis.risk_assessment} based on {analysis.api_boundary_anys} API boundary usages."
        )
    else:
        ai_msg = (
            f"With {analysis.any_count} total 'any' warnings, use AI tools strategically: "
            f"TypeStat for automated inference (15-20% success rate), "
            f"ts-morph for AST-based transformations, "
            f"GitHub Copilot for context-aware type suggestions. "
            f"Never trust auto-fix blindly - validate with your test suite."
        )
    
    advice['ai_engineer'] = ('synthesis', ai_msg, 0.92)
    
    return advice