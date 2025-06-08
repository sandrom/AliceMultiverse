# Multi-Version Export Guide

Create platform-optimized versions of your videos automatically! This guide shows how to adapt a single timeline for Instagram, TikTok, YouTube, and more with intelligent cropping, pacing adjustments, and platform-specific features.

## Overview

The Multi-Version Export system automatically adapts your master timeline for different social media platforms, handling:
- **Aspect Ratio Conversion**: Smart cropping from 16:9 to 9:16, 1:1, etc.
- **Duration Constraints**: Trim or extend to meet platform limits
- **Pacing Optimization**: Adjust cut timing for platform preferences
- **Feature Adaptation**: Add platform-specific enhancements

## Quick Start

### Export to Multiple Platforms

```python
# In Claude:
"Export my timeline for Instagram Reel and TikTok"

# This will:
# 1. Convert to 9:16 vertical format
# 2. Ensure duration fits platform limits
# 3. Optimize pacing for short-form content
# 4. Apply platform-specific features
```

### Check Platform Compatibility

```python
# See which platforms work best with your timeline
"Check which platforms my 45-second horizontal video works for"

# Returns compatibility report with required adjustments
```

## Supported Platforms

### Vertical Short-Form
- **Instagram Reel**: 9:16, 3-90s, loop-friendly
- **Instagram Story**: 9:16, 1-60s, interactive zones
- **TikTok**: 9:16, 3-180s, trend optimization
- **YouTube Shorts**: 9:16, 1-60s, discovery features

### Square Format
- **Instagram Post**: 1:1, 3-60s, feed optimized

### Horizontal Long-Form
- **YouTube**: 16:9, unlimited duration, HDR support
- **Twitter/X**: 16:9, 0.5-140s, quick view optimized

### Archival
- **Master**: Original quality, 4K, HDR preservation

## Platform-Specific Features

### Instagram Reel
- **Safe Zones**: UI elements at top (15%) and bottom (10%)
- **Loop Optimization**: Seamless beginning/end transition
- **Max File Size**: 100MB
- **Preferred Duration**: 30 seconds

### TikTok
- **Trend Sync Points**: Identifies moments for sound sync
- **Quick Hook**: First 3 seconds optimized for attention
- **Extended Duration**: Up to 3 minutes supported
- **Max File Size**: 287MB

### YouTube Shorts
- **Shelf Eligibility**: Optimized for Shorts shelf
- **HDR Support**: Preserves high dynamic range
- **Discovery Features**: Metadata for algorithm

## Smart Adaptation Features

### Intelligent Cropping
The system uses AI to detect important regions in each clip:
```python
# Smart crop maintains subject focus
"Export for Instagram with smart cropping enabled"

# Center crop for simple framing
"Export for TikTok with center crop"
```

### Music Synchronization
When adapting duration, music sync is preserved:
```python
# Maintains beat alignment when trimming
"Export 90-second video for YouTube Shorts keeping music sync"
```

### Pacing Adjustments
Different platforms favor different pacing:
- **TikTok**: Faster cuts, dynamic hook
- **YouTube**: Balanced pacing, breathing room
- **Instagram**: Loop-friendly rhythm

## Workflow Examples

### 1. Music Video to Social Media

```python
# Original: 3-minute music video in 16:9

# Step 1: Check platform options
"What platforms can I export my 3-minute music video to?"

# Step 2: Create versions
"Export for Instagram Reel, TikTok, and YouTube Shorts"

# Results:
# - Instagram Reel: 90s max, 9:16 with chorus focus
# - TikTok: Full 3 minutes, 9:16 with trend markers
# - YouTube Shorts: 60s highlight, 9:16 with key moments
```

### 2. Batch Export for Campaign

```python
# Export everything at once
"Export my timeline for all social platforms and create a master"

# Creates:
# - timeline_instagram_reel_20250108_143022.json
# - timeline_instagram_story_20250108_143022.json
# - timeline_tiktok_20250108_143022.json
# - timeline_youtube_shorts_20250108_143022.json
# - timeline_master_20250108_143022.json
```

