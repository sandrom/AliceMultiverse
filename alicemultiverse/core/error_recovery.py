"""Error recovery and retry logic for resilient operations."""

import time
import logging
import functools
from typing import TypeVar, Callable, Any, Optional, Tuple, List, Type, Union
from pathlib import Path
import random

from .exceptions_extended import (
    RecoverableError,
    FatalError,
    APIRateLimitError,
    APITimeoutError,
    DatabaseTransactionError,
    FileOperationError,
    BatchProcessingError,
    PartialBatchFailure
)

logger = logging.getLogger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(self,
                 max_attempts: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True,
                 recoverable_exceptions: Optional[Tuple[Type[Exception], ...]] = None):
        """Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to prevent thundering herd
            recoverable_exceptions: Tuple of exception types to retry
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.recoverable_exceptions = recoverable_exceptions or (RecoverableError,)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = min(
            self.initial_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


class ErrorRecovery:
    """Provides error recovery and retry mechanisms."""
    
    # Default retry configurations for different scenarios
    DEFAULT_CONFIG = RetryConfig()
    
    API_CONFIG = RetryConfig(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=120.0,
        recoverable_exceptions=(APIRateLimitError, APITimeoutError, RecoverableError)
    )
    
    DATABASE_CONFIG = RetryConfig(
        max_attempts=3,
        initial_delay=0.5,
        max_delay=5.0,
        recoverable_exceptions=(DatabaseTransactionError,)
    )
    
    FILE_CONFIG = RetryConfig(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=2.0,
        recoverable_exceptions=(FileOperationError,)
    )
    
    @classmethod
    def retry_with_backoff(cls,
                          func: Optional[F] = None,
                          *,
                          config: Optional[RetryConfig] = None,
                          on_retry: Optional[Callable[[Exception, int], None]] = None) -> Union[F, Callable[[F], F]]:
        """Decorator to retry function with exponential backoff.
        
        Args:
            func: Function to wrap (or None if using as decorator factory)
            config: Retry configuration
            on_retry: Callback called on each retry with (exception, attempt)
            
        Returns:
            Wrapped function that retries on failure
        """
        if func is None:
            # Called as @retry_with_backoff(config=...)
            return functools.partial(cls.retry_with_backoff, config=config, on_retry=on_retry)
        
        config = config or cls.DEFAULT_CONFIG
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except config.recoverable_exceptions as e:
                    last_exception = e
                    
                    # Check if this is a rate limit error with retry_after
                    if isinstance(e, APIRateLimitError) and e.retry_after:
                        delay = e.retry_after
                    else:
                        delay = config.calculate_delay(attempt)
                    
                    if attempt < config.max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        time.sleep(delay)
                    else:
                        logger.error(f"All {config.max_attempts} attempts failed")
                        
                except FatalError:
                    # Don't retry fatal errors
                    raise
                    
                except Exception as e:
                    # Unexpected error - don't retry
                    logger.error(f"Unexpected error (not retrying): {e}")
                    raise
            
            # All retries exhausted
            if last_exception:
                raise last_exception
        
        return wrapper
    
    @classmethod
    def retry_api_call(cls, func: F) -> F:
        """Decorator specifically for API calls."""
        return cls.retry_with_backoff(func, config=cls.API_CONFIG)
    
    @classmethod
    def retry_database_operation(cls, func: F) -> F:
        """Decorator specifically for database operations."""
        return cls.retry_with_backoff(func, config=cls.DATABASE_CONFIG)
    
    @classmethod
    def retry_file_operation(cls, func: F) -> F:
        """Decorator specifically for file operations."""
        return cls.retry_with_backoff(func, config=cls.FILE_CONFIG)
    
    @staticmethod
    def handle_partial_batch_failure(
        batch_items: List[Any],
        process_func: Callable[[Any], Any],
        continue_on_error: bool = True
    ) -> Tuple[List[Any], List[Tuple[Any, Exception]]]:
        """Process batch with graceful handling of individual failures.
        
        Args:
            batch_items: Items to process
            process_func: Function to process each item
            continue_on_error: Whether to continue processing after errors
            
        Returns:
            Tuple of (successful_results, failed_items_with_errors)
        """
        successful_results = []
        failed_items = []
        
        for item in batch_items:
            try:
                result = process_func(item)
                successful_results.append(result)
            except Exception as e:
                logger.error(f"Failed to process item {item}: {e}")
                failed_items.append((item, e))
                
                if not continue_on_error:
                    # Re-raise with partial results
                    raise PartialBatchFailure(
                        batch_size=len(batch_items),
                        failed_items=[item for item, _ in failed_items],
                        successful_items=successful_results
                    )
        
        if failed_items:
            logger.warning(
                f"Batch processing completed with {len(failed_items)} failures "
                f"out of {len(batch_items)} items"
            )
        
        return successful_results, failed_items
    
    @staticmethod
    def create_dead_letter_queue(name: str = "failed_items") -> 'DeadLetterQueue':
        """Create a dead letter queue for permanently failed items."""
        return DeadLetterQueue(name)


class DeadLetterQueue:
    """Queue for items that permanently failed processing."""
    
    def __init__(self, name: str):
        self.name = name
        self.items: List[Tuple[Any, Exception, int]] = []  # (item, error, attempt_count)
    
    def add(self, item: Any, error: Exception, attempts: int) -> None:
        """Add failed item to queue."""
        self.items.append((item, error, attempts))
        logger.error(
            f"Added item to dead letter queue '{self.name}' after {attempts} attempts: {error}"
        )
    
    def get_all(self) -> List[Tuple[Any, Exception, int]]:
        """Get all items in queue."""
        return self.items.copy()
    
    def clear(self) -> None:
        """Clear the queue."""
        self.items.clear()
    
    def retry_all(self, process_func: Callable[[Any], Any]) -> Tuple[List[Any], List[Tuple[Any, Exception]]]:
        """Retry all items in queue."""
        items_to_retry = [item for item, _, _ in self.items]
        successful, failed = ErrorRecovery.handle_partial_batch_failure(
            items_to_retry,
            process_func
        )
        
        # Remove successful items from queue
        if successful:
            successful_set = set(successful)
            self.items = [
                (item, error, attempts) 
                for item, error, attempts in self.items 
                if item not in successful_set
            ]
        
        return successful, failed
    
    def save_to_file(self, path: Path) -> None:
        """Save dead letter queue to file for manual inspection."""
        import json
        
        data = []
        for item, error, attempts in self.items:
            data.append({
                "item": str(item),
                "error": str(error),
                "error_type": type(error).__name__,
                "attempts": attempts
            })
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(self.items)} failed items to {path}")


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open
    
    def __enter__(self):
        """Check if circuit is open before proceeding."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise RuntimeError("Circuit breaker is open")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Update circuit breaker state based on result."""
        if exc_type is None:
            # Success
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed after successful recovery")
        elif issubclass(exc_type, self.expected_exception):
            # Expected failure
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )
        
        return False  # Don't suppress exceptions
    
    def reset(self) -> None:
        """Manually reset circuit breaker."""
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = 0.0