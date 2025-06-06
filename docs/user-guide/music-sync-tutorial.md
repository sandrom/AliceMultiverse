# Music Sync Tutorial

This comprehensive guide covers how to create perfectly synchronized music videos using AliceMultiverse's beat detection and timeline automation features.

## Overview

AliceMultiverse can analyze your music to automatically:
- Detect beats, downbeats, and musical sections
- Match image energy to music intensity
- Create beat-synced timelines
- Export to your favorite editing software

## Prerequisites

- Music file (MP3, WAV, or M4A format)
- Collection of images or video clips
- Alice installed with music analysis dependencies:
  ```bash
  pip install librosa>=0.10.0
  ```

## Quick Start

### 1. Basic Music Video Creation

```python
# Through Claude MCP
"Create a music video using techno_track.mp3 and my cyberpunk images"

# Alice will:
# 1. Analyze the music structure
# 2. Select appropriate images
# 3. Create beat-synced timeline
# 4. Export for editing
```

### 2. Manual Workflow

```bash
# Analyze music first
alice analyze_music background_music.mp3

# Review the analysis
# - BPM: 128
# - Sections: Intro (0-16s), Buildup (16-32s), Drop (32-64s)
# - Energy peaks at: 32s, 48s, 96s

# Create timeline with specific sync
alice sync_images_to_music \
  --music background_music.mp3 \
  --images ./selected_images/ \
  --sync-mode beat \
  --output timeline.xml
```

## Music Analysis Deep Dive

### Understanding the Analysis Output

When you analyze music, Alice provides:

```json
{
  "tempo": 128.5,
  "beats": [0.469, 0.938, 1.406, ...],
  "downbeats": [0.469, 2.344, 4.219, ...],
  "sections": [
    {
      "name": "intro",
      "start": 0.0,
      "end": 15.5,
      "energy": 0.3,
      "mood": "building"
    },
    {
      "name": "verse",
      "start": 15.5,
      "end": 31.0,
      "energy": 0.6,
      "mood": "steady"
    },
    {
      "name": "drop",
      "start": 31.0,
      "end": 46.5,
      "energy": 1.0,
      "mood": "intense"
    }
  ]
}
```

### Key Concepts

**Beats**: Individual beat positions (typically quarter notes)
- Use for fast-paced, energetic cuts
- Good for action sequences or high-energy sections

**Downbeats**: Strong beats (typically first beat of each measure)
- Use for more relaxed pacing
- Good for establishing shots or emotional moments

**Sections**: Musical structure (intro, verse, chorus, etc.)
- Use for narrative progression
- Match visual themes to musical sections

## Sync Modes Explained

### 1. Beat Sync
```python
"Sync images to every beat"
# or
alice sync_images_to_music --sync-mode beat
```

**Characteristics:**
- Cuts on every beat
- Fast-paced editing
- High energy
- Best for: Action sequences, dance videos, energetic content

**Example Timeline:**
```
Beat:  |  |  |  |  |  |  |  |
Image: 1  2  3  4  5  6  7  8
Time:  0  0.5 1  1.5 2  2.5 3  3.5
```

### 2. Downbeat Sync
```python
"Sync images to downbeats only"
# or
alice sync_images_to_music --sync-mode downbeat
```

**Characteristics:**
- Cuts on strong beats only
- More breathing room
- Measured pacing
- Best for: Storytelling, emotional content, documentaries

**Example Timeline:**
```
Beat:  |  .  .  .  |  .  .  .  |
Image: 1           2           3
Time:  0           2           4
```

### 3. Section Sync
```python
"Change images at section boundaries"
# or
alice sync_images_to_music --sync-mode section
```

**Characteristics:**
- Cuts at major musical changes
- Long takes
- Narrative focus
- Best for: Story arcs, thematic progressions

**Example Timeline:**
```
Section: |---Intro---|---Verse---|---Chorus---|
Image:   1           2           3
Time:    0           16          32
```

## Energy Matching

### Automatic Energy Matching

Alice analyzes both music energy and image characteristics:

```python
"Match energetic images to high-energy music sections"
```

**How it works:**
1. Music energy is calculated from:
   - Amplitude/volume
   - Spectral density
   - Tempo changes
   - Harmonic complexity

2. Image energy is derived from:
   - Color vibrancy
   - Contrast levels
   - Motion blur
   - Compositional complexity

3. Matching algorithm:
   - Low energy music (0-0.3) → Calm, minimal images
   - Medium energy (0.3-0.7) → Balanced, steady images
   - High energy (0.7-1.0) → Vibrant, complex images

### Manual Energy Control

```python
# Override automatic matching
"Use calm images for the intro, energetic for the drop"

# Or specify exact mappings
alice sync_images_to_music \
  --energy-map "intro:calm,verse:medium,drop:intense"
```

## Timeline Creation Strategies

### 1. Narrative Arc
```python
# Tell a story following music structure
"Create timeline with establishing shots in intro, 
 action in verse, climax at drop"
```

### 2. Visual Rhythm
```python
# Match visual complexity to musical complexity
"Use simple compositions for simple sections,
 complex layered images for dense musical parts"
```

