# Intelligent Tag Hierarchies Guide

Smart tag organization with semantic relationships, auto-clustering, and personal taxonomies.

## Overview

AliceMultiverse now understands tag relationships:
- **Hierarchical Organization**: Tags have parent-child relationships
- **Auto-Clustering**: Similar tags group together automatically
- **Semantic Expansion**: Find related content through tag connections
- **Personal Taxonomies**: Create custom organization schemes

## Quick Start

### Basic Hierarchical Analysis

```
You: Analyze these images with tag hierarchies
- /inbox/cyberpunk/neon_city.png
- /inbox/cyberpunk/tech_portrait.png

Alice: Analyzing with intelligent tag hierarchies...

✓ neon_city.png:
  Tags: [cyberpunk, neon, city, night, futuristic]
  Hierarchy:
    cyberpunk → digital_art → art_style
    neon → artificial_light → lighting
    city → cityscape → architecture → subject
  
  Related tags: synthwave, sci-fi, blade_runner
  Coherence score: 0.89 (highly coherent)

✓ tech_portrait.png:
  Tags: [portrait, cyberpunk, tech, face]
  Hierarchy:
    portrait → person → subject
    cyberpunk → digital_art → art_style
  
  Suggested tags: neon, futuristic, digital_art
```

## Tag Hierarchies

### Default Hierarchy Structure

```
art_style/
├── digital_art/
│   ├── cyberpunk
│   ├── vaporwave
│   └── synthwave
├── traditional_art/
│   ├── oil_painting
│   └── watercolor
└── photography/
    ├── portrait
    └── landscape

subject/
├── person/
│   ├── portrait/
│   │   └── face
│   └── full_body
└── nature/
    ├── landscape
    └── seascape

mood/
├── positive_mood/
│   ├── happy
│   └── peaceful
└── negative_mood/
    ├── dark
    └── mysterious
```

### Semantic Relationships

```
You: Show me how "cyberpunk" relates to other tags

Alice: Tag relationships for "cyberpunk":

Parent: digital_art (style category)
Siblings: vaporwave, synthwave, glitch_art

Related tags (by co-occurrence):
- neon (90% correlation)
- futuristic (85%)
- sci-fi (80%)
- night (75%)
- urban (70%)

Common combinations:
- cyberpunk + portrait → tech character art
- cyberpunk + city → blade runner aesthetic
- cyberpunk + neon → classic cyberpunk style
```

## Auto-Clustering

### Cluster Similar Images

```
You: Cluster my latest 50 downloads by similarity

Alice: Analyzing and clustering 50 images...

Found 5 distinct clusters:

Cluster 1: "Portrait Collection" (15 images)
- Common tags: portrait, face, person
- Dominant style: photography
- Coherence: 0.92

Cluster 2: "Cyberpunk Scenes" (12 images)
- Common tags: cyberpunk, neon, city
- Dominant mood: dramatic
- Coherence: 0.88

Cluster 3: "Nature Landscapes" (10 images)
- Common tags: landscape, nature, sunset
- Dominant colors: warm tones
- Coherence: 0.85

Cluster 4: "Abstract Art" (8 images)
- Common tags: abstract, digital_art, geometric
- Mixed styles
- Coherence: 0.72

Cluster 5: "UI Designs" (5 images)
- Common tags: interface, minimal, tech
- Technical category
- Coherence: 0.90
```

### Tag-Based Organization

```
You: Auto-organize based on tag clusters

Alice: Creating smart collections from tag patterns...

Created collections:
1. "Portraits & People" → organized/collections/portraits/
   - 23 images with person/face/portrait tags
   
2. "Sci-Fi Aesthetics" → organized/collections/scifi/
   - 18 images with cyberpunk/futuristic/sci-fi tags
   
3. "Natural Scenes" → organized/collections/nature/
   - 15 images with landscape/nature/outdoor tags

Moved 56 images into thematic collections.
```

## Mood Boards

### Create Thematic Mood Boards

```
You: Create a "Neon Nights" mood board

Alice: Creating mood board "Neon Nights"...

Added to mood board:
- Tags: neon, night, cyberpunk, urban, lights
- Colors: #FF00FF, #00FFFF, #FF1493, #9400D3
- Reference images: 8 selected

Analysis:
- Dominant themes: artificial lighting, urban scenes
- Color palette: Pink/purple/cyan (synthwave colors)
- Coherence score: 0.94
- Suggested additions: rain, reflections, hologram
```

### Analyze Mood Board Coherence

```
You: Analyze my "Retro Future" mood board

Alice: Analyzing mood board coherence...

Tag clusters found:
1. Time period: retro, 80s, vintage, future
2. Style: synthwave, vaporwave, neon
3. Tech: computer, crt, arcade

Coherence analysis:
- Overall coherence: 0.87 (very cohesive)
- Strongest connection: retro ↔ synthwave (0.95)
- Weakest element: "nature" tag (0.42 fit)

Recommendations:
- Remove: nature, realistic (low coherence)
- Add: chrome, grid, sunset (high affinity)
- Similar boards: "Outrun", "Miami Vice"
```

## Project Tag Management

### Project-Specific Tags

