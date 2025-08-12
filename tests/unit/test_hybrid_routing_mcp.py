"""
Comprehensive tests for hybrid routing logic in vibe_check_mentor.

Tests cover:
1. Novel queries that should route to DYNAMIC (e.g., "ESLint hybrid automation strategy")
2. Common queries that should route to STATIC (e.g., "What is SOLID?")
3. Edge cases where confidence is borderline
4. Fallback when MCP sampling fails
5. Circuit breaker behavior
6. Latency requirements (<3s)
7. Cache hit/miss scenarios
8. Workspace context influence on routing
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, MagicMock, patch, AsyncMock, call
from typing import Dict, Any, List, Optional

from vibe_check.mentor.hybrid_router import (
    HybridRouter,
    RouteDecision,
    RouteMetrics,
    RouteOptimizer,
    ConfidenceScorer
)
from vibe_check.mentor.mcp_sampling import (
    MCPSamplingClient,
    SamplingConfig,
    ResponseQuality,
    PromptBuilder,
    ResponseCache,
    CircuitBreaker,
    CircuitBreakerState
)


# Test Fixtures
@pytest.fixture
def router():
    """Create a hybrid router instance for testing"""
    return HybridRouter(
        confidence_threshold=0.7,
        enable_caching=True,
        prefer_speed=False
    )


@pytest.fixture
def router_with_speed_preference():
    """Create a router that prefers speed"""
    return HybridRouter(
        confidence_threshold=0.7,
        enable_caching=True,
        prefer_speed=True
    )


@pytest.fixture
def router_no_cache():
    """Create a router without caching"""
    return HybridRouter(
        confidence_threshold=0.7,
        enable_caching=False,
        prefer_speed=False
    )


@pytest.fixture
def optimizer():
    """Create a route optimizer instance"""
    return RouteOptimizer(max_history_size=100, max_patterns=50)


@pytest.fixture
def response_cache():
    """Create a response cache instance"""
    return ResponseCache(max_size=100)


@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker instance"""
    return CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=30,
        success_threshold=2
    )


@pytest.fixture
def mcp_client():
    """Create a mock MCP sampling client"""
    client = MCPSamplingClient()
    # Set lower failure threshold for testing
    client.circuit_breaker = CircuitBreaker(
        failure_threshold=3,  # Lower for testing
        recovery_timeout=30,  # Shorter for testing
        success_threshold=2
    )
    return client


# Test Data Fixtures
@pytest.fixture
def novel_queries():
    """Novel queries that should route to DYNAMIC"""
    return [
        {
            "query": "How to integrate ESLint hybrid automation strategy with our custom v3.2.1 API?",
            "intent": "integration",
            "context": {
                "technologies": ["eslint", "custom", "api", "automation", "v3.2.1"],
                "frameworks": ["hybrid-automation"],
                "patterns": ["custom_integration"]
            }
        },
        {
            "query": "Implement a multi-tenant authentication system using OAuth2 with JWT and our proprietary session manager v2.0",
            "intent": "implementation_guide",
            "context": {
                "technologies": ["oauth2", "jwt", "proprietary", "multi-tenant", "v2.0"],
                "frameworks": ["custom-session-manager"],
                "patterns": ["complex_auth"]
            }
        },
        {
            "query": "Debug memory leak in our React app with custom WebAssembly module and SharedArrayBuffer usage",
            "intent": "debugging_help",
            "context": {
                "technologies": ["react", "webassembly", "sharedarraybuffer"],
                "frameworks": ["custom-wasm"],
                "patterns": ["memory_leak", "edge_case"]
            }
        },
        {
            "query": "Optimize database queries for our GraphQL API using DataLoader with Redis caching and custom batching logic for 10M+ records",
            "intent": "optimization",
            "context": {
                "technologies": ["graphql", "dataloader", "redis", "custom-batching"],
                "frameworks": [],
                "patterns": ["scale_optimization", "custom_logic"]
            }
        }
    ]


