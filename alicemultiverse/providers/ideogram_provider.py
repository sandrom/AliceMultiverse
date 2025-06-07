"""Ideogram API provider for AliceMultiverse.

Supports:
- Text to image generation with superior text rendering
- Multiple model versions (V2, V2 Turbo, V3)
- Various styles (Realistic, Design, 3D, Anime)
- Advanced typography and logo generation
"""

import logging
import os
from typing import Any, Dict, Optional
from pathlib import Path
import aiohttp
from enum import Enum

from .provider import Provider, GenerationError, AuthenticationError
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class IdeogramModel(Enum):
    """Available Ideogram models."""
    V2 = "V_2"
    V2_TURBO = "V_2_TURBO"
    V3 = "V_3"


class IdeogramStyle(Enum):
    """Available style types."""
    REALISTIC = "REALISTIC"
    DESIGN = "DESIGN"
    RENDER_3D = "RENDER_3D"
    ANIME = "ANIME"
    AUTO = "AUTO"


class IdeogramAspectRatio(Enum):
    """Available aspect ratios."""
    ASPECT_1_1 = "ASPECT_1_1"
    ASPECT_16_9 = "ASPECT_16_9"
    ASPECT_9_16 = "ASPECT_9_16"
    ASPECT_4_3 = "ASPECT_4_3"
    ASPECT_3_4 = "ASPECT_3_4"
    ASPECT_16_10 = "ASPECT_16_10"
    ASPECT_10_16 = "ASPECT_10_16"
    ASPECT_3_2 = "ASPECT_3_2"
    ASPECT_2_3 = "ASPECT_2_3"
    ASPECT_3_1 = "ASPECT_3_1"
    ASPECT_1_3 = "ASPECT_1_3"


