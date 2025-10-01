"""
Pattern Definition Validator

Validates anti-pattern definitions against the JSON schema to ensure
consistency and correctness.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

try:
    from jsonschema import validate, ValidationError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class PatternValidator:
    """Validates pattern definitions against schema"""

    def __init__(self, schema_path: str = None):
        """
        Initialize validator with schema

        Args:
            schema_path: Path to JSON schema file. If None, uses default schema.
        """
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError(
                "jsonschema library not available. Install with: pip install jsonschema"
            )

        if schema_path is None:
            # Default to schema in data directory
            current_dir = Path(__file__).parent
            schema_path = (
                current_dir.parent.parent.parent / "data" / "pattern_schema.json"
            )

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file"""
        try:
            with open(self.schema_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")

    def validate_patterns(self, patterns: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate pattern definitions against schema

        Args:
            patterns: Dictionary of pattern definitions

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            validate(patterns, self.schema)
            return True, []
        except ValidationError as e:
            error_msg = f"Validation error at {'.'.join(str(p) for p in e.absolute_path)}: {e.message}"
            return False, [error_msg]
        except Exception as e:
            return False, [f"Unexpected validation error: {str(e)}"]

    def validate_pattern_file(self, patterns_path: str) -> Tuple[bool, List[str]]:
        """
        Validate pattern file against schema

        Args:
            patterns_path: Path to patterns JSON file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            with open(patterns_path, "r") as f:
                patterns = json.load(f)
            return self.validate_patterns(patterns)
        except FileNotFoundError:
            return False, [f"Pattern file not found: {patterns_path}"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON in pattern file: {e}"]

    def validate_single_pattern(
        self, pattern_id: str, pattern_def: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate a single pattern definition

        Args:
            pattern_id: Pattern identifier
            pattern_def: Pattern definition dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Create a temporary patterns dict for validation
        temp_patterns = {pattern_id: pattern_def}
        return self.validate_patterns(temp_patterns)

    def get_pattern_summary(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary information about patterns

        Args:
            patterns: Dictionary of pattern definitions

        Returns:
            Summary dictionary with statistics
        """
        if not patterns:
            return {"total_patterns": 0}

        summary = {
            "total_patterns": len(patterns),
            "severities": {},
            "categories": {},
            "indicator_counts": {},
            "threshold_distribution": [],
        }

        for pattern_id, pattern in patterns.items():
            # Count severities
            severity = pattern.get("severity", "medium")
            summary["severities"][severity] = summary["severities"].get(severity, 0) + 1

            # Count categories
            category = pattern.get("category", "process")
            summary["categories"][category] = summary["categories"].get(category, 0) + 1

            # Count indicators
            indicator_count = len(pattern.get("indicators", []))
            neg_indicator_count = len(pattern.get("negative_indicators", []))
            summary["indicator_counts"][pattern_id] = {
                "positive": indicator_count,
                "negative": neg_indicator_count,
                "total": indicator_count + neg_indicator_count,
            }

            # Threshold distribution
            threshold = pattern.get("detection_threshold", 0.5)
            summary["threshold_distribution"].append(
                {"pattern": pattern_id, "threshold": threshold}
            )

        return summary


def validate_default_patterns() -> None:
    """
    Validate the default anti_patterns.json file
    Prints results to console
    """
    try:
        validator = PatternValidator()
        current_dir = Path(__file__).parent
        patterns_path = current_dir.parent.parent.parent / "data" / "anti_patterns.json"

        is_valid, errors = validator.validate_pattern_file(str(patterns_path))

        if is_valid:
            print("✅ Pattern validation passed successfully!")

            # Load patterns for summary
            with open(patterns_path, "r") as f:
                patterns = json.load(f)

            summary = validator.get_pattern_summary(patterns)
            print(f"📊 Validated {summary['total_patterns']} patterns")
            print(f"   Severities: {summary['severities']}")
            print(f"   Categories: {summary['categories']}")

        else:
            print("❌ Pattern validation failed:")
            for error in errors:
                print(f"   - {error}")

    except Exception as e:
        print(f"❌ Error during validation: {e}")


if __name__ == "__main__":
    validate_default_patterns()
