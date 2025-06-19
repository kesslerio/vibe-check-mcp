"""
Chunked PR Analysis Engine

Implements intelligent chunked analysis for medium-sized PRs that are too large
for single-pass analysis but still manageable with chunking.

Part of Phase 3 implementation for Issue #103.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from ..shared.pr_classifier import PrSizeCategory, PrSizeMetrics, classify_pr_size
from ..shared.claude_integration import analyze_content_async_with_circuit_breaker
from ...utils.token_utils import get_token_counter, analyze_content_size
from ..shared.circuit_breaker import ClaudeCliError, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


@dataclass
class FileChunk:
    """Represents a chunk of files for analysis."""
    chunk_id: int
    files: List[Dict[str, Any]]
    total_lines: int
    estimated_complexity: float
    file_types: List[str] = field(default_factory=list)
    estimated_tokens: int = 0  # Estimated token count for this chunk
    
    @property
    def file_count(self) -> int:
        return len(self.files)
    
    @property
    def filenames(self) -> List[str]:
        return [f.get('filename', f.get('name', 'unknown')) for f in self.files]
    
    def calculate_token_estimate(self, token_counter) -> int:
        """Calculate estimated token count for this chunk's content."""
        if not self.files:
            return 0
        
        # Estimate tokens based on patches/diffs in files
        total_content = ""
        for file_data in self.files:
            patch = file_data.get('patch', '')
            if patch:
                total_content += patch + "\n"
        
        if total_content:
            self.estimated_tokens = token_counter.count_tokens(total_content, "code")
        else:
            # Fallback: estimate from line count (roughly 10 tokens per line for code)
            self.estimated_tokens = self.total_lines * 10
        
        return self.estimated_tokens


