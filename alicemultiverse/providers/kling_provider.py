"""Official Kling API provider for video and image generation."""

import asyncio
import json
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


class KlingProvider(Provider):
    """Provider for official Kling AI API integration."""

    # API endpoints
    BASE_URL_GLOBAL = "https://api-app-global.klingai.com"
    BASE_URL_CN = "https://api-app-cn.klingai.com"
    
    # Model configurations
    MODELS = {
        # Video models (Kling V2.0)
        "kling-v2-text": "text-to-video",
        "kling-v2-image": "image-to-video",
        "kling-v2.1-text": "text-to-video-v2.1",
        "kling-v2.1-image": "image-to-video-v2.1",
        "kling-v2.1-pro-text": "text-to-video-v2.1-pro",
        "kling-v2.1-pro-image": "image-to-video-v2.1-pro",
        "kling-v2.1-master-text": "text-to-video-v2.1-master",
        "kling-v2.1-master-image": "image-to-video-v2.1-master",
        
        # Special features
        "kling-lipsync": "lip-sync",
        "kling-extend": "video-extend",
        "kling-effects": "video-effects",
        
        # Image models (Kolors V2.0)
        "kolors-v2": "kolors-v2",
        "kolors-v2-pro": "kolors-v2-pro",
        
        # Virtual Try-On
        "kling-tryon": "virtual-try-on-v1.5",
    }
    
    # Pricing per generation (based on units * $0.14)
    PRICING = {
        # Standard mode 5s video = 2 units = $0.28
        "kling-v2-text": 0.28,
        "kling-v2-image": 0.28,
        "kling-v2.1-text": 0.35,
        "kling-v2.1-image": 0.35,
        "kling-v2.1-pro-text": 0.42,  # Professional mode
        "kling-v2.1-pro-image": 0.42,
        "kling-v2.1-master-text": 0.56,  # Master quality
        "kling-v2.1-master-image": 0.56,
        
        # Special features
        "kling-lipsync": 0.35,
        "kling-extend": 0.28,
        "kling-effects": 0.21,
        
        # Image generation
        "kolors-v2": 0.07,  # 0.5 units
        "kolors-v2-pro": 0.14,  # 1 unit
        
        # Virtual Try-On
        "kling-tryon": 0.14,
    }

    def __init__(self, api_key: Optional[str] = None, region: str = "global"):
        """Initialize Kling provider.
        
        Args:
            api_key: Kling API key (or from KLING_API_KEY env var)
            region: API region - "global" or "cn" (China)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("KLING_API_KEY")
        self.region = region
        self.base_url = self.BASE_URL_GLOBAL if region == "global" else self.BASE_URL_CN
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "kling"

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.VIDEO, GenerationType.IMAGE],
            models=list(self.MODELS.keys()),
            max_resolution={
                "width": 1920,
                "height": 1080,
                "video_length_seconds": 10
            },
            formats=["mp4", "mov", "png", "jpg"],
            features=[
                "text_to_video",
                "image_to_video",
                "video_extension",
                "lip_sync",
                "video_effects",
                "multi_image_reference",
                "virtual_try_on",
                "professional_mode",
                "standard_mode",
            ],
            rate_limits={
                "concurrent_videos": 10,  # Varies by subscription
                "requests_per_minute": 60
            },
            pricing=self.PRICING
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def check_status(self) -> ProviderStatus:
        """Check Kling API status."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/user/me/profile") as response:
                if response.status == 200:
                    return ProviderStatus.AVAILABLE
                elif response.status == 401:
                    return ProviderStatus.AUTHENTICATION_ERROR
                else:
                    return ProviderStatus.UNAVAILABLE
        except Exception as e:
            logger.error(f"Error checking Kling status: {e}")
            return ProviderStatus.ERROR

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content using Kling API."""
        if not self.api_key:
            raise AuthenticationError("Kling API key not configured")
            
        # Get model configuration
        model = request.model or "kling-v2.1-text"
        model_type = self.MODELS.get(model)
        if not model_type:
            raise ValueError(f"Unknown model: {model}")
            
        # Determine generation type
        if model.startswith("kolors"):
            generation_type = GenerationType.IMAGE
        elif model == "kling-tryon":
            generation_type = GenerationType.IMAGE
        else:
            generation_type = GenerationType.VIDEO
            
        # Build API parameters
        api_params = self._build_api_params(request, model, model_type)
            
        # Make API request
        result_data = await self._call_api(generation_type, api_params)
        
        # Poll for completion
        if result_data.get("status") == "processing":
            result_data = await self._poll_for_completion(
                result_data["task_id"],
                generation_type
            )
        
        # Download generated content
        file_path = await self._download_result(request, result_data, generation_type)
        
        # Calculate cost
        cost = self.PRICING.get(model, 0.0)
        
        # Adjust cost for video duration
        if generation_type == GenerationType.VIDEO:
            duration = request.parameters.get("duration", 5)
            cost = cost * (duration / 5)  # Base price is for 5 seconds
        
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
                "kling_task_id": result_data.get("task_id"),
                "duration": api_params.get("duration"),
                "mode": api_params.get("mode", "standard"),
            }
        )

    def _build_api_params(self, request: GenerationRequest, model: str, model_type: str) -> Dict[str, Any]:
        """Build API parameters for Kling request."""
        params = {
            "model": model_type,
            "prompt": request.prompt,
        }
        
        # Video-specific parameters
        if model.startswith("kling") and not model.startswith("kolors"):
            params["duration"] = request.parameters.get("duration", 5)
            params["aspect_ratio"] = request.parameters.get("aspect_ratio", "16:9")
            params["camera_motion"] = request.parameters.get("camera_motion", "auto")
            
            # Professional vs Standard mode
            if "pro" in model or "master" in model:
                params["mode"] = "professional"
            else:
                params["mode"] = request.parameters.get("mode", "standard")
            
            # Image-to-video requires reference image
            if "image" in model and request.reference_assets:
                params["image"] = request.reference_assets[0]
                params["image_weight"] = request.parameters.get("image_weight", 0.5)
            
            # Lip sync parameters
            if model == "kling-lipsync" and len(request.reference_assets) >= 2:
                params["video"] = request.reference_assets[0]
                params["audio"] = request.reference_assets[1]
            
            # Video extension
            if model == "kling-extend" and request.reference_assets:
                params["video"] = request.reference_assets[0]
                params["extend_duration"] = request.parameters.get("extend_duration", 5)
                
        # Image generation parameters
        elif model.startswith("kolors"):
            params["width"] = request.parameters.get("width", 1024)
            params["height"] = request.parameters.get("height", 1024)
            params["num_images"] = request.parameters.get("num_images", 1)
            params["style"] = request.parameters.get("style", "default")
            
        # Virtual try-on
        elif model == "kling-tryon":
            if len(request.reference_assets) >= 2:
                params["person_image"] = request.reference_assets[0]
                params["garment_image"] = request.reference_assets[1]
            else:
                raise ValueError("Virtual try-on requires person and garment images")
        
        # Add any custom parameters
        if request.parameters:
            for key, value in request.parameters.items():
                if key not in params:
                    params[key] = value
        
        return params

    async def _call_api(self, generation_type: GenerationType, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to Kling."""
        session = await self._get_session()
        
        # Determine endpoint based on generation type
        if generation_type == GenerationType.VIDEO:
            endpoint = f"{self.base_url}/api/generation/video"
        else:
            endpoint = f"{self.base_url}/api/generation/image"
        
        try:
            async with session.post(endpoint, json=params) as response:
                response_data = await response.json()
                
                if response.status == 429:
                    raise RateLimitError("Kling rate limit exceeded")
                elif response.status == 401:
                    raise AuthenticationError("Invalid Kling API key")
                elif response.status == 402:
                    raise GenerationError("Insufficient credits")
                elif response.status != 200:
                    error_msg = response_data.get("message", "Unknown error")
                    raise GenerationError(f"Kling API error: {error_msg}")
                    
                return response_data
                
        except aiohttp.ClientError as e:
            raise GenerationError(f"Network error: {str(e)}")

    async def _poll_for_completion(
        self, 
        task_id: str, 
        generation_type: GenerationType,
        max_attempts: int = 120
    ) -> Dict[str, Any]:
        """Poll for task completion."""
        session = await self._get_session()
        
        # Status endpoint
        if generation_type == GenerationType.VIDEO:
            endpoint = f"{self.base_url}/api/generation/video/status/{task_id}"
        else:
            endpoint = f"{self.base_url}/api/generation/image/status/{task_id}"
        
        for attempt in range(max_attempts):
            try:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") == "completed":
                            return data
                        elif data.get("status") == "failed":
                            raise GenerationError(f"Generation failed: {data.get('error')}")
                        elif data.get("status") in ["cancelled", "expired"]:
                            raise GenerationError(f"Generation {data.get('status')}")
                    
                # Wait before next poll (longer for video)
                wait_time = 5 if generation_type == GenerationType.VIDEO else 2
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error polling for result: {e}")
                
        raise GenerationError("Timeout waiting for generation to complete")

    async def _download_result(
        self, 
        request: GenerationRequest, 
        result_data: Dict[str, Any],
        generation_type: GenerationType
    ) -> Path:
        """Download generated content."""
        # Get URL from result
        if generation_type == GenerationType.VIDEO:
            content_url = result_data.get("video_url")
            ext = ".mp4"
        else:
            content_url = result_data.get("image_url")
            ext = ".png"
            
        if not content_url:
            raise GenerationError("No content URL in response")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = request.model.replace("-", "_")
        filename = f"kling_{model_name}_{timestamp}{ext}"
        
        # Download file
        output_path = request.output_path or Path.cwd() / filename
        await download_file(content_url, output_path)
        
        return output_path

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None