"""Google AI (Imagen & Veo) provider for AliceMultiverse.

Supports:
- Imagen 3: Text to image generation with high quality output
- Veo 2: Video generation from text or image prompts
"""

import asyncio
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any

from .base_provider import BaseProvider
from .provider import GenerationError
from .provider_types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class GoogleAIBackend(Enum):
    """Backend options for Google AI services."""
    GEMINI = "gemini"  # Gemini API (recommended, simpler)
    VERTEX = "vertex"  # Vertex AI (requires GCP project)


class GoogleAIProvider(BaseProvider):
    """Google AI provider implementation for Imagen and Veo."""

    # Model mapping
    MODELS = {
        # Imagen 3 models
        "imagen-3": "imagen-3.0-generate-002",
        "imagen": "imagen-3.0-generate-002",  # Default alias
        "imagen-3.0": "imagen-3.0-generate-002",
        "imagen-3-fast": "imagen-3.0-fast-generate-001",

        # Veo models
        "veo-3": "veo-3.0-generate-preview",  # Latest Veo 3 (preview)
        "veo-3.0": "veo-3.0-generate-preview",
        "veo": "veo-3.0-generate-preview",  # Default to latest
        "veo-2": "veo-002",
        "veo-001": "veo-001",  # Earlier version
    }

    # API endpoints
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"
    VERTEX_BASE_URL = "https://{location}-aiplatform.googleapis.com"

    # Pricing per generation (approximate)
    PRICING = {
        "imagen-3.0-generate-002": 0.03,  # $0.03 per image
        "imagen-3.0-fast-generate-001": 0.02,  # Faster, slightly lower quality
        "veo-3.0-generate-preview": 0.35,  # ~$0.35 per second (8s = $2.80)
        "veo-002": 0.10,  # Estimated for 8-second video
        "veo-001": 0.08,  # Earlier version
    }

    # Supported aspect ratios
    ASPECT_RATIOS = {
        "imagen": ["1:1", "16:9", "9:16", "4:3", "3:4"],
        "veo": ["16:9", "9:16", "1:1"],  # Veo 3 supports more aspect ratios
    }

    def __init__(self, api_key: str = None, backend: GoogleAIBackend = GoogleAIBackend.GEMINI,
                 project_id: str = None, location: str = "us-central1", **kwargs):
        """Initialize Google AI provider.

        Args:
            api_key: API key for Gemini or service account key for Vertex
            backend: Which backend to use (GEMINI or VERTEX)
            project_id: GCP project ID (required for Vertex)
            location: GCP location (for Vertex, default: us-central1)
            **kwargs: Additional arguments for BaseProvider
        """
        self.backend = backend
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location

        if backend == GoogleAIBackend.VERTEX and not self.project_id:
            raise ValueError(
                "Vertex AI backend requires a project ID. "
                "Set GOOGLE_CLOUD_PROJECT environment variable."
            )

        # Initialize base class
        super().__init__("google_ai", api_key, **kwargs)

        self.access_token = None  # For Vertex AI
        self.token_expires_at = None


    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE, GenerationType.VIDEO],
            models=list(self.MODELS.keys()),
            max_resolution={"width": 2048, "height": 2048},  # Imagen 3
            formats=["png", "jpg", "mp4"],
            features=[
                "text_to_image",
                "text_to_video",
                "image_to_video",
                "aspect_ratio_control",
                "negative_prompt",
                "seed_control",
                "safety_filtering",
                "native_sound_generation",  # Veo 3
                "prompt_rewriting",  # Veo 3
                "speech_generation",  # Veo 3
            ],
            pricing=self.PRICING,
            supports_streaming=False,
            supports_batch=True,  # Up to 4 images
        )

    async def initialize(self):
        """Initialize the provider."""
        await self._ensure_session()

        # Authenticate if using Vertex AI
        if self.backend == GoogleAIBackend.VERTEX:
            await self._authenticate_vertex()


    async def _authenticate_vertex(self):
        """Authenticate with Vertex AI using service account."""
        # For Vertex AI, we need to get an access token
        # This is a simplified version - in production, use google-auth library
        if self.access_token and self.token_expires_at:
            if datetime.now().timestamp() < self.token_expires_at - 300:
                return

        # In a real implementation, use google.auth to get credentials
        # For now, assume the API key is an access token
        self.access_token = self.api_key
        self.token_expires_at = datetime.now().timestamp() + 3600

    def _get_base_url(self) -> str:
        """Get the appropriate base URL based on backend."""
        if self.backend == GoogleAIBackend.GEMINI:
            return self.GEMINI_BASE_URL
        else:
            return self.VERTEX_BASE_URL.format(location=self.location)

    def _estimate_generation_time(self, request: GenerationRequest) -> float:
        """Estimate generation time for a request."""
        if request.generation_type == GenerationType.VIDEO:
            # Video generation takes longer
            return 60.0  # Base 60 seconds for video
        else:
            # Image generation
            base_time = 5.0
            params = request.parameters or {}

            # More images take longer
            num_images = params.get("number_of_images", 1)
            base_time += (num_images - 1) * 2.0

            return base_time

    async def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate the cost of a generation request."""
        model_key = self.MODELS.get(request.model, request.model)
        base_cost = self.PRICING.get(model_key, 0.05)

        params = request.parameters or {}

        if request.generation_type == GenerationType.IMAGE:
            # Image generation cost
            num_images = params.get("number_of_images", 1)
            return base_cost * num_images
        else:
            # Video generation cost
            # Cost might vary by duration in the future
            return base_cost

    def _validate_aspect_ratio(self, aspect_ratio: str, model_type: str) -> bool:
        """Validate if aspect ratio is supported for model type."""
        supported = self.ASPECT_RATIOS.get(model_type, [])
        return aspect_ratio in supported

    async def _prepare_imagen_request(self, request: GenerationRequest) -> dict[str, Any]:
        """Prepare request body for Imagen API."""
        params = request.parameters or {}

        if self.backend == GoogleAIBackend.GEMINI:
            # Gemini API format
            body = {
                "prompt": request.prompt,
                "config": {
                    "number_of_images": params.get("number_of_images", 1),
                }
            }

            # Add optional parameters
            if params.get("negative_prompt"):
                body["config"]["negative_prompt"] = params["negative_prompt"]

            if params.get("aspect_ratio"):
                if self._validate_aspect_ratio(params["aspect_ratio"], "imagen"):
                    body["config"]["aspect_ratio"] = params["aspect_ratio"]

            if params.get("seed") is not None:
                body["config"]["seed"] = params["seed"]

        else:
            # Vertex AI format
            body = {
                "instances": [{
                    "prompt": request.prompt,
                }],
                "parameters": {
                    "sampleCount": params.get("number_of_images", 1),
                }
            }

            if params.get("negative_prompt"):
                body["parameters"]["negativePrompt"] = params["negative_prompt"]

            if params.get("aspect_ratio"):
                if self._validate_aspect_ratio(params["aspect_ratio"], "imagen"):
                    body["parameters"]["aspectRatio"] = params["aspect_ratio"]

            if params.get("seed") is not None:
                body["parameters"]["seed"] = params["seed"]

        return body

    async def _prepare_veo_request(self, request: GenerationRequest) -> dict[str, Any]:
        """Prepare request body for Veo API."""
        params = request.parameters or {}
        model_key = self.MODELS.get(request.model, request.model)
        is_veo3 = "veo-3" in model_key

        if self.backend == GoogleAIBackend.GEMINI:
            # Gemini API format
            body = {
                "config": {}
            }

            # Text or image prompt
            if request.prompt:
                body["text_prompt"] = request.prompt

            if request.reference_assets and len(request.reference_assets) > 0:
                # Image to video
                image_data = params.get("image_data")
                if image_data:
                    # In real implementation, upload image first
                    body["image_prompt"] = {"image_bytes": image_data}

            # Optional parameters
            if params.get("aspect_ratio"):
                if self._validate_aspect_ratio(params["aspect_ratio"], "veo"):
                    body["config"]["aspect_ratio"] = params["aspect_ratio"]

            if params.get("negative_prompt"):
                body["config"]["negative_prompt"] = params["negative_prompt"]

            if params.get("seed") is not None:
                body["config"]["seed"] = params["seed"]

            # Veo 3 specific parameters
            if is_veo3:
                body["config"]["enable_sound"] = params.get("enable_sound", False)
                body["config"]["enable_prompt_rewriting"] = params.get("enable_prompt_rewriting", True)
                body["config"]["number_of_videos"] = params.get("number_of_videos", 1)  # Max 2

        else:
            # Vertex AI format
            body = {
                "instances": [{}],
                "parameters": {}
            }

            if request.prompt:
                body["instances"][0]["prompt"] = request.prompt

            if request.reference_assets and len(request.reference_assets) > 0:
                # Image to video
                image_data = params.get("image_data")
                if image_data:
                    # In real implementation, handle image upload
                    body["instances"][0]["image"] = {"bytesBase64Encoded": image_data}

            # Parameters
            if params.get("aspect_ratio"):
                if self._validate_aspect_ratio(params["aspect_ratio"], "veo"):
                    body["parameters"]["aspectRatio"] = params["aspect_ratio"]

            if params.get("negative_prompt"):
                body["parameters"]["negativePrompt"] = params["negative_prompt"]

            if params.get("seed") is not None:
                body["parameters"]["seed"] = params["seed"]

            # Veo 3 specific parameters for Vertex AI
            if is_veo3:
                body["parameters"]["enableSound"] = params.get("enable_sound", False)
                body["parameters"]["enablePromptRewriting"] = params.get("enable_prompt_rewriting", True)
                body["parameters"]["sampleCount"] = params.get("number_of_videos", 1)  # Max 2

        return body

    async def _poll_long_running_operation(self, operation_name: str) -> dict[str, Any]:
        """Poll a long-running operation until completion."""
        await self._ensure_session()

        headers = self._get_headers()

        # For Vertex AI long-running operations
        max_attempts = 120  # 10 minutes with 5 second intervals
        for attempt in range(max_attempts):
            url = f"{self._get_base_url()}/v1/{operation_name}"

            async with self._session.get(url, headers=headers) as resp:
                await self._handle_response_errors(resp, "Operation status check")

                data = await resp.json()

                if data.get("done"):
                    if data.get("error"):
                        raise GenerationError(f"Operation failed: {data['error']}")
                    return data.get("response", {})

            # Wait before next poll
            await asyncio.sleep(5)

        raise GenerationError("Operation timed out after 10 minutes")

    def _get_headers(self) -> dict[str, str]:
        """Get appropriate headers based on backend."""
        if self.backend == GoogleAIBackend.GEMINI:
            return {
                "Content-Type": "application/json",
                "x-goog-api-key": self._get_api_key('GOOGLE_AI_API_KEY'),
            }
        else:
            # Vertex AI
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            }

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Perform the actual generation using Google AI."""
        session = await self._ensure_session()

        try:
            # Determine model and endpoint
            model_key = self.MODELS.get(request.model, request.model)
            is_video = request.generation_type == GenerationType.VIDEO

            # Prepare request based on model type
            if is_video:
                body = await self._prepare_veo_request(request)
                endpoint = self._get_veo_endpoint(model_key)
            else:
                body = await self._prepare_imagen_request(request)
                endpoint = self._get_imagen_endpoint(model_key)

            # Make API request
            headers = self._get_headers()
            url = f"{self._get_base_url()}{endpoint}"

            async with session.post(url, headers=headers, json=body) as resp:
                if resp.status == 202:
                    # This is OK - long-running operation
                    pass
                else:
                    await self._handle_response_errors(resp, "Generation")

                data = await resp.json()

                # Handle long-running operations (Vertex AI)
                if resp.status == 202 or "name" in data:
                    # This is a long-running operation
                    operation_name = data.get("name")
                    if operation_name:
                        result_data = await self._poll_long_running_operation(operation_name)
                    else:
                        result_data = data
                else:
                    result_data = data

            # Process results
            file_paths = []

            if is_video:
                # Video generation result
                videos = result_data.get("videos", [])
                for i, video in enumerate(videos):
                    video_data = video.get("video_bytes")
                    if video_data and request.output_path:
                        file_path = request.output_path / f"veo_{i}.mp4"
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        # In real implementation, decode base64 if needed
                        with open(file_path, "wb") as f:
                            f.write(video_data)
                        file_paths.append(file_path)
            else:
                # Image generation result
                if self.backend == GoogleAIBackend.GEMINI:
                    images = result_data.get("generated_images", [])
                    for i, image in enumerate(images):
                        image_data = image.get("image", {}).get("image_bytes")
                        if image_data and request.output_path:
                            file_path = request.output_path / f"imagen_{i}.png"
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            # In real implementation, decode base64 if needed
                            with open(file_path, "wb") as f:
                                f.write(image_data)
                            file_paths.append(file_path)
                else:
                    # Vertex AI format
                    predictions = result_data.get("predictions", [])
                    for i, pred in enumerate(predictions):
                        image_data = pred.get("bytesBase64Encoded")
                        if image_data and request.output_path:
                            file_path = request.output_path / f"imagen_{i}.png"
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            import base64
                            with open(file_path, "wb") as f:
                                f.write(base64.b64decode(image_data))
                            file_paths.append(file_path)

            # Calculate actual cost
            actual_cost = await self.estimate_cost(request)

            # Get generation metadata
            params = request.parameters or {}
            metadata = {
                "provider": "google_ai",
                "backend": self.backend.value,
                "model": model_key,
                "prompt": request.prompt,
                "generation_type": request.generation_type.value,
                "aspect_ratio": params.get("aspect_ratio"),
                "seed": params.get("seed"),
            }

            return GenerationResult(
                success=True,
                file_path=file_paths[0] if file_paths else None,
                cost=actual_cost,
                generation_time=0.0,  # Not reported by API
                metadata=metadata,
                provider="google_ai",
                model=request.model,
            )

        except Exception as e:
            logger.error(f"Google AI generation failed: {e!s}")
            return GenerationResult(
                success=False,
                error=str(e),
                provider="google_ai",
                model=request.model,
            )

    def _get_imagen_endpoint(self, model_key: str) -> str:
        """Get the appropriate endpoint for Imagen model."""
        if self.backend == GoogleAIBackend.GEMINI:
            return f"/v1beta/models/{model_key}:generateImages"
        else:
            # Vertex AI
            return f"/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_key}:predict"

    def _get_veo_endpoint(self, model_key: str) -> str:
        """Get the appropriate endpoint for Veo model."""
        if self.backend == GoogleAIBackend.GEMINI:
            return f"/v1beta/models/{model_key}:generateVideos"
        else:
            # Vertex AI
            return f"/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_key}:predictLongRunning"

    async def check_status(self) -> ProviderStatus:
        """Check provider availability status."""
        try:
            if not self._session:
                await self.initialize()

            # Try a simple API call
            headers = self._get_headers()

            if self.backend == GoogleAIBackend.GEMINI:
                # List models endpoint
                url = f"{self._get_base_url()}/v1beta/models"
            else:
                # Vertex AI health check
                url = f"{self._get_base_url()}/v1/projects/{self.project_id}/locations/{self.location}/models"

            async with self._session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    self._status = ProviderStatus.AVAILABLE
                    return ProviderStatus.AVAILABLE
                else:
                    self._status = ProviderStatus.DEGRADED
                    return ProviderStatus.DEGRADED

        except Exception as e:
            logger.error(f"Google AI status check failed: {e}")
            self._status = ProviderStatus.UNAVAILABLE
            return ProviderStatus.UNAVAILABLE
