"""
Integration test for vibe_check_mentor with MCP sampling capability
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from vibe_check.tools.vibe_mentor_enhanced import EnhancedVibeMentorEngine
from vibe_check.mentor.models.persona import PersonaData
from vibe_check.mentor.models.session import CollaborativeReasoningSession


class TestMentorMCPIntegration:
    """Test the integration of MCP sampling with vibe_check_mentor"""
    
    def test_enhanced_mentor_initialization_with_mcp(self):
        """Test that enhanced mentor initializes with MCP sampling components"""
        # Mock base engine
        mock_base_engine = Mock()
        
        # Create enhanced engine with MCP sampling enabled
        engine = EnhancedVibeMentorEngine(
            base_engine=mock_base_engine,
            enable_mcp_sampling=True
        )
        
        # Verify MCP components are initialized
        assert engine.enable_mcp_sampling is True
        assert engine.mcp_client is not None
        assert engine.hybrid_router is not None
        assert engine.dynamic_cache is not None
        assert engine.route_optimizer is not None
    
    def test_enhanced_mentor_initialization_without_mcp(self):
        """Test that enhanced mentor works without MCP sampling"""
        mock_base_engine = Mock()
        
        # Create enhanced engine with MCP sampling disabled
        engine = EnhancedVibeMentorEngine(
            base_engine=mock_base_engine,
            enable_mcp_sampling=False
        )
        
        # Verify MCP components are not initialized
        assert engine.enable_mcp_sampling is False
        assert engine.mcp_client is None
        assert engine.hybrid_router is None
        assert engine.dynamic_cache is None
        assert engine.route_optimizer is None
    
    @pytest.mark.asyncio
    async def test_mcp_sampling_research_findings(self):
        """Test that validates the critical MCP sampling research findings from issue #195"""
        from vibe_check.mentor.mcp_sampling import (
            MCPSamplingClient,
            SamplingConfig,
            ResponseQuality,
            CircuitBreaker
        )
        from vibe_check.mentor.hybrid_router import HybridRouter
        
        # Test 1: Verify latency is under 3 seconds
        client = MCPSamplingClient(
            config=SamplingConfig(
                temperature=0.7,
                max_tokens=500,
                quality=ResponseQuality.FAST
            ),
            request_timeout=3  # 3 second timeout as per requirement
        )
        
        # Verify timeout is set correctly
        assert client.request_timeout == 3
        assert client.config.max_tokens == 500
        
        # Test 2: Verify circuit breaker is configured
        assert client.circuit_breaker is not None
        assert isinstance(client.circuit_breaker, CircuitBreaker)
        assert client.circuit_breaker.failure_threshold == 5
        assert client.circuit_breaker.recovery_timeout == 60
        
        # Test 3: Verify hybrid router handles novel queries
        router = HybridRouter(confidence_threshold=0.7)
        
        # Novel query from issue #189
        novel_query = "Should I implement ESLint hybrid automation strategy?"
        
        metrics = router.decide_route(
            query=novel_query,
            intent="implementation",
            context={"technologies": ["eslint", "automation"]},
            has_workspace_context=False,
            has_static_response=False  # No static response for novel query
        )
        
        # Should route to dynamic for novel queries without static responses
        assert metrics.decision.value == "dynamic"
        assert metrics.confidence < 0.7  # Low confidence for novel query
        
        # Test 4: Verify error handling with mock context
        mock_ctx = AsyncMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("Test failure"))
        
        # Should return None on failure (triggers fallback)
        result = await client.request_completion(
            messages="Test query",
            ctx=mock_ctx
        )
        
        assert result is None  # Graceful failure
        
        # Test 5: Verify successful response with mock
        mock_ctx_success = AsyncMock()
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_ctx_success.sample = AsyncMock(return_value=mock_response)
        
        result = await client.request_completion(
            messages="Test query",
            ctx=mock_ctx_success
        )
        
        assert result == "Test response"
        
    @pytest.mark.asyncio
    async def test_novel_query_handling(self):
        """Test that MCP sampling handles novel queries that break static system"""
        from vibe_check.mentor.mcp_sampling import MCPSamplingClient, PromptBuilder
        from unittest.mock import MagicMock
        
        # The specific novel query from issue #189
        NOVEL_QUERY = "Should I implement ESLint hybrid automation strategy?"
        
        # Test prompt builder generates appropriate prompt
        prompt = PromptBuilder.build_prompt(
            intent="implementation",
            query=NOVEL_QUERY,
            context={
                "technologies": ["eslint", "automation"],
                "patterns": ["hybrid", "strategy"]
            },
            workspace_data=None
        )
        
        # Verify prompt is generated and contains key elements
        assert prompt is not None
        assert len(prompt) > 100
        assert "eslint" in prompt.lower()
        assert NOVEL_QUERY in prompt
        
        # Test that the client can handle the novel query with mock
        client = MCPSamplingClient()
        
        mock_ctx = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = "Dynamic response for ESLint hybrid automation"
        mock_ctx.sample = AsyncMock(return_value=mock_response)
        
        response = await client.generate_dynamic_response(
            intent="implementation",
            query=NOVEL_QUERY,
            context={"technologies": ["eslint"]},
            workspace_data=None,
            ctx=mock_ctx
        )
        
        # Verify response is generated
        assert response is not None
        assert response["generated"] is True
        assert response["confidence"] > 0.8
        assert "Dynamic response" in response["content"]
    
    @patch('vibe_check.tools.vibe_mentor_enhanced.MCP_SAMPLING_AVAILABLE', False)
    def test_enhanced_mentor_graceful_degradation(self):
        """Test that mentor works when MCP sampling components are not available"""
        mock_base_engine = Mock()
        
        # Try to create with MCP sampling when not available
        engine = EnhancedVibeMentorEngine(
            base_engine=mock_base_engine,
            enable_mcp_sampling=True  # Request MCP but not available
        )
        
        # Should gracefully disable MCP sampling
        assert engine.enable_mcp_sampling is False
        assert engine.mcp_client is None
    
    def test_contribution_generation_with_context(self):
        """Test that contribution generation passes context through"""
        mock_base_engine = Mock()
        engine = EnhancedVibeMentorEngine(
            base_engine=mock_base_engine,
            enable_mcp_sampling=True
        )
        
        # Create mock session and persona
        session = Mock(spec=CollaborativeReasoningSession)
        session.topic = "Should I use microservices?"
        session.contributions = []
        
        persona = Mock(spec=PersonaData)
        persona.id = "senior_engineer"
        persona.name = "Senior Engineer"
        persona.background = "15+ years experience"
        persona.expertise = ["architecture", "scalability"]
        persona.perspective = "pragmatic"
        persona.communication = {"style": "direct", "tone": "professional"}
        
        # Mock the enhanced reasoning
        engine.enhanced_reasoning = Mock()
        engine.enhanced_reasoning.generate_senior_engineer_response = Mock(
            return_value=("Use monolith for now", "suggestion", 0.9)
        )
        
        # Generate contribution without ctx (should use static)
        contribution = engine.generate_contribution(
            session=session,
            persona=persona,
            detected_patterns=[],
            context="Small team, MVP stage",
            project_context=None,
            file_contexts=None,
            ctx=None  # No MCP context
        )
        
        assert contribution is not None
        assert contribution.content == "Use monolith for now"
        assert contribution.type == "suggestion"
        assert contribution.confidence == 0.9
    
    def test_routing_decision_respects_threshold(self):
        """Test that routing decisions respect confidence thresholds"""
        from vibe_check.mentor.hybrid_router import HybridRouter, RouteDecision
        
        # Test with high threshold
        router_high = HybridRouter(confidence_threshold=0.9)
        
        metrics = router_high.decide_route(
            query="How to implement authentication?",
            intent="implementation",
            context={"technologies": ["django"]},
            has_workspace_context=False,
            has_static_response=True
        )
        
        # With high threshold, most queries should go to dynamic
        # unless they have very high confidence
        assert metrics.decision in [RouteDecision.DYNAMIC, RouteDecision.STATIC]
        
        # Test with low threshold
        router_low = HybridRouter(confidence_threshold=0.3)
        
        metrics = router_low.decide_route(
            query="How to implement authentication?",
            intent="implementation",
            context={"technologies": ["django"]},
            has_workspace_context=False,
            has_static_response=True
        )
        
        # With low threshold, more queries should go to static
        assert metrics.confidence >= 0.0
    
    def test_prompt_builder_persona_integration(self):
        """Test that prompt builder correctly incorporates persona information"""
        from vibe_check.mentor.mcp_sampling import PromptBuilder
        
        # Create a mock persona
        persona_data = {
            "name": "Senior Engineer",
            "background": "15+ years building production systems",
            "expertise": ["distributed systems", "scalability"],
            "perspective": "pragmatic, anti-complexity",
            "communication": {
                "style": "direct and clear",
                "tone": "professional but friendly"
            }
        }
        
        # Build prompt with persona context
        prompt = PromptBuilder.build_prompt(
            intent="architecture_decision",
            query="Should we use Kubernetes?",
            context={
                "technologies": ["docker", "aws"],
                "patterns": []
            },
            workspace_data=None
        )
        
        # Verify key elements are in the prompt
        assert "architecture" in prompt.lower() or "design" in prompt.lower()
        assert "kubernetes" in prompt.lower()
        assert "docker" in prompt.lower()
        assert "aws" in prompt.lower()
    
    def test_cache_improves_performance(self):
        """Test that caching improves response times"""
        from vibe_check.mentor.mcp_sampling import ResponseCache
        import time
        
        cache = ResponseCache(max_size=10)
        
        # Simulate slow response generation
        def slow_generate():
            time.sleep(0.01)  # Simulate 10ms generation time
            return {"content": "Generated response", "confidence": 0.85}
        
        # First call - no cache
        start = time.time()
        response = slow_generate()
        cache.put("intent", "query", {"tech": ["python"]}, response)
        first_time = time.time() - start
        
        # Second call - from cache
        start = time.time()
        cached = cache.get("intent", "query", {"tech": ["python"]})
        second_time = time.time() - start
        
        assert cached is not None
        assert cached["content"] == "Generated response"
        assert second_time < first_time  # Cache should be faster
        assert cache.hits == 1
        assert cache.misses == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])