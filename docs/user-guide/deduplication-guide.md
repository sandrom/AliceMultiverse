# Deduplication Guide

AliceMultiverse includes advanced deduplication capabilities to help you find and remove duplicate images and videos, saving storage space and avoiding redundant AI processing costs.

## Overview

The deduplication system uses multiple perceptual hashing algorithms to find:
- **Exact duplicates** - Identical files with different names
- **Visual duplicates** - Images that look the same but have different formats/sizes
- **Similar images** - Images that are variations of each other

## MCP Tools (Recommended)

When using Alice through Claude Desktop, use these MCP tools:

### Finding Duplicates

```
Find all duplicates in my collection
```

This will trigger `find_duplicates_advanced` which:
- Scans your organized folder
- Finds both exact and visually similar images
- Groups duplicates by similarity
- Shows potential space savings

### Removing Duplicates

```
Remove duplicate images, keeping the best quality versions
```

This uses `remove_duplicates` with smart selection:
- Keeps images in organized folders over inbox
- Preserves files with metadata
- Chooses larger file sizes (higher quality)
- Creates backups before removal

### Building Similarity Index

For large collections (10,000+ images), build an index first:

```
Build a similarity index for fast duplicate detection
```

This creates a FAISS index for instant similarity searches.

### Finding Similar Images

```
Find images similar to /path/to/image.jpg
```

Returns visually similar images ranked by similarity score.

## CLI Usage (Debug Only)

For debugging or automation:

```bash
# Find duplicates with default settings
alice dedupe find --directory ~/Pictures/AI/organized

# Find only exact duplicates
alice dedupe find --exact-only

# Find similar images with custom threshold
alice dedupe find --threshold 0.85  # More lenient (default: 0.95)

# Remove duplicates (dry run first)
alice dedupe remove --dry-run

# Remove duplicates, keep organized versions
alice dedupe remove --strategy keep_organized

# Remove duplicates using hardlinks (saves space without deletion)
alice dedupe remove --hardlinks

# Build similarity index
alice dedupe index --rebuild
```

## Understanding Similarity Scores

- **1.0** - Exact duplicate (identical pixels)
- **0.95-0.99** - Nearly identical (different compression/format)
- **0.90-0.95** - Very similar (minor edits, crops)
- **0.85-0.90** - Similar composition (same subject, different angle)
- **< 0.85** - Different images

## Deduplication Strategies

### Keep Organized (Default)
Preserves files in your organized structure, removes duplicates from inbox:
```
alice dedupe remove --strategy keep_organized
```

### Keep Largest
Keeps the highest quality version based on file size:
```
alice dedupe remove --strategy keep_largest
```

### Keep Newest
Keeps the most recently modified version:
```
alice dedupe remove --strategy keep_newest
```

### Interactive
Asks for each duplicate group:
```
alice dedupe remove --strategy interactive
```

## Integration with Workflows

### Before AI Processing
Always deduplicate before expensive operations:

```bash
# 1. Deduplicate first
alice dedupe remove --directory ~/Downloads/ai-images

# 2. Then run understanding
alice --understand --directory ~/Downloads/ai-images
```

This can save 20-40% on API costs by avoiding duplicate processing.

### After Downloading
When downloading from AI generators, duplicates are common:

```bash
# Download from Midjourney/DALL-E/etc
# Then immediately deduplicate
alice dedupe find --directory ~/Downloads/ai-images --remove
```

### Periodic Cleanup
Run monthly to keep your collection clean:

```bash
# Find all duplicates in organized folder
alice dedupe find --directory ~/Pictures/AI/organized

# Review the report
# Then remove with backup
alice dedupe remove --backup ~/Pictures/AI/duplicates-backup
```

## Performance Tips

1. **Use the similarity index** for collections over 10,000 images
2. **Start with higher thresholds** (0.95+) and lower if needed
3. **Always dry-run first** to preview what will be removed
4. **Use hardlinks** to save space without losing files
5. **Process in batches** for very large collections

## Video Deduplication

The system also handles video files:

```bash
# Include videos in deduplication
alice dedupe find --include-videos

# Video-specific threshold (more lenient due to compression)
alice dedupe find --include-videos --threshold 0.85
```

## Configuration

Add to your `settings.yaml`:

```yaml
deduplication:
  similarity_threshold: 0.95
  include_videos: true
  backup_before_remove: true
  preserve_metadata: true
  hash_algorithms:
    - phash  # Perceptual hash (default)
    - dhash  # Difference hash
    - whash  # Wavelet hash
```

## Cost Savings Example

For a typical collection:
- 10,000 images downloaded
- 25% are duplicates (2,500 images)
- Understanding cost: $0.004 per image
- **Savings: $10** from avoiding duplicate analysis

## Troubleshooting

### "No duplicates found"
- Lower the threshold: `--threshold 0.85`
- Check if images are in supported formats (JPG, PNG, WebP, HEIC)
- Ensure the directory path is correct

### "Too many false positives"
- Increase the threshold: `--threshold 0.98`
- Use `--exact-only` for identical files only
- Review similarity scores before removing

### "Process is too slow"
- Build a similarity index first
- Process smaller directories
- Use `--limit 1000` to process in chunks

## Best Practices

1. **Always backup** before first use
2. **Start conservative** with high thresholds
3. **Review groups** before batch removal
4. **Use hardlinks** when unsure
5. **Integrate early** in your workflow to maximize savings

The deduplication system is designed to be safe and conservative by default. It will never remove your only copy of an image and always provides detailed reports before taking action.