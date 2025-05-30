"""Tests for Google AI provider."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, create_autospec
import aiohttp
from datetime import datetime
from pathlib import Path
import base64

from alicemultiverse.providers.google_ai_provider import GoogleAIProvider, GoogleAIBackend
from alicemultiverse.providers.types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderStatus,
)


@pytest.fixture
def google_ai_provider():
    """Create a Google AI provider instance with Gemini backend."""
    return GoogleAIProvider(api_key="test_api_key", backend=GoogleAIBackend.GEMINI)


@pytest.fixture
def vertex_ai_provider():
    """Create a Google AI provider instance with Vertex backend."""
    return GoogleAIProvider(
        api_key="test_access_token",
        backend=GoogleAIBackend.VERTEX,
        project_id="test-project",
        location="us-central1"
    )


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


class TestGoogleAIProvider:
    """Test Google AI provider functionality."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        provider = GoogleAIProvider(api_key="test_key")
        assert provider.api_key == "test_key"
        assert provider.backend == GoogleAIBackend.GEMINI
        
    def test_init_with_vertex_backend(self):
        """Test initialization with Vertex AI backend."""
        provider = GoogleAIProvider(
            api_key="test_key",
            backend=GoogleAIBackend.VERTEX,
            project_id="my-project"
        )
        assert provider.backend == GoogleAIBackend.VERTEX
        assert provider.project_id == "my-project"
        assert provider.location == "us-central1"
        
    def test_init_missing_credentials(self):
        """Test initialization fails without credentials."""
        with pytest.raises(ValueError, match="Google AI requires"):
            GoogleAIProvider()
            
    def test_init_vertex_missing_project(self):
        """Test Vertex backend fails without project ID."""
        with pytest.raises(ValueError, match="Vertex AI backend requires"):
            GoogleAIProvider(api_key="test_key", backend=GoogleAIBackend.VERTEX)
    
    def test_model_mapping(self, google_ai_provider):
        """Test model name mapping."""
        assert google_ai_provider.MODELS["imagen-3"] == "imagen-3.0-generate-002"
        assert google_ai_provider.MODELS["imagen"] == "imagen-3.0-generate-002"
        assert google_ai_provider.MODELS["veo-2"] == "veo-002"
        assert google_ai_provider.MODELS["veo"] == "veo-002"
        
    def test_provider_name(self, google_ai_provider):
        """Test provider name property."""
        assert google_ai_provider.name == "google_ai"
        
    def test_capabilities(self, google_ai_provider):
        """Test capability reporting."""
        caps = google_ai_provider.capabilities
        
        assert GenerationType.IMAGE in caps.generation_types
        assert GenerationType.VIDEO in caps.generation_types
        assert "imagen-3" in caps.models
        assert "veo-2" in caps.models
        assert caps.max_resolution["width"] == 2048
        assert caps.max_resolution["height"] == 2048
        assert "text_to_image" in caps.features
        assert "text_to_video" in caps.features
        assert "image_to_video" in caps.features
        assert caps.supports_batch is True
        
    @pytest.mark.asyncio
    async def test_estimate_cost_imagen(self, google_ai_provider):
        """Test cost estimation for Imagen."""
        # Single image
        request = GenerationRequest(
            prompt="A sunset",
            generation_type=GenerationType.IMAGE,
            model="imagen-3",
            parameters={"number_of_images": 1}
        )
        cost = await google_ai_provider.estimate_cost(request)
        assert cost == 0.03  # $0.03 per image
        
        # Multiple images
        request.parameters["number_of_images"] = 4
        cost = await google_ai_provider.estimate_cost(request)
        assert cost == 0.12  # 4 * $0.03
        
    @pytest.mark.asyncio
    async def test_estimate_cost_veo(self, google_ai_provider):
        """Test cost estimation for Veo."""
        request = GenerationRequest(
            prompt="A cat playing",
            generation_type=GenerationType.VIDEO,
            model="veo-2",
        )
        cost = await google_ai_provider.estimate_cost(request)
        assert cost == 0.10  # $0.10 per video
        
    def test_estimate_generation_time(self, google_ai_provider):
        """Test generation time estimation."""
        # Image generation
        image_request = GenerationRequest(
            prompt="A sunset",
            generation_type=GenerationType.IMAGE,
            model="imagen-3",
            parameters={"number_of_images": 1}
        )
        time = google_ai_provider._estimate_generation_time(image_request)
        assert time == 5.0  # Base time
        
        # Multiple images
        image_request.parameters["number_of_images"] = 3
        time = google_ai_provider._estimate_generation_time(image_request)
        assert time == 9.0  # 5 + 2*2
        
        # Video generation
        video_request = GenerationRequest(
            prompt="A sunset",
            generation_type=GenerationType.VIDEO,
            model="veo-2",
        )
        time = google_ai_provider._estimate_generation_time(video_request)
        assert time == 60.0  # Base video time
        
    def test_validate_aspect_ratio(self, google_ai_provider):
        """Test aspect ratio validation."""
        assert google_ai_provider._validate_aspect_ratio("16:9", "imagen") is True
        assert google_ai_provider._validate_aspect_ratio("21:9", "imagen") is False
        assert google_ai_provider._validate_aspect_ratio("16:9", "veo") is True
        assert google_ai_provider._validate_aspect_ratio("4:3", "veo") is False
        
    def test_get_base_url(self, google_ai_provider, vertex_ai_provider):
        """Test base URL generation."""
        assert google_ai_provider._get_base_url() == "https://generativelanguage.googleapis.com"
        assert vertex_ai_provider._get_base_url() == "https://us-central1-aiplatform.googleapis.com"
        
    def test_get_headers(self, google_ai_provider, vertex_ai_provider):
        """Test header generation."""
        # Gemini headers
        headers = google_ai_provider._get_headers()
        assert headers["x-goog-api-key"] == "test_api_key"
        assert headers["Content-Type"] == "application/json"
        
        # Vertex headers
        vertex_ai_provider.access_token = "test_token"
        headers = vertex_ai_provider._get_headers()
        assert headers["Authorization"] == "Bearer test_token"
        
    @pytest.mark.asyncio
    async def test_prepare_imagen_request_gemini(self, google_ai_provider):
        """Test Imagen request preparation for Gemini backend."""
        request = GenerationRequest(
            prompt="A beautiful sunset",
            generation_type=GenerationType.IMAGE,
            model="imagen-3",
            parameters={
                "number_of_images": 2,
                "negative_prompt": "clouds",
                "aspect_ratio": "16:9",
                "seed": 42,
            }
        )
        
        body = await google_ai_provider._prepare_imagen_request(request)
        
        assert body["prompt"] == "A beautiful sunset"
        assert body["config"]["number_of_images"] == 2
        assert body["config"]["negative_prompt"] == "clouds"
        assert body["config"]["aspect_ratio"] == "16:9"
        assert body["config"]["seed"] == 42
        
    @pytest.mark.asyncio
    async def test_prepare_imagen_request_vertex(self, vertex_ai_provider):
        """Test Imagen request preparation for Vertex backend."""
        request = GenerationRequest(
            prompt="A mountain landscape",
            generation_type=GenerationType.IMAGE,
            model="imagen-3",
            parameters={
                "number_of_images": 1,
                "aspect_ratio": "4:3",
            }
        )
        
        body = await vertex_ai_provider._prepare_imagen_request(request)
        
        assert body["instances"][0]["prompt"] == "A mountain landscape"
        assert body["parameters"]["sampleCount"] == 1
        assert body["parameters"]["aspectRatio"] == "4:3"
        
    @pytest.mark.asyncio
    async def test_prepare_veo_request_text_to_video(self, google_ai_provider):
        """Test Veo request preparation for text-to-video."""
        request = GenerationRequest(
            prompt="A cat playing with yarn",
            generation_type=GenerationType.VIDEO,
            model="veo-2",
            parameters={
                "aspect_ratio": "16:9",
                "negative_prompt": "blurry",
                "seed": 123,
            }
        )
        
        body = await google_ai_provider._prepare_veo_request(request)
        
        assert body["text_prompt"] == "A cat playing with yarn"
        assert body["config"]["aspect_ratio"] == "16:9"
        assert body["config"]["negative_prompt"] == "blurry"
        assert body["config"]["seed"] == 123
        
    @pytest.mark.asyncio
    async def test_poll_long_running_operation(self, google_ai_provider, mock_session):
        """Test polling for long-running operations."""
        google_ai_provider._session = mock_session
        
        # Mock status responses - pending then done
        status_responses = [
            {"done": False},
            {"done": True, "response": {"predictions": [{"data": "result"}]}}
        ]
        response_iter = iter(status_responses)
        
        # Create mock responses
        mock_responses = []
        for status_data in status_responses:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json.return_value = status_data
            mock_responses.append(mock_resp)
        
        # Setup side effect to return different responses
        response_iter = iter(mock_responses)
        mock_session.get.side_effect = lambda *args, **kwargs: create_async_context_manager(next(response_iter))
        
        result = await google_ai_provider._poll_long_running_operation("operations/12345")
        
        assert result["predictions"][0]["data"] == "result"
        
    @pytest.mark.asyncio
    async def test_generate_imagen(self, google_ai_provider, mock_session):
        """Test Imagen generation flow."""
        google_ai_provider._session = mock_session
        
        # Mock generation response
        gen_resp = AsyncMock()
        gen_resp.status = 200
        gen_resp.json.return_value = {
            "generated_images": [{
                "image": {"image_bytes": b"fake_image_data"}
            }]
        }
        
        mock_session.post.return_value = create_async_context_manager(gen_resp)
        
        request = GenerationRequest(
            prompt="A sunset",
            generation_type=GenerationType.IMAGE,
            model="imagen-3",
            parameters={"number_of_images": 1},
            output_path=Path("/tmp/test")
        )
        
        result = await google_ai_provider._generate(request)
        
        assert isinstance(result, GenerationResult)
        assert result.success is True
        assert result.cost == 0.03
        assert result.metadata["model"] == "imagen-3.0-generate-002"
        
    @pytest.mark.asyncio
    async def test_generate_veo(self, google_ai_provider, mock_session):
        """Test Veo video generation flow."""
        google_ai_provider._session = mock_session
        
        # Mock generation response
        gen_resp = AsyncMock()
        gen_resp.status = 200
        gen_resp.json.return_value = {
            "videos": [{
                "video_bytes": b"fake_video_data"
            }]
        }
        
        mock_session.post.return_value = create_async_context_manager(gen_resp)
        
        request = GenerationRequest(
            prompt="A flying bird",
            generation_type=GenerationType.VIDEO,
            model="veo-2",
            output_path=Path("/tmp/test")
        )
        
        result = await google_ai_provider._generate(request)
        
        assert isinstance(result, GenerationResult)
        assert result.success is True
        assert result.cost == 0.10
        assert result.metadata["generation_type"] == "video"
        
    @pytest.mark.asyncio
    async def test_check_status(self, google_ai_provider, mock_session):
        """Test provider status check."""
        google_ai_provider._session = mock_session
        
        # Mock successful response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = {"models": []}
        
        mock_session.get.return_value = create_async_context_manager(mock_resp)
        
        status = await google_ai_provider.check_status()
        
        assert status == ProviderStatus.AVAILABLE