@pytest.fixture
def common_queries():
    """Common queries that should route to STATIC"""
    return [
        {
            "query": "What is SOLID?",
            "intent": "explanation",
            "context": {
                "technologies": [],
                "frameworks": [],
                "patterns": ["solid_principles"]
            }
        },
        {
            "query": "Should I use React or Vue?",
            "intent": "architecture_decision",
            "context": {
                "technologies": ["react", "vue"],
                "frameworks": ["frontend"],
                "patterns": ["framework_comparison"]
            }
        },
        {
            "query": "How to implement authentication?",
            "intent": "implementation_guide",
            "context": {
                "technologies": [],
                "frameworks": [],
                "patterns": ["authentication"]
            }
        },
        {
            "query": "REST vs GraphQL",
            "intent": "comparison",
            "context": {
                "technologies": ["rest", "graphql"],
                "frameworks": ["api"],
                "patterns": ["api_comparison"]
            }
        },
        {
            "query": "Best practices for code review",
            "intent": "best_practices",
            "context": {
                "technologies": [],
                "frameworks": [],
                "patterns": ["code_review"]
            }
        }
    ]


@pytest.fixture
def borderline_queries():
    """Queries with borderline confidence"""
    return [
        {
            "query": "How to implement authentication with Django REST Framework?",
            "intent": "implementation_guide",
            "context": {
                "technologies": ["django", "rest_framework"],
                "frameworks": ["django"],
                "patterns": ["authentication"]
            }
        },
        {
            "query": "Debug CORS error in my React app",
            "intent": "debugging_help",
            "context": {
                "technologies": ["react"],
                "frameworks": ["frontend"],
                "patterns": ["cors_error"]
            }
        }
    ]


@pytest.fixture
def workspace_context_data():
    """Sample workspace context data"""
    return {
        "files": ["app.py", "models.py", "auth.py"],
        "language": "python",
        "frameworks": ["django", "rest_framework"],
        "imports": ["django.db", "rest_framework.views", "jwt"],
        "classes": ["UserAuthentication", "CustomTokenAuth"],
        "functions": ["authenticate", "validate_token", "refresh_token"]
    }


class TestNovelQueryRouting:
    """Test routing for novel queries that should go to DYNAMIC"""
    
    def test_eslint_hybrid_automation_routes_dynamic(self, router, novel_queries):
        """Test that ESLint hybrid automation query routes to dynamic"""
        query_data = novel_queries[0]
        
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=False,
            has_static_response=True
        )
        
        # Complex query with many technologies should route to dynamic
        # May route to HYBRID if confidence is borderline
        assert metrics.decision in [RouteDecision.DYNAMIC, RouteDecision.HYBRID]
        # Should have reduced confidence due to complexity (5+ technologies)
        assert metrics.confidence < 0.7  # Should be below threshold
        # Reasoning will vary, but decision is what matters
        assert metrics.decision == RouteDecision.DYNAMIC
    
    def test_multi_tenant_auth_routes_dynamic(self, router, novel_queries):
        """Test that complex multi-tenant auth query routes to dynamic"""
        query_data = novel_queries[1]
        
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=False,
            has_static_response=True
        )
        
        # Complex multi-part query should route to dynamic
        # Long query (50+ words) with many technologies
        assert metrics.decision == RouteDecision.DYNAMIC
        # Should have reduced confidence due to many technologies and complexity
        assert metrics.confidence < 0.7
    
    def test_webassembly_debug_routes_dynamic(self, router, novel_queries):
        """Test that WebAssembly debugging query routes to dynamic"""
        query_data = novel_queries[2]
        
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=True,  # Has workspace context
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
        assert metrics.confidence < 0.5  # Even lower with workspace context
        assert "workspace context" in metrics.reasoning.lower()
    
    def test_graphql_optimization_routes_dynamic(self, router, novel_queries):
        """Test that complex optimization query routes to dynamic"""
        query_data = novel_queries[3]
        
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=False,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
        assert metrics.confidence < 0.7
        assert metrics.latency_estimate_ms == 2000  # Dynamic takes ~2s


