"""Simple tests for ElevenLabs provider without complex async mocking."""


import pytest

from alicemultiverse.providers.elevenlabs_provider import ElevenLabsProvider
from alicemultiverse.providers.types import (
    GenerationRequest,
    GenerationType,
)


class TestElevenLabsProvider:
    """Test ElevenLabs provider functionality."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = ElevenLabsProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.name == "elevenlabs"

    def test_capabilities(self):
        """Test provider capabilities."""
        provider = ElevenLabsProvider(api_key="test-key")
        caps = provider.capabilities
        assert GenerationType.AUDIO in caps.generation_types
        assert "sound-effects" in caps.models
        assert "mp3" in caps.formats
        assert "text_to_sound_effects" in caps.features
        assert caps.pricing["sound-effects"] == 0.08

    def test_build_sound_params(self):
        """Test building sound generation parameters."""
        provider = ElevenLabsProvider(api_key="test-key")
        request = GenerationRequest(
            prompt="ocean waves",
            generation_type=GenerationType.AUDIO,
            parameters={
                "duration_seconds": 15,
                "prompt_influence": 0.7,
                "output_format": "mp3_44100_192"
            }
        )

        params = provider._build_sound_params(request, "sound-effects")

        assert params["text"] == "ocean waves"
        assert params["duration_seconds"] == 15
        assert params["prompt_influence"] == 0.7
        assert params["output_format"] == "mp3_44100_192"

    def test_build_sound_params_duration_clamping(self):
        """Test duration is clamped to maximum."""
        provider = ElevenLabsProvider(api_key="test-key")
        request = GenerationRequest(
            prompt="thunder",
            generation_type=GenerationType.AUDIO,
            parameters={"duration_seconds": 30}  # Over max
        )

        params = provider._build_sound_params(request, "sound-effects")
        assert params["duration_seconds"] == 22  # Max duration

    def test_build_sound_params_prompt_influence_clamping(self):
        """Test prompt influence is clamped to 0-1 range."""
        provider = ElevenLabsProvider(api_key="test-key")

        # Test upper bound
        request = GenerationRequest(
            prompt="rain",
            generation_type=GenerationType.AUDIO,
            parameters={"prompt_influence": 1.5}
        )
        params = provider._build_sound_params(request, "sound-effects")
        assert params["prompt_influence"] == 1.0

        # Test lower bound
        request.parameters["prompt_influence"] = -0.5
        params = provider._build_sound_params(request, "sound-effects")
        assert params["prompt_influence"] == 0.0

    def test_build_sound_params_invalid_format(self):
        """Test invalid output format falls back to default."""
        provider = ElevenLabsProvider(api_key="test-key")
        request = GenerationRequest(
            prompt="footsteps",
            generation_type=GenerationType.AUDIO,
            parameters={"output_format": "invalid_format"}
        )

        params = provider._build_sound_params(request, "sound-effects")
        assert params["output_format"] == "mp3_44100_128"  # Default

    @pytest.mark.asyncio
    async def test_save_audio_with_output_path(self, tmp_path):
        """Test saving audio with specified output path."""
        provider = ElevenLabsProvider(api_key="test-key")
        audio_data = b"fake audio data"
        output_path = tmp_path / "test_sound.mp3"

        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.AUDIO,
            output_path=output_path
        )

        saved_path = await provider._save_audio(request, audio_data, "mp3_44100_128")

        assert saved_path == output_path
        assert saved_path.exists()
        assert saved_path.read_bytes() == audio_data

    @pytest.mark.asyncio
    async def test_save_audio_correct_extension(self, tmp_path):
        """Test audio is saved with correct extension based on format."""
        provider = ElevenLabsProvider(api_key="test-key")
        audio_data = b"fake audio data"

        # Test MP3
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.AUDIO,
            output_path=tmp_path / "sound.wav"  # Wrong extension
        )
        saved_path = await provider._save_audio(request, audio_data, "mp3_44100_128")
        assert saved_path.suffix == ".mp3"

        # Test PCM (should be WAV)
        request.output_path = tmp_path / "sound.mp3"  # Wrong extension
        saved_path = await provider._save_audio(request, audio_data, "pcm_44100")
        assert saved_path.suffix == ".wav"

    def test_get_default_model(self):
        """Test getting default model."""
        provider = ElevenLabsProvider(api_key="test-key")
        assert provider.get_default_model(GenerationType.AUDIO) == "sound-effects"
        # For non-audio types, it will call parent class which returns first model
        assert provider.get_default_model(GenerationType.IMAGE) == "sound-effects"  # Only model available

    def test_get_models_for_type(self):
        """Test getting models for generation type."""
        provider = ElevenLabsProvider(api_key="test-key")
        audio_models = provider.get_models_for_type(GenerationType.AUDIO)
        assert audio_models == ["sound-effects"]

        image_models = provider.get_models_for_type(GenerationType.IMAGE)
        assert image_models == []

    @pytest.mark.asyncio
    async def test_estimate_cost(self):
        """Test cost estimation."""
        provider = ElevenLabsProvider(api_key="test-key")
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.AUDIO
        )
        cost = await provider.estimate_cost(request)
        assert cost == 0.08  # Fixed cost per generation

        # Test with different model (should still be same cost)
        request.model = None
        cost = await provider.estimate_cost(request)
        assert cost == 0.08

    @pytest.mark.asyncio
    async def test_generate_wrong_type(self):
        """Test generation fails for non-audio types."""
        provider = ElevenLabsProvider(api_key="test-key")
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE
        )

        with pytest.raises(Exception) as exc_info:
            await provider._generate(request)
        assert "only supports audio generation" in str(exc_info.value)
