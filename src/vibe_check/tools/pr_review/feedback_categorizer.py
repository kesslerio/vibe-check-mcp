"""
Feedback Categorizer

Implements CLAUDE.md PR review guidelines for systematic feedback categorization.
Uses Clear-Thought decision framework for evaluating review items.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReviewItem:
    """Represents a single review feedback item."""
    content: str
    category: str  # CRITICAL, IMPORTANT, NICE_TO_HAVE, OVERENGINEERING
    rationale: str
    action_required: bool
    follow_up_worthy: bool
    confidence: float


class FeedbackCategorizer:
    """
    Categorizes PR feedback following CLAUDE.md guidelines.
    
    Implements systematic decision framework for review item evaluation:
    - CRITICAL (blocking): Must fix in current PR
    - IMPORTANT (actionable): Create follow-up issues for future work
    - NICE-TO-HAVE (optional): Evaluate if truly needed or overengineering
    - OVERENGINEERING (reject): Recommendations that add unnecessary complexity
    """
    
    def __init__(self):
        """Initialize feedback categorizer with decision criteria."""
        self.logger = logger
        
        # Decision criteria based on CLAUDE.md guidelines
        self.critical_indicators = [
            "missing issue linkage",
            "security vulnerability", 
            "critical bug",
            "breaking functionality",
            "breaks merge",
            "compilation error",
            "test failure"
        ]
        
        self.important_indicators = [
            "performance improvement",
            "documentation enhancement", 
            "refactoring suggestion",
            "error handling",
            "validation improvement",
            "user experience"
        ]
        
        self.overengineering_indicators = [
            "abstract factory",
            "design pattern",
            "premature optimization",
            "over-abstraction",
            "complex architecture",
            "unnecessary complexity"
        ]
        
        self.nice_to_have_indicators = [
            "style preference",
            "minor optimization",
            "cosmetic change",
            "subjective improvement",
            "nice to have"
        ]
    
    def categorize_feedback_items(self, feedback_text: str) -> List[ReviewItem]:
        """
        Categorize individual feedback items from review text.
        
        Args:
            feedback_text: Raw feedback content
            
        Returns:
            List of categorized review items
        """
        self.logger.info("🔍 Categorizing feedback items using decision framework...")
        
        # Split feedback into individual items (simple approach)
        items = self._extract_feedback_items(feedback_text)
        categorized_items = []
        
        for item_text in items:
            review_item = self._categorize_single_item(item_text)
            categorized_items.append(review_item)
        
        self.logger.info(f"✅ Categorized {len(categorized_items)} feedback items")
        return categorized_items
    
    def _extract_feedback_items(self, text: str) -> List[str]:
        """Extract individual feedback items from text."""
        # Simple extraction - split by bullet points or numbered lists
        import re
        
        # Split by common list patterns
        patterns = [
            r'[-*•]\s+(.+?)(?=[-*•]|\n\n|\Z)',  # Bullet points
            r'\d+\.\s+(.+?)(?=\d+\.|\n\n|\Z)',  # Numbered lists
            r'\n\s*(.+?)(?=\n\s*\n|\Z)'  # Paragraph breaks
        ]
        
        items = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            if matches:
                items.extend([match.strip() for match in matches if match.strip()])
                break  # Use first successful pattern
        
        # Fallback: treat whole text as single item
        if not items and text.strip():
            items = [text.strip()]
        
        return items
    
    def _categorize_single_item(self, item_text: str) -> ReviewItem:
        """
        Categorize a single feedback item using decision framework.
        
        Args:
            item_text: Individual feedback item text
            
        Returns:
            Categorized review item
        """
        item_lower = item_text.lower()
        
        # Check for critical indicators
        critical_score = sum(1 for indicator in self.critical_indicators 
                           if indicator in item_lower)
        
        # Check for important indicators  
        important_score = sum(1 for indicator in self.important_indicators
                            if indicator in item_lower)
        
        # Check for overengineering indicators
        overengineering_score = sum(1 for indicator in self.overengineering_indicators
                                  if indicator in item_lower)
        
        # Check for nice-to-have indicators
        nice_to_have_score = sum(1 for indicator in self.nice_to_have_indicators
                               if indicator in item_lower)
        
        # Apply decision logic
        if critical_score > 0:
            category = "CRITICAL"
            action_required = True
            follow_up_worthy = False
            confidence = min(0.9, 0.7 + (critical_score * 0.1))
            rationale = "Contains critical indicators requiring immediate attention"
            
        elif overengineering_score > 0:
            category = "OVERENGINEERING"
            action_required = False
            follow_up_worthy = False
            confidence = min(0.8, 0.6 + (overengineering_score * 0.1))
            rationale = "May add unnecessary complexity without clear business value"
            
        elif important_score > 0:
            category = "IMPORTANT"
            action_required = False
            follow_up_worthy = True
            confidence = min(0.8, 0.5 + (important_score * 0.1))
            rationale = "Good suggestion that could be addressed in follow-up work"
            
        elif nice_to_have_score > 0:
            category = "NICE_TO_HAVE"
            action_required = False
            follow_up_worthy = False
            confidence = min(0.7, 0.4 + (nice_to_have_score * 0.1))
            rationale = "Minor improvement with unclear value (YAGNI applies)"
            
        else:
            # Default classification based on content analysis
            if any(word in item_lower for word in ["must", "required", "need", "should fix"]):
                category = "CRITICAL"
                action_required = True
                follow_up_worthy = False
                confidence = 0.6
                rationale = "Language suggests urgency or requirement"
            else:
                category = "IMPORTANT"
                action_required = False
                follow_up_worthy = True
                confidence = 0.5
                rationale = "Default classification for actionable feedback"
        
        return ReviewItem(
            content=item_text,
            category=category,
            rationale=rationale,
            action_required=action_required,
            follow_up_worthy=follow_up_worthy,
            confidence=confidence
        )
    
    def generate_categorization_summary(self, review_items: List[ReviewItem]) -> Dict[str, Any]:
        """
        Generate summary of categorized feedback for decision making.
        
        Args:
            review_items: List of categorized review items
            
        Returns:
            Summary with recommendations and statistics
        """
        summary = {
            "total_items": len(review_items),
            "categories": {
                "CRITICAL": [],
                "IMPORTANT": [],
                "NICE_TO_HAVE": [],
                "OVERENGINEERING": []
            },
            "action_summary": {
                "must_fix_before_merge": 0,
                "potential_follow_ups": 0,
                "can_ignore": 0
            },
            "decision_recommendation": ""
        }
        
        # Categorize items
        for item in review_items:
            summary["categories"][item.category].append({
                "content": item.content,
                "rationale": item.rationale,
                "confidence": item.confidence
            })
            
            if item.action_required:
                summary["action_summary"]["must_fix_before_merge"] += 1
            elif item.follow_up_worthy:
                summary["action_summary"]["potential_follow_ups"] += 1
            else:
                summary["action_summary"]["can_ignore"] += 1
        
        # Generate decision recommendation
        critical_count = len(summary["categories"]["CRITICAL"])
        important_count = len(summary["categories"]["IMPORTANT"])
        
        if critical_count > 0:
            summary["decision_recommendation"] = f"REQUEST_CHANGES - {critical_count} critical issue(s) must be fixed before merge"
        elif important_count > 2:
            summary["decision_recommendation"] = f"APPROVE with follow-up - Consider creating {min(important_count, 2)} follow-up issues"
        else:
            summary["decision_recommendation"] = "APPROVE - No blocking issues found"
        
        self.logger.info(f"📊 Categorization summary: {critical_count} critical, {important_count} important")
        
        return summary