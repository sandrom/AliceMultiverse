"""Tests for parallel processing functionality."""

import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from alicemultiverse.organizer.parallel_processor import (
    ParallelBatchProcessor,
    ParallelProcessor,
)


class TestParallelProcessor:
    """Test ParallelProcessor functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create parallel processor with 2 workers."""
        return ParallelProcessor(max_workers=2)
    
    @pytest.fixture
    def sample_files(self):
        """Create sample file paths."""
        return [Path(f"/test/file{i}.jpg") for i in range(10)]
    
    def test_initialization(self):
        """Test processor initialization."""
        processor = ParallelProcessor(max_workers=4)
        assert processor.max_workers == 4
        assert processor.executor is not None
        assert isinstance(processor.executor, ThreadPoolExecutor)
    
    def test_process_files_parallel(self, processor, sample_files):
        """Test parallel file processing."""
        # Mock processing function
        def mock_process(file_path):
            # Simulate some work
            time.sleep(0.01)
            return {"path": str(file_path), "status": "success"}
        
        results = processor.process_files_parallel(
            sample_files[:5], 
            mock_process,
            batch_size=2
        )
        
        assert len(results) == 5
        # Results should be (path, result) tuples
        for path, result in results:
            assert isinstance(path, Path)
            assert result["status"] == "success"
            assert result["path"] == str(path)
    
    def test_process_files_with_errors(self, processor, sample_files):
        """Test handling of processing errors."""
        def mock_process_with_errors(file_path):
            if "file3" in str(file_path):
                raise ValueError("Test error")
            return {"status": "success"}
        
        results = processor.process_files_parallel(
            sample_files[:5],
            mock_process_with_errors,
            batch_size=3
        )
        
        # Should still get 5 results
        assert len(results) == 5
        
        # Check that error was captured
        success_count = sum(1 for _, r in results if r and r.get("status") == "success")
        error_count = sum(1 for _, r in results if r is None)
        
        assert success_count == 4
        assert error_count == 1
    
    def test_extract_metadata_parallel(self, processor):
        """Test parallel metadata extraction."""
        test_files = [Path(f"/test/image{i}.jpg") for i in range(3)]
        
        # Mock the _extract_file_metadata method
        def mock_extract(file_path):
            return {
                "content_hash": f"hash_{file_path.name}",
                "size": 1000,
                "type": "image/jpeg"
            }
        
        with patch.object(processor, '_extract_file_metadata', side_effect=mock_extract):
            metadata_map = processor.extract_metadata_parallel(test_files)
        
        assert len(metadata_map) == 3
        for file_path, metadata in metadata_map.items():
            assert metadata["content_hash"] == f"hash_{file_path.name}"
            assert metadata["size"] == 1000
    
    def test_extract_file_metadata(self, processor, tmp_path):
        """Test single file metadata extraction."""
        # Create a test file
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")
        
        metadata = processor._extract_file_metadata(test_file)
        
        assert "content_hash" in metadata
        assert metadata["size"] == 15  # Length of "fake image data"
        assert metadata["exists"] is True
        assert "modified" in metadata
    
    def test_extract_metadata_nonexistent_file(self, processor):
        """Test metadata extraction for non-existent file."""
        fake_path = Path("/nonexistent/file.jpg")
        
        metadata = processor._extract_file_metadata(fake_path)
        
        assert metadata["exists"] is False
        assert metadata["error"] is not None
    
    def test_shutdown(self, processor):
        """Test proper shutdown of thread pool."""
        # Process something to ensure executor is used
        processor.process_files_parallel(
            [Path("/test.jpg")],
            lambda x: {"status": "ok"}
        )
        
        # Shutdown
        processor.shutdown()
        
        # Executor should be shut down
        assert processor.executor._shutdown is True
    
    def test_context_manager(self):
        """Test using processor as context manager."""
        with ParallelProcessor(max_workers=2) as processor:
            results = processor.process_files_parallel(
                [Path("/test1.jpg"), Path("/test2.jpg")],
                lambda x: {"processed": True}
            )
            assert len(results) == 2
        
        # Executor should be shut down after exiting context
        assert processor.executor._shutdown is True
    
    @pytest.mark.parametrize("batch_size,expected_batches", [
        (1, 5),  # 5 files, batch size 1 = 5 batches
        (2, 3),  # 5 files, batch size 2 = 3 batches (2,2,1)
        (5, 1),  # 5 files, batch size 5 = 1 batch
        (10, 1), # 5 files, batch size 10 = 1 batch
    ])
    def test_different_batch_sizes(self, processor, sample_files, batch_size, expected_batches):
        """Test processing with different batch sizes."""
        processed_batches = 0
        
        def mock_process(file_path):
            nonlocal processed_batches
            processed_batches += 1
            return {"status": "ok"}
        
        # Mock executor to count batch submissions
        batch_count = 0
        original_submit = processor.executor.submit
        
        def counting_submit(*args, **kwargs):
            nonlocal batch_count
            batch_count += 1
            return original_submit(*args, **kwargs)
        
        processor.executor.submit = counting_submit
        
        results = processor.process_files_parallel(
            sample_files[:5],
            mock_process,
            batch_size=batch_size
        )
        
        assert len(results) == 5
        # Each batch creates one future
        assert batch_count >= expected_batches


