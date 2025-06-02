"""
PR Size Classifier

Multi-dimensional PR size classification system.
This module handles PR size analysis extracted from the monolithic PRReviewTool.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PRSizeClassifier:
    """
    Multi-dimensional PR size classification engine.
    
    Classifies PRs based on:
    - Line changes (additions + deletions)
    - File count 
    - Character count of diff
    - Special handling for test PRs
    
    Determines overall size and review strategy.
    """
    
    # Size classification thresholds
    LINE_THRESHOLDS = {
        "SMALL": 500,
        "MEDIUM": 1500, 
        "LARGE": 5000
    }
    
    FILE_THRESHOLDS = {
        "SMALL": 3,
        "MEDIUM": 8,
        "LARGE": 20
    }
    
    CHAR_THRESHOLDS = {
        "REGULAR": {"LARGE": 50000, "VERY_LARGE": 100000},
        "TEST": {"LARGE": 100000, "VERY_LARGE": 300000}  # More lenient for test PRs
    }
    
    def __init__(self):
        """Initialize the PR size classifier."""
        self.logger = logger
    
    def classify_pr_size(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform multi-dimensional PR size classification.
        
        Args:
            pr_data: PR data from data collector
            
        Returns:
            Comprehensive size analysis with strategy recommendation
        """
        stats = pr_data["statistics"]
        total_changes = stats["total_changes"]
        files_count = stats["files_count"]
        
        # Line-based classification
        size_by_lines = self._classify_by_lines(total_changes)
        
        # File-based classification  
        size_by_files = self._classify_by_files(files_count)
        
        # Character-based classification with test PR detection
        size_by_chars = self._classify_by_chars(pr_data)
        
        # Overall size determination
        overall_size = self._determine_overall_size([size_by_lines, size_by_files, size_by_chars])
        
        # Review strategy determination
        review_strategy = self._determine_review_strategy(overall_size, total_changes)
        
        classification = {
            "size_by_lines": size_by_lines,
            "size_by_files": size_by_files,
            "size_by_chars": size_by_chars,
            "overall_size": overall_size,
            "review_strategy": review_strategy,
            "size_reasons": [
                f"{total_changes} line changes ({size_by_lines})",
                f"{files_count} files ({size_by_files})",
                f"{len(pr_data.get('diff', ''))} char diff ({size_by_chars})"
            ]
        }
        
        self.logger.info(f"📏 PR size classification: {overall_size} "
                        f"(Lines: {size_by_lines}, Files: {size_by_files}, Chars: {size_by_chars})")
        
        return classification
    
    def _classify_by_lines(self, total_changes: int) -> str:
        """Classify PR size by total line changes."""
        if total_changes <= self.LINE_THRESHOLDS["SMALL"]:
            return "SMALL"
        elif total_changes <= self.LINE_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        elif total_changes <= self.LINE_THRESHOLDS["LARGE"]:
            return "LARGE"
        else:
            return "VERY_LARGE"
    
    def _classify_by_files(self, files_count: int) -> str:
        """Classify PR size by number of files changed."""
        if files_count <= self.FILE_THRESHOLDS["SMALL"]:
            return "SMALL"
        elif files_count <= self.FILE_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        elif files_count <= self.FILE_THRESHOLDS["LARGE"]:
            return "LARGE"
        else:
            return "VERY_LARGE"
    
    def _classify_by_chars(self, pr_data: Dict[str, Any]) -> str:
        """Classify PR size by character count with test PR detection."""
        diff_size = len(pr_data.get("diff", ""))
        files = pr_data.get("files", [])
        
        # Detect if this is primarily a test PR
        is_test_pr = self._is_test_pr(files)
        
        # Use appropriate thresholds
        thresholds = self.CHAR_THRESHOLDS["TEST"] if is_test_pr else self.CHAR_THRESHOLDS["REGULAR"]
        
        if diff_size > thresholds["VERY_LARGE"]:
            return "VERY_LARGE"
        elif diff_size > thresholds["LARGE"]:
            return "LARGE"
        else:
            return "SMALL"
    
    def _is_test_pr(self, files: list) -> bool:
        """
        Determine if this is primarily a test PR.
        
        Args:
            files: List of changed files
            
        Returns:
            True if >50% of files are test files
        """
        if not files:
            return False
            
        test_files = [f for f in files if "test" in f.get("path", "").lower()]
        return len(test_files) / len(files) > 0.5
    
    def _determine_overall_size(self, sizes: list) -> str:
        """Determine overall size from individual classifications."""
        if "VERY_LARGE" in sizes:
            return "VERY_LARGE"
        elif "LARGE" in sizes:
            return "LARGE"
        elif "MEDIUM" in sizes:
            return "MEDIUM"
        else:
            return "SMALL"
    
    def _determine_review_strategy(self, overall_size: str, total_changes: int) -> str:
        """
        Determine review strategy based on size analysis.
        
        Args:
            overall_size: Overall size classification
            total_changes: Total line changes
            
        Returns:
            Review strategy: FULL_ANALYSIS or SUMMARY_ANALYSIS
        """
        if overall_size in ["VERY_LARGE", "LARGE"] or total_changes > 10000:
            return "SUMMARY_ANALYSIS"
        else:
            return "FULL_ANALYSIS"