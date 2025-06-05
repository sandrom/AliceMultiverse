# Video Export Guide

This guide covers how to export video timelines from AliceMultiverse to popular editing software.

## Overview

AliceMultiverse can export your image sequences and music-synced timelines to:
- **DaVinci Resolve** (EDL and XML formats)
- **CapCut** (JSON format for mobile editing)

## MCP Tools

### export_timeline

Export an existing timeline to various formats:

```python
# Example timeline data
timeline_data = {
    "name": "My_Video_Project",
    "duration": 60.0,
    "frame_rate": 30.0,
    "resolution": [1920, 1080],
    "clips": [
        {
            "path": "/path/to/image1.jpg",
            "start_time": 0.0,
            "duration": 2.0,
            "transition_in": "crossfade",
            "transition_in_duration": 0.5,
            "beat_aligned": True,
            "sync_point": 0.0
        },
        {
            "path": "/path/to/image2.jpg", 
            "start_time": 1.5,
            "duration": 2.0,
            "transition_in": "dissolve",
            "transition_in_duration": 0.5
        }
    ],
    "markers": [
        {"time": 0.0, "name": "Intro", "type": "section"},
        {"time": 30.0, "name": "Chorus", "type": "section"}
    ],
    "metadata": {
        "mood": "energetic",
        "bpm": 128
    }
}

# Export to all formats with proxies
result = await export_timeline(
    timeline_data=timeline_data,
    output_formats=["edl", "xml", "capcut"],
    generate_proxies=True,
    proxy_resolution=[1280, 720]
)
```

### create_video_timeline

Create a complete video timeline from images with optional music sync:

```python
# Simple timeline without music
timeline = await create_video_timeline(
    image_paths=[
        "/path/to/img1.jpg",
        "/path/to/img2.jpg",
        "/path/to/img3.jpg"
    ],
    duration_per_image=2.0,
    transition_type="crossfade",
    transition_duration=0.5,
    export_formats=["xml", "capcut"]
)

# Music-synced timeline
timeline_with_music = await create_video_timeline(
    image_paths=image_list,
    audio_path="/path/to/music.mp3",
    sync_to_beat=True,
    transition_type="dissolve",
    export_formats=["edl", "xml", "capcut"]
)
```

## Export Formats

### DaVinci Resolve

#### EDL (Edit Decision List)
- Simple text format compatible with most NLEs
- Includes basic cuts and transitions
- Limited to 8-character reel names
- Best for simple timelines

Example EDL output:
```
TITLE: My_Video_Project
FCM: NON-DROP FRAME

001  IMAGE_1 V     C        00:00:00:00 00:00:02:00 00:00:00:00 00:00:02:00
* FROM CLIP NAME: image1.jpg
* SOURCE FILE: /path/to/image1.jpg
* EFFECT NAME: CROSSFADE
* EFFECT DURATION: 15
```

#### XML (FCPXML-like)
- More detailed than EDL
- Preserves all metadata
- Includes markers and effects
- Better for complex timelines

Features:
- Full asset paths
- Transition details
- Beat sync markers
- Color metadata (if available)

### CapCut

JSON format optimized for mobile editing:
- Millisecond precision timing
- Material library with assets
- Track-based structure
- Effect and transition support
- Mood-based suggestions

Example structure:
```json
{
    "version": "1.0",
    "project_name": "My_Video_Project",
    "duration": 60000,
    "fps": 30.0,
    "tracks": {
        "video": [...],
        "audio": [...],
        "effect": [...],
        "text": [...]
    },
    "materials": [...],
    "markers": [...],
    "suggestions": {
        "transitions": ["zoom_in", "slide_right"],
        "effects": ["shake", "flash"],
        "pace": "fast"
    }
}
```

## Proxy Generation

For smooth editing of high-resolution images:

