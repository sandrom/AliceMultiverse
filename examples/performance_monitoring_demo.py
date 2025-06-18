#!/usr/bin/env python3
"""
Performance Monitoring Demo

This script demonstrates the performance monitoring capabilities of AliceMultiverse.
It shows how to:
1. Track file processing performance
2. Monitor cache effectiveness
3. Analyze database operations
4. Generate performance reports
"""

import time
from pathlib import Path
import tempfile

from alicemultiverse.monitoring.metrics import MetricsCollector
from alicemultiverse.monitoring.tracker import (
    PerformanceTracker,
    track_file_processing,
    track_database_operation,
    track_operation,
    track_cache_access
)
from alicemultiverse.monitoring.dashboard import MetricsDashboard


def simulate_file_processing():
    """Simulate processing files with performance tracking."""
    tracker = PerformanceTracker()
    
    print("Simulating file processing...")
    
    # Create some temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Simulate processing different file types
        file_types = [".jpg", ".png", ".mp4", ".webp"]
        for i in range(20):
            file_type = file_types[i % len(file_types)]
            file_path = tmppath / f"file_{i}{file_type}"
            file_path.write_bytes(b"dummy content" * 100)
            
            # Track file processing
            with track_file_processing(file_path):
                # Simulate processing time
                processing_time = 0.05 + (i % 4) * 0.02
                time.sleep(processing_time)
                
                # Simulate cache access (80% hit rate)
                if i % 5 != 0:
                    track_cache_access(True)
                else:
                    track_cache_access(False)
                
                # Simulate database operations
                if i % 3 == 0:
                    with track_database_operation():
                        time.sleep(0.01)
        
        print(f"Processed {i+1} files")


def simulate_batch_operations():
    """Simulate batch database operations."""
    print("\nSimulating batch operations...")
    
    # Track different types of operations
    operations = [
        ("metadata.extract", 0.02),
        ("ai.analyze", 0.1),
        ("hash.compute", 0.03),
        ("index.update", 0.01)
    ]
    
    for op_name, duration in operations * 5:
        with track_operation(op_name):
            time.sleep(duration)
    
    print("Completed batch operations")


def show_performance_report():
    """Display the performance report."""
    collector = MetricsCollector.get_instance()
    report = collector.get_performance_report()
    
    print("\n" + "="*60)
    print("PERFORMANCE REPORT")
    print("="*60)
    
    # Summary
    summary = report['summary']
    print(f"\nSummary:")
    print(f"  Total Files: {summary['total_files']:,}")
    print(f"  Total Time: {summary['total_time']:.2f}s")
    print(f"  Processing Rate: {summary['files_per_second']:.2f} files/sec")
    print(f"  Error Rate: {summary['error_rate']:.1f}%")
    
    # Memory
    memory = report['memory']
    print(f"\nMemory Usage:")
    print(f"  Current: {memory['current_mb']:.1f} MB")
    print(f"  Peak: {memory['peak_mb']:.1f} MB")
    
    # Cache Performance
    cache = report['cache']
    print(f"\nCache Performance:")
    print(f"  Hits: {cache['hits']:,}")
    print(f"  Misses: {cache['misses']:,}")
    print(f"  Hit Rate: {cache['hit_rate']:.1f}%")
    
    # Database Performance
    database = report['database']
    print(f"\nDatabase Performance:")
    print(f"  Operations: {database['operations']:,}")
    print(f"  Total Time: {database['total_time']:.2f}s")
    print(f"  Overhead: {database['overhead_percent']:.1f}%")
    
    # File Types
    print(f"\nFile Type Breakdown:")
    for ext, stats in sorted(report['file_types'].items(), 
                           key=lambda x: x[1]['count'], reverse=True):
        print(f"  {ext}: {stats['count']} files, "
              f"{stats['average_time']:.3f}s avg, "
              f"{stats['average_size_mb']:.2f} MB avg size")
    
    # Top Operations
    print(f"\nTop Operations by Time:")
    sorted_ops = sorted(report['operations'].items(), 
                       key=lambda x: x[1]['total'], reverse=True)[:5]
    for op_name, stats in sorted_ops:
        print(f"  {op_name}: {stats['count']} calls, "
              f"{stats['average']:.3f}s avg, "
              f"{stats['total']:.2f}s total")


def main():
    """Run the performance monitoring demo."""
    print("AliceMultiverse Performance Monitoring Demo")
    print("-" * 40)
    
    # Reset metrics to start fresh
    collector = MetricsCollector.get_instance()
    collector.reset()
    
    # Run simulations
    simulate_file_processing()
    simulate_batch_operations()
    
    # Show report
    show_performance_report()
    
    # Show dashboard (for 5 seconds)
    print("\n\nShowing live dashboard for 5 seconds...")
    dashboard = MetricsDashboard()
    dashboard.show_once()
    
    # Export metrics
    print("\nExporting metrics to performance_demo.json...")
    Path("performance_demo.json").unlink(missing_ok=True)
    collector.save_report(Path("performance_demo.json"))
    print("Done!")


if __name__ == "__main__":
    main()