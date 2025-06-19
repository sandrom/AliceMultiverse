"""Memory optimization utilities for large-scale operations."""

import os
import gc
import mmap
import weakref
import psutil
import logging
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, List, Callable, TypeVar, Generic
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import OrderedDict
import threading
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class MemoryConfig:
    """Memory optimization configuration."""
    # Memory limits
    max_memory_mb: int = 1024  # Maximum memory usage
    warning_threshold: float = 0.8  # Warn at 80% of max
    
    # Cache settings
    cache_size_mb: int = 256  # Maximum cache size
    cache_ttl_seconds: int = 300  # Cache time-to-live
    
    # Streaming settings
    chunk_size_kb: int = 1024  # File reading chunk size
    use_mmap: bool = True  # Use memory-mapped files
    
    # Garbage collection
    gc_threshold_mb: int = 512  # Trigger GC above this
    gc_interval_seconds: int = 60  # Periodic GC interval
    
    # Batch processing
    adaptive_batch_size: bool = True  # Adjust batch size based on memory
    min_batch_size: int = 10
    max_batch_size: int = 1000


class MemoryMonitor:
    """Monitor and control memory usage."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.process = psutil.Process()
        self._last_gc_time = time.time()
        self._peak_memory_mb = 0
        self._gc_count = 0
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        mem_info = self.process.memory_info()
        virtual_mem = psutil.virtual_memory()
        
        current_mb = mem_info.rss / 1024 / 1024
        self._peak_memory_mb = max(self._peak_memory_mb, current_mb)
        
        return {
            'current_mb': current_mb,
            'peak_mb': self._peak_memory_mb,
            'available_mb': virtual_mem.available / 1024 / 1024,
            'percent': virtual_mem.percent,
            'limit_mb': self.config.max_memory_mb,
            'usage_ratio': current_mb / self.config.max_memory_mb
        }
    
    def check_memory_pressure(self) -> bool:
        """Check if system is under memory pressure."""
        usage = self.get_memory_usage()
        
        # Check against configured limit
        if usage['usage_ratio'] > self.config.warning_threshold:
            logger.warning(
                f"Memory usage high: {usage['current_mb']:.1f}MB "
                f"({usage['usage_ratio']:.1%} of limit)"
            )
            return True
        
        # TODO: Review unreachable code - # Check system memory
        # TODO: Review unreachable code - if usage['percent'] > 90:
        # TODO: Review unreachable code - logger.warning(f"System memory usage critical: {usage['percent']:.1f}%")
        # TODO: Review unreachable code - return True
        
        # TODO: Review unreachable code - return False
    
    def maybe_collect_garbage(self, force: bool = False) -> bool:
        """Conditionally trigger garbage collection."""
        current_time = time.time()
        usage = self.get_memory_usage()
        
        should_collect = (
            force or
            usage['current_mb'] > self.config.gc_threshold_mb or
            current_time - self._last_gc_time > self.config.gc_interval_seconds
        )
        
        if should_collect:
            logger.debug(f"Triggering GC (memory: {usage['current_mb']:.1f}MB)")
            gc.collect()
            self._gc_count += 1
            self._last_gc_time = current_time
            return True
        
        # TODO: Review unreachable code - return False
    
    def get_adaptive_batch_size(self, base_size: int) -> int:
        """Calculate adaptive batch size based on memory pressure."""
        if not self.config.adaptive_batch_size:
            return base_size
        
        # TODO: Review unreachable code - usage = self.get_memory_usage()
        
        # TODO: Review unreachable code - # Reduce batch size under memory pressure
        # TODO: Review unreachable code - if usage['usage_ratio'] > 0.8:
        # TODO: Review unreachable code - factor = 0.25
        # TODO: Review unreachable code - elif usage['usage_ratio'] > 0.6:
        # TODO: Review unreachable code - factor = 0.5
        # TODO: Review unreachable code - elif usage['usage_ratio'] > 0.4:
        # TODO: Review unreachable code - factor = 0.75
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - factor = 1.0
        
        # TODO: Review unreachable code - adjusted_size = int(base_size * factor)
        # TODO: Review unreachable code - return max(self.config.min_batch_size,
        # TODO: Review unreachable code - min(adjusted_size, self.config.max_batch_size))


class StreamingFileReader:
    """Memory-efficient file reading with streaming and memory mapping."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.chunk_size = config.chunk_size_kb * 1024
    
    @contextmanager
    def open_mmap(self, file_path: Path, mode: str = 'r'):
        """Open file with memory mapping."""
        if not self.config.use_mmap or file_path.stat().st_size == 0:
            # Fall back to regular file for empty or when mmap disabled
            with open(file_path, mode) as f:
                yield f
            return
        
        # TODO: Review unreachable code - with open(file_path, 'r+b' if mode == 'w' else 'rb') as f:
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
        # TODO: Review unreachable code - if mode == 'r':
        # TODO: Review unreachable code - # Wrap in text mode for reading
        # TODO: Review unreachable code - import io
        # TODO: Review unreachable code - yield io.TextIOWrapper(io.BufferedReader(mmapped))
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - yield mmapped
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.debug(f"mmap failed for {file_path}, using regular file: {e}")
        # TODO: Review unreachable code - f.seek(0)
        # TODO: Review unreachable code - yield f
    
    def read_chunks(self, file_path: Path) -> Iterator[bytes]:
        """Read file in memory-efficient chunks."""
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk
    
    def read_lines(self, file_path: Path, encoding: str = 'utf-8') -> Iterator[str]:
        """Read file line by line with minimal memory usage."""
        with self.open_mmap(file_path, 'r') as f:
            for line in f:
                yield line.rstrip('\n')
    
    def process_large_file(self, file_path: Path, 
                          processor: Callable[[bytes], Any]) -> List[Any]:
        """Process large file in chunks with memory management."""
        results = []
        monitor = MemoryMonitor(self.config)
        
        for i, chunk in enumerate(self.read_chunks(file_path)):
            # Check memory pressure
            if monitor.check_memory_pressure():
                monitor.maybe_collect_garbage(force=True)
            
            # Process chunk
            result = processor(chunk)
            if result is not None:
                results.append(result)
            
            # Periodic garbage collection
            if i % 100 == 0:
                monitor.maybe_collect_garbage()
        
        return results


