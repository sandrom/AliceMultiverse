# Advanced Video Features Guide

This guide covers the latest advanced video creation features in AliceMultiverse.

## Overview

The new features transform AliceMultiverse into a comprehensive video creation platform with:

1. **Web Timeline Preview** - Interactive preview before export
2. **Natural Language Editing** - Chat-based timeline modifications
3. **Multi-Version Export** - Platform-specific adaptations
4. **Performance Analytics** - Track and improve workflows
5. **Style Memory** - Learn from your preferences
6. **Story Templates** - Professional narrative structures
7. **Social Media Templates** - Platform-optimized content
8. **New Video Providers** - Runway, Pika, Luma, MiniMax
9. **Smart Variations** - Reuse successful content
10. **Composition Analysis** - AI-powered flow feedback

## Web Timeline Preview

Launch an interactive web interface to preview and edit timelines before export.

### Starting the Preview Server

```python
# Through MCP
await start_timeline_preview(
    timeline_data={
        "name": "My Video",
        "duration": 60,
        "clips": [...]
    },
    port=8080
)
```

### Features

- **Drag & Drop**: Reorder clips visually
- **Real-time Updates**: See changes instantly
- **Playback Controls**: Preview with timeline scrubbing
- **Undo/Redo**: Full edit history
- **WebSocket Sync**: Multiple viewers stay in sync

### Interface Controls

- Click and drag clips to reorder
- Double-click to edit clip properties
- Use timeline ruler to navigate
- Export button saves changes

## Natural Language Timeline Editing

Edit timelines using natural language commands instead of manual adjustments.

### Supported Commands

```python
# Process natural language edits
result = await process_timeline_edit(
    timeline_data=timeline,
    command="make the intro punchier and add energy to the middle section"
)
```

### Command Examples

**Pacing Adjustments:**
- "Make the whole video faster"
- "Slow down the ending"
- "Make it more dynamic"
- "Create a rhythmic flow"

**Specific Edits:**
- "Remove the third clip"
- "Make the intro 5 seconds"
- "Add a fade between clips 2 and 3"
- "Extend the sunset scene"

**Style Changes:**
- "Make it feel more dramatic"
- "Add smooth transitions throughout"
- "Create a dreamy atmosphere"
- "Make the cuts more abrupt"

**Content Management:**
- "Remove any dark scenes"
- "Keep only the action shots"
- "Emphasize the close-ups"
- "Focus on movement"

## Multi-Version Export

Automatically adapt timelines for different platforms with intelligent cropping and timing.

### Platform Specifications

```python
# Export for multiple platforms
result = await export_multi_version(
    timeline_data=timeline,
    platforms=["instagram_reel", "tiktok", "youtube_short"],
    base_resolution=(1920, 1080)
)
```

### Supported Platforms

| Platform | Aspect Ratio | Duration | Special Features |
|----------|--------------|----------|------------------|
| Instagram Reel | 9:16 | 90s max | Vertical, loops |
| Instagram Post | 1:1 | 60s max | Square format |
| TikTok | 9:16 | 180s max | Vertical, trends |
| YouTube Short | 9:16 | 60s max | Vertical |
| Twitter/X | 16:9 | 140s max | Autoplay optimized |
| LinkedIn | 1:1 or 16:9 | 600s max | Professional |
| Facebook | Various | 240s max | Multiple formats |
| Snapchat | 9:16 | 60s max | Vertical, AR ready |

### Intelligent Adaptations

- **Smart Cropping**: AI detects important regions
- **Duration Fitting**: Speeds up or creates highlights
- **Safe Zones**: Avoids UI overlays
- **Platform Optimization**: Format-specific encoding

## Performance Analytics

Track workflow performance and get improvement suggestions.

### Session Tracking

```python
# Start tracking
session = await start_analytics_session()

# Your workflow here...

# Get insights
summary = await end_analytics_session()
print(f"Workflows completed: {summary['workflows_completed']}")
print(f"Average time: {summary['average_workflow_time']}s")
```

### Metrics Tracked

- **Workflow Metrics**: Time, success rate, errors
- **Export Analytics**: Formats used, quality settings
- **API Usage**: Calls per provider, costs
- **User Patterns**: Common workflows, preferences

### Improvement Suggestions

```python
suggestions = await get_improvement_suggestions(
    lookback_days=30
)
# Returns optimization tips based on your usage
```

## Style Memory System

Learn from your preferences and make personalized suggestions.

### Automatic Learning

The system automatically tracks:
- Color preferences
- Composition choices
- Transition styles
- Pacing preferences
- Music taste

### Getting Recommendations

```python
# Get style suggestions
recommendations = await get_style_recommendations(
    context="social_media",
    content_type="video"
)

# Analyze your style evolution
evolution = await get_style_evolution(
    days=90
)
```

