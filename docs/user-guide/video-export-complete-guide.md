# Video Export Complete Guide

This comprehensive guide covers all aspects of exporting video timelines from AliceMultiverse to professional editing software.

## Overview

AliceMultiverse supports export to three major formats:
- **EDL (Edit Decision List)** - Universal format for DaVinci Resolve, Premiere Pro, etc.
- **XML (Final Cut Pro XML)** - Advanced format with effects and metadata
- **JSON (CapCut)** - Mobile-friendly format for CapCut editing

## Quick Start

### Basic Timeline Export

```bash
# Create and export a simple timeline
alice create_video_timeline \
  --images "cyberpunk_city_*.jpg" \
  --audio "synthwave_track.mp3" \
  --export-formats edl,xml,capcut
```

This creates timeline files in `~/Documents/AliceExports/[timestamp]/`

### Using MCP Tools in Claude

```text
User: Create a video timeline from my cyberpunk images synced to music

Claude: I'll create a beat-synced timeline for your cyberpunk images.
[Uses create_video_timeline tool with beat sync enabled]

Created timeline with 47 clips synced to beats. Exported to:
- EDL: ~/Documents/AliceExports/Alice_Timeline_20241220_143022/timeline.edl
- XML: ~/Documents/AliceExports/Alice_Timeline_20241220_143022/timeline.xml
- CapCut: ~/Documents/AliceExports/Alice_Timeline_20241220_143022/timeline.json
```

## Export Formats Explained

### EDL (Edit Decision List)

EDL is the most universal format, dating back to tape-based editing. It's simple but reliable.

**Structure:**
```edl
TITLE: Alice Timeline Export

001  001      V     C        00:00:00:00 00:00:02:00 00:00:00:00 00:00:02:00
* FROM CLIP NAME: cyberpunk_city_001.jpg

002  001      V     C        00:00:02:00 00:00:04:00 00:00:02:00 00:00:04:00
* FROM CLIP NAME: cyberpunk_city_002.jpg
* EFFECT NAME: CROSS DISSOLVE
* EFFECT DURATION: 00:00:00:15
```

**Advantages:**
- Works with almost all professional NLEs
- Simple and human-readable
- Reliable for basic cuts and dissolves

**Limitations:**
- No color information
- Limited transition types
- No advanced effects

### XML (Final Cut Pro XML)

XML format carries much more information including effects, color corrections, and metadata.

**Key Features:**
- Full transition support
- Metadata preservation (tags, ratings, notes)
- Audio track support
- Marker/beat sync points
- Color space information

**DaVinci Resolve Import:**
1. File → Import → Timeline → Import AAF, EDL, XML
2. Select the XML file
3. Choose "Import as New Timeline"
4. Enable "Automatically import source clips into media pool"

### JSON (CapCut Format)

Optimized for mobile editing with CapCut's specific requirements.

**Features:**
- Simplified structure for mobile
- Direct asset references
- Effect presets
- Text overlay timing

**CapCut Import Process:**
1. Copy JSON file to phone
2. Open CapCut → New Project
3. Import → Timeline → Select JSON
4. CapCut will prompt to locate media files

## Proxy Generation

Proxies are lower-resolution versions of your media for smoother editing.

### Automatic Proxy Generation

```bash
# Export with 720p proxies
alice export_timeline \
  --timeline timeline.json \
  --generate-proxies \
  --proxy-resolution 1280x720
```

### Proxy Settings

**Recommended Resolutions:**
- **1080p Editing**: 960×540 proxies
- **4K Editing**: 1280×720 proxies  
- **8K Editing**: 1920×1080 proxies

**Codec Options:**
- H.264: Best compatibility
- ProRes Proxy: Best quality (Mac)
- DNxHD: Best for Windows

## Beat Sync and Markers

### Music-Synced Timelines

When you provide audio, Alice automatically:
1. Detects beats and tempo
2. Identifies downbeats (strong beats)
3. Aligns cuts to musical rhythm
4. Adds markers for key moments

### Beat Sync Example

```python
# Using Python API
from alicemultiverse.workflows import create_video_timeline

timeline = create_video_timeline(
    images=["shot1.jpg", "shot2.jpg", "shot3.jpg"],
    audio="music.mp3",
    sync_to_beat=True,
    cuts_per_beat=0.5  # Cut every 2 beats
)
```

### Marker Types

**Beat Markers:**
- Color: Blue
- Purpose: Show rhythm points
- Use: Manual fine-tuning

**Section Markers:**
- Color: Green  
- Purpose: Song structure (verse, chorus)
- Use: Major edit decisions

**Mood Markers:**
- Color: Purple
- Purpose: Energy/mood changes
- Use: Pacing adjustments

## Advanced Timeline Creation

### Multi-Track Audio

```python
timeline_data = {
    "name": "Complex Edit",
    "video_tracks": [...],
    "audio_tracks": [
        {
            "path": "music.mp3",
            "track": 1,
            "volume": 0.8
        },
        {
            "path": "voiceover.wav", 
            "track": 2,
            "volume": 1.0,
            "start_time": 5.0
        }
    ]
}
```

### Transition Specifications

