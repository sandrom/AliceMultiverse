# Subject Morphing Guide

Subject morphing enables smooth transitions between similar subjects across shots, creating professional-looking morphing effects that can be exported to After Effects.

## Overview

The subject morphing feature:
- Detects subjects in images using AI analysis
- Finds matching subjects between consecutive shots
- Generates smooth morphing keyframes
- Exports After Effects-compatible data

## Usage

### Basic Morphing Analysis

Analyze a sequence of images for morphing opportunities:

```bash
alice transitions morph image1.jpg image2.jpg image3.jpg -o morph_data/
```

This will:
1. Detect subjects in each image
2. Find matching subjects between consecutive images
3. Generate morph keyframes
4. Export After Effects data and scripts

### Options

- `--duration/-d`: Set morph duration in seconds (default: 1.2s)
- `--fps`: Frames per second for export (default: 30)
- `--min-similarity`: Minimum similarity threshold (default: 0.6)
- `--verbose/-v`: Show detailed analysis

### Subject Detection

Check what subjects are detected in a single image:

```bash
alice transitions subjects portrait.jpg
```

Output example:
```
Detected 2 subjects:

1. person
   Confidence: 95%
   Position: (0.50, 0.50)
   Area: 24.00% of image

2. face
   Confidence: 98%
   Position: (0.50, 0.40)
   Area: 9.00% of image
```

## Morphing Types

The system supports different morphing curves:

- **smooth**: Standard ease-in-out curve (default)
- **linear**: Constant speed morphing
- **elastic**: Bouncy, organic movement
- **bounce**: Playful bounce effect

## Subject Matching

Subjects are matched based on:

1. **Label similarity**: Same or related labels (e.g., "person" matches "face")
2. **Spatial proximity**: Similar positions in frame
3. **Size similarity**: Comparable subject sizes

### Related Subject Groups

The system recognizes these related labels:
- People: person, people, man, woman, child, face, portrait
- Cats: cat, kitten, feline
- Dogs: dog, puppy, canine
- Vehicles: car, vehicle, automobile
- Nature: tree, forest, woods, flower, plant

## After Effects Integration

### Generated Files

For each morph transition, the system creates:

1. **JSON data file** (`morph_01.json`): Contains all keyframe data
2. **JSX script** (`morph_01.jsx`): Import script for After Effects
3. **Summary file** (`morph_summary.json`): Overview of all transitions

### Import Process

1. Open your After Effects composition
2. Go to File → Scripts → Run Script File...
3. Select the `.jsx` file for the transition you want
4. The script will:
   - Create a control null object
   - Add morph layers for each subject pair
   - Set up all keyframes automatically

### Manual Integration

If you prefer manual control, the JSON files contain:

```json
{
  "version": "1.0",
  "project": {
    "fps": 30,
    "duration": 1.2,
    "source_layer": "image1.jpg",
    "target_layer": "image2.jpg"
  },
  "morph_data": [{
    "name": "Morph_person_0",
    "source_anchor": [960, 540],
    "target_anchor": [1008, 550],
    "keyframes": [...]
  }]
}
```

## Example Workflow

### Portrait Sequence Morphing

```bash
# 1. Analyze portrait sequence
alice transitions morph \
  portraits/shot1.jpg \
  portraits/shot2.jpg \
  portraits/shot3.jpg \
  -o portraits_morph/ \
  --duration 1.5

# 2. Review detected subjects
alice transitions subjects portraits/shot1.jpg -v

# 3. Import in After Effects
# Open AE, run portraits_morph/morph_01.jsx
```

### Multi-Subject Scene

```bash
# Analyze scene with multiple subjects
alice transitions morph \
  scene/wide.jpg \
  scene/medium.jpg \
  scene/close.jpg \
  -o scene_morph/ \
  --min-similarity 0.5  # Lower threshold for complex scenes
```

## Advanced Usage

### Integrated Transition Analysis

Use morphing with full transition analysis:

```python
from alicemultiverse.transitions import TransitionMatcher

# Create matcher
matcher = TransitionMatcher()

# Analyze with morphing (async)
suggestions = await matcher.analyze_sequence_with_morphing(image_paths)

# Each suggestion now includes morphing data if applicable
for s in suggestions:
    if s.transition_type == TransitionType.MORPH:
        print(f"Morphing {s.effects['subject_count']} subjects")
```

### Custom Morphing

```python
from alicemultiverse.transitions.morphing import SubjectMorpher

morpher = SubjectMorpher()

# Detect subjects
subjects1 = await morpher.detect_subjects("image1.jpg")
subjects2 = await morpher.detect_subjects("image2.jpg")

# Find matches
matches = morpher.find_similar_subjects(subjects1, subjects2)

# Generate custom keyframes
keyframes = morpher.generate_morph_keyframes(
    matches,
    duration=2.0,
    morph_type="elastic",
    keyframe_count=20  # More keyframes for smoother motion
)
```

## Tips for Best Results

1. **Similar Framing**: Subjects should be similarly framed for smooth morphs
2. **Consistent Lighting**: Major lighting changes can disrupt the morph effect
3. **Clear Subjects**: Well-defined subjects morph better than ambiguous ones
4. **Sequential Shots**: Plan your shots with morphing in mind

## Troubleshooting

### No Subjects Detected

- Ensure images have clear, recognizable subjects
- Check that AI providers are configured correctly
- Try running with `--verbose` for detailed logs

### Poor Match Quality

- Lower the `--min-similarity` threshold
- Ensure subjects are in similar positions
- Check that subject labels are related

### After Effects Import Issues

- Verify After Effects is running the correct version
- Check that source images are in the AE project
- Review the JSX console for error messages

## Performance Considerations

- Subject detection uses AI providers (costs apply)
- Results are cached to avoid re-analysis
- Batch processing is more efficient than individual images
- Export is lightweight and fast

## Integration with Workflows

Subject morphing works seamlessly with other Alice features:

```bash
# Combine with scene detection
alice scene detect video.mp4 --export-frames
alice transitions morph output/frames/*.jpg -o morph/

# Use with organized media
alice transitions morph organized/2024-01-15/project/*.jpg -o project_morph/
```