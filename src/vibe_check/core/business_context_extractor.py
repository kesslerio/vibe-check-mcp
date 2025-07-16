"""
Business Context Extractor for Vibe Check MCP

This module provides intelligent context extraction to distinguish between:
- Planning discussions vs completion reports
- Review requests vs implementation proposals
- Business process descriptions vs technical anti-patterns

Helps prevent premature pattern matching by understanding user intent.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Primary context types for business understanding"""
    COMPLETION_REPORT = "completion_report"
    REVIEW_REQUEST = "review_request"
    PLANNING_DISCUSSION = "planning_discussion"
    IMPLEMENTATION_PROPOSAL = "implementation_proposal"
    PROCESS_DESCRIPTION = "process_description"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    """Confidence levels for context determination"""
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    UNCERTAIN = 0.2


class ConfidenceThresholds:
    """Thresholds for confidence-based decisions"""
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7


@dataclass
class BusinessContext:
    """Structured business context information"""
    primary_type: ContextType
    confidence: float
    indicators: List[str]
    questions_needed: List[str]
    metadata: Dict[str, any]
    
    @property
    def is_completion_report(self) -> bool:
        return self.primary_type == ContextType.COMPLETION_REPORT
    
    @property
    def is_review_request(self) -> bool:
        return self.primary_type == ContextType.REVIEW_REQUEST
    
    @property
    def is_planning_phase(self) -> bool:
        return self.primary_type in [ContextType.PLANNING_DISCUSSION, ContextType.IMPLEMENTATION_PROPOSAL]
    
    @property
    def needs_clarification(self) -> bool:
        return self.confidence < ConfidenceLevel.MEDIUM.value or len(self.questions_needed) > 0


