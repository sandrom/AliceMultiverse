#!/usr/bin/env python3
"""Fix memory_optimization.py by creating a clean version."""

from pathlib import Path

def create_clean_memory_optimization():
    """Create a clean version of memory_optimization.py."""
    
    # Create the clean content
    content = '''"""Memory optimization utilities for large-scale operations."""

import gc
import logging
import mmap
import os
import psutil
import resource
import sys
import threading
import time
import weakref
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, TypeVar

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
        
        # Check system memory
        if usage['percent'] > 90:
            logger.warning(f"System memory usage critical: {usage['percent']:.1f}%")
            return True
        
        return False
    
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
        
        return False
    
    def get_adaptive_batch_size(self, base_size: int) -> int:
        """Calculate adaptive batch size based on memory pressure."""
        if not self.config.adaptive_batch_size:
            return base_size
        
        usage = self.get_memory_usage()
        
        # Reduce batch size under memory pressure
        if usage['usage_ratio'] > 0.8:
            factor = 0.25
        elif usage['usage_ratio'] > 0.6:
            factor = 0.5
        elif usage['usage_ratio'] > 0.4:
            factor = 0.75
        else:
            factor = 1.0
        
        adjusted_size = int(base_size * factor)
        return max(self.config.min_batch_size, 
                  min(adjusted_size, self.config.max_batch_size))


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
        
        with open(file_path, 'r+b' if mode == 'w' else 'rb') as f:
            try:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
                    if mode == 'r':
                        # Wrap in text mode for reading
                        import io
                        yield io.TextIOWrapper(io.BufferedReader(mmapped))
                    else:
                        yield mmapped
            except Exception as e:
                logger.debug(f"mmap failed for {file_path}, using regular file: {e}")
                f.seek(0)
                yield f
    
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
                yield line.rstrip('\\n')
    
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


class BoundedCache(Generic[T]):
    """Memory-bounded LRU cache with TTL support."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.max_size_bytes = config.cache_size_mb * 1024 * 1024
        self.ttl_seconds = config.cache_ttl_seconds
        
        self._cache: OrderedDict[str, tuple[T, float, int]] = OrderedDict()
        self._current_size = 0
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        if isinstance(value, (str, bytes)):
            return len(value)
        elif isinstance(value, (list, tuple)):
            return sum(self._estimate_size(item) for item in value)
        elif isinstance(value, dict):
            return sum(
                self._estimate_size(k) + self._estimate_size(v) 
                for k, v in value.items()
            )
        else:
            return sys.getsizeof(value)
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            value, timestamp, size = self._cache[key]
            
            # Check TTL
            if self.ttl_seconds > 0:
                if time.time() - timestamp > self.ttl_seconds:
                    del self._cache[key]
                    self._current_size -= size
                    self._misses += 1
                    return None
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._hits += 1
            return value
    
    def set(self, key: str, value: T) -> None:
        """Set value in cache with size limit enforcement."""
        with self._lock:
            # Estimate size
            size = self._estimate_size(value)
            
            # If single item is too large, don't cache
            if size > self.max_size_bytes:
                return
            
            # Remove old entry if exists
            if key in self._cache:
                _, _, old_size = self._cache[key]
                self._current_size -= old_size
            
            # Evict items if needed
            while self._current_size + size > self.max_size_bytes and self._cache:
                evict_key, (_, _, evict_size) = self._cache.popitem(last=False)
                self._current_size -= evict_size
            
            # Add new entry
            self._cache[key] = (value, time.time(), size)
            self._current_size += size
    
    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._current_size = 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'size_mb': self._current_size / 1024 / 1024,
                'items': len(self._cache)
            }


class ObjectPool(Generic[T]):
    """Object pool for reusing expensive objects."""
    
    def __init__(self, 
                 factory: Callable[[], T],
                 reset_func: Optional[Callable[[T], None]] = None,
                 max_size: int = 10):
        self.factory = factory
        self.reset_func = reset_func
        self.max_size = max_size
        self._pool: List[T] = []
        self._lock = threading.Lock()
        self._created = 0
        self._reused = 0
    
    @contextmanager
    def acquire(self) -> Iterator[T]:
        """Acquire object from pool."""
        obj = None
        
        # Try to get from pool
        with self._lock:
            if self._pool:
                obj = self._pool.pop()
                self._reused += 1
            else:
                obj = self.factory()
                self._created += 1
        
        try:
            yield obj
        finally:
            # Return to pool if space available
            with self._lock:
                if len(self._pool) < self.max_size:
                    if self.reset_func:
                        self.reset_func(obj)
                    self._pool.append(obj)
    
    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        return {
            'pool_size': len(self._pool),
            'created': self._created,
            'reused': self._reused,
            'reuse_rate': self._reused / (self._created + self._reused) 
                         if self._created + self._reused > 0 else 0
        }


class WeakValueCache:
    """Cache that allows garbage collection of unused values."""
    
    def __init__(self):
        self._cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self._strong_refs: OrderedDict[str, Any] = OrderedDict()
        self._max_strong_refs = 100
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = self._cache.get(key)
        
        if value is not None:
            # Keep strong reference to recently used items
            self._strong_refs[key] = value
            self._strong_refs.move_to_end(key)
            
            # Limit strong references
            while len(self._strong_refs) > self._max_strong_refs:
                self._strong_refs.popitem(last=False)
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self._cache[key] = value
        self._strong_refs[key] = value
        
        # Limit strong references
        while len(self._strong_refs) > self._max_strong_refs:
            self._strong_refs.popitem(last=False)


class MemoryOptimizedBatchProcessor:
    """Process items in batches with memory optimization."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.monitor = MemoryMonitor(config)
    
    def process_items(self,
                      items: Iterator[T],
                      processor: Callable[[List[T]], Any],
                      base_batch_size: int = 100) -> Iterator[Any]:
        """Process items in memory-optimized batches."""
        batch: List[T] = []
        
        for item in items:
            batch.append(item)
            
            # Get adaptive batch size
            batch_size = self.monitor.get_adaptive_batch_size(base_batch_size)
            
            if len(batch) >= batch_size:
                # Process batch
                yield processor(batch)
                
                # Clear batch and check memory
                batch = []
                self.monitor.maybe_collect_garbage()
        
        # Process remaining items
        if batch:
            yield processor(batch)


@contextmanager
def memory_limit(max_memory_mb: int):
    """Context manager to limit memory usage."""
    # Get current limits
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    
    # Set new limit
    new_limit = max_memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (new_limit, hard))
    
    try:
        yield
    finally:
        # Restore original limits
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))


def optimize_for_memory(func: Callable) -> Callable:
    """Decorator to optimize function for memory usage."""
    def wrapper(*args, **kwargs):
        # Force garbage collection before
        gc.collect()
        
        # Disable GC during execution for performance
        gc_was_enabled = gc.isenabled()
        gc.disable()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Re-enable GC
            if gc_was_enabled:
                gc.enable()
            
            # Force collection after
            gc.collect()
    
    return wrapper
'''
    
    # Write the clean content
    file_path = Path("alicemultiverse/core/memory_optimization.py")
    file_path.write_text(content)
    print(f"Created clean version of {file_path}")

if __name__ == "__main__":
    create_clean_memory_optimization()