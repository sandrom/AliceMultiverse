"""Freepik API provider for Magnific upscaling and Mystic image generation."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import aiohttp

from .provider import Provider, GenerationError, ProviderStatus
from .types import (
    CostEstimate,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
)

logger = logging.getLogger(__name__)


class FreepikProvider(Provider):
    """Provider for Freepik API (Magnific upscaler and Mystic model)."""
    
    # API configuration
    BASE_URL = "https://api.freepik.com/v1"
    
    # Model mappings
    MODELS = {
        # Magnific upscaler engines
        "magnific-sparkle": "magnific_sparkle",  # Best quality, slower
        "magnific-illusio": "magnific_illusio",  # Balanced
        "magnific-sharpy": "magnific_sharpy",    # Fast, good for sharp images
        
        # Mystic image generation
        "mystic": "mystic",                       # Photorealistic generation
        "mystic-2k": "mystic",                    # 2K resolution
        "mystic-4k": "mystic",                    # 4K resolution
    }
    
    # Pricing (EUR)
    PRICING = {
        # Magnific upscaling - based on output pixels
        "magnific-sparkle": 0.01,    # Per megapixel
        "magnific-illusio": 0.008,   # Per megapixel
        "magnific-sharpy": 0.006,    # Per megapixel
        
        # Mystic generation
        "mystic": 0.004,             # Per image
        "mystic-2k": 0.006,          # 2K resolution
        "mystic-4k": 0.008,          # 4K resolution
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Freepik provider.
        
        Args:
            api_key: Freepik API key
        """
        super().__init__(api_key)
        self.session = None
        
        # Build capabilities
        self._capabilities = ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=list(self.MODELS.keys()),
            formats=["jpg", "jpeg", "png", "webp"],
            features=[
                "upscaling",
                "style_reference", 
                "lora_support",
                "async_generation",
            ],
            max_resolution={"width": 16384, "height": 16384},  # 16K upscaling
        )
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "freepik"
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return self._capabilities
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> dict[str, str]:
        """Get API headers."""
        return {
            "x-freepik-api-key": self.api_key,
            "Content-Type": "application/json",
        }
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure aiohttp session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content using Freepik API.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        model = request.model
        
        # Determine if this is upscaling or generation
        if model.startswith("magnific"):
            return await self._upscale_image(request)
        elif model.startswith("mystic"):
            return await self._generate_image(request)
        else:
            raise ValueError(f"Unknown model: {model}")
    
    async def _upscale_image(self, request: GenerationRequest) -> GenerationResult:
        """Upscale image using Magnific.
        
        Args:
            request: Generation request with reference image
            
        Returns:
            Upscaling result
        """
        if not request.reference_assets:
            raise ValueError("Magnific upscaling requires a reference image")
        
        session = await self._ensure_session()
        
        # Prepare upscaling parameters
        params = self._build_upscale_params(request)
        
        # Submit upscaling task
        url = urljoin(self.BASE_URL, "/ai/image-upscaler")
        
        async with session.post(
            url,
            json=params,
            headers=self._get_headers()
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise GenerationError(f"Upscaling failed: {error}")
            
            data = await response.json()
            task_id = data["data"]["_id"]
        
        # Poll for completion
        result_url = await self._poll_task(task_id, "image-upscaler")
        
        # Calculate cost based on output size
        output_megapixels = self._calculate_megapixels(params.get("scale", 2))
        cost = self.PRICING[request.model] * output_megapixels
        
        return GenerationResult(
            success=True,
            file_path=Path(result_url),
            metadata={
                "task_id": task_id,
                "engine": self.MODELS[request.model],
                "scale": params.get("scale", 2),
                "output_megapixels": output_megapixels,
                "parameters": params,
                "generation_id": task_id,
            },
            cost=cost,
            provider=self.name,
            model=request.model,
        )
    
    async def _generate_image(self, request: GenerationRequest) -> GenerationResult:
        """Generate image using Mystic model.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        session = await self._ensure_session()
        
        # Prepare generation parameters
        params = self._build_mystic_params(request)
        
        # Submit generation task
        url = urljoin(self.BASE_URL, "/ai/mystic")
        
        async with session.post(
            url,
            json=params,
            headers=self._get_headers()
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise GenerationError(f"Generation failed: {error}")
            
            data = await response.json()
            task_id = data["data"]["_id"]
        
        # Poll for completion
        result_url = await self._poll_task(task_id, "mystic")
        
        return GenerationResult(
            success=True,
            file_path=Path(result_url),
            metadata={
                "task_id": task_id,
                "prompt": request.prompt,
                "resolution": params.get("image", {}).get("size", "square_1024"),
                "parameters": params,
                "generation_id": task_id,
            },
            cost=self.PRICING[request.model],
            provider=self.name,
            model=request.model,
        )
    
    def _build_upscale_params(self, request: GenerationRequest) -> dict[str, Any]:
        """Build parameters for Magnific upscaling.
        
        Args:
            request: Generation request
            
        Returns:
            API parameters
        """
        params = request.parameters or {}
        
        # Get reference image URL
        image_url = str(request.reference_assets[0])
        
        return {
            "image": {"url": image_url},
            "scale": params.get("scale", 2),  # 2x, 4x, 8x, 16x
            "engine": self.MODELS[request.model],
            "creativity": params.get("creativity", 0.5),  # 0-10
            "hdr": params.get("hdr", 0.5),  # 0-10
            "resemblance": params.get("resemblance", 0.5),  # 0-10
            "fractality": params.get("fractality", 0.5),  # 0-10
            "detail_refinement": params.get("detail_refinement", 0.5),  # 0-10
            "style": params.get("style", "auto"),  # auto, cinematic, photographic, etc.
            "webhook": params.get("webhook"),  # Optional webhook URL
        }
    
    def _build_mystic_params(self, request: GenerationRequest) -> dict[str, Any]:
        """Build parameters for Mystic generation.
        
        Args:
            request: Generation request
            
        Returns:
            API parameters
        """
        params = request.parameters or {}
        
        # Determine resolution
        if request.model == "mystic-4k":
            size = "landscape_4k"
        elif request.model == "mystic-2k":
            size = "landscape_2k"
        else:
            size = params.get("size", "square_1024")
        
        api_params = {
            "prompt": request.prompt,
            "negative_prompt": params.get("negative_prompt", ""),
            "image": {
                "size": size,
                "guidance_scale": params.get("guidance_scale", 5.0),  # 1-10
                "num_inference_steps": params.get("num_inference_steps", 50),  # 10-50
                "seed": params.get("seed"),  # Optional
            },
            "styling": {
                "style": params.get("style", ""),  # Optional style preset
                "detail": params.get("detail", 1.0),  # 0-2
                "style_strength": params.get("style_strength", 0.5),  # 0-1
                "structure": params.get("structure", 0.6),  # 0-1
            },
        }
        
        # Add reference image if provided (for style reference)
        if request.reference_assets:
            api_params["styling"]["references"] = [
                {"url": str(ref)} for ref in request.reference_assets
            ]
        
        # Add LoRA if specified
        if params.get("lora"):
            api_params["lora"] = {
                "name": params["lora"],
                "strength": params.get("lora_strength", 0.7),
            }
        
        return api_params
    
    async def _poll_task(
        self,
        task_id: str,
        endpoint: str,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> str:
        """Poll for task completion.
        
        Args:
            task_id: Task ID to poll
            endpoint: API endpoint (image-upscaler or mystic)
            timeout: Maximum wait time in seconds
            poll_interval: Seconds between polls
            
        Returns:
            Result URL
        """
        session = await self._ensure_session()
        url = urljoin(self.BASE_URL, f"/ai/{endpoint}/{task_id}")
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status != 200:
                    error = await response.text()
                    raise GenerationError(f"Failed to check task status: {error}")
                
                data = await response.json()
                task_data = data["data"]
                
                status = task_data.get("status")
                
                if status == "completed":
                    # Get result URL
                    if endpoint == "image-upscaler":
                        return task_data["result"]["url"]
                    else:  # mystic
                        return task_data["images"][0]["url"]
                
                elif status == "failed":
                    error = task_data.get("error", "Unknown error")
                    raise GenerationError(f"Task failed: {error}")
                
                # Still processing
                await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
    
    def _calculate_megapixels(self, scale: int) -> float:
        """Calculate output megapixels for pricing.
        
        Args:
            scale: Upscaling factor (2, 4, 8, 16)
            
        Returns:
            Estimated megapixels
        """
        # Assume average input is 1 megapixel
        # Output = input * scale^2
        base_megapixels = 1.0
        return base_megapixels * (scale ** 2)
    
    async def estimate_cost(self, request: GenerationRequest) -> CostEstimate:
        """Estimate generation cost.
        
        Args:
            request: Generation request
            
        Returns:
            Cost estimate
        """
        base_cost_eur = self.PRICING.get(request.model, 0.01)
        
        # For upscaling, estimate based on scale
        if request.model.startswith("magnific"):
            scale = request.parameters.get("scale", 2) if request.parameters else 2
            megapixels = self._calculate_megapixels(scale)
            base_cost_eur *= megapixels
        
        # Convert EUR to USD (approximate)
        cost_usd = base_cost_eur * 1.1
        
        # Get time estimate
        min_time, max_time = self.get_generation_time(request)
        
        return CostEstimate(
            provider=self.name,
            model=request.model,
            estimated_cost=cost_usd,
            confidence=0.95,
            breakdown={
                "base_cost_eur": base_cost_eur,
                "exchange_rate": 1.1,
                "megapixels": megapixels if request.model.startswith("magnific") else None
            }
        )
    
    async def validate_request(self, request: GenerationRequest) -> None:
        """Validate generation request.
        
        Args:
            request: Request to validate
            
        Raises:
            ValueError: If request is invalid
        """
        if request.model not in self.MODELS:
            raise ValueError(f"Model {request.model} not supported by Freepik")
        
        # Upscaling requires reference image
        if request.model.startswith("magnific") and not request.reference_assets:
            raise ValueError("Magnific upscaling requires a reference image")
        
        # Mystic requires prompt
        if request.model.startswith("mystic") and not request.prompt:
            raise ValueError("Mystic generation requires a prompt")
    
    def get_generation_time(self, request: GenerationRequest) -> tuple[int, int]:
        """Get estimated generation time range.
        
        Args:
            request: Generation request
            
        Returns:
            Tuple of (min_seconds, max_seconds)
        """
        if request.model.startswith("magnific"):
            # Upscaling time depends on scale
            scale = request.parameters.get("scale", 2) if request.parameters else 2
            if scale <= 2:
                return (10, 30)
            elif scale <= 4:
                return (20, 60)
            elif scale <= 8:
                return (40, 120)
            else:  # 16x
                return (60, 180)
        else:  # Mystic
            return (15, 45)
    
    async def check_status(self) -> ProviderStatus:
        """Check provider availability.
        
        Returns:
            Provider status
        """
        try:
            session = await self._ensure_session()
            
            # Try to check API health endpoint or use a simple endpoint
            url = urljoin(self.BASE_URL, "/ai/loras")  # List LoRAs as health check
            
            async with session.get(url, headers=self._get_headers(), timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    self._status = ProviderStatus.AVAILABLE
                elif response.status == 401:
                    self._status = ProviderStatus.AUTH_FAILED
                elif response.status == 429:
                    self._status = ProviderStatus.RATE_LIMITED
                else:
                    self._status = ProviderStatus.ERROR
                    
        except asyncio.TimeoutError:
            self._status = ProviderStatus.TIMEOUT
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            self._status = ProviderStatus.ERROR
            
        self._last_check = datetime.now()
        return self._status