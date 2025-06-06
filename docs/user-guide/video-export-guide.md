# Video Export Complete Guide

This comprehensive guide covers AliceMultiverse's video timeline export features, from basic usage to advanced workflows for professional video editing.

## Overview

AliceMultiverse transforms your AI-generated images into professional video timelines with:
- **DaVinci Resolve**: Industry-standard EDL and XML formats
- **CapCut**: Mobile-optimized JSON for on-the-go editing
- **Proxy Generation**: Smart optimization for 4K+ content
- **Beat Synchronization**: Music-driven editing with frame accuracy
- **Metadata Preservation**: Never lose your creative context

## Quick Start: Music-Driven Video Creation

### Prerequisites

1. **Music file**: MP3, WAV, or M4A format
2. **Selected images**: Use quick selection or search
3. **Export destination**: Folder with write permissions

### Step 1: Analyze Your Music

```python
# Through Claude MCP - Natural language
"Analyze the music file background_music.mp3"

# Or with specific focus
"Analyze background_music.mp3 focusing on beat points for cuts"

# Detailed analysis returns:
{
    "tempo": 120,  # BPM
    "key": "C major",
    "mood": "energetic",
    "energy_profile": [
        {"time": 0, "energy": 0.3},
        {"time": 5, "energy": 0.7},
        {"time": 20, "energy": 1.0}  # Peak
    ],
    "beats": [0.5, 1.0, 1.5, ...],  # All beat positions
    "downbeats": [0.5, 2.5, 4.5, ...],  # Strong beats
    "sections": [
        {"name": "intro", "start": 0, "end": 5, "mood": "building"},
        {"name": "verse", "start": 5, "end": 20, "mood": "steady"},
        {"name": "chorus", "start": 20, "end": 35, "mood": "energetic"}
    ]
}
```

### Step 2: Sync Images to Music

```python
# Sync images to beat
"Sync these images to the music beats"

# Or sync to specific sections
"Match energetic images to the chorus sections"
```

The system will:
- Align transitions to beats
- Match image mood to music mood
- Calculate optimal shot durations
- Create a beat-synced timeline

### Step 3: Export Timeline

```python
# Export for DaVinci Resolve
"Export timeline as DaVinci Resolve project"

# Export for CapCut
"Export timeline for CapCut mobile"
```

## Export Formats

### DaVinci Resolve EDL

Standard Edit Decision List format:
```
TITLE: My Music Video
FCM: NON-DROP FRAME

001  CLIP_0 V     C        00:00:00:00 00:00:02:00 00:00:00:00 00:00:02:00
* FROM CLIP NAME: image_001.jpg
* SOURCE FILE: /path/to/image_001.jpg
* EFFECT NAME: CROSSFADE
* EFFECT DURATION: 15
```

Features:
- Frame-accurate timings
- Transition metadata
- Source file paths
- Effect durations

### DaVinci Resolve XML

Full project structure in FCPXML format:
```xml
<fcpxml version="1.8">
  <resources>
    <format id="r1" name="1920x1080" frameDuration="1/30s"/>
    <asset id="r2" name="clip_0" src="/path/to/image.jpg"/>
  </resources>
  <library>
    <event name="My Project">
      <project name="Music Video">
        <sequence format="r1" duration="30s">
          <spine>
            <clip name="clip_0" ref="r2" offset="0s" duration="2s">
              <transition name="crossfade" duration="0.5s"/>
            </clip>
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
```

Features:
- Complete project structure
- Asset management
- Transition effects
- Beat markers

### CapCut JSON

Mobile-optimized format:
```json
{
  "version": "1.0",
  "project_name": "Music Video",
  "duration": 30000,
  "resolution": {
    "width": 1080,
    "height": 1920
  },
  "tracks": {
    "video": [{
      "id": "clip_0",
      "material_id": "abc123",
      "start_time": 0,
      "duration": 2000,
      "transition_in": {
        "type": "fade",
        "duration": 500
      },
      "beat_sync": true
    }],
    "audio": [{
      "path": "/path/to/music.mp3",
      "start_time": 0,
      "duration": 30000
    }]
  },
  "markers": [{
    "time": 500,
    "name": "Beat 1",
    "type": "beat"
  }]
}
```

Features:
- Vertical video support
- Beat sync markers
- Effect suggestions
- Mobile-optimized transitions

## Proxy Generation

For smooth editing of high-resolution content:

```python
# Generate proxies during export
"Export timeline with proxy files"
```

Proxy settings:
- Resolution: 1280x720 (configurable)
- Codec: H.264 for compatibility
- Quality: Optimized for editing
- Automatic for 4K+ content

