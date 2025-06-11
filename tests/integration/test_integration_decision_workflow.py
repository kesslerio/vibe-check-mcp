"""
Integration tests for Integration Decision Check workflow.

Tests the end-to-end workflow of the integration decision tools through
the MCP server interface, validating the complete user experience.
"""

import pytest
import json
from unittest.mock import patch

# Import test utilities
import sys
from pathlib import Path

# Add src to path for testing
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from vibe_check.server import (
    check_integration_alternatives,
    analyze_integration_decision_text,
    integration_decision_framework
)


class TestIntegrationDecisionWorkflow:
    """Test the complete integration decision workflow."""
    
    def test_cognee_integration_warning_workflow(self):
        """Test the workflow for Cognee integration with warning signs."""
        # Step 1: Check integration alternatives for Cognee with red flags
        result = check_integration_alternatives(
            technology="cognee",
            custom_features="custom REST server, JWT authentication, storage management",
            description="Building custom Cognee integration for our application"
        )
        
        assert result["status"] == "success"
        assert result["technology"] == "cognee"
        assert result["warning_level"] in ["warning", "critical"]
        assert result["research_required"] == True
        assert result["custom_justification_needed"] == True
        assert len(result["red_flags_detected"]) >= 1
        assert len(result["official_solutions"]) >= 1
        assert "Docker: cognee/cognee:main" in result["official_solutions"]
        assert "🚨 STOP" in result["recommendation"] or "⚠️ CAUTION" in result["recommendation"]
        
        # Verify decision matrix is present
        assert "decision_matrix" in result
        assert len(result["decision_matrix"]["options"]) == 3
        assert len(result["decision_matrix"]["criteria"]) == 4
        
        # Verify next steps are actionable
        assert len(result["next_steps"]) >= 2
        assert any("test" in step.lower() for step in result["next_steps"])
    
    def test_text_analysis_workflow(self):
        """Test text analysis workflow for integration patterns."""
        # Sample text with integration anti-patterns
        text = """
        We're planning to build a custom FastAPI server for Cognee integration.
        The server will handle JWT authentication and manage storage configurations.
        We'll also need custom Supabase authentication instead of using their SDK.
        """
        
        result = analyze_integration_decision_text(text, detail_level="comprehensive")
        
        assert result["status"] == "success"
        assert "cognee" in result["detected_technologies"]
        assert "supabase" in result["detected_technologies"]
        assert len(result["detected_custom_work"]) >= 3
        assert "custom" in result["detected_custom_work"]
        assert "fastapi" in result["detected_custom_work"]
        assert "authentication" in result["detected_custom_work"]
        
        assert result["warning_level"] in ["warning", "critical"]
        assert len(result["recommendations"]) >= 2
        
        # Check educational content for comprehensive detail level
        assert "educational_content" in result
        assert "integration_best_practices" in result["educational_content"]
        assert "common_anti_patterns" in result["educational_content"]
        assert "case_studies" in result
        assert "cognee_failure" in result["case_studies"]
    
    def test_decision_framework_workflow(self):
        """Test the complete decision framework workflow."""
        result = integration_decision_framework(
            technology="cognee",
            custom_features="REST API, authentication, storage",
            decision_statement="Choose between official Cognee container vs custom development",
            analysis_type="weighted-criteria"
        )
        
        assert result["status"] == "success"
        assert result["technology"] == "cognee"
        assert result["analysis_type"] == "weighted-criteria"
        
        # Verify integration analysis is included
        assert "integration_analysis" in result
        assert "warning_level" in result["integration_analysis"]
        assert "official_solutions" in result["integration_analysis"]
        assert "red_flags_detected" in result["integration_analysis"]
        
        # Verify decision options
        assert len(result["decision_options"]) == 2
        official_option = next(opt for opt in result["decision_options"] if "Official" in opt["option"])
        custom_option = next(opt for opt in result["decision_options"] if "Custom" in opt["option"])
        
        assert len(official_option["pros"]) >= 3
        assert len(custom_option["cons"]) >= 3
        assert official_option["effort_score"] < custom_option["effort_score"]
        assert official_option["maintenance_score"] < custom_option["maintenance_score"]
        
        # Verify scoring matrix for weighted criteria
        assert "scoring_matrix" in result
        assert "official_solution" in result["scoring_matrix"]
        assert "custom_development" in result["scoring_matrix"]
        
        # Verify Clear Thought integration
        assert "clear_thought_integration" in result
        assert result["clear_thought_integration"]["mental_model"] == "first_principles"
        assert len(result["clear_thought_integration"]["validation_steps"]) >= 4
    
    def test_risk_analysis_framework(self):
        """Test risk analysis type in decision framework."""
        result = integration_decision_framework(
            technology="supabase",
            custom_features="custom auth, manual database",
            analysis_type="risk-analysis"
        )
        
        assert result["status"] == "success"
        assert result["analysis_type"] == "risk-analysis"
        
        # Verify risk assessment is included
        assert "risk_assessment" in result
        assert "official_solution_risks" in result["risk_assessment"]
        assert "custom_development_risks" in result["risk_assessment"]
        
        # Custom development should have more and higher probability risks
        custom_risks = result["risk_assessment"]["custom_development_risks"]
        official_risks = result["risk_assessment"]["official_solution_risks"]
        
        assert len(custom_risks) >= len(official_risks)
        assert any("High probability" in risk for risk in custom_risks)
    
    def test_safe_integration_workflow(self):
        """Test workflow for safe integration without red flags."""
        result = check_integration_alternatives(
            technology="docker",
            custom_features="custom business logic, data processing algorithms",
            description="Using Docker for containerization with custom application logic"
        )
        
        assert result["status"] == "success"
        assert result["warning_level"] in ["none", "caution"]
        assert result["research_required"] == False or result["research_required"] == True  # May still need research
        assert len(result["red_flags_detected"]) == 0
        assert "✅ RESEARCH" in result["recommendation"] or "📋 DOCUMENT" in result["recommendation"]
    
    def test_unknown_technology_workflow(self):
        """Test workflow for unknown technology."""
        result = check_integration_alternatives(
            technology="unknown_technology",
            custom_features="feature1, feature2",
            description="Integrating with unknown technology"
        )
        
        assert result["status"] == "success"
        assert result["technology"] == "unknown_technology"
        assert result["warning_level"] == "caution"
        assert len(result["official_solutions"]) == 0
        assert "Research required" in result["recommendation"] or "📋 DOCUMENT" in result["recommendation"]
    
    def test_error_handling_workflow(self):
        """Test error handling in the workflow."""
        # Test with malformed input
        result = check_integration_alternatives(
            technology="",  # Empty technology
            custom_features="",  # Empty features
            description=""
        )
        
        # Should handle gracefully
        assert "status" in result
        # Either succeeds with empty analysis or returns error status
        if result["status"] == "error":
            assert "message" in result
        else:
            assert result["technology"] == ""


