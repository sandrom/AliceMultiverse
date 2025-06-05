# Style Similarity Clusters Guide

Discover and organize images by visual style using AI-powered style analysis.

## Overview

AliceMultiverse extracts "Visual DNA" from images:
- **Color Palettes**: Dominant colors, temperature, harmony
- **Composition**: Balance, complexity, focal points
- **Lighting**: Mood, direction, contrast, time of day
- **Texture**: Smoothness, grain, detail density
- **Style Fingerprints**: Numerical representation for similarity

## Quick Start

### Analyze Visual Style

```
You: Analyze the visual style of these images
- /inbox/sunset_portrait.jpg
- /inbox/neon_city.png
- /inbox/minimal_abstract.jpg

Alice: Extracting visual style fingerprints...

✓ sunset_portrait.jpg:
  Color: Warm tones, vibrant, bright
  - Dominant: rgb(255, 178, 102) [orange]
  - Temperature: warm
  - Harmony: analogous
  
  Composition: Medium complexity, rule of thirds (0.78)
  - Balance: centered
  - Negative space: 35%
  
  Lighting: Natural, golden hour
  - Mood: soft
  - Contrast: medium
  - Time: golden_hour
  
  Style tags: warm_tones, vibrant_colors, golden_hour, 
             medium_composition, soft_lighting

✓ neon_city.png:
  Color: Cool tones, vibrant, dark
  - Dominant: rgb(0, 255, 255) [cyan]
  - Temperature: cool
  
  Lighting: Artificial, dramatic
  - Mood: dramatic
  - Contrast: high
```

## Finding Similar Styles

### "More Like This" Search

```
You: Find images with similar style to my favorite cyberpunk shot

Alice: Searching for visually similar images...

Found 8 similar images:

1. cyber_alley.png (92% match)
   - Same: cool tones, high contrast, neon lighting
   - Similar: urban night scene, dramatic mood
   
2. tech_noir.jpg (87% match)
   - Same: color temperature, lighting mood
   - Different: slightly less contrast
   
3. blade_runner_inspired.png (85% match)
   - Same: compositional complexity, color harmony
   - Similar: artificial lighting, dark overall
```

### Style-Based Clustering

```
You: Group my recent downloads by visual style

Alice: Analyzing 150 images and clustering by style...

Found 6 distinct style clusters:

Cluster 1: "Warm Dramatic" (23 images)
- Common elements: warm colors, high contrast, dramatic lighting
- Coherence: 0.89 (very cohesive)
- Centroid: sunset_dramatic_01.jpg

Cluster 2: "Cool Minimalist" (18 images)
- Common elements: cool tones, simple composition, soft lighting
- Coherence: 0.92 (excellent match)
- Centroid: minimal_blue_05.png

Cluster 3: "Vibrant Complex" (15 images)
- Common elements: vibrant colors, complex composition, mixed lighting
- Coherence: 0.76 (good match)
```

## Style Transfer Hints

### Extract Reusable Prompts

```
You: Extract style prompts from this cohesive set

Alice: Analyzing style elements for prompt extraction...

Style Transfer Hints:

From sunset_portrait_collection:
- Prompt fragments: "warm color palette", "golden hour", 
                   "soft lighting", "medium contrast"
- Color palette: rgb(255, 178, 102), rgb(255, 204, 153), rgb(255, 153, 102)
- Technical: 16:9 aspect ratio, medium complexity

Combined prompt suggestion:
"warm color palette, golden hour lighting, soft natural light, 
 medium contrast, analogous color harmony"

Success rate: 85% (based on cluster coherence)
```

### Identify Working Combinations

```
You: What styles work well together?

Alice: Analyzing style combinations...

Successful pairings:
1. Warm + Dramatic lighting (found in 15 images)
2. Minimal composition + Cool tones (found in 12 images)
3. High contrast + Monochrome (found in 10 images)

Conflicting combinations:
- Soft lighting + High contrast (rarely successful)
- Complex composition + Minimal negative space (contradictory)
```

## Auto-Collections

### Build Style-Based Collections

```
You: Create automatic collections based on visual style

Alice: Building style collections...

Created 8 collections:

1. "Warm Tones" (45 images)
   - All images with warm color temperature
   - Compatibility: 0.82
   
2. "Dramatic Lighting" (32 images)
   - High contrast, dramatic mood
   - Compatibility: 0.88
   
3. "Golden Hour" (28 images)
   - Specific time-of-day lighting
   - Compatibility: 0.94
   
4. "Minimalist" (25 images)
   - High negative space ratio (>60%)
   - Compatibility: 0.91
   
5. "Cool Minimalist" (15 images)
   - Intersection of cool tones + minimal
   - Compatibility: 0.95 (highest!)
```

