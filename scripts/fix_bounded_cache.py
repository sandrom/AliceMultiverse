#!/usr/bin/env python3
"""Fix the BoundedCache class in memory_optimization.py."""

from pathlib import Path

# Correct implementation of BoundedCache
BOUNDED_CACHE_CODE = '''class BoundedCache(Generic[T]):
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
        import sys
        
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
            }'''

def main():
    """Fix the memory_optimization.py file."""
    file_path = Path("alicemultiverse/core/memory_optimization.py")
    
    # Read the file
    content = file_path.read_text()
    
    # Find where BoundedCache starts
    start_idx = content.find('class BoundedCache')
    if start_idx == -1:
        print("BoundedCache class not found!")
        return
        
    # Find the next class or end of file
    next_class_idx = content.find('\nclass ', start_idx + 1)
    if next_class_idx == -1:
        next_class_idx = len(content)
    
    # Replace the BoundedCache implementation
    before = content[:start_idx]
    after = content[next_class_idx:]
    
    # Reconstruct the file
    new_content = before + BOUNDED_CACHE_CODE + '\n\n' + after
    
    # Write back
    file_path.write_text(new_content)
    print(f"Fixed BoundedCache in {file_path}")

if __name__ == "__main__":
    main()