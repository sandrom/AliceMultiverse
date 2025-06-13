# B-Roll Suggestions Guide

AliceMultiverse now includes an intelligent B-roll suggestion system that helps you find and place supplementary footage to enhance your video projects. This guide covers how to use the automatic b-roll features effectively.

## Overview

B-roll footage serves several purposes in video production:
- 📊 Adds visual variety to long shots
- 🎭 Provides cutaways during dialogue
- 🔄 Smooths transitions between scenes
- 🎯 Maintains viewer engagement
- 📝 Illustrates concepts being discussed

The b-roll suggestion system analyzes your timeline and intelligently suggests relevant footage based on:
- Scene context (subject, location, mood)
- Visual similarity to main footage
- Energy levels and pacing
- Transition requirements

## Getting B-Roll Suggestions

### For an Entire Timeline

```python
# Get suggestions for your timeline
suggestions = await suggest_broll_for_timeline(
    timeline_data=my_timeline,
    project_context={
        "genre": "documentary",
        "style": "informative",
        "target_audience": "general"
    },
    max_suggestions_per_scene=5
)

# Review suggestions
for clip_idx, suggestions_list in suggestions["suggestions"].items():
    print(f"\nClip {clip_idx} suggestions:")
    for suggestion in suggestions_list:
        print(f"  - {suggestion['asset_path']}")
        print(f"    Type: {suggestion['type']}")
        print(f"    Reasoning: {suggestion['reasoning']}")
        print(f"    Placement: {suggestion['placement']}")
```

### Analyzing Individual Scenes

```python
# Analyze a specific scene
analysis = await analyze_scene_for_broll(
    asset_path="/path/to/main/footage.mp4",
    start_time=10.0,
    duration=8.0,
    scene_metadata={
        "type": "interview",
        "subject": "scientist",
        "location": "laboratory"
    }
)

if analysis["needs_broll"]:
    print("B-roll recommended:")
    for reason in analysis["reasoning"]:
        print(f"  - {reason}")
```

## Automatic B-Roll Insertion

### Basic Auto-Insert

Let the system automatically place b-roll in your timeline:

```python
# Enhance timeline with b-roll
enhanced = await auto_insert_broll(
    timeline_data=original_timeline,
    max_broll_percentage=0.3,  # 30% max b-roll
    prefer_types=["contextual", "mood"]
)

print(f"Added {enhanced['statistics']['broll_clips_added']} b-roll clips")
print(f"B-roll percentage: {enhanced['statistics']['broll_percentage']:.1%}")
```

### Controlling B-Roll Placement

Different placement strategies for different needs:

```python
# Documentary style - more contextual b-roll
enhanced = await auto_insert_broll(
    timeline_data=timeline,
    max_broll_percentage=0.4,
    prefer_types=["contextual", "mood"]
)

# Music video - quick visual cuts
enhanced = await auto_insert_broll(
    timeline_data=timeline,
    max_broll_percentage=0.5,
    prefer_types=["visual", "transition"]
)

# Narrative - subtle enhancements
enhanced = await auto_insert_broll(
    timeline_data=timeline,
    max_broll_percentage=0.2,
    prefer_types=["mood", "visual"]
)
```

## Finding Specific B-Roll

### Search by Criteria

Find b-roll matching specific requirements:

```python
# Find nature b-roll with calm mood
results = await find_broll_by_criteria(
    subject="nature",
    mood="peaceful",
    energy_level="low",
    location="outdoor",
    limit=20
)

# Find urban b-roll with high energy
results = await find_broll_by_criteria(
    subject="city",
    mood="dynamic",
    energy_level="high",
    location="urban",
    exclude_paths=["/already/used/clip.mp4"]
)
```

### Generate Shot Lists

Create professional b-roll shot lists:

```python
# Generate documentary-style shot list
shot_list = await generate_broll_shot_list(
    timeline_data=timeline,
    style="documentary",
    include_descriptions=True
)

print(f"Total shots recommended: {shot_list['summary']['total_shots']}")
for shot in shot_list["shots"]:
    print(f"\n{shot['shot_number']}: {shot['description']}")
    print(f"  Position: {shot['timeline_position']}s")
    print(f"  Duration: {shot['suggested_duration']}s")
```

## B-Roll Types and Usage

### Contextual B-Roll
Footage that directly relates to the subject matter:
- Interview about cooking → kitchen/food shots
- Discussion of nature → landscape footage
- Tech presentation → device close-ups

