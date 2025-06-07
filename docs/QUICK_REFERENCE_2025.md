# AliceMultiverse Quick Reference (January 2025)

## 🎯 Prompt Management

### CLI Commands
```bash
# Search for effective prompts
alice prompts search "cyberpunk" --min-rating 8

# List prompts by category
alice prompts list --category image_generation

# Show prompt details
alice prompts show <prompt_id>

# Export prompts
alice prompts export --format yaml --output my_prompts.yaml
```

### MCP Tools (in Claude)
```
"Find effective prompts for dark fantasy images"
"Search prompts that worked well with Midjourney"
"Create a new prompt template for product photography"
"Track this prompt's effectiveness"
```

### Video Generation (in Claude)
```
"Generate a 5-second video of ocean waves with sound using Veo 3"
"Create a video with speech: 'News anchor saying Breaking news...'"
"Make a vertical video for social media with Veo 3"
"Generate a silent video of clouds moving over mountains"
```

## 🎬 Video Generation

### Google Veo 3
```python
# Basic video
alice generate video --model veo-3 \
  --prompt "Sunset timelapse over city" \
  --duration 5

# With audio
alice generate video --model veo-3 --audio \
  --prompt "Thunderstorm with rain sounds" \
  --duration 5

# With speech
alice generate video --model veo-3 --audio \
  --prompt 'News anchor saying "Breaking news..."' \
  --duration 5
```

### Other Video Models
- `kling-v2.1-pro`: 10s videos, professional quality
- `kling-v2.1-master`: Highest quality Kling
- `svd`: Stable Video Diffusion (open source)
- `mmaudio-v2`: Add audio to existing videos

## 🔄 Transition Effects

### Subject Morphing
```bash
# Analyze two shots for morphing
alice transitions morph face1.jpg face2.jpg -o morph.json

# Export for After Effects
alice transitions morph shot1.jpg shot2.jpg -f after_effects
```

### Color Flow
```bash
# Analyze color transitions
alice transitions colorflow sunset.jpg night.jpg -o flow.json

# Analyze sequence
alice transitions colorflow *.jpg -o sequence_flow.json
```

### Match Cuts
```bash
# Find match cuts in sequence
alice transitions matchcuts *.jpg -o cuts.json

# With custom threshold
alice transitions matchcuts *.jpg -t 0.6 -o cuts.edl
```

### Portal Effects
```bash
# Detect portals for transition
alice transitions portal door.jpg room.jpg -o portal.jsx

# With verbose output
alice transitions portal entrance.jpg exit.jpg -v
```

### Visual Rhythm
```bash
# Analyze pacing
alice transitions rhythm *.jpg -o rhythm.json

# With target duration
alice transitions rhythm *.jpg -d 30 -o timed.json

# Sync to BPM
alice transitions rhythm *.jpg -b 120 -o beat_sync.csv
```

## 📊 Quick Stats

### Costs (Approximate)
| Model | Type | Cost |
|-------|------|------|
| Veo 3 (no audio) | Video | $0.50/sec |
| Veo 3 (with audio) | Video | $0.75/sec |
| Kling 2.1 Pro | Video | $0.25/sec |
| Kling 2.1 Master | Video | $0.30/sec |
| FLUX Pro | Image | $0.05/image |
| Imagen 3 | Image | $0.03/image |

### Video Durations
- Veo 3: 5-8 seconds
- Kling 2.1: 5-10 seconds  
- SVD: 2-4 seconds

### Export Formats
- **Transitions**: JSON, After Effects JSX, EDL, CSV
- **Videos**: MP4, MOV
- **Timelines**: EDL, XML (Resolve), JSON (CapCut)

## 🎯 Common Workflows

### 1. Music Video Creation
```bash
# Analyze music
alice music analyze song.mp3 -o beats.json

# Generate storyboard
alice video storyboard images/ -o storyboard.json

# Create timeline
alice video timeline images/ --music song.mp3 --style music_video

# Export for editing
alice export timeline -f edl -o music_video.edl
```

### 2. Transition Sequence
```bash
# Find all transition opportunities
alice transitions analyze *.jpg -o all_transitions.json

# Create match cut sequence
alice transitions matchcuts *.jpg -t 0.7 -o cuts.edl

# Add rhythm timing
alice transitions rhythm *.jpg -b 128 -o timing.csv
```

### 3. Prompt Optimization
```bash
# Find what worked
alice prompts search --min-success-rate 0.8

# Analyze batch performance
alice prompts analyze --provider midjourney --last-week

# Export best prompts
alice prompts export --top-rated --output best_prompts.yaml
```

## 🔧 Configuration

### Enable Features
```yaml
# settings.yaml
understanding:
  enabled: true
  providers: [anthropic, openai, google]

transitions:
  default_threshold: 0.7
  export_format: after_effects

prompts:
  track_effectiveness: true
  min_success_for_suggestion: 0.8
```

### API Keys Required
```bash
# For video generation
export FAL_KEY="your-key"

# For understanding
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_AI_API_KEY="your-key"
```

## 📚 Documentation

- **Guides**: `docs/user-guide/`
- **Examples**: `examples/advanced/`
- **API Reference**: `docs/api/`
- **Architecture**: `docs/architecture/`

## 🆘 Troubleshooting

### Common Issues

**No prompts found**
- Check if prompts exist: `ls ~/.alice/prompts/`
- Rebuild index: `alice prompts reindex`

**Transition not detected**
- Lower threshold: `-t 0.5`
- Check image quality
- Ensure clear shapes/motion

**Video generation fails**
- Check API key: `echo $FAL_KEY`
- Verify model name
- Check rate limits

**High costs**
- Use `--dry-run` to preview
- Check cost tracking: `alice cost report`
- Set budgets: `alice cost set-budget --daily 10`

---

For detailed help: `alice --help` or check the comprehensive guides.