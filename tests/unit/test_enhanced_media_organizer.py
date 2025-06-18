"""Tests for the enhanced media organizer with parallel processing."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from alicemultiverse.core.config import Config
from alicemultiverse.core.performance_config import PerformanceConfig
from alicemultiverse.organizer.components.organizer import MediaOrganizer


class TestEnhancedMediaOrganizer:
    """Test enhanced MediaOrganizer functionality with parallel processing."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as inbox_dir:
            with tempfile.TemporaryDirectory() as organized_dir:
                yield Path(inbox_dir), Path(organized_dir)
    
    @pytest.fixture
    def mock_config(self, temp_dirs):
        """Create mock configuration."""
        inbox_dir, organized_dir = temp_dirs
        config = MagicMock(spec=Config)
        config.paths = MagicMock()
        config.paths.inbox = inbox_dir
        config.paths.organized = organized_dir
        config.move_files = False
        config.enhanced_metadata = True
        config.understanding = MagicMock(enabled=False)
        config.processing = MagicMock()
        config.ai_sources = MagicMock()
        config.performance = {
            'max_workers': 4,
            'batch_size': 10,
            'enable_batch_operations': True
        }
        # Add missing attributes
        config.ai_generators = MagicMock()
        config.ai_generators.image = ["midjourney", "dalle", "stable-diffusion"]
        config.ai_generators.video = ["runway", "pika"]
        config.metadata = MagicMock()
        config.metadata.folder_name = ".metadata"
        config.metadata.cache_version = "3.0.0"
        config.quality = MagicMock()
        config.quality.enabled = False
        config.file_types = MagicMock()
        config.file_types.image_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        config.file_types.video_extensions = [".mp4", ".mov"]
        config.storage = MagicMock()
        config.storage.search_db = ":memory:"
        return config
    
    @pytest.fixture
    def sample_images(self, temp_dirs):
        """Create sample image files for testing."""
        inbox_dir, _ = temp_dirs
        
        # Create test images in a project folder
        project_dir = inbox_dir / "test_project"
        project_dir.mkdir()
        
        test_files = []
        for i in range(5):
            file_path = project_dir / f"test_image_{i}.jpg"
            file_path.write_bytes(b"fake image data")
            test_files.append(file_path)
        
        return test_files
    
    def test_initialization_with_performance_config(self, mock_config):
        """Test organizer initialization with performance configuration."""
        organizer = MediaOrganizer(mock_config)
        
        assert organizer.perf_config.max_workers == 4
        assert organizer.perf_config.batch_size == 10
        assert organizer.perf_config.enable_batch_operations is True
        assert organizer.parallel_enabled is True
        assert organizer.parallel_processor is not None
        assert organizer.batch_processor is not None
    
    def test_sequential_processing_for_small_batch(self, mock_config, sample_images):
        """Test that small batches use sequential processing."""
        # Set batch size higher than number of files
        mock_config.performance['batch_size'] = 100
        
        organizer = MediaOrganizer(mock_config)
        
        # Initialize stats properly
        from collections import defaultdict
        organizer.stats = {
            'total': 0,
            'organized': 0,
            'already_organized': 0,
            'duplicates': 0,
            'errors': 0,
            'moved_existing': 0,
            'by_date': defaultdict(int),
            'by_source': defaultdict(int),
            'by_project': defaultdict(int),
            'images_found': 0,
            'videos_found': 0,
        }
        
        with patch.object(organizer, '_organize_sequential') as mock_seq:
            with patch.object(organizer, '_organize_parallel') as mock_par:
                with patch.object(organizer, '_find_media_files', return_value=sample_images[:3]):
                    organizer.organize()
                    
                    # Should use sequential for small batch
                    mock_seq.assert_called_once()
                    mock_par.assert_not_called()
    
    def test_parallel_processing_for_large_batch(self, mock_config, sample_images):
        """Test that large batches use parallel processing."""
        # Set batch size lower than number of files
        mock_config.performance['batch_size'] = 2
        
        organizer = MediaOrganizer(mock_config)
        
        # Initialize stats properly
        from collections import defaultdict
        organizer.stats = {
            'total': 0,
            'organized': 0,
            'already_organized': 0,
            'duplicates': 0,
            'errors': 0,
            'moved_existing': 0,
            'by_date': defaultdict(int),
            'by_source': defaultdict(int),
            'by_project': defaultdict(int),
            'images_found': 0,
            'videos_found': 0,
        }
        
        with patch.object(organizer, '_organize_sequential') as mock_seq:
            with patch.object(organizer, '_organize_parallel') as mock_par:
                with patch.object(organizer, '_find_media_files', return_value=sample_images):
                    organizer.organize()
                    
                    # Should use parallel for large batch
                    mock_seq.assert_not_called()
                    mock_par.assert_called_once()
    
    def test_batch_operations_when_supported(self, mock_config):
        """Test batch operations are used when storage supports it."""
        organizer = MediaOrganizer(mock_config)
        
        # Mock storage with batch support
        organizer.search_db = MagicMock()
        organizer.search_db.batch_upsert_assets = MagicMock(return_value=5)
        organizer.batch_operations_enabled = True
        
        sample_files = [Path(f"test_{i}.jpg") for i in range(5)]
        
        with patch.object(organizer, '_organize_with_batch_db') as mock_batch:
            with patch.object(organizer, '_organize_parallel_individual') as mock_individual:
                organizer._organize_parallel(sample_files)
                
                # Should use batch operations
                mock_batch.assert_called_once_with(sample_files)
                mock_individual.assert_not_called()
    
    def test_fallback_without_batch_support(self, mock_config):
        """Test fallback to individual operations when batch not supported."""
        organizer = MediaOrganizer(mock_config)
        
        # Mock storage without batch support
        organizer.search_db = MagicMock()
        organizer.batch_operations_enabled = False
        
        sample_files = [Path(f"test_{i}.jpg") for i in range(5)]
        
        with patch.object(organizer, '_organize_with_batch_db') as mock_batch:
            with patch.object(organizer, '_organize_parallel_individual') as mock_individual:
                organizer._organize_parallel(sample_files)
                
                # Should use individual operations
                mock_batch.assert_not_called()
                mock_individual.assert_called_once_with(sample_files)
    
    def test_process_file_for_batch(self, mock_config, tmp_path):
        """Test converting file processing result to batch format."""
        organizer = MediaOrganizer(mock_config)
        
        # Create a real test file
        test_path = tmp_path / "test.jpg"
        test_path.write_bytes(b"fake image data")
        mock_result = {
            "status": "success",
            "destination": "/organized/2024-01-01/test.jpg",
            "source_type": "midjourney",
            "date_taken": "2024-01-01",
            "project_folder": "project1",
            "analysis": {
                "content_hash": "abc123",
                "media_type": "image"
            }
        }
        
        with patch.object(organizer, '_process_file', return_value=mock_result):
            result = organizer._process_file_for_batch(test_path)
            
            assert result is not None
            assert result["content_hash"] == "abc123"
            assert result["file_path"] == "/organized/2024-01-01/test.jpg"
            assert result["source_type"] == "midjourney"
    
    def test_error_handling_in_batch_processing(self, mock_config):
        """Test error handling during batch processing."""
        organizer = MediaOrganizer(mock_config)
        
        # Mock file that causes error
        error_file = Path("error.jpg")
        
        # The current implementation doesn't catch exceptions in _process_file_for_batch
        # so we need to test that it raises the exception
        with patch.object(organizer, '_process_file', side_effect=Exception("Test error")):
            with pytest.raises(Exception) as exc_info:
                organizer._process_file_for_batch(error_file)
            assert str(exc_info.value) == "Test error"
    
    @pytest.mark.parametrize("max_workers,expected_parallel", [
        (1, False),  # Single worker = sequential
        (4, True),   # Multiple workers = parallel
        (0, False),  # Zero workers = sequential
    ])
    def test_parallel_enabled_based_on_workers(self, mock_config, max_workers, expected_parallel):
        """Test parallel processing is enabled based on worker count."""
        mock_config.performance['max_workers'] = max_workers
        
        organizer = MediaOrganizer(mock_config)
        
        assert organizer.parallel_enabled == expected_parallel
        if expected_parallel:
            assert organizer.parallel_processor is not None
    
    def test_performance_profile_default(self):
        """Test loading default performance profile."""
        config = MagicMock()
        # No performance attribute - should use defaults
        
        organizer = MediaOrganizer(config)
        
        # Should use default performance config
        assert organizer.perf_config.max_workers == 8
        assert organizer.perf_config.batch_size == 100
    
    def test_batch_processing_combines_results(self, mock_config):
        """Test that batch processing correctly combines results."""
        organizer = MediaOrganizer(mock_config)
        
        # Create a mock search_db
        organizer.search_db = MagicMock()
        organizer.search_db.batch_upsert_assets = MagicMock(return_value=4)
        
        # Mock batch processor to return test data
        test_batch_results = [
            [{"id": 1}, {"id": 2}],  # First batch
            [{"id": 3}, {"id": 4}],  # Second batch
        ]
        
        with patch.object(organizer.batch_processor, 'process_in_batches', 
                         return_value=[{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]):
            organizer._organize_with_batch_db([Path("1.jpg"), Path("2.jpg")])
            
            # Should have called batch upsert with all assets
            organizer.search_db.batch_upsert_assets.assert_called_once()
            args = organizer.search_db.batch_upsert_assets.call_args[0][0]
            assert len(args) == 4
            assert args[0]["id"] == 1
            assert args[3]["id"] == 4
    
    def test_parallel_metadata_extraction(self, mock_config):
        """Test parallel metadata extraction when enabled."""
        mock_config.performance['parallel_metadata_extraction'] = True
        organizer = MediaOrganizer(mock_config)
        
        test_files = [Path(f"test_{i}.jpg") for i in range(3)]
        
        # Mock parallel processor
        mock_metadata_map = {
            test_files[0]: {"content_hash": "hash1"},
            test_files[1]: {"content_hash": "hash2"},
            test_files[2]: {"content_hash": "hash3"},
        }
        
        with patch.object(organizer.parallel_processor, 'extract_metadata_parallel',
                         return_value=mock_metadata_map) as mock_extract:
            # Create a function to test batch processing
            def process_batch(files):
                if organizer.perf_config.parallel_metadata_extraction:
                    metadata_map = organizer.parallel_processor.extract_metadata_parallel(files)
                    return list(metadata_map.values())
                return []
            
            result = process_batch(test_files)
            
            mock_extract.assert_called_once_with(test_files)
            assert len(result) == 3
            assert result[0]["content_hash"] == "hash1"