# Quick Selection Workflow Guide

This guide explains how to rapidly mark and organize your favorite AI-generated images using AliceMultiverse's quick selection tools.

## Overview

The quick selection workflow allows you to:
- Instantly mark images as favorites, hero shots, or "maybe later"
- Review and export your selections
- Work at the speed of thought without detailed metadata

## Quick Mark Types

- **favorite**: Your best images that you want to keep
- **hero**: Outstanding shots perfect for presentations
- **maybe**: Images to review later
- **review**: Images needing further evaluation

## Workflow Examples

### 1. Rapid Triage During Search

When browsing search results, quickly mark the best ones:

```
You: Search for cyberpunk portraits from this week

Claude: [Shows search results with content hashes]

You: Mark the first three as favorites

Claude: [Uses quick_mark tool with asset_ids and mark_type="favorite"]
```

### 2. Building a Hero Collection

Collect your best shots across multiple searches:

```
You: Mark these as hero shots for my presentation

Claude: [Uses quick_mark with mark_type="hero"]

You: Show me all my hero marks from this week

Claude: [Uses list_quick_marks with mark_type="hero"]
```

### 3. Review Later Workflow

Mark images for later review when you're unsure:

```
You: These three are interesting but I'm not sure - mark them as maybe

Claude: [Uses quick_mark with mark_type="maybe"]

You: Later... Show me all my maybe marks

Claude: [Uses list_quick_marks with mark_type="maybe"]
```

### 4. Export Your Selections

Export marked images to use in other tools:

```
You: Export today's favorites to a folder

Claude: [Lists today's quick marks, then uses export_quick_marks]
```

## How It Works

1. **Daily Collections**: Quick marks are automatically organized into daily collections (e.g., "quick-favorite-2025-06-05")

2. **Project Association**: Optionally associate quick marks with a project

3. **Persistent Storage**: Quick marks use the full selection service, so they're saved permanently

4. **Easy Export**: Export any collection with files or just a manifest

## Integration with Full Selection System

Quick marks create proper selections that can be:
- Edited with full metadata later
- Combined into larger collections
- Used in video creation workflows
- Tracked with detailed history

## Tips for Fast Workflow

1. **Use Batch Marking**: Mark multiple images at once
   ```
   Mark images abc123, def456, and ghi789 as favorites
   ```

2. **Review Periodically**: Check your maybe marks weekly
   ```
   Show me all maybe marks from the last 7 days
   ```

3. **Export for Projects**: Export hero shots for presentations
   ```
   Export this week's hero marks to ~/Desktop/presentation
   ```

4. **Combine with Search**: Mark during search sessions
   ```
   Search for landscapes, then mark the best 5 as favorites
   ```

## Example Session

```
You: Search for fantasy art from yesterday

Claude: Found 23 fantasy art images from yesterday...
[Shows results]

You: Mark the dragon one and the castle scene as favorites

Claude: Marked 2 assets as favorite
- Added to selection: quick-favorite-2025-06-05
- Total in today's favorites: 7

You: Also mark the wizard portrait as a hero shot

Claude: Marked 1 asset as hero
- Added to selection: quick-hero-2025-06-05
- Total in today's heroes: 3

You: Show me all my quick marks from today

Claude: Found 2 quick mark collections from today:
1. quick-favorite-2025-06-05 (7 assets)
2. quick-hero-2025-06-05 (3 assets)

You: Export the hero shots

Claude: Exported 3 assets to exports/quick-hero-2025-06-05/
- Files copied successfully
- Manifest created with metadata
```

## Next Steps

- Use `quick_mark` during any image browsing session
- Review marks with `list_quick_marks` 
- Export collections with `export_quick_marks`
- Graduate important selections to full project selections when needed