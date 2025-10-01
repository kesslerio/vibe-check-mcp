"""
Configuration Loader for Technology Patterns and Responses

Loads and validates configuration from YAML files with staleness detection.
"""

import yaml
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigMetadata:
    """Configuration metadata with staleness tracking"""

    last_updated: str
    version: str
    schema_version: str

    def is_stale(self, max_age_days: int = 30) -> bool:
        """Check if configuration is stale based on last_updated date"""
        try:
            updated_date = datetime.fromisoformat(self.last_updated)
            age = datetime.now() - updated_date
            return age > timedelta(days=max_age_days)
        except (ValueError, TypeError):
            return True  # Consider invalid dates as stale


@dataclass
class LLMModel:
    """LLM model pricing information"""

    name: str
    input_price: float
    output_price: float
    currency: str
    description: str
    last_verified: str
    highlight: bool = False

    def format_pricing(self) -> str:
        """Format pricing for display"""
        return f"${self.input_price}/${self.output_price} per 1M tokens"


class ConfigLoader:
    """Load and manage technology patterns configuration"""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "tech_patterns.yaml"

        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
        self._metadata: Optional[ConfigMetadata] = None

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration from YAML file with caching"""
        if self._config is not None and not force_reload:
            return self._config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)

            # Load metadata
            if "metadata" in self._config:
                metadata = self._config["metadata"]
                self._metadata = ConfigMetadata(
                    last_updated=metadata.get("last_updated", ""),
                    version=metadata.get("version", ""),
                    schema_version=metadata.get("schema_version", ""),
                )

                # Warn if configuration is stale
                if self._metadata.is_stale():
                    logger.warning(
                        f"Configuration is stale (last updated: {self._metadata.last_updated}). "
                        "Consider updating technology patterns and pricing data."
                    )

            return self._config

        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            # Return minimal fallback configuration
            return self._get_fallback_config()

    def get_tech_patterns(self) -> Dict[str, List[str]]:
        """Get technology patterns dictionary"""
        config = self.load_config()
        return config.get("tech_patterns", {})

    def get_problem_indicators(self) -> Dict[str, List[str]]:
        """Get problem type indicators"""
        config = self.load_config()
        return config.get("problem_indicators", {})

    def get_budget_llm_models(self) -> Dict[str, LLMModel]:
        """Get budget LLM models with pricing"""
        config = self.load_config()
        pricing_data = config.get("llm_pricing", {}).get("budget_models", {})

        models = {}
        for key, data in pricing_data.items():
            models[key] = LLMModel(**data)

        return models

    def get_premium_llm_models(self) -> Dict[str, LLMModel]:
        """Get premium LLM models with pricing"""
        config = self.load_config()
        pricing_data = config.get("llm_pricing", {}).get("premium_models", {})

        models = {}
        for key, data in pricing_data.items():
            models[key] = LLMModel(**data)

        return models

    def get_framework_comparisons(self) -> Dict[str, Any]:
        """Get framework comparison templates"""
        config = self.load_config()
        return config.get("framework_comparisons", {})

    def get_metadata(self) -> Optional[ConfigMetadata]:
        """Get configuration metadata"""
        self.load_config()  # Ensure config is loaded
        return self._metadata

    def _get_fallback_config(self) -> Dict[str, Any]:
        """Minimal fallback configuration when YAML loading fails"""
        return {
            "metadata": {
                "last_updated": "2025-06-19",
                "version": "1.0.0",
                "schema_version": "1.0",
            },
            "tech_patterns": {
                "frameworks": [
                    "react",
                    "vue",
                    "angular",
                    "nextjs",
                    "django",
                    "fastapi",
                ],
                "languages": [
                    "python",
                    "javascript",
                    "typescript",
                    "java",
                    "go",
                    "rust",
                ],
                "databases": ["postgres", "mysql", "mongodb", "redis"],
            },
            "problem_indicators": {
                "decision": ["vs", "or", "choose", "decide", "which", "better"]
            },
        }


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get singleton configuration loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def reload_config() -> None:
    """Force reload configuration from disk"""
    global _config_loader
    if _config_loader is not None:
        _config_loader.load_config(force_reload=True)
