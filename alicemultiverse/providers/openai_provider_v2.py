"""OpenAI provider implementation using enhanced base class."""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .base_provider import BaseProvider
from .provider import GenerationError
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
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
        """Initialize OpenAI provider."""
        super().__init__(name="openai", api_key=api_key, **kwargs)
        # Use base class helper to get API key
        self.api_key = self._get_api_key("OPENAI_API_KEY")

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE, GenerationType.TEXT],
            models=list(self.MODELS.keys()),
            max_images_per_request=1,
            supports_img2img=False,
            supports_video=False,
            supports_audio=False,
            supports_3d=False,
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get OpenAI-specific headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate(self, request: GenerationRequest) -> List[GenerationResult]:
        """Generate images using DALL-E.
        
        Args:
            request: Generation request
            
        Returns:
            List of generation results
        """
        # Validate model using base class helper
        model = self._validate_model(request.model, GenerationType.IMAGE)
        
        # Only DALL-E models support image generation
        if not model.startswith("dall-e"):
            raise ValueError(f"Model {model} does not support image generation")
        
        # Get model configuration
        model_config = self.MODELS[model]
        
        # Build parameters
        params = self._build_parameters(request, model, model_config)
        
        # Make API request using base class session management
        session = await self._ensure_session()
        url = f"{self.BASE_URL}{model_config['endpoint']}"
        
        try:
            async with session.post(url, json=params) as response:
                # Use base class error handling
                await self._handle_response_errors(response, f"DALL-E {model}")
                
                data = await response.json()
                
                # Process results
                results = []
                timestamp = datetime.now()
                
                for idx, image_data in enumerate(data.get("data", [])):
                    if "url" in image_data:
                        # Download image using base class helper
                        output_path = await self._download_result(
                            image_data["url"],
                            request.output_dir,
                            f"dalle_{model}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{idx}.png"
                        )
                    elif "b64_json" in image_data:
                        # Handle base64 response
                        output_path = await self._save_base64_image(
                            image_data["b64_json"],
                            request.output_dir,
                            f"dalle_{model}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{idx}.png"
                        )
                    else:
                        continue
                    
                    # Create result
                    result = GenerationResult(
                        file_path=output_path,
                        generation_type=GenerationType.IMAGE,
                        metadata={
                            "provider": self.name,
                            "model": model,
                            "prompt": request.prompt,
                            "parameters": params,
                            "revised_prompt": image_data.get("revised_prompt"),
                            "timestamp": timestamp.isoformat(),
                        },
                        cost=self._calculate_cost(model, params),
                    )
                    results.append(result)
                
                return results
                
        except aiohttp.ClientError as e:
            raise GenerationError(f"OpenAI API request failed: {str(e)}")

    def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate generation cost.
        
        Args:
            request: Generation request
            
        Returns:
            Estimated cost in USD
        """
        model = self._validate_model(request.model, GenerationType.IMAGE)
        
        if model.startswith("dall-e-3"):
            quality = request.parameters.get("quality", "standard")
            size = request.parameters.get("size", "1024x1024")
            return self.PRICING["dall-e-3"][quality].get(size, 0.08)
        elif model == "dall-e-2":
            size = request.parameters.get("size", "1024x1024")
            return self.PRICING["dall-e-2"].get(size, 0.02)
        else:
            # Text/vision models
            return self.PRICING.get(model, 0.01)

    def get_status(self) -> ProviderStatus:
        """Get provider status."""
        return ProviderStatus(
            is_available=bool(self.api_key),
            error_message=None if self.api_key else "API key not configured",
        )

    def get_default_model(self, generation_type: GenerationType) -> str:
        """Get default model for generation type."""
        if generation_type == GenerationType.IMAGE:
            return "dall-e-3"
        elif generation_type == GenerationType.TEXT:
            return "gpt-4o-mini"
        else:
            raise ValueError(f"OpenAI does not support {generation_type}")

    # ===== Private Helper Methods =====

    def _build_parameters(
        self,
        request: GenerationRequest,
        model: str,
        model_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build API parameters."""
        # Use base class helper to extract common params
        params = self._extract_common_params(request.parameters)
        
        # Add required fields
        params["prompt"] = request.prompt
        params["model"] = model
        params["n"] = params.get("num_images", 1)
        
        # Handle size parameter
        if "size" not in params:
            params["size"] = "1024x1024"
        
        # Validate size for model
        if params["size"] not in model_config.get("max_size", {params["size"]}):
            params["size"] = "1024x1024"  # Default to safe size
        
        # DALL-E 3 specific parameters
        if model == "dall-e-3":
            if "quality" in request.parameters:
                params["quality"] = request.parameters["quality"]
            if "style" in request.parameters:
                params["style"] = request.parameters["style"]
        
        # Handle response format
        params["response_format"] = request.parameters.get("response_format", "url")
        
        # Remove parameters not supported by API
        api_params = ["prompt", "model", "n", "size", "quality", "style", "response_format"]
        return {k: v for k, v in params.items() if k in api_params}

    def _calculate_cost(self, model: str, params: Dict[str, Any]) -> float:
        """Calculate actual cost for generation."""
        if model == "dall-e-3":
            quality = params.get("quality", "standard")
            size = params.get("size", "1024x1024")
            return self.PRICING["dall-e-3"][quality].get(size, 0.08)
        elif model == "dall-e-2":
            size = params.get("size", "1024x1024")
            return self.PRICING["dall-e-2"].get(size, 0.02)
        else:
            return self.PRICING.get(model, 0.01)

    async def _save_base64_image(
        self,
        base64_data: str,
        output_dir: Path,
        filename: str
    ) -> Path:
        """Save base64 encoded image to file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        # Decode and save
        image_data = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return output_path