# TODO: Review unreachable code - class BoundedCache(Generic[T]):
# TODO: Review unreachable code - """Memory-bounded LRU cache with TTL support."""
    
# TODO: Review unreachable code - def __init__(self, config: MemoryConfig):
# TODO: Review unreachable code - self.config = config
# TODO: Review unreachable code - self.max_size_bytes = config.cache_size_mb * 1024 * 1024
# TODO: Review unreachable code - self.ttl_seconds = config.cache_ttl_seconds
        
# TODO: Review unreachable code - self._cache: OrderedDict[str, tuple[T, float, int]] = OrderedDict()
# TODO: Review unreachable code - self._current_size = 0
# TODO: Review unreachable code - self._lock = threading.RLock()
# TODO: Review unreachable code - self._hits = 0
# TODO: Review unreachable code - self._misses = 0
    
# TODO: Review unreachable code - def _estimate_size(self, value: Any) -> int:
# TODO: Review unreachable code - """Estimate memory size of value."""
# TODO: Review unreachable code - import sys
        
# TODO: Review unreachable code - if isinstance(value, (str, bytes)):
# TODO: Review unreachable code - return int(len(value))
# TODO: Review unreachable code - elif isinstance(value, (list, tuple)):
# TODO: Review unreachable code - return sum(self._estimate_size(item) for item in value)
# TODO: Review unreachable code - elif isinstance(value, dict):
# TODO: Review unreachable code - return sum(
# TODO: Review unreachable code - self._estimate_size(k) + self._estimate_size(v) 
# TODO: Review unreachable code - for k, v in value.items()
# TODO: Review unreachable code - )
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - return sys.getsizeof(value)
    
# TODO: Review unreachable code - def get(self, key: str) -> Optional[T]:
# TODO: Review unreachable code - """Get value from cache."""
# TODO: Review unreachable code - with self._lock:
# TODO: Review unreachable code - if key not in self._cache:
# TODO: Review unreachable code - self._misses += 1
# TODO: Review unreachable code - return None
            
# TODO: Review unreachable code - value, timestamp, size = self._cache[key]
            
# TODO: Review unreachable code - # Check TTL
# TODO: Review unreachable code - if self.ttl_seconds > 0:
# TODO: Review unreachable code - if time.time() - timestamp > self.ttl_seconds:
# TODO: Review unreachable code - del self._cache[key]
# TODO: Review unreachable code - self._current_size -= size
# TODO: Review unreachable code - self._misses += 1
# TODO: Review unreachable code - return None
            
# TODO: Review unreachable code - # Move to end (LRU)
# TODO: Review unreachable code - self._cache.move_to_end(key)
# TODO: Review unreachable code - self._hits += 1
# TODO: Review unreachable code - return value
    
# TODO: Review unreachable code - def set(self, key: str, value: T) -> None:
# TODO: Review unreachable code - """Set value in cache with size limit enforcement."""
# TODO: Review unreachable code - with self._lock:
# TODO: Review unreachable code - # Estimate size
# TODO: Review unreachable code - size = self._estimate_size(value)
            
