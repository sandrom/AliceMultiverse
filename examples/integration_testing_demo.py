#!/usr/bin/env python3
"""
Integration Testing Demo

This script demonstrates the comprehensive integration testing capabilities
including performance benchmarking, memory profiling, and stress testing.
"""

import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.monitoring.metrics import PerformanceMetrics
from alicemultiverse.monitoring.dashboard import MetricsDashboard
from alicemultiverse.organizer.resilient_organizer import ResilientMediaOrganizer
from alicemultiverse.core.config import AliceMultiverseConfig
from tests.integration.test_large_scale_performance import create_test_files
from tests.integration.test_memory_profiling import MemoryProfiler
from tests.integration.test_stress_resilience import ChaosMonkey


def demonstrate_performance_testing():
    """Demonstrate performance testing capabilities."""
    print("\n" + "="*60)
    print("Performance Testing Demo")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        inbox = tmppath / "inbox"
        inbox.mkdir()
        organized = tmppath / "organized"
        organized.mkdir()
        
        # Test different file counts
        file_counts = [100, 500, 1000]
        
        for count in file_counts:
            print(f"\n→ Testing with {count} files...")
            
            # Clear inbox
            for f in inbox.glob("*"):
                f.unlink()
            
            # Create test files
            start = time.time()
            files = create_test_files(inbox, count)
            create_time = time.time() - start
            print(f"  Created {count} files in {create_time:.2f}s")
            
            # Configure for performance
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized},
                performance={'profile': 'fast', 'max_workers': 8}
            )
            
            # Process files
            organizer = ResilientMediaOrganizer(config)
            start = time.time()
            results = organizer.organize()
            process_time = time.time() - start
            
            # Show results
            rate = count / process_time
            print(f"  Processed {count} files in {process_time:.2f}s")
            print(f"  Rate: {rate:.2f} files/second")
            print(f"  Errors: {results.statistics['errors']}")
            
            # Get metrics
            metrics = PerformanceMetrics.get_instance()
            print(f"  Cache hit rate: {metrics.get_cache_hit_rate():.2%}")
            
            # Reset metrics for next run
            PerformanceMetrics._instance = None


def demonstrate_memory_profiling():
    """Demonstrate memory profiling capabilities."""
    print("\n" + "="*60)
    print("Memory Profiling Demo")
    print("="*60)
    
    profiler = MemoryProfiler()
    profiler.start()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Simulate memory-intensive operations
        for i in range(3):
            print(f"\n→ Iteration {i+1}")
            
            inbox = tmppath / f"inbox_{i}"
            inbox.mkdir()
            organized = tmppath / f"organized_{i}"
            organized.mkdir()
            
            # Create files
            files = create_test_files(inbox, 500)
            
            # Process with memory monitoring
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': organized},
                performance={'profile': 'memory_constrained'}
            )
            
            organizer = ResilientMediaOrganizer(config)
            results = organizer.organize()
            
            # Take memory snapshot
            profiler.take_snapshot(f"after_iteration_{i+1}")
            
            # Clean up
            del organizer
            del results
    
    profiler.stop()
    
    # Show memory analysis
    print("\n=== Memory Analysis ===")
    profiler.compare_snapshots(0, -1)
    
    stats = profiler.get_memory_stats()
    print(f"\nMemory Statistics:")
    print(f"  Initial: {stats['initial_mb']:.2f} MB")
    print(f"  Peak: {stats['peak_mb']:.2f} MB")
    print(f"  Final: {stats['final_mb']:.2f} MB")
    print(f"  Growth: {stats['growth_mb']:.2f} MB")
    
    # Save memory plot
    profiler.plot_memory_usage("demo_memory_usage.png")


