"""
Retry Logic with Exponential Backoff

Implements retry patterns for Claude CLI calls with intelligent backoff
strategies to handle transient failures gracefully.

Part of Phase 2 implementation for issue #102.
"""

import asyncio
import logging
import random
from typing import Any, Callable, Optional, List
from dataclasses import dataclass

from .circuit_breaker import (
    ClaudeCliCircuitBreaker,
    CircuitBreakerOpenError,
    ClaudeCliError,
    CircuitBreakerConfig,
)


logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    # Maximum number of retry attempts
    max_retries: int = CircuitBreakerConfig.DEFAULT_MAX_RETRIES

    # Base delay for exponential backoff (seconds)
    base_delay: float = CircuitBreakerConfig.DEFAULT_BASE_DELAY

    # Maximum delay between retries (seconds)
    max_delay: float = 60.0

    # Jitter factor to avoid thundering herd (0.0 to 1.0)
    jitter_factor: float = 0.1

    # Exceptions that should trigger retries
    retryable_exceptions: tuple = (
        ClaudeCliError,
        asyncio.TimeoutError,
        ConnectionError,
    )

    # Exceptions that should NOT trigger retries
    non_retryable_exceptions: tuple = (CircuitBreakerOpenError,)


class RetryStrategy:
    """Base class for retry strategies."""

    def calculate_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Calculate delay for the given attempt number."""
        raise NotImplementedError


class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff with optional jitter."""

    def __init__(self, jitter_factor: float = 0.1):
        self.jitter_factor = jitter_factor

    def calculate_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Calculate exponential backoff delay: base_delay * (2 ** attempt)."""
        # Exponential backoff: 1s, 2s, 4s, 8s, ...
        delay = min(base_delay * (2**attempt), max_delay)

        # Add jitter to avoid thundering herd problem
        if self.jitter_factor > 0:
            jitter = delay * self.jitter_factor * random.random()
            delay = delay + jitter

        return delay


class LinearBackoffStrategy(RetryStrategy):
    """Linear backoff strategy."""

    def calculate_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Calculate linear backoff delay: base_delay * attempt."""
        return min(base_delay * (attempt + 1), max_delay)


