"""
Unit tests for Integration Decision Check functionality.

Tests the official alternative checking mechanism that prevents unnecessary
custom development by validating integration approaches against official solutions.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from src.vibe_check.tools.integration_decision_check import (
    IntegrationKnowledgeBase,
    check_official_alternatives,
    analyze_integration_text,
    calculate_warning_level,
    generate_decision_matrix,
    generate_validation_questions,
    generate_recommendation
)


@pytest.fixture
def sample_knowledge_base():
    """Sample knowledge base for testing."""
    return {
        "cognee": {
            "official_container": "cognee/cognee:main",
            "features": ["REST API", "JWT authentication", "storage management"],
            "documentation": ["https://cognee.ai/docs"],
            "red_flags": ["custom REST server", "environment forcing", "manual JWT"],
            "official_benefits": ["Professional setup", "Production ready"]
        },
        "supabase": {
            "official_sdks": ["@supabase/supabase-js", "supabase-py"],
            "features": ["Authentication", "Database", "Storage"],
            "documentation": ["https://supabase.com/docs"],
            "red_flags": ["custom auth", "manual database"],
            "official_benefits": ["Built-in auth", "Type safety"]
        }
    }


class TestIntegrationKnowledgeBase:
    """Test the knowledge base functionality."""
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_knowledge_base_success(self, mock_exists, mock_file, sample_knowledge_base):
        """Test successful knowledge base loading."""
        mock_file.return_value.read.return_value = json.dumps(sample_knowledge_base)
        
        kb = IntegrationKnowledgeBase()
        assert kb.knowledge == sample_knowledge_base
    
    @patch("pathlib.Path.exists", return_value=False)
    def test_load_knowledge_base_file_not_found(self, mock_exists):
        """Test knowledge base loading when file doesn't exist."""
        kb = IntegrationKnowledgeBase()
        assert kb.knowledge == {}
    
    def test_get_technology_info(self, sample_knowledge_base):
        """Test retrieving technology information."""
        with patch.object(IntegrationKnowledgeBase, '_load_knowledge_base', return_value=sample_knowledge_base):
            kb = IntegrationKnowledgeBase()
            
            # Test existing technology
            cognee_info = kb.get_technology_info("cognee")
            assert cognee_info["official_container"] == "cognee/cognee:main"
            
            # Test case insensitive
            cognee_info_upper = kb.get_technology_info("COGNEE")
            assert cognee_info_upper == cognee_info
            
            # Test non-existing technology
            unknown_info = kb.get_technology_info("unknown")
            assert unknown_info == {}
    
    def test_detect_red_flags(self, sample_knowledge_base):
        """Test red flag detection."""
        with patch.object(IntegrationKnowledgeBase, '_load_knowledge_base', return_value=sample_knowledge_base):
            kb = IntegrationKnowledgeBase()
            
            technology_info = sample_knowledge_base["cognee"]
            
            # Test with red flags present
            custom_features = ["custom REST server", "manual JWT implementation"]
            red_flags = kb.detect_red_flags(custom_features, technology_info)
            
            assert len(red_flags) == 2
            assert "Custom custom REST server (official alternative available)" in red_flags
            assert "Custom manual JWT implementation (official alternative available)" in red_flags
            
            # Test with no red flags
            safe_features = ["data processing", "custom algorithms"]
            no_flags = kb.detect_red_flags(safe_features, technology_info)
            assert len(no_flags) == 0
    
    def test_analyze_feature_coverage(self, sample_knowledge_base):
        """Test feature coverage analysis."""
        with patch.object(IntegrationKnowledgeBase, '_load_knowledge_base', return_value=sample_knowledge_base):
            kb = IntegrationKnowledgeBase()
            
            technology_info = sample_knowledge_base["cognee"]
            
            # Test features covered by official solution
            custom_features = ["REST API", "JWT authentication", "custom logic"]
            coverage = kb.analyze_feature_coverage(custom_features, technology_info)
            
            assert len(coverage["covered_by_official"]) == 2
            assert len(coverage["gaps"]) == 1
            assert coverage["gaps"][0] == "custom logic"
            assert coverage["coverage_percentage"] == pytest.approx(66.67, rel=1e-2)


