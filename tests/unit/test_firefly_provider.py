"""Tests for Adobe Firefly provider."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, create_autospec

import aiohttp
import pytest

from alicemultiverse.providers.firefly_provider import FireflyProvider
from alicemultiverse.providers.types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderStatus,
)


@pytest.fixture
def firefly_provider():
    """Create a Firefly provider instance."""
    return FireflyProvider(api_key="test_client_id:test_client_secret")


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


class TestFireflyProvider:
    """Test Firefly provider functionality."""

    def test_init_with_combined_key(self):
        """Test initialization with combined key format."""
        provider = FireflyProvider(api_key="client123:secret456")
        assert provider.client_id == "client123"
        assert provider.client_secret == "secret456"

    def test_init_with_separate_keys(self):
        """Test initialization with separate keys."""
        provider = FireflyProvider(api_key="client123", api_secret="secret456")
        assert provider.client_id == "client123"
        assert provider.client_secret == "secret456"

    def test_init_missing_credentials(self):
        """Test initialization fails without credentials."""
        with pytest.raises(ValueError, match="Adobe Firefly requires"):
            FireflyProvider()

    def test_model_mapping(self, firefly_provider):
        """Test model name mapping."""
        assert firefly_provider.MODELS["firefly-v3"] == "firefly_v3"
        assert firefly_provider.MODELS["firefly"] == "firefly_v3"
        assert firefly_provider.MODELS["firefly-fill"] == "firefly_v3"
        assert firefly_provider.MODELS["firefly-expand"] == "firefly_v3"

    def test_provider_name(self, firefly_provider):
        """Test provider name property."""
        assert firefly_provider.name == "firefly"

    def test_capabilities(self, firefly_provider):
        """Test capability reporting."""
        caps = firefly_provider.capabilities

        assert GenerationType.IMAGE in caps.generation_types
        assert "firefly-v3" in caps.models
        assert "firefly-fill" in caps.models
        assert caps.max_resolution["width"] == 2048
        assert caps.max_resolution["height"] == 2048
        assert "text_to_image" in caps.features
        assert "inpainting" in caps.features
        assert "outpainting" in caps.features
        assert caps.supports_streaming is False
        assert caps.supports_batch is False

    @pytest.mark.asyncio
    async def test_estimate_cost(self, firefly_provider):
        """Test cost estimation."""
        # Basic text-to-image
        request = GenerationRequest(
            prompt="A sunset",
            generation_type=GenerationType.IMAGE,
            model="firefly-v3",
            parameters={"width": 1024, "height": 1024, "num_images": 1}
        )
        cost = await firefly_provider.estimate_cost(request)
        assert cost == 0.002  # Base cost

        # Multiple images
        request.parameters["num_images"] = 4
        cost = await firefly_provider.estimate_cost(request)
        assert cost == 0.008  # 4 * base cost

        # Larger image
        request.parameters["width"] = 2048
        request.parameters["height"] = 2048
        request.parameters["num_images"] = 1
        cost = await firefly_provider.estimate_cost(request)
        assert cost == 0.003  # 1.5x for larger image

        # With image input
        request.reference_assets = ["dummy_ref"]
        cost = await firefly_provider.estimate_cost(request)
        assert cost == 0.0036  # 1.2x for image input

    def test_estimate_generation_time(self, firefly_provider):
        """Test generation time estimation."""
        request = GenerationRequest(
            prompt="A sunset",
            generation_type=GenerationType.IMAGE,
            model="firefly-v3",
            parameters={"width": 1024, "height": 1024}
        )

        time = firefly_provider._estimate_generation_time(request)
        assert 10 <= time <= 20  # Base time plus size factor

        # With image input
        request.reference_assets = ["dummy_ref"]
        time = firefly_provider._estimate_generation_time(request)
        assert 15 <= time <= 25  # Additional time for image input

    def test_get_model_key(self, firefly_provider):
        """Test model key resolution."""
        assert firefly_provider._get_model_key("firefly-v3") == "firefly_v3"
        assert firefly_provider._get_model_key("firefly") == "firefly_v3"
        assert firefly_provider._get_model_key("unknown") == "firefly_v3"  # Default
        assert firefly_provider._get_model_key("firefly_v3") == "firefly_v3"  # Direct key

    def test_get_endpoint_for_model(self, firefly_provider):
        """Test endpoint selection based on model."""
        assert firefly_provider._get_endpoint_for_model("firefly") == "/v3/images/generate"
        assert firefly_provider._get_endpoint_for_model("firefly-fill") == "/v3/images/fill"
        assert firefly_provider._get_endpoint_for_model("firefly-expand") == "/v3/images/expand"
        assert firefly_provider._get_endpoint_for_model("firefly-composite") == "/v3/images/composite"
        assert firefly_provider._get_endpoint_for_model("firefly-similar") == "/v3/images/similar"

    @pytest.mark.asyncio
    async def test_authenticate(self, firefly_provider, mock_session):
        """Test authentication flow."""
        firefly_provider._session = mock_session

        # Mock successful auth response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }

        # Setup context manager
        mock_session.post.return_value = create_async_context_manager(mock_resp)

        await firefly_provider._authenticate()

        assert firefly_provider.access_token == "test_token"
        assert firefly_provider.token_expires_at is not None

        # Verify auth request
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://ims-na1.adobelogin.com/ims/token/v3"
        assert call_args[1]["data"]["grant_type"] == "client_credentials"
        assert call_args[1]["data"]["client_id"] == "test_client_id"
        assert call_args[1]["data"]["client_secret"] == "test_client_secret"

    @pytest.mark.asyncio
    async def test_authenticate_reuse_valid_token(self, firefly_provider, mock_session):
        """Test that valid tokens are reused."""
        firefly_provider._session = mock_session
        firefly_provider.access_token = "existing_token"
        firefly_provider.token_expires_at = datetime.now().timestamp() + 3600  # Valid for 1 hour

        await firefly_provider._authenticate()

        # Should not make a new auth request
        mock_session.post.assert_not_called()
        assert firefly_provider.access_token == "existing_token"

    @pytest.mark.asyncio
    async def test_upload_image(self, firefly_provider, mock_session):
        """Test image upload."""
        firefly_provider._session = mock_session
        firefly_provider.access_token = "test_token"
        firefly_provider.client_id = "test_client_id"
        # Mark token as valid to skip auth
        firefly_provider.token_expires_at = datetime.now().timestamp() + 3600

        # Mock upload response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = {
            "images": [{"id": "uploaded_image_id"}]
        }

        mock_session.post.return_value = create_async_context_manager(mock_resp)

        image_id = await firefly_provider._upload_image(b"fake_image_data")

        assert image_id == "uploaded_image_id"

        # Verify upload request
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://firefly-api.adobe.io/v2/storage/image"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
        assert call_args[1]["headers"]["x-api-key"] == "test_client_id"
        assert call_args[1]["data"] == b"fake_image_data"

    @pytest.mark.asyncio
    async def test_prepare_request_body_text_to_image(self, firefly_provider):
        """Test request body preparation for text-to-image."""
        request = GenerationRequest(
            prompt="A beautiful sunset",
            generation_type=GenerationType.IMAGE,
            model="firefly-v3",
            parameters={
                "width": 1024,
                "height": 1024,
                "num_images": 2,
                "seed": 42,
                "negative_prompt": "clouds",
                "style_preset": "watercolor",
                "content_class": "photo",
                "tileable": True,
            }
        )

        body = await firefly_provider._prepare_request_body(request)

        assert body["prompt"] == "A beautiful sunset"
        assert body["negativePrompt"] == "clouds"
        assert body["numVariations"] == 2
        assert body["size"]["width"] == 1024
        assert body["size"]["height"] == 1024
        assert body["seeds"] == [42]
        assert body["style"]["presets"] == ["watercolor"]
        assert body["contentClass"] == "photo"
        assert body["tileable"] is True
        assert body["promptBiasingLocaleCode"] == "en-US"

    @pytest.mark.asyncio
    async def test_poll_async_job_success(self, firefly_provider, mock_session):
        """Test polling async job to success."""
        firefly_provider._session = mock_session
        firefly_provider.access_token = "test_token"
        firefly_provider.client_id = "test_client_id"
        # Mark token as valid to skip auth
        firefly_provider.token_expires_at = datetime.now().timestamp() + 3600

        # Mock status responses - pending then succeeded
        status_responses = [
            {"status": "pending"},
            {"status": "succeeded", "outputs": [{"image": {"url": "result_url"}}]}
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

        result = await firefly_provider._poll_async_job("http://status_url", "http://cancel_url")

        assert result["status"] == "succeeded"
        assert len(result["outputs"]) == 1

    @pytest.mark.asyncio
    async def test_generate_text_to_image(self, firefly_provider, mock_session):
        """Test full text-to-image generation flow."""
        firefly_provider._session = mock_session
        firefly_provider.access_token = "test_token"
        firefly_provider.client_id = "test_client_id"
        # Mark token as valid to skip auth
        firefly_provider.token_expires_at = datetime.now().timestamp() + 3600

        # Mock generation response
        gen_resp = AsyncMock()
        gen_resp.status = 200
        gen_resp.json.return_value = {
            "outputs": [{
                "image": {"url": "http://result.png"},
                "seed": 12345
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
            prompt="A sunset",
            generation_type=GenerationType.IMAGE,
            model="firefly-v3",
            parameters={"width": 1024, "height": 1024, "num_images": 1},
            output_path=Path("/tmp/test")
        )

        result = await firefly_provider._generate(request)

        assert isinstance(result, GenerationResult)
        assert result.success is True
        assert result.cost == 0.002
        assert result.metadata["seed"] == 12345

    @pytest.mark.asyncio
    async def test_check_status(self, firefly_provider, mock_session):
        """Test provider status check."""
        firefly_provider._session = mock_session

        # Mock successful auth
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }

        mock_session.post.return_value = create_async_context_manager(mock_resp)

        status = await firefly_provider.check_status()

        assert status == ProviderStatus.AVAILABLE
