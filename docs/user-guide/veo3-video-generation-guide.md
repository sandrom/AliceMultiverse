# Google Veo 3 Video Generation Guide

Use Google's state-of-the-art Veo 3 model for creating videos with native audio, speech, and exceptional realism through AliceMultiverse.

## Overview

Google Veo 3 is the latest advancement in AI video generation, offering:
- **Native Audio Generation**: Creates ambient sounds, music, and effects
- **Speech Capabilities**: Generate dialogue with accurate lip sync
- **Superior Physics**: Realistic fluid dynamics, object interactions
- **Prompt Adherence**: Better understanding of complex descriptions
- **8-Second Videos**: Longer than most competitors

## Quick Start

### Basic Video Generation

```python
from alicemultiverse.providers.fal_provider import FalProvider
from alicemultiverse.providers.types import GenerationRequest, GenerationType

# Generate a simple video
provider = FalProvider()
request = GenerationRequest(
    prompt="A peaceful beach at sunset with waves gently rolling in",
    model="veo-3",
    generation_type=GenerationType.VIDEO,
    parameters={
        "duration": 5,
        "aspect_ratio": "16:9",
        "enable_audio": False
    }
)
result = await provider.generate(request)
```

### Video with Audio

```python
# Enable native audio generation
request = GenerationRequest(
    prompt="A thunderstorm approaching over mountains with lightning and rain",
    model="veo-3", 
    generation_type=GenerationType.VIDEO,
    parameters={
        "duration": 5,
        "aspect_ratio": "16:9",
        "enable_audio": True  # Adds realistic sound effects
    }
)
```

## Pricing

Veo 3 pricing on fal.ai:
- **Without Audio**: $0.50 per second ($2.50 for 5s video)
- **With Audio**: $0.75 per second ($3.75 for 5s video)

## Advanced Features

### 1. Speech Generation with Lip Sync

```python
# Generate video with spoken dialogue
request = GenerationRequest(
    prompt='A teacher explaining "The water cycle starts with evaporation" with clear lip sync',
    model="veo-3",
    generation_type=GenerationType.VIDEO,
    parameters={
        "duration": 5,
        "enable_audio": True  # Required for speech
    }
)
```

### 2. Complex Physics Simulation

```python
# Veo 3 excels at realistic physics
physics_prompts = [
    "Honey slowly dripping from a spoon into a jar",
    "Colored ink dispersing in water in slow motion",
    "Sand flowing through an hourglass, particles visible",
    "Soap bubbles floating and popping in sunlight"
]
```

### 3. Camera Movement Control

```python
# Specify camera movements in your prompt
camera_styles = [
    "smooth dolly forward through a forest path",
    "aerial drone shot circling a lighthouse", 
    "handheld POV walking through a busy market",
    "time-lapse of clouds moving over cityscape"
]
```

## Best Practices

### 1. Prompt Engineering for Veo 3

**Structure your prompts with:**
- Subject/Scene description
- Camera movement (if desired)
- Lighting conditions
- Audio expectations (if enabled)

Example:
```
"A master chef preparing sushi in a high-end restaurant kitchen,
close-up shots of knife work, warm lighting from above,
sounds of chopping and sizzling"
```

### 2. Audio Considerations

When `enable_audio=True`:
- Veo 3 automatically generates appropriate sounds
- Mention specific sounds for better control
- Speech requires clear dialogue in quotes
- Ambient sounds match the visual scene

### 3. Aspect Ratios

Supported ratios:
- `16:9` - Standard widescreen (recommended)
- `9:16` - Vertical for social media
- `1:1` - Square format

### 4. Duration Settings

- Default: 5 seconds
- Maximum: 8 seconds (Veo 3 on fal.ai)
- Longer videos = higher cost

## Integration Examples

### Batch Video Generation

