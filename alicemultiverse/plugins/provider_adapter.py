"""Adapter to integrate plugin providers with the existing provider system."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..providers.provider import Provider
from ..providers.types import GenerationRequest, GenerationResult, GenerationType
from .base import ProviderPlugin

logger = logging.getLogger(__name__)


class PluginProviderAdapter(Provider):
    """Adapts a ProviderPlugin to work with the existing Provider interface."""
    
    def __init__(self, plugin: ProviderPlugin):
        """
        Initialize adapter with a provider plugin.
        
        Args:
            plugin: The provider plugin to adapt
        """
        super().__init__()
        self.plugin = plugin
        self.name = plugin.metadata.name
        self.version = plugin.metadata.version
    
    async def initialize(self):
        """Initialize the provider plugin."""
        success = await self.plugin.initialize()
        if not success:
            raise RuntimeError(f"Failed to initialize plugin provider: {self.name}")
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate content using the plugin provider.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        # Convert GenerationRequest to plugin format
        plugin_request = {
            "prompt": request.prompt,
            "model": request.model,
            "parameters": request.parameters or {},
            "generation_type": request.generation_type.value,
            "output_path": str(request.output_path) if request.output_path else None
        }
        
        # Call plugin generate
        try:
            result = await self.plugin.generate(plugin_request)
            
            if result.get("success"):
                # Convert plugin result to GenerationResult
                file_path = result.get("file_path")
                if isinstance(file_path, str):
                    file_path = Path(file_path)
                
                return GenerationResult(
                    success=True,
                    file_path=file_path,
                    cost=result.get("cost", 0.0),
                    metadata=result.get("metadata", {}),
                    provider=self.name,
                    model=request.model
                )
            else:
                return GenerationResult(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    provider=self.name,
                    model=request.model
                )
                
        except Exception as e:
            logger.error(f"Plugin provider error: {e}")
            return GenerationResult(
                success=False,
                error=str(e),
                provider=self.name,
                model=request.model
            )
    
    async def cleanup(self):
        """Clean up plugin resources."""
        await self.plugin.cleanup()
    
    def get_supported_models(self) -> List[str]:
        """Get supported models from plugin."""
        return self.plugin.get_supported_models()
    
    def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate cost using plugin."""
        plugin_request = {
            "model": request.model,
            "parameters": request.parameters or {}
        }
        return self.plugin.estimate_cost(plugin_request)
    
    def supports_generation_type(self, generation_type: GenerationType) -> bool:
        """Check if plugin supports generation type."""
        # Plugin should specify this in metadata or config
        supported_types = self.plugin.config.get("supported_types", ["image"])
        type_mapping = {
            GenerationType.IMAGE: "image",
            GenerationType.VIDEO: "video",
            GenerationType.AUDIO: "audio",
            GenerationType.TEXT: "text"
        }
        return type_mapping.get(generation_type, "image") in supported_types