"""
Vibe Check Configuration Schema

Defines the structure for .vibe-check/ directory configuration files
and provides validation for project-specific contextual settings.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class LibraryDetectionConfig:
    """Configuration for library detection settings"""

    languages: List[str] = None
    depth: str = "imports_only"  # "imports_only" or "full_dependency_tree"
    max_files_to_scan: int = 1000
    timeout_seconds: int = 30
    exclude_patterns: List[str] = None

    def __post_init__(self):
        if self.languages is None:
            self.languages = ["python", "javascript", "typescript"]
        if self.exclude_patterns is None:
            self.exclude_patterns = ["node_modules/", "__pycache__/", ".git/", "*.pyc"]


@dataclass
class ProjectDocsConfig:
    """Configuration for project documentation parsing"""

    paths: List[str] = None
    exclude_patterns: List[str] = None
    max_file_size_kb: int = 500

    def __post_init__(self):
        if self.paths is None:
            self.paths = ["docs/", "README.md", "CONTRIBUTING.md", "ARCHITECTURE.md"]
        if self.exclude_patterns is None:
            self.exclude_patterns = ["node_modules/", "__pycache__/", ".git/"]


@dataclass
class PerformanceConfig:
    """Performance optimization settings"""

    max_files_to_scan: int = 1000
    timeout_seconds: int = 30
    lazy_loading: bool = True
    parallel_processing: bool = True
    cache_size_mb: int = 100


@dataclass
class ContextLoadingConfig:
    """Main context loading configuration"""

    enabled: bool = True
    cache_duration_minutes: int = 60
    library_detection: LibraryDetectionConfig = None
    project_docs: ProjectDocsConfig = None
    performance: PerformanceConfig = None

    def __post_init__(self):
        if self.library_detection is None:
            self.library_detection = LibraryDetectionConfig()
        if self.project_docs is None:
            self.project_docs = ProjectDocsConfig()
        if self.performance is None:
            self.performance = PerformanceConfig()


@dataclass
class LibraryOverride:
    """Library-specific configuration override"""

    version: str
    patterns: List[str]
    exceptions: List[str] = None
    architecture: Optional[str] = None

    def __post_init__(self):
        if self.exceptions is None:
            self.exceptions = []


@dataclass
class VibeCheckConfig:
    """Complete .vibe-check/config.json configuration"""

    context_loading: ContextLoadingConfig = None
    libraries: Dict[str, LibraryOverride] = None
    project_patterns: Dict[str, str] = None
    exceptions: List[str] = None

    def __post_init__(self):
        if self.context_loading is None:
            self.context_loading = ContextLoadingConfig()
        if self.libraries is None:
            self.libraries = {}
        if self.project_patterns is None:
            self.project_patterns = {}
        if self.exceptions is None:
            self.exceptions = []


class VibeCheckConfigLoader:
    """Loads and validates .vibe-check/config.json configurations"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.config_dir = self.project_root / ".vibe-check"
        self.config_file = self.config_dir / "config.json"

    def load_config(self) -> VibeCheckConfig:
        """Load configuration from .vibe-check/config.json"""
        if not self.config_file.exists():
            logger.info(
                f"No .vibe-check/config.json found at {self.config_file}, using defaults"
            )
            return VibeCheckConfig()

        try:
            with open(self.config_file, "r") as f:
                config_data = json.load(f)

            # Convert dict to dataclass
            config = self._dict_to_config(config_data)
            logger.info(f"Loaded vibe-check configuration from {self.config_file}")
            return config

        except Exception as e:
            logger.error(f"Error loading .vibe-check/config.json: {e}")
            logger.info("Using default configuration")
            return VibeCheckConfig()

    def create_default_config(self) -> None:
        """Create default .vibe-check/config.json file"""
        self.config_dir.mkdir(exist_ok=True)

        default_config = {
            "context_loading": {
                "enabled": True,
                "cache_duration_minutes": 60,
                "library_detection": {
                    "languages": ["python", "javascript", "typescript"],
                    "depth": "imports_only",
                    "max_files_to_scan": 1000,
                    "timeout_seconds": 30,
                    "exclude_patterns": [
                        "node_modules/",
                        "__pycache__/",
                        ".git/",
                        "*.pyc",
                    ],
                },
                "project_docs": {
                    "paths": [
                        "docs/",
                        "README.md",
                        "CONTRIBUTING.md",
                        "ARCHITECTURE.md",
                    ],
                    "exclude_patterns": ["node_modules/", "__pycache__/", ".git/"],
                    "max_file_size_kb": 500,
                },
                "performance": {
                    "max_files_to_scan": 1000,
                    "timeout_seconds": 30,
                    "lazy_loading": True,
                    "parallel_processing": True,
                    "cache_size_mb": 100,
                },
            },
            "libraries": {
                "react": {
                    "version": "18.x",
                    "patterns": ["hooks-preferred", "functional-components"],
                    "exceptions": ["legacy-class-components-in-tests"],
                },
                "fastapi": {
                    "version": "0.100+",
                    "patterns": ["dependency-injection", "async-preferred"],
                    "architecture": "microservices",
                },
            },
            "project_patterns": {
                "authentication": "custom-jwt-required",
                "database": "postgresql-preferred",
                "testing": "pytest-with-coverage",
            },
            "exceptions": [
                "custom-auth-required-for-compliance",
                "monorepo-shared-utilities-allowed",
            ],
        }

        with open(self.config_file, "w") as f:
            json.dump(default_config, f, indent=2)

        logger.info(f"Created default .vibe-check/config.json at {self.config_file}")

    def _dict_to_config(self, data: Dict[str, Any]) -> VibeCheckConfig:
        """Convert dictionary to VibeCheckConfig dataclass"""
        try:
            # Parse context_loading section
            context_loading_data = data.get("context_loading", {})

            # Parse library detection config
            lib_detection_data = context_loading_data.get("library_detection", {})
            library_detection = LibraryDetectionConfig(
                languages=lib_detection_data.get("languages"),
                depth=lib_detection_data.get("depth", "imports_only"),
                max_files_to_scan=lib_detection_data.get("max_files_to_scan", 1000),
                timeout_seconds=lib_detection_data.get("timeout_seconds", 30),
                exclude_patterns=lib_detection_data.get("exclude_patterns"),
            )

            # Parse project docs config
            proj_docs_data = context_loading_data.get("project_docs", {})
            project_docs = ProjectDocsConfig(
                paths=proj_docs_data.get("paths"),
                exclude_patterns=proj_docs_data.get("exclude_patterns"),
                max_file_size_kb=proj_docs_data.get("max_file_size_kb", 500),
            )

            # Parse performance config
            perf_data = context_loading_data.get("performance", {})
            performance = PerformanceConfig(
                max_files_to_scan=perf_data.get("max_files_to_scan", 1000),
                timeout_seconds=perf_data.get("timeout_seconds", 30),
                lazy_loading=perf_data.get("lazy_loading", True),
                parallel_processing=perf_data.get("parallel_processing", True),
                cache_size_mb=perf_data.get("cache_size_mb", 100),
            )

            # Create context loading config
            context_loading = ContextLoadingConfig(
                enabled=context_loading_data.get("enabled", True),
                cache_duration_minutes=context_loading_data.get(
                    "cache_duration_minutes", 60
                ),
                library_detection=library_detection,
                project_docs=project_docs,
                performance=performance,
            )

            # Parse library overrides
            libraries = {}
            for lib_name, lib_data in data.get("libraries", {}).items():
                libraries[lib_name] = LibraryOverride(
                    version=lib_data.get("version", "latest"),
                    patterns=lib_data.get("patterns", []),
                    exceptions=lib_data.get("exceptions", []),
                    architecture=lib_data.get("architecture"),
                )

            # Parse project patterns and exceptions
            project_patterns = data.get("project_patterns", {})
            exceptions = data.get("exceptions", [])

            return VibeCheckConfig(
                context_loading=context_loading,
                libraries=libraries,
                project_patterns=project_patterns,
                exceptions=exceptions,
            )

        except Exception as e:
            logger.error(f"Error parsing config dictionary: {e}")
            logger.info("Falling back to default configuration")
            return VibeCheckConfig()

    def validate_config(self, config: VibeCheckConfig) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Validate performance settings
        if config.context_loading.performance.max_files_to_scan <= 0:
            errors.append("max_files_to_scan must be positive")

        if config.context_loading.performance.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")

        if config.context_loading.cache_duration_minutes <= 0:
            errors.append("cache_duration_minutes must be positive")

        # Validate library detection
        supported_languages = ["python", "javascript", "typescript", "go", "rust"]
        for lang in config.context_loading.library_detection.languages:
            if lang not in supported_languages:
                errors.append(f"Unsupported language: {lang}")

        return errors


