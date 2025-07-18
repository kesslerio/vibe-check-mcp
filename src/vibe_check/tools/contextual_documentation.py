"""
Contextual Documentation Tools

Implements Context 7 integration and library detection for project-aware analysis.
Provides MCP tools for detecting project libraries and loading contextual documentation.
"""

import json
import logging
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..config.vibe_check_config import get_vibe_check_config, VibeCheckConfig
from ..core.pattern_detector import PatternDetector

logger = logging.getLogger(__name__)


@dataclass
class LibraryDetectionResult:
    """Result of library detection scan"""
    libraries: Dict[str, Any]
    scan_duration_ms: int
    files_scanned: int
    detection_confidence: float
    errors: List[str]


@dataclass
class AnalysisContext:
    """Unified context object for analysis tools"""
    library_docs: Dict[str, str]
    project_conventions: Dict[str, Any]
    pattern_exceptions: List[str]
    conflict_resolution: Dict[str, str]
    context_metadata: Dict[str, Any]
    
    def get_contextual_recommendation(self, generic_pattern: str) -> str:
        """Transform generic advice into project-aware guidance"""
        # Priority: project-specific > library-specific > generic
        if generic_pattern in self.pattern_exceptions:
            return self.conflict_resolution.get(generic_pattern, generic_pattern)
        
        # Check library-specific overrides
        for library, docs in self.library_docs.items():
            if generic_pattern in docs:
                return f"For {library}: {docs[generic_pattern]}"
        
        return generic_pattern


