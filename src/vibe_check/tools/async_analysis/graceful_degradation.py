"""
Graceful Degradation for Async Analysis System

Provides robust fallback mechanisms and enhanced error handling when
the async analysis system is unavailable or experiencing issues.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SystemAvailability(Enum):
    """System availability states."""
    FULLY_AVAILABLE = "fully_available"
    DEGRADED = "degraded"
    PARTIAL_FAILURE = "partial_failure"
    UNAVAILABLE = "unavailable"


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior."""
    
    # Timeout settings
    quick_timeout_seconds: int = 5
    normal_timeout_seconds: int = 30
    extended_timeout_seconds: int = 60
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    exponential_backoff: bool = True
    
    # Fallback thresholds
    max_queue_size_for_fallback: int = 45  # Out of 50
    max_memory_usage_for_fallback: float = 90.0  # Percent
    max_error_rate_for_fallback: float = 50.0  # Percent
    
    # Feature flags
    enable_fast_analysis_fallback: bool = True
    enable_basic_metrics_fallback: bool = True
    enable_queue_bypass: bool = True
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60


class GracefulDegradationManager:
    """
    Manages graceful degradation and fallback mechanisms.
    
    Provides intelligent fallbacks when system components are unavailable,
    ensuring users always get useful responses even during system issues.
    """
    
    def __init__(self, config: FallbackConfig = None):
        self.config = config or FallbackConfig()
        self.system_availability = SystemAvailability.FULLY_AVAILABLE
        self.last_availability_check = 0
        self.consecutive_failures = 0
        self.circuit_breaker_open_until = 0
        self.fallback_stats = {
            "total_requests": 0,
            "fallback_used": 0,
            "circuit_breaker_trips": 0,
            "successful_recoveries": 0
        }
        
        logger.info("GracefulDegradationManager initialized")
    
    async def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Callable,
        operation_name: str,
        timeout_seconds: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a function with fallback on failure.
        
        Args:
            primary_func: Primary function to execute
            fallback_func: Fallback function if primary fails
            operation_name: Name of operation for logging
            timeout_seconds: Custom timeout for operation
            **kwargs: Arguments to pass to functions
            
        Returns:
            Result from primary or fallback function
        """
        self.fallback_stats["total_requests"] += 1
        timeout = timeout_seconds or self.config.normal_timeout_seconds
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            logger.warning(f"Circuit breaker open for {operation_name}, using fallback immediately")
            return await self._execute_fallback(fallback_func, operation_name, **kwargs)
        
        # Try primary function with retries
        for attempt in range(self.config.max_retries):
            try:
                result = await asyncio.wait_for(
                    primary_func(**kwargs),
                    timeout=timeout
                )
                
                # Success - reset failure counter
                if self.consecutive_failures > 0:
                    logger.info(f"Recovery detected for {operation_name} after {self.consecutive_failures} failures")
                    self.fallback_stats["successful_recoveries"] += 1
                    self.consecutive_failures = 0
                
                return self._add_degradation_metadata(result, used_fallback=False, operation=operation_name)
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout in {operation_name} attempt {attempt + 1}/{self.config.max_retries}")
                self._record_failure()
                
                if attempt < self.config.max_retries - 1:
                    await self._backoff_delay(attempt)
                    continue
                    
            except Exception as e:
                logger.error(f"Error in {operation_name} attempt {attempt + 1}: {e}")
                self._record_failure()
                
                if attempt < self.config.max_retries - 1:
                    await self._backoff_delay(attempt)
                    continue
        
        # All primary attempts failed, use fallback
        logger.warning(f"All primary attempts failed for {operation_name}, using fallback")
        return await self._execute_fallback(fallback_func, operation_name, **kwargs)
    
    async def check_system_availability(self) -> SystemAvailability:
        """
        Check current system availability status.
        
        Returns:
            Current system availability level
        """
        current_time = time.time()
        
        # Cache availability check for 30 seconds
        if current_time - self.last_availability_check < 30:
            return self.system_availability
        
        self.last_availability_check = current_time
        
        try:
            # Check async system status
            from .integration import get_system_status, _system_initialized
            
            if not _system_initialized:
                self.system_availability = SystemAvailability.UNAVAILABLE
                return self.system_availability
            
            system_status = await asyncio.wait_for(
                get_system_status(),
                timeout=self.config.quick_timeout_seconds
            )
            
            # Analyze system health
            availability = self._analyze_system_health(system_status)
            self.system_availability = availability
            
            logger.debug(f"System availability: {availability.value}")
            return availability
            
        except asyncio.TimeoutError:
            logger.warning("System availability check timed out")
            self.system_availability = SystemAvailability.DEGRADED
            return self.system_availability
            
        except Exception as e:
            logger.error(f"Error checking system availability: {e}")
            self.system_availability = SystemAvailability.PARTIAL_FAILURE
            return self.system_availability
    
    def get_recommended_strategy(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recommended analysis strategy based on system availability and PR characteristics.
        
        Args:
            pr_data: PR metadata
            
        Returns:
            Recommended strategy with reasoning
        """
        availability = self.system_availability
        total_changes = pr_data.get('additions', 0) + pr_data.get('deletions', 0)
        changed_files = pr_data.get('changed_files', 0)
        
        # Determine PR size category
        if total_changes > 1500 or changed_files > 30:
            pr_size = "massive"
        elif total_changes > 500 or changed_files > 15:
            pr_size = "large"
        elif total_changes > 100 or changed_files > 5:
            pr_size = "medium"
        else:
            pr_size = "small"
        
        strategy = {
            "pr_size": pr_size,
            "system_availability": availability.value,
            "total_changes": total_changes,
            "changed_files": changed_files
        }
        
        # Recommend strategy based on availability and PR size
        if availability == SystemAvailability.FULLY_AVAILABLE:
            if pr_size == "massive":
                strategy.update({
                    "recommended_approach": "async_analysis",
                    "reasoning": "System healthy, PR suitable for background processing",
                    "expected_duration": "15-30 minutes",
                    "confidence": "high"
                })
            elif pr_size == "large":
                strategy.update({
                    "recommended_approach": "chunked_analysis",
                    "reasoning": "System healthy, PR suitable for chunked processing",
                    "expected_duration": "5-15 minutes",
                    "confidence": "high"
                })
            else:
                strategy.update({
                    "recommended_approach": "standard_analysis",
                    "reasoning": "System healthy, PR suitable for standard processing",
                    "expected_duration": "1-5 minutes",
                    "confidence": "high"
                })
        
        elif availability == SystemAvailability.DEGRADED:
            if pr_size in ["massive", "large"]:
                strategy.update({
                    "recommended_approach": "fast_analysis_with_summary",
                    "reasoning": "System degraded, using pattern detection with basic insights",
                    "expected_duration": "30-60 seconds",
                    "confidence": "medium",
                    "limitation": "Reduced analysis depth due to system constraints"
                })
            else:
                strategy.update({
                    "recommended_approach": "standard_analysis",
                    "reasoning": "System degraded but PR small enough for standard processing",
                    "expected_duration": "1-3 minutes",
                    "confidence": "medium"
                })
        
        elif availability in [SystemAvailability.PARTIAL_FAILURE, SystemAvailability.UNAVAILABLE]:
            strategy.update({
                "recommended_approach": "basic_pattern_detection",
                "reasoning": "System unavailable, providing basic pattern analysis only",
                "expected_duration": "10-30 seconds",
                "confidence": "low",
                "limitation": "Limited to pattern detection without LLM analysis"
            })
        
        return strategy
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """
        Get statistics about fallback usage.
        
        Returns:
            Fallback usage statistics
        """
        total = self.fallback_stats["total_requests"]
        fallback_rate = (self.fallback_stats["fallback_used"] / total * 100) if total > 0 else 0
        
        return {
            "total_requests": total,
            "fallback_used": self.fallback_stats["fallback_used"],
            "fallback_rate_percent": round(fallback_rate, 2),
            "circuit_breaker_trips": self.fallback_stats["circuit_breaker_trips"],
            "successful_recoveries": self.fallback_stats["successful_recoveries"],
            "consecutive_failures": self.consecutive_failures,
            "circuit_breaker_open": self._is_circuit_breaker_open(),
            "system_availability": self.system_availability.value
        }
    
    async def _execute_fallback(
        self,
        fallback_func: Callable,
        operation_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute fallback function with error handling."""
        self.fallback_stats["fallback_used"] += 1
        
        try:
            result = await asyncio.wait_for(
                fallback_func(**kwargs),
                timeout=self.config.quick_timeout_seconds
            )
            
            return self._add_degradation_metadata(
                result,
                used_fallback=True,
                operation=operation_name,
                fallback_reason="Primary function failed after retries"
            )
            
        except Exception as e:
            logger.error(f"Fallback function also failed for {operation_name}: {e}")
            
            # Ultimate fallback - return basic error response
            return {
                "status": "fallback_failed",
                "error": f"Both primary and fallback functions failed for {operation_name}",
                "fallback_error": str(e),
                "operation": operation_name,
                "recommendation": "System experiencing significant issues, try again later",
                "degradation_info": {
                    "used_fallback": True,
                    "fallback_failed": True,
                    "system_availability": self.system_availability.value,
                    "timestamp": time.time()
                }
            }
    
    def _add_degradation_metadata(
        self,
        result: Dict[str, Any],
        used_fallback: bool,
        operation: str,
        fallback_reason: str = None
    ) -> Dict[str, Any]:
        """Add degradation metadata to response."""
        if not isinstance(result, dict):
            result = {"data": result}
        
        result["degradation_info"] = {
            "used_fallback": used_fallback,
            "system_availability": self.system_availability.value,
            "operation": operation,
            "timestamp": time.time()
        }
        
        if used_fallback:
            result["degradation_info"]["fallback_reason"] = fallback_reason
            result["degradation_info"]["reduced_functionality"] = True
        
        return result
    
    def _analyze_system_health(self, system_status: Dict[str, Any]) -> SystemAvailability:
        """Analyze system status to determine availability level."""
        try:
            # Check if system is running
            if system_status.get("system_status") != "running":
                return SystemAvailability.UNAVAILABLE
            
            # Check resource monitoring
            resource_info = system_status.get("resource_monitoring", {})
            system_check = resource_info.get("system_status", {})
            
            # Check for critical violations
            if not system_check.get("within_limits", True):
                violations = system_check.get("violations", [])
                if any("exceeded" in v.lower() for v in violations):
                    return SystemAvailability.PARTIAL_FAILURE
            
            # Check queue status
            queue_info = system_status.get("queue_overview", {})
            queue_size = queue_info.get("pending_jobs", 0)
            
            if queue_size > self.config.max_queue_size_for_fallback:
                return SystemAvailability.DEGRADED
            
            # Check warnings
            warnings = system_check.get("warnings", [])
            if warnings:
                return SystemAvailability.DEGRADED
            
            return SystemAvailability.FULLY_AVAILABLE
            
        except Exception as e:
            logger.warning(f"Error analyzing system health: {e}")
            return SystemAvailability.PARTIAL_FAILURE
    
    def _record_failure(self):
        """Record a failure and check circuit breaker."""
        self.consecutive_failures += 1
        
        if self.consecutive_failures >= self.config.circuit_breaker_failure_threshold:
            self.circuit_breaker_open_until = time.time() + self.config.circuit_breaker_timeout_seconds
            self.fallback_stats["circuit_breaker_trips"] += 1
            logger.warning(
                f"Circuit breaker opened after {self.consecutive_failures} consecutive failures. "
                f"Will retry after {self.config.circuit_breaker_timeout_seconds} seconds."
            )
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is currently open."""
        return time.time() < self.circuit_breaker_open_until
    
    async def _backoff_delay(self, attempt: int):
        """Calculate and apply backoff delay."""
        if self.config.exponential_backoff:
            delay = self.config.retry_delay_seconds * (2 ** attempt)
        else:
            delay = self.config.retry_delay_seconds
        
        await asyncio.sleep(delay)


# Global graceful degradation manager
_global_degradation_manager: Optional[GracefulDegradationManager] = None


def get_global_degradation_manager(config: FallbackConfig = None) -> GracefulDegradationManager:
    """Get or create the global degradation manager."""
    global _global_degradation_manager
    
    if _global_degradation_manager is None:
        _global_degradation_manager = GracefulDegradationManager(config)
    
    return _global_degradation_manager


# Convenience functions for common fallback patterns

async def async_analysis_with_fallback(pr_number: int, repository: str, pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempt async analysis with intelligent fallback.
    
    Args:
        pr_number: PR number
        repository: Repository name
        pr_data: PR metadata
        
    Returns:
        Analysis result with fallback information
    """
    degradation_manager = get_global_degradation_manager()
    
    async def primary_func(**kwargs):
        from .integration import start_async_analysis
        return await start_async_analysis(kwargs["pr_number"], kwargs["repository"], kwargs["pr_data"])
    
    async def fallback_func(**kwargs):
        from ..analyze_pr_nollm import analyze_pr_nollm
        return analyze_pr_nollm(
            kwargs["pr_number"],
            kwargs["repository"],
            analysis_mode="quick",
            detail_level="brief"
        )
    
    return await degradation_manager.execute_with_fallback(
        primary_func=primary_func,
        fallback_func=fallback_func,
        operation_name="async_analysis",
        pr_number=pr_number,
        repository=repository,
        pr_data=pr_data
    )


async def system_status_with_fallback() -> Dict[str, Any]:
    """
    Get system status with fallback to basic information.
    
    Returns:
        System status with fallback information
    """
    degradation_manager = get_global_degradation_manager()
    
    async def primary_func(**kwargs):
        # Implement the actual system status logic here to avoid circular import
        from .queue_manager import get_global_queue
        from .worker import get_global_worker_manager
        from .status_tracker import StatusTracker
        from .resource_monitor import get_global_resource_monitor
        from .integration import _status_tracker, _system_initialized
        
        if not _system_initialized:
            return {
                "system_status": "not_initialized",
                "message": "Async analysis system is not running"
            }
        
        queue = await get_global_queue()
        worker_manager = await get_global_worker_manager(queue)
        
        # Get resource monitoring status
        resource_monitor = get_global_resource_monitor()
        resource_status = resource_monitor.get_comprehensive_status()
        
        return {
            "system_status": "running",
            "queue_overview": _status_tracker.get_queue_overview(queue),
            "worker_status": worker_manager.get_worker_status(),
            "resource_monitoring": resource_status,
            "system_initialized": _system_initialized
        }
    
    async def fallback_func(**kwargs):
        return {
            "system_status": "basic_info_only",
            "message": "Detailed system status unavailable, providing basic information",
            "availability_check": degradation_manager.system_availability.value,
            "timestamp": time.time()
        }
    
    return await degradation_manager.execute_with_fallback(
        primary_func=primary_func,
        fallback_func=fallback_func,
        operation_name="system_status",
        timeout_seconds=5
    )