class TestParallelBatchProcessor:
    """Test ParallelBatchProcessor functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create batch processor."""
        return ParallelBatchProcessor(batch_size=3, max_workers=2)
    
    def test_initialization(self):
        """Test batch processor initialization."""
        processor = ParallelBatchProcessor(batch_size=10, max_workers=4)
        assert processor.batch_size == 10
        assert processor.parallel_processor.max_workers == 4
    
    def test_process_in_batches(self, processor):
        """Test batch processing."""
        items = list(range(10))
        
        def process_batch(batch):
            # Sum the batch
            return sum(batch)
        
        def combine_results(batch_results):
            # Sum all batch sums
            return sum(batch_results)
        
        result = processor.process_in_batches(
            items,
            process_batch,
            combine_results
        )
        
        # Should sum all numbers 0-9
        assert result == sum(range(10))
    
    def test_process_in_batches_no_combine(self, processor):
        """Test batch processing without combine function."""
        items = ["a", "b", "c", "d", "e"]
        
        def process_batch(batch):
            return [item.upper() for item in batch]
        
        results = processor.process_in_batches(items, process_batch)
        
        # Should return list of batch results
        assert len(results) == 2  # 2 batches with batch_size=3
        # First batch: ["A", "B", "C"]
        assert results[0] == ["A", "B", "C"]
        # Second batch: ["D", "E"]
        assert results[1] == ["D", "E"]
    
    def test_create_batches(self, processor):
        """Test batch creation."""
        items = list(range(10))
        batches = list(processor._create_batches(items, batch_size=3))
        
        assert len(batches) == 4  # 3,3,3,1
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]
    
    def test_empty_input(self, processor):
        """Test processing empty input."""
        result = processor.process_in_batches(
            [],
            lambda batch: len(batch),
            lambda results: sum(results)
        )
        
        assert result == 0
    
    def test_batch_processing_with_errors(self, processor):
        """Test error handling in batch processing."""
        items = list(range(10))
        
        def process_with_error(batch):
            if 5 in batch:
                raise ValueError("Error processing batch with 5")
            return len(batch)
        
        # Process without combine function to see individual results
        results = processor.process_in_batches(items, process_with_error)
        
        # Should have 4 results (batches)
        assert len(results) == 4
        # One batch should be None due to error
        assert None in results
        # Other batches should have valid lengths
        valid_results = [r for r in results if r is not None]
        assert len(valid_results) == 3
    
    def test_shutdown(self, processor):
        """Test shutdown of batch processor."""
        # Use the processor
        processor.process_in_batches(
            [1, 2, 3],
            lambda x: x
        )
        
        # Shutdown
        processor.shutdown()
        
        # Check that parallel processor was shut down
        assert processor.parallel_processor.executor._shutdown is True
    
    def test_large_dataset_performance(self, processor):
        """Test performance with larger dataset."""
        # Create 1000 items
        items = list(range(1000))
        
        def process_batch(batch):
            # Simulate some work
            time.sleep(0.001)
            return len(batch)
        
        start_time = time.time()
        result = processor.process_in_batches(
            items,
            process_batch,
            lambda results: sum(results)
        )
        elapsed = time.time() - start_time
        
        assert result == 1000
        # With parallel processing, should be faster than sequential
        # Sequential would take ~0.334s (1000/3 * 0.001)
        # Parallel with 2 workers should be significantly faster
        assert elapsed < 0.2  # Allow some overhead
    
    def test_custom_batch_size_per_call(self, processor):
        """Test that batch size can be customized per call."""
        items = list(range(20))
        
        # Override default batch_size
        processor.batch_size = 5
        
        batches_processed = []
        
        def track_batches(batch):
            batches_processed.append(len(batch))
            return len(batch)
        
        processor.process_in_batches(items, track_batches)
        
        # Should have 4 batches of size 5
        assert len(batches_processed) == 4
        assert all(size == 5 for size in batches_processed)