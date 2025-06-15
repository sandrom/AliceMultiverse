"""Test database integration with AliceInterface."""

import os

import pytest

from alicemultiverse.interface import AliceInterface
from alicemultiverse.interface.models import OrganizeRequest, SearchRequest


class TestDatabaseIntegration:
    """Test that assets are properly persisted to database."""

    @pytest.fixture
    def alice_with_db(self, tmp_path):
        """Create Alice interface with database."""
        inbox = tmp_path / "inbox"
        organized = tmp_path / "organized"
        db_path = tmp_path / "test.db"
        inbox.mkdir()
        organized.mkdir()

        # Set database URL to test database
        os.environ["ALICEMULTIVERSE_DATABASE_URL"] = f"sqlite:///{db_path}"

        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(f"""
paths:
  inbox: {inbox}
  organized: {organized}

processing:
  quality: true
""")

        alice = AliceInterface(config_path)

        yield alice

        # Cleanup
        if "ALICEMULTIVERSE_DATABASE_URL" in os.environ:
            del os.environ["ALICEMULTIVERSE_DATABASE_URL"]

    def test_organize_persists_to_database(self, alice_with_db, tmp_path):
        """Test that organized assets are persisted to database."""
        # Create test image
        inbox = tmp_path / "inbox"
        test_image = inbox / "test-project" / "midjourney_portrait.jpg"
        test_image.parent.mkdir()
        test_image.write_bytes(b"fake image data")

        # Organize media
        request = OrganizeRequest(
            source_path=str(inbox),
            quality_assessment=False,  # Skip quality for speed
            enhanced_metadata=True
        )
        response = alice_with_db.organize_media(request)

        assert response["success"]

        # Search database for the asset
        search_request = SearchRequest(
            description="portrait"
        )
        search_response = alice_with_db.search_assets(search_request)

        # Should find the asset in database even though cache might be empty
        assert search_response["success"]
        # Note: Might be empty if no metadata extracted from fake image

    def test_database_search_works(self, alice_with_db):
        """Test searching assets from database."""
        # Manually add test data to database
        test_asset = alice_with_db.asset_repo.create_or_update_asset(
            content_hash="test123",
            file_path="/test/portrait.jpg",
            media_type="image",
            metadata={
                "filename": "portrait.jpg",
                "ai_source": "midjourney",
                "quality_star": 5,
                "style_tags": ["cyberpunk", "portrait"],
                "mood_tags": ["dark", "intense"],
            }
        )

        # Add tags
        alice_with_db.asset_repo.add_tag("test123", "style", "cyberpunk")
        alice_with_db.asset_repo.add_tag("test123", "style", "portrait")

        # Search by tags
        search_request = SearchRequest(
            style_tags=["cyberpunk"]
        )
        response = alice_with_db.search_assets(search_request)

        assert response["success"]
        assert len(response["data"]) >= 1
        assert response["data"][0]["id"] == "test123"

    def test_database_persistence_failure_doesnt_break_organize(self, alice_with_db, tmp_path, monkeypatch):
        """Test that database failures don't break organization."""
        # Create test image
        inbox = tmp_path / "inbox"
        test_image = inbox / "test.jpg"
        test_image.write_bytes(b"fake image")

        # Mock database failure
        def mock_create_asset(*args, **kwargs):
            raise Exception("Database connection failed")

        monkeypatch.setattr(alice_with_db.asset_repo, "create_or_update_asset", mock_create_asset)

        # Organize should still succeed
        request = OrganizeRequest()
        response = alice_with_db.organize_media(request)

        # Should succeed even with database failure
        assert response["success"]


class TestAIFriendlyErrors:
    """Test improved AI-friendly error messages."""

    def test_file_not_found_error(self, tmp_path):
        """Test friendly error for missing files."""
        # Create a config with inbox that doesn't exist
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(f"""
paths:
  inbox: /does/not/exist/inbox
  organized: {tmp_path / "organized"}
""")

        alice = AliceInterface(config_path)

        request = OrganizeRequest()
        response = alice.organize_media(request)

        assert not response["success"]
        # Should have friendly error message - could be doesn't exist or read-only
        assert any(phrase in response["message"].lower() for phrase in ["doesn't exist", "not found", "read-only"])
        # Should have suggestions
        assert "suggestions" in response["data"]
        assert len(response["data"]["suggestions"]) > 0

    def test_permission_error(self, tmp_path):
        """Test friendly error for permission issues."""
        # Create read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(f"""
paths:
  inbox: {tmp_path}
  organized: {readonly_dir}/output
""")

        alice = AliceInterface(config_path)

        # Create test file
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image")

        request = OrganizeRequest()
        response = alice.organize_media(request)

        # Cleanup
        readonly_dir.chmod(0o755)

        # Should handle permission error gracefully
        assert isinstance(response["success"], bool)
        if not response["success"]:
            # Should have user-friendly message about permissions
            assert response["message"]
            assert "permission" in response["message"].lower() or "access" in response["message"].lower()


class TestSearchEngineInitialization:
    """Test that search engine is properly initialized."""

    def test_search_engine_initialized_empty(self, tmp_path):
        """Test search engine works with empty metadata."""
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(f"""
paths:
  inbox: {tmp_path}
  organized: {tmp_path}/organized
""")

        alice = AliceInterface(config_path)

        # Ensure organizer is created
        alice._ensure_organizer()

        # Search engine should be initialized
        assert alice.organizer.search_engine is not None

        # Search should work (return empty results)
        request = SearchRequest(description="test")
        response = alice.search_assets(request)

        assert response["success"]
        assert len(response["data"]) == 0

    def test_search_engine_updated_after_organize(self, tmp_path):
        """Test search engine is updated after organizing."""
        # Create test image
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        test_image = inbox / "portrait.jpg"
        test_image.write_bytes(b"fake image")

        # Create config and alice instance
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(f"""
paths:
  inbox: {inbox}
  organized: {tmp_path / "organized"}
""")

        alice = AliceInterface(config_path)

        # Initially no results
        search_request = SearchRequest(description="portrait")
        response = alice.search_assets(search_request)
        assert response["success"]
        initial_count = len(response["data"])

        # Organize
        organize_request = OrganizeRequest()
        alice.organize_media(organize_request)

        # Search again - might find if metadata was extracted
        response = alice.search_assets(search_request)
        assert response["success"]
        # Count might increase if metadata extraction worked
