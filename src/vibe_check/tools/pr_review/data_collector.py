"""
PR Data Collection Module

Handles comprehensive PR data collection using GitHub CLI and API.
Extracted from pr_review.py to improve modularity.
"""

import json
import logging
import re
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PRDataCollector:
    """Handles comprehensive PR data collection and linked issue analysis."""
    
    def collect_pr_data(self, pr_number: int, repository: str) -> Dict[str, Any]:
        """
        Collect comprehensive PR data using GitHub CLI.
        Replaces lines 121-184 of original pr_review.py.
        """
        try:
            # Get comprehensive PR information
            pr_result = subprocess.run([
                "gh", "pr", "view", str(pr_number),
                "--repo", repository,
                "--json", "title,body,files,additions,deletions,author,createdAt,baseRefName,headRefName,comments"
            ], capture_output=True, text=True, check=True)
            
            pr_info = json.loads(pr_result.stdout)
            
            # Get PR diff
            diff_result = subprocess.run([
                "gh", "pr", "diff", str(pr_number),
                "--repo", repository
            ], capture_output=True, text=True, timeout=15)
            
            pr_diff = diff_result.stdout if diff_result.returncode == 0 else ""
            
            # Extract linked issues from PR body
            linked_issues = self.extract_linked_issues(pr_info.get("body", ""), repository)
            
            # Build comprehensive data structure
            pr_data = {
                "metadata": {
                    "number": pr_number,
                    "title": pr_info["title"],
                    "body": pr_info.get("body", ""),
                    "author": pr_info["author"]["login"],
                    "created_at": pr_info["createdAt"],
                    "base_branch": pr_info["baseRefName"],
                    "head_branch": pr_info["headRefName"]
                },
                "statistics": {
                    "files_count": len(pr_info.get("files", [])),
                    "additions": pr_info.get("additions", 0),
                    "deletions": pr_info.get("deletions", 0),
                    "total_changes": pr_info.get("additions", 0) + pr_info.get("deletions", 0)
                },
                "files": pr_info.get("files", []),
                "diff": pr_diff,
                "comments": pr_info.get("comments", []),
                "linked_issues": linked_issues
            }
            
            logger.info(f"📊 PR data collected: {pr_data['statistics']['files_count']} files, "
                       f"+{pr_data['statistics']['additions']}/-{pr_data['statistics']['deletions']} lines")
            
            return pr_data
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to fetch PR #{pr_number}: {e}")
            return {"error": f"Failed to fetch PR #{pr_number}: {e.stderr}"}
        except Exception as e:
            logger.error(f"PR data collection failed: {e}")
            return {"error": f"Failed to collect PR data: {str(e)}"}
    
    def extract_linked_issues(self, pr_body: str, repository: str) -> List[Dict[str, Any]]:
        """Extract and analyze linked issues from PR body."""
        try:
            # Extract issue numbers from PR body using same pattern as review-pr.sh
            issue_pattern = r"(Fixes|Closes|Resolves)\s+#(\d+)"
            matches = re.findall(issue_pattern, pr_body, re.IGNORECASE)
            
            linked_issues = []
            for action, issue_num in matches:
                try:
                    # Get issue details
                    issue_result = subprocess.run([
                        "gh", "issue", "view", issue_num,
                        "--repo", repository,
                        "--json", "title,body,labels,state"
                    ], capture_output=True, text=True, check=True)
                    
                    issue_data = json.loads(issue_result.stdout)
                    linked_issues.append({
                        "number": int(issue_num),
                        "action": action,
                        "title": issue_data["title"],
                        "body": issue_data.get("body", ""),
                        "labels": [label["name"] for label in issue_data.get("labels", [])],
                        "state": issue_data["state"]
                    })
                    
                except subprocess.CalledProcessError:
                    logger.warning(f"Could not fetch issue #{issue_num}")
                    linked_issues.append({
                        "number": int(issue_num),
                        "action": action,
                        "error": "Issue not found or inaccessible"
                    })
            
            return linked_issues
            
        except Exception as e:
            logger.error(f"Failed to extract linked issues: {e}")
            return []