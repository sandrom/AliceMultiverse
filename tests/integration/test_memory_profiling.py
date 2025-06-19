"""Memory profiling and leak detection tests."""

import pytest
import tempfile
import gc
import time
import tracemalloc
import psutil
import weakref
from pathlib import Path
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import numpy as np

from alicemultiverse.organizer.resilient_organizer import ResilientMediaOrganizer
from alicemultiverse.core.config import AliceMultiverseConfig
from alicemultiverse.monitoring.metrics import PerformanceMetrics
from alicemultiverse.core.cache import UnifiedCache


class MemoryProfiler:
    """Memory profiling utilities."""
    
    def __init__(self):
        self.snapshots: List[tracemalloc.Snapshot] = []
        self.memory_usage: List[float] = []
        self.timestamps: List[float] = []
        self.start_time = time.time()
    
    def start(self):
        """Start memory profiling."""
        tracemalloc.start()
        self.take_snapshot("start")
    
    def stop(self):
        """Stop memory profiling."""
        self.take_snapshot("end")
        tracemalloc.stop()
    
    def take_snapshot(self, label: str):
        """Take a memory snapshot."""
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append(snapshot)
        
        # Record current memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_usage.append(memory_mb)
        self.timestamps.append(time.time() - self.start_time)
        
        # Get top memory consumers
        top_stats = snapshot.statistics('lineno')[:10]
        
        print(f"\n=== Memory Snapshot: {label} ===")
        print(f"Total memory: {memory_mb:.2f} MB")
        print("\nTop 10 memory consumers:")
        for stat in top_stats:
            print(f"  {stat}")
    
    def compare_snapshots(self, start_idx: int = 0, end_idx: int = -1):
        """Compare two snapshots to find memory growth."""
        if len(self.snapshots) < 2:
            return
        
        start = self.snapshots[start_idx]
        end = self.snapshots[end_idx]
        
        top_stats = end.compare_to(start, 'lineno')[:10]
        
        print("\n=== Memory Growth ===")
        for stat in top_stats:
            print(f"  {stat}")
    
    def plot_memory_usage(self, filename: str = "memory_usage.png"):
        """Plot memory usage over time."""
        if not self.memory_usage:
            return
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.timestamps, self.memory_usage, 'b-', linewidth=2)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Memory Usage (MB)')
        plt.title('Memory Usage Over Time')
        plt.grid(True, alpha=0.3)
        
        # Add markers for min/max
        min_idx = np.argmin(self.memory_usage)
        max_idx = np.argmax(self.memory_usage)
        
        plt.plot(self.timestamps[min_idx], self.memory_usage[min_idx], 'go', 
                markersize=10, label=f'Min: {self.memory_usage[min_idx]:.2f} MB')
        plt.plot(self.timestamps[max_idx], self.memory_usage[max_idx], 'ro', 
                markersize=10, label=f'Max: {self.memory_usage[max_idx]:.2f} MB')
        
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
        
        print(f"\nMemory usage plot saved to: {filename}")
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory statistics."""
        if not self.memory_usage:
            return {}
        
        return {
            'initial_mb': self.memory_usage[0],
            'final_mb': self.memory_usage[-1],
            'peak_mb': max(self.memory_usage),
            'min_mb': min(self.memory_usage),
            'growth_mb': self.memory_usage[-1] - self.memory_usage[0],
            'avg_mb': sum(self.memory_usage) / len(self.memory_usage)
        }


class TestMemoryLeaks:
    """Test for memory leaks in various components."""
    
    @pytest.mark.slow
    def test_organizer_memory_leak(self):
        """Test for memory leaks in the organizer."""
        profiler = MemoryProfiler()
        profiler.start()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Run multiple iterations
            for i in range(5):
                print(f"\n--- Iteration {i+1} ---")
                
                # Create fresh directories
                inbox = tmppath / f"inbox_{i}"
                inbox.mkdir()
                organized = tmppath / f"organized_{i}"
                organized.mkdir()
                
                # Create test files
                for j in range(1000):
                    file_path = inbox / f"test_{j:04d}.jpg"
                    file_path.write_bytes(b'test' * 1000)
                
                # Create and use organizer
                config = AliceMultiverseConfig(
                    paths={'inbox': inbox, 'organized': organized}
                )
                
                organizer = ResilientMediaOrganizer(config)
                results = organizer.organize()
                
                # Clean up references
                del organizer
                del results
                del config
                
                # Force garbage collection
                gc.collect()
                
                # Take snapshot
                profiler.take_snapshot(f"iteration_{i+1}")
        
        profiler.stop()
        profiler.compare_snapshots()
        profiler.plot_memory_usage("test_organizer_memory.png")
        
        # Check for memory growth
        stats = profiler.get_memory_stats()
        growth = stats['growth_mb']
        
        print(f"\nMemory growth: {growth:.2f} MB")
        assert growth < 50, f"Excessive memory growth: {growth:.2f} MB"
    
    @pytest.mark.slow
    def test_cache_memory_leak(self):
        """Test for memory leaks in the cache system."""
        profiler = MemoryProfiler()
        profiler.start()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache"
            cache = UnifiedCache(cache_path)
            
            # Simulate heavy cache usage
            for i in range(10):
                print(f"\nCache iteration {i+1}")
                
                # Add many items to cache
                for j in range(1000):
                    key = f"test_key_{i}_{j}"
                    data = {
                        'data': 'x' * 1000,  # 1KB of data
                        'metadata': {
                            'iteration': i,
                            'index': j
                        }
                    }
                    cache.set(key, data)
                
                # Clear some items
                if i % 2 == 0:
                    cache.cache_data.clear()
                
                # Take snapshot
                profiler.take_snapshot(f"cache_iter_{i+1}")
                
                # Force garbage collection
                gc.collect()
        
        profiler.stop()
        profiler.compare_snapshots()
        
        stats = profiler.get_memory_stats()
        assert stats['growth_mb'] < 100, f"Cache memory leak: {stats['growth_mb']:.2f} MB growth"
    
    def test_metrics_memory_leak(self):
        """Test for memory leaks in metrics collection."""
        profiler = MemoryProfiler()
        profiler.start()
        
        metrics = PerformanceMetrics.get_instance()
        
        # Simulate heavy metrics collection
        for i in range(10000):
            metrics.record_file_processed(Path(f"test_{i}.jpg"), 0.01)
            metrics.record_cache_hit()
            metrics.record_database_operation("select", 0.001)
            
            if i % 1000 == 0:
                profiler.take_snapshot(f"metrics_{i}")
        
        profiler.stop()
        stats = profiler.get_memory_stats()
        
        # Metrics should have bounded memory usage
        assert stats['growth_mb'] < 10, f"Metrics memory leak: {stats['growth_mb']:.2f} MB growth"
    
    def test_circular_references(self):
        """Test for circular references that prevent garbage collection."""
        # Track object creation
        created_objects = []
        
        class TrackedOrganizer(ResilientMediaOrganizer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                created_objects.append(weakref.ref(self))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized}
            )
            
            # Create organizer
            organizer = TrackedOrganizer(config)
            
            # Create potential circular reference
            organizer._self_ref = organizer
            
            # Delete organizer
            del organizer
            
            # Force garbage collection
            gc.collect()
            
            # Check if object was collected
            alive_objects = [ref for ref in created_objects if ref() is not None]
            assert len(alive_objects) == 0, "Circular reference prevents garbage collection"


class TestResourceUsage:
    """Test resource usage patterns."""
    
    @pytest.mark.slow
    def test_file_handle_management(self):
        """Test that file handles are properly closed."""
        process = psutil.Process()
        initial_handles = len(process.open_files())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create many files
            for i in range(1000):
                file_path = inbox / f"test_{i:04d}.jpg"
                file_path.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized}
            )
            
            organizer = ResilientMediaOrganizer(config)
            results = organizer.organize()
            
            # Check file handles
            final_handles = len(process.open_files())
            handle_growth = final_handles - initial_handles
            
            print(f"\nFile handles - Initial: {initial_handles}, Final: {final_handles}")
            assert handle_growth < 10, f"File handle leak: {handle_growth} handles not closed"
    
    @pytest.mark.slow
    def test_thread_cleanup(self):
        """Test that threads are properly cleaned up."""
        import threading
        
        initial_threads = threading.active_count()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            organized = tmppath / "organized"
            organized.mkdir()
            
            # Create files
            for i in range(100):
                file_path = inbox / f"test_{i:03d}.jpg"
                file_path.write_text(f"content {i}")
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized},
                performance={'max_workers': 8}
            )
            
            # Process files
            organizer = ResilientMediaOrganizer(config)
            results = organizer.organize()
            
            # Give threads time to clean up
            time.sleep(1)
            
            # Check thread count
            final_threads = threading.active_count()
            thread_growth = final_threads - initial_threads
            
            print(f"\nThreads - Initial: {initial_threads}, Final: {final_threads}")
            assert thread_growth <= 1, f"Thread leak: {thread_growth} threads not cleaned up"


class TestMemoryOptimization:
    """Test memory optimization strategies."""
    
    def test_batch_size_memory_impact(self):
        """Test memory usage with different batch sizes."""
        batch_sizes = [50, 100, 500, 1000]
        memory_usage = {}
        
        for batch_size in batch_sizes:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)
                inbox = tmppath / "inbox"
                inbox.mkdir()
                organized = tmppath / "organized"
                organized.mkdir()
                
                # Create files
                for i in range(2000):
                    file_path = inbox / f"test_{i:04d}.jpg"
                    file_path.write_bytes(b'x' * 10000)  # 10KB files
                
                config = AliceMultiverseConfig(
                    paths={'inbox': inbox, 'organized': organized},
                    performance={'batch_size': batch_size}
                )
                
                # Measure memory before
                gc.collect()
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024
                
                # Process files
                organizer = ResilientMediaOrganizer(config)
                results = organizer.organize()
                
                # Measure memory after
                memory_after = process.memory_info().rss / 1024 / 1024
                memory_peak = memory_after  # Simplified, would need monitoring
                
                memory_usage[batch_size] = {
                    'before': memory_before,
                    'after': memory_after,
                    'peak': memory_peak,
                    'growth': memory_after - memory_before
                }
                
                print(f"\nBatch size {batch_size}:")
                print(f"  Memory growth: {memory_usage[batch_size]['growth']:.2f} MB")
        
        # Larger batch sizes should use more memory
        assert memory_usage[1000]['peak'] > memory_usage[50]['peak']
        
        # But growth should be reasonable
        for batch_size, usage in memory_usage.items():
            assert usage['growth'] < 200, f"Excessive memory growth with batch size {batch_size}"


def create_memory_report(results: Dict[str, Any], output_file: str = "memory_report.md"):
    """Create a memory profiling report."""
    with open(output_file, 'w') as f:
        f.write("# Memory Profiling Report\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Initial Memory: {results.get('initial_mb', 0):.2f} MB\n")
        f.write(f"- Peak Memory: {results.get('peak_mb', 0):.2f} MB\n")
        f.write(f"- Final Memory: {results.get('final_mb', 0):.2f} MB\n")
        f.write(f"- Memory Growth: {results.get('growth_mb', 0):.2f} MB\n\n")
        
        f.write("## Recommendations\n\n")
        
        if results.get('growth_mb', 0) > 100:
            f.write("- **High memory growth detected**. Consider:\n")
            f.write("  - Reducing batch sizes\n")
            f.write("  - Implementing memory limits\n")
            f.write("  - Adding periodic garbage collection\n\n")
        
        if results.get('peak_mb', 0) > 1000:
            f.write("- **High peak memory usage**. Consider:\n")
            f.write("  - Using memory_constrained profile\n")
            f.write("  - Reducing parallel workers\n")
            f.write("  - Streaming large files\n\n")
    
    print(f"\nMemory report saved to: {output_file}")