# TODO: Review unreachable code - # If single item is too large, don't cache
# TODO: Review unreachable code - if size > self.max_size_bytes:
# TODO: Review unreachable code - return
            
# TODO: Review unreachable code - # Remove old entry if exists
# TODO: Review unreachable code - if key in self._cache:
# TODO: Review unreachable code - _, _, old_size = self._cache[key]
# TODO: Review unreachable code - self._current_size -= old_size
            
# TODO: Review unreachable code - # Evict items if needed
# TODO: Review unreachable code - while self._current_size + size > self.max_size_bytes and self._cache:
# TODO: Review unreachable code - evict_key, (_, _, evict_size) = self._cache.popitem(last=False)
# TODO: Review unreachable code - self._current_size -= evict_size
            
# TODO: Review unreachable code - # Add new entry
# TODO: Review unreachable code - self._cache[key] = (value, time.time(), size)
# TODO: Review unreachable code - self._current_size += size
    
# TODO: Review unreachable code - def clear(self) -> None:
# TODO: Review unreachable code - """Clear the cache."""
# TODO: Review unreachable code - with self._lock:
# TODO: Review unreachable code - self._cache.clear()
# TODO: Review unreachable code - self._current_size = 0
    
# TODO: Review unreachable code - def get_stats(self) -> dict:
# TODO: Review unreachable code - """Get cache statistics."""
# TODO: Review unreachable code - with self._lock:
# TODO: Review unreachable code - total_requests = self._hits + self._misses
# TODO: Review unreachable code - hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
# TODO: Review unreachable code - return {
# TODO: Review unreachable code - 'hits': self._hits,
# TODO: Review unreachable code - 'misses': self._misses,
# TODO: Review unreachable code - 'hit_rate': hit_rate,
# TODO: Review unreachable code - 'size_mb': self._current_size / 1024 / 1024,
# TODO: Review unreachable code - 'items': len(self._cache)
# TODO: Review unreachable code - }


# TODO: Review unreachable code - class ObjectPool(Generic[T]):
# TODO: Review unreachable code - """Object pool for reusing expensive objects."""
    
# TODO: Review unreachable code - def __init__(self, 
# TODO: Review unreachable code - factory: Callable[[], T],
# TODO: Review unreachable code - reset_func: Optional[Callable[[T], None]] = None,
# TODO: Review unreachable code - max_size: int = 10):
# TODO: Review unreachable code - self.factory = factory
# TODO: Review unreachable code - self.reset_func = reset_func
# TODO: Review unreachable code - self.max_size = max_size
# TODO: Review unreachable code - self._pool: List[T] = []
# TODO: Review unreachable code - self._lock = threading.Lock()
# TODO: Review unreachable code - self._created = 0
# TODO: Review unreachable code - self._reused = 0
    
# TODO: Review unreachable code - @contextmanager
# TODO: Review unreachable code - def acquire(self) -> Iterator[T]:
# TODO: Review unreachable code - """Acquire object from pool."""
# TODO: Review unreachable code - obj = None
        
# TODO: Review unreachable code - # Try to get from pool
# TODO: Review unreachable code - with self._lock:
# TODO: Review unreachable code - if self._pool:
# TODO: Review unreachable code - obj = self._pool.pop()
# TODO: Review unreachable code - self._reused += 1
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - obj = self.factory()
# TODO: Review unreachable code - self._created += 1
        
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - yield obj
# TODO: Review unreachable code - finally:
# TODO: Review unreachable code - # Return to pool if space available
# TODO: Review unreachable code - with self._lock:
# TODO: Review unreachable code - if len(self._pool) < self.max_size:
# TODO: Review unreachable code - if self.reset_func:
# TODO: Review unreachable code - self.reset_func(obj)
# TODO: Review unreachable code - self._pool.append(obj)
    
# TODO: Review unreachable code - def get_stats(self) -> Dict[str, int]:
# TODO: Review unreachable code - """Get pool statistics."""
# TODO: Review unreachable code - return {
# TODO: Review unreachable code - 'pool_size': len(self._pool),
# TODO: Review unreachable code - 'created': self._created,
# TODO: Review unreachable code - 'reused': self._reused,
# TODO: Review unreachable code - 'reuse_rate': self._reused / (self._created + self._reused) 
# TODO: Review unreachable code - if self._created + self._reused > 0 else 0
# TODO: Review unreachable code - }


# TODO: Review unreachable code - class WeakValueCache:
# TODO: Review unreachable code - """Cache that allows garbage collection of unused values."""
    
# TODO: Review unreachable code - def __init__(self):
# TODO: Review unreachable code - self._cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
# TODO: Review unreachable code - self._strong_refs: OrderedDict[str, Any] = OrderedDict()
# TODO: Review unreachable code - self._max_strong_refs = 100
    
