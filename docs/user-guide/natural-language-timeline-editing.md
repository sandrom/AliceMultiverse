# Natural Language Timeline Editing Guide

Edit your video timelines using natural language commands like "make the intro punchier" or "add breathing room after the drop". This guide covers the AI-powered timeline editing features.

## Overview

Natural language editing allows you to:
- 🚀 Adjust pacing with commands like "speed up the intro"
- 🎵 Sync to music with "match all cuts to the beat"
- 💨 Control energy with "build intensity in the chorus"
- 🌊 Add space with "let the outro breathe"
- 🔄 Change transitions with "add dissolve effects"

## Getting Started

### Basic Usage

```python
# Start with a timeline
timeline = await create_video_timeline(
    images=image_list,
    music_path="song.mp3"
)

# Apply a natural language edit
result = await edit_timeline_naturally(
    command="make the intro punchier",
    timeline_data=timeline["timeline"]
)

# The timeline is now modified with faster intro cuts
print(f"Applied: {result['message']}")
```

### Understanding Edit Commands

Commands are interpreted based on:
1. **Intent**: What you want to do (pace, sync, energy, etc.)
2. **Target**: Which part of the timeline (intro, outro, all, etc.)
3. **Parameters**: How much to change (faster, slower, more, less)

## Command Categories

### Pace Adjustments

Control the speed and rhythm of your cuts:

```python
# Speed up sections
"Make the intro faster"
"Speed up the middle section"
"Tighten the entire edit"
"Make punchier cuts during the chorus"

# Slow down sections
"Make the outro slower"
"Let the bridge breathe more"
"Slow down the pace"
"Give the intro more time"
```

### Music Synchronization

Align your cuts with the beat:

```python
# Sync to beat
"Sync all cuts to the beat"
"Put the drops on the beat"
"Make it more rhythmic"
"Align transitions with the music"
"Match cuts to the rhythm"
```

### Energy & Intensity

Control the emotional flow:

```python
# Increase energy
"Build more energy in the buildup"
"Add intensity to the chorus"
"Make the intro more exciting"
"Create more excitement"

# Decrease energy
"Calm down the bridge"
"Make the outro more chill"
"Relax the middle section"
"Reduce intensity"
```

### Breathing Room & Pauses

Add space and moments to breathe:

```python
# Add pauses
"Add breathing room after the drop"
"Give me a moment before the chorus"
"Hold on the hero shot longer"
"Let the intro breathe"
"Add a pause after the climax"
```

### Transitions

Change how clips flow together:

```python
# Modify transitions
"Add dissolve transitions"
"Use cuts instead of fades"
"Make all transitions faster"
"Remove transitions"
"Add smooth transitions between scenes"
```

## Advanced Usage

### Multiple Commands

Apply several edits in sequence:

```python
commands = [
    "Make the intro faster",
    "Add breathing room after the intro",
    "Sync all cuts to the beat",
    "Add dissolve transitions"
]

result = await apply_timeline_commands(
    commands=commands,
    timeline_data=timeline["timeline"]
)

print(f"Applied {result['commands_processed']} edits successfully")
```

### Getting Suggestions

Let AI analyze your timeline and suggest improvements:

```python
suggestions = await suggest_timeline_improvements(
    timeline_data=timeline["timeline"]
)

print("Timeline Analysis:")
print(f"- Pace: {suggestions['analysis']['pace']}")
print(f"- Average clip duration: {suggestions['analysis']['average_clip_duration']:.1f}s")

print("\nSuggested edits:")
for suggestion in suggestions['suggestions']:
    print(f"- {suggestion}")
```

### Integration with Preview

Combine with timeline preview for real-time updates:

```python
# Open timeline in preview
preview = await preview_video_timeline(timeline["timeline"])

# Apply natural language edits with live preview
result = await edit_timeline_naturally(
    command="make it more dynamic with faster cuts",
    timeline_data=timeline["timeline"],
    session_id=preview["session_id"]  # Updates preview automatically
)
```

## Understanding How It Works

### Section Detection

The system recognizes common section names:
- **Intro**: Beginning, start, opening
- **Outro**: Ending, conclusion, finale
- **Chorus**: Hook, refrain
- **Verse**: Verse sections
- **Bridge**: Middle, break
- **Drop**: Beat drop, bass drop
- **Buildup**: Build-up, rise

### Confidence Levels

Each edit has a confidence score:
- **High (0.8+)**: Clear, specific commands
- **Medium (0.6-0.8)**: General but understandable
- **Low (<0.6)**: Ambiguous, may need clarification

### Edit Application

Edits are applied intelligently:
1. **Pace changes** adjust clip durations proportionally
2. **Sync adjustments** snap to nearest beat markers
3. **Energy changes** modify both pace and transitions
4. **Pauses** insert gaps without disrupting flow

## Examples by Workflow

### Music Video Workflow

```python
# Start with beat-detected timeline
timeline = await create_video_timeline(
    images=images,
    music_path="track.mp3",
    style="music_video"
)

# Progressive refinement
commands = [
    "Sync all cuts to the beat",
    "Make the verses calmer",
    "Build energy in the chorus",
    "Add breathing room before the drop",
    "Make the outro fade out slowly"
]

final_timeline = await apply_timeline_commands(
    commands=commands,
    timeline_data=timeline["timeline"]
)
```

### Documentary Style

```python
# Create narrative timeline
timeline = await create_video_timeline(
    images=images,
    style="documentary"
)

# Apply documentary pacing
result = await edit_timeline_naturally(
    command="give each shot time to breathe",
    timeline_data=timeline["timeline"]
)

# Add dramatic pauses
result = await edit_timeline_naturally(
    command="add a pause before revealing the main subject",
    timeline_data=result["timeline"]
)
```

### Action Sequence

```python
# Fast-paced edit
commands = [
    "Make all cuts faster",
    "Sync to the beat",
    "Build intensity throughout",
    "Use hard cuts instead of dissolves"
]

result = await apply_timeline_commands(
    commands=commands,
    timeline_data=timeline["timeline"]
)
```

## Tips and Best Practices

### Be Specific

More specific commands work better:
- ❌ "Make it better"
- ✅ "Make the intro punchier with faster cuts"

### Use Section Names

Target specific parts:
- "Speed up the **intro**"
- "Add energy to the **chorus**"
- "Let the **outro** breathe"

### Combine Commands

Layer effects for complex results:
1. Set the rhythm: "Sync to beat"
2. Adjust pacing: "Make verses slower"
3. Add dynamics: "Build energy in chorus"
4. Polish: "Add smooth transitions"

### Check Suggestions

Use AI suggestions as a starting point:
```python
# Get AI analysis
suggestions = await suggest_timeline_improvements(timeline_data)

# Apply the ones you like
for suggestion in suggestions['suggestions'][:3]:
    result = await edit_timeline_naturally(
        command=suggestion,
        timeline_data=timeline_data
    )
```

## Troubleshooting

### Command Not Understood

If a command isn't recognized:
1. Check the suggestions returned
2. Try rephrasing with section names
3. Break complex commands into steps

### Unexpected Results

If edits don't match expectations:
1. Review the confidence scores
2. Use more specific language
3. Apply edits one at a time

### Performance

For large timelines:
- Apply edits to sections separately
- Use batch commands for efficiency
- Preview changes before exporting

## Future Enhancements

Planned improvements include:
- Visual preview of edits
- Undo specific commands
- Custom section detection
- Voice command support
- Learning from your preferences

The natural language editing system makes timeline refinement as simple as describing what you want, bridging the gap between creative vision and technical execution.