"""
Integration Tests for Architectural Concept Detection

Tests the full integration with real GitHub issue examples
as suggested in the PR review feedback.
"""

import pytest
from unittest.mock import Mock, patch

from vibe_check.tools.analyze_issue_nollm import GitHubIssueAnalyzer
from vibe_check.core.architectural_concept_detector import ArchitecturalConceptDetector


class TestArchitecturalIntegration:
    """Integration tests for architectural concept detection with issue analysis"""

    def test_real_github_issue_examples(self):
        """Test with real-world GitHub issue examples"""
        detector = ArchitecturalConceptDetector()

        # Real-world issue examples that should trigger architectural concept detection
        real_issue_examples = [
            {
                "title": "Authentication timeout on login",
                "body": "Users are experiencing timeouts when trying to log in. The authentication service seems to be slow.",
                "expected_concepts": ["authentication"],
            },
            {
                "title": "Payment processing error with Stripe webhooks",
                "body": "We're getting intermittent failures in payment processing. Stripe webhooks are not being handled correctly.",
                "expected_concepts": ["payment"],
            },
            {
                "title": "API rate limiting not working",
                "body": "The rate limiting on our REST API endpoints is not functioning properly. Users can make unlimited requests.",
                "expected_concepts": ["api"],
            },
            {
                "title": "Database connection pool exhausted",
                "body": "Our application is running out of database connections. The connection pool seems to be leaking connections.",
                "expected_concepts": ["database"],
            },
            {
                "title": "Redis caching strategy review needed",
                "body": "Our current caching implementation with Redis is causing memory issues. We need to review the TTL strategy.",
                "expected_concepts": ["caching"],
            },
            {
                "title": "Multi-concept issue",
                "body": "Users can't complete payments because the authentication API is slow and the database is timing out during checkout.",
                "expected_concepts": ["authentication", "payment", "api", "database"],
            },
        ]

        for example in real_issue_examples:
            # Test architectural concept detection
            full_text = f"Title: {example['title']}\n{example['body']}"
            result = detector.detect_concepts(
                example["body"], f"Title: {example['title']}"
            )

            detected_concepts = [c.concept_name for c in result.detected_concepts]

            # Verify expected concepts are detected
            for expected_concept in example["expected_concepts"]:
                assert expected_concept in detected_concepts, (
                    f"Expected '{expected_concept}' in issue: {example['title']}\n"
                    f"Detected: {detected_concepts}"
                )

            # Verify search guidance is provided
            assert (
                len(result.github_search_queries) > 0
            ), f"No search guidance for: {example['title']}"

    def test_end_to_end_issue_analysis_integration(self):
        """Test end-to-end integration with GitHubIssueAnalyzer (mocked GitHub API)"""

        # Mock GitHub API response
        mock_issue_data = {
            "number": 123,
            "title": "Authentication system performance issues",
            "body": "Users are reporting slow login times. The JWT validation seems to be taking too long.",
            "author": "testuser",
            "created_at": "2025-06-20T00:00:00Z",
            "repository": "test/repo",
            "url": "https://github.com/test/repo/issues/123",
            "labels": ["bug", "performance"],
        }

        # Create analyzer with mocked GitHub data
        analyzer = GitHubIssueAnalyzer()

        # Mock the GitHub API call to return our test data
        with patch.object(analyzer, "_fetch_issue_data", return_value=mock_issue_data):
            # Run analysis
            result = analyzer.analyze_issue(123, "test/repo", detail_level="standard")

            # Verify architectural concepts were detected and included in response
            assert "architectural_concepts" in result
            arch_concepts = result["architectural_concepts"]

            assert arch_concepts["detected"] is True
            assert arch_concepts["primary_concept"]["name"] == "authentication"
            assert len(arch_concepts["search_guidance"]["github_queries"]) > 0

            # Verify architectural guidance is in recommended actions
            actions = result["recommended_actions"]
            auth_guidance_found = any(
                "authentication" in action.lower() for action in actions
            )
            assert (
                auth_guidance_found
            ), "Expected authentication-specific guidance in recommended actions"

    def test_integration_with_no_concepts_detected(self):
        """Test integration when no architectural concepts are detected"""
        detector = ArchitecturalConceptDetector()

        # Issue with no architectural concepts
        result = detector.detect_concepts(
            "The user interface colors are wrong and the text is too small",
            "Title: UI styling issues",
        )

        assert len(result.detected_concepts) == 0
        assert len(result.search_recommendations) == 0
        assert len(result.github_search_queries) == 0

        # Verify analysis context handles no concepts gracefully
        context = detector.generate_analysis_context(result)
        assert context["architectural_focus"] is None
        assert context["analysis_mode"] == "general"

    def test_architectural_recommendations_quality(self):
        """Test that architectural recommendations are specific and actionable"""
        detector = ArchitecturalConceptDetector()

        # Test each supported concept for recommendation quality
        concept_tests = [
            ("authentication", "Authentication system is slow"),
            ("payment", "Payment processing is failing"),
            ("api", "API endpoints are not responding"),
            ("database", "Database queries are timing out"),
            ("caching", "Cache invalidation is not working"),
        ]

        for concept_name, test_text in concept_tests:
            result = detector.detect_concepts(test_text)

            # Should detect the concept
            assert len(result.detected_concepts) > 0
            concept = result.detected_concepts[0]
            assert concept.concept_name == concept_name

            # Get specific recommendations
            recommendations = detector._get_concept_specific_recommendations(concept)

            # Verify recommendations are specific and actionable
            assert len(recommendations) > 0

            # Check that recommendations contain concept-specific keywords
            rec_text = " ".join(recommendations).lower()

            if concept_name == "authentication":
                assert any(
                    keyword in rec_text
                    for keyword in ["jwt", "token", "session", "password"]
                )
            elif concept_name == "payment":
                assert any(
                    keyword in rec_text
                    for keyword in ["stripe", "webhook", "transaction", "billing"]
                )
            elif concept_name == "api":
                assert any(
                    keyword in rec_text
                    for keyword in ["endpoint", "route", "middleware", "validation"]
                )
            elif concept_name == "database":
                assert any(
                    keyword in rec_text
                    for keyword in ["query", "connection", "index", "migration"]
                )
            elif concept_name == "caching":
                assert any(
                    keyword in rec_text
                    for keyword in ["redis", "ttl", "invalidation", "cache"]
                )

    def test_github_search_query_generation_quality(self):
        """Test that generated GitHub search queries are well-formed and useful"""
        detector = ArchitecturalConceptDetector()

        result = detector.detect_concepts(
            "Authentication middleware is causing timeouts"
        )

        assert len(result.github_search_queries) > 0

        # Verify queries contain relevant search terms
        queries_text = " ".join(result.github_search_queries).lower()
        assert any(
            term in queries_text
            for term in ["auth", "login", "jwt", "token", "session"]
        )

        # Test with repository context
        concept = result.detected_concepts[0]
        guidance = detector.get_file_discovery_guidance(concept, "owner/repo")

        # Verify repository-scoped queries
        scoped_queries = guidance["github_search_queries"]
        assert any("repo:owner/repo" in query for query in scoped_queries)

        # Verify file pattern queries
        assert any("path:" in query for query in scoped_queries)

    def test_confidence_scoring_accuracy(self):
        """Test that confidence scores reflect detection accuracy"""
        detector = ArchitecturalConceptDetector()

        # High confidence cases (multiple keywords)
        high_confidence_text = (
            "JWT authentication token validation in login session middleware"
        )
        result = detector.detect_concepts(high_confidence_text)

        assert len(result.detected_concepts) > 0
        auth_concept = result.detected_concepts[0]
        assert auth_concept.concept_name == "authentication"
        assert auth_concept.confidence >= 0.8  # Should be high confidence

        # Lower confidence cases (single keyword)
        low_confidence_text = "System authentication"
        result = detector.detect_concepts(low_confidence_text)

        if result.detected_concepts:  # Might not detect due to improved precision
            auth_concept = result.detected_concepts[0]
            assert auth_concept.confidence < 0.8  # Should be lower confidence

    def test_edge_cases_and_robustness(self):
        """Test edge cases and system robustness"""
        detector = ArchitecturalConceptDetector()

        # Empty and minimal inputs
        edge_cases = ["", "a", "The system", "error occurred", "needs fixing"]

        for case in edge_cases:
            # Should not crash
            result = detector.detect_concepts(case)
            assert isinstance(result.detected_concepts, list)
            assert isinstance(result.search_recommendations, list)
            assert isinstance(result.github_search_queries, list)

        # Very long input
        long_text = "authentication " * 1000
        result = detector.detect_concepts(long_text)
        assert len(result.detected_concepts) > 0  # Should still detect

        # Special characters and encoding
        special_text = "Authentication with émojis 🔐 and spéciál characters"
        result = detector.detect_concepts(special_text)
        assert len(result.detected_concepts) > 0  # Should still detect authentication
