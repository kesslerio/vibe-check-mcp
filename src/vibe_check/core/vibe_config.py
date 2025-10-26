"""
Vibe Configuration System

Manages vibe language intensity and messaging style across the tool.
Allows users to adjust the personality level from professional to playful.
"""

import os
import threading
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional


class VibeLevel(str, Enum):
    """
    Vibe intensity levels for consistent messaging tone.

    PROFESSIONAL: Minimal vibe language, enterprise-friendly
    CASUAL: Balanced vibe language with personality
    PLAYFUL: Full vibe language with maximum personality
    """

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    PLAYFUL = "playful"


@dataclass
class VibeMessages:
    """
    Vibe-aware message templates for different contexts.
    Each level provides appropriate tone for the target audience.
    """

    # Success messages
    success: str
    analysis_complete: str
    no_patterns: str

    # Error messages
    error_prefix: str
    failed_prefix: str
    config_error: str
    file_not_found: str
    api_timeout: str

    # Status messages
    starting_analysis: str
    processing_file: str
    github_integration: str

    # Educational messages
    pattern_detected: str
    severity_high: str
    recommendation: str


class VibeConfig:
    """Configuration manager for vibe language settings."""

    def __init__(self, level: Optional[VibeLevel] = None):
        """
        Initialize vibe configuration.

        Args:
            level: Vibe intensity level (defaults to environment or casual)
        """
        self.level = level or self._detect_vibe_level()
        self._messages = self._get_messages_for_level(self.level)

    def _detect_vibe_level(self) -> VibeLevel:
        """Detect vibe level from environment variables or defaults."""
        env_level = os.getenv("VIBE_LEVEL", "casual").lower()

        try:
            return VibeLevel(env_level)
        except ValueError:
            # Log warning for invalid level and default to casual
            logger.warning(
                f"Invalid VIBE_LEVEL '{env_level}' specified. Valid values are: professional, casual, playful. Falling back to 'casual'."
            )
            return VibeLevel.CASUAL

    def _get_messages_for_level(self, level: VibeLevel) -> VibeMessages:
        """Get appropriate messages for the specified vibe level."""

        if level == VibeLevel.PROFESSIONAL:
            return VibeMessages(
                success="✅ Analysis complete",
                analysis_complete="Analysis finished successfully",
                no_patterns="No concerning patterns detected",
                error_prefix="❌ Error:",
                failed_prefix="Failed to",
                config_error="Configuration error",
                file_not_found="File not found",
                api_timeout="Request timeout",
                starting_analysis="Starting analysis",
                processing_file="Processing file",
                github_integration="GitHub integration required",
                pattern_detected="Pattern detected",
                severity_high="High severity",
                recommendation="Recommendation",
            )

        elif level == VibeLevel.CASUAL:
            return VibeMessages(
                success="✅ Vibe check complete",
                analysis_complete="Analysis done - looking good!",
                no_patterns="Clean vibes detected! 🎯",
                error_prefix="😅 Oops:",
                failed_prefix="Couldn't",
                config_error="Config vibes aren't right",
                file_not_found="Can't find that file",
                api_timeout="Request took too long ⏰",
                starting_analysis="Checking the vibes...",
                processing_file="Scanning file for vibe disruptions",
                github_integration="Need GitHub integration for full vibe powers",
                pattern_detected="Vibe pattern spotted",
                severity_high="Major vibe disruption",
                recommendation="Vibe restoration",
            )

        else:  # PLAYFUL
            return VibeMessages(
                success="✨ Vibe check complete - you're killing it!",
                analysis_complete="Analysis done and dusted! 🎉",
                no_patterns="Squeaky clean vibes! No drama here! 🌟",
                error_prefix="🚨 Whoopsie:",
                failed_prefix="Epic fail on",
                config_error="Config vibes are totally off",
                file_not_found="That file is playing hide and seek 📁",
                api_timeout="The vibes took forever to respond ⏰",
                starting_analysis="Time to check those vibes! 🔍",
                processing_file="Hunting for vibe killers in",
                github_integration="Need GitHub magic for maximum vibe powers 🪄",
                pattern_detected="Vibe killer spotted in the wild!",
                severity_high="MAJOR vibe disruption alert! 🚨",
                recommendation="Let's restore those good vibes",
            )

    def get_message(self, key: str) -> str:
        """
        Get a vibe-appropriate message for the given key.

        Args:
            key: Message key (matches VibeMessages attributes)

        Returns:
            Vibe-appropriate message string
        """
        if hasattr(self._messages, key):
            return getattr(self._messages, key)
        else:
            logger.warning(
                f"Unknown vibe message key '{key}'. Available keys: {list(self._messages.__dict__.keys())}"
            )
            return f"[Unknown message: {key}]"

    def set_level(self, level: VibeLevel):
        """
        Change the vibe level and update messages.

        Args:
            level: New vibe intensity level
        """
        self.level = level
        self._messages = self._get_messages_for_level(level)

    def is_professional(self) -> bool:
        """Check if using professional vibe level."""
        return self.level == VibeLevel.PROFESSIONAL

    def is_casual(self) -> bool:
        """Check if using casual vibe level."""
        return self.level == VibeLevel.CASUAL

    def is_playful(self) -> bool:
        """Check if using playful vibe level."""
        return self.level == VibeLevel.PLAYFUL

    def format_pattern_detection(self, pattern_type: str, confidence: float) -> str:
        """
        Format pattern detection message with appropriate vibe level.

        Args:
            pattern_type: Type of pattern detected
            confidence: Detection confidence (0-1)

        Returns:
            Formatted detection message
        """
        # Validate confidence range
        if not 0.0 <= confidence <= 1.0:
            logger.warning(
                f"Invalid confidence value {confidence}. Expected range 0.0-1.0. Clamping to valid range."
            )
            confidence = max(0.0, min(1.0, confidence))

        if self.level == VibeLevel.PROFESSIONAL:
            return f"Pattern detected: {pattern_type} (confidence: {confidence:.2f})"
        elif self.level == VibeLevel.CASUAL:
            return f"Vibe pattern spotted: {pattern_type} ({confidence:.2f} confidence)"
        else:  # PLAYFUL
            return f"🎯 Caught a vibe killer! {pattern_type} spotted with {confidence:.2f} confidence"

    def format_error(self, error_msg: str) -> str:
        """
        Format error message with appropriate vibe level.

        Args:
            error_msg: Original error message

        Returns:
            Vibe-appropriate error message
        """
        prefix = self.get_message("error_prefix")
        return f"{prefix} {error_msg}"

    def get_severity_indicator(self, severity: str) -> str:
        """
        Get vibe-appropriate severity indicator.

        Args:
            severity: Severity level (high, medium, low)

        Returns:
            Formatted severity indicator
        """
        if severity.lower() == "high":
            if self.level == VibeLevel.PROFESSIONAL:
                return "🚨 HIGH PRIORITY"
            elif self.level == VibeLevel.CASUAL:
                return "🚨 Major vibe disruption"
            else:  # PLAYFUL
                return "🚨 MASSIVE vibe killer alert!"
        elif severity.lower() == "medium":
            if self.level == VibeLevel.PROFESSIONAL:
                return "⚠️ MEDIUM PRIORITY"
            elif self.level == VibeLevel.CASUAL:
                return "⚠️ Vibe disruption"
            else:  # PLAYFUL
                return "⚠️ Vibe killer on the loose!"
        else:  # low
            if self.level == VibeLevel.PROFESSIONAL:
                return "💡 CONSIDER"
            elif self.level == VibeLevel.CASUAL:
                return "💡 Minor vibe concern"
            else:  # PLAYFUL
                return "💡 Tiny vibe hiccup"


# Global vibe configuration instance
_global_vibe_config = None
_config_lock = threading.Lock()

logger = logging.getLogger(__name__)


def get_vibe_config() -> VibeConfig:
    """Get the global vibe configuration instance with thread safety."""
    global _global_vibe_config
    if _global_vibe_config is None:
        with _config_lock:
            # Double-checked locking pattern
            if _global_vibe_config is None:
                _global_vibe_config = VibeConfig()
    return _global_vibe_config


def set_vibe_level(level: VibeLevel):
    """Set the global vibe level."""
    config = get_vibe_config()
    config.set_level(level)


def vibe_message(key: str) -> str:
    """Convenience function to get vibe-appropriate message."""
    return get_vibe_config().get_message(key)


def vibe_error(error_msg: str) -> str:
    """Convenience function to format error with vibe level."""
    return get_vibe_config().format_error(error_msg)


def vibe_pattern(pattern_type: str, confidence: float) -> str:
    """Convenience function to format pattern detection."""
    return get_vibe_config().format_pattern_detection(pattern_type, confidence)


def vibe_severity(severity: str) -> str:
    """Convenience function to get severity indicator."""
    return get_vibe_config().get_severity_indicator(severity)
