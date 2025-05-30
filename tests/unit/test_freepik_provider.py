"""Tests for Freepik provider."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alicemultiverse.providers.freepik_provider import FreepikProvider
from alicemultiverse.providers.types import GenerationRequest, GenerationType


@pytest.fixture
def provider():
    """Create Freepik provider instance."""
    return FreepikProvider(api_key="test-api-key")


@pytest.fixture
def mock_session():
    """Create mock aiohttp session."""
    session = MagicMock()
    session.post = AsyncMock()
    session.get = AsyncMock()
    session.close = AsyncMock()
    return session


class TestFreepikProvider:
    """Test Freepik provider functionality."""
    
    def test_provider_properties(self, provider):
        """Test provider properties."""
        assert provider.name == "freepik"
        assert "magnific-sparkle" in provider.capabilities.models
        assert "mystic" in provider.capabilities.models
        assert GenerationType.IMAGE in provider.capabilities.generation_types
        assert "upscaling" in provider.capabilities.features
    
    def test_model_mappings(self, provider):
        """Test model mappings are correct."""
        assert provider.MODELS["magnific-sparkle"] == "magnific_sparkle"
        assert provider.MODELS["magnific-illusio"] == "magnific_illusio"
        assert provider.MODELS["magnific-sharpy"] == "magnific_sharpy"
        assert provider.MODELS["mystic"] == "mystic"
    
    def test_headers(self, provider):
        """Test API headers."""
        headers = provider._get_headers()
        assert headers["x-freepik-api-key"] == "test-api-key"
        assert headers["Content-Type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, provider):
        """Test async context manager."""
        async with provider as p:
            assert p.session is not None
        # Session should be closed
        assert provider.session is not None
    
    @pytest.mark.asyncio
    async def test_validate_request_upscaling(self, provider):
        """Test request validation for upscaling."""
        # Valid upscaling request
        request = GenerationRequest(
            prompt="",
            model="magnific-sparkle",
            generation_type=GenerationType.IMAGE,
            reference_assets=["https://example.com/image.jpg"]
        )
        await provider.validate_request(request)  # Should not raise
        
        # Missing reference image
        request = GenerationRequest(
            prompt="",
            model="magnific-sparkle",
            generation_type=GenerationType.IMAGE
        )
        with pytest.raises(ValueError, match="requires a reference image"):
            await provider.validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_request_generation(self, provider):
        """Test request validation for generation."""
        # Valid generation request
        request = GenerationRequest(
            prompt="A beautiful landscape",
            model="mystic",
            generation_type=GenerationType.IMAGE
        )
        await provider.validate_request(request)  # Should not raise
        
        # Missing prompt
        request = GenerationRequest(
            prompt="",
            model="mystic",
            generation_type=GenerationType.IMAGE
        )
        with pytest.raises(ValueError, match="requires a prompt"):
            await provider.validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_request_invalid_model(self, provider):
        """Test request validation with invalid model."""
        request = GenerationRequest(
            prompt="test",
            model="invalid-model",
            generation_type=GenerationType.IMAGE
        )
        with pytest.raises(ValueError, match="not supported"):
            await provider.validate_request(request)
    
    def test_build_upscale_params(self, provider):
        """Test building upscale parameters."""
        request = GenerationRequest(
            prompt="",
            model="magnific-sparkle",
            generation_type=GenerationType.IMAGE,
            reference_assets=["https://example.com/image.jpg"],
            parameters={
                "scale": 4,
                "creativity": 0.7,
                "hdr": 0.8,
                "style": "cinematic"
            }
        )
        
        params = provider._build_upscale_params(request)
        
        assert params["image"]["url"] == "https://example.com/image.jpg"
        assert params["scale"] == 4
        assert params["engine"] == "magnific_sparkle"
        assert params["creativity"] == 0.7
        assert params["hdr"] == 0.8
        assert params["style"] == "cinematic"
    
    def test_build_mystic_params(self, provider):
        """Test building Mystic parameters."""
        request = GenerationRequest(
            prompt="A futuristic city",
            model="mystic-4k",
            generation_type=GenerationType.IMAGE,
            parameters={
                "negative_prompt": "blurry, low quality",
                "guidance_scale": 7.5,
                "style": "cyberpunk",
                "seed": 42
            }
        )
        
        params = provider._build_mystic_params(request)
        
        assert params["prompt"] == "A futuristic city"
        assert params["negative_prompt"] == "blurry, low quality"
        assert params["image"]["size"] == "landscape_4k"
        assert params["image"]["guidance_scale"] == 7.5
        assert params["image"]["seed"] == 42
        assert params["styling"]["style"] == "cyberpunk"
    
    def test_build_mystic_params_with_reference(self, provider):
        """Test building Mystic parameters with style reference."""
        request = GenerationRequest(
            prompt="A portrait",
            model="mystic",
            generation_type=GenerationType.IMAGE,
            reference_assets=["https://example.com/style.jpg"],
            parameters={
                "lora": "portrait_pro",
                "lora_strength": 0.8
            }
        )
        
        params = provider._build_mystic_params(request)
        
        assert params["styling"]["references"][0]["url"] == "https://example.com/style.jpg"
        assert params["lora"]["name"] == "portrait_pro"
        assert params["lora"]["strength"] == 0.8
    
    def test_calculate_megapixels(self, provider):
        """Test megapixel calculation for pricing."""
        assert provider._calculate_megapixels(2) == 4.0
        assert provider._calculate_megapixels(4) == 16.0
        assert provider._calculate_megapixels(8) == 64.0
        assert provider._calculate_megapixels(16) == 256.0
    
    @pytest.mark.asyncio
    async def test_estimate_cost_upscaling(self, provider):
        """Test cost estimation for upscaling."""
        request = GenerationRequest(
            prompt="",
            model="magnific-sparkle",
            generation_type=GenerationType.IMAGE,
            reference_assets=["test.jpg"],
            parameters={"scale": 4}
        )
        
        estimate = await provider.estimate_cost(request)
        # 0.01 EUR/megapixel * 16 megapixels * 1.1 USD/EUR
        expected = 0.01 * 16 * 1.1
        assert estimate.estimated_cost == pytest.approx(expected)
    
    @pytest.mark.asyncio
    async def test_estimate_cost_generation(self, provider):
        """Test cost estimation for generation."""
        request = GenerationRequest(
            prompt="Test",
            model="mystic-4k",
            generation_type=GenerationType.IMAGE
        )
        
        estimate = await provider.estimate_cost(request)
        # 0.008 EUR * 1.1 USD/EUR
        expected = 0.008 * 1.1
        assert estimate.estimated_cost == pytest.approx(expected)
    
    def test_generation_time_estimates(self, provider):
        """Test generation time estimates."""
        # Upscaling 2x
        request = GenerationRequest(
            prompt="",
            model="magnific-sparkle",
            generation_type=GenerationType.IMAGE,
            reference_assets=["test.jpg"],
            parameters={"scale": 2}
        )
        min_time, max_time = provider.get_generation_time(request)
        assert min_time == 10
        assert max_time == 30
        
        # Upscaling 16x
        request.parameters = {"scale": 16}
        min_time, max_time = provider.get_generation_time(request)
        assert min_time == 60
        assert max_time == 180
        
        # Mystic generation
        request = GenerationRequest(
            prompt="Test",
            model="mystic",
            generation_type=GenerationType.IMAGE
        )
        min_time, max_time = provider.get_generation_time(request)
        assert min_time == 15
        assert max_time == 45
    
    @pytest.mark.asyncio
    async def test_upscale_image_success(self, provider, mock_session):
        """Test successful image upscaling."""
        provider.session = mock_session
        
        # Mock API responses
        mock_session.post.return_value.__aenter__.return_value.status = 200
        mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"data": {"_id": "task-123"}}
        )
        
        mock_session.get.return_value.__aenter__.return_value.status = 200
        mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={
                "data": {
                    "status": "completed",
                    "result": {"url": "https://cdn.freepik.com/upscaled.jpg"}
                }
            }
        )
        
        request = GenerationRequest(
            prompt="",
            model="magnific-sparkle",
            generation_type=GenerationType.IMAGE,
            reference_assets=["https://example.com/input.jpg"],
            parameters={"scale": 2}
        )
        
        result = await provider._generate(request)
        
        assert str(result.file_path) == "https://cdn.freepik.com/upscaled.jpg"
        assert result.provider == "freepik"
        assert result.model == "magnific-sparkle"
        assert result.metadata["task_id"] == "task-123"
        assert result.metadata["scale"] == 2
        assert result.cost == pytest.approx(0.01 * 4)  # 4 megapixels
    
    @pytest.mark.asyncio
    async def test_generate_image_success(self, provider, mock_session):
        """Test successful image generation."""
        provider.session = mock_session
        
        # Mock API responses
        mock_session.post.return_value.__aenter__.return_value.status = 200
        mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"data": {"_id": "task-456"}}
        )
        
        mock_session.get.return_value.__aenter__.return_value.status = 200
        mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={
                "data": {
                    "status": "completed",
                    "images": [{"url": "https://cdn.freepik.com/generated.jpg"}]
                }
            }
        )
        
        request = GenerationRequest(
            prompt="A beautiful sunset",
            model="mystic",
            generation_type=GenerationType.IMAGE
        )
        
        result = await provider._generate(request)
        
        assert str(result.file_path) == "https://cdn.freepik.com/generated.jpg"
        assert result.provider == "freepik"
        assert result.model == "mystic"
        assert result.metadata["task_id"] == "task-456"
        assert result.metadata["prompt"] == "A beautiful sunset"
        assert result.cost == pytest.approx(0.004)
    
    @pytest.mark.asyncio
    async def test_poll_timeout(self, provider, mock_session):
        """Test polling timeout."""
        provider.session = mock_session
        
        # Mock always returns processing status
        mock_session.get.return_value.__aenter__.return_value.status = 200
        mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"data": {"status": "processing"}}
        )
        
        with pytest.raises(TimeoutError):
            await provider._poll_task("task-123", "mystic", timeout=1, poll_interval=0.1)
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, provider, mock_session):
        """Test API error handling."""
        provider.session = mock_session
        
        # Mock API error
        mock_session.post.return_value.__aenter__.return_value.status = 400
        mock_session.post.return_value.__aenter__.return_value.text = AsyncMock(
            return_value="Invalid API key"
        )
        
        request = GenerationRequest(
            prompt="Test",
            model="mystic",
            generation_type=GenerationType.IMAGE
        )
        
        with pytest.raises(Exception, match="Invalid API key"):
            await provider._generate(request)