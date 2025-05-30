"""Hedra provider for AI avatar video generation."""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import requests
import aiohttp
import asyncio

from .provider import Provider as BaseProvider
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus
)
from ..core.exceptions import ValidationError
from .provider import ProviderError
from ..core.structured_logging import get_logger
from ..events.postgres_events import publish_event

logger = get_logger(__name__)


class HedraProvider(BaseProvider):
    """Provider for Hedra's Character API for talking avatar videos."""
    
    BASE_URL = "https://api.hedra.com/web-app/public"
    POLL_INTERVAL = 5  # seconds
    DEFAULT_MODEL_ID = "d1dd37a3-e39a-4854-a298-6510289f9cf2"  # Character-2
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Hedra provider.
        
        Args:
            api_key: Hedra API key. If not provided, uses HEDRA_API_KEY env var.
        """
        super().__init__()
        self.api_key = api_key or os.getenv("HEDRA_API_KEY")
        if not self.api_key:
            raise ValueError("Hedra API key not provided")
        
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    @property
    def name(self) -> str:
        return "hedra"
    
    @property
    def supported_types(self) -> List[GenerationType]:
        return [GenerationType.VIDEO]
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            generation_types=[GenerationType.VIDEO],
            models=["character-2"],
            features=["image_to_video", "audio_to_video"],
            pricing={"character-2": 0.50}
        )
    
    @property
    def available_models(self) -> List[str]:
        return ["character-2"]
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        if model == "character-2":
            return {
                "id": "character-2",
                "name": "Character-2",
                "description": "Hedra's Character-2 foundation model for talking avatars",
                "supports": [GenerationType.VIDEO],
                "cost_per_generation": 0.50,
                "parameters": {
                    "aspect_ratio": ["16:9", "9:16", "1:1"],
                    "resolution": ["540p", "720p"],
                    "max_duration_ms": 60000,
                    "requires_audio": True,
                    "requires_image": True
                }
            }
        raise ValueError(f"Unknown model: {model}")
    
    def _get_request_url(self, endpoint: str) -> str:
        """Build full request URL."""
        return f"{self.BASE_URL}{endpoint}"
    
    async def _upload_asset(
        self,
        session: aiohttp.ClientSession,
        file_path: Path,
        asset_type: str
    ) -> str:
        """Upload an asset (image or audio) to Hedra.
        
        Args:
            session: Async HTTP session
            file_path: Path to the file to upload
            asset_type: Type of asset ("image" or "audio")
            
        Returns:
            Asset ID
        """
        # Create asset record
        create_data = {
            "name": file_path.name,
            "type": asset_type
        }
        
        async with session.post(
            self._get_request_url("/assets"),
            json=create_data,
            headers=self.headers
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ProviderError(f"Failed to create {asset_type}: {error_text}")
            
            result = await response.json()
            asset_id = result["id"]
        
        # Upload file
        with open(file_path, "rb") as f:
            data = aiohttp.FormData()
            data.add_field("file", f, filename=file_path.name)
            
            upload_headers = self.headers.copy()
            # Remove Content-Type for multipart upload
            upload_headers.pop("Content-Type", None)
            
            async with session.post(
                self._get_request_url(f"/assets/{asset_id}/upload"),
                data=data,
                headers=upload_headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(f"Failed to upload {asset_type}: {error_text}")
        
        logger.info(f"Uploaded {asset_type} asset", asset_id=asset_id)
        return asset_id
    
    async def _wait_for_generation(
        self,
        session: aiohttp.ClientSession,
        generation_id: str
    ) -> Dict[str, Any]:
        """Poll for generation completion.
        
        Args:
            session: Async HTTP session
            generation_id: ID of the generation to poll
            
        Returns:
            Final status response
        """
        while True:
            async with session.get(
                self._get_request_url(f"/generations/{generation_id}/status"),
                headers=self.headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(f"Failed to get status: {error_text}")
                
                status_data = await response.json()
                status = status_data["status"]
                
                logger.info(
                    "Generation status",
                    generation_id=generation_id,
                    status=status
                )
                
                if status in ["complete", "error"]:
                    return status_data
                
                await asyncio.sleep(self.POLL_INTERVAL)
    
    async def _download_video(
        self,
        session: aiohttp.ClientSession,
        url: str,
        output_path: Path
    ) -> None:
        """Download generated video.
        
        Args:
            session: Async HTTP session
            url: Download URL (likely presigned S3)
            output_path: Where to save the video
        """
        # Use regular session without API headers for presigned URL
        async with session.get(url) as response:
            if response.status != 200:
                raise ProviderError(f"Failed to download video: {response.status}")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    f.write(chunk)
        
        logger.info("Downloaded video", path=str(output_path))
    
    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate a talking avatar video.
        
        Args:
            request: Generation request with prompt, audio, and image
            
        Returns:
            Generation result with video file
        """
        start_time = datetime.now()
        
        # Validate request
        if request.generation_type != GenerationType.VIDEO:
            raise ValidationError(f"Hedra only supports video generation")
        
        if not request.reference_assets or len(request.reference_assets) < 2:
            raise ValidationError("Hedra requires an image and audio file")
        
        # Extract image and audio paths
        # Convention: first reference is image, second is audio
        image_path = Path(request.reference_assets[0])
        audio_path = Path(request.reference_assets[1])
        
        if not image_path.exists():
            raise ValidationError(f"Image file not found: {image_path}")
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        # Extract parameters
        params = request.parameters or {}
        aspect_ratio = params.get("aspect_ratio", "16:9")
        resolution = params.get("resolution", "720p")
        duration_ms = params.get("duration_ms")
        seed = params.get("seed")
        
        # Validate parameters
        model_info = self.get_model_info("character-2")
        if aspect_ratio not in model_info["parameters"]["aspect_ratio"]:
            raise ValidationError(f"Invalid aspect ratio: {aspect_ratio}")
        if resolution not in model_info["parameters"]["resolution"]:
            raise ValidationError(f"Invalid resolution: {resolution}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get model ID (use default for now)
                model_id = self.DEFAULT_MODEL_ID
                
                # Upload assets
                logger.info("Uploading assets to Hedra")
                image_id = await self._upload_asset(session, image_path, "image")
                audio_id = await self._upload_asset(session, audio_path, "audio")
                
                # Create generation request
                generation_data = {
                    "type": "video",
                    "ai_model_id": model_id,
                    "start_keyframe_id": image_id,
                    "audio_id": audio_id,
                    "generated_video_inputs": {
                        "text_prompt": request.prompt,
                        "resolution": resolution,
                        "aspect_ratio": aspect_ratio
                    }
                }
                
                # Add optional parameters
                if duration_ms is not None:
                    generation_data["generated_video_inputs"]["duration_ms"] = duration_ms
                if seed is not None:
                    generation_data["generated_video_inputs"]["seed"] = seed
                
                # Submit generation request
                logger.info("Submitting generation request")
                async with session.post(
                    self._get_request_url("/generations"),
                    json=generation_data,
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(f"Failed to create generation: {error_text}")
                    
                    result = await response.json()
                    generation_id = result["id"]
                
                # Publish generation started event
                await publish_event(
                    "generation.started",
                    {
                        "generation_id": generation_id,
                        "provider": self.name,
                        "model": "character-2",
                        "prompt": request.prompt,
                        "parameters": generation_data
                    }
                )
                
                # Wait for completion
                logger.info("Waiting for generation to complete", generation_id=generation_id)
                status_response = await self._wait_for_generation(session, generation_id)
                
                if status_response["status"] == "error":
                    error_msg = status_response.get("error_message", "Unknown error")
                    await publish_event(
                        "generation.failed",
                        {
                            "generation_id": generation_id,
                            "error": error_msg
                        }
                    )
                    raise ProviderError(f"Generation failed: {error_msg}")
                
                # Download video
                download_url = status_response.get("url")
                if not download_url:
                    raise ProviderError("No download URL in response")
                
                # Generate output path
                output_dir = Path("output") / "hedra" / datetime.now().strftime("%Y%m%d")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                asset_id = status_response.get("asset_id", generation_id)
                output_path = output_dir / f"{asset_id}.mp4"
                
                logger.info("Downloading generated video")
                await self._download_video(session, download_url, output_path)
                
                # Calculate generation time and cost
                generation_time = (datetime.now() - start_time).total_seconds()
                cost = self.get_model_info("character-2")["cost_per_generation"]
                
                # Publish completion event
                await publish_event(
                    "generation.completed",
                    {
                        "generation_id": generation_id,
                        "output_path": str(output_path),
                        "generation_time": generation_time,
                        "cost": cost
                    }
                )
                
                return GenerationResult(
                    success=True,
                    file_path=output_path,
                    generation_time=generation_time,
                    cost=cost,
                    metadata={
                        "generation_id": generation_id,
                        "asset_id": asset_id,
                        "aspect_ratio": aspect_ratio,
                        "resolution": resolution,
                        "image_id": image_id,
                        "audio_id": audio_id,
                        "prompt": request.prompt
                    },
                    provider=self.name,
                    model="character-2",
                    timestamp=start_time
                )
                
        except aiohttp.ClientError as e:
            logger.error("Network error", error=str(e), exc_info=True)
            raise ProviderError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error", error=str(e), exc_info=True)
            raise ProviderError(f"Unexpected error: {str(e)}")
    
    def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate cost for a generation request.
        
        Args:
            request: Generation request
            
        Returns:
            Estimated cost in USD
        """
        if request.generation_type != GenerationType.VIDEO:
            return 0.0
        
        # Fixed cost per generation for now
        return self.get_model_info("character-2")["cost_per_generation"]
    
    async def check_status(self) -> ProviderStatus:
        """Check provider availability.
        
        Returns:
            Provider status
        """
        try:
            # Try to get models endpoint to check API status
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self._get_request_url("/models"),
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return ProviderStatus.AVAILABLE
                    elif response.status == 401:
                        logger.error("Hedra API authentication failed")
                        return ProviderStatus.UNAVAILABLE
                    else:
                        logger.warning(f"Hedra API returned status {response.status}")
                        return ProviderStatus.DEGRADED
        except asyncio.TimeoutError:
            logger.warning("Hedra API timeout")
            return ProviderStatus.DEGRADED
        except Exception as e:
            logger.error(f"Failed to check Hedra status: {e}")
            return ProviderStatus.UNAVAILABLE
    
    async def validate_request(self, request: GenerationRequest) -> None:
        """Validate a generation request.
        
        Args:
            request: Generation request to validate
            
        Raises:
            ValidationError: If request is invalid
        """
        if request.generation_type != GenerationType.VIDEO:
            raise ValidationError("Hedra only supports video generation")
        
        if not request.reference_assets or len(request.reference_assets) < 2:
            raise ValidationError("Hedra requires an image and audio file as reference assets")
        
        # Check file existence
        image_path = Path(request.reference_assets[0])
        audio_path = Path(request.reference_assets[1])
        
        if not image_path.exists():
            raise ValidationError(f"Image file not found: {image_path}")
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        # Validate parameters
        params = request.parameters or {}
        aspect_ratio = params.get("aspect_ratio", "16:9")
        resolution = params.get("resolution", "720p")
        
        model_info = self.get_model_info("character-2")
        if aspect_ratio not in model_info["parameters"]["aspect_ratio"]:
            raise ValidationError(
                f"Invalid aspect ratio: {aspect_ratio}. "
                f"Must be one of: {model_info['parameters']['aspect_ratio']}"
            )
        if resolution not in model_info["parameters"]["resolution"]:
            raise ValidationError(
                f"Invalid resolution: {resolution}. "
                f"Must be one of: {model_info['parameters']['resolution']}"
            )
        
        # Check duration limit
        duration_ms = params.get("duration_ms")
        if duration_ms and duration_ms > model_info["parameters"]["max_duration_ms"]:
            raise ValidationError(
                f"Duration {duration_ms}ms exceeds maximum "
                f"{model_info['parameters']['max_duration_ms']}ms"
            )