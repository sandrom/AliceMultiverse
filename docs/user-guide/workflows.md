# Multi-Modal Workflows

AliceMultiverse provides a powerful workflow system for chaining AI operations across multiple providers. This enables complex pipelines like image generation → upscaling → variations or video generation → audio addition → enhancement.

## Overview

Workflows allow you to:
- **Chain operations** across different providers
- **Optimize costs** by selecting the best provider for each step
- **Handle failures** gracefully with conditional execution
- **Track progress** through event-driven updates
- **Reuse templates** for common pipelines

## Built-in Workflows

### Image Enhancement
Generate, upscale, and create variations of images.

```python
from alicemultiverse.workflows import get_workflow, WorkflowExecutor

# Get the workflow
workflow = get_workflow("image_enhancement")

# Execute it
executor = WorkflowExecutor()
result = await executor.execute(
    workflow=workflow,
    initial_prompt="A serene mountain landscape at sunset",
    parameters={
        "initial_provider": "leonardo",
        "upscale_provider": "magnific",
        "generate_variations": True,
        "variation_count": 3
    }
)

print(f"Completed: {result.completed_steps}/{result.total_steps} steps")
print(f"Total cost: ${result.total_cost:.2f}")
print(f"Outputs: {result.final_outputs}")
```

### Video Production
Generate videos with synchronized audio and enhancements.

```python
workflow = get_workflow("video_production")

result = await executor.execute(
    workflow=workflow,
    initial_prompt="Drone footage of a futuristic city",
    parameters={
        "video_provider": "veo",
        "video_duration": 8,
        "add_audio": True,
        "audio_style": "cinematic",
        "enhance_video": True
    }
)
```

### Style Transfer
Apply artistic styles to images with multiple variations.

```python
workflow = get_workflow("style_transfer")

result = await executor.execute(
    workflow=workflow,
    initial_prompt="Portrait photo",
    parameters={
        "input_image": "path/to/photo.jpg",
        "style_reference": "Van Gogh painting style",
        "num_variations": 4,
        "style_strength": 0.7
    }
)
```

## Workflow Parameters

### Common Parameters
- `initial_prompt`: Base prompt for generation
- `budget_limit`: Maximum cost for the workflow
- `dry_run`: Estimate costs without executing

### Image Enhancement Parameters
- `initial_provider`: Provider for initial generation (default: leonardo)
- `initial_model`: Model for initial generation (default: phoenix)
- `upscale_provider`: Provider for upscaling (default: magnific)
- `upscale_scale`: Upscaling factor (default: 2)
- `generate_variations`: Whether to generate variations
- `variation_count`: Number of variations (default: 3)

### Video Production Parameters
- `video_provider`: Provider for video generation (default: veo)
- `video_duration`: Duration in seconds (default: 8)
- `add_audio`: Whether to add audio (default: true)
- `audio_provider`: Provider for audio (default: mmaudio)
- `enhance_video`: Whether to enhance quality
- `add_captions`: Whether to add captions

### Style Transfer Parameters
- `input_image`: Path to input image (optional)
- `style_reference`: Style description or image path
- `style_provider`: Provider for style transfer (default: firefly)
- `num_variations`: Number of style variations (default: 3)
- `style_strength`: How strongly to apply style (0-1)
- `preserve_content`: How much original to preserve (0-1)

## Workflow Variants

### Quick Workflows
Optimized for speed with reduced quality settings.

```python
# Quick enhancement
workflow = get_workflow("quick_enhance")

# Quick video
workflow = get_workflow("quick_video")
```

### Premium Workflows
Maximum quality with all enhancements enabled.

```python
# Premium enhancement with 5 variations
workflow = get_workflow("premium_enhance")

# Cinematic video with color grading
workflow = get_workflow("cinematic_video")
```

## Cost Optimization

