"""Integration test for ElevenLabs provider with the overall system."""

import os

import pytest

from alicemultiverse.providers import GenerationRequest, GenerationType, get_registry


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ELEVENLABS_API_KEY"),
    reason="ELEVENLABS_API_KEY not set"
)
class TestElevenLabsIntegration:
    """Test ElevenLabs provider integration with the system."""

    @pytest.fixture
    def registry(self):
        """Get provider registry."""
        return get_registry()

    @pytest.mark.asyncio
    async def test_provider_registration(self, registry):
        """Test ElevenLabs provider is registered correctly."""
        # Check provider is in list
        providers = registry.list_providers()
        assert "elevenlabs" in providers
        assert "eleven-labs" in providers  # Alias
        assert "11labs" in providers  # Alias

        # Get provider instance
        provider = registry.get_provider("elevenlabs")
        assert provider.name == "elevenlabs"

        # Check capabilities
        audio_providers = registry.get_providers_for_type(GenerationType.AUDIO)
        assert "elevenlabs" in audio_providers

    @pytest.mark.asyncio
    async def test_generate_sound_effect(self, registry, tmp_path):
        """Test actual sound effect generation (requires API key)."""
        provider = registry.get_provider("elevenlabs")

        request = GenerationRequest(
            prompt="short beep sound",
            generation_type=GenerationType.AUDIO,
            parameters={
                "duration_seconds": 1,
                "prompt_influence": 0.5
            },
            output_path=tmp_path / "test_beep.mp3"
        )

        # Generate with full provider infrastructure
        result = await provider.generate(request)

        assert result.success
        assert result.file_path.exists()
        assert result.file_path.suffix == ".mp3"
        assert result.cost == 0.08
        assert result.provider == "elevenlabs"
        assert result.model == "sound-effects"

        # Check file size (should have actual audio data)
        file_size = result.file_path.stat().st_size
        assert file_size > 1000  # At least 1KB

    @pytest.mark.asyncio
    async def test_workflow_integration(self, registry, tmp_path):
        """Test ElevenLabs in a multi-modal workflow."""
        # This would be used with other providers in a workflow
        # For example: generate image, then generate matching sound

        # Generate sound effect
        sound_provider = registry.get_provider("elevenlabs")
        sound_request = GenerationRequest(
            prompt="futuristic sci-fi ambient sound",
            generation_type=GenerationType.AUDIO,
            parameters={
                "duration_seconds": 5,
                "prompt_influence": 0.3
            },
            output_path=tmp_path / "scifi_ambient.mp3"
        )

        sound_result = await sound_provider.generate(sound_request)
        assert sound_result.success

        # In a real workflow, this could be combined with:
        # - Image generation from another provider
        # - Video generation that uses this audio
        # - Multiple sound layers for complex audio

        # Track total cost
        total_cost = sound_result.cost
        assert total_cost == 0.08

    @pytest.mark.asyncio
    async def test_error_handling(self, registry):
        """Test error handling for invalid requests."""
        provider = registry.get_provider("elevenlabs")

        # Test wrong generation type
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE  # Wrong type
        )

        with pytest.raises(Exception) as exc_info:
            await provider.generate(request)
        assert "only supports audio generation" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_provider_health(self, registry):
        """Test provider health monitoring."""
        provider = registry.get_provider("elevenlabs")

        # Check status
        status = await provider.check_status()
        # Should be AVAILABLE if API key is valid
        assert status.value in ["available", "unknown"]  # Unknown if can't connect

        # Get health metrics
        metrics = provider.get_health_metrics()
        # Metrics might be None if no requests have been made
        if metrics:
            assert "total_requests" in metrics
            assert "is_healthy" in metrics
