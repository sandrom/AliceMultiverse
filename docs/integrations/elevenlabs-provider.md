# ElevenLabs Provider Integration

The ElevenLabs provider enables AI-powered sound effects generation from text descriptions. Create cinematic sound design, game audio, foley effects, and ambient soundscapes using natural language prompts.

## Features

- **Text-to-Sound Effects**: Generate any sound from text descriptions
- **Duration Control**: Specify exact duration (up to 22 seconds)
- **Prompt Influence**: Control how closely the output matches your description
- **Multiple Formats**: MP3 and PCM/WAV output with various quality options
- **Cinematic Quality**: Professional-grade sound effects for media production
- **Royalty-Free**: All generated sounds can be used commercially

## Setup

### API Key

1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Get your API key from the dashboard
3. Set the environment variable:
   ```bash
   export ELEVENLABS_API_KEY="your-api-key"
   ```

### Installation

The ElevenLabs provider is included with AliceMultiverse. No additional dependencies required.

## Basic Usage

### Simple Sound Effect

```python
from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType

# Initialize provider
provider = get_provider("elevenlabs")

# Generate a sound effect
request = GenerationRequest(
    prompt="dog barking happily",
    generation_type=GenerationType.AUDIO
)

result = await provider.generate(request)
print(f"Generated: {result.file_path}")
```

### With Duration Control

```python
request = GenerationRequest(
    prompt="thunderstorm with heavy rain",
    generation_type=GenerationType.AUDIO,
    parameters={
        "duration_seconds": 15,  # 15-second storm
        "prompt_influence": 0.7  # Higher accuracy
    }
)
```

## Parameters

### Core Parameters

- **prompt** (required): Text description of the sound
- **generation_type**: Must be `GenerationType.AUDIO`
- **model**: Default is "sound-effects" (currently only model)

### Optional Parameters

- **duration_seconds**: Length of sound (max 22 seconds)
  - If not specified, automatically determines optimal duration
- **prompt_influence**: How closely to match prompt (0.0-1.0)
  - Default: 0.3
  - Higher values = more literal interpretation
  - Lower values = more creative variation
- **output_format**: Audio format and quality
  - Standard: `mp3_44100_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`
  - Pro tier: `mp3_44100_192`, `pcm_44100`

## Output Formats

### Standard Formats (All Tiers)
- `mp3_44100_32`: MP3 at 32 kbps
- `mp3_44100_64`: MP3 at 64 kbps
- `mp3_44100_96`: MP3 at 96 kbps
- `mp3_44100_128`: MP3 at 128 kbps (default)

### Premium Formats (Pro Tier)
- `mp3_44100_192`: High-quality MP3 at 192 kbps
- `pcm_16000`: PCM 16kHz (WAV)
- `pcm_22050`: PCM 22.05kHz (WAV)
- `pcm_24000`: PCM 24kHz (WAV)
- `pcm_44100`: Studio-quality PCM 44.1kHz (WAV)

## Use Cases

### 1. Cinematic Sound Design

```python
cinematic_sounds = [
    "spaceship engine starting with deep rumble",
    "sword unsheathing with metallic ring",
    "magical spell casting with ethereal chimes"
]

for prompt in cinematic_sounds:
    request = GenerationRequest(
        prompt=prompt,
        generation_type=GenerationType.AUDIO,
        parameters={"prompt_influence": 0.4}
    )
    result = await provider.generate(request)
```

### 2. Game Audio Effects

```python
# Short, punchy game sounds
game_sounds = {
    "coin_collect": "bright coin pickup chime",
    "jump": "character jump whoosh",
    "powerup": "ascending power-up tones"
}

for name, prompt in game_sounds.items():
    request = GenerationRequest(
        prompt=prompt,
        generation_type=GenerationType.AUDIO,
        parameters={
            "duration_seconds": 2,  # Short for games
            "prompt_influence": 0.6
        }
    )
```

### 3. Ambient Soundscapes

```python
# Longer ambient tracks
request = GenerationRequest(
    prompt="peaceful forest with birds and gentle wind",
    generation_type=GenerationType.AUDIO,
    parameters={
        "duration_seconds": 20,
        "prompt_influence": 0.3  # More variation
    }
)
```

