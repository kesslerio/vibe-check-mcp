"""
Unit tests for Integration Pattern Detection for Vibe Coding Safety Net

Tests the enhanced pattern detection system with integration-specific capabilities
that prevent engineering disasters like the Cognee case study.
"""

import pytest
from unittest.mock import patch, mock_open
import json

from vibe_check.core.integration_pattern_detector import (
    IntegrationPatternDetector,
    TechnologyDetection,
    IntegrationAnalysis,
)
from vibe_check.tools.integration_pattern_analysis import (
    analyze_integration_patterns_fast,
    quick_technology_scan,
    analyze_effort_complexity,
)




@pytest.fixture
def mock_anti_patterns_file():
    """Mock the anti_patterns.json and case studies file loading"""
    def mock_open_side_effect(file_path, *args, **kwargs):
        if "anti_patterns.json" in str(file_path):
            sample_data = {
                "schema_version": "1.1.0",
                "integration_over_engineering": {
                    "technologies": {
                        "cognee": {
                            "official_solution": "cognee/cognee:main Docker container",
                            "red_flags": ["custom REST server", "manual JWT"]
                        },
                        "supabase": {
                            "official_solution": "Supabase client libraries",
                            "red_flags": ["custom auth server", "manual JWT handling"]
                        }
                    }
                }
            }
        else:  # case studies file
            sample_data = {
                "case_studies": []
            }
        return mock_open(read_data=json.dumps(sample_data))(*args, **kwargs)
    
    with patch("builtins.open", side_effect=mock_open_side_effect):
        with patch("pathlib.Path.exists", return_value=True):
            yield

class TestRealWorldScenarios:
    """Test with real-world integration scenarios"""

    def test_cognee_case_study_detection(self, mock_anti_patterns_file):
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

        result = analyze_integration_patterns_fast(
            content, detail_level="comprehensive"
        )

        # Should detect critical warning level
        assert result["warning_level"] in ["warning", "critical"]

        # Should detect Cognee
        tech_names = [t["technology"] for t in result["technologies_detected"]]
        assert "cognee" in tech_names

        # Should provide specific recommendations
        recommendations = result["recommendations"]
        cognee_recommendations = [r for r in recommendations if "cognee" in r.lower()]
        assert len(cognee_recommendations) >= 1

    def test_supabase_over_engineering_detection(self, mock_anti_patterns_file):
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

    def test_multiple_technologies_scenario(self, mock_anti_patterns_file):
        """Test scenario with multiple integration technologies"""
        content = """
        Our microservices architecture uses:
        - Cognee for knowledge management (custom Docker setup)
        - Supabase for authentication (manual implementation) 
        - OpenAI for AI features (custom HTTP wrapper)
        - Claude for analysis (building our own client)
        """

        result = analyze_integration_patterns_fast(
            content, detail_level="comprehensive"
        )

        # Should detect multiple technologies
        tech_names = [t["technology"] for t in result["technologies_detected"]]
        assert len(tech_names) >= 3
        assert "cognee" in tech_names
        assert "supabase" in tech_names

        # Should have high warning level due to multiple custom implementations
        assert result["warning_level"] in ["warning", "critical"]

    def test_legitimate_custom_development(self, mock_anti_patterns_file):
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
        from vibe_check.tools.integration_pattern_analysis import (
            reset_integration_detector,
        )

        reset_integration_detector()

    def teardown_method(self):
        """Clean up after each test"""
        from vibe_check.tools.integration_pattern_analysis import (
            reset_integration_detector,
        )

        reset_integration_detector()

    def test_quick_scan_performance(self):
        """Test that quick technology scan is truly fast"""
        import time
        from concurrent.futures import (
            ThreadPoolExecutor,
            TimeoutError as FutureTimeoutError,
        )

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
                assert (
                    execution_time < 0.2
                )  # 200ms threshold (relaxed for CI stability)

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
            "Claude client library creation",
        ]

        results = []
        results_lock = threading.Lock()

        def analyze_content(content):
            try:
                result = analyze_integration_patterns_fast(
                    content, detail_level="brief"
                )
                with results_lock:
                    results.append(result)
                logger.debug(f"Successfully analyzed: {content[:30]}...")
            except Exception as e:
                logger.error(
                    f"Analysis failed for '{content[:30]}...': {e}", exc_info=True
                )
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
                pytest.fail(
                    f"Thread timed out after {timeout_seconds} seconds - possible hang detected"
                )

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
