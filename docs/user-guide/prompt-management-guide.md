# Prompt Management Guide

AliceMultiverse includes a comprehensive prompt management system that helps you track, organize, and optimize your AI prompts across different providers and projects.

## Overview

The prompt management system provides:

- **Centralized Database**: Fast searchable index using DuckDB
- **Project Storage**: Human-readable YAML files in project directories  
- **Usage Tracking**: Automatic tracking of prompt performance
- **Effectiveness Analytics**: Success rates, costs, and ratings
- **Multi-Provider Support**: Works with all supported AI providers

## Using Through AI Assistants (Claude/ChatGPT)

The prompt management system is fully integrated with AI assistants through MCP. Here are example conversations:

### Finding Effective Prompts

```text
User: Find me effective prompts for cyberpunk cityscapes

Assistant: I'll search for effective cyberpunk cityscape prompts.

[Finds 8 prompts with 85%+ success rate]

Top performers:
1. "Cyberpunk megacity at night, neon-lit skyscrapers, flying vehicles, rain-slicked streets"
   - Success rate: 92.3% (12 uses)
   - Best with: Midjourney, Flux
   - Style: cyberpunk, neon-noir

2. "Futuristic Tokyo street scene, holographic advertisements, crowded with cyborgs"
   - Success rate: 88.9% (9 uses) 
   - Best with: Stable Diffusion
   - Style: anime-cyberpunk

Recommendation: Based on 8 effective prompts, Midjourney works best for this style with 91.2% average success.
```

### Creating and Tracking Prompts

```text
User: Create a prompt for dramatic fantasy landscapes with Flux and Leonardo

Assistant: I'll create a fantasy landscape prompt for you.

[Created prompt: 7a8b9c10...]

Prompt: "Epic fantasy landscape with towering mountains, ancient ruins, dramatic storm clouds"
- Category: image_generation
- Providers: flux, leonardo
- Project: None (add with --project if needed)
- Tags: [fantasy, landscape, dramatic, mountains, ruins]

Saved successfully! Track usage with: prompt_track_usage 7a8b9c10 <provider> <success>
```

### Tracking Results

```text
User: That fantasy prompt worked great with Flux! Cost was $0.08

Assistant: I'll track this successful usage.

[Tracked usage for prompt 7a8b9c10]

Updated stats:
- Total uses: 1
- Success rate: 100.0%
- Total successes: 1

The prompt is performing well!
```

### Getting Project Insights

```text
User: Show me prompts for my SciFiProject

Assistant: I'll get all prompts and insights for SciFiProject.

[Found 24 prompts]

Project: SciFiProject
Statistics:
- Total prompts: 24
- Total uses: 187
- Success rate: 84.5%
- Total cost: $15.73
- Most used provider: midjourney (102 uses)
- Top category: image_generation (20 prompts)

Top prompts:
1. "Alien megastructure orbiting binary star system" - 95.8% success (24 uses)
2. "Quantum computer core with holographic interface" - 91.7% success (12 uses)
3. "Terraformed Mars colony at sunset" - 88.2% success (17 uses)
```

## Getting Started

### Initialize Prompt Storage in a Project

```bash
# Initialize with YAML format (recommended)
alice prompts init ~/Projects/MyProject

# Initialize with JSON format
alice prompts init ~/Projects/MyProject --format json
```

This creates:
```
MyProject/
└── .alice/prompts/
    ├── README.md          # Quick reference guide
    ├── prompts.yaml       # Main prompt collection
    ├── templates/         # Example templates
    │   └── example.yaml
    └── exports/          # For exported collections
```

### Adding Prompts

#### Via CLI

```bash
# Basic prompt
alice prompts add -t "A serene Japanese garden at sunset" \
  -c image_generation -p midjourney flux

# With full metadata
alice prompts add \
  -t "Cyberpunk cityscape with neon lights and flying cars" \
  -c image_generation \
  -p midjourney stable_diffusion flux \
  --tags cyberpunk futuristic neon \
  --project "FutureCities" \
  --style cyberpunk \
  -d "Creates dramatic futuristic cityscapes" \
  -n "Works best with --ar 16:9 and high quality settings"
```

