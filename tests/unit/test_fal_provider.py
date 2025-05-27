"""Unit tests for fal.ai provider."""

from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest

from alicemultiverse.providers import GenerationRequest, GenerationType, get_provider
from alicemultiverse.providers.base import GenerationError, RateLimitError, AuthenticationError
from alicemultiverse.providers.fal_provider import FalProvider


class TestFalProvider:
    """Test fal.ai provider functionality."""
    
    def test_provider_initialization(self):
        """Test provider initialization."""
        # Without API key
        provider = FalProvider()
        assert provider.name == "fal.ai"
        assert provider.api_key is None
        
        # With API key
        provider = FalProvider(api_key="test-key")
        assert provider.api_key == "test-key"
    
    def test_provider_capabilities(self):
        """Test provider capabilities."""
        provider = FalProvider()
        caps = provider.capabilities
        
        # Check generation types
        assert GenerationType.IMAGE in caps.generation_types
        assert GenerationType.VIDEO in caps.generation_types
        
        # Check models
        assert "flux-pro" in caps.models
        assert "flux-dev" in caps.models
        assert "flux-schnell" in caps.models
        assert "kling-v1-text" in caps.models
        assert "kling-v2-text" in caps.models
        assert "kling-elements" in caps.models
        assert "kling-lipsync" in caps.models
        
        # Check pricing
        assert caps.pricing["flux-pro"] == 0.05
        assert caps.pricing["kling-v2-text"] == 0.20
        assert caps.pricing["kling-lipsync"] == 0.20
        
        # Check features
        assert "video_generation" in caps.features
        assert "upscaling" in caps.features
    
    def test_all_models_have_pricing(self):
        """Test that all models have pricing defined."""
        provider = FalProvider()
        for model in provider.MODELS:
            assert model in provider.PRICING, f"Model {model} has no pricing"
    
    def test_build_api_params_flux(self):
        """Test API parameter building for FLUX models."""
        provider = FalProvider()
        
        request = GenerationRequest(
            prompt="Test prompt",
            generation_type=GenerationType.IMAGE,
            model="flux-pro",
            parameters={"width": 1024, "height": 768, "custom_param": "value"}
        )
        
        params = provider._build_api_params(request, "flux-pro")
        
        assert params["prompt"] == "Test prompt"
        assert params["num_inference_steps"] == 50  # Default for non-schnell
        assert params["guidance_scale"] == 3.5
        assert params["num_images"] == 1
        assert params["enable_safety_checker"] is True
        assert params["custom_param"] == "value"
        assert params["image_size"]["width"] == 1024
        assert params["image_size"]["height"] == 768
    
    def test_build_api_params_kling(self):
        """Test API parameter building for Kling models."""
        provider = FalProvider()
        
        request = GenerationRequest(
            prompt="Test video prompt",
            generation_type=GenerationType.VIDEO,
            model="kling-v2-text",
            parameters={"aspect_ratio": "9:16"}
        )
        
        params = provider._build_api_params(request, "kling-v2-text")
        
        assert params["prompt"] == "Test video prompt"
        assert params["duration"] == "5"  # Default
        assert params["aspect_ratio"] == "9:16"  # Overridden
        assert params["cfg_scale"] == 0.5
        assert "num_images" not in params  # Should be removed for video
        assert "image_size" not in params  # Should be removed for video
    
    @pytest.mark.asyncio
    async def test_generate_validation(self):
        """Test request validation."""
        provider = FalProvider()
        
        # Test with invalid model
        request = GenerationRequest(
            prompt="Test",
            model="invalid-model",
            generation_type=GenerationType.IMAGE
        )
        
        result = await provider.generate(request)
        assert not result.success
        assert "not available" in result.error
        assert "invalid-model" in result.error
    
    @pytest.mark.asyncio
    async def test_download_result_image(self):
        """Test result downloading for images."""
        provider = FalProvider()
        
        # Mock result data
        result_data = {
            "images": [{"url": "https://example.com/image.png"}]
        }
        
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            output_path=Path("/tmp/test.png")
        )
        
        with patch("alicemultiverse.providers.fal_provider.download_file", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = None
            
            path = await provider._download_result(request, result_data)
            
            assert path == Path("/tmp/test.png")
            mock_download.assert_called_once_with("https://example.com/image.png", Path("/tmp/test.png"))
    
    @pytest.mark.asyncio
    async def test_download_result_video(self):
        """Test result downloading for videos."""
        provider = FalProvider()
        
        # Mock result data
        result_data = {
            "video": {"url": "https://example.com/video.mp4"}
        }
        
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.VIDEO,
            output_path=Path("/tmp/test.mp4")
        )
        
        with patch("alicemultiverse.providers.fal_provider.download_file", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = None
            
            path = await provider._download_result(request, result_data)
            
            assert path == Path("/tmp/test.mp4")
            mock_download.assert_called_once_with("https://example.com/video.mp4", Path("/tmp/test.mp4"))
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Mock setup needs improvement")
    async def test_api_error_handling(self):
        """Test API error handling."""
        provider = FalProvider(api_key="test-key")
        
        # Mock session with proper async context manager
        mock_response = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post.return_value = mock_context
        
        with patch.object(provider, "_get_session", return_value=mock_session):
            # Test rate limit error
            mock_response.status = 429
            with pytest.raises(RateLimitError):
                await provider._call_api("flux-pro", {"prompt": "test"})
            
            # Test authentication error
            mock_response.status = 401
            with pytest.raises(AuthenticationError):
                await provider._call_api("flux-pro", {"prompt": "test"})
            
            # Test general API error
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Server error")
            with pytest.raises(GenerationError) as exc_info:
                await provider._call_api("flux-pro", {"prompt": "test"})
            assert "Server error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Mock setup needs improvement")
    async def test_poll_for_completion(self):
        """Test polling for queued requests."""
        provider = FalProvider(api_key="test-key")
        
        # Mock session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        # Simulate polling: first processing, then completed
        mock_response.json = AsyncMock(side_effect=[
            {"status": "processing"},
            {"status": "completed", "result": {"images": [{"url": "test.png"}]}}
        ])
        
        with patch.object(provider, "_get_session", return_value=mock_session):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await provider._poll_for_completion("test-id")
                assert result == {"images": [{"url": "test.png"}]}
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        async with FalProvider() as provider:
            assert isinstance(provider, FalProvider)
        
        # Session should be closed
        assert provider._session is None
    
    def test_get_provider_from_registry(self):
        """Test getting provider from registry."""
        provider = get_provider("fal")
        assert isinstance(provider, FalProvider)
        assert provider.name == "fal.ai"
        
        # Test alias
        provider2 = get_provider("fal.ai")
        assert isinstance(provider2, FalProvider)