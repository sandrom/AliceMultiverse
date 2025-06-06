# Style Clustering Guide

Learn how to use AliceMultiverse's visual DNA extraction and style clustering to organize, discover, and create cohesive visual collections.

## Overview

Style clustering analyzes the visual characteristics of your images to:
- Group similar-looking content automatically
- Extract "visual DNA" - the essence of an image's style
- Find images with similar aesthetics across projects
- Maintain visual consistency in your work
- Discover your signature styles

## How Style Clustering Works

### Visual DNA Extraction

Each image is analyzed for multiple style dimensions:

1. **Color Characteristics**
   - Dominant color palette
   - Color temperature (warm/cool)
   - Saturation levels
   - Contrast ratios

2. **Compositional Elements**
   - Rule of thirds usage
   - Symmetry/asymmetry
   - Visual weight distribution
   - Negative space usage

3. **Stylistic Features**
   - Artistic style (photorealistic, painterly, graphic)
   - Texture density
   - Edge definition
   - Lighting style

4. **Technical Attributes**
   - Depth of field characteristics
   - Motion blur presence
   - Grain/noise patterns
   - Resolution indicators

### The Clustering Process

```python
# Visual DNA is encoded as a high-dimensional vector
visual_dna = [
    0.8,  # Warm color bias
    0.3,  # Low saturation
    0.9,  # High contrast
    0.7,  # Center-weighted composition
    ...   # Many more dimensions
]

# Similar images have similar vectors
# Clustering groups images by vector proximity
```

## Basic Usage

### Quick Clustering

```python
# Through Claude MCP
"Cluster my images by visual style"

# Alice will:
# 1. Extract visual DNA from each image
# 2. Group similar styles together
# 3. Show you the clusters with examples
```

### Manual Clustering

```bash
# Analyze a directory
alice cluster_styles --path ./my_images --output style_report.json

# With specific parameters
alice cluster_styles \
  --path ./my_images \
  --num-clusters auto \
  --similarity-threshold 0.85 \
  --save-visualizations
```

## Understanding Cluster Results

### Cluster Report Structure

```json
{
  "cluster_count": 5,
  "clusters": [
    {
      "id": 0,
      "name": "Moody Portraits",
      "size": 23,
      "characteristics": {
        "dominant_colors": ["#2C3E50", "#34495E", "#7F8C8D"],
        "style": "dramatic lighting, low key",
        "mood": "serious, contemplative",
        "technical": "shallow DOF, center focus"
      },
      "representative_images": [
        "portrait_001.jpg",
        "headshot_dark_003.jpg"
      ],
      "visual_coherence": 0.92
    }
  ]
}
```

### Key Metrics

**Visual Coherence**: How similar images within a cluster are (0-1)
- 0.9+ = Very tight cluster, almost identical styles
- 0.7-0.9 = Good cluster, clear style similarity
- 0.5-0.7 = Loose cluster, some variety
- <0.5 = Consider splitting cluster

**Cluster Size**: Number of images
- Large clusters = Your dominant styles
- Small clusters = Unique/experimental work
- Single-image clusters = Outliers

## Similarity Threshold Tuning

### Finding the Right Threshold

The similarity threshold controls how similar images must be to group together:

```bash
# Very similar only (tight clusters)
alice cluster_styles --similarity-threshold 0.95

# Moderate similarity (balanced)
alice cluster_styles --similarity-threshold 0.85

# Loose similarity (fewer, larger clusters)
alice cluster_styles --similarity-threshold 0.70
```

### Guidelines by Use Case

**Portfolio Organization** (0.90-0.95)
- Very tight clusters
- Ensures strong visual consistency
- Good for client presentations

**Style Discovery** (0.80-0.90)
- Balanced clustering
- Reveals style patterns
- Default for most uses

**Broad Categorization** (0.70-0.80)
- Loose clustering
- General style families
- Good for initial organization

### Adaptive Thresholding

```python
# Let Alice determine optimal threshold
"Cluster my images with automatic threshold detection"

# Alice analyzes the visual diversity and chooses
# threshold to create meaningful groups
```

## Cluster Visualization

### Visual Cluster Maps

```python
# Generate visual representation
"Show me a visual map of my style clusters"

# Creates:
# - 2D scatter plot of visual DNA
# - Images plotted by similarity
# - Clusters shown as colored regions
```

### Cluster Montages

```python
# Create montage for each cluster
"Create a style board for each cluster"

# Generates grid showing:
# - Representative images
# - Color palette
# - Style characteristics
```

### Interactive Explorer

```bash
# Launch web interface
alice cluster_styles --interactive

# Features:
# - Drag to explore clusters
# - Click for image details
# - Adjust threshold in real-time
# - Export selected clusters
```

## Practical Use Cases

### 1. Portfolio Curation

```python
# Find your signature styles
"Show me my most consistent visual styles"

# Results might show:
# - Cluster 1: Minimalist portraits (45 images)
# - Cluster 2: Vibrant street photography (32 images)
# - Cluster 3: Moody landscapes (28 images)
```

### 2. Project Consistency

```python
# Ensure visual cohesion
"Check if these images belong to the same visual style"

# Or find matching images
"Find all images that match this style"
```

### 3. Style Evolution Tracking

