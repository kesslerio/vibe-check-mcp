"""
Token Counting Utilities for MCP Token Limit Bypass

Provides accurate token counting using tiktoken for intelligent content splitting
and file-based communication when approaching MCP's 25K token limit.
"""

import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available - falling back to character-based estimation")


class TokenCounter:
    """
    Accurate token counting utility using tiktoken.
    
    Provides precise token counts for different Claude models and
    fallback character-based estimation when tiktoken is unavailable.
    """
    
    # MCP protocol limits
    MCP_TOKEN_LIMIT = 25000
    FILE_MODE_THRESHOLD = 20000  # Switch to file mode before hitting limit
    CHUNKED_MODE_THRESHOLD = 50000  # Use chunking for very large content
    
    # Character-to-token estimation ratios by content type
    CHAR_TO_TOKEN_RATIOS = {
        "code": 4.0,      # Code is typically ~4 chars per token
        "text": 4.5,      # Natural text is slightly higher
        "mixed": 4.2,     # Mixed content average
        "default": 4.0    # Conservative default
    }
    
    def __init__(self, model: str = "claude-3-sonnet-20240229"):
        """
        Initialize token counter for specific model.
        
        Args:
            model: Claude model name for tiktoken encoding
        """
        self.model = model
        self.encoder = None
        
        if TIKTOKEN_AVAILABLE:
            try:
                # Try to get encoding for the specific model
                self.encoder = tiktoken.encoding_for_model("gpt-4")  # Use GPT-4 as proxy for Claude
                logger.debug(f"TokenCounter initialized with tiktoken for model: {model}")
            except Exception as e:
                logger.warning(f"Failed to initialize tiktoken encoder: {e}")
                self.encoder = None
        
        if not self.encoder:
            logger.info("Using character-based token estimation")
    
    def count_tokens(self, text: str, content_type: str = "mixed") -> int:
        """
        Count tokens in text using tiktoken or character-based estimation.
        
        Args:
            text: Text content to count tokens for
            content_type: Type of content for estimation ("code", "text", "mixed")
            
        Returns:
            Number of tokens in the text
        """
        if not text:
            return 0
        
        if self.encoder:
            try:
                return len(self.encoder.encode(text))
            except Exception as e:
                logger.warning(f"tiktoken encoding failed, falling back to estimation: {e}")
        
        # Fallback to character-based estimation
        return self.estimate_tokens_from_chars(len(text), content_type)
    
    def estimate_tokens_from_chars(self, char_count: int, content_type: str = "mixed") -> int:
        """
        Estimate token count from character count.
        
        Args:
            char_count: Number of characters
            content_type: Type of content for estimation
            
        Returns:
            Estimated number of tokens
        """
        ratio = self.CHAR_TO_TOKEN_RATIOS.get(content_type, self.CHAR_TO_TOKEN_RATIOS["default"])
        return int(char_count / ratio)
    
    def should_use_file_mode(self, text: str, threshold: Optional[int] = None) -> bool:
        """
        Determine if file-based communication should be used.
        
        Args:
            text: Text content to evaluate
            threshold: Custom threshold (defaults to FILE_MODE_THRESHOLD)
            
        Returns:
            True if file mode should be used
        """
        if threshold is None:
            threshold = self.FILE_MODE_THRESHOLD
        
        token_count = self.count_tokens(text)
        should_use_file = token_count > threshold
        
        if should_use_file:
            logger.info(f"🗂️ File mode recommended: {token_count} tokens > {threshold}")
        
        return should_use_file
    
    def should_use_chunked_mode(self, text: str, threshold: Optional[int] = None) -> bool:
        """
        Determine if chunked analysis should be used.
        
        Args:
            text: Text content to evaluate
            threshold: Custom threshold (defaults to CHUNKED_MODE_THRESHOLD)
            
        Returns:
            True if chunked mode should be used
        """
        if threshold is None:
            threshold = self.CHUNKED_MODE_THRESHOLD
        
        token_count = self.count_tokens(text)
        should_use_chunked = token_count > threshold
        
        if should_use_chunked:
            logger.info(f"🧩 Chunked mode recommended: {token_count} tokens > {threshold}")
        
        return should_use_chunked
    
    def get_content_analysis_mode(self, text: str) -> str:
        """
        Determine the appropriate analysis mode based on token count.
        
        Args:
            text: Text content to evaluate
            
        Returns:
            Analysis mode: "standard", "file_based", or "chunked"
        """
        token_count = self.count_tokens(text)
        
        if token_count <= self.FILE_MODE_THRESHOLD:
            return "standard"
        elif token_count <= self.CHUNKED_MODE_THRESHOLD:
            return "file_based"
        else:
            return "chunked"
    
    def split_content_by_tokens(
        self, 
        text: str, 
        max_tokens_per_chunk: int, 
        overlap_tokens: int = 200
    ) -> list[str]:
        """
        Split content into chunks based on token limits.
        
        Args:
            text: Text content to split
            max_tokens_per_chunk: Maximum tokens per chunk
            overlap_tokens: Overlap tokens between chunks for context
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        total_tokens = self.count_tokens(text)
        
        if total_tokens <= max_tokens_per_chunk:
            return [text]
        
        chunks = []
        lines = text.split('\n')
        current_chunk_lines = []
        current_chunk_tokens = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line + '\n')
            
            # If single line exceeds chunk size, add it as its own chunk
            if line_tokens > max_tokens_per_chunk:
                if current_chunk_lines:
                    chunks.append('\n'.join(current_chunk_lines))
                    current_chunk_lines = []
                    current_chunk_tokens = 0
                
                # Split very long lines by characters as fallback
                if len(line) > max_tokens_per_chunk * 4:  # Rough char estimate
                    chunk_size = max_tokens_per_chunk * 4
                    for i in range(0, len(line), chunk_size):
                        chunks.append(line[i:i + chunk_size])
                else:
                    chunks.append(line)
                continue
            
            # Check if adding this line would exceed the chunk limit
            if current_chunk_tokens + line_tokens > max_tokens_per_chunk and current_chunk_lines:
                chunks.append('\n'.join(current_chunk_lines))
                
                # Start new chunk with overlap if possible
                if overlap_tokens > 0 and len(current_chunk_lines) > 1:
                    # Calculate how many lines to include for overlap
                    overlap_lines = []
                    overlap_token_count = 0
                    
                    for prev_line in reversed(current_chunk_lines):
                        prev_line_tokens = self.count_tokens(prev_line + '\n')
                        if overlap_token_count + prev_line_tokens <= overlap_tokens:
                            overlap_lines.insert(0, prev_line)
                            overlap_token_count += prev_line_tokens
                        else:
                            break
                    
                    current_chunk_lines = overlap_lines
                    current_chunk_tokens = overlap_token_count
                else:
                    current_chunk_lines = []
                    current_chunk_tokens = 0
            
            current_chunk_lines.append(line)
            current_chunk_tokens += line_tokens
        
        # Add final chunk if there are remaining lines
        if current_chunk_lines:
            chunks.append('\n'.join(current_chunk_lines))
        
        logger.info(f"Split {total_tokens} tokens into {len(chunks)} chunks (max {max_tokens_per_chunk} tokens each)")
        return chunks
    
    def log_token_analysis(self, text: str, context: str = "") -> dict:
        """
        Log detailed token analysis for debugging.
        
        Args:
            text: Text to analyze
            context: Context description for logging
            
        Returns:
            Analysis details as dictionary
        """
        char_count = len(text)
        token_count = self.count_tokens(text)
        mode = self.get_content_analysis_mode(text)
        
        analysis = {
            "context": context,
            "character_count": char_count,
            "token_count": token_count,
            "analysis_mode": mode,
            "file_mode_needed": self.should_use_file_mode(text),
            "chunked_mode_needed": self.should_use_chunked_mode(text),
            "encoding_method": "tiktoken" if self.encoder else "character_estimation"
        }
        
        logger.info(f"📊 Token Analysis{' - ' + context if context else ''}")
        logger.info(f"📏 Content: {char_count:,} chars, {token_count:,} tokens")
        logger.info(f"🔄 Mode: {mode} ({analysis['encoding_method']})")
        
        return analysis


# Global token counter instance
_global_token_counter: Optional[TokenCounter] = None


def get_token_counter() -> TokenCounter:
    """Get the global token counter instance."""
    global _global_token_counter
    
    if _global_token_counter is None:
        _global_token_counter = TokenCounter()
    
    return _global_token_counter


def count_tokens(text: str, content_type: str = "mixed") -> int:
    """
    Convenience function to count tokens using global counter.
    
    Args:
        text: Text content to count
        content_type: Type of content for estimation
        
    Returns:
        Number of tokens in the text
    """
    counter = get_token_counter()
    return counter.count_tokens(text, content_type)


def analyze_content_size(text: str, context: str = "") -> dict:
    """
    Convenience function to analyze content size and determine mode.
    
    Args:
        text: Text content to analyze
        context: Context description
        
    Returns:
        Analysis details dictionary
    """
    counter = get_token_counter()
    return counter.log_token_analysis(text, context)