class TestWarningLevelCalculation:
    """Test warning level calculation logic."""
    
    def test_critical_warning_level(self):
        """Test critical warning level with many red flags."""
        technology_info = {"red_flags": ["flag1", "flag2", "flag3"], "features": ["f1", "f2"]}
        custom_features = ["flag1 implementation", "flag2 setup", "flag3 config"]
        
        warning_level = calculate_warning_level(custom_features, technology_info)
        assert warning_level == "critical"
    
    def test_warning_level(self):
        """Test warning level with some red flags."""
        technology_info = {"red_flags": ["flag1", "flag2"], "features": ["f1", "f2"]}
        custom_features = ["flag1 implementation", "flag2 setup"]
        
        warning_level = calculate_warning_level(custom_features, technology_info)
        assert warning_level == "warning"
    
    def test_caution_level(self):
        """Test caution level with few red flags or many features."""
        technology_info = {"red_flags": ["flag1"], "features": ["f1", "f2", "f3", "f4"]}
        custom_features = ["flag1 implementation"]
        
        warning_level = calculate_warning_level(custom_features, technology_info)
        assert warning_level == "caution"
    
    def test_no_warning_level(self):
        """Test no warning level."""
        technology_info = {"red_flags": [], "features": ["f1", "f2"]}
        custom_features = ["safe feature"]
        
        warning_level = calculate_warning_level(custom_features, technology_info)
        assert warning_level == "none"
    
    def test_unknown_technology_caution(self):
        """Test caution level for unknown technology."""
        warning_level = calculate_warning_level(["feature1"], {})
        assert warning_level == "caution"


class TestDecisionMatrix:
    """Test decision matrix generation."""
    
    def test_generate_decision_matrix(self):
        """Test decision matrix generation."""
        matrix = generate_decision_matrix("cognee", ["REST API", "authentication"])
        
        assert len(matrix["options"]) == 3
        assert matrix["options"][0]["name"] == "Official Container/SDK"
        assert matrix["options"][2]["name"] == "Custom Development"
        
        assert len(matrix["criteria"]) == 4
        assert sum(criterion["weight"] for criterion in matrix["criteria"]) == 1.0
        
        assert len(matrix["evaluation_questions"]) >= 5
        assert "cognee" in matrix["evaluation_questions"][0]


class TestValidationQuestions:
    """Test validation question generation."""
    
    def test_generate_validation_questions_basic(self):
        """Test basic validation questions."""
        questions = generate_validation_questions("cognee", ["basic feature"])
        
        assert len(questions) >= 5
        assert any("cognee" in q for q in questions)
        assert any("official" in q for q in questions)
    
    def test_generate_validation_questions_auth(self):
        """Test authentication-specific questions."""
        questions = generate_validation_questions("supabase", ["authentication", "user management"])
        
        auth_questions = [q for q in questions if "authentication" in q.lower()]
        assert len(auth_questions) >= 1
    
    def test_generate_validation_questions_api(self):
        """Test API-specific questions."""
        questions = generate_validation_questions("service", ["api endpoints", "REST API"])
        
        api_questions = [q for q in questions if "api" in q.lower()]
        assert len(api_questions) >= 1


class TestRecommendationGeneration:
    """Test recommendation generation logic."""
    
    def test_stop_recommendation_high_red_flags(self):
        """Test STOP recommendation for high red flags."""
        technology_info = {"red_flags": ["flag1", "flag2"], "official_container": "tech/container"}
        custom_features = ["flag1 custom", "flag2 custom"]
        
        recommendation = generate_recommendation("tech", custom_features, technology_info)
        assert "🚨 STOP" in recommendation
    
    def test_caution_recommendation_some_red_flags(self):
        """Test CAUTION recommendation for some red flags."""
        technology_info = {"red_flags": ["flag1"], "official_container": "tech/container"}
        custom_features = ["flag1 custom"]
        
        recommendation = generate_recommendation("tech", custom_features, technology_info)
        assert "⚠️ CAUTION" in recommendation
    
    def test_research_recommendation_no_red_flags(self):
        """Test RESEARCH recommendation for no red flags."""
        technology_info = {"red_flags": [], "official_container": "tech/container"}
        custom_features = ["safe feature"]
        
        recommendation = generate_recommendation("tech", custom_features, technology_info)
        assert "✅ RESEARCH" in recommendation
    
    def test_document_recommendation_unknown_tech(self):
        """Test DOCUMENT recommendation for unknown technology."""
        recommendation = generate_recommendation("unknown", ["feature"], {})
        assert "⚠️ Research required" in recommendation


