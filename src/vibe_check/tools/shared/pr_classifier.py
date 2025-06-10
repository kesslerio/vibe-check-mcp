"""
PR Size Classification for Chunked Analysis

Intelligent classification of PRs into size categories to determine
optimal analysis strategy. Part of Phase 3 implementation for Issue #103.
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PrSizeCategory(Enum):
    """PR size categories for analysis strategy selection."""
    SMALL = "small"      # ≤500 lines, ≤10 files - Full LLM analysis
    MEDIUM = "medium"    # 500-1000 lines, 10-20 files - Chunked analysis  
    LARGE = "large"      # >1000 lines, >20 files - Basic analysis only


@dataclass
class PrSizeMetrics:
    """Detailed metrics about PR size and complexity."""
    
    # Basic size metrics
    total_changes: int
    additions: int
    deletions: int
    changed_files: int
    
    # Complexity indicators
    lines_per_file_avg: float
    largest_file_changes: int
    files_per_change_ratio: float
    
    # Classification results
    size_category: PrSizeCategory
    analysis_strategy: str
    estimated_chunks: int
    
    # Risk factors
    has_large_files: bool
    has_many_small_changes: bool
    file_diversity_score: float


class PrSizeClassifier:
    """
    Intelligent PR size classifier for determining analysis strategy.
    
    Analyzes PR characteristics to determine optimal processing approach:
    - SMALL: Single-pass LLM analysis
    - MEDIUM: Chunked LLM analysis 
    - LARGE: Basic pattern detection only
    """
    
    # Configuration thresholds
    SMALL_LINES_THRESHOLD = 500
    SMALL_FILES_THRESHOLD = 10
    
    MEDIUM_LINES_THRESHOLD = 1000
    MEDIUM_FILES_THRESHOLD = 20
    
    # Chunking parameters
    CHUNK_SIZE_LINES = 500
    CHUNK_TIMEOUT_SECONDS = 60
    
    # File size thresholds
    LARGE_FILE_THRESHOLD = 200  # Single file with >200 changes
    MANY_SMALL_CHANGES_THRESHOLD = 0.8  # >80% of files have <10 changes
    
    def __init__(self):
        logger.debug("PR size classifier initialized")
    
    def classify_pr(self, pr_data: Dict[str, Any]) -> PrSizeMetrics:
        """
        Classify PR size and determine analysis strategy.
        
        Args:
            pr_data: PR data from GitHub API or similar structure
            
        Returns:
            Comprehensive PR size metrics and classification
        """
        # Extract basic metrics
        additions = pr_data.get('additions', 0)
        deletions = pr_data.get('deletions', 0)
        total_changes = additions + deletions
        changed_files = pr_data.get('changed_files', 0)
        
        # Calculate complexity indicators
        lines_per_file_avg = total_changes / max(changed_files, 1)
        files_per_change_ratio = changed_files / max(total_changes, 1)
        
        # Analyze file characteristics if detailed file data available
        file_metrics = self._analyze_file_characteristics(pr_data.get('files', []))
        
        # Determine size category
        size_category = self._determine_size_category(total_changes, changed_files)
        
        # Calculate analysis strategy details
        analysis_strategy = self._get_analysis_strategy(size_category)
        estimated_chunks = self._estimate_chunk_count(total_changes, size_category)
        
        metrics = PrSizeMetrics(
            total_changes=total_changes,
            additions=additions,
            deletions=deletions,
            changed_files=changed_files,
            lines_per_file_avg=lines_per_file_avg,
            largest_file_changes=file_metrics['largest_file_changes'],
            files_per_change_ratio=files_per_change_ratio,
            size_category=size_category,
            analysis_strategy=analysis_strategy,
            estimated_chunks=estimated_chunks,
            has_large_files=file_metrics['has_large_files'],
            has_many_small_changes=file_metrics['has_many_small_changes'],
            file_diversity_score=file_metrics['diversity_score']
        )
        
        logger.info(
            f"PR classified as {size_category.value.upper()}: "
            f"{total_changes} lines, {changed_files} files, "
            f"strategy: {analysis_strategy}"
        )
        
        return metrics
    
    def _determine_size_category(self, total_changes: int, changed_files: int) -> PrSizeCategory:
        """Determine PR size category based on thresholds."""
        
        # Check for SMALL category first
        if (total_changes <= self.SMALL_LINES_THRESHOLD and 
            changed_files <= self.SMALL_FILES_THRESHOLD):
            return PrSizeCategory.SMALL
        
        # Check for MEDIUM category
        elif (total_changes <= self.MEDIUM_LINES_THRESHOLD and 
              changed_files <= self.MEDIUM_FILES_THRESHOLD):
            return PrSizeCategory.MEDIUM
        
        # Everything else is LARGE
        else:
            return PrSizeCategory.LARGE
    
    def _get_analysis_strategy(self, size_category: PrSizeCategory) -> str:
        """Get analysis strategy description for size category."""
        
        strategies = {
            PrSizeCategory.SMALL: "full_llm_analysis",
            PrSizeCategory.MEDIUM: "chunked_llm_analysis", 
            PrSizeCategory.LARGE: "pattern_detection_only"
        }
        
        return strategies[size_category]
    
    def _estimate_chunk_count(self, total_changes: int, size_category: PrSizeCategory) -> int:
        """Estimate number of chunks needed for analysis."""
        
        if size_category == PrSizeCategory.SMALL:
            return 1
        elif size_category == PrSizeCategory.MEDIUM:
            # Calculate chunks based on chunk size
            return max(1, (total_changes + self.CHUNK_SIZE_LINES - 1) // self.CHUNK_SIZE_LINES)
        else:
            return 0  # No LLM chunking for large PRs
    
    def _analyze_file_characteristics(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze detailed file characteristics if available."""
        
        if not files:
            return {
                'largest_file_changes': 0,
                'has_large_files': False,
                'has_many_small_changes': False,
                'diversity_score': 0.0
            }
        
        # Calculate file change sizes
        file_changes = []
        file_types = set()
        
        for file_data in files:
            # Try different possible keys for change count
            changes = (
                file_data.get('changes', 0) or
                file_data.get('additions', 0) + file_data.get('deletions', 0) or
                0
            )
            file_changes.append(changes)
            
            # Track file types for diversity
            filename = file_data.get('filename', '')
            if '.' in filename:
                file_types.add(filename.split('.')[-1].lower())
        
        if not file_changes:
            return {
                'largest_file_changes': 0,
                'has_large_files': False,
                'has_many_small_changes': False,
                'diversity_score': 0.0
            }
        
        largest_file_changes = max(file_changes)
        has_large_files = largest_file_changes > self.LARGE_FILE_THRESHOLD
        
        # Check if many files have small changes
        small_change_files = sum(1 for changes in file_changes if changes < 10)
        has_many_small_changes = (
            small_change_files / len(file_changes) > self.MANY_SMALL_CHANGES_THRESHOLD
        )
        
        # Calculate file diversity score (0.0 to 1.0)
        # Higher score = more diverse file types
        diversity_score = min(1.0, len(file_types) / max(len(files), 1))
        
        return {
            'largest_file_changes': largest_file_changes,
            'has_large_files': has_large_files,
            'has_many_small_changes': has_many_small_changes,
            'diversity_score': diversity_score
        }
    
    def get_chunking_recommendation(self, metrics: PrSizeMetrics) -> Dict[str, Any]:
        """
        Get detailed chunking recommendations for a classified PR.
        
        Args:
            metrics: PR size metrics from classify_pr()
            
        Returns:
            Chunking strategy recommendations
        """
        
        if metrics.size_category == PrSizeCategory.SMALL:
            return {
                "should_chunk": False,
                "strategy": "single_pass_analysis",
                "estimated_duration": "30-60 seconds",
                "recommendation": "Full LLM analysis in single pass"
            }
        
        elif metrics.size_category == PrSizeCategory.MEDIUM:
            # Calculate chunking parameters
            chunk_count = metrics.estimated_chunks
            estimated_duration = chunk_count * self.CHUNK_TIMEOUT_SECONDS
            
            return {
                "should_chunk": True,
                "strategy": "file_based_chunking",
                "chunk_count": chunk_count,
                "chunk_size_lines": self.CHUNK_SIZE_LINES,
                "chunk_timeout": self.CHUNK_TIMEOUT_SECONDS,
                "estimated_duration": f"{estimated_duration} seconds",
                "recommendation": (
                    f"Chunk into {chunk_count} parts of ~{self.CHUNK_SIZE_LINES} lines each"
                ),
                "special_considerations": self._get_chunking_considerations(metrics)
            }
        
        else:  # LARGE
            return {
                "should_chunk": False,
                "strategy": "pattern_detection_only",
                "estimated_duration": "5-10 seconds",
                "recommendation": "Skip LLM analysis, use pattern detection only",
                "reason": f"Too large ({metrics.total_changes} lines, {metrics.changed_files} files)"
            }
    
    def _get_chunking_considerations(self, metrics: PrSizeMetrics) -> List[str]:
        """Get special considerations for chunking this PR."""
        considerations = []
        
        if metrics.has_large_files:
            considerations.append(
                f"Contains large files (max {metrics.largest_file_changes} lines) - "
                "may need single-file chunks"
            )
        
        if metrics.has_many_small_changes:
            considerations.append(
                "Many small file changes - group related files together"
            )
        
        if metrics.file_diversity_score > 0.7:
            considerations.append(
                "High file diversity - consider grouping by file type or component"
            )
        
        if metrics.files_per_change_ratio > 0.5:
            considerations.append(
                "Many files with few changes - efficient chunking possible"
            )
        
        return considerations


# Global classifier instance
_classifier_instance: Optional[PrSizeClassifier] = None


def get_classifier() -> PrSizeClassifier:
    """Get the global PR size classifier instance."""
    global _classifier_instance
    
    if _classifier_instance is None:
        _classifier_instance = PrSizeClassifier()
    
    return _classifier_instance


def classify_pr_size(pr_data: Dict[str, Any]) -> PrSizeMetrics:
    """
    Convenience function to classify PR size.
    
    Args:
        pr_data: PR data from GitHub API
        
    Returns:
        PR size metrics and classification
    """
    classifier = get_classifier()
    return classifier.classify_pr(pr_data)


def should_use_chunked_analysis(pr_data: Dict[str, Any]) -> bool:
    """
    Quick check if PR should use chunked analysis.
    
    Args:
        pr_data: PR data from GitHub API
        
    Returns:
        True if chunked analysis is recommended
    """
    metrics = classify_pr_size(pr_data)
    return metrics.size_category == PrSizeCategory.MEDIUM