def demonstrate_chaos_testing():
    """Demonstrate chaos engineering and resilience testing."""
    print("\n" + "="*60)
    print("Chaos Engineering Demo")
    print("="*60)
    
    chaos = ChaosMonkey(failure_rate=0.3)  # 30% failure rate
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        inbox = tmppath / "inbox"
        inbox.mkdir()
        organized = tmppath / "organized"
        organized.mkdir()
        
        # Create test files
        file_count = 100
        files = create_test_files(inbox, file_count)
        
        config = AliceMultiverseConfig(
            paths={'inbox': inbox, 'organized': organized}
        )
        
        organizer = ResilientMediaOrganizer(config)
        
        # Inject chaos
        original_process = organizer._process_file_impl
        
        def chaotic_process(file_path: Path):
            chaos.maybe_fail(str(file_path))
            return original_process(file_path)
        
        organizer._process_file_impl = chaotic_process
        
        print(f"\n→ Processing {file_count} files with {chaos.failure_rate:.0%} failure rate...")
        
        # Process with chaos
        start = time.time()
        results = organizer.organize()
        duration = time.time() - start
        
        # Show results
        chaos_stats = chaos.get_stats()
        success_rate = results.statistics['organized'] / file_count
        
        print(f"\nResults:")
        print(f"  Files processed: {results.statistics['organized']}/{file_count}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Processing time: {duration:.2f}s")
        print(f"\nChaos Statistics:")
        print(f"  Failures injected: {chaos_stats['failure_count']}")
        print(f"  Actual failure rate: {chaos_stats['failure_rate']:.2%}")
        print(f"\nResilience Metrics:")
        print(f"  Retries performed: {organizer.error_recovery.get_retry_stats()['total_retries']}")
        print(f"  Degradation level: {organizer.graceful_degradation.get_current_level().name}")
        
        if organizer.graceful_degradation.disabled_features:
            print(f"  Disabled features: {', '.join(organizer.graceful_degradation.disabled_features)}")


def demonstrate_concurrent_testing():
    """Demonstrate concurrent operation testing."""
    print("\n" + "="*60)
    print("Concurrent Operations Demo")
    print("="*60)
    
    import concurrent.futures
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create multiple inbox directories
        inbox_count = 4
        file_per_inbox = 250
        
        inboxes = []
        for i in range(inbox_count):
            inbox = tmppath / f"inbox_{i}"
            inbox.mkdir()
            inboxes.append(inbox)
            create_test_files(inbox, file_per_inbox)
        
        organized = tmppath / "organized"
        organized.mkdir()
        
        print(f"\n→ Running {inbox_count} organizers concurrently...")
        print(f"  Each processing {file_per_inbox} files")
        
        # Function to run single organizer
        def run_organizer(inbox_path: Path) -> Dict[str, Any]:
            config = AliceMultiverseConfig(
                paths={'inbox': inbox_path, 'organized': organized},
                performance={'max_workers': 4}  # Limited workers per instance
            )
            
            organizer = ResilientMediaOrganizer(config)
            start = time.time()
            results = organizer.organize()
            duration = time.time() - start
            
            return {
                'inbox': inbox_path.name,
                'files': results.statistics['organized'],
                'errors': results.statistics['errors'],
                'duration': duration
            }
        
        # Run concurrently
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=inbox_count) as executor:
            future_to_inbox = {
                executor.submit(run_organizer, inbox): inbox 
                for inbox in inboxes
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_inbox):
                result = future.result()
                results.append(result)
                print(f"  ✓ {result['inbox']} completed: "
                      f"{result['files']} files in {result['duration']:.2f}s")
        
        total_duration = time.time() - start_time
        
        # Summary
        total_files = sum(r['files'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        
        print(f"\nConcurrent Processing Summary:")
        print(f"  Total files processed: {total_files}")
        print(f"  Total errors: {total_errors}")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Effective rate: {total_files/total_duration:.2f} files/second")


def main():
    """Run all demonstrations."""
    print("AliceMultiverse Integration Testing Demo")
    print("========================================")
    
    demos = [
        ("Performance Testing", demonstrate_performance_testing),
        ("Memory Profiling", demonstrate_memory_profiling),
        ("Chaos Engineering", demonstrate_chaos_testing),
        ("Concurrent Operations", demonstrate_concurrent_testing)
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n✗ {name} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)
    
    # Show performance dashboard
    print("\nWould you like to see the performance dashboard? (y/n): ", end='', flush=True)
    response = input().strip().lower()
    
    if response == 'y':
        print("\nStarting performance dashboard...")
        print("Press Ctrl+C to exit")
        
        dashboard = MetricsDashboard()
        try:
            dashboard.run()
        except KeyboardInterrupt:
            print("\nDashboard closed.")


if __name__ == "__main__":
    main()