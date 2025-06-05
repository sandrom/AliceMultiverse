# Batch Analysis Optimization Guide

This guide explains how to use AliceMultiverse's optimized batch analysis to save costs when analyzing large collections of AI-generated images.

## Overview

The optimized batch analyzer reduces API costs by:
- **Grouping similar images** using perceptual hashing
- **Analyzing representatives** instead of every image
- **Progressive provider strategy** starting with free/cheap options
- **Reusing results** for visually similar images

## Cost Savings Example

For a collection with 30% similar images:
- **Traditional**: 100 images × $0.01 = $1.00
- **Optimized**: 70 unique images × $0.01 = $0.70
- **Savings**: 30% or $0.30

## Using Optimized Analysis

### 1. Estimate Costs First

Always estimate costs before running analysis:

```
You: Estimate the cost to analyze 500 images

Claude: [Uses estimate_analysis_cost tool]

With optimization (assuming 30% similarity):
- Google AI (free): $0.00 
- DeepSeek: $0.035 (optimized from $0.05)
- OpenAI: $0.70 (optimized from $1.00)
- Anthropic: $2.10 (optimized from $3.00)

Savings: 30% across all providers
```

### 2. Run Optimized Analysis

Analyze images with similarity detection:

```
You: Analyze these images with optimization

Claude: [Uses analyze_images_optimized tool]

Analyzed 70 unique images, applied to 100 total
- API calls saved: 30
- Cost saved: $0.30
- Savings percentage: 30%
```

### 3. Adjust Similarity Threshold

Control how similar images must be to share analysis:

```
You: Analyze with 95% similarity threshold (very similar only)

Claude: [Uses analyze_images_optimized with similarity_threshold=0.95]

More conservative grouping for higher accuracy
```

## Progressive Provider Strategy

The system automatically escalates through provider tiers:

1. **Free Tier** (Google AI)
   - Basic tags and descriptions
   - No cost for first 50/day

2. **Budget Tier** (DeepSeek)
   - More detailed analysis
   - Very low cost

3. **Premium Tier** (Claude/GPT)
   - Best quality analysis
   - Used only when needed

## How Similarity Detection Works

1. **Perceptual Hashing**: Creates fingerprints of visual content
2. **Grouping**: Images with similar fingerprints are grouped
3. **Representative Selection**: One image per group is analyzed
4. **Result Application**: Analysis applied to all group members with confidence scores

## Best Practices

### 1. Pre-Sort Your Images
Group obviously similar images in folders:
```
project/
├── variations/  # Multiple versions of same concept
├── unique/      # Distinct images
└── drafts/      # Work in progress
```

### 2. Use Project-Based Analysis
Analyze entire projects at once for better grouping:
```
Analyze all images in project "cyberpunk-portraits" with optimization
```

### 3. Review Confidence Scores
Similar images get confidence scores:
- 100%: The analyzed representative
- 90-99%: Very similar, high confidence
- 80-89%: Similar, good confidence
- Below 80%: May need individual analysis

### 4. Set Cost Limits
Always set a maximum cost:
```
Analyze with optimization, max cost $5
```

## Understanding the Results

Results include optimization statistics:

```json
{
  "optimization_stats": {
    "total_images": 100,
    "unique_groups": 70,
    "images_analyzed": 70,
    "images_reused": 30,
    "api_calls_saved": 30,
    "cost_saved": 0.30,
    "total_cost": 0.70,
    "savings_percentage": 30.0
  }
}
```

## When to Use Optimization

**Good for:**
- Large collections with variations
- Multiple versions of same concept
- Batch processing after generation
- Budget-conscious analysis

**Not ideal for:**
- Small sets (<10 images)
- Completely unique images
- When highest accuracy needed
- Legal/compliance requirements

## Combining with Other Features

### With Quick Selection
1. Analyze optimized first
2. Quick mark the best versions
3. Export favorites only

### With Duplicate Detection
1. Remove exact duplicates first
2. Then analyze similar images optimized
3. Maximum cost savings

## Example Workflow

```
You: I have 200 cyberpunk portraits to analyze, what's the cost?

Claude: With 30% similarity estimate:
- Without optimization: $2.00 (OpenAI)
- With optimization: $1.40
- Potential savings: $0.60

You: Run optimized analysis with max cost $2

Claude: Starting optimized batch analysis...
- Grouped into 140 unique groups
- Analyzing representatives...

Complete! 
- Analyzed: 140 unique images
- Applied to: 200 total images
- Cost: $1.40
- Saved: $0.60 (30%)

You: Show me the ones tagged "neon" with high confidence

Claude: Found 45 images tagged "neon":
- 32 with 100% confidence (directly analyzed)
- 13 with 85-95% confidence (similar to analyzed)
```

## Tips for Maximum Savings

1. **Batch by Visual Style**: Process similar styles together
2. **Use Free Tier First**: Let Google AI handle basic analysis
3. **Progressive Enhancement**: Only use premium for heroes
4. **Regular Cleanup**: Remove duplicates before analysis
5. **Track Spending**: Monitor your optimization rates

The optimization system typically saves 20-40% on analysis costs while maintaining high quality results through intelligent grouping and provider selection.