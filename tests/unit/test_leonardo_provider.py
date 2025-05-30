"""Tests for Leonardo.ai provider."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile

import aiohttp
import pytest

from alicemultiverse.providers.leonardo_provider import (
    LeonardoModel,
    LeonardoProvider,
    PresetStyle,
)
from alicemultiverse.providers.types import (
    GenerationRequest,
    GenerationType,
    ProviderStatus,
)


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "test-leonardo-api-key"


@pytest.fixture
def provider(mock_api_key):
    """Create Leonardo provider instance."""
    with patch.dict("os.environ", {"LEONARDO_API_KEY": mock_api_key}):
        return LeonardoProvider()


class TestLeonardoProvider:
    """Test Leonardo provider functionality."""
    
    def test_initialization(self, mock_api_key):
        """Test provider initialization."""
        # Test with environment variable
        with patch.dict("os.environ", {"LEONARDO_API_KEY": mock_api_key}):
            provider = LeonardoProvider()
            assert provider.api_key == mock_api_key
        
        # Test with direct API key
        provider = LeonardoProvider(api_key="direct-key")
        assert provider.api_key == "direct-key"
        
        # Test without API key
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(Exception) as exc_info:
                LeonardoProvider()
            assert "Leonardo API key is required" in str(exc_info.value)
    
    def test_name(self, provider):
        """Test provider name."""
        assert provider.name == "leonardo"
    
    def test_capabilities(self, provider):
        """Test provider capabilities."""
        capabilities = provider.capabilities
        assert GenerationType.IMAGE in capabilities.generation_types
        assert "jpg" in capabilities.formats
        assert "png" in capabilities.formats
        assert capabilities.supports_batch is True
        assert capabilities.rate_limits["requests_per_minute"] == 60
        assert "phoenix" in capabilities.models
        assert "alchemy" in capabilities.features
        assert "photo_real" in capabilities.features
    
    def test_model_resolution(self, provider):
        """Test model alias resolution."""
        # Test aliases
        assert provider._resolve_model("phoenix") == LeonardoModel.PHOENIX_1_0.value
        assert provider._resolve_model("flux") == LeonardoModel.FLUX_DEV.value
        assert provider._resolve_model("flux-schnell") == LeonardoModel.FLUX_SCHNELL.value
        assert provider._resolve_model("vision-xl") == LeonardoModel.VISION_XL.value
        
        # Test direct model IDs
        assert provider._resolve_model(LeonardoModel.PHOENIX_1_0.value) == LeonardoModel.PHOENIX_1_0.value
        
        # Test unknown model (should default to Phoenix 1.0)
        assert provider._resolve_model("unknown-model") == LeonardoModel.PHOENIX_1_0.value
    
    @pytest.mark.asyncio
    async def test_generate_basic(self, provider):
        """Test basic image generation."""
        # Mock responses
        mock_create_response = {
            "sdGenerationJob": {
                "generationId": "test-generation-123"
            }
        }
        
        mock_poll_response = {
            "generations_by_pk": {
                "status": "COMPLETE",
                "generated_images": [
                    {
                        "url": "https://example.com/image1.jpg",
                        "id": "img-123",
                        "width": 1024,
                        "height": 1024,
                        "seed": 12345,
                    }
                ],
                "generation_time": 10.5
            }
        }
        
        # Mock aiohttp
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock the context managers
            mock_post = AsyncMock()
            mock_get = AsyncMock()
            mock_download = AsyncMock()
            
            # Set up response mocks
            post_response = AsyncMock()
            post_response.status = 200
            post_response.json = AsyncMock(return_value=mock_create_response)
            
            get_response = AsyncMock()
            get_response.status = 200
            get_response.json = AsyncMock(return_value=mock_poll_response)
            
            download_response = AsyncMock()
            download_response.status = 200
            download_response.read = AsyncMock(return_value=b"fake image data")
            
            # Configure the mocks
            mock_post.__aenter__.return_value = post_response
            mock_get.__aenter__.return_value = get_response
            mock_download.__aenter__.return_value = download_response
            
            # Set up session mock
            session_instance = AsyncMock()
            session_instance.post.return_value = mock_post
            session_instance.get.side_effect = [mock_get, mock_download]  # poll then download
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            # Create request
            request = GenerationRequest(
                prompt="A beautiful sunset over mountains",
                generation_type=GenerationType.IMAGE,
                model="phoenix",
                parameters={
                    "width": 1024,
                    "height": 1024,
                    "num_images": 1,
                }
            )
            
            # Generate
            result = await provider.generate(request)
            
            # Verify result
            assert result.success is True
            assert result.file_path is not None
            assert result.cost == 0.02  # Base cost for Phoenix at 1024x1024
            assert result.generation_time == 10.5
            assert result.metadata["generation_id"] == "test-generation-123"
            assert result.metadata["seed"] == 12345
    
    @pytest.mark.asyncio
    async def test_generate_with_alchemy(self, provider):
        """Test generation with Alchemy enhancement."""
        # Mock responses
        mock_create_response = {
            "sdGenerationJob": {"generationId": "test-123"}
        }
        
        mock_poll_response = {
            "generations_by_pk": {
                "status": "COMPLETE",
                "generated_images": [{"url": "https://example.com/image.jpg"}]
            }
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            # Set up mocks
            post_response = AsyncMock()
            post_response.status = 200
            post_response.json = AsyncMock(return_value=mock_create_response)
            post_response.text = AsyncMock(return_value="")
            
            get_response = AsyncMock()
            get_response.status = 200
            get_response.json = AsyncMock(return_value=mock_poll_response)
            
            download_response = AsyncMock()
            download_response.status = 200
            download_response.read = AsyncMock(return_value=b"fake image data")
            
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = post_response
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = get_response
            
            mock_download = AsyncMock()
            mock_download.__aenter__.return_value = download_response
            
            session_instance = AsyncMock()
            session_instance.post.return_value = mock_post
            session_instance.get.side_effect = [mock_get, mock_download]
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            # Request with Alchemy
            request = GenerationRequest(
                prompt="Epic fantasy landscape",
                generation_type=GenerationType.IMAGE,
                model="vision-xl",  # SDXL model for Alchemy v2
                parameters={
                    "alchemy": True,
                    "preset_style": PresetStyle.CREATIVE.value
                }
            )
            
            result = await provider.generate(request)
            
            # Verify Alchemy was enabled
            assert result.success is True
            # Verify API was called with alchemy
            call_args = session_instance.post.call_args
            payload = call_args[1]["json"]
            assert payload["alchemy"] is True
            assert payload["presetStyle"] == PresetStyle.CREATIVE.value
    
    @pytest.mark.asyncio
    async def test_generate_photoreal(self, provider):
        """Test PhotoReal generation."""
        # Mock responses
        mock_create_response = {
            "sdGenerationJob": {"generationId": "test-123"}
        }
        
        mock_poll_response = {
            "generations_by_pk": {
                "status": "COMPLETE",
                "generated_images": [{"url": "https://example.com/image.jpg"}]
            }
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            # Set up mocks (similar to above)
            post_response = AsyncMock()
            post_response.status = 200
            post_response.json = AsyncMock(return_value=mock_create_response)
            
            get_response = AsyncMock()
            get_response.status = 200
            get_response.json = AsyncMock(return_value=mock_poll_response)
            
            download_response = AsyncMock()
            download_response.status = 200
            download_response.read = AsyncMock(return_value=b"fake image data")
            
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = post_response
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = get_response
            
            mock_download = AsyncMock()
            mock_download.__aenter__.return_value = download_response
            
            session_instance = AsyncMock()
            session_instance.post.return_value = mock_post
            session_instance.get.side_effect = [mock_get, mock_download]
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            # Request with PhotoReal v1 (no model ID)
            request = GenerationRequest(
                prompt="Photorealistic portrait",
                generation_type=GenerationType.IMAGE,
                model="any-model",  # Will be ignored for PhotoReal v1
                parameters={
                    "photo_real": True,
                    "photo_real_version": "v1",
                    "preset_style": PresetStyle.CINEMATIC.value
                }
            )
            
            result = await provider.generate(request)
            
            # Verify PhotoReal settings
            assert result.success is True
            call_args = session_instance.post.call_args
            payload = call_args[1]["json"]
            assert payload["photoReal"] is True
            assert "modelId" not in payload  # No model ID for PhotoReal v1
            assert payload["presetStyle"] == PresetStyle.CINEMATIC.value
    
    @pytest.mark.asyncio
    async def test_generate_error_handling(self, provider):
        """Test error handling during generation."""
        # Mock API error
        with patch("aiohttp.ClientSession") as mock_session:
            post_response = AsyncMock()
            post_response.status = 400
            post_response.text = AsyncMock(return_value="Bad request")
            
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = post_response
            
            session_instance = AsyncMock()
            session_instance.post.return_value = mock_post
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            request = GenerationRequest(
                prompt="Test",
                generation_type=GenerationType.IMAGE,
                model="phoenix"
            )
            
            result = await provider.generate(request)
            
            assert result.success is False
            assert "Leonardo API error: 400" in result.error
    
    def test_cost_estimation_basic(self, provider):
        """Test basic cost estimation."""
        # Phoenix model at 1024x1024
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="phoenix",
            parameters={
                "width": 1024,
                "height": 1024,
                "num_images": 1,
            }
        )
        
        cost = provider.estimate_cost(request)
        # 20 tokens base / 1000 = $0.02
        assert cost == 0.02
    
    def test_cost_estimation_with_resolution(self, provider):
        """Test cost estimation with different resolution."""
        # Double resolution = 4x pixels = 4x cost
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="phoenix",
            parameters={
                "width": 2048,
                "height": 2048,
                "num_images": 1,
            }
        )
        
        cost = provider.estimate_cost(request)
        # 20 tokens * 4 = 80 tokens / 1000 = $0.08
        assert cost == 0.08
    
    def test_cost_estimation_with_alchemy(self, provider):
        """Test cost estimation with Alchemy."""
        # SDXL model with Alchemy v2
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="vision-xl",
            parameters={
                "width": 1024,
                "height": 1024,
                "num_images": 1,
                "alchemy": True,
            }
        )
        
        cost = provider.estimate_cost(request)
        # 20 tokens * 1.75 (Alchemy v2) = 35 tokens / 1000 = $0.035
        assert cost == 0.035
    
    def test_cost_estimation_multiple_images(self, provider):
        """Test cost estimation for multiple images."""
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="flux-schnell",
            parameters={
                "width": 1024,
                "height": 1024,
                "num_images": 4,
            }
        )
        
        cost = provider.estimate_cost(request)
        # 15 tokens * 4 images = 60 tokens / 1000 = $0.06
        assert cost == 0.06
    
    def test_generation_time_estimation(self, provider):
        """Test generation time estimation."""
        # Flux Schnell is fast
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="flux-schnell",
            parameters={"num_images": 1}
        )
        
        time_est = provider.get_generation_time(request)
        assert time_est == 5.0
        
        # With Alchemy
        request.parameters["alchemy"] = True
        time_with_alchemy = provider.get_generation_time(request)
        assert time_with_alchemy == 7.5  # 5.0 * 1.5
        
        # Multiple images with alchemy still enabled
        request.parameters["num_images"] = 4
        time_multiple = provider.get_generation_time(request)
        assert time_multiple == 24.0  # 7.5 * 4 * 0.8
    
    @pytest.mark.asyncio
    async def test_list_elements(self, provider):
        """Test listing Elements."""
        mock_response = {
            "user_elements": [
                {"id": "elem-1", "name": "Cyberpunk"},
                {"id": "elem-2", "name": "Fantasy"},
            ]
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            get_response = AsyncMock()
            get_response.status = 200
            get_response.json = AsyncMock(return_value=mock_response)
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = get_response
            
            session_instance = AsyncMock()
            session_instance.get.return_value = mock_get
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            elements = await provider.list_elements()
            assert len(elements) == 2
            assert elements[0]["name"] == "Cyberpunk"
    
    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        """Test listing platform models."""
        mock_response = {
            "platform_models": [
                {"id": LeonardoModel.PHOENIX_1_0.value, "name": "Phoenix 1.0"},
                {"id": LeonardoModel.FLUX_DEV.value, "name": "Flux Dev"},
            ]
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            get_response = AsyncMock()
            get_response.status = 200
            get_response.json = AsyncMock(return_value=mock_response)
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = get_response
            
            session_instance = AsyncMock()
            session_instance.get.return_value = mock_get
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            models = await provider.list_models()
            assert len(models) == 2
            assert models[0]["name"] == "Phoenix 1.0"
    
    @pytest.mark.asyncio
    async def test_get_status(self, provider):
        """Test provider status."""
        # With API key
        status = await provider.check_status()
        assert status == ProviderStatus.AVAILABLE
        
        # Without API key
        provider.api_key = None
        status = await provider.check_status()
        assert status == ProviderStatus.UNAVAILABLE