```python
async def generate_video_series():
    """Generate multiple related videos."""
    
    scenes = [
        "Sunrise: Empty coffee shop, first light through windows",
        "Morning: Barista arrives, turning on machines", 
        "Busy: Customers filling the shop, steam and chatter",
        "Evening: Last customer leaves, chairs being stacked"
    ]
    
    for i, scene in enumerate(scenes):
        request = GenerationRequest(
            prompt=scene,
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            output_path=Path(f"output/coffee_shop_day/scene_{i+1}"),
            parameters={
                "duration": 5,
                "enable_audio": True,
                "aspect_ratio": "16:9"
            }
        )
        result = await provider.generate(request)
```

### Style Consistency

```python
# Maintain consistent style across videos
style_suffix = ", cinematic color grading, shallow depth of field, 24fps film look"

prompts = [
    f"Opening shot of vintage car on highway{style_suffix}",
    f"Driver's hands on steering wheel{style_suffix}",
    f"Landscape rushing by through window{style_suffix}"
]
```

## Comparison with Other Models

| Feature | Veo 3 | Kling 2.1 | Runway Gen-3 |
|---------|--------|-----------|--------------|
| Max Duration | 8s | 10s | 10s |
| Native Audio | ✓ | ✗ | ✗ |
| Speech + Lip Sync | ✓ | Limited | ✗ |
| Physics Quality | Excellent | Good | Good |
| Prompt Following | Excellent | Good | Fair |
| Cost per Second | $0.50-0.75 | $0.25-0.30 | $0.50 |

## Limitations

1. **Access**: Currently through fal.ai API (Google Vertex AI requires allowlist)
2. **Duration**: Maximum 8 seconds per generation
3. **Resolution**: Output resolution not directly controllable
4. **Queue Times**: May experience delays during peak usage

## Tips and Tricks

### 1. Optimize Costs
- Use `enable_audio=False` unless sound is essential
- Test with shorter durations first
- Batch similar videos to refine prompts

### 2. Better Results
- Be specific about lighting and time of day
- Include camera movement for dynamic shots
- Mention materials and textures explicitly
- Use cinematography terms (dolly, pan, tilt)

### 3. Audio Enhancement
- Describe ambient sounds in detail
- Put dialogue in quotes for speech
- Mention music style if desired
- Specify sound effects timing

## Troubleshooting

### Common Issues

**No audio in output:**
- Ensure `enable_audio=True`
- Check if prompt includes audio cues
- Verify file player supports audio

**Poor physics simulation:**
- Be specific about materials
- Mention speed (slow motion, real-time)
- Describe expected behavior

**Incorrect speech/lip sync:**
- Put exact dialogue in quotes
- Keep sentences short and clear
- Avoid complex pronunciations

## Example Workflows

### 1. Product Showcase
```python
"Luxury watch rotating on pedestal, macro lens revealing intricate gears,
studio lighting with reflections, mechanical ticking sounds"
```

### 2. Educational Content
```python
"Science teacher demonstrating 'This is how photosynthesis works' 
while pointing to plant diagram, classroom setting"
```

### 3. Atmospheric Scenes
```python
"Foggy forest at dawn, deer stepping through mist,
birds chirping, twigs snapping, mystical atmosphere"
```

## API Integration

### Using with MCP Tools

```text
User: Create a video of a cooking scene with sound

Claude: I'll generate a cooking video with audio using Veo 3.
[Generates video with sizzling, chopping sounds]
```

### Direct CLI Usage

```bash
# If integrated into CLI
alice generate video --model veo-3 --audio \
  --prompt "Chef preparing pasta in Italian kitchen" \
  --duration 5 --output cooking_demo.mp4
```

## Summary

Google Veo 3 through fal.ai offers:
- State-of-the-art video generation
- Unique native audio capabilities
- Excellent physics and realism
- Speech generation with lip sync
- Competitive pricing for quality

Best for:
- Videos requiring realistic sound
- Dialogue and presentation content
- Physics demonstrations
- High-quality cinematic shots

For more details:
- [fal.ai Veo 3 Documentation](https://fal.ai/models/fal-ai/veo3)
- [Video Creation Workflow Guide](video-creation-workflow-guide.md)
- [Cost Optimization Guide](api-cost-optimization-guide.md)