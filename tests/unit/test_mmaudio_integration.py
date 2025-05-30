"""Tests for mmaudio integration through fal provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from alicemultiverse.providers.fal_provider import FalProvider
from alicemultiverse.providers.types import GenerationRequest, GenerationType


class TestMMAudioIntegration:
    """Test mmaudio functionality through fal provider."""
    
    @pytest.fixture
    def provider(self):
        """Create fal provider instance."""
        return FalProvider(api_key="test-api-key")
    
    def test_mmaudio_in_models(self, provider):
        """Test that mmaudio is registered in the provider."""
        assert "mmaudio-v2" in provider.MODELS
        assert provider.MODELS["mmaudio-v2"] == "fal-ai/mmaudio-v2"
    
    def test_mmaudio_pricing(self, provider):
        """Test mmaudio pricing configuration."""
        assert "mmaudio-v2" in provider.PRICING
        assert provider.PRICING["mmaudio-v2"] == 0.05  # $0.05 base cost
    
    @pytest.mark.asyncio
    async def test_mmaudio_parameter_preparation(self, provider):
        """Test parameter preparation for mmaudio."""
        request = GenerationRequest(
            prompt="Nature sounds with birds chirping",
            generation_type=GenerationType.AUDIO,
            model="mmaudio-v2",
            parameters={
                "video_url": "https://example.com/nature.mp4",
                "negative_prompt": "music, voices",
                "duration": 10
            }
        )
        
        # Prepare parameters
        params = provider._build_api_params(request, "mmaudio-v2")
        
        # Check defaults are set
        assert params["num_steps"] == 25
        assert params["cfg_strength"] == 4.5
        assert params["mask_away_clip"] is False
        assert params["seed"] is None
        
        # Check provided params are preserved
        assert params["video_url"] == "https://example.com/nature.mp4"
        assert params["negative_prompt"] == "music, voices"
        assert params["duration"] == 10
    
    @pytest.mark.asyncio
    async def test_mmaudio_requires_video_url(self, provider):
        """Test that mmaudio requires a video URL."""
        request = GenerationRequest(
            prompt="Add sound",
            generation_type=GenerationType.AUDIO,
            model="mmaudio-v2",
            parameters={}  # No video_url
        )
        
        with pytest.raises(ValueError, match="mmaudio-v2 requires a video_url"):
            provider._build_api_params(request, "mmaudio-v2")
    
    @pytest.mark.asyncio
    async def test_mmaudio_with_reference_asset(self, provider):
        """Test mmaudio can use reference asset as video URL."""
        request = GenerationRequest(
            prompt="Add dramatic music",
            generation_type=GenerationType.AUDIO,
            model="mmaudio-v2",
            reference_assets=["https://example.com/video.mp4"],
            parameters={}  # No explicit video_url
        )
        
        params = provider._build_api_params(request, "mmaudio-v2")
        assert params["video_url"] == "https://example.com/video.mp4"
    
    @pytest.mark.asyncio
    async def test_mmaudio_cost_estimation(self, provider):
        """Test cost estimation for mmaudio."""
        request = GenerationRequest(
            prompt="Generate audio",
            generation_type=GenerationType.AUDIO,
            model="mmaudio-v2",
            parameters={
                "video_url": "test.mp4",
                "duration": 8  # 8 seconds
            }
        )
        
        cost_estimate = await provider.estimate_cost(request)
        # Currently, FalProvider only returns base cost, not duration-based
        assert cost_estimate.estimated_cost == 0.05
        assert cost_estimate.model == "mmaudio-v2"
        assert cost_estimate.provider == "fal.ai"
    
    @pytest.mark.asyncio
    async def test_mmaudio_generation_flow(self, provider):
        """Test complete mmaudio generation flow."""
        request = GenerationRequest(
            prompt="Epic orchestral music",
            generation_type=GenerationType.AUDIO,
            model="mmaudio-v2",
            parameters={
                "video_url": "https://example.com/epic-scene.mp4",
                "duration": 5,
                "cfg_strength": 6.0
            }
        )
        
        # Mock fal_client
        mock_result = {
            "video": {
                "url": "https://fal.ai/output/video-with-audio.mp4",
                "content_type": "video/mp4",
                "file_name": "output.mp4",
                "file_size": 5242880
            }
        }
        
        with patch.object(provider, '_call_api', return_value=mock_result) as mock_api:
            
            # Mock download
            mock_path = Path("output/video-with-audio.mp4")
            with patch("alicemultiverse.providers.fal_provider.download_file") as mock_download:
                mock_download.return_value = None
                with patch("pathlib.Path.exists", return_value=True):
                    
                    result = await provider.generate(request)
                    
                    # Verify API was called correctly
                    mock_api.assert_called_once()
                    call_args = mock_api.call_args
                    assert call_args[0][0] == "mmaudio-v2"
                    
                    # Check parameters
                    params = call_args[0][1]  # Second argument to _call_api
                    assert params["prompt"] == "Epic orchestral music"
                    assert params["video_url"] == "https://example.com/epic-scene.mp4"
                    assert params["duration"] == 5
                    assert params["cfg_strength"] == 6.0
                    
                    # Verify result
                    assert result.success is True
                    assert result.model == "mmaudio-v2"
                    assert result.provider == "fal.ai"
                    # Note: Current implementation doesn't calculate duration-based cost
                    assert result.cost == 0.05  # Base cost only
    
    def test_mmaudio_with_all_parameters(self, provider):
        """Test mmaudio with all available parameters."""
        request = GenerationRequest(
            prompt="Ambient soundscape",
            generation_type=GenerationType.AUDIO,
            model="mmaudio-v2",
            parameters={
                "video_url": "https://example.com/scene.mp4",
                "negative_prompt": "loud, harsh, music",
                "num_steps": 30,
                "duration": 12,
                "cfg_strength": 3.5,
                "seed": 42,
                "mask_away_clip": True
            }
        )
        
        params = provider._build_api_params(request, "mmaudio-v2")
        
        # All parameters should be preserved
        assert params["video_url"] == "https://example.com/scene.mp4"
        assert params["negative_prompt"] == "loud, harsh, music"
        assert params["num_steps"] == 30
        assert params["duration"] == 12
        assert params["cfg_strength"] == 3.5
        assert params["seed"] == 42
        assert params["mask_away_clip"] is True