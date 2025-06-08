"""Luma Dream Machine provider for high-quality video generation."""

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


class LumaProvider(Provider):
    """Provider for Luma Dream Machine API integration."""

    # API endpoints
    BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"
    
    # Model configurations
    MODELS = {
        # Dream Machine models
        "dream-machine": "dream_machine_v1",
        "dream-machine-turbo": "dream_machine_turbo",
        
        # Special features
        "luma-extend": "extend",
        "luma-interpolate": "interpolate",
        "luma-loop": "loop",  # Create perfect loops
        "luma-keyframes": "keyframes",  # Multi-keyframe control
    }
    
    # Pricing per generation
    PRICING = {
        "dream-machine": 0.24,  # 120 frames @ $0.002/frame
        "dream-machine-turbo": 0.12,  # Faster, lower quality
        "luma-extend": 0.20,
        "luma-interpolate": 0.16,
        "luma-loop": 0.24,
        "luma-keyframes": 0.32,  # More complex
    }
    
    # Video generation parameters
    VIDEO_PARAMS = {
        "dream-machine": {
            "frames": 120,  # 5 seconds at 24fps
            "fps": 24,
            "resolution": (1280, 720),
            "quality": "high",
        },
        "dream-machine-turbo": {
            "frames": 120,
            "fps": 24,
            "resolution": (1024, 576),
            "quality": "medium",
        },
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Luma provider.
        
        Args:
            api_key: Luma API key (or from LUMA_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("LUMA_API_KEY")
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def provider_id(self) -> str:
        """Get the provider ID."""
        return "luma"

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "Luma Dream Machine"

    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            supported_types=[GenerationType.VIDEO],
            max_resolution=(1280, 720),
            supports_streaming=False,
            supports_batch=True,
            models=list(self.MODELS.keys()),
            features=[
                "text_to_video",
                "image_to_video",
                "video_extend",
                "video_interpolation",
                "perfect_loops",
                "keyframe_control",
                "smooth_motion",
                "cinematic_quality",
                "physics_understanding",
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
                    f"{self.BASE_URL}/account/info",
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
        """Generate content using Luma API."""
        if not self.api_key:
            raise AuthenticationError("Luma API key not configured")

        model = request.model or "dream-machine"
        if model not in self.MODELS:
            raise GenerationError(f"Unknown model: {model}")

        try:
            # Start generation
            generation_id = await self._start_generation(request, model)
            
            # Poll for completion
            result_data = await self._poll_for_completion(generation_id)
            
            # Download the result
            local_path = await self._download_result(
                result_data["video_url"],
                request.output_path
            )
            
            # Calculate cost
            cost = self.PRICING.get(model, 0.24)
            
            return GenerationResult(
                success=True,
                provider=self.provider_id,
                model=model,
                output_path=local_path,
                cost=cost,
                metadata={
                    "generation_id": generation_id,
                    "frames": result_data.get("frames", 120),
                    "resolution": result_data.get("resolution"),
                    "fps": result_data.get("fps", 24),
                    "loop": result_data.get("is_loop", False),
                },
            )
            
        except Exception as e:
            logger.error(f"Luma generation failed: {e}")
            raise GenerationError(f"Generation failed: {str(e)}")

    async def _start_generation(
        self, request: GenerationRequest, model: str
    ) -> str:
        """Start a generation."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Prepare request data
        data = {
            "prompt": request.prompt,
        }
        
        # Model-specific parameters
        if model in ["dream-machine", "dream-machine-turbo"]:
            params = self.VIDEO_PARAMS[model]
            data["frames"] = request.parameters.get("frames", params["frames"])
            data["fps"] = params["fps"]
        
        # Handle different modes
        if model == "luma-loop":
            data["loop"] = True
            data["loop_frames"] = request.parameters.get("loop_frames", 120)
        
        elif model == "luma-keyframes":
            # Keyframe format: [{"frame": 0, "prompt": "..."}, ...]
            if "keyframes" in request.parameters:
                data["keyframes"] = request.parameters["keyframes"]
            else:
                # Default to single keyframe
                data["keyframes"] = [{"frame": 0, "prompt": request.prompt}]
        
        elif model == "luma-extend":
            if not request.input_image:
                raise ValueError("Video extension requires input video")
            data["video_url"] = request.input_image
            data["extend_frames"] = request.parameters.get("extend_frames", 60)
            data["direction"] = request.parameters.get("direction", "forward")
        
        elif model == "luma-interpolate":
            # Requires start and end frames
            if "start_image" not in request.parameters or "end_image" not in request.parameters:
                raise ValueError("Interpolation requires start_image and end_image")
            data["start_image"] = request.parameters["start_image"]
            data["end_image"] = request.parameters["end_image"]
            data["interpolation_frames"] = request.parameters.get("frames", 120)
        
        # Standard image-to-video
        elif request.input_image:
            data["image_url"] = request.input_image
        
        # Optional parameters
        if "seed" in request.parameters:
            data["seed"] = request.parameters["seed"]
        
        if "motion_scale" in request.parameters:
            data["motion_scale"] = request.parameters["motion_scale"]
        
        if "camera_motion" in request.parameters:
            data["camera_motion"] = request.parameters["camera_motion"]
        
        # Aspect ratio
        if "aspect_ratio" in request.parameters:
            data["aspect_ratio"] = request.parameters["aspect_ratio"]
        
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
                return result["id"]

    async def _poll_for_completion(
        self, generation_id: str, max_wait: int = 600
    ) -> Dict[str, Any]:
        """Poll for generation completion."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            async with self._get_session() as session:
                async with session.get(
                    f"{self.BASE_URL}/generations/{generation_id}",
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        raise GenerationError(f"Failed to check status: {response.status}")
                    
                    data = await response.json()
                    state = data["state"]
                    
                    if state == "completed":
                        return data
                    elif state == "failed":
                        raise GenerationError(f"Generation failed: {data.get('failure_reason')}")
                    
                    # Log progress
                    if "progress" in data:
                        logger.info(f"Generation progress: {data['progress']}%")
                    
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
            output_path = Path(f"outputs/luma_{timestamp}.mp4")
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
        model = request.model or "dream-machine"
        
        # Adjust cost for frame count
        if model in ["dream-machine", "dream-machine-turbo"]:
            frames = request.parameters.get("frames", 120)
            base_cost = self.PRICING.get(model, 0.24)
            return base_cost * (frames / 120)  # Scale by frame count
        
        return self.PRICING.get(model, 0.24)

    def validate_request(self, request: GenerationRequest) -> None:
        """Validate a generation request."""
        super().validate_request(request)
        
        model = request.model or "dream-machine"
        
        # Check model exists
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}")
        
        # Validate frame count
        if "frames" in request.parameters:
            frames = request.parameters["frames"]
            if not 24 <= frames <= 240:  # 1-10 seconds
                raise ValueError("Frames must be between 24 and 240")
        
        # Validate motion scale
        if "motion_scale" in request.parameters:
            scale = request.parameters["motion_scale"]
            if not 0 <= scale <= 1:
                raise ValueError("Motion scale must be between 0 and 1")
        
        # Validate keyframes
        if model == "luma-keyframes" and "keyframes" in request.parameters:
            keyframes = request.parameters["keyframes"]
            if not isinstance(keyframes, list):
                raise ValueError("Keyframes must be a list")
            
            for kf in keyframes:
                if not isinstance(kf, dict) or "frame" not in kf or "prompt" not in kf:
                    raise ValueError("Each keyframe must have 'frame' and 'prompt'")
                
                if not isinstance(kf["frame"], int) or kf["frame"] < 0:
                    raise ValueError("Keyframe frame must be a non-negative integer")
        
        # Validate camera motion
        if "camera_motion" in request.parameters:
            valid_motions = [
                "none", "zoom_in", "zoom_out", "pan_left", "pan_right",
                "pan_up", "pan_down", "orbit_left", "orbit_right", "dolly_in", "dolly_out"
            ]
            if request.parameters["camera_motion"] not in valid_motions:
                raise ValueError(f"Invalid camera motion. Must be one of: {valid_motions}")
        
        # Validate aspect ratio
        if "aspect_ratio" in request.parameters:
            valid_ratios = ["16:9", "9:16", "1:1", "4:3", "3:4"]
            if request.parameters["aspect_ratio"] not in valid_ratios:
                raise ValueError(f"Invalid aspect ratio. Must be one of: {valid_ratios}")