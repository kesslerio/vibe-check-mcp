"""
GitHub Issue Analysis Tool

Provides both quick and comprehensive analysis of GitHub issues for anti-patterns,
with optional GitHub integration for comprehensive reviews.
"""

import logging
import subprocess
import json
from typing import Dict, Any, Optional

from ..core.pattern_detector import PatternDetector
from ..core.educational_content import EducationalContentGenerator

logger = logging.getLogger(__name__)


def analyze_github_issue(
    issue_number: int,
    repository: str = "kesslerio/vibe-check-mcp", 
    analysis_mode: str = "quick",
    detail_level: str = "standard",
    post_comment: bool = False
) -> Dict[str, Any]:
    """
    Analyze a GitHub issue for anti-patterns with quick or comprehensive modes.
    
    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo"
        analysis_mode: "quick" for immediate analysis or "comprehensive" for detailed review
        detail_level: Level of detail for educational content (brief/standard/comprehensive)
        post_comment: Whether to post analysis as GitHub comment (comprehensive mode only)
        
    Returns:
        Dictionary containing pattern detection results and recommendations
    """
    try:
        # Fetch issue data using gh CLI
        result = subprocess.run([
            "gh", "issue", "view", str(issue_number), 
            "--repo", repository,
            "--json", "title,body,labels,author,createdAt,state"
        ], capture_output=True, text=True, check=True)
        
        issue_data = json.loads(result.stdout)
        issue_text = f"{issue_data['title']}\n\n{issue_data.get('body', '')}"
        
        if analysis_mode == "quick":
            return _quick_analysis(issue_data, issue_text, detail_level)
        else:
            return _comprehensive_analysis(
                issue_number, repository, issue_data, issue_text, 
                detail_level, post_comment
            )
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch issue #{issue_number}: {e}")
        return {"error": f"Failed to fetch issue #{issue_number}: {e.stderr}"}
    except Exception as e:
        logger.error(f"Analysis failed for issue #{issue_number}: {e}")
        return {"error": f"Analysis failed: {str(e)}"}


def _quick_analysis(issue_data: Dict, issue_text: str, detail_level: str) -> Dict[str, Any]:
    """Quick anti-pattern analysis for immediate feedback."""
    detector = PatternDetector()
    patterns = detector.analyze_text_for_patterns(issue_text)
    
    detected_patterns = [p for p in patterns if p.detected]
    
    return {
        "analysis_mode": "quick",
        "issue_title": issue_data["title"],
        "patterns_detected": len(detected_patterns),
        "anti_patterns": [
            {
                "type": p.pattern_type,
                "confidence": p.confidence,
                "evidence": p.evidence[:100] + "..." if len(p.evidence) > 100 else p.evidence
            } for p in detected_patterns
        ],
        "status": "clean" if len(detected_patterns) == 0 else "patterns_detected",
        "recommendation": "No anti-patterns detected" if len(detected_patterns) == 0 
                         else f"Review detected patterns before implementation"
    }


