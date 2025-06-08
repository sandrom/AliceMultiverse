"""Simplified provider registry for managing AI generation providers."""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Type

from .provider import Provider
from .types import GenerationType
from .health_monitor import health_monitor

logger = logging.getLogger(__name__)


@dataclass
class ProviderStats:
    """Statistics for a provider."""
    total_cost: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_generation_time: float = 0.0
    last_used: Optional[datetime] = None


class ProviderRegistry:
    """Simplified registry for managing generation providers."""
    
    def __init__(self, budget_limit: Optional[float] = None):
        """Initialize provider registry.
        
        Args:
            budget_limit: Global budget limit across all providers
        """
        self.budget_limit = budget_limit
        
        # Provider management
        self._provider_classes: Dict[str, Type[Provider]] = {}
        self._instances: Dict[str, Provider] = {}
        self._api_keys: Dict[str, str] = {}
        
        # Cost tracking
        self.total_cost = 0.0
        self._provider_stats: Dict[str, ProviderStats] = {}
        
        # Health monitoring task
        self._health_monitoring_task: Optional[asyncio.Task] = None
        
        # Register built-in providers
        self._register_builtin_providers()
    
    def _register_builtin_providers(self):
        """Register built-in provider classes."""
        # Import here to avoid circular imports
        from .fal_provider import FalProvider
        from .anthropic_provider import AnthropicProvider
        from .openai_provider import OpenAIProvider
        from .bfl_provider import BFLProvider
        from .kling_provider import KlingProvider
        from .hedra_provider import HedraProvider
        from .freepik_provider import FreepikProvider
        from .firefly_provider import FireflyProvider
        from .google_ai_provider import GoogleAIProvider
        from .ideogram_provider import IdeogramProvider
        from .leonardo_provider import LeonardoProvider
        from .elevenlabs_provider import ElevenLabsProvider
        from .midjourney_provider import MidjourneyProvider
        from .runway_provider import RunwayProvider
        from .pika_provider import PikaProvider
        from .luma_provider import LumaProvider
        from .minimax_provider import MiniMaxProvider
        
        self.register_provider("fal", FalProvider)
        self.register_provider("fal.ai", FalProvider)  # Alias
        self.register_provider("anthropic", AnthropicProvider)
        self.register_provider("claude", AnthropicProvider)  # Alias
        self.register_provider("openai", OpenAIProvider)
        self.register_provider("bfl", BFLProvider)
        self.register_provider("bfl.ai", BFLProvider)  # Alias
        self.register_provider("black-forest-labs", BFLProvider)  # Alias
        self.register_provider("kling", KlingProvider)
        self.register_provider("klingai", KlingProvider)  # Alias
        self.register_provider("kling-official", KlingProvider)  # Alias
        self.register_provider("hedra", HedraProvider)
        self.register_provider("hedra-character", HedraProvider)  # Alias
        self.register_provider("freepik", FreepikProvider)
        self.register_provider("magnific", FreepikProvider)  # Alias for Magnific users
        self.register_provider("firefly", FireflyProvider)
        self.register_provider("adobe", FireflyProvider)  # Alias
        self.register_provider("adobe-firefly", FireflyProvider)  # Alias
        self.register_provider("google", GoogleAIProvider)
        self.register_provider("google-ai", GoogleAIProvider)  # Alias
        self.register_provider("gemini", GoogleAIProvider)  # Alias
        self.register_provider("imagen", GoogleAIProvider)  # Alias
        self.register_provider("veo", GoogleAIProvider)  # Alias
        self.register_provider("ideogram", IdeogramProvider)
        self.register_provider("ideogram-ai", IdeogramProvider)  # Alias
        self.register_provider("leonardo", LeonardoProvider)
        self.register_provider("leonardo-ai", LeonardoProvider)  # Alias
        self.register_provider("leonardo.ai", LeonardoProvider)  # Alias
        self.register_provider("elevenlabs", ElevenLabsProvider)
        self.register_provider("eleven-labs", ElevenLabsProvider)  # Alias
        self.register_provider("11labs", ElevenLabsProvider)  # Alias
        self.register_provider("midjourney", MidjourneyProvider)
        self.register_provider("mj", MidjourneyProvider)  # Alias
        self.register_provider("runway", RunwayProvider)
        self.register_provider("runway-gen3", RunwayProvider)  # Alias
        self.register_provider("gen3-alpha", RunwayProvider)  # Alias
        self.register_provider("pika", PikaProvider)
        self.register_provider("pika-labs", PikaProvider)  # Alias
        self.register_provider("pika-2.1", PikaProvider)  # Alias
        self.register_provider("luma", LumaProvider)
        self.register_provider("luma-ai", LumaProvider)  # Alias
        self.register_provider("dream-machine", LumaProvider)  # Alias
        self.register_provider("minimax", MiniMaxProvider)
        self.register_provider("hailuo", MiniMaxProvider)  # Alias
        self.register_provider("minimax-hailuo", MiniMaxProvider)  # Alias
    
    def register_provider(self, name: str, provider_class: Type[Provider]):
        """Register a provider class.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        self._provider_classes[name.lower()] = provider_class
        logger.info(f"Registered provider: {name}")
    
    def register_api_key(self, provider_name: str, api_key: str):
        """Register an API key for a provider.
        
        Args:
            provider_name: Provider name
            api_key: API key
        """
        self._api_keys[provider_name.lower()] = api_key
    
    def get_provider(self, name: str) -> Provider:
        """Get a provider instance by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider not found
        """
        name_lower = name.lower()
        
        # Return existing instance if available
        if name_lower in self._instances:
            return self._instances[name_lower]
        
        # Create new instance
        if name_lower not in self._provider_classes:
            available = ", ".join(self._provider_classes.keys())
            raise ValueError(
                f"Unknown provider '{name}'. Available providers: {available}"
            )
        
        # Get provider class
        provider_class = self._provider_classes[name_lower]
        
        # Get API key if registered
        api_key = self._api_keys.get(name_lower)
        
        # Try environment variable if not registered
        if not api_key:
            env_vars = {
                "fal": "FAL_KEY",
                "fal.ai": "FAL_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "claude": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
                "hedra": "HEDRA_API_KEY",
                "hedra-character": "HEDRA_API_KEY",
                "freepik": "FREEPIK_API_KEY",
                "magnific": "FREEPIK_API_KEY",
                "firefly": "ADOBE_CLIENT_ID",
                "adobe": "ADOBE_CLIENT_ID",
                "adobe-firefly": "ADOBE_CLIENT_ID",
                "google": "GOOGLE_AI_API_KEY",
                "google-ai": "GOOGLE_AI_API_KEY",
                "gemini": "GEMINI_API_KEY",
                "imagen": "GOOGLE_AI_API_KEY",
                "veo": "GOOGLE_AI_API_KEY",
                "ideogram": "IDEOGRAM_API_KEY",
                "ideogram-ai": "IDEOGRAM_API_KEY",
                "leonardo": "LEONARDO_API_KEY",
                "leonardo-ai": "LEONARDO_API_KEY",
                "leonardo.ai": "LEONARDO_API_KEY",
                "elevenlabs": "ELEVENLABS_API_KEY",
                "eleven-labs": "ELEVENLABS_API_KEY",
                "11labs": "ELEVENLABS_API_KEY",
                "midjourney": "USEAPI_API_KEY",  # Default to UseAPI
                "mj": "USEAPI_API_KEY",
                "runway": "RUNWAY_API_KEY",
                "runway-gen3": "RUNWAY_API_KEY",
                "gen3-alpha": "RUNWAY_API_KEY",
                "pika": "PIKA_API_KEY",
                "pika-labs": "PIKA_API_KEY",
                "pika-2.1": "PIKA_API_KEY",
                "luma": "LUMA_API_KEY",
                "luma-ai": "LUMA_API_KEY",
                "dream-machine": "LUMA_API_KEY",
                "minimax": "MINIMAX_API_KEY",
                "hailuo": "MINIMAX_API_KEY",
                "minimax-hailuo": "MINIMAX_API_KEY",
            }
            if name_lower in env_vars:
                api_key = os.getenv(env_vars[name_lower])
        
        # Create instance
        instance = provider_class(api_key=api_key)
        self._instances[name_lower] = instance
        
        # Initialize stats
        if name_lower not in self._provider_stats:
            self._provider_stats[name_lower] = ProviderStats()
        
        logger.info(f"Initialized {name} provider")
        return instance
    
    async def get_provider_async(self, name: str) -> Provider:
        """Get a provider instance by name (async version).
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance
        """
        # For now, just wrap the sync version
        # In future, providers might need async initialization
        return self.get_provider(name)
    
    def get_providers_for_type(self, generation_type: GenerationType) -> List[str]:
        """Get providers that support a generation type.
        
        Args:
            generation_type: Type of generation
            
        Returns:
            List of provider names
        """
        providers = []
        
        for name, provider_class in self._provider_classes.items():
            # Create temporary instance to check capabilities
            instance = provider_class()
            if generation_type in instance.capabilities.generation_types:
                providers.append(name)
        
        return providers
    
    def list_providers(self) -> List[str]:
        """List all registered providers.
        
        Returns:
            List of provider names
        """
        return list(self._provider_classes.keys())
    
    def track_generation(self, provider_name: str, success: bool, cost: float = 0.0, generation_time: float = 0.0):
        """Track generation statistics.
        
        Args:
            provider_name: Provider name
            success: Whether generation succeeded
            cost: Generation cost
            generation_time: Time taken for generation
        """
        stats = self._provider_stats.get(provider_name.lower(), ProviderStats())
        
        stats.total_requests += 1
        stats.last_used = datetime.now(UTC)
        
        if success:
            stats.successful_requests += 1
            stats.total_cost += cost
            self.total_cost += cost
            
            # Update average generation time
            if stats.successful_requests > 0:
                stats.average_generation_time = (
                    (stats.average_generation_time * (stats.successful_requests - 1) + generation_time) 
                    / stats.successful_requests
                )
        else:
            stats.failed_requests += 1
        
        self._provider_stats[provider_name.lower()] = stats
    
    def check_budget(self, estimated_cost: float) -> bool:
        """Check if estimated cost is within budget.
        
        Args:
            estimated_cost: Estimated cost
            
        Returns:
            True if within budget
        """
        if self.budget_limit is None:
            return True
        
        return (self.total_cost + estimated_cost) <= self.budget_limit
    
    def get_stats(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for providers.
        
        Args:
            provider_name: Specific provider or None for all
            
        Returns:
            Statistics dictionary
        """
        if provider_name:
            stats = self._provider_stats.get(provider_name.lower(), ProviderStats())
            
            # Include health status in stats
            health_status = health_monitor.get_status(provider_name)
            health_metrics = health_monitor.get_metrics(provider_name)
            
            return {
                "provider": provider_name,
                "total_cost": stats.total_cost,
                "total_requests": stats.total_requests,
                "success_rate": stats.successful_requests / stats.total_requests if stats.total_requests > 0 else 0,
                "average_cost": stats.total_cost / stats.successful_requests if stats.successful_requests > 0 else 0,
                "average_time": stats.average_generation_time,
                "last_used": stats.last_used.isoformat() if stats.last_used else None,
                "health_status": health_status.value,
                "health_metrics": {
                    "consecutive_failures": health_metrics.consecutive_failures if health_metrics else 0,
                    "is_healthy": health_metrics.is_healthy if health_metrics else True
                }
            }
        else:
            return {
                "total_cost": self.total_cost,
                "budget_limit": self.budget_limit,
                "budget_remaining": (self.budget_limit - self.total_cost) if self.budget_limit else None,
                "provider_stats": {
                    name: self.get_stats(name) for name in self._provider_stats
                }
            }
    
    async def start_health_monitoring(self):
        """Start health monitoring for all providers."""
        if self._health_monitoring_task and not self._health_monitoring_task.done():
            logger.warning("Health monitoring already running")
            return
        
        # Get all provider instances
        providers = []
        for name in self._provider_classes:
            try:
                provider = self.get_provider(name)
                providers.append(provider)
            except Exception as e:
                logger.error(f"Failed to initialize {name} for health monitoring: {e}")
        
        # Start monitoring
        await health_monitor.start_monitoring(providers)
        logger.info(f"Started health monitoring for {len(providers)} providers")
    
    async def stop_health_monitoring(self):
        """Stop health monitoring."""
        await health_monitor.stop_monitoring()
    
    def get_health_statuses(self) -> Dict[str, str]:
        """Get health status for all providers.
        
        Returns:
            Dict of provider name to health status
        """
        return {
            name: health_monitor.get_status(name).value
            for name in self._provider_classes
        }


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """Get global provider registry.
    
    Returns:
        Provider registry
    """
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def get_provider(name: str, api_key: Optional[str] = None) -> Provider:
    """Convenience function to get a provider.
    
    Args:
        name: Provider name
        api_key: Optional API key to register
        
    Returns:
        Provider instance
    """
    registry = get_registry()
    
    if api_key:
        registry.register_api_key(name, api_key)
    
    return registry.get_provider(name)


async def get_provider_async(name: str, api_key: Optional[str] = None) -> Provider:
    """Async version of get_provider.
    
    Args:
        name: Provider name
        api_key: Optional API key to register
        
    Returns:
        Provider instance
    """
    registry = get_registry()
    
    if api_key:
        registry.register_api_key(name, api_key)
    
    return await registry.get_provider_async(name)