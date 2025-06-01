"""Tests for DuckDB search cache."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from alicemultiverse.storage import DuckDBSearchCache


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database file."""
    db_path = tmp_path / "test.db"
    yield db_path
    # Cleanup happens automatically with tmp_path


@pytest.fixture
def cache(temp_db):
    """Create a DuckDB cache instance."""
    return DuckDBSearchCache(temp_db)


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "media_type": "image",
        "metadata_version": "1.0",
        "tags": {
            "style": ["cyberpunk", "neon"],
            "mood": ["dramatic", "mysterious"],
            "subject": ["woman", "portrait"],
            "color": ["blue", "purple"],
            "custom_category": ["custom_value"]
        },
        "understanding": {
            "description": "A cyberpunk portrait of a woman",
            "generated_prompt": "cyberpunk woman portrait, neon lights",
            "negative_prompt": "blurry, low quality",
            "provider": "openai",
            "model": "gpt-4-vision",
            "cost": 0.002,
            "analyzed_at": datetime.now().isoformat(),
            "model_outputs": {
                "openai": {"description": "..."},
                "anthropic": {"description": "..."}
            }
        },
        "generation": {
            "provider": "midjourney",
            "model": "v6",
            "prompt": "original prompt",
            "parameters": {"steps": 50},
            "cost": 0.05,
            "generated_at": datetime.now().isoformat()
        }
    }


