# Video Creation Workflow Example

This example shows how to create a video from selected images using Claude Desktop.

## Prerequisites

1. You've already selected images using the selection workflow
2. You have image hashes from your selections
3. Alice MCP server is running

## Step-by-Step Example

### 1. Analyze Images for Video Potential

```
Claude, analyze these images for video potential:
- abc123def456...
- 789ghi012jkl...
- mno345pqr678...
```

Claude will use the `analyze_for_video` tool to examine each image and suggest:
- Camera movements based on composition
- Motion keywords found in the image
- Video generation hints

### 2. Create a Storyboard

```
Create a cinematic video storyboard from these 10 selected images 
for a 30-second video.
```

Claude will:
- Generate a complete storyboard with shots and transitions
- Save it as a JSON file in the storyboards/ directory
- Show you a summary of the shots

### 3. Generate Kling Prompts

```
Create Kling prompts from the storyboard using the professional model.
Show me in script format.
```

Claude will format the prompts specifically for Kling, including:
- Optimized prompt text
- Camera motion parameters
- Duration settings
- Cost estimates

### 4. Enhance Key Shots with Flux

```
I want to enhance shots 3 and 7. For shot 3, add dramatic lighting.
For shot 7, create a smooth transition to shot 8.
```

Claude will prepare Flux Kontext requests to:
- Enhance specific shots with modifications
- Create transition frames between scenes
- Maintain visual consistency

### 5. Export Editing Guide

```
Create a transition guide for video editing.
```

Claude will generate a detailed guide including:
- Shot-by-shot breakdown
- Transition types and timing
- Editing notes and tips
- Music sync suggestions

## Complete Conversation Example

```
User: I've selected 15 cyberpunk images. Let's create a 45-second music video.

Claude: I'll help you create a music video from your cyberpunk selections. 
Let me first analyze a few images to understand their video potential.

[Uses analyze_for_video on first 3 images]

Great! Your images have strong motion potential with neon effects and 
dynamic compositions. Now I'll create a music video storyboard.

[Uses generate_video_storyboard with style="music_video"]

Created storyboard "music_video_20250106_150000" with:
- 15 shots averaging 3 seconds each
- Dynamic camera movements (zooms, orbits)
- High-energy transitions
- Total duration: 45 seconds

Shall I create the Kling prompts for generation?

User: Yes, and also prepare Flux enhancements for the chorus sections 
(shots 6-10).

Claude: [Uses create_kling_prompts and prepare_flux_keyframes]

Perfect! I've prepared:

1. **Kling Prompts** (kling-v2.1-pro-text):
   - 15 video generation prompts
   - Estimated cost: $5.25
   - Emphasizes rhythm and energy

2. **Flux Enhancements** for shots 6-10:
   - Enhanced neon glow effects
   - Smooth morphing transitions
   - Beat-synchronized modifications
   - Additional cost: $0.35

Total estimated cost: $5.60

The files are ready for video generation. Would you like the editing guide?

User: Yes, create the guide and show me the workflow for shots 6-8.

Claude: [Uses create_transition_guide]

Here's the workflow for the chorus section (shots 6-8):

**Shot 6** (3s)
- Base: Generate with Kling using dynamic zoom
- Enhance: Apply Flux "intensify neon pulse" effect
- Transition Out: Motion blur to Shot 7

**Shot 7** (3s) 
- Base: Generate with orbit camera motion
- Enhance: Flux morph frame from Shot 6
- Transition Out: Quick cut on beat

**Shot 8** (3s)
- Base: Generate with track forward
- Enhance: Flux "add light trails" effect
- Transition Out: Dissolve to Shot 9

Sync these cuts to the music beats for maximum impact!
```

## Tips for Best Results

1. **Batch Similar Shots**: Group images with similar styles together
2. **Plan Transitions**: Think about flow between shots before generating
3. **Cost Optimization**: Use standard Kling for drafts, pro for finals
4. **Flux Strategy**: Only enhance hero shots and transitions
5. **Music First**: If you have music, let it guide shot duration

## Advanced Techniques

### Multi-Style Videos
Create sections with different styles:
```
Shots 1-5: documentary style (steady, observational)
Shots 6-10: music video style (dynamic, energetic)  
Shots 11-15: cinematic style (dramatic, composed)
```

### Narrative Arc
Build a story progression:
```
Opening: Wide establishing shots (track forward)
Development: Character focus (zoom in, orbit)
Climax: Action sequences (dynamic movements)
Resolution: Return to wide (zoom out, static)
```

### Cost-Conscious Workflow
```
1. Generate all shots in standard mode first
2. Review and identify hero shots
3. Regenerate only hero shots in pro mode
4. Use Flux only for critical enhancements
```

## Next Steps

After generating your videos:
1. Import into video editor (Premiere, DaVinci, etc.)
2. Follow the transition guide for assembly
3. Add music and sound design
4. Color grade for consistency
5. Export for your target platform