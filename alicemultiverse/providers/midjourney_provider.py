"""Midjourney provider using proxy API services.

Since Midjourney doesn't have an official API, this provider uses
third-party proxy services that interface with Discord.
"""

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

from ..core.structured_logging import get_logger
from ..events import publish_event_sync
from .provider import Provider, GenerationError, ProviderError
from .types import (
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = get_logger(__name__)


class MidjourneyProvider(Provider):
    """Provider for Midjourney image generation via proxy API.
    
    This provider supports multiple proxy services:
    - UseAPI (recommended)
    - GoAPI
    - Custom proxy endpoints
    """
    
    # Supported proxy services with their base URLs
    PROXY_SERVICES = {
        "useapi": "https://api.useapi.net/v2/midjourney",
        "goapi": "https://api.goapi.ai/v1/midjourney",
        "custom": None,  # User provides full URL
    }
    
    # Midjourney model versions
    MODELS = ["v6.1", "v6", "v5.2", "v5.1", "v5", "v4", "niji-6", "niji-5"]
    
    # Default parameters
    DEFAULT_MODEL = "v6.1"
    POLL_INTERVAL = 5  # seconds
    MAX_POLL_TIME = 300  # 5 minutes max wait
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        proxy_service: str = "useapi",
        proxy_url: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ):
        """Initialize Midjourney provider.
        
        Args:
            api_key: API key for the proxy service
            proxy_service: Which proxy service to use ("useapi", "goapi", "custom")
            proxy_url: Custom proxy URL (required if proxy_service is "custom")
            webhook_url: Optional webhook for async notifications
        """
        super().__init__(api_key)
        
        # Configure proxy service
        self.proxy_service = proxy_service
        if proxy_service == "custom":
            if not proxy_url:
                raise ValueError("proxy_url required for custom proxy service")
            self.base_url = proxy_url
        else:
            self.base_url = self.PROXY_SERVICES.get(proxy_service)
            if not self.base_url:
                raise ValueError(f"Unknown proxy service: {proxy_service}")
        
        self.webhook_url = webhook_url
        
        # Get API key from env if not provided
        if not self.api_key:
            env_key = f"{proxy_service.upper()}_API_KEY"
            self.api_key = os.getenv(env_key)
            if not self.api_key:
                raise ValueError(f"API key not provided and {env_key} not set")
        
        # Configure headers based on proxy service
        self.headers = self._configure_headers()
        
    def _configure_headers(self) -> Dict[str, str]:
        """Configure headers based on proxy service."""
        if self.proxy_service == "useapi":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        elif self.proxy_service == "goapi":
            return {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            }
        else:
            # Custom proxy - assume bearer token
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "midjourney"
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=self.MODELS,
            max_resolution={"width": 2048, "height": 2048},
            features=["image_to_image", "variations", "upscaling"],
            formats=["png", "jpg", "webp"],
            supports_batch=False,
            pricing={
                "v6.1": 0.30,  # Estimated per image
                "v6": 0.30,
                "v5.2": 0.25,
                "v5.1": 0.25,
                "v5": 0.25,
                "v4": 0.20,
                "niji-6": 0.30,
                "niji-5": 0.25,
            }
        )
    
    async def check_status(self) -> ProviderStatus:
        """Check if the proxy service is available."""
        try:
            async with aiohttp.ClientSession() as session:
                # Different health check endpoints per service
                if self.proxy_service == "useapi":
                    health_url = f"{self.base_url}/status"
                else:
                    health_url = self.base_url
                
                async with session.get(
                    health_url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self._status = ProviderStatus.READY
                    else:
                        self._status = ProviderStatus.ERROR
                        
        except Exception as e:
            logger.error(f"Failed to check Midjourney proxy status: {e}")
            self._status = ProviderStatus.ERROR
            
        self._last_check = datetime.now()
        return self._status
    
    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate image using Midjourney via proxy API."""
        start_time = time.time()
        
        try:
            # Parse prompt for Midjourney parameters
            prompt_data = self._parse_prompt(request.prompt)
            
            # Build generation request
            generation_request = self._build_generation_request(
                prompt_data,
                request
            )
            
            # Submit generation job
            job_id = await self._submit_generation(generation_request)
            logger.info(f"Submitted Midjourney job: {job_id}")
            
            # Wait for completion
            result_data = await self._wait_for_completion(job_id)
            
            # Download the generated image
            image_url = result_data.get("imageUrl") or result_data.get("url")
            if not image_url:
                raise GenerationError("No image URL in response")
            
            # Save image
            output_path = await self._download_image(image_url, job_id)
            
            # Calculate cost
            model = prompt_data.get("version", self.DEFAULT_MODEL)
            cost = self.capabilities.pricing.get(model, 0.30)
            
            return GenerationResult(
                success=True,
                file_path=output_path,
                model=model,
                cost=cost,
                generation_time=time.time() - start_time,
                metadata={
                    "job_id": job_id,
                    "seed": result_data.get("seed"),
                    "prompt": prompt_data["prompt"],
                    "parameters": prompt_data.get("parameters", {}),
                    "proxy_service": self.proxy_service,
                }
            )
            
        except Exception as e:
            logger.error(f"Midjourney generation failed: {e}")
            raise GenerationError(f"Generation failed: {str(e)}")
    
    def _parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parse Midjourney prompt with parameters.
        
        Midjourney uses special syntax like:
        - --v 6 (version)
        - --ar 16:9 (aspect ratio)
        - --q 2 (quality)
        - --s 750 (stylize)
        - --c 50 (chaos)
        """
        import re
        
        # Extract base prompt (everything before --)
        base_match = re.match(r"^(.*?)(?:\s*--|\s*$)", prompt)
        base_prompt = base_match.group(1).strip() if base_match else prompt
        
        # Extract parameters
        params = {}
        
        # Version
        version_match = re.search(r"--v\s+(\S+)", prompt)
        if version_match:
            version = version_match.group(1)
            # Normalize version format
            if version in ["6.1", "6", "5.2", "5.1", "5", "4"]:
                params["version"] = f"v{version}"
            else:
                params["version"] = version
        else:
            params["version"] = self.DEFAULT_MODEL
        
        # Aspect ratio
        ar_match = re.search(r"--ar\s+(\d+):(\d+)", prompt)
        if ar_match:
            params["aspect_ratio"] = f"{ar_match.group(1)}:{ar_match.group(2)}"
        
        # Quality
        q_match = re.search(r"--q\s+(\d+(?:\.\d+)?)", prompt)
        if q_match:
            params["quality"] = float(q_match.group(1))
        
        # Stylize
        s_match = re.search(r"--s\s+(\d+)", prompt)
        if s_match:
            params["stylize"] = int(s_match.group(1))
        
        # Chaos
        c_match = re.search(r"--c\s+(\d+)", prompt)
        if c_match:
            params["chaos"] = int(c_match.group(1))
        
        # No (negative)
        no_match = re.search(r"--no\s+([^-]+)", prompt)
        if no_match:
            params["no"] = no_match.group(1).strip()
        
        return {
            "prompt": base_prompt,
            "parameters": params,
            "version": params.get("version", self.DEFAULT_MODEL),
            "original_prompt": prompt,
        }
    
    def _build_generation_request(
        self,
        prompt_data: Dict[str, Any],
        request: GenerationRequest
    ) -> Dict[str, Any]:
        """Build generation request for proxy API."""
        params = prompt_data["parameters"]
        
        # Base request
        api_request = {
            "prompt": prompt_data["original_prompt"],  # Use full prompt with params
        }
        
        # Add webhook if configured
        if self.webhook_url:
            api_request["webhook"] = self.webhook_url
        
        # Service-specific formatting
        if self.proxy_service == "useapi":
            # UseAPI specific format
            if request.reference_assets and request.reference_assets[0]:
                api_request["image_url"] = request.reference_assets[0]
            
        elif self.proxy_service == "goapi":
            # GoAPI specific format
            api_request["model"] = params.get("version", self.DEFAULT_MODEL)
            if request.reference_assets and request.reference_assets[0]:
                api_request["init_image"] = request.reference_assets[0]
        
        return api_request
    
    async def _submit_generation(self, generation_request: Dict[str, Any]) -> str:
        """Submit generation job to proxy API."""
        async with aiohttp.ClientSession() as session:
            endpoint = f"{self.base_url}/imagine" if self.proxy_service == "useapi" else self.base_url
            
            async with session.post(
                endpoint,
                json=generation_request,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status not in [200, 201, 202]:
                    error_text = await response.text()
                    raise ProviderError(f"API error {response.status}: {error_text}")
                
                result = await response.json()
                
                # Extract job ID based on service
                if self.proxy_service == "useapi":
                    return result.get("task_id") or result.get("id")
                elif self.proxy_service == "goapi":
                    return result.get("job_id") or result.get("id")
                else:
                    # Try common fields
                    return result.get("id") or result.get("job_id") or result.get("task_id")
    
    async def _wait_for_completion(self, job_id: str) -> Dict[str, Any]:
        """Poll for job completion."""
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            while True:
                # Check timeout
                if time.time() - start_time > self.MAX_POLL_TIME:
                    raise GenerationError("Generation timed out")
                
                # Get status endpoint
                if self.proxy_service == "useapi":
                    status_url = f"{self.base_url}/task/{job_id}"
                else:
                    status_url = f"{self.base_url}/status/{job_id}"
                
                # Check status
                async with session.get(
                    status_url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Status check failed: {response.status}")
                        await asyncio.sleep(self.POLL_INTERVAL)
                        continue
                    
                    result = await response.json()
                    
                    # Check completion based on service
                    if self.proxy_service == "useapi":
                        status = result.get("status")
                        if status == "completed":
                            return result
                        elif status == "failed":
                            raise GenerationError(f"Generation failed: {result.get('error')}")
                    else:
                        # Generic status check
                        if result.get("status") in ["completed", "success", "done"]:
                            return result
                        elif result.get("status") in ["failed", "error"]:
                            raise GenerationError(f"Generation failed: {result.get('error')}")
                
                # Wait before next poll
                await asyncio.sleep(self.POLL_INTERVAL)
    
    async def _download_image(self, image_url: str, job_id: str) -> Path:
        """Download generated image."""
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise GenerationError(f"Failed to download image: {response.status}")
                
                # Create output directory
                output_dir = Path("output/midjourney") / datetime.now().strftime("%Y%m%d")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Determine file extension
                content_type = response.headers.get("content-type", "image/png")
                ext = "png"
                if "jpeg" in content_type or "jpg" in content_type:
                    ext = "jpg"
                elif "webp" in content_type:
                    ext = "webp"
                
                # Save file
                output_path = output_dir / f"{job_id}.{ext}"
                with open(output_path, "wb") as f:
                    f.write(await response.read())
                
                return output_path
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return {
            "name": model,
            "description": f"Midjourney {model}",
            "cost_per_generation": self.capabilities.pricing.get(model, 0.30),
            "features": ["variations", "upscaling", "image_to_image"],
            "max_prompt_length": 2000,
        }