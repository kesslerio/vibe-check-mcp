"""
Semantic Intent Classification Engine

Provides semantic understanding of queries through TF-IDF vectorization and 
cosine similarity matching. Replaces naive keyword substitution with actual
intent understanding.

Features:
- Intent classification using TF-IDF + cosine similarity
- Pre-defined intent templates for common query types
- Semantic matching to find contextually appropriate responses
- Lightweight and fast (no transformer models needed)
"""

import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class QueryIntent:
    """Represents the classified intent of a query"""
    intent_type: str  # tool_evaluation, technical_debt, decision, debugging, implementation
    confidence: float
    key_entities: List[str]  # Extracted entities (tools, technologies, etc.)
    context_signals: List[str]  # Context clues that influenced classification
    suggested_response_category: str  # Maps to response bank categories


class IntentTemplate:
    """Template for recognizing specific intent patterns"""
    
    def __init__(self, intent_type: str, patterns: List[str], signal_words: List[str]):
        self.intent_type = intent_type
        self.patterns = patterns  # Example queries for this intent
        self.signal_words = signal_words  # Key words that signal this intent
        
    def score_match(self, query: str) -> float:
        """Score how well a query matches this intent template"""
        query_lower = query.lower()
        
        # Check for signal words
        signal_score = sum(1 for word in self.signal_words if word in query_lower)
        signal_score = min(signal_score / max(len(self.signal_words), 1), 1.0)
        
        return signal_score


