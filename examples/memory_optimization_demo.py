#!/usr/bin/env python3
"""
Memory Optimization Demo

This script demonstrates memory optimization features including:
- Streaming file processing
- Bounded caching
- Object pooling
- Adaptive batch sizing
- Memory monitoring
"""

import sys
import time
import tempfile
import gc
from pathlib import Path
from typing import List, Dict, Any
import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.core.memory_optimization import (
    MemoryConfig, MemoryMonitor, StreamingFileReader,
    BoundedCache, ObjectPool, MemoryOptimizedBatchProcessor
)
from alicemultiverse.organizer.memory_optimized_organizer import (
    MemoryOptimizedOrganizer, StreamingAnalyzer
)
from alicemultiverse.core.config import AliceMultiverseConfig


def print_memory_usage(label: str):
    """Print current memory usage."""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"{label}: {memory_mb:.1f} MB")


def demonstrate_streaming_reader():
    """Demonstrate streaming file reading."""
    print("\n" + "="*60)
    print("Streaming File Reader Demo")
    print("="*60)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        # Create a large file
        print("\n→ Creating 10MB test file...")
        for i in range(1000000):
            tmp.write(f"Line {i}: {'x' * 50}\n")
        tmp_path = Path(tmp.name)
    
    try:
        file_size_mb = tmp_path.stat().st_size / 1024 / 1024
        print(f"  File size: {file_size_mb:.1f} MB")
        
        # Read entire file at once (bad for memory)
        print("\n→ Reading entire file at once...")
        print_memory_usage("  Before reading")
        
        start = time.time()
        with open(tmp_path, 'r') as f:
            content = f.read()
        
        print_memory_usage("  After reading")
        print(f"  Time: {time.time() - start:.2f}s")
        print(f"  Lines: {len(content.splitlines())}")
        
        del content
        gc.collect()
        
        # Read using streaming (memory efficient)
        print("\n→ Reading file with streaming...")
        print_memory_usage("  Before streaming")
        
        config = MemoryConfig(chunk_size_kb=512)
        reader = StreamingFileReader(config)
        
        start = time.time()
        line_count = 0
        for line in reader.read_lines(tmp_path):
            line_count += 1
        
        print_memory_usage("  After streaming")
        print(f"  Time: {time.time() - start:.2f}s")
        print(f"  Lines: {line_count}")
        
    finally:
        tmp_path.unlink()


def demonstrate_bounded_cache():
    """Demonstrate bounded cache with memory limits."""
    print("\n" + "="*60)
    print("Bounded Cache Demo")
    print("="*60)
    
    # Create cache with 10MB limit
    config = MemoryConfig(cache_size_mb=10, cache_ttl_seconds=60)
    cache = BoundedCache[str](config)
    
    print("\n→ Adding items to cache...")
    print_memory_usage("  Initial memory")
    
    # Add items until cache is full
    for i in range(1000):
        # Create 100KB strings
        value = 'x' * (100 * 1024)
        cache.set(f"key_{i}", value)
        
        if i % 100 == 0:
            stats = cache.get_stats()
            print(f"  Items: {stats['entries']}, "
                  f"Size: {stats['size_mb']:.1f} MB, "
                  f"Hit rate: {stats['hit_rate']:.2%}")
    
    print_memory_usage("  After filling cache")
    
    # Test cache hits
    print("\n→ Testing cache performance...")
    hits = 0
    misses = 0
    
    for i in range(200):
        # Try to get recent items (likely in cache)
        if cache.get(f"key_{900 + i}"):
            hits += 1
        else:
            misses += 1
    
    print(f"  Recent items - Hits: {hits}, Misses: {misses}")
    
    # Try old items (likely evicted)
    hits = misses = 0
    for i in range(200):
        if cache.get(f"key_{i}"):
            hits += 1
        else:
            misses += 1
    
    print(f"  Old items - Hits: {hits}, Misses: {misses}")
    
    final_stats = cache.get_stats()
    print(f"\n  Final cache stats:")
    print(f"    Entries: {final_stats['entries']}")
    print(f"    Size: {final_stats['size_mb']:.1f} MB")
    print(f"    Hit rate: {final_stats['hit_rate']:.2%}")


def demonstrate_object_pooling():
    """Demonstrate object pooling for resource reuse."""
    print("\n" + "="*60)
    print("Object Pooling Demo")
    print("="*60)
    
    # Expensive object creation
    class ExpensiveResource:
        instances_created = 0
        
        def __init__(self):
            ExpensiveResource.instances_created += 1
            self.id = ExpensiveResource.instances_created
            # Simulate expensive initialization
            time.sleep(0.1)
            self.data = [0] * 1000000  # ~8MB
        
        def reset(self):
            self.data = [0] * 1000000
    
    # Create pool
    pool = ObjectPool(
        factory=ExpensiveResource,
        reset_func=lambda obj: obj.reset(),
        max_size=3
    )
    
    print("\n→ Using resources without pooling...")
    start = time.time()
    
    # Without pooling - create new each time
    for i in range(5):
        resource = ExpensiveResource()
        print(f"  Created resource {resource.id}")
        del resource
    
    print(f"  Time: {time.time() - start:.2f}s")
    print(f"  Resources created: {ExpensiveResource.instances_created}")
    
    print("\n→ Using resources with pooling...")
    start = time.time()
    
    # With pooling - reuse resources
    for i in range(5):
        with pool.acquire() as resource:
            print(f"  Using resource {resource.id}")
    
    print(f"  Time: {time.time() - start:.2f}s")
    
    stats = pool.get_stats()
    print(f"  Pool stats - Created: {stats['created']}, Reused: {stats['reused']}")


