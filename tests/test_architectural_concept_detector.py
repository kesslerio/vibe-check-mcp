"""
Tests for Architectural Concept Detector

Tests the minimal viable architectural concept detection functionality
following MVP approach from vibe mentor feedback.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from vibe_check.core.architectural_concept_detector import (
    ArchitecturalConceptDetector,
    ArchitecturalConcept,
    ConceptDetectionResult
)


class TestArchitecturalConceptDetector:
    """Test suite for architectural concept detection"""

    def setup_method(self):
        """Setup test fixtures"""
        self.detector = ArchitecturalConceptDetector()

    def test_detect_authentication_concepts(self):
        """Test detection of authentication-related concepts"""
        text = "Our authentication system is slow and users can't log in"
        
        result = self.detector.detect_concepts(text)
        
        assert len(result.detected_concepts) == 1
        auth_concept = result.detected_concepts[0]
        assert auth_concept.concept_name == "authentication"
        assert auth_concept.confidence > 0.3
        assert "auth" in auth_concept.keywords_found or "login" in auth_concept.keywords_found
        assert len(auth_concept.search_terms) > 0
        assert len(auth_concept.file_patterns) > 0

    def test_detect_payment_concepts(self):
        """Test detection of payment-related concepts"""
        text = "Payment processing fails intermittently for some customers using Stripe"
        
        result = self.detector.detect_concepts(text)
        
        assert len(result.detected_concepts) >= 1
        payment_concept = next(
            (c for c in result.detected_concepts if c.concept_name == "payment"), 
            None
        )
        assert payment_concept is not None
        assert payment_concept.confidence > 0.3
        assert "payment" in payment_concept.keywords_found or "stripe" in payment_concept.keywords_found

    def test_detect_database_concepts(self):
        """Test detection of database-related concepts"""
        text = "Database connection pooling seems broken and queries are timing out"
        
        result = self.detector.detect_concepts(text)
        
        assert len(result.detected_concepts) >= 1
        db_concept = next(
            (c for c in result.detected_concepts if c.concept_name == "database"), 
            None
        )
        assert db_concept is not None
        assert db_concept.confidence > 0.3
        assert "database" in db_concept.keywords_found or "query" in db_concept.keywords_found

    def test_detect_multiple_concepts(self):
        """Test detection of multiple architectural concepts in one text"""
        text = """
        Our authentication system is slow and the payment processing 
        API endpoints are failing. Database queries are also timing out.
        """
        
        result = self.detector.detect_concepts(text)
        
        # Should detect at least authentication, payment, api, and database
        concept_names = [c.concept_name for c in result.detected_concepts]
        
        assert "authentication" in concept_names
        assert "payment" in concept_names or "api" in concept_names
        assert "database" in concept_names
        assert len(result.detected_concepts) >= 3

    def test_no_concepts_detected(self):
        """Test behavior when no architectural concepts are detected"""
        text = "The user interface colors look wrong and the font is too small"
        
        result = self.detector.detect_concepts(text)
        
        assert len(result.detected_concepts) == 0
        assert len(result.search_recommendations) == 0
        assert len(result.github_search_queries) == 0

    def test_confidence_threshold(self):
        """Test that concepts below confidence threshold are filtered out"""
        # Single keyword should be below threshold
        text = "auth"  # Just one keyword, should be low confidence
        
        result = self.detector.detect_concepts(text)
        
        # Should still detect but with lower confidence
        if result.detected_concepts:
            auth_concept = result.detected_concepts[0]
            assert auth_concept.confidence >= 0.3  # Our minimum threshold

    def test_context_enhancement(self):
        """Test that context enhances concept detection"""
        text = "The system is slow"
        context = "Title: Authentication login issues"
        
        result = self.detector.detect_concepts(text, context)
        
        # Should detect authentication from context
        concept_names = [c.concept_name for c in result.detected_concepts]
        assert "authentication" in concept_names

    def test_file_discovery_guidance(self):
        """Test file discovery guidance generation"""
        concept = ArchitecturalConcept(
            concept_name="authentication",
            confidence=0.8,
            keywords_found=["auth", "login"],
            search_terms=["jwt OR token OR session OR auth OR login"],
            file_patterns=["**/auth/**", "**/login/**"],
            common_files=["middleware", "routes", "models"]
        )
        
        guidance = self.detector.get_file_discovery_guidance(concept, "owner/repo")
        
        assert guidance["concept"] == "authentication"
        assert guidance["confidence"] == 0.8
        assert len(guidance["github_search_queries"]) > 0
        assert any("repo:owner/repo" in query for query in guidance["github_search_queries"])

    def test_analysis_context_generation(self):
        """Test analysis context generation for issue analysis"""
        # Create mock detection result
        concept = ArchitecturalConcept(
            concept_name="authentication",
            confidence=0.8,
            keywords_found=["auth", "login"],
            search_terms=["jwt OR token OR session OR auth OR login"],
            file_patterns=["**/auth/**", "**/login/**"],
            common_files=["middleware", "routes", "models"]
        )
        
        result = ConceptDetectionResult(
            detected_concepts=[concept],
            original_text="auth system slow",
            search_recommendations=["jwt OR token OR session OR auth OR login"],
            github_search_queries=["jwt OR token OR session OR auth OR login"]
        )
        
        context = self.detector.generate_analysis_context(result)
        
        assert context["architectural_focus"] == "authentication"
        assert context["analysis_mode"] == "architecture_aware"
        assert context["primary_concept"]["name"] == "authentication"
        assert len(context["recommendations"]) > 0

    def test_supported_concepts(self):
        """Test that all expected architectural concepts are supported"""
        concepts = self.detector.get_supported_concepts()
        
        expected_concepts = ["authentication", "payment", "api", "database", "caching"]
        for expected in expected_concepts:
            assert expected in concepts

    def test_concept_info_retrieval(self):
        """Test retrieval of concept information"""
        auth_info = self.detector.get_concept_info("authentication")
        
        assert auth_info is not None
        assert auth_info["name"] == "authentication"
        assert len(auth_info["keywords"]) > 0
        assert len(auth_info["file_patterns"]) > 0
        assert len(auth_info["search_terms"]) > 0

        # Test non-existent concept
        invalid_info = self.detector.get_concept_info("nonexistent")
        assert invalid_info is None

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive"""
        text_upper = "AUTHENTICATION SYSTEM IS SLOW"
        text_lower = "authentication system is slow"
        text_mixed = "Authentication System Is Slow"
        
        result_upper = self.detector.detect_concepts(text_upper)
        result_lower = self.detector.detect_concepts(text_lower)
        result_mixed = self.detector.detect_concepts(text_mixed)
        
        # All should detect authentication
        assert len(result_upper.detected_concepts) > 0
        assert len(result_lower.detected_concepts) > 0
        assert len(result_mixed.detected_concepts) > 0
        
        assert result_upper.detected_concepts[0].concept_name == "authentication"
        assert result_lower.detected_concepts[0].concept_name == "authentication"
        assert result_mixed.detected_concepts[0].concept_name == "authentication"