### 3. Platform-First Creation

```python
# Design for specific platform from start
"Create Instagram Reel version with 30-second target"

# Optimizations:
# - Selects best 30 seconds
# - Adds loop transitions
# - Ensures safe zones
# - Optimizes file size
```

## Advanced Features

### Custom Crop Regions

The system can use AI to detect subjects and maintain focus:
```python
# Each clip gets intelligent crop region
crop_regions = {
    "clip_0": {
        "x": 0.2,      # 20% from left
        "y": 0.0,      # Top aligned
        "width": 0.6,  # 60% of width
        "height": 1.0, # Full height
        "focus_point": [0.5, 0.3]  # Subject location
    }
}
```

### Platform Metadata

Each export includes platform-specific metadata:
```python
# Instagram features
"tap_zones": [
    {"type": "poll", "region": {"x": 0.2, "y": 0.1, "width": 0.6, "height": 0.15}}
]

# TikTok features
"trend_sync_points": [1.5, 5.0, 10.0, 15.0, 20.0]

# YouTube features
"chapters": ["Intro", "Verse", "Chorus", "Outro"]
```

## Export Formats

### JSON Export
Full timeline data with platform adaptations:
```json
{
  "name": "MyVideo_instagram_reel",
  "duration": 30.0,
  "resolution": [1080, 1920],
  "clips": [...],
  "metadata": {
    "platform": "instagram_reel",
    "adapted_for": "Instagram Reel",
    "aspect_ratio": "9:16"
  }
}
```

### EDL Export
For professional editing software:
```
TITLE: MyVideo_instagram_reel

001  001      V     C        00:00:00:00 00:00:05:00 00:00:00:00 00:00:05:00
* CROP: X=0.2 Y=0.0 W=0.6 H=1.0
```

## Tips & Best Practices

### 1. Start with Master Timeline
Always create a high-quality master version first, then adapt:
```python
"Export all platforms with master version"
```

### 2. Preview Before Export
Check adaptations before committing:
```python
"Show me how my video will look on each platform"
```

### 3. Test Key Moments
Ensure important scenes aren't cropped:
```python
"Check if the climax at 45 seconds fits in YouTube Shorts"
```

### 4. Optimize for Discovery
Each platform has different algorithms:
- **Instagram**: First 3 seconds crucial
- **TikTok**: Hook + trend alignment
- **YouTube**: Thumbnail moment + retention

### 5. File Size Management
Platforms have upload limits:
- Use preview quality for testing
- Export final quality for publishing
- Master version for archival

## Troubleshooting

### "Timeline too short for platform"
- Timeline will be extended by looping or holding last frame
- Consider adding b-roll or outro

### "Timeline too long for platform"
- Smart trim preserves important moments near markers
- Manual selection of best segment recommended

### "Aspect ratio crop loses important content"
- Enable smart cropping for AI detection
- Manually adjust crop regions if needed
- Consider platform-specific shoots

### "Pacing feels wrong after adaptation"
- Platform-specific pacing is applied automatically
- Disable with `maintain_original_pacing` option
- Fine-tune in editing software

## Integration with Other Features

### Timeline Preview
Preview adaptations before export:
```python
"Preview the TikTok version in browser"
```

### Natural Language Edits
Adjust platform versions:
```python
"Make the Instagram version more punchy"
```

### Style Consistency
Maintain visual coherence across platforms:
```python
"Apply consistent color grading to all versions"
```

## Next Steps

1. **Create Your First Multi-Version Export**
   ```python
   "Export my latest video for Instagram and TikTok"
   ```

2. **Experiment with Platform Features**
   ```python
   "Show me platform-specific features for my timeline"
   ```

3. **Build Platform-Optimized Templates**
   ```python
   "Create a template for Instagram Reels with my style"
   ```

Remember: Each platform has its own culture and preferences. The system handles technical requirements, but creative decisions about content selection and emphasis are yours to make!