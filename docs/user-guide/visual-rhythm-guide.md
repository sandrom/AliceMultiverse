# Visual Rhythm Guide

Master the art of pacing your edits with AliceMultiverse's visual rhythm analysis, which suggests optimal shot durations based on image complexity and energy levels.

## Overview

Visual rhythm analysis helps you create well-paced edits by analyzing:
- **Visual Complexity**: How much detail viewers need to process
- **Energy Levels**: The intensity and dynamism of each shot
- **Pacing Balance**: The rhythm and flow of your sequence
- **Musical Alignment**: Sync with beat patterns when provided

## Quick Start

### Basic Rhythm Analysis

```bash
# Analyze rhythm for image sequence
alice transitions rhythm shot1.jpg shot2.jpg shot3.jpg -o rhythm.json

# With target duration (30 seconds total)
alice transitions rhythm *.jpg -d 30 -o pacing.json

# Synced to music BPM (120 beats per minute)
alice transitions rhythm *.jpg -b 120 -o beat_sync.json

# Export as CSV for spreadsheet
alice transitions rhythm *.jpg -f csv -o timing.csv
```

### Using MCP Tools in Claude

```text
User: Analyze the pacing for my image sequence

Claude: I'll analyze the visual rhythm and suggest pacing for your sequence.
[Analyzes complexity and energy of each image]

Visual Rhythm Analysis:
Total suggested duration: 24.5 seconds
Balance score: 78% (Good variety)

Shot-by-shot breakdown:
1. establishing_wide.jpg
   - Duration: 3.5s (long hold)
   - Complexity: High (0.82)
   - Energy: Low (0.35)
   - Style: Establishing shot needs time

2. action_shot.jpg
   - Duration: 1.2s (quick cut)
   - Complexity: Medium (0.54)
   - Energy: High (0.88)
   - Style: High energy, quick read

3. detail_close.jpg
   - Duration: 2.0s (standard)
   - Complexity: Medium (0.61)
   - Energy: Medium (0.52)
   - Style: Balanced pacing
```

## Understanding Visual Analysis

### Visual Complexity Components

1. **Edge Density** (30%)
   - Amount of detail and lines
   - More edges = more complex
   - Affects processing time

2. **Color Variance** (20%)
   - Diversity of colors
   - Color relationships
   - Visual richness

3. **Texture Complexity** (20%)
   - Surface detail
   - Pattern density
   - Fine details

4. **Compositional Elements** (20%)
   - Number of distinct objects
   - Spatial relationships
   - Visual hierarchy

5. **Movement Potential** (10%)
   - Implied motion
   - Dynamic lines
   - Action cues

### Energy Profile Analysis

1. **Visual Energy**
   - Overall intensity
   - Combined metrics
   - Viewer engagement

2. **Brightness Energy**
   - Luminance levels
   - Light/dark balance
   - Attention drawing

3. **Color Energy**
   - Saturation intensity
   - Vibrancy
   - Emotional impact

4. **Motion Energy**
   - Blur detection
   - Movement indicators
   - Dynamic feeling

5. **Emotional Energy**
   - Color temperature
   - Mood indicators
   - Psychological impact

## Pacing Suggestions

### Cut Styles

#### Quick (< 1.0s)
- High energy shots
- Simple compositions
- Action moments
- Rhythmic emphasis

#### Standard (1.0-2.5s)
- Balanced complexity
- Normal viewing time
- Most common duration
- Steady pacing

#### Long (2.5-4.0s)
- Complex compositions
- Establishing shots
- Emotional moments
- Detailed scenes

#### Hold (> 4.0s)
- Very complex images
- Key story moments
- Contemplative scenes
- Major transitions

### Duration Calculation

Base formula:
```
Duration = Base × Complexity Factor × Energy Factor

Where:
- Base = 2.0 seconds (default)
- Complexity Factor = 1.0 + (complexity × 1.5)
- Energy Factor = 1.0 - (energy × 0.3)
```

## Music Synchronization

### BPM Alignment

When you provide BPM:
1. Calculates beat duration (60/BPM)
2. Rounds shot durations to nearest beat
3. Maintains musical rhythm
4. Creates cohesive flow

Example at 120 BPM:
- Beat = 0.5 seconds
- Durations: 1.0s (2 beats), 1.5s (3 beats), 2.0s (4 beats)

### Target Duration

When you specify total duration:
1. Calculates proportional durations
2. Scales to fit target
3. Maintains relative pacing
4. Achieves precise timing

## Rhythm Curves

### Understanding the Curve

The rhythm curve shows pacing variation:
```
High values = Fast cutting
Low values = Slow pacing

Example curve:
Shot 1: ████████████████████ (slow)
Shot 2: ████████ (fast)
Shot 3: ████████████ (medium)
Shot 4: ████ (very fast)
Shot 5: ████████████████ (slow)
```

### Balance Score

Measures rhythm variety:
- **>80%**: Excellent variety
- **60-80%**: Good balance
- **40-60%**: Moderate variety
- **<40%**: Monotonous pacing