```python
clips = [
    {
        "path": "shot1.jpg",
        "duration": 3.0,
        "transition_out": {
            "type": "cross_dissolve",
            "duration": 0.5
        }
    },
    {
        "path": "shot2.jpg",
        "duration": 3.0,
        "transition_in": {
            "type": "dip_to_color",
            "duration": 0.25,
            "color": "#000000"
        }
    }
]
```

### Speed Ramps and Time Remapping

```python
clip = {
    "path": "action_shot.jpg",
    "duration": 5.0,
    "speed_points": [
        {"time": 0.0, "speed": 1.0},
        {"time": 2.0, "speed": 0.5},   # Slow motion
        {"time": 3.0, "speed": 2.0},   # Speed up
        {"time": 5.0, "speed": 1.0}
    ]
}
```

## Platform-Specific Tips

### DaVinci Resolve

**Color Management:**
1. Set timeline color space to match your workflow
2. Enable "Use color space aware grading"
3. Apply input LUT if needed

**Proxy Workflow:**
1. Generate optimized media on import
2. Link proxies via filename matching
3. Toggle proxy mode with Playback → Proxy Mode

**Beat Sync Enhancement:**
- Use Fairlight page to visualize beat markers
- Adjust cuts with audio waveform visible
- Use "Slip Edit" mode to maintain sync

### Adobe Premiere Pro

**Import Process:**
1. File → Import → Select EDL
2. Choose sequence settings
3. Link media manually if needed

**Proxy Creation:**
- Use Media Encoder for batch proxy creation
- Create proxy preset matching Alice's output
- Enable "Attach Proxies" in project settings

### Final Cut Pro X

**XML Import:**
1. File → Import → XML
2. Create new event for organization
3. Let FCPX analyze for color balance

**Optimized Workflow:**
- Create optimized media on import
- Use "Audition" feature for shot alternatives
- Magnetic timeline respects beat markers

### CapCut Mobile

**Preparation:**
1. Transfer all media to phone first
2. Organize in CapCut folder structure
3. Import JSON last

**Performance Tips:**
- Use proxy files for smooth playback
- Enable hardware acceleration
- Close other apps during edit

## Troubleshooting

### Common Issues

**"Media Offline" Errors:**
- Check file paths are relative
- Ensure all media is in expected location
- Verify filename case sensitivity

**Sync Issues:**
- Confirm audio sample rate matches project
- Check frame rate consistency
- Verify beat detection accuracy

**Color Shifts:**
- Set correct color space in NLE
- Disable automatic color correction
- Check gamma settings

### Performance Optimization

**Large Projects (100+ clips):**
1. Generate proxies before import
2. Split into smaller sequences
3. Use nested timelines
4. Increase cache allocation

**Memory Management:**
- Close unnecessary applications
- Increase GPU memory allocation
- Use background render when possible

## Best Practices

### File Organization

```
ProjectName/
├── Exports/
│   ├── timeline.edl
│   ├── timeline.xml
│   └── timeline.json
├── Media/
│   ├── Images/
│   ├── Audio/
│   └── Proxies/
└── Projects/
    └── DaVinci/
```

### Naming Conventions

- Use sequential numbers: `shot_001.jpg`, `shot_002.jpg`
- Include date stamps: `20241220_shot_001.jpg`
- Avoid spaces and special characters
- Keep extensions lowercase

### Version Control

1. Export new version for each major change
2. Include version in timeline name
3. Keep master EDL as backup
4. Document changes in notes field

## Advanced Workflows

### Round-Trip Editing

1. Export from Alice → Edit in NLE → Export markers
2. Import markers back to Alice
3. Re-generate with modifications
4. Maintain sync throughout

### Multi-Platform Delivery

```bash
# Generate all formats with platform-specific settings
alice export_timeline \
  --timeline master.json \
  --formats youtube,instagram,tiktok \
  --include-proxies \
  --optimize-for-platform
```

### Collaborative Workflows

1. Export XML with full metadata
2. Share via cloud storage
3. Import preserves all creative decisions
4. Comments and markers travel with timeline

## CLI Reference

### Key Commands

```bash
# Create timeline from images
alice create_video_timeline --images "*.jpg" --duration-per-image 2.0

# Sync to music with beat detection  
alice create_video_timeline --images "*.jpg" --audio music.mp3 --sync-to-beat

# Export specific format
alice export_timeline --timeline project.json --formats edl

# Generate proxies only
alice generate_proxies --images "*.jpg" --resolution 1280x720
```

### Options Reference

- `--export-formats`: Comma-separated list (edl,xml,capcut)
- `--generate-proxies`: Create low-res versions
- `--proxy-resolution`: WIDTHxHEIGHT format
- `--sync-to-beat`: Enable music synchronization
- `--transition-type`: Default transition (cut,dissolve,fade)
- `--transition-duration`: Length in seconds

## Summary

The video export system in AliceMultiverse bridges the gap between AI-powered media organization and professional video editing. By supporting multiple formats and providing intelligent features like beat sync and proxy generation, it enables smooth workflows from creative selection to final edit.

Key takeaways:
- Choose format based on your NLE
- Always generate proxies for large projects
- Use beat sync for music videos
- Organize files before import
- Test with small projects first

For more specific workflows, see:
- [Music Sync Tutorial](music-sync-tutorial.md)
- [Quick Selection Workflow](quick-selection-workflow-guide.md)
- [Scene Detection Guide](scene-detection-guide.md)