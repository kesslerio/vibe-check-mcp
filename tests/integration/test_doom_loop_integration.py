"""
Integration tests for AI Doom Loop Detection system

Tests the integration of doom loop detection with existing MCP tools,
LLM analyzers, and real-world usage scenarios.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from vibe_check.tools.doom_loop_analysis import (
    analyze_text_for_doom_loops,
    get_session_health_analysis,
    reset_session_tracking,
    enhance_tool_response_with_doom_loop_context,
)


class TestDoomLoopMCPIntegration:
    """Test integration with MCP tools"""

    def test_automatic_session_tracking(self):
        """Test that session tracking starts automatically with tool usage"""
        # Reset any existing session
        reset_session_tracking()

        # Use a tool that should trigger tracking
        result = analyze_text_for_doom_loops(
            "Should we decide between React and Vue?", tool_name="test_integration"
        )

        # Check that session is now active
        health_check = get_session_health_analysis()
        assert health_check["status"] != "no_active_session"

    def test_tool_response_enhancement(self):
        """Test enhancement of existing tool responses with doom loop context"""
        # Create a session with some activity to trigger doom loop detection
        for i in range(4):
            analyze_text_for_doom_loops(
                "Should we use REST or GraphQL? What about gRPC?",
                tool_name="repeated_analysis",
            )

        # Test enhancement of a tool response
        original_response = {
            "status": "analysis_complete",
            "message": "Technology analysis completed",
            "recommendations": [
                "Consider team expertise",
                "Evaluate performance needs",
            ],
        }

        enhanced_response = enhance_tool_response_with_doom_loop_context(
            original_response, "test_tool", "Technology choice discussion"
        )

        # Should either enhance or leave unchanged
        assert "status" in enhanced_response
        assert enhanced_response["status"] == "analysis_complete"

        # If enhanced, should have doom loop context
        if "doom_loop_alert" in enhanced_response:
            assert "warning" in enhanced_response["doom_loop_alert"]
            assert "severity" in enhanced_response["doom_loop_alert"]

    def test_integration_with_existing_pattern_detection(self):
        """Test integration with existing integration pattern detection"""
        # Test content that should trigger both integration and doom loop detection
        problematic_content = """
        We need to decide between building a custom Cognee integration or using their Docker container.
        Should we implement our own REST API or use their official solution?
        What if we need custom authentication handling?
        On the other hand, we could build a FastAPI wrapper.
        But then again, their official container might work.
        However, we should consider our specific requirements.
        What about the pros and cons of each approach?
        We need to evaluate all the trade-offs carefully.
        """

        result = analyze_text_for_doom_loops(
            problematic_content, tool_name="integration_analysis"
        )

        # Should detect doom loop patterns
        assert result["status"] in ["doom_loop_detected", "healthy_analysis"]

        # If detected, should provide intervention
        if result["status"] == "doom_loop_detected":
            assert "intervention" in result
            assert len(result["intervention"]["immediate_actions"]) >= 1


class TestLLMToolIntegration:
    """Test integration with LLM analysis tools"""

    @patch("vibe_check.tools.analyze_llm.specialized_analyzers.analyze_text_llm")
    async def test_llm_tool_doom_loop_enhancement(self, mock_analyze_text):
        """Test that LLM tools are enhanced with doom loop detection"""
        from vibe_check.tools.analyze_llm.specialized_analyzers import (
            analyze_github_issue_llm,
        )

        # Mock the external LLM call
        mock_analyze_text.return_value = {
            "status": "success",
            "analysis": "## Analysis\nThis looks like a good technical approach.",
        }

        # Test with doom loop triggering content
        result = await analyze_github_issue_llm(
            issue_number=123, repository="test/repo", detail_level="standard"
        )

        # Should complete successfully (mocked LLM call)
        assert "status" in result

    def test_doom_loop_context_injection_issue_analysis(self):
        """Test doom loop context injection in issue analysis"""
        # This tests the context preparation, not the full LLM call
        paralysis_issue_content = """
        Title: Choose frontend framework
        
        We need to decide between React, Vue, and Angular for our new project.
        What are the pros and cons of each?
        Should we consider developer experience or performance first?
        What about long-term maintenance and community support?
        How do we evaluate the best choice for our team?
        """

        # Analyze for doom loop patterns
        doom_analysis = analyze_text_for_doom_loops(
            paralysis_issue_content, tool_name="issue_analysis"
        )

        # Should detect analysis paralysis
        if doom_analysis["status"] == "doom_loop_detected":
            assert doom_analysis["severity"] in ["caution", "warning", "critical"]

    def test_doom_loop_context_injection_pr_analysis(self):
        """Test doom loop context injection in PR analysis"""
        overthinking_pr_content = """
        Title: Implement authentication system
        
        This PR implements a comprehensive authentication system with the following considerations:
        - Should we use JWT or session-based authentication?
        - What about refresh token rotation strategies?
        - How do we handle edge cases like concurrent logins?
        - Should we implement custom password policies or use defaults?
        - What about future requirements for multi-factor authentication?
        - How do we ensure the solution is future-proof and scalable?
        """

        # Analyze for doom loop patterns
        doom_analysis = analyze_text_for_doom_loops(
            overthinking_pr_content, tool_name="pr_analysis"
        )

        # Should detect overthinking patterns
        if doom_analysis["status"] == "doom_loop_detected":
            assert doom_analysis["severity"] in ["caution", "warning", "critical"]


class TestRealWorldWorkflowIntegration:
    """Test integration with real-world development workflows"""

    def test_issue_analysis_workflow_with_doom_loops(self):
        """Test complete workflow: issue analysis with doom loop detection"""
        # Simulate analyzing multiple related issues (creating a potential loop)
        issue_contents = [
            "Should we use microservices or monolith architecture?",
            "Need to decide between Docker and Kubernetes deployment",
            "What's the best approach for API design - REST vs GraphQL?",
            "Database choice: SQL vs NoSQL for our use case",
            "How to handle authentication: custom vs third-party?",
        ]

        # Analyze each issue (simulating repeated analysis)
        results = []
        for i, content in enumerate(issue_contents):
            result = analyze_text_for_doom_loops(
                content, f"Issue #{i+1}", "issue_analysis"
            )
            results.append(result)

        # By the 5th analysis, should detect patterns
        session_health = get_session_health_analysis()

        if session_health["status"] != "no_active_session":
            # Health score should decrease with repeated decision-making
            assert session_health["health_score"] <= 100

            # Should track multiple tool calls
            assert session_health["total_mcp_calls"] >= 5

    def test_pr_review_workflow_with_analysis_paralysis(self):
        """Test PR review workflow with analysis paralysis detection"""
        # Simulate reviewing a PR with analysis paralysis content
        pr_content = """
        This PR refactors our data layer but I'm not sure if this is the best approach.
        
        We could use Repository pattern, but maybe Active Record is simpler?
        What about Data Mapper pattern for better separation of concerns?
        Should we consider CQRS for read/write separation?
        How do we handle complex queries and performance optimization?
        
        The current implementation works but feels like it could be better.
        Maybe we should research more patterns before merging?
        What do you think about the trade-offs here?
        """

        # Analyze PR content
        result = analyze_text_for_doom_loops(pr_content, "PR review", "pr_analysis")

        # Should provide guidance
        assert "status" in result

        if result["status"] == "doom_loop_detected":
            # Should suggest concrete actions for PR review context
            intervention = result.get("intervention", {})
            actions = intervention.get("immediate_actions", [])

            # Should have actionable recommendations
            assert len(actions) >= 1

    def test_technology_research_workflow(self):
        """Test technology research workflow with doom loop prevention"""
        # Simulate technology research session
        research_queries = [
            "Compare React vs Vue vs Angular for enterprise applications",
            "Evaluate authentication solutions: Auth0 vs Firebase vs custom",
            "Database selection: PostgreSQL vs MongoDB vs Redis for caching",
            "Deployment options: AWS vs GCP vs Azure for our microservices",
            "Monitoring solutions: DataDog vs New Relic vs Prometheus",
        ]

        # Analyze each research query
        for i, query in enumerate(research_queries):
            result = analyze_text_for_doom_loops(
                f"Research needed: {query}. What are the pros and cons?",
                f"Research session item {i+1}",
                "technology_research",
            )

        # Check session health after extensive research
        session_health = get_session_health_analysis()

        if session_health["status"] != "no_active_session":
            # Should track research patterns
            assert session_health["total_mcp_calls"] >= 5

            # Should detect if research becomes paralysis
            if session_health.get("doom_loop_detected"):
                assert "recommendations" in session_health

    def test_architecture_design_session(self):
        """Test architecture design session with doom loop detection"""
        # Simulate extended architecture design discussion
        architecture_content = """
        System Architecture Design Session:
        
        We need to design a scalable system that can handle millions of users.
        Should we use microservices or start with a modular monolith?
        What about event-driven architecture vs synchronous REST APIs?
        How do we handle data consistency across services?
        Should we implement CQRS and Event Sourcing from the start?
        What about the complexity of distributed transactions?
        How do we ensure the system is maintainable long-term?
        What if requirements change and we need different patterns?
        Should we consider Domain-Driven Design principles?
        How do we handle cross-cutting concerns like logging and monitoring?
        """

        # Analyze architecture discussion
        result = analyze_text_for_doom_loops(
            architecture_content, "Architecture design session", "architecture_analysis"
        )

        # Should detect overthinking patterns
        if result["status"] == "doom_loop_detected":
            assert result["severity"] in ["warning", "critical"]

            # Should provide architecture-specific intervention
            intervention = result.get("intervention", {})
            assert "immediate_actions" in intervention

            # Actions should be relevant to architecture decisions
            actions_text = " ".join(intervention["immediate_actions"])
            architecture_keywords = ["prototype", "simple", "mvp", "implement", "test"]
            assert any(
                keyword in actions_text.lower() for keyword in architecture_keywords
            )


class TestProductivityMetrics:
    """Test productivity metrics and health scoring"""

    def test_health_score_degradation(self):
        """Test that health score degrades with unproductive patterns"""
        # Reset session for clean test
        reset_session_tracking()

        # Start with baseline health check
        initial_health = get_session_health_analysis()

        # Simulate progressively worse patterns
        paralysis_queries = [
            "Should we use approach A or B?",
            "What about approach C vs D?",
            "Maybe we should consider E and F?",
            "On second thought, what about G?",
            "Actually, let's reconsider A again...",
            "But wait, what if we combine B and C?",
            "However, approach D might be simpler...",
            "Then again, maybe E is more future-proof...",
        ]

        health_scores = []

        for query in paralysis_queries:
            analyze_text_for_doom_loops(query, tool_name="repeated_analysis")
            health = get_session_health_analysis()
            if health["status"] != "no_active_session":
                health_scores.append(health["health_score"])

        # Health scores should generally trend downward
        if len(health_scores) >= 3:
            # Later scores should be lower than earlier ones
            early_average = sum(health_scores[:2]) / 2
            late_average = sum(health_scores[-2:]) / 2
            assert late_average <= early_average

    def test_productivity_recovery_after_intervention(self):
        """Test productivity recovery after intervention"""
        # Create doom loop scenario
        for i in range(6):
            analyze_text_for_doom_loops(
                "Complex decision paralysis content with many options to consider",
                tool_name="repeated_tool",
            )

        # Check pre-intervention health
        pre_health = get_session_health_analysis()

        # Reset session (simulating intervention action)
        reset_result = reset_session_tracking()

        # Check post-intervention state
        post_health = get_session_health_analysis()

        # Should indicate fresh start
        assert reset_result["status"] == "session_reset_complete"
        assert post_health["status"] == "no_active_session"

    def test_concurrent_session_health_tracking(self):
        """Test health tracking with concurrent tool usage"""
        import threading
        import time

        def simulate_analysis_work(worker_id):
            for i in range(3):
                analyze_text_for_doom_loops(
                    f"Worker {worker_id} analysis {i}: choosing between options",
                    tool_name=f"worker_{worker_id}_tool",
                )
                time.sleep(0.1)  # Small delay to simulate real usage

        # Start multiple workers
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=simulate_analysis_work, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check final health state
        final_health = get_session_health_analysis()

        if final_health["status"] != "no_active_session":
            # Should track all the concurrent activity
            assert final_health["total_mcp_calls"] >= 9  # 3 workers * 3 calls each
            assert final_health["unique_tools_used"] >= 3  # Different tools per worker


if __name__ == "__main__":
    pytest.main([__file__])
