"""
Unit tests for AI Doom Loop Detection and Analysis Paralysis Prevention

Tests the doom loop detection system that prevents developers from getting
stuck in unproductive AI conversation cycles and analysis paralysis.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from src.vibe_check.core.doom_loop_detector import (
    DoomLoopDetector,
    LoopSeverity,
    LoopPattern,
    SessionState,
    get_doom_loop_detector
)
from src.vibe_check.tools.doom_loop_analysis import (
    analyze_text_for_doom_loops,
    get_session_health_analysis,
    reset_session_tracking,
    force_doom_loop_intervention
)


class TestDoomLoopDetector:
    """Test the core doom loop detection engine"""
    
    def test_detector_initialization(self):
        """Test doom loop detector initializes correctly"""
        detector = DoomLoopDetector()
        
        assert detector is not None
        assert detector.current_session is None
        assert len(detector.detection_patterns) > 0
        assert len(detector.intervention_strategies) > 0
    
    def test_session_creation(self):
        """Test MCP session creation and tracking"""
        detector = DoomLoopDetector()
        
        session_id = detector.start_session()
        
        assert detector.current_session is not None
        assert detector.current_session.session_id == session_id
        assert detector.current_session.session_duration_minutes == 0
        assert len(detector.current_session.mcp_calls) == 0
    
    def test_mcp_call_tracking(self):
        """Test MCP call tracking functionality"""
        detector = DoomLoopDetector()
        detector.start_session()
        
        # Track several calls
        detector.track_mcp_call("analyze_issue", "Need to choose between React and Vue", "frontend framework")
        detector.track_mcp_call("analyze_issue", "Should we use Redux or Context", "state management")
        detector.track_mcp_call("analyze_issue", "What about TypeScript vs JavaScript", "typing")
        
        assert len(detector.current_session.mcp_calls) == 3
        assert detector.current_session.repeated_calls["analyze_issue"] == 3
        assert len(detector.current_session.topics_discussed) >= 1
    
    def test_text_pattern_detection_analysis_paralysis(self):
        """Test detection of analysis paralysis patterns in text"""
        detector = DoomLoopDetector()
        
        paralysis_text = """
        We need to decide between React and Vue for our frontend.
        Should we use Redux or Context API for state management?
        On the other hand, we could consider Angular.
        But then again, Vue might be simpler.
        However, we could also evaluate Svelte as an option.
        What if we instead go with vanilla JavaScript?
        The pros and cons of each framework need consideration.
        """
        
        pattern = detector.check_text_for_loop_patterns(paralysis_text)
        
        assert pattern is not None
        assert pattern.severity in [LoopSeverity.WARNING, LoopSeverity.CRITICAL]
        assert "paralysis" in pattern.pattern_type.lower()
        assert len(pattern.evidence) >= 1
    
    def test_text_pattern_detection_overthinking(self):
        """Test detection of overthinking patterns"""
        detector = DoomLoopDetector()
        
        overthinking_text = """
        We need a complex solution that handles all edge cases.
        The architecture should be future-proof and enterprise-ready.
        What if we need to scale to millions of users?
        We should follow best practices and design patterns.
        The solution needs to handle complex scenarios and corner cases.
        """
        
        pattern = detector.check_text_for_loop_patterns(overthinking_text)
        
        assert pattern is not None
        assert pattern.severity in [LoopSeverity.WARNING, LoopSeverity.CRITICAL]
        assert len(pattern.evidence) >= 1
    
    def test_text_pattern_detection_healthy_content(self):
        """Test that healthy content doesn't trigger false positives"""
        detector = DoomLoopDetector()
        
        healthy_text = """
        I'll implement user authentication using OAuth.
        The plan is to start with Google OAuth and add more providers later.
        First step: set up OAuth client credentials.
        Second step: implement login flow.
        Let's get the basic flow working today.
        """
        
        pattern = detector.check_text_for_loop_patterns(healthy_text)
        
        # Should not detect doom loops in action-oriented content
        assert pattern is None
    
    def test_temporal_pattern_detection(self):
        """Test detection of time-based doom loop patterns"""
        detector = DoomLoopDetector()
        
        # Create session with extended duration
        detector.start_session()
        # Simulate 35 minutes of session time
        detector.current_session.start_time = time.time() - (35 * 60)
        
        pattern = detector.analyze_current_session()
        
        assert pattern is not None
        assert pattern.severity == LoopSeverity.CRITICAL
        assert "session" in pattern.pattern_type.lower()
        assert pattern.duration_minutes >= 30
    
    def test_repetition_pattern_detection(self):
        """Test detection of repeated tool usage patterns"""
        detector = DoomLoopDetector()
        detector.start_session()
        
        # Simulate repeated tool calls
        for i in range(6):
            detector.track_mcp_call("analyze_issue", f"iteration {i}", "repeated analysis")
        
        pattern = detector.analyze_current_session()
        
        assert pattern is not None
        assert pattern.severity in [LoopSeverity.WARNING, LoopSeverity.CRITICAL]
        assert "repetition" in pattern.pattern_type.lower()
    
    def test_decision_paralysis_detection(self):
        """Test detection of decision paralysis patterns"""
        detector = DoomLoopDetector()
        detector.start_session()
        
        # Simulate decision paralysis conversations
        decision_phrases = [
            "should we use",
            "we need to decide",
            "what if we instead",
            "on the other hand"
        ]
        
        for phrase in decision_phrases:
            detector.track_mcp_call("analyze_issue", f"Content with {phrase}", "decision making")
        
        pattern = detector.analyze_current_session()
        
        assert pattern is not None
        assert pattern.severity in [LoopSeverity.WARNING, LoopSeverity.CRITICAL]
    
    def test_warning_level_calculation(self):
        """Test warning level calculation logic"""
        detector = DoomLoopDetector()
        detector.start_session()
        
        # Simulate critical scenario: long session + repetitions + decisions
        detector.current_session.start_time = time.time() - (45 * 60)  # 45 minutes
        for i in range(8):
            detector.track_mcp_call("analyze_issue", f"Should we decide iteration {i}", "decisions")
        
        pattern = detector.analyze_current_session()
        
        assert pattern is not None
        assert pattern.severity in [LoopSeverity.CRITICAL, LoopSeverity.EMERGENCY]
    
    def test_intervention_recommendations(self):
        """Test intervention recommendation generation"""
        detector = DoomLoopDetector()
        detector.start_session()
        
        # Create a critical loop pattern
        detector.current_session.start_time = time.time() - (40 * 60)
        for i in range(6):
            detector.track_mcp_call("integration_analysis", f"Custom vs official {i}", "integration")
        
        pattern = detector.analyze_current_session()
        intervention = detector.get_intervention_recommendation(pattern)
        
        assert intervention["severity"] in ["critical", "emergency"]
        assert len(intervention["immediate_actions"]) >= 3
        assert "time_budget" in intervention
        assert len(intervention["decision_forcing"]) >= 3


