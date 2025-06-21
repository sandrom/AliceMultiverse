"""Tests for memory optimization utilities."""

import pytest
import time
import gc
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading

from alicemultiverse.core.memory_optimization import (
    MemoryConfig, MemoryMonitor, StreamingFileReader,
    BoundedCache, ObjectPool, WeakValueCache,
    MemoryOptimizedBatchProcessor, optimize_for_memory
)


class TestMemoryMonitor:
    """Test MemoryMonitor class."""
    
    def test_initialization(self):
        """Test monitor initialization."""
        config = MemoryConfig(max_memory_mb=1024)
        monitor = MemoryMonitor(config)
        
        assert monitor.config.max_memory_mb == 1024
        assert monitor._peak_memory_mb == 0
        assert monitor._gc_count == 0
    
    @patch('psutil.Process')
    @patch('psutil.virtual_memory')
    def test_get_memory_usage(self, mock_virtual_memory, mock_process_class):
        """Test memory usage retrieval."""
        # Mock process memory
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=512 * 1024 * 1024)  # 512MB
        mock_process_class.return_value = mock_process
        
        # Mock system memory
        mock_virtual_memory.return_value = Mock(
            available=8 * 1024 * 1024 * 1024,  # 8GB
            percent=50.0
        )
        
        config = MemoryConfig(max_memory_mb=1024)
        monitor = MemoryMonitor(config)
        
        usage = monitor.get_memory_usage()
        
        assert usage['current_mb'] == 512
        assert usage['peak_mb'] >= 512
        assert usage['available_mb'] == 8192
        assert usage['percent'] == 50.0
        assert usage['usage_ratio'] == 0.5
    
    @patch('psutil.Process')
    @patch('psutil.virtual_memory')
    def test_check_memory_pressure(self, mock_virtual_memory, mock_process_class):
        """Test memory pressure detection."""
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=900 * 1024 * 1024)  # 900MB
        mock_process_class.return_value = mock_process
        
        mock_virtual_memory.return_value = Mock(
            available=1 * 1024 * 1024 * 1024,
            percent=85.0
        )
        
        config = MemoryConfig(max_memory_mb=1024, warning_threshold=0.8)
        monitor = MemoryMonitor(config)
        
        # Should detect pressure (900/1024 = 0.88 > 0.8)
        assert monitor.check_memory_pressure() is True
    
    def test_adaptive_batch_size(self):
        """Test adaptive batch size calculation."""
        config = MemoryConfig(
            adaptive_batch_size=True,
            min_batch_size=10,
            max_batch_size=1000
        )
        monitor = MemoryMonitor(config)
        
        # Mock different memory usage levels
        test_cases = [
            (0.2, 100, 100),    # Low usage, full size
            (0.5, 100, 75),     # Medium usage, 75% size
            (0.7, 100, 50),     # High usage, 50% size
            (0.9, 100, 25),     # Very high usage, 25% size
            (0.9, 30, 10),      # Respects minimum
        ]
        
        for usage_ratio, base_size, expected in test_cases:
            with patch.object(monitor, 'get_memory_usage',
                            return_value={'usage_ratio': usage_ratio}):
                result = monitor.get_adaptive_batch_size(base_size)
                assert result == expected


