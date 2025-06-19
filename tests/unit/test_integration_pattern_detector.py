"""
Unit tests for Integration Pattern Detection for Vibe Coding Safety Net

Tests the enhanced pattern detection system with integration-specific capabilities
that prevent engineering disasters like the Cognee case study.
"""

import pytest
from unittest.mock import patch, mock_open
import json

from src.vibe_check.core.integration_pattern_detector import (
    IntegrationPatternDetector,
    TechnologyDetection,
    IntegrationAnalysis
)
from src.vibe_check.tools.integration_pattern_analysis import (
    analyze_integration_patterns_fast,
    quick_technology_scan,
    analyze_effort_complexity
)


@pytest.fixture
def sample_anti_patterns():
    """Sample anti-patterns data with integration patterns"""
    return {
        "schema_version": "1.1.0",
        "data_version": "1.0.0",
        "infrastructure_without_implementation": {
            "id": "infrastructure_without_implementation",
            "version": "1.0.0",
            "name": "Infrastructure Without Implementation",
            "description": "Building custom solutions when standard APIs/SDKs exist",
            "severity": "high",
            "category": "architectural",
            "detection_threshold": 0.5,
            "indicators": [
                {
                    "regex": "\\b(?:custom|build|implement)\\s+(?:server|client|api)",
                    "description": "mentions building custom infrastructure",
                    "weight": 0.4,
                    "text": "custom infrastructure"
                }
            ],
            "negative_indicators": []
        },
        "integration_over_engineering": {
            "id": "integration_over_engineering",
            "version": "1.0.0",
            "name": "Integration Over-Engineering",
            "description": "Building custom integration solutions when official alternatives exist",
            "severity": "high",
            "category": "integration",
            "detection_threshold": 0.5,
            "technologies": {
                "cognee": {
                    "official_solution": "cognee/cognee:main Docker container",
                    "red_flags": ["custom REST server", "manual JWT"],
                    "features": ["REST API", "JWT authentication"]
                },
                "supabase": {
                    "official_solution": "Supabase official SDKs",
                    "red_flags": ["custom auth", "manual database"],
                    "features": ["Authentication", "Database"]
                }
            },
            "indicators": [
                {
                    "regex": "\\b(?:cognee|supabase)\\b.*\\bcustom\\s+(?:server|client)",
                    "description": "custom development for known technology",
                    "weight": 0.5,
                    "text": "custom integration for known tech"
                }
            ],
            "negative_indicators": []
        }
    }


class TestIntegrationPatternDetector:
    """Test the core integration pattern detector"""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    def test_detector_initialization(self, mock_exists, mock_file, sample_anti_patterns):
        """Test detector initializes with integration patterns"""
        mock_file.return_value.read.return_value = json.dumps(sample_anti_patterns)
        
        detector = IntegrationPatternDetector()
        
        assert detector is not None
        assert len(detector.technology_patterns) > 0
        assert "cognee" in detector.technology_patterns
        assert "supabase" in detector.technology_patterns
    
    def test_quick_technology_check(self):
        """Test ultra-fast technology detection"""
        detector = IntegrationPatternDetector()
        
        # Test Cognee detection
        content = "We need to integrate with Cognee for our knowledge management"
        detected = detector.quick_technology_check(content)
        assert "cognee" in detected
        
        # Test multiple technologies
        content = "Using Cognee and Supabase for our backend"
        detected = detector.quick_technology_check(content)
        assert "cognee" in detected
        assert "supabase" in detected
        
        # Test no detection
        content = "We're building a simple web application"
        detected = detector.quick_technology_check(content)
        assert len(detected) == 0
    
    def test_detect_technologies_with_confidence(self):
        """Test technology detection with confidence scoring"""
        detector = IntegrationPatternDetector()
        
        # High confidence detection (multiple indicators)
        content = "We're building a custom FastAPI server for Cognee integration with JWT authentication"
        technologies = detector._detect_technologies(content)
        
        cognee_tech = next((t for t in technologies if t.technology == "cognee"), None)
        assert cognee_tech is not None
        assert cognee_tech.confidence >= 0.6  # High confidence
        assert len(cognee_tech.indicators) >= 2
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_integration_patterns_cognee_case(self, mock_exists, mock_file, sample_anti_patterns):
        """Test analysis of Cognee integration case study scenario"""
        mock_file.return_value.read.return_value = json.dumps(sample_anti_patterns)
        
        detector = IntegrationPatternDetector()
        
        # Cognee case study content
        content = """
        We need to build a custom FastAPI server for Cognee integration.
        The server will handle JWT authentication and manage storage configurations.
        We'll implement our own REST API endpoints for Cognee functionality.
        """
        
        analysis = detector.analyze_integration_patterns(content)
        
        # Should detect Cognee technology
        assert len(analysis.detected_technologies) >= 1
        cognee_tech = next((t for t in analysis.detected_technologies if t.technology == "cognee"), None)
        assert cognee_tech is not None
        
        # Should detect integration anti-patterns
        assert len(analysis.integration_anti_patterns) >= 1
        
        # Should have warning level
        assert analysis.warning_level in ["caution", "warning", "critical"]
        
        # Should provide recommendations
        assert len(analysis.recommendations) >= 1
        
        # Should have research questions
        assert len(analysis.research_questions) >= 1
    
    def test_effort_analysis(self):
        """Test effort-value analysis for integration complexity"""
        detector = IntegrationPatternDetector()
        
        content = """
        This PR adds 2000+ lines for Cognee integration.
        We spent 3 weeks implementing the custom authentication system.
        The integration includes a complex REST server setup.
        """
        
        effort_analysis = detector._analyze_effort_indicators(content)
        
        assert len(effort_analysis["high_line_counts"]) >= 1
        assert effort_analysis["high_line_counts"][0]["count"] >= 2000
        assert len(effort_analysis["time_estimates"]) >= 1
    
    def test_warning_level_calculation(self):
        """Test warning level calculation logic"""
        detector = IntegrationPatternDetector()
        
        # Create mock technologies and patterns for testing
        from src.vibe_check.core.pattern_detector import DetectionResult
        
        # High warning scenario
        high_confidence_pattern = DetectionResult(
            pattern_type="integration_over_engineering",
            detected=True,
            confidence=0.8,
            evidence=["custom server for managed service"],
            threshold=0.5
        )
        
        mock_tech = TechnologyDetection(
            technology="cognee",
            confidence=0.9,
            indicators=["mentions cognee"],
            red_flags=["custom REST server"]
        )
        
        warning_level = detector._calculate_warning_level([mock_tech], [high_confidence_pattern])
        assert warning_level in ["warning", "critical"]