class TestDoomLoopAnalysisTools:
    """Test the MCP tools for doom loop analysis"""
    
    def test_analyze_text_for_doom_loops_tool(self):
        """Test the main text analysis tool"""
        paralysis_text = """
        We need to decide between implementing our own authentication
        or using a third-party service. Should we use Auth0, Firebase,
        or build something custom? On the other hand, we could use
        Supabase. But then again, what if we need custom features?
        However, we could also evaluate AWS Cognito.
        """
        
        result = analyze_text_for_doom_loops(paralysis_text, tool_name="test_analysis")
        
        assert "status" in result
        if result["status"] == "doom_loop_detected":
            assert "severity" in result
            assert "intervention" in result
            assert len(result["intervention"]["immediate_actions"]) >= 1
    
    def test_session_health_analysis_no_session(self):
        """Test session health analysis with no active session"""
        # Reset any existing session
        reset_session_tracking()
        
        result = get_session_health_analysis()
        
        assert result["status"] == "no_active_session"
    
    def test_session_health_analysis_active_session(self):
        """Test session health analysis with active session"""
        # Create some session activity
        analyze_text_for_doom_loops("Test content for session", tool_name="test")
        
        result = get_session_health_analysis()
        
        if result["status"] != "no_active_session":
            assert "health_score" in result
            assert "duration_minutes" in result
            assert result["health_score"] >= 0
            assert result["health_score"] <= 100
    
    def test_force_intervention(self):
        """Test emergency intervention forcing"""
        result = force_doom_loop_intervention()
        
        assert result["status"] == "emergency_intervention_activated"
        assert "intervention" in result
        assert "mandatory_actions" in result
        assert len(result["mandatory_actions"]) >= 4
    
    def test_session_reset(self):
        """Test session tracking reset"""
        # Create some session activity first
        analyze_text_for_doom_loops("Test content", tool_name="test")
        
        result = reset_session_tracking()
        
        assert result["status"] == "session_reset_complete"
        assert "new_session_id" in result
        assert "previous_session" in result