@dataclass
class ChunkAnalysisResult:
    """Result of analyzing a single chunk."""
    chunk_id: int
    success: bool
    duration: float
    
    # Analysis content
    patterns_detected: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: str = ""
    raw_analysis: str = ""
    
    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    files_analyzed: List[str] = field(default_factory=list)
    lines_analyzed: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ChunkedAnalysisResult:
    """Complete result of chunked PR analysis."""
    
    # Overall status
    status: str
    analysis_mode: str = "chunked_llm_analysis"
    total_chunks: int = 0
    successful_chunks: int = 0
    failed_chunks: int = 0
    total_duration: float = 0
    
    # Aggregated results
    patterns_detected: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    overall_assessment: str = ""
    
    # Chunk details
    chunk_summaries: List[Dict[str, Any]] = field(default_factory=list)
    chunk_results: List[ChunkAnalysisResult] = field(default_factory=list)
    
    # Metadata
    pr_metrics: Optional[PrSizeMetrics] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class FileChunker:
    """
    Intelligent file chunking strategy for PR analysis.
    
    Groups files into logical chunks based on token count, size, type, and relationships
    to optimize analysis quality and performance while respecting MCP token limits.
    """
    
    def __init__(self, max_lines_per_chunk: int = 500, max_tokens_per_chunk: int = 15000):
        self.max_lines_per_chunk = max_lines_per_chunk
        self.max_tokens_per_chunk = max_tokens_per_chunk  # Conservative token limit per chunk
        self.token_counter = get_token_counter()
        logger.debug(f"FileChunker initialized with max {max_lines_per_chunk} lines, {max_tokens_per_chunk} tokens per chunk")
    
    def create_chunks(self, pr_files: List[Dict[str, Any]]) -> List[FileChunk]:
        """
        Create intelligent file chunks for analysis.
        
        Args:
            pr_files: List of file data from PR
            
        Returns:
            List of file chunks optimized for analysis
        """
        if not pr_files:
            return []
        
        # Enhance file data with analysis metadata
        enhanced_files = [self._enhance_file_data(f) for f in pr_files]
        
        # Sort files by priority for optimal chunking
        sorted_files = self._sort_files_by_priority(enhanced_files)
        
        # Create chunks using intelligent grouping
        chunks = self._group_files_into_chunks(sorted_files)
        
        logger.info(
            f"Created {len(chunks)} chunks from {len(pr_files)} files",
            extra={
                "total_files": len(pr_files),
                "chunk_count": len(chunks),
                "avg_files_per_chunk": len(pr_files) / max(len(chunks), 1)
            }
        )
        
        return chunks
    
    def _enhance_file_data(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance file data with metadata for chunking decisions."""
        enhanced = file_data.copy()
        
        # Calculate file changes
        changes = (
            enhanced.get('changes', 0) or
            enhanced.get('additions', 0) + enhanced.get('deletions', 0)
        )
        enhanced['total_changes'] = changes
        
        # Extract file metadata
        filename = enhanced.get('filename', enhanced.get('name', ''))
        enhanced['filename'] = filename
        enhanced['extension'] = self._get_file_extension(filename)
        enhanced['file_type'] = self._classify_file_type(filename)
        enhanced['complexity_score'] = self._calculate_complexity_score(enhanced)
        
        return enhanced
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension."""
        if '.' in filename:
            return filename.split('.')[-1].lower()
        return ''
    
    def _classify_file_type(self, filename: str) -> str:
        """Classify file into broad categories."""
        extension = self._get_file_extension(filename)
        
        # Programming languages
        if extension in ['py', 'js', 'ts', 'java', 'cpp', 'c', 'go', 'rust', 'rb']:
            return 'code'
        elif extension in ['html', 'css', 'scss', 'sass']:
            return 'frontend'
        elif extension in ['json', 'yaml', 'yml', 'xml', 'toml']:
            return 'config'
        elif extension in ['md', 'txt', 'rst']:
            return 'documentation'
        elif extension in ['sql']:
            return 'database'
        elif extension in ['sh', 'bash', 'ps1']:
            return 'script'
        else:
            return 'other'
    
    def _calculate_complexity_score(self, file_data: Dict[str, Any]) -> float:
        """Calculate complexity score for chunking priority."""
        changes = file_data.get('total_changes', 0)
        filename = file_data.get('filename', '')
        
        # Base score from change count
        score = min(changes / 100.0, 1.0)  # Normalize to 0-1
        
        # Adjust based on file type
        if file_data.get('file_type') == 'code':
            score *= 1.5  # Code files are more complex
        elif file_data.get('file_type') == 'config':
            score *= 1.2  # Config files can be important
        elif file_data.get('file_type') == 'documentation':
            score *= 0.8  # Docs are usually simpler
        
        # Adjust based on filename patterns
        if any(pattern in filename.lower() for pattern in ['test', 'spec']):
            score *= 0.9  # Tests are usually more predictable
        elif any(pattern in filename.lower() for pattern in ['main', 'core', 'index']):
            score *= 1.3  # Core files are more important
        
        return min(score, 2.0)  # Cap at 2.0
    
    def _sort_files_by_priority(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort files by analysis priority."""
        return sorted(
            files,
            key=lambda f: (
                -f.get('complexity_score', 0),  # High complexity first
                -f.get('total_changes', 0),     # Large changes first
                f.get('file_type', 'zzz'),      # Group by type
                f.get('filename', '')           # Stable sort
            )
        )
    
    def _group_files_into_chunks(self, sorted_files: List[Dict[str, Any]]) -> List[FileChunk]:
        """Group files into logical chunks using both line and token limits."""
        chunks = []
        current_chunk_files = []
        current_chunk_lines = 0
        current_chunk_tokens = 0
        chunk_id = 1
        
        for file_data in sorted_files:
            file_changes = file_data.get('total_changes', 0)
            
            # Estimate tokens for this file
            file_content = file_data.get('patch', '')
            file_tokens = self.token_counter.count_tokens(file_content, "code") if file_content else file_changes * 10  # Fallback estimate
            
            # If this file alone exceeds chunk limits, create dedicated chunk
            if file_changes > self.max_lines_per_chunk or file_tokens > self.max_tokens_per_chunk:
                # Finalize current chunk if it has files
                if current_chunk_files:
                    chunk = self._create_chunk(chunk_id, current_chunk_files, current_chunk_lines)
                    chunk.estimated_tokens = current_chunk_tokens
                    chunks.append(chunk)
                    chunk_id += 1
                    current_chunk_files = []
                    current_chunk_lines = 0
                    current_chunk_tokens = 0
                
                # Create dedicated chunk for large file
                large_chunk = self._create_chunk(chunk_id, [file_data], file_changes)
                large_chunk.estimated_tokens = file_tokens
                chunks.append(large_chunk)
                chunk_id += 1
                continue
            
            # Check if adding this file would exceed either limit
            would_exceed_lines = current_chunk_lines + file_changes > self.max_lines_per_chunk
            would_exceed_tokens = current_chunk_tokens + file_tokens > self.max_tokens_per_chunk
            
            if (would_exceed_lines or would_exceed_tokens) and current_chunk_files:
                # Finalize current chunk
                chunk = self._create_chunk(chunk_id, current_chunk_files, current_chunk_lines)
                chunk.estimated_tokens = current_chunk_tokens
                chunks.append(chunk)
                chunk_id += 1
                current_chunk_files = []
                current_chunk_lines = 0
                current_chunk_tokens = 0
            
            # Add file to current chunk
            current_chunk_files.append(file_data)
            current_chunk_lines += file_changes
            current_chunk_tokens += file_tokens
        
        # Finalize last chunk if it has files
        if current_chunk_files:
            chunk = self._create_chunk(chunk_id, current_chunk_files, current_chunk_lines)
            chunk.estimated_tokens = current_chunk_tokens
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, chunk_id: int, files: List[Dict[str, Any]], total_lines: int) -> FileChunk:
        """Create a FileChunk from files."""
        file_types = list(set(f.get('file_type', 'other') for f in files))
        avg_complexity = sum(f.get('complexity_score', 0) for f in files) / len(files)
        
        return FileChunk(
            chunk_id=chunk_id,
            files=files,
            total_lines=total_lines,
            estimated_complexity=avg_complexity,
            file_types=file_types
        )


class ChunkedAnalyzer:
    """
    Main chunked analysis engine for medium-sized PRs.
    
    Orchestrates the chunking, analysis, and result merging process
    to provide comprehensive analysis of PRs too large for single-pass analysis.
    """
    
    def __init__(
        self,
        chunk_timeout: int = 60,
        max_concurrent_chunks: int = 3,
        max_lines_per_chunk: int = 500,
        max_tokens_per_chunk: int = 15000
    ):
        self.chunk_timeout = chunk_timeout
        self.max_concurrent_chunks = max_concurrent_chunks
        self.chunker = FileChunker(max_lines_per_chunk, max_tokens_per_chunk)
        self.token_counter = get_token_counter()
        
        logger.info(
            f"ChunkedAnalyzer initialized",
            extra={
                "chunk_timeout": chunk_timeout,
                "max_concurrent": max_concurrent_chunks,
                "max_lines_per_chunk": max_lines_per_chunk,
                "max_tokens_per_chunk": max_tokens_per_chunk
            }
        )
    
    async def analyze_pr_chunked(
        self,
        pr_data: Dict[str, Any],
        pr_files: List[Dict[str, Any]]
    ) -> ChunkedAnalysisResult:
        """
        Perform chunked analysis of a PR.
        
        Args:
            pr_data: PR metadata from GitHub API
            pr_files: List of changed files with content
            
        Returns:
            Comprehensive chunked analysis result
        """
        start_time = time.time()
        
        # Classify the PR to ensure it's appropriate for chunking
        pr_metrics = classify_pr_size(pr_data)
        
        logger.info(
            f"Starting chunked analysis for {pr_metrics.size_category.value} PR",
            extra={
                "pr_size": pr_metrics.size_category.value,
                "total_changes": pr_metrics.total_changes,
                "files": pr_metrics.changed_files
            }
        )
        
        # Create file chunks
        chunks = self.chunker.create_chunks(pr_files)
        
        if not chunks:
            return ChunkedAnalysisResult(
                status="no_files_to_analyze",
                pr_metrics=pr_metrics,
                total_duration=time.time() - start_time
            )
        
        # Analyze chunks with concurrency control
        chunk_results = await self._analyze_chunks_concurrently(chunks, pr_data)
        
        # Merge results
        merged_result = await self._merge_chunk_results(
            chunk_results, pr_metrics, time.time() - start_time
        )
        
        logger.info(
            f"Chunked analysis completed",
            extra={
                "total_chunks": len(chunks),
                "successful_chunks": merged_result.successful_chunks,
                "total_duration": merged_result.total_duration
            }
        )
        
        return merged_result
    
    async def _analyze_chunks_concurrently(
        self,
        chunks: List[FileChunk],
        pr_data: Dict[str, Any]
    ) -> List[ChunkAnalysisResult]:
        """Analyze chunks with controlled concurrency."""
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_chunks)
        
        # Create analysis tasks
        tasks = [
            self._analyze_single_chunk(chunk, pr_data, semaphore)
            for chunk in chunks
        ]
        
        # Execute with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        chunk_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                chunk_results.append(ChunkAnalysisResult(
                    chunk_id=chunks[i].chunk_id,
                    success=False,
                    duration=0.0,
                    error_type=type(result).__name__,
                    error_message=str(result),
                    files_analyzed=chunks[i].filenames
                ))
            else:
                chunk_results.append(result)
        
        return chunk_results
    
    async def _analyze_single_chunk(
        self,
        chunk: FileChunk,
        pr_data: Dict[str, Any],
        semaphore: asyncio.Semaphore
    ) -> ChunkAnalysisResult:
        """Analyze a single chunk of files."""
        
        async with semaphore:
            start_time = time.time()
            
            logger.debug(
                f"Analyzing chunk {chunk.chunk_id}",
                extra={
                    "chunk_id": chunk.chunk_id,
                    "files": chunk.file_count,
                    "lines": chunk.total_lines
                }
            )
            
            try:
                # Build analysis prompt for this chunk
                analysis_prompt = self._build_chunk_analysis_prompt(chunk, pr_data)
                
                # Perform Claude CLI analysis with circuit breaker
                claude_result = await analyze_content_async_with_circuit_breaker(
                    content=analysis_prompt,
                    task_type="pr_review",
                    timeout_seconds=self.chunk_timeout,
                    max_retries=2
                )
                
                if claude_result.success:
                    # Parse analysis results
                    return self._parse_chunk_analysis(
                        chunk, claude_result.output, time.time() - start_time
                    )
                else:
                    # Handle analysis failure
                    return ChunkAnalysisResult(
                        chunk_id=chunk.chunk_id,
                        success=False,
                        duration=time.time() - start_time,
                        error_type="ClaudeCliError",
                        error_message=claude_result.error or "Analysis failed",
                        files_analyzed=chunk.filenames,
                        lines_analyzed=chunk.total_lines
                    )
                    
            except (ClaudeCliError, CircuitBreakerOpenError) as e:
                logger.warning(
                    f"Chunk {chunk.chunk_id} analysis failed: {e}",
                    extra={"chunk_id": chunk.chunk_id, "error": str(e)}
                )
                
                return ChunkAnalysisResult(
                    chunk_id=chunk.chunk_id,
                    success=False,
                    duration=time.time() - start_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    files_analyzed=chunk.filenames,
                    lines_analyzed=chunk.total_lines
                )
                
            except Exception as e:
                logger.error(
                    f"Unexpected error analyzing chunk {chunk.chunk_id}: {e}",
                    extra={"chunk_id": chunk.chunk_id, "error": str(e)}
                )
                
                return ChunkAnalysisResult(
                    chunk_id=chunk.chunk_id,
                    success=False,
                    duration=time.time() - start_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    files_analyzed=chunk.filenames,
                    lines_analyzed=chunk.total_lines
                )
    
    def _build_chunk_analysis_prompt(
        self,
        chunk: FileChunk,
        pr_data: Dict[str, Any]
    ) -> str:
        """Build analysis prompt for a specific chunk."""
        
        pr_title = pr_data.get('title', 'PR Title Not Available')
        pr_description = pr_data.get('body', 'No description provided')
        
        # Build file summaries
        file_summaries = []
        for file_data in chunk.files:
            filename = file_data.get('filename', 'unknown')
            changes = file_data.get('total_changes', 0)
            file_type = file_data.get('file_type', 'unknown')
            
            # Get patch/diff if available
            patch = file_data.get('patch', '')
            if patch:
                # Truncate very long patches
                if len(patch) > 2000:
                    patch = patch[:2000] + "\n... (truncated)"
            
            file_summary = f"""
**File**: {filename} ({file_type}, {changes} lines changed)
{patch if patch else "No diff available"}
"""
            file_summaries.append(file_summary)
        
        prompt = f"""
Please analyze this chunk of files from a Pull Request as part of a larger chunked analysis.

**PR Context:**
- Title: {pr_title}
- Description: {pr_description[:500]}{'...' if len(pr_description) > 500 else ''}

**Chunk Information:**
- Chunk ID: {chunk.chunk_id}
- Files in chunk: {chunk.file_count}
- Total lines: {chunk.total_lines}
- File types: {', '.join(chunk.file_types)}

**Files in this chunk:**
{chr(10).join(file_summaries)}

**Analysis Instructions:**
1. Focus on this specific chunk while keeping the broader PR context in mind
2. Identify any patterns, anti-patterns, or concerns specific to these files
3. Provide actionable recommendations for improvement
4. Note any potential issues that might affect other parts of the PR
5. Keep recommendations concise since this is part of a larger analysis

**Expected Output Format:**
- **Patterns Detected**: List specific patterns found in this chunk
- **Recommendations**: Actionable suggestions for these files
- **Summary**: Brief summary of this chunk's changes and their impact

Please provide focused, actionable analysis for this chunk.
"""
        
        return prompt
    
    def _parse_chunk_analysis(
        self,
        chunk: FileChunk,
        analysis_output: str,
        duration: float
    ) -> ChunkAnalysisResult:
        """Parse Claude CLI analysis output into structured result."""
        
        # Simple parsing - in production, this could be more sophisticated
        patterns = []
        recommendations = []
        summary = ""
        
        # Extract sections from output
        lines = analysis_output.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if 'patterns detected' in line.lower() or 'patterns found' in line.lower():
                current_section = 'patterns'
                continue
            elif 'recommendations' in line.lower() or 'suggestions' in line.lower():
                current_section = 'recommendations'
                continue
            elif 'summary' in line.lower():
                current_section = 'summary'
                continue
            
            # Extract content based on section
            if current_section == 'patterns' and line and not line.startswith('#'):
                if line.startswith('-') or line.startswith('*'):
                    patterns.append(line[1:].strip())
                elif line and len(line) > 10:  # Avoid headers
                    patterns.append(line)
            elif current_section == 'recommendations' and line and not line.startswith('#'):
                if line.startswith('-') or line.startswith('*'):
                    recommendations.append(line[1:].strip())
                elif line and len(line) > 10:
                    recommendations.append(line)
            elif current_section == 'summary' and line and not line.startswith('#'):
                summary += line + " "
        
        # Clean up extracted content
        summary = summary.strip()
        if not summary:
            summary = f"Analyzed {chunk.file_count} files with {chunk.total_lines} total changes"
        
        return ChunkAnalysisResult(
            chunk_id=chunk.chunk_id,
            success=True,
            duration=duration,
            patterns_detected=patterns,
            recommendations=recommendations,
            summary=summary,
            raw_analysis=analysis_output,
            files_analyzed=chunk.filenames,
            lines_analyzed=chunk.total_lines
        )
    
    async def _merge_chunk_results(
        self,
        chunk_results: List[ChunkAnalysisResult],
        pr_metrics: PrSizeMetrics,
        total_duration: float
    ) -> ChunkedAnalysisResult:
        """Merge individual chunk results into cohesive analysis."""
        
        successful_results = [r for r in chunk_results if r.success]
        failed_results = [r for r in chunk_results if not r.success]
        
        # Aggregate patterns and recommendations
        all_patterns = []
        all_recommendations = []
        chunk_summaries = []
        
        for result in chunk_results:
            # Create chunk summary
            if result.success:
                chunk_summaries.append({
                    "chunk_id": result.chunk_id,
                    "status": "success",
                    "files_analyzed": len(result.files_analyzed),
                    "lines_analyzed": result.lines_analyzed,
                    "patterns_found": len(result.patterns_detected),
                    "recommendations_made": len(result.recommendations),
                    "duration": result.duration,
                    "key_findings": result.summary[:200] + "..." if len(result.summary) > 200 else result.summary
                })
                
                # Collect patterns and recommendations
                all_patterns.extend(result.patterns_detected)
                all_recommendations.extend(result.recommendations)
            else:
                chunk_summaries.append({
                    "chunk_id": result.chunk_id,
                    "status": "error",
                    "error_type": result.error_type,
                    "error_message": result.error_message,
                    "files_affected": result.files_analyzed,
                    "duration": result.duration
                })
        
        # Deduplicate and categorize patterns
        unique_patterns = self._deduplicate_patterns(all_patterns)
        prioritized_recommendations = self._prioritize_recommendations(all_recommendations)
        overall_assessment = self._create_overall_assessment(
            successful_results, failed_results, pr_metrics
        )
        
        # Determine overall status
        if len(successful_results) == len(chunk_results):
            status = "chunked_analysis_complete"
        elif len(successful_results) > 0:
            status = "chunked_analysis_partial"
        else:
            status = "chunked_analysis_failed"
        
        return ChunkedAnalysisResult(
            status=status,
            total_chunks=len(chunk_results),
            successful_chunks=len(successful_results),
            failed_chunks=len(failed_results),
            total_duration=total_duration,
            patterns_detected=unique_patterns,
            recommendations=prioritized_recommendations,
            overall_assessment=overall_assessment,
            chunk_summaries=chunk_summaries,
            chunk_results=chunk_results,
            pr_metrics=pr_metrics
        )
    
    def _deduplicate_patterns(self, patterns: List[str]) -> List[Dict[str, Any]]:
        """Deduplicate and categorize detected patterns."""
        
        # Simple deduplication by text similarity
        unique_patterns = []
        seen_patterns = set()
        
        for pattern in patterns:
            # Normalize pattern text
            normalized = pattern.lower().strip()
            
            # Skip if too short or already seen
            if len(normalized) < 10 or normalized in seen_patterns:
                continue
            
            seen_patterns.add(normalized)
            
            # Categorize pattern
            category = self._categorize_pattern(pattern)
            
            unique_patterns.append({
                "pattern": pattern,
                "category": category,
                "confidence": "medium"  # Could be enhanced with ML
            })
        
        return unique_patterns
    
    def _categorize_pattern(self, pattern: str) -> str:
        """Categorize a detected pattern."""
        pattern_lower = pattern.lower()
        
        if any(word in pattern_lower for word in ['security', 'vulnerability', 'unsafe']):
            return "security"
        elif any(word in pattern_lower for word in ['performance', 'optimization', 'slow']):
            return "performance"
        elif any(word in pattern_lower for word in ['bug', 'error', 'issue', 'problem']):
            return "bug_risk"
        elif any(word in pattern_lower for word in ['test', 'testing', 'coverage']):
            return "testing"
        elif any(word in pattern_lower for word in ['documentation', 'comment', 'doc']):
            return "documentation"
        elif any(word in pattern_lower for word in ['structure', 'organization', 'design']):
            return "architecture"
        else:
            return "general"
    
    def _prioritize_recommendations(self, recommendations: List[str]) -> List[str]:
        """Prioritize and deduplicate recommendations."""
        
        # Simple deduplication
        unique_recommendations = []
        seen_recommendations = set()
        
        for rec in recommendations:
            normalized = rec.lower().strip()
            
            if len(normalized) < 10 or normalized in seen_recommendations:
                continue
                
            seen_recommendations.add(normalized)
            unique_recommendations.append(rec)
        
        # Sort by priority (security and bugs first)
        def recommendation_priority(rec: str) -> int:
            rec_lower = rec.lower()
            if any(word in rec_lower for word in ['security', 'vulnerability']):
                return 1
            elif any(word in rec_lower for word in ['bug', 'error', 'fix']):
                return 2
            elif any(word in rec_lower for word in ['performance', 'optimization']):
                return 3
            else:
                return 4
        
        return sorted(unique_recommendations, key=recommendation_priority)
    
    def _create_overall_assessment(
        self,
        successful_results: List[ChunkAnalysisResult],
        failed_results: List[ChunkAnalysisResult],
        pr_metrics: PrSizeMetrics
    ) -> str:
        """Create overall assessment from chunk results."""
        
        total_chunks = len(successful_results) + len(failed_results)
        success_rate = len(successful_results) / total_chunks if total_chunks > 0 else 0
        
        assessment_parts = []
        
        # Overall status
        if success_rate >= 1.0:
            assessment_parts.append("✅ Complete chunked analysis successful")
        elif success_rate >= 0.7:
            assessment_parts.append(f"⚠️ Partial analysis completed ({len(successful_results)}/{total_chunks} chunks)")
        else:
            assessment_parts.append(f"❌ Limited analysis due to failures ({len(successful_results)}/{total_chunks} chunks)")
        
        # PR characteristics
        assessment_parts.append(
            f"PR characteristics: {pr_metrics.total_changes} lines across "
            f"{pr_metrics.changed_files} files (classified as {pr_metrics.size_category.value})"
        )
        
        # Analysis scope
        total_files_analyzed = sum(len(r.files_analyzed) for r in successful_results)
        total_lines_analyzed = sum(r.lines_analyzed for r in successful_results)
        
        assessment_parts.append(
            f"Analyzed: {total_files_analyzed} files, {total_lines_analyzed} lines of changes"
        )
        
        # Failure information if any
        if failed_results:
            failed_files = sum(len(r.files_analyzed) for r in failed_results)
            assessment_parts.append(f"Failed to analyze: {failed_files} files due to errors")
        
        return ". ".join(assessment_parts) + "."


# Global analyzer instance
_chunked_analyzer_instance: Optional[ChunkedAnalyzer] = None


def get_chunked_analyzer() -> ChunkedAnalyzer:
    """Get the global chunked analyzer instance."""
    global _chunked_analyzer_instance
    
    if _chunked_analyzer_instance is None:
        _chunked_analyzer_instance = ChunkedAnalyzer()
    
    return _chunked_analyzer_instance


async def analyze_pr_with_chunking(
    pr_data: Dict[str, Any],
    pr_files: List[Dict[str, Any]]
) -> ChunkedAnalysisResult:
    """
    Convenience function for chunked PR analysis.
    
    Args:
        pr_data: PR metadata from GitHub API
        pr_files: List of changed files with content
        
    Returns:
        Chunked analysis result
    """
    analyzer = get_chunked_analyzer()
    return await analyzer.analyze_pr_chunked(pr_data, pr_files)