#### Via YAML Files

Create a file in your project's `.alice/prompts/` directory:

```yaml
# cyberpunk_city.yaml
prompt: "Cyberpunk cityscape with neon lights and flying cars, rain-slicked streets"

category: image_generation

providers:
  - midjourney
  - flux
  - stable_diffusion

description: "Creates atmospheric cyberpunk cityscapes"

tags:
  - cyberpunk
  - cityscape
  - neon
  - futuristic

style: cyberpunk

project: FutureCities

context:
  aspect_ratio: "16:9"
  quality: "high"
  model_version: "v6"

notes: |
  Best results with:
  - Midjourney: --ar 16:9 --q 2 --v 6
  - Flux: steps=50, guidance=7.5
  - Add "raining" for more atmosphere
  - Try "from above" for aerial view
```

## Searching and Finding Prompts

### Basic Search

```bash
# Search by text
alice prompts search -q "cyberpunk"

# Search by category
alice prompts search -c image_generation

# Search by provider
alice prompts search -p midjourney

# Search by project
alice prompts search --project FutureCities

# Combine filters
alice prompts search -q "city" -c image_generation -p flux --style cyberpunk
```

### Finding Effective Prompts

```bash
# Show most effective prompts
alice prompts effective

# Filter by category and provider
alice prompts effective -c image_generation -p midjourney

# Adjust thresholds
alice prompts effective --min-success-rate 0.9 --min-uses 10
```

## Tracking Usage

### Record Usage Manually

```bash
# Successful generation
alice prompts use abc123 -p midjourney --success \
  --cost 0.10 --duration 15 \
  -n "Great result with v6"

# Failed generation  
alice prompts use abc123 -p flux --failure \
  -n "Model struggled with the concept"
```

### Automatic Tracking

When using AliceMultiverse providers, prompts are automatically tracked:

```python
from alicemultiverse.providers import MidjourneyProvider

provider = MidjourneyProvider(api_key="...")
result = await provider.generate(
    "A serene mountain landscape",
    project="NatureScenes"  # Automatically tracked
)
```

## Project Management

### Working with Project Prompts

```bash
# View project prompts
alice prompts project ~/Projects/MyProject

# Sync from project to central index
alice prompts project ~/Projects/MyProject --sync-to-index

# Pull prompts from index to project
alice prompts project ~/Projects/MyProject --sync-from-index
```

### Discovering Prompts Across Projects

```bash
# Discover all project prompts
alice prompts discover

# Discover and sync all
alice prompts discover --sync-all

# Specify base paths
alice prompts discover --base-paths ~/Projects ~/AI/Projects
```

## Analytics and Insights

### View Prompt Details

```bash
# Show full prompt information
alice prompts show abc123

# Supports partial ID matching
alice prompts show abc
```

### Export Prompts

```bash
# Export all prompts
alice prompts export all-prompts.json

# Export by category
alice prompts export image-prompts.json -c image_generation

# Export search results
alice prompts search --project MyProject --export project-prompts.json
```

### Update Ratings and Tags

```bash
# Rate effectiveness
alice prompts update abc123 -r 8.5

# Add tags
alice prompts update abc123 --add-tag experimental atmospheric

# Remove tags
alice prompts update abc123 --remove-tag test

# Update description
alice prompts update abc123 -d "Creates stunning atmospheric scenes"
```

## YAML Format Reference

### Single Prompt Format

```yaml
prompt: "Your detailed prompt text here"

category: image_generation  # Required

providers:  # At least one required
  - midjourney
  - flux

# Optional fields
description: "What this prompt creates"

tags:
  - style_tag
  - content_tag
  - mood_tag

style: artistic_style  # e.g., photorealistic, anime, abstract

project: ProjectName

context:
  aspect_ratio: "16:9"
  steps: 50
  guidance_scale: 7.5
  negative_prompt: "blurry, low quality"

effectiveness:
  rating: 8.5      # 0-10 scale
  uses: 24
  successes: 22
  success_rate: "91.7%"

notes: |
  Multi-line notes with usage tips,
  best practices, and variations to try.

metadata:
  id: "unique-id-here"
  created: "2024-01-15T10:30:00"
  updated: "2024-01-20T14:45:00"
  keywords:  # For enhanced search
    - additional
    - search
    - terms
```

