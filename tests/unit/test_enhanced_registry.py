"""Test enhanced provider registry with cost tracking."""

import pytest
from datetime import datetime
from pathlib import Path

from alicemultiverse.providers import (
    BaseProvider,
    BudgetExceededError,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)
from alicemultiverse.providers.enhanced_registry import (
    CostTracker,
    EnhancedProviderRegistry,
    ProviderStats,
)
from alicemultiverse.providers.registry import get_cost_report, get_registry, set_global_budget


class MockProvider(BaseProvider):
    """Mock provider for testing."""
    
    def __init__(self, name: str = "mock", cost_per_image: float = 0.01, **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._cost = cost_per_image
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=["mock-model"],
            pricing={"mock-model": self._cost}
        )
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Mock generation."""
        # Track for testing
        self._total_cost += self._cost
        self._generation_count += 1
        
        return GenerationResult(
            success=True,
            file_path=Path("/tmp/mock.png"),
            cost=self._cost,
            generation_time=1.0,
            provider=self.name,
            model="mock-model"
        )
    
    async def check_status(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


class ExpensiveProvider(MockProvider):
    """Expensive mock provider for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(name="expensive", cost_per_image=1.0, **kwargs)


class TestCostTracker:
    """Test cost tracking functionality."""
    
    def test_add_cost(self):
        """Test adding costs."""
        tracker = CostTracker()
        
        # Add costs
        tracker.add_cost("provider1", 10.0)
        tracker.add_cost("provider1", 5.0)
        tracker.add_cost("provider2", 20.0)
        
        assert tracker.total_cost == 35.0
        assert tracker.costs_by_provider["provider1"] == 15.0
        assert tracker.costs_by_provider["provider2"] == 20.0
    
    def test_project_tracking(self):
        """Test project-specific cost tracking."""
        tracker = CostTracker()
        
        # Add costs with projects
        tracker.add_cost("provider1", 10.0, "project1")
        tracker.add_cost("provider1", 5.0, "project2")
        tracker.add_cost("provider2", 20.0, "project1")
        
        assert tracker.costs_by_project["project1"] == 30.0
        assert tracker.costs_by_project["project2"] == 5.0
    
    def test_daily_tracking(self):
        """Test daily cost tracking."""
        tracker = CostTracker()
        
        # Add costs
        tracker.add_cost("provider1", 10.0)
        tracker.add_cost("provider1", 5.0)
        
        today = datetime.now().date().isoformat()
        assert tracker.daily_costs[today] == 15.0


class TestEnhancedRegistry:
    """Test enhanced provider registry."""
    
    @pytest.fixture
    def registry(self):
        """Create test registry."""
        reg = EnhancedProviderRegistry()
        reg.register_provider("mock", MockProvider)
        reg.register_provider("expensive", ExpensiveProvider)
        return reg
    
    @pytest.mark.asyncio
    async def test_provider_registration(self, registry):
        """Test registering providers."""
        providers = registry.list_providers()
        assert "mock" in providers
        assert "expensive" in providers
    
    @pytest.mark.asyncio
    async def test_get_provider(self, registry):
        """Test getting provider instances."""
        provider = await registry.get_provider("mock")
        assert provider.name == "mock"
        
        # Same instance returned
        provider2 = await registry.get_provider("mock")
        assert provider is provider2
    
    @pytest.mark.asyncio
    async def test_disable_provider(self, registry):
        """Test disabling providers."""
        registry.disable_provider("mock")
        
        with pytest.raises(ValueError, match="disabled"):
            await registry.get_provider("mock")
        
        # Re-enable
        registry.enable_provider("mock")
        provider = await registry.get_provider("mock")
        assert provider is not None
    
    @pytest.mark.asyncio
    async def test_preferred_provider(self, registry):
        """Test preferred provider selection."""
        registry.set_preferred_provider(GenerationType.IMAGE, "expensive")
        
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE
        )
        
        provider = await registry.select_provider(request)
        assert provider.name == "expensive"
    
    @pytest.mark.asyncio
    async def test_budget_selection(self, registry):
        """Test provider selection based on budget."""
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE,
            budget_limit=0.05  # Only mock provider fits
        )
        
        provider = await registry.select_provider(request)
        assert provider.name == "mock"
    
    @pytest.mark.asyncio
    async def test_budget_exceeded(self, registry):
        """Test budget exceeded error."""
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE,
            budget_limit=0.001  # Too low for any provider
        )
        
        with pytest.raises(BudgetExceededError):
            await registry.select_provider(request)
    
    @pytest.mark.asyncio
    async def test_global_budget(self, registry):
        """Test global budget enforcement."""
        registry.budget_limit = 0.05
        
        provider = await registry.get_provider("mock")
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE
        )
        
        # Generate until budget exceeded
        for _ in range(5):
            result = await provider.generate(request)
            assert result.success
        
        # Next should fail
        with pytest.raises(BudgetExceededError, match="global budget"):
            await provider.generate(request)
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, registry):
        """Test cost tracking across providers."""
        # Generate with different providers
        mock_provider = await registry.get_provider("mock")
        expensive_provider = await registry.get_provider("expensive")
        
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE
        )
        
        # Generate some content
        await mock_provider.generate(request)
        await mock_provider.generate(request)
        await expensive_provider.generate(request)
        
        # Check stats
        stats = registry.get_stats()
        assert stats["total_cost"] == 1.02  # 0.01 + 0.01 + 1.0
        assert stats["costs_by_provider"]["mock"] == 0.02
        assert stats["costs_by_provider"]["expensive"] == 1.0
        
        # Check provider-specific stats
        mock_stats = registry.get_stats("mock")
        assert mock_stats["total_requests"] == 2
        assert mock_stats["success_rate"] == 1.0
        assert mock_stats["average_cost"] == 0.01


class TestCompatibilityAPI:
    """Test backward compatibility with existing registry API."""
    
    def test_get_registry(self):
        """Test getting global registry."""
        registry = get_registry()
        assert registry is not None
        
        # Same instance
        registry2 = get_registry()
        assert registry is registry2
    
    def test_set_global_budget(self):
        """Test setting global budget."""
        set_global_budget(100.0)
        
        registry = get_registry()
        assert registry._enhanced_registry.budget_limit == 100.0
    
    def test_get_cost_report(self):
        """Test getting cost report."""
        report = get_cost_report()
        assert "total_cost" in report
        assert "costs_by_provider" in report