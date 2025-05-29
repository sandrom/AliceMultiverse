# Kling Video Generation Guide

AliceMultiverse supports Kling video generation through two providers:
1. **fal.ai** - Simple integration, no direct Kling account needed
2. **Official Kling API** - Direct access with more features and control

## Provider Comparison

| Feature | fal.ai | Official Kling API |
|---------|--------|-------------------|
| Authentication | FAL_KEY | KLING_API_KEY |
| Pricing | fal.ai markup | Direct Kling pricing |
| Models | Kling 1.0, 2.0, 2.1 | All latest models |
| Features | Basic video gen | Full feature set |
| Rate Limits | fal.ai limits | Kling subscription limits |
| Region | Global | Global + China |

## Using Kling via fal.ai

Simple and quick setup through fal.ai:

```python
from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType

# Configure fal.ai
provider = get_provider("fal", api_key="your-fal-key")

# Generate video with Kling 2.1
request = GenerationRequest(
    prompt="A serene lake at sunset with mountains in the background",
    generation_type=GenerationType.VIDEO,
    model="kling-v2.1-master-text",  # Highest quality
    parameters={
        "duration": "5",  # 5 or 10 seconds
        "aspect_ratio": "16:9",
        "cfg_scale": 0.5
    }
)

result = await provider.generate(request)
```

### Available Models via fal.ai
- `kling-v1-text` / `kling-v1-image`
- `kling-v2-text` / `kling-v2-image`
- `kling-v2.1-pro-text` / `kling-v2.1-pro-image`
- `kling-v2.1-master-text` / `kling-v2.1-master-image`
- `kling-elements`, `kling-lipsync`

## Using Official Kling API

Direct access with full features:

```python
# Configure Kling API
export KLING_API_KEY="your-kling-api-key"

# Use official provider
provider = get_provider("kling", region="global")  # or "cn" for China

# Professional mode video generation
request = GenerationRequest(
    prompt="Cinematic shot of a futuristic city",
    generation_type=GenerationType.VIDEO,
    model="kling-v2.1-pro-text",
    parameters={
        "duration": 10,  # Up to 10 seconds
        "mode": "professional",  # Higher quality
        "camera_motion": "zoom_in",
        "aspect_ratio": "21:9"  # Cinematic
    }
)

result = await provider.generate(request)
```

### Exclusive Official API Features

#### 1. Video Extension
```python
# Extend an existing video
request = GenerationRequest(
    prompt="Continue with a dramatic reveal",
    model="kling-extend",
    reference_assets=["/path/to/video.mp4"],
    parameters={
        "extend_duration": 5  # Add 5 more seconds
    }
)
```

#### 2. Lip Sync
```python
# Sync video with audio
request = GenerationRequest(
    prompt="Character speaking",
    model="kling-lipsync",
    reference_assets=[
        "/path/to/video.mp4",
        "/path/to/audio.mp3"
    ]
)
```

#### 3. Video Effects
```python
# Apply effects to existing video
request = GenerationRequest(
    prompt="Add slow motion effect",
    model="kling-effects",
    reference_assets=["/path/to/video.mp4"],
    parameters={
        "effect": "slow_motion",
        "intensity": 0.5
    }
)
```

#### 4. Kolors Image Generation
```python
# High-quality image generation
request = GenerationRequest(
    prompt="Detailed fantasy landscape",
    generation_type=GenerationType.IMAGE,
    model="kolors-v2-pro",
    parameters={
        "width": 1920,
        "height": 1080,
        "style": "fantasy_art"
    }
)
```

#### 5. Virtual Try-On
```python
# AI fashion try-on
request = GenerationRequest(
    prompt="Natural pose",
    model="kling-tryon",
    reference_assets=[
        "/path/to/person.jpg",
        "/path/to/garment.jpg"
    ]
)
```

## Model Selection Guide

### For Best Quality
- **Master**: `kling-v2.1-master-text` (highest quality, slower)
- **Pro**: `kling-v2.1-pro-text` (professional quality, balanced)
- **Standard**: `kling-v2.1-text` (good quality, faster)

### For Specific Needs
- **Cinematic**: Use Master with 21:9 aspect ratio
- **Social Media**: Use Pro with 9:16 (vertical) or 1:1 (square)
- **Quick Previews**: Use Standard mode
- **Character Animation**: Use image-to-video variants

## Cost Optimization

### Via fal.ai
- Fixed pricing per generation
- No subscription needed
- Pay-as-you-go model

### Via Official API
- Unit-based pricing (1 unit = $0.14)
- Standard 5s video = 2 units = $0.28
- Professional mode costs ~50% more
- Bulk packages available

### Tips
1. Use Standard mode for iterations
2. Switch to Pro/Master for final renders
3. Generate at lower resolution first
4. Use shorter durations for testing

## Camera Motion Options

Available for both providers:
- `static` - No camera movement
- `zoom_in` - Slow zoom in
- `zoom_out` - Slow zoom out
- `pan_left` - Pan to the left
- `pan_right` - Pan to the right
- `tilt_up` - Tilt camera up
- `tilt_down` - Tilt camera down
- `auto` - AI decides (default)

## Best Practices

1. **Prompt Engineering**
   - Be specific about motion and action
   - Describe camera angles explicitly
   - Include style keywords (cinematic, realistic, etc.)

2. **Image-to-Video**
   - Use high-quality source images
   - Match aspect ratios
   - Describe desired motion clearly

3. **Performance**
   - Videos take 2-10 minutes to generate
   - Use webhooks for production (if supported)
   - Cache results for iterative workflows

4. **Quality Settings**
   - Start with standard for drafts
   - Use professional for client work
   - Master mode for hero shots

## Error Handling

Both providers handle common errors:
- Rate limiting (automatic retry)
- Insufficient credits
- Invalid parameters
- Network timeouts

The official API provides more detailed error messages and status tracking.

## Choosing a Provider

**Use fal.ai when:**
- You want simple setup
- You're already using fal.ai for other models
- You need basic video generation
- You prefer consolidated billing

**Use Official Kling API when:**
- You need advanced features (extend, lipsync, effects)
- You want direct pricing without markup
- You need higher rate limits
- You're operating in China region
- You want access to latest features immediately