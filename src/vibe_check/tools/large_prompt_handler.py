"""
Simple Large Prompt Handler (Zen-style)

Implements the minimal approach inspired by Zen MCP server:
1. Detect prompts >50K characters
2. Ask Claude to save to file and resubmit
3. Handle file input when provided

No complex token counting, no multiple modes - just the simplest solution that works.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LargePromptHandler:
    """Simple handler for large prompts using file-based approach."""
    
    # Simple character-based threshold (no tiktoken needed!)
    CHARACTER_LIMIT = 50000  # 50K characters as per Zen MCP
    
    def __init__(self):
        logger.info(f"LargePromptHandler initialized with {self.CHARACTER_LIMIT:,} character limit")
    
    def should_use_file_mode(self, prompt: str) -> bool:
        """Check if prompt exceeds character limit."""
        char_count = len(prompt)
        should_use_file = char_count > self.CHARACTER_LIMIT
        
        if should_use_file:
            logger.info(f"Large prompt detected: {char_count:,} chars > {self.CHARACTER_LIMIT:,}")
        
        return should_use_file
    
    def get_file_mode_response(self, original_prompt: str) -> Dict[str, Any]:
        """Return the standard response asking Claude to save to file."""
        char_count = len(original_prompt)
        
        response = {
            "status": "prompt_too_large",
            "character_count": char_count,
            "limit": self.CHARACTER_LIMIT,
            "message": (
                f"The prompt is too large for MCP's limits ({char_count:,} characters > {self.CHARACTER_LIMIT:,}). "
                "Please save the prompt text to a temporary file named 'prompt.txt' and resend "
                "the request with an empty prompt string, including the absolute file path in the "
                "files parameter along with any other files you wish to share as context."
            ),
            "instructions": [
                "Save your prompt to a file (e.g., /tmp/prompt.txt)",
                "Resend the request with the file path",
                "Include any other relevant files as context"
            ]
        }
        
        logger.info(f"Requesting file mode for {char_count:,} character prompt")
        return response
    
    def read_from_file(self, file_path: str) -> Optional[str]:
        """Read content from the provided file path."""
        if not file_path:
            return None
            
        try:
            # Ensure file exists and is readable
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            if not os.path.isfile(file_path):
                logger.error(f"Path is not a file: {file_path}")
                return None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            char_count = len(content)
            logger.info(f"Successfully read {char_count:,} characters from {file_path}")
            
            return content
            
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode file {file_path}: {e}")
            return None
        except PermissionError as e:
            logger.error(f"Permission denied reading {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading {file_path}: {e}")
            return None
    
    def handle_request(self, prompt: str, files: Optional[list] = None) -> Dict[str, Any]:
        """
        Main handler for requests that may contain large prompts.
        
        Args:
            prompt: The prompt text
            files: Optional list of file paths
            
        Returns:
            Either the content to process or instructions to use file mode
        """
        # Check if we have files provided (file mode)
        if files and len(files) > 0:
            # Look for prompt.txt or similar
            for file_path in files:
                if 'prompt' in os.path.basename(file_path).lower():
                    content = self.read_from_file(file_path)
                    if content:
                        logger.info(f"Using file mode: loaded {len(content):,} chars from {file_path}")
                        return {
                            "status": "file_mode_success",
                            "content": content,
                            "source": file_path,
                            "character_count": len(content)
                        }
        
        # Check if prompt is too large for direct processing
        if self.should_use_file_mode(prompt):
            return self.get_file_mode_response(prompt)
        
        # Normal processing for small prompts
        return {
            "status": "normal_mode",
            "content": prompt,
            "character_count": len(prompt)
        }


# Global handler instance
_global_handler: Optional[LargePromptHandler] = None

def get_large_prompt_handler() -> LargePromptHandler:
    """Get the global large prompt handler instance."""
    global _global_handler
    
    if _global_handler is None:
        _global_handler = LargePromptHandler()
    
    return _global_handler

def handle_large_prompt(prompt: str, files: Optional[list] = None) -> Dict[str, Any]:
    """
    Convenience function for large prompt handling.
    
    Args:
        prompt: The prompt text
        files: Optional list of file paths
        
    Returns:
        Processed result or file mode instructions
    """
    handler = get_large_prompt_handler()
    return handler.handle_request(prompt, files)