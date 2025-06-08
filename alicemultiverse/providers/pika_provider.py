"""Pika Labs provider for HD video generation with ingredient control."""

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


class PikaProvider(Provider):
    """Provider for Pika Labs API integration."""

    # API endpoints
    BASE_URL = "https://api.pika.art/v1"
    
    # Model configurations
    MODELS = {
        # Pika 2.1 models
        "pika-2.1": "pika_2.1",
        "pika-2.1-hd": "pika_2.1_hd",
        "pika-2.0": "pika_2.0",  # Legacy
        
        # Special features
        "pika-ingredients": "ingredients",  # Ingredient control
        "pika-extend": "extend",
        "pika-animate": "animate",  # Image animation
        "pika-lip-sync": "lip_sync",
    }
    
    # Pricing per generation
    PRICING = {
        "pika-2.1": 0.05,  # Standard quality
        "pika-2.1-hd": 0.10,  # HD 1080p
        "pika-2.0": 0.04,  # Legacy
        "pika-ingredients": 0.08,
        "pika-extend": 0.06,
        "pika-animate": 0.07,
        "pika-lip-sync": 0.12,
    }
    
    # Video generation parameters
    VIDEO_PARAMS = {
        "pika-2.1": {
            "duration": 3,  # Fixed 3 seconds
            "fps": 24,
            "resolution": (1024, 576),  # 16:9
            "quality": "standard",
        },
        "pika-2.1-hd": {
            "duration": 3,
            "fps": 24,
            "resolution": (1920, 1080),  # Full HD
            "quality": "high",
        },
    }
    
    # Supported aspect ratios
    ASPECT_RATIOS = {
        "16:9": (1024, 576),
        "9:16": (576, 1024),  # Vertical
        "1:1": (768, 768),    # Square
        "4:3": (768, 576),
        "3:4": (576, 768),
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Pika provider.
        
        Args:
            api_key: Pika API key (or from PIKA_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("PIKA_API_KEY")
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def provider_id(self) -> str:
        """Get the provider ID."""
        return "pika"

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "Pika Labs"

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
                "hd_1080p",
                "ingredient_control",
                "video_extend",
                "lip_sync",
                "multiple_aspect_ratios",
                "animate_images",
                "style_control",
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
                    f"{self.BASE_URL}/account",
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
        """Generate content using Pika API."""
        if not self.api_key:
            raise AuthenticationError("Pika API key not configured")

        model = request.model or "pika-2.1"
        if model not in self.MODELS:
            raise GenerationError(f"Unknown model: {model}")

        try:
            # Start generation
            job_id = await self._start_generation(request, model)
            
            # Poll for completion
            result_data = await self._poll_for_completion(job_id)
            
            # Download the result
            local_path = await self._download_result(
                result_data["video_url"],
                request.output_path
            )
            
            # Calculate cost
            cost = self.PRICING.get(model, 0.05)
            
            return GenerationResult(
                success=True,
                provider=self.provider_id,
                model=model,
                output_path=local_path,
                cost=cost,
                metadata={
                    "job_id": job_id,
                    "duration": result_data.get("duration", 3),
                    "resolution": result_data.get("resolution"),
                    "fps": result_data.get("fps", 24),
                    "ingredients": result_data.get("ingredients", []),
                },
            )
            
        except Exception as e:
            logger.error(f"Pika generation failed: {e}")
            raise GenerationError(f"Generation failed: {str(e)}")

    async def _start_generation(
        self, request: GenerationRequest, model: str
    ) -> str:
        """Start a generation job."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Prepare request data
        data = {
            "model": self.MODELS[model],
            "prompt": request.prompt,
        }
        
        # Handle aspect ratio
        aspect_ratio = request.parameters.get("aspect_ratio", "16:9")
        if aspect_ratio in self.ASPECT_RATIOS:
            data["aspect_ratio"] = aspect_ratio
        
        # Handle ingredients (Pika's unique feature)
        if model == "pika-ingredients" or request.parameters.get("ingredients"):
            data["ingredients"] = request.parameters.get("ingredients", [])
            # Ingredients format: [{"type": "character", "description": "..."}, ...]
        
        # Add optional parameters
        if request.input_image:
            data["image_url"] = request.input_image
            data["mode"] = "image_to_video"
        else:
            data["mode"] = "text_to_video"
        
        if "seed" in request.parameters:
            data["seed"] = request.parameters["seed"]
        
        if "motion_strength" in request.parameters:
            data["motion_strength"] = request.parameters["motion_strength"]
        
        if "guidance_scale" in request.parameters:
            data["guidance_scale"] = request.parameters["guidance_scale"]
        
        # Style parameters
        if "style" in request.parameters:
            data["style"] = request.parameters["style"]
        
        # HD mode
        if model == "pika-2.1-hd":
            data["quality"] = "hd"
            data["resolution"] = "1080p"
        
        async with self._get_session() as session:
            async with session.post(
                f"{self.BASE_URL}/generate",
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
                return result["job_id"]

    async def _poll_for_completion(
        self, job_id: str, max_wait: int = 300
    ) -> Dict[str, Any]:
        """Poll for job completion."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            async with self._get_session() as session:
                async with session.get(
                    f"{self.BASE_URL}/jobs/{job_id}",
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
            output_path = Path(f"outputs/pika_{timestamp}.mp4")
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
        model = request.model or "pika-2.1"
        return self.PRICING.get(model, 0.05)

    def validate_request(self, request: GenerationRequest) -> None:
        """Validate a generation request."""
        super().validate_request(request)
        
        model = request.model or "pika-2.1"
        
        # Check model exists
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}")
        
        # Validate aspect ratio
        if "aspect_ratio" in request.parameters:
            if request.parameters["aspect_ratio"] not in self.ASPECT_RATIOS:
                raise ValueError(
                    f"Invalid aspect ratio. Must be one of: {list(self.ASPECT_RATIOS.keys())}"
                )
        
        # Validate ingredients format
        if "ingredients" in request.parameters:
            ingredients = request.parameters["ingredients"]
            if not isinstance(ingredients, list):
                raise ValueError("Ingredients must be a list")
            
            for ing in ingredients:
                if not isinstance(ing, dict) or "type" not in ing or "description" not in ing:
                    raise ValueError(
                        "Each ingredient must have 'type' and 'description'"
                    )
                
                valid_types = ["character", "object", "environment", "style"]
                if ing["type"] not in valid_types:
                    raise ValueError(
                        f"Ingredient type must be one of: {valid_types}"
                    )
        
        # Validate motion strength
        if "motion_strength" in request.parameters:
            strength = request.parameters["motion_strength"]
            if not 0 <= strength <= 1:
                raise ValueError("Motion strength must be between 0 and 1")
        
        # Validate guidance scale
        if "guidance_scale" in request.parameters:
            scale = request.parameters["guidance_scale"]
            if not 1 <= scale <= 20:
                raise ValueError("Guidance scale must be between 1 and 20")