Factors:
- Duration variety
- Energy distribution
- Pattern changes
- Overall flow

## Practical Applications

### 1. Music Videos

```python
# Fast-paced music video
"Analyze rhythm for EDM track at 128 BPM"

# Results in:
# - Quick cuts on beats
# - Energy matching music
# - Dynamic pacing
```

### 2. Documentary

```python
# Thoughtful pacing
"Analyze rhythm for documentary footage"

# Results in:
# - Longer holds for information
# - Breathing room
# - Natural flow
```

### 3. Action Sequence

```python
# High-energy cutting
"Analyze rhythm for chase scene"

# Results in:
# - Rapid cuts for action
# - Brief holds for orientation
# - Building tension
```

### 4. Artistic Montage

```python
# Varied pacing
"Create rhythm with 30 second target"

# Results in:
# - Mixed durations
# - Emotional flow
# - Precise timing
```

## Advanced Features

### Energy Matching to Music

```python
# When music energy data available
music_energy = [0.3, 0.5, 0.9, 0.7, 0.4]

# Matches:
# - Low energy music → longer shots
# - High energy music → faster cuts
# - Natural synchronization
```

### Multi-Layer Analysis

Considers multiple factors:
1. Visual complexity
2. Energy levels
3. Music rhythm
4. Narrative needs
5. Viewer psychology

### Custom Parameters

```python
analyzer = VisualRhythmAnalyzer()
analyzer.base_duration = 1.5  # Faster base
analyzer.complexity_multiplier = 2.0  # More variation
```

## Integration Examples

### With Scene Detection

```python
# Pace detected scenes
"Detect scenes, then analyze rhythm for each"
```

### With Match Cuts

```python
# Time match cuts rhythmically
"Find match cuts and place on beat"
```

### With Color Flow

```python
# Combine with color transitions
"Analyze rhythm and color flow together"
```

## Best Practices

### 1. Content Awareness
- Consider your audience
- Match genre expectations
- Respect narrative needs
- Balance variety with coherence

### 2. Testing and Refinement
- Start with suggestions
- Preview with music
- Adjust as needed
- Trust your instincts

### 3. Technical Considerations
- Higher resolution helps analysis
- Clear compositions work best
- Consistent image quality
- Proper sequence order

### 4. Creative Freedom
- Suggestions are starting points
- Override when needed
- Experiment with extremes
- Find your style

## Export Formats

### JSON Export

```json
{
  "shots": [
    {
      "complexity": 0.75,
      "energy": 0.45,
      "suggested_duration": 2.8,
      "cut_style": "long"
    }
  ],
  "rhythm_curve": [0.2, 0.8, 0.5, 0.9, 0.3],
  "energy_curve": [0.3, 0.9, 0.6, 0.8, 0.4],
  "balance_score": 0.78,
  "total_duration": 24.5
}
```

### CSV Export

```csv
shot,complexity,energy,duration,style,reasoning
0,0.75,0.45,2.8,long,"Complex shot needs time to read"
1,0.42,0.88,1.2,quick,"High energy, low complexity - quick cut"
```

## Troubleshooting

### Pacing Too Fast/Slow
- Adjust base_duration parameter
- Modify complexity_multiplier
- Check energy calculations
- Review shot selection

### Poor Balance Score
- Add variety to shots
- Mix complex and simple
- Vary energy levels
- Avoid repetition

### Music Sync Issues
- Verify BPM accuracy
- Check beat alignment
- Adjust snap tolerance
- Fine-tune manually

## Tips and Tricks

### 1. Genre Guidelines
- **Action**: 0.5-2s average
- **Drama**: 2-5s average
- **Documentary**: 3-8s average
- **Music Video**: Beat-dependent

### 2. Psychological Pacing
- Start slower to establish
- Build energy gradually
- Use pauses for impact
- End with resolution

### 3. Technical Optimization
- Batch similar content
- Cache analysis results
- Process at optimal resolution
- Use consistent formats

## CLI Reference

```bash
# Basic usage
alice transitions rhythm [images...] [options]

# Options
-o, --output      Output file (default: rhythm_analysis.json)
-d, --duration    Target total duration in seconds
-b, --bpm         Music BPM for rhythm matching
-f, --format      Export format: json, csv (default: json)
-v, --verbose     Show detailed complexity analysis

# Examples
alice transitions rhythm shot*.jpg -o pacing.json
alice transitions rhythm *.png -d 60 -b 120 -o timed.json
alice transitions rhythm sequence/*.jpg -f csv -o timing.csv
```

## Summary

Visual rhythm analysis in AliceMultiverse provides:
- Intelligent pacing suggestions
- Complexity-based timing
- Energy-aware cutting
- Musical synchronization
- Balance optimization

Key benefits:
- Remove guesswork from pacing
- Create professional rhythm
- Match music naturally
- Save editing time
- Improve viewer engagement

For more details:
- [Music Sync Tutorial](music-sync-tutorial.md)
- [Video Export Guide](video-export-complete-guide.md)
- [Scene Detection Guide](scene-detection-guide.md)