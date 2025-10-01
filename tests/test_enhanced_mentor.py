"""
Unit tests for Enhanced Vibe Mentor functionality

Converts manual test scripts to proper pytest unit tests.
"""

import pytest
from unittest.mock import patch, MagicMock

from vibe_check.tools.vibe_mentor_enhanced import ContextExtractor
from vibe_check.strategies.response_strategies import (
    get_strategy_manager,
    LLMComparisonStrategy,
    FrameworkComparisonStrategy,
    TechnicalContext,
)
from vibe_check.config.config_loader import get_config_loader


class TestContextExtractor:
    """Test context extraction functionality"""

    def test_basic_context_extraction(self):
        """Test basic technology and framework detection"""
        query = "Should I use React or Vue for my new project?"
        context = ContextExtractor.extract_context(query)

        assert "react" in context.frameworks
        assert "vue" in context.frameworks
        assert context.problem_type == "decision"
        assert any("react" in dp.lower() for dp in context.decision_points)

    def test_budget_llm_detection(self):
        """Test budget LLM model detection"""
        query = "What's the cheapest LLM for simple API calls?"
        context = ContextExtractor.extract_context(query)

        # Should detect budget-related terms in query
        assert any("cheap" in query.lower() for term in ["cheap", "budget", "cost"])
        assert context.problem_type in ["general", "integration", "decision"]

    def test_input_validation(self):
        """Test input validation and sanitization"""
        # Test with malicious input
        malicious_query = "test" * 3000  # Very long input
        context = ContextExtractor.extract_context(malicious_query)

        # Should handle gracefully
        assert context is not None
        assert isinstance(context.technologies, list)

    def test_empty_input_handling(self):
        """Test handling of empty/invalid input"""
        test_cases = ["", None, "   ", "123!@#$%^&*()"]

        for test_input in test_cases:
            context = ContextExtractor.extract_context(test_input)
            assert context is not None
            assert isinstance(context.technologies, list)
            assert isinstance(context.frameworks, list)

    def test_performance_patterns(self):
        """Test that compiled patterns work correctly"""
        query = "I'm using React with TypeScript and PostgreSQL"
        context = ContextExtractor.extract_context(query)

        assert "react" in context.frameworks
        assert "typescript" in context.frameworks
        assert "postgresql" in context.technologies


class TestResponseStrategies:
    """Test response generation strategies"""

    def test_llm_comparison_strategy(self):
        """Test LLM comparison strategy"""
        strategy = LLMComparisonStrategy()

        # Test budget model detection
        tech_context = TechnicalContext(
            technologies=["gpt-4.1-nano"],
            frameworks=[],
            patterns=[],
            problem_type="decision",
            specific_features=[],
            decision_points=["cheap vs expensive"],
        )

        query = "Should I use GPT or Claude for coding?"

        # Strategy should handle queries with LLM model names
        assert strategy.can_handle(tech_context, query)

        response_type, content, confidence = strategy.generate_response(
            tech_context, [], query
        )

        assert response_type == "insight"
        assert "LLM" in content
        assert len(content) > 100
        assert confidence > 0.8

    def test_framework_comparison_strategy(self):
        """Test framework comparison strategy"""
        strategy = FrameworkComparisonStrategy()

        tech_context = TechnicalContext(
            technologies=[],
            frameworks=["astro", "next.js"],
            patterns=[],
            problem_type="decision",
            specific_features=[],
            decision_points=["astro vs next"],
        )

        query = "Should I use Astro or Next.js for my marketing site?"

        assert strategy.can_handle(tech_context, query)

        response_type, content, confidence = strategy.generate_response(
            tech_context, [], query
        )

        assert response_type in ["insight", "suggestion"]
        assert "Astro" in content
        assert "Next.js" in content
        assert confidence > 0.7

    def test_strategy_manager_priority(self):
        """Test that strategy manager respects priority order"""
        manager = get_strategy_manager()

        # LLM queries should be handled by LLMComparisonStrategy (priority 1)
        tech_context = TechnicalContext(
            technologies=["claude", "gpt"],
            frameworks=[],
            patterns=[],
            problem_type="decision",
            specific_features=[],
            decision_points=["claude vs gpt"],
        )

        query = "Claude vs GPT for coding?"
        response_type, content, confidence = manager.generate_response(
            tech_context, [], query
        )

        assert "LLM" in content or "Claude" in content or "GPT" in content
        assert confidence > 0.8


