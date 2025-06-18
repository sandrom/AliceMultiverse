"""Tests for error recovery and resilience system."""

import time
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from alicemultiverse.core.exceptions_extended import (
    RecoverableError,
    FatalError,
    APIRateLimitError,
    APITimeoutError,
    DatabaseTransactionError,
    FileOperationError,
    PartialBatchFailure
)
from alicemultiverse.core.error_recovery import (
    RetryConfig,
    ErrorRecovery,
    DeadLetterQueue,
    CircuitBreaker
)
from alicemultiverse.core.graceful_degradation import (
    DegradationLevel,
    GracefulDegradation,
    FallbackChain,
    AdaptiveProcessor
)


class TestRetryConfig:
    """Test RetryConfig class."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_calculate_delay_exponential(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, jitter=False)
        
        assert config.calculate_delay(1) == 1.0
        assert config.calculate_delay(2) == 2.0
        assert config.calculate_delay(3) == 4.0
        assert config.calculate_delay(4) == 8.0
    
    def test_calculate_delay_max_limit(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )
        
        assert config.calculate_delay(10) == 5.0  # Would be 512 without cap
    
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(initial_delay=10.0, jitter=True)
        
        # Calculate multiple times to check jitter
        delays = [config.calculate_delay(1) for _ in range(10)]
        
        # All should be within ±25% of 10.0
        for delay in delays:
            assert 7.5 <= delay <= 12.5
        
        # They shouldn't all be the same (jitter working)
        assert len(set(delays)) > 1


class TestErrorRecovery:
    """Test ErrorRecovery class."""
    
    def test_retry_with_backoff_success(self):
        """Test successful retry."""
        attempt_count = 0
        
        @ErrorRecovery.retry_with_backoff(
            config=RetryConfig(max_attempts=3, initial_delay=0.01)
        )
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise RecoverableError("Temporary failure")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert attempt_count == 3
    
    def test_retry_with_backoff_all_fail(self):
        """Test all retries fail."""
        attempt_count = 0
        
        @ErrorRecovery.retry_with_backoff(
            config=RetryConfig(max_attempts=3, initial_delay=0.01)
        )
        def always_fails():
            nonlocal attempt_count
            attempt_count += 1
            raise RecoverableError("Always fails")
        
        with pytest.raises(RecoverableError):
            always_fails()
        
        assert attempt_count == 3
    
    def test_retry_does_not_retry_fatal_errors(self):
        """Test that fatal errors are not retried."""
        attempt_count = 0
        
        @ErrorRecovery.retry_with_backoff()
        def fatal_error():
            nonlocal attempt_count
            attempt_count += 1
            raise FatalError("Fatal error")
        
        with pytest.raises(FatalError):
            fatal_error()
        
        assert attempt_count == 1  # No retries
    
    def test_retry_with_rate_limit(self):
        """Test retry with rate limit error."""
        start_time = time.time()
        
        @ErrorRecovery.retry_with_backoff(
            config=RetryConfig(max_attempts=2)
        )
        def rate_limited():
            raise APIRateLimitError("test", retry_after=0.1)
        
        with pytest.raises(APIRateLimitError):
            rate_limited()
        
        # Should have waited at least 0.1 seconds
        assert time.time() - start_time >= 0.1
    
    def test_retry_with_callback(self):
        """Test retry with on_retry callback."""
        retry_calls = []
        
        def on_retry(exception, attempt):
            retry_calls.append((str(exception), attempt))
        
        @ErrorRecovery.retry_with_backoff(
            config=RetryConfig(max_attempts=3, initial_delay=0.01),
            on_retry=on_retry
        )
        def failing_function():
            raise RecoverableError("Test error")
        
        with pytest.raises(RecoverableError):
            failing_function()
        
        assert len(retry_calls) == 2  # Called on retry, not initial attempt
        assert retry_calls[0] == ("Test error", 1)
        assert retry_calls[1] == ("Test error", 2)
    
    def test_handle_partial_batch_failure(self):
        """Test handling of partial batch failures."""
        def process_item(item):
            if item % 2 == 0:
                return item * 2
            else:
                raise ValueError(f"Cannot process {item}")
        
        items = [1, 2, 3, 4, 5]
        successful, failed = ErrorRecovery.handle_partial_batch_failure(
            items, process_item
        )
        
        assert successful == [4, 8]  # 2*2, 4*2
        assert len(failed) == 3
        assert [item for item, _ in failed] == [1, 3, 5]
    
    def test_handle_partial_batch_failure_stop_on_error(self):
        """Test batch processing that stops on first error."""
        def process_item(item):
            if item == 3:
                raise ValueError(f"Cannot process {item}")
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        
        with pytest.raises(PartialBatchFailure) as exc_info:
            ErrorRecovery.handle_partial_batch_failure(
                items, process_item, continue_on_error=False
            )
        
        error = exc_info.value
        assert error.batch_size == 5
        assert error.successful_items == [2, 4]  # 1*2, 2*2
        assert error.failed_items == [3]


class TestDeadLetterQueue:
    """Test DeadLetterQueue class."""
    
    def test_add_and_get(self):
        """Test adding and getting items."""
        dlq = DeadLetterQueue("test")
        
        dlq.add("item1", ValueError("error1"), 3)
        dlq.add("item2", TypeError("error2"), 5)
        
        items = dlq.get_all()
        assert len(items) == 2
        assert items[0][0] == "item1"
        assert isinstance(items[0][1], ValueError)
        assert items[0][2] == 3
    
    def test_clear(self):
        """Test clearing the queue."""
        dlq = DeadLetterQueue("test")
        dlq.add("item", ValueError("error"), 1)
        
        assert len(dlq.items) == 1
        dlq.clear()
        assert len(dlq.items) == 0
    
    def test_retry_all(self):
        """Test retrying all items."""
        dlq = DeadLetterQueue("test")
        dlq.add(1, ValueError("error"), 1)
        dlq.add(2, ValueError("error"), 1)
        dlq.add(3, ValueError("error"), 1)
        
        def process_item(item):
            if item == 2:
                return item * 2
            raise ValueError("Still failing")
        
        successful, failed = dlq.retry_all(process_item)
        
        assert successful == [4]  # Only item 2 succeeded
        assert len(failed) == 2
        assert len(dlq.items) == 2  # Item 2 removed from queue
    
    def test_save_to_file(self, tmp_path):
        """Test saving queue to file."""
        dlq = DeadLetterQueue("test")
        dlq.add("item1", ValueError("error1"), 3)
        dlq.add("item2", TypeError("error2"), 5)
        
        file_path = tmp_path / "dlq.json"
        dlq.save_to_file(file_path)
        
        assert file_path.exists()
        
        import json
        with open(file_path) as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[0]["item"] == "item1"
        assert data[0]["error_type"] == "ValueError"
        assert data[0]["attempts"] == 3


class TestCircuitBreaker:
    """Test CircuitBreaker class."""
    
    def test_circuit_closed_on_success(self):
        """Test circuit remains closed on success."""
        cb = CircuitBreaker(failure_threshold=3)
        
        with cb:
            pass  # Success
        
        assert cb.state == "closed"
        assert cb.failure_count == 0
    
    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=3, expected_exception=ValueError)
        
        for i in range(3):
            try:
                with cb:
                    raise ValueError("Test error")
            except ValueError:
                pass
        
        assert cb.state == "open"
        assert cb.failure_count == 3
        
        # Should raise when trying to use open circuit
        with pytest.raises(RuntimeError, match="Circuit breaker is open"):
            with cb:
                pass
    
    def test_circuit_half_open_after_timeout(self):
        """Test circuit goes to half-open after timeout."""
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.1,
            expected_exception=ValueError
        )
        
        # Open the circuit
        try:
            with cb:
                raise ValueError("Test")
        except ValueError:
            pass
        
        assert cb.state == "open"
        
        # Wait for recovery timeout
        time.sleep(0.2)
        
        # Should go to half-open
        with cb:
            pass  # Success
        
        assert cb.state == "closed"
    
    def test_reset(self):
        """Test manual reset."""
        cb = CircuitBreaker(failure_threshold=1)
        
        # Open the circuit
        try:
            with cb:
                raise Exception("Test")
        except Exception:
            pass
        
        assert cb.state == "open"
        
        cb.reset()
        assert cb.state == "closed"
        assert cb.failure_count == 0


class TestGracefulDegradation:
    """Test GracefulDegradation class."""
    
    def test_initial_level(self):
        """Test initial degradation level."""
        gd = GracefulDegradation()
        
        assert gd.current_level.name == "normal"
        assert gd.current_level.disabled_features == []
    
    def test_degrade(self):
        """Test degrading to next level."""
        gd = GracefulDegradation()
        
        old_level = gd.degrade("Test failure", "test_feature")
        
        assert gd.current_level.name == "reduced_parallel"
        assert gd.feature_failures["test_feature"] == 1
        assert len(gd.degradation_history) == 1
    
    def test_degrade_to_limit(self):
        """Test degrading to maximum level."""
        gd = GracefulDegradation()
        
        # Degrade to maximum
        for i in range(10):
            gd.degrade(f"Failure {i}")
        
        assert gd.current_level.name == "safe_mode"
        assert gd.current_level_index == len(gd.LEVELS) - 1
    
    def test_recover(self):
        """Test recovering to previous level."""
        gd = GracefulDegradation()
        
        # Degrade twice
        gd.degrade("Failure 1")
        gd.degrade("Failure 2")
        
        assert gd.current_level.name == "sequential_only"
        
        # Recover once
        gd.recover()
        assert gd.current_level.name == "reduced_parallel"
    
    def test_is_feature_enabled(self):
        """Test feature enablement checking."""
        gd = GracefulDegradation()
        
        # All features enabled at normal level
        assert gd.is_feature_enabled("parallel_processing")
        
        # Degrade to sequential only
        gd.degrade("Test")
        gd.degrade("Test")
        
        assert not gd.is_feature_enabled("parallel_processing")
        assert not gd.is_feature_enabled("batch_operations")
    
    def test_get_constraint(self):
        """Test getting constraints."""
        gd = GracefulDegradation()
        
        # No constraints at normal level
        assert gd.get_constraint("max_workers") is None
        assert gd.get_constraint("max_workers", 8) == 8
        
        # Degrade to get constraints
        gd.degrade("Test")
        assert gd.get_constraint("max_workers") == 4
        assert gd.get_constraint("batch_size") == 50


class TestFallbackChain:
    """Test FallbackChain class."""
    
    def test_single_handler_success(self):
        """Test single successful handler."""
        chain = FallbackChain()
        chain.add_handler("handler1", lambda: "success")
        
        result = chain.execute()
        assert result == "success"
    
    def test_fallback_on_failure(self):
        """Test fallback to next handler."""
        def handler1():
            raise ValueError("Handler 1 failed")
        
        def handler2():
            return "handler 2 success"
        
        chain = FallbackChain()
        chain.add_handler("handler1", handler1)
        chain.add_handler("handler2", handler2)
        
        result = chain.execute()
        assert result == "handler 2 success"
    
    def test_all_handlers_fail(self):
        """Test all handlers failing."""
        def failing_handler():
            raise ValueError("Failed")
        
        chain = FallbackChain()
        chain.add_handler("handler1", failing_handler)
        chain.add_handler("handler2", failing_handler)
        
        with pytest.raises(ValueError):
            chain.execute()
    
    def test_constraints_applied(self):
        """Test constraints are applied to handlers."""
        def handler(value=None):
            return value
        
        chain = FallbackChain()
        chain.add_handler("handler1", handler, {"value": "constrained"})
        
        result = chain.execute()
        assert result == "constrained"


class TestAdaptiveProcessor:
    """Test AdaptiveProcessor class."""
    
    def test_initialization(self):
        """Test adaptive processor initialization."""
        config = {"max_workers": 8, "batch_size": 100}
        processor = AdaptiveProcessor(config)
        
        assert processor.base_config == config
        assert processor.degradation.current_level.name == "normal"
        assert processor.success_count == 0
        assert processor.failure_count == 0
    
    @patch('alicemultiverse.core.graceful_degradation.ThreadPoolExecutor')
    def test_process_with_success(self, mock_executor):
        """Test successful processing."""
        processor = AdaptiveProcessor({"max_workers": 4})
        
        def process_func(item):
            return item * 2
        
        items = [1, 2, 3]
        
        # Mock successful parallel processing
        mock_future = MagicMock()
        mock_future.result.side_effect = [2, 4, 6]
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
        
        results = processor.process_with_adaptation(items, process_func)
        
        assert processor.success_count == 1
        assert processor.consecutive_failures == 0