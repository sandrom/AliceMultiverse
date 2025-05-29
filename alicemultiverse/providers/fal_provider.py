"""fal.ai provider implementation for FLUX and other models."""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import aiohttp

from ..core.file_operations import download_file
from .provider import (
    Provider,
    AuthenticationError,
    GenerationError,
    RateLimitError,
)
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class FalProvider(Provider):
    """Provider for fal.ai API integration."""

    BASE_URL = "https://fal.run"
    
    # Model endpoints
    MODELS = {
        # FLUX models
        "flux-pro": "fal-ai/flux-pro",
        "flux-pro-v1.1": "fal-ai/flux-pro/v1.1",
        "flux-kontext-pro": "fal-ai/flux-pro/kontext",  # FLUX Kontext Pro - single reference image
        "flux-kontext-pro-multi": "fal-ai/flux-pro/kontext/multi",  # FLUX Kontext Pro - multiple reference images
        "flux-kontext-max": "fal-ai/flux-pro/kontext/max",  # FLUX Kontext Max - single reference
        "flux-kontext-max-multi": "fal-ai/flux-pro/kontext/max/multi",  # FLUX Kontext Max - multiple references
        "flux-dev": "fal-ai/flux/dev",
        "flux-dev-image-to-image": "fal-ai/flux/dev/image-to-image",
        "flux-schnell": "fal-ai/flux/schnell",
        "flux-realism": "fal-ai/flux-realism",
        "flux-lora": "fal-ai/flux-lora",  # Custom LoRA support
        
        # Fast SDXL
        "fast-sdxl": "fal-ai/fast-sdxl",
        "lightning-sdxl": "fal-ai/fast-lightning-sdxl",
        
        # Specialized models
        "stable-cascade": "fal-ai/stable-cascade",
        "pixart-sigma": "fal-ai/pixart-sigma",
        "kolors": "fal-ai/kolors",
        
        # Video models
        "animatediff": "fal-ai/animatediff-v2v",
        "svd": "fal-ai/stable-video-diffusion",
        
        # Kling video models
        "kling-v1-text": "fal-ai/kling-video/v1/pro/text-to-video",
        "kling-v1-image": "fal-ai/kling-video/v1/pro/image-to-video",
        "kling-v2-text": "fal-ai/kling-video/v2/master/text-to-video",
        "kling-v2-image": "fal-ai/kling-video/v2/master/image-to-video",
        "kling-v2.1-pro-text": "fal-ai/kling-video/v2.1/pro/text-to-video",  # New Kling 2.1 Pro
        "kling-v2.1-pro-image": "fal-ai/kling-video/v2.1/pro/image-to-video",  # New Kling 2.1 Pro
        "kling-v2.1-master-text": "fal-ai/kling-video/v2.1/master/text-to-video",  # New Kling 2.1 Master
        "kling-v2.1-master-image": "fal-ai/kling-video/v2.1/master/image-to-video",  # New Kling 2.1 Master
        
        # Kling specialized models
        "kling-elements": "fal-ai/kling-video/v1.6/pro/elements",
        "kling-lipsync": "fal-ai/kling-video/lipsync/audio-to-video",
        
        # Audio models
        "mmaudio-v2": "fal-ai/mmaudio-v2",  # Multimodal audio generation for video
        
        # Utility models
        "face-swap": "fal-ai/face-swap",
        "ccsr": "fal-ai/ccsr",  # upscaling
        "clarity-upscaler": "fal-ai/clarity-upscaler",
    }
    
    # Pricing per generation (approximate)
    PRICING = {
        "flux-pro": 0.05,
        "flux-pro-v1.1": 0.055,
        "flux-kontext-pro": 0.06,  # Single reference
        "flux-kontext-pro-multi": 0.07,  # Multiple references
        "flux-kontext-max": 0.08,  # Single reference
        "flux-kontext-max-multi": 0.09,  # Multiple references
        "flux-dev": 0.025,
        "flux-dev-image-to-image": 0.025,
        "flux-schnell": 0.003,
        "flux-realism": 0.025,
        "flux-lora": 0.03,
        "fast-sdxl": 0.003,
        "lightning-sdxl": 0.003,
        "stable-cascade": 0.01,
        "pixart-sigma": 0.01,
        "kolors": 0.01,
        "animatediff": 0.10,
        "svd": 0.10,
        "kling-v1-text": 0.15,
        "kling-v1-image": 0.15,
        "kling-v2-text": 0.20,
        "kling-v2-image": 0.20,
        "kling-v2.1-pro-text": 0.25,  # Kling 2.1 Pro tier
        "kling-v2.1-pro-image": 0.25,  # Kling 2.1 Pro tier
        "kling-v2.1-master-text": 0.30,  # Kling 2.1 Master tier - highest quality
        "kling-v2.1-master-image": 0.30,  # Kling 2.1 Master tier - highest quality
        "kling-elements": 0.15,
        "kling-lipsync": 0.20,
        "mmaudio-v2": 0.05,  # Multimodal audio generation
        "face-swap": 0.02,
        "ccsr": 0.02,
        "clarity-upscaler": 0.02,
    }

    def __init__(self, api_key: Optional[str] = None, event_bus: Optional[Any] = None):
        """Initialize fal.ai provider.
        
        Args:
            api_key: fal.ai API key (or from FAL_KEY env var)
            event_bus: Deprecated parameter, kept for compatibility
        """
        api_key = api_key or os.getenv("FAL_KEY")
        if not api_key:
            logger.warning("No fal.ai API key provided. Some features may be limited.")
        
        super().__init__(api_key)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "fal.ai"

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE, GenerationType.VIDEO, GenerationType.AUDIO],
            models=list(self.MODELS.keys()),
            max_resolution={"width": 2048, "height": 2048},  # FLUX can go higher
            formats=["png", "jpg", "webp"],
            features=[
                "style_reference",
                "image_to_image", 
                "inpainting",
                "controlnet",
                "lora",
                "face_swap",
                "upscaling",
                "video_generation",
                "audio_generation",
                "video_to_audio"
            ],
            rate_limits={
                "requests_per_minute": 60,
                "concurrent_requests": 10
            },
            pricing=self.PRICING
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Key {self.api_key}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def check_status(self) -> ProviderStatus:
        """Check fal.ai API status."""
        try:
            session = await self._get_session()
            # Use a lightweight model endpoint for status check
            async with session.get(
                f"{self.BASE_URL}/fal-ai/flux/schnell",
                params={"check": "true"}
            ) as response:
                if response.status == 200:
                    self._status = ProviderStatus.AVAILABLE
                elif response.status == 401:
                    self._status = ProviderStatus.UNAVAILABLE
                    logger.error("fal.ai authentication failed")
                else:
                    self._status = ProviderStatus.DEGRADED
                    
        except Exception as e:
            logger.error(f"Failed to check fal.ai status: {e}")
            self._status = ProviderStatus.UNKNOWN
            
        self._last_check = datetime.now()
        return self._status

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Perform the actual generation using fal.ai.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        # Determine model
        model = request.model or "flux-schnell"  # Default to fast model
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}")
        
        # Build API parameters
        api_params = self._build_api_params(request, model)
            
        # Make API request
        result_data = await self._call_api(model, api_params)
        
        # Download generated content
        file_path = await self._download_result(request, result_data)
        
        # Calculate cost
        cost = self.PRICING.get(model, 0.0)
        
        # Build result
        return GenerationResult(
            success=True,
            file_path=file_path,
            cost=cost,
            provider=self.name,
            model=model,
            metadata={
                "prompt": request.prompt,
                "model": model,
                "parameters": api_params,
                "fal_request_id": result_data.get("request_id"),
            }
        )

    def _build_api_params(self, request: GenerationRequest, model: str) -> Dict[str, Any]:
        """Build API parameters for fal.ai request."""
        params = {
            "prompt": request.prompt,
        }
        
        # Add custom parameters
        if request.parameters:
            params.update(request.parameters)
        
        # Model-specific defaults
        if "kontext" in model:
            # FLUX Kontext models support reference images for editing
            params.setdefault("num_inference_steps", 28)
            params.setdefault("guidance_scale", 3.5)
            params.setdefault("num_images", 1)
            
            # Handle reference images based on model type
            if request.reference_assets:
                if "multi" in model:
                    # Multi-reference models accept array of image URLs
                    params["image_urls"] = request.reference_assets
                    # Use provided weights or default to equal weights
                    if request.reference_weights:
                        params["image_weights"] = request.reference_weights
                    else:
                        params.setdefault("image_weights", [1.0] * len(request.reference_assets))
                else:
                    # Single reference models
                    params["image_url"] = request.reference_assets[0]
                    
        elif model == "flux-dev-image-to-image":
            # Image-to-image model
            params.setdefault("num_inference_steps", 28)
            params.setdefault("guidance_scale", 3.5)
            params.setdefault("strength", 0.85)  # How much to change the image
            
            if request.reference_assets:
                params["image_url"] = request.reference_assets[0]
            else:
                raise ValueError("flux-dev-image-to-image requires a reference image")
                
        elif model.startswith("flux"):
            params.setdefault("num_inference_steps", 28 if "schnell" in model else 50)
            params.setdefault("guidance_scale", 3.5)
            params.setdefault("num_images", 1)
            params.setdefault("enable_safety_checker", True)
            
        elif model in ["fast-sdxl", "lightning-sdxl"]:
            params.setdefault("num_inference_steps", 8)
            params.setdefault("guidance_scale", 2.0)
            params.setdefault("num_images", 1)
            
        elif model.startswith("kling"):
            # Kling video generation parameters
            params.setdefault("duration", "5")  # 5 seconds
            params.setdefault("aspect_ratio", "16:9")
            params.setdefault("cfg_scale", 0.5)
            # Remove any image-specific parameters
            params.pop("num_images", None)
            params.pop("image_size", None)
            
        elif model == "mmaudio-v2":
            # MMAudio v2 parameters for video-to-audio generation
            params.setdefault("num_steps", 25)
            params.setdefault("duration", 8)  # seconds
            params.setdefault("cfg_strength", 4.5)
            params.setdefault("seed", None)  # Random if not specified
            params.setdefault("negative_prompt", "")
            params.setdefault("mask_away_clip", False)
            
            # Require video URL for mmaudio
            if "video_url" not in params and request.reference_assets:
                # Use first reference asset as video URL
                params["video_url"] = str(request.reference_assets[0])
            elif "video_url" not in params:
                raise ValueError("mmaudio-v2 requires a video_url parameter")
            
        # Handle image-to-image
        if request.reference_assets and len(request.reference_assets) > 0:
            # This would need to be converted to a URL or base64
            # For now, we'll skip this feature
            logger.warning("Reference assets not yet implemented for fal.ai")
        
        # Set resolution
        if request.generation_type == GenerationType.IMAGE:
            params.setdefault("image_size", {
                "width": params.pop("width", 1024),
                "height": params.pop("height", 1024)
            })
        
        return params

    async def _call_api(self, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call to fal.ai."""
        endpoint = self.MODELS[model]
        url = f"{self.BASE_URL}/{endpoint}"
        
        session = await self._get_session()
        
        try:
            async with session.post(url, json=params) as response:
                if response.status == 429:
                    raise RateLimitError("fal.ai rate limit exceeded")
                elif response.status == 401:
                    raise AuthenticationError("Invalid fal.ai API key")
                elif response.status != 200:
                    error_text = await response.text()
                    raise GenerationError(f"fal.ai API error: {error_text}")
                
                result = await response.json()
                
                # Check if it's a queued request
                if result.get("status") == "queued":
                    # Poll for completion
                    result = await self._poll_for_completion(
                        result.get("request_id"),
                        result.get("status_url")
                    )
                
                return result
                
        except aiohttp.ClientError as e:
            raise GenerationError(f"Network error: {e}")

    async def _poll_for_completion(
        self, 
        request_id: str, 
        status_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Poll for queued request completion."""
        session = await self._get_session()
        
        # Use status URL or construct from request ID
        if not status_url:
            status_url = f"{self.BASE_URL}/queue/requests/{request_id}/status"
        
        max_attempts = 60  # 5 minutes with 5 second intervals
        for _ in range(max_attempts):
            async with session.get(status_url) as response:
                if response.status != 200:
                    raise GenerationError(f"Failed to check status: {response.status}")
                
                status_data = await response.json()
                
                if status_data.get("status") == "completed":
                    return status_data.get("result", {})
                elif status_data.get("status") == "failed":
                    raise GenerationError(
                        f"Generation failed: {status_data.get('error', 'Unknown error')}"
                    )
                
                # Still processing, wait
                await asyncio.sleep(5)
        
        raise GenerationError("Generation timed out after 5 minutes")

    async def _download_result(
        self, 
        request: GenerationRequest, 
        result_data: Dict[str, Any]
    ) -> Path:
        """Download generated content from result."""
        # Check if this is a video result (e.g., from Kling or mmaudio)
        video_url = result_data.get("video", {}).get("url")
        if video_url:
            media_url = video_url
            default_ext = ".mp4"
        else:
            # Extract image URL(s)
            images = result_data.get("images", [])
            if not images:
                # Try alternative response formats
                image_url = result_data.get("image", {}).get("url")
                if image_url:
                    images = [{"url": image_url}]
                else:
                    raise GenerationError("No images or video in fal.ai response")
            
            # Get first image URL
            media_url = images[0].get("url")
            if not media_url:
                raise GenerationError("No image URL in fal.ai response")
            default_ext = ".png"
        
        # Determine output path
        if request.output_path:
            output_path = request.output_path
        else:
            # Generate filename from URL
            url_path = urlparse(media_url).path
            filename = Path(url_path).name or f"fal_{datetime.now().timestamp()}{default_ext}"
            output_path = Path.cwd() / "generated" / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download file
        await download_file(media_url, output_path)
        
        return output_path

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        _ = (exc_type, exc_val, exc_tb)  # Unused but required by protocol
        if self._session:
            await self._session.close()
            self._session = None