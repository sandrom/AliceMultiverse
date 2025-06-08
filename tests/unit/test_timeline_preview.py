"""Tests for timeline preview functionality."""

import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from alicemultiverse.interface.timeline_preview import (
    PreviewSession,
    TimelinePreviewServer,
)
from alicemultiverse.interface.timeline_preview_mcp import (
    create_test_timeline,
    export_preview_timeline,
    preview_timeline,
    update_preview_timeline,
)
from alicemultiverse.workflows.video_export import Timeline, TimelineClip


class TestPreviewSession:
    """Test PreviewSession class."""
    
    def test_session_creation(self):
        """Test creating a preview session."""
        timeline = Timeline(
            name="Test Timeline",
            duration=10.0,
            clips=[
                TimelineClip(
                    asset_path=Path("/test/clip1.jpg"),
                    start_time=0.0,
                    duration=5.0
                )
            ]
        )
        
        session = PreviewSession(timeline)
        
        assert session.id is not None
        assert session.timeline == timeline
        assert session.version == 1
        assert len(session.undo_stack) == 0
        assert len(session.redo_stack) == 0
    
    def test_undo_redo(self):
        """Test undo/redo functionality."""
        timeline1 = Timeline(name="Timeline 1", duration=10.0)
        timeline2 = Timeline(name="Timeline 2", duration=20.0)
        timeline3 = Timeline(name="Timeline 3", duration=30.0)
        
        session = PreviewSession(timeline1)
        
        # Make changes
        session.update_timeline(timeline2)
        assert session.timeline.name == "Timeline 2"
        assert session.version == 2
        
        session.update_timeline(timeline3)
        assert session.timeline.name == "Timeline 3"
        assert session.version == 3
        
        # Undo
        assert session.undo() is True
        assert session.timeline.name == "Timeline 2"
        
        assert session.undo() is True
        assert session.timeline.name == "Timeline 1"
        
        assert session.undo() is False  # Nothing to undo
        
        # Redo
        assert session.redo() is True
        assert session.timeline.name == "Timeline 2"
        
        assert session.redo() is True
        assert session.timeline.name == "Timeline 3"
        
        assert session.redo() is False  # Nothing to redo
        
        # New change clears redo stack
        session.update_timeline(Timeline(name="Timeline 4", duration=40.0))
        assert len(session.redo_stack) == 0


class TestTimelinePreviewServer:
    """Test TimelinePreviewServer class."""
    
    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        return TimelinePreviewServer()
    
    def test_server_creation(self, server):
        """Test server initialization."""
        assert server.app is not None
        assert server.sessions == {}
        assert server.static_dir is not None
    
    def test_timeline_to_dict(self, server):
        """Test timeline serialization."""
        timeline = Timeline(
            name="Test",
            duration=10.0,
            clips=[
                TimelineClip(
                    asset_path=Path("/test/clip.jpg"),
                    start_time=0.0,
                    duration=5.0
                )
            ]
        )
        
        result = server._timeline_to_dict(timeline)
        
        assert result["name"] == "Test"
        assert result["duration"] == 10.0
        assert len(result["clips"]) == 1
        assert result["clips"][0]["asset_path"] == "/test/clip.jpg"
    
    def test_apply_reorder_operation(self, server):
        """Test reordering clips."""
        timeline = Timeline(
            name="Test",
            duration=15.0,
            clips=[
                TimelineClip(
                    asset_path=Path("/test/clip1.jpg"),
                    start_time=0.0,
                    duration=5.0
                ),
                TimelineClip(
                    asset_path=Path("/test/clip2.jpg"),
                    start_time=5.0,
                    duration=5.0
                ),
                TimelineClip(
                    asset_path=Path("/test/clip3.jpg"),
                    start_time=10.0,
                    duration=5.0
                ),
            ]
        )
        
        # Reorder: move clip at index 0 to index 2
        new_timeline = server._apply_timeline_operation(
            timeline,
            "reorder",
            [{"old_index": 0, "new_index": 2}]
        )
        
        # Verify order changed
        assert new_timeline.clips[0].asset_path.name == "clip2.jpg"
        assert new_timeline.clips[1].asset_path.name == "clip3.jpg"
        assert new_timeline.clips[2].asset_path.name == "clip1.jpg"
    
    def test_apply_trim_operation(self, server):
        """Test trimming clips."""
        timeline = Timeline(
            name="Test",
            duration=10.0,
            clips=[
                TimelineClip(
                    asset_path=Path("/test/clip1.jpg"),
                    start_time=0.0,
                    duration=10.0,
                    in_point=0.0,
                    out_point=10.0
                )
            ]
        )
        
        # Trim clip
        new_timeline = server._apply_timeline_operation(
            timeline,
            "trim",
            [{"index": 0, "in_point": 2.0, "out_point": 8.0, "duration": 6.0}]
        )
        
        clip = new_timeline.clips[0]
        assert clip.in_point == 2.0
        assert clip.out_point == 8.0
        assert clip.duration == 6.0
    
    def test_apply_transition_operation(self, server):
        """Test adding transitions."""
        timeline = Timeline(
            name="Test",
            duration=10.0,
            clips=[
                TimelineClip(
                    asset_path=Path("/test/clip1.jpg"),
                    start_time=0.0,
                    duration=5.0
                ),
                TimelineClip(
                    asset_path=Path("/test/clip2.jpg"),
                    start_time=5.0,
                    duration=5.0
                )
            ]
        )
        
        # Add transitions
        new_timeline = server._apply_timeline_operation(
            timeline,
            "add_transition",
            [
                {
                    "index": 0,
                    "transition_out": "dissolve",
                    "transition_out_duration": 1.0
                },
                {
                    "index": 1,
                    "transition_in": "dissolve",
                    "transition_in_duration": 1.0
                }
            ]
        )
        
        assert new_timeline.clips[0].transition_out == "dissolve"
        assert new_timeline.clips[0].transition_out_duration == 1.0
        assert new_timeline.clips[1].transition_in == "dissolve"
        assert new_timeline.clips[1].transition_in_duration == 1.0


