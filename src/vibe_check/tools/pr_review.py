"""
Comprehensive PR Review MCP Tool

Replicates ALL functionality from scripts/review-pr.sh as a native MCP tool.
Provides enterprise-grade PR review with multi-dimensional analysis,
re-review tracking, and comprehensive GitHub integration.

Features:
- Multi-dimensional PR size classification
- Intelligent review strategies based on complexity
- Re-review detection and progress tracking
- Linked issue analysis and validation
- Clear-Thought integration for systematic analysis
- Fallback analysis capabilities
- Permanent logging and GitHub integration
"""

import logging
import re
import subprocess
import json
import time
import select
import sys
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Import Claude CLI debug/verbose config
from ..utils import CLAUDE_CLI_DEBUG, CLAUDE_CLI_VERBOSE

# Import external Claude CLI integration
from .external_claude_cli import ExternalClaudeCli

logger = logging.getLogger(__name__)


class PRReviewTool:
    """
    Comprehensive PR review tool that replicates review-pr.sh functionality.
    
    Provides enterprise-grade analysis with:
    - Multi-dimensional size classification
    - Re-review detection and tracking
    - Linked issue validation
    - Clear-Thought systematic analysis
    - GitHub integration for comments and labels
    """
    
    def __init__(self):
        self.reviews_dir = Path("reviews/pr-reviews")
        self.reviews_dir.mkdir(parents=True, exist_ok=True)
        self.claude_cmd = None  # Store detected Claude command path (legacy)
        
        # Initialize external Claude CLI integration
        self.external_claude = ExternalClaudeCli(timeout_seconds=300)  # 5 min timeout for complex PRs
        
    async def review_pull_request(
        self,
        pr_number: int,
        repository: str = "kesslerio/vibe-check-mcp",
        force_re_review: bool = False,
        analysis_mode: str = "comprehensive",
        detail_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Comprehensive PR review with all review-pr.sh functionality.
        
        Args:
            pr_number: PR number to review
            repository: Repository in format "owner/repo"
            force_re_review: Force re-review mode even if not auto-detected
            analysis_mode: "comprehensive" or "quick" analysis
            detail_level: "brief", "standard", or "comprehensive"
            
        Returns:
            Complete analysis results with GitHub integration status
        """
        try:
            logger.info(f"🤖 Starting comprehensive review for PR #{pr_number}")
            
            # Phase 1: Data Collection (replaces lines 62-258 of review-pr.sh)
            pr_data = self._collect_pr_data(pr_number, repository)
            if "error" in pr_data:
                return pr_data
                
            # Phase 2: Size Classification (replaces lines 87-202)
            size_analysis = self._classify_pr_size(pr_data)
            
            # Phase 3: Re-review Detection (replaces lines 212-228)
            review_context = self._detect_re_review(pr_data, force_re_review)
            
            # Phase 4: Analysis Generation (replaces lines 260-572)
            analysis_result = await self._generate_comprehensive_analysis(
                pr_data, size_analysis, review_context, analysis_mode, detail_level
            )
            
            # Phase 5: GitHub Integration (replaces lines 670-731)
            github_result = self._post_review_to_github(
                pr_number, repository, analysis_result, review_context
            )
            
            # Phase 6: Permanent Logging
            log_result = self._save_permanent_log(
                pr_number, analysis_result, review_context
            )
            
            return {
                "pr_number": pr_number,
                "analysis": analysis_result,
                "github_integration": github_result,
                "logging": log_result,
                "review_context": review_context
            }
            
        except Exception as e:
            logger.error(f"PR review failed for #{pr_number}: {e}")
            return {"error": f"PR review failed: {str(e)}"}
    
    def _collect_pr_data(self, pr_number: int, repository: str) -> Dict[str, Any]:
        """
        Collect comprehensive PR data using GitHub MCP tools.
        Replaces lines 62-258 of review-pr.sh.
        """
        try:
            # Since we're in the MCP tool context, we need to import the MCP functions
            # For now, we'll use subprocess to call gh CLI as in the original script
            # This can be replaced with actual MCP tool calls when integrated
            
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
            linked_issues = self._extract_linked_issues(pr_info.get("body", ""), repository)
            
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
    
    def _extract_linked_issues(self, pr_body: str, repository: str) -> List[Dict[str, Any]]:
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
    
    def _classify_pr_size(self, pr_data: Dict) -> Dict[str, Any]:
        """
        Multi-dimensional PR size classification.
        Replaces lines 87-202 of review-pr.sh.
        """
        stats = pr_data["statistics"]
        total_changes = stats["total_changes"]
        files_count = stats["files_count"]
        
        # Line-based classification
        if total_changes <= 500:
            size_by_lines = "SMALL"
        elif total_changes <= 1500:
            size_by_lines = "MEDIUM"
        elif total_changes <= 5000:
            size_by_lines = "LARGE"
        else:
            size_by_lines = "VERY_LARGE"
            
        # File-based classification
        if files_count <= 3:
            size_by_files = "SMALL"
        elif files_count <= 8:
            size_by_files = "MEDIUM"
        elif files_count <= 20:
            size_by_files = "LARGE"
        else:
            size_by_files = "VERY_LARGE"
            
        # Character-based classification (from diff size)
        # Special handling for test PRs - they're legitimate large files
        diff_size = len(pr_data.get("diff", ""))
        files = pr_data.get("files", [])
        is_test_pr = any("test" in f.get("path", "").lower() for f in files) and len([f for f in files if "test" in f.get("path", "").lower()]) / len(files) > 0.5
        
        if is_test_pr:
            # Test PRs: More lenient thresholds (tests are verbose but simple)
            if diff_size > 300000:  # 300k instead of 100k
                size_by_chars = "VERY_LARGE"
            elif diff_size > 100000:  # 100k instead of 50k
                size_by_chars = "LARGE"
            else:
                size_by_chars = "SMALL"
        else:
            # Regular PRs: Original thresholds
            if diff_size > 100000:
                size_by_chars = "VERY_LARGE"
            elif diff_size > 50000:
                size_by_chars = "LARGE"
            else:
                size_by_chars = "SMALL"
            
        # Overall size determination
        sizes = [size_by_lines, size_by_files, size_by_chars]
        if "VERY_LARGE" in sizes:
            overall_size = "VERY_LARGE"
        elif "LARGE" in sizes:
            overall_size = "LARGE"
        elif "MEDIUM" in sizes:
            overall_size = "MEDIUM"
        else:
            overall_size = "SMALL"
            
        # Review strategy determination
        if overall_size in ["VERY_LARGE", "LARGE"] or total_changes > 10000:
            review_strategy = "SUMMARY_ANALYSIS"
        else:
            review_strategy = "FULL_ANALYSIS"
            
        return {
            "size_by_lines": size_by_lines,
            "size_by_files": size_by_files,
            "size_by_chars": size_by_chars,
            "overall_size": overall_size,
            "review_strategy": review_strategy,
            "size_reasons": [
                f"{total_changes} line changes ({size_by_lines})",
                f"{files_count} files ({size_by_files})",
                f"{diff_size} char diff ({size_by_chars})"
            ]
        }
    
    def _detect_re_review(self, pr_data: Dict, force_re_review: bool) -> Dict[str, Any]:
        """
        Detect re-review mode and extract previous review context.
        Replaces lines 212-228 of review-pr.sh.
        """
        # Check existing comments for automated review patterns
        automated_review_patterns = [
            "🎯.*Overview", "## 🎯", "🔍.*Analysis", "⚠️.*Critical Issues",
            "💡.*Suggestions", "Automated PR Review", "🔍 Automated PR Review",
            "## 🤖 Enhanced PR Review"
        ]
        
        comments = pr_data.get("comments", [])
        has_automated_reviews = any(
            any(re.search(pattern, comment.get("body", "")) for pattern in automated_review_patterns)
            for comment in comments
        )
        
        is_re_review = force_re_review or has_automated_reviews
        review_count = sum(
            1 for comment in comments
            if any(re.search(pattern, comment.get("body", "")) for pattern in automated_review_patterns)
        )
        
        return {
            "is_re_review": is_re_review,
            "review_count": review_count,
            "previous_reviews": comments if is_re_review else []
        }
    
    async def _generate_comprehensive_analysis(
        self,
        pr_data: Dict,
        size_analysis: Dict,
        review_context: Dict,
        analysis_mode: str,
        detail_level: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive PR analysis using Claude CLI integration.
        Replaces lines 260-572 of review-pr.sh with claude -p functionality.
        """
        try:
            # Create comprehensive review prompt (replicating lines 263-420 of review-pr.sh)
            prompt_content = self._create_comprehensive_prompt(
                pr_data, size_analysis, review_context, detail_level
            )
            
            # Create data file for claude -p (replicating lines 422-543)
            data_content = self._create_pr_data_content(
                pr_data, size_analysis, review_context
            )
            
            # Check for Claude CLI availability (lines 49-54 of review-pr.sh)
            logger.info("🔍 Checking Claude CLI availability for enhanced analysis...")
            claude_available = self._check_claude_availability()
            logger.info(f"🔍 Claude CLI availability result: {claude_available}")
            
            if claude_available:
                logger.info("✅ Claude CLI available - attempting enhanced analysis")
                # Use claude -p for comprehensive analysis (lines 549-572)
                analysis = await self._run_claude_analysis(
                    prompt_content, data_content, pr_data["metadata"]["number"]
                )
                
                if analysis:
                    logger.info("✅ Enhanced Claude analysis successful - returning results")
                    return analysis
                else:
                    logger.warning("⚠️ Enhanced Claude analysis failed - falling back to standard analysis")
            else:
                logger.info("ℹ️ Claude CLI not available - using fallback analysis")
                    
            # Fallback analysis when Claude is not available (lines 574-668)
            logger.info("📋 Generating fallback analysis...")
            fallback_result = self._generate_fallback_analysis(pr_data, size_analysis, review_context)
            logger.info("✅ Fallback analysis completed")
            return fallback_result
            
        except Exception as e:
            logger.error(f"❌ Analysis generation failed with exception: {e}")
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            logger.info("📋 Falling back to standard analysis due to exception...")
            return self._generate_fallback_analysis(pr_data, size_analysis, review_context)
    
    def _check_claude_availability(self) -> bool:
        """Check external Claude CLI integration availability."""
        logger.info("🔍 Checking external Claude CLI integration availability...")
        
        try:
            # Check environment for Docker
            import os
            docker_env_exists = os.path.exists("/.dockerenv")
            docker_env_var = os.environ.get("RUNNING_IN_DOCKER")
            
            if docker_env_exists or docker_env_var:
                logger.info("🐳 Running in Docker container - external Claude CLI not available, using fallback analysis")
                return False
            
            # Use our external Claude CLI integration to check availability
            claude_path = self.external_claude._find_claude_cli()
            
            if claude_path and claude_path != "claude":
                logger.info(f"✅ External Claude CLI integration available at {claude_path}")
                return True
            elif claude_path == "claude":
                # Test if default claude command works
                try:
                    result = subprocess.run(
                        ["claude", "--version"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if result.returncode == 0:
                        logger.info("✅ External Claude CLI integration available (default claude command)")
                        return True
                except Exception:
                    pass
            
            logger.warning("⚠️ External Claude CLI integration not available - will use fallback analysis")
            return False
            
        except Exception as e:
            logger.error(f"❌ Claude CLI check failed with exception: {e}")
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False
    
    def _create_comprehensive_prompt(
        self, 
        pr_data: Dict, 
        size_analysis: Dict, 
        review_context: Dict, 
        detail_level: str
    ) -> str:
        """
        Create comprehensive review prompt (replicating lines 263-420 of review-pr.sh).
        """
        is_re_review = review_context["is_re_review"]
        review_count = review_context["review_count"]
        linked_issues = pr_data.get("linked_issues", [])
        
        prompt = f"""You are an expert code reviewer with focus on systematic prevention of third-party integration failures. Apply project conventions from CLAUDE.md, .cursor/rules/*, or .windsurfrules (if available).

{self._format_re_review_context(is_re_review, review_count)}

1. Use available MCP GitHub tools for comprehensive PR analysis
2. Apply Clear-Thought MCP tools for systematic code review
3. Leverage research tools for validation of technical approaches
4. Employ debugging approaches for identifying potential issues

Perform a comprehensive review of this Pull Request and provide output in the exact format below:

🎯 **Overview**
Brief summary of what this PR accomplishes and its scope

{self._format_re_review_analysis_section(is_re_review, review_count)}

🔗 **Issue Linkage Validation**
{self._format_issue_linkage_prompt(linked_issues)}

📝 **Previous Review Comments Analysis**
{self._format_comments_analysis_prompt(pr_data.get("comments", []))}

🚫 **Third-Party Integration & Complexity Assessment**
- [ ] If this involves third-party services: Does it follow API-first development protocol from CLAUDE.md?
- [ ] Are we using standard APIs/SDKs instead of building custom implementations?
- [ ] **Assess (not necessarily block):** Infrastructure-without-implementation patterns
- [ ] **Consider:** Is custom code justified and well-documented for its purpose?
- [ ] **Advisory:** Working POC validation for complex third-party integrations
- [ ] **Apply Clear-Thought debugging approach:** Systematic analysis of complexity trade-offs
- [ ] **Use MCP research tools:** Validate third-party service integration approaches

✅ **Strengths** 
- Key positive aspects and good practices followed
- Well-implemented features and patterns
- Good code quality and architecture decisions
- Adherence to CLAUDE.md guidelines
- **Clear-Thought validation:** Systematic reasoning supporting good practices

⚠️ **Critical Issues**
- Bugs or problems that must be fixed before merge
- Breaking changes or compatibility issues
- Security vulnerabilities or concerns
- Missing issue linkage or requirement validation
- **Clear-Thought analysis:** Systematic identification of failure modes and risks

💡 **Complexity & Architecture Considerations**
- Over-engineering patterns or unnecessary complexity (advisory, not necessarily blocking)
- Infrastructure complexity vs. benefit trade-offs
- Optional vs. required dependencies assessment
- User experience and setup complexity considerations
- Alternative implementation approaches worth considering

💡 **Enhancement Suggestions**
- Code improvements and optimizations
- Best practice recommendations
- Performance considerations
- Architecture improvements
- Simplification opportunities (where beneficial, not dogmatic)
- Optional dependency management strategies
- User experience improvements
- **Research-backed recommendations:** External validation of suggested approaches
- **Clear-Thought insights:** Systematic thinking results informing suggestions

🧪 **Testing Requirements**
- What needs testing before merge
- Specific test scenarios to validate
- Integration test considerations
- Third-party service validation if applicable
- **Clear-Thought testing strategy:** Systematic approach to test coverage and validation

📋 **Action Items**
- [ ] **Required changes for approval** (critical issues only)
- [ ] Issue linkage corrections needed
- [ ] **Recommended improvements** (suggestions, not requirements)
- [ ] **Advisory considerations** (complexity trade-offs to consider)
- [ ] Documentation updates needed
- [ ] Third-party integration validation if applicable
- [ ] **Optional dependency management** (make MCP servers optional where feasible)
- [ ] **MCP GitHub follow-up:** Use GitHub tools for any additional PR interactions needed

🧠 **Clear-Thought Analysis Summary**
[Key insights from systematic thinking tools and how they inform the review]

🔍 **MCP Tools Usage Summary**
[GitHub tools used, research validation performed, systematic analysis applied]

**Recommendation**: [APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]
**Analysis Confidence**: [HIGH/MEDIUM/LOW] - [systematic validation quality]

**Review Philosophy**: 
- Distinguish between critical issues (must fix) and advisory considerations (worth considering)
- Recognize that complexity may be justified for specific purposes (logging, better analysis, etc.)
- Focus on helping vs. blocking: provide options and considerations rather than dogmatic requirements
- Validate third-party integrations but recognize their value when well-implemented
- Consider user experience: optional dependencies and graceful degradation where possible

**CRITICAL: Code Analysis Guidelines**
- **ONLY analyze the changed files in this PR diff** - do not count unrelated repository files
- **Focus on NET changes**: If files were deleted and replaced, analyze the complexity reduction vs. addition
- **Understand refactoring**: File deletions followed by simpler replacements represent complexity reduction
- **PR Statistics Context**: +{pr_data['statistics']['additions']}/-{pr_data['statistics']['deletions']} lines may include large deletions of over-engineered code
- **Validate Claims**: When author claims complexity reduction, look for evidence in deleted vs. added files
- **Files Changed**: {pr_data['statistics']['files_count']} files (focus analysis only on these files, not entire repository)

Focus on project conventions from CLAUDE.md/.cursor/rules/.windsurfrules, balanced assessment of complexity trade-offs, and actionable feedback enhanced by MCP tool capabilities.
"""
        return prompt
    
    def _format_re_review_context(self, is_re_review: bool, review_count: int) -> str:
        """Format re-review context section."""
        if is_re_review:
            return f"""**🔄 RE-REVIEW MODE** - This is review #{review_count + 1} for this PR
**Previous Review Context:**
- Focus on changes since last review
- Identify what issues have been resolved vs. still pending
- Avoid repeating previously identified issues that haven't changed
- Provide incremental analysis focusing on new developments

**Enhanced Re-Review Instructions:**
1. Compare current state against previous automated review findings
2. Highlight what has been addressed from previous feedback
3. Focus analysis on new changes and unresolved issues
4. Provide progress assessment on previous recommendations
"""
        else:
            return """**✨ FIRST REVIEW** - Comprehensive initial analysis

**Enhanced Review Instructions:**"""
    
    def _format_re_review_analysis_section(self, is_re_review: bool, review_count: int) -> str:
        """Format re-review analysis section."""
        if is_re_review:
            return f"""🔄 **Re-Review Analysis** (Review #{review_count + 1})
**Previous Review Summary:**
- [ ] Identify key issues flagged in previous automated review(s)
- [ ] Assess what has been resolved since last review
- [ ] Highlight new changes that need analysis
- [ ] Provide progress assessment: IMPROVED/UNCHANGED/REGRESSED
- [ ] Focus on incremental changes vs. comprehensive re-analysis
"""
        return ""
    
    def _format_issue_linkage_prompt(self, linked_issues: List[Dict]) -> str:
        """Format issue linkage validation prompt."""
        if linked_issues:
            issue_numbers = ", ".join([f"#{issue['number']}" for issue in linked_issues])
            return f"""- Linked Issues: {issue_numbers}
- [ ] Verify PR addresses the core problem described in linked issue(s)
- [ ] Check if acceptance criteria from issue are met
- [ ] Validate that solution approach aligns with issue requirements
- [ ] Apply Clear-Thought decision framework to assess PR-issue alignment
- [ ] Ensure all issue requirements are addressed by this PR

**Linked Issue Analysis Available Below** - Use this to validate alignment"""
        else:
            return """⚠️ NO LINKED ISSUES DETECTED - This PR should reference specific issues it addresses
- [ ] PR should link to relevant issues using 'Fixes #XXX' syntax
- [ ] Changes should be traceable to documented requirements
- [ ] Use MCP GitHub search to find related issues if needed"""
    
    def _format_comments_analysis_prompt(self, comments: List[Dict]) -> str:
        """Format previous comments analysis prompt."""
        if comments:
            return """- [ ] Analyze existing review feedback and concerns raised
- [ ] Verify that previous review issues have been addressed
- [ ] Check if changes align with reviewer suggestions
- [ ] Identify any unresolved review topics that need follow-up
- [ ] Apply Clear-Thought collaborative reasoning to assess reviewer consensus

**Previous Comments Available Below** - Address any unresolved feedback"""
        else:
            return """✅ This is the first review of this PR
- [ ] Provide comprehensive initial review
- [ ] Set clear expectations for any needed changes"""
    
    def _create_pr_data_content(
        self, 
        pr_data: Dict, 
        size_analysis: Dict, 
        review_context: Dict
    ) -> str:
        """
        Create PR data content for claude -p (replicating lines 422-543).
        """
        metadata = pr_data["metadata"]
        stats = pr_data["statistics"]
        
        # Determine review type based on size analysis
        if size_analysis["overall_size"] in ["VERY_LARGE"] or stats["total_changes"] > 10000:
            return self._create_very_large_pr_data(pr_data, review_context)
        elif size_analysis["overall_size"] == "LARGE" or len(pr_data.get("diff", "")) > 50000:
            return self._create_large_pr_data(pr_data, review_context)
        else:
            return self._create_standard_pr_data(pr_data, review_context)
    
    def _create_standard_pr_data(self, pr_data: Dict, review_context: Dict) -> str:
        """Create standard PR data content."""
        metadata = pr_data["metadata"]
        stats = pr_data["statistics"]
        files_changed = [f["path"] for f in pr_data.get("files", [])]
        
        content = f"""# PR #{metadata['number']} Review Data

## PR Information
**Title:** {metadata['title']}
**Author:** {metadata['author']}
**Created:** {metadata['created_at']}
**Branch:** {metadata['head_branch']} → {metadata['base_branch']}
**Files Changed:** {stats['files_count']}
**Lines:** +{stats['additions']}/-{stats['deletions']}

**Description:**
{metadata['body']}

**Files Modified:**
{chr(10).join(files_changed)}

**Complete Diff:**
```diff
{pr_data.get('diff', 'Diff not available')}
```

## Previous Review Comments
{self._format_existing_comments(pr_data.get('comments', []))}

{self._format_re_review_data_section(review_context)}

{self._format_issue_analysis_section(pr_data.get('linked_issues', []))}
"""
        return content
    
    def _create_large_pr_data(self, pr_data: Dict, review_context: Dict) -> str:
        """Create large PR data content with summary approach."""
        metadata = pr_data["metadata"]
        stats = pr_data["statistics"]
        diff_size = len(pr_data.get("diff", ""))
        
        # Get file stats summary
        file_stats = []
        for file_info in pr_data.get("files", []):
            if "path" in file_info:
                file_stats.append(f"{file_info['path']}: +{file_info.get('additions', 0)}/-{file_info.get('deletions', 0)}")
        
        # Get key diff patterns (sample)
        diff_content = pr_data.get("diff", "")
        diff_sample = self._extract_diff_patterns(diff_content, 200)
        
        content = f"""# PR #{metadata['number']} Review Data (Large PR - Summary Analysis)

## PR Information
**Title:** {metadata['title']}
**Author:** {metadata['author']}
**Created:** {metadata['created_at']}
**Branch:** {metadata['head_branch']} → {metadata['base_branch']}
**Files Changed:** {stats['files_count']}
**Lines:** +{stats['additions']}/-{stats['deletions']}

**Description:**
{metadata['body']}

**File Change Summary:**
{chr(10).join(file_stats)}

**Key Diff Patterns (Sample - 200 lines):**
```diff
{diff_sample}
```

**Note:** This is a large PR ({diff_size} chars). Review focuses on architecture, patterns, and high-level changes rather than line-by-line analysis.

## Previous Review Comments
{self._format_existing_comments(pr_data.get('comments', []))}

{self._format_re_review_data_section(review_context)}

{self._format_issue_analysis_section(pr_data.get('linked_issues', []))}
"""
        return content
    
    def _create_very_large_pr_data(self, pr_data: Dict, review_context: Dict) -> str:
        """Create very large PR data content with file-level analysis."""
        metadata = pr_data["metadata"]
        stats = pr_data["statistics"]
        
        # Get file stats summary
        file_stats = []
        for file_info in pr_data.get("files", []):
            if "path" in file_info:
                file_stats.append(f"{file_info['path']}: +{file_info.get('additions', 0)}/-{file_info.get('deletions', 0)}")
        
        # Get sample from first 5 files
        sample_content = self._get_sample_file_content(pr_data.get("files", [])[:5])
        
        content = f"""# PR #{metadata['number']} Review Data (Very Large PR - File Summary Analysis)

## PR Information
**Title:** {metadata['title']}
**Author:** {metadata['author']}
**Created:** {metadata['created_at']}
**Branch:** {metadata['head_branch']} → {metadata['base_branch']}
**Files Changed:** {stats['files_count']}
**Lines:** +{stats['additions']}/-{stats['deletions']}

**Description:**
{metadata['body']}

**File Change Summary:**
{chr(10).join(file_stats)}

**Sample Code Changes (First 5 files with 20-line previews):**
{sample_content}

**Note:** This PR exceeds normal size limits. Review focuses on file-level changes, architecture patterns, and high-level impact assessment rather than detailed line-by-line analysis.

**Review Strategy:**
- Focus on architectural changes and patterns
- Identify potential breaking changes or compatibility issues  
- Assess security implications of large-scale changes
- Recommend testing strategies for comprehensive changes
- Highlight areas that need careful manual review

## Previous Review Comments
{self._format_existing_comments(pr_data.get('comments', []))}

{self._format_re_review_data_section(review_context)}

{self._format_issue_analysis_section(pr_data.get('linked_issues', []))}
"""
        return content
    
    def _extract_diff_patterns(self, diff_content: str, max_lines: int) -> str:
        """Extract key patterns from diff content."""
        if not diff_content:
            return "Diff not available"
            
        lines = diff_content.split('\n')
        pattern_lines = []
        
        for line in lines:
            if (line.startswith('diff ') or 
                line.startswith('@@') or 
                line.startswith('+++') or 
                line.startswith('---') or 
                (line.startswith('+') and not line.startswith('++')) or
                (line.startswith('-') and not line.startswith('--'))):
                pattern_lines.append(line)
                
            if len(pattern_lines) >= max_lines:
                break
                
        return '\n'.join(pattern_lines)
    
    def _get_sample_file_content(self, files: List[Dict]) -> str:
        """Get sample content from files."""
        samples = []
        
        for file_info in files:
            file_path = file_info.get("path", "unknown")
            patch = file_info.get("patch", "")
            
            if patch:
                # Take first 20 lines of patch
                patch_lines = patch.split('\n')[:20]
                samples.append(f"""## {file_path}
```diff
{chr(10).join(patch_lines)}
```
""")
            else:
                samples.append(f"""## {file_path}
File too large or binary
""")
        
        return "\n".join(samples) if samples else "No sample content available"
    
    def _format_existing_comments(self, comments: List[Dict]) -> str:
        """Format existing PR comments."""
        if not comments:
            return "No comments found"
            
        formatted_comments = []
        for comment in comments:
            author = comment.get("author", {}).get("login", "Unknown")
            created_at = comment.get("createdAt", "Unknown")
            body = comment.get("body", "")
            formatted_comments.append(f"**@{author}** ({created_at}): {body}")
            
        return "\n\n".join(formatted_comments)
    
    def _format_re_review_data_section(self, review_context: Dict) -> str:
        """Format re-review data section."""
        if review_context["is_re_review"]:
            return f"""## Previous Automated Reviews (For Re-Review Analysis)
**Review Count**: {review_context['review_count']} previous automated reviews
**Previous Automated Review Details**:
{self._format_previous_reviews(review_context.get('previous_reviews', []))}

**Re-Review Focus**: Compare current state against previous findings and assess progress
"""
        return ""
    
    def _format_previous_reviews(self, previous_reviews: List[Dict]) -> str:
        """Format previous automated reviews."""
        if not previous_reviews:
            return "Previous automated reviews found but could not extract details"
            
        # Extract review patterns
        review_patterns = []
        for review in previous_reviews:
            body = review.get("body", "")
            if any(pattern in body for pattern in ["🎯", "💡", "⚠️", "Automated PR Review"]):
                review_patterns.append(body[:500] + "..." if len(body) > 500 else body)
                
        return "\n\n---\n\n".join(review_patterns) if review_patterns else "Previous reviews detected but content extraction failed"
    
    def _format_issue_analysis_section(self, linked_issues: List[Dict]) -> str:
        """Format linked issue analysis section."""
        if not linked_issues:
            return ""
            
        sections = []
        for issue in linked_issues:
            if "error" in issue:
                sections.append(f"""## Issue #{issue['number']} Analysis
**Status:** Issue not found or inaccessible
""")
            else:
                labels = ", ".join(issue.get("labels", []))
                sections.append(f"""## Issue #{issue['number']} Analysis
**Title:** {issue.get('title', 'N/A')}
**Labels:** {labels}
**Body:** 
{issue.get('body', 'No description')}
""")
                
        return "\n".join(sections)
    
    async def _run_claude_analysis(
        self, 
        prompt_content: str, 
        data_content: str, 
        pr_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Run Claude analysis using external Claude CLI integration.
        
        Replaces the complex subprocess implementation with our external Claude CLI
        integration that eliminates context blocking and timeout issues.
        """
        logger.info(f"🔍 Starting external Claude analysis for PR #{pr_number}")
        logger.info(f"🔍 Prompt content size: {len(prompt_content)} chars")
        logger.info(f"🔍 Data content size: {len(data_content)} chars")
        
        try:
            # Create combined content for analysis
            combined_content = f"{prompt_content}\n\n{data_content}"
            combined_size = len(combined_content)
            logger.info(f"🔍 Combined content size: {combined_size} chars")
            
            # Set adaptive timeout based on content size
            timeout_seconds = self._calculate_adaptive_timeout(combined_size, pr_number)
            
            # Update external Claude CLI timeout dynamically
            self.external_claude.timeout_seconds = timeout_seconds
            
            logger.info(f"🔍 Using external Claude CLI integration with {timeout_seconds}s timeout...")
            
            # Use external Claude CLI for PR review analysis
            result = await self.external_claude.analyze_content(
                content=combined_content,
                task_type="pr_review",
                additional_context=f"PR #{pr_number} Analysis"
            )
            
            # Log execution details
            logger.info(f"🔍 External Claude analysis completed in {result.execution_time:.2f}s")
            
            if result.success and result.output:
                output_size = len(result.output)
                logger.info(f"🔍 Claude output preview: {result.output[:200]}{'...' if len(result.output) > 200 else ''}")
                
                # Log SDK metadata if available
                if result.cost_usd:
                    logger.info(f"💰 Analysis cost: ${result.cost_usd:.4f}")
                if result.session_id:
                    logger.info(f"🔗 Session ID: {result.session_id}")
                if result.num_turns:
                    logger.info(f"🔄 Number of turns: {result.num_turns}")
                
                # Save debug information
                try:
                    timestamp = int(time.time())
                    debug_file = f"/tmp/claude_external_pr_{pr_number}_{timestamp}.log"
                    prompt_file = f"/tmp/claude_prompt_pr_{pr_number}_{timestamp}.md"
                    
                    # Save debug output with SDK metadata
                    with open(debug_file, 'w') as f:
                        f.write("=== External Claude CLI Analysis Session ===\n")
                        f.write(f"Command: {result.command_used}\n")
                        f.write(f"Exit code: {result.exit_code}\n")
                        f.write(f"Execution time: {result.execution_time:.2f}s\n")
                        f.write(f"Cost: ${result.cost_usd or 0:.4f}\n")
                        f.write(f"Session ID: {result.session_id or 'N/A'}\n")
                        f.write(f"Timestamp: {datetime.now()}\n")
                        f.write(f"Timeout: {timeout_seconds} seconds\n")
                        f.write(f"Prompt file: {prompt_file}\n")
                        f.write("\n=== SDK METADATA ===\n")
                        f.write(json.dumps(result.sdk_metadata, indent=2))
                        f.write("\n\n=== OUTPUT ===\n")
                        f.write(result.output)
                        if result.error:
                            f.write("\n\n=== ERROR ===\n")
                            f.write(result.error)
                    
                    # Save the prompt content
                    with open(prompt_file, 'w') as f:
                        f.write(combined_content)
                    
                    logger.info(f"🔍 External Claude debug output saved to: {debug_file}")
                    logger.info(f"🔍 Prompt content saved to: {prompt_file}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to save debug output: {e}")
                
                if output_size < 50:
                    logger.warning(f"⚠️ Generated review content seems too short ({output_size} chars)")
                    logger.info(f"🔍 Full short output: {result.output}")
                    return None
                    
                logger.info(f"✅ External Claude analysis completed successfully ({output_size} chars)")
                
                # Parse Claude output into structured format
                logger.info("🔍 Parsing Claude output into structured format...")
                parsed_result = self._parse_claude_output(result.output, pr_number)
                
                # Add SDK metadata to parsed result
                if parsed_result and result.sdk_metadata:
                    parsed_result["sdk_metadata"] = result.sdk_metadata
                    parsed_result["cost_usd"] = result.cost_usd
                    parsed_result["session_id"] = result.session_id
                    parsed_result["execution_time"] = result.execution_time
                    parsed_result["analysis_method"] = "external-claude-cli"
                
                if parsed_result:
                    logger.info("✅ Claude output parsed successfully")
                    return parsed_result
                else:
                    logger.error("❌ Failed to parse Claude output")
                    return None
                    
            else:
                logger.error(f"❌ External Claude analysis failed: {result.error}")
                logger.info(f"🔍 Exit code: {result.exit_code}")
                logger.info(f"🔍 Execution time: {result.execution_time:.2f}s")
                return None
                
        except Exception as e:
            logger.error(f"❌ External Claude analysis failed with exception: {e}")
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return None
    
    def _parse_claude_output(self, claude_output: str, pr_number: int = None) -> Dict[str, Any]:
        """Parse Claude output into structured analysis format."""
        # For now, return the raw Claude output
        # This could be enhanced to parse specific sections
        result = {
            "claude_analysis": claude_output,
            "analysis_method": "claude-cli",
            "timestamp": datetime.now().isoformat()
        }
        if pr_number:
            result["pr_number"] = pr_number
        return result
    
    def _generate_fallback_analysis(
        self, 
        pr_data: Dict, 
        size_analysis: Dict, 
        review_context: Dict
    ) -> Dict[str, Any]:
        """
        Generate fallback analysis when Claude is not available (lines 574-668).
        """
        metadata = pr_data["metadata"]
        stats = pr_data["statistics"]
        
        # Basic analysis without Claude reasoning
        analysis = {
            "pr_number": metadata['number'],
            "overview": f"Analysis of PR #{metadata['number']}",
            "size_analysis": size_analysis,
            "issue_linkage": self._analyze_issue_linkage(pr_data),
            "previous_comments": self._analyze_previous_comments(pr_data, review_context),
            "third_party_assessment": self._assess_third_party_integration(pr_data),
            "strengths": self._identify_strengths(pr_data),
            "critical_issues": self._identify_critical_issues(pr_data),
            "complexity_considerations": self._assess_complexity(pr_data),
            "enhancement_suggestions": self._generate_suggestions(pr_data),
            "testing_requirements": self._analyze_testing_needs(pr_data),
            "action_items": self._generate_action_items(pr_data),
            "recommendation": self._generate_recommendation(pr_data),
            "analysis_method": "fallback",
            "clear_thought_summary": "Using fallback analysis - Claude CLI analysis not available or failed",
            "mcp_tools_summary": "GitHub CLI integration used for data collection",
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
    
    def _analyze_issue_linkage(self, pr_data: Dict) -> Dict[str, Any]:
        """Analyze linked issues and validate PR-issue alignment."""
        # Extract issue numbers from PR body
        body = pr_data["metadata"].get("body", "")
        issue_pattern = r"(Fixes|Closes|Resolves)\s+#(\d+)"
        linked_issues = re.findall(issue_pattern, body, re.IGNORECASE)
        
        return {
            "linked_issues": linked_issues,
            "has_linkage": len(linked_issues) > 0,
            "validation_needed": len(linked_issues) == 0
        }
    
    def _analyze_previous_comments(self, pr_data: Dict, review_context: Dict) -> Dict[str, Any]:
        """Analyze existing review feedback."""
        comments = pr_data.get("comments", [])
        return {
            "comment_count": len(comments),
            "has_feedback": len(comments) > 0,
            "review_needed": review_context["is_re_review"]
        }
    
    def _assess_third_party_integration(self, pr_data: Dict) -> Dict[str, Any]:
        """Assess third-party integration patterns and complexity."""
        # Analyze diff for third-party integration patterns
        diff_content = pr_data.get("diff", "")
        body_content = pr_data["metadata"].get("body", "")
        
        third_party_keywords = [
            "api", "sdk", "integration", "client", "server", "http", "rest",
            "docker", "postgres", "redis", "openai", "anthropic"
        ]
        
        has_integration = any(
            keyword in diff_content.lower() or keyword in body_content.lower()
            for keyword in third_party_keywords
        )
        
        return {
            "has_third_party_integration": has_integration,
            "api_first_needed": has_integration,
            "poc_validation_needed": has_integration
        }
    
    def _identify_strengths(self, pr_data: Dict) -> List[str]:
        """Identify positive aspects and good practices."""
        strengths = []
        
        # Check for good practices
        if self._analyze_issue_linkage(pr_data)["has_linkage"]:
            strengths.append("✅ Proper issue linkage with 'Fixes #XXX' syntax")
            
        if pr_data["statistics"]["total_changes"] < 500:
            strengths.append("✅ Focused, manageable PR size")
            
        return strengths
    
    def _identify_critical_issues(self, pr_data: Dict) -> List[str]:
        """Identify critical issues that must be addressed."""
        issues = []
        
        if not self._analyze_issue_linkage(pr_data)["has_linkage"]:
            issues.append("❌ Missing issue linkage - PR should reference specific issues")
            
        if pr_data["statistics"]["total_changes"] > 5000:
            issues.append("⚠️ Very large PR - consider breaking into smaller changes")
            
        return issues
    
    def _assess_complexity(self, pr_data: Dict) -> List[str]:
        """Assess complexity and architecture considerations."""
        considerations = []
        
        if pr_data["statistics"]["files_count"] > 20:
            considerations.append("📁 High file count - verify architectural impact")
            
        if self._assess_third_party_integration(pr_data)["has_third_party_integration"]:
            considerations.append("🔗 Third-party integration detected - validate API-first approach")
            
        return considerations
    
    def _generate_suggestions(self, pr_data: Dict) -> List[str]:
        """Generate enhancement suggestions."""
        suggestions = []
        
        suggestions.append("📝 Consider adding/updating documentation for changes")
        suggestions.append("🧪 Verify comprehensive test coverage")
        
        return suggestions
    
    def _analyze_testing_needs(self, pr_data: Dict) -> List[str]:
        """Analyze testing requirements."""
        return [
            "🧪 Unit tests for new functionality",
            "🔗 Integration tests for API changes",
            "📊 Performance impact assessment"
        ]
    
    def _generate_action_items(self, pr_data: Dict) -> Dict[str, List[str]]:
        """Generate specific action items."""
        critical_issues = self._identify_critical_issues(pr_data)
        
        return {
            "required_changes": critical_issues,
            "recommended_improvements": self._generate_suggestions(pr_data),
            "testing_actions": self._analyze_testing_needs(pr_data)
        }
    
    def _generate_recommendation(self, pr_data: Dict) -> Dict[str, str]:
        """Generate final recommendation."""
        critical_issues = self._identify_critical_issues(pr_data)
        
        if critical_issues:
            return {
                "status": "REQUEST_CHANGES",
                "confidence": "HIGH",
                "reason": f"Critical issues must be addressed: {len(critical_issues)} issues found"
            }
        else:
            return {
                "status": "APPROVE",
                "confidence": "HIGH", 
                "reason": "No critical issues detected, good practices followed"
            }
    
    def _post_review_to_github(
        self,
        pr_number: int,
        repository: str,
        analysis: Dict,
        review_context: Dict
    ) -> Dict[str, Any]:
        """
        Post comprehensive review to GitHub.
        Replaces lines 670-731 of review-pr.sh.
        """
        try:
            # Format review comment
            comment_body = self._format_review_comment(analysis, review_context)
            
            # Post review comment using gh CLI
            comment_result = subprocess.run([
                "gh", "pr", "comment", str(pr_number),
                "--repo", repository,
                "--body", comment_body
            ], capture_output=True, text=True, check=True)
            
            logger.info(f"✅ Review comment posted to PR #{pr_number}")
            
            # Add appropriate labels
            labels_to_add = ["automated-review"]
            if review_context["is_re_review"]:
                labels_to_add.append("re-reviewed")
            
            try:
                for label in labels_to_add:
                    subprocess.run([
                        "gh", "pr", "edit", str(pr_number),
                        "--repo", repository,
                        "--add-label", label
                    ], capture_output=True, text=True, check=True)
                
                logger.info(f"✅ Labels added to PR #{pr_number}: {', '.join(labels_to_add)}")
                
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to add labels (continuing anyway): {e}")
            
            return {
                "comment_posted": True,
                "comment_result": comment_result.stdout.strip() if comment_result.stdout else "Success",
                "labels_added": labels_to_add,
                "re_review_label": review_context["is_re_review"],
                "github_url": f"https://github.com/{repository}/pull/{pr_number}"
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to post review to GitHub: {e}")
            return {"error": f"GitHub posting failed: {e.stderr}"}
        except Exception as e:
            logger.error(f"Failed to post review to GitHub: {e}")
            return {"error": f"GitHub posting failed: {str(e)}"}
    
    def _format_review_comment(self, analysis: Dict, review_context: Dict) -> str:
        """Format comprehensive analysis as GitHub comment."""
        is_re_review = review_context["is_re_review"]
        review_count = review_context["review_count"]
        analysis_method = analysis.get("analysis_method", "fallback")
        
        # Header with analysis method info
        header = ""
        if is_re_review:
            header = f"""## 🔄 **Automated PR Re-Review #{review_count + 1}**

**Previous Reviews**: {review_count} automated review(s) completed
**Re-Review Focus**: Changes since last review, progress assessment, new issues
**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Analysis Method**: {'🧠 Claude CLI Enhanced' if analysis_method == 'claude-cli' else '⚠️ Fallback Analysis'}

---

"""
        else:
            method_icon = "🧠" if analysis_method == "claude-cli" else "⚠️"
            method_name = "Claude CLI Enhanced Analysis" if analysis_method == "claude-cli" else "Fallback Analysis (Claude CLI not available)"
            header = f"""## 🎯 **Deep Vibe Check PR #{analysis.get('pr_number', 'XX')}**

**Analysis Method**: {method_name}
**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        # If we have Claude analysis, use it directly
        if analysis_method == "claude-cli" and "claude_analysis" in analysis:
            comment = f"""{header}{analysis['claude_analysis']}

---
*Enhanced review generated by Vibe Check MCP using Claude CLI • Comprehensive analysis with systematic reasoning*
"""
        else:
            # Use structured fallback format
            comment = f"""{header}### 🎯 Overview
{analysis.get('overview', 'Analysis overview not available')}

### 🔗 Issue Linkage Validation
{self._format_issue_linkage_section(analysis.get('issue_linkage', {}))}

### 📝 Previous Review Comments Analysis
{self._format_comments_section(analysis.get('previous_comments', {}))}

### 🚫 Third-Party Integration & Complexity Assessment
{self._format_third_party_section(analysis.get('third_party_assessment', {}))}

### ✅ Strengths
{self._format_list_section(analysis.get('strengths', []))}

### ⚠️ Critical Issues
{self._format_list_section(analysis.get('critical_issues', []))}

### 💡 Complexity & Architecture Considerations
{self._format_list_section(analysis.get('complexity_considerations', []))}

### 💡 Enhancement Suggestions
{self._format_list_section(analysis.get('enhancement_suggestions', []))}

### 🧪 Testing Requirements
{self._format_list_section(analysis.get('testing_requirements', []))}

### 📋 Action Items
{self._format_action_items(analysis.get('action_items', {}))}

### 🧠 Clear-Thought Analysis Summary
{analysis.get('clear_thought_summary', 'Analysis summary not available')}

### 🔍 MCP Tools Usage Summary
{analysis.get('mcp_tools_summary', 'Tool usage summary not available')}

**Recommendation**: {analysis.get('recommendation', {}).get('status', 'MANUAL_REVIEW_REQUIRED')}
**Analysis Confidence**: {analysis.get('recommendation', {}).get('confidence', 'LOW')} - {analysis.get('recommendation', {}).get('reason', 'Enhanced analysis requires Claude CLI')}

---
*Review generated by [Vibe Check MCP](https://github.com/kesslerio/vibe-check-mcp) • {'Enhanced with Claude CLI reasoning' if analysis_method == 'claude-cli' else 'Basic analysis - install Claude CLI for enhanced systematic reasoning'}*
"""
        
        return comment
    
    def _format_issue_linkage_section(self, linkage_data: Dict) -> str:
        """Format issue linkage validation section."""
        if linkage_data["has_linkage"]:
            issues = ", ".join([f"#{num}" for _, num in linkage_data["linked_issues"]])
            return f"✅ **Linked Issues Found**: {issues}"
        else:
            return "⚠️ **NO LINKED ISSUES DETECTED** - PR should reference specific issues using 'Fixes #XXX' syntax"
    
    def _format_comments_section(self, comments_data: Dict) -> str:
        """Format previous comments analysis section."""
        if comments_data["has_feedback"]:
            return f"📝 **{comments_data['comment_count']} existing comments** - Previous feedback should be addressed"
        else:
            return "✨ **First review** - No previous comments to address"
    
    def _format_third_party_section(self, third_party_data: Dict) -> str:
        """Format third-party integration assessment."""
        if third_party_data["has_third_party_integration"]:
            return """⚠️ **Third-party integration detected**
- [ ] API-first development protocol validation needed
- [ ] Working POC demonstration required
- [ ] Standard API/SDK usage verification needed"""
        else:
            return "✅ **No complex third-party integrations detected**"
    
    def _format_list_section(self, items: List[str]) -> str:
        """Format a list of items for the review."""
        if not items:
            return "*None identified*"
        return "\n".join([f"- {item}" for item in items])
    
    def _format_action_items(self, action_items: Dict) -> str:
        """Format action items section."""
        sections = []
        
        if action_items["required_changes"]:
            sections.append("**Required Changes for Approval:**")
            sections.extend([f"- [ ] {item}" for item in action_items["required_changes"]])
            
        if action_items["recommended_improvements"]:
            sections.append("\n**Recommended Improvements:**")
            sections.extend([f"- [ ] {item}" for item in action_items["recommended_improvements"]])
            
        if action_items["testing_actions"]:
            sections.append("\n**Testing Actions:**")
            sections.extend([f"- [ ] {item}" for item in action_items["testing_actions"]])
            
        return "\n".join(sections) if sections else "*No specific actions required*"
    
    def _calculate_adaptive_timeout(self, content_size: int, pr_number: int) -> int:
        """
        Calculate adaptive timeout based on content size and PR characteristics.
        
        Args:
            content_size: Total size of combined prompt + data content in characters
            pr_number: PR number for context
            
        Returns:
            Timeout in seconds optimized for content size
        """
        # Base timeout: 60 seconds (should be sufficient with fixed Claude CLI integration)
        base_timeout = 60
        
        # Size-based adjustments
        if content_size < 10000:      # Small PRs: <10k chars
            size_timeout = 45
        elif content_size < 30000:    # Medium PRs: 10k-30k chars  
            size_timeout = 60
        elif content_size < 100000:   # Large PRs: 30k-100k chars
            size_timeout = 90
        elif content_size < 200000:   # Very Large PRs: 100k-200k chars
            size_timeout = 120
        else:                         # Massive PRs: >200k chars
            size_timeout = 180
            
        # Use the larger of base or size-based timeout
        adaptive_timeout = max(base_timeout, size_timeout)
        
        logger.info(f"🔍 Adaptive timeout: {adaptive_timeout}s for {content_size:,} chars (PR #{pr_number})")
        
        return adaptive_timeout
    
    def _save_permanent_log(
        self,
        pr_number: int,
        analysis: Dict,
        review_context: Dict
    ) -> Dict[str, Any]:
        """Save permanent log of the review."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_file = self.reviews_dir / f"pr-{pr_number}-review-{timestamp}.json"
            
            log_data = {
                "pr_number": pr_number,
                "timestamp": timestamp,
                "analysis": analysis,
                "review_context": review_context
            }
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            return {
                "log_saved": True,
                "log_file": str(log_file)
            }
            
        except Exception as e:
            logger.error(f"Failed to save permanent log: {e}")
            return {"error": f"Log saving failed: {str(e)}"}


# MCP Tool Interface Function
async def review_pull_request(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    force_re_review: bool = False,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    MCP tool function for comprehensive PR review.
    
    Replicates ALL functionality from scripts/review-pr.sh including:
    - Multi-dimensional PR size classification
    - Re-review detection and progress tracking
    - Linked issue analysis and validation
    - Clear-Thought integration for systematic analysis
    - Comprehensive GitHub integration
    - Permanent logging and review tracking
    
    Args:
        pr_number: PR number to review
        repository: Repository in format "owner/repo"
        force_re_review: Force re-review mode
        analysis_mode: "comprehensive" or "quick"
        detail_level: "brief", "standard", or "comprehensive"
        
    Returns:
        Complete review results with GitHub integration status
    """
    tool = PRReviewTool()
    return await tool.review_pull_request(
        pr_number=pr_number,
        repository=repository,
        force_re_review=force_re_review,
        analysis_mode=analysis_mode,
        detail_level=detail_level
    )