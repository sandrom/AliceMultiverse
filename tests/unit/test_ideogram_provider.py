"""Tests for Ideogram provider."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, create_autospec
import aiohttp
from datetime import datetime
from pathlib import Path

from alicemultiverse.providers.ideogram_provider import (
    IdeogramProvider, 
    IdeogramModel,
    IdeogramStyle,
    IdeogramAspectRatio
)
from alicemultiverse.providers.types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderStatus,
)


@pytest.fixture
def ideogram_provider():
    """Create an Ideogram provider instance."""
    return IdeogramProvider(api_key="test_api_key")


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = create_autospec(aiohttp.ClientSession, instance=True)
    return session


def create_async_context_manager(mock_response):
    """Helper to create an async context manager for aiohttp responses."""
    cm = AsyncMock()
    cm.__aenter__.return_value = mock_response
    cm.__aexit__.return_value = None
    return cm


class TestIdeogramProvider:
    """Test Ideogram provider functionality."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        provider = IdeogramProvider(api_key="test_key")
        assert provider.api_key == "test_key"
        
    def test_init_missing_credentials(self):
        """Test initialization fails without credentials."""
        with pytest.raises(ValueError, match="Ideogram requires"):
            IdeogramProvider()
    
    def test_model_mapping(self, ideogram_provider):
        """Test model name mapping."""
        assert ideogram_provider.MODELS["ideogram-v2"] == IdeogramModel.V2.value
        assert ideogram_provider.MODELS["ideogram-v2-turbo"] == IdeogramModel.V2_TURBO.value
        assert ideogram_provider.MODELS["ideogram-v3"] == IdeogramModel.V3.value
        assert ideogram_provider.MODELS["ideogram"] == IdeogramModel.V3.value  # Default
        assert ideogram_provider.MODELS["turbo"] == IdeogramModel.V2_TURBO.value
        
    def test_provider_name(self, ideogram_provider):
        """Test provider name property."""
        assert ideogram_provider.name == "ideogram"
        
    def test_capabilities(self, ideogram_provider):
        """Test capability reporting."""
        caps = ideogram_provider.capabilities
        
        assert GenerationType.IMAGE in caps.generation_types
        assert "ideogram-v2" in caps.models
        assert "ideogram-v3" in caps.models
        assert caps.max_resolution["width"] == 2048
        assert caps.max_resolution["height"] == 2048
        assert "text_rendering" in caps.features
        assert "typography" in caps.features
        assert "logo_generation" in caps.features
        assert caps.supports_batch is True
        
    @pytest.mark.asyncio
    async def test_estimate_cost(self, ideogram_provider):
        """Test cost estimation."""
        # V2 model
        request = GenerationRequest(
            prompt="A logo",
            generation_type=GenerationType.IMAGE,
            model="ideogram-v2",
            parameters={"number_of_images": 1}
        )
        cost = await ideogram_provider.estimate_cost(request)
        assert cost == 0.08  # $0.08 per image
        
        # V2 Turbo model
        request.model = "ideogram-v2-turbo"
        cost = await ideogram_provider.estimate_cost(request)
        assert cost == 0.05  # $0.05 per image
        
        # Multiple images
        request.parameters["number_of_images"] = 3
        cost = await ideogram_provider.estimate_cost(request)
        assert abs(cost - 0.15) < 0.001  # 3 * $0.05 (with floating point tolerance)
        
        # With upscaling
        request.parameters["upscale"] = True
        request.parameters["number_of_images"] = 1
        cost = await ideogram_provider.estimate_cost(request)
        assert cost == 0.07  # $0.05 + $0.02 for upscaling
        
    def test_estimate_generation_time(self, ideogram_provider):
        """Test generation time estimation."""
        # Turbo model (fastest)
        request = GenerationRequest(
            prompt="A logo",
            generation_type=GenerationType.IMAGE,
            model="turbo",
            parameters={"number_of_images": 1}
        )
        time = ideogram_provider._estimate_generation_time(request)
        assert time == 10.0  # Base turbo time
        
        # V2 model
        request.model = "ideogram-v2"
        time = ideogram_provider._estimate_generation_time(request)
        assert time == 20.0  # Slower but higher quality
        
        # V3 model
        request.model = "ideogram-v3"
        time = ideogram_provider._estimate_generation_time(request)
        assert time == 25.0  # Latest model
        
        # Multiple images
        request.parameters["number_of_images"] = 3
        time = ideogram_provider._estimate_generation_time(request)
        assert time == 35.0  # 25 + 2*5
        
    def test_validate_aspect_ratio(self, ideogram_provider):
        """Test aspect ratio validation."""
        # Common formats
        assert ideogram_provider._validate_aspect_ratio("16:9") == IdeogramAspectRatio.ASPECT_16_9
        assert ideogram_provider._validate_aspect_ratio("1:1") == IdeogramAspectRatio.ASPECT_1_1
        assert ideogram_provider._validate_aspect_ratio("3:1") == IdeogramAspectRatio.ASPECT_3_1
        
        # Invalid format
        assert ideogram_provider._validate_aspect_ratio("invalid") is None
        
    def test_validate_style(self, ideogram_provider):
        """Test style validation."""
        # Lowercase variants
        assert ideogram_provider._validate_style("realistic") == IdeogramStyle.REALISTIC
        assert ideogram_provider._validate_style("design") == IdeogramStyle.DESIGN
        assert ideogram_provider._validate_style("3d") == IdeogramStyle.RENDER_3D
        assert ideogram_provider._validate_style("anime") == IdeogramStyle.ANIME
        
        # Direct enum
        assert ideogram_provider._validate_style("REALISTIC") == IdeogramStyle.REALISTIC
        
        # Invalid
        assert ideogram_provider._validate_style("invalid") is None
        
    @pytest.mark.asyncio
    async def test_prepare_request_body_v3(self, ideogram_provider):
        """Test request body preparation for V3 API."""
        request = GenerationRequest(
            prompt="Professional logo for tech company",
            generation_type=GenerationType.IMAGE,
            model="ideogram-v3",
            parameters={
                "number_of_images": 2,
                "style": "design",
                "aspect_ratio": "1:1",
                "negative_prompt": "amateur, pixelated",
                "seed": 12345,
                "color_palette": ["#FF5733", "#C70039", "#900C3F"],
                "magic_prompt_option": "ON",
            }
        )
        
        body, use_v3 = await ideogram_provider._prepare_request_body(request)
        
        assert use_v3 is True
        assert body["prompt"] == "Professional logo for tech company"
        assert body["options"]["model"] == IdeogramModel.V3.value
        assert body["options"]["count"] == 2
        assert body["options"]["style_type"] == IdeogramStyle.DESIGN.value
        assert body["options"]["aspect_ratio"] == IdeogramAspectRatio.ASPECT_1_1.value
        assert body["options"]["negative_prompt"] == "amateur, pixelated"
        assert body["options"]["seed"] == 12345
        assert body["options"]["color_palette"] == ["#FF5733", "#C70039", "#900C3F"]
        assert body["options"]["magic_prompt_option"] == "ON"
        
    @pytest.mark.asyncio
    async def test_prepare_request_body_v2(self, ideogram_provider):
        """Test request body preparation for V2 API."""
        request = GenerationRequest(
            prompt="Anime character portrait",
            generation_type=GenerationType.IMAGE,
            model="ideogram-v2",
            parameters={
                "number_of_images": 1,
                "style": "anime",
                "aspect_ratio": "9:16",
            }
        )
        
        body, use_v3 = await ideogram_provider._prepare_request_body(request)
        
        assert use_v3 is False
        assert body["image_request"]["prompt"] == "Anime character portrait"
        assert body["image_request"]["model"] == IdeogramModel.V2.value
        assert body["image_request"]["num_images"] == 1
        assert body["image_request"]["style_type"] == IdeogramStyle.ANIME.value
        assert body["image_request"]["aspect_ratio"] == IdeogramAspectRatio.ASPECT_9_16.value
        assert body["image_request"]["magic_prompt_option"] == "AUTO"
        
    @pytest.mark.asyncio
    async def test_download_image(self, ideogram_provider, mock_session):
        """Test image download functionality."""
        ideogram_provider._session = mock_session
        
        # Mock download response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"image_data"
        
        mock_session.get.return_value = create_async_context_manager(mock_resp)
        
        image_data = await ideogram_provider._download_image("http://example.com/image.png")
        
        assert image_data == b"image_data"
        mock_session.get.assert_called_once_with("http://example.com/image.png")
        
    @pytest.mark.asyncio
    async def test_generate_v3(self, ideogram_provider, mock_session):
        """Test V3 generation flow."""
        ideogram_provider._session = mock_session
        
        # Mock generation response
        gen_resp = AsyncMock()
        gen_resp.status = 200
        gen_resp.json.return_value = {
            "images": [{
                "url": "http://example.com/result.png",
                "seed": 12345,
                "style_type": "DESIGN",
                "is_image_safe": True,
            }]
        }
        
        # Mock image download
        img_resp = AsyncMock()
        img_resp.status = 200
        img_resp.read.return_value = b"generated_image_data"
        
        # Setup post for generation
        mock_session.post.return_value = create_async_context_manager(gen_resp)
        
        # Setup get for image download
        mock_session.get.return_value = create_async_context_manager(img_resp)
        
        request = GenerationRequest(
            prompt="A modern logo",
            generation_type=GenerationType.IMAGE,
            model="ideogram-v3",
            parameters={"style": "design"},
            output_path=Path("/tmp/test")
        )
        
        result = await ideogram_provider._generate(request)
        
        assert isinstance(result, GenerationResult)
        assert result.success is True
        assert result.cost == 0.10  # V3 cost
        assert result.metadata["images_metadata"][0]["seed"] == 12345
        
    @pytest.mark.asyncio
    async def test_generate_v2_turbo(self, ideogram_provider, mock_session):
        """Test V2 Turbo generation flow."""
        ideogram_provider._session = mock_session
        
        # Mock generation response
        gen_resp = AsyncMock()
        gen_resp.status = 200
        gen_resp.json.return_value = {
            "data": [{
                "url": "http://example.com/result.png",
                "prompt": "Enhanced prompt",
                "resolution": "1024x1024",
                "seed": 54321,
                "style_type": "REALISTIC",
                "is_image_safe": True,
            }]
        }
        
        # Mock image download
        img_resp = AsyncMock()
        img_resp.status = 200
        img_resp.read.return_value = b"turbo_image_data"
        
        mock_session.post.return_value = create_async_context_manager(gen_resp)
        mock_session.get.return_value = create_async_context_manager(img_resp)
        
        request = GenerationRequest(
            prompt="A quick sketch",
            generation_type=GenerationType.IMAGE,
            model="turbo",
            output_path=Path("/tmp/test")
        )
        
        result = await ideogram_provider._generate(request)
        
        assert result.success is True
        assert result.cost == 0.05  # Turbo cost
        
    @pytest.mark.asyncio
    async def test_generate_error_handling(self, ideogram_provider, mock_session):
        """Test error handling in generation."""
        ideogram_provider._session = mock_session
        
        # Mock 401 error
        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_resp.text.return_value = "Unauthorized"
        
        mock_session.post.return_value = create_async_context_manager(mock_resp)
        
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="ideogram-v2",
        )
        
        result = await ideogram_provider._generate(request)
        
        assert result.success is False
        assert "Invalid API key" in result.error
        
    @pytest.mark.asyncio
    async def test_upscale_image(self, ideogram_provider, mock_session):
        """Test image upscaling functionality."""
        ideogram_provider._session = mock_session
        
        # Create a test image file
        test_image = Path("/tmp/test_image.png")
        test_image.parent.mkdir(exist_ok=True)
        test_image.write_bytes(b"original_image_data")
        
        # Mock upscale response
        upscale_resp = AsyncMock()
        upscale_resp.status = 200
        upscale_resp.json.return_value = {
            "url": "http://example.com/upscaled.png"
        }
        
        # Mock download response
        download_resp = AsyncMock()
        download_resp.status = 200
        download_resp.read.return_value = b"upscaled_image_data"
        
        mock_session.post.return_value = create_async_context_manager(upscale_resp)
        mock_session.get.return_value = create_async_context_manager(download_resp)
        
        result = await ideogram_provider.upscale_image(test_image)
        
        assert result.success is True
        assert result.cost == 0.02  # Upscaling cost
        assert result.file_path.name == "test_image_upscaled.png"
        
        # Cleanup
        if test_image.exists():
            test_image.unlink()
        if result.file_path and result.file_path.exists():
            result.file_path.unlink()
            
    @pytest.mark.asyncio
    async def test_check_status(self, ideogram_provider, mock_session):
        """Test provider status check."""
        ideogram_provider._session = mock_session
        
        # Mock successful response (even 400 means API is working)
        mock_resp = AsyncMock()
        mock_resp.status = 400  # Bad request but API is responsive
        
        mock_session.post.return_value = create_async_context_manager(mock_resp)
        
        status = await ideogram_provider.check_status()
        
        assert status == ProviderStatus.AVAILABLE