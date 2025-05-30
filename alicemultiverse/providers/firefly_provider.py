"""Adobe Firefly API provider for AliceMultiverse.

Supports:
- Text to Image generation (Firefly Image Model 3)
- Generative Fill (inpainting)
- Generative Expand (outpainting)
- Object Composite
- Generate Similar
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import aiohttp

from .provider import Provider, GenerationError, AuthenticationError
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class FireflyProvider(Provider):
    """Adobe Firefly API provider implementation."""
    
    # Model mapping
    MODELS = {
        # Text to Image
        "firefly-v3": "firefly_v3",
        "firefly-image-3": "firefly_v3",
        "firefly": "firefly_v3",  # Default alias
        
        # Specialized models (use same base model with different endpoints)
        "firefly-fill": "firefly_v3",  # Generative Fill
        "firefly-expand": "firefly_v3",  # Generative Expand
        "firefly-composite": "firefly_v3",  # Object Composite
        "firefly-similar": "firefly_v3",  # Generate Similar
    }
    
    # Firefly API base URL
    BASE_URL = "https://firefly-api.adobe.io"
    
    # API endpoints
    ENDPOINTS = {
        "auth": "https://ims-na1.adobelogin.com/ims/token/v3",
        "generate": "/v3/images/generate",
        "fill": "/v3/images/fill",
        "expand": "/v3/images/expand",
        "composite": "/v3/images/composite",
        "similar": "/v3/images/similar",
        "upload": "/v2/storage/image",
        "status": "/v3/status/",
        "cancel": "/v3/cancel/",
    }
    
    # Pricing per generation
    PRICING = {
        "firefly_v3": 0.002,  # Estimated
    }
    
    # Style presets
    STYLE_PRESETS = [
        "art", "photo", "graphic", "b_and_w", "cool_colors", "warm_colors",
        "muted_colors", "vibrant_colors", "pastel_colors", "golden",
        "monochromatic", "dramatic", "photography", "film", "portrait",
        "landscape", "still_life", "double_exposure", "minimalist",
        "maximalist", "chaotic", "collage", "graffiti", "sketch",
        "watercolor", "oil_paint", "acrylic_paint", "digital_art",
        "3d", "isometric", "vector", "doodle", "line_art", "pop_art",
        "psychedelic", "cyberpunk", "steampunk", "synthwave", "fantasy",
        "sci_fi", "anime", "manga", "comic_book", "pixel_art",
    ]
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        """Initialize Firefly provider.
        
        Args:
            api_key: Adobe API client ID (can also be "client_id:client_secret")
            api_secret: Adobe API client secret (optional if included in api_key)
        """
        # Handle combined key format
        if api_key and ":" in api_key and not api_secret:
            client_id, client_secret = api_key.split(":", 1)
        else:
            client_id = api_key or os.getenv("ADOBE_CLIENT_ID")
            client_secret = api_secret or os.getenv("ADOBE_CLIENT_SECRET")
            
        if not client_id or not client_secret:
            raise ValueError(
                "Adobe Firefly requires both client ID and secret. "
                "Provide them as 'client_id:client_secret' or set "
                "ADOBE_CLIENT_ID and ADOBE_CLIENT_SECRET environment variables."
            )
        
        # Store as combined key for parent class
        super().__init__(api_key=f"{client_id}:{client_secret}")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        self._session: Optional[aiohttp.ClientSession] = None
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return "firefly"
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=list(self.MODELS.keys()),
            max_resolution={"width": 2048, "height": 2048},
            formats=["png", "jpg"],
            features=[
                "text_to_image",
                "inpainting",
                "outpainting",
                "style_reference",
                "structure_reference",
                "image_to_image",
            ],
            pricing=self.PRICING,
            supports_streaming=False,
            supports_batch=False,
        )
        
    async def initialize(self):
        """Initialize the provider and authenticate."""
        if not self._session:
            self._session = aiohttp.ClientSession()
        await self._authenticate()
        
    async def cleanup(self):
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None
            
    async def _authenticate(self):
        """Authenticate with Adobe IMS and get access token."""
        if self.access_token and self.token_expires_at:
            # Check if token is still valid (with 5 minute buffer)
            if datetime.now().timestamp() < self.token_expires_at - 300:
                return
                
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid,AdobeID,session,additional_info,read_organizations,firefly_api,ff_apis"
        }
        
        if not self._session:
            await self.initialize()
            
        async with self._session.post(self.ENDPOINTS["auth"], data=auth_data) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise AuthenticationError(f"Authentication failed: {error_text}")
                
            data = await resp.json()
            self.access_token = data["access_token"]
            # Token expires in seconds from now
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = datetime.now().timestamp() + expires_in
            
    def _estimate_generation_time(self, request: GenerationRequest) -> float:
        """Estimate generation time for a request."""
        # Base time for Firefly
        base_time = 10.0
        
        # Add time for larger images
        params = request.parameters or {}
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        size_factor = (width * height) / (1024 * 1024)
        size_time = size_factor * 5.0
        
        # Add time for complex operations
        if request.reference_assets:
            base_time += 5.0  # Image input operations take longer
            
        return base_time + size_time
        
    async def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate the cost of a generation request."""
        # Get model info
        model_key = self._get_model_key(request.model)
        base_cost = self.PRICING.get(model_key, 0.002)
        
        # Add cost for larger images
        params = request.parameters or {}
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        pixels = width * height
        if pixels > 1024 * 1024:
            base_cost *= 1.5  # 50% more for larger images
            
        # Add cost for complex operations
        if request.reference_assets:
            base_cost *= 1.2  # 20% more for image input
            
        num_images = params.get("num_images", 1)
        return base_cost * num_images
        
    def _get_model_key(self, model_name: str) -> str:
        """Get the internal model key from model name."""
        # Check direct match first
        if model_name in self.MODELS:
            return self.MODELS[model_name]
            
        # Check if it's already an internal key
        if model_name in self.PRICING:
            return model_name
            
        # Default to firefly v3
        return "firefly_v3"
        
    async def _upload_image(self, image_data: bytes) -> str:
        """Upload an image to Firefly storage and return the image ID."""
        await self._authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "x-api-key": self.client_id,
            "Content-Type": "image/png",  # Firefly accepts PNG
        }
        
        url = f"{self.BASE_URL}{self.ENDPOINTS['upload']}"
        async with self._session.post(url, headers=headers, data=image_data) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise GenerationError(f"Image upload failed: {error_text}")
                
            data = await resp.json()
            return data["images"][0]["id"]
            
    def _get_endpoint_for_model(self, model_name: str) -> str:
        """Get the appropriate endpoint based on model name."""
        if "fill" in model_name:
            return self.ENDPOINTS["fill"]
        elif "expand" in model_name:
            return self.ENDPOINTS["expand"]
        elif "composite" in model_name:
            return self.ENDPOINTS["composite"]
        elif "similar" in model_name:
            return self.ENDPOINTS["similar"]
        else:
            return self.ENDPOINTS["generate"]
            
    async def _prepare_request_body(self, request: GenerationRequest) -> Dict[str, Any]:
        """Prepare the request body for Firefly API."""
        params = request.parameters or {}
        
        body = {
            "numVariations": params.get("num_images", 1),
            "size": {
                "width": params.get("width", 1024),
                "height": params.get("height", 1024),
            }
        }
        
        # Add prompt for text-to-image
        if request.prompt and not request.reference_assets:
            body["prompt"] = request.prompt
            
        # Add negative prompt if provided
        if params.get("negative_prompt"):
            body["negativePrompt"] = params["negative_prompt"]
            
        # Add seed for reproducibility
        if params.get("seed") is not None:
            body["seeds"] = [params["seed"]]
            
        # Add style preset
        style_preset = params.get("style_preset")
        if style_preset and style_preset in self.STYLE_PRESETS:
            body["style"] = {"presets": [style_preset]}
            
        # Add style reference image
        style_reference = params.get("style_reference")
        if style_reference:
            # Upload style reference image
            style_id = await self._upload_image(style_reference)
            if "style" not in body:
                body["style"] = {}
            body["style"]["source"] = style_id
            body["style"]["strength"] = params.get("style_strength", 50)
            
        # Add structure reference
        structure_reference = params.get("structure_reference")
        if structure_reference:
            # Upload structure reference image
            structure_id = await self._upload_image(structure_reference)
            body["structure"] = {
                "source": structure_id,
                "strength": params.get("structure_strength", 50)
            }
            
        # Handle image input for fill/expand/composite
        if request.reference_assets and len(request.reference_assets) > 0:
            # Get image data from first reference
            image_data = params.get("image_data")
            if image_data:
                # Upload input image
                image_id = await self._upload_image(image_data)
                
                endpoint = self._get_endpoint_for_model(request.model)
                if "fill" in endpoint:
                    body["image"] = {"source": image_id}
                    mask_data = params.get("mask_data")
                    if mask_data:
                        mask_id = await self._upload_image(mask_data)
                        body["mask"] = {"source": mask_id}
                    if request.prompt:
                        body["prompt"] = request.prompt
                        
                elif "expand" in endpoint:
                    body["image"] = {"source": image_id}
                    # Add expand parameters
                    body["placement"] = params.get("placement", {
                        "inset": {"left": 0, "top": 0, "right": 0, "bottom": 0}
                    })
                    
                elif "composite" in endpoint:
                    body["image"] = {"source": image_id}
                    mask_data = params.get("mask_data")
                    if mask_data:
                        mask_id = await self._upload_image(mask_data)
                        body["mask"] = {"source": mask_id}
                        
                elif "similar" in endpoint:
                    body["source"] = image_id
                
        # Add content class if specified
        content_class = params.get("content_class")
        if content_class:
            body["contentClass"] = content_class
            
        # Add locale for region-specific content
        locale = params.get("locale", "en-US")
        body["promptBiasingLocaleCode"] = locale
        
        # Add tileable option
        if params.get("tileable", False):
            body["tileable"] = True
            
        return body
        
    async def _poll_async_job(self, status_url: str, cancel_url: str) -> Dict[str, Any]:
        """Poll an async job until completion."""
        await self._authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "x-api-key": self.client_id,
        }
        
        max_attempts = 60  # 5 minutes with 5 second intervals
        for attempt in range(max_attempts):
            async with self._session.get(status_url, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise GenerationError(f"Status check failed: {error_text}")
                    
                data = await resp.json()
                status = data.get("status")
                
                if status == "succeeded":
                    return data
                elif status == "failed":
                    error = data.get("error", {}).get("message", "Unknown error")
                    raise GenerationError(f"Generation failed: {error}")
                elif status == "cancelled":
                    raise GenerationError("Generation was cancelled")
                    
            # Wait before next poll
            await asyncio.sleep(5)
            
        # Timeout - try to cancel the job
        try:
            async with self._session.post(cancel_url, headers=headers) as resp:
                pass
        except:
            pass
            
        raise GenerationError("Generation timed out after 5 minutes")
        
    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Perform the actual generation using Firefly API."""
        if not self._session:
            await self.initialize()
            
        try:
            # Prepare request body
            body = await self._prepare_request_body(request)
            
            # Get the appropriate endpoint
            endpoint = self._get_endpoint_for_model(request.model)
            
            # Make the API request
            await self._authenticate()
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "x-api-key": self.client_id,
                "Content-Type": "application/json",
            }
            
            # Add custom model header if specified
            params = request.parameters or {}
            custom_model = params.get("custom_model")
            if custom_model:
                headers["x-model-version"] = custom_model
                
            url = f"{self.BASE_URL}{endpoint}"
            async with self._session.post(url, headers=headers, json=body) as resp:
                if resp.status not in [200, 202]:
                    error_text = await resp.text()
                    raise GenerationError(f"Generation failed: {error_text}")
                    
                data = await resp.json()
                
                # Check if this is an async job
                if resp.status == 202:
                    # Poll for completion
                    status_url = data.get("statusUrl")
                    cancel_url = data.get("cancelUrl")
                    if not status_url:
                        raise GenerationError("No status URL returned for async job")
                        
                    # Poll until completion
                    result_data = await self._poll_async_job(status_url, cancel_url)
                    outputs = result_data.get("outputs", [])
                else:
                    outputs = data.get("outputs", [])
                    
            # Process outputs
            file_paths = []
            for i, output in enumerate(outputs):
                image_url = output.get("image", {}).get("url")
                if image_url:
                    # Download the image
                    async with self._session.get(image_url) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            # Save to output path if specified
                            if request.output_path:
                                file_path = request.output_path / f"firefly_{i}.png"
                                file_path.parent.mkdir(parents=True, exist_ok=True)
                                with open(file_path, "wb") as f:
                                    f.write(image_data)
                                file_paths.append(file_path)
                            
            # Calculate actual cost
            actual_cost = await self.estimate_cost(request)
            
            # Get generation metadata
            metadata = {
                "provider": "firefly",
                "model": request.model,
                "width": params.get("width", 1024),
                "height": params.get("height", 1024),
                "prompt": request.prompt,
                "seed": outputs[0].get("seed") if outputs else None,
                "content_class": body.get("contentClass"),
                "style_preset": params.get("style_preset"),
            }
            
            return GenerationResult(
                success=True,
                file_path=file_paths[0] if file_paths else None,
                cost=actual_cost,
                generation_time=0.0,  # Firefly doesn't report this
                metadata=metadata,
                provider="firefly",
                model=request.model,
            )
            
        except Exception as e:
            logger.error(f"Firefly generation failed: {str(e)}")
            return GenerationResult(
                success=False,
                error=str(e),
                provider="firefly",
                model=request.model,
            )
    
    async def check_status(self) -> ProviderStatus:
        """Check provider availability status."""
        try:
            # Try to authenticate
            if not self._session:
                await self.initialize()
            await self._authenticate()
            self._status = ProviderStatus.AVAILABLE
            return ProviderStatus.AVAILABLE
        except Exception as e:
            logger.error(f"Firefly status check failed: {e}")
            self._status = ProviderStatus.UNAVAILABLE
            return ProviderStatus.UNAVAILABLE