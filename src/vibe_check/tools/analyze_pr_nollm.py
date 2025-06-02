"""
Direct PR Analysis Tool (No-LLM)

Provides fast PR analysis using direct pattern detection, metrics calculation,
and GitHub API data without LLM reasoning. For comprehensive LLM-powered 
analysis, use analyze_pr_llm instead.

This combines the functionality from the modular pr_review/ components
into a single file for direct analysis.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

# GitHub integration
try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

from ..core.pattern_detector import PatternDetector

logger = logging.getLogger(__name__)


def analyze_pr_nollm(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    analysis_mode: str = "quick",
    detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    Direct PR analysis using pattern detection and metrics (no LLM calls).
    
    Fast analysis that provides:
    - PR size classification and metrics
    - Basic anti-pattern detection
    - Issue linkage validation
    - File change analysis
    - Direct GitHub API data
    
    For comprehensive LLM-powered analysis, use analyze_pr_llm instead.
    
    Args:
        pr_number: PR number to analyze
        repository: Repository in format "owner/repo"
        analysis_mode: "quick" for basic analysis
        detail_level: "brief", "standard", or "comprehensive"
        
    Returns:
        Direct analysis results without LLM reasoning
    """
    if not GITHUB_AVAILABLE:
        return {
            "success": False,
            "error": "GitHub library not available. Install with: pip install PyGithub",
            "tool_type": "analyze_pr_nollm"
        }
    
    try:
        logger.info(f"🚀 Starting direct PR analysis for PR #{pr_number}")
        
        # Initialize GitHub client
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return {
                "success": False,
                "error": "GITHUB_TOKEN environment variable required",
                "tool_type": "analyze_pr_nollm"
            }
        
        github_client = Github(github_token)
        
        # Parse repository
        owner, repo_name = repository.split("/")
        repo = github_client.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Collect basic PR data
        pr_data = {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body or "",
            "state": pr.state,
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat(),
            "mergeable": pr.mergeable,
            "mergeable_state": pr.mergeable_state,
            "commits": pr.commits,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files
        }
        
        # Calculate PR size classification
        size_metrics = _calculate_pr_size(pr_data)
        
        # Analyze file changes
        files_analysis = _analyze_file_changes(pr)
        
        # Check issue linkage
        issue_linkage = _check_issue_linkage(pr_data["body"], pr_data["title"])
        
        # Basic anti-pattern detection
        patterns_detected = _detect_basic_patterns(pr_data, files_analysis)
        
        # Build analysis result
        analysis_result = {
            "success": True,
            "tool_type": "analyze_pr_nollm",
            "analysis_mode": analysis_mode,
            "detail_level": detail_level,
            "pr_data": pr_data,
            "size_classification": size_metrics,
            "files_analysis": files_analysis,
            "issue_linkage": issue_linkage,
            "patterns_detected": patterns_detected,
            "recommendations": _generate_basic_recommendations(
                size_metrics, issue_linkage, patterns_detected
            ),
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Direct PR analysis completed for PR #{pr_number}")
        return analysis_result
        
    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        return {
            "success": False,
            "error": f"GitHub API error: {e}",
            "tool_type": "analyze_pr_nollm"
        }
    except Exception as e:
        logger.error(f"PR analysis error: {e}")
        return {
            "success": False,
            "error": f"Analysis error: {e}",
            "tool_type": "analyze_pr_nollm"
        }


def _calculate_pr_size(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate PR size classification based on metrics."""
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)
    changed_files = pr_data.get("changed_files", 0)
    commits = pr_data.get("commits", 0)
    
    total_changes = additions + deletions
    
    # Size classification logic
    if total_changes <= 50 and changed_files <= 3:
        size = "XS"
        complexity = "Very Low"
    elif total_changes <= 200 and changed_files <= 10:
        size = "S"
        complexity = "Low"
    elif total_changes <= 500 and changed_files <= 20:
        size = "M"
        complexity = "Medium"
    elif total_changes <= 1000 and changed_files <= 40:
        size = "L"
        complexity = "High"
    else:
        size = "XL"
        complexity = "Very High"
    
    return {
        "size": size,
        "complexity": complexity,
        "total_changes": total_changes,
        "additions": additions,
        "deletions": deletions,
        "changed_files": changed_files,
        "commits": commits,
        "changes_per_commit": round(total_changes / max(commits, 1), 2)
    }


def _analyze_file_changes(pr) -> Dict[str, Any]:
    """Analyze the files changed in the PR."""
    try:
        files = pr.get_files()
        
        file_types = {}
        risk_files = []
        large_files = []
        
        for file in files:
            # Categorize by file extension
            if '.' in file.filename:
                ext = file.filename.split('.')[-1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            # Check for risky file patterns
            if any(pattern in file.filename.lower() for pattern in [
                'config', 'secret', 'key', 'password', 'token', 'env'
            ]):
                risk_files.append(file.filename)
            
            # Check for large file changes
            if file.changes > 100:
                large_files.append({
                    "filename": file.filename,
                    "changes": file.changes,
                    "additions": file.additions,
                    "deletions": file.deletions
                })
        
        return {
            "file_types": file_types,
            "risk_files": risk_files,
            "large_files": large_files,
            "total_files": len(list(files))
        }
        
    except Exception as e:
        logger.warning(f"Could not analyze file changes: {e}")
        return {"error": f"File analysis failed: {e}"}


def _check_issue_linkage(body: str, title: str) -> Dict[str, Any]:
    """Check if PR is properly linked to issues."""
    import re
    
    # Common issue linking patterns
    issue_patterns = [
        r'(?:fixes|resolves|closes|addresses)\s+#(\d+)',
        r'(?:fixes|resolves|closes|addresses)\s+(?:issue\s+)?#(\d+)',
        r'#(\d+)',
        r'issue\s+(\d+)'
    ]
    
    linked_issues = set()
    content = f"{title} {body}".lower()
    
    for pattern in issue_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        linked_issues.update(matches)
    
    return {
        "has_issue_links": len(linked_issues) > 0,
        "linked_issues": list(linked_issues),
        "linking_keywords_found": any(
            keyword in content for keyword in ['fixes', 'resolves', 'closes', 'addresses']
        )
    }


def _detect_basic_patterns(pr_data: Dict[str, Any], files_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Detect basic anti-patterns without LLM analysis."""
    patterns = []
    
    # Large PR pattern
    if pr_data.get("changed_files", 0) > 20:
        patterns.append({
            "pattern": "Large PR",
            "severity": "medium",
            "description": f"PR changes {pr_data.get('changed_files')} files. Consider splitting into smaller PRs."
        })
    
    # Too many commits pattern  
    if pr_data.get("commits", 0) > 10:
        patterns.append({
            "pattern": "Too Many Commits",
            "severity": "low", 
            "description": f"PR has {pr_data.get('commits')} commits. Consider squashing related commits."
        })
    
    # Missing description pattern
    if not pr_data.get("body") or len(pr_data.get("body", "").strip()) < 10:
        patterns.append({
            "pattern": "Missing Description",
            "severity": "medium",
            "description": "PR lacks a meaningful description. Add context about the changes."
        })
    
    # Risk files pattern
    if files_analysis.get("risk_files"):
        patterns.append({
            "pattern": "Sensitive Files",
            "severity": "high",
            "description": f"PR modifies sensitive files: {files_analysis['risk_files']}"
        })
    
    return {
        "patterns_found": len(patterns),
        "patterns": patterns,
        "highest_severity": _get_highest_severity(patterns)
    }


def _get_highest_severity(patterns: list) -> str:
    """Get the highest severity level from detected patterns."""
    if not patterns:
        return "none"
    
    severity_order = {"high": 3, "medium": 2, "low": 1, "none": 0}
    max_severity = max(pattern.get("severity", "none") for pattern in patterns)
    return max_severity


def _generate_basic_recommendations(
    size_metrics: Dict[str, Any], 
    issue_linkage: Dict[str, Any], 
    patterns: Dict[str, Any]
) -> list:
    """Generate basic recommendations based on analysis."""
    recommendations = []
    
    # Size-based recommendations
    if size_metrics["size"] in ["L", "XL"]:
        recommendations.append({
            "type": "size",
            "priority": "medium",
            "message": f"Large PR ({size_metrics['size']}). Consider splitting into smaller, focused changes."
        })
    
    # Issue linkage recommendations
    if not issue_linkage["has_issue_links"]:
        recommendations.append({
            "type": "process",
            "priority": "medium", 
            "message": "PR should reference related issues using 'Fixes #123' format."
        })
    
    # Pattern-based recommendations
    if patterns["highest_severity"] == "high":
        recommendations.append({
            "type": "risk",
            "priority": "high",
            "message": "High-risk patterns detected. Review carefully before merging."
        })
    
    if not recommendations:
        recommendations.append({
            "type": "positive",
            "priority": "info",
            "message": "PR looks good from basic analysis perspective!"
        })
    
    return recommendations