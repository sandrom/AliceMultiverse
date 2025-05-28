# Project Management in AliceMultiverse

AliceMultiverse includes a comprehensive project management system designed specifically for AI-driven creative workflows. This system tracks budgets, monitors AI generation costs, and maintains creative context across sessions.

## Overview

The project management system provides:

- **Budget Tracking**: Set and monitor project budgets with automatic pausing when limits are exceeded
- **Cost Analytics**: Detailed breakdown of costs by provider and model
- **Creative Context**: Persistent storage of style preferences, characters, and other creative decisions
- **Event-Driven Updates**: All project changes are published as events for real-time monitoring

## Architecture

### Core Components

1. **Project Model** (`alicemultiverse.database.models.Project`)
   - Stores project metadata, budget information, and creative context
   - Tracks budget spent and provides cost breakdowns by provider

2. **Generation Model** (`alicemultiverse.database.models.Generation`)
   - Records individual AI generation requests
   - Links costs to specific projects
   - Stores prompts and resulting asset hashes

3. **ProjectService** (`alicemultiverse.projects.ProjectService`)
   - Business logic for project management
   - Handles budget calculations and limit enforcement
   - Publishes events for all state changes

4. **Alice Interface** (`alicemultiverse.interface.alice_interface.AliceInterface`)
   - AI-friendly methods for project operations
   - Automatic error handling and suggestions

## Usage Examples

### Creating a Project

```python
from alicemultiverse.interface import AliceInterface

alice = AliceInterface()

# Create a project with budget
response = alice.create_project(
    name="Cyberpunk Music Video",
    description="A futuristic music video with neon aesthetics",
    budget=500.0,  # USD
    creative_context={
        "style": "cyberpunk",
        "color_palette": ["neon_pink", "electric_blue", "black"],
        "mood": "energetic",
        "references": ["Blade Runner", "Akira"]
    }
)

project_id = response["data"]["project_id"]
```

### Tracking Generation Costs

When using AI providers, track the costs:

```python
# After generating an image with DALL-E 3
response = alice.track_generation_cost(
    project_id=project_id,
    provider="openai",
    model="dall-e-3",
    cost=0.04,  # $0.04 per image
    request_type="image",
    prompt="Neon-lit cyberpunk street scene",
    result_assets=["hash_of_generated_image"]
)

# Check remaining budget
print(f"Budget remaining: ${response['data']['budget_remaining']}")
```

### Monitoring Budget Status

```python
# Get detailed project statistics
response = alice.get_project_budget_status(project_id)

stats = response["data"]
print(f"Total budget: ${stats['budget']['total']}")
print(f"Spent: ${stats['budget']['spent']}")
print(f"Remaining: ${stats['budget']['remaining']}")

# View cost breakdown by provider
for provider, info in stats["providers"].items():
    print(f"{provider}: {info['count']} generations, ${info['total_cost']}")
```

### Updating Creative Context

As the project evolves, update the creative context:

```python
# Add character definitions
response = alice.update_project_context(
    project_id=project_id,
    creative_context={
        "characters": {
            "protagonist": {
                "name": "Neo",
                "appearance": "Young hacker, black clothing, sunglasses",
                "style_ref": "Matrix-inspired"
            }
        }
    }
)
```

## Budget Management

### Automatic Budget Enforcement

When a project exceeds its budget:

1. The project status automatically changes to "paused"
2. A `workflow.failed` event is published with budget details
3. Further generation attempts will fail until the budget is increased

### Cost Tracking

The system tracks costs at multiple levels:

```json
{
  "cost_breakdown": {
    "openai:dall-e-3": {
      "count": 25,
      "total_cost": 1.0,
      "average_cost": 0.04
    },
    "anthropic:claude-3-haiku": {
      "count": 100,
      "total_cost": 0.25,
      "average_cost": 0.0025
    }
  }
}
```

## Events

All project operations publish events:

- `project.created` - New project created
- `context.updated` - Creative context modified
- `workflow.failed` - Budget exceeded or other failures
- `workflow.completed` - Project marked as completed

Monitor events in real-time:

```bash
python scripts/event_monitor.py
```

## Database Schema

### Projects Table
- `id` - UUID primary key
- `name` - Project name
- `budget_total` - Optional budget limit
- `budget_spent` - Current spending
- `budget_currency` - Currency code (default: USD)
- `status` - active, paused, completed, archived
- `creative_context` - JSON creative metadata
- `cost_breakdown` - JSON cost analytics

### Generations Table
- `id` - UUID primary key
- `project_id` - Foreign key to projects
- `provider` - AI provider name
- `model` - Specific model used
- `cost` - Generation cost
- `prompt` - Text prompt used
- `result_assets` - Array of content hashes

## Best Practices

1. **Set Realistic Budgets**: Consider the cost per generation and expected volume
2. **Track All Generations**: Even failed attempts should be tracked for accurate budgeting
3. **Update Context Regularly**: Keep creative context current for better AI assistance
4. **Monitor Events**: Use event monitoring to track project activity in real-time
5. **Archive Completed Projects**: Change status to "archived" to exclude from active lists

## Integration with Providers

The project system integrates seamlessly with the provider abstraction:

```python
from alicemultiverse.providers import get_provider

# Provider automatically tracks costs if project context is set
provider = get_provider("openai")
result = provider.generate(
    prompt="Cyberpunk scene",
    project_id=project_id  # Costs automatically tracked
)
```

## Future Enhancements

- **Budget Alerts**: Configurable warnings at percentage thresholds
- **Cost Optimization**: Automatic model selection based on budget
- **Team Budgets**: Shared budgets across multiple projects
- **Currency Support**: Multi-currency with automatic conversion
- **Reporting**: Detailed cost reports and analytics