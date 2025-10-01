"""
Tests for Contextual Documentation System

Tests the library detection, project documentation parsing, and context management
functionality for project-aware analysis.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from vibe_check.tools.contextual_documentation import (
    LibraryDetectionEngine,
    ProjectDocumentationParser,
    ContextualDocumentationManager,
    AnalysisContext,
    get_context_manager,
    clear_context_manager_cache,
)
from vibe_check.config.vibe_check_config import VibeCheckConfig


class TestLibraryDetectionEngine:
    """Test the library detection functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Mock(spec=VibeCheckConfig)
        config.context_loading.cache_duration_minutes = 60
        config.context_loading.library_detection.exclude_patterns = [
            "node_modules",
            "__pycache__",
        ]
        config.context_loading.library_detection.max_files_to_scan = 100
        config.context_loading.library_detection.timeout_seconds = 10
        return config

    @pytest.fixture
    def detection_engine(self, mock_config):
        """Create a LibraryDetectionEngine instance."""
        with patch(
            "src.vibe_check.tools.contextual_documentation.Path.open",
            mock_open(read_data="{}"),
        ):
            return LibraryDetectionEngine(mock_config)

    def test_detect_libraries_from_content_fastapi(self, detection_engine):
        """Test FastAPI detection from content."""
        content = """
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
        result = detection_engine.detect_libraries_from_content(
            content, "main.py", ".py"
        )

        assert "fastapi" in result
        assert result["fastapi"] > 0.8  # High confidence

    def test_detect_libraries_from_content_react(self, detection_engine):
        """Test React detection from content."""
        content = """
import React, { useState } from 'react';

function MyComponent() {
    const [count, setCount] = useState(0);
    
    return <div>Count: {count}</div>;
}
"""
        result = detection_engine.detect_libraries_from_content(
            content, "Component.tsx", ".tsx"
        )

        assert "react" in result
        assert result["react"] > 0.8  # High confidence

    def test_detect_libraries_from_dependencies_package_json(self, detection_engine):
        """Test library detection from package.json."""
        package_json_content = {
            "dependencies": {"react": "^18.0.0", "fastapi": "^0.100.0"},
            "devDependencies": {"typescript": "^4.0.0"},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            package_json_path = Path(temp_dir) / "package.json"
            with open(package_json_path, "w") as f:
                json.dump(package_json_content, f)

            result = detection_engine.detect_libraries_from_dependencies(temp_dir)

            # Should detect libraries from dependencies
            assert len(result) > 0

    def test_detect_libraries_from_dependencies_requirements_txt(
        self, detection_engine
    ):
        """Test library detection from requirements.txt."""
        requirements_content = """
fastapi==0.100.0
uvicorn[standard]==0.22.0
supabase==1.0.0
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            requirements_path = Path(temp_dir) / "requirements.txt"
            with open(requirements_path, "w") as f:
                f.write(requirements_content)

            result = detection_engine.detect_libraries_from_dependencies(temp_dir)

            # Should detect libraries from requirements
            assert len(result) > 0


class TestProjectDocumentationParser:
    """Test the project documentation parsing functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        return Mock(spec=VibeCheckConfig)

    @pytest.fixture
    def doc_parser(self, mock_config):
        """Create a ProjectDocumentationParser instance."""
        return ProjectDocumentationParser(mock_config)

    def test_load_integration_knowledge_base_missing_file(self, doc_parser):
        """Test knowledge base loading with missing file."""
        with patch("pathlib.Path.exists", return_value=False):
            result = doc_parser._load_integration_knowledge_base()
            assert result == {}

    def test_load_integration_knowledge_base_invalid_json(self, doc_parser):
        """Test knowledge base loading with invalid JSON."""
        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data="invalid json")
        ):
            result = doc_parser._load_integration_knowledge_base()
            assert result == {}

    def test_load_integration_knowledge_base_valid(self, doc_parser):
        """Test knowledge base loading with valid JSON."""
        valid_json = '{"fastapi": {"library_type": "backend_framework"}}'

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=valid_json)
        ):
            result = doc_parser._load_integration_knowledge_base()
            assert "fastapi" in result
            assert result["fastapi"]["library_type"] == "backend_framework"

    def test_parse_project_docs_with_readme(self, doc_parser):
        """Test parsing project docs with README file."""
        readme_content = """
# My Project

This project uses FastAPI and React for a full-stack application.

## Architecture

We use a microservices pattern with Supabase for authentication.
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            readme_path = Path(temp_dir) / "README.md"
            with open(readme_path, "w") as f:
                f.write(readme_content)

            # Mock the knowledge base loading
            with patch.object(
                doc_parser,
                "_load_integration_knowledge_base",
                return_value={"fastapi": {}, "react": {}, "supabase": {}},
            ):
                result = doc_parser.parse_project_docs(temp_dir)

            assert "project_overview" in result
            assert "technology_stack" in result["project_overview"]


class TestAnalysisContext:
    """Test the AnalysisContext functionality."""

    def test_get_contextual_recommendation_generic(self):
        """Test contextual recommendation with generic pattern."""
        context = AnalysisContext(
            library_docs={},
            project_conventions={},
            pattern_exceptions=[],
            conflict_resolution={},
            context_metadata={},
        )

        result = context.get_contextual_recommendation("build_custom_auth")
        assert result == "build_custom_auth"  # Returns generic if no context

    def test_get_contextual_recommendation_with_exception(self):
        """Test contextual recommendation with pattern exception."""
        context = AnalysisContext(
            library_docs={},
            project_conventions={},
            pattern_exceptions=["build_custom_auth"],
            conflict_resolution={"build_custom_auth": "GDPR requires custom auth"},
            context_metadata={},
        )

        result = context.get_contextual_recommendation("build_custom_auth")
        assert result == "GDPR requires custom auth"


class TestContextualDocumentationManager:
    """Test the main contextual documentation manager."""

    def setUp(self):
        """Clear cache before each test."""
        clear_context_manager_cache()

    def test_get_context_manager_caching(self):
        """Test that context managers are cached properly."""
        clear_context_manager_cache()

        manager1 = get_context_manager(".")
        manager2 = get_context_manager(".")

        # Should return the same instance
        assert manager1 is manager2

        # Different project should get different manager
        manager3 = get_context_manager("/tmp")
        assert manager1 is not manager3


class TestMissingFilenameKeyHandling:
    """Test that the contextual documentation handles missing keys gracefully."""

    def test_missing_filename_key_handling(self):
        """Test that missing filename keys don't break contextual analysis."""
        # This test ensures contextual documentation doesn't have the same
        # KeyError issue that was fixed in file_type_analyzer.py

        mock_config = Mock(spec=VibeCheckConfig)
        mock_config.context_loading.cache_duration_minutes = 60

        parser = ProjectDocumentationParser(mock_config)

        # Test with missing knowledge base (should not crash)
        with patch("pathlib.Path.exists", return_value=False):
            result = parser._load_integration_knowledge_base()
            assert isinstance(result, dict)
            assert result == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
