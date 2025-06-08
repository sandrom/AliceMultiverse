# Video Generation Providers

This guide covers the new video generation providers added to AliceMultiverse.

## Overview

AliceMultiverse now supports four additional cutting-edge video generation providers:

1. **Runway Gen-3 Alpha** - Professional quality video generation
2. **Pika Labs** - HD video with fine-grained ingredient control  
3. **Luma Dream Machine** - High-quality video with perfect loops and keyframes
4. **MiniMax Hailuo** - Competitive pricing with Chinese language optimization

## Provider Comparison

| Provider | Quality | Speed | Cost (5s) | Special Features |
|----------|---------|-------|-----------|------------------|
| Runway Gen-3 Alpha | ⭐⭐⭐⭐⭐ | Medium | $0.50 | Professional quality, camera control |
| Runway Gen-3 Turbo | ⭐⭐⭐⭐ | Fast | $0.25 | Faster generation, good quality |
| Pika 2.1 HD | ⭐⭐⭐⭐ | Medium | $0.10 | Ingredient control, HD 1080p |
| Pika 2.1 | ⭐⭐⭐ | Fast | $0.05 | Budget-friendly, good results |
| Luma Dream Machine | ⭐⭐⭐⭐⭐ | Slow | $0.24 | Perfect loops, keyframe control |
| MiniMax Hailuo | ⭐⭐⭐⭐ | Fast | $0.06 | Great pricing, Chinese optimization |

## Runway Provider

Professional-grade video generation with cinematic quality.

### Setup

```bash
export RUNWAY_API_KEY="your-runway-api-key"
```

### Features

- **Models**: `gen3-alpha`, `gen3-alpha-turbo`
- **Duration**: 5-16 seconds
- **Resolution**: Up to 1280x768
- **Camera Control**: zoom, pan, tilt, orbit movements
- **Style Presets**: cinematic, documentary, artistic

### Example Usage

```python
from alicemultiverse.providers import get_provider
from alicemultiverse.providers.types import GenerationRequest

runway = get_provider("runway")

request = GenerationRequest(
    prompt="Epic space battle with detailed spaceships",
    model="gen3-alpha",
    parameters={
        "duration": 10,
        "camera_motion": "slow_zoom_out",
        "style": "cinematic",
        "film_grain": 0.3
    }
)

result = await runway.generate(request)
```

## Pika Labs Provider

Unique ingredient-based control for precise video generation.

### Setup

```bash
export PIKA_API_KEY="your-pika-api-key"
```

### Features

- **Models**: `pika-2.1`, `pika-2.1-hd`
- **Duration**: Fixed 3 seconds
- **Resolution**: Up to 1920x1080 (HD model)
- **Ingredient Control**: Specify characters, objects, environments, styles
- **Aspect Ratios**: 16:9, 9:16, 1:1, 4:3, 3:4

### Ingredient System

```python
pika = get_provider("pika")

request = GenerationRequest(
    prompt="A magical forest scene",
    model="pika-2.1-hd",
    parameters={
        "ingredients": [
            {"type": "character", "description": "fairy with butterfly wings"},
            {"type": "object", "description": "glowing mushrooms"},
            {"type": "environment", "description": "misty forest"},
            {"type": "style", "description": "bioluminescent lighting"}
        ],
        "motion_strength": 0.7
    }
)
```

## Luma Dream Machine Provider

Advanced features for creative control including perfect loops.

### Setup

```bash
export LUMA_API_KEY="your-luma-api-key"
```

### Features

- **Models**: `dream-machine`, `dream-machine-turbo`
- **Special Modes**: loops, keyframes, extend, interpolate
- **Duration**: 1-10 seconds (24-240 frames)
- **Camera Motion**: Multiple preset movements
- **Physics Understanding**: Realistic motion simulation

### Perfect Loops

```python
luma = get_provider("luma")

# Create a seamless loop
request = GenerationRequest(
    prompt="Hypnotic geometric patterns",
    model="luma-loop",
    parameters={
        "loop_frames": 120,  # 5 seconds
        "motion_scale": 0.8
    }
)
```

### Keyframe Animation

```python
# Multi-keyframe control
request = GenerationRequest(
    prompt="Transformation sequence",
    model="luma-keyframes",
    parameters={
        "keyframes": [
            {"frame": 0, "prompt": "A seed in soil"},
            {"frame": 30, "prompt": "A sprout emerging"},
            {"frame": 60, "prompt": "A small plant growing"},
            {"frame": 90, "prompt": "A flower blooming"},
            {"frame": 120, "prompt": "A full bloom flower"}
        ]
    }
)
```

