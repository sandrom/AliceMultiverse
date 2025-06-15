"""Test for Veo 3 MCP tool integration."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_generate_veo3_video_tool():
    """Test the generate_veo3_video MCP tool."""

    # Mock the imports and provider
    with patch('alicemultiverse.mcp_server.FalProvider') as MockProvider:
        # Mock provider instance
        mock_provider = AsyncMock()
        MockProvider.return_value = mock_provider

        # Mock successful generation
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.file_path = Path("/tmp/veo3_video.mp4")
        mock_result.cost = 2.50
        mock_result.error = None

        mock_provider.generate = AsyncMock(return_value=mock_result)
        mock_provider.initialize = AsyncMock()
        mock_provider.cleanup = AsyncMock()

        # Import the function
        from alicemultiverse.mcp_server import generate_veo3_video

        # Test basic video generation
        result = await generate_veo3_video(
            prompt="A beautiful sunset over the ocean",
            duration=5,
            aspect_ratio="16:9",
            enable_audio=False
        )

        assert result["success"] is True
        assert "Generated Veo 3 video successfully" in result["message"]
        assert result["data"]["duration"] == 5
        assert result["data"]["has_audio"] is False
        assert result["data"]["model"] == "veo-3"
        assert result["data"]["provider"] == "fal.ai"

        # Verify provider was called correctly
        mock_provider.generate.assert_called_once()
        call_args = mock_provider.generate.call_args[0][0]
        assert call_args.model == "veo-3"
        assert call_args.parameters["duration"] == 5
        assert call_args.parameters["enable_audio"] is False


@pytest.mark.asyncio
async def test_veo3_with_audio():
    """Test Veo 3 generation with audio enabled."""

    with patch('alicemultiverse.mcp_server.FalProvider') as MockProvider:
        mock_provider = AsyncMock()
        MockProvider.return_value = mock_provider

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.file_path = Path("/tmp/veo3_audio.mp4")
        mock_result.cost = 3.75  # Higher cost with audio

        mock_provider.generate = AsyncMock(return_value=mock_result)
        mock_provider.initialize = AsyncMock()
        mock_provider.cleanup = AsyncMock()

        from alicemultiverse.mcp_server import generate_veo3_video

        result = await generate_veo3_video(
            prompt="Thunder and lightning with rain sounds",
            duration=5,
            enable_audio=True,
            enable_speech=False
        )

        assert result["success"] is True
        assert result["data"]["has_audio"] is True
        assert result["data"]["cost"] == 3.75
        assert "native audio" in result["data"]["features"]


@pytest.mark.asyncio
async def test_veo3_duration_validation():
    """Test Veo 3 duration validation."""

    from alicemultiverse.mcp_server import generate_veo3_video

    # Test invalid duration (too short)
    result = await generate_veo3_video(
        prompt="Test video",
        duration=3  # Too short
    )

    assert result["success"] is False
    assert "Duration must be between 5 and 8 seconds" in result["message"]

    # Test invalid duration (too long)
    result = await generate_veo3_video(
        prompt="Test video",
        duration=10  # Too long
    )

    assert result["success"] is False
    assert "Duration must be between 5 and 8 seconds" in result["message"]


@pytest.mark.asyncio
async def test_veo3_speech_enables_audio():
    """Test that enabling speech automatically enables audio."""

    with patch('alicemultiverse.mcp_server.FalProvider') as MockProvider:
        mock_provider = AsyncMock()
        MockProvider.return_value = mock_provider

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.file_path = Path("/tmp/veo3_speech.mp4")
        mock_result.cost = 3.75

        mock_provider.generate = AsyncMock(return_value=mock_result)
        mock_provider.initialize = AsyncMock()
        mock_provider.cleanup = AsyncMock()

        from alicemultiverse.mcp_server import generate_veo3_video

        result = await generate_veo3_video(
            prompt='Person saying "Hello world" with lip sync',
            duration=5,
            enable_audio=False,  # Should be overridden
            enable_speech=True
        )

        # Check that audio was enabled
        call_args = mock_provider.generate.call_args[0][0]
        assert call_args.parameters["enable_audio"] is True

        assert result["data"]["has_audio"] is True
        assert result["data"]["has_speech"] is True
        assert "speech with lip sync" in result["data"]["features"]


@pytest.mark.asyncio
async def test_veo3_error_handling():
    """Test Veo 3 error handling."""

    with patch('alicemultiverse.mcp_server.FalProvider') as MockProvider:
        mock_provider = AsyncMock()
        MockProvider.return_value = mock_provider

        # Mock failed generation
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "API rate limit exceeded"

        mock_provider.generate = AsyncMock(return_value=mock_result)
        mock_provider.initialize = AsyncMock()
        mock_provider.cleanup = AsyncMock()

        from alicemultiverse.mcp_server import generate_veo3_video

        result = await generate_veo3_video(
            prompt="Test video",
            duration=5
        )

        assert result["success"] is False
        assert "API rate limit exceeded" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
