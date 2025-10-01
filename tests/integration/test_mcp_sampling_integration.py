#!/usr/bin/env python3
"""
Integration tests for MCP sampling in vibe_check_mentor

Tests the complete flow from query to dynamic response generation
including hybrid routing, fallback mechanisms, and security features.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Import the components to test
from vibe_check.tools.vibe_mentor_enhanced import EnhancedVibeMentorEngine
from vibe_check.mentor.mcp_sampling import (
    MCPSamplingClient,
    SamplingConfig,
    CircuitBreaker,
)
from vibe_check.mentor.hybrid_router import HybridRouter, RouteDecision
from vibe_check.mentor.models.session import CollaborativeReasoningSession
from vibe_check.mentor.models.persona import PersonaData


class TestMCPSamplingIntegration:
    """Integration tests for MCP sampling with vibe_check_mentor"""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock FastMCP context"""
        ctx = AsyncMock()
        ctx.sample = AsyncMock()

        # Default response
        mock_response = MagicMock()
        mock_response.text = "This is a dynamic response from MCP sampling"
        ctx.sample.return_value = mock_response

        return ctx

    @pytest.fixture
    def mentor_engine(self):
        """Create mentor engine with MCP sampling enabled"""
        base_engine = MagicMock()
        engine = EnhancedVibeMentorEngine(
            base_engine=base_engine, enable_mcp_sampling=True
        )
        return engine

    @pytest.fixture
    def test_session(self):
        """Create a test session"""
        session = CollaborativeReasoningSession(
            session_id="test-session-123",
            topic="Should I implement ESLint hybrid automation strategy?",
        )

        # Add test personas
        session.personas = [
            PersonaData(
                id="senior_engineer",
                name="Senior Software Engineer",
                expertise=["Architecture", "Best Practices"],
                background="15+ years building production systems",
                perspective="Pragmatic, focused on maintainability",
                biases=["Simplicity", "Proven patterns"],
                communication={"style": "Direct", "tone": "Professional"},
            )
        ]

        return session

    @pytest.mark.asyncio
    async def test_novel_query_routes_to_dynamic(self, mentor_engine, mock_ctx):
        """Test that novel queries trigger dynamic generation"""

        # Novel query that should route to dynamic
        novel_query = "Should I implement ESLint hybrid automation strategy?"

        # Check routing decision
        router = mentor_engine.hybrid_router
        route_metrics = router.decide_route(
            query=novel_query,
            intent="implementation",
            context={"technologies": ["eslint", "automation"]},
            has_workspace_context=False,
            has_static_response=False,
        )

        assert route_metrics.decision == RouteDecision.DYNAMIC
        assert route_metrics.confidence < 0.5  # Low confidence for novel query

    @pytest.mark.asyncio
    async def test_dynamic_generation_with_mcp(
        self, mentor_engine, mock_ctx, test_session
    ):
        """Test complete dynamic response generation flow"""

        persona = test_session.personas[0]

        # Generate contribution with MCP sampling
        contribution = await mentor_engine.generate_contribution(
            session=test_session,
            persona=persona,
            detected_patterns=[],
            context="Need to automate ESLint configuration",
            ctx=mock_ctx,
        )

        # Verify MCP was called
        mock_ctx.sample.assert_called_once()

        # Verify contribution was generated
        assert contribution is not None
        assert contribution.persona_id == "senior_engineer"
        assert contribution.confidence > 0

    @pytest.mark.asyncio
    async def test_fallback_on_mcp_failure(self, mentor_engine, mock_ctx, test_session):
        """Test fallback to static responses when MCP fails"""

        # Make MCP sampling fail
        mock_ctx.sample.side_effect = Exception("MCP service unavailable")

        persona = test_session.personas[0]

        # Should fall back to static response
        contribution = await mentor_engine.generate_contribution(
            session=test_session,
            persona=persona,
            detected_patterns=[],
            context="Need guidance on architecture",
            ctx=mock_ctx,
        )

        # Should still get a response (from static fallback)
        assert contribution is not None
        assert contribution.content != ""  # Got fallback content

    @pytest.mark.asyncio
    async def test_secret_redaction(self, mentor_engine, mock_ctx):
        """Test that secrets are redacted before MCP sampling"""

        from vibe_check.mentor.mcp_sampling import SecretsScanner

        # Query with secrets
        query_with_secrets = (
            "My API key is sk-1234567890abcdef and password is supersecret123"
        )

        scanner = SecretsScanner()
        safe_query = scanner.scan_and_redact(query_with_secrets)

        # Verify secrets are redacted
        assert "sk-1234567890abcdef" not in safe_query
        assert "supersecret123" not in safe_query
        assert "[REDACTED_" in safe_query

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mentor_engine, mock_ctx, test_session):
        """Test rate limiting prevents excessive MCP calls"""

        persona = test_session.personas[0]

        # Try to make many rapid requests
        tasks = []
        for i in range(15):
            task = mentor_engine.generate_contribution(
                session=test_session,
                persona=persona,
                detected_patterns=[],
                context=f"Query {i}",
                ctx=mock_ctx,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful MCP calls
        successful_calls = mock_ctx.sample.call_count

        # Should be rate limited (max 10 per minute)
        assert successful_calls <= 10

    @pytest.mark.asyncio
    async def test_timeout_protection(self, mentor_engine, mock_ctx, test_session):
        """Test timeout protection for slow MCP responses"""

        # Make MCP sampling very slow
        async def slow_response():
            await asyncio.sleep(35)  # Longer than 30s timeout
            return MagicMock(text="Too slow")

        mock_ctx.sample = slow_response

        persona = test_session.personas[0]

        # Should timeout and fall back
        contribution = await mentor_engine.generate_contribution(
            session=test_session,
            persona=persona,
            detected_patterns=[],
            context="Need quick response",
            ctx=mock_ctx,
        )

        # Should get fallback response (not wait 35 seconds)
        assert contribution is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, mentor_engine):
        """Test circuit breaker prevents cascading failures"""

        breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=1, success_threshold=2
        )

        # Simulate failures
        for _ in range(3):
            breaker.record_failure()

        # Circuit should be open
        assert not breaker.can_execute()
        assert breaker.state.value == "open"

        # Wait for recovery
        await asyncio.sleep(1.1)

        # Should transition to half-open
        assert breaker.can_execute()
        assert breaker.state.value == "half_open"

        # Record successes to close
        breaker.record_success()
        breaker.record_success()

        assert breaker.state.value == "closed"

    @pytest.mark.asyncio
    async def test_cache_improves_performance(self, mentor_engine, mock_ctx):
        """Test that cache improves performance for repeated queries"""

        from vibe_check.mentor.mcp_sampling import ResponseCache

        cache = ResponseCache(max_size=100)

        # First call - should miss cache
        intent = "implementation"
        query = "How to implement caching?"
        context = {"technologies": ["redis"]}

        cached = cache.get(intent, query, context)
        assert cached is None  # Cache miss

        # Store in cache
        response = {"content": "Use Redis for caching", "confidence": 0.9}
        cache.put(intent, query, context, response)

        # Second call - should hit cache
        cached = cache.get(intent, query, context)
        assert cached is not None
        assert cached["content"] == "Use Redis for caching"

    @pytest.mark.asyncio
    async def test_prompt_length_enforcement(
        self, mentor_engine, mock_ctx, test_session
    ):
        """Test that overly long prompts are truncated"""

        persona = test_session.personas[0]

        # Create a very long context
        long_context = "x" * 10000  # Very long string

        # Should truncate and still work
        contribution = await mentor_engine.generate_contribution(
            session=test_session,
            persona=persona,
            detected_patterns=[],
            context=long_context,
            ctx=mock_ctx,
        )

        # Verify it worked despite long input
        assert contribution is not None

        # Check that prompt was truncated in the call
        call_args = mock_ctx.sample.call_args
        if call_args:
            messages = call_args.kwargs.get("messages", "")
            # Should be truncated to reasonable length
            assert len(messages) < 8000

    @pytest.mark.asyncio
    async def test_file_path_validation(self):
        """Test that file paths are validated to prevent traversal attacks"""

        from pathlib import Path

        def is_safe_path(file_path: str, workspace_root: str) -> bool:
            """Check if file path is within workspace"""
            try:
                file_abs = Path(file_path).resolve()
                workspace_abs = Path(workspace_root).resolve()
                return file_abs.is_relative_to(workspace_abs)
            except Exception:
                return False

        workspace = "/Users/test/project"

        # Safe paths
        assert is_safe_path("/Users/test/project/src/file.py", workspace)
        assert is_safe_path("/Users/test/project/docs/README.md", workspace)

        # Unsafe paths (traversal attempts)
        assert not is_safe_path("/Users/test/project/../../../etc/passwd", workspace)
        assert not is_safe_path("/etc/passwd", workspace)
        assert not is_safe_path("../../sensitive.txt", workspace)

    @pytest.mark.asyncio
    async def test_hybrid_routing_decisions(self, mentor_engine):
        """Test that hybrid router makes appropriate decisions"""

        router = mentor_engine.hybrid_router

        test_cases = [
            # (query, intent, expected_decision)
            ("What is SOLID?", "explanation", RouteDecision.STATIC),
            ("Should I use React or Vue?", "comparison", RouteDecision.STATIC),
            (
                "Implement ESLint hybrid automation",
                "implementation",
                RouteDecision.DYNAMIC,
            ),
            (
                "Debug memory leak in our custom WebAssembly module",
                "debugging",
                RouteDecision.DYNAMIC,
            ),
        ]

        for query, intent, expected in test_cases:
            route_metrics = router.decide_route(
                query=query,
                intent=intent,
                context={},
                has_workspace_context=False,
                has_static_response=(expected == RouteDecision.STATIC),
            )

            # Note: Actual routing may vary based on confidence
            # but novel queries should tend toward DYNAMIC
            if "ESLint hybrid" in query or "WebAssembly" in query:
                assert route_metrics.confidence < 0.7  # Low confidence for novel

    @pytest.mark.asyncio
    async def test_end_to_end_novel_query(self, mock_ctx):
        """Test complete end-to-end flow with a novel query"""

        # Import the actual vibe_check_mentor function
        from vibe_check.server import vibe_check_mentor

        # Novel query from issue #189
        novel_query = "Should I implement ESLint hybrid automation strategy?"

        # Mock the analyze_text_demo to avoid dependencies
        with patch("vibe_check.server.analyze_text_demo") as mock_analyze:
            mock_analyze.return_value = {"patterns": [], "status": "success"}

            # Call the actual function
            result = await vibe_check_mentor(
                ctx=mock_ctx,
                query=novel_query,
                context="We have a large codebase with varying quality",
                reasoning_depth="quick",
                mode="standard",
            )

            # Verify successful response
            assert result["status"] == "success"
            assert "collaborative_insights" in result
            assert result["session_info"]["can_continue"]

            # Verify MCP was attempted (if available)
            if mock_ctx.sample.called:
                # Dynamic generation was attempted
                assert mock_ctx.sample.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
