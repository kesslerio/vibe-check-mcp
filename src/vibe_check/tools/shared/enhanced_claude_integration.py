"""
Enhanced Claude CLI Integration with Automatic Context Injection

Extends ClaudeCliExecutor to automatically inject project-specific context into
Claude CLI prompts without requiring code changes to existing analysis tools.

Features:
- Automatic project context loading from .vibe-check/ directory
- Library-specific documentation injection via Context 7
- Pattern exception handling for project-specific overrides
- Graceful degradation when context loading fails
- Caching for performance optimization
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .claude_integration import ClaudeCliExecutor
from ...config.vibe_check_config import VibeCheckConfigLoader, VibeCheckConfig
from ...tools.contextual_documentation import get_context_manager, AnalysisContext

logger = logging.getLogger(__name__)


class EnhancedClaudeCliExecutor(ClaudeCliExecutor):
    """
    Enhanced Claude CLI executor with automatic project context injection.
    
    Extends the standard ClaudeCliExecutor to automatically load and inject
    project-specific context into Claude CLI prompts based on .vibe-check/
    configuration files.
    """
    
    def __init__(self, timeout_seconds: int = 60, project_root: str = "."):
        """
        Initialize enhanced executor with context loading capability.
        
        Args:
            timeout_seconds: Maximum time to wait for Claude CLI response
            project_root: Root directory for project context loading
        """
        super().__init__(timeout_seconds)
        self.project_root = Path(project_root).resolve()
        self.config_loader = VibeCheckConfigLoader(str(self.project_root))
        self._context_cache: Optional[AnalysisContext] = None
        self._context_cache_time: float = 0
        self._context_cache_ttl: int = 300  # 5 minutes default
    
    def _load_vibe_check_config(self) -> Optional[VibeCheckConfig]:
        """
        Load .vibe-check/config.json configuration if available.
        
        Returns:
            VibeCheckConfig object or None if not available/enabled
        """
        try:
            config = self.config_loader.load_config()
            if config.context_loading and config.context_loading.enabled:
                self._context_cache_ttl = config.context_loading.cache_duration_minutes * 60
                return config
        except Exception as e:
            logger.debug(f"Could not load vibe-check config: {e}")
        
        return None
    
    def _load_project_context_file(self) -> Optional[str]:
        """
        Load project-context.md file if it exists.
        
        Returns:
            Content of project-context.md or None if not found
        """
        context_file_path = self.project_root / ".vibe-check" / "project-context.md"
        
        if not context_file_path.exists():
            logger.debug(f"Project context file not found: {context_file_path}")
            return None
        
        try:
            with open(context_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                logger.debug(f"Loaded project context from {context_file_path}")
                return content
        except Exception as e:
            logger.warning(f"Error reading project context file: {e}")
            return None
    
    def _load_project_context_if_enabled(self) -> Optional[str]:
        """
        Load project-specific context if configuration enables it.
        
        Returns:
            Combined project context string or None if disabled/unavailable
        """
        # Check if context enhancement is enabled
        config = self._load_vibe_check_config()
        if not config:
            return None
        
        context_parts = []
        
        # Load project-context.md file
        project_context = self._load_project_context_file()
        if project_context:
            context_parts.append("## Project-Specific Context\n\n" + project_context)
        
        # Load pattern exceptions
        pattern_exceptions_path = self.project_root / ".vibe-check" / "pattern-exceptions.json"
        if pattern_exceptions_path.exists():
            try:
                with open(pattern_exceptions_path, 'r', encoding='utf-8') as f:
                    exceptions = json.load(f)
                
                if exceptions.get("approved_patterns") or exceptions.get("temporary_exceptions"):
                    exception_text = "## Approved Pattern Exceptions\n\n"
                    
                    approved = exceptions.get("approved_patterns", [])
                    if approved:
                        exception_text += "**Approved Patterns:**\n"
                        for pattern in approved:
                            reasoning = exceptions.get("reasoning", {}).get(pattern, "No reasoning provided")
                            exception_text += f"- {pattern}: {reasoning}\n"
                    
                    temporary = exceptions.get("temporary_exceptions", [])
                    if temporary:
                        exception_text += "\n**Temporary Exceptions:**\n"
                        for pattern in temporary:
                            exception_text += f"- {pattern}\n"
                    
                    context_parts.append(exception_text)
            except Exception as e:
                logger.warning(f"Error loading pattern exceptions: {e}")
        
        return "\n\n".join(context_parts) if context_parts else None
    
    def _get_cached_analysis_context(self, force_refresh: bool = False) -> Optional[AnalysisContext]:
        """
        Get cached analysis context or load fresh if expired.
        
        Args:
            force_refresh: Force refresh of cached context
            
        Returns:
            AnalysisContext object or None if unavailable
        """
        current_time = time.time()
        
        # Return cached context if valid and not forcing refresh
        if (not force_refresh and 
            self._context_cache and 
            (current_time - self._context_cache_time) < self._context_cache_ttl):
            logger.debug("Using cached analysis context")
            return self._context_cache
        
        # Load fresh context
        try:
            context_manager = get_context_manager(str(self.project_root))
            self._context_cache = context_manager.get_project_context(force_refresh=force_refresh)
            self._context_cache_time = current_time
            logger.debug("Loaded fresh analysis context")
            return self._context_cache
        except Exception as e:
            logger.warning(f"Could not load analysis context: {e}")
            return None
    
    def _load_library_context(self, detected_libraries: Optional[List[str]] = None) -> Optional[str]:
        """
        Load library-specific context using existing LibraryDetectionEngine.
        
        Args:
            detected_libraries: Optional list of specific libraries to load context for
            
        Returns:
            Library context string or None if unavailable
        """
        config = self._load_vibe_check_config()
        if not config or not config.context_loading.library_detection:
            return None
        
        try:
            analysis_context = self._get_cached_analysis_context()
            if not analysis_context or not analysis_context.library_docs:
                return None
            
            library_summaries = []
            
            # Focus on key libraries or use detected libraries
            libraries_to_include = detected_libraries or list(analysis_context.library_docs.keys())[:5]  # Limit to 5
            
            for library in libraries_to_include:
                if library in analysis_context.library_docs:
                    docs = analysis_context.library_docs[library]
                    if docs:
                        # Truncate docs to reasonable size for prompt injection
                        truncated_docs = docs[:500] + "..." if len(docs) > 500 else docs
                        library_summaries.append(f"### {library}\n{truncated_docs}")
            
            if library_summaries:
                return "## Library Context\n\n" + "\n\n".join(library_summaries)
            
        except Exception as e:
            logger.warning(f"Error loading library context: {e}")
        
        return None
    
    def _get_system_prompt(self, task_type: str) -> str:
        """
        Get specialized system prompt enhanced with project context.
        
        Args:
            task_type: Type of analysis task
            
        Returns:
            System prompt for the specific task, including project context if available
        """
        # Get base system prompt from parent class
        base_prompt = super()._get_system_prompt(task_type)
        
        # Attempt to load project context
        project_context = self._load_project_context_if_enabled()
        library_context = self._load_library_context()
        
        # Build enhanced prompt with context
        prompt_parts = [base_prompt]
        
        if project_context:
            prompt_parts.append(f"\n## Additional Project Context\n\n{project_context}")
            logger.info("Injected project-specific context into prompt")
        
        if library_context:
            prompt_parts.append(f"\n{library_context}")
            logger.info("Injected library-specific context into prompt")
        
        if not project_context and not library_context:
            logger.debug("No additional context available - using base prompt")
        
        return "\n".join(prompt_parts)
    
    def _get_claude_args(self, prompt: str, task_type: str, model: str = "sonnet") -> List[str]:
        """
        Build Claude CLI arguments with enhanced context injection.
        
        This overrides the parent method to inject context at the prompt level
        rather than at the system prompt level for better integration.
        
        Args:
            prompt: The prompt to send to Claude
            task_type: Type of task for specialized handling
            model: Claude model to use
            
        Returns:
            List of command line arguments with context-enhanced prompts
        """
        # Get context to inject into user prompt
        project_context = self._load_project_context_if_enabled()
        library_context = self._load_library_context()
        
        # Build context-enhanced prompt
        if project_context or library_context:
            enhanced_prompt_parts = []
            
            if project_context:
                enhanced_prompt_parts.append(project_context)
            
            if library_context:
                enhanced_prompt_parts.append(library_context)
            
            # Add original prompt
            enhanced_prompt_parts.append("## Analysis Request\n\n" + prompt)
            
            enhanced_prompt = "\n\n".join(enhanced_prompt_parts)
            logger.info("Enhanced prompt with project and library context")
        else:
            enhanced_prompt = prompt
            logger.debug("No context enhancement available")
        
        # Call parent method with enhanced prompt
        return super()._get_claude_args(enhanced_prompt, task_type, model)