"""
Workspace-Aware Vibe Check Mentor Tool

Enhanced version of vibe_check_mentor that reads actual code files from a configured
workspace directory. Uses the WORKSPACE environment variable to securely access files
and provide context-aware guidance based on real code instead of assumptions.

Security Features:
- Path validation against WORKSPACE directory
- File size and type restrictions
- Path traversal prevention

Performance Features:
- Session-based caching
- Lazy loading
- Multi-language support
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Import the enhanced mentor and context manager
from .vibe_mentor_enhanced import EnhancedVibeMentorEngine, ContextExtractor, TechnicalContext
from vibe_check.mentor.context_manager import get_context_cache, SecurityValidator, FileContext
from vibe_check.mentor.models.session import CollaborativeReasoningSession, ContributionData
from vibe_check.mentor.models.persona import PersonaData
from vibe_check.core.pattern_detector import PatternDetector

logger = logging.getLogger(__name__)

# Constants
MAX_CONTEXT_FILES = 5  # Maximum number of files to include in context
MAX_CONTEXT_SIZE = 50000  # Maximum total size of context in characters


class WorkspaceAwareMentorEngine(EnhancedVibeMentorEngine):
    """Extended mentor engine with workspace file reading capabilities"""
    
    def __init__(self):
        super().__init__()
        self.context_cache = get_context_cache()
        self.pattern_detector = PatternDetector()
        self.workspace = SecurityValidator.get_workspace_directory()
        
        if self.workspace:
            logger.info(f"Workspace-aware mentor initialized with workspace: {self.workspace}")
        else:
            logger.info("Workspace-aware mentor initialized without workspace (will use generic advice)")
    
    def _extract_files_from_query(self, query: str, context: Optional[str] = None) -> List[str]:
        """Extract file references from the query and context"""
        combined_text = f"{query} {context or ''}"
        
        # Use context cache's file extraction logic
        files = self.context_cache.extract_files_from_query(combined_text)
        
        # Also check for common patterns like "in the X file" or "the X.py"
        import re
        file_patterns = [
            r'(?:in|from|at|the)\s+(\w+\.(?:py|js|ts|go|rs|java|cpp|c|h|rb|php|swift|kt))',
            r'(?:file|module|class)\s+(\w+\.(?:py|js|ts|go|rs|java|cpp|c|h|rb|php|swift|kt))',
            r'`([^`]+\.(?:py|js|ts|go|rs|java|cpp|c|h|rb|php|swift|kt))`'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            files.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for f in files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)
        
        return unique_files[:MAX_CONTEXT_FILES]
    
    def _load_workspace_context(
        self,
        session_id: str,
        query: str,
        context: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ) -> Tuple[List[FileContext], List[str]]:
        """Load relevant files from the workspace"""
        
        if not self.workspace:
            return [], ["No workspace configured. Set WORKSPACE environment variable to enable file reading."]
        
        # Extract files from query if not provided
        if not file_paths:
            file_paths = self._extract_files_from_query(query, context)
        
        if not file_paths:
            # Try to find relevant files based on query terms
            # This is a simple heuristic - could be enhanced with better search
            return [], []
        
        # Convert relative paths to absolute paths within workspace
        absolute_paths = []
        for file_path in file_paths:
            if not os.path.isabs(file_path):
                # Try to find the file in the workspace
                workspace_path = Path(self.workspace)
                
                # First try direct path
                full_path = workspace_path / file_path
                if full_path.exists():
                    absolute_paths.append(str(full_path))
                else:
                    # Try to find it recursively (limited depth for performance)
                    found = False
                    for root, dirs, files in os.walk(self.workspace):
                        # Limit search depth
                        depth = root[len(self.workspace):].count(os.sep)
                        if depth > 3:
                            dirs[:] = []
                            continue
                        
                        # Skip common non-source directories
                        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']]
                        
                        if os.path.basename(file_path) in files:
                            full_path = os.path.join(root, os.path.basename(file_path))
                            absolute_paths.append(full_path)
                            found = True
                            break
                    
                    if not found:
                        logger.warning(f"File not found in workspace: {file_path}")
            else:
                absolute_paths.append(file_path)
        
        # Load files into context cache
        return self.context_cache.add_files_to_session(
            session_id,
            absolute_paths,
            self.workspace,
            query
        )
    
    def _format_file_context(self, file_contexts: List[FileContext]) -> str:
        """Format file contexts into a readable string for the personas"""
        if not file_contexts:
            return ""
        
        formatted = []
        total_size = 0
        
        for fc in file_contexts:
            if total_size + len(fc.content) > MAX_CONTEXT_SIZE:
                # Truncate if too large
                remaining = MAX_CONTEXT_SIZE - total_size
                if remaining > 1000:  # Only include if we can show meaningful content
                    content_preview = fc.content[:remaining] + "\n... (truncated)"
                else:
                    break
            else:
                content_preview = fc.content
            
            # Format the file information
            file_info = [
                f"\n=== File: {fc.path} ===",
                f"Language: {fc.language}",
            ]
            
            if fc.classes:
                file_info.append(f"Classes: {', '.join(fc.classes[:10])}")
            if fc.functions:
                file_info.append(f"Functions: {', '.join(fc.functions[:10])}")
            if fc.imports:
                file_info.append(f"Imports: {', '.join(fc.imports[:10])}")
            
            # Add relevant lines if available
            if fc.relevant_lines:
                file_info.append("\nRelevant sections:")
                for category, lines in fc.relevant_lines.items():
                    if lines:
                        file_info.append(f"  {category}:")
                        for line_num, line_content in lines[:3]:  # Show first 3 relevant lines
                            file_info.append(f"    Line {line_num}: {line_content[:100]}")
            
            # Add a preview of the actual content
            if content_preview:
                lines = content_preview.split('\n')
                preview_lines = lines[:20]  # Show first 20 lines
                if len(lines) > 20:
                    preview_lines.append(f"... ({len(lines) - 20} more lines)")
                file_info.append("\nContent preview:")
                file_info.extend([f"  {line}" for line in preview_lines])
            
            formatted.append('\n'.join(file_info))
            total_size += len(fc.content)
        
        return '\n\n'.join(formatted)
    
    def _enhance_context_with_workspace(
        self,
        tech_context: TechnicalContext,
        file_contexts: List[FileContext]
    ) -> TechnicalContext:
        """Enhance the technical context with information from workspace files"""
        
        if not file_contexts:
            return tech_context
        
        # Extract additional technologies and frameworks from actual code
        for fc in file_contexts:
            # Add imports as technologies
            if fc.imports:
                for imp in fc.imports:
                    # Extract the main module name
                    module = imp.split('.')[0] if '.' in imp else imp
                    if module and module not in tech_context.technologies:
                        tech_context.technologies.append(module)
            
            # Add file language as a framework if not present
            if fc.language and fc.language not in tech_context.frameworks:
                tech_context.frameworks.append(fc.language)
        
        # Limit to reasonable number of items
        tech_context.technologies = tech_context.technologies[:10]
        tech_context.frameworks = tech_context.frameworks[:10]
        
        return tech_context
    
    def analyze_with_workspace(
        self,
        query: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
        reasoning_depth: str = "standard",
        continue_session: bool = False,
        file_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze query with workspace file context.
        
        Args:
            query: The technical question or decision
            context: Additional context
            session_id: Session ID for continuity
            reasoning_depth: Analysis depth (quick/standard/comprehensive)
            continue_session: Whether to continue existing session
            file_paths: Explicit file paths to load (optional)
        
        Returns:
            Analysis results with workspace-aware insights
        """
        
        # Generate session ID if not provided
        if not session_id:
            import time
            import hashlib
            session_id = f"workspace-{int(time.time())}-{hashlib.md5(query.encode()).hexdigest()[:8]}"
        
        # Load workspace context
        file_contexts, file_errors = self._load_workspace_context(
            session_id, query, context, file_paths
        )
        
        # Format file context for inclusion
        formatted_file_context = self._format_file_context(file_contexts)
        
        # Combine context with file information
        enhanced_context = context or ""
        if formatted_file_context:
            enhanced_context = f"{enhanced_context}\n\n--- Workspace Files ---\n{formatted_file_context}"
        
        # Extract technical context
        tech_context = ContextExtractor.extract_context(query, enhanced_context)
        
        # Enhance with workspace information
        tech_context = self._enhance_context_with_workspace(tech_context, file_contexts)
        
        # Detect patterns in the query and actual code
        patterns = []
        if file_contexts:
            # Analyze actual code for patterns
            for fc in file_contexts:
                # Simple pattern detection in code
                code_patterns = self.pattern_detector.detect_patterns(fc.content)
                patterns.extend(code_patterns)
        
        # Get base analysis
        result = self.analyze(
            query=query,
            context=enhanced_context,
            session_id=session_id,
            reasoning_depth=reasoning_depth,
            continue_session=continue_session
        )
        
        # Add workspace-specific information
        result['workspace_info'] = {
            'workspace_configured': self.workspace is not None,
            'workspace_path': self.workspace,
            'files_loaded': len(file_contexts),
            'files_analyzed': [fc.path for fc in file_contexts],
            'file_errors': file_errors,
            'total_context_size': sum(fc.size for fc in file_contexts)
        }
        
        # Add specific code insights if available
        if file_contexts:
            code_insights = []
            
            for fc in file_contexts:
                if fc.relevant_lines and fc.relevant_lines.get('potential_issues'):
                    for line_num, line_content in fc.relevant_lines['potential_issues']:
                        code_insights.append(f"Potential issue in {fc.path} at line {line_num}: {line_content.strip()}")
            
            if code_insights:
                result['code_insights'] = code_insights
        
        return result


