"""Large-scale integration tests for performance features."""

import pytest
import tempfile
import time
import random
import threading
import psutil
import json
from pathlib import Path
from unittest.mock import Mock, patch
from typing import List, Dict, Any, Tuple
import multiprocessing

from alicemultiverse.monitoring.metrics import PerformanceMetrics
from alicemultiverse.monitoring.tracker import PerformanceTracker
from alicemultiverse.organizer.resilient_organizer import ResilientMediaOrganizer
from alicemultiverse.core.config import AliceMultiverseConfig
from alicemultiverse.core.enums import MediaType
from alicemultiverse.core.error_recovery import ErrorRecovery, RetryConfig
from alicemultiverse.core.graceful_degradation import GracefulDegradation


def create_test_files(directory: Path, count: int, file_types: List[str] = None) -> List[Path]:
    """Create test files for benchmarking.
    
    Args:
        directory: Directory to create files in
        count: Number of files to create
        file_types: List of extensions (default: ['.jpg', '.png', '.mp4'])
        
    Returns:
        List of created file paths
    """
    if file_types is None:
        file_types = ['.jpg', '.png', '.mp4', '.webp', '.heic']
    
    files = []
    for i in range(count):
        ext = random.choice(file_types)
        file_path = directory / f"test_file_{i:06d}{ext}"
        
        # Create realistic file sizes
        if ext in ['.jpg', '.png', '.webp']:
            size = random.randint(500_000, 5_000_000)  # 500KB - 5MB
        elif ext == '.heic':
            size = random.randint(1_000_000, 3_000_000)  # 1MB - 3MB
        else:  # video
            size = random.randint(10_000_000, 100_000_000)  # 10MB - 100MB
        
        with open(file_path, 'wb') as f:
            f.write(b'\x00' * size)
        
        files.append(file_path)
    
    return files