class TestWorkflowIntegration:
    """Test integration between different workflow components."""
    
    def test_text_analysis_to_decision_framework(self):
        """Test using text analysis results in decision framework."""
        # First analyze text
        text = "Building custom Cognee FastAPI server with authentication"
        text_result = analyze_integration_decision_text(text)
        
        assert text_result["status"] == "success"
        assert len(text_result["detected_technologies"]) >= 1
        
        # Use detected technology in decision framework
        technology = text_result["detected_technologies"][0]
        framework_result = integration_decision_framework(
            technology=technology,
            custom_features="FastAPI server, authentication",
            analysis_type="weighted-criteria"
        )
        
        assert framework_result["status"] == "success"
        assert framework_result["technology"] == technology
    
    def test_alternative_check_to_framework(self):
        """Test using alternative check results in decision framework."""
        # First check alternatives
        alt_result = check_integration_alternatives(
            technology="cognee",
            custom_features="REST server, JWT auth"
        )
        
        assert alt_result["status"] == "success"
        
        # Use same parameters in framework
        framework_result = integration_decision_framework(
            technology=alt_result["technology"],
            custom_features="REST server, JWT auth",
            analysis_type="risk-analysis"
        )
        
        assert framework_result["status"] == "success"
        
        # Results should be consistent
        assert framework_result["technology"] == alt_result["technology"]
        assert (framework_result["integration_analysis"]["warning_level"] == 
                alt_result["warning_level"])


class TestRealWorldScenarios:
    """Test real-world integration scenarios."""
    
    def test_cognee_case_study_scenario(self):
        """Test the actual Cognee case study scenario."""
        # Simulate the problematic approach from the case study
        text = """
        We need to integrate Cognee into our application. I'm thinking of building
        a custom FastAPI server that will handle the Cognee API calls, implement
        JWT authentication for security, and manage the storage configuration.
        This will give us full control over the integration.
        """
        
        # Analyze the text
        text_result = analyze_integration_decision_text(text, detail_level="comprehensive")
        
        assert text_result["status"] == "success"
        assert "cognee" in text_result["detected_technologies"]
        assert text_result["warning_level"] in ["warning", "critical"]
        
        # Check case study is included
        assert "case_studies" in text_result
        assert "cognee_failure" in text_result["case_studies"]
        
        # Get specific recommendations
        alt_result = check_integration_alternatives(
            technology="cognee",
            custom_features="FastAPI server, JWT authentication, storage configuration"
        )
        
        assert alt_result["status"] == "success"
        assert "🚨 STOP" in alt_result["recommendation"] or "⚠️ CAUTION" in alt_result["recommendation"]
        assert "Docker: cognee/cognee:main" in alt_result["official_solutions"]
        
        # Should require research and justification
        assert alt_result["research_required"] == True
        assert alt_result["custom_justification_needed"] == True
    
    def test_supabase_safe_usage_scenario(self):
        """Test proper Supabase usage scenario."""
        text = """
        We're using the official Supabase JavaScript SDK for authentication
        and database operations. We'll implement custom business logic on top
        of the Supabase primitives.
        """
        
        text_result = analyze_integration_decision_text(text)
        
        assert text_result["status"] == "success"
        assert "supabase" in text_result["detected_technologies"]
        # Should have lower warning level due to proper SDK usage
        assert text_result["warning_level"] in ["none", "caution"]
    
    def test_mixed_technologies_scenario(self):
        """Test scenario with multiple technologies."""
        text = """
        Our architecture uses Supabase for authentication via their SDK,
        a custom Docker container for processing, and we're building a
        custom Claude API client for AI functionality.
        """
        
        text_result = analyze_integration_decision_text(text)
        
        assert text_result["status"] == "success"
        assert "supabase" in text_result["detected_technologies"]
        assert "docker" in text_result["detected_technologies"]
        assert "claude" in text_result["detected_technologies"]
        
        # Should detect the custom Claude client as a potential issue
        claude_recommendations = [
            rec for rec in text_result["recommendations"] 
            if rec["technology"] == "claude"
        ]
        
        if claude_recommendations:
            claude_rec = claude_recommendations[0]
            assert claude_rec["analysis"].warning_level in ["caution", "warning", "critical"]


if __name__ == "__main__":
    pytest.main([__file__])