### 3. Color Progression
```python
# Progress through color schemes
"Start with cool colors, warm up through verse,
 hot colors at drop, cool down in outro"
```

## Advanced Techniques

### Fine-Tuning Cut Points

```python
# Offset cuts slightly before beat for anticipation
alice sync_images_to_music --beat-offset -0.05

# Add variation to prevent monotony
alice sync_images_to_music --cut-variation 0.2
```

### Transition Matching

```python
# Match transition types to music
"Use hard cuts on kicks, dissolves on sustained notes"

# Automatic transition suggestion
alice suggest_cuts_for_mood --music track.mp3
```

### Multi-Layer Synchronization

```python
# Sync multiple visual layers
"Create main timeline on downbeats,
 overlay effects on hi-hats,
 color changes on bass hits"
```

## Practical Examples

### Example 1: EDM Music Video

```python
# High-energy electronic music
music = "edm_banger.mp3"
images = "neon_cyberpunk_collection"

# Strategy:
# - Fast cuts on beats during drops
# - Slower during breakdowns
# - Match neon intensity to bass energy

"Create EDM video with fast cuts on drops,
 breathing room on breakdowns,
 sync neon intensity to bass"
```

### Example 2: Indie Rock Video

```python
# Moderate tempo rock
music = "indie_rock.mp3"
images = "urban_photography"

# Strategy:
# - Cut on drumbeats
# - Hold shots during guitar solos
# - Match mood to lyrics

"Sync to drum pattern, hold during solos,
 use moody shots for verses, bright for chorus"
```

### Example 3: Ambient Soundscape

```python
# Slow, atmospheric music
music = "ambient_piece.mp3"
images = "nature_timelapses"

# Strategy:
# - Very slow transitions
# - Sync to harmonic changes
# - Let visuals breathe

"Use section sync with long crossfades,
 match scene changes to harmonic shifts"
```

## Manual Adjustments

### After Automatic Sync

The timeline is just a starting point. Common adjustments:

1. **Extend hero shots**
   ```python
   "Make the sunset shot at 1:32 last longer"
   ```

2. **Adjust transition timing**
   ```python
   "Move the cut at 0:45 to hit exactly on the snare"
   ```

3. **Replace specific shots**
   ```python
   "Replace shot 23 with a close-up"
   ```

### Timeline Editing Tips

1. **Preview in context**: Always preview with music
2. **Trust your instincts**: Override automation when it feels wrong
3. **Consider viewer fatigue**: Don't cut too fast for too long
4. **Leave breathing room**: Not every beat needs a cut

## Export Settings

### For DaVinci Resolve

```python
# Best settings for Resolve
alice export_timeline \
  --format xml \
  --frame-rate 30 \
  --include-beat-markers \
  --generate-proxies
```

### For CapCut Mobile

```python
# Optimized for mobile editing
alice export_timeline \
  --format capcut \
  --optimize-mobile \
  --max-resolution 1080p
```

## Troubleshooting

### Common Issues

**Problem**: Cuts feel off-beat
- Solution: Check frame rate matches project (30fps vs 24fps)
- Try: `--beat-offset 0.03` to compensate

**Problem**: Too many cuts, feels frantic
- Solution: Use downbeat or section sync instead
- Try: `--min-shot-duration 1.0`

**Problem**: Energy matching seems wrong
- Solution: Manually tag image energy levels
- Try: Energy mapping override

**Problem**: Music analysis seems incorrect
- Solution: Pre-process audio (normalize, remove silence)
- Try: Different audio format (WAV instead of MP3)

## Best Practices

### 1. Music Selection
- **Clear beat**: Electronic, hip-hop, pop work best
- **Dynamic range**: Variety creates interest
- **Section structure**: Clear verses/choruses help

### 2. Image Preparation
- **Consistent quality**: Similar resolution/style
- **Variety**: Mix of shots (wide, medium, close)
- **Energy range**: Calm to intense options

### 3. Workflow Optimization
- **Analyze first**: Review music structure before syncing
- **Start simple**: Begin with downbeat sync, refine later
- **Iterate**: First pass won't be perfect

### 4. Performance Tips
- **Batch analyze**: Process multiple songs at once
- **Cache results**: Reuse music analysis
- **Proxy generation**: For smooth preview

## Integration with Other Features

### Style Clustering
```python
# Group similar shots together
"Use style clusters for visual consistency,
 change cluster every 8 bars"
```

### Transition Analysis
```python
# Combine with motion matching
"Analyze transitions between shots,
 ensure smooth visual flow on beat"
```

### Scene Detection
```python
# For video sources
"Detect scenes in footage,
 sync scene changes to musical sections"
```

## Next Steps

1. **Experiment with sync modes**: Try each mode with your content
2. **Build a template library**: Save successful sync patterns
3. **Study references**: Analyze professional music videos
4. **Share your results**: Export and get feedback

## Additional Resources

- [Video Export Guide](./video-export-guide.md) - Detailed export options
- [Style Clustering Guide](./style-clustering-guide.md) - Group similar content
- [Workflow Examples](../examples/video_workflow_example.md) - Complete workflows

---

**Remember**: The algorithm provides a starting point, but your creative vision makes the final decisions. Use the sync as a foundation, then refine to match your artistic intent.