```python
# Proxies are generated automatically with create_video_timeline
# Or manually control proxy settings:
result = await export_timeline(
    timeline_data=timeline_data,
    generate_proxies=True,
    proxy_resolution=[1280, 720]  # HD proxies
)

# Access proxy mappings
for original, proxy in result["data"]["proxies"].items():
    print(f"Original: {original}")
    print(f"Proxy: {proxy}")
```

Proxy features:
- JPEG format for images (85% quality)
- H.264 for video clips
- Maintains aspect ratio
- Organized in proxies/ subfolder

## Beat Synchronization

When creating timelines with music:

1. **Automatic Beat Detection**
   ```python
   # First analyze the music
   music_analysis = await analyze_music(
       audio_path="/path/to/song.mp3",
       detect_sections=True,
       extract_mood=True
   )
   
   # Then create synced timeline
   timeline = await create_video_timeline(
       image_paths=images,
       audio_path="/path/to/song.mp3",
       sync_to_beat=True
   )
   ```

2. **Sync Modes**
   - Beat sync: Changes on every beat
   - Measure sync: Changes on downbeats
   - Section sync: Changes at musical sections

3. **Distribution Strategy**
   - Images distributed evenly across beats
   - Transitions aligned to beat grid
   - Markers added at sync points

## Workflow Examples

### Music Video Creation

```python
# 1. Analyze music for mood and beats
analysis = await analyze_music(
    audio_path="song.mp3",
    detect_sections=True,
    extract_mood=True
)

# 2. Find images matching the mood
images = await search_assets(
    tags=[analysis["data"]["mood"]["category"]],
    limit=50
)

# 3. Create beat-synced timeline
timeline = await create_video_timeline(
    image_paths=[img["path"] for img in images["data"]["assets"]],
    audio_path="song.mp3",
    sync_to_beat=True,
    transition_type="crossfade",
    export_formats=["xml", "capcut"]
)

# 4. Results include all export paths
print(f"DaVinci XML: {timeline['data']['exports']['xml']}")
print(f"CapCut JSON: {timeline['data']['exports']['capcut']}")
```

### Style-Based Slideshow

```python
# 1. Find images with similar style
style_collection = await build_style_collections(
    min_collection_size=10
)

# 2. Create timeline from a style group
collection = style_collection["data"]["collections"][0]
timeline = await create_video_timeline(
    image_paths=collection["images"],
    duration_per_image=3.0,
    transition_type="dissolve",
    transition_duration=1.0,
    export_formats=["edl", "xml"]
)
```

## Tips and Best Practices

1. **File Organization**
   - Exports go to `~/Documents/AliceExports/[timeline_name]/`
   - Keep original files accessible during editing
   - Proxies in subfolder for easy management

2. **Performance**
   - Use proxies for 4K+ content
   - EDL for simple cuts
   - XML for complex timelines with effects

3. **Compatibility**
   - Test EDL import with your NLE version
   - CapCut JSON works best with latest app
   - Some effects may need manual adjustment

4. **Music Sync**
   - Analyze music first to verify beat detection
   - Use "measure" sync for slower songs
   - Add extra images for better distribution

## Troubleshooting

### Common Issues

1. **Missing transitions in EDL**
   - EDL has limited effect support
   - Use XML for full transition details

2. **Proxy generation fails**
   - Ensure ffmpeg is installed
   - Check disk space for proxy storage
   - Verify source files are accessible

3. **Beat sync off**
   - Try different sync modes
   - Manually adjust BPM if needed
   - Check audio file quality

### Debug Information

Enable detailed logging:
```python
result = await create_video_timeline(
    image_paths=images,
    audio_path="song.mp3",
    sync_to_beat=True,
    # Returns detailed sync information
)

# Check sync details
sync_info = result["data"]["sync_info"]
print(f"Beat synced: {sync_info['beat_synced']}")
print(f"Beat count: {sync_info['beat_count']}")
print(f"BPM: {sync_info['bpm']}")
print(f"Mood: {sync_info['mood']}")
```