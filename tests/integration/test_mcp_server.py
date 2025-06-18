"""Integration tests for MCP server and AI workflows."""

from unittest.mock import patch

import pytest

from alicemultiverse.interface import AliceInterface
from alicemultiverse.interface.models import (
    OrganizeRequest,
    SearchRequest,
)


class TestMCPServerIntegration:
    """Test the MCP server integration with Alice interface."""

    @pytest.fixture
    def alice_interface(self, tmp_path):
        """Create Alice interface with test configuration."""
        # Create test directories
        inbox = tmp_path / "inbox"
        organized = tmp_path / "organized"
        inbox.mkdir()
        organized.mkdir()

        # Create test config
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(f"""
paths:
  inbox: {inbox}
  organized: {organized}

processing:
  quality: true

enhanced_metadata: true
""")

        return AliceInterface(config_path)

    @pytest.fixture
    def mock_mcp_server(self):
        """Create a mock MCP server context."""
        with patch('alicemultiverse.mcp_server.MCP_AVAILABLE', True):
            with patch('alicemultiverse.mcp_server.alice') as mock_alice:
                yield mock_alice

    async def test_search_assets_workflow(self, mock_mcp_server):
        """Test AI searching for assets with natural language."""
        # Mock response
        mock_response = {
            "success": True,
            "message": "Found 5 matching assets",
            "data": {
                "results": [
                    {
                        "id": "abc123",
                        "path": "image1.jpg",
                        "tags": ["cyberpunk", "portrait", "neon"],
                        "quality_stars": 5,
                    }
                ],
                "total": 1,
            },
            "error": None
        }
        mock_mcp_server.search_assets.return_value = mock_response

        # Import and call the MCP function
        from alicemultiverse.mcp_server import search_assets

        # Simulate AI assistant calling the function
        result = await search_assets(
            description="dark moody portraits with neon lighting",
            style_tags=["cyberpunk", "noir"],
            min_quality_stars=4
        )

        # Verify the call
        assert mock_mcp_server.search_assets.called
        call_args = mock_mcp_server.search_assets.call_args[0][0]
        # SearchRequest is a TypedDict, so check it's a dict with expected keys
        assert isinstance(call_args, dict)
        assert call_args["description"] == "dark moody portraits with neon lighting"
        assert call_args["style_tags"] == ["cyberpunk", "noir"]
        assert call_args["min_quality_stars"] == 4

        # Verify response format for AI
        assert result["success"] is True
        assert "results" in result["data"]

    async def test_organize_media_workflow(self, mock_mcp_server):
        """Test AI organizing media with quality assessment."""
        # Mock response
        mock_response = {
            "success": True,
            "message": "Organized 10 files",
            "data": {
                "processed": 10,
                "by_source": {"midjourney": 5, "stable-diffusion": 5},
                "by_quality": {"5-star": 2, "4-star": 5, "3-star": 3}
            },
            "error": None
        }
        mock_mcp_server.organize_media.return_value = mock_response

        from alicemultiverse.mcp_server import organize_media

        # Simulate AI organizing with quality
        result = await organize_media(
            quality_assessment=True,
            pipeline="standard"
        )

        # Verify the call
        assert mock_mcp_server.organize_media.called
        call_args = mock_mcp_server.organize_media.call_args[0][0]
        # OrganizeRequest is a TypedDict
        assert isinstance(call_args, dict)
        assert call_args["quality_assessment"] is True
        assert call_args["pipeline"] == "standard"

        # Verify AI-friendly response
        assert result["success"] is True
        assert result["data"]["processed"] == 10

    async def test_tag_assets_workflow(self, mock_mcp_server):
        """Test AI tagging assets with semantic tags."""
        # Mock response
        mock_response = {
            "success": True,
            "message": "Tagged 3 assets",
            "data": {"tagged": 3},
            "error": None
        }
        mock_mcp_server.tag_assets.return_value = mock_response

        from alicemultiverse.mcp_server import tag_assets

        # Simulate AI tagging
        result = await tag_assets(
            asset_ids=["id1", "id2", "id3"],
            style_tags=["minimalist", "abstract"],
            mood_tags=["serene", "contemplative"],
            role="hero"
        )

        # Verify the call
        assert mock_mcp_server.tag_assets.called
        call_args = mock_mcp_server.tag_assets.call_args[0][0]
        # TagRequest is a TypedDict
        assert isinstance(call_args, dict)
        assert call_args["asset_ids"] == ["id1", "id2", "id3"]
        assert call_args["style_tags"] == ["minimalist", "abstract"]
        assert call_args["role"] == "hero"

    async def test_error_handling(self, mock_mcp_server):
        """Test AI-friendly error handling."""
        # Mock an error
        mock_mcp_server.search_assets.side_effect = Exception("Database connection failed")

        from alicemultiverse.mcp_server import search_assets

        # Should return AI-friendly error
        result = await search_assets(description="test search")

        assert result["success"] is False
        assert "error" in result
        assert "Search failed" in result["message"]
        # Error should be understandable by AI
        assert "Database connection failed" in result["error"]

    async def test_get_stats_workflow(self, mock_mcp_server):
        """Test AI getting collection statistics."""
        # Mock response
        mock_response = {
            "success": True,
            "message": "Collection statistics retrieved",
            "data": {
                "total_assets": 150,
                "by_source": {"midjourney": 80, "dalle": 70},
                "by_quality": {"5-star": 30, "4-star": 60, "3-star": 60},
                "by_project": {"portraits": 50, "landscapes": 100}
            },
            "error": None
        }
        mock_mcp_server.get_stats.return_value = mock_response

        from alicemultiverse.mcp_server import get_organization_stats

        # Simulate AI checking stats
        result = await get_organization_stats()

        # Verify response is AI-friendly
        assert result["success"] is True
        assert result["data"]["total_assets"] == 150
        assert "by_source" in result["data"]
        assert "by_quality" in result["data"]


