# Video Creation Workflow Guide

This guide shows how to turn your selected images into engaging videos using Alice's video creation workflow.

## Overview

The video creation workflow helps you:
1. **Analyze** images for video generation potential
2. **Generate** storyboards with shot descriptions and transitions
3. **Create** Kling-ready prompts with camera movements
4. **Prepare** enhanced keyframes using Flux Kontext
5. **Export** guides for video editing

## Complete Workflow Example

### 1. Starting with Selected Images

After selecting images for your video (see selection-workflow-guide.md):

```
Me: I've selected 20 cyberpunk images. Let's create a video storyboard.

Claude: I'll help you create a video storyboard from your selected cyberpunk images. Let me first analyze a few to understand their video potential.

[Claude uses analyze_for_video tool]

Analysis of first image shows:
- Suggested camera motion: zoom_in (character focus detected)
- Motion keywords: ["neon", "rain", "reflection"]
- Composition: Has character, deep perspective
- Video potential: High - dynamic elements present

Would you like a cinematic or music video style?
```

### 2. Generating the Storyboard

```
Me: Let's go with cinematic style, about 45 seconds total.

Claude: I'll create a cinematic storyboard for your 45-second video.

[Claude uses generate_video_storyboard tool]

Created storyboard: "cinematic_video_20250106_143022"
- Total duration: 45 seconds
- 20 shots @ 2-3 seconds each
- Style: Cinematic with dramatic camera movements

Shot highlights:
- Shot 1: Wide establishing shot, track forward (3s)
- Shot 5: Character close-up, slow zoom in (2s)
- Shot 12: Action sequence, orbit left (3s)
- Shot 20: Final shot, zoom out with fade (3s)

Saved to: storyboards/cinematic_video_20250106_143022.json

Next steps: Generate Kling prompts or prepare Flux keyframes?
```

### 3. Creating Kling Prompts

```
Me: Generate the Kling prompts. Use the professional model.

Claude: I'll create Kling prompts optimized for the professional model.

[Claude uses create_kling_prompts tool]

Generated 20 Kling prompts for model: kling-v2.1-pro-text

Sample prompts:
Shot 1: "Cinematic shot: cyberpunk cityscape, neon rain, wide composition, camera track forward, dramatic angle"
Shot 5: "Cinematic shot: character portrait, neon lighting, camera zoom in, film grain"

Estimated cost: $7.00 (20 shots × $0.35)

Output formats available:
- List view (current)
- Script format for production
- Detailed with all parameters

The prompts emphasize movement and atmosphere for video generation.
```

### 4. Enhancing with Flux Kontext

```
Me: I want to modify shots 5 and 12 - make them more dramatic. 
    Also create transition frames between major scenes.

Claude: I'll prepare enhanced keyframes with your modifications.

[Claude uses prepare_flux_keyframes tool]

Prepared Flux keyframes:
- Shot 5: Base + modified version "Add dramatic rain and lightning"
- Shot 12: Base + modified version "Intensify neon glow and add motion blur"
- 4 transition frames for smooth morphing between scenes

Total keyframes: 8
Estimated Flux cost: $0.56

These keyframes will provide better control over the final video generation.
```

### 5. Creating Editing Guide

```
Me: Create a transition guide for video editing.

Claude: I'll create a comprehensive editing guide for your video.

[Claude uses create_transition_guide tool]

# Transition Guide for cinematic_video_20250106_143022
Total Duration: 45 seconds
Number of Shots: 20

## Shot List with Transitions:

### Shot 1
- Duration: 3s
- Camera: track_forward
- Transition In: fade
- Transition Out: cut
- Prompt: Cinematic shot: cyberpunk cityscape...

### Shot 5 (Enhanced)
- Duration: 2s
- Camera: zoom_in
- Transition In: cut
- Transition Out: dissolve
- Note: Use Flux-enhanced version with rain effects

[Full guide continues...]

## Editing Notes:
- Use 0.5s overlap for dissolve transitions
- Match motion blur transitions with camera movement
- Sync cuts to music beats if applicable
- Shot 5 & 12 have enhanced versions available
```

## Advanced Techniques

### Style-Specific Workflows

Different styles optimize for different outcomes:

```
# Documentary style - steady, observational
storyboard = generate_video_storyboard(
    image_hashes=selections,
    style="documentary",
    target_duration=60
)

# Music video - dynamic, rhythmic
storyboard = generate_video_storyboard(
    image_hashes=selections,
    style="music_video",
    target_duration=30
)

# Abstract - experimental, artistic
storyboard = generate_video_storyboard(
    image_hashes=selections,
    style="abstract",
    target_duration=40
)
```

### Camera Motion Analysis

Understanding suggested camera motions:

```
Me: Analyze these three images for their video potential.

Claude: [Analyzes each image]

Image 1 - Landscape vista:
- Suggested: track_forward (explore the depth)
- Alternative: pan_right (survey the scene)

Image 2 - Character portrait:
- Suggested: zoom_in (intimate focus)
- Alternative: orbit_left (reveal character)

Image 3 - Abstract pattern:
- Suggested: auto (let AI decide)
- Alternative: static (appreciate details)
```

