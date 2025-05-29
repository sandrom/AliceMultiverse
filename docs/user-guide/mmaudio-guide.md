# MMAudio V2 Integration Guide

MMAudio V2 is a multimodal audio generation model that creates contextually appropriate sound for videos. It analyzes video content and generates synchronized audio, including sound effects, ambient noise, and atmospheric sounds.

## Overview

- **Purpose**: Transform silent videos into immersive experiences with AI-generated audio
- **Model**: `mmaudio-v2` (via fal.ai)
- **Input**: Video file (1-30 seconds)
- **Output**: Video with generated audio track
- **Cost**: ~$0.05 per generation

## Usage Examples

### Basic Video-to-Audio Generation

```python
from alicemultiverse.interface import AliceOrchestrator
from alicemultiverse.providers.types import GenerationRequest, GenerationType

async def generate_audio_for_video():
    alice = AliceOrchestrator()
    
    request = GenerationRequest(
        prompt="peaceful nature sounds with birds chirping",
        generation_type=GenerationType.AUDIO,
        model="mmaudio-v2",
        parameters={
            "video_url": "https://example.com/my-nature-video.mp4",
            "duration": 10,  # seconds
            "num_steps": 25  # quality/speed tradeoff
        }
    )
    
    result = await alice.generate_creative_asset(request)
    print(f"Video with audio saved to: {result.file_path}")
```

### Advanced Parameters

```python
request = GenerationRequest(
    prompt="dramatic orchestral music with rising tension",
    generation_type=GenerationType.AUDIO,
    model="mmaudio-v2",
    parameters={
        "video_url": "https://example.com/action-scene.mp4",
        "negative_prompt": "silence, static, noise",
        "duration": 30,  # max duration
        "num_steps": 50,  # higher quality
        "cfg_strength": 6.0,  # stronger prompt adherence
        "seed": 42,  # reproducible results
        "mask_away_clip": False  # keep original audio if any
    }
)
```

### Using Local Video Files

For local video files, you'll need to upload them first or serve them via a local URL:

```python
# Option 1: Upload to a temporary hosting service
# Option 2: Run a local server
# Option 3: Use reference_assets with a file path (requires additional setup)

request = GenerationRequest(
    prompt="footsteps and door creaking sounds",
    generation_type=GenerationType.AUDIO, 
    model="mmaudio-v2",
    reference_assets=["path/to/local/video.mp4"],  # Will be converted to URL
    parameters={
        "duration": 15
    }
)
```

## Prompt Engineering Tips

### Effective Prompts
- **Specific sounds**: "rain falling on metal roof with distant thunder"
- **Mood and atmosphere**: "eerie ambient sounds for horror scene"
- **Musical styles**: "upbeat electronic music with synth bass"
- **Environmental audio**: "busy city street with traffic and people talking"

### Negative Prompts
Use negative prompts to avoid unwanted sounds:
- "silence, static, distortion"
- "loud, harsh, jarring"
- "music" (if you only want sound effects)
- "speech, talking, voices" (for non-verbal audio)

## Parameters Reference

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `video_url` | string | - | Required | URL of input video |
| `prompt` | string | - | Required | Audio generation prompt |
| `negative_prompt` | string | - | "" | What to avoid |
| `duration` | int | 1-30 | 8 | Audio duration in seconds |
| `num_steps` | int | 4-50 | 25 | Generation steps (quality) |
| `cfg_strength` | float | 0-20 | 4.5 | Prompt adherence strength |
| `seed` | int | 0-65535 | Random | For reproducibility |
| `mask_away_clip` | bool | - | False | Mask the CLIP model |

## Best Practices

1. **Video Duration**: Keep videos under 30 seconds for best results
2. **Prompt Clarity**: Be specific about the type of audio you want
3. **Quality vs Speed**: Use `num_steps=25` for balanced results, 50 for highest quality
4. **Iterative Refinement**: Use seeds to reproduce good results while tweaking prompts
5. **Context Matching**: The AI analyzes video content - ensure prompts align with visuals

## Common Use Cases

### Film Production
```python
# Add foley sounds to action sequence
prompt = "fighting sounds, punches, grunts, and breaking objects"
```

### Social Media Content
```python
# Add background music to lifestyle video
prompt = "chill lo-fi hip hop beat with soft melodies"
```

### Educational Content
```python
# Add narration-friendly background
prompt = "subtle ambient music, soft and unobtrusive"
```

### Game Development
```python
# Generate environmental audio
prompt = "medieval tavern ambience with chatter and lute music"
```

## Integration with Alice Workflow

MMAudio fits naturally into multi-stage creative workflows:

```python
# 1. Generate video with Kling
video_result = await alice.generate_creative_asset(
    GenerationRequest(
        prompt="time-lapse of flowers blooming",
        generation_type=GenerationType.VIDEO,
        model="kling-v2.1-pro-text"
    )
)

# 2. Add audio with MMAudio
audio_result = await alice.generate_creative_asset(
    GenerationRequest(
        prompt="gentle nature sounds, soft breeze, birds singing",
        generation_type=GenerationType.AUDIO,
        model="mmaudio-v2",
        parameters={
            "video_url": video_result.file_path.as_uri(),
            "duration": 10
        }
    )
)
```

## Troubleshooting

### Common Issues

1. **"video_url required" error**: Ensure you're providing a valid video URL
2. **Duration mismatch**: Audio duration can differ from video - trim as needed
3. **Quality issues**: Increase `num_steps` and `cfg_strength` for better results
4. **Inappropriate audio**: Refine prompts and use negative prompts

### Performance Tips

- Process videos in batches during off-peak hours
- Cache generated audio for similar videos
- Use lower `num_steps` for draft versions
- Consider video resolution impact on processing time

## Future Enhancements

Planned improvements for MMAudio integration:
- Automatic local file upload handling
- Batch processing support
- Audio style presets
- Integration with video editing workflows
- Real-time preview generation