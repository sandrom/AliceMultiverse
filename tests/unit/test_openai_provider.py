"""Test OpenAI provider implementation."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from contextlib import asynccontextmanager

from alicemultiverse.providers import (
    AuthenticationError,
    GenerationRequest,
    GenerationType,
    ProviderStatus,
    RateLimitError,
)
from alicemultiverse.providers.openai_provider import OpenAIProvider


class TestOpenAIProvider:
    """Test OpenAI provider functionality."""
    
    @pytest.fixture
    def provider(self):
        """Create test provider with mock API key."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            return OpenAIProvider()
    
    def test_init_requires_api_key(self):
        """Test that initialization requires API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                OpenAIProvider()
    
    def test_name_and_capabilities(self, provider):
        """Test provider name and capabilities."""
        assert provider.name == "openai"
        
        caps = provider.capabilities
        assert GenerationType.IMAGE in caps.generation_types
        assert GenerationType.TEXT in caps.generation_types
        assert "dall-e-3" in caps.models
        assert "gpt-4-vision-preview" in caps.models
        assert caps.max_resolution["width"] == 1792
        assert caps.max_resolution["height"] == 1792
    
    def test_get_default_model(self, provider):
        """Test default model selection."""
        assert provider.get_default_model(GenerationType.IMAGE) == "dall-e-3"
        assert provider.get_default_model(GenerationType.TEXT) == "gpt-4o-mini"
    
    def test_get_models_for_type(self, provider):
        """Test getting models by type."""
        image_models = provider.get_models_for_type(GenerationType.IMAGE)
        assert "dall-e-3" in image_models
        assert "dall-e-2" in image_models
        
        text_models = provider.get_models_for_type(GenerationType.TEXT)
        assert "gpt-4-vision-preview" in text_models
        assert "gpt-4o" in text_models
    
    @pytest.mark.asyncio
    async def test_check_status(self, provider):
        """Test API status check."""
        mock_response = Mock()
        mock_response.status = 200
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_get(*args, **kwargs):
            yield mock_response
        
        mock_session.get = mock_get
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            status = await provider.check_status()
            assert status == ProviderStatus.AVAILABLE
    
    def test_build_dalle_params(self, provider):
        """Test DALL-E parameter building."""
        request = GenerationRequest(
            prompt="A test image",
            generation_type=GenerationType.IMAGE,
            parameters={
                "size": "1024x1792",
                "quality": "hd",
                "style": "natural"
            }
        )
        
        params = provider._build_dalle_params(request, "dall-e-3")
        
        assert params["prompt"] == "A test image"
        assert params["size"] == "1024x1792"
        assert params["quality"] == "hd"
        assert params["style"] == "natural"
        assert params["n"] == 1
    
    def test_calculate_dalle_cost(self, provider):
        """Test DALL-E cost calculation."""
        # Standard quality
        params = {"quality": "standard", "size": "1024x1024"}
        cost = provider._calculate_dalle_cost("dall-e-3", params)
        assert cost == 0.040
        
        # HD quality
        params = {"quality": "hd", "size": "1024x1792"}
        cost = provider._calculate_dalle_cost("dall-e-3", params)
        assert cost == 0.120
        
        # DALL-E 2
        params = {"size": "512x512"}
        cost = provider._calculate_dalle_cost("dall-e-2", params)
        assert cost == 0.018
    
    @pytest.mark.asyncio
    async def test_generate_image_success(self, provider):
        """Test successful image generation."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": [{
                "url": "https://example.com/image.png",
                "revised_prompt": "A detailed test image"
            }]
        })
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            yield mock_response
        
        mock_session.post = mock_post
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            with patch("alicemultiverse.providers.openai_provider.download_file") as mock_download:
                mock_download.return_value = None
                
                request = GenerationRequest(
                    prompt="Test image",
                    generation_type=GenerationType.IMAGE,
                    output_path=Path("/tmp/test.png")
                )
                
                result = await provider.generate(request)
                
                assert result.success
                assert result.provider == "openai"
                assert result.model == "dall-e-3"
                assert result.cost == 0.040
                assert result.metadata["revised_prompt"] == "A detailed test image"
    
    @pytest.mark.asyncio
    async def test_generate_rate_limit(self, provider):
        """Test rate limit handling."""
        mock_response = Mock()
        mock_response.status = 429
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            yield mock_response
        
        mock_session.post = mock_post
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            request = GenerationRequest(
                prompt="Test",
                generation_type=GenerationType.IMAGE
            )
            
            result = await provider.generate(request)
            assert not result.success
            assert "rate limit" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_generate_auth_error(self, provider):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status = 401
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            yield mock_response
        
        mock_session.post = mock_post
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            request = GenerationRequest(
                prompt="Test",
                generation_type=GenerationType.IMAGE
            )
            
            result = await provider.generate(request)
            assert not result.success
            assert "api key" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_image(self, provider):
        """Test image analysis with GPT-4 Vision."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": "This is a test image analysis"
                }
            }],
            "usage": {
                "total_tokens": 150
            }
        })
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            yield mock_response
        
        mock_session.post = mock_post
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            with patch.object(provider, "_encode_image", return_value="base64data"):
                request = GenerationRequest(
                    prompt="Analyze this image",
                    generation_type=GenerationType.TEXT,
                    model="gpt-4-vision-preview",
                    reference_assets=["/tmp/test.jpg"]
                )
                
                result = await provider.generate(request)
                
                assert result.success
                assert result.metadata["analysis"] == "This is a test image analysis"
                assert result.metadata["tokens_used"] == 150
                assert result.cost == 0.0015  # 150 tokens * 0.01/1000
    
    @pytest.mark.asyncio
    async def test_context_manager(self, provider):
        """Test async context manager."""
        async with provider as p:
            assert p is provider
        
        # Session should be closed
        assert provider._session is None or provider._session.closed