# TODO: Review unreachable code - def get(self, key: str) -> Optional[Any]:
# TODO: Review unreachable code - """Get value from cache."""
# TODO: Review unreachable code - value = self._cache.get(key)
        
# TODO: Review unreachable code - if value is not None:
# TODO: Review unreachable code - # Keep strong reference to recently used items
# TODO: Review unreachable code - self._strong_refs[key] = value
# TODO: Review unreachable code - self._strong_refs.move_to_end(key)
            
# TODO: Review unreachable code - # Limit strong references
# TODO: Review unreachable code - while len(self._strong_refs) > self._max_strong_refs:
# TODO: Review unreachable code - self._strong_refs.popitem(last=False)
        
# TODO: Review unreachable code - return value
    
# TODO: Review unreachable code - def set(self, key: str, value: Any) -> None:
# TODO: Review unreachable code - """Set value in cache."""
# TODO: Review unreachable code - self._cache[key] = value
# TODO: Review unreachable code - self._strong_refs[key] = value
        
# TODO: Review unreachable code - # Limit strong references
# TODO: Review unreachable code - while len(self._strong_refs) > self._max_strong_refs:
# TODO: Review unreachable code - self._strong_refs.popitem(last=False)


# TODO: Review unreachable code - class MemoryOptimizedBatchProcessor:
# TODO: Review unreachable code - """Process items in batches with memory optimization."""
    
# TODO: Review unreachable code - def __init__(self, config: MemoryConfig):
# TODO: Review unreachable code - self.config = config
# TODO: Review unreachable code - self.monitor = MemoryMonitor(config)
    
# TODO: Review unreachable code - def process_items(self,
# TODO: Review unreachable code - items: Iterator[T],
# TODO: Review unreachable code - processor: Callable[[List[T]], Any],
# TODO: Review unreachable code - base_batch_size: int = 100) -> Iterator[Any]:
# TODO: Review unreachable code - """Process items in memory-optimized batches."""
# TODO: Review unreachable code - batch: List[T] = []
        
# TODO: Review unreachable code - for item in items:
# TODO: Review unreachable code - batch.append(item)
            
# TODO: Review unreachable code - # Get adaptive batch size
# TODO: Review unreachable code - batch_size = self.monitor.get_adaptive_batch_size(base_batch_size)
            
# TODO: Review unreachable code - if len(batch) >= batch_size:
# TODO: Review unreachable code - # Process batch
# TODO: Review unreachable code - yield processor(batch)
                
# TODO: Review unreachable code - # Clear batch and check memory
# TODO: Review unreachable code - batch = []
# TODO: Review unreachable code - self.monitor.maybe_collect_garbage()
        
# TODO: Review unreachable code - # Process remaining items
# TODO: Review unreachable code - if batch:
# TODO: Review unreachable code - yield processor(batch)


# TODO: Review unreachable code - @contextmanager
# TODO: Review unreachable code - def memory_limit(max_memory_mb: int):
# TODO: Review unreachable code - """Context manager to limit memory usage."""
# TODO: Review unreachable code - import resource
    
# TODO: Review unreachable code - # Get current limits
# TODO: Review unreachable code - soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    
# TODO: Review unreachable code - # Set new limit
# TODO: Review unreachable code - new_limit = max_memory_mb * 1024 * 1024
# TODO: Review unreachable code - resource.setrlimit(resource.RLIMIT_AS, (new_limit, hard))
    
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - yield
# TODO: Review unreachable code - finally:
# TODO: Review unreachable code - # Restore original limits
# TODO: Review unreachable code - resource.setrlimit(resource.RLIMIT_AS, (soft, hard))


# TODO: Review unreachable code - def optimize_for_memory(func: Callable) -> Callable:
# TODO: Review unreachable code - """Decorator to optimize function for memory usage."""
# TODO: Review unreachable code - def wrapper(*args, **kwargs):
# TODO: Review unreachable code - # Force garbage collection before
# TODO: Review unreachable code - gc.collect()
        
# TODO: Review unreachable code - # Disable GC during execution for performance
# TODO: Review unreachable code - gc_was_enabled = gc.isenabled()
# TODO: Review unreachable code - gc.disable()
        
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - result = func(*args, **kwargs)
# TODO: Review unreachable code - return result
# TODO: Review unreachable code - finally:
# TODO: Review unreachable code - # Re-enable GC
# TODO: Review unreachable code - if gc_was_enabled:
# TODO: Review unreachable code - gc.enable()
            
# TODO: Review unreachable code - # Force collection after
# TODO: Review unreachable code - gc.collect()
    
# TODO: Review unreachable code - return wrapper