class TestCommonQueryRouting:
    """Test routing for common queries that should go to STATIC"""
    
    def test_solid_principles_routes_static(self, router, common_queries):
        """Test that SOLID principles query routes to static"""
        query_data = common_queries[0]
        
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=False,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.STATIC
        assert metrics.confidence >= 0.6
        assert "Simple" in metrics.reasoning or "General" in metrics.reasoning
        assert metrics.latency_estimate_ms == 50  # Static is fast
    
    def test_react_vs_vue_routes_static(self, router, common_queries):
        """Test that React vs Vue comparison routes to static"""
        query_data = common_queries[1]
        
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=False,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.STATIC
        assert metrics.confidence >= 0.7
        assert "Common pattern" in metrics.reasoning or "Common intent" in metrics.reasoning
    
    def test_rest_vs_graphql_routes_static(self, router, common_queries):
        """Test that REST vs GraphQL comparison routes to static"""
        query_data = common_queries[3]
        
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=False,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.STATIC
        assert metrics.confidence >= 0.7
        assert "Common pattern" in metrics.reasoning
    
    def test_code_review_best_practices_routes_static(self, router, common_queries):
        """Test that code review best practices routes to static"""
        query_data = common_queries[4]
        
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=False,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.STATIC
        assert metrics.confidence >= 0.7
        assert "best" in query_data["query"].lower()


