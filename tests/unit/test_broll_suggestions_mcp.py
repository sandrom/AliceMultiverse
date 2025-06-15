"""Test b-roll suggestions MCP integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from alicemultiverse.interface.broll_suggestions_mcp import (
    analyze_scene_for_broll,
    auto_insert_broll,
    find_broll_by_criteria,
    generate_broll_shot_list,
    register_broll_tools,
    suggest_broll_for_timeline,
)


@pytest.mark.asyncio
async def test_suggest_broll_for_timeline():
    """Test b-roll suggestions for timeline."""
    timeline_data = {
        "duration": 60,
        "clips": [
            {
                "asset_path": "/path/to/main1.mp4",
                "start_time": 0,
                "duration": 10
            },
            {
                "asset_path": "/path/to/main2.mp4",
                "start_time": 10,
                "duration": 15
            }
        ]
    }

    with patch("alicemultiverse.interface.broll_suggestions_mcp.BRollSuggestionEngine") as mock_engine_class:
        mock_engine = Mock()
        mock_suggestions = {
            "0": [
                Mock(
                    asset_path="/path/to/broll1.mp4",
                    relevance_score=0.9,
                    suggestion_type="contextual",
                    reasoning="Adds context to main footage",
                    placement_hint="cutaway",
                    duration_suggestion=2.0
                )
            ]
        }
        mock_engine.suggest_broll_for_timeline = AsyncMock(return_value=mock_suggestions)
        mock_engine_class.return_value = mock_engine

        result = await suggest_broll_for_timeline(
            timeline_data=timeline_data,
            max_suggestions_per_scene=5
        )

        assert "suggestions" in result
        assert "0" in result["suggestions"]
        assert result["clips_analyzed"] == 2
        assert result["scenes_needing_broll"] == 1


@pytest.mark.asyncio
async def test_auto_insert_broll():
    """Test automatic b-roll insertion."""
    timeline_data = {
        "duration": 30,
        "clips": [
            {
                "asset_path": "/path/to/main.mp4",
                "start_time": 0,
                "duration": 30
            }
        ]
    }

    enhanced_timeline = {
        "duration": 30,
        "clips": [
            {
                "asset_path": "/path/to/main.mp4",
                "start_time": 0,
                "duration": 10
            },
            {
                "asset_path": "/path/to/broll.mp4",
                "start_time": 10,
                "duration": 2,
                "type": "broll"
            },
            {
                "asset_path": "/path/to/main.mp4",
                "start_time": 12,
                "duration": 18
            }
        ],
        "broll_percentage": 0.067
    }

    with patch("alicemultiverse.interface.broll_suggestions_mcp.BRollWorkflow") as mock_workflow_class:
        mock_workflow = Mock()
        mock_workflow.enhance_timeline_with_broll = AsyncMock(return_value=enhanced_timeline)
        mock_workflow_class.return_value = mock_workflow

        result = await auto_insert_broll(
            timeline_data=timeline_data,
            max_broll_percentage=0.3
        )

        assert "timeline" in result
        assert "statistics" in result
        assert result["statistics"]["broll_clips_added"] == 2
        assert result["statistics"]["broll_percentage"] == 0.067


@pytest.mark.asyncio
async def test_analyze_scene_for_broll():
    """Test single scene analysis for b-roll needs."""
    with patch("alicemultiverse.interface.broll_suggestions_mcp.BRollSuggestionEngine") as mock_engine_class:
        mock_engine = Mock()
        mock_scene_info = {
            "type": "dialogue",
            "mood": "dramatic",
            "subject": "conversation",
            "tags": ["dialogue", "indoor", "two-shot"]
        }
        mock_engine._analyze_clip_scene = AsyncMock(return_value=mock_scene_info)
        mock_engine._assess_energy_level = Mock(return_value="medium")
        mock_engine_class.return_value = mock_engine

        result = await analyze_scene_for_broll(
            asset_path="/path/to/scene.mp4",
            start_time=10.0,
            duration=8.0
        )

        assert result["needs_broll"] is True
        assert result["scene_type"] == "dialogue"
        assert result["energy_level"] == "medium"
        assert "Dialogue scenes benefit from cutaways" in result["reasoning"]
        assert "contextual" in result["suggested_broll_types"]


@pytest.mark.asyncio
async def test_find_broll_by_criteria():
    """Test finding b-roll by specific criteria."""
    mock_results = [
        {
            "file_path": "/path/to/broll1.mp4",
            "content_hash": "hash1",
            "tags": ["outdoor", "nature", "peaceful"],
            "score": 0.95,
            "subject": "landscape",
            "mood": "peaceful",
            "scene_type": "wide"
        },
        {
            "file_path": "/path/to/broll2.mp4",
            "content_hash": "hash2",
            "tags": ["outdoor", "nature", "serene"],
            "score": 0.90,
            "subject": "forest",
            "mood": "peaceful",
            "scene_type": "medium"
        }
    ]

    with patch("alicemultiverse.interface.broll_suggestions_mcp.UnifiedDuckDBStorage") as mock_db_class:
        mock_db = Mock()
        mock_db.search_assets = Mock(return_value=mock_results)
        mock_db_class.return_value = mock_db

        result = await find_broll_by_criteria(
            subject="nature",
            mood="peaceful",
            location="outdoor",
            limit=10
        )

        assert result["count"] == 2
        assert result["criteria"]["subject"] == "nature"
        assert result["criteria"]["mood"] == "peaceful"
        assert len(result["results"]) == 2
        assert result["results"][0]["asset_path"] == "/path/to/broll1.mp4"


@pytest.mark.asyncio
async def test_generate_broll_shot_list():
    """Test b-roll shot list generation."""
    timeline_data = {
        "duration": 120,
        "clips": [
            {
                "asset_path": "/path/to/interview.mp4",
                "start_time": 0,
                "duration": 60
            },
            {
                "asset_path": "/path/to/main.mp4",
                "start_time": 60,
                "duration": 60
            }
        ]
    }

    with patch("alicemultiverse.interface.broll_suggestions_mcp.BRollSuggestionEngine") as mock_engine_class:
        mock_engine = Mock()
        mock_suggestions = {
            "0": [
                Mock(
                    asset_path="/path/to/context1.mp4",
                    relevance_score=0.9,
                    suggestion_type="contextual",
                    reasoning="Provides visual context",
                    placement_hint="cutaway",
                    duration_suggestion=2.5,
                    tags=["office", "workspace", "professional"]
                )
            ],
            "1": [
                Mock(
                    asset_path="/path/to/mood1.mp4",
                    relevance_score=0.85,
                    suggestion_type="mood",
                    reasoning="Enhances emotional tone",
                    placement_hint="overlay",
                    duration_suggestion=3.0,
                    tags=["nature", "calm", "transition"]
                )
            ]
        }
        mock_engine.suggest_broll_for_timeline = AsyncMock(return_value=mock_suggestions)
        mock_engine_class.return_value = mock_engine

        result = await generate_broll_shot_list(
            timeline_data=timeline_data,
            style="documentary",
            include_descriptions=True
        )

        assert result["project_style"] == "documentary"
        assert result["timeline_duration"] == 120
        assert len(result["shots"]) == 2
        assert result["shots"][0]["shot_number"] == "B1.1"
        assert result["shots"][0]["type"] == "contextual"
        assert "description" in result["shots"][0]
        assert result["summary"]["total_shots"] == 2


def test_register_broll_tools():
    """Test tool registration function."""
    mock_server = Mock()
    mock_server.tool = Mock(return_value=lambda f: f)

    # Should not raise any exceptions
    register_broll_tools(mock_server)

    # Verify all tools were registered
    assert mock_server.tool.call_count == 5  # 5 b-roll tools
