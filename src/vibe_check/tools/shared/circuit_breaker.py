"""
Circuit Breaker Pattern for Claude CLI Reliability

Implements Phase 2 of issue #102 - circuit breaker pattern to handle
Claude CLI failures gracefully and prevent cascading failures.

The circuit breaker has three states:
- CLOSED: Normal operation, calls go through
- OPEN: Circuit is broken, calls fail fast
- HALF_OPEN: Testing if the service has recovered
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Circuit broken, fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerConfig:
    """Configuration constants for circuit breaker behavior."""
    
    # Number of failures before opening circuit
    DEFAULT_FAILURE_THRESHOLD = 3
    
    # Time to wait before attempting recovery (seconds)
    DEFAULT_RECOVERY_TIMEOUT = 300  # 5 minutes
    
    # Maximum number of retry attempts
    DEFAULT_MAX_RETRIES = 2
    
    # Base delay for exponential backoff (seconds)
    DEFAULT_BASE_DELAY = 1
    
    # Health monitoring thresholds
    HEALTH_MIN_SUCCESS_RATE = 0.7
    HEALTH_MAX_CONSECUTIVE_FAILURES = 5
    HEALTH_MAX_TIME_WITHOUT_SUCCESS = 600  # 10 minutes


@dataclass
class CircuitBreakerStats:
    """Statistics tracked by the circuit breaker."""
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    circuit_opened_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate current success rate."""
        return self.success_count / self.total_calls if self.total_calls > 0 else 0.0
    
    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        return self.failure_count / self.total_calls if self.total_calls > 0 else 0.0


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and calls are rejected."""
    pass


class ClaudeCliError(Exception):
    """Raised when Claude CLI analysis fails."""
    pass


class ClaudeCliCircuitBreaker:
    """
    Circuit breaker for Claude CLI reliability.
    
    Prevents cascading failures by tracking Claude CLI errors and
    temporarily disabling calls when failure threshold is exceeded.
    """
    
    def __init__(
        self,
        failure_threshold: int = CircuitBreakerConfig.DEFAULT_FAILURE_THRESHOLD,
        recovery_timeout: int = CircuitBreakerConfig.DEFAULT_RECOVERY_TIMEOUT,
        name: str = "claude_cli"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        
        # State management
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        
        # Timing
        self.state_changed_at = time.time()
        
        logger.info(
            f"Circuit breaker '{name}' initialized",
            extra={
                "failure_threshold": failure_threshold,
                "recovery_timeout": recovery_timeout
            }
        )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call a function through the circuit breaker.
        
        Args:
            func: Function to call (should be async)
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
            ClaudeCliError: When the underlying function fails
        """
        # Check circuit state
        await self._check_and_update_state()
        
        if self.state == CircuitBreakerState.OPEN:
            self._record_rejected_call()
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service temporarily unavailable for {self.recovery_timeout}s."
            )
        
        # Attempt the call
        self.stats.total_calls += 1
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            
            logger.debug(
                f"Circuit breaker '{self.name}' call succeeded",
                extra={
                    "duration": time.time() - start_time,
                    "success_rate": self.stats.success_rate
                }
            )
            
            return result
            
        except Exception as e:
            self._record_failure(e)
            
            logger.warning(
                f"Circuit breaker '{self.name}' call failed",
                extra={
                    "error": str(e),
                    "consecutive_failures": self.stats.consecutive_failures,
                    "failure_rate": self.stats.failure_rate
                }
            )
            
            raise ClaudeCliError(f"Analysis failed: {str(e)}")
    
    async def _check_and_update_state(self):
        """Check if circuit breaker state should change."""
        current_time = time.time()
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if current_time - self.state_changed_at >= self.recovery_timeout:
                self._transition_to_half_open()
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # In half-open state, let one call through to test recovery
            pass
    
    def _record_success(self):
        """Record a successful call."""
        self.stats.success_count += 1
        self.stats.consecutive_failures = 0
        self.stats.last_success_time = time.time()
        
        # If we were in HALF_OPEN state, close the circuit
        if self.state == CircuitBreakerState.HALF_OPEN:
            self._transition_to_closed()
    
    def _record_failure(self, error: Exception):
        """Record a failed call."""
        self.stats.failure_count += 1
        self.stats.consecutive_failures += 1
        self.stats.last_failure_time = time.time()
        
        # Check if we should open the circuit
        if (self.state == CircuitBreakerState.CLOSED and 
            self.stats.consecutive_failures >= self.failure_threshold):
            self._transition_to_open()
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during recovery test, go back to OPEN
            self._transition_to_open()
    
    def _record_rejected_call(self):
        """Record a call that was rejected due to open circuit."""
        # Don't count rejected calls in total_calls to avoid skewing success rate
        pass
    
    def _transition_to_open(self):
        """Transition circuit breaker to OPEN state."""
        previous_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.state_changed_at = time.time()
        self.stats.circuit_opened_count += 1
        
        logger.warning(
            f"Circuit breaker '{self.name}' opened",
            extra={
                "previous_state": previous_state.value,
                "consecutive_failures": self.stats.consecutive_failures,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout
            }
        )
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state."""
        previous_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.state_changed_at = time.time()
        
        logger.info(
            f"Circuit breaker '{self.name}' half-opened",
            extra={
                "previous_state": previous_state.value,
                "testing_recovery": True
            }
        )
    
    def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state."""
        previous_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.state_changed_at = time.time()
        
        logger.info(
            f"Circuit breaker '{self.name}' closed",
            extra={
                "previous_state": previous_state.value,
                "recovery_successful": True,
                "success_rate": self.stats.success_rate
            }
        )
    
    @property
    def is_healthy(self) -> bool:
        """Check if the service behind the circuit breaker is healthy."""
        current_time = time.time()
        
        # Basic health checks
        if self.stats.consecutive_failures >= CircuitBreakerConfig.HEALTH_MAX_CONSECUTIVE_FAILURES:
            return False
        
        if self.stats.success_rate < CircuitBreakerConfig.HEALTH_MIN_SUCCESS_RATE:
            return False
        
        if (self.stats.last_success_time and 
            current_time - self.stats.last_success_time > CircuitBreakerConfig.HEALTH_MAX_TIME_WITHOUT_SUCCESS):
            return False
        
        return True
    
    def reset(self):
        """Reset circuit breaker to initial state (for testing)."""
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self.state_changed_at = time.time()
        
        logger.info(f"Circuit breaker '{self.name}' reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status for monitoring."""
        current_time = time.time()
        
        return {
            "name": self.name,
            "state": self.state.value,
            "is_healthy": self.is_healthy,
            "stats": {
                "total_calls": self.stats.total_calls,
                "success_count": self.stats.success_count,
                "failure_count": self.stats.failure_count,
                "consecutive_failures": self.stats.consecutive_failures,
                "success_rate": self.stats.success_rate,
                "failure_rate": self.stats.failure_rate,
                "circuit_opened_count": self.stats.circuit_opened_count
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout
            },
            "timing": {
                "state_changed_at": self.state_changed_at,
                "time_in_current_state": current_time - self.state_changed_at,
                "last_success_time": self.stats.last_success_time,
                "last_failure_time": self.stats.last_failure_time
            }
        }