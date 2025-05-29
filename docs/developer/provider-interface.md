# Provider Interface

## Overview

The provider system in AliceMultiverse enables integration with various AI generation services (image, video, audio, text) through a unified interface. This document describes the provider abstraction and how to implement new providers.

## Architecture

### Core Components

- **Provider**: The unified base class all providers must inherit from (includes event publishing and cost tracking)
- **ProviderRegistry**: Simple registry for managing provider instances

### Key Types

```python
from alicemultiverse.providers.types import (
    GenerationType,      # IMAGE, VIDEO, AUDIO, TEXT
    GenerationRequest,   # Request to generate content
    GenerationResult,    # Result of generation
    CostEstimate,       # Detailed cost breakdown
    ProviderCapabilities # What a provider can do
)
```

## Implementing a Provider

### 1. Basic Structure

```python
from alicemultiverse.providers import Provider, ProviderCapabilities
from alicemultiverse.providers.types import GenerationType, GenerationRequest, GenerationResult

class MyProvider(Provider):
    """Provider for MyService API."""
    
    @property
    def name(self) -> str:
        return "myservice"
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            generation_types=[GenerationType.IMAGE],
            models=["model-1", "model-2"],
            max_resolution={"width": 2048, "height": 2048},
            formats=["png", "jpg"],
            pricing={"model-1": 0.02, "model-2": 0.05},
            supports_streaming=False,
            supports_batch=True
        )
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        # Validate request
        await self.validate_request(request)
        
        # Publish start event
        self._publish_started(request)
        
        try:
            # Your generation logic here
            result = await self._call_api(request)
            
            # Track costs
            self._total_cost += result.cost
            self._generation_count += 1
            
            # Publish success event
            self._publish_success(request, result)
            
            return result
            
        except Exception as e:
            # Publish failure event
            self._publish_failure(request, str(e))
            raise
    
    async def check_status(self) -> ProviderStatus:
        # Check if API is available
        try:
            # Make a lightweight API call
            return ProviderStatus.AVAILABLE
        except Exception:
            return ProviderStatus.UNAVAILABLE
```

### 2. Cost Estimation

Providers should implement accurate cost estimation:

```python
async def estimate_cost(self, request: GenerationRequest) -> CostEstimate:
    # Call parent for base implementation
    estimate = await super().estimate_cost(request)
    
    # Add provider-specific modifiers
    if request.parameters.get("premium_feature"):
        estimate.estimated_cost *= 1.5
        estimate.breakdown["premium"] = estimate.estimated_cost * 0.5
    
    return estimate
```

### 3. Budget Validation

The base class handles budget validation automatically:

```python
request = GenerationRequest(
    prompt="Generate image",
    generation_type=GenerationType.IMAGE,
    budget_limit=0.10  # Max $0.10
)

# validate_request will raise BudgetExceededError if over budget
await provider.validate_request(request)
```

## Provider Registry

### Registering Providers

```python
from alicemultiverse.providers.registry import ProviderRegistry

# Add to PROVIDERS dict in registry.py
class ProviderRegistry:
    PROVIDERS = {
        "myservice": MyProvider,
        # ... other providers
    }
```

### Using Providers

```python
from alicemultiverse.providers import get_provider

# Get provider instance
provider = get_provider("myservice", api_key="...")

# Generate content
result = await provider.generate(request)
```

## Events

Providers automatically publish events:

- `generation.started` - When generation begins
- `asset.generated` - When generation succeeds
- `generation.failed` - When generation fails

## Testing

### Unit Tests

```python
class TestMyProvider:
    @pytest.mark.asyncio
    async def test_capabilities(self):
        provider = MyProvider()
        assert GenerationType.IMAGE in provider.capabilities.generation_types
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self):
        provider = MyProvider()
        request = GenerationRequest(...)
        estimate = await provider.estimate_cost(request)
        assert estimate.estimated_cost > 0
```

### Integration Tests

```python
@pytest.mark.integration
async def test_real_generation():
    provider = MyProvider(api_key=os.getenv("MYSERVICE_KEY"))
    request = GenerationRequest(
        prompt="test",
        generation_type=GenerationType.IMAGE
    )
    result = await provider.generate(request)
    assert result.success
    assert result.file_path.exists()
```

## Best Practices

1. **Error Handling**: Use specific exceptions (RateLimitError, AuthenticationError)
2. **Cost Tracking**: Always track actual costs in generate()
3. **Event Publishing**: Use the mixin methods for consistent events
4. **Validation**: Validate requests early with validate_request()
5. **Resource Cleanup**: Implement __aexit__ for cleanup

## Migration from Old Interface

The old `GenerationProvider` class is deprecated but still available for backward compatibility. New providers should use `BaseProvider` which offers:

- Better cost estimation with breakdowns
- Budget validation
- Cost tracking
- Enhanced capabilities
- Consistent event publishing