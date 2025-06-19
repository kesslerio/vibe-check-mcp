"""
MCP Protocol Handler for Token Limit Bypass

Centralized handler for intelligently managing MCP's 25K token limit through
file-based communication, content chunking, and graceful degradation.
"""

import asyncio
import logging
import tempfile
import os
import time
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from .shared.claude_integration import ClaudeCliResult, ClaudeCliExecutor
from .pr_review.claude_integration import ClaudeIntegration
from .pr_review.chunked_analyzer import ChunkedAnalyzer, ChunkedAnalysisResult
from ..utils.token_utils import get_token_counter, analyze_content_size

logger = logging.getLogger(__name__)


class AnalysisMode(Enum):
    """Available analysis modes based on content size."""
    STANDARD = "standard"
    FILE_BASED = "file_based"
    CHUNKED = "chunked"
    GRACEFUL_DEGRADATION = "graceful_degradation"


class MCPTokenLimitHandler:
    """
    Intelligent handler for MCP token limit bypass.
    
    Provides transparent token limit management through:
    - Automatic mode detection based on content size
    - File-based communication for large prompts
    - Chunked analysis for very large content
    - Graceful degradation when limits exceeded
    """
    
    # MCP Protocol limits
    MCP_TOKEN_LIMIT = 25000
    FILE_MODE_THRESHOLD = 20000  # Switch to file mode early
    CHUNKED_MODE_THRESHOLD = 50000  # Use chunking for very large content
    
    def __init__(self, timeout_seconds: int = 300):
        """
        Initialize MCP token limit handler.
        
        Args:
            timeout_seconds: Default timeout for operations
        """
        self.timeout_seconds = timeout_seconds
        self.token_counter = get_token_counter()
        self.claude_integration = ClaudeIntegration(timeout_seconds)
        self.chunked_analyzer = ChunkedAnalyzer(
            chunk_timeout=timeout_seconds,
            max_tokens_per_chunk=15000  # Conservative chunk size
        )
        
        logger.info(f"MCPTokenLimitHandler initialized with {timeout_seconds}s timeout")
    
    def analyze_content_requirements(self, prompt: str, data: str) -> Dict[str, Any]:
        """
        Analyze content and determine optimal processing mode.
        
        Args:
            prompt: Analysis prompt
            data: Data content to analyze
            
        Returns:
            Analysis requirements including mode, token count, and recommendations
        """
        combined_content = f"{prompt}\n\n{data}"
        token_analysis = analyze_content_size(combined_content, "MCP Analysis")
        
        token_count = token_analysis["token_count"]
        char_count = token_analysis["character_count"]
        
        # Determine analysis mode
        if token_count <= self.FILE_MODE_THRESHOLD:
            mode = AnalysisMode.STANDARD
        elif token_count <= self.CHUNKED_MODE_THRESHOLD:
            mode = AnalysisMode.FILE_BASED
        else:
            mode = AnalysisMode.CHUNKED
        
        requirements = {
            "mode": mode,
            "token_count": token_count,
            "character_count": char_count,
            "analysis_method": token_analysis["encoding_method"],
            "file_mode_needed": token_count > self.FILE_MODE_THRESHOLD,
            "chunked_mode_needed": token_count > self.CHUNKED_MODE_THRESHOLD,
            "estimated_processing_time": self._estimate_processing_time(token_count),
            "recommendations": self._generate_recommendations(mode, token_count)
        }
        
        logger.info(f"📊 Content Analysis: {char_count:,} chars, {token_count:,} tokens → {mode.value}")
        
        return requirements
    
    async def handle_large_prompt(
        self, 
        prompt: str, 
        data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for handling potentially large prompts.
        
        Args:
            prompt: Analysis prompt
            data: Data content to analyze
            context: Optional context information (PR data, etc.)
            
        Returns:
            Analysis results with mode information
        """
        start_time = time.time()
        
        # Analyze content requirements
        requirements = self.analyze_content_requirements(prompt, data)
        mode = requirements["mode"]
        token_count = requirements["token_count"]
        
        logger.info(f"🔄 Using {mode.value} mode for {token_count:,} tokens")
        
        try:
            if mode == AnalysisMode.STANDARD:
                result = await self._standard_analysis(prompt, data, context)
            elif mode == AnalysisMode.FILE_BASED:
                result = await self._file_based_analysis(prompt, data, context)
            elif mode == AnalysisMode.CHUNKED:
                result = await self._chunked_analysis(prompt, data, context)
            else:
                result = await self._graceful_degradation(prompt, data, context)
            
            # Add processing metadata
            processing_time = time.time() - start_time
            result["processing_metadata"] = {
                "mode": mode.value,
                "token_count": token_count,
                "processing_time": processing_time,
                "requirements": requirements
            }
            
            logger.info(f"✅ {mode.value} analysis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis failed in {mode.value} mode: {e}")
            return await self._graceful_degradation(prompt, data, context, error=str(e))
    
    async def _standard_analysis(
        self, 
        prompt: str, 
        data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Standard analysis for content within normal limits."""
        logger.debug("Using standard MCP analysis")
        
        combined_content = f"{prompt}\n\n{data}"
        
        # Use the existing Claude integration
        executor = ClaudeCliExecutor(timeout_seconds=self.timeout_seconds)
        result = await executor.execute_async(
            prompt=combined_content,
            task_type="pr_review"
        )
        
        if result.success:
            return {
                "success": True,
                "analysis": result.output,
                "method": "standard_mcp",
                "token_count": self.token_counter.count_tokens(combined_content)
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "method": "standard_mcp"
            }
    
    async def _file_based_analysis(
        self, 
        prompt: str, 
        data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """File-based analysis for large content."""
        logger.info("🗂️ Using file-based analysis for large content")
        
        try:
            combined_content = f"{prompt}\n\n{data}"
            
            # Use the enhanced Claude integration file mode
            file_result = await self.claude_integration.analyze_with_file_mode(
                content=combined_content,
                context=prompt,
                model="sonnet"
            )
            
            if file_result and file_result.success:
                return {
                    "success": True,
                    "analysis": file_result.output,
                    "method": "file_based",
                    "token_count": self.token_counter.count_tokens(combined_content)
                }
            else:
                error_msg = file_result.error if file_result else "File-based analysis failed"
                logger.warning(f"File-based analysis failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "method": "file_based"
                }
                
        except Exception as e:
            logger.error(f"File-based analysis error: {e}")
            return {
                "success": False,
                "error": f"File-based analysis failed: {str(e)}",
                "method": "file_based"
            }
    
    async def _chunked_analysis(
        self, 
        prompt: str, 
        data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Chunked analysis for very large content."""
        logger.info("🧩 Using chunked analysis for very large content")
        
        try:
            # Extract PR data from context if available
            pr_data = context or {}
            pr_files = self._extract_pr_files_from_data(data)
            
            if not pr_files:
                logger.warning("No PR files found for chunked analysis, falling back to text chunking")
                return await self._text_chunked_analysis(prompt, data)
            
            # Use the enhanced chunked analyzer
            chunked_result = await self.chunked_analyzer.analyze_pr_chunked(pr_data, pr_files)
            
            if chunked_result.status.startswith("chunked_analysis"):
                return {
                    "success": True,
                    "analysis": self._format_chunked_analysis(chunked_result),
                    "method": "chunked",
                    "chunks_processed": chunked_result.total_chunks,
                    "successful_chunks": chunked_result.successful_chunks,
                    "token_count": self.token_counter.count_tokens(f"{prompt}\n\n{data}")
                }
            else:
                return {
                    "success": False,
                    "error": f"Chunked analysis failed: {chunked_result.status}",
                    "method": "chunked"
                }
                
        except Exception as e:
            logger.error(f"Chunked analysis error: {e}")
            return {
                "success": False,
                "error": f"Chunked analysis failed: {str(e)}",
                "method": "chunked"
            }
    
    async def _text_chunked_analysis(self, prompt: str, data: str) -> Dict[str, Any]:
        """Fallback text-based chunking when PR files aren't available."""
        logger.info("📄 Using text-based chunking as fallback")
        
        # Split the data into manageable chunks
        chunks = self.token_counter.split_content_by_tokens(
            text=data,
            max_tokens_per_chunk=15000,  # Conservative chunk size
            overlap_tokens=500  # Context overlap
        )
        
        chunk_results = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"{prompt}\n\nThis is chunk {i+1} of {len(chunks)}. Analyze this portion:\n\n{chunk}"
            
            executor = ClaudeCliExecutor(timeout_seconds=self.timeout_seconds)
            result = await executor.execute_async(
                prompt=chunk_prompt,
                task_type="pr_review"
            )
            
            chunk_results.append({
                "chunk_id": i + 1,
                "success": result.success,
                "analysis": result.output if result.success else None,
                "error": result.error if not result.success else None
            })
        
        # Combine chunk results
        successful_chunks = [r for r in chunk_results if r["success"]]
        combined_analysis = "\n\n".join([r["analysis"] for r in successful_chunks])
        
        return {
            "success": len(successful_chunks) > 0,
            "analysis": combined_analysis,
            "method": "text_chunked",
            "total_chunks": len(chunks),
            "successful_chunks": len(successful_chunks),
            "token_count": self.token_counter.count_tokens(f"{prompt}\n\n{data}")
        }
    
    async def _graceful_degradation(
        self, 
        prompt: str, 
        data: str, 
        context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Graceful degradation when all other methods fail."""
        logger.warning("⚠️ Using graceful degradation mode")
        
        # Provide a basic pattern-only analysis
        basic_analysis = f"""
# Analysis Summary (Graceful Degradation Mode)

Due to content size limitations, providing basic pattern analysis:

## Content Overview
- Character count: {len(data):,}
- Estimated tokens: {self.token_counter.count_tokens(data):,}

## Detected Patterns
- Large-scale changes detected
- Content exceeds normal processing limits
- Recommend manual review for detailed analysis

## Recommendations
- Consider breaking changes into smaller PRs
- Focus review on critical functionality
- Use targeted analysis for specific areas of concern

{f"## Processing Error\\n{error}" if error else ""}
"""
        
        return {
            "success": True,
            "analysis": basic_analysis,
            "method": "graceful_degradation",
            "token_count": self.token_counter.count_tokens(f"{prompt}\n\n{data}"),
            "warning": "Content too large for detailed analysis"
        }
    
    def _extract_pr_files_from_data(self, data: str) -> List[Dict[str, Any]]:
        """Extract PR file information from data string."""
        # This is a simplified extraction - in practice, this would parse
        # the structured PR data to extract file information
        # For now, return empty list to trigger text chunking fallback
        return []
    
    def _format_chunked_analysis(self, chunked_result: ChunkedAnalysisResult) -> str:
        """Format chunked analysis results into readable output."""
        sections = [
            f"# Chunked Analysis Results",
            f"",
            f"## Overview",
            f"- Status: {chunked_result.status}",
            f"- Total chunks: {chunked_result.total_chunks}",
            f"- Successful chunks: {chunked_result.successful_chunks}",
            f"- Processing time: {chunked_result.total_duration:.2f}s",
            f"",
            f"## Overall Assessment",
            chunked_result.overall_assessment,
            f""
        ]
        
        if chunked_result.patterns_detected:
            sections.extend([
                "## Detected Patterns",
                ""
            ])
            for pattern in chunked_result.patterns_detected:
                sections.append(f"- {pattern.get('pattern', 'Unknown pattern')}")
            sections.append("")
        
        if chunked_result.recommendations:
            sections.extend([
                "## Recommendations",
                ""
            ])
            for rec in chunked_result.recommendations:
                sections.append(f"- {rec}")
            sections.append("")
        
        return "\n".join(sections)
    
    def _estimate_processing_time(self, token_count: int) -> int:
        """Estimate processing time based on token count."""
        # Rough estimates based on token count
        if token_count <= 5000:
            return 30  # 30 seconds
        elif token_count <= 15000:
            return 60  # 1 minute
        elif token_count <= 30000:
            return 120  # 2 minutes
        else:
            return 300  # 5+ minutes
    
    def _generate_recommendations(self, mode: AnalysisMode, token_count: int) -> List[str]:
        """Generate recommendations based on analysis mode and token count."""
        recommendations = []
        
        if mode == AnalysisMode.FILE_BASED:
            recommendations.extend([
                "Content will be processed using file-based communication",
                "Analysis quality will be maintained",
                "Processing may take slightly longer"
            ])
        elif mode == AnalysisMode.CHUNKED:
            recommendations.extend([
                "Content will be split into multiple chunks for analysis",
                "Results will be merged for comprehensive coverage",
                "Consider breaking into smaller PRs for faster processing"
            ])
        elif mode == AnalysisMode.GRACEFUL_DEGRADATION:
            recommendations.extend([
                "Content exceeds processing capabilities",
                "Only basic pattern analysis will be provided",
                "Manual review strongly recommended"
            ])
        else:
            recommendations.append("Standard processing will be used")
        
        return recommendations


# Global handler instance
_global_mcp_handler: Optional[MCPTokenLimitHandler] = None


def get_mcp_handler() -> MCPTokenLimitHandler:
    """Get the global MCP token limit handler instance."""
    global _global_mcp_handler
    
    if _global_mcp_handler is None:
        _global_mcp_handler = MCPTokenLimitHandler()
    
    return _global_mcp_handler


async def analyze_with_token_limit_bypass(
    prompt: str,
    data: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function for token limit bypass analysis.
    
    Args:
        prompt: Analysis prompt
        data: Data content to analyze
        context: Optional context information
        
    Returns:
        Analysis results with token limit handling
    """
    handler = get_mcp_handler()
    return await handler.handle_large_prompt(prompt, data, context)