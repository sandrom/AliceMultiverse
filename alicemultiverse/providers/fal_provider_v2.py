"""fal.ai provider implementation using configuration loader."""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import aiohttp

from ..core.config_loader import get_config
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


class FalProvider(Provider):
    """Provider for fal.ai API integration with configuration support."""

    # Load configuration
    _config = get_config()
    
    # Get base URL from config or environment
    BASE_URL = _config.get("providers.fal.base_url", "https://fal.run")
    
    # Get timeout and polling settings from config
    TIMEOUT = _config.get("providers.fal.timeout", 300)
    POLL_INTERVAL = _config.get("providers.fal.poll_interval", 5)
    MAX_POLL_ATTEMPTS = _config.get("providers.fal.max_poll_attempts", 60)
    
    # Model endpoints (could also be moved to config)
    MODELS = {
        # FLUX models
        "flux-pro": "fal-ai/flux-pro",
        "flux-pro-v1.1": "fal-ai/flux-pro/v1.1",
        "flux-kontext-pro": "fal-ai/flux-pro/kontext",
        "flux-kontext-pro-multi": "fal-ai/flux-pro/kontext/multi",
        "flux-kontext-max": "fal-ai/flux-pro/kontext/max",
        "flux-kontext-max-multi": "fal-ai/flux-pro/kontext/max/multi",
        "flux-dev": "fal-ai/flux/dev",
        "flux-dev-image-to-image": "fal-ai/flux/dev/image-to-image",
        "flux-schnell": "fal-ai/flux/schnell",
        "flux-realism": "fal-ai/flux-realism",
        "flux-lora": "fal-ai/flux-lora",
        
        # Other models...
        "stable-diffusion-v3-medium": "fal-ai/stable-diffusion-v3-medium",
        "recraft-v3": "fal-ai/recraft-v3",
        "aura-flow": "fal-ai/aura-flow",
        
        # Video models
        "stable-video": "fal-ai/stable-video",
        "haiper-video": "fal-ai/haiper-video",
        "lumav1.5": "fal-ai/lumav1.5",
        "veo-3": "fal-ai/veo3",
        
        # Audio models
        "mmaudio": "fal-ai/mmaudio",
        
        # 3D models
        "stable-fast-3d": "fal-ai/stable-fast-3d",
        "triposr": "fal-ai/triposr",
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize fal.ai provider with configuration support."""
        api_key = api_key or os.getenv("FAL_KEY")
        if not api_key:
            raise ValueError("fal.ai API key is required. Set FAL_KEY environment variable.")
        
        super().__init__(api_key=api_key, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Override config with instance-specific settings
        if "timeout" in kwargs:
            self.TIMEOUT = kwargs["timeout"]
        if "poll_interval" in kwargs:
            self.POLL_INTERVAL = kwargs["poll_interval"]

    async def _wait_for_result(
        self,
        request_id: str,
        endpoint: str,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Poll for async job completion using configuration."""
        session = await self._get_session()
        status_url = f"{self.BASE_URL}/{endpoint}/requests/{request_id}/status"
        result_url = f"{self.BASE_URL}/{endpoint}/requests/{request_id}"
        
        for attempt in range(self.MAX_POLL_ATTEMPTS):
            try:
                # Check status
                async with session.get(status_url, headers=headers) as response:
                    if response.status != 200:
                        continue
                    
                    status_data = await response.json()
                    status = status_data.get("status")
                    
                    if status == "COMPLETED":
                        # Get final result
                        async with session.get(result_url, headers=headers) as result_response:
                            if result_response.status == 200:
                                return await result_response.json()
                    elif status == "FAILED":
                        error_msg = status_data.get("error", "Generation failed")
                        raise GenerationError(f"fal.ai generation failed: {error_msg}")
                    
            except aiohttp.ClientError:
                pass  # Continue polling
            
            # Wait before next poll
            await asyncio.sleep(self.POLL_INTERVAL)
        
        raise GenerationError(
            f"Generation timed out after {self.MAX_POLL_ATTEMPTS * self.POLL_INTERVAL} seconds"
        )

    # ... rest of the implementation remains similar but uses config values ...