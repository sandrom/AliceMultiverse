"""Test provider interface extraction."""

from pathlib import Path

import pytest

from alicemultiverse.providers import (
    BudgetExceededError,
    CostEstimate,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    Provider,
    ProviderCapabilities,
    ProviderStatus,
)


class TestProviderInterface:
    """Test the extracted provider interface."""

    def test_types_are_importable(self):
        """Test that all types can be imported."""
        # Types should be accessible
        assert GenerationType.IMAGE == "image"
        assert GenerationType.VIDEO == "video"
        assert ProviderStatus.AVAILABLE == "available"

    def test_provider_abstract(self):
        """Test that Provider is abstract."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Provider()

    def test_generation_request_fields(self):
        """Test GenerationRequest has all expected fields."""
        request = GenerationRequest(
            prompt="test prompt",
            generation_type=GenerationType.IMAGE,
            model="test-model",
            project_id="project-123",
            budget_limit=5.0
        )

        assert request.prompt == "test prompt"
        assert request.generation_type == GenerationType.IMAGE
        assert request.model == "test-model"
        assert request.project_id == "project-123"
        assert request.budget_limit == 5.0

    def test_generation_result_timestamp(self):
        """Test GenerationResult auto-sets timestamp."""
        result = GenerationResult(success=True)
        assert result.timestamp is not None

    def test_cost_estimate_structure(self):
        """Test CostEstimate dataclass."""
        estimate = CostEstimate(
            provider="test",
            model="test-model",
            estimated_cost=1.5,
            confidence=0.8,
            breakdown={"base": 1.0, "resolution": 0.5}
        )

        assert estimate.provider == "test"
        assert estimate.estimated_cost == 1.5
        assert estimate.confidence == 0.8
        assert estimate.breakdown["base"] == 1.0

    def test_provider_capabilities_enhanced(self):
        """Test enhanced ProviderCapabilities."""
        caps = ProviderCapabilities(
            generation_types=[GenerationType.IMAGE, GenerationType.VIDEO],
            models=["model1", "model2"],
            supports_streaming=True,
            supports_batch=False
        )

        assert GenerationType.IMAGE in caps.generation_types
        assert caps.supports_streaming is True
        assert caps.supports_batch is False


class MockProvider(Provider):
    """Mock provider for testing."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=["mock-model"],
            pricing={"mock-model": 0.01}
        )

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Mock generation."""
        return GenerationResult(
            success=True,
            file_path=Path("/tmp/mock.png"),
            cost=0.01,
            provider=self.name,
            model=request.model or "mock-model"
        )

    async def check_status(self) -> ProviderStatus:
        """Mock status check."""
        return ProviderStatus.AVAILABLE


class TestBaseProviderFeatures:
    """Test BaseProvider enhanced features."""

    @pytest.mark.asyncio
    async def test_cost_estimation(self):
        """Test cost estimation with resolution modifier."""
        provider = MockProvider()

        # Base cost
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE,
            model="mock-model"
        )
        estimate = await provider.estimate_cost(request)
        assert estimate.estimated_cost == 0.01

        # High resolution cost
        request_hires = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE,
            model="mock-model",
            parameters={"width": 2048, "height": 2048}
        )
        estimate_hires = await provider.estimate_cost(request_hires)
        assert estimate_hires.estimated_cost > 0.01  # Should be higher
        assert "resolution" in estimate_hires.breakdown

    @pytest.mark.asyncio
    async def test_budget_validation(self):
        """Test budget validation in validate_request."""
        provider = MockProvider()

        # Within budget
        request = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE,
            budget_limit=1.0
        )
        await provider.validate_request(request)  # Should not raise

        # Exceeds budget
        request_over = GenerationRequest(
            prompt="test",
            generation_type=GenerationType.IMAGE,
            budget_limit=0.001
        )
        with pytest.raises(BudgetExceededError):
            await provider.validate_request(request_over)

    def test_cost_tracking(self):
        """Test provider tracks total cost."""
        provider = MockProvider()
        assert provider.total_cost == 0.0
        assert provider.generation_count == 0

    def test_default_model_selection(self):
        """Test default model selection."""
        provider = MockProvider()
        assert provider.get_default_model(GenerationType.IMAGE) == "mock-model"