class TestLargeScalePerformance:
    """Test performance with large file collections."""
    
    @pytest.mark.slow
    @pytest.mark.parametrize("file_count,expected_time", [
        (10_000, 60),    # 10K files should process in under 1 minute
        (50_000, 300),   # 50K files should process in under 5 minutes
        (100_000, 600),  # 100K files should process in under 10 minutes
    ])
    def test_large_collection_processing(self, file_count: int, expected_time: float):
        """Test processing large collections within time constraints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create test files
            print(f"\nCreating {file_count:,} test files...")
            start_create = time.time()
            files = create_test_files(inbox, file_count)
            create_time = time.time() - start_create
            print(f"Created {file_count:,} files in {create_time:.2f}s")
            
            # Configure for performance
            config = AliceMultiverseConfig(
                paths={
                    'inbox': inbox,
                    'organized': organized
                },
                performance={
                    'profile': 'large_collection',
                    'max_workers': 12,
                    'batch_size': 500
                }
            )
            
            # Create organizer with monitoring
            organizer = ResilientMediaOrganizer(config, dry_run=False)
            
            # Process files
            print(f"Processing {file_count:,} files...")
            start_time = time.time()
            results = organizer.organize()
            process_time = time.time() - start_time
            
            print(f"Processed {file_count:,} files in {process_time:.2f}s")
            print(f"Rate: {file_count / process_time:.2f} files/second")
            
            # Verify results
            assert results.statistics['organized'] == file_count
            assert results.statistics['errors'] == 0
            assert process_time < expected_time, f"Processing took {process_time:.2f}s, expected < {expected_time}s"
            
            # Get performance metrics
            metrics = PerformanceMetrics.get_instance()
            
            # Check performance metrics
            assert metrics.files_processed == file_count
            avg_time = metrics.processing_time / metrics.files_processed
            assert avg_time < 0.1, f"Average processing time too high: {avg_time:.3f}s"
    
    @pytest.mark.slow
    def test_memory_usage_stability(self):
        """Test memory usage remains stable during large operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create 20K files
            files = create_test_files(inbox, 20_000)
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized},
                performance={'profile': 'memory_constrained'}
            )
            
            organizer = ResilientMediaOrganizer(config)
            
            # Monitor memory usage
            process = psutil.Process()
            memory_samples = []
            
            def monitor_memory():
                while hasattr(monitor_memory, 'running'):
                    memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
                    time.sleep(0.5)
            
            # Start monitoring
            monitor_memory.running = True
            monitor_thread = threading.Thread(target=monitor_memory)
            monitor_thread.start()
            
            # Process files
            results = organizer.organize()
            
            # Stop monitoring
            del monitor_memory.running
            monitor_thread.join()
            
            # Analyze memory usage
            if memory_samples:
                initial_memory = memory_samples[0]
                peak_memory = max(memory_samples)
                final_memory = memory_samples[-1]
                avg_memory = sum(memory_samples) / len(memory_samples)
                
                print(f"\nMemory usage:")
                print(f"  Initial: {initial_memory:.2f} MB")
                print(f"  Peak: {peak_memory:.2f} MB")
                print(f"  Final: {final_memory:.2f} MB")
                print(f"  Average: {avg_memory:.2f} MB")
                
                # Check for memory leaks
                memory_growth = final_memory - initial_memory
                assert memory_growth < 100, f"Memory grew by {memory_growth:.2f} MB"
                
                # Check peak usage
                assert peak_memory < 1000, f"Peak memory too high: {peak_memory:.2f} MB"
    
    @pytest.mark.slow
    def test_concurrent_operations(self):
        """Test system behavior under concurrent load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create multiple inbox directories
            inboxes = []
            for i in range(4):
                inbox = tmppath / f"inbox_{i}"
                inbox.mkdir()
                inboxes.append(inbox)
                # Create 5K files in each
                create_test_files(inbox, 5_000)
            
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Run multiple organizers concurrently
            def run_organizer(inbox_path: Path) -> Dict[str, Any]:
                config = AliceMultiverseConfig(
                    paths={'inbox': inbox_path, 'organized': organized},
                    performance={'max_workers': 4, 'batch_size': 100}
                )
                
                organizer = ResilientMediaOrganizer(config)
                start = time.time()
                results = organizer.organize()
                duration = time.time() - start
                
                return {
                    'inbox': str(inbox_path),
                    'files': results.statistics['organized'],
                    'errors': results.statistics['errors'],
                    'duration': duration
                }
            
            # Run concurrently
            with multiprocessing.Pool(processes=4) as pool:
                results = pool.map(run_organizer, inboxes)
            
            # Verify results
            total_files = sum(r['files'] for r in results)
            total_errors = sum(r['errors'] for r in results)
            
            assert total_files == 20_000
            assert total_errors == 0
            
            # Check performance
            max_duration = max(r['duration'] for r in results)
            assert max_duration < 120, f"Concurrent processing took too long: {max_duration:.2f}s"


class TestDataIntegrity:
    """Test data integrity during batch operations."""
    
    @pytest.mark.slow
    def test_batch_operation_integrity(self):
        """Verify data integrity after batch operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create files with known content
            file_checksums = {}
            for i in range(1000):
                file_path = inbox / f"test_{i:04d}.jpg"
                content = f"content_{i}".encode() * 1000
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Calculate checksum
                import hashlib
                file_checksums[file_path.name] = hashlib.sha256(content).hexdigest()
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized},
                performance={'batch_size': 100}
            )
            
            organizer = ResilientMediaOrganizer(config)
            results = organizer.organize()
            
            # Verify all files were moved correctly
            assert results.statistics['organized'] == 1000
            
            # Check file integrity
            for org_file in organized.rglob("*.jpg"):
                original_name = org_file.name.split('_', 1)[1]  # Remove sequence prefix
                
                with open(org_file, 'rb') as f:
                    content = f.read()
                    checksum = hashlib.sha256(content).hexdigest()
                
                # Find original checksum
                for orig_name, orig_checksum in file_checksums.items():
                    if orig_name in org_file.name:
                        assert checksum == orig_checksum, f"Checksum mismatch for {org_file.name}"
                        break
    
    def test_transaction_rollback(self):
        """Test transaction rollback on batch failures."""
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
                performance={'batch_size': 50}
            )
            
            # Mock database to fail on second batch
            with patch('alicemultiverse.storage.duckdb_search.DuckDBSearchCache') as mock_db:
                mock_instance = Mock()
                mock_db.return_value = mock_instance
                
                # Fail on second batch insert
                call_count = 0
                def side_effect(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 2:
                        raise Exception("Database error")
                    return Mock()
                
                mock_instance.batch_upsert_assets.side_effect = side_effect
                
                organizer = ResilientMediaOrganizer(config)
                
                # Should handle the error gracefully
                results = organizer.organize()
                
                # First batch should succeed, second should be retried
                assert results.statistics['organized'] > 0
                assert results.statistics['errors'] < 50  # Some files might fail


class TestStressScenarios:
    """Test system under stress conditions."""
    
    def test_cascading_failures(self):
        """Test system behavior during cascading failures."""
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
            
            # Create organizer with failure injection
            organizer = ResilientMediaOrganizer(config)
            
            # Inject failures
            failure_count = 0
            original_process = organizer._process_file_impl
            
            def failing_process(file_path: Path):
                nonlocal failure_count
                failure_count += 1
                
                # Fail first 10 attempts
                if failure_count <= 10:
                    raise Exception(f"Simulated failure {failure_count}")
                
                return original_process(file_path)
            
            organizer._process_file_impl = failing_process
            
            # Should degrade gracefully
            results = organizer.organize()
            
            # Should still process most files
            assert results.statistics['organized'] > 80
            
            # Check that degradation occurred
            degradation = organizer.graceful_degradation
            assert degradation.current_level > 0
    
    def test_resource_exhaustion(self):
        """Test behavior when resources are exhausted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create files
            create_test_files(inbox, 1000)
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized},
                performance={'max_workers': 100}  # Excessive
            )
            
            # Mock low memory condition
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value = Mock(
                    available=100 * 1024 * 1024,  # 100MB available
                    total=16 * 1024 * 1024 * 1024  # 16GB total
                )
                
                organizer = ResilientMediaOrganizer(config)
                
                # Should adapt to low memory
                results = organizer.organize()
                
                # Should complete but with reduced performance
                assert results.statistics['organized'] > 0
                
                # Check performance was throttled
                metrics = PerformanceMetrics.get_instance()
                # Workers should have been reduced
                assert organizer.config.performance.max_workers < 100
    
    @pytest.mark.slow
    def test_long_running_stability(self):
        """Test system stability over long runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            config = AliceMultiverseConfig(
                paths={
                    'inbox': tmppath / "inbox",
                    'organized': tmppath / "organized"
                }
            )
            
            # Run for multiple iterations
            total_processed = 0
            iterations = 10
            
            for i in range(iterations):
                # Create fresh inbox
                inbox = tmppath / "inbox"
                if inbox.exists():
                    import shutil
                    shutil.rmtree(inbox)
                inbox.mkdir()
                
                # Create files
                create_test_files(inbox, 1000)
                
                # Process
                organizer = ResilientMediaOrganizer(config)
                results = organizer.organize()
                
                total_processed += results.statistics['organized']
                
                # Check for resource leaks
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                open_files = len(process.open_files())
                
                print(f"\nIteration {i+1}:")
                print(f"  Processed: {results.statistics['organized']}")
                print(f"  Memory: {memory_mb:.2f} MB")
                print(f"  Open files: {open_files}")
                
                # Memory should not grow unbounded
                if i > 0:
                    assert memory_mb < 500, f"Memory leak detected: {memory_mb:.2f} MB"
                
                # File handles should be closed
                assert open_files < 100, f"File handle leak: {open_files} open files"
            
            assert total_processed == iterations * 1000


class TestPerformanceBenchmarks:
    """Benchmark different performance profiles."""
    
    def run_benchmark(self, config: AliceMultiverseConfig, file_count: int) -> Dict[str, Any]:
        """Run a single benchmark."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            
            # Set paths in config
            config.paths.inbox = inbox
            config.paths.organized = tmppath / "organized"
            
            # Create test files
            files = create_test_files(inbox, file_count)
            
            # Create organizer
            organizer = ResilientMediaOrganizer(config)
            
            # Measure performance
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            results = organizer.organize()
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            duration = end_time - start_time
            
            return {
                'profile': config.performance.profile,
                'file_count': file_count,
                'duration': duration,
                'files_per_second': file_count / duration,
                'memory_used': end_memory - start_memory,
                'errors': results.statistics['errors']
            }
    
    @pytest.mark.slow
    def test_profile_comparison(self):
        """Compare performance of different profiles."""
        profiles = ['default', 'fast', 'memory_constrained', 'large_collection']
        file_counts = [1000, 5000, 10000]
        
        results = []
        
        for profile in profiles:
            for file_count in file_counts:
                config = AliceMultiverseConfig(
                    performance={'profile': profile}
                )
                
                print(f"\nBenchmarking {profile} with {file_count} files...")
                benchmark = self.run_benchmark(config, file_count)
                results.append(benchmark)
                
                print(f"  Duration: {benchmark['duration']:.2f}s")
                print(f"  Rate: {benchmark['files_per_second']:.2f} files/s")
                print(f"  Memory: {benchmark['memory_used']:.2f} MB")
        
        # Save results
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(results, f, indent=2)
            print(f"\nBenchmark results saved to: {f.name}")
        
        # Verify fast profile is actually faster
        fast_results = [r for r in results if r['profile'] == 'fast']
        default_results = [r for r in results if r['profile'] == 'default']
        
        for fast, default in zip(fast_results, default_results):
            if fast['file_count'] == default['file_count']:
                assert fast['files_per_second'] > default['files_per_second']


@pytest.fixture
def reset_metrics():
    """Reset performance metrics between tests."""
    yield
    PerformanceMetrics._instance = None
    PerformanceTracker._instance = None