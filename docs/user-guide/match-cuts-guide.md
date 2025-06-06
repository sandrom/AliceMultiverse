# Match Cuts Guide

Learn how to use AliceMultiverse's match cut detection to create seamless transitions where movement, shapes, or composition align perfectly between shots.

## Overview

Match cuts are a powerful editing technique where visual elements align between consecutive shots, creating smooth, almost invisible transitions. AliceMultiverse automatically detects:

- **Motion Matching**: Similar movement patterns between shots
- **Shape Matching**: Aligned geometric shapes (circles, rectangles, lines)
- **Action Continuity**: Natural flow of movement across cuts
- **Compositional Alignment**: Similar framing and visual weight

## Quick Start

### Basic Match Cut Detection

```bash
# Analyze a sequence for match cuts
alice transitions matchcuts shot1.jpg shot2.jpg shot3.jpg -o match_cuts.json

# With custom threshold (lower = more matches)
alice transitions matchcuts *.jpg -t 0.6 -o cuts.json

# Export as EDL for editing software
alice transitions matchcuts *.jpg -f edl -o cuts.edl
```

### Using MCP Tools in Claude

```text
User: Find match cuts in my action sequence

Claude: I'll analyze your action sequence for match cuts.
[Analyzes images for matching motion and shapes]

Found 3 potential match cuts:
1. shot_012.jpg → shot_015.jpg
   - Type: Motion match
   - Confidence: 87%
   - Both show rightward movement

2. shot_023.jpg → shot_024.jpg  
   - Type: Shape match
   - Confidence: 92%
   - Circular objects align perfectly

3. shot_031.jpg → shot_033.jpg
   - Type: Action continuity
   - Confidence: 78%
   - Jump motion continues across cut
```

## Understanding Match Cuts

### Types of Match Cuts

#### 1. Motion Match
Objects or camera movement continues across the cut:
- Person walking left → continues left in next shot
- Camera pan right → continues right
- Falling object → continues falling

#### 2. Shape Match
Similar shapes in similar positions:
- Circle (sun) → Circle (clock face)
- Rectangle (door) → Rectangle (window)
- Line (horizon) → Line (table edge)

#### 3. Action Match
Action continues naturally:
- Throwing motion → Object flying
- Door opening → Entering room
- Head turn → New angle same direction

#### 4. Composite Match
Multiple elements align:
- Motion + shape alignment
- Color + composition match
- All elements working together

### Match Cut Analysis

Each detected match includes:

```json
{
  "from_index": 12,
  "to_index": 15,
  "analysis": {
    "match_type": "motion",
    "confidence": 0.87,
    "action_continuity": 0.82,
    "motion_matches": [
      {
        "vector1": {
          "direction": [0.9, 0.1],
          "magnitude": 0.8,
          "center": [0.7, 0.5]
        },
        "similarity": 0.91
      }
    ],
    "shape_matches": [
      {
        "type": "circle",
        "confidence": 0.85,
        "alignment": 0.88
      }
    ]
  }
}
```

## Practical Applications

### 1. Action Sequences

```python
# Find match cuts in fight scene
"Analyze these action shots for match cuts"

# Results help create:
# - Seamless combat flow
# - Continuous movement
# - Dynamic energy
```

### 2. Montage Creation

```python
# Build thematic montage
"Find shape matches for circular transition theme"

# Creates connections like:
# - Sun → Clock → Eye → Wheel
# - All circular, smooth flow
```

### 3. Scene Transitions

```python
# Connect different locations
"Find match cuts to transition between scenes"

# Examples:
# - Door closing → Door opening (new location)
# - Looking up → Looking down (POV shift)
# - Hand reaching → Hand grabbing
```

## Advanced Techniques

### Threshold Tuning

```bash
# Strict matching (high confidence only)
alice transitions matchcuts *.jpg -t 0.85

# Loose matching (find more possibilities)
alice transitions matchcuts *.jpg -t 0.6

# Very loose (experimental/creative)
alice transitions matchcuts *.jpg -t 0.4
```

### Multi-Image Analysis

The system checks multiple frame distances:
- Adjacent frames (1→2)
- Skip 1 frame (1→3)
- Skip up to 4 frames (1→5)

This finds matches even with intermediate shots.

### Export Formats

#### EDL (Edit Decision List)
```edl
001  001      V     C        00:00:12:00 00:00:15:00
* MATCH CUT: MOTION
* CONFIDENCE: 87%
```

#### JSON (Detailed Data)
```json
{
  "match_cuts": [...],
  "total_matches": 5,
  "metadata": {
    "threshold": 0.7,
    "images_analyzed": 50
  }
}
```

## Visual Examples

### Example 1: Motion Match
- **Shot A**: Car moving left to right
- **Shot B**: Train moving left to right
- **Result**: Seamless motion continuation

### Example 2: Shape Match  
- **Shot A**: Full moon in upper right
- **Shot B**: Clock face in upper right
- **Result**: Object transformation effect

### Example 3: Action Match
- **Shot A**: Person throwing ball
- **Shot B**: Ball flying through air
- **Result**: Natural action flow

## Integration with Other Features

### With Scene Detection
```python
# Find match cuts at scene boundaries
"Detect scenes then find match cuts between them"
```

### With Visual Rhythm
```python
# Time match cuts to music
"Find match cuts and sync to beat"
```

### With Color Flow
```python
# Combine techniques
"Find match cuts with compatible colors"
```

## Best Practices

### 1. Shooting for Match Cuts
- Plan shots with exits/entrances in mind
- Maintain consistent screen direction
- Use similar framing for matched shots
- Consider shape and motion continuity

### 2. Detection Strategy
- Start with default threshold (0.7)
- Review results and adjust
- Lower threshold if missing good matches
- Raise threshold if too many false positives

### 3. Creative Use
- Don't force match cuts everywhere
- Use sparingly for maximum impact
- Consider pacing and rhythm
- Match cuts can compress time/space

### 4. Technical Considerations
- Higher resolution = better detection
- Clear shapes and motion work best
- Consistent lighting helps matching
- Avoid overly complex compositions

## Troubleshooting

### No Matches Found
- Lower threshold with `-t 0.5`
- Check if shots have clear motion/shapes
- Ensure images are in sequence
- Try analyzing fewer images at once

### Too Many False Matches
- Raise threshold with `-t 0.8`
- Review match types in output
- Focus on specific match types
- Manually curate results

### Performance Issues
- Process in batches of 50-100 images
- Use lower resolution for initial detection
- Cache results for repeated analysis

## CLI Reference

```bash
# Basic usage
alice transitions matchcuts [images...] [options]

# Options
-o, --output     Output file (default: match_cuts.json)
-t, --threshold  Match confidence threshold 0-1 (default: 0.7)
-f, --format     Export format: json, edl (default: json)
-v, --verbose    Show detailed analysis

# Examples
alice transitions matchcuts shot*.jpg -o cuts.json
alice transitions matchcuts *.png -t 0.6 -f edl -o timeline.edl
alice transitions matchcuts sequence/*.jpg -v
```

## Summary

Match cut detection in AliceMultiverse enables:
- Automatic discovery of cutting opportunities
- Smooth, professional transitions
- Creative connections between shots
- Time and space compression
- Enhanced visual flow

Key points:
- Motion, shape, and action matching
- Adjustable detection threshold
- Multiple export formats
- Integration with other features
- Creative and technical applications

For more details:
- [Transition Analysis Guide](transitions-guide.md)
- [Visual Rhythm Guide](visual-rhythm-guide.md)
- [Video Export Guide](video-export-complete-guide.md)