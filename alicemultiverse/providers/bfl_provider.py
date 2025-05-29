"""Black Forest Labs (BFL) API provider for FLUX models."""

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


class BFLProvider(Provider):
    """Provider for Black Forest Labs API (bfl.ai) integration."""

    BASE_URL = "https://api.bfl.ai/v1"
    
    # Model endpoints
    MODELS = {
        # FLUX.1 models
        "flux-pro": "flux-pro-1.1",
        "flux-dev": "flux-dev",
        "flux-schnell": "flux-schnell",
        
        # FLUX.1 Kontext models
        "flux-kontext-pro": "flux-pro-kontext",
        "flux-kontext-max": "flux-pro-kontext-max",
        "flux-kontext-dev": "flux-dev-kontext",  # Coming soon
        
        # Fill enhancement
        "flux-fill-pro": "flux-pro-fill",
        "flux-fill-dev": "flux-dev-fill",
        
        # Canny control
        "flux-canny-pro": "flux-pro-canny",
        "flux-canny-dev": "flux-dev-canny",
        
        # Depth control
        "flux-depth-pro": "flux-pro-depth",
        "flux-depth-dev": "flux-dev-depth",
    }
    
    # Pricing per generation (based on BFL pricing)
    PRICING = {
        "flux-pro": 0.055,
        "flux-dev": 0.025,
        "flux-schnell": 0.003,
        "flux-kontext-pro": 0.06,
        "flux-kontext-max": 0.08,
        "flux-kontext-dev": 0.03,
        "flux-fill-pro": 0.055,
        "flux-fill-dev": 0.025,
        "flux-canny-pro": 0.055,
        "flux-canny-dev": 0.025,
        "flux-depth-pro": 0.055,
        "flux-depth-dev": 0.025,
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize BFL provider.
        
        Args:
            api_key: BFL API key (or from BFL_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("BFL_API_KEY")
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "bfl"

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=list(self.MODELS.keys()),
            max_resolution={"width": 1440, "height": 1440},
            formats=["png", "jpg", "webp"],
            features=[
                "text_to_image",
                "image_to_image",
                "inpainting",
                "outpainting",
                "canny_control",
                "depth_control",
                "iterative_editing",
                "style_reference",
            ],
            rate_limits={
                "requests_per_minute": 100,
                "concurrent_requests": 10
            },
            pricing=self.PRICING
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            headers = {
                "Content-Type": "application/json"
            }
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def check_status(self) -> ProviderStatus:
        """Check BFL API status."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.BASE_URL}/health") as response:
                if response.status == 200:
                    return ProviderStatus.AVAILABLE
                elif response.status == 401:
                    return ProviderStatus.AUTHENTICATION_ERROR
                else:
                    return ProviderStatus.UNAVAILABLE
        except Exception as e:
            logger.error(f"Error checking BFL status: {e}")
            return ProviderStatus.ERROR

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content using BFL API."""
        if not self.api_key:
            raise AuthenticationError("BFL API key not configured")
            
        # Get model endpoint
        model = request.model or "flux-pro"
        model_id = self.MODELS.get(model)
        if not model_id:
            raise ValueError(f"Unknown model: {model}")
            
        # Build API parameters
        api_params = self._build_api_params(request, model)
            
        # Make API request
        result_data = await self._call_api(model_id, api_params)
        
        # Poll for completion if needed
        if result_data.get("status") == "pending":
            result_data = await self._poll_for_completion(result_data["id"])
        
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
                "bfl_request_id": result_data.get("id"),
            }
        )

    def _build_api_params(self, request: GenerationRequest, model: str) -> Dict[str, Any]:
        """Build API parameters for BFL request."""
        params = {
            "prompt": request.prompt,
            "width": request.parameters.get("width", 1024),
            "height": request.parameters.get("height", 1024),
            "steps": request.parameters.get("num_inference_steps", 28),
            "guidance": request.parameters.get("guidance_scale", 3.5),
            "output_format": request.parameters.get("output_format", "png"),
        }
        
        # Add custom parameters
        if request.parameters:
            # Map common parameter names
            param_mapping = {
                "num_inference_steps": "steps",
                "guidance_scale": "guidance",
            }
            for key, value in request.parameters.items():
                mapped_key = param_mapping.get(key, key)
                params[mapped_key] = value
        
        # Handle Kontext models with reference images
        if "kontext" in model and request.reference_assets:
            params["image"] = request.reference_assets[0]
            
        # Handle fill models with mask
        if "fill" in model and len(request.reference_assets) > 1:
            params["image"] = request.reference_assets[0]
            params["mask"] = request.reference_assets[1]
            
        # Handle control models
        if "canny" in model or "depth" in model:
            if request.reference_assets:
                params["control_image"] = request.reference_assets[0]
                params["control_strength"] = request.parameters.get("control_strength", 0.7)
        
        return params

    async def _call_api(self, model_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to BFL."""
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/image"
        data = {
            "model": model_id,
            **params
        }
        
        try:
            async with session.post(url, json=data) as response:
                response_data = await response.json()
                
                if response.status == 429:
                    raise RateLimitError("BFL rate limit exceeded")
                elif response.status == 401:
                    raise AuthenticationError("Invalid BFL API key")
                elif response.status != 200:
                    error_msg = response_data.get("error", "Unknown error")
                    raise GenerationError(f"BFL API error: {error_msg}")
                    
                return response_data
                
        except aiohttp.ClientError as e:
            raise GenerationError(f"Network error: {str(e)}")

    async def _poll_for_completion(self, request_id: str, max_attempts: int = 60) -> Dict[str, Any]:
        """Poll for request completion."""
        session = await self._get_session()
        url = f"{self.BASE_URL}/get_result"
        
        for attempt in range(max_attempts):
            try:
                async with session.get(url, params={"id": request_id}) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "completed":
                            return data
                        elif data.get("status") == "failed":
                            raise GenerationError(f"Generation failed: {data.get('error')}")
                    
                # Wait before next poll
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error polling for result: {e}")
                
        raise GenerationError("Timeout waiting for generation to complete")

    async def _download_result(self, request: GenerationRequest, result_data: Dict[str, Any]) -> Path:
        """Download generated content."""
        # Get image URL from result
        image_url = result_data.get("sample")
        if not image_url:
            raise GenerationError("No image URL in response")
            
        # Determine file extension
        parsed_url = urlparse(image_url)
        ext = Path(parsed_url.path).suffix or ".png"
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bfl_{request.prompt[:30].replace(' ', '_')}_{timestamp}{ext}"
        
        # Download file
        output_path = request.output_path or Path.cwd() / filename
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