"""Tests for Midjourney provider."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile

import aiohttp
import pytest

from alicemultiverse.providers.midjourney_provider import MidjourneyProvider
from alicemultiverse.providers.types import (
    GenerationRequest,
    GenerationType,
    ProviderStatus,
)
from alicemultiverse.providers.provider import GenerationError, ProviderError


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "test-midjourney-api-key"


@pytest.fixture
def provider_useapi(mock_api_key):
    """Create Midjourney provider instance with UseAPI."""
    with patch.dict("os.environ", {"USEAPI_API_KEY": mock_api_key}):
        return MidjourneyProvider(proxy_service="useapi")


@pytest.fixture
def provider_goapi(mock_api_key):
    """Create Midjourney provider instance with GoAPI."""
    with patch.dict("os.environ", {"GOAPI_API_KEY": mock_api_key}):
        return MidjourneyProvider(proxy_service="goapi")


@pytest.fixture
def provider_custom(mock_api_key):
    """Create Midjourney provider instance with custom proxy."""
    return MidjourneyProvider(
        api_key=mock_api_key,
        proxy_service="custom",
        proxy_url="https://custom.proxy.com/api"
    )


class TestMidjourneyProvider:
    """Test Midjourney provider functionality."""
    
    def test_initialization_useapi(self, mock_api_key):
        """Test provider initialization with UseAPI."""
        # Test with environment variable
        with patch.dict("os.environ", {"USEAPI_API_KEY": mock_api_key}):
            provider = MidjourneyProvider(proxy_service="useapi")
            assert provider.api_key == mock_api_key
            assert provider.proxy_service == "useapi"
            assert provider.base_url == "https://api.useapi.net/v2/midjourney"
            assert "Authorization" in provider.headers
            assert provider.headers["Authorization"] == f"Bearer {mock_api_key}"
        
        # Test with direct API key
        provider = MidjourneyProvider(api_key="direct-key", proxy_service="useapi")
        assert provider.api_key == "direct-key"
        
        # Test without API key
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                MidjourneyProvider(proxy_service="useapi")
            assert "API key not provided" in str(exc_info.value)
    
    def test_initialization_goapi(self, mock_api_key):
        """Test provider initialization with GoAPI."""
        with patch.dict("os.environ", {"GOAPI_API_KEY": mock_api_key}):
            provider = MidjourneyProvider(proxy_service="goapi")
            assert provider.api_key == mock_api_key
            assert provider.proxy_service == "goapi"
            assert provider.base_url == "https://api.goapi.ai/v1/midjourney"
            assert "X-API-Key" in provider.headers
            assert provider.headers["X-API-Key"] == mock_api_key
    
    def test_initialization_custom(self, mock_api_key):
        """Test provider initialization with custom proxy."""
        # Test with custom proxy URL
        custom_url = "https://custom.proxy.com/api"
        provider = MidjourneyProvider(
            api_key=mock_api_key,
            proxy_service="custom",
            proxy_url=custom_url
        )
        assert provider.api_key == mock_api_key
        assert provider.proxy_service == "custom"
        assert provider.base_url == custom_url
        assert "Authorization" in provider.headers
        
        # Test without proxy URL
        with pytest.raises(ValueError) as exc_info:
            MidjourneyProvider(api_key=mock_api_key, proxy_service="custom")
        assert "proxy_url required" in str(exc_info.value)
    
    def test_initialization_invalid_service(self, mock_api_key):
        """Test provider initialization with invalid proxy service."""
        with pytest.raises(ValueError) as exc_info:
            MidjourneyProvider(api_key=mock_api_key, proxy_service="invalid")
        assert "Unknown proxy service" in str(exc_info.value)
    
    def test_name(self, provider_useapi):
        """Test provider name."""
        assert provider_useapi.name == "midjourney"
    
    def test_capabilities(self, provider_useapi):
        """Test provider capabilities."""
        capabilities = provider_useapi.capabilities
        assert GenerationType.IMAGE in capabilities.generation_types
        assert "v6.1" in capabilities.models
        assert "v6" in capabilities.models
        assert "v5.2" in capabilities.models
        assert "niji-6" in capabilities.models
        assert "image_to_image" in capabilities.features
        assert capabilities.supports_batch is False
        assert capabilities.pricing["v6.1"] == 0.30
        assert capabilities.pricing["v5.2"] == 0.25
        assert capabilities.pricing["niji-6"] == 0.30
    
    def test_parse_prompt_basic(self, provider_useapi):
        """Test basic prompt parsing."""
        result = provider_useapi._parse_prompt("A beautiful sunset over mountains")
        assert result["prompt"] == "A beautiful sunset over mountains"
        assert result["version"] == "v6.1"  # Default
        assert result["original_prompt"] == "A beautiful sunset over mountains"
        assert result["parameters"]["version"] == "v6.1"
    
    def test_parse_prompt_with_version(self, provider_useapi):
        """Test prompt parsing with version parameter."""
        # Test v6
        result = provider_useapi._parse_prompt("A sunset --v 6")
        assert result["prompt"] == "A sunset"
        assert result["version"] == "v6"
        assert result["parameters"]["version"] == "v6"
        
        # Test v5.2
        result = provider_useapi._parse_prompt("A sunset --v 5.2")
        assert result["version"] == "v5.2"
        
        # Test niji
        result = provider_useapi._parse_prompt("Anime style --v niji-6")
        assert result["version"] == "niji-6"
    
    def test_parse_prompt_with_aspect_ratio(self, provider_useapi):
        """Test prompt parsing with aspect ratio."""
        result = provider_useapi._parse_prompt("A sunset --ar 16:9")
        assert result["prompt"] == "A sunset"
        assert result["parameters"]["aspect_ratio"] == "16:9"
        
        # Test different ratio
        result = provider_useapi._parse_prompt("Portrait --ar 9:16")
        assert result["parameters"]["aspect_ratio"] == "9:16"
    
    def test_parse_prompt_with_quality(self, provider_useapi):
        """Test prompt parsing with quality parameter."""
        result = provider_useapi._parse_prompt("A sunset --q 2")
        assert result["parameters"]["quality"] == 2.0
        
        # Test decimal quality
        result = provider_useapi._parse_prompt("A sunset --q 0.5")
        assert result["parameters"]["quality"] == 0.5
    
    def test_parse_prompt_with_stylize(self, provider_useapi):
        """Test prompt parsing with stylize parameter."""
        result = provider_useapi._parse_prompt("A sunset --s 750")
        assert result["parameters"]["stylize"] == 750
    
    def test_parse_prompt_with_chaos(self, provider_useapi):
        """Test prompt parsing with chaos parameter."""
        result = provider_useapi._parse_prompt("A sunset --c 50")
        assert result["parameters"]["chaos"] == 50
    
    def test_parse_prompt_with_no(self, provider_useapi):
        """Test prompt parsing with no (negative) parameter."""
        result = provider_useapi._parse_prompt("A sunset --no clouds")
        assert result["parameters"]["no"] == "clouds"
        
        # Test multiple words
        result = provider_useapi._parse_prompt("A forest --no people, cars, buildings")
        assert result["parameters"]["no"] == "people, cars, buildings"
    
    def test_parse_prompt_with_multiple_params(self, provider_useapi):
        """Test prompt parsing with multiple parameters."""
        prompt = "Epic fantasy landscape --v 6 --ar 16:9 --q 2 --s 1000 --c 75 --no text"
        result = provider_useapi._parse_prompt(prompt)
        
        assert result["prompt"] == "Epic fantasy landscape"
        assert result["version"] == "v6"
        assert result["parameters"]["version"] == "v6"
        assert result["parameters"]["aspect_ratio"] == "16:9"
        assert result["parameters"]["quality"] == 2.0
        assert result["parameters"]["stylize"] == 1000
        assert result["parameters"]["chaos"] == 75
        assert result["parameters"]["no"] == "text"
    
    def test_build_generation_request_useapi(self, provider_useapi):
        """Test building generation request for UseAPI."""
        prompt_data = {
            "prompt": "A sunset",
            "original_prompt": "A sunset --v 6 --ar 16:9",
            "parameters": {"version": "v6", "aspect_ratio": "16:9"},
            "version": "v6"
        }
        
        request = GenerationRequest(
            prompt="A sunset --v 6 --ar 16:9",
            generation_type=GenerationType.IMAGE,
            model="v6"
        )
        
        api_request = provider_useapi._build_generation_request(prompt_data, request)
        assert api_request["prompt"] == "A sunset --v 6 --ar 16:9"
        assert "webhook" not in api_request  # No webhook configured
        
        # Test with image URL
        request.reference_assets = ["https://example.com/image.jpg"]
        api_request = provider_useapi._build_generation_request(prompt_data, request)
        assert api_request["image_url"] == "https://example.com/image.jpg"
    
    def test_build_generation_request_goapi(self, provider_goapi):
        """Test building generation request for GoAPI."""
        prompt_data = {
            "prompt": "A sunset",
            "original_prompt": "A sunset --v 6",
            "parameters": {"version": "v6"},
            "version": "v6"
        }
        
        request = GenerationRequest(
            prompt="A sunset --v 6",
            generation_type=GenerationType.IMAGE,
            model="v6"
        )
        
        api_request = provider_goapi._build_generation_request(prompt_data, request)
        assert api_request["prompt"] == "A sunset --v 6"
        assert api_request["model"] == "v6"
        
        # Test with image URL
        request.reference_assets = ["https://example.com/image.jpg"]
        api_request = provider_goapi._build_generation_request(prompt_data, request)
        assert api_request["init_image"] == "https://example.com/image.jpg"
    
    def test_build_generation_request_with_webhook(self, mock_api_key):
        """Test building generation request with webhook."""
        webhook_url = "https://my.webhook.com/callback"
        provider = MidjourneyProvider(
            api_key=mock_api_key,
            proxy_service="useapi",
            webhook_url=webhook_url
        )
        
        prompt_data = {
            "prompt": "A sunset",
            "original_prompt": "A sunset",
            "parameters": {"version": "v6.1"},
            "version": "v6.1"
        }
        
        request = GenerationRequest(
            prompt="A sunset",
            generation_type=GenerationType.IMAGE,
            model="v6.1"
        )
        
        api_request = provider._build_generation_request(prompt_data, request)
        assert api_request["webhook"] == webhook_url
    
    @pytest.mark.asyncio
    @patch("alicemultiverse.providers.provider.publish_event_sync")
    async def test_generate_basic_useapi(self, mock_publish_event, provider_useapi):
        """Test basic image generation with UseAPI."""
        # Mock responses
        mock_submit_response = {
            "task_id": "test-task-123",
            "status": "pending"
        }
        
        mock_status_response = {
            "task_id": "test-task-123",
            "status": "completed",
            "imageUrl": "https://example.com/generated-image.png",
            "seed": 12345
        }
        
        # Mock aiohttp using a different approach
        with patch("aiohttp.ClientSession") as mock_session_class:
            # Create a mock session instance
            mock_session = MagicMock()
            
            # Mock responses
            post_response = MagicMock()
            post_response.status = 202
            post_response.json = AsyncMock(return_value=mock_submit_response)
            post_response.__aenter__ = AsyncMock(return_value=post_response)
            post_response.__aexit__ = AsyncMock(return_value=None)
            
            status_response = MagicMock()
            status_response.status = 200
            status_response.json = AsyncMock(return_value=mock_status_response)
            status_response.__aenter__ = AsyncMock(return_value=status_response)
            status_response.__aexit__ = AsyncMock(return_value=None)
            
            image_response = MagicMock()
            image_response.status = 200
            image_response.read = AsyncMock(return_value=b"fake image data")
            image_response.headers = {"content-type": "image/png"}
            image_response.__aenter__ = AsyncMock(return_value=image_response)
            image_response.__aexit__ = AsyncMock(return_value=None)
            
            # Configure session methods
            mock_session.post = MagicMock(return_value=post_response)
            mock_session.get = MagicMock(side_effect=[status_response, image_response])
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Configure the class to return our mock session
            mock_session_class.return_value = mock_session
            
            # Create request
            request = GenerationRequest(
                prompt="A beautiful sunset --v 6.1 --ar 16:9",
                generation_type=GenerationType.IMAGE,
                model="v6.1"
            )
            
            # Mock file operations
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.write.return_value = None
                
                # Generate
                result = await provider_useapi.generate(request)
            
            # Verify result
            assert result.success is True
            assert result.file_path is not None
            assert result.cost == 0.30  # v6.1 cost
            assert result.model == "v6.1"
            assert result.metadata["job_id"] == "test-task-123"
            assert result.metadata["seed"] == 12345
            assert result.metadata["proxy_service"] == "useapi"
    
    @pytest.mark.asyncio
    @patch("alicemultiverse.providers.provider.publish_event_sync")
    async def test_generate_basic_goapi(self, mock_publish_event, provider_goapi):
        """Test basic image generation with GoAPI."""
        # Mock responses
        mock_submit_response = {
            "job_id": "test-job-456",
            "status": "processing"
        }
        
        mock_status_response = {
            "job_id": "test-job-456",
            "status": "completed",
            "url": "https://example.com/generated-image.jpg",
            "seed": 67890
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            # Set up mocks
            post_response = AsyncMock()
            post_response.status = 200
            post_response.json = AsyncMock(return_value=mock_submit_response)
            
            status_response = AsyncMock()
            status_response.status = 200
            status_response.json = AsyncMock(return_value=mock_status_response)
            
            image_response = AsyncMock()
            image_response.status = 200
            image_response.read = AsyncMock(return_value=b"fake image data")
            image_response.headers = {"content-type": "image/jpeg"}
            
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = post_response
            
            mock_get_status = AsyncMock()
            mock_get_status.__aenter__.return_value = status_response
            
            mock_get_image = AsyncMock()
            mock_get_image.__aenter__.return_value = image_response
            
            session_instance = AsyncMock()
            session_instance.post.return_value = mock_post
            session_instance.get.side_effect = [mock_get_status, mock_get_image]
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            # Create request
            request = GenerationRequest(
                prompt="Fantasy landscape --v 5.2",
                generation_type=GenerationType.IMAGE,
                model="v5.2"
            )
            
            # Generate
            result = await provider_goapi.generate(request)
            
            # Verify result
            assert result.success is True
            assert result.file_path is not None
            assert result.file_path.suffix == ".jpg"
            assert result.cost == 0.25  # v5.2 cost
            assert result.model == "v5.2"
            assert result.metadata["job_id"] == "test-job-456"
            assert result.metadata["proxy_service"] == "goapi"
    
    @pytest.mark.asyncio
    async def test_submit_generation_error(self, provider_useapi):
        """Test error handling during job submission."""
        with patch("aiohttp.ClientSession") as mock_session:
            post_response = AsyncMock()
            post_response.status = 400
            post_response.text = AsyncMock(return_value="Invalid prompt")
            
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = post_response
            
            session_instance = AsyncMock()
            session_instance.post.return_value = mock_post
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            generation_request = {"prompt": "test"}
            
            with pytest.raises(ProviderError) as exc_info:
                await provider_useapi._submit_generation(generation_request)
            
            assert "API error 400" in str(exc_info.value)
            assert "Invalid prompt" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self, provider_useapi):
        """Test timeout during polling."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock status response that never completes
            status_response = AsyncMock()
            status_response.status = 200
            status_response.json = AsyncMock(return_value={
                "task_id": "test-123",
                "status": "processing"
            })
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = status_response
            
            session_instance = AsyncMock()
            session_instance.get.return_value = mock_get
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            # Reduce timeout for testing
            provider_useapi.MAX_POLL_TIME = 0.1
            provider_useapi.POLL_INTERVAL = 0.05
            
            with pytest.raises(GenerationError) as exc_info:
                await provider_useapi._wait_for_completion("test-123")
            
            assert "Generation timed out" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_failed(self, provider_useapi):
        """Test handling of failed generation."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock failed status response
            status_response = AsyncMock()
            status_response.status = 200
            status_response.json = AsyncMock(return_value={
                "task_id": "test-123",
                "status": "failed",
                "error": "Content policy violation"
            })
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = status_response
            
            session_instance = AsyncMock()
            session_instance.get.return_value = mock_get
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            with pytest.raises(GenerationError) as exc_info:
                await provider_useapi._wait_for_completion("test-123")
            
            assert "Generation failed" in str(exc_info.value)
            assert "Content policy violation" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_download_image_error(self, provider_useapi):
        """Test error handling during image download."""
        with patch("aiohttp.ClientSession") as mock_session:
            download_response = AsyncMock()
            download_response.status = 404
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = download_response
            
            session_instance = AsyncMock()
            session_instance.get.return_value = mock_get
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            with pytest.raises(GenerationError) as exc_info:
                await provider_useapi._download_image("https://example.com/missing.jpg", "test-123")
            
            assert "Failed to download image: 404" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_download_image_different_formats(self, provider_useapi):
        """Test downloading images in different formats."""
        test_cases = [
            ("image/png", ".png"),
            ("image/jpeg", ".jpg"),
            ("image/jpg", ".jpg"),
            ("image/webp", ".webp"),
            ("application/octet-stream", ".png"),  # Default
        ]
        
        for content_type, expected_ext in test_cases:
            with patch("aiohttp.ClientSession") as mock_session:
                download_response = AsyncMock()
                download_response.status = 200
                download_response.read = AsyncMock(return_value=b"fake image data")
                download_response.headers = {"content-type": content_type}
                
                mock_get = AsyncMock()
                mock_get.__aenter__.return_value = download_response
                
                session_instance = AsyncMock()
                session_instance.get.return_value = mock_get
                
                mock_session.return_value.__aenter__.return_value = session_instance
                
                output_path = await provider_useapi._download_image(
                    "https://example.com/image",
                    f"test-{content_type.replace('/', '-')}"
                )
                
                assert output_path.suffix == expected_ext
    
    def test_cost_estimation_different_models(self, provider_useapi):
        """Test cost estimation for different models."""
        test_cases = [
            ("v6.1", 0.30),
            ("v6", 0.30),
            ("v5.2", 0.25),
            ("v5.1", 0.25),
            ("v5", 0.25),
            ("v4", 0.20),
            ("niji-6", 0.30),
            ("niji-5", 0.25),
        ]
        
        for model, expected_cost in test_cases:
            request = GenerationRequest(
                prompt=f"Test --v {model}",
                generation_type=GenerationType.IMAGE,
                model=model
            )
            
            cost = provider_useapi.estimate_cost(request)
            assert cost == expected_cost
    
    def test_cost_estimation_unknown_model(self, provider_useapi):
        """Test cost estimation for unknown model."""
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="unknown-model"
        )
        
        # Should default to 0.30
        cost = provider_useapi.estimate_cost(request)
        assert cost == 0.30
    
    @pytest.mark.asyncio
    async def test_check_status_useapi(self, provider_useapi):
        """Test status check for UseAPI."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock successful health check
            health_response = AsyncMock()
            health_response.status = 200
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = health_response
            
            session_instance = AsyncMock()
            session_instance.get.return_value = mock_get
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            status = await provider_useapi.check_status()
            assert status == ProviderStatus.READY
            
            # Verify correct endpoint was called
            session_instance.get.assert_called_with(
                "https://api.useapi.net/v2/midjourney/status",
                headers=provider_useapi.headers,
                timeout=aiohttp.ClientTimeout(total=10)
            )
    
    @pytest.mark.asyncio
    async def test_check_status_error(self, provider_useapi):
        """Test status check with error."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock failed health check
            health_response = AsyncMock()
            health_response.status = 503
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = health_response
            
            session_instance = AsyncMock()
            session_instance.get.return_value = mock_get
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            status = await provider_useapi.check_status()
            assert status == ProviderStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_check_status_exception(self, provider_useapi):
        """Test status check with exception."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock network error
            session_instance = AsyncMock()
            session_instance.get.side_effect = aiohttp.ClientError("Network error")
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            status = await provider_useapi.check_status()
            assert status == ProviderStatus.ERROR
    
    def test_get_model_info(self, provider_useapi):
        """Test getting model information."""
        info = provider_useapi.get_model_info("v6.1")
        assert info["name"] == "v6.1"
        assert info["description"] == "Midjourney v6.1"
        assert info["cost_per_generation"] == 0.30
        assert "variations" in info["features"]
        assert "upscaling" in info["features"]
        assert info["max_prompt_length"] == 2000
        
        # Test different model
        info = provider_useapi.get_model_info("v5.2")
        assert info["cost_per_generation"] == 0.25
    
    @pytest.mark.asyncio
    async def test_generate_with_image_url(self, provider_useapi):
        """Test generation with image URL (image-to-image)."""
        mock_submit_response = {"task_id": "test-img2img-123"}
        mock_status_response = {
            "task_id": "test-img2img-123",
            "status": "completed",
            "imageUrl": "https://example.com/result.png"
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            # Set up mocks
            post_response = AsyncMock()
            post_response.status = 202
            post_response.json = AsyncMock(return_value=mock_submit_response)
            
            status_response = AsyncMock()
            status_response.status = 200
            status_response.json = AsyncMock(return_value=mock_status_response)
            
            image_response = AsyncMock()
            image_response.status = 200
            image_response.read = AsyncMock(return_value=b"fake image data")
            image_response.headers = {"content-type": "image/png"}
            
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = post_response
            
            mock_get_status = AsyncMock()
            mock_get_status.__aenter__.return_value = status_response
            
            mock_get_image = AsyncMock()
            mock_get_image.__aenter__.return_value = image_response
            
            session_instance = AsyncMock()
            session_instance.post.return_value = mock_post
            session_instance.get.side_effect = [mock_get_status, mock_get_image]
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            # Create request with image URL
            request = GenerationRequest(
                prompt="Make it more vibrant --v 6.1",
                generation_type=GenerationType.IMAGE,
                model="v6.1",
                image_url="https://example.com/source.jpg"
            )
            
            # Generate
            result = await provider_useapi.generate(request)
            
            # Verify result
            assert result.success is True
            
            # Verify API was called with image URL
            call_args = session_instance.post.call_args
            payload = call_args[1]["json"]
            assert payload["image_url"] == "https://example.com/source.jpg"
    
    @pytest.mark.asyncio
    async def test_generate_no_image_url_in_response(self, provider_useapi):
        """Test handling response without image URL."""
        mock_submit_response = {"task_id": "test-123"}
        mock_status_response = {
            "task_id": "test-123",
            "status": "completed",
            # No imageUrl or url field
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            # Set up mocks
            post_response = AsyncMock()
            post_response.status = 202
            post_response.json = AsyncMock(return_value=mock_submit_response)
            
            status_response = AsyncMock()
            status_response.status = 200
            status_response.json = AsyncMock(return_value=mock_status_response)
            
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = post_response
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = status_response
            
            session_instance = AsyncMock()
            session_instance.post.return_value = mock_post
            session_instance.get.return_value = mock_get
            
            mock_session.return_value.__aenter__.return_value = session_instance
            
            request = GenerationRequest(
                prompt="Test",
                generation_type=GenerationType.IMAGE,
                model="v6.1"
            )
            
            result = await provider_useapi.generate(request)
            
            assert result.success is False
            assert "No image URL in response" in result.error