# FLUX Kontext Guide

FLUX Kontext is a groundbreaking multimodal flow model that enables iterative image editing with unprecedented consistency and control.

## Overview

FLUX Kontext models excel at:
- **Character consistency** across different scenes
- **Local image editing** without affecting the entire image
- **Style preservation** while transforming content
- **Interactive editing** with minimal quality degradation
- **Typography generation** with improved accuracy

## Available Models

### Via fal.ai Provider

```python
# FLUX Kontext Pro - Fast iterative editing
provider = "fal"
model = "flux-kontext-pro"

# FLUX Kontext Max - Maximum performance
provider = "fal"
model = "flux-kontext-max"
```

### Via BFL Provider (Direct API)

```python
# Configure BFL API key
export BFL_API_KEY="your-bfl-api-key"

# Use BFL provider
provider = "bfl"
model = "flux-kontext-pro"  # or "flux-kontext-max"
```

## Usage Examples

### Basic Image Editing

```python
from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType

# Get provider (fal or bfl)
provider = get_provider("fal", api_key="your-key")

# Edit an existing image
request = GenerationRequest(
    prompt="Change the background to a sunset beach scene",
    generation_type=GenerationType.IMAGE,
    model="flux-kontext-pro",
    reference_assets=["/path/to/original/image.jpg"],
    parameters={
        "guidance_scale": 3.5,
        "num_inference_steps": 28
    }
)

result = await provider.generate(request)
```

### Character Consistency

```python
# Transform a character into different scenes while maintaining identity
request = GenerationRequest(
    prompt="The same person sitting in a coffee shop, reading a book",
    model="flux-kontext-max",  # Use Max for best consistency
    reference_assets=["/path/to/character.jpg"],
    parameters={
        "guidance_scale": 4.0,  # Higher for stronger adherence
    }
)
```

### Local Editing

```python
# Edit specific parts of an image
request = GenerationRequest(
    prompt="Replace the red car with a blue motorcycle",
    model="flux-kontext-pro",
    reference_assets=["/path/to/street_scene.jpg"],
    parameters={
        "guidance_scale": 3.0,  # Lower for more creative freedom
    }
)
```

## Model Comparison

| Model | Speed | Consistency | Best For | Cost |
|-------|-------|------------|----------|------|
| Kontext Pro | Fast | Good | Quick iterations, local edits | $0.06 |
| Kontext Max | Medium | Excellent | Character consistency, typography | $0.08 |

## Advanced Features

### Style Reference

Kontext models can maintain artistic style while changing content:

```python
request = GenerationRequest(
    prompt="Transform into pixel art style",
    model="flux-kontext-pro",
    reference_assets=["/path/to/photo.jpg"],
    parameters={
        "style_strength": 0.8,  # If supported
    }
)
```

### Iterative Editing

Kontext models are optimized for multiple editing passes:

```python
# First pass: Change environment
result1 = await provider.generate(GenerationRequest(
    prompt="Place in a futuristic city",
    model="flux-kontext-pro",
    reference_assets=[original_image]
))

# Second pass: Adjust lighting
result2 = await provider.generate(GenerationRequest(
    prompt="Add neon lighting and rain",
    model="flux-kontext-pro",
    reference_assets=[result1.file_path]
))

# Quality remains high even after multiple edits
```

## Best Practices

1. **Choose the right model**:
   - Use Pro for speed and general editing
   - Use Max for character consistency and typography

2. **Prompt engineering**:
   - Be specific about what to change
   - Mention what to preserve explicitly
   - Use descriptive language for style

3. **Parameter tuning**:
   - Lower guidance (2.5-3.5) for creative edits
   - Higher guidance (4.0-5.0) for precise control
   - Adjust steps based on complexity (28-50)

4. **Iterative workflow**:
   - Start with broad changes
   - Refine with specific edits
   - Save intermediate results

## Limitations

- Potential artifacts after many iterations
- May occasionally misinterpret complex instructions
- Limited world knowledge compared to text models

## Cost Optimization

- Use Kontext Pro for experimentation
- Switch to Kontext Max only for final renders
- Batch similar edits to reduce API calls
- Cache results for iterative workflows