## Style Compatibility

### Check Set Coherence

```
You: Check if these images work together for my portfolio

Alice: Analyzing style compatibility...

Overall compatibility: 0.73 (Good)

Best pairs:
1. image1.jpg ↔ image3.jpg (0.91 compatibility)
2. image2.png ↔ image5.png (0.88 compatibility)

Style outliers:
- image4.jpg would improve set coherence by 15% if removed
  (Different lighting mood disrupts flow)

Recommendation: This set works well together. Consider removing 
the outlier or grouping into two sub-collections.
```

## Visual DNA Details

### Color Analysis
```
Color Palette:
- Dominant colors (top 5 extracted)
- Color temperature (warm/cool/neutral)
- Saturation level (vibrant/muted/monochrome)
- Brightness (bright/medium/dark)
- Harmony type (complementary/analogous/triadic)
```

### Composition Analysis
```
Composition:
- Rule of thirds adherence (0-1 score)
- Symmetry score (0-1)
- Balance (centered/left-heavy/right-heavy)
- Focal points (detected key areas)
- Complexity (simple/medium/complex)
- Negative space ratio (0-1)
```

### Lighting Analysis
```
Lighting:
- Direction (frontal/side/back/ambient)
- Contrast level (low/medium/high)
- Shadow quality (soft/hard/minimal)
- Highlights (blown/balanced/subdued)
- Mood (dramatic/soft/harsh/natural)
- Time of day (golden_hour/blue_hour/midday/night)
```

### Texture Analysis
```
Texture:
- Overall texture (smooth/medium/rough)
- Texture variance (numerical)
- Patterns detected (stripes/repetitive/etc)
- Grain level (none/fine/coarse)
- Detail density (sparse/medium/dense)
```

## Advanced Usage

### Progressive Style Analysis

```
You: Analyze my project evolution over time

Alice: Tracking style changes across project timeline...

Week 1: Experimental phase
- High style variance (0.45 coherence)
- Mixed color temperatures
- Varying composition styles

Week 2: Style convergence
- Warming trend in colors
- Settling on dramatic lighting
- Coherence improved to 0.68

Week 3: Established style
- Consistent warm dramatic theme
- High coherence (0.84)
- Clear visual identity emerged

Recommendation: Your style stabilized around warm, dramatic 
lighting with medium complexity compositions.
```

### Style-Based Curation

```
You: Help me select images for different contexts

Alice: Creating context-appropriate selections...

For Portfolio (need coherence):
- Selected 20 images from "Warm Dramatic" cluster
- Compatibility: 0.89
- Consistent professional style

For Social Media (need variety):
- Selected 2-3 from each cluster
- Maintains interest while showing range
- Each post visually distinct

For Print Series (need harmony):
- Selected 12 from "Cool Minimalist"
- Compatibility: 0.94
- Perfect for cohesive exhibition
```

## Integration with Other Features

### With Tag Hierarchies
```
Style + Tags = Powerful organization
- "warm_tones" + "portrait" → Golden hour portraits
- "high_contrast" + "urban" → Dramatic cityscapes
```

### With Quick Selection
```
You: Mark favorites from "Dramatic Lighting" collection

Alice: Showing 32 images with dramatic lighting...
[Visual browser with style-grouped images]

Quick mark your selections for further curation.
```

### With Batch Analysis
```
Optimize costs by:
1. Analyzing style (local, fast)
2. Finding clusters
3. Analyzing one per cluster with AI
4. Applying insights to all similar
```

## Best Practices

1. **Build Style Library**: Let the system learn your preferences
2. **Regular Clustering**: Re-cluster as collection grows
3. **Use Outlier Detection**: Find images that don't fit
4. **Export Successful Prompts**: Save what works
5. **Track Style Evolution**: See how your style develops

## Tips & Tricks

- **Quick Style Check**: Analyze just 10-20 images to understand a batch
- **Color-First Grouping**: Start with color temperature for fast organization  
- **Lighting Moods**: Group by lighting for consistent atmosphere
- **Compatibility Threshold**: 0.7+ for portfolios, 0.5+ for collections
- **Style Fingerprint Cache**: Reuse analysis for faster operations

Style similarity clustering helps you understand and organize your visual content at a deeper level than tags alone, creating collections that truly "feel" right together.