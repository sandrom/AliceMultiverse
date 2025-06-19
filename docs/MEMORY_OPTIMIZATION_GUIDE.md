# Memory Optimization Guide

This guide covers memory optimization features in AliceMultiverse for handling large media collections efficiently.

## Overview

AliceMultiverse includes comprehensive memory optimization features:

- **Streaming file processing** to handle files larger than available RAM
- **Bounded caching** with automatic eviction and TTL support
- **Object pooling** for expensive resource reuse
- **Adaptive batch sizing** based on memory pressure
- **Memory monitoring** with real-time tracking
- **Garbage collection** optimization

## Memory Profiles

### Default Configuration

```python
MemoryConfig(
    max_memory_mb=1024,      # 1GB limit
    cache_size_mb=256,       # 256MB cache
    chunk_size_kb=1024,      # 1MB chunks
    adaptive_batch_size=True # Dynamic adjustment
)
```

### Memory-Constrained Systems

For systems with limited RAM (< 8GB):

```python
MemoryConfig(
    max_memory_mb=512,       # 512MB limit
    cache_size_mb=64,        # 64MB cache
    chunk_size_kb=256,       # 256KB chunks
    gc_threshold_mb=256,     # Aggressive GC
    min_batch_size=10,       # Small batches
    max_batch_size=100
)
```

### Large Collections

For processing 50K+ files:

```python
MemoryConfig(
    max_memory_mb=2048,      # 2GB limit
    cache_size_mb=512,       # 512MB cache
    chunk_size_kb=2048,      # 2MB chunks
    adaptive_batch_size=True,
    max_batch_size=1000      # Large batches
)
```

## Using Memory-Optimized Organizer

### Basic Usage

```python
from alicemultiverse.organizer.memory_optimized_organizer import (
    MemoryOptimizedOrganizer
)
from alicemultiverse.core.memory_optimization import MemoryConfig

# Configure memory limits
memory_config = MemoryConfig(
    max_memory_mb=512,
    cache_size_mb=64,
    adaptive_batch_size=True
)

# Create organizer
organizer = MemoryOptimizedOrganizer(config, memory_config)

# Process files with memory optimization
results = organizer.organize()

# Check memory statistics
stats = organizer.get_memory_stats()
print(f"Peak memory: {stats['peak_memory_mb']:.1f} MB")
print(f"Cache hit rate: {stats['cache_stats']['hit_rate']:.2%}")
```

### Monitoring Memory Usage

```python
from alicemultiverse.core.memory_optimization import MemoryMonitor

monitor = MemoryMonitor(memory_config)

# Check current usage
usage = monitor.get_memory_usage()
print(f"Current: {usage['current_mb']:.1f} MB")
print(f"Available: {usage['available_mb']:.1f} MB")

# Check for memory pressure
if monitor.check_memory_pressure():
    print("Warning: High memory usage!")
    monitor.maybe_collect_garbage(force=True)

# Get adaptive batch size
batch_size = monitor.get_adaptive_batch_size(100)
```

## Streaming File Processing

### Reading Large Files

```python
from alicemultiverse.core.memory_optimization import StreamingFileReader

reader = StreamingFileReader(memory_config)

# Read in chunks
for chunk in reader.read_chunks(large_file_path):
    process_chunk(chunk)

# Read line by line
for line in reader.read_lines(text_file_path):
    process_line(line)

# Process with memory management
results = reader.process_large_file(
    file_path,
    chunk_processor_func
)
```

### Memory-Mapped Files

```python
# Use memory mapping for efficient access
with reader.open_mmap(file_path, 'r') as f:
    # File is memory-mapped
    content = f.read()
```

## Bounded Caching

### Cache with Size Limits

```python
from alicemultiverse.core.memory_optimization import BoundedCache

# Create cache with 100MB limit
cache = BoundedCache[Dict](MemoryConfig(cache_size_mb=100))

# Add items
cache.set("key1", large_data)

# Automatic eviction when full
stats = cache.get_stats()
print(f"Cache usage: {stats['size_mb']:.1f}/{stats['max_size_mb']} MB")
```

### TTL Support

```python
# Cache with 5-minute TTL
config = MemoryConfig(cache_ttl_seconds=300)
cache = BoundedCache(config)

cache.set("temp_key", data)
# Automatically expires after 5 minutes
```

## Object Pooling

### Reusing Expensive Objects

```python
from alicemultiverse.core.memory_optimization import ObjectPool

# Pool for thread executors
executor_pool = ObjectPool(
    factory=lambda: ThreadPoolExecutor(max_workers=8),
    reset_func=lambda ex: None,  # No reset needed
    max_size=3
)

# Use pooled object
with executor_pool.acquire() as executor:
    futures = [executor.submit(task) for task in tasks]
    
# Object returned to pool for reuse
```

### Custom Resource Pooling