class IdeogramProvider(Provider):
    """Ideogram API provider implementation."""
    
    # Model mapping
    MODELS = {
        # Standard models
        "ideogram-v2": IdeogramModel.V2.value,
        "ideogram-v2-turbo": IdeogramModel.V2_TURBO.value,
        "ideogram-v3": IdeogramModel.V3.value,
        
        # Aliases
        "ideogram": IdeogramModel.V3.value,  # Default to latest
        "v2": IdeogramModel.V2.value,
        "v2-turbo": IdeogramModel.V2_TURBO.value,
        "turbo": IdeogramModel.V2_TURBO.value,
        "v3": IdeogramModel.V3.value,
    }
    
    # API endpoints
    BASE_URL = "https://api.ideogram.ai"
    ENDPOINTS = {
        "generate": "/generate",
        "generate_v3": "/generate/v3",
        "upscale": "/upscale",
        "remix": "/remix",
        "describe": "/describe",
    }
    
    # Pricing per generation
    PRICING = {
        IdeogramModel.V2.value: 0.08,  # $0.08 per image
        IdeogramModel.V2_TURBO.value: 0.05,  # $0.05 per image (faster)
        IdeogramModel.V3.value: 0.10,  # Estimated for V3
    }
    
    # Style to aspect ratio recommendations
    STYLE_ASPECT_RECOMMENDATIONS = {
        IdeogramStyle.DESIGN: [IdeogramAspectRatio.ASPECT_1_1, IdeogramAspectRatio.ASPECT_16_9],
        IdeogramStyle.RENDER_3D: [IdeogramAspectRatio.ASPECT_1_1, IdeogramAspectRatio.ASPECT_4_3],
        IdeogramStyle.ANIME: [IdeogramAspectRatio.ASPECT_9_16, IdeogramAspectRatio.ASPECT_3_4],
        IdeogramStyle.REALISTIC: [IdeogramAspectRatio.ASPECT_16_9, IdeogramAspectRatio.ASPECT_3_2],
    }
    
    def __init__(self, api_key: str = None):
        """Initialize Ideogram provider.
        
        Args:
            api_key: Ideogram API key
        """
        self.api_key = api_key or os.getenv("IDEOGRAM_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Ideogram requires an API key. "
                "Set IDEOGRAM_API_KEY environment variable."
            )
        
        # Store for parent class
        super().__init__(api_key=self.api_key)
        
        self._session: Optional[aiohttp.ClientSession] = None
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return "ideogram"
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=list(self.MODELS.keys()),
            max_resolution={"width": 2048, "height": 2048},  # Varies by aspect ratio
            formats=["png", "jpg"],
            features=[
                "text_to_image",
                "text_rendering",
                "typography",
                "logo_generation",
                "style_control",
                "color_palette",
                "aspect_ratio_flexibility",
                "magic_prompt",
                "upscaling",
                "remixing",
            ],
            pricing=self.PRICING,
            supports_streaming=False,
            supports_batch=True,  # Can request multiple images
        )
        
    async def initialize(self):
        """Initialize the provider."""
        if not self._session:
            self._session = aiohttp.ClientSession()
            
    async def cleanup(self):
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None
            
    def _estimate_generation_time(self, request: GenerationRequest) -> float:
        """Estimate generation time for a request."""
        params = request.parameters or {}
        model = self.MODELS.get(request.model, IdeogramModel.V3.value)
        
        # Base times by model
        if model == IdeogramModel.V2_TURBO.value:
            base_time = 10.0  # 7-12 seconds for turbo
        elif model == IdeogramModel.V2.value:
            base_time = 20.0  # Slower but higher quality
        else:  # V3
            base_time = 25.0  # Latest model
            
        # Add time for multiple images
        num_images = params.get("number_of_images", 1)
        base_time += (num_images - 1) * 5.0
        
        return base_time
        
    async def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate the cost of a generation request."""
        model_key = self.MODELS.get(request.model, IdeogramModel.V3.value)
        base_cost = self.PRICING.get(model_key, 0.10)
        
        params = request.parameters or {}
        num_images = params.get("number_of_images", 1)
        
        # Additional cost for upscaling
        if params.get("upscale", False):
            base_cost += 0.02  # Additional cost for upscaling
            
        return base_cost * num_images
        
    def _validate_aspect_ratio(self, aspect_ratio: str) -> Optional[IdeogramAspectRatio]:
        """Validate and convert aspect ratio string."""
        # Handle common formats
        ratio_map = {
            "1:1": IdeogramAspectRatio.ASPECT_1_1,
            "16:9": IdeogramAspectRatio.ASPECT_16_9,
            "9:16": IdeogramAspectRatio.ASPECT_9_16,
            "4:3": IdeogramAspectRatio.ASPECT_4_3,
            "3:4": IdeogramAspectRatio.ASPECT_3_4,
            "16:10": IdeogramAspectRatio.ASPECT_16_10,
            "10:16": IdeogramAspectRatio.ASPECT_10_16,
            "3:2": IdeogramAspectRatio.ASPECT_3_2,
            "2:3": IdeogramAspectRatio.ASPECT_2_3,
            "3:1": IdeogramAspectRatio.ASPECT_3_1,
            "1:3": IdeogramAspectRatio.ASPECT_1_3,
        }
        
        if aspect_ratio in ratio_map:
            return ratio_map[aspect_ratio]
            
        # Try to match enum directly
        try:
            return IdeogramAspectRatio[aspect_ratio]
        except KeyError:
            return None
            
    def _validate_style(self, style: str) -> Optional[IdeogramStyle]:
        """Validate and convert style string."""
        style_map = {
            "realistic": IdeogramStyle.REALISTIC,
            "design": IdeogramStyle.DESIGN,
            "3d": IdeogramStyle.RENDER_3D,
            "render_3d": IdeogramStyle.RENDER_3D,
            "anime": IdeogramStyle.ANIME,
            "auto": IdeogramStyle.AUTO,
        }
        
        style_lower = style.lower()
        if style_lower in style_map:
            return style_map[style_lower]
            
        # Try to match enum directly
        try:
            return IdeogramStyle[style]
        except KeyError:
            return None
            
    async def _prepare_request_body(self, request: GenerationRequest) -> Dict[str, Any]:
        """Prepare the request body for Ideogram API."""
        params = request.parameters or {}
        model = self.MODELS.get(request.model, IdeogramModel.V3.value)
        
        # Determine endpoint version
        use_v3 = model == IdeogramModel.V3.value
        
        if use_v3:
            # V3 API format
            body = {
                "prompt": request.prompt,
                "options": {
                    "model": model,
                }
            }
            
            # Number of images
            if params.get("number_of_images"):
                body["options"]["count"] = params["number_of_images"]
                
            # Style
            if params.get("style"):
                style = self._validate_style(params["style"])
                if style:
                    body["options"]["style_type"] = style.value
                    
            # Aspect ratio
            if params.get("aspect_ratio"):
                aspect = self._validate_aspect_ratio(params["aspect_ratio"])
                if aspect:
                    body["options"]["aspect_ratio"] = aspect.value
                    
            # Negative prompt
            if params.get("negative_prompt"):
                body["options"]["negative_prompt"] = params["negative_prompt"]
                
            # Seed
            if params.get("seed") is not None:
                body["options"]["seed"] = params["seed"]
                
            # Color palette
            if params.get("color_palette"):
                body["options"]["color_palette"] = params["color_palette"]
                
            # Magic prompt
            magic_prompt = params.get("magic_prompt_option", "AUTO")
            body["options"]["magic_prompt_option"] = magic_prompt
            
        else:
            # Legacy API format (V2)
            body = {
                "image_request": {
                    "prompt": request.prompt,
                    "model": model,
                }
            }
            
            # Number of images
            if params.get("number_of_images"):
                body["image_request"]["num_images"] = params["number_of_images"]
                
            # Style
            if params.get("style"):
                style = self._validate_style(params["style"])
                if style:
                    body["image_request"]["style_type"] = style.value
                    
            # Aspect ratio
            if params.get("aspect_ratio"):
                aspect = self._validate_aspect_ratio(params["aspect_ratio"])
                if aspect:
                    body["image_request"]["aspect_ratio"] = aspect.value
                    
            # Negative prompt
            if params.get("negative_prompt"):
                body["image_request"]["negative_prompt"] = params["negative_prompt"]
                
            # Seed
            if params.get("seed") is not None:
                body["image_request"]["seed"] = params["seed"]
                
            # Magic prompt
            magic_prompt = params.get("magic_prompt_option", "AUTO")
            body["image_request"]["magic_prompt_option"] = magic_prompt
            
        return body, use_v3
        
    async def _download_image(self, url: str) -> bytes:
        """Download image from URL (Ideogram images expire)."""
        async with self._session.get(url) as resp:
            if resp.status != 200:
                raise GenerationError(f"Failed to download image: {resp.status}")
            return await resp.read()
            
    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Perform the actual generation using Ideogram API."""
        if not self._session:
            await self.initialize()
            
        try:
            # Prepare request
            body, use_v3 = await self._prepare_request_body(request)
            
            # Determine endpoint
            endpoint = self.ENDPOINTS["generate_v3"] if use_v3 else self.ENDPOINTS["generate"]
            
            # Make API request
            headers = {
                "Api-Key": self.api_key,
                "Content-Type": "application/json",
            }
            
            url = f"{self.BASE_URL}{endpoint}"
            
            async with self._session.post(url, headers=headers, json=body) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    if resp.status == 401:
                        raise AuthenticationError("Invalid API key")
                    elif resp.status == 429:
                        raise GenerationError("Rate limit exceeded")
                    else:
                        raise GenerationError(f"Generation failed: {error_text}")
                        
                data = await resp.json()
                
            # Process results
            file_paths = []
            metadata_list = []
            
            # V3 response format
            if use_v3:
                images = data.get("images", [])
                for i, image_data in enumerate(images):
                    # Download image (URLs expire)
                    image_url = image_data.get("url")
                    if image_url:
                        image_bytes = await self._download_image(image_url)
                        
                        if request.output_path:
                            file_path = request.output_path / f"ideogram_{i}.png"
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(file_path, "wb") as f:
                                f.write(image_bytes)
                            file_paths.append(file_path)
                            
                        metadata_list.append({
                            "seed": image_data.get("seed"),
                            "style": image_data.get("style_type"),
                            "is_safe": image_data.get("is_image_safe", True),
                        })
            else:
                # Legacy response format
                images = data.get("data", [])
                for i, image_data in enumerate(images):
                    # Download image (URLs expire)
                    image_url = image_data.get("url")
                    if image_url:
                        image_bytes = await self._download_image(image_url)
                        
                        if request.output_path:
                            file_path = request.output_path / f"ideogram_{i}.png"
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(file_path, "wb") as f:
                                f.write(image_bytes)
                            file_paths.append(file_path)
                            
                        metadata_list.append({
                            "prompt": image_data.get("prompt"),
                            "resolution": image_data.get("resolution"),
                            "seed": image_data.get("seed"),
                            "style": image_data.get("style_type"),
                            "is_safe": image_data.get("is_image_safe", True),
                        })
                        
            # Calculate actual cost
            actual_cost = await self.estimate_cost(request)
            
            # Get generation metadata
            params = request.parameters or {}
            metadata = {
                "provider": "ideogram",
                "model": request.model,
                "prompt": request.prompt,
                "style": params.get("style"),
                "aspect_ratio": params.get("aspect_ratio"),
                "images_metadata": metadata_list,
            }
            
            return GenerationResult(
                success=True,
                file_path=file_paths[0] if file_paths else None,
                cost=actual_cost,
                generation_time=self._estimate_generation_time(request),
                metadata=metadata,
                provider="ideogram",
                model=request.model,
            )
            
        except Exception as e:
            logger.error(f"Ideogram generation failed: {str(e)}")
            return GenerationResult(
                success=False,
                error=str(e),
                provider="ideogram",
                model=request.model,
            )
            
    async def upscale_image(self, image_path: Path, resolution: str = "2048x2048") -> GenerationResult:
        """Upscale an image using Ideogram's upscaling feature.
        
        Args:
            image_path: Path to image to upscale
            resolution: Target resolution
            
        Returns:
            GenerationResult with upscaled image
        """
        if not self._session:
            await self.initialize()
            
        try:
            # Read image
            with open(image_path, "rb") as f:
                image_data = f.read()
                
            # Upload and upscale
            headers = {
                "Api-Key": self.api_key,
                "Content-Type": "application/json",
            }
            
            # In real implementation, would need to upload image first
            body = {
                "image_data": image_data,
                "resolution": resolution,
            }
            
            url = f"{self.BASE_URL}{self.ENDPOINTS['upscale']}"
            
            async with self._session.post(url, headers=headers, json=body) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise GenerationError(f"Upscaling failed: {error_text}")
                    
                data = await resp.json()
                
            # Download result
            result_url = data.get("url")
            if result_url:
                upscaled_data = await self._download_image(result_url)
                
                output_path = image_path.parent / f"{image_path.stem}_upscaled{image_path.suffix}"
                with open(output_path, "wb") as f:
                    f.write(upscaled_data)
                    
                return GenerationResult(
                    success=True,
                    file_path=output_path,
                    cost=0.02,  # Upscaling cost
                    provider="ideogram",
                    model="upscaler",
                )
                
        except Exception as e:
            logger.error(f"Ideogram upscaling failed: {str(e)}")
            return GenerationResult(
                success=False,
                error=str(e),
                provider="ideogram",
                model="upscaler",
            )
            
    async def check_status(self) -> ProviderStatus:
        """Check provider availability status."""
        try:
            if not self._session:
                await self.initialize()
                
            # Try a simple API call with minimal parameters
            headers = {
                "Api-Key": self.api_key,
                "Content-Type": "application/json",
            }
            
            # Use a minimal test request
            body = {
                "image_request": {
                    "prompt": "test",
                    "model": IdeogramModel.V2_TURBO.value,
                }
            }
            
            url = f"{self.BASE_URL}{self.ENDPOINTS['generate']}"
            
            # We don't actually want to generate, just check auth
            # Most APIs will validate auth before processing
            async with self._session.post(url, headers=headers, json=body) as resp:
                if resp.status == 401:
                    self._status = ProviderStatus.UNAVAILABLE
                    return ProviderStatus.UNAVAILABLE
                elif resp.status in [200, 400, 429]:  # 400/429 means API is working
                    self._status = ProviderStatus.AVAILABLE
                    return ProviderStatus.AVAILABLE
                else:
                    self._status = ProviderStatus.DEGRADED
                    return ProviderStatus.DEGRADED
                    
        except Exception as e:
            logger.error(f"Ideogram status check failed: {e}")
            self._status = ProviderStatus.UNAVAILABLE
            return ProviderStatus.UNAVAILABLE