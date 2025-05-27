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
from ..events.base import EventBus
from .base import (
    AuthenticationError,
    GenerationError,
    GenerationProvider,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class FalProvider(GenerationProvider):
    """Provider for fal.ai API integration."""

    BASE_URL = "https://fal.run"
    
    # Model endpoints
    MODELS = {
        # FLUX models
        "flux-pro": "fal-ai/flux-pro",
        "flux-dev": "fal-ai/flux/dev",
        "flux-schnell": "fal-ai/flux/schnell",
        "flux-realism": "fal-ai/flux-realism",
        
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
        
        # Utility models
        "face-swap": "fal-ai/face-swap",
        "ccsr": "fal-ai/ccsr",  # upscaling
        "clarity-upscaler": "fal-ai/clarity-upscaler",
    }
    
    # Pricing per generation (approximate)
    PRICING = {
        "flux-pro": 0.05,
        "flux-dev": 0.025,
        "flux-schnell": 0.003,
        "flux-realism": 0.025,
        "fast-sdxl": 0.003,
        "lightning-sdxl": 0.003,
        "stable-cascade": 0.01,
        "pixart-sigma": 0.01,
        "kolors": 0.01,
        "animatediff": 0.10,
        "svd": 0.10,
        "face-swap": 0.02,
        "ccsr": 0.02,
        "clarity-upscaler": 0.02,
    }

    def __init__(self, api_key: Optional[str] = None, event_bus: Optional[EventBus] = None):
        """Initialize fal.ai provider.
        
        Args:
            api_key: fal.ai API key (or from FAL_KEY env var)
            event_bus: Event bus for publishing events
        """
        api_key = api_key or os.getenv("FAL_KEY")
        if not api_key:
            logger.warning("No fal.ai API key provided. Some features may be limited.")
        
        super().__init__(api_key, event_bus)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "fal.ai"

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE, GenerationType.VIDEO],
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
                "video_generation"
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

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content using fal.ai.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        start_time = datetime.now()
        
        try:
            # Validate request
            await self.validate_request(request)
            
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
            
            # Calculate cost and time
            generation_time = (datetime.now() - start_time).total_seconds()
            cost = self.PRICING.get(model, 0.0)
            
            # Build result
            result = GenerationResult(
                success=True,
                file_path=file_path,
                generation_time=generation_time,
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
            
            # Publish success event
            self._publish_success(request, result)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"fal.ai generation failed: {error_msg}")
            
            # Publish failure event
            self._publish_failure(request, error_msg)
            
            # Return error result
            return GenerationResult(
                success=False,
                error=error_msg,
                provider=self.name,
                model=request.model
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
        if model.startswith("flux"):
            params.setdefault("num_inference_steps", 28 if "schnell" in model else 50)
            params.setdefault("guidance_scale", 3.5)
            params.setdefault("num_images", 1)
            params.setdefault("enable_safety_checker", True)
            
        elif model in ["fast-sdxl", "lightning-sdxl"]:
            params.setdefault("num_inference_steps", 8)
            params.setdefault("guidance_scale", 2.0)
            params.setdefault("num_images", 1)
            
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
        for attempt in range(max_attempts):
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
        # Extract image URL(s)
        images = result_data.get("images", [])
        if not images:
            # Try alternative response formats
            image_url = result_data.get("image", {}).get("url")
            if image_url:
                images = [{"url": image_url}]
            else:
                raise GenerationError("No images in fal.ai response")
        
        # Get first image URL
        image_url = images[0].get("url")
        if not image_url:
            raise GenerationError("No image URL in fal.ai response")
        
        # Determine output path
        if request.output_path:
            output_path = request.output_path
        else:
            # Generate filename from URL
            url_path = urlparse(image_url).path
            filename = Path(url_path).name or f"fal_{datetime.now().timestamp()}.png"
            output_path = Path.cwd() / "generated" / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download file
        await download_file(image_url, output_path)
        
        return output_path

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None