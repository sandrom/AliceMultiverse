"""Anthropic provider implementation for Claude vision and analysis."""

import asyncio
import base64
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from ..core.file_operations import save_text_file
from .base_provider import BaseProvider, GenerationError, RateLimitError, AuthenticationError
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic API integration (Claude vision and analysis)."""
    
    BASE_URL = "https://api.anthropic.com/v1"
    
    # Model configurations
    MODELS = {
        "claude-3-opus-20240229": {
            "endpoint": "/messages",
            "type": GenerationType.TEXT,
            "max_tokens": 4096,
            "vision": True,
            "context_window": 200000,
        },
        "claude-3-sonnet-20240229": {
            "endpoint": "/messages",
            "type": GenerationType.TEXT,
            "max_tokens": 4096,
            "vision": True,
            "context_window": 200000,
        },
        "claude-3-haiku-20240307": {
            "endpoint": "/messages", 
            "type": GenerationType.TEXT,
            "max_tokens": 4096,
            "vision": True,
            "context_window": 200000,
        },
        "claude-3-5-sonnet-20241022": {
            "endpoint": "/messages",
            "type": GenerationType.TEXT,
            "max_tokens": 8192,
            "vision": True,
            "context_window": 200000,
        },
    }
    
    # Pricing per 1M tokens (input/output)
    PRICING = {
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    }
    
    def __init__(self, api_key: Optional[str] = None, event_bus: Optional[Any] = None):
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            event_bus: Deprecated parameter, kept for compatibility
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")
            
        super().__init__(api_key)
        self._session = None
        
    @property
    def name(self) -> str:
        """Provider name."""
        return "anthropic"
        
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.TEXT],
            models=list(self.MODELS.keys()),
            features=[
                "vision",
                "image_analysis",
                "quality_assessment",
                "defect_detection",
                "long_context",
            ],
            rate_limits={
                "requests_per_minute": 50,
                "tokens_per_minute": 40000,
            },
            pricing={
                model: f"${pricing['input']}/{pricing['output']} per 1M tokens"
                for model, pricing in self.PRICING.items()
            }
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def check_status(self) -> ProviderStatus:
        """Check Anthropic API status."""
        try:
            session = await self._get_session()
            # Anthropic doesn't have a status endpoint, so we'll do a minimal request
            test_request = {
                "model": "claude-3-haiku-20240307",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
            }
            
            async with session.post(f"{self.BASE_URL}/messages", json=test_request) as response:
                if response.status == 200:
                    self._status = ProviderStatus.AVAILABLE
                elif response.status == 401:
                    self._status = ProviderStatus.UNAVAILABLE
                    logger.error("Anthropic authentication failed")
                else:
                    self._status = ProviderStatus.DEGRADED
                    
        except Exception as e:
            logger.error(f"Failed to check Anthropic status: {e}")
            self._status = ProviderStatus.UNKNOWN
            
        self._last_check = datetime.now()
        return self._status

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content using Anthropic Claude.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        start_time = datetime.now()
        
        try:
            # Validate request
            await self.validate_request(request)
            
            # Publish start event
            self._publish_started(request)
            
            # Determine model
            model = request.model or self.get_default_model(request.generation_type)
            
            # Only TEXT generation is supported
            if request.generation_type != GenerationType.TEXT:
                raise GenerationError(f"Anthropic only supports TEXT generation, not {request.generation_type}")
            
            # Analyze image or generate text
            if request.reference_assets and len(request.reference_assets) > 0:
                result = await self._analyze_image(request, model)
            else:
                result = await self._generate_text(request, model)
            
            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds()
            result.generation_time = generation_time
            
            # Publish success event
            self._publish_success(request, result)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Anthropic generation failed: {error_msg}")
            
            # Publish failure
            self._publish_failure(request, error_msg)
            
            # Return error result
            return GenerationResult(
                success=False,
                error=error_msg,
                provider=self.name,
                model=request.model
            )

    async def _analyze_image(self, request: GenerationRequest, model: str) -> GenerationResult:
        """Analyze image using Claude vision."""
        if not request.reference_assets:
            raise GenerationError("Image analysis requires reference_assets")
        
        # Build vision request
        content = [{"type": "text", "text": request.prompt}]
        
        # Add images
        for asset_path in request.reference_assets:
            image_data = await self._encode_image(asset_path)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self._get_media_type(asset_path),
                    "data": image_data,
                }
            })
        
        messages = [{"role": "user", "content": content}]
        
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": request.parameters.get("max_tokens", 1024) if request.parameters else 1024,
        }
        
        # Add temperature if specified
        if request.parameters and "temperature" in request.parameters:
            params["temperature"] = request.parameters["temperature"]
        
        # Call API
        session = await self._get_session()
        
        async with session.post(f"{self.BASE_URL}/messages", json=params) as response:
            if response.status == 429:
                raise RateLimitError("Anthropic rate limit exceeded")
            elif response.status == 401:
                raise AuthenticationError("Invalid Anthropic API key")
            elif response.status != 200:
                error_data = await response.json()
                raise GenerationError(f"Anthropic API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            data = await response.json()
        
        # Extract response
        analysis = data["content"][0]["text"]
        input_tokens = data["usage"]["input_tokens"]
        output_tokens = data["usage"]["output_tokens"]
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Save analysis if output path specified
        file_path = None
        if request.output_path:
            file_path = request.output_path
            await save_text_file(file_path, analysis)
        
        return GenerationResult(
            success=True,
            file_path=file_path,
            cost=total_cost,
            provider=self.name,
            model=model,
            metadata={
                "analysis": analysis,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "prompt": request.prompt,
            }
        )

    async def _generate_text(self, request: GenerationRequest, model: str) -> GenerationResult:
        """Generate text using Claude."""
        messages = [{"role": "user", "content": request.prompt}]
        
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": request.parameters.get("max_tokens", 1024) if request.parameters else 1024,
        }
        
        # Add optional parameters
        if request.parameters:
            if "temperature" in request.parameters:
                params["temperature"] = request.parameters["temperature"]
            if "system" in request.parameters:
                params["system"] = request.parameters["system"]
        
        # Call API
        session = await self._get_session()
        
        async with session.post(f"{self.BASE_URL}/messages", json=params) as response:
            if response.status == 429:
                raise RateLimitError("Anthropic rate limit exceeded")
            elif response.status == 401:
                raise AuthenticationError("Invalid Anthropic API key")
            elif response.status != 200:
                error_data = await response.json()
                raise GenerationError(f"Anthropic API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            data = await response.json()
        
        # Extract response
        text = data["content"][0]["text"]
        input_tokens = data["usage"]["input_tokens"]
        output_tokens = data["usage"]["output_tokens"]
        
        # Calculate cost
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Save text if output path specified
        file_path = None
        if request.output_path:
            file_path = request.output_path
            await save_text_file(file_path, text)
        
        return GenerationResult(
            success=True,
            file_path=file_path,
            cost=total_cost,
            provider=self.name,
            model=model,
            metadata={
                "text": text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "prompt": request.prompt,
            }
        )

    async def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        path = Path(image_path)
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_media_type(self, image_path: str) -> str:
        """Get media type from file extension."""
        ext = Path(image_path).suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(ext, "image/jpeg")

    def get_default_model(self, generation_type: GenerationType) -> str:
        """Get default model for generation type."""
        if generation_type == GenerationType.TEXT:
            return "claude-3-haiku-20240307"  # Cheapest for basic tasks
        return None

    def get_models_for_type(self, generation_type: GenerationType) -> List[str]:
        """Get available models for a generation type."""
        return [
            model for model, config in self.MODELS.items()
            if config["type"] == generation_type
        ]

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None