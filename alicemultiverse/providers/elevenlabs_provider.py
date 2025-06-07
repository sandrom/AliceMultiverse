"""ElevenLabs provider implementation for AI sound effects generation."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

# from ..core.file_operations import ensure_directory  # Not needed - use pathlib
from .provider import Provider, GenerationError, RateLimitError, AuthenticationError
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class ElevenLabsProvider(Provider):
    """Provider for ElevenLabs API integration for sound effects generation."""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    # Available models
    MODELS = {
        "sound-effects": {
            "endpoint": "/sound-generation",
            "type": GenerationType.AUDIO,
            "max_duration": 22,  # seconds
            "default_duration": 10,
            "default_prompt_influence": 0.3,
        }
    }
    
    # Pricing per generation
    PRICING = {
        "sound-effects": 0.08,  # Estimated cost per generation
    }
    
    # Supported output formats
    OUTPUT_FORMATS = {
        "mp3_44100_32": {"codec": "mp3", "sample_rate": 44100, "bitrate": 32},
        "mp3_44100_64": {"codec": "mp3", "sample_rate": 44100, "bitrate": 64},
        "mp3_44100_96": {"codec": "mp3", "sample_rate": 44100, "bitrate": 96},
        "mp3_44100_128": {"codec": "mp3", "sample_rate": 44100, "bitrate": 128},
        "mp3_44100_192": {"codec": "mp3", "sample_rate": 44100, "bitrate": 192},  # Pro tier
        "pcm_16000": {"codec": "pcm", "sample_rate": 16000, "bitrate": None},
        "pcm_22050": {"codec": "pcm", "sample_rate": 22050, "bitrate": None},
        "pcm_24000": {"codec": "pcm", "sample_rate": 24000, "bitrate": None},
        "pcm_44100": {"codec": "pcm", "sample_rate": 44100, "bitrate": None},  # Pro tier
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize ElevenLabs provider.
        
        Args:
            api_key: ElevenLabs API key (or from ELEVENLABS_API_KEY env var)
            **kwargs: Additional arguments for BaseProvider
        """
        api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs API key is required")
        
        super().__init__(api_key=api_key, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "elevenlabs"

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.AUDIO],
            models=list(self.MODELS.keys()),
            formats=["mp3", "pcm", "wav"],
            features=[
                "text_to_sound_effects",
                "duration_control",
                "prompt_influence",
                "cinematic_sound_design",
                "foley_sounds",
                "ambient_sounds",
            ],
            rate_limits={
                "requests_per_minute": 60,  # Estimate based on typical API limits
            },
            pricing={
                "sound-effects": self.PRICING["sound-effects"],
            }
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def check_status(self) -> ProviderStatus:
        """Check ElevenLabs API status."""
        try:
            session = await self._get_session()
            # Use user endpoint to check API key validity
            async with session.get(f"{self.BASE_URL}/user") as response:
                if response.status == 200:
                    self._status = ProviderStatus.AVAILABLE
                elif response.status == 401:
                    self._status = ProviderStatus.UNAVAILABLE
                    logger.error("ElevenLabs authentication failed")
                else:
                    self._status = ProviderStatus.DEGRADED
                    
        except Exception as e:
            logger.error(f"Failed to check ElevenLabs status: {e}")
            self._status = ProviderStatus.UNKNOWN
            
        self._last_check = datetime.now()
        return self._status

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Perform the actual generation using ElevenLabs.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        # Only support audio generation
        if request.generation_type != GenerationType.AUDIO:
            raise GenerationError(f"ElevenLabs only supports audio generation, not {request.generation_type}")
        
        # Generate sound effect
        model = request.model or "sound-effects"
        result = await self._generate_sound_effect(request, model)
        
        return result

    async def _generate_sound_effect(self, request: GenerationRequest, model: str) -> GenerationResult:
        """Generate sound effect using ElevenLabs API."""
        # Build parameters
        params = self._build_sound_params(request, model)
        
        # Call API
        session = await self._get_session()
        endpoint = self.MODELS[model]["endpoint"]
        
        try:
            async with session.post(f"{self.BASE_URL}{endpoint}", json=params) as response:
                if response.status == 429:
                    raise RateLimitError("ElevenLabs rate limit exceeded")
                elif response.status == 401:
                    raise AuthenticationError("Invalid ElevenLabs API key")
                elif response.status == 422:
                    error_data = await response.json()
                    raise GenerationError(f"Invalid parameters: {error_data}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise GenerationError(f"ElevenLabs API error ({response.status}): {error_text}")
                
                # Stream the audio content
                audio_content = await response.read()
        
        except aiohttp.ClientError as e:
            raise GenerationError(f"Network error calling ElevenLabs API: {str(e)}")
        
        # Save audio file
        file_path = await self._save_audio(request, audio_content, params.get("output_format", "mp3_44100_128"))
        
        # Calculate cost
        cost = self.PRICING[model]
        
        return GenerationResult(
            success=True,
            file_path=file_path,
            cost=cost,
            provider=self.name,
            model=model,
            metadata={
                "prompt": request.prompt,
                "duration_seconds": params.get("duration_seconds"),
                "prompt_influence": params.get("prompt_influence"),
                "output_format": params.get("output_format"),
                "generation_type": "sound_effect",
            }
        )

    def _build_sound_params(self, request: GenerationRequest, model: str) -> Dict[str, Any]:
        """Build parameters for sound generation request."""
        params = {
            "text": request.prompt,
        }
        
        # Get parameters from request
        req_params = request.parameters or {}
        model_config = self.MODELS[model]
        
        # Duration
        duration = req_params.get("duration_seconds")
        if duration is not None:
            # Clamp to max duration
            duration = min(duration, model_config["max_duration"])
            params["duration_seconds"] = duration
        
        # Prompt influence (0.0 to 1.0)
        prompt_influence = req_params.get("prompt_influence")
        if prompt_influence is not None:
            # Ensure it's between 0 and 1
            prompt_influence = max(0.0, min(1.0, prompt_influence))
            params["prompt_influence"] = prompt_influence
        
        # Output format
        output_format = req_params.get("output_format", "mp3_44100_128")
        if output_format in self.OUTPUT_FORMATS:
            params["output_format"] = output_format
        else:
            # Default to standard MP3
            params["output_format"] = "mp3_44100_128"
        
        return params

    async def _save_audio(self, request: GenerationRequest, audio_data: bytes, output_format: str) -> Path:
        """Save audio data to file."""
        # Determine file extension from format
        format_info = self.OUTPUT_FORMATS.get(output_format, {})
        codec = format_info.get("codec", "mp3")
        extension = "wav" if codec == "pcm" else codec
        
        # Determine output path
        if request.output_path:
            output_path = request.output_path
            # Ensure correct extension
            if output_path.suffix.lower() != f".{extension}":
                output_path = output_path.with_suffix(f".{extension}")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sound_effect_{timestamp}.{extension}"
            output_path = Path.cwd() / "generated" / "audio" / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save audio
        output_path.write_bytes(audio_data)
        
        logger.info(f"Saved sound effect to {output_path}")
        
        return output_path

    def get_default_model(self, generation_type: GenerationType) -> str:
        """Get default model for generation type."""
        if generation_type == GenerationType.AUDIO:
            return "sound-effects"
        return super().get_default_model(generation_type)

    def get_models_for_type(self, generation_type: GenerationType) -> List[str]:
        """Get available models for a generation type."""
        if generation_type == GenerationType.AUDIO:
            return ["sound-effects"]
        return []

    async def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate cost for a generation request.
        
        Args:
            request: Generation request
            
        Returns:
            Estimated cost in USD
        """
        # Fixed cost per generation
        model = request.model or "sound-effects"
        return self.PRICING.get(model, 0.08)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None