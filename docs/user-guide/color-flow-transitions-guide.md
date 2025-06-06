# Color Flow Transitions Guide

The Color Flow Transitions feature analyzes color palettes and lighting between consecutive shots to create smooth, visually pleasing transitions for video editing.

## Overview

Color Flow Transitions help video editors create seamless transitions by:
- Analyzing dominant color palettes in each shot
- Detecting lighting direction and intensity
- Suggesting appropriate transition types
- Generating gradient masks and color matching data
- Exporting editor-specific formats

## Command Line Usage

### Analyze a Sequence

Analyze color flow across multiple shots:

```bash
alice transitions colorflow shot1.jpg shot2.jpg shot3.jpg -o color_data/
```

Options:
- `-o, --output`: Output directory for transition data
- `-d, --duration`: Transition duration in frames (default: 30)
- `-e, --editor`: Target editor: resolve, premiere, fcpx, fusion (default: resolve)
- `-v, --verbose`: Show detailed color palette information

### Analyze a Single Transition

For detailed analysis of a single transition:

```bash
alice transitions colorpair shot1.jpg shot2.jpg -o transition.json -v
```

This provides:
- Detailed color palette breakdown
- Lighting analysis with direction vectors
- Compatibility score explanation
- All suggested effects

## Python API Usage

### Basic Analysis

```python
from alicemultiverse.transitions import ColorFlowAnalyzer

# Create analyzer
analyzer = ColorFlowAnalyzer(n_colors=5)

# Analyze two shots
analysis = analyzer.analyze_shot_pair(
    'sunset.jpg',
    'night.jpg',
    transition_duration=30
)

# Check compatibility
print(f"Compatibility: {analysis.compatibility_score:.2%}")
print(f"Transition type: {analysis.gradient_transition.transition_type}")
```

### Sequence Analysis

```python
from alicemultiverse.transitions import analyze_sequence

# Analyze entire sequence
shots = ['shot1.jpg', 'shot2.jpg', 'shot3.jpg', 'shot4.jpg']
analyses = analyze_sequence(shots, transition_duration=24)

# Export for video editor
for i, analysis in enumerate(analyses):
    export_analysis_for_editor(
        analysis,
        f'transition_{i}.json',
        editor='resolve'
    )
```

## Understanding the Analysis

### Color Palette Extraction

The analyzer extracts:
- **Dominant Colors**: Top 5 colors by pixel count using K-means clustering
- **Color Weights**: Percentage of image each color represents
- **Average Brightness**: Overall luminance (0.0 to 1.0)
- **Average Saturation**: Color intensity (0.0 to 1.0)
- **Color Temperature**: Warm (>0.5) or cool (<0.5) tendency

### Lighting Analysis

Lighting detection includes:
- **Direction**: 2D vector showing primary light source direction
- **Intensity**: Brightness of highlights (0.0 to 1.0)
- **Type**: Classification as directional, ambient, or mixed
- **Shadow Density**: Percentage of dark areas

### Compatibility Score

The compatibility score (0-100%) considers:
- **Color Similarity** (40%): How well palettes match
- **Brightness Compatibility** (20%): Difference in overall brightness
- **Saturation Compatibility** (20%): Difference in color intensity
- **Lighting Compatibility** (20%): Similarity in lighting conditions

Higher scores indicate smoother, more natural transitions.

### Transition Types

Based on the analysis, three transition types are suggested:

1. **Linear**: Horizontal gradient, good for similar shots
2. **Radial**: Center-out gradient, ideal for brightness changes
3. **Diagonal**: Angled gradient, matches directional lighting

### Suggested Effects

Common effect suggestions include:
- `color_temperature_shift`: For warm/cool transitions
- `exposure_ramp`: For brightness differences
- `saturation_blend`: For saturation changes
- `lighting_transition`: For different lighting types
- `shadow_morph`: For shadow density changes
- `light_sweep`: For directional light changes
- `gradient_wipe`: Always suggested for smooth blending
- `color_match`: Always suggested for color harmony

## Editor Integration

### DaVinci Resolve

```bash
alice transitions colorflow *.jpg -o resolve_data/ -e resolve
```

Creates:
- JSON files with Fusion-compatible data
- Color matching LUTs (.cube files) for low compatibility transitions
- Import into Fusion for node-based compositing

### Adobe Premiere Pro

```bash
alice transitions colorflow *.jpg -o premiere_data/ -e premiere
```

Generates:
- JSON with keyframe data
- Color effect parameters
- Apply using expressions or manual keyframing

### Final Cut Pro X

```bash
alice transitions colorflow *.jpg -o fcpx_data/ -e fcpx
```

Produces:
- Motion template parameters
- Generator settings
- Use as transition generators between clips

### Blackmagic Fusion

```bash
alice transitions colorflow *.jpg -o fusion_data/ -e fusion
```

Exports:
- Complete node setup
- Background gradient settings
- Color corrector parameters
- Merge node with animated mix

## Best Practices

### Shot Selection
- Use consecutive shots from your timeline
- Include both source and target frames
- Higher resolution provides better color analysis

### Transition Duration
- 24-30 frames (1 second at 24-30fps) for subtle transitions
- 12-18 frames for quick cuts
- 48-60 frames for slow, dramatic transitions

### Color Matching
- Compatibility >70%: Natural transition, minimal correction needed
- Compatibility 50-70%: Use suggested effects for smoothing
- Compatibility <50%: Consider color matching LUT or different shot order

### Workflow Tips
1. Analyze your entire sequence first
2. Review compatibility scores
3. Reorder shots if needed for better flow
4. Export for your specific editor
5. Fine-tune in your editing software

## Examples

### Example 1: Day to Night Transition

```bash
alice transitions colorpair sunset.jpg night.jpg -v
```

Output:
```
Color Flow Analysis:
  Compatibility score: 42%
  Transition type: radial
  Blend curve: ease-in-out

Shot 1 Analysis:
  Dominant colors:
    1. RGB(255, 147, 41) (35.2%)  # Orange sunset
    2. RGB(255, 209, 102) (22.1%) # Yellow highlights
    3. RGB(135, 81, 138) (15.3%)  # Purple sky
  Color temperature: Warm (0.78)
  Lighting: directional (intensity: 0.92)

Shot 2 Analysis:
  Dominant colors:
    1. RGB(25, 42, 86) (42.1%)    # Dark blue night
    2. RGB(41, 74, 107) (28.3%)   # Medium blue
    3. RGB(255, 255, 200) (8.2%)  # Stars/lights
  Color temperature: Cool (0.21)
  Lighting: ambient (intensity: 0.35)

Suggested effects:
  - color_temperature_shift
  - exposure_ramp
  - gradient_wipe
  - color_match
```

### Example 2: Similar Shots

```bash
alice transitions colorpair forest1.jpg forest2.jpg
```

Output:
```
Color Flow Analysis:
  Compatibility score: 87%
  Transition type: linear
  Duration: 30 frames

High compatibility - natural transition recommended
Suggested effects:
  - gradient_wipe
  - color_match
```

## Troubleshooting

### Low Compatibility Scores
- Check if shots are in correct order
- Consider intermediate shots for smoother flow
- Use generated LUTs for color matching

### Export Issues
- Ensure output directory exists
- Check write permissions
- Verify editor format is supported

### Performance
- Large images may take longer to analyze
- Consider resizing to 2K for faster processing
- Results are cached to avoid reanalysis