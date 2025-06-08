"""MiniMax Hailuo provider for competitive video generation."""

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


class MiniMaxProvider(Provider):
    """Provider for MiniMax Hailuo API integration."""

    # API endpoints
    BASE_URL = "https://api.minimax.chat/v1"
    
    # Model configurations
    MODELS = {
        # Hailuo video models
        "hailuo-video": "video01",
        "hailuo-video-pro": "video01-pro",
        
        # Image models
        "hailuo-image": "image01",
        
        # Special features
        "hailuo-extend": "video-extend",
        "hailuo-music-video": "music-video",  # Music-driven generation
        "hailuo-style-transfer": "style-transfer",
    }
    
    # Pricing per generation
    PRICING = {
        "hailuo-video": 0.06,  # Competitive pricing
        "hailuo-video-pro": 0.12,  # Higher quality
        "hailuo-image": 0.02,
        "hailuo-extend": 0.08,
        "hailuo-music-video": 0.15,  # Includes music analysis
        "hailuo-style-transfer": 0.10,
    }
    
    # Video generation parameters
    VIDEO_PARAMS = {
        "hailuo-video": {
            "duration": 6,  # 6 seconds standard
            "fps": 24,
            "resolution": (1280, 720),
            "quality": "standard",
        },
        "hailuo-video-pro": {
            "duration": 6,
            "fps": 30,
            "resolution": (1920, 1080),
            "quality": "high",
        },
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize MiniMax provider.
        
        Args:
            api_key: MiniMax API key (or from MINIMAX_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def provider_id(self) -> str:
        """Get the provider ID."""
        return "minimax"

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "MiniMax Hailuo"

    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            supported_types=[GenerationType.VIDEO, GenerationType.IMAGE],
            max_resolution=(1920, 1080),
            supports_streaming=False,
            supports_batch=True,
            models=list(self.MODELS.keys()),
            features=[
                "text_to_video",
                "image_to_video",
                "video_extend",
                "music_sync",
                "style_transfer",
                "chinese_optimization",  # Better Chinese prompt understanding
                "competitive_pricing",
                "fast_generation",
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
                    f"{self.BASE_URL}/user/profile",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ProviderStatus(
                            is_available=True,
                            credits_remaining=data.get("balance", 0),
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
        """Generate content using MiniMax API."""
        if not self.api_key:
            raise AuthenticationError("MiniMax API key not configured")

        model = request.model or "hailuo-video"
        if model not in self.MODELS:
            raise GenerationError(f"Unknown model: {model}")

        try:
            # Start generation
            task_id = await self._start_generation(request, model)
            
            # Poll for completion
            result_data = await self._poll_for_completion(task_id)
            
            # Download the result
            local_path = await self._download_result(
                result_data["file_url"],
                request.output_path
            )
            
            # Calculate cost
            cost = self.PRICING.get(model, 0.06)
            
            return GenerationResult(
                success=True,
                provider=self.provider_id,
                model=model,
                output_path=local_path,
                cost=cost,
                metadata={
                    "task_id": task_id,
                    "duration": result_data.get("duration", 6),
                    "resolution": result_data.get("resolution"),
                    "fps": result_data.get("fps", 24),
                },
            )
            
        except Exception as e:
            logger.error(f"MiniMax generation failed: {e}")
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
        
        # Model-specific parameters
        if model in self.VIDEO_PARAMS:
            params = self.VIDEO_PARAMS[model]
            data.update({
                "video_length": request.parameters.get("duration", params["duration"]),
                "fps": params["fps"],
                "resolution": f"{params['resolution'][0]}x{params['resolution'][1]}",
            })
        
        # Handle music video mode
        if model == "hailuo-music-video":
            if "music_url" not in request.parameters:
                raise ValueError("Music video mode requires music_url parameter")
            data["music_url"] = request.parameters["music_url"]
            data["sync_to_beat"] = request.parameters.get("sync_to_beat", True)
        
        # Handle style transfer
        elif model == "hailuo-style-transfer":
            if "style_reference" not in request.parameters:
                raise ValueError("Style transfer requires style_reference parameter")
            data["style_reference"] = request.parameters["style_reference"]
            data["style_strength"] = request.parameters.get("style_strength", 0.7)
        
        # Standard parameters
        if request.input_image:
            data["image_url"] = request.input_image
            data["generation_mode"] = "image_to_video"
        else:
            data["generation_mode"] = "text_to_video"
        
        if "seed" in request.parameters:
            data["seed"] = request.parameters["seed"]
        
        if "motion_intensity" in request.parameters:
            data["motion_intensity"] = request.parameters["motion_intensity"]
        
        # Language optimization
        if "language" in request.parameters:
            data["language"] = request.parameters["language"]  # zh or en
        else:
            # Auto-detect Chinese
            if any(ord(c) > 127 for c in request.prompt):
                data["language"] = "zh"
            else:
                data["language"] = "en"
        
        async with self._get_session() as session:
            async with session.post(
                f"{self.BASE_URL}/video/submit_task",
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
        self, task_id: str, max_wait: int = 360
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
                    f"{self.BASE_URL}/video/query_task",
                    headers=headers,
                    params={"task_id": task_id},
                ) as response:
                    if response.status != 200:
                        raise GenerationError(f"Failed to check status: {response.status}")
                    
                    data = await response.json()
                    status = data["status"]
                    
                    if status == "success":
                        return data
                    elif status == "failed":
                        raise GenerationError(f"Generation failed: {data.get('error_msg')}")
                    
                    # Show progress
                    if "progress" in data:
                        logger.info(f"Generation progress: {data['progress']}%")
                    
                    # Wait before next poll
                    await asyncio.sleep(3)
        
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
            output_path = Path(f"outputs/minimax_{timestamp}.mp4")
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
        model = request.model or "hailuo-video"
        return self.PRICING.get(model, 0.06)

    def validate_request(self, request: GenerationRequest) -> None:
        """Validate a generation request."""
        super().validate_request(request)
        
        model = request.model or "hailuo-video"
        
        # Check model exists
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}")
        
        # Validate video duration
        if "duration" in request.parameters:
            duration = request.parameters["duration"]
            if not 1 <= duration <= 10:
                raise ValueError("Duration must be between 1 and 10 seconds")
        
        # Validate motion intensity
        if "motion_intensity" in request.parameters:
            intensity = request.parameters["motion_intensity"]
            if not 0 <= intensity <= 1:
                raise ValueError("Motion intensity must be between 0 and 1")
        
        # Validate style strength
        if "style_strength" in request.parameters:
            strength = request.parameters["style_strength"]
            if not 0 <= strength <= 1:
                raise ValueError("Style strength must be between 0 and 1")
        
        # Validate language
        if "language" in request.parameters:
            if request.parameters["language"] not in ["zh", "en"]:
                raise ValueError("Language must be 'zh' or 'en'")