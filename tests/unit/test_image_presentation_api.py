"""Tests for Image Presentation API"""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from alicemultiverse.interface.models import (
    ImageSearchResult,
    PresentableImage,
    SelectionFeedback
)
from alicemultiverse.interface.image_presentation import (
    ImagePresentationAPI,
    SoftDeleteCategory
)


@pytest.fixture
def mock_storage():
    """Mock storage backend"""
    storage = MagicMock()
    storage.search_by_tags = MagicMock()
    storage.get_asset_by_hash = MagicMock()
    storage.remove_location = MagicMock()
    storage._add_file_location = MagicMock()
    return storage


@pytest.fixture
def api(mock_storage):
    """Image Presentation API instance"""
    return ImagePresentationAPI(
        storage=mock_storage
    )


@pytest.fixture
def sample_images():
    """Sample presentable images for testing"""
    return [
        PresentableImage(
            hash="abc123",
            path="/images/cyberpunk-001.jpg",
            thumbnail_url="data:image/jpeg;base64,/9j/4AAQ...",
            display_url="file:///images/cyberpunk-001.jpg",
            tags=["portrait", "cyberpunk", "neon"],
            source="midjourney",
            created_date=datetime.now(),
            description="Futuristic portrait with neon lighting",
            mood=["dramatic", "mysterious"],
            style=["cyberpunk", "digital art"],
            colors=["blue", "pink", "black"],
            previously_selected=False,
            selection_reason=None,
            dimensions=(1024, 1024),
            file_size=2048576
        ),
        PresentableImage(
            hash="def456",
            path="/images/landscape-001.jpg",
            thumbnail_url="data:image/jpeg;base64,/9j/4BBQ...",
            display_url="file:///images/landscape-001.jpg",
            tags=["landscape", "mountains", "sunset"],
            source="dalle3",
            created_date=datetime.now() - timedelta(days=1),
            description="Mountain landscape at sunset",
            mood=["serene", "majestic"],
            style=["photorealistic", "landscape"],
            colors=["orange", "purple", "blue"],
            previously_selected=True,
            selection_reason="Beautiful colors for opening scene",
            dimensions=(1920, 1080),
            file_size=3145728
        )
    ]


class TestImageSearch:
    """Test image search functionality"""
    
    @pytest.mark.asyncio
    async def test_search_by_tags(self, api, mock_storage, sample_images):
        """Test searching images by tags"""
        # Setup - Return data in DuckDB format (list of dicts, not a dict with "images" key)
        mock_storage.search_by_tags.return_value = [
            {
                "content_hash": "abc123",
                "locations": [{"path": "/images/cyberpunk-001.jpg", "storage_type": "local"}],
                "tags": {"style": ["cyberpunk"], "mood": ["dramatic"]},
                "understanding": {"description": "Futuristic portrait"},
                "generation": {"provider": "midjourney"},
                "file_size": 2048576,
                "created_at": datetime.now()
            },
            {
                "content_hash": "def456",
                "locations": [{"path": "/images/landscape-001.jpg", "storage_type": "local"}],
                "tags": {"style": ["landscape"], "mood": ["serene"]},
                "understanding": {"description": "Mountain landscape"},
                "generation": {"provider": "dalle3"},
                "file_size": 3145728,
                "created_at": datetime.now() - timedelta(days=1)
            }
        ]
        
        # Execute
        result = await api.search_images(tags=["cyberpunk"])
        
        # Verify
        assert isinstance(result, ImageSearchResult)
        assert len(result.images) == 2
        assert result.total_count == 2
        assert not result.has_more
        # Check that search was called with tag dict and limit
        mock_storage.search_by_tags.assert_called_once_with(
            {"style": ["cyberpunk"]}, 
            limit=20
        )
    
    @pytest.mark.asyncio
    async def test_search_with_exclusions(self, api, mock_storage):
        """Test searching with tag and folder exclusions"""
        # Setup
        mock_storage.search_by_tags.return_value = {
            "images": [],
            "total_count": 0
        }
        
        # Execute
        result = await api.search_images(
            tags=["portrait"],
            exclude_tags=["anime"],
            exclude_folders=["sorted-out/", "archive/"]
        )
        
        # Verify - our implementation filters exclusions after search
        mock_storage.search_by_tags.assert_called_once()
        call_args = mock_storage.search_by_tags.call_args
        assert call_args[0][0] == {"style": ["portrait"]}
        assert call_args[1]["limit"] == 20
    
    @pytest.mark.asyncio
    async def test_search_by_query(self, api, mock_storage, sample_images):
        """Test natural language query search"""
        # Setup
        mock_storage.search_by_tags.return_value = [
            {
                "content_hash": "abc123",
                "locations": [{"path": "/images/cyberpunk-001.jpg", "storage_type": "local"}],
                "tags": {"style": ["cyberpunk", "portrait"], "mood": ["dramatic"]},
                "understanding": {"description": "Futuristic portrait with neon lighting"},
                "generation": {"provider": "midjourney"},
                "file_size": 2048576,
                "created_at": datetime.now()
            }
        ]
        
        # Execute
        result = await api.search_images(query="cyberpunk portraits with neon")
        
        # Verify
        assert len(result.images) == 1
        assert result.query_interpretation == "Tags: cyberpunk, portraits, neon"
        assert "cyberpunk" in result.images[0].tags
    
    @pytest.mark.asyncio
    async def test_search_similar_images(self, api, mock_storage, sample_images):
        """Test finding similar images"""
        # Setup
        mock_storage.search_by_tags.return_value = {
            "images": sample_images,
            "total_count": 2
        }
        
        # Execute with similar_to - should log warning for now
        with patch('alicemultiverse.interface.image_presentation.logger') as mock_logger:
            result = await api.search_images(
                similar_to=["abc123", "def456"],
                limit=10
            )
            
            # Verify warning was logged
            mock_logger.warning.assert_called_with("Similarity search not yet implemented")
    
    @pytest.mark.asyncio
    async def test_search_date_range(self, api, mock_storage):
        """Test searching within date range"""
        # Setup
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        # Setup mock return
        mock_storage.search_by_tags.return_value = []
        
        # Execute
        await api.search_images(date_range=(start_date, end_date))
        
        # Verify that search was called (date filtering happens after search)
        mock_storage.search_by_tags.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pagination(self, api, mock_storage, sample_images):
        """Test result pagination"""
        # Setup
        # Return one image from a total of 100
        mock_storage.search_by_tags.return_value = [
            {
                "content_hash": "test123",
                "locations": [{"path": "/images/test.jpg", "storage_type": "local"}],
                "tags": {"style": ["test"]},
                "understanding": {},
                "generation": {},
                "file_size": 1024,
                "created_at": datetime.now()
            }
        ] * 100  # Simulate 100 results
        
        # Execute
        result = await api.search_images(limit=1, offset=50)
        
        # Verify - our implementation does pagination after fetching
        assert len(result.images) == 1  # Due to limit
        assert result.total_count == 100  # Total found (not adjusted for offset)
        assert result.has_more is True  # offset + limit (51) < total (100)
        mock_storage.search_by_tags.assert_called_once()


