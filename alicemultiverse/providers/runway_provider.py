"""Runway Gen-3 Alpha provider for professional video generation."""

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

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


class RunwayProvider(Provider):
    """Provider for Runway Gen-3 Alpha API integration."""

    # API endpoints
    BASE_URL = "https://api.runwayml.com/v1"
    
    # Model configurations
    MODELS = {
        # Gen-3 Alpha models
        "gen3-alpha": "gen3_alpha",
        "gen3-alpha-turbo": "gen3_alpha_turbo",
        
        # Legacy models (if still available)
        "gen2": "gen2",
        
        # Special features
        "runway-extend": "extend",
        "runway-interpolate": "interpolate",
        "runway-upscale": "upscale",
    }
    
    # Pricing per second of video
    PRICING = {
        "gen3-alpha": 0.10,  # $0.10 per second
        "gen3-alpha-turbo": 0.05,  # Faster, lower quality
        "gen2": 0.05,  # Legacy pricing
        "runway-extend": 0.08,
        "runway-interpolate": 0.06,
        "runway-upscale": 0.04,
    }
    
    # Video generation parameters
    VIDEO_PARAMS = {
        "gen3-alpha": {
            "min_duration": 5,
            "max_duration": 10,
            "fps": 24,
            "resolution": (1280, 768),  # 5:3 aspect ratio
            "quality": "high",
        },
        "gen3-alpha-turbo": {
            "min_duration": 5,
            "max_duration": 10,
            "fps": 24,
            "resolution": (1280, 768),
            "quality": "medium",
        },
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Runway provider.
        
        Args:
            api_key: Runway API key (or from RUNWAY_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("RUNWAY_API_KEY")
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def provider_id(self) -> str:
        """Get the provider ID."""
        return "runway"

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "Runway"

    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            supported_types=[GenerationType.VIDEO, GenerationType.IMAGE],
            max_resolution=(1280, 768),
            supports_streaming=False,
            supports_batch=False,
            models=list(self.MODELS.keys()),
            features=[
                "text_to_video",
                "image_to_video",
                "video_extend",
                "video_interpolation",
                "video_upscaling",
                "professional_quality",
                "cinematic_generation",
            ],
        )

    async def check_status(self) -> ProviderStatus:
        """Check provider status."""
        if not self.api_key:
            return ProviderStatus(
                is_available=False,
                error_message="API key not configured",
            )

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            async with self._get_session() as session:
                async with session.get(
                    f"{self.BASE_URL}/user",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ProviderStatus(
                            is_available=True,
                            credits_remaining=data.get("credits", 0),
                        )
                    elif response.status == 401:
                        return ProviderStatus(
                            is_available=False,
                            error_message="Invalid API key",
                        )
                    else:
                        return ProviderStatus(
                            is_available=False,
                            error_message=f"API error: {response.status}",
                        )
                        
        except Exception as e:
            return ProviderStatus(
                is_available=False,
                error_message=str(e),
            )

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content using Runway API."""
        if not self.api_key:
            raise AuthenticationError("Runway API key not configured")

        model = request.model or "gen3-alpha"
        if model not in self.MODELS:
            raise GenerationError(f"Unknown model: {model}")

        try:
            # Start generation
            task_id = await self._start_generation(request, model)
            
            # Poll for completion
            result_data = await self._poll_for_completion(task_id)
            
            # Download the result
            local_path = await self._download_result(
                result_data["output_url"],
                request.output_path
            )
            
            # Calculate cost
            duration = result_data.get("duration", 5)
            cost = self.PRICING.get(model, 0.10) * duration
            
            return GenerationResult(
                success=True,
                provider=self.provider_id,
                model=model,
                output_path=local_path,
                cost=cost,
                metadata={
                    "task_id": task_id,
                    "duration": duration,
                    "resolution": result_data.get("resolution"),
                    "fps": result_data.get("fps", 24),
                },
            )
            
        except Exception as e:
            logger.error(f"Runway generation failed: {e}")
            raise GenerationError(f"Generation failed: {str(e)}")

    async def _start_generation(
        self, request: GenerationRequest, model: str
    ) -> str:
        """Start a generation task."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Prepare request data
        data = {
            "model": self.MODELS[model],
            "prompt": request.prompt,
        }
        
        # Add model-specific parameters
        if model in self.VIDEO_PARAMS:
            params = self.VIDEO_PARAMS[model]
            data.update({
                "duration": min(
                    request.parameters.get("duration", params["min_duration"]),
                    params["max_duration"]
                ),
                "fps": params["fps"],
                "resolution": params["resolution"],
            })
        
        # Add optional parameters
        if request.input_image:
            data["image_url"] = request.input_image
            data["mode"] = "image_to_video"
        else:
            data["mode"] = "text_to_video"
        
        if "seed" in request.parameters:
            data["seed"] = request.parameters["seed"]
        
        if "motion_amount" in request.parameters:
            data["motion_amount"] = request.parameters["motion_amount"]
        
        # Camera controls if specified
        if "camera_motion" in request.parameters:
            data["camera_motion"] = request.parameters["camera_motion"]
        
        async with self._get_session() as session:
            async with session.post(
                f"{self.BASE_URL}/generations",
                headers=headers,
                json=data,
            ) as response:
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status != 200:
                    error_data = await response.json()
                    raise GenerationError(
                        f"API error: {error_data.get('message', 'Unknown error')}"
                    )
                
                result = await response.json()
                return result["task_id"]

    async def _poll_for_completion(
        self, task_id: str, max_wait: int = 600
    ) -> Dict[str, Any]:
        """Poll for task completion."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            async with self._get_session() as session:
                async with session.get(
                    f"{self.BASE_URL}/generations/{task_id}",
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        raise GenerationError(f"Failed to check status: {response.status}")
                    
                    data = await response.json()
                    status = data["status"]
                    
                    if status == "completed":
                        return data
                    elif status == "failed":
                        raise GenerationError(f"Generation failed: {data.get('error')}")
                    
                    # Wait before next poll
                    await asyncio.sleep(5)
        
        raise GenerationError("Generation timed out")

    async def _download_result(
        self, url: str, output_path: Optional[Path]
    ) -> Path:
        """Download the generated video."""
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Generate default path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"outputs/runway_{timestamp}.mp4")
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        await download_file(url, output_path)
        return output_path

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session and not self._session.closed:
            await self._session.close()

    def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate the cost of a generation request."""
        model = request.model or "gen3-alpha"
        
        if model in self.VIDEO_PARAMS:
            params = self.VIDEO_PARAMS[model]
            duration = request.parameters.get("duration", params["min_duration"])
            return self.PRICING.get(model, 0.10) * duration
        
        return self.PRICING.get(model, 0.10)

    def validate_request(self, request: GenerationRequest) -> None:
        """Validate a generation request."""
        super().validate_request(request)
        
        model = request.model or "gen3-alpha"
        
        # Check model exists
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}")
        
        # Validate video parameters
        if model in self.VIDEO_PARAMS:
            params = self.VIDEO_PARAMS[model]
            duration = request.parameters.get("duration", params["min_duration"])
            
            if duration < params["min_duration"] or duration > params["max_duration"]:
                raise ValueError(
                    f"Duration must be between {params['min_duration']} "
                    f"and {params['max_duration']} seconds"
                )
        
        # Validate camera motion if provided
        if "camera_motion" in request.parameters:
            valid_motions = [
                "static", "zoom_in", "zoom_out", "pan_left", "pan_right",
                "tilt_up", "tilt_down", "orbit_left", "orbit_right"
            ]
            if request.parameters["camera_motion"] not in valid_motions:
                raise ValueError(
                    f"Invalid camera motion. Must be one of: {valid_motions}"
                )