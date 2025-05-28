"""Simplified provider registry for managing AI generation providers."""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Type

from .provider import Provider, BudgetExceededError
from .types import GenerationRequest, GenerationType

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
        
        # Register built-in providers
        self._register_builtin_providers()
    
    def _register_builtin_providers(self):
        """Register built-in provider classes."""
        # Import here to avoid circular imports
        from .fal_provider import FalProvider
        from .anthropic_provider import AnthropicProvider
        from .openai_provider import OpenAIProvider
        
        self.register_provider("fal", FalProvider)
        self.register_provider("fal.ai", FalProvider)  # Alias
        self.register_provider("anthropic", AnthropicProvider)
        self.register_provider("claude", AnthropicProvider)  # Alias
        self.register_provider("openai", OpenAIProvider)
    
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
            return {
                "provider": provider_name,
                "total_cost": stats.total_cost,
                "total_requests": stats.total_requests,
                "success_rate": stats.successful_requests / stats.total_requests if stats.total_requests > 0 else 0,
                "average_cost": stats.total_cost / stats.successful_requests if stats.successful_requests > 0 else 0,
                "average_time": stats.average_generation_time,
                "last_used": stats.last_used.isoformat() if stats.last_used else None
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