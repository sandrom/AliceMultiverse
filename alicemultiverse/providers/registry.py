"""Provider registry for managing AI generation providers."""

import logging
from typing import Dict, List, Optional, Type

from ..events.base import EventBus
from .base import GenerationProvider, GenerationType
from .fal_provider import FalProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for managing generation providers."""

    # Available provider classes
    PROVIDERS: Dict[str, Type[GenerationProvider]] = {
        "fal": FalProvider,
        "fal.ai": FalProvider,  # Alias
    }

    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize provider registry.
        
        Args:
            event_bus: Event bus for providers to use
        """
        self.event_bus = event_bus or EventBus()
        self._instances: Dict[str, GenerationProvider] = {}
        self._api_keys: Dict[str, str] = {}

    def register_api_key(self, provider_name: str, api_key: str):
        """Register an API key for a provider.
        
        Args:
            provider_name: Provider name
            api_key: API key
        """
        self._api_keys[provider_name.lower()] = api_key

    def get_provider(self, name: str) -> GenerationProvider:
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
        if name_lower not in self.PROVIDERS:
            available = ", ".join(self.PROVIDERS.keys())
            raise ValueError(
                f"Unknown provider '{name}'. Available providers: {available}"
            )
        
        # Get provider class
        provider_class = self.PROVIDERS[name_lower]
        
        # Get API key if registered
        api_key = self._api_keys.get(name_lower)
        
        # Create instance
        instance = provider_class(api_key=api_key, event_bus=self.event_bus)
        self._instances[name_lower] = instance
        
        logger.info(f"Initialized {name} provider")
        return instance

    def get_providers_for_type(self, generation_type: GenerationType) -> List[str]:
        """Get providers that support a generation type.
        
        Args:
            generation_type: Type of generation
            
        Returns:
            List of provider names
        """
        providers = []
        
        for name, provider_class in self.PROVIDERS.items():
            # Create temporary instance to check capabilities
            instance = provider_class()
            if generation_type in instance.capabilities.generation_types:
                providers.append(name)
        
        return providers

    def list_providers(self) -> List[str]:
        """List all available providers.
        
        Returns:
            List of provider names
        """
        return list(self.PROVIDERS.keys())


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_registry(event_bus: Optional[EventBus] = None) -> ProviderRegistry:
    """Get global provider registry.
    
    Args:
        event_bus: Event bus to use (only on first call)
        
    Returns:
        Provider registry
    """
    global _registry
    if _registry is None:
        _registry = ProviderRegistry(event_bus)
    return _registry


def get_provider(name: str, api_key: Optional[str] = None) -> GenerationProvider:
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