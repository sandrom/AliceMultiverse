#!/usr/bin/env python3
"""
Error Recovery and Resilience Demo

This script demonstrates the error recovery and resilience features of AliceMultiverse:
1. Retry logic with exponential backoff
2. Graceful degradation
3. Circuit breaker pattern
4. Dead letter queue handling
"""

import time
import random
from pathlib import Path
from typing import Any

from alicemultiverse.core.exceptions_extended import (
    RecoverableError,
    APIRateLimitError,
    DatabaseTransactionError,
    FileOperationError,
    PartialBatchFailure
)
from alicemultiverse.core.error_recovery import (
    ErrorRecovery,
    RetryConfig,
    DeadLetterQueue,
    CircuitBreaker
)
from alicemultiverse.core.graceful_degradation import (
    GracefulDegradation,
    FallbackChain,
    AdaptiveProcessor
)


def demonstrate_retry_logic():
    """Demonstrate retry with exponential backoff."""
    print("\n=== Retry Logic Demo ===")
    
    attempt_count = 0
    
    @ErrorRecovery.retry_with_backoff(
        config=RetryConfig(
            max_attempts=4,
            initial_delay=1.0,
            exponential_base=2.0
        ),
        on_retry=lambda e, a: print(f"  Retry {a} after error: {e}")
    )
    def flaky_operation():
        nonlocal attempt_count
        attempt_count += 1
        print(f"Attempt {attempt_count}...")
        
        if attempt_count < 3:
            raise RecoverableError(f"Temporary failure on attempt {attempt_count}")
        
        return "Success!"
    
    try:
        result = flaky_operation()
        print(f"Final result: {result}")
    except RecoverableError as e:
        print(f"Failed after all retries: {e}")


def demonstrate_api_retry():
    """Demonstrate API-specific retry with rate limiting."""
    print("\n=== API Retry Demo ===")
    
    @ErrorRecovery.retry_api_call
    def api_call():
        # Simulate rate limit on first call
        if not hasattr(api_call, 'called'):
            api_call.called = True
            print("API call hit rate limit!")
            raise APIRateLimitError("OpenAI", retry_after=2)
        
        print("API call succeeded!")
        return {"result": "data"}
    
    print("Making API call...")
    result = api_call()
    print(f"Result: {result}")


def demonstrate_graceful_degradation():
    """Demonstrate graceful degradation system."""
    print("\n=== Graceful Degradation Demo ===")
    
    degradation = GracefulDegradation()
    
    print(f"Initial level: {degradation.current_level.name}")
    print(f"Features enabled: parallel={degradation.is_feature_enabled('parallel_processing')}")
    
    # Simulate failures
    for i in range(3):
        print(f"\nSimulating failure {i+1}...")
        degradation.degrade(f"Database timeout #{i+1}", "database")
        
        print(f"Current level: {degradation.current_level.name}")
        print(f"Max workers: {degradation.get_constraint('max_workers', 8)}")
        print(f"Batch operations: {degradation.is_feature_enabled('batch_operations')}")
    
    # Show disabled features
    if degradation.current_level.disabled_features:
        print(f"\nDisabled features: {', '.join(degradation.current_level.disabled_features)}")
    
    # Attempt recovery
    print("\nSimulating recovery after success...")
    degradation.recover()
    print(f"Recovered to: {degradation.current_level.name}")


def demonstrate_circuit_breaker():
    """Demonstrate circuit breaker pattern."""
    print("\n=== Circuit Breaker Demo ===")
    
    circuit_breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=2.0,
        expected_exception=DatabaseTransactionError
    )
    
    def database_operation():
        # Simulate random failures
        if random.random() < 0.7:  # 70% failure rate
            raise DatabaseTransactionError("INSERT", Exception("Connection lost"))
        return "Success"
    
    # Try operations until circuit opens
    for i in range(10):
        try:
            with circuit_breaker:
                result = database_operation()
                print(f"Operation {i+1}: {result}")
        except DatabaseTransactionError as e:
            print(f"Operation {i+1}: Failed - {e}")
        except RuntimeError as e:
            print(f"Operation {i+1}: {e}")
            break
    
    print(f"\nCircuit state: {circuit_breaker.state}")
    print(f"Failure count: {circuit_breaker.failure_count}")
    
    # Wait for recovery
    if circuit_breaker.state == "open":
        print("\nWaiting for recovery timeout...")
        time.sleep(2.5)
        
        print("Attempting operation after timeout...")
        try:
            with circuit_breaker:
                # Force success for demo
                print("Operation succeeded - circuit recovered!")
        except Exception as e:
            print(f"Still failing: {e}")