class TestIntegrationPatternAnalysisTools:
    """Test the MCP tools for integration pattern analysis"""
    
    def test_analyze_integration_patterns_fast(self):
        """Test the main MCP tool for fast integration analysis"""
        content = "We're building a custom Cognee server with FastAPI and JWT authentication"
        
        result = analyze_integration_patterns_fast(content, detail_level="standard")
        
        assert result["status"] == "analysis_complete"
        assert "technologies_detected" in result
        assert "warning_level" in result
        assert "recommendations" in result
        
        # Should detect Cognee
        tech_names = [t["technology"] for t in result["technologies_detected"]]
        assert "cognee" in tech_names
    
    def test_quick_tech_scan_tool(self):
        """Test the ultra-fast technology scan MCP tool"""
        content = "Using Supabase for authentication and Cognee for knowledge management"
        
        result = quick_technology_scan(content)
        
        if result["status"] == "technologies_detected":
            tech_names = [t["technology"] for t in result["technologies"]]
            assert "supabase" in tech_names or "cognee" in tech_names
            assert "quick_recommendations" in result
    
    def test_analyze_effort_complexity_tool(self):
        """Test the effort-complexity analysis MCP tool"""
        content = "This 2000+ line integration took 3 weeks to implement for Cognee"
        pr_metrics = {
            "additions": 1500,
            "deletions": 200,
            "changed_files": 25
        }
        
        result = analyze_effort_complexity(content, pr_metrics)
        
        assert result["status"] == "effort_analysis_complete"
        assert "complexity_assessment" in result
        assert "pr_metrics" in result
        
        # Should flag high effort
        assert result["complexity_assessment"] in ["high", "medium"]
    
    def test_error_handling(self):
        """Test graceful error handling in MCP tools"""
        # Test with problematic content that might cause issues
        problematic_content = ""
        
        result = analyze_integration_patterns_fast(problematic_content)
        
        # Should handle gracefully
        assert "status" in result
        # Should either succeed or provide meaningful error info
        assert result["status"] in ["analysis_complete", "error"]