```python
class DatabaseConnection:
    def __init__(self):
        self.conn = create_connection()
    
    def reset(self):
        self.conn.rollback()

# Pool database connections
db_pool = ObjectPool(
    factory=DatabaseConnection,
    reset_func=lambda db: db.reset(),
    max_size=10
)
```

## Adaptive Batch Processing

### Dynamic Batch Sizing

```python
from alicemultiverse.core.memory_optimization import (
    MemoryOptimizedBatchProcessor
)

processor = MemoryOptimizedBatchProcessor(memory_config)

# Process items with adaptive batching
for result in processor.process_items(
    items=file_iterator,
    processor=batch_processor_func,
    base_batch_size=100
):
    handle_result(result)
```

The batch size automatically adjusts based on memory pressure:
- Normal (< 40% memory): 100% of base size
- Medium (40-60% memory): 75% of base size  
- High (60-80% memory): 50% of base size
- Critical (> 80% memory): 25% of base size

## CLI Commands

### Memory Monitoring

```bash
# Real-time memory monitoring
alice --debug debug memory monitor --duration 60

# Memory profiling for a directory
alice --debug debug memory profile /path/to/media --top 20

# Show optimization recommendations
alice --debug debug memory optimize --profile memory_constrained

# Test memory configurations
alice --debug debug memory test /path/to/media --max-memory 512

# Force garbage collection
alice --debug debug memory gc
```

### Example Output

```
Memory Usage
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Metric       ┃ Value     ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Current      │ 245.3 MB  │
│ Peak         │ 487.2 MB  │
│ Available    │ 8192.0 MB │
│ System %     │ 45.2%     │
│ Limit        │ 512 MB    │
│ Usage Ratio  │ 47.9%     │
└──────────────┴───────────┘
```

## Best Practices

### 1. Choose Appropriate Limits

```python
# Based on system RAM
if total_ram < 4 * 1024:  # 4GB
    max_memory_mb = 256
elif total_ram < 8 * 1024:  # 8GB
    max_memory_mb = 512
else:
    max_memory_mb = 1024
```

### 2. Monitor Critical Operations

```python
@optimize_for_memory
def process_large_collection(files):
    """Automatically manages memory."""
    # GC before and after
    # GC disabled during execution
    return process_files(files)
```

### 3. Use Streaming for Large Files

```python
# Don't do this for large files
content = file_path.read_bytes()  # Loads entire file

# Do this instead
for chunk in reader.read_chunks(file_path):
    process_chunk(chunk)
```

### 4. Configure Cache Appropriately

```python
# Cache frequently accessed small items
metadata_cache = BoundedCache(
    MemoryConfig(cache_size_mb=256, cache_ttl_seconds=3600)
)

# Don't cache large binary data
# Use weak references for large objects
large_object_cache = WeakValueCache()
```

### 5. Pool Expensive Resources

```python
# Pool anything expensive to create
pools = {
    'executor': ObjectPool(create_executor),
    'analyzer': ObjectPool(create_analyzer),
    'connection': ObjectPool(create_connection)
}
```

## Performance Tips

### 1. Batch Size Tuning

Start with these baseline batch sizes:
- Small files (< 1MB): 500-1000 per batch
- Medium files (1-10MB): 100-200 per batch
- Large files (> 10MB): 20-50 per batch

### 2. Cache Size Guidelines

- Metadata cache: 10-20% of max memory
- Hash cache: 5-10% of max memory
- Result cache: 20-30% of max memory

### 3. GC Optimization

```python
# For batch operations
gc.disable()
try:
    process_batch()
finally:
    gc.enable()
    gc.collect()
```

### 4. Memory Profiling

```python
import tracemalloc

tracemalloc.start()
# Your code here
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')[:10]
```

## Troubleshooting

### High Memory Usage

1. Check cache sizes:
```bash
alice --debug debug memory monitor
```

2. Reduce batch sizes:
```python
config.performance.batch_size = 50
```

3. Enable aggressive GC:
```python
memory_config.gc_threshold_mb = 256
memory_config.gc_interval_seconds = 30
```

### Memory Leaks

1. Use memory profiling:
```bash
alice --debug debug memory profile /path --top 20
```

2. Check for circular references:
```python
import gc
gc.set_debug(gc.DEBUG_LEAK)
```

3. Monitor object counts:
```python
import sys
before = len(gc.get_objects())
# Your code
after = len(gc.get_objects())
print(f"Objects created: {after - before}")
```

### Out of Memory Errors

1. Use memory-constrained profile:
```bash
export ALICE_PERFORMANCE=memory_constrained
```

2. Process in smaller batches:
```python
memory_config.max_batch_size = 50
```

3. Enable streaming for all files:
```python
memory_config.use_mmap = True
memory_config.chunk_size_kb = 256
```

## Demo

Try the interactive demo:

```bash
python examples/memory_optimization_demo.py
```

This demonstrates:
- Streaming vs. regular file reading
- Bounded cache behavior
- Object pooling benefits
- Adaptive batch processing
- Memory-optimized organization