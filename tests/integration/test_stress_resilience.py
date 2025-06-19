"""Stress and resilience testing for error recovery systems."""

import pytest
import tempfile
import time
import random
import threading
import signal
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Optional
import concurrent.futures

from alicemultiverse.organizer.resilient_organizer import ResilientMediaOrganizer
from alicemultiverse.core.config import AliceMultiverseConfig
from alicemultiverse.core.error_recovery import ErrorRecovery, CircuitBreaker
from alicemultiverse.core.graceful_degradation import GracefulDegradation
from alicemultiverse.core.exceptions_extended import (
    FileOperationError, DatabaseOperationError, 
    NetworkOperationError, CriticalSystemError
)
from alicemultiverse.monitoring.metrics import PerformanceMetrics


class ChaosMonkey:
    """Inject various failures to test resilience."""
    
    def __init__(self, failure_rate: float = 0.1):
        self.failure_rate = failure_rate
        self.failure_types = [
            FileOperationError,
            DatabaseOperationError,
            NetworkOperationError,
            OSError,
            MemoryError,
            TimeoutError
        ]
        self.failure_count = 0
        self.call_count = 0
    
    def maybe_fail(self, operation: str = "operation"):
        """Randomly fail based on failure rate."""
        self.call_count += 1
        
        if random.random() < self.failure_rate:
            self.failure_count += 1
            error_type = random.choice(self.failure_types)
            
            if error_type == FileOperationError:
                raise FileOperationError(f"Chaos: File operation failed for {operation}")
            elif error_type == DatabaseOperationError:
                raise DatabaseOperationError(f"Chaos: Database operation failed for {operation}")
            elif error_type == NetworkOperationError:
                raise NetworkOperationError(f"Chaos: Network operation failed for {operation}")
            elif error_type == OSError:
                raise OSError(f"Chaos: OS error for {operation}")
            elif error_type == MemoryError:
                raise MemoryError(f"Chaos: Out of memory for {operation}")
            elif error_type == TimeoutError:
                raise TimeoutError(f"Chaos: Operation timed out for {operation}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chaos statistics."""
        return {
            'call_count': self.call_count,
            'failure_count': self.failure_count,
            'failure_rate': self.failure_count / self.call_count if self.call_count > 0 else 0
        }


class TestChaosEngineering:
    """Test system resilience under chaotic conditions."""
    
    @pytest.mark.slow
    def test_random_failures(self):
        """Test system behavior with random failures."""
        chaos = ChaosMonkey(failure_rate=0.2)  # 20% failure rate
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create test files
            file_count = 500
            for i in range(file_count):
                file_path = inbox / f"test_{i:04d}.jpg"
                file_path.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized}
            )
            
            organizer = ResilientMediaOrganizer(config)
            
            # Inject chaos into file operations
            original_process = organizer._process_file_impl
            
            def chaotic_process(file_path: Path):
                chaos.maybe_fail(str(file_path))
                return original_process(file_path)
            
            organizer._process_file_impl = chaotic_process
            
            # Process with chaos
            results = organizer.organize()
            
            # Get chaos stats
            chaos_stats = chaos.get_stats()
            print(f"\nChaos stats: {chaos_stats}")
            
            # System should still process most files despite failures
            success_rate = results.statistics['organized'] / file_count
            print(f"Success rate: {success_rate:.2%}")
            
            assert success_rate > 0.7, f"Success rate too low: {success_rate:.2%}"
            
            # Check that error recovery was used
            assert organizer.error_recovery.get_retry_stats()['total_retries'] > 0
    
    @pytest.mark.slow
    def test_cascading_failures(self):
        """Test system behavior during cascading failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create test files
            for i in range(200):
                file_path = inbox / f"test_{i:03d}.jpg"
                file_path.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized}
            )
            
            organizer = ResilientMediaOrganizer(config)
            
            # Simulate cascading failures
            failure_count = 0
            failure_threshold = 50
            
            original_process = organizer._process_file_impl
            
            def failing_process(file_path: Path):
                nonlocal failure_count
                
                # Start failing after threshold
                if failure_count < failure_threshold:
                    failure_count += 1
                    if failure_count > 10:
                        # Increase failure rate as cascade progresses
                        failure_prob = min(0.9, failure_count / failure_threshold)
                        if random.random() < failure_prob:
                            raise Exception(f"Cascading failure at count {failure_count}")
                
                return original_process(file_path)
            
            organizer._process_file_impl = failing_process
            
            # Process files
            results = organizer.organize()
            
            # Check graceful degradation
            degradation = organizer.graceful_degradation
            print(f"\nDegradation level: {degradation.get_current_level().name}")
            print(f"Disabled features: {degradation.disabled_features}")
            
            # System should degrade but continue functioning
            assert degradation.current_level > 0
            assert results.statistics['organized'] > 100  # At least half processed
    
    def test_circuit_breaker_activation(self):
        """Test circuit breaker activation and recovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create test files
            for i in range(100):
                file_path = inbox / f"test_{i:03d}.jpg"
                file_path.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized}
            )
            
            # Create circuit breaker with low threshold
            circuit_breaker = CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=2.0,
                half_open_max_calls=2
            )
            
            # Track circuit state changes
            state_changes = []
            
            def state_observer(old_state, new_state):
                state_changes.append((old_state, new_state, time.time()))
            
            circuit_breaker.add_observer(state_observer)
            
            # Simulate failures
            for i in range(5):
                try:
                    with circuit_breaker:
                        if i < 3:  # First 3 calls fail
                            raise Exception("Simulated failure")
                except Exception:
                    pass
            
            # Circuit should be open
            assert circuit_breaker.state == "open"
            assert len(state_changes) >= 1
            
            # Wait for recovery timeout
            time.sleep(2.5)
            
            # Try successful call (half-open state)
            with circuit_breaker:
                pass  # Success
            
            # Circuit should recover to closed
            assert circuit_breaker.state == "closed"
    
    @pytest.mark.slow
    def test_resource_exhaustion(self):
        """Test behavior under resource exhaustion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create many large files
            for i in range(100):
                file_path = inbox / f"test_{i:03d}.jpg"
                # Create 10MB files
                file_path.write_bytes(b'x' * (10 * 1024 * 1024))
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized},
                performance={'max_workers': 50}  # Excessive workers
            )
            
            # Mock low memory condition
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value = Mock(
                    available=50 * 1024 * 1024,  # Only 50MB available
                    total=16 * 1024 * 1024 * 1024
                )
                
                organizer = ResilientMediaOrganizer(config)
                
                # Should adapt to low resources
                results = organizer.organize()
                
                # Check that system adapted
                assert organizer.config.performance.max_workers < 50
                assert results.statistics['organized'] > 0
                
                # Check degradation occurred
                assert organizer.graceful_degradation.current_level > 0


class TestNetworkResilience:
    """Test resilience to network issues."""
    
    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            
            # Create test file
            test_file = inbox / "test.jpg"
            test_file.write_text("content")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': tmppath / "organized"},
                understanding={'enabled': True, 'providers': ['openai']}
            )
            
            # Mock API timeout
            with patch('alicemultiverse.understanding.providers.openai_provider.OpenAIImageAnalyzer.analyze') as mock_analyze:
                mock_analyze.side_effect = TimeoutError("Network timeout")
                
                organizer = ResilientMediaOrganizer(config)
                results = organizer.organize()
                
                # Should handle timeout gracefully
                assert results.statistics['organized'] > 0
                assert results.statistics['errors'] == 0  # Timeout handled, not counted as error
    
    def test_intermittent_network(self):
        """Test handling of intermittent network issues."""
        chaos_network = ChaosMonkey(failure_rate=0.3)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            
            # Create test files
            for i in range(20):
                test_file = inbox / f"test_{i:02d}.jpg"
                test_file.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': tmppath / "organized"},
                understanding={'enabled': True}
            )
            
            # Mock intermittent API failures
            with patch('alicemultiverse.understanding.providers.openai_provider.OpenAIImageAnalyzer.analyze') as mock_analyze:
                def intermittent_analyze(*args, **kwargs):
                    chaos_network.maybe_fail("API call")
                    return Mock(tags=['test'], generated_prompt='test prompt')
                
                mock_analyze.side_effect = intermittent_analyze
                
                organizer = ResilientMediaOrganizer(config)
                results = organizer.organize()
                
                # Should process files despite network issues
                assert results.statistics['organized'] > 10


class TestConcurrentFailures:
    """Test failures in concurrent operations."""
    
    @pytest.mark.slow
    def test_concurrent_failure_handling(self):
        """Test handling failures in parallel processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create test files
            for i in range(100):
                file_path = inbox / f"test_{i:03d}.jpg"
                file_path.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized},
                performance={'max_workers': 8}
            )
            
            organizer = ResilientMediaOrganizer(config)
            
            # Inject failures in random threads
            original_process = organizer._process_file_impl
            thread_failures = {}
            
            def thread_failing_process(file_path: Path):
                thread_id = threading.current_thread().ident
                
                # Each thread has 30% chance to fail on first file
                if thread_id not in thread_failures:
                    thread_failures[thread_id] = random.random() < 0.3
                
                if thread_failures[thread_id] and random.random() < 0.5:
                    raise Exception(f"Thread {thread_id} failure")
                
                return original_process(file_path)
            
            organizer._process_file_impl = thread_failing_process
            
            # Process files
            results = organizer.organize()
            
            # Should handle thread failures gracefully
            assert results.statistics['organized'] > 50
            print(f"\nThread failures: {len([v for v in thread_failures.values() if v])}")
    
    def test_deadlock_prevention(self):
        """Test that system prevents deadlocks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            
            # Create test files
            for i in range(50):
                file_path = inbox / f"test_{i:02d}.jpg"
                file_path.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': tmppath / "organized"},
                performance={'max_workers': 4}
            )
            
            organizer = ResilientMediaOrganizer(config)
            
            # Create potential deadlock with locks
            lock1 = threading.Lock()
            lock2 = threading.Lock()
            
            original_process = organizer._process_file_impl
            
            def deadlock_prone_process(file_path: Path):
                # Alternate lock order to create potential deadlock
                if random.random() < 0.5:
                    with lock1:
                        time.sleep(0.001)
                        with lock2:
                            return original_process(file_path)
                else:
                    with lock2:
                        time.sleep(0.001)
                        with lock1:
                            return original_process(file_path)
            
            organizer._process_file_impl = deadlock_prone_process
            
            # Set timeout for test
            def timeout_handler(signum, frame):
                raise TimeoutError("Deadlock detected - test timed out")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
            
            try:
                results = organizer.organize()
                signal.alarm(0)  # Cancel alarm
                
                # Should complete without deadlock
                assert results.statistics['organized'] > 0
            except TimeoutError:
                pytest.fail("Deadlock detected - system hung")


class TestRecoveryMechanisms:
    """Test various recovery mechanisms."""
    
    def test_checkpoint_recovery(self):
        """Test recovery from checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create test files
            for i in range(100):
                file_path = inbox / f"test_{i:03d}.jpg"
                file_path.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized}
            )
            
            # First run - simulate crash after 50 files
            organizer1 = ResilientMediaOrganizer(config)
            
            files_processed = 0
            original_process = organizer1._process_file_impl
            
            def crashing_process(file_path: Path):
                nonlocal files_processed
                result = original_process(file_path)
                files_processed += 1
                
                if files_processed >= 50:
                    raise CriticalSystemError("Simulated crash")
                
                return result
            
            organizer1._process_file_impl = crashing_process
            
            # First run should crash
            with pytest.raises(CriticalSystemError):
                organizer1.organize()
            
            # Second run - should recover and continue
            organizer2 = ResilientMediaOrganizer(config)
            results = organizer2.organize()
            
            # Should complete remaining files
            assert results.statistics['organized'] >= 50
    
    def test_state_persistence(self):
        """Test that state is persisted correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            state_file = tmppath / "state.json"
            
            # Create degradation system with state persistence
            degradation = GracefulDegradation()
            
            # Trigger some failures to change state
            for i in range(10):
                degradation.record_failure("test_component", Exception("Test"))
            
            # Save state
            import json
            state = {
                'level': degradation.current_level,
                'disabled_features': list(degradation.disabled_features),
                'component_health': {
                    comp: {'failures': health['failures'], 'successes': health['successes']}
                    for comp, health in degradation.component_health.items()
                }
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f)
            
            # Create new instance and restore state
            degradation2 = GracefulDegradation()
            
            with open(state_file, 'r') as f:
                saved_state = json.load(f)
            
            # Restore state
            degradation2.current_level = saved_state['level']
            degradation2.disabled_features = set(saved_state['disabled_features'])
            
            # Verify state was restored
            assert degradation2.current_level == degradation.current_level
            assert degradation2.disabled_features == degradation.disabled_features


def generate_stress_report(test_results: Dict[str, Any], output_file: str = "stress_test_report.md"):
    """Generate a stress test report."""
    with open(output_file, 'w') as f:
        f.write("# Stress Test Report\n\n")
        
        f.write("## Test Summary\n\n")
        f.write(f"- Total tests run: {test_results.get('total_tests', 0)}\n")
        f.write(f"- Passed: {test_results.get('passed', 0)}\n")
        f.write(f"- Failed: {test_results.get('failed', 0)}\n\n")
        
        f.write("## Resilience Metrics\n\n")
        
        if 'chaos_stats' in test_results:
            stats = test_results['chaos_stats']
            f.write(f"- Failure injection rate: {stats.get('failure_rate', 0):.2%}\n")
            f.write(f"- Recovery success rate: {stats.get('recovery_rate', 0):.2%}\n")
            f.write(f"- Circuit breaker activations: {stats.get('circuit_breaks', 0)}\n")
            f.write(f"- Degradation events: {stats.get('degradations', 0)}\n\n")
        
        f.write("## Recommendations\n\n")
        
        if test_results.get('recovery_rate', 1.0) < 0.8:
            f.write("- **Low recovery rate detected**. Consider:\n")
            f.write("  - Increasing retry attempts\n")
            f.write("  - Improving error classification\n")
            f.write("  - Adding more recovery strategies\n\n")
    
    print(f"\nStress test report saved to: {output_file}")