class TestAliceInterfaceIntegration:
    """Test the actual Alice interface methods."""

    @pytest.fixture
    def alice(self, tmp_path):
        """Create real Alice interface."""
        inbox = tmp_path / "inbox"
        organized = tmp_path / "organized"
        inbox.mkdir()
        organized.mkdir()

        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(f"""
paths:
  inbox: {inbox}
  organized: {organized}
""")

        return AliceInterface(config_path)

    def test_search_assets_real(self, alice):
        """Test real search functionality."""
        # Create test metadata in cache using the internal unified cache
        test_metadata = {
            "file_hash": "test123",
            "filename": "portrait.jpg",
            "ai_source": "midjourney",
            "quality_star": 5,
            "tags": ["portrait", "cyberpunk", "neon"],
            "style_tags": ["cyberpunk", "futuristic"],
            "mood_tags": ["dark", "moody"],
            "project": "test-project",
        }
        # Access the internal unified cache directly
        alice.organizer.metadata_cache._unified.metadata_index["test123"] = test_metadata

        # Update the search engine with new metadata
        alice.organizer._update_search_engine()

        # Search for assets
        request = SearchRequest(
            description="cyberpunk portrait",
            style_tags=["cyberpunk"],
            min_quality_stars=4
        )
        response = alice.search_assets(request)

        assert response["success"]
        assert len(response["data"]) > 0
        assert response["data"][0]["id"] == "test123"

    def test_get_asset_info_real(self, alice):
        """Test getting asset information."""
        # Create test metadata
        test_metadata = {
            "file_hash": "info123",
            "filename": "test.jpg",
            "ai_source": "dalle",
            "quality_star": 4,
            "prompt": "A beautiful landscape",
            "tags": ["landscape", "nature"],
            "brisque_score": 25.5,
        }
        alice.organizer.metadata_cache._unified.metadata_index["info123"] = test_metadata

        # Get asset info
        response = alice.get_asset_info("info123")

        assert response["success"]
        assert response["data"]["asset"]["id"] == "info123"
        assert response["data"]["asset"]["source"] == "dalle"
        assert response["data"]["asset"]["quality_stars"] == 4

    def test_assess_quality_real(self, alice):
        """Test quality assessment retrieval."""
        # Create test metadata with quality info
        test_metadata = {
            "file_hash": "quality123",
            "filename": "assessed.jpg",
            "brisque_score": 30.0,
            "quality_star": 4,
            "pipeline_scores": {
                "brisque": 0.7,
                "sightengine": 0.8
            },
            "quality_issues": []
        }
        alice.organizer.metadata_cache._unified.metadata_index["quality123"] = test_metadata

        # Assess quality
        response = alice.assess_quality(["quality123"], "standard")

        assert response["success"]
        assert len(response["data"]["quality_results"]) == 1
        result = response["data"]["quality_results"][0]
        assert result["asset_id"] == "quality123"
        assert result["brisque_score"] == 30.0
        assert result["quality_star"] == 4

    def test_get_stats_real(self, alice):
        """Test statistics generation."""
        # Create multiple test metadata entries
        for i in range(5):
            alice.organizer.metadata_cache._unified.metadata_index[f"stat{i}"] = {
                "file_hash": f"stat{i}",
                "ai_source": "midjourney" if i < 3 else "dalle",
                "quality_star": 5 - i,
                "project": "test-project",
                "date_taken": "2024-01-15T10:00:00",
                "media_type": "image",
            }

        # Get stats
        response = alice.get_stats()

        assert response["success"]
        stats = response["data"]
        assert stats["total_assets"] == 5
        assert stats["by_source"]["midjourney"] == 3
        assert stats["by_source"]["dalle"] == 2
        assert stats["by_quality"]["5-star"] == 1
        assert stats["media_types"]["image"] == 5


class TestAIWorkflowScenarios:
    """Test complete AI workflow scenarios."""

    @pytest.fixture
    def alice(self, tmp_path):
        """Create Alice interface for scenarios."""
        inbox = tmp_path / "inbox"
        organized = tmp_path / "organized"
        inbox.mkdir()
        organized.mkdir()

        # Create test image
        test_image = inbox / "test-project" / "midjourney_portrait.jpg"
        test_image.parent.mkdir()
        test_image.write_text("fake image data")

        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(f"""
paths:
  inbox: {inbox}
  organized: {organized}
""")

        return AliceInterface(config_path)

    def test_ai_conversation_workflow(self, alice):
        """Test a complete AI conversation workflow."""
        # Scenario: AI helps user organize and find best images

        # 1. AI organizes media
        organize_request = OrganizeRequest(
            quality_assessment=True,
            pipeline="basic"
        )
        organize_response = alice.organize_media(organize_request)
        assert organize_response["success"]

        # 2. AI searches for specific content
        search_request = SearchRequest(
            description="portrait images",
            min_quality_stars=3
        )
        search_response = alice.search_assets(search_request)
        # Will be empty since we didn't process real images
        assert search_response["success"]

        # 3. AI gets statistics
        stats_response = alice.get_stats()
        assert stats_response["success"]
        assert isinstance(stats_response["data"]["total_assets"], int)

    def test_ai_error_recovery(self, alice):
        """Test AI handling errors gracefully."""
        # Try to get info for non-existent asset
        response = alice.get_asset_info("nonexistent")

        assert not response["success"]
        assert "not found" in response["message"].lower()
        assert response["error"] is not None

        # AI should be able to understand and explain the error to user
        assert "Asset not found" in response["error"]
