"""
Tests for Semantic Intent Classification Engine

Validates that the semantic engine correctly classifies intents and
provides contextually appropriate responses without template substitution.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vibe_check.tools.semantic_engine import (
    QueryIntentClassifier,
    SemanticResponseMatcher,
    SemanticEngine,
    QueryIntent
)


class TestQueryIntentClassifier:
    """Test intent classification accuracy"""
    
    def setup_method(self):
        """Setup test instance"""
        self.classifier = QueryIntentClassifier()
    
    def test_tool_evaluation_intent(self):
        """Test recognition of tool evaluation queries"""
        queries = [
            "Should I abandon ts-migrate that increased warnings?",
            "This tool is causing more problems than solving",
            "Is it worth continuing with this library?",
            "The migration tool made things worse"
        ]
        
        for query in queries:
            intent = self.classifier.classify_intent(query)
            assert intent.intent_type == "tool_evaluation", f"Failed for: {query}"
            assert intent.confidence > 0.5
            assert "tool_decisions" in intent.suggested_response_category
    
    def test_technical_debt_intent(self):
        """Test recognition of technical debt queries"""
        queries = [
            "Should I refactor this legacy code?",
            "Is this technical debt worth addressing?",
            "We have three auth systems, should we consolidate?"
        ]
        
        for query in queries:
            intent = self.classifier.classify_intent(query)
            assert intent.intent_type == "technical_debt", f"Failed for: {query}"
            assert intent.confidence > 0.4
    
    def test_debugging_intent(self):
        """Test recognition of debugging queries"""
        queries = [
            "How to debug this timeout issue?",
            "Finding the root cause of the crash",
            "Why is this API failing?"
        ]
        
        for query in queries:
            intent = self.classifier.classify_intent(query)
            assert intent.intent_type == "debugging", f"Failed for: {query}"
            assert intent.confidence > 0.4
    
    def test_implementation_intent(self):
        """Test recognition of implementation queries"""
        queries = [
            "How to ship this feature quickly?",
            "Best way to implement authentication",
            "MVP approach for this feature"
        ]
        
        for query in queries:
            intent = self.classifier.classify_intent(query)
            assert intent.intent_type == "implementation", f"Failed for: {query}"
            assert intent.confidence > 0.4
    
    def test_entity_extraction(self):
        """Test extraction of key entities from queries"""
        query = "Should I abandon ts-migrate tool that's causing TypeScript warnings?"
        intent = self.classifier.classify_intent(query)
        
        # Should extract tool names and technologies
        assert any("ts-migrate" in entity or "TypeScript" in entity for entity in intent.key_entities)
    
    def test_context_signals(self):
        """Test extraction of context signals"""
        query = "This tool is failing urgently and I've tried everything"
        intent = self.classifier.classify_intent(query)
        
        assert "negative_experience" in intent.context_signals
        assert "prior_attempts" in intent.context_signals


class TestSemanticResponseMatcher:
    """Test response matching without template substitution"""
    
    def setup_method(self):
        """Setup test instance"""
        # Use test response bank if available, otherwise defaults
        self.matcher = SemanticResponseMatcher()
    
    def test_no_template_substitution(self):
        """Ensure responses don't contain template patterns"""
        intent = QueryIntent(
            intent_type="tool_evaluation",
            confidence=0.8,
            key_entities=["ts-migrate", "TypeScript"],
            context_signals=["negative_experience"],
            suggested_response_category="tool_decisions"
        )
        
        query = "Should I abandon ts-migrate that increased warnings?"
        response, confidence = self.matcher.find_best_response(query, intent)
        
        # Check no template patterns remain
        assert "{technology}" not in response
        assert "{framework}" not in response
        assert "{tech}" not in response
        assert "{{" not in response
        
        # Check response is contextually relevant
        assert len(response) > 50  # Not a placeholder
        assert confidence > 0.0
    
    def test_tool_decision_responses(self):
        """Test responses for tool evaluation queries"""
        intent = QueryIntent(
            intent_type="tool_evaluation",
            confidence=0.9,
            key_entities=["ts-migrate"],
            context_signals=["negative_experience"],
            suggested_response_category="tool_decisions"
        )
        
        query = "ts-migrate added 500 warnings instead of fixing them"
        response, confidence = self.matcher.find_best_response(query, intent)
        
        # Should mention ROI, abandonment, or migration strategies
        relevant_terms = ["ROI", "abandon", "migration", "warnings", "manual"]
        assert any(term.lower() in response.lower() for term in relevant_terms)
    
    def test_fallback_responses(self):
        """Test fallback responses for unmatched queries"""
        intent = QueryIntent(
            intent_type="unknown_type",
            confidence=0.2,
            key_entities=[],
            context_signals=[],
            suggested_response_category="general_advice"
        )
        
        query = "random query with no clear intent"
        response, confidence = self.matcher.find_best_response(query, intent)
        
        # Should still return a valid response
        assert len(response) > 20
        assert confidence >= 0.0