### Mood B-Roll
Footage that reinforces emotional tone:
- Sad moment → rain, empty spaces
- Happy scene → sunlight, flowers
- Tense situation → shadows, tight spaces

### Visual B-Roll
Footage with similar visual characteristics:
- Matching color palettes
- Similar compositions
- Complementary movement

### Transition B-Roll
Neutral footage for scene changes:
- Abstract textures
- Natural elements (water, clouds)
- Geometric patterns

## Best Practices

### 1. **Don't Overuse B-Roll**
```python
# Keep b-roll under 30% for most projects
enhanced = await auto_insert_broll(
    timeline_data=timeline,
    max_broll_percentage=0.3
)
```

### 2. **Match Energy Levels**
The system automatically considers energy levels:
- High energy main footage → Dynamic b-roll
- Calm scenes → Peaceful inserts
- Dialogue → Static or slow-motion b-roll

### 3. **Consider Context**
```python
# Provide project context for better suggestions
suggestions = await suggest_broll_for_timeline(
    timeline_data=timeline,
    project_context={
        "genre": "educational",
        "topic": "climate change",
        "tone": "serious"
    }
)
```

### 4. **Review Before Inserting**
```python
# Get suggestions first
suggestions = await suggest_broll_for_timeline(timeline)

# Review and filter
selected_broll = review_and_select(suggestions)

# Then insert manually
timeline_with_broll = insert_selected_broll(timeline, selected_broll)
```

## Integration with Workflows

### Music Video Workflow
```python
# Create music video with automatic b-roll
from alicemultiverse.workflows import create_music_video

video = await create_music_video(
    audio_path="/path/to/song.mp3",
    main_footage=footage_list,
    enable_broll=True,
    broll_percentage=0.4
)
```

### Documentary Workflow
```python
# Documentary with contextual b-roll
timeline = await create_documentary_timeline(
    interviews=interview_clips,
    narration=voiceover_track
)

# Add contextual b-roll
enhanced = await auto_insert_broll(
    timeline_data=timeline,
    prefer_types=["contextual"],
    max_broll_percentage=0.35
)
```

## Advanced Usage

### Custom B-Roll Rules
```python
# Define custom rules for b-roll selection
class CustomBRollEngine(BRollSuggestionEngine):
    def _needs_broll(self, clip, scene_info, clip_idx, timeline):
        # Custom logic
        if "interview" in scene_info.get("tags", []):
            return True
        if clip["duration"] > 3.0:  # Shorter threshold
            return True
        return False
```

### Batch Processing
```python
# Process multiple timelines
timelines = load_project_timelines()
for timeline in timelines:
    enhanced = await auto_insert_broll(
        timeline_data=timeline,
        max_broll_percentage=0.25
    )
    save_timeline(enhanced)
```

## Troubleshooting

### "No b-roll suggestions found"
- Ensure your media library has assets tagged appropriately
- Run understanding/analysis on your footage first
- Check that similarity index is built

### "Too much b-roll inserted"
- Lower the `max_broll_percentage` parameter
- Use `prefer_types` to limit suggestion types
- Manually review suggestions before auto-insert

### "B-roll doesn't match style"
- Provide more detailed `project_context`
- Use visual similarity type for style matching
- Pre-filter your b-roll library by style

## Cost Considerations

B-roll suggestions use existing metadata and don't require additional API calls. However:
- Initial asset analysis (understanding) has API costs
- Building similarity index is a one-time local operation
- Subsequent suggestions are free and fast

## Example: Complete B-Roll Workflow

```python
# 1. Analyze your timeline
timeline = load_timeline("my_project.json")

# 2. Get initial suggestions
suggestions = await suggest_broll_for_timeline(
    timeline_data=timeline,
    project_context={
        "style": "documentary",
        "topic": "urban life"
    }
)

# 3. Review suggestions
print(f"Found b-roll opportunities in {suggestions['scenes_needing_broll']} scenes")

# 4. Auto-insert with constraints
if suggestions['scenes_needing_broll'] > 0:
    enhanced = await auto_insert_broll(
        timeline_data=timeline,
        max_broll_percentage=0.3,
        prefer_types=["contextual", "mood"]
    )
    
    # 5. Export enhanced timeline
    export_timeline(enhanced['timeline'], "enhanced_timeline.edl")
```

The b-roll suggestion system helps maintain visual interest and professional pacing in your videos while saving time in the editing process.