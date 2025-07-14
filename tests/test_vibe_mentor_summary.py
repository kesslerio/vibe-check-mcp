"""
Unit tests for _generate_summary() function - the critical bug fix for issue #156.

Tests the core logic that was failing to report persona concerns when no patterns detected.
"""

import unittest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vibe_check.tools.vibe_mentor import _generate_summary


class TestGenerateSummary(unittest.TestCase):
    """Test the _generate_summary function that was fixed in issue #156."""
    
    def test_patterns_detected_infrastructure_type(self):
        """Test summary when infrastructure_without_implementation pattern detected."""
        patterns = [{"pattern_type": "infrastructure_without_implementation"}]
        result = _generate_summary("medium", patterns)
        self.assertEqual(result, "Consider using official SDK instead of custom implementation")
    
    def test_patterns_detected_custom_type(self):
        """Test summary when custom-related patterns detected."""
        patterns = [{"pattern_type": "custom_solution_without_research"}]
        result = _generate_summary("medium", patterns)
        self.assertEqual(result, "Explore standard solutions before building custom")
    
    def test_patterns_detected_other_type(self):
        """Test summary when other pattern types detected."""
        patterns = [{"pattern_type": "complexity_escalation"}]
        result = _generate_summary("medium", patterns)
        self.assertEqual(result, "Some patterns detected - check recommendations below")
    
    def test_no_patterns_but_persona_concerns(self):
        """Test the critical bug fix: personas have concerns but no patterns detected."""
        synthesis = {
            "primary_concerns": [
                "Senior engineer concerned about approach",
                "Product manager questions necessity"
            ],
            "consensus_points": []
        }
        result = _generate_summary("medium", [], synthesis)
        self.assertEqual(result, "Engineering team has concerns - review collaborative insights")
    
    def test_no_patterns_but_consensus_concerns(self):
        """Test personas identify concerns through consensus points."""
        synthesis = {
            "primary_concerns": [],
            "consensus_points": [
                "Team consensus: this approach has risks",
                "Avoid custom solutions when APIs exist"
            ]
        }
        result = _generate_summary("medium", [], synthesis)
        self.assertEqual(result, "Engineering team has concerns - review collaborative insights")
    
    def test_no_patterns_no_concerns(self):
        """Test clean state: no patterns, no persona concerns."""
        synthesis = {
            "primary_concerns": [],
            "consensus_points": ["Approach looks solid", "Good architecture choice"]
        }
        result = _generate_summary("medium", [], synthesis)
        self.assertEqual(result, "No concerning patterns detected - looking good!")
    
    def test_no_patterns_no_synthesis(self):
        """Test with no patterns and no synthesis data."""
        result = _generate_summary("medium", [])
        self.assertEqual(result, "No concerning patterns detected - looking good!")
    
    def test_patterns_override_persona_concerns(self):
        """Test that detected patterns take precedence over persona concerns."""
        patterns = [{"pattern_type": "infrastructure_without_implementation"}]
        synthesis = {
            "primary_concerns": ["Some concern"],
            "consensus_points": []
        }
        result = _generate_summary("medium", patterns, synthesis)
        self.assertEqual(result, "Consider using official SDK instead of custom implementation")
    
    def test_concern_indicator_detection(self):
        """Test that concern indicators in consensus are properly detected."""
        test_cases = [
            "avoid this approach",
            "concern about scalability", 
            "risk of overengineering",
            "problem with implementation",
            "issue with architecture",
            "anti-pattern detected"
        ]
        
        for concern_text in test_cases:
            synthesis = {
                "primary_concerns": [],
                "consensus_points": [concern_text]
            }
            result = _generate_summary("medium", [], synthesis)
            self.assertEqual(result, "Engineering team has concerns - review collaborative insights")
    
    def test_case_insensitive_concern_detection(self):
        """Test that concern indicators work regardless of case."""
        synthesis = {
            "primary_concerns": [],
            "consensus_points": ["AVOID this ANTI-PATTERN approach"]
        }
        result = _generate_summary("medium", [], synthesis)
        self.assertEqual(result, "Engineering team has concerns - review collaborative insights")


if __name__ == "__main__":
    unittest.main()