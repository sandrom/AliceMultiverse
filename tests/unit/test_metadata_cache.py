"""Consolidated unit tests for metadata cache module."""

import json
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from alicemultiverse.core.exceptions import CacheError
from alicemultiverse.core.cache_migration import MetadataCacheAdapter as MetadataCache
from alicemultiverse.core.unified_cache import get_content_hash, get_file_hash
from alicemultiverse.core.types import MediaType


class TestHashFunctions:
    """Test hash generation functions."""

    def test_get_file_hash(self, temp_dir):
        """Test file hash generation."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        # Get hash
        hash1 = get_file_hash(test_file)

        # Verify hash format
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 produces 64 hex characters

        # Verify same content produces same hash
        hash2 = get_file_hash(test_file)
        assert hash1 == hash2

        # Verify different content produces different hash
        test_file.write_text("Different content")
        hash3 = get_file_hash(test_file)
        assert hash3 != hash1

    def test_get_file_hash_nonexistent(self):
        """Test hash generation for non-existent file."""
        with pytest.raises(CacheError):
            get_file_hash(Path("nonexistent.txt"))

    def test_get_content_hash(self, temp_dir):
        """Test content hash generation for images."""
        # Create test image file
        img_file = temp_dir / "test.png"
        img_file.write_bytes(b"fake png data")

        # For now, get_content_hash is same as get_file_hash
        hash1 = get_content_hash(img_file)
        assert isinstance(hash1, str)
        assert len(hash1) == 64


class TestMetadataCache:
    """Test metadata cache functionality."""

    @pytest.fixture
    def cache(self, temp_dir):
        """Create a metadata cache instance."""
        return MetadataCache(temp_dir)

    @pytest.fixture
    def sample_file(self, temp_dir):
        """Create a sample file for testing."""
        file_path = temp_dir / "test_image.jpg"
        file_path.write_bytes(b"fake image data")
        return file_path

    @pytest.fixture
    def sample_analysis(self):
        """Create sample analysis result."""
        return {
            "source_type": "stable-diffusion",
            "date_taken": datetime.now().isoformat(),
            "project_folder": "test",
            "quality_stars": 4,
            "brisque_score": 35.0,
            "media_type": MediaType.IMAGE,
            "file_number": 1,
        }

    def test_init(self, temp_dir):
        """Test cache initialization."""
        cache = MetadataCache(temp_dir)
        assert cache.source_root == temp_dir
        assert cache.force_reindex is False
        assert cache.cache_hits == 0
        assert cache.cache_misses == 0
        assert cache.analysis_time_saved == 0.0

        # Check cache directory created
        cache_dir = temp_dir / ".metadata"
        assert cache_dir.exists()

    def test_init_force_reindex(self, temp_dir):
        """Test cache initialization with force reindex."""
        cache = MetadataCache(temp_dir, force_reindex=True)
        assert cache.force_reindex is True

        # Cache directory should not be created with force_reindex
        cache_dir = temp_dir / ".metadata"
        assert not cache_dir.exists()

    def test_content_hash(self, cache, sample_file):
        """Test content hash generation."""
        hash1 = cache.get_content_hash(sample_file)
        hash2 = cache.get_content_hash(sample_file)

        # Hash should be consistent
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_save_and_load(self, cache, sample_file, sample_analysis):
        """Test saving and loading metadata."""
        # Save metadata
        cache.save(sample_file, sample_analysis, 1.23)

        # Load metadata
        metadata = cache.load(sample_file)

        assert metadata is not None
        assert metadata["analysis"]["source_type"] == "stable-diffusion"
        assert metadata["analysis"]["quality_stars"] == 4
        assert metadata["analysis_time"] == 1.23
        assert "cached_at" in metadata

    def test_save_creates_shard_directory(self, cache, sample_file, sample_analysis):
        """Test that save creates proper shard directory structure."""
        cache.save(sample_file, sample_analysis, 1.0)

        # Check shard directory exists
        content_hash = cache.get_content_hash(sample_file)
        shard_dir = cache._cache_dir / content_hash[:2]
        assert shard_dir.exists()

        # Check cache file exists
        cache_file = shard_dir / f"{content_hash}.json"
        assert cache_file.exists()

    def test_load_nonexistent(self, cache, temp_dir):
        """Test loading metadata for non-cached file."""
        nonexistent = temp_dir / "nonexistent.jpg"
        nonexistent.write_bytes(b"data")

        metadata = cache.load(nonexistent)
        assert metadata is None

    def test_cache_invalidation(self, cache, sample_file, sample_analysis):
        """Test cache invalidation when file changes."""
        # Save metadata
        cache.save(sample_file, sample_analysis, 1.0)

        # Verify it loads
        assert cache.load(sample_file) is not None

        # Modify file
        time.sleep(0.01)  # Ensure mtime changes
        sample_file.write_bytes(b"modified image data")

        # Cache should be invalidated
        metadata = cache.load(sample_file)
        assert metadata is None

    def test_force_reindex(self, temp_dir, sample_file, sample_analysis):
        """Test force reindex bypasses cache."""
        # First save with normal cache
        normal_cache = MetadataCache(temp_dir)
        normal_cache.save(sample_file, sample_analysis, 1.0)
        assert normal_cache.load(sample_file) is not None

        # Create cache with force_reindex
        force_cache = MetadataCache(temp_dir, force_reindex=True)

        # Load should return None due to force_reindex
        metadata = force_cache.load(sample_file)
        assert metadata is None

    def test_cache_version_mismatch(self, cache, sample_file):
        """Test cache invalidation on version mismatch."""
        # Create cache with wrong version
        content_hash = cache.get_content_hash(sample_file)
        cache_path = cache._get_cache_path(content_hash)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_path, "w") as f:
            json.dump({"version": "1.0", "analysis": {}}, f)

        # Should return None due to version mismatch
        metadata = cache.load(sample_file)
        assert metadata is None

    def test_cache_stats(self, cache, sample_file, sample_analysis):
        """Test cache statistics tracking."""
        # Save metadata
        cache.save(sample_file, sample_analysis, 1.0)

        # First load - cache hit
        cache.load(sample_file)
        cache.update_stats(from_cache=True, time_saved=1.0)

        # Second load - simulate cache miss
        cache.update_stats(from_cache=False)

        stats = cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 50.0
        assert stats["time_saved"] == 1.0
        assert stats["total_processed"] == 2

    def test_has_metadata(self, cache, sample_file, sample_analysis):
        """Test checking if metadata exists."""
        # Initially no metadata
        assert cache.has_metadata(sample_file) is False

        # Save metadata
        cache.save(sample_file, sample_analysis, 1.0)

        # Now should exist
        assert cache.has_metadata(sample_file) is True

    def test_metadata_aliases(self, cache, sample_file, sample_analysis):
        """Test get_metadata and set_metadata aliases."""
        # Test set_metadata alias
        cache.set_metadata(sample_file, sample_analysis, 2.0)

        # Test get_metadata alias
        metadata = cache.get_metadata(sample_file)
        assert metadata is not None
        assert metadata["analysis"]["source_type"] == "stable-diffusion"
        assert metadata["analysis_time"] == 2.0

    def test_media_type_enum_handling(self, cache, sample_file):
        """Test proper handling of MediaType enum serialization."""
        analysis = {"source_type": "test", "media_type": MediaType.IMAGE}  # Enum value

        # Save with enum
        cache.save(sample_file, analysis, 1.0)

        # Load and verify enum is restored
        metadata = cache.load(sample_file)
        assert metadata is not None
        assert metadata["analysis"]["media_type"] == MediaType.IMAGE
        assert isinstance(metadata["analysis"]["media_type"], MediaType)

    def test_cache_error_handling(self, cache, sample_file):
        """Test error handling in cache operations."""
        # Test with invalid cache path
        with patch.object(cache, "_get_cache_path") as mock_path:
            mock_path.return_value = Path("/invalid/path/cache.json")

            # Save should not raise, just log error
            cache.save(sample_file, {"test": "data"}, 1.0)

        # Test corrupted cache file
        content_hash = cache.get_content_hash(sample_file)
        cache_path = cache._get_cache_path(content_hash)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("invalid json")

        # Load should return None, not raise
        metadata = cache.load(sample_file)
        assert metadata is None

    def test_quick_hash(self, cache, sample_file):
        """Test quick hash for change detection."""
        hash1 = cache._compute_quick_hash(sample_file)
        assert isinstance(hash1, str)
        assert len(hash1) == 16  # MD5 truncated to 16 chars

        # Same file should produce same hash
        hash2 = cache._compute_quick_hash(sample_file)
        assert hash1 == hash2

        # Modified file should produce different hash
        time.sleep(0.01)
        sample_file.write_bytes(b"modified")
        hash3 = cache._compute_quick_hash(sample_file)
        assert hash3 != hash1

    def test_relative_path_handling(self, cache, temp_dir):
        """Test handling of files outside source root."""
        # Create file outside source root
        outside_file = Path(tempfile.mktemp(suffix=".jpg"))
        outside_file.write_bytes(b"test data")

        try:
            # Should handle gracefully
            cache.save(outside_file, {"test": "data"}, 1.0)
            metadata = cache.load(outside_file)
            assert metadata is not None
            assert metadata["original_path"] == str(outside_file)
        finally:
            outside_file.unlink(missing_ok=True)