def demonstrate_dead_letter_queue():
    """Demonstrate dead letter queue handling."""
    print("\n=== Dead Letter Queue Demo ===")
    
    dlq = DeadLetterQueue("failed_files")
    
    def process_file(filename):
        # Simulate processing with 50% failure rate
        if "bad" in filename:
            raise FileOperationError(f"Cannot process {filename}")
        return f"Processed: {filename}"
    
    # Process batch with failures
    files = ["good1.jpg", "bad1.jpg", "good2.jpg", "bad2.jpg", "good3.jpg"]
    
    print("Processing files...")
    for file in files:
        try:
            result = process_file(file)
            print(f"  ✓ {result}")
        except FileOperationError as e:
            print(f"  ✗ Failed: {file}")
            dlq.add(file, e, 1)
    
    print(f"\nDead letter queue size: {len(dlq.items)}")
    
    # Show failed items
    print("\nFailed items:")
    for item, error, attempts in dlq.get_all():
        print(f"  - {item}: {error} (attempts: {attempts})")
    
    # Save to file
    dlq.save_to_file(Path("failed_items_demo.json"))
    print("\nSaved failed items to failed_items_demo.json")


def demonstrate_adaptive_processing():
    """Demonstrate adaptive processing with automatic degradation."""
    print("\n=== Adaptive Processing Demo ===")
    
    processor = AdaptiveProcessor({
        "max_workers": 8,
        "batch_size": 10
    })
    
    # Counter to control failure rate
    process_count = 0
    
    def process_item(item):
        nonlocal process_count
        process_count += 1
        
        # High failure rate initially, then recover
        if process_count <= 15 and random.random() < 0.6:
            raise ProcessingError(f"Failed to process {item}")
        
        return f"Processed: {item}"
    
    # Process multiple batches
    for batch_num in range(3):
        print(f"\n--- Batch {batch_num + 1} ---")
        items = [f"item_{batch_num}_{i}" for i in range(5)]
        
        print(f"Degradation level: {processor.degradation.current_level.name}")
        print(f"Processing {len(items)} items...")
        
        try:
            results = processor.process_with_adaptation(
                items,
                process_item,
                "demo_processing"
            )
            print(f"Successfully processed {len(results)} items")
        except Exception as e:
            print(f"Batch failed: {e}")
        
        print(f"Success rate: {processor.success_count}/{processor.success_count + processor.failure_count}")


def demonstrate_fallback_chain():
    """Demonstrate fallback chain for progressive degradation."""
    print("\n=== Fallback Chain Demo ===")
    
    def primary_handler(data):
        print("  Trying primary handler (full features)...")
        raise RecoverableError("Primary service unavailable")
    
    def secondary_handler(data):
        print("  Trying secondary handler (reduced features)...")
        raise RecoverableError("Secondary service overloaded")
    
    def fallback_handler(data):
        print("  Trying fallback handler (basic features)...")
        return f"Processed with basic features: {len(data)} items"
    
    chain = FallbackChain()
    chain.add_handler("primary", primary_handler)
    chain.add_handler("secondary", secondary_handler)
    chain.add_handler("fallback", fallback_handler)
    
    data = ["item1", "item2", "item3"]
    print(f"Processing {len(data)} items through fallback chain...")
    
    try:
        result = chain.execute(data)
        print(f"Result: {result}")
    except Exception as e:
        print(f"All handlers failed: {e}")


def main():
    """Run all demonstrations."""
    print("AliceMultiverse Error Recovery & Resilience Demo")
    print("=" * 50)
    
    demonstrate_retry_logic()
    demonstrate_api_retry()
    demonstrate_graceful_degradation()
    demonstrate_circuit_breaker()
    demonstrate_dead_letter_queue()
    demonstrate_adaptive_processing()
    demonstrate_fallback_chain()
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    
    # Cleanup
    demo_file = Path("failed_items_demo.json")
    if demo_file.exists():
        demo_file.unlink()


if __name__ == "__main__":
    main()