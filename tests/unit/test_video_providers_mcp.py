"""Test video providers MCP integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from alicemultiverse.interface.video_providers_mcp import (
    generate_video_runway,
    generate_video_pika,
    generate_video_luma,
    generate_video_minimax,
    generate_video_kling,
    generate_video_hedra,
    compare_video_providers,
    estimate_video_costs
)
from alicemultiverse.providers.types import GenerationResult


@pytest.mark.asyncio
async def test_generate_video_runway():
    """Test Runway video generation."""
    mock_result = GenerationResult(
        success=True,
        file_path=Path("/tmp/test_video.mp4"),
        cost=0.05,
        metadata={"duration": 5}
    )
    
    with patch("alicemultiverse.interface.video_providers_mcp.get_provider") as mock_get:
        mock_provider = Mock()
        mock_provider.generate = AsyncMock(return_value=mock_result)
        mock_get.return_value = mock_provider
        
        result = await generate_video_runway(
            prompt="A serene landscape",
            duration=5,
            output_path="/tmp/test_video.mp4"
        )
        
        assert result["success"] is True
        assert result["provider"] == "runway"
        assert result["video_path"] == "/tmp/test_video.mp4"
        assert result["cost"] == 0.05


@pytest.mark.asyncio
async def test_generate_video_pika():
    """Test Pika video generation."""
    mock_result = GenerationResult(
        success=True,
        file_path=Path("/tmp/test_pika.mp4"),
        cost=0.03,
        metadata={"duration": 3}
    )
    
    with patch("alicemultiverse.interface.video_providers_mcp.get_provider") as mock_get:
        mock_provider = Mock()
        mock_provider.generate = AsyncMock(return_value=mock_result)
        mock_get.return_value = mock_provider
        
        result = await generate_video_pika(
            prompt="A dancing robot",
            duration=3,
            aspect_ratio="16:9"
        )
        
        assert result["success"] is True
        assert result["provider"] == "pika"
        assert result["aspect_ratio"] == "16:9"


@pytest.mark.asyncio
async def test_generate_video_kling():
    """Test Kling video generation."""
    mock_result = GenerationResult(
        success=True,
        file_path=Path("/tmp/test_kling.mp4"),
        cost=0.04,
        metadata={"quality": "professional"}
    )
    
    with patch("alicemultiverse.interface.video_providers_mcp.get_provider") as mock_get:
        mock_provider = Mock()
        mock_provider.generate = AsyncMock(return_value=mock_result)
        mock_get.return_value = mock_provider
        
        result = await generate_video_kling(
            prompt="Cinematic sunset",
            quality="professional",
            motion_strength=0.7
        )
        
        assert result["success"] is True
        assert result["provider"] == "kling"
        assert result["quality"] == "professional"


@pytest.mark.asyncio
async def test_generate_video_hedra():
    """Test Hedra avatar video generation."""
    mock_result = GenerationResult(
        success=True,
        file_path=Path("/tmp/test_hedra.mp4"),
        cost=0.02,
        metadata={"type": "avatar"}
    )
    
    with patch("alicemultiverse.interface.video_providers_mcp.get_provider") as mock_get:
        mock_provider = Mock()
        mock_provider.generate = AsyncMock(return_value=mock_result)
        mock_get.return_value = mock_provider
        
        result = await generate_video_hedra(
            prompt="Hello world",
            audio_input="Hello world",
            aspect_ratio="1:1"
        )
        
        assert result["success"] is True
        assert result["provider"] == "hedra"
        assert result["aspect_ratio"] == "1:1"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in video generation."""
    with patch("alicemultiverse.interface.video_providers_mcp.get_provider") as mock_get:
        mock_get.side_effect = Exception("Provider not available")
        
        result = await generate_video_runway(
            prompt="Test prompt"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert result["provider"] == "runway"


@pytest.mark.asyncio
async def test_compare_video_providers():
    """Test video provider comparison."""
    # Mock successful results for different providers
    mock_results = {
        "runway": GenerationResult(
            success=True,
            file_path=Path("/tmp/runway.mp4"),
            cost=0.05,
            metadata={}
        ),
        "pika": GenerationResult(
            success=True,
            file_path=Path("/tmp/pika.mp4"),
            cost=0.03,
            metadata={}
        )
    }
    
    with patch("alicemultiverse.interface.video_providers_mcp.get_provider") as mock_get:
        def get_provider_mock(name):
            mock_provider = Mock()
            mock_provider.generate = AsyncMock(return_value=mock_results.get(name))
            return mock_provider
        
        mock_get.side_effect = get_provider_mock
        
        result = await compare_video_providers(
            prompt="Test comparison",
            providers=["runway", "pika"],
            compare_cost=True,
            compare_speed=True
        )
        
        assert result["prompt"] == "Test comparison"
        assert result["summary"]["total_providers"] == 2
        assert result["summary"]["successful"] >= 0
        assert "cost_analysis" in result
        assert "speed_analysis" in result


@pytest.mark.asyncio
async def test_estimate_video_costs():
    """Test cost estimation across providers."""
    with patch("alicemultiverse.interface.video_providers_mcp.get_provider") as mock_get:
        mock_provider = Mock()
        mock_provider.estimate_cost = Mock(return_value=0.05)
        mock_provider.get_capabilities = Mock(return_value=Mock(
            models=["model1"],
            features=["feature1"],
            max_resolution="1920x1080"
        ))
        mock_get.return_value = mock_provider
        
        result = await estimate_video_costs(
            prompt="Test prompt",
            providers=["runway", "pika"],
            duration=5
        )
        
        assert result["duration"] == 5
        assert "providers" in result
        assert "summary" in result