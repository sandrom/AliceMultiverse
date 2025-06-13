# Timeline Preview Guide

The Timeline Preview feature provides an interactive web interface for reviewing and adjusting video timelines before exporting to your editing software. This guide covers how to use the preview tools effectively.

## Overview

The timeline preview allows you to:
- 📊 Visualize your timeline with clips, transitions, and markers
- 🎯 Drag-and-drop to reorder clips
- ✂️ Trim clip in/out points
- 🔄 Add or modify transitions
- 💾 Export to EDL, XML, or JSON formats

## Starting a Preview Session

### From an Existing Timeline

```python
# If you have a timeline from create_video_timeline
result = await create_video_timeline(
    images=["hash1", "hash2", "hash3"],
    music_path="/path/to/music.mp3",
    style="music_video"
)

# Preview the timeline
preview = await preview_video_timeline(
    timeline_data=result["timeline"],
    auto_open=True  # Opens browser automatically
)

print(f"Preview URL: {preview['preview_url']}")
print(f"Session ID: {preview['session_id']}")
```

### Creating a Custom Timeline

```python
# Build timeline data manually
timeline_data = {
    "name": "My Project",
    "duration": 30.0,
    "frame_rate": 30.0,
    "resolution": [1920, 1080],
    "clips": [
        {
            "asset_path": "/path/to/clip1.jpg",
            "start_time": 0.0,
            "duration": 5.0,
            "transition_out": "dissolve",
            "transition_out_duration": 1.0
        },
        {
            "asset_path": "/path/to/clip2.jpg", 
            "start_time": 5.0,
            "duration": 5.0,
            "transition_in": "dissolve",
            "transition_in_duration": 1.0
        }
    ],
    "markers": [
        {"time": 5.0, "type": "beat", "label": "Drop"},
        {"time": 10.0, "type": "section", "label": "Chorus"}
    ],
    "audio_tracks": [{
        "path": "/path/to/music.mp3",
        "start_time": 0.0
    }]
}

# Open preview
preview = await preview_video_timeline(timeline_data)
```

## Using the Web Interface

### Interface Overview

The preview interface consists of:

1. **Video Preview Area**: Shows current frame preview (future: video playback)
2. **Timeline Track**: Visual representation of clips
3. **Controls**: Play, pause, undo, redo, export buttons
4. **Status Bar**: Shows current operation status

### Reordering Clips

1. Click and drag any clip in the timeline
2. Drop it in the new position
3. The timeline automatically adjusts timing
4. Use Undo if you want to revert

### Trimming Clips

Currently requires using the API:

```python
# Trim the second clip
await update_preview_timeline(
    session_id=preview["session_id"],
    operation="trim",
    clips=[{
        "index": 1,  # Second clip (0-indexed)
        "in_point": 1.0,  # Start 1 second in
        "out_point": 4.0,  # End at 4 seconds
        "duration": 3.0   # New duration
    }]
)
```

### Adding Transitions

```python
# Add a fade transition between clips
await update_preview_timeline(
    session_id=preview["session_id"],
    operation="add_transition",
    clips=[
        {
            "index": 0,
            "transition_out": "fade",
            "transition_out_duration": 1.0
        },
        {
            "index": 1,
            "transition_in": "fade", 
            "transition_in_duration": 1.0
        }
    ]
)
```

### Keyboard Shortcuts

The timeline preview interface supports the following keyboard shortcuts for efficient navigation and editing:

**Playback Controls:**
- `Space` - Play/Pause timeline
- `←` (Left Arrow) - Step backward one frame
- `→` (Right Arrow) - Step forward one frame
- `Home` - Jump to beginning of timeline
- `End` - Jump to end of timeline

**Editing:**
- `Ctrl+Z` / `Cmd+Z` - Undo last action
- `Ctrl+Y` / `Cmd+Y` - Redo last undone action
- `Delete` - Delete selected clip
- `Ctrl+A` / `Cmd+A` - Select all clips

**Navigation:**
- `+` / `=` - Zoom in timeline
- `-` - Zoom out timeline
- `0` - Reset zoom to fit timeline
- `Shift+Scroll` - Horizontal scroll through timeline
- `Ctrl+Scroll` / `Cmd+Scroll` - Zoom in/out timeline

**Export:**
- `Ctrl+E` / `Cmd+E` - Open export dialog
- `Ctrl+S` / `Cmd+S` - Quick export to JSON

**View:**
- `F` - Toggle fullscreen preview
- `G` - Toggle grid overlay
- `M` - Toggle marker visibility
- `W` - Toggle waveform display (when audio track present)

## Exporting Your Timeline

### Export Formats

1. **JSON** - Full timeline data for further processing
2. **EDL** - Edit Decision List for DaVinci Resolve
3. **XML** - Final Cut Pro XML format

### Export Examples

```python
# Export to EDL for DaVinci Resolve
result = await export_preview_timeline(
    session_id=preview["session_id"],
    format="edl",
    output_path="~/Desktop/my_project.edl"
)

# Export to JSON for archival
result = await export_preview_timeline(
    session_id=preview["session_id"],
    format="json",
    output_path="~/Desktop/my_project_timeline.json"
)
```

## Advanced Usage

### Checking Server Status

```python
# Check if preview server is running
status = await get_timeline_preview_status()
print(f"Server running: {status['running']}")
print(f"Active sessions: {status.get('sessions', 0)}")
```

### Working with Multiple Sessions

You can have multiple preview sessions open simultaneously:

```python
# Create multiple previews
preview1 = await preview_video_timeline(timeline1_data)
preview2 = await preview_video_timeline(timeline2_data)

# Work with specific sessions
await update_preview_timeline(
    session_id=preview1["session_id"],
    operation="reorder",
    clips=[{"old_index": 0, "new_index": 2}]
)
```

## Tips and Best Practices

### Performance

- The preview server runs locally on port 8001
- Keep sessions under 1000 clips for best performance
- Close unused sessions to free memory

### Workflow Integration

1. **Quick Preview**: Use for rough cut review before detailed editing
2. **Collaboration**: Share preview URLs for feedback (local network only)
3. **Version Control**: Export JSON timelines for version tracking

### Troubleshooting

**Server won't start:**
- Check if port 8001 is already in use
- Ensure you have the required dependencies: `pip install fastapi uvicorn`

**Can't see preview:**
- Make sure your browser allows localhost connections
- Check the browser console for errors

**Changes not saving:**
- Always export your timeline before closing the browser
- The preview is session-based and doesn't auto-save

## Future Enhancements

Planned features include:
- Real-time video playback in preview
- Visual transition effects
- Beat grid overlay
- Auto-save functionality
- Cloud preview sharing

## Example: Complete Music Video Workflow

```python
# 1. Create video timeline from images and music
timeline_result = await create_video_timeline(
    images=selected_images,
    music_path="song.mp3",
    style="music_video"
)

# 2. Open in preview
preview = await preview_video_timeline(
    timeline_data=timeline_result["timeline"],
    auto_open=True
)

# 3. Make adjustments in the browser
# ... user makes changes ...

# 4. Export final timeline
final_edl = await export_preview_timeline(
    session_id=preview["session_id"],
    format="edl",
    output_path="final_cut.edl"
)

print(f"Timeline exported to: {final_edl['output_path']}")
```

The timeline preview provides a bridge between AI-generated timelines and professional editing software, allowing you to refine your cuts before committing to a full edit.