## Beat Synchronization

### Automatic Beat Detection

The music analyzer detects:
- **Tempo**: Overall BPM
- **Beats**: Individual beat positions
- **Downbeats**: Strong beats (measures)
- **Sections**: Musical structure

### Sync Modes

1. **Beat Sync**: Cut on every beat
   - Fast-paced, energetic
   - Good for action sequences

2. **Downbeat Sync**: Cut on strong beats
   - More relaxed pacing
   - Good for emotional content

3. **Section Sync**: Change at musical sections
   - Narrative progression
   - Good for storytelling

### Manual Adjustments

Timeline clips include:
- `beat_aligned`: Boolean flag
- `sync_point`: Exact beat time
- `transition_in_duration`: Adjustable

## Real-World Workflow Examples

### Complete Music Video Workflow

```python
# 1. Prepare your assets
"Mark my favorite cyberpunk images for the video"
"Find all neon-lit portraits from last week"

# 2. Analyze music structure
"Analyze techno_track.mp3 for video editing"
# Output: 128 BPM, high energy, clear drops at 0:45 and 2:15

# 3. Match visuals to music
"Create a timeline matching image energy to music energy"
# System automatically:
# - Places calm images during intro
# - Saves intense visuals for drops
# - Syncs cuts to beats

# 4. Fine-tune the edit
"Move the glitch effect images to the first drop"
"Make cuts faster during the chorus"
"Add 1-second crossfades between similar shots"

# 5. Export for your editor
"Export timeline as DaVinci Resolve XML with proxies"
# Creates:
# - Project.fcpxml (timeline structure)
# - /proxies/ folder (optimized files)
# - beat_markers.txt (reference)
```

### Quick Instagram Reel (30 seconds)

```python
# Fast workflow for social media
"Create a 30-second reel from my best portraits"
"Use upbeat section of song.mp3 starting at chorus"
"Export for CapCut mobile with 9:16 aspect ratio"

# Result: Ready-to-edit timeline with:
# - Vertical framing
# - Fast cuts (0.5-1s per shot)
# - Beat-synced transitions
# - Mobile-optimized file paths
```

### Documentary Style Edit

```python
# Longer form content with narrative
"Group images by visual theme"
"Create 3-minute timeline with slow pacing"
"Use ambient_music.mp3 without beat syncing"
"Export as EDL with 2-second dissolves"

# Features:
# - Thematic grouping
# - Longer shot durations (3-5s)
# - Smooth transitions
# - Narrative flow
```

### Quick Social Media Edit

```python
# Create 30-second reel
timeline = create_timeline(
    duration=30,
    aspect_ratio="9:16",  # Vertical
    images=selected_images,
    music="background.mp3"
)

# Export for CapCut mobile
export_timeline(timeline, format="capcut")
```

## Pro Tips and Best Practices

### Image Preparation

1. **Quality Check First**
   ```python
   "Show me images with technical issues"
   "Find images with artifacts or low resolution"
   ```

2. **Organize by Visual Flow**
   - Group similar compositions
   - Consider color progression
   - Plan entry/exit points
   ```python
   "Group images by dominant color"
   "Find images with similar compositions"
   ```

3. **Tag for Searchability**
   ```python
   "Add 'hero' tag to best shots"
   "Mark establishing shots"
   ```

### Music Selection

1. **Structure Matters**
   - Clear sections (intro/verse/chorus)
   - Consistent tempo
   - Dynamic range for pacing

2. **BPM Guidelines**
   - 60-90 BPM: Slow, emotional
   - 90-120 BPM: Moderate, versatile
   - 120-140 BPM: Energetic, fast cuts
   - 140+ BPM: Rapid fire, action

3. **Audio Preparation**
   - Normalize levels
   - Add 1-2 second handles
   - Export as high-quality MP3/WAV

### Timeline Optimization

1. **Shot Duration Formula**
   ```
   Base duration = 60 / BPM * 4 (one measure)
   Complexity factor:
   - Simple composition: 0.5x
   - Medium complexity: 1x
   - Complex/detailed: 1.5x
   ```

2. **Transition Strategies**
   - **On beat**: Hard cuts for energy
   - **Between beats**: Smooth for flow
   - **Across measures**: Long for emotion

3. **Pacing Variation**
   - Start slow (establish mood)
   - Build to climax
   - Vary shot lengths
   - Use pauses effectively

## Troubleshooting

### EDL Not Importing
- Check frame rate matches project (default 30fps)
- Ensure all source files are accessible
- Verify timecode format

