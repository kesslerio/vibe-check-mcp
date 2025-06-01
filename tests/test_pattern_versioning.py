#!/usr/bin/env python3
"""
Tests for pattern versioning functionality

Tests version metadata handling, backward compatibility, and version utilities
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

# Import components under test
from src.vibe_check.core.pattern_detector import PatternDetector, DetectionResult
from src.vibe_check.utils.version_utils import (
    parse_semantic_version,
    compare_versions,
    is_compatible_version,
    get_migration_path
)
from validation.detect_patterns import PatternDetector as ValidationPatternDetector


class TestVersionUtilities:
    """Test version utility functions"""
    
    def test_parse_semantic_version(self):
        """Test semantic version parsing"""
        # Valid versions
        assert parse_semantic_version("1.0.0") == (1, 0, 0)
        assert parse_semantic_version("2.5.3") == (2, 5, 3)
        assert parse_semantic_version("10.20.30") == (10, 20, 30)
        
        # Invalid versions
        with pytest.raises(ValueError):
            parse_semantic_version("1.0")
        
        with pytest.raises(ValueError):
            parse_semantic_version("1.0.0.1")
        
        with pytest.raises(ValueError):
            parse_semantic_version("v1.0.0")
    
    def test_compare_versions(self):
        """Test version comparison"""
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.0.1", "1.0.0") == 1
        assert compare_versions("2.0.0", "1.9.9") == 1
        assert compare_versions("1.9.9", "2.0.0") == -1
    
    def test_is_compatible_version(self):
        """Test version compatibility checking"""
        # Major compatibility
        assert is_compatible_version("1.2.3", "1.0.0", "major") == True
        assert is_compatible_version("2.0.0", "1.0.0", "major") == False
        
        # Minor compatibility
        assert is_compatible_version("1.2.0", "1.1.0", "minor") == True
        assert is_compatible_version("1.1.0", "1.2.0", "minor") == False
        assert is_compatible_version("2.0.0", "1.9.0", "minor") == False
        
        # Patch compatibility
        assert is_compatible_version("1.0.2", "1.0.1", "patch") == True
        assert is_compatible_version("1.0.1", "1.0.2", "patch") == False
    
    def test_get_migration_path(self):
        """Test migration path generation"""
        # No migration needed
        assert get_migration_path("1.0.0", "1.0.0") is None
        
        # Major upgrade
        result = get_migration_path("1.0.0", "2.0.0")
        assert "Major version upgrade required" in result
        
        # Minor upgrade
        result = get_migration_path("1.0.0", "1.1.0")
        assert "Minor version upgrade" in result
        
        # Patch upgrade
        result = get_migration_path("1.0.0", "1.0.1")
        assert "Patch version upgrade" in result
        
        # Downgrade
        result = get_migration_path("1.1.0", "1.0.0")
        assert "Version downgrade" in result


class TestPatternVersioning:
    """Test pattern versioning in detection systems"""
    
    @pytest.fixture
    def sample_pattern_data(self) -> Dict[str, Any]:
        """Sample pattern data with versioning"""
        return {
            "schema_version": "1.1.0",
            "data_version": "1.0.0",
            "test_pattern": {
                "id": "test_pattern",
                "version": "1.0.0",
                "name": "Test Pattern",
                "description": "A test pattern for validation",
                "severity": "medium",
                "category": "process",
                "detection_threshold": 0.5,
                "indicators": [
                    {
                        "regex": "test pattern",
                        "description": "test indicator",
                        "weight": 0.6,
                        "text": "test"
                    }
                ]
            }
        }
    
    def test_validation_detector_versioning(self, tmp_path, sample_pattern_data):
        """Test versioning in validation pattern detector"""
        # Create temporary pattern file
        pattern_file = tmp_path / "test_patterns.json"
        with open(pattern_file, 'w') as f:
            json.dump(sample_pattern_data, f)
        
        # Initialize detector
        detector = ValidationPatternDetector(str(pattern_file))
        
        # Test version extraction
        version_info = detector.get_version_info()
        assert version_info["schema_version"] == "1.1.0"
        assert version_info["data_version"] == "1.0.0"
        
        # Test pattern extraction (should exclude version fields)
        assert "schema_version" not in detector.patterns
        assert "data_version" not in detector.patterns
        assert "test_pattern" in detector.patterns
    
    def test_core_detector_versioning(self, tmp_path, sample_pattern_data):
        """Test versioning in core pattern detector"""
        # Create temporary pattern file
        pattern_file = tmp_path / "test_patterns.json"
        with open(pattern_file, 'w') as f:
            json.dump(sample_pattern_data, f)
        
        # Create minimal case studies file
        case_studies_file = tmp_path / "test_case_studies.json"
        with open(case_studies_file, 'w') as f:
            json.dump({}, f)
        
        # Initialize detector
        detector = PatternDetector(str(pattern_file), str(case_studies_file))
        
        # Test version extraction
        version_info = detector.get_version_info()
        assert version_info["schema_version"] == "1.1.0"
        assert version_info["data_version"] == "1.0.0"
        
        # Test pattern extraction
        assert "test_pattern" in detector.patterns
        assert detector.patterns["test_pattern"]["version"] == "1.0.0"
    
    def test_detection_result_versioning(self, tmp_path, sample_pattern_data):
        """Test that detection results include pattern version"""
        # Create temporary files
        pattern_file = tmp_path / "test_patterns.json"
        with open(pattern_file, 'w') as f:
            json.dump(sample_pattern_data, f)
        
        # Test validation detector
        detector = ValidationPatternDetector(str(pattern_file))
        result = detector._detect_single_pattern(
            "test pattern content", 
            "context",
            sample_pattern_data["test_pattern"]
        )
        
        assert "pattern_version" in result
        assert result["pattern_version"] == "1.0.0"
    
    def test_backward_compatibility(self, tmp_path):
        """Test backward compatibility with patterns without version fields"""
        # Pattern data without version fields
        legacy_pattern_data = {
            "legacy_pattern": {
                "id": "legacy_pattern",
                "name": "Legacy Pattern",
                "description": "A pattern without version fields",
                "detection_threshold": 0.5,
                "indicators": [
                    {
                        "regex": "legacy",
                        "description": "legacy indicator",
                        "weight": 0.6,
                        "text": "legacy"
                    }
                ]
            }
        }
        
        # Create temporary pattern file
        pattern_file = tmp_path / "legacy_patterns.json"
        with open(pattern_file, 'w') as f:
            json.dump(legacy_pattern_data, f)
        
        # Initialize detector
        detector = ValidationPatternDetector(str(pattern_file))
        
        # Test default version handling
        version_info = detector.get_version_info()
        assert version_info["schema_version"] == "1.0.0"  # Default
        assert version_info["data_version"] == "1.0.0"    # Default
        
        # Test detection still works
        result = detector._detect_single_pattern(
            "legacy content",
            "",
            legacy_pattern_data["legacy_pattern"]
        )
        
        assert result["pattern_version"] == "1.0.0"  # Default


class TestSchemaValidation:
    """Test schema validation with versioning"""
    
    def test_schema_version_validation(self):
        """Test that schema validates version formats"""
        # Load actual schema
        schema_file = Path(__file__).parent.parent / "data" / "pattern_schema.json"
        with open(schema_file) as f:
            schema = json.load(f)
        
        # Verify version field definitions exist
        assert "schema_version" in schema["properties"]
        assert "data_version" in schema["properties"]
        
        # Verify version pattern validation
        version_pattern = schema["properties"]["schema_version"]["pattern"]
        assert version_pattern == "^\\d+\\.\\d+\\.\\d+$"
    
    def test_pattern_schema_versioning(self):
        """Test that pattern definitions include version fields"""
        # Load actual schema
        schema_file = Path(__file__).parent.parent / "data" / "pattern_schema.json"
        with open(schema_file) as f:
            schema = json.load(f)
        
        # Get pattern property schema
        pattern_schemas = list(schema["patternProperties"].values())
        assert len(pattern_schemas) > 0
        
        pattern_schema = pattern_schemas[0]
        
        # Verify version field exists in pattern schema
        assert "version" in pattern_schema["properties"]
        assert pattern_schema["properties"]["version"]["default"] == "1.0.0"


class TestActualPatternData:
    """Test the actual pattern data files"""
    
    def test_actual_pattern_file_versioning(self):
        """Test that actual anti_patterns.json has versioning"""
        pattern_file = Path(__file__).parent.parent / "data" / "anti_patterns.json"
        
        with open(pattern_file) as f:
            pattern_data = json.load(f)
        
        # Verify global version fields exist
        assert "schema_version" in pattern_data
        assert "data_version" in pattern_data
        
        # Verify version format
        schema_version = pattern_data["schema_version"]
        data_version = pattern_data["data_version"]
        
        # Should parse without error
        parse_semantic_version(schema_version)
        parse_semantic_version(data_version)
        
        # Verify pattern-level versions
        for pattern_id, pattern_config in pattern_data.items():
            if pattern_id not in ["schema_version", "data_version"]:
                assert "version" in pattern_config
                parse_semantic_version(pattern_config["version"])
    
    def test_detector_with_actual_data(self):
        """Test detectors work with actual versioned data"""
        # Test validation detector
        validation_detector = ValidationPatternDetector()
        version_info = validation_detector.get_version_info()
        
        assert "schema_version" in version_info
        assert "data_version" in version_info
        
        # Test actual detection works (use text more likely to trigger)
        result = validation_detector.detect_infrastructure_without_implementation(
            "I'll implement our own custom HTTP client since their SDK might be limiting"
        )
        
        assert "pattern_version" in result
        # Just verify the field exists, detection depends on exact patterns


@pytest.mark.integration
class TestVersioningIntegration:
    """Integration tests for versioning functionality"""
    
    def test_end_to_end_versioning(self):
        """Test complete versioning workflow"""
        # Load actual pattern detector
        detector = ValidationPatternDetector()
        
        # Get version info
        version_info = detector.get_version_info()
        assert version_info["schema_version"] is not None
        assert version_info["data_version"] is not None
        
        # Run detection (use text that should trigger pattern)
        test_text = "I'll create our own custom implementation instead of testing the standard approach"
        result = detector.detect_infrastructure_without_implementation(test_text)
        
        # Verify result includes version information
        assert "pattern_version" in result
        assert result["pattern_version"] is not None
        
        # Verify version format
        parse_semantic_version(result["pattern_version"])
    
    def test_version_compatibility_check(self):
        """Test version compatibility checking"""
        detector = ValidationPatternDetector()
        version_info = detector.get_version_info()
        
        # Test schema compatibility
        current_schema = version_info["schema_version"]
        assert is_compatible_version(current_schema, "1.0.0", "major")
        
        # Test data compatibility
        current_data = version_info["data_version"]
        assert is_compatible_version(current_data, "1.0.0", "major")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])