class TestArchitecturalConceptIntegration:
    """Integration tests for architectural concept detection with issue analysis"""

    def test_concept_specific_recommendations(self):
        """Test that concept-specific recommendations are generated"""
        detector = ArchitecturalConceptDetector()
        
        # Create authentication concept
        concept = ArchitecturalConcept(
            concept_name="authentication",
            confidence=0.8,
            keywords_found=["auth", "login"],
            search_terms=["jwt OR token OR session OR auth OR login"],
            file_patterns=["**/auth/**", "**/login/**"],
            common_files=["middleware", "routes", "models"]
        )
        
        recommendations = detector._get_concept_specific_recommendations(concept)
        
        assert len(recommendations) > 0
        assert any("JWT" in rec or "jwt" in rec.lower() for rec in recommendations)
        assert any("session" in rec.lower() for rec in recommendations)

    def test_github_search_query_generation(self):
        """Test GitHub search query generation for concepts"""
        detector = ArchitecturalConceptDetector()
        
        text = "Authentication system performance issues"
        result = detector.detect_concepts(text)
        
        assert len(result.github_search_queries) > 0
        # Should contain search terms for authentication
        assert any("auth" in query.lower() for query in result.github_search_queries)

    def test_mvp_functionality_scope(self):
        """Test that MVP implementation covers the core use cases from Issue #155"""
        detector = ArchitecturalConceptDetector()
        
        # Test cases from the issue description
        test_cases = [
            "Our authentication system is slow",
            "Payment processing fails intermittently", 
            "The API rate limiting isn't working",
            "Database connection pooling seems broken",
            "Caching strategy needs review"
        ]
        
        for test_case in test_cases:
            result = detector.detect_concepts(test_case)
            
            # Each should detect at least one relevant concept
            assert len(result.detected_concepts) > 0, f"Failed to detect concepts in: {test_case}"
            
            # Should provide search guidance
            assert len(result.github_search_queries) > 0, f"No search guidance for: {test_case}"