## MiniMax Hailuo Provider

Cost-effective with special features for music videos and style transfer.

### Setup

```bash
export MINIMAX_API_KEY="your-minimax-api-key"
```

### Features

- **Models**: `hailuo-video`, `hailuo-video-pro`
- **Special Modes**: music sync, style transfer
- **Duration**: 1-10 seconds
- **Language**: Optimized for Chinese prompts
- **Competitive Pricing**: Starting at $0.06 per generation

### Music Video Generation

```python
minimax = get_provider("minimax")

# Create music-synced video
request = GenerationRequest(
    prompt="Abstract visuals dancing to the beat",
    model="hailuo-music-video",
    parameters={
        "music_url": "https://example.com/song.mp3",
        "sync_to_beat": True,
        "motion_intensity": 0.9
    }
)
```

### Style Transfer

```python
# Apply artistic style to video
request = GenerationRequest(
    prompt="Modern city street",
    model="hailuo-style-transfer", 
    parameters={
        "style_reference": "https://example.com/vangogh.jpg",
        "style_strength": 0.7,
        "language": "en"  # or "zh" for Chinese
    }
)
```

## Cost Optimization Tips

1. **Use Turbo Models**: Runway and Luma offer turbo variants at 50% cost
2. **Pika for Budget**: Pika 2.1 offers excellent value at $0.05
3. **MiniMax for Volume**: Best pricing for large-scale generation
4. **Test with Short Clips**: Start with minimum duration to test prompts

## Advanced Techniques

### A/B Testing Across Providers

```python
import asyncio

async def compare_providers(prompt: str):
    providers = [
        ("runway", "gen3-alpha-turbo"),
        ("pika", "pika-2.1"),
        ("luma", "dream-machine-turbo"),
        ("minimax", "hailuo-video")
    ]
    
    tasks = []
    for provider_name, model in providers:
        provider = get_provider(provider_name)
        request = GenerationRequest(
            prompt=prompt,
            model=model,
            parameters={"seed": 42}  # Same seed
        )
        tasks.append(provider.generate(request))
    
    results = await asyncio.gather(*tasks)
    return results
```

### Batch Processing

```python
# Process multiple prompts efficiently
async def batch_generate(prompts: list, provider_name: str):
    provider = get_provider(provider_name)
    
    tasks = []
    for prompt in prompts:
        request = GenerationRequest(prompt=prompt)
        tasks.append(provider.generate(request))
    
    return await asyncio.gather(*tasks)
```

## Best Practices

1. **Prompt Engineering**
   - Runway: Cinematic descriptions work best
   - Pika: Use ingredients for precise control
   - Luma: Physics-based descriptions excel
   - MiniMax: Try prompts in Chinese for better results

2. **Cost Management**
   - Set budget limits in provider configuration
   - Use estimate_cost() before generation
   - Monitor usage with provider stats

3. **Quality vs Speed**
   - High quality: Runway Gen-3 Alpha, Luma Dream Machine
   - Fast generation: Pika 2.1, MiniMax Hailuo
   - Balance: Runway Turbo, Luma Turbo

## Troubleshooting

### Common Issues

1. **Rate Limits**
   - All providers have rate limits
   - Implement exponential backoff
   - Use provider health monitoring

2. **Generation Failures**
   - Check prompt for prohibited content
   - Verify API key is valid
   - Ensure parameters are within limits

3. **Quality Issues**
   - Adjust motion strength/scale parameters
   - Try different models
   - Experiment with seed values

## Integration with AliceMultiverse

These providers integrate seamlessly with existing workflows:

```python
# Use in video creation workflow
from alicemultiverse.workflows import VideoCreationWorkflow

workflow = VideoCreationWorkflow(
    video_provider="luma",  # or any new provider
    video_model="dream-machine"
)

# Generate timeline with mixed providers
timeline = await workflow.create_mixed_timeline(
    clips=[
        {"prompt": "Opening shot", "provider": "runway"},
        {"prompt": "Main scene", "provider": "pika"},
        {"prompt": "Closing loop", "provider": "luma", "model": "luma-loop"}
    ]
)
```

## Future Enhancements

Coming soon:
- Provider-specific prompt optimization
- Automatic quality selection based on scene
- Cost-optimized provider routing
- Multi-provider composition tools