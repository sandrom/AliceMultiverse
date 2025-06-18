"""Tests for metadata caching."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from alicemultiverse.core.cache_migration import MetadataCacheAdapter as MetadataCache
from alicemultiverse.core.types import AnalysisResult


class TestMetadataCache:
    """Test metadata cache functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache(self, temp_dir):
        """Create a metadata cache instance."""
        return UnifiedCache(temp_dir)

    @pytest.fixture
    def sample_file(self, temp_dir):
        """Create a sample file for testing."""
        file_path = temp_dir / "test_image.jpg"
        file_path.write_bytes(b"fake image data")
        return file_path

    def test_content_hash(self, cache, sample_file):
        """Test content hash generation."""
        hash1 = cache.get_content_hash(sample_file)
        hash2 = cache.get_content_hash(sample_file)

        # Hash should be consistent
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_save_and_load(self, cache, sample_file):
        """Test saving and loading metadata."""
        analysis: AnalysisResult = {
            "source_type": "image",
            "date_taken": datetime.now().isoformat(),
            "project_folder": "test",
            "quality_stars": 4,
            "brisque_score": 35.0,
            "pipeline_result": None,
        }

        # Save metadata
        cache.save(sample_file, analysis, 1.23)

        # Load metadata
        metadata = cache.load(sample_file)

        assert metadata is not None
        assert metadata["analysis"]["source_type"] == "image"
        assert metadata["analysis"]["quality_stars"] == 4
        assert metadata["analysis_time"] == 1.23

    def test_cache_invalidation(self, cache, sample_file):
        """Test cache invalidation when file changes."""
        analysis: AnalysisResult = {
            "source_type": "image",
            "date_taken": datetime.now().isoformat(),
            "project_folder": "test",
            "quality_stars": 4,
            "brisque_score": 35.0,
            "pipeline_result": None,
        }

        # Save metadata
        cache.save(sample_file, analysis, 1.0)

        # Modify file
        sample_file.write_bytes(b"modified image data")

        # Cache should be invalidated
        metadata = cache.load(sample_file)
        assert metadata is None

    def test_force_reindex(self, temp_dir, sample_file):
        """Test force reindex bypasses cache."""
        cache = UnifiedCache(temp_dir, force_reindex=True)

        analysis: AnalysisResult = {
            "source_type": "image",
            "date_taken": datetime.now().isoformat(),
            "project_folder": "test",
            "quality_stars": 4,
            "brisque_score": 35.0,
            "pipeline_result": None,
        }

        # Save metadata
        cache.save(sample_file, analysis, 1.0)

        # Load should return None due to force_reindex
        metadata = cache.load(sample_file)
        assert metadata is None

    def test_cache_stats(self, cache, sample_file):
        """Test cache statistics tracking."""
        analysis: AnalysisResult = {
            "source_type": "image",
            "date_taken": datetime.now().isoformat(),
            "project_folder": "test",
            "quality_stars": 4,
            "brisque_score": 35.0,
            "pipeline_result": None,
        }

        # Save metadata
        cache.save(sample_file, analysis, 1.0)

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