### Estimate Costs
```python
# Dry run to see costs
result = await executor.execute(
    workflow=workflow,
    initial_prompt="Test",
    dry_run=True
)
print(f"Estimated cost: ${result.total_cost:.2f}")
```

### Set Budget Limits
```python
# Stop if cost exceeds $1.00
result = await executor.execute(
    workflow=workflow,
    initial_prompt="Complex scene",
    budget_limit=1.00
)
```

### Per-Step Cost Limits
```python
parameters={
    "initial_cost_limit": 0.10,    # Max $0.10 for generation
    "upscale_cost_limit": 0.20,    # Max $0.20 for upscaling
    "variation_cost_limit": 0.05    # Max $0.05 per variation
}
```

## Conditional Execution

Steps can have conditions that determine if they run:

```python
parameters={
    "enhance_only_if_quality": True,  # Only enhance high-quality results
    "skip_variations_on_budget": True  # Skip variations if over budget
}
```

## Progress Tracking

Workflows publish events for progress tracking:

```python
from alicemultiverse.events import EventBus

# Subscribe to workflow events
bus = EventBus()

@bus.subscribe("workflow.started")
async def on_start(event):
    print(f"Started {event.workflow_name}")

@bus.subscribe("workflow.step.completed")
async def on_step(event):
    print(f"Completed {event.step_name}")

# Use bus with executor
executor = WorkflowExecutor(event_bus=bus)
```

## Custom Workflows

Create your own workflow templates:

```python
from alicemultiverse.workflows import WorkflowTemplate, WorkflowStep

class MyCustomWorkflow(WorkflowTemplate):
    """My custom image pipeline."""
    
    def define_steps(self, context):
        return [
            WorkflowStep(
                name="generate",
                provider="ideogram",
                operation="generate",
                parameters={
                    "model": "ideogram-v3",
                    "style": "realistic"
                }
            ),
            WorkflowStep(
                name="enhance",
                provider="magnific",
                operation="upscale",
                parameters={
                    "input_from": "generate",
                    "scale": 2
                },
                condition="previous.success"
            )
        ]

# Register and use
from alicemultiverse.workflows import register_workflow

register_workflow("my_custom", MyCustomWorkflow)
workflow = get_workflow("my_custom")
```

## Error Handling

Workflows handle errors gracefully:

```python
result = await executor.execute(workflow, prompt)

if not result.success:
    print(f"Workflow failed: {result.status}")
    for error in result.errors:
        print(f"  - {error}")
else:
    print(f"Success! Outputs: {result.final_outputs}")
```

## Best Practices

1. **Start with dry runs** to estimate costs
2. **Set budget limits** to avoid surprises
3. **Use appropriate providers** for each step
4. **Monitor events** for long workflows
5. **Clean up temp files** (automatic in most cases)
6. **Save workflow results** for reproducibility

## Examples

### Professional Headshot Enhancement
```python
result = await executor.execute(
    workflow=get_workflow("image_enhancement"),
    initial_prompt="Professional headshot of a business executive",
    parameters={
        "initial_provider": "leonardo",
        "initial_model": "photoreal",
        "upscale_provider": "magnific",
        "upscale_scale": 2,
        "generate_variations": False,  # Keep consistent
        "upscale_creativity": 0.1,     # Minimal changes
        "upscale_resemblance": 0.9     # High resemblance
    }
)
```

### Artistic Style Exploration
```python
result = await executor.execute(
    workflow=get_workflow("artistic_style"),
    initial_prompt="Still life with flowers",
    parameters={
        "style_reference": "impressionist painting",
        "num_variations": 5,
        "style_strength": 0.8,
        "enhance_results": True
    }
)
```

### Social Media Video
```python
result = await executor.execute(
    workflow=get_workflow("quick_video"),
    initial_prompt="Trendy product showcase",
    parameters={
        "video_duration": 15,
        "add_audio": True,
        "audio_style": "upbeat",
        "add_captions": True,
        "optimize_for_web": True
    }
)
```