### Workflow Integration

```python
# Start a style-aware workflow
workflow = await start_style_workflow(
    workflow_type="video_creation",
    target_style="cinematic"
)

# Get next action suggestions
next_action = await suggest_next_action(
    current_state=workflow
)
```

## Story Arc Templates

Professional narrative structures for compelling videos.

### Available Templates

**Three-Act Structure:**
```python
video = await create_story_arc_video(
    images=image_paths,
    structure="three_act",
    music_file="epic_music.mp3",
    act_durations=[20, 40, 20]  # seconds
)
```

**Hero's Journey:**
```python
video = await create_story_arc_video(
    images=image_paths,
    structure="heros_journey",
    chapter_names=[
        "Ordinary World",
        "Call to Adventure",
        "Crossing the Threshold",
        # ... etc
    ]
)
```

**Other Structures:**
- Five-Act (Freytag's Pyramid)
- Kishōtenketsu (Japanese 4-act)
- Circular (Return to beginning)
- Vignette (Thematic scenes)
- Montage (Rapid cuts)

### Documentary Mode

```python
documentary = await create_documentary_video(
    interviews=interview_clips,
    broll=broll_footage,
    narration="narration.mp3",
    style="investigative",  # or "educational", "biographical"
    chapters=["Introduction", "Background", "Investigation", "Conclusion"]
)
```

## Social Media Templates

Platform-specific templates optimized for engagement.

### Instagram Reels

```python
reel = await create_instagram_reel(
    images=images,
    music_file="trending_audio.mp3",
    style="aesthetic",  # or "energetic", "smooth", "glitch"
    text_overlays=[
        {"text": "POV:", "time": 0},
        {"text": "You discovered Alice", "time": 2}
    ],
    effects=["blur_transition", "zoom_pulse"]
)
```

### TikTok Videos

```python
tiktok = await create_tiktok_video(
    images=images,
    music_file="viral_sound.mp3",
    caption="Check this out! #ai #creative",
    hashtags=["aiart", "creative", "viral"],
    challenges=["#AiArtChallenge"],
    duet_ready=True
)
```

### Platform Features

Each platform template includes:
- Optimal aspect ratios
- Duration limits
- Safe zones for UI
- Trending styles
- Engagement optimizations

## New Video Providers

Four cutting-edge video generation providers with unique capabilities.

### Runway Gen-3

Professional quality with advanced camera controls.

```python
from alicemultiverse.providers import get_provider

runway = get_provider("runway")
result = await runway.generate({
    "prompt": "Cinematic space battle",
    "model": "gen3-alpha",
    "parameters": {
        "duration": 10,
        "camera_motion": "orbit_right",
        "style": "cinematic"
    }
})
```

### Pika Labs

Unique ingredient-based control system.

```python
pika = get_provider("pika")
result = await pika.generate({
    "prompt": "Fantasy forest",
    "model": "pika-2.1-hd",
    "parameters": {
        "ingredients": [
            {"type": "character", "description": "glowing fairy"},
            {"type": "environment", "description": "ancient trees"},
            {"type": "style", "description": "ethereal lighting"}
        ]
    }
})
```

### Luma Dream Machine

Perfect loops and keyframe animation.

```python
luma = get_provider("luma")

# Create a perfect loop
loop = await luma.generate({
    "prompt": "Infinite spiral",
    "model": "luma-loop",
    "parameters": {"loop_frames": 120}
})

# Keyframe animation
animated = await luma.generate({
    "prompt": "Transformation",
    "model": "luma-keyframes",
    "parameters": {
        "keyframes": [
            {"frame": 0, "prompt": "Ice cube"},
            {"frame": 60, "prompt": "Water droplet"},
            {"frame": 120, "prompt": "Steam cloud"}
        ]
    }
})
```

### MiniMax Hailuo

Music-synced videos and style transfer.

```python
minimax = get_provider("minimax")

# Music video
music_video = await minimax.generate({
    "prompt": "Abstract visuals",
    "model": "hailuo-music-video",
    "parameters": {
        "music_url": "https://example.com/song.mp3",
        "sync_to_beat": True
    }
})
```

## Smart Content Variations

Generate intelligent variations of successful content.

### Creating Variations

```python
# Generate variations
variations = await generate_content_variations(
    base_content_id="original_001",
    original_prompt="Sunset over mountains",
    variation_types=["style", "mood", "color"],
    strategy="performance_based",
    max_variations=5
)
```

### Variation Types

- **Style**: Different artistic interpretations
- **Mood**: Emotional tone variations
- **Color**: Palette alternatives
- **Composition**: Layout changes
- **Time**: Different times of day
- **Camera**: Angle variations

### Performance Tracking

```python
# Track how variations perform
await track_variation_performance(
    content_id="variation_001",
    metrics={
        "views": 1500,
        "likes": 230,
        "shares": 45,
        "play_duration": 18.5
    }
)

# Find top performers
top = await find_top_variations(
    metric="engagement_rate",
    min_views=100
)
```

## Visual Composition Analysis

AI-powered analysis of timeline flow and visual composition.

### Timeline Flow Analysis

```python
# Analyze pacing and rhythm
flow_analysis = await analyze_timeline_flow(
    timeline_data=timeline,
    target_mood="upbeat",
    target_energy="rising_action"
)

print(f"Timeline health: {flow_analysis['health_score']}/100")
for issue in flow_analysis['issues']:
    print(f"- {issue['description']} (severity: {issue['severity']})")
```

### Issue Detection

- **Pacing Problems**: Too fast/slow clips
- **Energy Flow**: Unexpected drops or spikes
- **Visual Continuity**: Color/brightness jumps
- **Narrative Breaks**: Story flow issues
- **Technical Issues**: Missing transitions

### Composition Analysis

```python
# Analyze single image
comp = await analyze_image_composition(
    image_path="/path/to/image.jpg"
)

print(f"Composition type: {comp['composition_type']}")
print(f"Overall quality: {comp['overall_score']:.2f}")
```

### Timeline Optimization

```python
# Auto-optimize timeline
optimized = await optimize_timeline(
    timeline_data=timeline,
    strategy="balanced",  # or "minimal", "aggressive"
    preserve_clips=[0, 5, 10],  # Don't modify these
    target_duration=60  # Optional duration target
)

print(f"Made {len(optimized['changes_made'])} improvements")
print(f"Improvement score: {optimized['improvement_score']:.2%}")
```

### Clip Ordering

```python
# Get optimal clip order
order = await suggest_clip_order(
    clip_paths=image_paths,
    target_flow="climactic"  # Build to climax
)

print(f"Suggested order: {order['suggested_order']}")
print(f"Energy curve: {order['energy_curve']}")
```

## Best Practices

### 1. Workflow Optimization

- Use analytics to identify bottlenecks
- Let style memory guide decisions
- Batch similar operations

### 2. Platform Strategy

- Create once, export everywhere
- Use platform-specific optimizations
- Track performance per platform

### 3. Creative Enhancement

- Start with templates for structure
- Use variations to explore options
- Apply composition analysis early

### 4. Cost Management

- Monitor provider usage
- Use local preview before cloud processing
- Batch operations when possible

### 5. Quality Control

- Always preview before export
- Use flow analysis to catch issues
- Test on target platforms

## Example Workflows

### Social Media Campaign

```python
# 1. Create base content
base_video = await create_story_arc_video(
    images=campaign_images,
    structure="three_act",
    music_file="brand_music.mp3"
)

# 2. Generate variations
variations = await generate_content_variations(
    base_content_id=base_video['id'],
    original_prompt=base_video['prompt'],
    variation_types=["style", "mood"],
    max_variations=3
)

# 3. Export for platforms
exports = await export_multi_version(
    timeline_data=base_video['timeline'],
    platforms=["instagram_reel", "tiktok", "youtube_short"]
)

# 4. Track performance
for platform, video_id in exports.items():
    await track_variation_performance(
        content_id=video_id,
        metrics=get_platform_metrics(platform, video_id)
    )
```

### Music Video Creation

```python
# 1. Analyze music
music_analysis = await analyze_music(
    audio_file="song.mp3"
)

# 2. Create beat-synced timeline
timeline = await sync_images_to_music(
    image_paths=images,
    audio_path="song.mp3",
    sync_to_beat=True
)

# 3. Analyze and optimize flow
flow = await analyze_timeline_flow(
    timeline_data=timeline,
    target_energy="wave"  # Match music energy
)

# 4. Apply optimizations
if flow['health_score'] < 80:
    timeline = await optimize_timeline(
        timeline_data=timeline,
        strategy="energy_focused"
    )

# 5. Export with effects
final = await export_timeline(
    timeline_data=timeline,
    output_format="mp4",
    effects=["beat_flash", "color_sync"]
)
```

## Troubleshooting

### Common Issues

**Preview Server Won't Start:**
- Check port availability (default 8080)
- Ensure no firewall blocking
- Try different port number

**Natural Language Not Working:**
- Be specific with commands
- Use supported keywords
- Check for ambiguous requests

**Export Failures:**
- Verify platform specifications
- Check resolution compatibility
- Ensure sufficient duration

**Performance Tracking Missing:**
- Start analytics session first
- End session to see summary
- Check date ranges

**Style Not Learning:**
- Need multiple similar choices
- Allow time for pattern detection
- Check preference recording

## Future Enhancements

Coming soon:
- Real-time collaboration
- Mobile app integration
- AI voice narration
- 3D scene support
- Live streaming tools