class QueryIntentClassifier:
    """Classifies query intent using semantic analysis"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 3),
            stop_words='english',
            lowercase=True
        )
        
        # Define intent templates with example patterns
        self.intent_templates = self._build_intent_templates()
        
        # Pre-compute template vectors
        self.template_texts = []
        self.template_labels = []
        for template in self.intent_templates:
            for pattern in template.patterns:
                self.template_texts.append(pattern)
                self.template_labels.append(template.intent_type)
        
        if self.template_texts:
            self.template_vectors = self.vectorizer.fit_transform(self.template_texts)
        else:
            self.template_vectors = None
            
    def _build_intent_templates(self) -> List[IntentTemplate]:
        """Build intent recognition templates"""
        return [
            IntentTemplate(
                intent_type="tool_evaluation",
                patterns=[
                    "should I abandon this tool that's not working",
                    "is it worth continuing with this library",
                    "this tool increased warnings should I stop using it",
                    "when to give up on a failing integration",
                    "tool is causing more problems than solving"
                ],
                signal_words=["abandon", "stop", "quit", "give up", "worth", "failing", "problems", "warnings", "errors"]
            ),
            IntentTemplate(
                intent_type="technical_debt",
                patterns=[
                    "should I refactor this code",
                    "is this technical debt worth addressing",
                    "when to pay down technical debt",
                    "legacy code migration strategy",
                    "consolidate multiple implementations"
                ],
                signal_words=["refactor", "technical debt", "legacy", "consolidate", "migrate", "cleanup", "modernize"]
            ),
            IntentTemplate(
                intent_type="decision",
                patterns=[
                    "should I build or buy",
                    "which framework should I choose",
                    "custom solution vs third party",
                    "is it time to migrate",
                    "choosing between options"
                ],
                signal_words=["should", "choose", "vs", "or", "decide", "which", "better", "compare", "alternative"]
            ),
            IntentTemplate(
                intent_type="debugging",
                patterns=[
                    "how to debug this issue",
                    "finding the root cause",
                    "troubleshooting performance problems",
                    "why is this failing",
                    "tracking down a bug"
                ],
                signal_words=["debug", "troubleshoot", "fix", "issue", "bug", "problem", "failing", "error", "crash"]
            ),
            IntentTemplate(
                intent_type="implementation",
                patterns=[
                    "how to implement this feature",
                    "best way to build this",
                    "implementation strategy for",
                    "how to ship this quickly",
                    "mvp approach for this feature"
                ],
                signal_words=["implement", "build", "create", "ship", "develop", "code", "mvp", "prototype", "feature"]
            ),
            IntentTemplate(
                intent_type="integration",
                patterns=[
                    "how to integrate with this API",
                    "connecting to third party service",
                    "SDK vs custom implementation",
                    "integration best practices",
                    "should I use the official client"
                ],
                signal_words=["integrate", "api", "sdk", "connect", "third-party", "service", "client", "library"]
            ),
            IntentTemplate(
                intent_type="architecture",
                patterns=[
                    "microservices vs monolith",
                    "architectural pattern for this",
                    "system design approach",
                    "scaling strategy",
                    "how to structure this application"
                ],
                signal_words=["architecture", "design", "pattern", "structure", "microservice", "monolith", "scale", "system"]
            )
        ]
    
    def classify_intent(self, query: str, context: Optional[str] = None) -> QueryIntent:
        """Classify the intent of a query using semantic similarity"""
        
        # Combine query with context if provided
        full_text = query
        if context:
            full_text = f"{query} {context}"
        
        # First, try template-based classification
        best_intent = None
        best_score = 0.0
        
        for template in self.intent_templates:
            score = template.score_match(full_text)
            if score > best_score:
                best_score = score
                best_intent = template.intent_type
        
        # If we have pre-computed vectors, use cosine similarity
        if self.template_vectors is not None and len(self.template_texts) > 0:
            try:
                query_vector = self.vectorizer.transform([full_text])
                similarities = cosine_similarity(query_vector, self.template_vectors).flatten()
                
                # Get top matching template
                best_idx = np.argmax(similarities)
                if similarities[best_idx] > 0.3:  # Threshold for semantic match
                    best_intent = self.template_labels[best_idx]
                    best_score = max(best_score, similarities[best_idx])
            except Exception as e:
                logger.warning(f"Semantic matching failed: {e}")
        
        # Extract key entities from the query
        entities = self._extract_entities(full_text)
        
        # Extract context signals
        context_signals = self._extract_context_signals(full_text)
        
        # Map to response category
        response_category = self._map_to_response_category(best_intent or "general")
        
        return QueryIntent(
            intent_type=best_intent or "general",
            confidence=min(best_score, 1.0),
            key_entities=entities,
            context_signals=context_signals,
            suggested_response_category=response_category
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities (tools, technologies, etc.) from text"""
        entities = []
        
        # Common tool/technology patterns
        tool_indicators = ["tool", "library", "framework", "sdk", "api", "service", "package"]
        
        # Simple entity extraction based on capitalization and known patterns
        words = text.split()
        for i, word in enumerate(words):
            # Check for tool indicators followed by names
            if i > 0 and words[i-1].lower() in tool_indicators:
                entities.append(word.strip(".,!?"))
            # Check for capitalized words that might be tool names
            elif word[0].isupper() and word.lower() not in ['i', 'the', 'a', 'an']:
                entities.append(word.strip(".,!?"))
            # Check for code-like terms (contains dash, underscore, or ends with .js, .py, etc.)
            elif '-' in word or '_' in word or any(word.endswith(ext) for ext in ['.js', '.py', '.ts', '.go']):
                entities.append(word.strip(".,!?"))
        
        return list(set(entities))[:5]  # Return up to 5 unique entities
    
    def _extract_context_signals(self, text: str) -> List[str]:
        """Extract context signals that help understand the situation"""
        signals = []
        text_lower = text.lower()
        
        # Negative signals
        if any(word in text_lower for word in ["failing", "broken", "not working", "errors", "warnings"]):
            signals.append("negative_experience")
        
        # Urgency signals  
        if any(word in text_lower for word in ["quickly", "asap", "urgent", "deadline", "today", "now"]):
            signals.append("time_pressure")
        
        # Evaluation signals
        if any(word in text_lower for word in ["worth", "should", "better", "vs", "compare"]):
            signals.append("evaluation_needed")
        
        # Experience signals
        if any(word in text_lower for word in ["tried", "attempted", "failed", "stuck", "struggling"]):
            signals.append("prior_attempts")
        
        return signals
    
    def _map_to_response_category(self, intent_type: str) -> str:
        """Map intent type to response bank category"""
        mapping = {
            "tool_evaluation": "tool_decisions",
            "technical_debt": "debt_management",
            "decision": "architecture_decisions", 
            "debugging": "debugging_strategies",
            "implementation": "implementation_approaches",
            "integration": "integration_patterns",
            "architecture": "architecture_patterns",
            "general": "general_advice"
        }
        return mapping.get(intent_type, "general_advice")