### Collection Format

```yaml
title: "Project Prompt Collection"
generated_at: "2024-01-20T15:00:00"
total_prompts: 42

prompts_by_category:
  image_generation:
    - prompt: "First prompt..."
      category: image_generation
      # ... rest of fields
      
    - prompt: "Second prompt..."
      category: image_generation
      # ... rest of fields
      
  video_generation:
    - prompt: "Video prompt..."
      category: video_generation
      # ... rest of fields
```

## Best Practices

### Organizing Prompts

1. **Use Descriptive Tags**: Include style, mood, content, and technical tags
2. **Document Context**: Record settings that work well
3. **Track Variations**: Link related prompts with parent_id
4. **Project Association**: Always specify the project for better organization

### Effective Prompts

1. **Be Specific**: Include details about style, lighting, composition
2. **Note What Works**: Document successful parameters in notes
3. **Rate Honestly**: Use the rating system to track what actually works
4. **Share Context**: Include aspect ratios, quality settings, model versions

### Version Control

YAML files in `.alice/prompts/` are perfect for git:

```bash
# Track prompt changes
git add .alice/prompts/
git commit -m "Add cyberpunk city prompts"

# Share with team
git push
```

## Integration with Providers

### Automatic Tracking

Prompts are automatically tracked when using AliceMultiverse providers:

```python
# In your code
from alicemultiverse.providers import Provider
from alicemultiverse.prompts import track_prompt_usage

class MyProvider(Provider):
    @track_prompt_usage("my_provider")
    async def generate(self, prompt: str, **kwargs):
        # Your generation code
        return result
```

### Manual Integration

```python
from alicemultiverse.prompts import PromptService

service = PromptService()

# After generation
service.record_usage(
    prompt_id="abc123",
    provider=ProviderType.MIDJOURNEY,
    success=True,
    output_path="/path/to/result.png",
    cost=0.10
)
```

## Advanced Features

### Prompt Templates

Create reusable templates with variables:

```yaml
# templates/character_portrait.yaml
prompt: "Portrait of {character_type} with {mood} expression, {style} art style"

variables:
  character_type: "e.g., warrior, mage, scientist"
  mood: "e.g., determined, mysterious, friendly"
  style: "e.g., fantasy, cyberpunk, realistic"

examples:
  - variables:
      character_type: "cyberpunk hacker"
      mood: "focused"
      style: "neon noir"
    result: "Portrait of cyberpunk hacker with focused expression, neon noir art style"
```

### Batch Operations

Process multiple prompts:

```python
from alicemultiverse.prompts import PromptService

service = PromptService()

# Get all prompts for a project
prompts = service.search_prompts(project="MyProject")

# Bulk update
for prompt in prompts:
    if prompt.success_rate() > 0.8:
        prompt.effectiveness_rating = 9.0
        service.update_prompt(prompt)
```

### Export for Analysis

```python
from alicemultiverse.prompts import PromptProviderIntegration

integration = PromptProviderIntegration()

# Export project insights
integration.export_project_insights(
    "MyProject",
    Path("insights/myproject_analysis.json")
)
```

## Troubleshooting

### Common Issues

1. **Prompts not syncing**: Ensure `.alice/prompts/` exists in project
2. **Search not finding prompts**: Run sync commands to update index
3. **YAML parsing errors**: Check for proper indentation and syntax

### Performance Tips

1. **Use specific searches**: Add filters to narrow results
2. **Limit discovery scope**: Specify exact base paths
3. **Regular cleanup**: Remove unused prompts periodically

## Summary

The prompt management system helps you:

- **Track what works**: Monitor success rates and costs
- **Stay organized**: Keep prompts with projects
- **Find inspiration**: Search your prompt history
- **Improve over time**: Learn from effectiveness data
- **Collaborate**: Share prompts through version control

Start with `alice prompts init` in your project and begin building your prompt library!