"""Test complete provider registry with all providers."""

import pytest
from unittest.mock import patch

from alicemultiverse.providers import (
    get_provider,
    GenerationType,
    ProviderRegistry,
)


class TestCompleteProviderRegistry:
    """Test registry with all providers."""
    
    @pytest.fixture
    def registry(self):
        """Create registry instance."""
        return ProviderRegistry()
    
    def test_all_providers_available(self, registry):
        """Test that all providers are registered."""
        # Check provider classes are available
        assert "fal" in registry.PROVIDERS
        assert "openai" in registry.PROVIDERS
        assert "anthropic" in registry.PROVIDERS
        assert "claude" in registry.PROVIDERS  # Alias
        
        # Check aliases work
        assert registry.PROVIDERS["fal"] == registry.PROVIDERS["fal.ai"]
        assert registry.PROVIDERS["anthropic"] == registry.PROVIDERS["claude"]
    
    def test_get_fal_provider(self):
        """Test getting fal provider."""
        with patch.dict("os.environ", {"FAL_KEY": "test-key"}):
            provider = get_provider("fal")
            assert provider.name == "fal.ai"  # Fal provider returns "fal.ai" as name
            assert GenerationType.IMAGE in provider.capabilities.generation_types
    
    def test_get_openai_provider(self):
        """Test getting OpenAI provider."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = get_provider("openai")
            assert provider.name == "openai"
            assert GenerationType.IMAGE in provider.capabilities.generation_types
            assert GenerationType.TEXT in provider.capabilities.generation_types
    
    def test_get_anthropic_provider(self):
        """Test getting Anthropic provider."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = get_provider("anthropic")
            assert provider.name == "anthropic"
            assert GenerationType.TEXT in provider.capabilities.generation_types
            assert GenerationType.IMAGE not in provider.capabilities.generation_types
    
    def test_get_provider_by_alias(self):
        """Test getting provider by alias."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = get_provider("claude")
            assert provider.name == "anthropic"
    
    def test_provider_capabilities(self):
        """Test provider capabilities."""
        with patch.dict("os.environ", {
            "FAL_KEY": "test-key",
            "OPENAI_API_KEY": "test-key",
            "ANTHROPIC_API_KEY": "test-key"
        }):
            # Fal - images and video
            fal = get_provider("fal")
            assert "flux-pro" in fal.capabilities.models  # Use actual model name
            assert GenerationType.VIDEO in fal.capabilities.generation_types
            
            # OpenAI - images and text
            openai = get_provider("openai")
            assert "dall-e-3" in openai.capabilities.models
            assert "gpt-4-vision-preview" in openai.capabilities.models
            
            # Anthropic - text only with vision
            anthropic = get_provider("anthropic")
            assert "claude-3-opus-20240229" in anthropic.capabilities.models
            assert "vision" in anthropic.capabilities.features
            assert "image_analysis" in anthropic.capabilities.features