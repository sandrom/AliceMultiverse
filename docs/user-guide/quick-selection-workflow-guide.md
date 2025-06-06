# Quick Selection Workflow Guide

Master the art of rapidly marking, organizing, and exporting your favorite images with AliceMultiverse's Quick Selection system.

## Overview

Quick Selection is designed for the moments when you're reviewing hundreds or thousands of images and need to:
- Mark favorites instantly
- Track why you selected each image
- Build collections for specific purposes  
- Export organized sets for different uses
- Maintain selection history

## Core Concepts

### Selection vs. Organization

**Quick Selection** is about:
- Temporary marking for immediate use
- Building project-specific sets
- Fast decision making
- Export preparation

**Organization** is about:
- Permanent folder structure
- Long-term storage
- Comprehensive metadata
- Archive management

Quick Selection feeds into Organization but serves a different purpose.

## Basic Workflow

### 1. Marking Images

```python
# Through Claude MCP
"Mark this image as a favorite"
"Quick mark all portraits from today"
"Star the best 5 images from this set"

# Direct commands
alice quick_mark image_001.jpg
alice quick_mark --batch portrait_*.jpg
```

### 2. Selection Criteria

Each selection can include:
- **Rating**: 1-5 stars
- **Purpose**: What it's selected for
- **Notes**: Why you chose it
- **Tags**: Quick categorization

```python
# Rich selection
"Mark this as 5-star for client portfolio"

# Creates:
{
  "image": "sunset_001.jpg",
  "rating": 5,
  "purpose": "client portfolio",
  "selected_at": "2024-01-20T15:30:00Z",
  "notes": "Perfect golden hour lighting"
}
```

### 3. Viewing Selections

```python
# See current selections
"Show my quick selections"
"List 5-star selections from this week"
"Show selections marked for Instagram"
```

## Efficient Marking Strategies

### Keyboard Shortcuts (Web UI)

When using the comparison interface:
- `1-5`: Rate current image
- `Space`: Quick mark (toggle)
- `X`: Reject/hide
- `N`: Add note
- `T`: Quick tag
- `→`: Next image
- `←`: Previous image

### Batch Operations

```python
# Mark multiple at once
"Mark all images with 'sunset' tag"
"Quick select top 10 by quality score"
"Mark images 5-15 from this folder"
```

### Smart Selections

```python
# AI-assisted marking
"Mark the sharpest portraits"
"Select images with best composition"
"Find and mark all golden hour shots"
```

## Selection Management

### Collections

Group selections into named collections:

```python
# Create collection
"Create collection 'Website Hero Images'"

# Add to collection  
"Add current selection to 'Website Heroes'"

# View collection
"Show me the 'Website Heroes' collection"
```

### Selection States

Images can be in multiple states:
- **Unmarked**: Not yet reviewed
- **Marked**: Selected for use
- **Starred**: Rated (1-5 stars)
- **Rejected**: Marked as no-use
- **Pending**: Needs further review

### Selection History

```python
# Track decision history
"Show selection history for this image"

# Returns:
- 2024-01-15: Marked for review
- 2024-01-16: Rated 4 stars
- 2024-01-18: Added to 'Client' collection
- 2024-01-20: Upgraded to 5 stars
```

## Export Manifest Creation

### Basic Export

```python
# Export selection list
"Export my selections as a list"

# Creates: selections_2024_01_20.json
{
  "selection_count": 47,
  "date_range": "2024-01-15 to 2024-01-20",
  "images": [
    {
      "path": "portrait_001.jpg",
      "rating": 5,
      "purpose": "portfolio"
    }
  ]
}
```

### Organized Export

```python
# Export with structure
"Export selections organized by rating"

# Creates folders:
/export/
  /5_star/
  /4_star/
  /3_star/
```

### Platform-Specific Exports

```python
# Instagram-ready export
"Export Instagram selections as 1:1 crops"

# Web-optimized export  
"Export website selections at 2048px with WebP"

# Print-ready export
"Export print selections at 300 DPI TIFF"
```

## Batch Operations

### Bulk Actions

```python
# Upgrade ratings
"Upgrade all 4-star portraits to 5-star"

# Clear selections
"Clear selections older than 30 days"

# Transfer selections
"Move project A selections to project B"
```

### Conditional Operations

```python
# Complex selections
"Mark all images where:
 - Quality score > 85
 - Has 'portrait' tag
 - Taken this month"
```

### Selection Filters

```python
# Filter current selections
"Show only 5-star selections"
"Hide rejected images"
"Show unmarked images only"
```

## Integration with Other Features

### With Style Clustering

```python
# Select by style
"Mark best image from each style cluster"
"Select all from 'minimalist' cluster rated 4+"
```

### With AI Understanding

```python
# Smart content selection
"Mark all images containing cats"
"Select best composed landscapes"
"Find and mark all close-ups"
```

### With Timeline Creation

```python
# Video preparation
"Use my 5-star selections for hero shots"
"Create timeline from 'music video' collection"
```

## Advanced Workflows