class FixedBackoffStrategy(RetryStrategy):
    """Fixed delay strategy."""

    def calculate_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Always return the base delay."""
        return min(base_delay, max_delay)


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""

    attempt_number: int
    delay: float
    exception: Optional[Exception] = None
    duration: Optional[float] = None


class RetryExecutor:
    """
    Executes functions with retry logic and circuit breaker integration.

    Combines retry strategies with circuit breaker patterns for robust
    error handling in Claude CLI operations.
    """

    def __init__(
        self,
        circuit_breaker: ClaudeCliCircuitBreaker,
        config: Optional[RetryConfig] = None,
        strategy: Optional[RetryStrategy] = None,
    ):
        self.circuit_breaker = circuit_breaker
        self.config = config or RetryConfig()
        self.strategy = strategy or ExponentialBackoffStrategy(
            self.config.jitter_factor
        )

        logger.debug(
            f"RetryExecutor initialized for circuit breaker '{circuit_breaker.name}'",
            extra={
                "max_retries": self.config.max_retries,
                "base_delay": self.config.base_delay,
                "strategy": self.strategy.__class__.__name__,
            },
        )

    async def execute_with_retry(
        self, func: Callable, *args, timeout: Optional[float] = None, **kwargs
    ) -> Any:
        """
        Execute a function with retry logic and circuit breaker protection.

        Args:
            func: Async function to execute
            *args, **kwargs: Arguments to pass to the function
            timeout: Optional timeout for each attempt

        Returns:
            Result of the function call

        Raises:
            ClaudeCliError: After all retries are exhausted
            CircuitBreakerOpenError: When circuit breaker is open
        """
        attempts: List[RetryAttempt] = []
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Execute through circuit breaker with optional timeout
                if timeout:
                    result = await asyncio.wait_for(
                        self.circuit_breaker.call(func, *args, **kwargs),
                        timeout=timeout,
                    )
                else:
                    result = await self.circuit_breaker.call(func, *args, **kwargs)

                # Success! Log the attempt details if we had retries
                if attempts:
                    logger.info(
                        f"Function succeeded after {attempt} retries",
                        extra={
                            "circuit_breaker": self.circuit_breaker.name,
                            "total_attempts": attempt + 1,
                            "previous_failures": len(attempts),
                        },
                    )

                return result

            except self.config.non_retryable_exceptions as e:
                # Don't retry these exceptions
                logger.debug(
                    f"Non-retryable exception, failing immediately: {e}",
                    extra={"exception_type": type(e).__name__},
                )
                raise

            except self.config.retryable_exceptions as e:
                last_exception = e

                # Record this attempt
                delay = (
                    self.strategy.calculate_delay(
                        attempt, self.config.base_delay, self.config.max_delay
                    )
                    if attempt < self.config.max_retries
                    else 0
                )

                attempts.append(
                    RetryAttempt(attempt_number=attempt, delay=delay, exception=e)
                )

                # If this was our last attempt, don't sleep
                if attempt >= self.config.max_retries:
                    break

                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s",
                    extra={
                        "circuit_breaker": self.circuit_breaker.name,
                        "error": str(e),
                        "attempt": attempt + 1,
                        "max_retries": self.config.max_retries + 1,
                        "delay": delay,
                    },
                )

                # Wait before retrying
                await asyncio.sleep(delay)

            except Exception as e:
                # Unexpected exception, log and re-raise
                logger.error(
                    f"Unexpected exception during retry execution: {e}",
                    extra={"exception_type": type(e).__name__, "attempt": attempt + 1},
                )
                raise ClaudeCliError(f"Unexpected error: {str(e)}")

        # All retries exhausted
        total_attempts = len(attempts)
        logger.error(
            f"All retry attempts exhausted",
            extra={
                "circuit_breaker": self.circuit_breaker.name,
                "total_attempts": total_attempts,
                "max_retries": self.config.max_retries,
                "final_error": str(last_exception),
            },
        )

        raise ClaudeCliError(
            f"Analysis failed after {total_attempts} attempts. "
            f"Last error: {str(last_exception)}"
        )


async def claude_cli_with_retry(
    func: Callable,
    circuit_breaker: ClaudeCliCircuitBreaker,
    max_retries: int = CircuitBreakerConfig.DEFAULT_MAX_RETRIES,
    timeout: Optional[float] = None,
    *args,
    **kwargs,
) -> Any:
    """
    Convenience function for executing Claude CLI calls with retry logic.

    Args:
        func: Async function to execute
        circuit_breaker: Circuit breaker instance to use
        max_retries: Maximum number of retry attempts
        timeout: Optional timeout for each attempt
        *args, **kwargs: Arguments to pass to the function

    Returns:
        Result of the function call

    Example:
        result = await claude_cli_with_retry(
            analyze_content_async,
            circuit_breaker,
            max_retries=2,
            timeout=60,
            content="...",
            task_type="pr_review"
        )
    """
    config = RetryConfig(max_retries=max_retries)
    executor = RetryExecutor(circuit_breaker, config)

    return await executor.execute_with_retry(func, timeout=timeout, *args, **kwargs)


# Global circuit breaker instance for Claude CLI operations
# This can be configured based on environment or injected via dependency injection
_global_circuit_breaker: Optional[ClaudeCliCircuitBreaker] = None


def get_global_circuit_breaker() -> ClaudeCliCircuitBreaker:
    """Get or create the global circuit breaker instance."""
    global _global_circuit_breaker

    if _global_circuit_breaker is None:
        _global_circuit_breaker = ClaudeCliCircuitBreaker(
            failure_threshold=3,
            recovery_timeout=300,  # 5 minutes
            name="global_claude_cli",
        )
        logger.info("Global circuit breaker created")

    return _global_circuit_breaker


def set_global_circuit_breaker(circuit_breaker: ClaudeCliCircuitBreaker):
    """Set a custom global circuit breaker (useful for testing)."""
    global _global_circuit_breaker
    _global_circuit_breaker = circuit_breaker
    logger.info(f"Global circuit breaker set to '{circuit_breaker.name}'")


async def execute_with_global_circuit_breaker(
    func: Callable,
    max_retries: int = CircuitBreakerConfig.DEFAULT_MAX_RETRIES,
    timeout: Optional[float] = None,
    *args,
    **kwargs,
) -> Any:
    """
    Execute a function using the global circuit breaker.

    Convenience function for simple use cases that don't need custom
    circuit breaker configuration.
    """
    circuit_breaker = get_global_circuit_breaker()
    return await claude_cli_with_retry(
        func, circuit_breaker, max_retries=max_retries, timeout=timeout, *args, **kwargs
    )