class BusinessContextExtractor:
    """Extract business context to prevent premature pattern matching"""
    
    # Completion indicators with high confidence
    COMPLETION_PATTERNS = [
        (r'\b(?:completed|finished|implemented|done|shipped)\s+(?:the\s+)?(?:issue|feature|story|ticket|task|pr|pull\s+request)\s*#?\d+', 0.9),
        (r'\b(?:just|already|successfully)?\s*(?:completed|finished|implemented|shipped|deployed|released)\s+(?:the\s+)?(?:implementation|feature|change|update|integration)', 0.8),
        (r'\b(?:here\'s|this\s+is)\s+(?:what\s+i|the)\s+(?:did|implemented|built|created)', 0.7),
        (r'\b(?:i\'ve|we\'ve)\s+(?:just|already)?\s*(?:implemented|built|created|updated|changed)', 0.7),
        (r'\bfollow(?:ed|ing)\s+(?:the\s+)?(?:plan|design|requirements|specification|issue)', 0.6),
        (r'\b(?:just\s+)?finished\s+implementing', 0.8),  # Added for "Just finished implementing"
    ]
    
    # Review request indicators
    REVIEW_PATTERNS = [
        (r'\b(?:did\s+i\s+miss|what\s+did\s+i\s+miss|anything\s+(?:i\s+)?(?:missed|forgot))', 0.9),
        (r'\b(?:feedback\s+on|review\s+(?:of|this)|thoughts\s+on|look\s+good|check\s+(?:my|this))', 0.8),
        (r'\b(?:any\s+)?(?:suggestions|improvements|concerns|issues)\s*\?', 0.6),
        (r'\b(?:what\s+do\s+you\s+think|how\s+does\s+this\s+look|is\s+this\s+correct)', 0.7),
    ]
    
    # Planning indicators
    PLANNING_PATTERNS = [
        (r'\b(?:planning|going|want|need)\s+to\s+(?:build|implement|create|develop)', 0.8),
        (r'\b(?:should\s+i|should\s+we|can\s+i|can\s+we)\s+(?:build|implement|create|use)', 0.7),
        (r'\b(?:thinking\s+(?:of|about)|considering|evaluating|exploring)', 0.6),
        (r'\b(?:how\s+to|best\s+way\s+to|approach\s+for)\s+(?:implement|build|create)', 0.7),
        (r'\bhow\s+should\s+i\s+approach', 0.6),  # Added for "How should I approach"
    ]
    
    # Process description indicators
    PROCESS_PATTERNS = [
        (r'\b(?:strategy|approach|method|process)\s+(?:update|change|migration|refactor)', 0.7),
        (r'\b(?:changed|updated|modified)\s+from\s+.+\s+to\s+', 0.8),
        (r'\b(?:three|3)-(?:path|step|phase|tier)\s+(?:approach|strategy|process)', 0.7),
        (r'\b(?:workflow|pipeline|architecture)\s+(?:design|implementation|update)', 0.6),
    ]
    
    def extract_context(self, query: str, additional_context: Optional[str] = None, phase: Optional[str] = None) -> BusinessContext:
        """
        Extract business context from user query and additional context.
        
        Args:
            query: User's query text
            additional_context: Optional additional context
            phase: Optional explicit phase (e.g., "planning", "implementation", "review")
                  When provided, acts as high-confidence signal to bypass ambiguity detection
        
        Returns a structured context with confidence level and suggested questions
        for clarification when confidence is low/medium.
        """
        full_text = f"{query} {additional_context or ''}".lower()
        
        # Handle explicit phase parameter - HIGH CONFIDENCE SIGNAL
        if phase:
            phase_lower = phase.lower()
            if phase_lower == "planning":
                # Explicit planning phase - skip ambiguity detection
                context_type = ContextType.PLANNING_DISCUSSION
                confidence = ConfidenceLevel.HIGH.value
                questions = []
                detected_patterns = [f"explicit_phase: planning (confidence: {confidence})"]
                logger.info(f"Explicit phase=planning detected, bypassing ambiguity detection")
            elif phase_lower in ["implementation", "coding", "development"]:
                context_type = ContextType.IMPLEMENTATION_PROPOSAL
                confidence = ConfidenceLevel.HIGH.value
                questions = []
                detected_patterns = [f"explicit_phase: {phase_lower} (confidence: {confidence})"]
                logger.info(f"Explicit phase={phase_lower} detected, bypassing ambiguity detection")
            elif phase_lower == "review":
                context_type = ContextType.REVIEW_REQUEST
                confidence = ConfidenceLevel.HIGH.value
                questions = []
                detected_patterns = [f"explicit_phase: review (confidence: {confidence})"]
                logger.info(f"Explicit phase=review detected, bypassing ambiguity detection")
            else:
                # Unknown phase - fall back to pattern detection
                logger.warning(f"Unknown explicit phase '{phase}', falling back to pattern detection")
                phase = None  # Reset to trigger normal detection below
        
        # Normal pattern detection when no explicit phase or unknown phase
        if not phase:
            # Track all detected patterns
            detected_patterns = []
            
            # Check for completion indicators
            completion_score = self._check_patterns(full_text, self.COMPLETION_PATTERNS, "completion")
            detected_patterns.extend(completion_score[2])
            
            # Check for review requests
            review_score = self._check_patterns(full_text, self.REVIEW_PATTERNS, "review")
            detected_patterns.extend(review_score[2])
            
            # Check for planning indicators
            planning_score = self._check_patterns(full_text, self.PLANNING_PATTERNS, "planning")
            detected_patterns.extend(planning_score[2])
            
            # Check for process descriptions
            process_score = self._check_patterns(full_text, self.PROCESS_PATTERNS, "process")
            detected_patterns.extend(process_score[2])
            
            # Determine primary context type
            context_type, confidence, questions = self._determine_context_type(
                completion_score[0], review_score[0], planning_score[0], process_score[0],
                full_text
            )
        
        # Extract metadata
        metadata = self._extract_metadata(full_text)
        
        return BusinessContext(
            primary_type=context_type,
            confidence=confidence,
            indicators=detected_patterns,
            questions_needed=questions,
            metadata=metadata
        )
    
    def _check_patterns(self, text: str, patterns: List[Tuple[str, float]], pattern_type: str) -> Tuple[float, str, List[str]]:
        """Check patterns and return score, type, and matched indicators"""
        total_score = 0.0
        matched_indicators = []
        
        for pattern, weight in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    total_score += weight
                    matched_indicators.append(f"{pattern_type}: {pattern[:50]}...")
            except re.error as e:
                logger.warning(f"Regex pattern error in {pattern_type}: {pattern[:50]}... - {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error checking pattern in {pattern_type}: {str(e)}")
                continue
        
        return (total_score, pattern_type, matched_indicators)
    
    def _determine_context_type(self, completion_score: float, review_score: float, 
                                planning_score: float, process_score: float, 
                                full_text: str) -> Tuple[ContextType, float, List[str]]:
        """Determine primary context type and generate clarifying questions if needed"""
        scores = {
            ContextType.COMPLETION_REPORT: completion_score,
            ContextType.REVIEW_REQUEST: review_score,
            ContextType.PLANNING_DISCUSSION: planning_score,
            ContextType.PROCESS_DESCRIPTION: process_score
        }
        
        # Get the highest scoring context
        max_score = max(scores.values())
        
        # If no clear signal, return unknown with questions
        if max_score < ConfidenceThresholds.LOW:
            return (ContextType.UNKNOWN, ConfidenceLevel.UNCERTAIN.value, 
                   self._generate_clarifying_questions(full_text, "unknown"))
        
        # Get the primary type - prioritize completion/review over process
        primary_type = max(scores, key=scores.get)
        
        # Special handling for mixed signals
        if completion_score > ConfidenceThresholds.MEDIUM and review_score > ConfidenceThresholds.MEDIUM:
            # Both indicators present - it's a completion with review request
            primary_type = ContextType.COMPLETION_REPORT
            confidence = ConfidenceLevel.HIGH.value
            questions = []
        elif completion_score > ConfidenceThresholds.LOW and planning_score > ConfidenceThresholds.LOW:
            # Mixed completion and planning signals - lower confidence
            primary_type = ContextType.COMPLETION_REPORT if completion_score > planning_score else ContextType.PLANNING_DISCUSSION
            confidence = ConfidenceLevel.MEDIUM.value
            questions = ["Are you describing completed work or planning future implementation?"]
        else:
            # Calculate confidence based on score difference
            sorted_scores = sorted(scores.values(), reverse=True)
            score_diff = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]
            
            # Determine confidence level
            if score_diff > ConfidenceThresholds.MEDIUM and max_score > ConfidenceThresholds.HIGH:
                confidence = ConfidenceLevel.HIGH.value
                questions = []
            elif score_diff > ConfidenceThresholds.LOW or max_score > ConfidenceThresholds.MEDIUM:
                confidence = ConfidenceLevel.MEDIUM.value
                questions = self._generate_clarifying_questions(full_text, primary_type.value) if max_score < ConfidenceThresholds.HIGH else []
            else:
                confidence = ConfidenceLevel.LOW.value
                questions = self._generate_clarifying_questions(full_text, primary_type.value)
        
        return (primary_type, confidence, questions)
    
    def _generate_clarifying_questions(self, text: str, context_type: str) -> List[str]:
        """Generate intelligent clarifying questions based on context"""
        questions = []
        
        # Check for ambiguous implementation language
        if re.search(r'\b(?:implement|build|create)', text, re.IGNORECASE):
            has_completion_words = re.search(r'\b(?:completed|finished|done|implemented|shipped)', text, re.IGNORECASE)
            has_planning_words = re.search(r'\b(?:planning|going|want)\s+to', text, re.IGNORECASE)
            
            if not has_completion_words and not has_planning_words:
                questions.append("Are you planning to implement this, or have you already completed the implementation?")
        
        # Check for review ambiguity
        if context_type == "review_request":
            questions.append("Are you looking for feedback on completed work, or guidance on how to approach this?")
        
        # Check for missing context about status
        if context_type == "unknown":
            questions.append("Could you clarify - is this something you've already built, or are you planning the implementation?")
            questions.append("What specific feedback or guidance are you looking for?")
        
        # Technology-specific clarification - only for planning contexts
        if context_type in ["planning_discussion", "unknown"]:
            if re.search(r'\b(?:api|sdk|integration|service)', text, re.IGNORECASE):
                if not re.search(r'\b(?:official|standard|existing|already)', text, re.IGNORECASE):
                    questions.append("Have you already researched the official SDK/API documentation for this integration?")
        
        return questions[:2]  # Limit to 2 most relevant questions
    
    def _extract_metadata(self, text: str) -> Dict[str, any]:
        """Extract relevant metadata from the text"""
        metadata = {}
        
        # Extract issue/PR numbers
        issue_match = re.search(r'(?:issue|pr|pull\s+request)\s*#?(\d+)', text, re.IGNORECASE)
        if issue_match:
            metadata['reference_number'] = issue_match.group(1)
        
        # Extract technology mentions
        tech_keywords = ['api', 'sdk', 'integration', 'service', 'database', 'framework']
        detected_tech = [tech for tech in tech_keywords if tech in text.lower()]
        if detected_tech:
            metadata['technologies'] = detected_tech
        
        # Extract action verbs for better understanding
        action_verbs = re.findall(r'\b(?:implemented|built|created|updated|changed|planning|considering|completed)\b', text, re.IGNORECASE)
        if action_verbs:
            metadata['actions'] = list(set([v.lower() for v in action_verbs]))
        
        return metadata