class TestRealWorldScenarios:
    """Test with real-world integration scenarios"""
    
    def test_cognee_case_study_detection(self):
        """Test detection of the actual Cognee case study pattern"""
        content = """
        # Cognee Integration Implementation
        
        We're implementing a custom FastAPI server for Cognee integration.
        The implementation includes:
        - Custom JWT authentication handling
        - Manual storage path configuration
        - Environment variable forcing for Docker setup
        - Custom REST endpoints for Cognee functionality
        
        This is a 2000+ line implementation that took 2+ weeks to develop.
        """
        
        result = analyze_integration_patterns_fast(content, detail_level="comprehensive")
        
        # Should detect critical warning level
        assert result["warning_level"] in ["warning", "critical"]
        
        # Should detect Cognee
        tech_names = [t["technology"] for t in result["technologies_detected"]]
        assert "cognee" in tech_names
        
        # Should provide specific recommendations
        recommendations = result["recommendations"]
        cognee_recommendations = [r for r in recommendations if "cognee" in r.lower()]
        assert len(cognee_recommendations) >= 1
    
    def test_supabase_over_engineering_detection(self):
        """Test detection of Supabase over-engineering patterns"""
        content = """
        Building custom authentication system for our app.
        We're implementing manual database connections to Supabase.
        Custom HTTP client for Supabase API calls instead of using their SDK.
        """
        
        result = analyze_integration_patterns_fast(content)
        
        # Should detect Supabase
        tech_names = [t["technology"] for t in result["technologies_detected"]]
        assert "supabase" in tech_names
        
        # Should flag manual implementation - 3 red flags should trigger critical
        assert result["warning_level"] in ["warning", "critical"]
    
    def test_multiple_technologies_scenario(self):
        """Test scenario with multiple integration technologies"""
        content = """
        Our microservices architecture uses:
        - Cognee for knowledge management (custom Docker setup)
        - Supabase for authentication (manual implementation) 
        - OpenAI for AI features (custom HTTP wrapper)
        - Claude for analysis (building our own client)
        """
        
        result = analyze_integration_patterns_fast(content, detail_level="comprehensive")
        
        # Should detect multiple technologies
        tech_names = [t["technology"] for t in result["technologies_detected"]]
        assert len(tech_names) >= 3
        assert "cognee" in tech_names
        assert "supabase" in tech_names
        
        # Should have high warning level due to multiple custom implementations
        assert result["warning_level"] in ["warning", "critical"]
    
    def test_legitimate_custom_development(self):
        """Test scenario where custom development is justified"""
        content = """
        We tested the official Cognee Docker container extensively.
        The official solution lacks support for our specific requirements:
        - Custom data transformation pipeline
        - Specialized authentication integration with our SSO
        - Performance optimizations for our use case
        
        After documenting these gaps, we decided to build a custom solution.
        We're using the Cognee SDK where possible and only customizing necessary parts.
        """
        
        result = analyze_integration_patterns_fast(content)
        
        # Should still detect Cognee but with lower warning level
        tech_names = [t["technology"] for t in result["technologies_detected"]]
        assert "cognee" in tech_names
        
        # Should have lower warning level due to justification
        assert result["warning_level"] in ["none", "caution"]


class TestPerformanceAndRealTimeUsage:
    """Test performance characteristics for real-time MCP usage"""
    
    def setup_method(self):
        """Reset detector state before each test"""
        from src.vibe_check.tools.integration_pattern_analysis import reset_integration_detector
        reset_integration_detector()
    
    def teardown_method(self):
        """Clean up after each test"""
        from src.vibe_check.tools.integration_pattern_analysis import reset_integration_detector
        reset_integration_detector()
    
    def test_quick_scan_performance(self):
        """Test that quick technology scan is truly fast"""
        import time
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
        
        content = "We're using Cognee, Supabase, OpenAI, and Claude in our application"
        
        # Cross-platform timeout protection using concurrent.futures
        with ThreadPoolExecutor(max_workers=1) as executor:
            start_time = time.time()
            future = executor.submit(quick_technology_scan, content)
            
            try:
                result = future.result(timeout=2.0)  # 2-second timeout
                end_time = time.time()
                
                # Should complete in under 100ms for real-time usage (relaxed to 200ms for CI)
                execution_time = end_time - start_time
                assert execution_time < 0.2  # 200ms threshold (relaxed for CI stability)
                
                # Should still provide useful results
                assert "status" in result
            except FutureTimeoutError:
                raise TimeoutError("Quick scan test timed out - possible hang")
    
    def test_concurrent_analysis(self):
        """Test behavior under concurrent usage (simulating multiple MCP calls)"""
        import threading
        import time
        import logging
        
        # Set up logger for debugging
        logger = logging.getLogger(__name__)
        
        contents = [
            "Building custom Cognee integration",
            "Supabase authentication implementation", 
            "OpenAI API wrapper development",
            "Claude client library creation"
        ]
        
        results = []
        results_lock = threading.Lock()
        
        def analyze_content(content):
            try:
                result = analyze_integration_patterns_fast(content, detail_level="brief")
                with results_lock:
                    results.append(result)
                logger.debug(f"Successfully analyzed: {content[:30]}...")
            except Exception as e:
                logger.error(f"Analysis failed for '{content[:30]}...': {e}", exc_info=True)
                with results_lock:
                    results.append({"status": "error", "error": str(e)})
        
        # Start multiple concurrent analyses
        threads = []
        start_time = time.time()
        
        for content in contents:
            thread = threading.Thread(target=analyze_content, args=(content,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete with timeout
        timeout_seconds = 5.0  # Prevent hanging
        for thread in threads:
            thread.join(timeout=timeout_seconds)
            if thread.is_alive():
                # Thread is still running - this indicates a hang
                pytest.fail(f"Thread timed out after {timeout_seconds} seconds - possible hang detected")
        
        end_time = time.time()
        
        # All should complete successfully
        assert len(results) == 4
        for result in results:
            assert "status" in result
            assert result["status"] in ["analysis_complete", "error"]
        
        # Total time should be reasonable for real-time usage
        total_time = end_time - start_time
        assert total_time < 2.0  # 2 second threshold for 4 concurrent analyses


if __name__ == "__main__":
    pytest.main([__file__])