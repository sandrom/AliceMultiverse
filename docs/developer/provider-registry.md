# Provider Registry with Cost Tracking

## Overview

The enhanced provider registry manages AI generation providers with comprehensive cost tracking, budget management, and provider selection capabilities.

## Features

### Cost Tracking
- Track costs per provider, model, and project
- Daily cost aggregation
- Historical statistics

### Budget Management
- Global budget limits
- Per-request budget constraints
- Automatic provider selection based on cost

### Provider Management
- Enable/disable providers dynamically
- Set preferred providers for each generation type
- Provider health monitoring

## Usage

### Basic Setup

```python
from alicemultiverse.providers import get_registry, set_global_budget

# Set a global budget limit
set_global_budget(100.0)  # $100 USD

# Get the registry
registry = get_registry()

# Register API keys
registry.register_api_key("fal", "your-fal-key")
registry.register_api_key("openai", "your-openai-key")
```

### Cost-Aware Generation

```python
from alicemultiverse.providers import GenerationRequest, GenerationType

# Request with budget constraint
request = GenerationRequest(
    prompt="A beautiful sunset",
    generation_type=GenerationType.IMAGE,
    budget_limit=0.10  # Max $0.10 for this request
)

# Registry automatically selects cheapest provider
provider = await registry.select_provider(request)
result = await provider.generate(request)
```

### Cost Reporting

```python
from alicemultiverse.providers import get_cost_report

# Get comprehensive cost report
report = get_cost_report()
print(f"Total cost: ${report['total_cost']:.2f}")
print(f"Costs by provider: {report['costs_by_provider']}")
print(f"Daily costs: {report['daily_costs']}")

# Get provider-specific stats
stats = registry.get_stats("fal")
print(f"Fal.ai success rate: {stats['success_rate']:.1%}")
```

### Provider Management

```python
# Disable expensive provider temporarily
registry.disable_provider("expensive-provider")

# Set preferred provider for images
registry.set_preferred_provider(GenerationType.IMAGE, "fal")

# List available providers
providers = registry.list_providers()
print(f"Available: {providers}")
```

## CLI Commands

The provider system includes CLI commands for management:

```bash
# List providers
alice providers list
alice providers list --show-disabled

# Cost report
alice providers cost
alice providers cost --provider fal
alice providers cost --json

# Enable/disable providers
alice providers disable expensive-provider
alice providers enable expensive-provider

# Set global budget
alice providers budget 100.0
```

## Architecture

### Registry Structure

```
EnhancedProviderRegistry
├── Provider Management
│   ├── Provider registration
│   ├── Instance caching
│   └── Health monitoring
├── Cost Tracking
│   ├── Per-provider costs
│   ├── Per-project costs
│   └── Daily aggregation
└── Provider Selection
    ├── Budget-based selection
    ├── Preferred providers
    └── Capability matching
```

### Cost Tracking Flow

1. **Pre-generation**: Estimate cost and check budgets
2. **Generation**: Execute and track actual cost
3. **Post-generation**: Update statistics and totals
4. **Reporting**: Aggregate by provider, project, and time

## Best Practices

### 1. Set Budget Limits
Always set appropriate budget limits to prevent unexpected costs:

```python
# Global limit
set_global_budget(50.0)  # $50 daily limit

# Per-request limit
request.budget_limit = 0.10  # $0.10 max
```

### 2. Monitor Costs
Regularly check cost reports:

```python
# In your monitoring script
report = get_cost_report()
if report['total_cost'] > 40.0:  # 80% of budget
    send_alert("Approaching budget limit")
```

### 3. Use Preferred Providers
Set preferred providers for consistent results:

```python
# Prefer fast provider for drafts
registry.set_preferred_provider(GenerationType.IMAGE, "flux-schnell")

# But allow budget constraints to override
request = GenerationRequest(
    prompt="quick draft",
    generation_type=GenerationType.IMAGE,
    budget_limit=0.01  # Forces cheapest option
)
```

### 4. Handle Provider Failures
The registry tracks provider health:

```python
stats = registry.get_stats("provider-name")
if stats['success_rate'] < 0.8:  # 80% success
    registry.disable_provider("provider-name")
    # Use alternative provider
```

## Integration with Projects

When project management is implemented, costs will be tracked per project:

```python
request = GenerationRequest(
    prompt="Project asset",
    generation_type=GenerationType.IMAGE,
    project_id="proj-123"  # Track cost to project
)

# Later, get project costs
report = get_cost_report()
project_cost = report['costs_by_project']['proj-123']
```

## Testing

The registry includes comprehensive testing:

```python
# tests/unit/test_enhanced_registry.py
class TestEnhancedRegistry:
    async def test_budget_enforcement(self):
        # Test that budget limits are enforced
        
    async def test_cost_tracking(self):
        # Test accurate cost tracking
        
    async def test_provider_selection(self):
        # Test intelligent provider selection
```

## Future Enhancements

1. **Cost Optimization**
   - Batch request grouping
   - Off-peak pricing awareness
   - Provider cost negotiation

2. **Advanced Analytics**
   - Cost trends and forecasting
   - Provider performance metrics
   - ROI analysis per project

3. **Multi-Currency Support**
   - Currency conversion
   - Regional pricing
   - Tax calculations