def demonstrate_adaptive_batch_processing():
    """Demonstrate adaptive batch processing based on memory."""
    print("\n" + "="*60)
    print("Adaptive Batch Processing Demo")
    print("="*60)
    
    config = MemoryConfig(
        max_memory_mb=512,
        adaptive_batch_size=True,
        min_batch_size=10,
        max_batch_size=500
    )
    
    processor = MemoryOptimizedBatchProcessor(config)
    
    # Create items to process
    items = range(1000)
    
    print("\n→ Processing with adaptive batch sizes...")
    print_memory_usage("  Initial memory")
    
    batch_sizes = []
    
    def process_batch(batch: List[int]) -> Dict[str, Any]:
        """Process a batch of items."""
        batch_sizes.append(len(batch))
        
        # Simulate memory-intensive processing
        data = [list(range(1000)) for _ in batch]
        
        print(f"  Processing batch of {len(batch)} items...")
        
        # Simulate some work
        time.sleep(0.1)
        
        return {
            'count': len(batch),
            'sum': sum(batch),
            'data_size': len(data)
        }
    
    # Process all items
    results = list(processor.process_items(
        iter(items),
        process_batch,
        base_batch_size=200
    ))
    
    print_memory_usage("  Final memory")
    
    print(f"\n  Processed {len(results)} batches")
    print(f"  Batch sizes: {batch_sizes}")
    print(f"  Average batch size: {sum(batch_sizes) / len(batch_sizes):.1f}")


def demonstrate_memory_optimized_organizer():
    """Demonstrate memory-optimized file organization."""
    print("\n" + "="*60)
    print("Memory-Optimized Organizer Demo")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        inbox = tmppath / "inbox"
        inbox.mkdir()
        organized = tmppath / "organized"
        organized.mkdir()
        
        # Create test files
        print("\n→ Creating test files...")
        file_count = 500
        for i in range(file_count):
            file_path = inbox / f"test_{i:04d}.jpg"
            # Create files of varying sizes
            size = 10000 + (i % 100) * 1000  # 10KB to 110KB
            file_path.write_bytes(b'x' * size)
        
        total_size_mb = sum(f.stat().st_size for f in inbox.rglob("*")) / 1024 / 1024
        print(f"  Created {file_count} files, total size: {total_size_mb:.1f} MB")
        
        # Configure for memory optimization
        config = AliceMultiverseConfig(
            paths={'inbox': inbox, 'organized': organized},
            performance={'profile': 'memory_constrained'}
        )
        
        memory_config = MemoryConfig(
            max_memory_mb=256,
            cache_size_mb=32,
            adaptive_batch_size=True
        )
        
        print("\n→ Processing with memory optimization...")
        print(f"  Memory limit: {memory_config.max_memory_mb} MB")
        print(f"  Cache size: {memory_config.cache_size_mb} MB")
        
        organizer = MemoryOptimizedOrganizer(config, memory_config)
        
        # Monitor memory during processing
        print_memory_usage("  Before processing")
        
        start = time.time()
        results = organizer.organize()
        duration = time.time() - start
        
        print_memory_usage("  After processing")
        
        # Show results
        stats = organizer.get_memory_stats()
        
        print(f"\n  Results:")
        print(f"    Files processed: {results.statistics['organized']}")
        print(f"    Time: {duration:.2f}s")
        print(f"    Rate: {results.statistics['organized'] / duration:.1f} files/s")
        
        print(f"\n  Memory stats:")
        print(f"    Peak memory: {stats['peak_memory_mb']:.1f} MB")
        print(f"    GC collections: {stats['gc_collections']}")
        print(f"    Cache hit rate: {stats['cache_stats']['hit_rate']:.2%}")
        print(f"    Objects pooled: {stats['executor_pool_stats']['reused']}")


def main():
    """Run all demonstrations."""
    print("AliceMultiverse Memory Optimization Demo")
    print("=" * 60)
    
    demos = [
        ("Streaming File Reader", demonstrate_streaming_reader),
        ("Bounded Cache", demonstrate_bounded_cache),
        ("Object Pooling", demonstrate_object_pooling),
        ("Adaptive Batch Processing", demonstrate_adaptive_batch_processing),
        ("Memory-Optimized Organizer", demonstrate_memory_optimized_organizer)
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n✗ {name} failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Clean up between demos
        gc.collect()
        time.sleep(1)
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)
    
    # Final memory report
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"\nFinal memory report:")
    print(f"  RSS: {memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"  VMS: {memory_info.vms / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()