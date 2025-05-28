"""Enhanced provider registry with cost tracking and management."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Dict, List, Optional, Set, Type

from ..events.base import EventBus, create_event
from .base_provider import BaseProvider, BudgetExceededError
from .types import CostEstimate, GenerationRequest, GenerationType

logger = logging.getLogger(__name__)


@dataclass
class ProviderStats:
    """Statistics for a provider."""
    total_cost: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_generation_time: float = 0.0
    costs_by_model: Dict[str, float] = field(default_factory=dict)
    last_used: Optional[datetime] = None


@dataclass
class CostTracker:
    """Track costs across all providers."""
    total_cost: float = 0.0
    costs_by_provider: Dict[str, float] = field(default_factory=dict)
    costs_by_project: Dict[str, float] = field(default_factory=dict)
    daily_costs: Dict[str, float] = field(default_factory=dict)
    
    def add_cost(self, provider: str, cost: float, project_id: Optional[str] = None):
        """Add a cost entry."""
        self.total_cost += cost
        self.costs_by_provider[provider] = self.costs_by_provider.get(provider, 0.0) + cost
        
        if project_id:
            self.costs_by_project[project_id] = self.costs_by_project.get(project_id, 0.0) + cost
        
        # Track daily costs
        today = datetime.now(UTC).date().isoformat()
        self.daily_costs[today] = self.daily_costs.get(today, 0.0) + cost


class EnhancedProviderRegistry:
    """Enhanced registry with cost tracking and provider management."""
    
    def __init__(self, event_bus: Optional[EventBus] = None, budget_limit: Optional[float] = None):
        """Initialize enhanced registry.
        
        Args:
            event_bus: Event bus for providers to use
            budget_limit: Global budget limit across all providers
        """
        self.event_bus = event_bus or EventBus()
        self.budget_limit = budget_limit
        
        # Provider management
        self._provider_classes: Dict[str, Type[BaseProvider]] = {}
        self._instances: Dict[str, BaseProvider] = {}
        self._api_keys: Dict[str, str] = {}
        
        # Cost tracking
        self.cost_tracker = CostTracker()
        self._provider_stats: Dict[str, ProviderStats] = defaultdict(ProviderStats)
        
        # Provider selection
        self._preferred_providers: Dict[GenerationType, str] = {}
        self._disabled_providers: Set[str] = set()
    
    def register_provider(self, name: str, provider_class: Type[BaseProvider], aliases: Optional[List[str]] = None):
        """Register a provider class.
        
        Args:
            name: Primary provider name
            provider_class: Provider class
            aliases: Alternative names for the provider
        """
        name_lower = name.lower()
        self._provider_classes[name_lower] = provider_class
        
        # Register aliases
        if aliases:
            for alias in aliases:
                self._provider_classes[alias.lower()] = provider_class
        
        logger.info(f"Registered provider: {name}")
    
    def register_api_key(self, provider_name: str, api_key: str):
        """Register an API key for a provider.
        
        Args:
            provider_name: Provider name
            api_key: API key
        """
        self._api_keys[provider_name.lower()] = api_key
    
    def set_preferred_provider(self, generation_type: GenerationType, provider_name: str):
        """Set preferred provider for a generation type.
        
        Args:
            generation_type: Type of generation
            provider_name: Preferred provider name
        """
        if provider_name.lower() not in self._provider_classes:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        self._preferred_providers[generation_type] = provider_name.lower()
    
    def disable_provider(self, provider_name: str):
        """Temporarily disable a provider.
        
        Args:
            provider_name: Provider to disable
        """
        self._disabled_providers.add(provider_name.lower())
        logger.warning(f"Disabled provider: {provider_name}")
    
    def enable_provider(self, provider_name: str):
        """Re-enable a disabled provider.
        
        Args:
            provider_name: Provider to enable
        """
        self._disabled_providers.discard(provider_name.lower())
        logger.info(f"Enabled provider: {provider_name}")
    
    async def get_provider(self, name: str) -> BaseProvider:
        """Get a provider instance by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider not found or disabled
        """
        name_lower = name.lower()
        
        # Check if disabled
        if name_lower in self._disabled_providers:
            raise ValueError(f"Provider '{name}' is currently disabled")
        
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
        
        # Create instance with cost tracking wrapper
        instance = CostTrackingProvider(
            provider_class(api_key=api_key, event_bus=self.event_bus),
            self
        )
        self._instances[name_lower] = instance
        
        logger.info(f"Initialized {name} provider")
        return instance
    
    async def select_provider(self, request: GenerationRequest) -> BaseProvider:
        """Select best provider for a request.
        
        Args:
            request: Generation request
            
        Returns:
            Selected provider
            
        Raises:
            ValueError: If no suitable provider found
        """
        # Check preferred provider first
        if request.generation_type in self._preferred_providers:
            preferred = self._preferred_providers[request.generation_type]
            if preferred not in self._disabled_providers:
                return await self.get_provider(preferred)
        
        # Find available providers
        available_providers = []
        for name, provider_class in self._provider_classes.items():
            if name in self._disabled_providers:
                continue
            
            # Check capabilities
            temp_instance = provider_class()
            if request.generation_type in temp_instance.capabilities.generation_types:
                available_providers.append(name)
        
        if not available_providers:
            raise ValueError(f"No available providers for {request.generation_type}")
        
        # Select based on cost if budget specified
        if request.budget_limit is not None:
            best_provider = None
            best_estimate = None
            
            for provider_name in available_providers:
                provider = await self.get_provider(provider_name)
                estimate = await provider.estimate_cost(request)
                
                if estimate.estimated_cost <= request.budget_limit:
                    if best_estimate is None or estimate.estimated_cost < best_estimate.estimated_cost:
                        best_provider = provider_name
                        best_estimate = estimate
            
            if best_provider:
                return await self.get_provider(best_provider)
            else:
                raise BudgetExceededError(
                    f"No provider can fulfill request within budget ${request.budget_limit:.2f}"
                )
        
        # Default to first available
        return await self.get_provider(available_providers[0])
    
    def get_providers_for_type(self, generation_type: GenerationType) -> List[str]:
        """Get providers that support a generation type.
        
        Args:
            generation_type: Type of generation
            
        Returns:
            List of provider names
        """
        providers = []
        
        for name, provider_class in self._provider_classes.items():
            if name in self._disabled_providers:
                continue
            
            # Create temporary instance to check capabilities
            instance = provider_class()
            if generation_type in instance.capabilities.generation_types:
                providers.append(name)
        
        return providers
    
    def list_providers(self, include_disabled: bool = False) -> List[str]:
        """List all registered providers.
        
        Args:
            include_disabled: Include disabled providers
            
        Returns:
            List of provider names
        """
        providers = list(self._provider_classes.keys())
        
        if not include_disabled:
            providers = [p for p in providers if p not in self._disabled_providers]
        
        return providers
    
    def get_stats(self, provider_name: Optional[str] = None) -> Dict[str, any]:
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
                "average_cost": stats.total_cost / stats.total_requests if stats.total_requests > 0 else 0,
                "average_time": stats.total_generation_time / stats.successful_requests if stats.successful_requests > 0 else 0,
                "costs_by_model": stats.costs_by_model,
                "last_used": stats.last_used.isoformat() if stats.last_used else None
            }
        else:
            return {
                "total_cost": self.cost_tracker.total_cost,
                "costs_by_provider": dict(self.cost_tracker.costs_by_provider),
                "costs_by_project": dict(self.cost_tracker.costs_by_project),
                "daily_costs": dict(self.cost_tracker.daily_costs),
                "provider_stats": {
                    name: self.get_stats(name) for name in self._provider_stats
                }
            }
    
    def check_budget(self, estimated_cost: float) -> bool:
        """Check if estimated cost is within budget.
        
        Args:
            estimated_cost: Estimated cost
            
        Returns:
            True if within budget
        """
        if self.budget_limit is None:
            return True
        
        return (self.cost_tracker.total_cost + estimated_cost) <= self.budget_limit
    
    def _track_generation(self, provider_name: str, result):
        """Track generation statistics.
        
        Args:
            provider_name: Provider name
            result: Generation result
        """
        stats = self._provider_stats[provider_name.lower()]
        stats.total_requests += 1
        stats.last_used = datetime.now(UTC)
        
        if result.success:
            stats.successful_requests += 1
            if result.cost:
                stats.total_cost += result.cost
                self.cost_tracker.add_cost(provider_name, result.cost)
                
                if result.model:
                    stats.costs_by_model[result.model] = stats.costs_by_model.get(result.model, 0.0) + result.cost
            
            if result.generation_time:
                stats.total_generation_time += result.generation_time
        else:
            stats.failed_requests += 1


class CostTrackingProvider(BaseProvider):
    """Wrapper that tracks costs for a provider."""
    
    def __init__(self, provider: BaseProvider, registry: EnhancedProviderRegistry):
        """Initialize cost tracking wrapper.
        
        Args:
            provider: Actual provider instance
            registry: Registry for tracking
        """
        self._provider = provider
        self._registry = registry
        
        # Delegate attributes
        self.api_key = provider.api_key
        self.event_bus = provider.event_bus
    
    @property
    def name(self) -> str:
        return self._provider.name
    
    @property
    def capabilities(self):
        return self._provider.capabilities
    
    async def generate(self, request: GenerationRequest):
        """Generate with cost tracking."""
        # Check global budget
        estimate = await self.estimate_cost(request)
        if not self._registry.check_budget(estimate.estimated_cost):
            raise BudgetExceededError(
                f"Generation would exceed global budget. "
                f"Current: ${self._registry.cost_tracker.total_cost:.2f}, "
                f"Limit: ${self._registry.budget_limit:.2f}"
            )
        
        # Generate
        result = await self._provider.generate(request)
        
        # Track result
        self._registry._track_generation(self.name, result)
        
        # Track project cost if specified
        if request.project_id and result.cost:
            self._registry.cost_tracker.add_cost(self.name, 0, request.project_id)
        
        return result
    
    async def check_status(self):
        return await self._provider.check_status()
    
    async def estimate_cost(self, request: GenerationRequest) -> CostEstimate:
        return await self._provider.estimate_cost(request)
    
    async def validate_request(self, request: GenerationRequest):
        return await self._provider.validate_request(request)
    
    def get_default_model(self, generation_type: GenerationType) -> str:
        return self._provider.get_default_model(generation_type)
    
    def get_models_for_type(self, generation_type: GenerationType) -> List[str]:
        return self._provider.get_models_for_type(generation_type)
    
    @property
    def total_cost(self) -> float:
        return self._provider.total_cost
    
    @property
    def generation_count(self) -> int:
        return self._provider.generation_count
    
    async def __aenter__(self):
        await self._provider.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._provider.__aexit__(exc_type, exc_val, exc_tb)