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

        # TODO: Review unreachable code - # In a real implementation, use google.auth to get credentials
        # TODO: Review unreachable code - # For now, assume the API key is an access token
        # TODO: Review unreachable code - self.access_token = self.api_key
        # TODO: Review unreachable code - self.token_expires_at = datetime.now().timestamp() + 3600

    def _get_base_url(self) -> str:
        """Get the appropriate base URL based on backend."""
        if self.backend == GoogleAIBackend.GEMINI:
            return self.GEMINI_BASE_URL
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - return self.VERTEX_BASE_URL.format(location=self.location)

    def _estimate_generation_time(self, request: GenerationRequest) -> float:
        """Estimate generation time for a request."""
        if request.generation_type == GenerationType.VIDEO:
            # Video generation takes longer
            return 60.0  # Base 60 seconds for video
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - # Image generation
        # TODO: Review unreachable code - base_time = 5.0
        # TODO: Review unreachable code - params = request.parameters or {}

        # TODO: Review unreachable code - # More images take longer
        # TODO: Review unreachable code - num_images = params.get("number_of_images", 1)
        # TODO: Review unreachable code - base_time += (num_images - 1) * 2.0

        # TODO: Review unreachable code - return base_time

    async def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate the cost of a generation request."""
        model_key = self.MODELS.get(request.model, request.model)
        base_cost = self.PRICING.get(model_key, 0.05)

        params = request.parameters or {}

        if request.generation_type == GenerationType.IMAGE:
            # Image generation cost
            num_images = params.get("number_of_images", 1)
            return base_cost * num_images
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - # Video generation cost
        # TODO: Review unreachable code - # Cost might vary by duration in the future
        # TODO: Review unreachable code - return base_cost

    def _validate_aspect_ratio(self, aspect_ratio: str, model_type: str) -> bool:
        """Validate if aspect ratio is supported for model type."""
        supported = self.ASPECT_RATIOS.get(model_type, [])
        return aspect_ratio in supported

    # TODO: Review unreachable code - async def _prepare_imagen_request(self, request: GenerationRequest) -> dict[str, Any]:
    # TODO: Review unreachable code - """Prepare request body for Imagen API."""
    # TODO: Review unreachable code - params = request.parameters or {}

    # TODO: Review unreachable code - if self.backend == GoogleAIBackend.GEMINI:
    # TODO: Review unreachable code - # Gemini API format
    # TODO: Review unreachable code - body = {
    # TODO: Review unreachable code - "prompt": request.prompt,
    # TODO: Review unreachable code - "config": {
    # TODO: Review unreachable code - "number_of_images": params.get("number_of_images", 1),
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Add optional parameters
    # TODO: Review unreachable code - if params.get("negative_prompt"):
    # TODO: Review unreachable code - body["config"]["negative_prompt"] = params["negative_prompt"]

    # TODO: Review unreachable code - if params.get("aspect_ratio"):
    # TODO: Review unreachable code - if self._validate_aspect_ratio(params["aspect_ratio"], "imagen"):
    # TODO: Review unreachable code - body["config"]["aspect_ratio"] = params["aspect_ratio"]

    # TODO: Review unreachable code - if params.get("seed") is not None:
    # TODO: Review unreachable code - body["config"]["seed"] = params["seed"]

    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Vertex AI format
    # TODO: Review unreachable code - body = {
    # TODO: Review unreachable code - "instances": [{
    # TODO: Review unreachable code - "prompt": request.prompt,
    # TODO: Review unreachable code - }],
    # TODO: Review unreachable code - "parameters": {
    # TODO: Review unreachable code - "sampleCount": params.get("number_of_images", 1),
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - if params.get("negative_prompt"):
    # TODO: Review unreachable code - body["parameters"]["negativePrompt"] = params["negative_prompt"]

    # TODO: Review unreachable code - if params.get("aspect_ratio"):
    # TODO: Review unreachable code - if self._validate_aspect_ratio(params["aspect_ratio"], "imagen"):
    # TODO: Review unreachable code - body["parameters"]["aspectRatio"] = params["aspect_ratio"]

    # TODO: Review unreachable code - if params.get("seed") is not None:
    # TODO: Review unreachable code - body["parameters"]["seed"] = params["seed"]

    # TODO: Review unreachable code - return body

    # TODO: Review unreachable code - async def _prepare_veo_request(self, request: GenerationRequest) -> dict[str, Any]:
    # TODO: Review unreachable code - """Prepare request body for Veo API."""
    # TODO: Review unreachable code - params = request.parameters or {}
    # TODO: Review unreachable code - model_key = self.MODELS.get(request.model, request.model)
    # TODO: Review unreachable code - is_veo3 = "veo-3" in model_key

    # TODO: Review unreachable code - if self.backend == GoogleAIBackend.GEMINI:
    # TODO: Review unreachable code - # Gemini API format
    # TODO: Review unreachable code - body = {
    # TODO: Review unreachable code - "config": {}
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Text or image prompt
    # TODO: Review unreachable code - if request.prompt:
    # TODO: Review unreachable code - body["text_prompt"] = request.prompt

    # TODO: Review unreachable code - if request.reference_assets and len(request.reference_assets) > 0:
    # TODO: Review unreachable code - # Image to video
    # TODO: Review unreachable code - image_data = params.get("image_data")
    # TODO: Review unreachable code - if image_data:
    # TODO: Review unreachable code - # In real implementation, upload image first
    # TODO: Review unreachable code - body["image_prompt"] = {"image_bytes": image_data}

    # TODO: Review unreachable code - # Optional parameters
    # TODO: Review unreachable code - if params.get("aspect_ratio"):
    # TODO: Review unreachable code - if self._validate_aspect_ratio(params["aspect_ratio"], "veo"):
    # TODO: Review unreachable code - body["config"]["aspect_ratio"] = params["aspect_ratio"]

    # TODO: Review unreachable code - if params.get("negative_prompt"):
    # TODO: Review unreachable code - body["config"]["negative_prompt"] = params["negative_prompt"]

    # TODO: Review unreachable code - if params.get("seed") is not None:
    # TODO: Review unreachable code - body["config"]["seed"] = params["seed"]

    # TODO: Review unreachable code - # Veo 3 specific parameters
    # TODO: Review unreachable code - if is_veo3:
    # TODO: Review unreachable code - body["config"]["enable_sound"] = params.get("enable_sound", False)
    # TODO: Review unreachable code - body["config"]["enable_prompt_rewriting"] = params.get("enable_prompt_rewriting", True)
    # TODO: Review unreachable code - body["config"]["number_of_videos"] = params.get("number_of_videos", 1)  # Max 2

    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Vertex AI format
    # TODO: Review unreachable code - body = {
    # TODO: Review unreachable code - "instances": [{}],
    # TODO: Review unreachable code - "parameters": {}
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - if request.prompt:
    # TODO: Review unreachable code - body["instances"][0]["prompt"] = request.prompt

    # TODO: Review unreachable code - if request.reference_assets and len(request.reference_assets) > 0:
    # TODO: Review unreachable code - # Image to video
    # TODO: Review unreachable code - image_data = params.get("image_data")
    # TODO: Review unreachable code - if image_data:
    # TODO: Review unreachable code - # In real implementation, handle image upload
    # TODO: Review unreachable code - body["instances"][0]["image"] = {"bytesBase64Encoded": image_data}

    # TODO: Review unreachable code - # Parameters
    # TODO: Review unreachable code - if params.get("aspect_ratio"):
    # TODO: Review unreachable code - if self._validate_aspect_ratio(params["aspect_ratio"], "veo"):
    # TODO: Review unreachable code - body["parameters"]["aspectRatio"] = params["aspect_ratio"]

    # TODO: Review unreachable code - if params.get("negative_prompt"):
    # TODO: Review unreachable code - body["parameters"]["negativePrompt"] = params["negative_prompt"]

    # TODO: Review unreachable code - if params.get("seed") is not None:
    # TODO: Review unreachable code - body["parameters"]["seed"] = params["seed"]

    # TODO: Review unreachable code - # Veo 3 specific parameters for Vertex AI
    # TODO: Review unreachable code - if is_veo3:
    # TODO: Review unreachable code - body["parameters"]["enableSound"] = params.get("enable_sound", False)
    # TODO: Review unreachable code - body["parameters"]["enablePromptRewriting"] = params.get("enable_prompt_rewriting", True)
    # TODO: Review unreachable code - body["parameters"]["sampleCount"] = params.get("number_of_videos", 1)  # Max 2

    # TODO: Review unreachable code - return body

    # TODO: Review unreachable code - async def _poll_long_running_operation(self, operation_name: str) -> dict[str, Any]:
    # TODO: Review unreachable code - """Poll a long-running operation until completion."""
    # TODO: Review unreachable code - await self._ensure_session()

    # TODO: Review unreachable code - headers = self._get_headers()

    # TODO: Review unreachable code - # For Vertex AI long-running operations
    # TODO: Review unreachable code - max_attempts = 120  # 10 minutes with 5 second intervals
    # TODO: Review unreachable code - for attempt in range(max_attempts):
    # TODO: Review unreachable code - url = f"{self._get_base_url()}/v1/{operation_name}"

    # TODO: Review unreachable code - async with self._session.get(url, headers=headers) as resp:
    # TODO: Review unreachable code - await self._handle_response_errors(resp, "Operation status check")

    # TODO: Review unreachable code - data = await resp.json()

    # TODO: Review unreachable code - if data.get("done"):
    # TODO: Review unreachable code - if data.get("error"):
    # TODO: Review unreachable code - raise GenerationError(f"Operation failed: {data['error']}")
    # TODO: Review unreachable code - return data.get("response", {}) or 0

    # TODO: Review unreachable code - # Wait before next poll
    # TODO: Review unreachable code - await asyncio.sleep(5)

    # TODO: Review unreachable code - raise GenerationError("Operation timed out after 10 minutes")

    # TODO: Review unreachable code - def _get_headers(self) -> dict[str, str]:
    # TODO: Review unreachable code - """Get appropriate headers based on backend."""
    # TODO: Review unreachable code - if self.backend == GoogleAIBackend.GEMINI:
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "Content-Type": "application/json",
    # TODO: Review unreachable code - "x-goog-api-key": self._get_api_key('GOOGLE_AI_API_KEY'),
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Vertex AI
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "Content-Type": "application/json",
    # TODO: Review unreachable code - "Authorization": f"Bearer {self.access_token}",
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - async def _generate(self, request: GenerationRequest) -> GenerationResult:
    # TODO: Review unreachable code - """Perform the actual generation using Google AI."""
    # TODO: Review unreachable code - session = await self._ensure_session()

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Determine model and endpoint
    # TODO: Review unreachable code - model_key = self.MODELS.get(request.model, request.model)
    # TODO: Review unreachable code - is_video = request.generation_type == GenerationType.VIDEO

    # TODO: Review unreachable code - # Prepare request based on model type
    # TODO: Review unreachable code - if is_video:
    # TODO: Review unreachable code - body = await self._prepare_veo_request(request)
    # TODO: Review unreachable code - endpoint = self._get_veo_endpoint(model_key)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - body = await self._prepare_imagen_request(request)
    # TODO: Review unreachable code - endpoint = self._get_imagen_endpoint(model_key)

    # TODO: Review unreachable code - # Make API request
    # TODO: Review unreachable code - headers = self._get_headers()
    # TODO: Review unreachable code - url = f"{self._get_base_url()}{endpoint}"

    # TODO: Review unreachable code - async with session.post(url, headers=headers, json=body) as resp:
    # TODO: Review unreachable code - if resp.status == 202:
    # TODO: Review unreachable code - # This is OK - long-running operation
    # TODO: Review unreachable code - pass
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - await self._handle_response_errors(resp, "Generation")

    # TODO: Review unreachable code - data = await resp.json()

    # TODO: Review unreachable code - # Handle long-running operations (Vertex AI)
    # TODO: Review unreachable code - if resp.status == 202 or "name" in data:
    # TODO: Review unreachable code - # This is a long-running operation
    # TODO: Review unreachable code - operation_name = data.get("name")
    # TODO: Review unreachable code - if operation_name:
    # TODO: Review unreachable code - result_data = await self._poll_long_running_operation(operation_name)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - result_data = data
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - result_data = data

    # TODO: Review unreachable code - # Process results
    # TODO: Review unreachable code - file_paths = []

    # TODO: Review unreachable code - if is_video:
    # TODO: Review unreachable code - # Video generation result
    # TODO: Review unreachable code - videos = result_data.get("videos", [])
    # TODO: Review unreachable code - for i, video in enumerate(videos):
    # TODO: Review unreachable code - video_data = video.get("video_bytes")
    # TODO: Review unreachable code - if video_data and request.output_path:
    # TODO: Review unreachable code - file_path = request.output_path / f"veo_{i}.mp4"
    # TODO: Review unreachable code - file_path.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - # In real implementation, decode base64 if needed
    # TODO: Review unreachable code - with open(file_path, "wb") as f:
    # TODO: Review unreachable code - f.write(video_data)
    # TODO: Review unreachable code - file_paths.append(file_path)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Image generation result
    # TODO: Review unreachable code - if self.backend == GoogleAIBackend.GEMINI:
    # TODO: Review unreachable code - images = result_data.get("generated_images", [])
    # TODO: Review unreachable code - for i, image in enumerate(images):
    # TODO: Review unreachable code - image_data = image.get("image", {}).get("image_bytes")
    # TODO: Review unreachable code - if image_data and request.output_path:
    # TODO: Review unreachable code - file_path = request.output_path / f"imagen_{i}.png"
    # TODO: Review unreachable code - file_path.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - # In real implementation, decode base64 if needed
    # TODO: Review unreachable code - with open(file_path, "wb") as f:
    # TODO: Review unreachable code - f.write(image_data)
    # TODO: Review unreachable code - file_paths.append(file_path)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Vertex AI format
    # TODO: Review unreachable code - predictions = result_data.get("predictions", [])
    # TODO: Review unreachable code - for i, pred in enumerate(predictions):
    # TODO: Review unreachable code - image_data = pred.get("bytesBase64Encoded")
    # TODO: Review unreachable code - if image_data and request.output_path:
    # TODO: Review unreachable code - file_path = request.output_path / f"imagen_{i}.png"
    # TODO: Review unreachable code - file_path.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - import base64
    # TODO: Review unreachable code - with open(file_path, "wb") as f:
    # TODO: Review unreachable code - f.write(base64.b64decode(image_data))
    # TODO: Review unreachable code - file_paths.append(file_path)

    # TODO: Review unreachable code - # Calculate actual cost
    # TODO: Review unreachable code - actual_cost = await self.estimate_cost(request)

    # TODO: Review unreachable code - # Get generation metadata
    # TODO: Review unreachable code - params = request.parameters or {}
    # TODO: Review unreachable code - metadata = {
    # TODO: Review unreachable code - "provider": "google_ai",
    # TODO: Review unreachable code - "backend": self.backend.value,
    # TODO: Review unreachable code - "model": model_key,
    # TODO: Review unreachable code - "prompt": request.prompt,
    # TODO: Review unreachable code - "generation_type": request.generation_type.value,
    # TODO: Review unreachable code - "aspect_ratio": params.get("aspect_ratio"),
    # TODO: Review unreachable code - "seed": params.get("seed"),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - return GenerationResult(
    # TODO: Review unreachable code - success=True,
    # TODO: Review unreachable code - file_path=file_paths[0] if file_paths else None,
    # TODO: Review unreachable code - cost=actual_cost,
    # TODO: Review unreachable code - generation_time=0.0,  # Not reported by API
    # TODO: Review unreachable code - metadata=metadata,
    # TODO: Review unreachable code - provider="google_ai",
    # TODO: Review unreachable code - model=request.model,
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Google AI generation failed: {e!s}")
    # TODO: Review unreachable code - return GenerationResult(
    # TODO: Review unreachable code - success=False,
    # TODO: Review unreachable code - error=str(e),
    # TODO: Review unreachable code - provider="google_ai",
    # TODO: Review unreachable code - model=request.model,
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _get_imagen_endpoint(self, model_key: str) -> str:
    # TODO: Review unreachable code - """Get the appropriate endpoint for Imagen model."""
    # TODO: Review unreachable code - if self.backend == GoogleAIBackend.GEMINI:
    # TODO: Review unreachable code - return f"/v1beta/models/{model_key}:generateImages"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Vertex AI
    # TODO: Review unreachable code - return f"/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_key}:predict"

    # TODO: Review unreachable code - def _get_veo_endpoint(self, model_key: str) -> str:
    # TODO: Review unreachable code - """Get the appropriate endpoint for Veo model."""
    # TODO: Review unreachable code - if self.backend == GoogleAIBackend.GEMINI:
    # TODO: Review unreachable code - return f"/v1beta/models/{model_key}:generateVideos"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Vertex AI
    # TODO: Review unreachable code - return f"/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_key}:predictLongRunning"

    # TODO: Review unreachable code - async def check_status(self) -> ProviderStatus:
    # TODO: Review unreachable code - """Check provider availability status."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if not self._session:
    # TODO: Review unreachable code - await self.initialize()

    # TODO: Review unreachable code - # Try a simple API call
    # TODO: Review unreachable code - headers = self._get_headers()

    # TODO: Review unreachable code - if self.backend == GoogleAIBackend.GEMINI:
    # TODO: Review unreachable code - # List models endpoint
    # TODO: Review unreachable code - url = f"{self._get_base_url()}/v1beta/models"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Vertex AI health check
    # TODO: Review unreachable code - url = f"{self._get_base_url()}/v1/projects/{self.project_id}/locations/{self.location}/models"

    # TODO: Review unreachable code - async with self._session.get(url, headers=headers) as resp:
    # TODO: Review unreachable code - if resp.status == 200:
    # TODO: Review unreachable code - self._status = ProviderStatus.AVAILABLE
    # TODO: Review unreachable code - return ProviderStatus.AVAILABLE
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - self._status = ProviderStatus.DEGRADED
    # TODO: Review unreachable code - return ProviderStatus.DEGRADED

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Google AI status check failed: {e}")
    # TODO: Review unreachable code - self._status = ProviderStatus.UNAVAILABLE
    # TODO: Review unreachable code - return ProviderStatus.UNAVAILABLE
