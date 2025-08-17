import logging
from typing import Dict, Any
from pathlib import Path
from ..core import mcp
from ...tools.contextual_documentation import get_context_manager
from ...config.vibe_check_config import create_vibe_check_directory

logger = logging.getLogger(__name__)

def register_project_context_tools(mcp_instance):
    """Registers project context tools with the MCP server."""
    mcp_instance.add_tool(detect_project_libraries)
    mcp_instance.add_tool(load_project_context)
    mcp_instance.add_tool(create_vibe_check_directory_structure)
    mcp_instance.add_tool(register_project_for_vibe_check)

@mcp.tool()
def detect_project_libraries(
    project_root: str = ".",
    max_files: int = 1000,
    timeout_seconds: int = 30,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    🔍 Detect libraries used in project with performance optimization.
    
    Scans project files for library usage patterns, dependency declarations,
    and import statements to build contextual awareness for analysis tools.
    
    Features:
    - Multi-language support (Python, JavaScript, TypeScript)
    - Performance limits (max files, timeout)
    - Dependency file parsing (package.json, requirements.txt)
    - Import statement analysis
    - Confidence scoring for detections
    - Caching for repeated scans
    
    Args:
        project_root: Root directory to scan (default: current directory)
        max_files: Maximum files to scan for performance (default: 1000)
        timeout_seconds: Timeout for scan operation (default: 30)
        force_refresh: Force refresh of cached results (default: false)
        
    Returns:
        Detection results with libraries, confidence scores, and performance metrics
    """
    try:
        logger.info(f"Detecting project libraries in {project_root}")
        
        # Get context manager
        context_manager = get_context_manager(project_root)
        
        # Configure performance limits
        context_manager.detection_engine.config.context_loading.library_detection.max_files_to_scan = max_files
        context_manager.detection_engine.config.context_loading.library_detection.timeout_seconds = timeout_seconds
        
        # Perform detection
        detection_result = context_manager.detection_engine.scan_project_files(project_root)
        
        # Format results
        return {
            "status": "success",
            "libraries_detected": detection_result.libraries,
            "performance_metrics": {
                "scan_duration_ms": detection_result.scan_duration_ms,
                "files_scanned": detection_result.files_scanned,
                "detection_confidence": detection_result.detection_confidence
            },
            "errors": detection_result.errors,
            "recommendations": [
                f"Found {len(detection_result.libraries)} libraries in {detection_result.files_scanned} files",
                "Consider using Context 7 for up-to-date documentation",
                "Add .vibe-check/config.json for project-specific patterns"
            ]
        }
        
    except Exception as e:
        logger.error(f"Library detection error: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "recommendations": [
                "Check project_root path exists and is accessible",
                "Verify file permissions for scanning",
                "Try with smaller max_files limit"
            ]
        }


@mcp.tool()
def load_project_context(
    project_root: str = ".",
    include_docs: bool = True,
    include_libraries: bool = True,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    📚 Load complete project context for analysis tools.
    
    Combines library detection, project documentation parsing, and pattern
    exceptions to create unified context for project-aware analysis.
    
    Features:
    - Library detection with Context 7 integration
    - Project documentation parsing
    - Pattern exception loading
    - Conflict resolution setup
    - Context caching for performance
    
    Args:
        project_root: Root directory to analyze (default: current directory)
        include_docs: Include project documentation parsing (default: true)
        include_libraries: Include library detection (default: true)
        force_refresh: Force refresh of cached context (default: false)
        
    Returns:
        Complete project context with libraries, documentation, and patterns
    """
    try:
        logger.info(f"Loading project context for {project_root}")
        
        # Get context manager
        context_manager = get_context_manager(project_root)
        
        # Load complete context
        context = context_manager.get_project_context(force_refresh=force_refresh)
        
        # Format results
        return {
            "status": "success",
            "context": {
                "libraries": list(context.library_docs.keys()) if include_libraries else [],
                "project_conventions": context.project_conventions if include_docs else {},
                "pattern_exceptions": context.pattern_exceptions,
                "context_metadata": context.context_metadata
            },
            "summary": {
                "libraries_detected": len(context.library_docs),
                "documentation_sources": len(context.project_conventions),
                "pattern_exceptions": len(context.pattern_exceptions),
                "last_updated": context.context_metadata.get("last_updated", "unknown")
            },
            "recommendations": [
                "Context loaded successfully - analysis tools will use this for project-aware recommendations",
                "Consider adding .vibe-check/config.json for custom patterns",
                "Use Context 7 for latest library documentation"
            ]
        }
        
    except Exception as e:
        logger.error(f"Context loading error: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "recommendations": [
                "Check project_root path exists and is accessible",
                "Verify .vibe-check/ directory structure",
                "Try with force_refresh=true to clear any cached errors"
            ]
        }