### 4. Foley Effects

```python
foley_sounds = [
    "footsteps on wooden floor",
    "door creaking open slowly",
    "paper rustling",
    "chair scraping on floor"
]
```

## Best Practices

### Prompt Writing

1. **Be Specific**: "heavy wooden door creaking" > "door sound"
2. **Include Context**: "footsteps on gravel approaching slowly"
3. **Describe Quality**: "bright", "muffled", "echoing", "sharp"
4. **Use Audio Terms**: "low rumble", "high-pitched", "staccato"

### Duration Guidelines

- **UI/Game sounds**: 1-3 seconds
- **Cinematic effects**: 3-10 seconds
- **Ambient loops**: 15-22 seconds
- **Let auto-determine**: Omit duration for optimal length

### Prompt Influence Settings

- **0.1-0.3**: Maximum variation, natural sounds
- **0.3-0.5**: Balanced (default range)
- **0.5-0.7**: Close match to description
- **0.7-1.0**: Very literal interpretation

## Cost Information

- **Pricing**: ~$0.08 per generation (estimated)
- **No duration-based pricing**: Same cost for 1s or 22s
- **Format doesn't affect cost**: Premium formats same price

## Error Handling

```python
try:
    result = await provider.generate(request)
except RateLimitError:
    print("Too many requests, please wait")
except AuthenticationError:
    print("Invalid API key")
except GenerationError as e:
    print(f"Generation failed: {e}")
```

## Advanced Features

### Batch Generation

```python
async def generate_sound_library(prompts: list):
    results = []
    for prompt in prompts:
        request = GenerationRequest(
            prompt=prompt,
            generation_type=GenerationType.AUDIO
        )
        result = await provider.generate(request)
        results.append(result)
    return results
```

### Custom Output Paths

```python
from pathlib import Path

request = GenerationRequest(
    prompt="explosion",
    generation_type=GenerationType.AUDIO,
    output_path=Path("assets/sfx/explosion.mp3")
)
```

## Limitations

- **Maximum duration**: 22 seconds
- **Single generation**: No batch API currently
- **Model selection**: Only "sound-effects" model available
- **No streaming**: Must wait for complete generation

## Tips for Quality

1. **Layer sounds**: Generate components separately
2. **Use descriptive adjectives**: "metallic", "wooden", "glassy"
3. **Specify environment**: "in a large hall", "outdoors", "underwater"
4. **Include motion**: "approaching", "fading away", "spinning"
5. **Describe texture**: "smooth", "rough", "crisp", "muffled"

## Integration with Workflows

### Video Production Workflow

```python
# Generate sound effects for video scenes
async def create_scene_audio(scene_descriptions: dict):
    audio_tracks = {}
    
    for scene, sounds in scene_descriptions.items():
        scene_audio = []
        for sound in sounds:
            request = GenerationRequest(
                prompt=sound,
                generation_type=GenerationType.AUDIO
            )
            result = await provider.generate(request)
            scene_audio.append(result)
        
        audio_tracks[scene] = scene_audio
    
    return audio_tracks
```

### Multi-Modal Generation

```python
# Combine with other providers
image = await image_provider.generate(image_request)
sound = await elevenlabs_provider.generate(sound_request)
# Combine in video editing software
```

## Troubleshooting

### Common Issues

1. **"Invalid API key"**: Check ELEVENLABS_API_KEY is set correctly
2. **"Rate limit exceeded"**: Add delays between requests
3. **"Invalid duration"**: Ensure duration ≤ 22 seconds
4. **Format not available**: Some formats require Pro subscription

### Debug Mode

```python
import logging
logging.getLogger("alicemultiverse.providers.elevenlabs_provider").setLevel(logging.DEBUG)
```

## See Also

- [ElevenLabs Documentation](https://elevenlabs.io/docs)
- [Sound Effects Best Practices](https://elevenlabs.io/docs/capabilities/sound-effects)
- [API Reference](https://elevenlabs.io/docs/api-reference/text-to-sound-effects)