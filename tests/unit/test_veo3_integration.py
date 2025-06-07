"""Tests for Google Veo 3 integration."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from alicemultiverse.providers.fal_provider import FalProvider
from alicemultiverse.providers.google_ai_provider import GoogleAIProvider, GoogleAIBackend
from alicemultiverse.providers.types import GenerationRequest, GenerationType


class TestVeo3FalProvider:
    """Test Veo 3 integration in fal.ai provider."""
    
    @pytest.fixture
    def provider(self):
        """Create fal provider instance."""
        return FalProvider(api_key="test-key")
    
    def test_veo3_in_models(self, provider):
        """Test that Veo 3 models are registered."""
        assert "veo-3" in provider.MODELS
        assert "veo3" in provider.MODELS
        assert provider.MODELS["veo-3"] == "fal-ai/veo3"
        assert provider.MODELS["veo3"] == "fal-ai/veo3"
    
    def test_veo3_pricing(self, provider):
        """Test Veo 3 pricing configuration."""
        assert "veo-3" in provider.PRICING
        assert provider.PRICING["veo-3"] == 0.50  # $0.50 per second
        assert provider.PRICING["veo3"] == 0.50
    
    def test_veo3_capabilities(self, provider):
        """Test that Veo 3 capabilities are included."""
        caps = provider.capabilities
        assert "native_audio_generation" in caps.features
        assert "speech_capabilities" in caps.features
        assert "lip_sync" in caps.features
    
    def test_veo3_parameter_preparation(self, provider):
        """Test Veo 3 specific parameter preparation."""
        request = GenerationRequest(
            prompt="Test video",
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            parameters={
                "duration": 8,
                "enable_audio": True,
                "aspect_ratio": "16:9"
            }
        )
        
        # Test internal method that builds API params
        params = provider._build_api_params(request, "veo-3")
        
        assert params["prompt"] == "Test video"
        assert params["duration"] == 8
        assert params["enable_audio"] is True
        assert params["aspect_ratio"] == "16:9"
    
    @pytest.mark.asyncio
    async def test_veo3_cost_with_audio(self, provider):
        """Test cost calculation for Veo 3 with audio."""
        # Note: In real implementation, we'd need to handle audio pricing
        request = GenerationRequest(
            prompt="Test",
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            parameters={"enable_audio": True, "duration": 1}
        )
        
        cost_estimate = await provider.estimate_cost(request)
        assert cost_estimate.estimated_cost == 0.50  # Base cost per second


class TestVeo3GoogleAIProvider:
    """Test Veo 3 integration in Google AI provider."""
    
    @pytest.fixture
    def provider(self):
        """Create Google AI provider instance."""
        return GoogleAIProvider(
            api_key="test-key",
            backend=GoogleAIBackend.VERTEX,
            project_id="test-project"
        )
    
    def test_veo3_in_models(self, provider):
        """Test that Veo 3 models are registered."""
        assert "veo-3" in provider.MODELS
        assert "veo-3.0" in provider.MODELS  
        assert provider.MODELS["veo-3"] == "veo-3.0-generate-preview"
        assert provider.MODELS["veo"] == "veo-3.0-generate-preview"  # Default to latest
    
    def test_veo3_pricing(self, provider):
        """Test Veo 3 pricing configuration."""
        assert provider.PRICING["veo-3.0-generate-preview"] == 0.35
    
    def test_veo3_aspect_ratios(self, provider):
        """Test Veo 3 supports additional aspect ratios."""
        assert "1:1" in provider.ASPECT_RATIOS["veo"]
        assert "16:9" in provider.ASPECT_RATIOS["veo"]
        assert "9:16" in provider.ASPECT_RATIOS["veo"]
    
    def test_veo3_capabilities(self, provider):
        """Test that Veo 3 capabilities are included."""
        caps = provider.capabilities
        assert "native_sound_generation" in caps.features
        assert "prompt_rewriting" in caps.features
        assert "speech_generation" in caps.features
    
    @pytest.mark.asyncio
    async def test_veo3_request_preparation(self, provider):
        """Test Veo 3 specific request preparation."""
        request = GenerationRequest(
            prompt="Test video with sound",
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            parameters={
                "enable_sound": True,
                "enable_prompt_rewriting": False,
                "number_of_videos": 2,
                "aspect_ratio": "1:1"
            }
        )
        
        body = await provider._prepare_veo_request(request)
        
        # Test Vertex AI format
        assert body["instances"][0]["prompt"] == "Test video with sound"
        assert body["parameters"]["enableSound"] is True
        assert body["parameters"]["enablePromptRewriting"] is False
        assert body["parameters"]["sampleCount"] == 2
        assert body["parameters"]["aspectRatio"] == "1:1"
    
    @pytest.mark.asyncio
    async def test_veo3_request_defaults(self, provider):
        """Test Veo 3 default parameters."""
        request = GenerationRequest(
            prompt="Test video",
            model="veo-3",
            generation_type=GenerationType.VIDEO
        )
        
        body = await provider._prepare_veo_request(request)
        
        # Check defaults
        assert body["parameters"]["enableSound"] is False
        assert body["parameters"]["enablePromptRewriting"] is True
        assert body["parameters"]["sampleCount"] == 1


class TestVeo3EndToEnd:
    """End-to-end tests for Veo 3 generation."""
    
    @pytest.mark.asyncio
    @patch('alicemultiverse.providers.fal_provider.download_file')
    @patch('aiohttp.ClientSession.post')
    async def test_veo3_generation_fal(self, mock_post, mock_download):
        """Test end-to-end Veo 3 generation on fal.ai."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "video": {
                "url": "https://example.com/video.mp4"
            },
            "duration": 5,
            "has_audio": True
        })
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Mock download
        mock_download.return_value = None
        
        provider = FalProvider(api_key="test-key")
        
        request = GenerationRequest(
            prompt="A beautiful sunset over the ocean with sound",
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            output_path=Path("/tmp/test"),
            parameters={
                "duration": 5,
                "enable_audio": True,
                "aspect_ratio": "16:9"
            }
        )
        
        result = await provider.generate(request)
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://fal.run/fal-ai/veo3"
        
        # Check request body
        request_body = call_args[1]["json"]
        assert request_body["prompt"] == "A beautiful sunset over the ocean with sound"
        assert request_body["duration"] == 5
        assert request_body["enable_audio"] is True
        assert request_body["aspect_ratio"] == "16:9"
    
    def test_veo3_parameter_validation(self):
        """Test parameter validation for Veo 3."""
        provider = FalProvider(api_key="test-key")
        
        # Test with invalid aspect ratio (should still prepare, validation elsewhere)
        request = GenerationRequest(
            prompt="Test",
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            parameters={
                "duration": 10,  # Over typical limit
                "number_of_videos": 5,  # Over Veo 3 limit
            }
        )
        
        params = provider._build_api_params(request, "veo-3")
        
        # Parameters are passed through, validation happens at API level
        assert params["duration"] == 10
        assert params["number_of_videos"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])