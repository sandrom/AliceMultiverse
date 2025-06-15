"""Tests for deduplication MCP tools."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from alicemultiverse.interface.deduplication_mcp import (
    build_similarity_index,
    find_duplicates_advanced,
    find_similar_images,
    get_deduplication_report,
    remove_duplicates,
)


@pytest.mark.asyncio
async def test_find_duplicates_advanced_exact_only():
    """Test finding exact duplicates only."""
    mock_duplicates = {
        "/path/to/master.jpg": [
            {"path": "/path/to/dup1.jpg", "size": 1024000, "similarity": 1.0},
            {"path": "/path/to/dup2.jpg", "size": 1024000, "similarity": 1.0}
        ]
    }

    with patch("alicemultiverse.interface.deduplication_mcp.DuplicateFinder") as mock_finder_class:
        mock_finder = Mock()
        mock_finder_class.return_value = mock_finder
        mock_finder.find_exact_duplicates = AsyncMock(return_value=mock_duplicates)

        result = await find_duplicates_advanced(
            paths=["/test/path"],
            exact_only=True,
            limit=10
        )

        assert result["success"] is True
        assert len(result["data"]["duplicate_groups"]) == 1
        assert result["data"]["summary"]["total_duplicates"] == 2
        assert result["data"]["summary"]["search_type"] == "exact"


@pytest.mark.asyncio
async def test_find_duplicates_advanced_perceptual():
    """Test finding similar images with perceptual hashing."""
    mock_duplicates = {
        "/path/to/master.jpg": [
            {"path": "/path/to/similar1.jpg", "size": 1024000, "similarity": 0.92},
            {"path": "/path/to/similar2.jpg", "size": 1048576, "similarity": 0.88}
        ]
    }

    with patch("alicemultiverse.interface.deduplication_mcp.DuplicateFinder") as mock_finder_class:
        mock_finder = Mock()
        mock_finder_class.return_value = mock_finder
        mock_finder.find_similar_images = AsyncMock(return_value=mock_duplicates)

        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value = Mock(st_size=1024000)

            result = await find_duplicates_advanced(
                paths=["/test/path"],
                exact_only=False,
                similarity_threshold=0.85,
                limit=10
            )

        assert result["success"] is True
        assert result["data"]["summary"]["search_type"] == "perceptual"
        assert result["data"]["summary"]["similarity_threshold"] == 0.85
        assert len(result["data"]["duplicate_groups"]) == 1
        assert result["data"]["duplicate_groups"][0]["duplicates"][0]["similarity"] == 0.92


@pytest.mark.asyncio
async def test_remove_duplicates_dry_run():
    """Test removing duplicates in dry run mode."""
    duplicate_groups = [
        {
            "master": "/path/to/master.jpg",
            "duplicates": [
                {"path": "/path/to/dup1.jpg", "size": 1024000, "similarity": 1.0},
                {"path": "/path/to/dup2.jpg", "size": 1024000, "similarity": 1.0}
            ]
        }
    ]

    with patch("alicemultiverse.interface.deduplication_mcp.DuplicateFinder") as mock_finder_class:
        mock_finder = Mock()
        mock_finder_class.return_value = mock_finder
        mock_finder.remove_duplicates = AsyncMock(
            return_value=(["/path/to/dup1.jpg", "/path/to/dup2.jpg"], 2048000)
        )

        result = await remove_duplicates(
            duplicate_groups=duplicate_groups,
            strategy="keep_organized",
            dry_run=True
        )

        assert result["success"] is True
        assert "Would remove" in result["message"]
        assert result["data"]["dry_run"] is True
        assert result["data"]["space_saved"] == 2048000
        assert len(result["data"]["removed_files"]) == 2


@pytest.mark.asyncio
async def test_remove_duplicates_with_hardlinks():
    """Test removing duplicates using hardlinks."""
    with patch("alicemultiverse.interface.deduplication_mcp.DuplicateFinder") as mock_finder_class:
        mock_finder = Mock()
        mock_finder_class.return_value = mock_finder
        mock_finder.remove_duplicates = AsyncMock(
            return_value=([], 0)  # No actual removal with hardlinks
        )

        # Find duplicates first
        with patch("alicemultiverse.interface.deduplication_mcp.find_duplicates_advanced") as mock_find:
            mock_find.return_value = {
                "success": True,
                "data": {
                    "duplicate_groups": [
                        {
                            "master": "/path/to/master.jpg",
                            "duplicates": [{"path": "/path/to/dup.jpg", "size": 1024000}]
                        }
                    ]
                }
            }

            result = await remove_duplicates(
                strategy="keep_largest",
                use_hardlinks=True,
                dry_run=False
            )

        assert result["success"] is True
        assert result["data"]["strategy"] == "keep_largest"
        mock_finder.remove_duplicates.assert_called_once()


@pytest.mark.asyncio
async def test_build_similarity_index():
    """Test building similarity search index."""
    with patch("alicemultiverse.interface.deduplication_mcp.SimilarityIndex") as mock_index_class:
        mock_index = Mock()
        mock_index_class.return_value = mock_index
        mock_index.index_exists.return_value = False
        mock_index.index_path = Path("/test/index.faiss")
        mock_index.index = Mock(ntotal=100)
        mock_index.add_image = AsyncMock()

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = [
                Path("/test/img1.jpg"),
                Path("/test/img2.jpg"),
                Path("/test/img3.png")
            ]

            result = await build_similarity_index(
                paths=["/test/path"],
                index_type="flat",
                force_rebuild=False
            )

        assert result["success"] is True
        assert result["data"]["index_type"] == "flat"
        assert result["data"]["total_files"] == 3
        assert result["data"]["index_size"] == 100
        assert mock_index.add_image.call_count == 3
        mock_index.save_index.assert_called_once()


@pytest.mark.asyncio
async def test_build_similarity_index_exists():
    """Test building index when it already exists."""
    with patch("alicemultiverse.interface.deduplication_mcp.SimilarityIndex") as mock_index_class:
        mock_index = Mock()
        mock_index_class.return_value = mock_index
        mock_index.index_exists.return_value = True
        mock_index.index_path = Path("/test/index.faiss")

        result = await build_similarity_index(
            paths=["/test/path"],
            force_rebuild=False
        )

        assert result["success"] is True
        assert result["data"]["status"] == "exists"
        assert "force_rebuild=True" in result["data"]["recommendation"]


@pytest.mark.asyncio
async def test_find_similar_images_with_index():
    """Test finding similar images using index."""
    similar_results = [
        {"path": Path("/test/similar1.jpg"), "similarity": 0.95, "distance": 0.05},
        {"path": Path("/test/similar2.jpg"), "similarity": 0.89, "distance": 0.11},
        {"path": Path("/test/similar3.jpg"), "similarity": 0.75, "distance": 0.25}
    ]

    with patch("alicemultiverse.interface.deduplication_mcp.SimilarityIndex") as mock_index_class:
        mock_index = Mock()
        mock_index_class.return_value = mock_index
        mock_index.index_exists.return_value = True
        mock_index.find_similar = AsyncMock(return_value=similar_results)

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            result = await find_similar_images(
                image_path="/test/query.jpg",
                count=10,
                similarity_threshold=0.8,
                use_index=True
            )

        assert result["success"] is True
        assert len(result["data"]["similar_images"]) == 2  # Only those above threshold
        assert result["data"]["similar_images"][0]["similarity"] == 0.95
        assert result["data"]["method"] == "index_search"


@pytest.mark.asyncio
async def test_find_similar_images_direct_search():
    """Test finding similar images without index."""
    with patch("alicemultiverse.interface.deduplication_mcp.SimilarityIndex") as mock_index_class:
        mock_index = Mock()
        mock_index_class.return_value = mock_index
        mock_index.index_exists.return_value = False

        with patch("alicemultiverse.interface.deduplication_mcp.PerceptualHasher") as mock_hasher_class:
            mock_hasher = Mock()
            mock_hasher_class.return_value = mock_hasher
            mock_hasher.compute_all_hashes = AsyncMock()
            mock_hasher.compute_similarity = AsyncMock(side_effect=[0.92, 0.78, 0.85])

            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True

                with patch("pathlib.Path.rglob") as mock_rglob:
                    mock_rglob.return_value = [
                        Path("/test/img1.jpg"),
                        Path("/test/img2.jpg"),
                        Path("/test/img3.jpg")
                    ]

                    result = await find_similar_images(
                        image_path="/test/query.jpg",
                        count=2,
                        similarity_threshold=0.8,
                        use_index=False
                    )

        assert result["success"] is True
        assert len(result["data"]["similar_images"]) == 2
        assert result["data"]["similar_images"][0]["similarity"] == 0.92
        assert result["data"]["method"] == "direct_search"


@pytest.mark.asyncio
async def test_get_deduplication_report():
    """Test generating deduplication report."""
    exact_result = {
        "data": {
            "summary": {
                "total_groups": 5,
                "total_duplicates": 10,
                "total_wasted_space_mb": 50.5
            },
            "duplicate_groups": [{"master": "/test/exact.jpg", "wasted_space": 1024000}]
        }
    }

    similar_result = {
        "data": {
            "summary": {
                "total_groups": 3,
                "total_duplicates": 6,
                "total_wasted_space_mb": 30.2,
                "similarity_threshold": 0.95
            },
            "duplicate_groups": [
                {
                    "master": "/test/similar.jpg",
                    "wasted_space": 2048000,
                    "duplicates": [{"similarity": 0.96}]
                }
            ]
        }
    }

    with patch("alicemultiverse.interface.deduplication_mcp.find_duplicates_advanced") as mock_find:
        mock_find.side_effect = [
            {"success": True, **exact_result},
            {"success": True, **similar_result}
        ]

        result = await get_deduplication_report(
            paths=["/test/path"],
            include_recommendations=True
        )

        assert result["success"] is True
        assert result["data"]["exact_duplicates"]["total_groups"] == 5
        assert result["data"]["similar_images"]["total_groups"] == 3
        assert result["data"]["total_potential_savings_mb"] == 80.7
        assert "recommendations" in result["data"]


@pytest.mark.asyncio
async def test_get_deduplication_report_with_export():
    """Test exporting deduplication report."""
    with patch("alicemultiverse.interface.deduplication_mcp.find_duplicates_advanced") as mock_find:
        mock_find.return_value = {
            "success": True,
            "data": {
                "summary": {
                    "total_groups": 1,
                    "total_duplicates": 2,
                    "total_wasted_space_mb": 10.0
                },
                "duplicate_groups": []
            }
        }

        with patch("builtins.open", create=True) as mock_open:
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                result = await get_deduplication_report(
                    export_path="/test/report.json"
                )

                assert result["success"] is True
                assert result["data"]["export_path"] == "/test/report.json"
                mock_mkdir.assert_called_once()
                mock_open.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in deduplication tools."""
    with patch("alicemultiverse.interface.deduplication_mcp.DuplicateFinder") as mock_finder_class:
        mock_finder_class.side_effect = Exception("Test error")

        result = await find_duplicates_advanced()

        assert result["success"] is False
        assert "Test error" in result["error"]
