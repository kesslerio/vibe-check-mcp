"""
Unit tests for MCP Sampling integration in vibe_check_mentor
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, Any

from vibe_check.mentor.mcp_sampling import (
    MCPSamplingClient,
    SamplingConfig,
    ResponseQuality,
    PromptBuilder,
    ResponseCache
)
from vibe_check.mentor.hybrid_router import (
    HybridRouter,
    RouteDecision,
    RouteOptimizer,
    ConfidenceScorer
)


class TestPromptBuilder:
    """Test the prompt building functionality"""
    
    def test_build_prompt_architecture_decision(self):
        """Test building prompt for architecture decisions"""
        prompt = PromptBuilder.build_prompt(
            intent="architecture_decision",
            query="Should I use microservices or monolith?",
            context={
                "technologies": ["python", "django"],
                "patterns": ["monolith_vs_microservices"]
            },
            workspace_data=None
        )
        
        assert "architecture_decision" in prompt.lower() or "architecture" in prompt.lower()
        assert "microservices or monolith" in prompt
        assert "python" in prompt
        assert "django" in prompt
    
    def test_build_prompt_with_workspace_data(self):
        """Test building prompt with workspace context"""
        workspace_data = {
            "files": ["app.py", "models.py"],
            "language": "python",
            "frameworks": ["django", "rest_framework"],
            "imports": ["django.db", "rest_framework.views"]
        }
        
        prompt = PromptBuilder.build_prompt(
            intent="implementation_guide",
            query="How to add authentication?",
            context={"technologies": ["django"]},
            workspace_data=workspace_data
        )
        
        assert "app.py" in prompt
        assert "django" in prompt
        assert "rest_framework" in prompt
    
    def test_map_intent_to_template(self):
        """Test intent to template mapping"""
        # Architecture intents
        assert PromptBuilder._map_intent_to_template("architecture") == "architecture_decision"
        assert PromptBuilder._map_intent_to_template("design pattern") == "architecture_decision"
        
        # Review intents
        assert PromptBuilder._map_intent_to_template("code review") == "code_review"
        assert PromptBuilder._map_intent_to_template("feedback") == "code_review"
        
        # Implementation intents
        assert PromptBuilder._map_intent_to_template("implement feature") == "implementation_guide"
        assert PromptBuilder._map_intent_to_template("build api") == "implementation_guide"
        
        # Debugging intents
        assert PromptBuilder._map_intent_to_template("debug error") == "debugging_help"
        assert PromptBuilder._map_intent_to_template("fix issue") == "debugging_help"
        
        # General fallback
        assert PromptBuilder._map_intent_to_template("random query") == "general_advice"


class TestResponseCache:
    """Test the response caching functionality"""
    
    def test_cache_basic_operations(self):
        """Test basic cache put and get operations"""
        cache = ResponseCache(max_size=10)
        
        response = {
            "content": "Test response",
            "confidence": 0.9
        }
        
        # Put item in cache
        cache.put(
            intent="test_intent",
            query="test query",
            context={"tech": ["python"]},
            response=response
        )
        
        # Get item from cache
        cached = cache.get(
            intent="test_intent",
            query="test query",
            context={"tech": ["python"]}
        )
        
        assert cached is not None
        assert cached["content"] == "Test response"
        assert cached["confidence"] == 0.9
        assert cache.hits == 1
        assert cache.misses == 0
    
    def test_cache_miss(self):
        """Test cache miss scenario"""
        cache = ResponseCache(max_size=10)
        
        result = cache.get(
            intent="nonexistent",
            query="not in cache",
            context={}
        )
        
        assert result is None
        assert cache.hits == 0
        assert cache.misses == 1
    
    def test_cache_max_size(self):
        """Test cache eviction when max size is reached"""
        cache = ResponseCache(max_size=2)
        
        # Add items up to max size
        cache.put("intent1", "query1", {}, {"content": "response1"})
        cache.put("intent2", "query2", {}, {"content": "response2"})
        
        assert len(cache.cache) == 2
        
        # Add one more item - should evict oldest
        cache.put("intent3", "query3", {}, {"content": "response3"})
        
        assert len(cache.cache) == 2
        # First item should be evicted
        assert cache.get("intent1", "query1", {}) is None
        # Second and third items should still be there
        assert cache.get("intent2", "query2", {}) is not None
        assert cache.get("intent3", "query3", {}) is not None
    
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = ResponseCache(max_size=10)
        
        # Generate some activity
        cache.put("intent", "query", {}, {"content": "response"})
        cache.get("intent", "query", {})  # Hit
        cache.get("other", "query", {})   # Miss
        cache.get("intent", "query", {})  # Hit
        
        stats = cache.get_stats()
        
        assert stats["size"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == "66.7%"


class TestConfidenceScorer:
    """Test confidence scoring for routing decisions"""
    
    def test_high_confidence_patterns(self):
        """Test that common patterns get high confidence"""
        confidence, reasoning = ConfidenceScorer.calculate_confidence(
            query="Should I use React or Vue?",
            intent="decision",
            context={"technologies": ["javascript"]},
            has_workspace_context=False
        )
        
        assert confidence > 0.5  # Should have decent confidence
        assert "Common pattern" in reasoning or "Simple" in reasoning
    
    def test_low_confidence_patterns(self):
        """Test that novel scenarios get low confidence"""
        confidence, reasoning = ConfidenceScorer.calculate_confidence(
            query="How to integrate X with Y and Z in my custom implementation?",
            intent="integration",
            context={"technologies": ["x", "y", "z", "custom", "proprietary"]},
            has_workspace_context=True
        )
        
        assert confidence < 0.5  # Should have low confidence
        assert "Novel scenario" in reasoning or "workspace context" in reasoning.lower()
    
    def test_workspace_context_reduces_confidence(self):
        """Test that workspace context reduces confidence"""
        # Without workspace context
        conf_without, _ = ConfidenceScorer.calculate_confidence(
            query="How to implement auth?",
            intent="implementation",
            context={"technologies": ["django"]},
            has_workspace_context=False
        )
        
        # With workspace context
        conf_with, _ = ConfidenceScorer.calculate_confidence(
            query="How to implement auth?",
            intent="implementation",
            context={"technologies": ["django"]},
            has_workspace_context=True
        )
        
        assert conf_with < conf_without


class TestHybridRouter:
    """Test the hybrid routing functionality"""
    
    def test_route_decision_static(self):
        """Test routing to static responses for high confidence"""
        router = HybridRouter(confidence_threshold=0.7)
        
        metrics = router.decide_route(
            query="Should I use REST or GraphQL?",
            intent="decision",
            context={"technologies": []},
            has_workspace_context=False,
            has_static_response=True
        )
        
        # Common pattern should route to static
        assert metrics.decision in [RouteDecision.STATIC, RouteDecision.HYBRID]
        assert metrics.confidence >= 0.4  # Should have reasonable confidence
    
    def test_route_decision_dynamic(self):
        """Test routing to dynamic generation for low confidence"""
        router = HybridRouter(confidence_threshold=0.7)
        
        metrics = router.decide_route(
            query="How to integrate our custom ESLint hybrid automation strategy with the new v3.2.1 API?",
            intent="integration",
            context={"technologies": ["eslint", "custom", "api", "v3.2.1"]},
            has_workspace_context=True,
            has_static_response=True
        )
        
        # Novel, specific scenario should route to dynamic
        assert metrics.decision == RouteDecision.DYNAMIC
        assert metrics.confidence < 0.7
    
    def test_force_dynamic(self):
        """Test forcing dynamic generation"""
        router = HybridRouter()
        
        metrics = router.decide_route(
            query="Simple query",
            intent="general",
            context={},
            has_workspace_context=False,
            has_static_response=True,
            force_dynamic=True
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
        assert "Forced dynamic" in metrics.reasoning
    
    def test_no_static_available(self):
        """Test routing when no static response is available"""
        router = HybridRouter()
        
        metrics = router.decide_route(
            query="Any query",
            intent="any",
            context={},
            has_workspace_context=False,
            has_static_response=False  # No static response
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
    
    def test_should_fallback(self):
        """Test fallback logic"""
        router = HybridRouter()
        
        metrics = router.decide_route(
            query="test",
            intent="test",
            context={},
            has_workspace_context=False,
            has_static_response=True
        )
        
        # Should fallback on failure
        assert router.should_fallback(metrics, generation_failed=True, latency_ms=100)
        
        # Should fallback on high latency
        assert router.should_fallback(metrics, generation_failed=False, latency_ms=6000)
        
        # Should not fallback on success with reasonable latency
        assert not router.should_fallback(metrics, generation_failed=False, latency_ms=2000)
    
    def test_router_stats(self):
        """Test router statistics tracking"""
        router = HybridRouter()
        
        # Make some routing decisions
        router.decide_route("query1", "intent1", {}, False, True)
        router.decide_route("query2", "intent2", {}, True, True, force_dynamic=True)
        router.decide_route("query3", "intent3", {}, False, False)
        
        stats = router.get_stats()
        
        assert stats["total_requests"] == 3
        assert stats["dynamic_routes"] >= 2  # At least 2 dynamic (forced + no static)
        assert "dynamic_percentage" in stats
        assert "cache_hit_rate" in stats


class TestRouteOptimizer:
    """Test route optimization functionality"""
    
    def test_record_outcome(self):
        """Test recording routing outcomes"""
        optimizer = RouteOptimizer()
        
        optimizer.record_outcome(
            query="Test query",
            decision=RouteDecision.STATIC,
            latency_ms=50,
            success=True
        )
        
        assert len(optimizer.history) == 1
        assert optimizer.history[0]["decision"] == "static"
        assert optimizer.history[0]["success"] is True
    
    def test_pattern_recommendation(self):
        """Test pattern-based recommendations"""
        optimizer = RouteOptimizer()
        
        # Record multiple outcomes for a pattern
        for _ in range(5):
            optimizer.record_outcome(
                query="Should I use X",
                decision=RouteDecision.STATIC,
                latency_ms=50,
                success=True
            )
        
        for _ in range(2):
            optimizer.record_outcome(
                query="Should I use Y",
                decision=RouteDecision.DYNAMIC,
                latency_ms=2000,
                success=False
            )
        
        # Should recommend static for the successful pattern
        recommendation = optimizer.get_pattern_recommendation("Should I use Z")
        assert recommendation == RouteDecision.STATIC
        
        # No recommendation for unknown pattern
        recommendation = optimizer.get_pattern_recommendation("Completely different query")
        assert recommendation is None
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        optimizer = RouteOptimizer()
        
        # Record some outcomes
        optimizer.record_outcome("query1", RouteDecision.STATIC, 50, True)
        optimizer.record_outcome("query2", RouteDecision.DYNAMIC, 2000, True)
        optimizer.record_outcome("query3", RouteDecision.STATIC, 45, False)
        
        summary = optimizer.get_performance_summary()
        
        assert summary["total_requests"] == 3
        assert summary["static_requests"] == 2
        assert summary["dynamic_requests"] == 1
        assert "success_rate" in summary
        assert "avg_latency_ms" in summary


@pytest.mark.asyncio
class TestMCPSamplingClient:
    """Test the MCP sampling client"""
    
    async def test_sampling_config_to_params(self):
        """Test converting config to MCP parameters"""
        config = SamplingConfig(
            temperature=0.8,
            max_tokens=500,
            model_preferences=["claude-3", "gpt-4"],
            quality=ResponseQuality.HIGH
        )
        
        params = config.to_params()
        
        assert params["temperature"] == 0.8
        assert params["maxTokens"] == 500
        assert params["modelPreferences"]["hints"] == ["claude-3", "gpt-4"]
    
    @patch('vibe_check.mentor.mcp_sampling.logger')
    async def test_generate_dynamic_response_error_handling(self, mock_logger):
        """Test error handling in dynamic response generation"""
        client = MCPSamplingClient()
        
        # Mock context that raises an error
        mock_ctx = AsyncMock()
        mock_ctx.sample.side_effect = Exception("Sampling failed")
        
        result = await client.generate_dynamic_response(
            intent="test",
            query="test query",
            context={},
            workspace_data=None,
            ctx=mock_ctx
        )
        
        assert result is None
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])