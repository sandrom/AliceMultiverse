"""OpenAI provider implementation for DALL-E image generation."""

import base64
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from ..core.file_operations import download_file
from .provider import Provider, GenerationError, RateLimitError, AuthenticationError
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(Provider):
    """Provider for OpenAI API integration (DALL-E, GPT-4 Vision)."""
    
    BASE_URL = "https://api.openai.com/v1"
    
    # Available models
    MODELS = {
        # Image generation
        "dall-e-3": {
            "endpoint": "/images/generations",
            "type": GenerationType.IMAGE,
            "max_size": {"1024x1024", "1024x1792", "1792x1024"},
            "styles": ["vivid", "natural"],
            "quality": ["standard", "hd"],
        },
        "dall-e-2": {
            "endpoint": "/images/generations", 
            "type": GenerationType.IMAGE,
            "max_size": {"256x256", "512x512", "1024x1024"},
        },
        # Vision models for analysis
        "gpt-4-vision-preview": {
            "endpoint": "/chat/completions",
            "type": GenerationType.TEXT,
            "capabilities": ["image_analysis"],
        },
        "gpt-4o": {
            "endpoint": "/chat/completions",
            "type": GenerationType.TEXT,
            "capabilities": ["image_analysis", "text_generation"],
        },
        "gpt-4o-mini": {
            "endpoint": "/chat/completions",
            "type": GenerationType.TEXT,
            "capabilities": ["image_analysis", "text_generation"],
        },
    }
    
    # Pricing (approximate per generation/request)
    PRICING = {
        "dall-e-3": {
            "standard": {"1024x1024": 0.040, "1024x1792": 0.080, "1792x1024": 0.080},
            "hd": {"1024x1024": 0.080, "1024x1792": 0.120, "1792x1024": 0.120},
        },
        "dall-e-2": {
            "256x256": 0.016,
            "512x512": 0.018,
            "1024x1024": 0.020,
        },
        "gpt-4-vision-preview": 0.01,  # Per 1K tokens (approximate)
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env var)
            **kwargs: Additional arguments for BaseProvider
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        super().__init__(api_key=api_key, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "openai"

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE, GenerationType.TEXT],
            models=list(self.MODELS.keys()),
            max_resolution={"width": 1792, "height": 1792},  # DALL-E 3 max
            formats=["png", "jpg"],
            features=[
                "prompt_rewriting",  # DALL-E 3 rewrites prompts
                "style_selection",   # vivid/natural styles
                "quality_selection", # standard/hd quality
                "image_analysis",    # GPT-4V capabilities
            ],
            rate_limits={
                "requests_per_minute": 5,  # DALL-E 3 tier 1
                "images_per_minute": 5,
            },
            pricing={
                "dall-e-3-standard": 0.040,
                "dall-e-3-hd": 0.080,
                "dall-e-2": 0.020,
                "gpt-4-vision": 0.01,
            }
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def check_status(self) -> ProviderStatus:
        """Check OpenAI API status."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.BASE_URL}/models") as response:
                if response.status == 200:
                    self._status = ProviderStatus.AVAILABLE
                elif response.status == 401:
                    self._status = ProviderStatus.UNAVAILABLE
                    logger.error("OpenAI authentication failed")
                else:
                    self._status = ProviderStatus.DEGRADED
                    
        except Exception as e:
            logger.error(f"Failed to check OpenAI status: {e}")
            self._status = ProviderStatus.UNKNOWN
            
        self._last_check = datetime.now()
        return self._status

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Perform the actual generation using OpenAI.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        # Determine model
        model = request.model or self.get_default_model(request.generation_type)
        
        # Generate based on type
        if request.generation_type == GenerationType.IMAGE:
            result = await self._generate_image(request, model)
        elif request.generation_type == GenerationType.TEXT:
            result = await self._analyze_image(request, model)
        else:
            raise GenerationError(f"Unsupported generation type: {request.generation_type}")
        
        return result

    async def _generate_image(self, request: GenerationRequest, model: str) -> GenerationResult:
        """Generate image using DALL-E."""
        # Build parameters
        params = self._build_dalle_params(request, model)
        
        # Call API
        session = await self._get_session()
        endpoint = self.MODELS[model]["endpoint"]
        
        async with session.post(f"{self.BASE_URL}{endpoint}", json=params) as response:
            if response.status == 429:
                raise RateLimitError("OpenAI rate limit exceeded")
            elif response.status == 401:
                raise AuthenticationError("Invalid OpenAI API key")
            elif response.status != 200:
                error_data = await response.json()
                raise GenerationError(f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            data = await response.json()
        
        # Download image
        image_data = data["data"][0]
        
        if "url" in image_data:
            # Download from URL
            image_url = image_data["url"]
            file_path = await self._download_image(request, image_url)
        else:
            # Save base64 data
            b64_data = image_data["b64_json"]
            file_path = await self._save_base64_image(request, b64_data)
        
        # Calculate cost
        cost = self._calculate_dalle_cost(model, params)
        
        # Get revised prompt if available (DALL-E 3)
        revised_prompt = image_data.get("revised_prompt") if image_data else request.prompt
        
        return GenerationResult(
            success=True,
            file_path=file_path,
            cost=cost,
            provider=self.name,
            model=model,
            metadata={
                "prompt": request.prompt,
                "revised_prompt": revised_prompt,
                "model": model,
                "size": params.get("size"),
                "quality": params.get("quality", "standard"),
                "style": params.get("style", "vivid"),
            }
        )

    async def _analyze_image(self, request: GenerationRequest, model: str) -> GenerationResult:
        """Analyze image using GPT-4 Vision."""
        if not request.reference_assets:
            raise GenerationError("Image analysis requires reference_assets")
        
        # Build vision request
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": request.prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{await self._encode_image(request.reference_assets[0])}"
                    }
                }
            ]
        }]
        
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": request.parameters.get("max_tokens", 300) if request.parameters else 300,
        }
        
        # Call API
        session = await self._get_session()
        endpoint = self.MODELS[model]["endpoint"]
        
        async with session.post(f"{self.BASE_URL}{endpoint}", json=params) as response:
            if response.status != 200:
                error_data = await response.json()
                raise GenerationError(f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            data = await response.json()
        
        # Extract response
        analysis = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens", 0)
        
        # Calculate cost
        cost = (tokens_used / 1000) * self.PRICING.get(model, 0.01)
        
        return GenerationResult(
            success=True,
            provider=self.name,
            model=model,
            cost=cost,
            metadata={
                "analysis": analysis,
                "tokens_used": tokens_used,
                "prompt": request.prompt,
            }
        )

    def _build_dalle_params(self, request: GenerationRequest, model: str) -> Dict[str, Any]:
        """Build parameters for DALL-E request."""
        params = {
            "model": model,
            "prompt": request.prompt,
            "n": 1,  # Number of images
        }
        
        # Get parameters from request
        req_params = request.parameters or {}
        
        if model == "dall-e-3":
            # Size
            size = req_params.get("size", "1024x1024")
            if size not in self.MODELS[model]["max_size"]:
                size = "1024x1024"  # Default
            params["size"] = size
            
            # Quality
            quality = req_params.get("quality", "standard")
            if quality in ["standard", "hd"]:
                params["quality"] = quality
            
            # Style
            style = req_params.get("style", "vivid")
            if style in ["vivid", "natural"]:
                params["style"] = style
                
        elif model == "dall-e-2":
            # Size
            size = req_params.get("size", "1024x1024")
            if size not in self.MODELS[model]["max_size"]:
                size = "1024x1024"
            params["size"] = size
        
        # Response format
        if req_params.get("response_format") == "b64_json":
            params["response_format"] = "b64_json"
        
        return params

    def _calculate_dalle_cost(self, model: str, params: Dict[str, Any]) -> float:
        """Calculate cost for DALL-E generation."""
        if model == "dall-e-3":
            quality = params.get("quality", "standard")
            size = params.get("size", "1024x1024")
            return self.PRICING["dall-e-3"][quality].get(size, 0.040)
        elif model == "dall-e-2":
            size = params.get("size", "1024x1024")
            return self.PRICING["dall-e-2"].get(size, 0.020)
        return 0.0

    async def _download_image(self, request: GenerationRequest, url: str) -> Path:
        """Download image from URL."""
        # Determine output path
        if request.output_path:
            output_path = request.output_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dalle_{timestamp}.png"
            output_path = Path.cwd() / "generated" / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download
        await download_file(url, output_path)
        
        return output_path

    async def _save_base64_image(self, request: GenerationRequest, b64_data: str) -> Path:
        """Save base64 image data."""
        # Determine output path
        if request.output_path:
            output_path = request.output_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dalle_{timestamp}.png"
            output_path = Path.cwd() / "generated" / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Decode and save
        image_data = base64.b64decode(b64_data)
        output_path.write_bytes(image_data)
        
        return output_path

    async def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for vision API."""
        path = Path(image_path)
        if not path.exists():
            raise GenerationError(f"Image not found: {image_path}")
        
        return base64.b64encode(path.read_bytes()).decode('utf-8')

    def get_default_model(self, generation_type: GenerationType) -> str:
        """Get default model for generation type."""
        if generation_type == GenerationType.IMAGE:
            return "dall-e-3"
        elif generation_type == GenerationType.TEXT:
            return "gpt-4o-mini"  # Cheapest vision model
        return super().get_default_model(generation_type)

    def get_models_for_type(self, generation_type: GenerationType) -> List[str]:
        """Get available models for a generation type."""
        models = []
        for name, info in self.MODELS.items():
            if info.get("type") == generation_type:
                models.append(name)
            elif generation_type == GenerationType.TEXT and "image_analysis" in info.get("capabilities", []):
                models.append(name)
        return models

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None