class SemanticResponseMatcher:
    """Matches queries to appropriate responses using semantic similarity"""
    
    def __init__(self, response_bank_path: Optional[Path] = None):
        self.response_bank_path = response_bank_path or self._get_default_response_path()
        self.responses = self._load_response_bank()
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        # Pre-compute response vectors
        self._prepare_response_vectors()
    
    def _get_default_response_path(self) -> Path:
        """Get default path for response bank"""
        return Path(__file__).parent.parent / "data" / "response_bank.json"
    
    def _load_response_bank(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load response bank from JSON file"""
        if not self.response_bank_path.exists():
            logger.warning(f"Response bank not found at {self.response_bank_path}, using defaults")
            return self._get_default_responses()
        
        try:
            with open(self.response_bank_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load response bank: {e}")
            return self._get_default_responses()
    
    def _get_default_responses(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get default responses if bank not available"""
        return {
            "tool_decisions": [
                {
                    "context": "tool causing more problems than solving",
                    "response": "When a tool increases complexity without clear benefits, it's time to reassess. "
                               "Calculate the ROI: if you've spent more time fighting the tool than it would take "
                               "to build a simpler solution, abandon it. I've killed many 'smart' integrations "
                               "that became maintenance nightmares. Document what didn't work to help others.",
                    "key_phrases": ["increased warnings", "more problems", "not working", "abandon"]
                },
                {
                    "context": "evaluating tool continuation",
                    "response": "Give a tool 3 iterations to prove value: initial setup, one major integration, "
                               "and one debugging session. If it's still fighting you after that, the relationship "
                               "won't improve. Trust your instincts - developer ergonomics matter more than features.",
                    "key_phrases": ["should continue", "worth it", "keep trying", "give up"]
                }
            ],
            "debt_management": [
                {
                    "context": "deciding on refactoring priority",
                    "response": "Refactor when the cost of change exceeds the cost of cleanup. Track how many "
                               "times you've worked around the same issue. After the third workaround, refactoring "
                               "becomes cheaper than continued patches. Focus on code that changes frequently first.",
                    "key_phrases": ["refactor", "technical debt", "cleanup", "worth fixing"]
                }
            ],
            "architecture_decisions": [
                {
                    "context": "build vs buy decision",
                    "response": "Build when it's your core differentiator. Buy when it's infrastructure. "
                               "The real cost isn't development - it's maintenance. That authentication system "
                               "will need security updates forever. Use the 6-month test: will you still want "
                               "to maintain this in 6 months?",
                    "key_phrases": ["build or buy", "custom vs third party", "make or buy"]
                }
            ],
            "debugging_strategies": [
                {
                    "context": "systematic debugging approach",
                    "response": "Start with binary search: cut the problem space in half repeatedly. "
                               "Disable half the features - does it still break? Then the bug's in the active half. "
                               "Most bugs hide where data transforms: API boundaries, serialization, type conversions. "
                               "Check those first.",
                    "key_phrases": ["debug", "find bug", "troubleshoot", "not working"]
                }
            ],
            "implementation_approaches": [
                {
                    "context": "shipping features quickly",
                    "response": "Ship the walking skeleton first: the simplest end-to-end flow that provides value. "
                               "No abstractions, no optimization, just working code. You'll learn more from 10 users "
                               "on a basic version than 6 months of perfect architecture. Real usage reveals real requirements.",
                    "key_phrases": ["ship quickly", "mvp", "implement fast", "deliver soon"]
                }
            ]
        }
    
    def _prepare_response_vectors(self):
        """Pre-compute TF-IDF vectors for all responses"""
        self.response_texts = []
        self.response_mappings = []
        
        for category, responses in self.responses.items():
            for response_data in responses:
                # Combine context and key phrases for vectorization
                text = f"{response_data.get('context', '')} {' '.join(response_data.get('key_phrases', []))}"
                self.response_texts.append(text)
                self.response_mappings.append((category, response_data))
        
        if self.response_texts:
            self.response_vectors = self.vectorizer.fit_transform(self.response_texts)
        else:
            self.response_vectors = None
    
    def find_best_response(
        self, 
        query: str, 
        intent: QueryIntent,
        min_similarity: float = 0.2
    ) -> Tuple[str, float]:
        """Find the best matching response for a query"""
        
        # First try to get responses from the suggested category
        category_responses = self.responses.get(intent.suggested_response_category, [])
        
        if not category_responses and self.response_vectors is None:
            return self._get_fallback_response(intent), 0.5
        
        # Use semantic similarity to find best match
        if self.response_vectors is not None:
            try:
                # Include intent context in query vector
                enhanced_query = f"{query} {intent.intent_type} {' '.join(intent.key_entities)}"
                query_vector = self.vectorizer.transform([enhanced_query])
                similarities = cosine_similarity(query_vector, self.response_vectors).flatten()
                
                # Filter by category if specified
                if intent.suggested_response_category:
                    category_indices = [
                        i for i, (cat, _) in enumerate(self.response_mappings)
                        if cat == intent.suggested_response_category
                    ]
                    if category_indices:
                        # Boost similarity scores for suggested category
                        for idx in category_indices:
                            similarities[idx] *= 1.5
                
                # Get best match
                best_idx = np.argmax(similarities)
                if similarities[best_idx] >= min_similarity:
                    _, response_data = self.response_mappings[best_idx]
                    return response_data['response'], float(similarities[best_idx])
                    
            except Exception as e:
                logger.warning(f"Semantic response matching failed: {e}")
        
        # Fallback to category-based selection
        if category_responses:
            # Simple keyword matching as fallback
            query_lower = query.lower()
            best_response = category_responses[0]
            best_score = 0.0
            
            for response_data in category_responses:
                score = sum(
                    1 for phrase in response_data.get('key_phrases', [])
                    if phrase.lower() in query_lower
                )
                if score > best_score:
                    best_score = score
                    best_response = response_data
            
            return best_response['response'], min(best_score * 0.3, 0.9)
        
        return self._get_fallback_response(intent), 0.3
    
    def _get_fallback_response(self, intent: QueryIntent) -> str:
        """Get a fallback response based on intent type"""
        fallbacks = {
            "tool_evaluation": "Consider the time invested vs. value delivered. If the tool isn't solving your core problem after reasonable effort, it's okay to move on.",
            "technical_debt": "Address technical debt when it blocks feature development or causes repeated issues. Track the pain points.",
            "decision": "List your constraints, then pick the solution that best fits today's needs. You can always change later.",
            "debugging": "Isolate the problem systematically. Start with the most recent changes and work backwards.",
            "implementation": "Start with the simplest working version. Complexity can come later if needed.",
            "integration": "Check for official SDKs first. Custom implementations should be a last resort.",
            "architecture": "Choose patterns that match your team's expertise and your problem's complexity.",
            "general": "Focus on solving the immediate problem. Perfect is the enemy of good."
        }
        return fallbacks.get(intent.intent_type, fallbacks["general"])


class SemanticEngine:
    """Main semantic engine combining intent classification and response matching"""
    
    def __init__(self, response_bank_path: Optional[Path] = None):
        self.intent_classifier = QueryIntentClassifier()
        self.response_matcher = SemanticResponseMatcher(response_bank_path)
    
    def process_query(
        self, 
        query: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a query and return semantic understanding with appropriate response"""
        
        # Classify intent
        intent = self.intent_classifier.classify_intent(query, context)
        
        # Find best response
        response, confidence = self.response_matcher.find_best_response(query, intent)
        
        # Ensure no template substitution patterns remain
        response = self._clean_response(response, intent)
        
        return {
            "intent": {
                "type": intent.intent_type,
                "confidence": intent.confidence,
                "entities": intent.key_entities,
                "signals": intent.context_signals
            },
            "response": response,
            "response_confidence": confidence,
            "success": True
        }
    
    def _clean_response(self, response: str, intent: QueryIntent) -> str:
        """Clean response of any template patterns"""
        # Replace any remaining template patterns with specific values
        if intent.key_entities:
            # Use actual entities instead of generic placeholders
            response = response.replace("{technology}", intent.key_entities[0] if intent.key_entities else "the tool")
            response = response.replace("{framework}", intent.key_entities[1] if len(intent.key_entities) > 1 else "the framework")
            response = response.replace("{tech}", intent.key_entities[0] if intent.key_entities else "this technology")
        
        # Remove any remaining curly brace patterns
        import re
        response = re.sub(r'\{[^}]+\}', '', response)
        
        return response.strip()