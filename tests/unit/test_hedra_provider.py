"""Tests for Hedra provider."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from alicemultiverse.providers.hedra_provider import HedraProvider
from alicemultiverse.providers.types import (
    GenerationRequest,
    GenerationType,
    ProviderCapabilities
)
from alicemultiverse.core.exceptions import ValidationError
from alicemultiverse.providers.provider import ProviderError


class TestHedraProvider:
    """Test Hedra provider functionality."""
    
    @pytest.fixture
    def provider(self):
        """Create Hedra provider instance."""
        return HedraProvider(api_key="test-api-key")
    
    def test_provider_properties(self, provider):
        """Test provider properties."""
        assert provider.name == "hedra"
        assert GenerationType.VIDEO in provider.supported_types
        assert GenerationType.VIDEO in provider.capabilities.generation_types
        assert "image_to_video" in provider.capabilities.features
        assert "audio_to_video" in provider.capabilities.features
        assert "character-2" in provider.available_models
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key not provided"):
                HedraProvider()
    
    def test_init_with_env_api_key(self):
        """Test initialization with environment API key."""
        with patch.dict("os.environ", {"HEDRA_API_KEY": "env-api-key"}):
            provider = HedraProvider()
            assert provider.api_key == "env-api-key"
    
    @pytest.mark.asyncio
    async def test_validate_request_invalid_type(self, provider):
        """Test validation with invalid generation type."""
        request = GenerationRequest(
            prompt="Test prompt",
            generation_type=GenerationType.IMAGE
        )
        
        with pytest.raises(ValidationError, match="only supports video"):
            await provider.validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_request_missing_assets(self, provider):
        """Test validation with missing reference assets."""
        request = GenerationRequest(
            prompt="Test prompt",
            generation_type=GenerationType.VIDEO
        )
        
        with pytest.raises(ValidationError, match="requires an image and audio"):
            await provider.validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_request_invalid_aspect_ratio(self, provider, tmp_path):
        """Test validation with invalid aspect ratio."""
        # Create dummy files
        image_path = tmp_path / "test.jpg"
        audio_path = tmp_path / "test.mp3"
        image_path.touch()
        audio_path.touch()
        
        request = GenerationRequest(
            prompt="Test prompt",
            generation_type=GenerationType.VIDEO,
            reference_assets=[str(image_path), str(audio_path)],
            parameters={"aspect_ratio": "4:3"}  # Invalid
        )
        
        with pytest.raises(ValidationError, match="Invalid aspect ratio"):
            await provider.validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_request_valid(self, provider, tmp_path):
        """Test validation with valid request."""
        # Create dummy files
        image_path = tmp_path / "test.jpg"
        audio_path = tmp_path / "test.mp3"
        image_path.touch()
        audio_path.touch()
        
        request = GenerationRequest(
            prompt="Test prompt",
            generation_type=GenerationType.VIDEO,
            reference_assets=[str(image_path), str(audio_path)],
            parameters={"aspect_ratio": "16:9", "resolution": "720p"}
        )
        
        # Should not raise
        await provider.validate_request(request)
    
    def test_estimate_cost(self, provider):
        """Test cost estimation."""
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.VIDEO
        )
        
        cost = provider.estimate_cost(request)
        assert cost == 0.50  # Expected cost for character-2
        
        # Non-video should return 0
        request.generation_type = GenerationType.IMAGE
        cost = provider.estimate_cost(request)
        assert cost == 0.0
    
    @pytest.mark.asyncio
    async def test_generate_success(self, provider, tmp_path):
        """Test successful video generation."""
        # Create dummy files
        image_path = tmp_path / "test.jpg"
        audio_path = tmp_path / "test.mp3"
        image_path.write_bytes(b"fake image data")
        audio_path.write_bytes(b"fake audio data")
        
        request = GenerationRequest(
            prompt="A person talking",
            generation_type=GenerationType.VIDEO,
            reference_assets=[str(image_path), str(audio_path)],
            parameters={"aspect_ratio": "16:9", "resolution": "720p"}
        )
        
        # Mock HTTP responses
        mock_session = AsyncMock()
        
        # Create async context managers for responses
        def create_async_context_manager(response):
            """Create an async context manager that returns the response."""
            class AsyncContextManager:
                async def __aenter__(self):
                    return response
                async def __aexit__(self, *args):
                    pass
            return AsyncContextManager()
        
        # Mock asset creation responses
        mock_create_image_response = AsyncMock()
        mock_create_image_response.status = 200
        mock_create_image_response.json = AsyncMock(return_value={"id": "image-123"})
        
        mock_create_audio_response = AsyncMock()
        mock_create_audio_response.status = 200
        mock_create_audio_response.json = AsyncMock(return_value={"id": "audio-456"})
        
        # Mock asset upload responses
        mock_upload_response = AsyncMock()
        mock_upload_response.status = 200
        
        # Mock generation creation
        mock_gen_response = AsyncMock()
        mock_gen_response.status = 200
        mock_gen_response.json = AsyncMock(return_value={"id": "gen-789"})
        
        # Mock status polling
        mock_status_response = AsyncMock()
        mock_status_response.status = 200
        mock_status_response.json = AsyncMock(return_value={
            "status": "complete",
            "url": "https://example.com/video.mp4",
            "asset_id": "asset-999"
        })
        
        # Mock video download
        mock_download_response = AsyncMock()
        mock_download_response.status = 200
        mock_download_response.content.iter_chunked = AsyncMock(
            return_value=async_iter([b"fake video data"])
        )
        
        # Create a mock that tracks calls and returns appropriate responses
        post_call_count = 0
        get_call_count = 0
        
        def mock_post(*args, **kwargs):
            nonlocal post_call_count
            responses = [
                create_async_context_manager(mock_create_image_response),  # Create image asset
                create_async_context_manager(mock_upload_response),        # Upload image
                create_async_context_manager(mock_create_audio_response),  # Create audio asset
                create_async_context_manager(mock_upload_response),        # Upload audio
                create_async_context_manager(mock_gen_response),          # Create generation
            ]
            result = responses[post_call_count]
            post_call_count += 1
            return result
        
        def mock_get(*args, **kwargs):
            nonlocal get_call_count
            responses = [
                create_async_context_manager(mock_status_response),        # Status check
                create_async_context_manager(mock_download_response)       # Video download
            ]
            result = responses[get_call_count]
            get_call_count += 1
            return result
        
        mock_session.post = mock_post
        mock_session.get = mock_get
        
        # Create a mock ClientSession class that returns our configured session
        class MockClientSession:
            async def __aenter__(self):
                return mock_session
            async def __aexit__(self, *args):
                pass
        
        with patch("aiohttp.ClientSession", return_value=MockClientSession()):
            
            # Mock the publish_event function and download
            with patch("alicemultiverse.providers.hedra_provider.publish_event", new_callable=AsyncMock):
                # Mock Path.mkdir to avoid creating directories
                with patch("pathlib.Path.mkdir"):
                    # Mock the download method to avoid file I/O
                    async def mock_download(*args):
                        pass
                    
                    with patch.object(provider, "_download_video", mock_download):
                        result = await provider.generate(request)
            
            assert result.success is True
            assert result.file_path.exists()
            assert result.file_path.suffix == ".mp4"
            assert result.model == "character-2"
            assert result.cost == 0.50
            assert result.metadata["generation_id"] == "gen-789"
            assert result.metadata["asset_id"] == "asset-999"
    
    @pytest.mark.asyncio
    async def test_generate_api_error(self, provider, tmp_path):
        """Test handling of API errors."""
        # Create dummy files
        image_path = tmp_path / "test.jpg"
        audio_path = tmp_path / "test.mp3"
        image_path.touch()
        audio_path.touch()
        
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.VIDEO,
            reference_assets=[str(image_path), str(audio_path)]
        )
        
        # Mock failed response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad request")
        mock_session.post.return_value = mock_response
        
        with patch("aiohttp.ClientSession") as mock_client:
            mock_client.return_value.__aenter__.return_value = mock_session
            
            with pytest.raises(ProviderError, match="Failed to create"):
                await provider.generate(request)
    
    @pytest.mark.asyncio
    async def test_generate_with_optional_params(self, provider, tmp_path):
        """Test generation with optional parameters."""
        # Create dummy files
        image_path = tmp_path / "test.jpg"
        audio_path = tmp_path / "test.mp3"
        image_path.touch()
        audio_path.touch()
        
        request = GenerationRequest(
            prompt="Test with duration",
            generation_type=GenerationType.VIDEO,
            reference_assets=[str(image_path), str(audio_path)],
            parameters={
                "aspect_ratio": "9:16",
                "resolution": "540p",
                "duration_ms": 30000,
                "seed": 42
            }
        )
        
        # Mock successful flow
        with patch.object(provider, "_upload_asset", return_value="asset-id"):
            with patch.object(provider, "_wait_for_generation", return_value={
                "status": "complete",
                "url": "https://example.com/video.mp4",
                "asset_id": "final-asset"
            }):
                with patch.object(provider, "_download_video"):
                    with patch("aiohttp.ClientSession"):
                        # Mock the generation request
                        mock_session = AsyncMock()
                        mock_response = AsyncMock()
                        mock_response.status = 200
                        mock_response.json = AsyncMock(return_value={"id": "gen-123"})
                        mock_session.post.return_value = mock_response
                        
                        with patch("aiohttp.ClientSession") as mock_client:
                            mock_client.return_value.__aenter__.return_value = mock_session
                            
                            result = await provider.generate(request)
                            
                            # Verify the generation request was made with optional params
                            call_args = mock_session.post.call_args[1]["json"]
                            assert call_args["generated_video_inputs"]["duration_ms"] == 30000
                            assert call_args["generated_video_inputs"]["seed"] == 42


# Helper for async iteration
async def async_iter(items):
    """Create async iterator from list."""
    for item in items:
        yield item