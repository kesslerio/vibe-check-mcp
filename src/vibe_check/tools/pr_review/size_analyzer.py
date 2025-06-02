"""
PR Size Analysis Module

Handles multi-dimensional PR size classification and review strategy determination.
Extracted from pr_review.py to improve modularity.
"""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PRSizeAnalyzer:
    """Handles multi-dimensional PR size classification and review strategy."""
    
    def classify_pr_size(self, pr_data: Dict) -> Dict[str, Any]:
        """
        Multi-dimensional PR size classification.
        Replaces lines 227-307 of original pr_review.py.
        """
        stats = pr_data["statistics"]
        total_changes = stats["total_changes"]
        files_count = stats["files_count"]
        
        # Line-based classification
        if total_changes <= 500:
            size_by_lines = "SMALL"
        elif total_changes <= 1500:
            size_by_lines = "MEDIUM"
        elif total_changes <= 5000:
            size_by_lines = "LARGE"
        else:
            size_by_lines = "VERY_LARGE"
            
        # File-based classification
        if files_count <= 3:
            size_by_files = "SMALL"
        elif files_count <= 8:
            size_by_files = "MEDIUM"
        elif files_count <= 20:
            size_by_files = "LARGE"
        else:
            size_by_files = "VERY_LARGE"
            
        # Character-based classification (from diff size)
        # Special handling for test PRs - they're legitimate large files
        diff_size = len(pr_data.get("diff", ""))
        files = pr_data.get("files", [])
        is_test_pr = any("test" in f.get("path", "").lower() for f in files) and len([f for f in files if "test" in f.get("path", "").lower()]) / len(files) > 0.5
        
        if is_test_pr:
            # Test PRs: More lenient thresholds (tests are verbose but simple)
            if diff_size > 300000:  # 300k instead of 100k
                size_by_chars = "VERY_LARGE"
            elif diff_size > 100000:  # 100k instead of 50k
                size_by_chars = "LARGE"
            else:
                size_by_chars = "SMALL"
        else:
            # Regular PRs: Original thresholds
            if diff_size > 100000:
                size_by_chars = "VERY_LARGE"
            elif diff_size > 50000:
                size_by_chars = "LARGE"
            else:
                size_by_chars = "SMALL"
            
        # Overall size determination
        sizes = [size_by_lines, size_by_files, size_by_chars]
        if "VERY_LARGE" in sizes:
            overall_size = "VERY_LARGE"
        elif "LARGE" in sizes:
            overall_size = "LARGE"
        elif "MEDIUM" in sizes:
            overall_size = "MEDIUM"
        else:
            overall_size = "SMALL"
            
        # Review strategy determination
        if overall_size in ["VERY_LARGE", "LARGE"] or total_changes > 10000:
            review_strategy = "SUMMARY_ANALYSIS"
        else:
            review_strategy = "FULL_ANALYSIS"
            
        return {
            "size_by_lines": size_by_lines,
            "size_by_files": size_by_files,
            "size_by_chars": size_by_chars,
            "overall_size": overall_size,
            "review_strategy": review_strategy,
            "size_reasons": [
                f"{total_changes} line changes ({size_by_lines})",
                f"{files_count} files ({size_by_files})",
                f"{diff_size} char diff ({size_by_chars})"
            ]
        }
    
    def detect_re_review(self, pr_data: Dict, force_re_review: bool) -> Dict[str, Any]:
        """
        Detect re-review mode and extract previous review context.
        Replaces lines 309-337 of original pr_review.py.
        """
        # Check existing comments for automated review patterns
        automated_review_patterns = [
            "🎯.*Overview", "## 🎯", "🔍.*Analysis", "⚠️.*Critical Issues",
            "💡.*Suggestions", "Automated PR Review", "🔍 Automated PR Review",
            "## 🤖 Enhanced PR Review"
        ]
        
        comments = pr_data.get("comments", [])
        has_automated_reviews = any(
            any(re.search(pattern, comment.get("body", "")) for pattern in automated_review_patterns)
            for comment in comments
        )
        
        is_re_review = force_re_review or has_automated_reviews
        review_count = sum(
            1 for comment in comments
            if any(re.search(pattern, comment.get("body", "")) for pattern in automated_review_patterns)
        )
        
        return {
            "is_re_review": is_re_review,
            "review_count": review_count,
            "previous_reviews": comments if is_re_review else []
        }