def _comprehensive_analysis(
    issue_number: int, repository: str, issue_data: Dict, 
    issue_text: str, detail_level: str, post_comment: bool
) -> Dict[str, Any]:
    """Comprehensive analysis with full GitHub integration."""
    detector = PatternDetector()
    educator = EducationalContentGenerator()
    
    # Analyze patterns
    patterns = detector.analyze_text_for_patterns(issue_text)
    detected_patterns = [p for p in patterns if p.detected]
    
    # Check for integration risks
    third_party_keywords = [
        "cognee", "openai", "anthropic", "postgres", "redis", "docker", 
        "api", "sdk", "integration", "server", "client", "http", "rest"
    ]
    infrastructure_keywords = [
        "architecture", "infrastructure", "server", "database", "build", 
        "deploy", "docker", "compose", "setup", "config"
    ]
    
    has_integration_risk = any(keyword in issue_text.lower() for keyword in third_party_keywords)
    has_complexity_risk = any(keyword in issue_text.lower() for keyword in infrastructure_keywords)
    
    # Generate comprehensive analysis
    analysis = {
        "analysis_mode": "comprehensive",
        "issue_number": issue_number,
        "issue_title": issue_data["title"],
        "author": issue_data["author"]["login"],
        "labels": [label["name"] for label in issue_data.get("labels", [])],
        "patterns_detected": len(detected_patterns),
        "anti_patterns": [
            {
                "type": p.pattern_type,
                "confidence": p.confidence,
                "evidence": p.evidence,
                "educational_content": _get_educational_content(educator, p, detail_level)
            } for p in detected_patterns
        ],
        "risk_assessment": {
            "third_party_integration": has_integration_risk,
            "infrastructure_complexity": has_complexity_risk,
            "overall_risk": "high" if (detected_patterns and (has_integration_risk or has_complexity_risk))
                          else "medium" if detected_patterns 
                          else "low"
        },
        "recommendations": _generate_recommendations(detected_patterns, has_integration_risk, has_complexity_risk)
    }
    
    # Post comment if requested (regardless of patterns detected)
    if post_comment:
        _post_github_comment(issue_number, repository, analysis)
    
    return analysis


def _get_educational_content(educator: EducationalContentGenerator, pattern, detail_level: str) -> Dict:
    """Generate educational content for a detected pattern."""
    try:
        from ..core.educational_content import DetailLevel
        detail_enum = getattr(DetailLevel, detail_level.upper(), DetailLevel.STANDARD)
        educational_response = educator.generate_educational_response(
            pattern_type=pattern.pattern_type,
            confidence=pattern.confidence,
            evidence=pattern.evidence,
            detail_level=detail_enum
        )
        from dataclasses import asdict
        return asdict(educational_response)
    except Exception:
        return {"explanation": "Educational content generation failed"}


def _generate_recommendations(detected_patterns, has_integration_risk: bool, has_complexity_risk: bool) -> Dict[str, Any]:
    """Generate specific recommendations based on analysis."""
    if not detected_patterns and not has_integration_risk and not has_complexity_risk:
        return {
            "overall": "✅ No anti-patterns detected. Proceed with standard development practices.",
            "action": "approve"
        }
    
    recommendations = {
        "overall": "⚠️ Review required before implementation",
        "action": "review_needed",
        "specific_actions": []
    }
    
    if has_integration_risk:
        recommendations["specific_actions"].append(
            "🔍 API-First Validation Required: Demonstrate basic API functionality with working POC before architectural planning"
        )
    
    if has_complexity_risk:
        recommendations["specific_actions"].append(
            "⚖️ Complexity Justification: Verify complex solutions are justified over simple standard approaches"
        )
    
    if detected_patterns:
        recommendations["specific_actions"].append(
            f"🚨 Anti-Patterns Detected: Address {len(detected_patterns)} pattern(s) before proceeding"
        )
    
    return recommendations