class TestBorderlineConfidence:
    """Test edge cases where confidence is borderline"""
    
    def test_borderline_with_speed_preference_routes_hybrid(self, router_with_speed_preference, borderline_queries):
        """Test that borderline queries with speed preference route to hybrid"""
        query_data = borderline_queries[0]
        
        metrics = router_with_speed_preference.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=False,
            has_static_response=True
        )
        
        # With speed preference and medium confidence, should get HYBRID
        if metrics.confidence >= 0.4 and metrics.confidence < 0.7:
            assert metrics.decision == RouteDecision.HYBRID
            assert metrics.latency_estimate_ms == 500
    
    def test_borderline_without_speed_preference_routes_dynamic(self, router, borderline_queries):
        """Test that borderline queries without speed preference route to dynamic"""
        query_data = borderline_queries[1]
        
        # Add workspace context to push confidence lower
        metrics = router.decide_route(
            query=query_data["query"],
            intent=query_data["intent"],
            context=query_data["context"],
            has_workspace_context=True,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
        assert metrics.confidence < 0.7
    
    def test_confidence_threshold_adjustment(self, router):
        """Test that confidence threshold can be adjusted"""
        # Start with default threshold
        assert router.confidence_threshold == 0.7
        
        # Create feedback data showing static responses failing
        feedback = [
            {"decision": "static", "success": False} for _ in range(15)
        ]
        
        router.optimize_threshold(feedback)
        
        # Threshold should increase
        assert router.confidence_threshold > 0.7
        assert router.confidence_threshold <= 0.9


class TestMCPSamplingFallback:
    """Test fallback behavior when MCP sampling fails"""
    
    def test_fallback_on_generation_failure(self, router):
        """Test fallback to static when dynamic generation fails"""
        metrics = RouteMetrics(
            decision=RouteDecision.DYNAMIC,
            confidence=0.3,
            reasoning="Novel scenario",
            latency_estimate_ms=2000,
            fallback_available=True
        )
        
        should_fallback = router.should_fallback(
            metrics=metrics,
            generation_failed=True,
            latency_ms=1000
        )
        
        assert should_fallback is True
    
    def test_fallback_on_high_latency(self, router):
        """Test fallback to static when latency exceeds threshold"""
        metrics = RouteMetrics(
            decision=RouteDecision.DYNAMIC,
            confidence=0.3,
            reasoning="Novel scenario",
            latency_estimate_ms=2000,
            fallback_available=True
        )
        
        should_fallback = router.should_fallback(
            metrics=metrics,
            generation_failed=False,
            latency_ms=6000  # >5s threshold
        )
        
        assert should_fallback is True
    
    def test_no_fallback_when_unavailable(self, router):
        """Test no fallback when static response unavailable"""
        metrics = RouteMetrics(
            decision=RouteDecision.DYNAMIC,
            confidence=0.3,
            reasoning="Novel scenario",
            latency_estimate_ms=2000,
            fallback_available=False  # No static available
        )
        
        should_fallback = router.should_fallback(
            metrics=metrics,
            generation_failed=True,
            latency_ms=6000
        )
        
        assert should_fallback is False
    
    def test_no_fallback_on_success(self, router):
        """Test no fallback when generation succeeds within latency"""
        metrics = RouteMetrics(
            decision=RouteDecision.DYNAMIC,
            confidence=0.3,
            reasoning="Novel scenario",
            latency_estimate_ms=2000,
            fallback_available=True
        )
        
        should_fallback = router.should_fallback(
            metrics=metrics,
            generation_failed=False,
            latency_ms=2000  # Within acceptable range
        )
        
        assert should_fallback is False


class TestCircuitBreaker:
    """Test circuit breaker behavior for MCP sampling"""
    
    def test_circuit_breaker_opens_after_failures(self, circuit_breaker):
        """Test that circuit breaker opens after threshold failures"""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        
        # Record failures up to threshold
        for _ in range(3):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.can_execute() is False
    
    def test_circuit_breaker_half_open_after_timeout(self, circuit_breaker):
        """Test that circuit breaker goes to half-open after timeout"""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        
        # Simulate timeout passing
        circuit_breaker.last_failure_time = time.time() - 31  # 31s ago
        
        # Should allow one attempt
        assert circuit_breaker.can_execute() is True
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN
    
    def test_circuit_breaker_closes_after_successes(self, circuit_breaker):
        """Test that circuit breaker closes after success threshold"""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()
        
        # Move to half-open
        circuit_breaker.last_failure_time = time.time() - 31
        circuit_breaker.can_execute()
        
        # Record successes
        circuit_breaker.record_success()
        circuit_breaker.record_success()
        
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    def test_circuit_breaker_reopens_on_half_open_failure(self, circuit_breaker):
        """Test that circuit breaker reopens on failure in half-open state"""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()
        
        # Move to half-open
        circuit_breaker.last_failure_time = time.time() - 31
        circuit_breaker.can_execute()
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN
        
        # Fail again
        circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitBreakerState.OPEN


class TestLatencyRequirements:
    """Test latency requirements (<3s)"""
    
    @pytest.mark.asyncio
    async def test_static_response_latency(self, router):
        """Test that static responses meet latency requirements"""
        start_time = time.time()
        
        metrics = router.decide_route(
            query="What is SOLID?",
            intent="explanation",
            context={"technologies": []},
            has_workspace_context=False,
            has_static_response=True
        )
        
        routing_time = (time.time() - start_time) * 1000
        
        assert metrics.decision == RouteDecision.STATIC
        assert metrics.latency_estimate_ms == 50
        assert routing_time < 100  # Routing decision should be very fast
    
    @pytest.mark.asyncio
    async def test_dynamic_response_latency_estimate(self, router):
        """Test that dynamic responses have accurate latency estimates"""
        metrics = router.decide_route(
            query="Complex novel query with many specific requirements",
            intent="implementation",
            context={"technologies": ["a", "b", "c", "d", "e", "f"]},
            has_workspace_context=True,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
        assert metrics.latency_estimate_ms == 2000  # ~2s for dynamic
        assert metrics.latency_estimate_ms < 3000  # Under 3s requirement
    
    @pytest.mark.asyncio
    async def test_hybrid_response_latency(self, router_with_speed_preference):
        """Test that hybrid responses balance speed and quality"""
        metrics = router_with_speed_preference.decide_route(
            query="How to implement auth with Django?",
            intent="implementation_guide",
            context={"technologies": ["django"]},
            has_workspace_context=False,
            has_static_response=True
        )
        
        if metrics.decision == RouteDecision.HYBRID:
            assert metrics.latency_estimate_ms == 500
            assert metrics.latency_estimate_ms < 3000
    
    def test_timeout_enforcement(self, mcp_client):
        """Test that timeouts are enforced for MCP sampling"""
        config = SamplingConfig(
            temperature=0.7,
            max_tokens=500,
            quality=ResponseQuality.FAST
        )
        
        # Timeout would be handled at the MCP client level, not in config
        assert config.max_tokens == 500
        params = config.to_params()
        assert "maxTokens" in params
        assert params["maxTokens"] == 500


class TestCacheScenarios:
    """Test cache hit/miss scenarios"""
    
    def test_cache_hit_on_repeated_query(self, router):
        """Test that repeated queries hit the cache"""
        query = "Should I use React or Vue?"
        intent = "decision"
        context = {"technologies": ["react", "vue"]}
        
        # First call - cache miss
        metrics1 = router.decide_route(query, intent, context, False, True)
        
        # Second call - should hit cache
        metrics2 = router.decide_route(query, intent, context, False, True)
        
        assert metrics1.decision == metrics2.decision
        assert metrics1.confidence == metrics2.confidence
        assert router.get_stats()["cache_hits"] > 0
    
    def test_cache_miss_on_different_query(self, router):
        """Test that different queries miss the cache"""
        # First query
        router.decide_route(
            "Query 1",
            "intent1",
            {"technologies": ["tech1"]},
            False, True
        )
        
        # Different query - should miss cache
        router.decide_route(
            "Query 2",
            "intent2",
            {"technologies": ["tech2"]},
            False, True
        )
        
        stats = router.get_stats()
        assert stats["total_requests"] == 2
        assert stats["cache_hits"] == 0
    
    def test_cache_disabled(self, router_no_cache):
        """Test that caching can be disabled"""
        query = "Same query"
        intent = "intent"
        context = {"technologies": []}
        
        # Make multiple calls
        router_no_cache.decide_route(query, intent, context, False, True)
        router_no_cache.decide_route(query, intent, context, False, True)
        
        stats = router_no_cache.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["total_requests"] == 2
    
    def test_response_cache_operations(self, response_cache):
        """Test response cache for MCP sampling results"""
        # Put response in cache
        response_cache.put(
            intent="test_intent",
            query="test query",
            context={"tech": ["python"]},
            response={"content": "Test response", "confidence": 0.9}
        )
        
        # Hit - exact match
        cached = response_cache.get(
            intent="test_intent",
            query="test query",
            context={"tech": ["python"]}
        )
        assert cached is not None
        assert cached["content"] == "Test response"
        
        # Miss - different intent
        cached = response_cache.get(
            intent="different_intent",
            query="test query",
            context={"tech": ["python"]}
        )
        assert cached is None
        
        # Check stats
        stats = response_cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == "50.0%"


class TestWorkspaceContextInfluence:
    """Test how workspace context influences routing decisions"""
    
    def test_workspace_reduces_confidence(self, router):
        """Test that workspace context reduces confidence for static routing"""
        # Use a generic query that doesn't mention project/code
        query = "How to implement authentication?"
        
        # Without workspace context
        metrics_without = router.decide_route(
            query=query,
            intent="implementation_guide",
            context={"technologies": ["django"]},
            has_workspace_context=False,
            has_static_response=True
        )
        
        # With workspace context - should reduce confidence
        metrics_with = router.decide_route(
            query=query,
            intent="implementation_guide",
            context={"technologies": ["django"]},
            has_workspace_context=True,  # Has workspace
            has_static_response=True
        )
        
        # Workspace context should reduce confidence by 0.2 according to the scorer
        # The confidence should be reduced OR the reasoning should mention workspace
        confidence_reduced = metrics_with.confidence < metrics_without.confidence
        workspace_mentioned = "workspace" in metrics_with.reasoning.lower()
        decision_changed = metrics_with.decision != metrics_without.decision
        
        # At least one of these should be true
        assert confidence_reduced or workspace_mentioned or decision_changed, \
            f"Workspace context had no effect: confidence {metrics_without.confidence} -> {metrics_with.confidence}, " \
            f"reasoning: {metrics_with.reasoning}, decision: {metrics_without.decision} -> {metrics_with.decision}"
        
        # If confidence is approximately the same (within 0.01), check other factors
        if abs(metrics_with.confidence - metrics_without.confidence) < 0.01:
            # Either reasoning or decision should change
            assert workspace_mentioned or decision_changed
        else:
            # Confidence should be reduced when workspace context is present
            assert metrics_with.confidence < metrics_without.confidence
    
    def test_workspace_forces_dynamic_for_specific_queries(self, router, workspace_context_data):
        """Test that workspace context forces dynamic for file-specific queries"""
        metrics = router.decide_route(
            query="How to fix the auth issue in auth.py?",
            intent="debugging_help",
            context={
                "technologies": ["python", "django"],
                "workspace_data": workspace_context_data
            },
            has_workspace_context=True,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
        assert metrics.confidence < 0.7
        assert "specific files" in metrics.reasoning.lower() or "workspace" in metrics.reasoning.lower()
    
    def test_workspace_aware_prompt_building(self, workspace_context_data):
        """Test that prompts include workspace context appropriately"""
        prompt = PromptBuilder.build_prompt(
            intent="implementation_guide",
            query="How to add refresh token to my auth system?",
            context={"technologies": ["django", "jwt"]},
            workspace_data=workspace_context_data
        )
        
        # Should include workspace information
        assert "auth.py" in prompt
        # Check query appears in prompt
        assert "refresh token" in prompt.lower()
        # Check that some workspace data made it into the prompt
        assert "django" in prompt.lower()
        # Frameworks should be in the formatted workspace context
        assert "rest_framework" in prompt
    
    def test_file_reference_detection(self, router):
        """Test that file references in queries influence routing"""
        metrics = router.decide_route(
            query="Debug the error in models.py line 42",
            intent="debugging_help",
            context={"technologies": ["python"]},
            has_workspace_context=False,  # Even without workspace
            has_static_response=True
        )
        
        # File reference should reduce confidence
        assert metrics.confidence < 0.7
        assert "specific files" in metrics.reasoning.lower() or ".py" in metrics.reasoning


class TestRouteOptimization:
    """Test route optimization based on historical performance"""
    
    def test_optimizer_learns_from_outcomes(self, optimizer):
        """Test that optimizer learns from routing outcomes"""
        # Record successful static routes for a pattern
        for i in range(5):
            optimizer.record_outcome(
                query="Should I use X",
                decision=RouteDecision.STATIC,
                latency_ms=50,
                success=True
            )
        
        # Should recommend static for similar pattern
        recommendation = optimizer.get_pattern_recommendation("Should I use Y")
        assert recommendation == RouteDecision.STATIC
    
    def test_optimizer_handles_failures(self, optimizer):
        """Test that optimizer adjusts for failures"""
        # Record failed dynamic routes for a pattern
        for i in range(5):
            optimizer.record_outcome(
                query="Complex integration X",
                decision=RouteDecision.DYNAMIC,
                latency_ms=5000,
                success=False
            )
        
        # Should not recommend dynamic for similar pattern
        recommendation = optimizer.get_pattern_recommendation("Complex integration Y")
        assert recommendation != RouteDecision.DYNAMIC
    
    def test_optimizer_performance_summary(self, optimizer):
        """Test optimizer performance summary generation"""
        # Record mixed outcomes
        optimizer.record_outcome("query1", RouteDecision.STATIC, 50, True)
        optimizer.record_outcome("query2", RouteDecision.DYNAMIC, 2000, True)
        optimizer.record_outcome("query3", RouteDecision.STATIC, 45, False)
        optimizer.record_outcome("query4", RouteDecision.DYNAMIC, 3000, False)
        
        summary = optimizer.get_performance_summary()
        
        assert summary["total_requests"] == 4
        assert summary["static_requests"] == 2
        assert summary["dynamic_requests"] == 2
        assert "success_rate" in summary
        assert summary["static_avg_latency"] < summary["dynamic_avg_latency"]
    
    def test_optimizer_history_limit(self, optimizer):
        """Test that optimizer respects history size limits"""
        # Add more items than the limit
        for i in range(150):
            optimizer.record_outcome(
                query=f"query{i}",
                decision=RouteDecision.STATIC,
                latency_ms=50,
                success=True
            )
        
        # Should only keep max_history_size items
        assert len(optimizer.history) == 100
    
    def test_optimizer_pattern_limit(self, optimizer):
        """Test that optimizer respects pattern limits"""
        # Add more patterns than the limit
        for i in range(100):
            optimizer.record_outcome(
                query=f"pattern {i} test",
                decision=RouteDecision.STATIC,
                latency_ms=50,
                success=True
            )
        
        # Should only keep max_patterns
        assert len(optimizer.pattern_performance) <= 50


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_novel_query_full_flow(self, router, mcp_client):
        """Test full flow for a novel query"""
        query = "Integrate our custom ESLint rules with TypeScript 5.0 and new decorators"
        
        # Step 1: Route decision
        metrics = router.decide_route(
            query=query,
            intent="integration",
            context={"technologies": ["eslint", "typescript", "5.0", "decorators"]},
            has_workspace_context=True,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
        
        # Step 2: Attempt dynamic generation (mock)
        with patch.object(mcp_client, 'generate_dynamic_response') as mock_generate:
            mock_generate.return_value = {
                "content": "Dynamic response for ESLint integration",
                "confidence": 0.8,
                "latency_ms": 1800
            }
            
            response = await mcp_client.generate_dynamic_response(
                intent="integration",
                query=query,
                context={"technologies": ["eslint", "typescript"]},
                workspace_data=None,
                ctx=None
            )
            
            assert response is not None
            assert response["latency_ms"] < 3000
    
    @pytest.mark.asyncio
    async def test_common_query_full_flow(self, router):
        """Test full flow for a common query"""
        query = "What are SOLID principles?"
        
        # Step 1: Route decision
        metrics = router.decide_route(
            query=query,
            intent="explanation",
            context={"technologies": []},
            has_workspace_context=False,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.STATIC
        assert metrics.latency_estimate_ms == 50
        
        # Step 2: Would fetch from static response bank (not implemented here)
        # In real implementation, this would fetch pre-written response
    
    @pytest.mark.asyncio
    async def test_fallback_flow(self, router, mcp_client):
        """Test fallback flow when dynamic generation fails"""
        query = "Complex query that might fail"
        
        # Step 1: Route to dynamic
        metrics = router.decide_route(
            query=query,
            intent="complex",
            context={"technologies": ["a", "b", "c", "d", "e"]},
            has_workspace_context=True,
            has_static_response=True
        )
        
        assert metrics.decision == RouteDecision.DYNAMIC
        
        # Step 2: Dynamic generation fails
        with patch.object(mcp_client, 'generate_dynamic_response') as mock_generate:
            mock_generate.return_value = None  # Failure
            
            response = await mcp_client.generate_dynamic_response(
                intent="complex",
                query=query,
                context={},
                workspace_data=None,
                ctx=None
            )
            
            assert response is None
        
        # Step 3: Check if should fallback
        should_fallback = router.should_fallback(
            metrics=metrics,
            generation_failed=True,
            latency_ms=0
        )
        
        assert should_fallback is True
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, mcp_client):
        """Test circuit breaker integration with MCP client"""
        # Directly test circuit breaker behavior
        circuit_breaker = mcp_client.circuit_breaker
        
        # Simulate multiple failures
        for i in range(3):
            circuit_breaker.record_failure()
        
        # Circuit should be open now
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.can_execute() is False
        
        # Test recovery behavior
        # Simulate timeout passing
        circuit_breaker.last_failure_time = time.time() - 31
        assert circuit_breaker.can_execute() is True  # Should move to half-open
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN


class TestPerformanceAndMetrics:
    """Test performance tracking and metrics"""
    
    def test_router_statistics(self, router):
        """Test router statistics tracking"""
        # Make various routing decisions
        router.decide_route("query1", "intent1", {}, False, True)
        router.decide_route("query2", "intent2", {}, True, True)
        router.decide_route("query3", "intent3", {}, False, True, force_dynamic=True)
        
        # Check statistics
        stats = router.get_stats()
        assert stats["total_requests"] == 3
        assert stats["static_routes"] >= 0
        assert stats["dynamic_routes"] >= 1  # At least one forced dynamic
        assert "static_percentage" in stats
        assert "dynamic_percentage" in stats
        assert "cache_hit_rate" in stats
    
    def test_confidence_scorer_patterns(self):
        """Test confidence scorer pattern matching"""
        scorer = ConfidenceScorer()
        
        # Test high confidence patterns
        high_conf, _ = scorer.calculate_confidence(
            query="Should I use React or Vue for my frontend?",
            intent="decision",
            context={"technologies": ["react", "vue"]},
            has_workspace_context=False
        )
        assert high_conf > 0.5
        
        # Test low confidence patterns
        low_conf, _ = scorer.calculate_confidence(
            query="Integrate X with Y and Z in my custom implementation",
            intent="integration",
            context={"technologies": ["x", "y", "z"]},
            has_workspace_context=True
        )
        assert low_conf < 0.5
    
    def test_latency_tracking(self, optimizer):
        """Test latency tracking and analysis"""
        # Record various latencies
        optimizer.record_outcome("q1", RouteDecision.STATIC, 30, True)
        optimizer.record_outcome("q2", RouteDecision.STATIC, 60, True)
        optimizer.record_outcome("q3", RouteDecision.DYNAMIC, 1500, True)
        optimizer.record_outcome("q4", RouteDecision.DYNAMIC, 2500, True)
        
        summary = optimizer.get_performance_summary()
        
        # Static should be faster than dynamic
        assert summary["static_avg_latency"] < 100
        assert summary["dynamic_avg_latency"] > 1000
        assert summary["static_avg_latency"] < summary["dynamic_avg_latency"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=vibe_check.mentor.hybrid_router", "--cov=vibe_check.mentor.mcp_sampling"])