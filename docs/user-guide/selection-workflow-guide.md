# Selection Workflow Guide

This guide shows how to use the complete selection and curation workflow through Claude Desktop.

## Overview

The selection workflow helps you:
1. **Browse** images collaboratively with Claude
2. **Select/Reject** with reasons
3. **Find Similar** images based on your selections
4. **Soft Delete** unwanted images to keep your library clean
5. **Track Everything** for future reference

## Complete Workflow Example

### 1. Starting a Selection Session

```
Me: I need to select images for a cyberpunk video. Show me what I have.

Claude: I'll help you browse your cyberpunk images for video selection.

[Claude uses search_images tool]

Found 147 cyberpunk-themed images. Here's a selection to start:
[Shows image grid with hashes]

What kind of mood are you going for in your video?
```

### 2. Making Selections with Reasons

```
Me: I like the first three - they have that neon-noir feel I want. 
    Skip the fourth one, too bright. The fifth is perfect for the opening.

Claude: I'll track your selections and reasons.

[Claude uses track_selection tool multiple times]

Tracked your selections:
✅ Image 1 (hash: abc123...) - "neon-noir feel"
✅ Image 2 (hash: def456...) - "neon-noir feel"  
✅ Image 3 (hash: ghi789...) - "neon-noir feel"
❌ Image 4 (hash: jkl012...) - "too bright"
✅ Image 5 (hash: mno345...) - "perfect for opening"

Shall I show you more images, or find similar ones to your selections?
```

### 3. Finding Similar Images

```
Me: Find more like the ones I selected, especially similar to the fifth one.

Claude: I'll search for images similar to your selections, particularly the opening shot.

[Claude uses find_similar_assets tool]

Found 23 similar images based on visual style:
- 12 with similar neon-noir atmosphere
- 8 matching the composition of your opening shot
- 3 with comparable color grading

[Shows similar images]

These all share the dark backgrounds with neon accents you selected.
```

### 4. Batch Selection

```
Me: Perfect! Select the first 8, they all work. The last 3 are too generic - 
    move them to sorted out.

Claude: I'll track your selections and move the unwanted images.

[Claude uses track_selection for selections]
[Claude uses soft_delete_image for rejections]

✅ Selected 8 images for your project
🗑️ Moved 3 images to sorted-out/rejected/

Your sorted-out folder now has:
- sorted-out/rejected/ (3 files) - "too generic"
- sorted-out/quality-issues/ (empty)
- sorted-out/duplicates/ (empty)
```

### 5. Reviewing Selections

```
Me: Show me everything I've selected so far for this video.

Claude: I'll get your selection summary.

[Claude uses get_selection_summary tool]

**Cyberpunk Video Selections** (13 total):

Opening Sequence (1):
- mno345... - "perfect for opening"

Main Footage (12):
- abc123... - "neon-noir feel"
- def456... - "neon-noir feel"
- ghi789... - "neon-noir feel"
- [8 more with similar style]

Common themes in your selections:
- Dark backgrounds with neon lighting
- Urban/industrial settings
- Blue and purple color dominance
- High contrast compositions
```

### 6. Creating Selection Rounds

```
Me: Save these as "Round 1 - Dark Mood". I might want to try a different style too.

Claude: I'll save your current selections as Round 1.

[Project structure created]:
my-cyberpunk-video/
├── .alice/
│   └── selections/
│       ├── round-1-dark-mood.json
│       └── selection-history.json
├── rounds/
│   └── round-1-dark-mood/
│       └── [13 selected images copied here]
└── project.yaml

Ready to explore a different style for Round 2?
```

## Advanced Selection Features

### Similarity-Based Curation

```
Me: I changed my mind about the bright ones. Show me brighter cyberpunk images, 
    but still with good composition.

Claude: I'll search for brighter cyberpunk images while maintaining quality composition.

[Claude uses search_images with adjusted parameters]

Here are brighter cyberpunk images with strong composition:
[Shows new selection]

These have more vibrant neon colors and daylight scenes while keeping 
the cyberpunk aesthetic.
```

### Cleaning Up Mistakes

```
Me: Actually, I accidentally rejected some good ones earlier. 
    Can you check the sorted-out folder?

Claude: I'll show you what's in your sorted-out folders.

[Claude searches with exclude_folders parameter removed]

Found 15 images in sorted-out:
- rejected/ (12) - Various reasons
- too-bright/ (3) - From earlier session

[Shows rejected images]

Would you like to restore any of these?
```

### Selection Statistics

```
Me: How's my selection process going? Any patterns?

Claude: Let me analyze your selection patterns.

Selection Statistics:
- Total reviewed: 78 images
- Selected: 31 (39.7%)
- Rejected: 15 (19.2%)
- Undecided: 32 (41.0%)

Your preferences:
- Color: Strong preference for blue/purple (87% of selections)
- Composition: Center-weighted (65% of selections)
- Brightness: Dark/moody (74% of selections)
- Time: Most productive 2-4pm (18 selections)

Suggestion: You have 32 undecided images. Would you like to review those 
with your current criteria in mind?
```

## File Organization

After a selection session, your files are organized:

```
inbox/
├── sorted-out/
│   ├── rejected/        # Generic rejections
│   ├── quality-issues/  # Blurry, artifacts, etc.
│   ├── duplicates/      # Near-duplicates
│   ├── wrong-style/     # Doesn't fit project
│   └── archive/         # Keep but not for this project

project/
├── .alice/
│   └── selections/
│       ├── {selection-id}.json  # Complete history
│       └── summary.json         # Quick overview
└── rounds/
    ├── round-1/  # First selection attempt
    ├── round-2/  # Alternative style
    └── final/    # Final curated set
```

## Tips for Effective Selection

1. **Be Specific with Reasons**
   - Bad: "don't like it"
   - Good: "too saturated for dark mood"

2. **Use Similarity Search**
   - Select 2-3 exemplars first
   - Then find similar to build collection

3. **Organize Rejections**
   - Use categories for soft delete
   - Makes it easier to review later

4. **Work in Rounds**
   - Try different styles/moods
   - Compare rounds before finalizing

5. **Review Patterns**
   - Check your selection statistics
   - Refine criteria based on patterns

## Integration with Other Features

### Cost-Aware Selection

```
Me: If I want to enhance these 31 selected images, what would it cost?

Claude: [Uses estimate_cost tool]

Cost estimate for enhancing 31 images:
- Magnific AI upscaling: $12.40 ($0.40 × 31)
- Real-ESRGAN: $0.31 ($0.01 × 31)
- Flux image-to-image: $0.93 ($0.03 × 31)

Recommendation: Start with Real-ESRGAN for testing, then use Magnific 
for hero shots only.
```

### Export for Video Creation

```
Me: Export my final selections with metadata for Kling prompts.

Claude: I'll prepare your selections for video creation.

Created export package:
exports/
├── cyberpunk-video-selections/
│   ├── images/
│   │   └── [31 selected images]
│   ├── metadata.json
│   ├── kling-prompts.txt
│   └── shot-list.csv

The kling-prompts.txt includes:
- Motion suggestions based on composition
- Transition hints between similar shots
- Timing recommendations

Ready for video generation!
```

## The Complete Flow

1. **Search** → Find initial candidates
2. **Select** → Choose with specific reasons  
3. **Similar** → Expand selection intelligently
4. **Clean** → Soft delete unwanted images
5. **Round** → Try different approaches
6. **Review** → Check statistics and patterns
7. **Export** → Prepare for next step

This workflow ensures you build a thoughtful, curated collection while keeping your library organized and your creative decisions documented.