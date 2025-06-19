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


# TODO: Review unreachable code - class ErrorRecovery:
# TODO: Review unreachable code - """Provides error recovery and retry mechanisms."""
    
# TODO: Review unreachable code - # Default retry configurations for different scenarios
# TODO: Review unreachable code - DEFAULT_CONFIG = RetryConfig()
    
# TODO: Review unreachable code - API_CONFIG = RetryConfig(
# TODO: Review unreachable code - max_attempts=5,
# TODO: Review unreachable code - initial_delay=2.0,
# TODO: Review unreachable code - max_delay=120.0,
# TODO: Review unreachable code - recoverable_exceptions=(APIRateLimitError, APITimeoutError, RecoverableError)
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - DATABASE_CONFIG = RetryConfig(
# TODO: Review unreachable code - max_attempts=3,
# TODO: Review unreachable code - initial_delay=0.5,
# TODO: Review unreachable code - max_delay=5.0,
# TODO: Review unreachable code - recoverable_exceptions=(DatabaseTransactionError,)
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - FILE_CONFIG = RetryConfig(
# TODO: Review unreachable code - max_attempts=3,
# TODO: Review unreachable code - initial_delay=0.1,
# TODO: Review unreachable code - max_delay=2.0,
# TODO: Review unreachable code - recoverable_exceptions=(FileOperationError,)
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - @classmethod
# TODO: Review unreachable code - def retry_with_backoff(cls,
# TODO: Review unreachable code - func: Optional[F] = None,
# TODO: Review unreachable code - *,
# TODO: Review unreachable code - config: Optional[RetryConfig] = None,
# TODO: Review unreachable code - on_retry: Optional[Callable[[Exception, int], None]] = None) -> Union[F, Callable[[F], F]]:
# TODO: Review unreachable code - """Decorator to retry function with exponential backoff.
        
# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - func: Function to wrap (or None if using as decorator factory)
# TODO: Review unreachable code - config: Retry configuration
# TODO: Review unreachable code - on_retry: Callback called on each retry with (exception, attempt)
            
# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Wrapped function that retries on failure
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if func is None:
# TODO: Review unreachable code - # Called as @retry_with_backoff(config=...)
# TODO: Review unreachable code - return functools.partial(cls.retry_with_backoff, config=config, on_retry=on_retry)
        
# TODO: Review unreachable code - config = config or cls.DEFAULT_CONFIG
        
# TODO: Review unreachable code - @functools.wraps(func)
# TODO: Review unreachable code - def wrapper(*args, **kwargs):
# TODO: Review unreachable code - last_exception = None
            
# TODO: Review unreachable code - for attempt in range(1, config.max_attempts + 1):
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - return func(*args, **kwargs)
                    
# TODO: Review unreachable code - except config.recoverable_exceptions as e:
# TODO: Review unreachable code - last_exception = e
                    
# TODO: Review unreachable code - # Check if this is a rate limit error with retry_after
# TODO: Review unreachable code - if isinstance(e, APIRateLimitError) and e.retry_after:
# TODO: Review unreachable code - delay = e.retry_after
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - delay = config.calculate_delay(attempt)
                    
# TODO: Review unreachable code - if attempt < config.max_attempts:
# TODO: Review unreachable code - logger.warning(
# TODO: Review unreachable code - f"Attempt {attempt}/{config.max_attempts} failed: {e}. "
# TODO: Review unreachable code - f"Retrying in {delay:.1f}s..."
# TODO: Review unreachable code - )
                        
# TODO: Review unreachable code - if on_retry:
# TODO: Review unreachable code - on_retry(e, attempt)
                        
# TODO: Review unreachable code - time.sleep(delay)
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - logger.error(f"All {config.max_attempts} attempts failed")
                        
# TODO: Review unreachable code - except FatalError:
# TODO: Review unreachable code - # Don't retry fatal errors
# TODO: Review unreachable code - raise
                    
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - # Unexpected error - don't retry
# TODO: Review unreachable code - logger.error(f"Unexpected error (not retrying): {e}")
# TODO: Review unreachable code - raise
            
# TODO: Review unreachable code - # All retries exhausted
# TODO: Review unreachable code - if last_exception:
# TODO: Review unreachable code - raise last_exception
        
# TODO: Review unreachable code - return wrapper
    
# TODO: Review unreachable code - @classmethod
# TODO: Review unreachable code - def retry_api_call(cls, func: F) -> F:
# TODO: Review unreachable code - """Decorator specifically for API calls."""
# TODO: Review unreachable code - return cls.retry_with_backoff(func, config=cls.API_CONFIG)
    
# TODO: Review unreachable code - @classmethod
# TODO: Review unreachable code - def retry_database_operation(cls, func: F) -> F:
# TODO: Review unreachable code - """Decorator specifically for database operations."""
# TODO: Review unreachable code - return cls.retry_with_backoff(func, config=cls.DATABASE_CONFIG)
    
# TODO: Review unreachable code - @classmethod
# TODO: Review unreachable code - def retry_file_operation(cls, func: F) -> F:
# TODO: Review unreachable code - """Decorator specifically for file operations."""
# TODO: Review unreachable code - return cls.retry_with_backoff(func, config=cls.FILE_CONFIG)
    
# TODO: Review unreachable code - @staticmethod
# TODO: Review unreachable code - def handle_partial_batch_failure(
# TODO: Review unreachable code - batch_items: List[Any],
# TODO: Review unreachable code - process_func: Callable[[Any], Any],
# TODO: Review unreachable code - continue_on_error: bool = True
# TODO: Review unreachable code - ) -> Tuple[List[Any], List[Tuple[Any, Exception]]]:
# TODO: Review unreachable code - """Process batch with graceful handling of individual failures.
        
# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - batch_items: Items to process
# TODO: Review unreachable code - process_func: Function to process each item
# TODO: Review unreachable code - continue_on_error: Whether to continue processing after errors
            
# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Tuple of (successful_results, failed_items_with_errors)
# TODO: Review unreachable code - """
# TODO: Review unreachable code - successful_results = []
# TODO: Review unreachable code - failed_items = []
        
# TODO: Review unreachable code - for item in batch_items:
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - result = process_func(item)
# TODO: Review unreachable code - successful_results.append(result)
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.error(f"Failed to process item {item}: {e}")
# TODO: Review unreachable code - failed_items.append((item, e))
                
# TODO: Review unreachable code - if not continue_on_error:
# TODO: Review unreachable code - # Re-raise with partial results
# TODO: Review unreachable code - raise PartialBatchFailure(
# TODO: Review unreachable code - batch_size=len(batch_items),
# TODO: Review unreachable code - failed_items=[item for item, _ in failed_items],
# TODO: Review unreachable code - successful_items=successful_results
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - if failed_items:
# TODO: Review unreachable code - logger.warning(
# TODO: Review unreachable code - f"Batch processing completed with {len(failed_items)} failures "
# TODO: Review unreachable code - f"out of {len(batch_items)} items"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - return successful_results, failed_items
    
# TODO: Review unreachable code - @staticmethod
# TODO: Review unreachable code - def create_dead_letter_queue(name: str = "failed_items") -> 'DeadLetterQueue':
# TODO: Review unreachable code - """Create a dead letter queue for permanently failed items."""
# TODO: Review unreachable code - return DeadLetterQueue(name)


# TODO: Review unreachable code - class DeadLetterQueue:
# TODO: Review unreachable code - """Queue for items that permanently failed processing."""
    
# TODO: Review unreachable code - def __init__(self, name: str):
# TODO: Review unreachable code - self.name = name
# TODO: Review unreachable code - self.items: List[Tuple[Any, Exception, int]] = []  # (item, error, attempt_count)
    
# TODO: Review unreachable code - def add(self, item: Any, error: Exception, attempts: int) -> None:
# TODO: Review unreachable code - """Add failed item to queue."""
# TODO: Review unreachable code - self.items.append((item, error, attempts))
# TODO: Review unreachable code - logger.error(
# TODO: Review unreachable code - f"Added item to dead letter queue '{self.name}' after {attempts} attempts: {error}"
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - def get_all(self) -> List[Tuple[Any, Exception, int]]:
# TODO: Review unreachable code - """Get all items in queue."""
# TODO: Review unreachable code - return self.items.copy()
    
# TODO: Review unreachable code - def clear(self) -> None:
# TODO: Review unreachable code - """Clear the queue."""
# TODO: Review unreachable code - self.items.clear()
    
# TODO: Review unreachable code - def retry_all(self, process_func: Callable[[Any], Any]) -> Tuple[List[Any], List[Tuple[Any, Exception]]]:
# TODO: Review unreachable code - """Retry all items in queue."""
# TODO: Review unreachable code - items_to_retry = [item for item, _, _ in self.items]
# TODO: Review unreachable code - successful, failed = ErrorRecovery.handle_partial_batch_failure(
# TODO: Review unreachable code - items_to_retry,
# TODO: Review unreachable code - process_func
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - # Remove successful items from queue
# TODO: Review unreachable code - if successful:
# TODO: Review unreachable code - successful_set = set(successful)
# TODO: Review unreachable code - self.items = [
# TODO: Review unreachable code - (item, error, attempts) 
# TODO: Review unreachable code - for item, error, attempts in self.items 
# TODO: Review unreachable code - if item not in successful_set
# TODO: Review unreachable code - ]
        
# TODO: Review unreachable code - return successful, failed
    
# TODO: Review unreachable code - def save_to_file(self, path: Path) -> None:
# TODO: Review unreachable code - """Save dead letter queue to file for manual inspection."""
# TODO: Review unreachable code - import json
        
# TODO: Review unreachable code - data = []
# TODO: Review unreachable code - for item, error, attempts in self.items:
# TODO: Review unreachable code - data.append({
# TODO: Review unreachable code - "item": str(item),
# TODO: Review unreachable code - "error": str(error),
# TODO: Review unreachable code - "error_type": type(error).__name__,
# TODO: Review unreachable code - "attempts": attempts
# TODO: Review unreachable code - })
        
# TODO: Review unreachable code - with open(path, 'w') as f:
# TODO: Review unreachable code - json.dump(data, f, indent=2)
        
# TODO: Review unreachable code - logger.info(f"Saved {len(self.items)} failed items to {path}")


# TODO: Review unreachable code - class CircuitBreaker:
# TODO: Review unreachable code - """Circuit breaker pattern for preventing cascading failures."""
    
# TODO: Review unreachable code - def __init__(self,
# TODO: Review unreachable code - failure_threshold: int = 5,
# TODO: Review unreachable code - recovery_timeout: float = 60.0,
# TODO: Review unreachable code - expected_exception: Type[Exception] = Exception):
# TODO: Review unreachable code - """Initialize circuit breaker.
        
# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - failure_threshold: Number of failures before opening circuit
# TODO: Review unreachable code - recovery_timeout: Time to wait before attempting recovery
# TODO: Review unreachable code - expected_exception: Exception type to track
# TODO: Review unreachable code - """
# TODO: Review unreachable code - self.failure_threshold = failure_threshold
# TODO: Review unreachable code - self.recovery_timeout = recovery_timeout
# TODO: Review unreachable code - self.expected_exception = expected_exception
        
# TODO: Review unreachable code - self.failure_count = 0
# TODO: Review unreachable code - self.last_failure_time = 0.0
# TODO: Review unreachable code - self.state = "closed"  # closed, open, half-open
    
# TODO: Review unreachable code - def __enter__(self):
# TODO: Review unreachable code - """Check if circuit is open before proceeding."""
# TODO: Review unreachable code - if self.state == "open":
# TODO: Review unreachable code - if time.time() - self.last_failure_time > self.recovery_timeout:
# TODO: Review unreachable code - self.state = "half-open"
# TODO: Review unreachable code - logger.info("Circuit breaker entering half-open state")
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - raise RuntimeError("Circuit breaker is open")
# TODO: Review unreachable code - return self
    
# TODO: Review unreachable code - def __exit__(self, exc_type, exc_val, exc_tb):
# TODO: Review unreachable code - """Update circuit breaker state based on result."""
# TODO: Review unreachable code - if exc_type is None:
# TODO: Review unreachable code - # Success
# TODO: Review unreachable code - if self.state == "half-open":
# TODO: Review unreachable code - self.state = "closed"
# TODO: Review unreachable code - self.failure_count = 0
# TODO: Review unreachable code - logger.info("Circuit breaker closed after successful recovery")
# TODO: Review unreachable code - elif issubclass(exc_type, self.expected_exception):
# TODO: Review unreachable code - # Expected failure
# TODO: Review unreachable code - self.failure_count += 1
# TODO: Review unreachable code - self.last_failure_time = time.time()
            
# TODO: Review unreachable code - if self.failure_count >= self.failure_threshold:
# TODO: Review unreachable code - self.state = "open"
# TODO: Review unreachable code - logger.error(
# TODO: Review unreachable code - f"Circuit breaker opened after {self.failure_count} failures"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - return False  # Don't suppress exceptions
    
# TODO: Review unreachable code - def reset(self) -> None:
# TODO: Review unreachable code - """Manually reset circuit breaker."""
# TODO: Review unreachable code - self.state = "closed"
# TODO: Review unreachable code - self.failure_count = 0
# TODO: Review unreachable code - self.last_failure_time = 0.0