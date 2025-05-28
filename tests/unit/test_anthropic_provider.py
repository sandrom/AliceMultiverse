"""Test Anthropic provider implementation."""

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
from alicemultiverse.providers.anthropic_provider import AnthropicProvider


class TestAnthropicProvider:
    """Test Anthropic provider functionality."""
    
    @pytest.fixture
    def provider(self):
        """Create test provider with mock API key."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            return AnthropicProvider()
    
    def test_init_requires_api_key(self):
        """Test that initialization requires API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                AnthropicProvider()
    
    def test_name_and_capabilities(self, provider):
        """Test provider name and capabilities."""
        assert provider.name == "anthropic"
        
        caps = provider.capabilities
        assert GenerationType.TEXT in caps.generation_types
        assert GenerationType.IMAGE not in caps.generation_types
        assert "claude-3-opus-20240229" in caps.models
        assert "claude-3-haiku-20240307" in caps.models
        assert "vision" in caps.features
        assert "image_analysis" in caps.features
    
    def test_get_default_model(self, provider):
        """Test default model selection."""
        assert provider.get_default_model(GenerationType.TEXT) == "claude-3-haiku-20240307"
        assert provider.get_default_model(GenerationType.IMAGE) is None
    
    def test_get_models_for_type(self, provider):
        """Test getting models by type."""
        text_models = provider.get_models_for_type(GenerationType.TEXT)
        assert "claude-3-opus-20240229" in text_models
        assert "claude-3-sonnet-20240229" in text_models
        assert "claude-3-haiku-20240307" in text_models
        assert "claude-3-5-sonnet-20241022" in text_models
        
        image_models = provider.get_models_for_type(GenerationType.IMAGE)
        assert len(image_models) == 0
    
    @pytest.mark.asyncio
    async def test_check_status(self, provider):
        """Test API status check."""
        mock_response = Mock()
        mock_response.status = 200
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            yield mock_response
        
        mock_session.post = mock_post
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            status = await provider.check_status()
            assert status == ProviderStatus.AVAILABLE
    
    def test_calculate_cost(self, provider):
        """Test cost calculation for different models."""
        # Haiku model
        pricing = provider.PRICING["claude-3-haiku-20240307"]
        input_cost = (1000 / 1_000_000) * pricing["input"]
        output_cost = (500 / 1_000_000) * pricing["output"]
        expected = input_cost + output_cost
        assert expected == (1000 / 1_000_000) * 0.25 + (500 / 1_000_000) * 1.25
        
        # Opus model
        pricing = provider.PRICING["claude-3-opus-20240229"]
        input_cost = (1000 / 1_000_000) * pricing["input"]
        output_cost = (500 / 1_000_000) * pricing["output"]
        expected = input_cost + output_cost
        assert expected == (1000 / 1_000_000) * 15.0 + (500 / 1_000_000) * 75.0
    
    @pytest.mark.asyncio
    async def test_analyze_image_success(self, provider):
        """Test successful image analysis."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "content": [{
                "text": "This image shows a beautiful landscape"
            }],
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 50
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
                    reference_assets=["/tmp/test.jpg"]
                )
                
                result = await provider.generate(request)
                
                assert result.success
                assert result.provider == "anthropic"
                assert result.model == "claude-3-haiku-20240307"
                assert result.metadata["analysis"] == "This image shows a beautiful landscape"
                assert result.metadata["input_tokens"] == 1000
                assert result.metadata["output_tokens"] == 50
                # Check cost calculation (haiku pricing)
                expected_cost = (1000 / 1_000_000) * 0.25 + (50 / 1_000_000) * 1.25
                assert result.cost == expected_cost
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, provider):
        """Test successful text generation."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "content": [{
                "text": "Here is the generated text response"
            }],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 200
            }
        })
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            yield mock_response
        
        mock_session.post = mock_post
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            request = GenerationRequest(
                prompt="Write a poem about AI",
                generation_type=GenerationType.TEXT,
                parameters={"temperature": 0.7}
            )
            
            result = await provider.generate(request)
            
            assert result.success
            assert result.provider == "anthropic"
            assert result.metadata["text"] == "Here is the generated text response"
            assert result.metadata["input_tokens"] == 100
            assert result.metadata["output_tokens"] == 200
    
    @pytest.mark.asyncio
    async def test_generate_with_output_path(self, provider):
        """Test generation with file output."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "content": [{
                "text": "Analysis result"
            }],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50
            }
        })
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            yield mock_response
        
        mock_session.post = mock_post
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            with patch("alicemultiverse.providers.anthropic_provider.save_text_file") as mock_save:
                mock_save.return_value = None
                
                request = GenerationRequest(
                    prompt="Analyze this",
                    generation_type=GenerationType.TEXT,
                    output_path=Path("/tmp/analysis.txt")
                )
                
                result = await provider.generate(request)
                
                assert result.success
                assert result.file_path == Path("/tmp/analysis.txt")
                mock_save.assert_called_once_with(
                    Path("/tmp/analysis.txt"),
                    "Analysis result"
                )
    
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
                generation_type=GenerationType.TEXT
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
                generation_type=GenerationType.TEXT
            )
            
            result = await provider.generate(request)
            assert not result.success
            assert "api key" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_generate_invalid_type(self, provider):
        """Test error for unsupported generation type."""
        request = GenerationRequest(
            prompt="Generate an image",
            generation_type=GenerationType.IMAGE
        )
        
        result = await provider.generate(request)
        assert not result.success
        assert "does not support GenerationType.IMAGE" in result.error
    
    @pytest.mark.asyncio
    async def test_analyze_without_images(self, provider):
        """Test that empty reference_assets uses text generation."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "content": [{
                "text": "Generated text without image"
            }],
            "usage": {
                "input_tokens": 50,
                "output_tokens": 20
            }
        })
        
        mock_session = AsyncMock()
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            yield mock_response
        
        mock_session.post = mock_post
        
        with patch.object(provider, '_get_session', return_value=mock_session):
            request = GenerationRequest(
                prompt="Analyze this image",
                generation_type=GenerationType.TEXT,
                model="claude-3-opus-20240229",
                reference_assets=[]  # Empty list - should use text generation
            )
            
            result = await provider.generate(request)
            assert result.success
            assert result.metadata["text"] == "Generated text without image"
    
    def test_get_media_type(self, provider):
        """Test media type detection."""
        assert provider._get_media_type("test.jpg") == "image/jpeg"
        assert provider._get_media_type("test.jpeg") == "image/jpeg"
        assert provider._get_media_type("test.png") == "image/png"
        assert provider._get_media_type("test.gif") == "image/gif"
        assert provider._get_media_type("test.webp") == "image/webp"
        assert provider._get_media_type("test.bmp") == "image/jpeg"  # Default
    
    @pytest.mark.asyncio
    async def test_context_manager(self, provider):
        """Test async context manager."""
        async with provider as p:
            assert p is provider
        
        # Session should be closed
        assert provider._session is None or provider._session.closed