```python
# Analyze style changes over time
"Show how my style has evolved this year"

# Reveals:
# - New clusters appearing
# - Clusters growing/shrinking
# - Style drift within clusters
```

### 4. Client Deliverables

```python
# Create consistent sets
"Select 20 images from the 'corporate portrait' cluster"

# Ensures delivered images have:
# - Consistent look and feel
# - Professional cohesion
# - No style outliers
```

## Performance Optimization

### Caching Strategy

Visual DNA extraction is computationally intensive:

```bash
# First run: Extracts and caches visual DNA
alice cluster_styles --path ./images --cache-dna

# Subsequent runs: Uses cached DNA (much faster)
alice cluster_styles --path ./images
```

### Batch Processing

```python
# Process large collections efficiently
"Cluster my entire library in batches of 1000"

# Prevents memory issues
# Shows progress
# Can resume if interrupted
```

### Incremental Updates

```python
# Add new images to existing clusters
"Add today's images to my existing style clusters"

# Only processes new images
# Assigns to best matching cluster
# Suggests new cluster if needed
```

## Advanced Techniques

### Multi-Level Clustering

```python
# Hierarchical clustering
"Create main style categories, then sub-styles"

# Example result:
# Portrait Photography
#   ├── Environmental Portraits
#   ├── Studio Headshots
#   └── Candid Street Portraits
```

### Cross-Project Analysis

```python
# Find style connections
"Show style similarities across all my projects"

# Reveals:
# - Recurring themes
# - Style preferences
# - Unexpected connections
```

### Style Fingerprinting

```python
# Create unique style ID
"Generate a style fingerprint for this cluster"

# Returns style DNA that can be:
# - Saved for future matching
# - Shared with others
# - Used as generation prompt
```

## Integration with Other Features

### With Quick Selection

```python
# Select by style
"Mark all images from the 'neon cyberpunk' cluster"

# Quickly builds cohesive selections
```

### With Music Sync

```python
# Match visual styles to music sections
"Use minimalist cluster for verse, vibrant for chorus"

# Creates visual rhythm aligned with music
```

### With Generation

```python
# Generate in existing style
"Create new images matching my 'dreamy portrait' cluster"

# Maintains your signature look
```

## Troubleshooting

### Common Issues

**Too Many Clusters**
- Lower similarity threshold
- Check for duplicates
- Consider image quality variance

**Everything in One Cluster**
- Raise similarity threshold  
- Check if images are too similar
- Enable more feature extraction

**Inconsistent Results**
- Clear DNA cache and re-extract
- Check for corrupted images
- Ensure consistent preprocessing

### Debugging Commands

```bash
# Verbose output
alice cluster_styles --verbose --debug

# Analyze specific image
alice analyze_style single_image.jpg

# Compare two images
alice style_similarity img1.jpg img2.jpg
```

## Best Practices

### 1. Regular Clustering
- Run monthly to track style evolution
- Before major projects for style audit
- After large imports for organization

### 2. Threshold Experimentation
- Start with default (0.85)
- Adjust based on your needs
- Save successful thresholds

### 3. Cluster Naming
- Give meaningful names to clusters
- Document cluster characteristics
- Track cluster purposes

### 4. Quality Control
- Review cluster outliers
- Verify representative images
- Check cluster coherence scores

## Style Cluster Management

### Saving Clusters

```bash
# Save cluster definitions
alice save_clusters --name "2024_styles"

# Includes:
# - Cluster parameters
# - Image assignments  
# - Visual DNA cache
# - Statistics
```

### Cluster Operations

```python
# Merge similar clusters
"Merge the 'sunset' and 'golden hour' clusters"

# Split large clusters
"Split the portrait cluster by lighting style"

# Remove outliers
"Remove style outliers from each cluster"
```

### Cluster Evolution

```python
# Track changes
"Show how the 'minimalist' cluster changed this month"

# Set alerts
"Alert me when a new style cluster emerges"
```

## Practical Examples

### Example 1: Wedding Photography

```python
# Organize wedding portfolio
clusters = cluster_styles("wedding_photos/")

# Typical clusters:
# - Golden hour couples
# - Candid reception moments  
# - Detail shots (rings, flowers)
# - Formal group portraits
# - Black & white artistic
```

### Example 2: Product Photography

```python
# Ensure catalog consistency
clusters = cluster_styles("product_shots/")

# Look for:
# - Consistent lighting
# - Background uniformity
# - Angle consistency
# - Color grading match
```

### Example 3: AI Art Organization

```python
# Organize AI generations
clusters = cluster_styles("ai_art/")

# Discovers:
# - Prompt style families
# - Model preferences
# - Artistic periods
# - Failed experiments
```

## Next Steps

1. **Run your first clustering**: Start with a small folder
2. **Experiment with thresholds**: Find what works for your content
3. **Name your clusters**: Build your style vocabulary
4. **Use clusters in workflows**: Selection, generation, curation

## Additional Resources

- [Quick Selection Guide](./quick-selection-guide.md) - Select images efficiently
- [Similarity Search Guide](./similarity-search-guide.md) - Find similar images
- [Understanding System Guide](./intelligent-tag-hierarchies-guide.md) - Semantic organization

---

**Remember**: Style clustering reveals patterns in your work you might not consciously recognize. Use these insights to understand your artistic voice and make more intentional creative choices.