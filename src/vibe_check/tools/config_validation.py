"""
Configuration validation for Claude CLI and MCP integration.

This module provides comprehensive validation of Claude CLI installation,
MCP configuration files, tool permissions, and startup validation for
critical components to prevent integration issues.

Implements the requirements from issue #98:
- Claude CLI availability validated on startup
- MCP configuration file structure validated
- Tool permissions verified
- Clear error messages for misconfiguration
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    CRITICAL = "critical"  # Blocks server startup
    WARNING = "warning"   # Server can start but with degraded functionality
    INFO = "info"         # Informational only


@dataclass
class ValidationResult:
    """Result of a configuration validation check."""
    check_name: str
    level: ValidationLevel
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None


class ConfigurationValidator:
    """
    Validates Claude CLI and MCP configuration for proper integration.
    
    Provides comprehensive startup validation to prevent issues like
    the Claude CLI hanging problem resolved in issue #94.
    """
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.home_dir = Path.home()
        
    def validate_all(self) -> Tuple[bool, List[ValidationResult]]:
        """
        Run all configuration validations.
        
        Returns:
            Tuple of (all_critical_passed, list_of_results)
        """
        self.results = []
        
        # Core validations in order of importance
        self._validate_claude_cli_availability()
        self._validate_mcp_configuration_files()
        self._validate_tool_permissions()
        self._validate_environment_setup()
        self._validate_critical_dependencies()
        
        # Check if any critical validations failed
        critical_failures = [r for r in self.results if r.level == ValidationLevel.CRITICAL and not r.success]
        all_critical_passed = len(critical_failures) == 0
        
        return all_critical_passed, self.results
    
    def _validate_claude_cli_availability(self) -> None:
        """Validate Claude CLI installation and accessibility."""
        try:
            # Check if claude command exists in PATH using cross-platform method
            claude_path = shutil.which("claude")
            
            if not claude_path:
                self.results.append(ValidationResult(
                    check_name="claude_cli_availability",
                    level=ValidationLevel.WARNING,
                    success=False,
                    message="Claude CLI not found in PATH",
                    details={"path_searched": os.environ.get("PATH", "")},
                    suggestion="Install Claude CLI or add it to your PATH for full functionality"
                ))
                return
            
            # Try to get version information
            version_result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if version_result.returncode == 0:
                self.results.append(ValidationResult(
                    check_name="claude_cli_availability",
                    level=ValidationLevel.INFO,
                    success=True,
                    message="Claude CLI is available and working",
                    details={
                        "path": claude_path,
                        "version_output": version_result.stdout.strip(),
                        "version_stderr": version_result.stderr.strip()
                    }
                ))
            else:
                self.results.append(ValidationResult(
                    check_name="claude_cli_availability",
                    level=ValidationLevel.WARNING,
                    success=False,
                    message="Claude CLI found but version check failed",
                    details={
                        "path": claude_path,
                        "version_exit_code": version_result.returncode,
                        "version_stderr": version_result.stderr.strip()
                    },
                    suggestion="Check Claude CLI installation and permissions"
                ))
                
        except subprocess.TimeoutExpired:
            self.results.append(ValidationResult(
                check_name="claude_cli_availability",
                level=ValidationLevel.WARNING,
                success=False,
                message="Claude CLI check timed out",
                suggestion="Claude CLI may be experiencing timeout issues (similar to issue #94)"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                check_name="claude_cli_availability",
                level=ValidationLevel.WARNING,
                success=False,
                message=f"Error checking Claude CLI: {str(e)}",
                suggestion="Check system configuration and permissions"
            ))
    
    def _validate_mcp_configuration_files(self) -> None:
        """Validate MCP configuration file structure."""
        # Common MCP configuration locations
        config_paths = [
            self.home_dir / ".claude_desktop_config.json",
            self.home_dir / ".cursor" / "mcp.json",
            Path.cwd() / "config" / "claude-permission-mcp.json"
        ]
        
        configs_found = []
        for config_path in config_paths:
            if config_path.exists():
                configs_found.append(str(config_path))
                self._validate_mcp_config_file(config_path)
        
        if not configs_found:
            self.results.append(ValidationResult(
                check_name="mcp_configuration_files",
                level=ValidationLevel.WARNING,
                success=False,
                message="No MCP configuration files found",
                details={"checked_paths": [str(p) for p in config_paths]},
                suggestion="Create MCP configuration file for Claude CLI integration"
            ))
        else:
            self.results.append(ValidationResult(
                check_name="mcp_configuration_files",
                level=ValidationLevel.INFO,
                success=True,
                message=f"Found MCP configuration files: {', '.join(configs_found)}"
            ))
    
    def _validate_mcp_config_file(self, config_path: Path) -> None:
        """Validate structure of a specific MCP configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check basic structure
            if "mcpServers" not in config:
                self.results.append(ValidationResult(
                    check_name=f"mcp_config_structure_{config_path.name}",
                    level=ValidationLevel.WARNING,
                    success=False,
                    message=f"MCP config missing 'mcpServers' section: {config_path.name}",
                    suggestion="Add 'mcpServers' section to configuration"
                ))
                return
            
            servers = config["mcpServers"]
            if not isinstance(servers, dict):
                self.results.append(ValidationResult(
                    check_name=f"mcp_config_structure_{config_path.name}",
                    level=ValidationLevel.WARNING,
                    success=False,
                    message=f"'mcpServers' must be an object: {config_path.name}",
                    suggestion="Fix 'mcpServers' structure in configuration"
                ))
                return
            
            # Check for vibe-check server configuration
            has_vibe_check = any("vibe-check" in server_name.lower() for server_name in servers.keys())
            if has_vibe_check:
                self.results.append(ValidationResult(
                    check_name=f"mcp_vibe_check_config_{config_path.name}",
                    level=ValidationLevel.INFO,
                    success=True,
                    message=f"Vibe-check server configured in {config_path.name}"
                ))
            
            # Validate server configurations
            for server_name, server_config in servers.items():
                self._validate_server_config(server_name, server_config, config_path.name)
                
        except json.JSONDecodeError as e:
            self.results.append(ValidationResult(
                check_name=f"mcp_config_json_{config_path.name}",
                level=ValidationLevel.CRITICAL,
                success=False,
                message=f"Invalid JSON in {config_path.name}: {str(e)}",
                suggestion="Fix JSON syntax errors in configuration file"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                check_name=f"mcp_config_read_{config_path.name}",
                level=ValidationLevel.WARNING,
                success=False,
                message=f"Error reading {config_path.name}: {str(e)}",
                suggestion="Check file permissions and format"
            ))
    
    def _validate_server_config(self, server_name: str, config: Dict[str, Any], config_file: str) -> None:
        """Validate individual MCP server configuration."""
        required_fields = ["command", "args"] if "command" in config else ["type"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            self.results.append(ValidationResult(
                check_name=f"mcp_server_config_{server_name}",
                level=ValidationLevel.WARNING,
                success=False,
                message=f"Server '{server_name}' missing required fields: {missing_fields}",
                details={"config_file": config_file, "missing_fields": missing_fields},
                suggestion=f"Add missing fields to server '{server_name}' configuration"
            ))
    
    def _validate_tool_permissions(self) -> None:
        """Validate tool permissions and allowlists."""
        # Check for common permission configuration files
        permission_files = [
            Path.cwd() / "config" / "claude-permission-mcp.json",
            self.home_dir / ".claude" / "permissions.json"
        ]
        
        permissions_found = False
        for perm_file in permission_files:
            if perm_file.exists():
                permissions_found = True
                self._validate_permission_file(perm_file)
        
        if not permissions_found:
            self.results.append(ValidationResult(
                check_name="tool_permissions",
                level=ValidationLevel.INFO,
                success=True,
                message="No explicit permission files found (using defaults)",
                details={"checked_paths": [str(p) for p in permission_files]},
                suggestion="Consider creating permission configuration for enhanced security"
            ))
    
    def _validate_permission_file(self, perm_file: Path) -> None:
        """Validate tool permission configuration file."""
        try:
            with open(perm_file, 'r') as f:
                permissions = json.load(f)
            
            # Check structure for Claude permission files
            if "mcpServers" in permissions:
                self.results.append(ValidationResult(
                    check_name=f"permission_file_{perm_file.name}",
                    level=ValidationLevel.INFO,
                    success=True,
                    message=f"Tool permissions configured in {perm_file.name}",
                    details={"servers_count": len(permissions["mcpServers"])}
                ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                check_name=f"permission_file_{perm_file.name}",
                level=ValidationLevel.WARNING,
                success=False,
                message=f"Error reading permission file {perm_file.name}: {str(e)}",
                suggestion="Check permission file format and access"
            ))
    
    def _validate_environment_setup(self) -> None:
        """Validate environment variables and setup."""
        env_checks = [
            ("PYTHONPATH", "Python path configuration"),
            ("GITHUB_TOKEN", "GitHub API access (optional)"),
            ("MCP_TRANSPORT", "MCP transport override (optional)")
        ]
        
        env_issues = []
        for env_var, description in env_checks:
            if env_var == "PYTHONPATH":
                # Check if vibe_check module is importable, regardless of PYTHONPATH
                try:
                    import vibe_check
                    # If we can import it, PYTHONPATH is effectively correct
                    pass
                except ImportError:
                    # Only warn if we can't import AND PYTHONPATH is not set
                    if env_var not in os.environ:
                        env_issues.append(f"{env_var} not set and vibe_check module not in Python path ({description})")
                    elif not any("vibe_check" in path_part for path_part in os.environ[env_var].split(os.pathsep)):
                        env_issues.append(f"{env_var} does not include vibe_check in any path component")
        
        if env_issues:
            self.results.append(ValidationResult(
                check_name="environment_setup",
                level=ValidationLevel.WARNING,
                success=False,
                message="Environment configuration issues detected",
                details={"issues": env_issues},
                suggestion="Set PYTHONPATH to include vibe_check source directory"
            ))
        else:
            self.results.append(ValidationResult(
                check_name="environment_setup",
                level=ValidationLevel.INFO,
                success=True,
                message="Environment setup looks good"
            ))
    
    def _validate_critical_dependencies(self) -> None:
        """Validate critical Python dependencies."""
        critical_deps = ["fastmcp", "click", "aiohttp"]
        missing_deps = []
        
        for dep in critical_deps:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
        
        if missing_deps:
            self.results.append(ValidationResult(
                check_name="critical_dependencies",
                level=ValidationLevel.CRITICAL,
                success=False,
                message=f"Missing critical dependencies: {', '.join(missing_deps)}",
                suggestion="Install missing dependencies: pip install " + " ".join(missing_deps)
            ))
        else:
            self.results.append(ValidationResult(
                check_name="critical_dependencies",
                level=ValidationLevel.INFO,
                success=True,
                message="All critical dependencies available"
            ))


def validate_configuration() -> Tuple[bool, List[ValidationResult]]:
    """
    Main entry point for configuration validation.
    
    Returns:
        Tuple of (can_start_server, validation_results)
    """
    validator = ConfigurationValidator()
    return validator.validate_all()


def format_validation_results(results: List[ValidationResult]) -> str:
    """Format validation results for display."""
    lines = ["Configuration Validation Results:", "=" * 40]
    
    # Group by level
    by_level = {level: [] for level in ValidationLevel}
    for result in results:
        by_level[result.level].append(result)
    
    # Display in order: CRITICAL, WARNING, INFO
    for level in [ValidationLevel.CRITICAL, ValidationLevel.WARNING, ValidationLevel.INFO]:
        level_results = by_level[level]
        if not level_results:
            continue
            
        lines.append(f"\n{level.value.upper()}:")
        for result in level_results:
            status = "✅" if result.success else "❌"
            lines.append(f"  {status} {result.message}")
            if result.suggestion:
                lines.append(f"     💡 {result.suggestion}")
    
    return "\n".join(lines)


def log_validation_results(results: List[ValidationResult]) -> None:
    """Log validation results using appropriate log levels."""
    for result in results:
        if result.level == ValidationLevel.CRITICAL:
            if result.success:
                logger.info(f"✅ {result.message}")
            else:
                logger.error(f"❌ {result.message}")
                if result.suggestion:
                    logger.error(f"   Suggestion: {result.suggestion}")
        elif result.level == ValidationLevel.WARNING:
            if result.success:
                logger.info(f"✅ {result.message}")
            else:
                logger.warning(f"⚠️ {result.message}")
                if result.suggestion:
                    logger.warning(f"   Suggestion: {result.suggestion}")
        else:  # INFO
            logger.info(f"ℹ️ {result.message}")


def register_config_validation_tools(mcp) -> None:
    """Register configuration validation tools with the MCP server."""
    
    @mcp.tool()
    def validate_mcp_configuration() -> Dict[str, Any]:
        """
        🔍 Validate Claude CLI and MCP configuration for integration issues.
        
        Comprehensive validation of Claude CLI installation, MCP configuration files,
        tool permissions, and startup validation for critical components. Helps prevent
        integration issues like the Claude CLI hanging problem resolved in issue #94.
        
        Features:
        - ✅ Claude CLI availability and version checking
        - 📄 MCP configuration file structure validation
        - 🔐 Tool permissions and allowlist verification
        - 🔧 Environment and dependency validation
        - 💡 Clear error messages and actionable suggestions
        
        Use this tool for: "validate my MCP setup", "check Claude CLI config", "diagnose integration issues"
        
        Returns:
            Comprehensive configuration validation results with recommendations
        """
        logger.info("Configuration validation requested via MCP tool")
        
        can_start, results = validate_configuration()
        
        # Group results by level
        critical_results = [r for r in results if r.level == ValidationLevel.CRITICAL]
        warning_results = [r for r in results if r.level == ValidationLevel.WARNING] 
        info_results = [r for r in results if r.level == ValidationLevel.INFO]
        
        # Calculate summary statistics
        total_checks = len(results)
        passed_checks = len([r for r in results if r.success])
        failed_checks = total_checks - passed_checks
        
        critical_failures = len([r for r in critical_results if not r.success])
        warnings = len([r for r in warning_results if not r.success])
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = "❌ Critical Issues"
            status_level = "critical"
        elif warnings > 0:
            overall_status = "⚠️ Warnings Present"
            status_level = "warning"
        else:
            overall_status = "✅ All Checks Passed"
            status_level = "success"
        
        return {
            "status": "validation_complete",
            "overall_status": overall_status,
            "status_level": status_level,
            "can_start_server": can_start,
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "failed_checks": failed_checks,
                "critical_failures": critical_failures,
                "warnings": warnings
            },
            "results_by_level": {
                "critical": [
                    {
                        "check_name": r.check_name,
                        "success": r.success,
                        "message": r.message,
                        "suggestion": r.suggestion,
                        "details": r.details
                    }
                    for r in critical_results
                ],
                "warning": [
                    {
                        "check_name": r.check_name,
                        "success": r.success,
                        "message": r.message,
                        "suggestion": r.suggestion,
                        "details": r.details
                    }
                    for r in warning_results
                ],
                "info": [
                    {
                        "check_name": r.check_name,
                        "success": r.success,
                        "message": r.message,
                        "suggestion": r.suggestion,
                        "details": r.details
                    }
                    for r in info_results
                ]
            },
            "formatted_output": format_validation_results(results),
            "recommendations": _generate_recommendations(results)
        }
    
    @mcp.tool()
    def check_claude_cli_integration() -> Dict[str, Any]:
        """
        🔧 Quick Claude CLI integration health check.
        
        Fast validation focused specifically on Claude CLI availability and basic
        integration health. Useful for troubleshooting Claude CLI timeout issues
        and basic connectivity problems.
        
        Features:
        - ⚡ Fast Claude CLI availability check
        - 🔍 Basic integration environment validation
        - 🎯 Focused troubleshooting guidance
        - 💊 Quick remediation suggestions
        
        Use this tool for: "quick Claude CLI check", "is Claude CLI working?", "basic integration test"
        
        Returns:
            Focused Claude CLI integration status and basic recommendations
        """
        logger.info("Quick Claude CLI integration check requested")
        
        validator = ConfigurationValidator()
        validator._validate_claude_cli_availability()
        validator._validate_environment_setup()
        
        # Get only Claude CLI related results
        claude_results = [r for r in validator.results if "claude_cli" in r.check_name.lower()]
        env_results = [r for r in validator.results if "environment" in r.check_name.lower()]
        
        all_results = claude_results + env_results
        
        # Determine Claude CLI status
        claude_available = any(r.success for r in claude_results if "availability" in r.check_name)
        
        if claude_available:
            cli_status = "✅ Available"
            status_level = "success"
        else:
            cli_status = "❌ Not Available"
            status_level = "error"
        
        return {
            "status": "claude_cli_check_complete",
            "claude_cli_status": cli_status,
            "status_level": status_level,
            "checks_performed": len(all_results),
            "issues_found": len([r for r in all_results if not r.success]),
            "results": [
                {
                    "check": r.check_name,
                    "success": r.success,
                    "message": r.message,
                    "suggestion": r.suggestion
                }
                for r in all_results
            ],
            "quick_actions": _generate_quick_actions(all_results)
        }