```
You: Set up tags for my "Sci-Fi Book Cover" project

Alice: Creating project taxonomy...

Base tags added:
- Genre: sci-fi, futuristic, space
- Style: book_cover, dramatic, epic
- Elements: spaceship, planet, stars

Suggested expansions:
- Color schemes: dark_background, bright_accents
- Moods: mysterious, adventurous, vast
- Technical: high_contrast, centered_composition

Auto-inherited from hierarchy:
- sci-fi → science_fiction → genre
- futuristic → future → time_period
```

### Smart Tag Suggestions

```
You: Suggest more tags based on what's in the project

Alice: Analyzing project patterns...

Based on your current 25 images:
1. You have "spaceship" → suggest "spacecraft", "vessel"
2. You have "planet" → suggest "alien_world", "exoplanet"
3. You have "stars" → suggest "nebula", "galaxy", "cosmos"

From similar projects:
- "space_battle" (used in 3 similar projects)
- "alien_technology" (high correlation with your tags)
- "distant_future" (matches your time period)

Missing important tags:
- No character tags (consider: astronaut, pilot)
- No danger tags (consider: conflict, threat)
```

## Custom Taxonomies

### Create Personal Organization Scheme

```
You: Create my custom "Creative Stages" taxonomy

Alice: Creating custom taxonomy scheme...

Define your hierarchy:
1. Inspiration/
   ├── references/
   ├── mood_boards/
   └── sketches/

2. Development/
   ├── rough_drafts/
   ├── iterations/
   └── experiments/

3. Final/
   ├── approved/
   ├── published/
   └── archived/

This taxonomy can be applied across all projects.
```

### Export/Import Taxonomies

```
You: Export my taxonomy for backup

Alice: Exporting complete taxonomy...

Exported to: ~/.alice/taxonomies/export_2025_06_05.json

Contents:
- 342 tag definitions
- 15 custom hierarchies
- 28 tag clusters
- 12 mood boards
- 5 project schemes

You can import this to another system or share it.
```

## Advanced Features

### Tag Evolution Tracking

```
You: Show me trending tags over time

Alice: Tag trend analysis (last 30 days):

Rising tags:
1. "minimalist" ↑ 45% (appearing more frequently)
2. "pastel" ↑ 38% (new color trend)
3. "geometric" ↑ 32% (style shift)

Declining tags:
1. "vintage" ↓ 28% (less usage)
2. "grunge" ↓ 22% (style change)

Stable core tags:
- portrait, landscape, digital_art (consistent usage)
```

### Co-occurrence Insights

```
You: What tags often appear together?

Alice: Top tag combinations:

1. cyberpunk + neon (92% co-occurrence)
   - Almost always paired
   - Strong stylistic connection

2. portrait + shallow_dof (78%)
   - Technical/subject pairing
   - Professional photography marker

3. sunset + golden_hour (75%)
   - Redundant pairing
   - Consider using just one

4. minimalist + geometric (68%)
   - Style combination
   - Modern aesthetic marker
```

## Best Practices

### 1. Build Hierarchies Gradually
```
Start broad:
- art_style, subject, mood

Then specialize:
- art_style → digital_art → your_specific_styles
```

### 2. Use Consistent Naming
```
Good: portrait, portrait_photography, portrait_painting
Bad: portrait, photo_portrait, painted-face
```

### 3. Leverage Auto-Suggestions
```
You: I tagged with "sunset"

Alice: Related suggestions:
- Parent: golden_hour (captures time)
- Siblings: sunrise, dusk
- Technical: warm_colors, backlighting
```

### 4. Regular Clustering
```
You: Cluster recent additions weekly

Alice: Weekly clustering helps:
- Discover emerging themes
- Maintain organization
- Spot duplicates
- Refine taxonomies
```

### 5. Project-Based Evolution
```
Each project refines your taxonomy:
- New tags get categorized
- Relationships strengthen
- Personal style emerges
```

## Integration Examples

### With Quick Selection
```
You: Mark favorites from the "Portrait" cluster

Alice: Showing Portrait cluster (15 images)...
[Shows images with portrait tags]

You select 5 favorites.

Added to:
- Quick marks: favorite
- Auto-collection: "Best Portraits"
- Mood board: "Portrait Inspiration"
```

### With Batch Analysis
```
You: Analyze and auto-tag by hierarchy

Alice: Batch hierarchical analysis:
1. Analyze with providers
2. Normalize tags
3. Expand with hierarchy
4. Group by clusters
5. Suggest organization

Result: 100 images → 12 coherent groups
Cost saved: 30% through clustering
```

### With Local Models
```
You: Use local models for basic tags, cloud for style

Alice: Hybrid hierarchical approach:
1. Ollama: Extract objects, scenes (free)
2. Add to hierarchy: person → portrait
3. Cloud: Analyze artistic style
4. Combine: Complete hierarchical tags

Efficient and comprehensive tagging.
```

## Tips & Tricks

1. **Start Simple**: Use default hierarchies, customize later
2. **Watch Patterns**: Let co-occurrence guide relationships  
3. **Prune Regularly**: Remove unused tags and clusters
4. **Share Schemes**: Export taxonomies for team consistency
5. **Trust Coherence**: High scores = good organization

The intelligent tag system learns from your usage, becoming more personalized and effective over time.