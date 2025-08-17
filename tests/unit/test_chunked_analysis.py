"""
Tests for Chunked Analysis System (Issue #103)

Comprehensive tests for the chunked PR analysis implementation including
PR classification, file chunking, analysis execution, and result merging.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

from vibe_check.tools.shared.pr_classifier import (
    PrSizeClassifier, 
    PrSizeCategory, 
    PrSizeMetrics,
    classify_pr_size,
    should_use_chunked_analysis
)
from vibe_check.tools.pr_review.chunked_analyzer import (
    FileChunker,
    ChunkedAnalyzer,
    FileChunk,
    ChunkAnalysisResult,
    ChunkedAnalysisResult,
    analyze_pr_with_chunking
)


class TestPrSizeClassifier:
    """Test PR size classification logic."""
    
    def test_classifier_initialization(self):
        """Test classifier initializes correctly."""
        classifier = PrSizeClassifier()
        
        assert classifier.SMALL_LINES_THRESHOLD == 500
        assert classifier.SMALL_FILES_THRESHOLD == 10
        assert classifier.MEDIUM_LINES_THRESHOLD == 1000
        assert classifier.MEDIUM_FILES_THRESHOLD == 20
    
    def test_small_pr_classification(self):
        """Test classification of small PRs."""
        classifier = PrSizeClassifier()
        
        pr_data = {
            'additions': 200,
            'deletions': 100,
            'changed_files': 5
        }
        
        metrics = classifier.classify_pr(pr_data)
        
        assert metrics.size_category == PrSizeCategory.SMALL
        assert metrics.analysis_strategy == "full_llm_analysis"
        assert metrics.total_changes == 300
        assert metrics.changed_files == 5
        assert metrics.estimated_chunks == 1
    
    def test_medium_pr_classification(self):
        """Test classification of medium PRs."""
        classifier = PrSizeClassifier()
        
        pr_data = {
            'additions': 500,
            'deletions': 200,
            'changed_files': 15
        }
        
        metrics = classifier.classify_pr(pr_data)
        
        assert metrics.size_category == PrSizeCategory.MEDIUM
        assert metrics.analysis_strategy == "chunked_llm_analysis"
        assert metrics.total_changes == 700
        assert metrics.changed_files == 15
        assert metrics.estimated_chunks == 2  # 700 lines / 500 = 2 chunks
    
    def test_large_pr_classification(self):
        """Test classification of large PRs."""
        classifier = PrSizeClassifier()
        
        pr_data = {
            'additions': 800,
            'deletions': 400,
            'changed_files': 25
        }
        
        metrics = classifier.classify_pr(pr_data)
        
        assert metrics.size_category == PrSizeCategory.LARGE
        assert metrics.analysis_strategy == "pattern_detection_only"
        assert metrics.total_changes == 1200
        assert metrics.changed_files == 25
        assert metrics.estimated_chunks == 0  # No chunking for large PRs
    
    def test_edge_case_thresholds(self):
        """Test classification at threshold boundaries."""
        classifier = PrSizeClassifier()
        
        # Exactly at SMALL threshold
        small_edge_data = {
            'additions': 500,
            'deletions': 0,
            'changed_files': 10
        }
        
        metrics = classifier.classify_pr(small_edge_data)
        assert metrics.size_category == PrSizeCategory.SMALL
        
        # Just over SMALL threshold
        medium_edge_data = {
            'additions': 501,
            'deletions': 0,
            'changed_files': 10
        }
        
        metrics = classifier.classify_pr(medium_edge_data)
        assert metrics.size_category == PrSizeCategory.MEDIUM
    
    def test_file_characteristics_analysis(self):
        """Test analysis of detailed file characteristics."""
        classifier = PrSizeClassifier()
        
        files_data = [
            {'filename': 'large_file.py', 'changes': 250, 'additions': 200, 'deletions': 50},
            {'filename': 'small_file.py', 'changes': 5, 'additions': 3, 'deletions': 2},
            {'filename': 'medium_file.js', 'changes': 50, 'additions': 30, 'deletions': 20}
        ]
        
        pr_data = {
            'additions': 233,
            'deletions': 72,
            'changed_files': 3,
            'files': files_data
        }
        
        metrics = classifier.classify_pr(pr_data)
        
        assert metrics.largest_file_changes == 250
        assert metrics.has_large_files is True  # 250 > 200 threshold
        assert metrics.file_diversity_score > 0  # Multiple file types
    
    def test_chunking_recommendations(self):
        """Test chunking recommendations for different PR sizes."""
        classifier = PrSizeClassifier()
        
        # Small PR - no chunking
        small_metrics = PrSizeMetrics(
            total_changes=300, additions=200, deletions=100, changed_files=5,
            lines_per_file_avg=60, largest_file_changes=80, files_per_change_ratio=0.017,
            size_category=PrSizeCategory.SMALL, analysis_strategy="full_llm_analysis",
            estimated_chunks=1, has_large_files=False, has_many_small_changes=False,
            file_diversity_score=0.6
        )
        
        recommendation = classifier.get_chunking_recommendation(small_metrics)
        assert recommendation["should_chunk"] is False
        assert recommendation["strategy"] == "single_pass_analysis"
        
        # Medium PR - should chunk
        medium_metrics = PrSizeMetrics(
            total_changes=750, additions=500, deletions=250, changed_files=15,
            lines_per_file_avg=50, largest_file_changes=120, files_per_change_ratio=0.02,
            size_category=PrSizeCategory.MEDIUM, analysis_strategy="chunked_llm_analysis",
            estimated_chunks=2, has_large_files=False, has_many_small_changes=False,
            file_diversity_score=0.7
        )
        
        recommendation = classifier.get_chunking_recommendation(medium_metrics)
        assert recommendation["should_chunk"] is True
        assert recommendation["strategy"] == "file_based_chunking"
        assert recommendation["chunk_count"] == 2
    
    def test_convenience_functions(self):
        """Test convenience functions for PR classification."""
        # Test classify_pr_size function
        pr_data = {'additions': 400, 'deletions': 200, 'changed_files': 12}
        metrics = classify_pr_size(pr_data)
        assert isinstance(metrics, PrSizeMetrics)
        assert metrics.size_category == PrSizeCategory.MEDIUM
        
        # Test should_use_chunked_analysis function
        assert should_use_chunked_analysis(pr_data) is True
        
        small_pr_data = {'additions': 200, 'deletions': 100, 'changed_files': 5}
        assert should_use_chunked_analysis(small_pr_data) is False


class TestFileChunker:
    """Test file chunking strategy."""
    
    def test_chunker_initialization(self):
        """Test chunker initializes correctly."""
        chunker = FileChunker(max_lines_per_chunk=400)
        assert chunker.max_lines_per_chunk == 400
    
    def test_file_enhancement(self):
        """Test file data enhancement with metadata."""
        chunker = FileChunker()
        
        file_data = {
            'filename': 'example.py',
            'additions': 50,
            'deletions': 20,
            'changes': 70
        }
        
        enhanced = chunker._enhance_file_data(file_data)
        
        assert enhanced['total_changes'] == 70
        assert enhanced['extension'] == 'py'
        assert enhanced['file_type'] == 'code'
        assert 'complexity_score' in enhanced
    
    def test_file_type_classification(self):
        """Test file type classification."""
        chunker = FileChunker()
        
        test_cases = [
            ('main.py', 'code'),
            ('styles.css', 'frontend'),
            ('config.json', 'config'),
            ('README.md', 'documentation'),
            ('script.sh', 'script'),
            ('data.sql', 'database'),
            ('unknown.xyz', 'other')
        ]
        
        for filename, expected_type in test_cases:
            assert chunker._classify_file_type(filename) == expected_type
    
    def test_simple_chunking(self):
        """Test basic file chunking."""
        chunker = FileChunker(max_lines_per_chunk=100)
        
        files = [
            {'filename': 'file1.py', 'changes': 50},
            {'filename': 'file2.py', 'changes': 40},
            {'filename': 'file3.py', 'changes': 30}
        ]
        
        chunks = chunker.create_chunks(files)
        
        assert len(chunks) == 2  # First chunk: 50+40=90, Second chunk: 30
        assert chunks[0].total_lines == 90
        assert chunks[1].total_lines == 30
        assert chunks[0].file_count == 2
        assert chunks[1].file_count == 1
    
    def test_large_file_chunking(self):
        """Test chunking with files larger than chunk size."""
        chunker = FileChunker(max_lines_per_chunk=100)
        
        files = [
            {'filename': 'small.py', 'changes': 50},
            {'filename': 'large.py', 'changes': 150},  # Exceeds chunk size
            {'filename': 'medium.py', 'changes': 80}
        ]
        
        chunks = chunker.create_chunks(files)
        
        # Should create 3 chunks: [small], [large], [medium]
        assert len(chunks) == 3
        assert chunks[0].total_lines == 50
        assert chunks[1].total_lines == 150  # Large file gets its own chunk
        assert chunks[2].total_lines == 80
    
    def test_chunk_metadata(self):
        """Test chunk metadata generation."""
        chunker = FileChunker()
        
        files = [
            {'filename': 'code.py', 'changes': 50, 'total_changes': 50},
            {'filename': 'config.json', 'changes': 20, 'total_changes': 20}
        ]
        
        # Enhance files first
        enhanced_files = [chunker._enhance_file_data(f) for f in files]
        
        chunk = chunker._create_chunk(1, enhanced_files, 70)
        
        assert chunk.chunk_id == 1
        assert chunk.total_lines == 70
        assert chunk.file_count == 2
        assert 'code' in chunk.file_types
        assert 'config' in chunk.file_types
        assert chunk.estimated_complexity > 0


class TestChunkedAnalyzer:
    """Test the main chunked analysis engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ChunkedAnalyzer(
            chunk_timeout=30,
            max_concurrent_chunks=2,
            max_lines_per_chunk=100
        )
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        assert self.analyzer.chunk_timeout == 30
        assert self.analyzer.max_concurrent_chunks == 2
        assert self.analyzer.chunker.max_lines_per_chunk == 100
    
    def test_chunk_analysis_prompt_building(self):
        """Test building analysis prompt for chunks."""
        chunk = FileChunk(
            chunk_id=1,
            files=[
                {'filename': 'test.py', 'total_changes': 50, 'file_type': 'code', 'patch': 'def test(): pass'},
                {'filename': 'config.json', 'total_changes': 20, 'file_type': 'config'}
            ],
            total_lines=70,
            estimated_complexity=1.2,
            file_types=['code', 'config']
        )
        
        pr_data = {
            'title': 'Test PR',
            'body': 'This is a test PR description'
        }
        
        prompt = self.analyzer._build_chunk_analysis_prompt(chunk, pr_data)
        
        assert 'Test PR' in prompt
        assert 'Chunk ID: 1' in prompt
        assert 'test.py' in prompt
        assert 'config.json' in prompt
        assert 'def test(): pass' in prompt
    
    def test_chunk_analysis_parsing(self):
        """Test parsing of chunk analysis results."""
        chunk = FileChunk(
            chunk_id=1,
            files=[{'filename': 'test.py'}],
            total_lines=50,
            estimated_complexity=1.0
        )
        
        # Mock Claude output
        analysis_output = """
        **Patterns Detected**:
        - Good error handling pattern
        - Consistent naming conventions
        
        **Recommendations**:
        - Add more unit tests
        - Consider using type hints
        
        **Summary**:
        Clean code with good structure, minor improvements needed.
        """
        
        result = self.analyzer._parse_chunk_analysis(chunk, analysis_output, 1.5)
        
        assert result.chunk_id == 1
        assert result.success is True
        assert result.duration == 1.5
        assert len(result.patterns_detected) >= 2
        assert len(result.recommendations) >= 2
        assert 'Clean code' in result.summary
    
    @pytest.mark.asyncio
    async def test_successful_chunked_analysis(self):
        """Test successful end-to-end chunked analysis."""
        # Mock PR data
        pr_data = {
            'title': 'Test PR',
            'body': 'Test description',
            'additions': 150,
            'deletions': 50,
            'changed_files': 4
        }
        
        pr_files = [
            {'filename': 'file1.py', 'changes': 60, 'patch': '+ new code'},
            {'filename': 'file2.py', 'changes': 40, 'patch': '+ more code'},
            {'filename': 'file3.py', 'changes': 50, 'patch': '+ even more'},
            {'filename': 'file4.py', 'changes': 50, 'patch': '+ final code'}
        ]
        
        # Mock the Claude CLI analysis to return successful results
        with patch('src.vibe_check.tools.shared.claude_integration.analyze_content_async_with_circuit_breaker') as mock_claude:
            mock_claude.return_value = Mock(
                success=True,
                output="**Patterns Detected**: Good code structure\n**Recommendations**: Add tests\n**Summary**: Well structured code"
            )
            
            result = await self.analyzer.analyze_pr_chunked(pr_data, pr_files)
            
            assert result.status == "chunked_analysis_complete"
            assert result.total_chunks >= 2  # Should create multiple chunks
            assert result.successful_chunks == result.total_chunks
            assert result.failed_chunks == 0
            assert len(result.chunk_summaries) == result.total_chunks
    
    @pytest.mark.asyncio
    async def test_partial_failure_chunked_analysis(self):
        """Test chunked analysis with some chunks failing."""
        pr_data = {'title': 'Test PR', 'additions': 100, 'deletions': 50, 'changed_files': 2}
        pr_files = [
            {'filename': 'good.py', 'changes': 80},
            {'filename': 'bad.py', 'changes': 70}
        ]
        
        # Mock Claude CLI to succeed for first chunk, fail for second
        call_count = 0
        async def mock_claude_analysis(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Mock(success=True, output="**Summary**: Good chunk")
            else:
                return Mock(success=False, error="Analysis failed")
        
        with patch('src.vibe_check.tools.shared.claude_integration.analyze_content_async_with_circuit_breaker', side_effect=mock_claude_analysis):
            result = await self.analyzer.analyze_pr_chunked(pr_data, pr_files)
            
            assert result.status == "chunked_analysis_partial"
            assert result.successful_chunks >= 1
            assert result.failed_chunks >= 1
            assert result.total_chunks == 2
    
    def test_pattern_deduplication(self):
        """Test deduplication of detected patterns."""
        patterns = [
            "Security vulnerability detected",
            "Performance issue found",
            "security vulnerability detected",  # Duplicate (case different)
            "Documentation needs improvement",
            "Performance issue found"  # Duplicate
        ]
        
        unique_patterns = self.analyzer._deduplicate_patterns(patterns)
        
        # Should deduplicate and categorize
        assert len(unique_patterns) == 3
        
        # Check categorization
        security_patterns = [p for p in unique_patterns if p['category'] == 'security']
        performance_patterns = [p for p in unique_patterns if p['category'] == 'performance']
        doc_patterns = [p for p in unique_patterns if p['category'] == 'documentation']
        
        assert len(security_patterns) == 1
        assert len(performance_patterns) == 1
        assert len(doc_patterns) == 1
    
    def test_recommendation_prioritization(self):
        """Test prioritization of recommendations."""
        recommendations = [
            "Consider refactoring this function",
            "Fix security vulnerability in authentication",
            "Add error handling for edge cases",
            "Update documentation",
            "Optimize performance bottleneck"
        ]
        
        prioritized = self.analyzer._prioritize_recommendations(recommendations)
        
        # Security should come first
        assert "security" in prioritized[0].lower()
        # Bug fixes should come second
        assert any("error" in rec.lower() or "fix" in rec.lower() for rec in prioritized[:2])
    
    def test_overall_assessment_creation(self):
        """Test creation of overall assessment from chunk results."""
        successful_results = [
            ChunkAnalysisResult(chunk_id=1, success=True, duration=1.0, files_analyzed=['file1.py'], lines_analyzed=50),
            ChunkAnalysisResult(chunk_id=2, success=True, duration=1.5, files_analyzed=['file2.py'], lines_analyzed=60)
        ]
        
        failed_results = [
            ChunkAnalysisResult(chunk_id=3, success=False, duration=0.5, files_analyzed=['file3.py'], lines_analyzed=0, error_type="TimeoutError")
        ]
        
        pr_metrics = PrSizeMetrics(
            total_changes=160, additions=100, deletions=60, changed_files=3,
            lines_per_file_avg=53, largest_file_changes=60, files_per_change_ratio=0.019,
            size_category=PrSizeCategory.MEDIUM, analysis_strategy="chunked_llm_analysis",
            estimated_chunks=3, has_large_files=False, has_many_small_changes=False,
            file_diversity_score=0.7
        )
        
        assessment = self.analyzer._create_overall_assessment(successful_results, failed_results, pr_metrics)
        
        assert "Partial analysis completed (2/3 chunks)" in assessment
        assert "160 lines across 3 files" in assessment
        assert "medium" in assessment.lower()


class TestIntegration:
    """Test integration between components."""
    
    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test the convenience function for chunked analysis."""
        pr_data = {'title': 'Test', 'additions': 300, 'deletions': 200, 'changed_files': 8}
        pr_files = [
            {'filename': f'file{i}.py', 'changes': 70} for i in range(8)
        ]
        
        with patch('src.vibe_check.tools.shared.claude_integration.analyze_content_async_with_circuit_breaker') as mock_claude:
            mock_claude.return_value = Mock(
                success=True,
                output="**Summary**: Good analysis"
            )
            
            result = await analyze_pr_with_chunking(pr_data, pr_files)
            
            assert isinstance(result, ChunkedAnalysisResult)
            assert result.status in ["chunked_analysis_complete", "chunked_analysis_partial"]
    
    def test_empty_files_handling(self):
        """Test handling of PRs with no files."""
        chunker = FileChunker()
        chunks = chunker.create_chunks([])
        assert len(chunks) == 0
    
    def test_malformed_file_data(self):
        """Test handling of malformed file data."""
        chunker = FileChunker()
        
        # Files with missing data
        files = [
            {'filename': 'good.py', 'changes': 50},
            {'name': 'alt_name.py'},  # Different key structure
            {}  # Empty file data
        ]
        
        chunks = chunker.create_chunks(files)
        
        # Should handle gracefully and create chunks from valid data
        assert len(chunks) >= 1
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of analysis timeouts."""
        analyzer = ChunkedAnalyzer(chunk_timeout=0.1)  # Very short timeout
        
        pr_data = {'title': 'Test', 'additions': 100, 'deletions': 50, 'changed_files': 2}
        pr_files = [{'filename': 'test.py', 'changes': 150}]
        
        # Mock Claude CLI to be slow
        async def slow_claude_analysis(*args, **kwargs):
            await asyncio.sleep(0.2)  # Longer than timeout
            return Mock(success=True, output="Late response")
        
        with patch('src.vibe_check.tools.shared.claude_integration.analyze_content_async_with_circuit_breaker', side_effect=slow_claude_analysis):
            result = await analyzer.analyze_pr_chunked(pr_data, pr_files)
            
            # Should handle timeout gracefully
            assert result.status in ["chunked_analysis_partial", "chunked_analysis_failed"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])