def _generate_recommendations(results: List[ValidationResult]) -> List[str]:
    """Generate actionable recommendations based on validation results."""
    recommendations = []
    
    # Check for common issues and provide specific recommendations
    failed_results = [r for r in results if not r.success]
    
    for result in failed_results:
        if result.suggestion:
            recommendations.append(result.suggestion)
        elif "claude_cli" in result.check_name.lower():
            recommendations.append("Install Claude CLI or verify PATH configuration")
        elif "mcp" in result.check_name.lower():
            recommendations.append("Review MCP configuration file structure")
        elif "permission" in result.check_name.lower():
            recommendations.append("Check tool permissions and access controls")
    
    # Add general recommendations if no specific ones
    if not recommendations:
        recommendations.extend([
            "Configuration looks good - continue with normal operation",
            "Monitor logs for any runtime issues",
            "Consider running periodic validation checks"
        ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recommendations = []
    for rec in recommendations:
        if rec not in seen:
            unique_recommendations.append(rec)
            seen.add(rec)
    
    return unique_recommendations[:5]  # Limit to top 5


def _generate_quick_actions(results: List[ValidationResult]) -> List[str]:
    """Generate quick action items for Claude CLI integration issues."""
    actions = []
    
    failed_checks = [r for r in results if not r.success]
    
    if not failed_checks:
        return ["✅ No action needed - Claude CLI integration looks healthy"]
    
    for result in failed_checks:
        if "availability" in result.check_name and "claude_cli" in result.check_name:
            actions.append("🔧 Install Claude CLI: Visit claude.ai for installation instructions")
        elif "environment" in result.check_name:
            actions.append("🌍 Set PYTHONPATH to include vibe_check source directory")
    
    if not actions:
        actions.append("📋 Review configuration validation results for specific guidance")
    
    return actions