@pytest.mark.asyncio
class TestTimelinePreviewMCP:
    """Test MCP tool functions."""
    
    async def test_create_test_timeline(self):
        """Test creating a test timeline."""
        timeline = await create_test_timeline()
        
        assert timeline.name == "Test Timeline"
        assert timeline.duration == 7.5
        assert len(timeline.clips) == 3
        assert len(timeline.markers) == 3
    
    @patch('alicemultiverse.interface.timeline_preview_mcp.httpx.AsyncClient')
    async def test_preview_timeline(self, mock_client):
        """Test previewing a timeline."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "session_id": "test-session-123",
            "timeline": {}
        }
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test timeline data
        timeline_data = {
            "name": "Test Timeline",
            "duration": 10.0,
            "clips": []
        }
        
        result = await preview_timeline(timeline_data, auto_open=False)
        
        assert result["success"] is True
        assert result["session_id"] == "test-session-123"
        assert "preview_url" in result
        assert "127.0.0.1:8001" in result["preview_url"]
    
    @patch('alicemultiverse.interface.timeline_preview_mcp.httpx.AsyncClient')
    async def test_update_preview_timeline(self, mock_client):
        """Test updating a timeline in preview."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "timeline": {},
            "version": 2
        }
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        result = await update_preview_timeline(
            "test-session-123",
            "reorder",
            [{"old_index": 0, "new_index": 2}]
        )
        
        assert result["success"] is True
        assert result["version"] == 2
    
    @patch('alicemultiverse.interface.timeline_preview_mcp.httpx.AsyncClient')
    async def test_export_preview_timeline(self, mock_client, tmp_path):
        """Test exporting a timeline from preview."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Test Timeline",
            "duration": 10.0,
            "clips": []
        }
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test export to file
        output_path = tmp_path / "timeline.json"
        result = await export_preview_timeline(
            "test-session-123",
            format="json",
            output_path=output_path
        )
        
        assert result["success"] is True
        assert result["format"] == "json"
        assert output_path.exists()
        
        # Verify file content
        with open(output_path) as f:
            data = json.load(f)
            assert data["name"] == "Test Timeline"
            assert data["duration"] == 10.0


# Integration test that requires the server to be running
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_preview_workflow():
    """Test the full preview workflow with a running server."""
    from alicemultiverse.interface.timeline_preview_mcp import (
        start_preview_server,
        stop_preview_server,
        get_preview_status,
    )
    
    # Start server
    assert await start_preview_server(port=8002) is True
    
    # Check status
    status = await get_preview_status(port=8002)
    assert status["running"] is True
    assert status["port"] == 8002
    
    # Create and preview timeline
    timeline = await create_test_timeline()
    timeline_dict = {
        "name": timeline.name,
        "duration": timeline.duration,
        "clips": [
            {
                "asset_path": str(clip.asset_path),
                "start_time": clip.start_time,
                "duration": clip.duration,
            }
            for clip in timeline.clips
        ],
    }
    
    result = await preview_timeline(timeline_dict, auto_open=False, port=8002)
    assert result["success"] is True
    session_id = result["session_id"]
    
    # Update timeline
    update_result = await update_preview_timeline(
        session_id,
        "reorder",
        [{"old_index": 0, "new_index": 1}],
        port=8002
    )
    assert update_result["success"] is True
    
    # Export timeline
    export_result = await export_preview_timeline(
        session_id,
        format="json",
        port=8002
    )
    assert export_result["success"] is True
    
    # Stop server
    assert await stop_preview_server() is True