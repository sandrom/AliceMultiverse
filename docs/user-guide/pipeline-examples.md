# Pipeline Configuration Examples

This guide explains the 4 main pipeline variants and when to use each one.

## The 4 Pipeline Variants

AliceMultiverse offers 4 pipeline configurations, each adding more sophisticated analysis:

| Pipeline | Command | Cost | What It Does |
|----------|---------|------|--------------|
| 1. BRISQUE | `--pipeline brisque` | Free | Local quality assessment only |
| 2. BRISQUE + SightEngine | `--pipeline brisque-sightengine` | $0.001/image | Adds technical quality validation |
| 3. BRISQUE + Claude | `--pipeline brisque-claude` | ~$0.002/image* | Adds AI defect detection |
| 4. BRISQUE + SightEngine + Claude | `--pipeline brisque-sightengine-claude` | ~$0.003/image* | Full analysis pipeline |

*Only charges for 4-5 star images that pass initial BRISQUE filtering

### 1. BRISQUE Only (Free)

```bash
alice --pipeline brisque
# Alias: alice --pipeline basic
```

**Use when:**
- Testing the system
- Budget is $0
- You only need basic quality filtering
- Processing large batches where API costs would be high

**What it does:**
- Uses BRISQUE algorithm for quality assessment
- Organizes images into 1-5 star folders
- No API calls, completely free

### 2. BRISQUE + SightEngine ($0.001/image)

```bash
alice --pipeline brisque-sightengine
# Alias: alice --pipeline standard
```

**Use when:**
- You want technical quality validation
- Budget allows for $1 per 1,000 images
- You need AI detection confirmation
- Quality refinement is important

**What it does:**
- BRISQUE filters out 1-2 star images
- SightEngine refines quality ratings for 3-5 star images
- Provides technical quality metrics

### 3. BRISQUE + Claude (~$0.002/image for 4-5 stars)

```bash
alice --pipeline brisque-claude
```

**Use when:**
- You want AI defect detection
- Don't need SightEngine's technical analysis
- Want to save $0.001 per image vs premium
- Focus is on catching AI-specific defects

**What it does:**
- BRISQUE filters out 1-3 star images
- Claude analyzes 4-5 star images for AI defects
- Skips SightEngine to reduce costs
- Final quality based on BRISQUE + Claude

### 4. BRISQUE + SightEngine + Claude (~$0.003/image for 4-5 stars)

```bash
alice --pipeline brisque-sightengine-claude
# Aliases: alice --pipeline premium
#          alice --pipeline full
```

**Use when:**
- Quality is paramount
- You want maximum accuracy
- Budget allows for comprehensive analysis
- Processing high-value content

**What it does:**
- BRISQUE provides initial assessment
- SightEngine adds technical quality analysis
- Claude detects AI-specific defects
- Combined scoring from all three stages

## Cost Comparison

Assuming a batch of 1,000 images with typical quality distribution:
- 20% are 1-2 stars (200 images)
- 30% are 3 stars (300 images)
- 30% are 4 stars (300 images)
- 20% are 5 stars (200 images)

| Pipeline | Images Processed | Cost |
|----------|-----------------|------|
| basic | 1,000 (all) | $0.00 |
| standard | 1,000 BRISQUE + 800 SightEngine | $0.80 |
| brisque-claude | 1,000 BRISQUE + 500 Claude | $1.00 |
| premium | 1,000 BRISQUE + 800 SightEngine + 500 Claude | $1.80 |

## Custom Pipelines

You can create custom pipelines with specific stages:

```bash
# Just SightEngine (unusual but possible)
alice --pipeline custom --stages "sightengine"

# Reverse order (not recommended)
alice --pipeline custom --stages "claude,sightengine,brisque"

# Skip BRISQUE (not recommended - no initial filtering)
alice --pipeline custom --stages "sightengine,claude"
```

## Recommendations by Use Case

### Hobbyist / Personal Use
- Start with `--pipeline basic`
- Upgrade to `--pipeline standard` for better accuracy

### Content Creator
- Use `--pipeline brisque-claude` for AI defect detection
- Skip SightEngine if technical quality isn't critical

### Professional / Commercial
- Use `--pipeline premium` for maximum quality
- Set cost limits: `--cost-limit 10.0`

### Large Scale Processing
- Use `--pipeline basic` for initial sorting
- Run `--pipeline brisque-claude` on "keeper" folders only

## Tips

1. **Always do a dry run first:**
   ```bash
   alice --pipeline premium --dry-run
   ```

2. **Set cost limits to avoid surprises:**
   ```bash
   alice --pipeline premium --cost-limit 5.0
   ```

3. **Process in batches:**
   ```bash
   # Process by project
   alice inbox/project1 --pipeline brisque-claude
   alice inbox/project2 --pipeline standard
   ```

4. **Use watch mode for ongoing organization:**
   ```bash
   alice -w --pipeline basic  # Free continuous monitoring
   ```

## Progressive Quality Enhancement

You can run different pipelines on the same images:

```bash
# First pass: Basic organization
alice --pipeline basic

# Second pass: Add SightEngine for 4-5 star images
alice organized/*/project/*/4-star --pipeline standard
alice organized/*/project/*/5-star --pipeline standard

# Third pass: Claude for the very best
alice organized/*/project/*/5-star --pipeline brisque-claude
```

This approach lets you progressively invest in quality assessment based on initial results.