class TestSemanticEngine:
    """Test the complete semantic engine integration"""
    
    def setup_method(self):
        """Setup test instance"""
        self.engine = SemanticEngine()
    
    def test_process_tool_evaluation_query(self):
        """Test processing a real tool evaluation query"""
        query = "Should I abandon ts-migrate that increased warnings from 0 to 500?"
        result = self.engine.process_query(query)
        
        assert result['success']
        assert result['intent']['type'] in ["tool_evaluation", "decision"]
        assert result['response']
        assert "{" not in result['response']  # No templates
        
        # Response should be relevant to tool abandonment
        response_lower = result['response'].lower()
        assert any(term in response_lower for term in ["abandon", "roi", "time", "migration"])
    
    def test_process_with_context(self):
        """Test processing with additional context"""
        query = "Should I continue with this approach?"
        context = "We're using ts-migrate for TypeScript migration but it's adding warnings"
        
        result = self.engine.process_query(query, context)
        
        assert result['success']
        assert result['intent']['type'] in ["tool_evaluation", "decision"]
        assert len(result['response']) > 50
    
    def test_clean_response_no_templates(self):
        """Ensure cleaned responses have no template artifacts"""
        queries = [
            "How to integrate with Stripe API?",
            "Should I use React or Vue?",
            "Debug this MongoDB connection issue",
            "Refactor this legacy Python code"
        ]
        
        for query in queries:
            result = self.engine.process_query(query)
            response = result['response']
            
            # Check for common template patterns
            assert "{technology}" not in response
            assert "{framework}" not in response
            assert "{tech}" not in response
            assert not any(c in response for c in ["{", "}"])
    
    def test_confidence_scores(self):
        """Test that confidence scores are reasonable"""
        # Clear intent should have high confidence
        clear_query = "Should I abandon this failing tool?"
        result = self.engine.process_query(clear_query)
        assert result['intent']['confidence'] > 0.6
        
        # Vague query should have lower confidence
        vague_query = "What about this thing?"
        result = self.engine.process_query(vague_query)
        assert result['intent']['confidence'] < 0.5


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def setup_method(self):
        """Setup test instance"""
        self.engine = SemanticEngine()
    
    def test_ts_migrate_scenario(self):
        """Test the specific ts-migrate scenario from Issue #185"""
        query = "Should I abandon ts-migrate that increased warnings?"
        result = self.engine.process_query(query)
        
        # Should recognize this as tool evaluation
        assert result['intent']['type'] == "tool_evaluation"
        
        # Response should address tool ROI and abandonment
        response = result['response'].lower()
        assert "abandon" in response or "roi" in response or "migration" in response
        
        # Should not have generic templates
        assert "ship context + typescript this week" not in response.lower()
        assert "{technology}" not in result['response']
    
    def test_multiple_tool_comparison(self):
        """Test comparing multiple tools/frameworks"""
        query = "Should I use React or Vue for this project?"
        result = self.engine.process_query(query)
        
        assert result['intent']['type'] in ["decision", "architecture"]
        assert result['response']
        
        # Should provide decision framework, not templates
        response = result['response'].lower()
        assert any(term in response for term in ["choose", "team", "productivity", "framework"])


@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks for semantic engine"""
    
    def test_classification_speed(self, benchmark):
        """Benchmark intent classification speed"""
        classifier = QueryIntentClassifier()
        query = "Should I abandon this tool that's causing problems?"
        
        # Should complete in under 100ms
        result = benchmark(classifier.classify_intent, query)
        assert result.intent_type is not None
    
    def test_response_matching_speed(self, benchmark):
        """Benchmark response matching speed"""
        engine = SemanticEngine()
        query = "How to debug this API timeout?"
        
        # Should complete in under 200ms
        result = benchmark(engine.process_query, query)
        assert result['success']


if __name__ == "__main__":
    # Run specific test for development
    test = TestSemanticEngine()
    test.setup_method()
    test.test_process_tool_evaluation_query()
    print("✅ Semantic engine test passed!")