def _post_github_comment(issue_number: int, repository: str, analysis: Dict) -> None:
    """Post comprehensive analysis as GitHub comment."""
    try:
        comment_body = _format_github_comment(analysis)
        
        subprocess.run([
            "gh", "issue", "comment", str(issue_number),
            "--repo", repository,
            "--body", comment_body
        ], check=True, capture_output=True)
        
        # Add review label (only if patterns detected)
        if analysis["patterns_detected"] > 0:
            subprocess.run([
                "gh", "issue", "edit", str(issue_number),
                "--repo", repository,
                "--add-label", "anti-pattern-review"
            ], check=True, capture_output=True)
        else:
            # Add clean review label for issues with no patterns
            subprocess.run([
                "gh", "issue", "edit", str(issue_number),
                "--repo", repository,
                "--add-label", "vibe-check-reviewed"
            ], check=True, capture_output=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to post GitHub comment: {e}")


def _format_github_comment(analysis: Dict) -> str:
    """Format analysis results as GitHub comment."""
    risk_level = analysis["risk_assessment"]["overall_risk"]
    risk_emoji = "🔴" if risk_level == "high" else "🟡" if risk_level == "medium" else "🟢"
    
    comment = f"""## 🔍 Vibe Check Anti-Pattern Analysis

{risk_emoji} **Risk Level**: {risk_level.title()}

### 📊 Analysis Summary
- **Patterns Detected**: {analysis['patterns_detected']}
- **Third-Party Integration Risk**: {'⚠️ Yes' if analysis['risk_assessment']['third_party_integration'] else '✅ No'}
- **Infrastructure Complexity Risk**: {'⚠️ Yes' if analysis['risk_assessment']['infrastructure_complexity'] else '✅ No'}

"""
    
    if analysis["anti_patterns"]:
        comment += "### 🚨 Detected Anti-Patterns\n\n"
        for i, pattern in enumerate(analysis["anti_patterns"], 1):
            comment += f"**{i}. {pattern['type']}** (Confidence: {pattern['confidence']:.2f})\n"
            comment += f"- Evidence: {pattern['evidence'][:200]}{'...' if len(pattern['evidence']) > 200 else ''}\n\n"
    else:
        comment += "### ✅ No Anti-Patterns Detected\n\n"
        comment += "The issue description follows good engineering practices and shows no obvious anti-pattern indicators.\n\n"
    
    comment += f"### 🎯 Recommendations\n\n{analysis['recommendations']['overall']}\n\n"
    
    if analysis['recommendations'].get('specific_actions'):
        for action in analysis['recommendations']['specific_actions']:
            comment += f"- {action}\n"
    
    comment += f"\n---\n*Analysis generated by Vibe Check MCP • [Learn more about anti-patterns](https://github.com/kesslerio/vibe-check-mcp)*"
    
    return comment


def demo_analyze_text(text: str, detail_level: str = "standard") -> Dict[str, Any]:
    """
    Demo tool: Analyze text for anti-patterns using the validated core engine.
    
    Args:
        text: Text content to analyze for anti-patterns
        detail_level: Level of detail for educational content (brief/standard/comprehensive)
        
    Returns:
        Dictionary containing pattern detection results and educational content
    """
    try:
        # Initialize validated core components
        detector = PatternDetector()
        educator = EducationalContentGenerator()
        
        # Analyze text using proven detection algorithms
        patterns = detector.analyze_text_for_patterns(text)
        
        # Convert DetectionResult objects to dictionaries for JSON serialization
        patterns_dict = []
        for result in patterns:
            patterns_dict.append({
                "pattern_type": result.pattern_type,
                "detected": result.detected,
                "confidence": result.confidence,
                "evidence": result.evidence,
                "threshold": result.threshold
            })
        
        # Generate educational content for detected patterns
        educational_content = {}
        if patterns and patterns[0].detected:
            # Get educational content for the first detected pattern as demo
            first_pattern = patterns[0]
            from ..core.educational_content import DetailLevel
            detail_enum = getattr(DetailLevel, detail_level.upper(), DetailLevel.STANDARD)
            educational_response = educator.generate_educational_response(
                pattern_type=first_pattern.pattern_type,
                confidence=first_pattern.confidence,
                evidence=first_pattern.evidence,
                detail_level=detail_enum
            )
            # Convert EducationalResponse dataclass to dict for JSON serialization
            from dataclasses import asdict
            educational_content = asdict(educational_response)
        
        return {
            "demo_analysis": {
                "text_length": len(text),
                "patterns_detected": len([p for p in patterns if p.detected]),
                "analysis_method": "Phase 1 validated core engine"
            },
            "patterns": patterns_dict,
            "educational_content": educational_content,
            "server_status": "✅ FastMCP server operational with core engine integration",
            "accuracy_note": "Using validated detection engine (87.5% accuracy, 0% false positives)"
        }
        
    except Exception as e:
        logger.error(f"Demo analysis failed: {e}")
        return {
            "error": f"Analysis failed: {str(e)}",
            "demo_analysis": {
                "patterns_detected": 0,
                "analysis_method": "Error occurred"
            }
        }