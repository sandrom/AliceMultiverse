"""Leonardo.ai provider implementation.

Leonardo.ai is a powerful AI image generation platform offering:
- Multiple models (Phoenix, Flux, PhotoReal, Alchemy)
- Custom model training
- Elements system for style control
- Real-time canvas features
- Advanced control with ControlNet
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
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


class LeonardoModel(str, Enum):
    """Leonardo model identifiers."""

    # Phoenix Models
    PHOENIX_1_0 = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3"
    PHOENIX_0_9 = "6b645e3a-d64f-4341-a6d8-7a3690fbf042"
    
    # Flux Models
    FLUX_DEV = "b2614463-296c-462a-9586-aafdb8f00e36"
    FLUX_SCHNELL = "1dd50843-d653-4516-a8e3-f0238ee453ff"
    
    # SDXL Models (for Alchemy V2)
    VISION_XL = "aa77f04e-3eec-4034-9c07-d0f619684628"  # Leonardo Vision XL
    DIFFUSION_XL = "b7aa9939-abed-4d4e-96c4-140b8c65dd92"  # Leonardo Diffusion XL
    KINO_XL = "b24e16ff-06e3-43eb-8d33-4416c2d75876"  # Leonardo Kino XL
    ALBEDO_BASE_XL = "2067ae52-33fd-4a82-bb92-c2c55e7d2786"  # AlbedoBase XL


class PresetStyle(str, Enum):
    """Preset styles for generation."""
    
    # PhotoReal styles
    CINEMATIC = "CINEMATIC"
    CREATIVE = "CREATIVE"
    VIBRANT = "VIBRANT"
    
    # Alchemy styles
    ANIME = "ANIME"
    DYNAMIC = "DYNAMIC"
    ENVIRONMENT = "ENVIRONMENT"
    GENERAL = "GENERAL"
    ILLUSTRATION = "ILLUSTRATION"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    RAYTRACED = "RAYTRACED"
    RENDER_3D = "RENDER_3D"
    SKETCH_BW = "SKETCH_BW"
    SKETCH_COLOR = "SKETCH_COLOR"
    
    NONE = "NONE"


class LeonardoProvider(Provider):
    """Leonardo.ai provider for AI image generation.
    
    Features:
    - Multiple models: Phoenix, Flux, PhotoReal, SDXL
    - Alchemy enhancement for better quality
    - Custom Elements for style control
    - ControlNet support
    - Image-to-image generation
    - Custom model training
    """
    
    BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"
    
    # Model aliases for user convenience
    MODELS = {
        "phoenix": LeonardoModel.PHOENIX_1_0.value,
        "phoenix-1.0": LeonardoModel.PHOENIX_1_0.value,
        "phoenix-0.9": LeonardoModel.PHOENIX_0_9.value,
        "flux": LeonardoModel.FLUX_DEV.value,
        "flux-dev": LeonardoModel.FLUX_DEV.value,
        "flux-schnell": LeonardoModel.FLUX_SCHNELL.value,
        "vision-xl": LeonardoModel.VISION_XL.value,
        "diffusion-xl": LeonardoModel.DIFFUSION_XL.value,
        "kino-xl": LeonardoModel.KINO_XL.value,
        "albedo-xl": LeonardoModel.ALBEDO_BASE_XL.value,
        "leonardo": LeonardoModel.PHOENIX_1_0.value,  # Default
    }
    
    # Base pricing in tokens (1000 tokens = $1 on standard plan)
    PRICING = {
        LeonardoModel.PHOENIX_1_0.value: 20,  # Base cost
        LeonardoModel.PHOENIX_0_9.value: 20,
        LeonardoModel.FLUX_DEV.value: 25,
        LeonardoModel.FLUX_SCHNELL.value: 15,
        LeonardoModel.VISION_XL.value: 20,
        LeonardoModel.DIFFUSION_XL.value: 20,
        LeonardoModel.KINO_XL.value: 20,
        LeonardoModel.ALBEDO_BASE_XL.value: 20,
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Leonardo provider.
        
        Args:
            api_key: Leonardo API key. Can also be set via LEONARDO_API_KEY env var.
        """
        super().__init__(api_key)
        if not self.api_key:
            self.api_key = os.environ.get("LEONARDO_API_KEY")
        
        if not self.api_key:
            raise AuthenticationError("Leonardo API key is required")
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "leonardo"
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=list(self.MODELS.keys()),
            max_resolution={"width": 1536, "height": 1536},
            formats=["jpg", "jpeg", "png", "webp"],
            features=[
                "alchemy",
                "photo_real",
                "elements",
                "control_net",
                "enhance_prompt",
                "style_presets",
                "negative_prompt",
                "image_to_image",
            ],
            rate_limits={"requests_per_minute": 60},
            pricing={
                "phoenix": 0.02,  # $0.02 per image base
                "flux-dev": 0.025,
                "flux-schnell": 0.015,
                "vision-xl": 0.02,
            },
            supports_streaming=False,
            supports_batch=True,
        )
    
    def _resolve_model(self, model: str) -> str:
        """Resolve model alias to actual model ID."""
        model_lower = model.lower()
        
        # Check if it's an alias
        if model_lower in self.MODELS:
            return self.MODELS[model_lower]
        
        # Check if it's a direct model ID
        for m in LeonardoModel:
            if model == m.value:
                return model
        
        # Default to Phoenix 1.0
        logger.warning(f"Unknown model {model}, defaulting to Phoenix 1.0")
        return LeonardoModel.PHOENIX_1_0.value
    
    async def _generate(
        self,
        request: GenerationRequest
    ) -> GenerationResult:
        """Generate images using Leonardo.ai.
        
        Args:
            request: Generation request
        
        Returns:
            Generation result with images
        """
        try:
            # Validate request
            if request.generation_type != GenerationType.IMAGE:
                raise ValueError(f"Leonardo only supports image generation, not {request.generation_type}")
            
            # Extract parameters
            params = request.parameters or {}
            
            # Resolve model
            model_id = self._resolve_model(request.model or "phoenix")
            
            # Build generation payload
            payload = {
                "prompt": request.prompt,
                "num_images": params.get("num_images", 1),
                "width": params.get("width", 1024),
                "height": params.get("height", 1024),
                "guidance_scale": params.get("guidance_scale", 7.0),
                "seed": params.get("seed"),
            }
            
            # Add model ID unless using PhotoReal v1
            photo_real = params.get("photo_real", False)
            photo_real_version = params.get("photo_real_version", "v1")
            
            if not (photo_real and photo_real_version == "v1"):
                payload["modelId"] = model_id
            
            # PhotoReal settings
            if photo_real:
                payload["photoReal"] = True
                if photo_real_version == "v2":
                    payload["photoRealVersion"] = "v2"
                if "preset_style" in params:
                    payload["presetStyle"] = params["preset_style"]
                if "photo_real_strength" in params:
                    payload["photoRealStrength"] = params["photo_real_strength"]
            
            # Alchemy settings
            if params.get("alchemy"):
                payload["alchemy"] = True
                if "preset_style" in params:
                    payload["presetStyle"] = params["preset_style"]
            
            # Phoenix-specific settings
            if model_id in [LeonardoModel.PHOENIX_1_0.value, LeonardoModel.PHOENIX_0_9.value]:
                if "contrast" in params:
                    payload["contrast"] = params["contrast"]
                if params.get("enhance_prompt"):
                    payload["enhancePrompt"] = True
                    if "enhance_prompt_instruction" in params:
                        payload["enhancePromptInstruction"] = params["enhance_prompt_instruction"]
            
            # Additional parameters
            if "negative_prompt" in params:
                payload["negative_prompt"] = params["negative_prompt"]
            
            if "elements" in params:
                payload["elements"] = params["elements"]
            
            # Image-to-image
            if "init_image_id" in params:
                payload["init_image_id"] = params["init_image_id"]
                payload["init_strength"] = params.get("init_strength", 0.5)
            
            # ControlNet
            if params.get("control_net"):
                payload["controlNet"] = True
                if "control_net_type" in params:
                    payload["controlNetType"] = params["control_net_type"]
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                async with session.post(
                    f"{self.BASE_URL}/generations",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise GenerationError(f"Leonardo API error: {response.status} - {error_text}")
                    
                    data = await response.json()
                    generation_id = data["sdGenerationJob"]["generationId"]
            
            # Poll for completion
            result = await self._poll_generation(generation_id)
            
            # Download the first image
            image_url = result["generated_images"][0]["url"]
            image_path = await self._download_image(image_url, request.output_path)
            
            # Calculate cost
            cost = self.estimate_cost(request)
            
            return GenerationResult(
                success=True,
                file_path=image_path,
                generation_time=result.get("generation_time", 15.0),
                cost=cost,
                metadata={
                    "generation_id": generation_id,
                    "model": model_id,
                    "prompt": request.prompt,
                    "seed": result["generated_images"][0].get("seed"),
                    "all_images": [img["url"] for img in result.get("generated_images", [])],
                    "leonardo_params": {k: v for k, v in params.items() if k != "api_key"},
                },
                provider=self.name,
                model=request.model,
            )
            
        except Exception as e:
            logger.error(f"Leonardo generation failed: {e}")
            return GenerationResult(
                success=False,
                error=str(e),
                provider=self.name,
                model=request.model,
            )
    
    async def _poll_generation(
        self,
        generation_id: str,
        max_attempts: int = 60,
        delay: float = 2.0
    ) -> Dict[str, Any]:
        """Poll for generation completion.
        
        Args:
            generation_id: Leonardo generation ID
            max_attempts: Maximum polling attempts
            delay: Delay between polls in seconds
            
        Returns:
            Generation result data
        """
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            for attempt in range(max_attempts):
                try:
                    async with session.get(
                        f"{self.BASE_URL}/generations/{generation_id}",
                        headers=headers
                    ) as response:
                        if response.status != 200:
                            raise GenerationError(f"Failed to poll generation: {response.status}")
                        
                        data = await response.json()
                        generation = data.get("generations_by_pk", {})
                        
                        if generation.get("status") == "COMPLETE":
                            return generation
                        elif generation.get("status") == "FAILED":
                            raise GenerationError(f"Generation failed: {generation.get('error')}")
                        
                        # Still processing
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"Error polling generation: {e}")
                    if attempt == max_attempts - 1:
                        raise
        
        raise TimeoutError(f"Generation {generation_id} timed out after {max_attempts * delay}s")
    
    async def _download_image(self, url: str, output_path: Optional[Path] = None) -> Path:
        """Download image from URL.
        
        Args:
            url: Image URL
            output_path: Where to save the image
            
        Returns:
            Path to downloaded image
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise GenerationError(f"Failed to download image: {response.status}")
                
                # Use provided path or create temp file
                if output_path:
                    file_path = output_path
                else:
                    import tempfile
                    fd, temp_path = tempfile.mkstemp(suffix=".png")
                    os.close(fd)
                    file_path = Path(temp_path)
                
                # Save image
                content = await response.read()
                file_path.write_bytes(content)
                
                return file_path
    
    def estimate_cost(
        self,
        request: GenerationRequest
    ) -> float:
        """Estimate generation cost.
        
        Leonardo uses a token system where 1000 tokens = $1 on standard plan.
        Costs vary based on model, resolution, and features.
        
        Args:
            request: Generation request
            
        Returns:
            Estimated cost in dollars
        """
        params = request.parameters or {}
        
        # Get base cost for model
        model_id = self._resolve_model(request.model or "phoenix")
        base_tokens = self.PRICING.get(model_id, 20)
        
        # PhotoReal costs more
        if params.get("photo_real"):
            base_tokens = 20  # Fixed cost for PhotoReal
        
        # Resolution multiplier
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        pixels = width * height
        base_pixels = 1024 * 1024
        resolution_multiplier = pixels / base_pixels
        
        # Alchemy multiplier
        alchemy_multiplier = 1.0
        if params.get("alchemy"):
            # Alchemy v2 outputs 1.75x bigger
            if model_id in [LeonardoModel.VISION_XL.value, LeonardoModel.DIFFUSION_XL.value,
                           LeonardoModel.KINO_XL.value, LeonardoModel.ALBEDO_BASE_XL.value]:
                alchemy_multiplier = 1.75
            else:
                # Alchemy v1 outputs 1.5x bigger
                alchemy_multiplier = 1.5
        
        # Calculate total tokens
        num_images = params.get("num_images", 1)
        total_tokens = base_tokens * resolution_multiplier * alchemy_multiplier * num_images
        
        # Convert to dollars (1000 tokens = $1)
        cost = total_tokens / 1000.0
        
        return round(cost, 4)
    
    def get_generation_time(
        self,
        request: GenerationRequest
    ) -> float:
        """Estimate generation time in seconds.
        
        Args:
            request: Generation request
            
        Returns:
            Estimated time in seconds
        """
        params = request.parameters or {}
        
        # Base times for different models
        model_id = self._resolve_model(request.model or "phoenix")
        
        if model_id == LeonardoModel.FLUX_SCHNELL.value:
            base_time = 5.0  # Schnell is fast
        elif model_id in [LeonardoModel.FLUX_DEV.value, LeonardoModel.PHOENIX_1_0.value]:
            base_time = 15.0
        else:
            base_time = 10.0
        
        # Alchemy adds time
        if params.get("alchemy"):
            base_time *= 1.5
        
        # PhotoReal adds time
        if params.get("photo_real"):
            base_time *= 1.3
        
        # Multiple images
        num_images = params.get("num_images", 1)
        base_time *= num_images * 0.8  # Some parallelization
        
        return base_time
    
    async def upload_image(self, image_path: Path) -> str:
        """Upload an image for img2img or ControlNet.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Leonardo image ID
        """
        # TODO: Implement image upload endpoint
        # This would use the upload endpoint and return an image ID
        raise NotImplementedError("Image upload not yet implemented")
    
    async def list_elements(self) -> List[Dict[str, Any]]:
        """List available Elements for style control.
        
        Returns:
            List of Element objects with IDs and descriptions
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                async with session.get(
                    f"{self.BASE_URL}/elements",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to list elements: {response.status}")
                        return []
                    
                    data = await response.json()
                    return data.get("user_elements", [])
                    
        except Exception as e:
            logger.error(f"Error listing elements: {e}")
            return []
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available platform models.
        
        Returns:
            List of model objects
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                async with session.get(
                    f"{self.BASE_URL}/platformModels",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to list models: {response.status}")
                        return []
                    
                    data = await response.json()
                    return data.get("platform_models", [])
                    
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def check_status(self) -> ProviderStatus:
        """Check provider availability."""
        # For now, assume available if API key is set
        if self.api_key:
            return ProviderStatus.AVAILABLE
        return ProviderStatus.UNAVAILABLE