def get_vibe_check_config(project_root: str = ".") -> VibeCheckConfig:
    """Convenience function to get vibe-check configuration"""
    loader = VibeCheckConfigLoader(project_root)
    return loader.load_config()


def create_vibe_check_directory(project_root: str = ".") -> None:
    """Create .vibe-check/ directory structure with default files"""
    config_dir = Path(project_root) / ".vibe-check"
    config_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (config_dir / "context-cache").mkdir(exist_ok=True)

    # Create default config.json
    loader = VibeCheckConfigLoader(project_root)
    if not loader.config_file.exists():
        loader.create_default_config()

    # Create pattern-exceptions.json
    exceptions_file = config_dir / "pattern-exceptions.json"
    if not exceptions_file.exists():
        default_exceptions = {
            "approved_patterns": [
                "custom-auth-required-for-compliance",
                "legacy-components-in-maintenance-mode",
            ],
            "temporary_exceptions": ["migration-phase-mixed-patterns"],
            "reasoning": {
                "custom-auth-required-for-compliance": "GDPR requirements mandate custom authentication flow",
                "legacy-components-in-maintenance-mode": "Gradual migration strategy approved by architecture team",
            },
        }

        with open(exceptions_file, "w") as f:
            json.dump(default_exceptions, f, indent=2)

    # Create library-context.json (this will be populated by detection)
    library_context_file = config_dir / "library-context.json"
    if not library_context_file.exists():
        with open(library_context_file, "w") as f:
            json.dump(
                {
                    "detected_libraries": {},
                    "last_scan": None,
                    "scan_settings": {"max_files_scanned": 0, "scan_duration_ms": 0},
                },
                f,
                indent=2,
            )

    logger.info(f"Created .vibe-check/ directory structure at {config_dir}")