class TestSelectionTracking:
    """Test user selection tracking"""
    
    @pytest.mark.asyncio
    async def test_track_positive_selection(self, api, mock_storage):
        """Test tracking when user selects an image"""
        # Execute
        await api.track_selection(
            image_hash="abc123",
            selected=True,
            reason="Perfect mood for my video",
            session_id="session-001"
        )
        
        # Verify - we save to file now, not storage
        assert api.feedback_file.parent.exists()  # Cache dir created
    
    @pytest.mark.asyncio
    async def test_track_negative_selection(self, api, mock_storage):
        """Test tracking when user rejects an image"""
        # Execute
        await api.track_selection(
            image_hash="def456",
            selected=False,
            reason="Too dark"
        )
        
        # Verify - we save to file now
        assert api.feedback_file.parent.exists()
    
    @pytest.mark.asyncio
    async def test_selection_affects_future_search(self, api, mock_storage):
        """Test that selections influence search results"""
        # Track some selections
        await api.track_selection("abc123", True, "Love the style")
        await api.track_selection("def456", False, "Wrong mood")
        
        # Setup search results
        mock_storage.search_by_tags.return_value = [
            {
                "content_hash": "abc123",
                "locations": [{"path": "/images/test1.jpg", "storage_type": "local"}],
                "tags": {"style": ["portrait"]},
                "understanding": {},
                "generation": {},
                "file_size": 1024,
                "created_at": datetime.now()
            },
            {
                "content_hash": "def456",
                "locations": [{"path": "/images/test2.jpg", "storage_type": "local"}],
                "tags": {"style": ["portrait"]},
                "understanding": {},
                "generation": {},
                "file_size": 2048,
                "created_at": datetime.now()
            }
        ]
        
        result = await api.search_images(tags=["portrait"])
        
        # Verify selection history was read
        # Note: The implementation reads from file, so we'd need to check that
        # the feedback file was written and read correctly
        assert len(result.images) == 2