class LibraryDetectionEngine:
    """Detects project libraries with performance optimization"""
    
    def __init__(self, config: VibeCheckConfig):
        self.config = config
        self.detection_patterns = self._load_detection_patterns()
        self.cache = {}
        self.cache_ttl = config.context_loading.cache_duration_minutes * 60
    
    def _load_detection_patterns(self) -> Dict[str, Any]:
        """Load library detection patterns from knowledge base"""
        try:
            knowledge_base_path = Path(__file__).parent.parent.parent.parent / "data" / "integration_knowledge_base.json"
            with open(knowledge_base_path, 'r') as f:
                knowledge_base = json.load(f)
            
            patterns = {}
            for library, info in knowledge_base.items():
                if "detection_patterns" in info:
                    patterns[library] = info["detection_patterns"]
            
            return patterns
        except Exception as e:
            logger.error(f"Error loading detection patterns: {e}")
            return {}
    
    @lru_cache(maxsize=128)
    def detect_libraries_from_content(
        self, 
        content: str, 
        file_path: str = "", 
        file_extension: str = ""
    ) -> Dict[str, float]:
        """Detect libraries from file content with caching"""
        detected = {}
        
        for library, patterns in self.detection_patterns.items():
            confidence = 0.0
            
            # Check imports
            for import_pattern in patterns.get("imports", []):
                if import_pattern in content:
                    confidence += 0.8
            
            # Check file extension match
            if file_extension in patterns.get("file_extensions", []):
                confidence += 0.2
            
            # Check for library-specific content patterns from knowledge base
            version_data = patterns.get("versions", {})
            if version_data:
                # Use first available version for pattern matching
                version_patterns = next(iter(version_data.values()), {})
                specific_patterns = version_patterns.get("specific_patterns", {})
                
                # Check for React hooks
                if library == "react" and file_extension in [".jsx", ".tsx"]:
                    react_hooks = ["useState", "useEffect", "useContext", "useReducer", "useMemo", "useCallback"]
                    if any(hook in content for hook in react_hooks):
                        confidence += 0.3
                
                # Check for FastAPI decorators
                if library == "fastapi" and file_extension == ".py":
                    fastapi_decorators = ["@app.get", "@app.post", "@app.put", "@app.delete", "@router."]
                    if any(decorator in content for decorator in fastapi_decorators):
                        confidence += 0.4
            
            if confidence > 0.3:  # Minimum confidence threshold
                detected[library] = min(confidence, 1.0)
        
        return detected
    
    def detect_libraries_from_dependencies(self, project_root: str) -> Dict[str, float]:
        """Detect libraries from dependency files"""
        detected = {}
        project_path = Path(project_root)
        
        # Check package.json for JavaScript/TypeScript projects
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                all_deps = {}
                all_deps.update(package_data.get("dependencies", {}))
                all_deps.update(package_data.get("devDependencies", {}))
                
                for library, patterns in self.detection_patterns.items():
                    for dep_name in patterns.get("dependencies", []):
                        if dep_name in all_deps:
                            detected[library] = 0.9  # High confidence from dependencies
                            
            except Exception as e:
                logger.warning(f"Error parsing package.json: {e}")
        
        # Check requirements.txt for Python projects
        requirements_files = [
            project_path / "requirements.txt",
            project_path / "pyproject.toml",
            project_path / "setup.py"
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                try:
                    content = req_file.read_text()
                    
                    for library, patterns in self.detection_patterns.items():
                        for dep_name in patterns.get("dependencies", []):
                            if dep_name in content:
                                detected[library] = 0.9
                                
                except Exception as e:
                    logger.warning(f"Error parsing {req_file}: {e}")
        
        return detected
    
    def scan_project_files(
        self, 
        project_root: str, 
        max_files: int = None, 
        timeout_seconds: int = None
    ) -> LibraryDetectionResult:
        """Scan project files for library usage with performance limits"""
        start_time = time.time()
        
        if max_files is None:
            max_files = self.config.context_loading.library_detection.max_files_to_scan
        if timeout_seconds is None:
            timeout_seconds = self.config.context_loading.library_detection.timeout_seconds
        
        project_path = Path(project_root)
        all_detected = {}
        files_scanned = 0
        errors = []
        
        # First, check dependency files (fast and reliable)
        dependency_detected = self.detect_libraries_from_dependencies(project_root)
        all_detected.update(dependency_detected)
        
        # Then scan source files
        exclude_patterns = self.config.context_loading.library_detection.exclude_patterns
        supported_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs"]
        
        try:
            for root, dirs, files in os.walk(project_path):
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    logger.warning(f"Library detection timed out after {timeout_seconds}s")
                    break
                
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                
                for file in files:
                    if files_scanned >= max_files:
                        logger.info(f"Reached max files limit: {max_files}")
                        break
                    
                    file_path = Path(root) / file
                    file_extension = file_path.suffix
                    
                    # Skip excluded files
                    if any(pattern in str(file_path) for pattern in exclude_patterns):
                        continue
                    
                    # Only scan supported file types
                    if file_extension not in supported_extensions:
                        continue
                    
                    try:
                        # Try UTF-8 first, fall back to latin-1 for binary files
                        try:
                            content = file_path.read_text(encoding='utf-8')
                        except UnicodeDecodeError:
                            try:
                                content = file_path.read_text(encoding='latin-1')
                            except UnicodeDecodeError:
                                logger.warning(f"Skipping file with encoding issues: {file_path}")
                                continue
                        
                        # Detect libraries in this file
                        file_detected = self.detect_libraries_from_content(
                            content, str(file_path), file_extension
                        )
                        
                        # Merge with overall detection (take max confidence)
                        for library, confidence in file_detected.items():
                            all_detected[library] = max(
                                all_detected.get(library, 0), 
                                confidence
                            )
                        
                        files_scanned += 1
                        
                    except Exception as e:
                        errors.append(f"Error scanning {file_path}: {e}")
                        continue
                
                if files_scanned >= max_files:
                    break
        
        except Exception as e:
            errors.append(f"Error during project scan: {e}")
        
        scan_duration = int((time.time() - start_time) * 1000)
        
        # Calculate overall detection confidence
        detection_confidence = sum(all_detected.values()) / len(all_detected) if all_detected else 0.0
        
        return LibraryDetectionResult(
            libraries=all_detected,
            scan_duration_ms=scan_duration,
            files_scanned=files_scanned,
            detection_confidence=detection_confidence,
            errors=errors
        )


class ProjectDocumentationParser:
    """Parses project-specific documentation for context"""
    
    def __init__(self, config: VibeCheckConfig):
        self.config = config
    
    def parse_project_docs(self, project_root: str) -> Dict[str, Any]:
        """Parse project documentation files for context"""
        project_path = Path(project_root)
        context = {
            "team_conventions": {},
            "architecture_decisions": {},
            "pattern_exceptions": [],
            "project_metadata": {}
        }
        
        # Parse common documentation files
        doc_files = [
            ("README.md", "project_overview"),
            ("CONTRIBUTING.md", "team_conventions"),
            ("ARCHITECTURE.md", "architecture_decisions"),
            ("docs/TECHNICAL.md", "technical_details")
        ]
        
        for file_name, context_key in doc_files:
            file_path = project_path / file_name
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    context[context_key] = self._extract_context_from_content(content)
                except Exception as e:
                    logger.warning(f"Error parsing {file_path}: {e}")
        
        return context
    
    def _extract_context_from_content(self, content: str) -> Dict[str, Any]:
        """Extract structured context from documentation content"""
        context = {}
        
        # Extract coding standards
        if "coding standard" in content.lower() or "style guide" in content.lower():
            context["coding_standards"] = self._extract_coding_standards(content)
        
        # Extract architecture decisions
        if "architecture" in content.lower() or "design decision" in content.lower():
            context["architecture_decisions"] = self._extract_architecture_decisions(content)
        
        # Extract technology stack using knowledge base libraries
        knowledge_base = self._load_integration_knowledge_base()
        tech_pattern = r'\b(' + '|'.join(knowledge_base.keys()) + r')\b'
        tech_mentions = re.findall(tech_pattern, content.lower())
        if tech_mentions:
            context["technology_stack"] = list(set(tech_mentions))
        
        return context
    
    def _extract_coding_standards(self, content: str) -> List[str]:
        """Extract coding standards from documentation"""
        standards = []
        
        # Look for bullet points about standards
        bullet_pattern = r'^\s*[-*]\s*(.+)'
        lines = content.split('\n')
        
        in_standards_section = False
        for line in lines:
            if "coding standard" in line.lower() or "style guide" in line.lower():
                in_standards_section = True
                continue
            
            if in_standards_section:
                if line.strip() == "":
                    continue
                if line.startswith("#"):
                    break
                
                match = re.match(bullet_pattern, line)
                if match:
                    standards.append(match.group(1).strip())
        
        return standards
    
    def _extract_architecture_decisions(self, content: str) -> List[str]:
        """Extract architecture decisions from documentation"""
        decisions = []
        
        # Look for ADR-style decisions
        adr_pattern = r'## ADR-\d+: (.+)'
        matches = re.findall(adr_pattern, content)
        decisions.extend(matches)
        
        # Look for decision sections
        decision_pattern = r'### Decision:\s*(.+)'
        matches = re.findall(decision_pattern, content)
        decisions.extend(matches)
        
        return decisions


class ContextualDocumentationManager:
    """Manages contextual documentation loading and caching"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.config = get_vibe_check_config(project_root)
        self.detection_engine = LibraryDetectionEngine(self.config)
        self.doc_parser = ProjectDocumentationParser(self.config)
        self.cache = {}
        self.cache_ttl = self.config.context_loading.cache_duration_minutes * 60
    
    def get_project_context(self, force_refresh: bool = False) -> AnalysisContext:
        """Get complete project context with caching"""
        cache_key = f"project_context_{self.project_root}"
        
        # Check cache
        if not force_refresh and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        # Detect libraries
        logger.info("Detecting project libraries...")
        detection_result = self.detection_engine.scan_project_files(self.project_root)
        
        # Parse project documentation
        logger.info("Parsing project documentation...")
        project_docs = self.doc_parser.parse_project_docs(self.project_root)
        
        # Load library documentation (placeholder for Context 7 integration)
        library_docs = {}
        for library in detection_result.libraries:
            library_docs[library] = f"Documentation for {library} (Context 7 integration pending)"
        
        # Load pattern exceptions
        pattern_exceptions = self._load_pattern_exceptions()
        
        # Create context object
        context = AnalysisContext(
            library_docs=library_docs,
            project_conventions=project_docs,
            pattern_exceptions=pattern_exceptions,
            conflict_resolution={},
            context_metadata={
                "detection_result": detection_result,
                "last_updated": time.time()
            }
        )
        
        # Cache the result
        self.cache[cache_key] = (context, time.time())
        
        return context
    
    def _load_pattern_exceptions(self) -> List[str]:
        """Load pattern exceptions from .vibe-check/pattern-exceptions.json"""
        try:
            exceptions_file = Path(self.project_root) / ".vibe-check" / "pattern-exceptions.json"
            if exceptions_file.exists():
                with open(exceptions_file, 'r') as f:
                    data = json.load(f)
                    return data.get("approved_patterns", [])
        except Exception as e:
            logger.warning(f"Error loading pattern exceptions: {e}")
        
        return []


# Project-aware context manager cache
_context_managers: Dict[str, ContextualDocumentationManager] = {}


def get_context_manager(project_root: str = ".") -> ContextualDocumentationManager:
    """Get or create context manager instance for specific project"""
    # Normalize project root to absolute path for consistent caching
    from pathlib import Path
    abs_project_root = str(Path(project_root).resolve())
    
    if abs_project_root not in _context_managers:
        _context_managers[abs_project_root] = ContextualDocumentationManager(project_root)
    return _context_managers[abs_project_root]


def clear_context_manager_cache() -> None:
    """Clear global context manager cache for testing/cleanup"""
    global _context_managers
    _context_managers.clear()


def get_cached_projects() -> List[str]:
    """Get list of projects currently cached"""
    return list(_context_managers.keys())