class TestDuckDBSearchCache:
    """Test DuckDB search cache functionality."""
    
    def test_initialization(self, cache):
        """Test cache initialization and schema creation."""
        # Check tables exist
        tables = cache.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        
        table_names = [t[0] for t in tables]
        assert "assets" in table_names
        assert "asset_tags" in table_names
        assert "asset_understanding" in table_names
        assert "asset_generation" in table_names
    
    def test_upsert_new_asset(self, cache, sample_metadata):
        """Test inserting a new asset."""
        content_hash = "abc123"
        file_path = Path("/test/image.jpg")
        
        cache.upsert_asset(content_hash, file_path, sample_metadata)
        
        # Verify asset was created
        result = cache.get_asset_by_hash(content_hash)
        assert result is not None
        assert result["content_hash"] == content_hash
        assert result["media_type"] == "image"
        assert len(result["locations"]) == 1
        assert result["locations"][0]["path"] == str(file_path)
    
    def test_upsert_existing_asset_new_location(self, cache, sample_metadata):
        """Test adding a new location to existing asset."""
        content_hash = "abc123"
        file_path1 = Path("/test/image1.jpg")
        file_path2 = Path("/backup/image1.jpg")
        
        # Insert initial asset
        cache.upsert_asset(content_hash, file_path1, sample_metadata)
        
        # Add new location
        cache.upsert_asset(content_hash, file_path2, sample_metadata, "network")
        
        # Verify both locations exist
        result = cache.get_asset_by_hash(content_hash)
        assert len(result["locations"]) == 2
        
        paths = [loc["path"] for loc in result["locations"]]
        assert str(file_path1) in paths
        assert str(file_path2) in paths
        
        # Check storage types
        storage_types = {loc["path"]: loc["storage_type"] for loc in result["locations"]}
        assert storage_types[str(file_path1)] == "local"
        assert storage_types[str(file_path2)] == "network"
    
    def test_search_by_tags(self, cache, sample_metadata):
        """Test searching assets by tags."""
        # Insert test assets
        cache.upsert_asset("hash1", Path("/test1.jpg"), sample_metadata)
        
        # Modify metadata for second asset
        metadata2 = sample_metadata.copy()
        metadata2["tags"]["style"] = ["anime", "colorful"]
        cache.upsert_asset("hash2", Path("/test2.jpg"), metadata2)
        
        # Search for cyberpunk style
        results = cache.search_by_tags({"style": ["cyberpunk"]})
        assert len(results) == 1
        assert results[0]["content_hash"] == "hash1"
        
        # Search for multiple styles (OR operation)
        results = cache.search_by_tags({"style": ["cyberpunk", "anime"]})
        assert len(results) == 2
        
        # Search for mood
        results = cache.search_by_tags({"mood": ["dramatic"]})
        assert len(results) == 2  # Both have dramatic mood
    
    def test_search_by_text(self, cache, sample_metadata):
        """Test text search in descriptions and prompts."""
        cache.upsert_asset("hash1", Path("/test1.jpg"), sample_metadata)
        
        # Search for "cyberpunk"
        results = cache.search_by_text("cyberpunk")
        assert len(results) == 1
        assert results[0]["content_hash"] == "hash1"
        
        # Search for "woman"
        results = cache.search_by_text("woman")
        assert len(results) == 1
        
        # Search for non-existent text
        results = cache.search_by_text("landscape")
        assert len(results) == 0
    
    def test_get_all_locations(self, cache, sample_metadata):
        """Test getting all locations for an asset."""
        content_hash = "abc123"
        locations = [
            (Path("/local/image.jpg"), "local"),
            (Path("/backup/image.jpg"), "network"),
            (Path("s3://bucket/image.jpg"), "s3")
        ]
        
        # Add asset with first location
        cache.upsert_asset(content_hash, locations[0][0], sample_metadata, locations[0][1])
        
        # Add other locations
        for path, storage_type in locations[1:]:
            cache.upsert_asset(content_hash, path, sample_metadata, storage_type)
        
        # Get all locations
        all_locations = cache.get_all_locations(content_hash)
        assert len(all_locations) == 3
        
        # Verify all paths and types
        for path, storage_type in locations:
            found = False
            for loc in all_locations:
                if loc["path"] == str(path) and loc["storage_type"] == storage_type:
                    found = True
                    break
            assert found, f"Location {path} with type {storage_type} not found"
    
    def test_remove_location(self, cache, sample_metadata):
        """Test removing a location from an asset."""
        content_hash = "abc123"
        file_path1 = Path("/test/image1.jpg")
        file_path2 = Path("/backup/image1.jpg")
        
        # Add asset with two locations
        cache.upsert_asset(content_hash, file_path1, sample_metadata)
        cache.upsert_asset(content_hash, file_path2, sample_metadata)
        
        # Remove first location
        cache.remove_location(content_hash, file_path1)
        
        # Verify only second location remains
        locations = cache.get_all_locations(content_hash)
        assert len(locations) == 1
        assert locations[0]["path"] == str(file_path2)
    
    def test_delete_asset(self, cache, sample_metadata):
        """Test deleting an asset completely."""
        content_hash = "abc123"
        cache.upsert_asset(content_hash, Path("/test.jpg"), sample_metadata)
        
        # Verify asset exists
        assert cache.get_asset_by_hash(content_hash) is not None
        
        # Delete asset
        cache.delete_asset(content_hash)
        
        # Verify asset is gone
        assert cache.get_asset_by_hash(content_hash) is None
        
        # Verify related data is also gone
        tags = cache.conn.execute(
            "SELECT * FROM asset_tags WHERE content_hash = ?",
            [content_hash]
        ).fetchone()
        assert tags is None
    
    def test_rebuild_from_scratch(self, cache, sample_metadata):
        """Test clearing and rebuilding cache."""
        # Add some data
        cache.upsert_asset("hash1", Path("/test1.jpg"), sample_metadata)
        cache.upsert_asset("hash2", Path("/test2.jpg"), sample_metadata)
        
        # Verify data exists
        stats = cache.get_statistics()
        assert stats["total_assets"] == 2
        
        # Rebuild from scratch
        cache.rebuild_from_scratch()
        
        # Verify cache is empty
        stats = cache.get_statistics()
        assert stats["total_assets"] == 0
    
    def test_get_statistics(self, cache, sample_metadata):
        """Test getting cache statistics."""
        # Add test data
        cache.upsert_asset("hash1", Path("/test1.jpg"), sample_metadata)
        
        metadata2 = sample_metadata.copy()
        metadata2["media_type"] = "video"
        cache.upsert_asset("hash2", Path("/test2.mp4"), metadata2)
        
        # Add asset with multiple locations
        cache.upsert_asset("hash3", Path("/local/test3.jpg"), sample_metadata)
        cache.upsert_asset("hash3", Path("s3://bucket/test3.jpg"), sample_metadata, "s3")
        
        # Get statistics
        stats = cache.get_statistics()
        
        assert stats["total_assets"] == 3
        assert stats["by_media_type"]["image"] == 2
        assert stats["by_media_type"]["video"] == 1
        assert stats["total_locations"] == 4  # 1 + 1 + 2
        assert stats["assets_with_tags"] == 3
        assert stats["assets_with_understanding"] == 3
        assert stats["by_storage_type"]["local"] == 3
        assert stats["by_storage_type"]["s3"] == 1
    
    def test_export_to_parquet(self, cache, sample_metadata, tmp_path):
        """Test exporting cache to Parquet files."""
        # Add test data
        cache.upsert_asset("hash1", Path("/test1.jpg"), sample_metadata)
        cache.upsert_asset("hash2", Path("/test2.jpg"), sample_metadata)
        
        # Export to Parquet
        output_files = cache.export_to_parquet(tmp_path)
        
        # Verify files were created
        assert len(output_files) == 4
        for table_name, file_path in output_files.items():
            assert file_path.exists()
            assert file_path.suffix == ".parquet"
            assert table_name in file_path.stem
    
    def test_custom_tags(self, cache, sample_metadata):
        """Test handling of custom tag categories."""
        content_hash = "abc123"
        
        # Add custom tags
        sample_metadata["tags"]["brand"] = ["nike", "adidas"]
        sample_metadata["tags"]["season"] = ["summer", "2024"]
        
        cache.upsert_asset(content_hash, Path("/test.jpg"), sample_metadata)
        
        # Verify custom tags are stored
        result = cache.get_asset_by_hash(content_hash)
        tags = result["tags"]
        
        # Standard tags
        assert "style" in tags
        assert "mood" in tags
        
        # Custom tags should be in the custom map
        assert "custom_category" in tags["custom"]
        assert tags["custom"]["custom_category"] == ["custom_value"]
        assert "brand" in tags["custom"]
        assert tags["custom"]["brand"] == ["nike", "adidas"]
        assert "season" in tags["custom"]
        assert tags["custom"]["season"] == ["summer", "2024"]
    
    def test_embedding_storage(self, cache, sample_metadata):
        """Test storing and retrieving embeddings."""
        content_hash = "abc123"
        
        # Add embedding to metadata
        embedding = [0.1] * 1536  # OpenAI ada-002 size
        sample_metadata["understanding"]["embedding"] = embedding
        
        cache.upsert_asset(content_hash, Path("/test.jpg"), sample_metadata)
        
        # Retrieve and verify
        result = cache.conn.execute(
            "SELECT embedding FROM asset_understanding WHERE content_hash = ?",
            [content_hash]
        ).fetchone()
        
        assert result is not None
        assert len(result[0]) == 1536
        assert abs(result[0][0] - 0.1) < 0.0001  # Allow for floating point precision