# Freepik Provider Integration

The Freepik provider gives you access to **Magnific upscaler** and **Mystic image generation** through a unified API.

## Overview

- **Magnific**: State-of-the-art AI upscaler supporting up to 16K resolution
- **Mystic**: Photorealistic image generation model based on Flux
- **Cost-effective**: Pay-as-you-go pricing starting at €0.004 per image
- **No subscription required**: Just API credits

## Setup

### 1. Get API Key

1. Visit [Freepik API](https://www.freepik.com/api/)
2. Sign up (new users get €5 free credits)
3. Generate your API key with one click

### 2. Configure Alice

```bash
# Set environment variable
export FREEPIK_API_KEY="your-api-key"

# Or use alice keys setup
alice keys setup
```

## Models

### Magnific Upscaling

| Model | Description | Cost (per MP) |
|-------|-------------|---------------|
| `magnific-sparkle` | Best quality, slower | €0.01 |
| `magnific-illusio` | Balanced quality/speed | €0.008 |
| `magnific-sharpy` | Fast, good for sharp images | €0.006 |

### Mystic Generation

| Model | Description | Cost |
|-------|-------------|------|
| `mystic` | Standard resolution | €0.004 |
| `mystic-2k` | 2K resolution | €0.006 |
| `mystic-4k` | 4K resolution | €0.008 |

## Usage Examples

### Basic Upscaling (2x)

```python
from alicemultiverse.providers.registry import get_provider
from alicemultiverse.providers.base import GenerateRequest, GenerationType

provider = get_provider("freepik")

request = GenerateRequest(
    prompt="",
    model="magnific-sparkle",
    provider="freepik",
    generation_type=GenerationType.IMAGE,
    reference_assets=["path/to/input.jpg"],
    parameters={
        "scale": 2,  # 2x upscaling
        "creativity": 0.5,  # Balanced enhancement
        "hdr": 0.5,
    }
)

async with provider:
    result = await provider.generate(request)
    print(f"Upscaled: {result.asset_url}")
```

### High-Quality 4K Upscaling

```python
request = GenerateRequest(
    prompt="",
    model="magnific-sparkle",
    provider="freepik",
    generation_type=GenerationType.IMAGE,
    reference_assets=["input.jpg"],
    parameters={
        "scale": 4,
        "creativity": 0.7,  # More creative enhancement
        "hdr": 0.8,  # Strong HDR
        "resemblance": 0.6,  # Balance between original and enhanced
        "fractality": 0.5,  # Fractal detail
        "detail_refinement": 0.8,  # Fine details
        "style": "cinematic",  # Apply style
    }
)
```

### Mystic Photorealistic Generation

```python
request = GenerateRequest(
    prompt="Professional headshot of a CEO in modern office",
    model="mystic-4k",
    provider="freepik",
    generation_type=GenerationType.IMAGE,
    parameters={
        "negative_prompt": "cartoon, anime, low quality",
        "guidance_scale": 7.5,
        "num_inference_steps": 50,
        "style": "professional",
        "detail": 1.5,
        "seed": 42,  # For reproducibility
    }
)
```

### Style Transfer with Mystic

```python
request = GenerateRequest(
    prompt="Mountain landscape",
    model="mystic",
    provider="freepik",
    generation_type=GenerationType.IMAGE,
    reference_assets=["style_reference.jpg"],  # Style image
    parameters={
        "style_strength": 0.9,  # Strong style influence
        "structure": 0.7,  # Maintain structure
        "lora": "landscape_enhanced",  # Use LoRA
        "lora_strength": 0.8,
    }
)
```

## Parameters

### Magnific Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| `scale` | 2, 4, 8, 16 | Upscaling factor |
| `creativity` | 0-10 | Creative enhancement level |
| `hdr` | 0-10 | HDR enhancement |
| `resemblance` | 0-10 | Similarity to original |
| `fractality` | 0-10 | Fractal detail enhancement |
| `detail_refinement` | 0-10 | Fine detail enhancement |
| `style` | string | Style preset (auto, cinematic, etc.) |

### Mystic Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| `guidance_scale` | 1-10 | Prompt adherence |
| `num_inference_steps` | 10-50 | Quality vs speed |
| `style` | string | Style preset |
| `detail` | 0-2 | Detail level |
| `style_strength` | 0-1 | Style influence |
| `structure` | 0-1 | Structural coherence |
| `seed` | int | Random seed |
| `lora` | string | LoRA model name |
| `lora_strength` | 0-1 | LoRA influence |

## Workflows

### Generate → Upscale Pipeline

```python
# 1. Generate base image
generated = await provider.generate(GenerateRequest(
    prompt="Epic fantasy castle",
    model="mystic",
    provider="freepik",
    generation_type=GenerationType.IMAGE
))

# 2. Upscale to 4K
upscaled = await provider.generate(GenerateRequest(
    prompt="",
    model="magnific-sparkle",
    provider="freepik",
    generation_type=GenerationType.IMAGE,
    reference_assets=[generated.asset_url],
    parameters={"scale": 4, "style": "fantasy"}
))
```

### Batch Upscaling

```python
images = ["img1.jpg", "img2.jpg", "img3.jpg"]

async def upscale_batch(images):
    results = []
    async with provider:
        for img in images:
            request = GenerateRequest(
                prompt="",
                model="magnific-illusio",
                provider="freepik",
                generation_type=GenerationType.IMAGE,
                reference_assets=[img],
                parameters={"scale": 2}
            )
            result = await provider.generate(request)
            results.append(result)
    return results
```

## Cost Optimization

1. **Choose the right engine**:
   - Use `magnific-sharpy` for sharp images needing less enhancement
   - Use `magnific-illusio` for balanced quality/cost
   - Reserve `magnific-sparkle` for hero images

2. **Scale wisely**:
   - 2x scale = 4 megapixels
   - 4x scale = 16 megapixels
   - 8x scale = 64 megapixels
   - Cost scales with output size!

3. **Use Mystic efficiently**:
   - Standard resolution for drafts
   - 4K only for final outputs
   - Batch similar styles together

## Tips & Best Practices

1. **For Upscaling**:
   - Start with good quality inputs
   - Use lower creativity for photographic content
   - Use higher creativity for artistic enhancement
   - Match style parameter to content type

2. **For Generation**:
   - Be specific in prompts
   - Use negative prompts to avoid unwanted elements
   - Experiment with guidance_scale (7-8 usually best)
   - Save seeds for reproducible results

3. **Performance**:
   - Upscaling time increases with scale factor
   - Use webhooks for long operations
   - Cache results to avoid re-processing

## Troubleshooting

### Rate Limits
- Burst: 50 requests/second
- Average: 10 requests/second
- Solution: Implement rate limiting in your code

### Task Timeouts
- Default timeout: 5 minutes
- For 16x upscaling: May take up to 3 minutes
- Solution: Increase timeout for large scales

### API Errors
- Check API key validity
- Verify you have sufficient credits
- Ensure image URLs are accessible
- Check file size limits

## Integration with Alice

The Freepik provider integrates seamlessly with Alice's workflow:

```bash
# Upscale images in your inbox
alice --provider freepik --model magnific-sparkle --upscale 4x

# Generate new images
alice generate "professional headshot" --provider freepik --model mystic-4k
```

## Resources

- [Freepik API Documentation](https://docs.freepik.com/api/)
- [Magnific Website](https://magnific.ai/)
- [API Status](https://status.freepik.com/)
- [Pricing Calculator](https://www.freepik.com/api/pricing)