def create_workspace_aware_mentor() -> WorkspaceAwareMentorEngine:
    """Factory function to create workspace-aware mentor instance"""
    return WorkspaceAwareMentorEngine()


# Export the main analyze function for tool registration
async def analyze_with_workspace_mentor(
    query: str,
    context: Optional[str] = None,
    session_id: Optional[str] = None,
    reasoning_depth: str = "standard",
    continue_session: bool = False,
    file_paths: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Workspace-aware collaborative reasoning tool.
    
    Reads actual code files from configured workspace directory to provide
    specific, context-aware guidance instead of generic advice.
    
    Configure workspace by setting WORKSPACE environment variable.
    
    Args:
        query: Technical question or decision to discuss
        context: Additional context (code, architecture, requirements)
        session_id: Session ID to continue previous conversation
        reasoning_depth: Analysis depth - quick/standard/comprehensive
        continue_session: Whether to continue existing session
        file_paths: Specific files to analyze (optional, auto-detected from query)
    
    Returns:
        Collaborative reasoning analysis with workspace-aware insights
    """
    engine = create_workspace_aware_mentor()
    return engine.analyze_with_workspace(
        query=query,
        context=context,
        session_id=session_id,
        reasoning_depth=reasoning_depth,
        continue_session=continue_session,
        file_paths=file_paths
    )