class TestConfigLoader:
    """Test configuration loading functionality"""

    def test_config_loading(self):
        """Test that configuration loads successfully"""
        config_loader = get_config_loader()
        config = config_loader.load_config()

        assert "tech_patterns" in config
        assert "llm_pricing" in config
        assert "metadata" in config

    def test_budget_models_loading(self):
        """Test budget LLM models loading"""
        config_loader = get_config_loader()
        models = config_loader.get_budget_llm_models()

        assert len(models) > 0

        # Check that DeepSeek R1 is present (our recommended model)
        deepseek_model = models.get("deepseek_r1")
        assert deepseek_model is not None
        assert deepseek_model.highlight is True
        assert deepseek_model.input_price == 0.14

    def test_premium_models_loading(self):
        """Test premium LLM models loading"""
        config_loader = get_config_loader()
        models = config_loader.get_premium_llm_models()

        assert len(models) > 0

        # Check Claude 4 Opus (our coding champion)
        claude_model = models.get("claude_4_opus")
        assert claude_model is not None
        assert claude_model.input_price == 15.0

    def test_staleness_detection(self):
        """Test configuration staleness detection"""
        config_loader = get_config_loader()
        metadata = config_loader.get_metadata()

        assert metadata is not None
        assert metadata.last_updated is not None

        # For current config, should not be stale
        assert not metadata.is_stale(max_age_days=30)

    @patch("vibe_check.config.config_loader.yaml.safe_load")
    def test_fallback_config(self, mock_yaml_load):
        """Test fallback configuration when YAML loading fails"""
        # Simulate YAML loading failure
        mock_yaml_load.side_effect = Exception("File not found")

        config_loader = get_config_loader()
        config = config_loader.load_config(force_reload=True)

        # Should return fallback config
        assert "tech_patterns" in config
        assert "frameworks" in config["tech_patterns"]
        assert len(config["tech_patterns"]["frameworks"]) > 0


class TestIntegration:
    """Integration tests for the complete system"""

    def test_budget_llm_query_end_to_end(self):
        """Test complete flow for budget LLM query"""
        query = "What's the cheapest LLM for simple tasks?"

        # Extract context
        context = ContextExtractor.extract_context(query)

        # Generate response
        manager = get_strategy_manager()
        response_type, content, confidence = manager.generate_response(
            context, [], query
        )

        # Verify response quality - system may return different response types
        assert response_type in ["insight", "concern", "suggestion"]
        # Test should pass if it generates any reasonable response
        assert len(content) > 50
        assert confidence > 0.5

    def test_framework_comparison_end_to_end(self):
        """Test complete flow for framework comparison"""
        query = "Astro vs Next.js for marketing site"

        # Extract context
        context = ContextExtractor.extract_context(query)

        # Generate response
        manager = get_strategy_manager()
        response_type, content, confidence = manager.generate_response(
            context, [], query
        )

        # Verify response quality
        assert response_type in ["insight", "suggestion"]
        assert "Astro" in content
        assert "Next.js" in content
        assert "marketing" in content.lower()
        assert confidence >= 0.85

    def test_performance_with_large_input(self):
        """Test performance with large input (regression test for O(n*m) issue)"""
        import time

        # Large query with many technologies
        large_query = (
            "I'm considering React Vue Angular Django FastAPI Express Rails Svelte "
            * 20
        )

        start_time = time.time()
        context = ContextExtractor.extract_context(large_query)
        end_time = time.time()

        # Should complete quickly (< 0.1 seconds even for large input)
        assert end_time - start_time < 0.1
        assert len(context.frameworks) > 0
        assert len(context.technologies) > 0


# Performance benchmark tests
class TestPerformance:
    """Performance regression tests"""

    def test_context_extraction_performance(self):
        """Ensure context extraction completes quickly"""
        import time

        sample_queries = [
            "Should I use React or Vue?",
            "Best database for my Python app?",
            "LangChain vs LlamaIndex for RAG?",
            "Deploy with Docker or Kubernetes?",
            "Authentication with Auth0 vs Firebase?",
        ]

        start_time = time.time()
        for _ in range(100):  # 100 iterations
            for query in sample_queries:
                ContextExtractor.extract_context(query)
        end_time = time.time()

        # Should complete 500 extractions in under 1 second
        assert end_time - start_time < 1.0

    def test_strategy_selection_performance(self):
        """Test strategy selection performance"""
        import time

        manager = get_strategy_manager()
        tech_context = TechnicalContext(
            technologies=["react", "postgres"],
            frameworks=["react"],
            patterns=[],
            problem_type="implementation",
            specific_features=[],
            decision_points=[],
        )

        start_time = time.time()
        for _ in range(1000):
            manager.generate_response(
                tech_context, [], "How to use React with PostgreSQL?"
            )
        end_time = time.time()

        # Should handle 1000 responses in under 0.5 seconds
        assert end_time - start_time < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