class TestRealWorldScenarios:
    """Test with real-world doom loop scenarios"""
    
    def test_architecture_analysis_paralysis(self):
        """Test detection of architecture analysis paralysis"""
        architecture_paralysis = """
        We need to decide on our microservices architecture.
        Should we use REST APIs or GraphQL for inter-service communication?
        What about message queues - should we use RabbitMQ, Kafka, or Redis?
        On the other hand, we could go with a monolith first approach.
        But then again, microservices give us better scalability.
        However, we could also consider a modular monolith.
        What if we need to handle millions of requests per second?
        The pros and cons of each approach need careful evaluation.
        We should consider future requirements and edge cases.
        """
        
        result = analyze_text_for_doom_loops(architecture_paralysis)
        
        assert result["status"] == "doom_loop_detected"
        assert result["severity"] in ["warning", "critical"]
    
    def test_technology_choice_paralysis(self):
        """Test detection of technology choice paralysis"""
        tech_choice_paralysis = """
        For our frontend, we're comparing React, Vue, and Angular.
        React has a large ecosystem but Vue is simpler to learn.
        Angular is enterprise-ready but has a steep learning curve.
        Should we also consider Svelte or stick with established frameworks?
        What about TypeScript vs JavaScript for type safety?
        We need to evaluate long-term maintenance and team expertise.
        The decision impacts our entire development workflow.
        Maybe we should prototype with multiple frameworks first?
        """
        
        result = analyze_text_for_doom_loops(tech_choice_paralysis)
        
        assert result["status"] == "doom_loop_detected"
        assert result["severity"] in ["warning", "critical"]
    
    def test_database_decision_paralysis(self):
        """Test detection of database decision paralysis"""
        db_paralysis = """
        We're stuck on choosing between SQL and NoSQL databases.
        PostgreSQL offers ACID compliance and complex queries.
        MongoDB provides flexibility and horizontal scaling.
        But what if we need both relational and document features?
        Should we consider a polyglot persistence approach?
        What about performance implications and query complexity?
        We need to handle future scale requirements and data relationships.
        The choice affects our entire data architecture and team skills.
        """
        
        result = analyze_text_for_doom_loops(db_paralysis)
        
        assert result["status"] == "doom_loop_detected"
        assert result["severity"] in ["caution", "warning", "critical"]
    
    def test_healthy_implementation_focused_content(self):
        """Test that implementation-focused content is recognized as healthy"""
        healthy_implementation = """
        I'm implementing user authentication today.
        Step 1: Set up OAuth with Google (using their official SDK)
        Step 2: Create user session management
        Step 3: Add protected route middleware
        Step 4: Test with real user accounts
        
        Starting with the simplest working version.
        Will add more OAuth providers after validating the basic flow.
        Timeline: Complete by end of week, iterate based on user feedback.
        """
        
        result = analyze_text_for_doom_loops(healthy_implementation)
        
        assert result["status"] == "healthy_analysis"
    
    def test_productive_decision_making(self):
        """Test that productive decision-making is not flagged"""
        productive_decisions = """
        After evaluating options, I'm going with PostgreSQL for the initial implementation.
        Reasons: Team expertise, ACID compliance, and good performance for our scale.
        I can always add MongoDB later if we need document storage.
        
        Next steps:
        1. Set up PostgreSQL instance (today)
        2. Design initial schema (tomorrow)
        3. Implement basic CRUD operations (this week)
        4. Add migrations system (next week)
        
        Will validate with real data and iterate based on performance testing.
        """
        
        result = analyze_text_for_doom_loops(productive_decisions)
        
        assert result["status"] == "healthy_analysis"