### Multi-Model Workflow

Combining Kling and Flux for best results:

```
1. Generate base videos with Kling standard mode
2. Identify shots needing enhancement
3. Create Flux keyframes for those shots
4. Regenerate specific shots with Kling Pro
5. Assemble in video editor following transition guide
```

### Batch Processing

For large projects:

```
Me: I have 100 selected images. Create multiple 30-second videos.

Claude: I'll create multiple storyboards for manageable video segments.

Creating 4 storyboards:
1. "cinematic_video_batch_1" (25 images, 30s)
2. "cinematic_video_batch_2" (25 images, 30s)
3. "cinematic_video_batch_3" (25 images, 30s)
4. "cinematic_video_batch_4" (25 images, 30s)

This approach allows parallel processing and easier editing.
```

## Video Styles Explained

### Cinematic
- **Characteristics**: Dramatic angles, deliberate movements, film-like
- **Best for**: Storytelling, showcases, portfolios
- **Camera bias**: Track forward, orbit, zoom in
- **Duration**: 5 seconds per shot

### Documentary
- **Characteristics**: Natural, observational, steady
- **Best for**: Behind-the-scenes, process videos, educational
- **Camera bias**: Pan, static, subtle movements
- **Duration**: 4 seconds per shot

### Music Video
- **Characteristics**: Dynamic, rhythmic, high energy
- **Best for**: Promotional content, social media, entertainment
- **Camera bias**: Quick zooms, orbits, varied movements
- **Duration**: 3 seconds per shot

### Narrative
- **Characteristics**: Story-driven, emotional, purposeful
- **Best for**: Short films, advertisements, brand stories
- **Camera bias**: Character-focused movements
- **Duration**: 5 seconds per shot

### Abstract
- **Characteristics**: Experimental, artistic, unconventional
- **Best for**: Art projects, mood pieces, backgrounds
- **Camera bias**: Auto, unexpected movements
- **Duration**: 4 seconds per shot

## Flux Kontext Strategies

### When to Use Flux Enhancement

1. **Transitions**: Create smooth morphs between different scenes
2. **Consistency**: Maintain character/style across shots
3. **Effects**: Add weather, lighting, or atmospheric changes
4. **Corrections**: Fix issues in selected images before video

### Flux Modification Examples

```
Common modifications for video:
- "Add rain and reflections for continuity"
- "Match lighting to previous shot"
- "Add motion blur suggesting movement"
- "Blend this character into new environment"
- "Create intermediate frame between these scenes"
```

## Cost Optimization

### Budget-Conscious Workflow

```
1. Preview with standard Kling ($0.28/shot)
2. Identify hero shots only
3. Upgrade heroes to Pro ($0.35/shot)
4. Use Flux only for critical transitions ($0.07/image)

Example 20-shot video:
- 15 standard shots: $4.20
- 5 pro shots: $1.75
- 3 Flux transitions: $0.21
- Total: $6.16 (vs $7.00 all-pro)
```

### Quality vs Cost Trade-offs

- **Draft Mode**: All standard, no Flux ($5.60 for 20 shots)
- **Balanced Mode**: Mix of standard/pro + key Flux ($6-7)
- **Premium Mode**: All pro + extensive Flux ($8-10)

## Troubleshooting

### Common Issues

**Issue**: Camera motions don't match content
- Solution: Override in create_kling_prompts with custom motions

**Issue**: Transitions too abrupt
- Solution: Use prepare_flux_keyframes for smooth morphs

**Issue**: Inconsistent style across video
- Solution: Add style keywords to all prompts consistently

**Issue**: Generated videos too fast/slow
- Solution: Adjust shot durations in storyboard

## Integration with Editor

### Export for Premiere/DaVinci/Final Cut

The transition guide includes:
- Frame-accurate timing
- Transition types and durations  
- Notes for color grading
- Music sync points
- Effect suggestions

### Assembly Workflow

1. Import all generated videos
2. Follow transition guide for timing
3. Apply specified transitions
4. Add music/sound design
5. Color grade for consistency
6. Export final video

## Next Steps

After creating your video:

1. **Archive Project**: Save storyboard and assets together
2. **Document Learnings**: Note successful prompts/settings
3. **Create Templates**: Save effective prompt patterns
4. **Share Results**: Export for intended platform
5. **Iterate**: Refine based on results

## Example Projects

### "Neon Dreams" - Cyberpunk Showcase
- 30 selected images → 60-second video
- Cinematic style with pro model
- 5 Flux-enhanced transitions
- Total cost: $12.50
- Result: Cohesive narrative with smooth flow

### "Process Evolution" - Art Documentation  
- 50 progress images → 90-second documentary
- Standard model with strategic pro shots
- Minimal Flux usage
- Total cost: $8.75
- Result: Clear progression with steady pacing

### "Energy Burst" - Music Video
- 40 action images → 45-second music video
- Mixed models based on shot importance
- Heavy Flux usage for effects
- Total cost: $15.00
- Result: High-energy synchronized to beat