### Progressive Refinement

Start broad, narrow down:

```python
# Round 1: Initial pass
"Quickly mark anything interesting"
# Result: 200 marked

# Round 2: Quality filter  
"From marked, keep only sharp images"
# Result: 150 remain

# Round 3: Composition
"From these, select best composed"
# Result: 75 remain

# Round 4: Final picks
"Rate top 20 as 5-star"
# Result: 20 portfolio images
```

### Purpose-Driven Selection

```python
# Define purpose first
purposes = [
  "hero_images",      # 5-10 stunning shots
  "supporting",       # 20-30 good shots
  "social_media",     # 50+ shareable
  "archive"          # Everything decent
]

# Select accordingly
"Mark top 5 as hero images"
"Mark next 20 as supporting"
```

### Collaborative Selection

```python
# Export for review
"Export selections with preview URLs"

# Import feedback
"Import selection feedback from client"

# Merge selections
"Combine my picks with client picks"
```

## Selection Analytics

### Usage Patterns

```python
# Understand your preferences
"Show my selection statistics"

# Returns:
- Average images marked: 15%
- Favorite time: Golden hour
- Preferred style: Minimalist
- Top tags: portrait, landscape, sunset
```

### Quality Metrics

```python
# Track selection quality
"Show average quality score of selections"

# Helps understand:
- Are you too picky?
- Are you too lenient?
- Is quality improving?
```

## Practical Examples

### Example 1: Event Photography

```python
# Wedding selection workflow
workflow = {
  "1_getting_ready": "Mark candid moments",
  "2_ceremony": "Mark key moments + emotions",
  "3_portraits": "Select sharp, well-lit shots",
  "4_reception": "Mark dancing, speeches, details",
  "5_hero_shots": "Pick 10 absolute best"
}

# Execute each stage
for stage, instruction in workflow.items():
    execute(instruction)
```

### Example 2: Product Shoot

```python
# E-commerce selection
"Mark all products with clean backgrounds"
"From those, select sharpest angle of each"
"Rate hero angles as 5-star"
"Export at 2000x2000 white background"
```

### Example 3: Travel Photography

```python
# Location-based selection
"Group by GPS location"
"Select 2-3 best from each location"
"Mark one hero shot per day"
"Create story sequence for blog"
```

## Tips and Tricks

### Speed Techniques

1. **Use comparison mode**: See images side-by-side
2. **Keyboard only**: Keep hands on keys
3. **Batch similar**: Process groups together
4. **Quick reject**: Remove obvious no-gos first

### Decision Helpers

1. **Trust first instinct**: Don't overthink
2. **Purpose clarity**: Know why you're selecting
3. **Quality threshold**: Set minimum standards
4. **Time limit**: Don't spend too long per image

### Organization Tips

1. **Clear regularly**: Don't let selections pile up
2. **Name collections**: Make them searchable
3. **Document criteria**: Note why images were selected
4. **Export promptly**: Use selections while fresh

## Troubleshooting

### Common Issues

**Too many selections**
- Be more selective
- Use rating system
- Create sub-collections

**Lost selections**
- Check selection history
- Look in collections
- Review export logs

**Slow performance**
- Clear old selections
- Use batch operations
- Enable selection cache

### Recovery Options

```bash
# Backup selections
alice backup_selections --output backup.json

# Restore selections
alice restore_selections --input backup.json

# Merge selection sets
alice merge_selections set1.json set2.json
```

## Best Practices

### 1. Regular Reviews
- Weekly: Export and clear
- Monthly: Analyze patterns
- Quarterly: Refine workflow

### 2. Clear Criteria
- Define before selecting
- Document decisions
- Maintain consistency

### 3. Efficient Processing
- Work in batches
- Use keyboard shortcuts
- Leverage AI assistance

### 4. Purposeful Export
- Know final use
- Export appropriately
- Maintain quality

## Quick Selection API

For automation:

```python
# Programmatic selection
from alicemultiverse.selections import QuickSelector

selector = QuickSelector()

# Mark images
selector.mark_image("path/to/image.jpg", 
    rating=5,
    purpose="portfolio",
    tags=["hero", "client_favorite"]
)

# Bulk operations
selector.mark_batch(
    pattern="*.jpg",
    criteria=lambda img: img.quality_score > 90
)

# Export
selector.export_collection("portfolio", 
    format="organized",
    resize=(2048, None),
    quality=95
)
```

## Next Steps

1. **Practice quick marking**: Build muscle memory
2. **Develop your criteria**: What makes an image selection-worthy?
3. **Create templates**: Standard collections for repeated needs
4. **Track success**: Which selections get used?

## Additional Resources

- [Selection Tracking Guide](./selection-tracking.md) - Deep dive on analytics
- [Export Guide](./video-export-guide.md) - Detailed export options
- [Workflow Examples](./selection-workflow-guide.md) - Real-world workflows

---

**Remember**: Quick Selection is about speed and decisiveness. Don't aim for perfection—aim for efficiently identifying images worth further attention. You can always refine later.