"""
Review Context Analyzer

Handles re-review detection and context tracking.
This module extracts re-review analysis functionality from the monolithic PRReviewTool.
"""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ReviewContextAnalyzer:
    """
    Analyzes review context and detects re-review scenarios.

    Responsibilities:
    - Detect existing automated reviews
    - Count previous review attempts
    - Extract relevant context from previous reviews
    - Determine if this is a re-review scenario
    """

    # Patterns that indicate automated review comments
    AUTOMATED_REVIEW_PATTERNS = [
        r"🎯.*Overview",
        r"## 🎯",
        r"🔍.*Analysis",
        r"⚠️.*Critical Issues",
        r"💡.*Suggestions",
        r"Automated PR Review",
        r"🔍 Automated PR Review",
        r"## 🤖 Enhanced PR Review",
    ]

    def __init__(self):
        """Initialize the review context analyzer."""
        self.logger = logger

    def detect_re_review(
        self, pr_data: Dict[str, Any], force_re_review: bool = False
    ) -> Dict[str, Any]:
        """
        Detect re-review mode and extract previous review context.

        Args:
            pr_data: PR data from data collector
            force_re_review: Force re-review mode regardless of detection

        Returns:
            Review context with re-review status and previous review data
        """
        comments = pr_data.get("comments", [])

        # Check existing comments for automated review patterns
        has_automated_reviews = self._has_automated_reviews(comments)

        # Determine if this is a re-review
        is_re_review = force_re_review or has_automated_reviews

        # Count previous automated reviews
        review_count = self._count_automated_reviews(comments)

        # Extract relevant previous reviews if this is a re-review
        previous_reviews = comments if is_re_review else []

        context = {
            "is_re_review": is_re_review,
            "review_count": review_count,
            "previous_reviews": previous_reviews,
            "force_re_review": force_re_review,
            "has_automated_reviews": has_automated_reviews,
        }

        if is_re_review:
            self.logger.info(
                f"🔄 Re-review detected: {review_count} previous automated reviews found"
            )
        else:
            self.logger.info("✨ First review - no previous automated reviews detected")

        return context

    def _has_automated_reviews(self, comments: list) -> bool:
        """
        Check if any comments match automated review patterns.

        Args:
            comments: List of PR comments

        Returns:
            True if automated review patterns are found
        """
        return any(
            self._matches_automated_pattern(comment.get("body", ""))
            for comment in comments
        )

    def _count_automated_reviews(self, comments: list) -> int:
        """
        Count the number of automated reviews in comments.

        Args:
            comments: List of PR comments

        Returns:
            Number of automated review comments found
        """
        return sum(
            1
            for comment in comments
            if self._matches_automated_pattern(comment.get("body", ""))
        )

    def _matches_automated_pattern(self, comment_body: str) -> bool:
        """
        Check if a comment body matches automated review patterns.

        Args:
            comment_body: Comment text to analyze

        Returns:
            True if comment matches any automated review pattern
        """
        return any(
            re.search(pattern, comment_body, re.IGNORECASE)
            for pattern in self.AUTOMATED_REVIEW_PATTERNS
        )

    def extract_review_history_summary(self, previous_reviews: list) -> str:
        """
        Extract a summary of previous review history.

        Args:
            previous_reviews: List of previous review comments

        Returns:
            Formatted summary of review history
        """
        if not previous_reviews:
            return "No previous automated reviews found."

        automated_reviews = [
            review
            for review in previous_reviews
            if self._matches_automated_pattern(review.get("body", ""))
        ]

        if not automated_reviews:
            return "No previous automated reviews found."

        summary_parts = [
            f"Found {len(automated_reviews)} previous automated review(s):"
        ]

        for i, review in enumerate(automated_reviews[-3:], 1):  # Show last 3 reviews
            author = review.get("author", {}).get("login", "Unknown")
            created_at = review.get("createdAt", "Unknown time")
            body_preview = (
                review.get("body", "")[:100] + "..."
                if len(review.get("body", "")) > 100
                else review.get("body", "")
            )

            summary_parts.append(f"  {i}. By {author} at {created_at}")
            summary_parts.append(f"     Preview: {body_preview}")

        return "\n".join(summary_parts)
