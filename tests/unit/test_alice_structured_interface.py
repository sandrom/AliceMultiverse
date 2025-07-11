"""Tests for the Alice Structured Interface."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Valid SHA256 hashes for testing
TEST_HASH1 = "a" * 64  # 64 hex chars
TEST_HASH2 = "b" * 64  # 64 hex chars

from alicemultiverse.interface.alice_structured import AliceStructuredInterface
from alicemultiverse.interface.structured_models import (
    AssetRole,
    DimensionFilter,
    GroupingRequest,
    MediaType,
    OrganizeRequest,
    RangeFilter,
    SearchFilters,
    SearchRequest,
    SortField,
    SortOrder,
    TagUpdateRequest,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock()
    config.paths.inbox = "/test/inbox"
    config.paths.organized = "/test/organized"
    config.processing.quality = False
    config.processing.watch = False
    config.processing.move = False
    config.pipeline.mode = "basic"
    return config


@pytest.fixture
def alice_interface(mock_config):
    """Create Alice interface with mocked dependencies."""
    with patch('alicemultiverse.interface.alice_structured.load_config', return_value=mock_config):
        with patch('alicemultiverse.interface.alice_structured.EnhancedMediaOrganizer'):
            interface = AliceStructuredInterface()
            # Mock the organizer
            interface.organizer = MagicMock()
            return interface


class TestSearchAssets:
    """Test search_assets functionality."""

    def test_search_with_media_type_filter(self, alice_interface):
        """Test searching with media type filter."""
        # Setup mock data
        mock_results = [{
            "asset_id": TEST_HASH1,
            "content_hash": "c" * 64,
            "file_path": "/test/image.jpg",
            "file_name": "image.jpg",
            "media_type": "image",
            "file_size": 1024,
            "source_type": "stable-diffusion",
            "quality_stars": 4,
            "created_at": datetime.now(),
            "modified_at": datetime.now(),
            "discovered_at": datetime.now(),
            "width": 1024,
            "height": 768,
            "prompt": "test prompt",
            "style_tags": ["cyberpunk"],
            "mood_tags": ["dark"],
            "subject_tags": ["portrait"],
            "custom_tags": [],
        }]
        alice_interface.organizer.search_assets.return_value = mock_results

        # Create request
        request = SearchRequest(
            filters=SearchFilters(media_type=MediaType.IMAGE),
            sort_by=SortField.CREATED_DATE,
            order=SortOrder.DESC,
            limit=10
        )

        # Execute search
        response = alice_interface.search_assets(request)

        # Verify response
        assert response["success"] is True
        assert "Found 1 assets" in response["message"]
        assert response["data"]["total_count"] == 1
        assert len(response["data"]["results"]) == 1

        # Verify result structure
        result = response["data"]["results"][0]
        assert result["content_hash"] == "c" * 64
        assert result["media_type"] == MediaType.IMAGE
        assert len(result["tags"]) == 3  # cyberpunk, dark, portrait

    def test_search_with_tag_filters(self, alice_interface):
        """Test searching with various tag filters."""
        # Setup
        alice_interface.organizer.search_assets.return_value = []

        # Create request with tag filters
        request = SearchRequest(
            filters=SearchFilters(
                tags=["cyberpunk", "portrait"],  # AND operation
                any_tags=["neon", "dark"],  # OR operation
                exclude_tags=["sketch", "wip"]  # NOT operation
            )
        )

        # Execute
        response = alice_interface.search_assets(request)

        # Verify the organizer was called with correct parameters
        call_args = alice_interface.organizer.search_assets.call_args[1]
        assert call_args["all_tags"] == ["cyberpunk", "portrait"]
        assert call_args["any_tags"] == ["neon", "dark"]
        assert call_args["exclude_tags"] == ["sketch", "wip"]

    def test_search_with_quality_filter(self, alice_interface):
        """Test searching with quality rating filter."""
        alice_interface.organizer.search_assets.return_value = []

        request = SearchRequest(
            filters=SearchFilters(
                quality_rating=RangeFilter(min=4, max=5)
            )
        )

        response = alice_interface.search_assets(request)

        call_args = alice_interface.organizer.search_assets.call_args[1]
        assert call_args["min_stars"] == 4
        assert call_args["max_stars"] == 5

    def test_search_with_date_range(self, alice_interface):
        """Test searching with date range filter."""
        alice_interface.organizer.search_assets.return_value = []

        start_date = "2024-01-01"
        end_date = "2024-01-31"

        request = SearchRequest(
            filters=SearchFilters(
                created_date=RangeFilter(
                    min=datetime(2024, 1, 1).timestamp(),
                    max=datetime(2024, 1, 31).timestamp()
                )
            )
        )

        response = alice_interface.search_assets(request)

        call_args = alice_interface.organizer.search_assets.call_args[1]
        assert call_args["timeframe_start"].date() == datetime(2024, 1, 1).date()
        assert call_args["timeframe_end"].date() == datetime(2024, 1, 31).date()

    def test_search_with_dimension_filters(self, alice_interface):
        """Test searching with dimension filters."""
        # Mock data with various dimensions
        mock_results = [
            {
                "content_hash": TEST_HASH1,
                "file_path": "/test/image1.jpg",
                "file_name": "image1.jpg",
                "media_type": "image",
                "file_size": 1024,
                "width": 1920,
                "height": 1080,
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
                "discovered_at": datetime.now(),
            },
            {
                "content_hash": TEST_HASH2,
                "file_path": "/test/image2.jpg",
                "file_name": "image2.jpg",
                "media_type": "image",
                "file_size": 2048,
                "width": 800,
                "height": 600,
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
                "discovered_at": datetime.now(),
            }
        ]
        alice_interface.organizer.search_assets.return_value = mock_results

        # Request images with minimum width of 1000px
        request = SearchRequest(
            filters=SearchFilters(
                dimensions=DimensionFilter(
                    width=RangeFilter(min=1000),
                    aspect_ratio=RangeFilter(min=1.5, max=2.0)
                )
            )
        )

        response = alice_interface.search_assets(request)

        # Should only return the first image (1920x1080)
        assert response["data"]["total_count"] == 1
        assert response["data"]["results"][0]["content_hash"] == TEST_HASH1

    def test_search_with_filename_pattern(self, alice_interface):
        """Test searching with filename regex pattern."""
        mock_results = [
            {
                "content_hash": TEST_HASH1,
                "file_path": "/test/cyberpunk_001.jpg",
                "file_name": "cyberpunk_001.jpg",
                "media_type": "image",
                "file_size": 1024,
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
                "discovered_at": datetime.now(),
            },
            {
                "content_hash": TEST_HASH2,
                "file_path": "/test/fantasy_001.jpg",
                "file_name": "fantasy_001.jpg",
                "media_type": "image",
                "file_size": 1024,
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
                "discovered_at": datetime.now(),
            }
        ]
        alice_interface.organizer.search_assets.return_value = mock_results

        # Search for cyberpunk files
        request = SearchRequest(
            filters=SearchFilters(
                filename_pattern=r"cyberpunk.*\.jpg"
            )
        )

        response = alice_interface.search_assets(request)

        assert response["data"]["total_count"] == 1
        assert "cyberpunk" in response["data"]["results"][0]["file_path"]

    def test_search_facets_calculation(self, alice_interface):
        """Test that search returns proper facets."""
        mock_results = [
            {
                "content_hash": "d" * 64,
                "file_path": f"/test/image{i}.jpg",
                "file_name": f"image{i}.jpg",
                "media_type": "image",
                "file_size": 1024,
                "source_type": "stable-diffusion" if i % 2 == 0 else "midjourney",
                "quality_stars": 4 if i < 3 else 5,
                "style_tags": ["cyberpunk"] if i % 2 == 0 else ["fantasy"],
                "mood_tags": ["dark"],
                "subject_tags": ["portrait"],
                "custom_tags": [],
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
                "discovered_at": datetime.now(),
            }
            for i in range(5)
        ]
        alice_interface.organizer.search_assets.return_value = mock_results

        request = SearchRequest(filters=SearchFilters())
        response = alice_interface.search_assets(request)

        facets = response["data"]["facets"]

        # Check tag facets
        tag_values = {f["value"]: f["count"] for f in facets["tags"]}
        assert tag_values["dark"] == 5  # All have dark mood
        assert tag_values["portrait"] == 5  # All have portrait subject
        assert tag_values["cyberpunk"] == 3  # 0, 2, 4
        assert tag_values["fantasy"] == 2  # 1, 3

        # Check source facets
        source_values = {f["value"]: f["count"] for f in facets["ai_sources"]}
        assert source_values["stable-diffusion"] == 3
        assert source_values["midjourney"] == 2


class TestOrganizeMedia:
    """Test organize_media functionality."""

    def test_organize_with_quality_assessment(self, alice_interface):
        """Test organization with quality assessment enabled."""
        # Mock the EnhancedMediaOrganizer class itself
        with patch('alicemultiverse.interface.alice_structured.EnhancedMediaOrganizer') as MockOrganizer:
            # Configure the mock instance
            mock_instance = MagicMock()
            mock_instance.organize.return_value = True
            mock_instance.stats = {"processed": 10, "organized": 8}
            mock_instance.metadata_cache.get_all_metadata.return_value = [{}] * 10
            MockOrganizer.return_value = mock_instance

            request = OrganizeRequest(
                source_path="/custom/inbox",
                quality_assessment=True,
                pipeline="brisque-claude"
            )

            response = alice_interface.organize_media(request)

            assert response["success"] is True
            assert response["data"]["stats"]["processed"] == 10
            assert response["data"]["metadata_count"] == 10

            # Verify config was updated
            assert alice_interface.config.paths.inbox == "/custom/inbox"
            assert alice_interface.config.processing.quality is True
            assert alice_interface.config.pipeline.mode == "brisque-claude"

    def test_organize_with_watch_mode(self, alice_interface):
        """Test organization with watch mode enabled."""
        with patch('alicemultiverse.interface.alice_structured.EnhancedMediaOrganizer') as MockOrganizer:
            # Configure the mock instance
            mock_instance = MagicMock()
            mock_instance.organize.return_value = True
            mock_instance.stats = {"processed": 5}
            mock_instance.metadata_cache.get_all_metadata.return_value = []
            MockOrganizer.return_value = mock_instance

            request = OrganizeRequest(watch_mode=True)

            response = alice_interface.organize_media(request)

            assert response["success"] is True
            assert alice_interface.config.processing.watch is True


class TestTagOperations:
    """Test tag update operations."""

    def test_add_tags(self, alice_interface):
        """Test adding tags to assets."""
        # Mock existing asset
        alice_interface.organizer.metadata_cache.get_metadata_by_id.return_value = {
            "asset_id": TEST_HASH1,
            "custom_tags": ["existing"]
        }
        alice_interface.organizer.metadata_cache.update_metadata.return_value = True

        request = TagUpdateRequest(
            asset_ids=[TEST_HASH1],
            add_tags=["new1", "new2"]
        )

        response = alice_interface.update_tags(request)

        assert response["success"] is True
        assert response["data"]["updated_count"] == 1

        # Verify tags were merged
        update_call = alice_interface.organizer.metadata_cache.update_metadata.call_args
        updated_metadata = update_call[0][1]
        assert set(updated_metadata["custom_tags"]) == {"existing", "new1", "new2"}

    def test_remove_tags(self, alice_interface):
        """Test removing tags from assets."""
        alice_interface.organizer.metadata_cache.get_metadata_by_id.return_value = {
            "asset_id": TEST_HASH1,
            "custom_tags": ["tag1", "tag2", "tag3"]
        }
        alice_interface.organizer.metadata_cache.update_metadata.return_value = True

        request = TagUpdateRequest(
            asset_ids=[TEST_HASH1],
            remove_tags=["tag2"]
        )

        response = alice_interface.update_tags(request)

        update_call = alice_interface.organizer.metadata_cache.update_metadata.call_args
        updated_metadata = update_call[0][1]
        assert set(updated_metadata["custom_tags"]) == {"tag1", "tag3"}

    def test_set_tags(self, alice_interface):
        """Test replacing all tags."""
        alice_interface.organizer.metadata_cache.get_metadata_by_id.return_value = {
            "asset_id": TEST_HASH1,
            "custom_tags": ["old1", "old2"]
        }
        alice_interface.organizer.metadata_cache.update_metadata.return_value = True

        request = TagUpdateRequest(
            asset_ids=[TEST_HASH1],
            set_tags=["new1", "new2", "new3"]
        )

        response = alice_interface.update_tags(request)

        update_call = alice_interface.organizer.metadata_cache.update_metadata.call_args
        updated_metadata = update_call[0][1]
        assert updated_metadata["custom_tags"] == ["new1", "new2", "new3"]


class TestAssetOperations:
    """Test individual asset operations."""

    def test_get_asset_by_id(self, alice_interface):
        """Test retrieving a single asset."""
        mock_metadata = {
            "asset_id": TEST_HASH1,
            "content_hash": "c" * 64,
            "file_path": "/test/image.jpg",
            "file_name": "image.jpg",
            "media_type": "image",
            "file_size": 1024,
            "width": 1920,
            "height": 1080,
            "source_type": "stable-diffusion",
            "quality_stars": 5,
            "style_tags": ["cyberpunk"],
            "mood_tags": ["dark"],
            "subject_tags": [],
            "custom_tags": [],
            "created_at": datetime.now(),
            "modified_at": datetime.now(),
            "discovered_at": datetime.now(),
            "prompt": "cyberpunk city at night",
        }
        alice_interface.organizer.metadata_cache.get_metadata_by_id.return_value = mock_metadata

        response = alice_interface.get_asset_by_id(TEST_HASH1)

        assert response["success"] is True
        assert response["data"]["content_hash"] == "c" * 64
        assert response["data"]["media_type"] == MediaType.IMAGE
        assert "cyberpunk" in response["data"]["tags"]
        assert response["data"]["metadata"]["prompt"] == "cyberpunk city at night"

    def test_get_nonexistent_asset(self, alice_interface):
        """Test retrieving a nonexistent asset."""
        alice_interface.organizer.metadata_cache.get_metadata_by_id.return_value = None

        response = alice_interface.get_asset_by_id("nonexistent")

        assert response["success"] is False
        assert "not found" in response["message"]

    def test_set_asset_role(self, alice_interface):
        """Test setting asset role."""
        alice_interface.organizer.set_asset_role.return_value = True

        response = alice_interface.set_asset_role(TEST_HASH1, AssetRole.HERO)

        assert response["success"] is True
        assert response["data"]["role"] == "hero"

        # Verify the organizer was called correctly
        alice_interface.organizer.set_asset_role.assert_called_once()
        call_args = alice_interface.organizer.set_asset_role.call_args[0]
        assert call_args[0] == TEST_HASH1
        assert call_args[1].value == "hero"


class TestGroupOperations:
    """Test asset grouping operations."""

    def test_group_assets(self, alice_interface):
        """Test grouping assets together."""
        alice_interface.organizer.group_assets.return_value = True

        request = GroupingRequest(
            asset_ids=[TEST_HASH1, TEST_HASH2, "c" * 64],
            group_name="Campaign Photos",
            group_metadata={"campaign": "summer_2024"}
        )

        response = alice_interface.group_assets(request)

        assert response["success"] is True
        assert response["data"]["group_name"] == "Campaign Photos"
        assert response["data"]["asset_count"] == 3

        alice_interface.organizer.group_assets.assert_called_with(
            [TEST_HASH1, TEST_HASH2, "c" * 64],
            "Campaign Photos"
        )


class TestErrorHandling:
    """Test error handling in various operations."""

    def test_search_error_handling(self, alice_interface):
        """Test error handling in search."""
        alice_interface.organizer.search_assets.side_effect = Exception("Database error")

        request = SearchRequest(filters=SearchFilters())
        response = alice_interface.search_assets(request)

        assert response["success"] is False
        assert "Database error" in response["error"]

    def test_organize_error_handling(self, alice_interface):
        """Test error handling in organize."""
        with patch('alicemultiverse.interface.alice_structured.EnhancedMediaOrganizer') as MockOrganizer:
            # Make the constructor raise an exception
            MockOrganizer.side_effect = Exception("Permission denied")

            request = OrganizeRequest()
            response = alice_interface.organize_media(request)

            assert response["success"] is False
            assert response["error"] is not None
            assert "Permission denied" in response["error"]


class TestDateParsing:
    """Test ISO date parsing."""

    def test_parse_iso_date(self, alice_interface):
        """Test various ISO date formats."""
        # Full ISO with timezone
        dt1 = alice_interface._parse_iso_date("2024-01-15T10:30:00Z")
        assert dt1.year == 2024
        assert dt1.month == 1
        assert dt1.day == 15

        # Date only
        dt2 = alice_interface._parse_iso_date("2024-01-15")
        assert dt2.year == 2024
        assert dt2.month == 1
        assert dt2.day == 15

        # With offset
        dt3 = alice_interface._parse_iso_date("2024-01-15T10:30:00+05:00")
        assert dt3.year == 2024
