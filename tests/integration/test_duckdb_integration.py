"""Integration tests for the refactored DuckDB storage system."""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from alicemultiverse.storage import UnifiedDuckDBStorage


class TestDuckDBIntegration:
    """Test the integrated DuckDB storage functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        import uuid
        temp_dir = Path(tempfile.gettempdir())
        db_path = temp_dir / f"test_{uuid.uuid4().hex}.duckdb"
        
        db = UnifiedDuckDBStorage(db_path)
        yield db
        db.close()
        db_path.unlink(missing_ok=True)
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return {
            "media_type": "image",
            "file_size": 1024000,
            "ai_source": "midjourney",
            "quality_rating": 4,
            "description": "A beautiful sunset over mountains",
            "prompt": "sunset, mountains, golden hour, landscape photography",
            "created_at": datetime.now().isoformat(),
            "project": "nature",
            "tags": {
                "subject": ["sunset", "mountains"],
                "style": ["landscape", "photography"],
                "mood": ["peaceful", "serene"]
            }
        }
    
    def test_basic_upsert_and_retrieval(self, temp_db, sample_metadata):
        """Test basic asset storage and retrieval."""
        # Upsert an asset
        content_hash = "test_hash_123"
        file_path = Path("/test/image.jpg")
        
        temp_db.upsert_asset(content_hash, file_path, sample_metadata)
        
        # Retrieve by hash
        asset = temp_db.get_asset_by_hash(content_hash)
        assert asset is not None
        assert asset["content_hash"] == content_hash
        assert asset["media_type"] == "image"
        assert asset["ai_source"] == "midjourney"
        assert len(asset["locations"]) == 1
        assert asset["locations"][0]["path"] == str(file_path)
    
    def test_multi_location_support(self, temp_db, sample_metadata):
        """Test that assets can have multiple locations."""
        content_hash = "multi_location_hash"
        path1 = Path("/original/image.jpg")
        path2 = Path("/backup/image.jpg")
        path3 = Path("/organized/2024/image.jpg")
        
        # Add asset with first location
        temp_db.upsert_asset(content_hash, path1, sample_metadata)
        
        # Add same asset with additional locations
        temp_db.upsert_asset(content_hash, path2, sample_metadata)
        temp_db.upsert_asset(content_hash, path3, sample_metadata)
        
        # Verify all locations are tracked
        asset = temp_db.get_asset_by_hash(content_hash)
        locations = asset["locations"]
        assert len(locations) == 3
        
        location_paths = [loc["path"] for loc in locations]
        assert str(path1) in location_paths
        assert str(path2) in location_paths
        assert str(path3) in location_paths
    
    def test_search_functionality(self, temp_db):
        """Test search with various filters."""
        # Add multiple assets
        assets = [
            ("hash1", "/images/sunset.jpg", {"media_type": "image", "ai_source": "midjourney", "quality_rating": 5}),
            ("hash2", "/images/portrait.jpg", {"media_type": "image", "ai_source": "dalle3", "quality_rating": 4}),
            ("hash3", "/videos/clip.mp4", {"media_type": "video", "ai_source": "runway", "quality_rating": 3}),
        ]
        
        for content_hash, path, metadata in assets:
            temp_db.upsert_asset(content_hash, Path(path), metadata)
        
        # Test search by media type
        results, count = temp_db.search(filters={"media_type": "image"})
        assert count == 2
        assert all(r["media_type"] == "image" for r in results)
        
        # Test search by AI source
        results, count = temp_db.search(filters={"ai_source": "midjourney"})
        assert count == 1
        assert results[0]["content_hash"] == "hash1"
        
        # Test search by quality rating
        results, count = temp_db.search(filters={"quality_rating": {"min": 4}})
        assert count == 2
        assert all(r["quality_rating"] >= 4 for r in results)
    
    def test_tag_search(self, temp_db):
        """Test searching by tags."""
        # Add assets with tags
        temp_db.upsert_asset(
            "tagged1", 
            Path("/img1.jpg"),
            {"media_type": "image", "tags": {"style": ["cyberpunk", "neon"], "mood": ["dark"]}}
        )
        temp_db.upsert_asset(
            "tagged2",
            Path("/img2.jpg"), 
            {"media_type": "image", "tags": {"style": ["cyberpunk", "futuristic"], "mood": ["bright"]}}
        )
        temp_db.upsert_asset(
            "tagged3",
            Path("/img3.jpg"),
            {"media_type": "image", "tags": {"style": ["nature"], "mood": ["peaceful"]}}
        )
        
        # Search for cyberpunk images
        results, count = temp_db.search_by_tags(["cyberpunk"])
        assert count == 2
        
        # Search for multiple tags (OR)
        results, count = temp_db.search_by_tags(["neon", "peaceful"])
        assert count == 2  # tagged1 and tagged3
        
        # Search for multiple tags (AND)
        results, count = temp_db.search_by_tags(["cyberpunk", "futuristic"], match_all=True)
        assert count == 1  # Only tagged2
    
    def test_asset_roles(self, temp_db):
        """Test asset role functionality."""
        # Add assets
        temp_db.upsert_asset("primary1", Path("/primary.jpg"), {"media_type": "image"})
        temp_db.upsert_asset("broll1", Path("/broll1.jpg"), {"media_type": "image"})
        temp_db.upsert_asset("broll2", Path("/broll2.jpg"), {"media_type": "image"})
        
        # Set roles
        assert temp_db.set_asset_role("broll1", "b-roll")
        assert temp_db.set_asset_role("broll2", "b-roll")
        
        # Search by role
        results, count = temp_db.search(filters={"asset_role": "b-roll"})
        assert count == 2
        assert all(r["asset_role"] == "b-roll" for r in results)
        
        # Get assets by role
        broll_assets = temp_db.get_assets_by_role("b-roll")
        assert len(broll_assets) == 2
        
        # Verify default role
        primary_asset = temp_db.get_asset_by_hash("primary1")
        assert primary_asset["asset_role"] == "primary"
    
    def test_batch_operations(self, temp_db):
        """Test batch upsert functionality."""
        batch_items = [
            ("batch1", Path("/batch/img1.jpg"), {"media_type": "image", "ai_source": "midjourney"}),
            ("batch2", Path("/batch/img2.jpg"), {"media_type": "image", "ai_source": "dalle3"}),
            ("batch3", Path("/batch/img3.jpg"), {"media_type": "image", "ai_source": "midjourney"}),
        ]
        
        result = temp_db.upsert_assets_batch(batch_items)
        
        assert result["total"] == 3
        assert result["processed"] == 3
        assert result["success_rate"] == 1.0
        assert len(result["errors"]) == 0
        
        # Verify all assets were added
        results, count = temp_db.search()
        assert count == 3
    
    def test_statistics(self, temp_db):
        """Test analytics functionality."""
        # Add varied assets
        assets_data = [
            ("img1", Path("/images/1.jpg"), {"media_type": "image", "ai_source": "midjourney", "file_size": 1000000}),
            ("img2", Path("/images/2.jpg"), {"media_type": "image", "ai_source": "dalle3", "file_size": 2000000}),
            ("vid1", Path("/videos/1.mp4"), {"media_type": "video", "ai_source": "runway", "file_size": 10000000}),
        ]
        
        for content_hash, path, metadata in assets_data:
            temp_db.upsert_asset(content_hash, path, metadata)
        
        stats = temp_db.get_statistics()
        
        assert stats["total_assets"] == 3
        assert stats["by_media_type"]["image"] == 2
        assert stats["by_media_type"]["video"] == 1
        assert stats["by_ai_source"]["midjourney"] == 1
        assert stats["storage"]["total_files"] == 3
        assert stats["storage"]["total_size_bytes"] == 13000000
    
    def test_perceptual_hash_similarity(self, temp_db):
        """Test similarity search functionality."""
        # Add assets with perceptual hashes
        temp_db.upsert_asset("img1", Path("/1.jpg"), {"media_type": "image"})
        temp_db.upsert_asset("img2", Path("/2.jpg"), {"media_type": "image"})
        temp_db.upsert_asset("img3", Path("/3.jpg"), {"media_type": "image"})
        
        # Index perceptual hashes (simulated)
        temp_db.index_perceptual_hashes(
            "img1",
            phash="1111111111111111",
            dhash="1111111111111111"
        )
        temp_db.index_perceptual_hashes(
            "img2",
            phash="1111111111111110",  # 1 bit different
            dhash="1111111111111110"
        )
        temp_db.index_perceptual_hashes(
            "img3",
            phash="0000000000000000",  # Very different
            dhash="0000000000000000"
        )
        
        # Find similar images
        # With 1 bit different out of 64 bits: similarity = 1 - (1/64) = 0.984
        similar = temp_db.find_similar("img1", threshold=0.95)
        
        # Should find img2 (1 bit different) but not img3
        assert len(similar) >= 1
        assert any(s["content_hash"] == "img2" for s in similar)
        assert not any(s["content_hash"] == "img3" for s in similar)
    
    def test_location_removal(self, temp_db):
        """Test removing specific locations while preserving asset."""
        content_hash = "multi_loc"
        path1 = Path("/original/image.jpg")
        path2 = Path("/backup/image.jpg")
        
        # Add asset with multiple locations
        temp_db.upsert_asset(content_hash, path1, {"media_type": "image"})
        temp_db.upsert_asset(content_hash, path2, {"media_type": "image"})
        
        # Remove one location
        temp_db.remove_location(content_hash, path1)
        
        # Asset should still exist with remaining location
        asset = temp_db.get_asset_by_hash(content_hash)
        assert asset is not None
        assert len(asset["locations"]) == 1
        assert asset["locations"][0]["path"] == str(path2)
        
        # Remove last location - asset should be deleted
        temp_db.remove_location(content_hash, path2)
        asset = temp_db.get_asset_by_hash(content_hash)
        assert asset is None
    
    def test_content_hash_as_id(self, temp_db):
        """Test that content hash serves as a stable identifier."""
        content_hash = "stable_hash_123"
        original_path = Path("/original/photo.jpg")
        
        # Add asset
        temp_db.upsert_asset(content_hash, original_path, {
            "media_type": "image",
            "description": "Original photo"
        })
        
        # "Move" the file by adding new location and removing old
        new_path = Path("/organized/2024/photo_renamed.jpg")
        temp_db.upsert_asset(content_hash, new_path, {})
        temp_db.remove_location(content_hash, original_path)
        
        # Asset should still be findable by content hash
        asset = temp_db.get_asset_by_hash(content_hash)
        assert asset is not None
        assert asset["description"] == "Original photo"  # Metadata preserved
        assert len(asset["locations"]) == 1
        assert asset["locations"][0]["path"] == str(new_path)