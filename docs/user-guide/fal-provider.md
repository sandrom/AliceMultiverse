# fal.ai Provider Guide

The fal.ai provider enables AliceMultiverse to generate images and videos using state-of-the-art AI models including FLUX and Kling.

## Available Models

### Image Generation

#### FLUX Models
- **flux-schnell** ($0.003) - Fast generation (~2s), good for quick iterations
- **flux-dev** ($0.025) - Balanced quality and speed (~10s)
- **flux-pro** ($0.05) - Highest quality, professional results
- **flux-realism** ($0.025) - Optimized for photorealistic output

#### Other Image Models
- **fast-sdxl** ($0.003) - Fast SDXL variant
- **lightning-sdxl** ($0.003) - Ultra-fast generation
- **stable-cascade** ($0.01) - High-resolution cascaded generation
- **pixart-sigma** ($0.01) - Artistic style generation
- **kolors** ($0.01) - Specialized color model

### Video Generation

#### Kling Models
- **kling-v1-text** ($0.15) - Text-to-video generation
- **kling-v1-image** ($0.15) - Image-to-video animation
- **kling-v2-text** ($0.20) - Latest text-to-video with improved quality
- **kling-v2-image** ($0.20) - Latest image-to-video animation
- **kling-elements** ($0.15) - Special effects (heart, hug, kiss, etc.)
- **kling-lipsync** ($0.20) - Audio or text-based lip sync

#### Other Video Models
- **animatediff** ($0.10) - Animated diffusion
- **svd** ($0.10) - Stable Video Diffusion

### Utility Models
- **face-swap** ($0.02) - Face swapping
- **ccsr** ($0.02) - Image upscaling
- **clarity-upscaler** ($0.02) - Enhanced upscaling

## Setup

### 1. Configure API Key

Run the interactive setup:
```bash
alice keys setup
```

Or set the environment variable:
```bash
export FAL_KEY="your-api-key-here"
```

### 2. Test the Provider

Run the example script:
```bash
python examples/advanced/fal_provider_example.py
```

## Usage Examples

### Basic Image Generation (FLUX Schnell)

```python
from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType

# Get the provider
provider = get_provider("fal")

# Create a request
request = GenerationRequest(
    prompt="A serene mountain landscape at sunset",
    generation_type=GenerationType.IMAGE,
    model="flux-schnell",  # Fast model
    parameters={
        "width": 1024,
        "height": 768
    }
)

# Generate
result = await provider.generate(request)
if result.success:
    print(f"Image saved to: {result.file_path}")
    print(f"Cost: ${result.cost}")
```

### Premium Quality (FLUX Pro)

```python
request = GenerationRequest(
    prompt="Award-winning photograph of a majestic eagle, National Geographic style",
    generation_type=GenerationType.IMAGE,
    model="flux-pro",  # Premium model
    parameters={
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 50,  # More steps for quality
        "guidance_scale": 3.5
    }
)
```

### Video Generation (Kling)

```python
# Text-to-video
request = GenerationRequest(
    prompt="A graceful dancer performing ballet in a moonlit forest",
    generation_type=GenerationType.VIDEO,
    model="kling-v2-text",
    parameters={
        "duration": "5",  # 5 seconds
        "aspect_ratio": "16:9",
        "cfg_scale": 0.5
    }
)

# Special effects
request = GenerationRequest(
    prompt="Create a magical transformation",
    generation_type=GenerationType.VIDEO,
    model="kling-elements",
    parameters={
        "effect": "heart_gesture",  # or: hug, kiss, squish, expansion
        "duration": "5",
        "aspect_ratio": "16:9"
    }
)
```

## Cost Optimization

1. **Use flux-schnell for iterations** - At $0.003 per image, it's ideal for testing prompts
2. **Progressive refinement** - Start with schnell, refine with dev, finalize with pro
3. **Batch similar requests** - Process multiple variations together
4. **Set cost limits** - Use the pipeline system's cost limiting features

## Integration with AliceMultiverse

The fal.ai provider integrates seamlessly with Alice's workflow:

1. **Automatic organization** - Generated content is automatically organized
2. **Quality assessment** - Use pipelines to assess generated content
3. **Metadata embedding** - Prompts and parameters are embedded in files
4. **Event tracking** - All generations trigger events for monitoring

### Example Workflow

```python
# 1. Generate images
results = []
for variation in ["morning", "sunset", "night"]:
    request = GenerationRequest(
        prompt=f"Mountain landscape at {variation}",
        model="flux-dev",
        generation_type=GenerationType.IMAGE
    )
    result = await provider.generate(request)
    results.append(result)

# 2. Organize generated content
alice organize --quality

# 3. Search for best results
alice search "mountain landscape" --quality-min 4
```

## Best Practices

1. **Prompt Engineering**
   - Be specific and descriptive
   - Include style references for consistency
   - Use quality descriptors ("professional", "cinematic", etc.)

2. **Model Selection**
   - flux-schnell: Quick tests and iterations
   - flux-dev: Production work with good balance
   - flux-pro: Hero images and final assets
   - kling-v2: High-quality video generation

3. **Parameter Tuning**
   - Higher inference steps = better quality but slower
   - Guidance scale affects prompt adherence (3.5 is balanced)
   - Resolution affects both quality and cost

## Troubleshooting

### No API Key Error
```bash
# Configure key
alice keys setup

# Or set environment
export FAL_KEY="your-key"
```

### Rate Limiting
The provider handles rate limits automatically with retry logic.

### Generation Failures
- Check your API key is valid
- Ensure prompt doesn't violate content policy
- Verify model name is correct
- Check API status at fal.ai

## Advanced Usage

### Custom Parameters
Each model supports specific parameters:

```python
# FLUX models
parameters = {
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 50,
    "guidance_scale": 3.5,
    "num_images": 1,
    "enable_safety_checker": True
}

# Kling video models
parameters = {
    "duration": "5",  # seconds
    "aspect_ratio": "16:9",  # or "9:16", "1:1"
    "cfg_scale": 0.5,  # 0.0-1.0
}
```

### Event Monitoring
Subscribe to generation events:

```python
from alicemultiverse.events import EventBus

bus = EventBus()
bus.subscribe("generation.started", on_start)
bus.subscribe("generation.completed", on_complete)
bus.subscribe("generation.failed", on_fail)
```

## Next Steps

1. Explore the [Pipeline Architecture](../architecture/pipeline-architecture.md) for quality assessment
2. Learn about [Event-Driven Architecture](../architecture/event-driven-architecture.md) for automation
3. Check the [API Reference](../api/reference/) for detailed provider documentation