@mcp.tool()
def create_vibe_check_directory_structure(
    project_root: str = ".",
    include_examples: bool = True
) -> Dict[str, Any]:
    """
    🏗️ Create .vibe-check/ directory structure with default configuration.
    
    Sets up the complete .vibe-check/ directory with configuration files,
    cache directories, and example patterns for contextual documentation.
    
    Features:
    - Creates .vibe-check/ directory structure
    - Generates default config.json
    - Sets up pattern-exceptions.json
    - Creates context-cache/ directory
    - Includes example configurations
    
    Args:
        project_root: Root directory to create structure in (default: current directory)
        include_examples: Include example configurations (default: true)
        
    Returns:
        Creation status and directory structure details
    """
    try:
        logger.info(f"Creating .vibe-check/ directory structure in {project_root}")
        
        # Create directory structure
        create_vibe_check_directory(project_root)
        
        # Verify creation
        vibe_check_dir = Path(project_root) / ".vibe-check"
        created_files = []
        
        if vibe_check_dir.exists():
            created_files = [str(f.relative_to(vibe_check_dir)) for f in vibe_check_dir.rglob("*") if f.is_file()]
        
        return {
            "status": "success",
            "directory_created": str(vibe_check_dir),
            "files_created": created_files,
            "next_steps": [
                "Edit .vibe-check/config.json to customize library detection",
                "Add project-specific patterns to pattern-exceptions.json",
                "Run detect_project_libraries to populate library context",
                "Use load_project_context to verify setup"
            ],
            "recommendations": [
                "Commit .vibe-check/config.json to version control",
                "Add .vibe-check/context-cache/ to .gitignore",
                "Review pattern-exceptions.json for your project needs"
            ]
        }
        
    except Exception as e:
        logger.error(f"Directory creation error: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "recommendations": [
                "Check write permissions in project_root",
                "Verify directory path exists and is accessible",
                "Try with absolute path to project_root"
            ]
        }


@mcp.tool()
def register_project_for_vibe_check(
    project_name: str,
    project_path: str
) -> Dict[str, Any]:
    """
    📁 Register a project for auto-discovery by vibe_check_mentor.
    
    Once registered, vibe_check_mentor will automatically find this project
    when the project name is mentioned in queries, eliminating the need to
    specify file_paths and working_directory every time.
    
    Args:
        project_name: Short name for the project (e.g., "lead_enrichment")
        project_path: Full path to the project directory
        
    Returns:
        Registration status and current registry
    """
    try:
        from ...mentor.context_manager import get_context_cache
        context_cache = get_context_cache()
        
        # Register the project
        context_cache.register_project(project_name, project_path)
        
        # Load current registry to show all registered projects
        registry = context_cache.load_project_registry()
        
        return {
            "status": "success",
            "message": f"Project '{project_name}' registered successfully",
            "registered_projects": registry,
            "usage_example": f"""
Now you can use vibe_check_mentor without specifying paths:

vibe_check_mentor(
    query="Should I fix the deduplication in {project_name} by disabling aggressive mode?",
    # No need for file_paths or working_directory!
)

The tool will automatically:
1. Detect '{project_name}' in the query
2. Use the registered path: {project_path}
3. Extract file names like 'universal_mapper.py' from the query
4. Load and analyze the actual code
            """
        }
    except Exception as e:
        logger.error(f"Failed to register project: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "recommendations": [
                "Verify the project_path exists and is accessible",
                "Ensure project_name doesn't contain special characters",
                "Check write permissions for ~/.vibe-check/project_registry.json"
            ]
        }