class TestPerformanceAndReliability:
    """Test performance and reliability characteristics"""
    
    def test_large_content_analysis_performance(self):
        """Test performance with large content"""
        import time
        
        # Create large content (simulating long discussions)
        large_content = "We need to decide between options. " * 1000 + \
                       "Should we use approach A or B? " * 500 + \
                       "What if we consider alternative C? " * 300
        
        start_time = time.time()
        result = analyze_text_for_doom_loops(large_content)
        end_time = time.time()
        
        # Should complete in reasonable time (under 2 seconds)
        execution_time = end_time - start_time
        assert execution_time < 2.0
        
        # Should still provide analysis
        assert "status" in result
    
    def test_error_handling_malformed_content(self):
        """Test error handling with malformed content"""
        malformed_inputs = [
            "",  # Empty string
            None,  # None input would be converted to string
            "A" * 10000,  # Very long string
            "🔥💥🚀" * 100,  # Unicode emojis
            "\n\n\n\t\t\t   ",  # Only whitespace
        ]
        
        for malformed_input in malformed_inputs:
            try:
                if malformed_input is None:
                    result = analyze_text_for_doom_loops("None")
                else:
                    result = analyze_text_for_doom_loops(str(malformed_input))
                
                # Should handle gracefully
                assert "status" in result
                assert result["status"] in ["doom_loop_detected", "healthy_analysis"]
                
            except Exception as e:
                # Should not raise unhandled exceptions
                pytest.fail(f"Unhandled exception with input {malformed_input}: {e}")
    
    def test_concurrent_session_tracking(self):
        """Test behavior with concurrent analysis requests"""
        import threading
        import time
        
        results = []
        
        def analyze_content(content_id):
            content = f"Analysis paralysis content {content_id} - should we decide between options A, B, or C?"
            result = analyze_text_for_doom_loops(content, tool_name=f"test_{content_id}")
            results.append(result)
        
        # Start multiple concurrent analyses
        threads = []
        for i in range(5):
            thread = threading.Thread(target=analyze_content, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All should complete successfully
        assert len(results) == 5
        for result in results:
            assert "status" in result
    
    def test_memory_usage_with_long_sessions(self):
        """Test memory usage during long sessions"""
        detector = DoomLoopDetector()
        detector.start_session()
        
        # Simulate a very long session with many calls
        for i in range(1000):
            detector.track_mcp_call(
                f"tool_{i % 10}",  # Rotate through 10 different tools
                f"Content for iteration {i}",
                f"Context {i}"
            )
        
        # Session should still be functional
        pattern = detector.analyze_current_session()
        health_report = detector.get_session_health_report()
        
        assert health_report is not None
        assert "health_score" in health_report
        
        # Check that memory usage is reasonable (MCP calls should be truncated)
        for call in detector.current_session.mcp_calls:
            assert len(call["content"]) <= 500  # Content should be truncated


if __name__ == "__main__":
    pytest.main([__file__])