### XML Import Issues
- DaVinci Resolve prefers FCPXML 1.8
- Check resolution matches project
- Verify asset paths are absolute

### CapCut Compatibility
- Ensure JSON is valid (no trailing commas)
- Use supported transition types
- Keep file paths accessible to mobile

## Advanced Features

### Custom Transition Mapping

```python
# Define transition rules based on content
"Set zoom transitions for action shots"
"Use dissolves between similar colors"
"Add glitch effects on beat drops"

# Advanced mapping
transition_rules = {
    "content_based": {
        "portrait_to_portrait": "morph",
        "landscape_to_landscape": "wipe",
        "different_scenes": "cut"
    },
    "mood_based": {
        "calm_to_energetic": "accelerate",
        "energetic_to_calm": "decelerate",
        "same_mood": "dissolve"
    },
    "beat_based": {
        "downbeat": "impact_zoom",
        "offbeat": "subtle_fade",
        "drop": "glitch"
    }
}
```

### AI-Powered Scene Analysis

```python
# Coming soon: Motion vectors
"Analyze motion direction in each image"
"Create transitions that follow motion flow"

# Example output:
{
    "image1": {"motion": "left_to_right", "speed": 0.7},
    "image2": {"motion": "right_to_left", "speed": 0.3},
    "suggested_transition": "momentum_preserve"
}
```

### Multi-Track Timelines

```python
# Add multiple video tracks
timeline.add_track("overlay", overlay_clips)
timeline.add_track("titles", title_clips)
```

### Color Metadata

Include color information for easier grading:
- Dominant colors
- Color temperature
- Suggested LUT based on style

## Integration with Other Features

### Style Clustering for Visual Coherence
```python
# Group clips by visual style
"Cluster images by visual similarity"
"Create timeline sections from each style cluster"

# Result: Smooth visual flow with gradual style transitions
```

### Quick Selections as Hero Shots
```python
# Use your marked favorites strategically
"Place quick-selected images at key moments"
"Use favorites for opening and closing shots"
"Add extra duration to hero shots"
```

### Batch Analysis for Rich Metadata
```python
# Pre-analyze everything for better timeline decisions
"Analyze all images with style and mood detection"
"Create timeline based on mood progression"
"Export with full metadata for color grading"
```

### Project Context Integration
```python
# Maintain creative vision
"Load project 'Cyberpunk Music Video'"
"Create timeline following project mood board"
"Export with project-specific settings"
```

### Smart Templates (Coming Soon)
```python
# One-click video creation
"Use music video template with my selections"
"Apply Instagram reel template"
"Create YouTube shorts with trending style"
```

## Troubleshooting Deep Dive

### DaVinci Resolve Import Issues

#### Problem: EDL Not Recognized
```bash
# Check EDL format
head -20 exported_timeline.edl

# Should show:
TITLE: Your Project
FCM: NON-DROP FRAME
```

**Solutions**:
1. Verify frame rate matches project
2. Check file paths are absolute
3. Ensure no special characters in filenames
4. Try importing as CMX 3600 EDL

#### Problem: Missing Media in XML
```xml
<!-- Check asset paths in XML -->
<asset id="r2" src="file:///absolute/path/to/image.jpg"/>
```

**Solutions**:
1. Use absolute paths
2. Keep media in same location
3. Relink media in Resolve
4. Check file permissions

### CapCut Mobile Issues

#### Problem: JSON Won't Import
**Common causes**:
1. Invalid JSON syntax
2. Unsupported effects
3. Path issues on mobile

**Debug steps**:
```python
# Validate JSON
"Check if the CapCut export is valid JSON"

# Simplify export
"Export basic timeline without effects"

# Use cloud paths
"Export with cloud-friendly paths for CapCut"
```

### Performance Optimization

#### Large Projects (100+ clips)
1. **Enable proxy generation**
   ```python
   "Export with low-res proxies for editing"
   ```

2. **Split into sequences**
   ```python
   "Create separate timelines for each song section"
   ```

3. **Optimize media**
   ```python
   "Convert images to edit-friendly format first"
   ```

## Keyboard Shortcuts Reference

### DaVinci Resolve
- `I`: Set in point at beat
- `O`: Set out point at beat
- `Alt+X`: Add transition
- `Shift+T`: Adjust transition length

### CapCut
- Tap clip: Select
- Long press: Options
- Pinch: Adjust duration
- Swipe: Add transition

## Next Steps

1. **Watch the video tutorials**: [Coming soon]
2. **Download example projects**: [Coming soon]
3. **Join the community**: Share your edits
4. **Request features**: What would help your workflow?