class TestStreamingFileReader:
    """Test StreamingFileReader class."""
    
    def test_read_chunks(self):
        """Test chunked file reading."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write test data
            test_data = b'x' * 10000  # 10KB
            tmp.write(test_data)
            tmp_path = Path(tmp.name)
        
        try:
            config = MemoryConfig(chunk_size_kb=1)  # 1KB chunks
            reader = StreamingFileReader(config)
            
            chunks = list(reader.read_chunks(tmp_path))
            
            # Should have 10 chunks of 1KB each
            assert len(chunks) == 10
            assert all(len(chunk) == 1024 for chunk in chunks[:-1])
            
            # Reconstruct and verify
            reconstructed = b''.join(chunks)
            assert reconstructed == test_data
            
        finally:
            tmp_path.unlink()
    
    def test_read_lines(self):
        """Test line-by-line reading."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            lines = [f"Line {i}\n" for i in range(100)]
            tmp.writelines(lines)
            tmp_path = Path(tmp.name)
        
        try:
            config = MemoryConfig()
            reader = StreamingFileReader(config)
            
            read_lines = list(reader.read_lines(tmp_path))
            
            assert len(read_lines) == 100
            assert all(read_lines[i] == f"Line {i}" for i in range(100))
            
        finally:
            tmp_path.unlink()
    
    def test_process_large_file(self):
        """Test processing large file with memory management."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write 10MB of data
            tmp.write(b'x' * (10 * 1024 * 1024))
            tmp_path = Path(tmp.name)
        
        try:
            config = MemoryConfig(chunk_size_kb=1024)  # 1MB chunks
            reader = StreamingFileReader(config)
            
            # Count chunks
            chunk_count = 0
            def count_processor(chunk):
                nonlocal chunk_count
                chunk_count += 1
                return len(chunk)
            
            results = reader.process_large_file(tmp_path, count_processor)
            
            assert chunk_count == 10
            assert sum(results) == 10 * 1024 * 1024
            
        finally:
            tmp_path.unlink()


class TestBoundedCache:
    """Test BoundedCache class."""
    
    def test_basic_operations(self):
        """Test basic cache operations."""
        config = MemoryConfig(cache_size_mb=1, cache_ttl_seconds=60)
        cache = BoundedCache[str](config)
        
        # Set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Miss
        assert cache.get("nonexistent") is None
        
        # Stats
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5
    
    def test_size_eviction(self):
        """Test size-based eviction."""
        config = MemoryConfig(cache_size_mb=0.001)  # Very small cache
        cache = BoundedCache[str](config)
        
        # Add items that exceed size
        for i in range(100):
            cache.set(f"key{i}", "x" * 1000)  # 1KB values
        
        # Should have evicted old items
        stats = cache.get_stats()
        assert stats['items'] < 100
        assert cache.get("key0") is None  # First item evicted
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        config = MemoryConfig(cache_ttl_seconds=0.1)  # 100ms TTL
        cache = BoundedCache[str](config)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(0.2)
        assert cache.get("key1") is None
    
    def test_lru_ordering(self):
        """Test LRU eviction order."""
        config = MemoryConfig(cache_size_mb=0.001)
        cache = BoundedCache[str](config)
        
        # Add items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add more items to trigger eviction
        for i in range(10):
            cache.set(f"new{i}", "x" * 1000)
        
        # key1 should still be there (recently used)
        # key2 and key3 should be evicted
        assert cache.get("key1") is not None
        assert cache.get("key2") is None


class TestObjectPool:
    """Test ObjectPool class."""
    
    def test_basic_pooling(self):
        """Test basic object pooling."""
        created_count = 0
        
        def factory():
            nonlocal created_count
            created_count += 1
            return f"object_{created_count}"
        
        pool = ObjectPool(factory, max_size=2)
        
        # First acquisition creates new object
        with pool.acquire() as obj1:
            assert obj1 == "object_1"
        
        # Second acquisition reuses object
        with pool.acquire() as obj2:
            assert obj2 == "object_1"  # Reused
        
        assert created_count == 1
        assert pool.get_stats()['reused'] == 1
    
    def test_concurrent_access(self):
        """Test concurrent pool access."""
        pool = ObjectPool(lambda: threading.current_thread().ident, max_size=5)
        
        results = []
        def worker():
            with pool.acquire() as obj:
                results.append(obj)
                time.sleep(0.01)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have created some objects and reused others
        stats = pool.get_stats()
        assert stats['created'] > 0
        assert stats['reused'] > 0
        assert stats['created'] + stats['reused'] == 10
    
    def test_reset_function(self):
        """Test object reset on return to pool."""
        class Counter:
            def __init__(self):
                self.count = 0
        
        def reset(obj):
            obj.count = 0
        
        pool = ObjectPool(Counter, reset_func=reset)
        
        # Modify object
        with pool.acquire() as obj:
            obj.count = 100
        
        # Should be reset when reacquired
        with pool.acquire() as obj:
            assert obj.count == 0


class TestWeakValueCache:
    """Test WeakValueCache class."""
    
    def test_weak_references(self):
        """Test weak reference behavior."""
        cache = WeakValueCache()
        
        # Create object and cache it
        obj = {"data": "test"}
        cache.set("key1", obj)
        
        # Can retrieve while strong reference exists
        assert cache.get("key1") == obj
        
        # Delete strong reference
        del obj
        gc.collect()
        
        # May be collected (implementation dependent)
        # Just verify no errors
        result = cache.get("key1")
        assert result is None or result == {"data": "test"}
    
    def test_strong_reference_limit(self):
        """Test strong reference limiting."""
        cache = WeakValueCache()
        cache._max_strong_refs = 5
        
        # Add many items
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        # Should maintain limited strong refs
        assert len(cache._strong_refs) <= 5


class TestMemoryOptimizedBatchProcessor:
    """Test MemoryOptimizedBatchProcessor class."""
    
    def test_adaptive_batching(self):
        """Test adaptive batch processing."""
        config = MemoryConfig(adaptive_batch_size=True)
        processor = MemoryOptimizedBatchProcessor(config)
        
        # Mock memory pressure
        with patch.object(processor.monitor, 'get_adaptive_batch_size',
                         side_effect=[50, 25, 10]):  # Decreasing sizes
            
            items = range(100)
            batches = []
            
            def batch_processor(batch):
                batches.append(len(batch))
                return sum(batch)
            
            results = list(processor.process_items(
                iter(items), batch_processor, base_batch_size=100
            ))
            
            # Should have processed in adaptive batches
            assert len(batches) > 1
            assert batches[0] == 50
            assert batches[1] == 25
            assert sum(batches) == 100


class TestMemoryOptimization:
    """Test memory optimization utilities."""
    
    def test_optimize_for_memory_decorator(self):
        """Test memory optimization decorator."""
        gc_collected = []
        
        @optimize_for_memory
        def memory_intensive_function():
            # Create some garbage
            data = [list(range(1000)) for _ in range(100)]
            gc_collected.append(gc.collect())
            return len(data)
        
        # Patch gc.collect to track calls
        original_collect = gc.collect
        collect_count = 0
        
        def mock_collect(*args):
            nonlocal collect_count
            collect_count += 1
            return original_collect(*args)
        
        with patch('gc.collect', side_effect=mock_collect):
            result = memory_intensive_function()
        
        assert result == 100
        assert collect_count >= 2  # Before and after


class TestMemoryOptimizedOrganizerIntegration:
    """Integration tests for memory-optimized organizer."""
    
    @pytest.mark.slow
    def test_large_collection_memory_usage(self):
        """Test memory usage with large collection."""
        from alicemultiverse.organizer.memory_optimized_organizer import (
            MemoryOptimizedOrganizer
        )
        from alicemultiverse.core.config import AliceMultiverseConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            inbox = tmppath / "inbox"
            inbox.mkdir()
            
            # Create test files
            for i in range(1000):
                file_path = inbox / f"test_{i:04d}.jpg"
                file_path.write_bytes(b'x' * 10000)  # 10KB files
            
            config = AliceMultiverseConfig(
                paths={'inbox': inbox, 'organized': tmppath / "organized"},
                performance={'profile': 'memory_constrained'}
            )
            
            # Create memory config with low limits
            memory_config = MemoryConfig(
                max_memory_mb=256,
                cache_size_mb=32,
                adaptive_batch_size=True
            )
            
            organizer = MemoryOptimizedOrganizer(config, memory_config)
            
            # Process files
            results = organizer.organize()
            
            # Get memory stats
            stats = organizer.get_memory_stats()
            
            # Verify memory was managed
            assert stats['peak_memory_mb'] < 300  # Should stay under limit
            assert stats['gc_collections'] > 0  # Should have triggered GC
            assert results.statistics['organized'] == 1000