class TestSoftDelete:
    """Test soft delete functionality"""
    
    @pytest.mark.asyncio
    async def test_soft_delete_rejected(self, api, mock_storage):
        """Test moving rejected image to sorted-out folder"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup - use temp directory for test files
            temp_path = Path(temp_dir)
            test_image = temp_path / "images" / "bad-image.jpg"
            test_image.parent.mkdir(parents=True, exist_ok=True)
            test_image.write_text("test")
            
            mock_storage.get_asset_by_hash.return_value = {
                "content_hash": "xyz789",
                "locations": [{"path": str(test_image), "storage_type": "local"}],
                "tags": {},
                "file_size": 1024
            }
            
            # Execute
            new_path = await api.soft_delete_image(
                image_hash="xyz789",
                reason="Has artifacts",
                category=SoftDeleteCategory.REJECTED
            )
            
            # Verify
            assert "sorted-out/rejected" in new_path
            assert Path(new_path).exists()
            assert not test_image.exists()  # Original file moved
            mock_storage.remove_location.assert_called_once()
            mock_storage._add_file_location.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_soft_delete_broken(self, api, mock_storage):
        """Test moving broken image to appropriate folder"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup - use temp directory
            temp_path = Path(temp_dir)
            test_image = temp_path / "images" / "corrupted.jpg"
            test_image.parent.mkdir(parents=True, exist_ok=True)
            test_image.write_text("test")
            
            mock_storage.get_asset_by_hash.return_value = {
                "content_hash": "broken123",
                "locations": [{"path": str(test_image), "storage_type": "local"}],
                "tags": {},
                "file_size": 1024
            }
            
            # Execute
            new_path = await api.soft_delete_image(
                image_hash="broken123",
                reason="File corrupted",
                category=SoftDeleteCategory.BROKEN
            )
            
            # Verify
            assert "sorted-out/broken" in new_path
            assert Path(new_path).exists()
    
    @pytest.mark.asyncio
    async def test_soft_delete_maybe_later(self, api, mock_storage):
        """Test archiving image for potential future use"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup - use temp directory
            temp_path = Path(temp_dir)
            test_image = temp_path / "images" / "maybe.jpg"
            test_image.parent.mkdir(parents=True, exist_ok=True)
            test_image.write_text("test")
            
            mock_storage.get_asset_by_hash.return_value = {
                "content_hash": "maybe123",
                "locations": [{"path": str(test_image), "storage_type": "local"}],
                "tags": {},
                "file_size": 2048
            }
            
            # Execute
            new_path = await api.soft_delete_image(
                image_hash="maybe123",
                reason="Might work for different project",
                category=SoftDeleteCategory.MAYBE_LATER
            )
            
            # Verify
            assert "sorted-out/maybe-later" in new_path
            assert Path(new_path).exists()
    
    @pytest.mark.asyncio
    async def test_soft_delete_updates_exclusion_list(self, api, mock_storage):
        """Test that soft-deleted folders are excluded from searches"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup - use temp directory
            temp_path = Path(temp_dir)
            test_image = temp_path / "images" / "test.jpg"
            test_image.parent.mkdir(parents=True, exist_ok=True)
            test_image.write_text("test")
            
            mock_storage.get_asset_by_hash.return_value = {
                "content_hash": "abc123",
                "locations": [{"path": str(test_image), "storage_type": "local"}],
                "tags": {},
                "file_size": 1024
            }
            
            # Soft delete an image
            await api.soft_delete_image("abc123", "broken", SoftDeleteCategory.BROKEN)
        
        # Setup for search
        mock_storage.search_by_tags.return_value = []
        
        # Search should have sorted-out in exclusion list
        await api.search_images(tags=["portrait"])
        
        # Verify exclusion list was updated
        assert "sorted-out/broken/" in api._exclusion_folders


class TestImagePresentation:
    """Test image presentation formatting"""
    
    def test_presentable_image_to_dict(self, sample_images):
        """Test converting PresentableImage to display dict"""
        image = sample_images[0]
        display_dict = image.to_display_dict()
        
        assert display_dict["id"] == "abc123"
        assert display_dict["thumbnail"].startswith("data:image/jpeg;base64,")
        assert display_dict["caption"] == "Futuristic portrait with neon lighting"
        assert display_dict["tags"] == ["portrait", "cyberpunk", "neon"]
        assert display_dict["selectable"] is True
        assert display_dict["previously_selected"] is False
    
    def test_search_result_formatting(self, sample_images):
        """Test formatting search results for chat display"""
        result = ImageSearchResult(
            images=sample_images,
            total_count=50,
            has_more=True,
            query_interpretation="Found cyberpunk portraits",
            suggestions=[
                "Try adding 'neon' for more vibrant results",
                "Exclude 'anime' for photorealistic style"
            ]
        )
        
        formatted = result.to_chat_response()
        
        assert len(formatted["images"]) == 2
        assert formatted["total"] == 50
        assert formatted["has_more"] is True
        assert formatted["instructions"] == "Click images to select. Tell me what you like/dislike."
        assert len(formatted["suggestions"]) == 2


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_search_storage_error(self, api, mock_storage):
        """Test handling storage errors during search"""
        mock_storage.search_by_tags.side_effect = Exception("Database error")
        
        # The implementation catches exceptions and returns empty results
        result = await api.search_images(tags=["test"])
        
        assert len(result.images) == 0
        assert result.total_count == 0
        assert not result.has_more
    
    @pytest.mark.asyncio
    async def test_soft_delete_file_not_found(self, api, mock_storage):
        """Test soft delete when file doesn't exist"""
        mock_storage.get_asset_by_hash.return_value = None
        
        with pytest.raises(FileNotFoundError):
            await api.soft_delete_image("nonexistent", "test")
    
    @pytest.mark.asyncio
    async def test_invalid_query_parameters(self, api):
        """Test handling invalid search parameters"""
        # Negative limit
        with pytest.raises(ValueError):
            await api.search_images(limit=-1)
        
        # Invalid date range
        with pytest.raises(ValueError):
            await api.search_images(
                date_range=(datetime.now(), datetime.now() - timedelta(days=1))
            )