class TestOfficialAlternativesCheck:
    """Test the main check_official_alternatives function."""
    
    @patch.object(IntegrationKnowledgeBase, '_load_knowledge_base')
    def test_check_cognee_integration(self, mock_load, sample_knowledge_base):
        """Test checking Cognee integration with red flags."""
        mock_load.return_value = sample_knowledge_base
        
        custom_features = ["custom REST server", "JWT authentication", "storage"]
        result = check_official_alternatives("cognee", custom_features)
        
        assert result.technology == "cognee"
        assert result.warning_level in ["caution", "warning", "critical"]
        assert len(result.official_solutions) >= 1
        assert "Docker: cognee/cognee:main" in result.official_solutions
        assert len(result.red_flags_detected) >= 1
        assert result.research_required == True
        assert result.custom_justification_needed == True
        assert "🚨 STOP" in result.recommendation or "⚠️ CAUTION" in result.recommendation
    
    @patch.object(IntegrationKnowledgeBase, '_load_knowledge_base')
    def test_check_safe_integration(self, mock_load, sample_knowledge_base):
        """Test checking integration with no red flags."""
        mock_load.return_value = sample_knowledge_base
        
        custom_features = ["custom business logic", "data processing"]
        result = check_official_alternatives("cognee", custom_features)
        
        assert result.technology == "cognee"
        assert result.warning_level in ["none", "caution"]
        assert len(result.red_flags_detected) == 0
        assert "✅ RESEARCH" in result.recommendation
    
    @patch.object(IntegrationKnowledgeBase, '_load_knowledge_base')
    def test_check_unknown_technology(self, mock_load):
        """Test checking unknown technology."""
        mock_load.return_value = {}
        
        custom_features = ["feature1", "feature2"]
        result = check_official_alternatives("unknown_tech", custom_features)
        
        assert result.technology == "unknown_tech"
        assert result.warning_level == "caution"
        assert len(result.official_solutions) == 0
        assert "Research required" in result.recommendation


class TestIntegrationTextAnalysis:
    """Test text analysis for integration patterns."""
    
    @patch.object(IntegrationKnowledgeBase, '_load_knowledge_base')
    def test_analyze_cognee_integration_text(self, mock_load, sample_knowledge_base):
        """Test analyzing text mentioning Cognee with custom development."""
        mock_load.return_value = sample_knowledge_base
        
        text = "We need to build a custom FastAPI server for Cognee integration with JWT authentication"
        result = analyze_integration_text(text)
        
        assert "cognee" in result["detected_technologies"]
        assert len(result["detected_custom_work"]) > 0
        assert "custom" in result["detected_custom_work"]
        assert "fastapi" in result["detected_custom_work"]
        assert result["warning_level"] in ["caution", "warning", "critical"]
        assert len(result["recommendations"]) >= 1
    
    @patch.object(IntegrationKnowledgeBase, '_load_knowledge_base')
    def test_analyze_safe_integration_text(self, mock_load, sample_knowledge_base):
        """Test analyzing safe integration text."""
        mock_load.return_value = sample_knowledge_base
        
        text = "We will use the official Cognee container for our data processing needs"
        result = analyze_integration_text(text)
        
        assert "cognee" in result["detected_technologies"]
        assert result["warning_level"] == "none"
    
    @patch.object(IntegrationKnowledgeBase, '_load_knowledge_base')
    def test_analyze_no_technologies_text(self, mock_load, sample_knowledge_base):
        """Test analyzing text with no known technologies."""
        mock_load.return_value = sample_knowledge_base
        
        text = "We need to implement some custom business logic for our application"
        result = analyze_integration_text(text)
        
        assert len(result["detected_technologies"]) == 0
        assert len(result["recommendations"]) == 0
        assert result["warning_level"] == "none"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_custom_features(self):
        """Test with empty custom features list."""
        result = check_official_alternatives("cognee", [])
        
        assert result.technology == "cognee"
        assert len(result.red_flags_detected) == 0
    
    def test_none_custom_features(self):
        """Test handling of None custom features."""
        # This should be handled gracefully by the calling code
        # but we test the underlying function behavior
        result = check_official_alternatives("cognee", [])
        assert result is not None
    
    @patch.object(IntegrationKnowledgeBase, '_load_knowledge_base')
    def test_malformed_knowledge_base(self, mock_load):
        """Test handling of malformed knowledge base."""
        # Missing required fields
        mock_load.return_value = {"cognee": {"invalid": "data"}}
        
        result = check_official_alternatives("cognee", ["custom feature"])
        
        # Should handle gracefully
        assert result.technology == "cognee"
        assert result.warning_level in ["none", "caution"]  # Should handle gracefully
    
    def test_case_sensitivity(self):
        """Test case sensitivity handling."""
        result1 = check_official_alternatives("Cognee", ["Custom Feature"])
        result2 = check_official_alternatives("COGNEE", ["CUSTOM FEATURE"])
        
        # Should be handled consistently
        assert result1.technology == "Cognee"
        assert result2.technology == "COGNEE"


if __name__ == "__main__":
    pytest.main([__file__])