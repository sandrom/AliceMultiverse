# Claude Integration Guide

This guide covers the Claude API integration for AI defect detection in AliceMultiverse's quality pipelines.

## Overview

The Claude integration provides advanced AI defect detection that can be used in two pipeline configurations:
- **brisque-claude**: Direct BRISQUE → Claude pipeline for faster processing
- **brisque-sightengine-claude**: Full three-stage pipeline with technical quality checks

It uses Claude's vision capabilities to identify common issues in AI-generated images such as:

- Anatomical errors (extra fingers, merged limbs, impossible poses)
- Facial distortions (asymmetry, unnatural features) 
- Texture inconsistencies (skin, fabric, materials)
- Lighting and shadow errors
- Background anomalies
- Object coherence issues
- Perspective and scale problems

## Setup

### 1. Install the Required Package

The Anthropic package is included in the optional dependencies:

```bash
# Install with premium features
pip install "alicemultiverse[premium]"

# Or install directly
pip install anthropic>=0.18.0
```

### 2. Get Your API Key

1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Navigate to API Keys section
3. Create a new API key
4. Copy the key (starts with `sk-ant-`)

### 3. Configure the API Key

Use the interactive setup wizard:

```bash
alice keys setup
# Select option 2 for Anthropic Claude
# Paste your API key when prompted
```

Or set it directly:

```bash
# Note: The setup command will prompt for your key interactively
alice keys setup
```

For containerized environments, use environment variables:

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

## Usage

### Pipeline Options with Claude

You have two pipeline options that include Claude:

```bash
# Option 1: BRISQUE → Claude (skip SightEngine)
alice --pipeline brisque-claude

# Option 2: BRISQUE → SightEngine → Claude (full analysis)
alice --pipeline brisque-sightengine-claude

# Using aliases
alice --pipeline premium  # Same as brisque-sightengine-claude
alice --pipeline full     # Same as brisque-sightengine-claude
```

### Cost Considerations

Claude pricing (as of 2024):
- **Haiku** (default): ~$0.002 per image
- **Sonnet**: ~$0.008 per image  
- **Opus**: ~$0.024 per image

The pipeline uses progressive filtering to minimize costs:
1. BRISQUE filters out 1-3 star images (free)
2. SightEngine processes 3-5 star images ($0.001 each)
3. Claude only processes 4-5 star images (~$0.002+ each)

This typically reduces Claude API costs by 70-90%.

### Cost Management

Set a cost limit to control spending:

```bash
# Limit total pipeline cost to $10
alice --pipeline brisque-sightengine-claude --cost-limit 10.0

# Dry run to estimate costs
alice --pipeline brisque-claude --dry-run
```

## How It Works

### 1. Progressive Quality Filtering

Depending on your chosen pipeline, images are processed through different stages:

```
# brisque-claude pipeline:
All Images → BRISQUE (local) → 4+ stars → Claude

# brisque-sightengine-claude pipeline:
All Images → BRISQUE (local) → 3+ stars → SightEngine → 4+ stars → Claude
```

### 2. Defect Detection

Claude analyzes high-quality images for AI-specific defects:

```python
# Example Claude analysis result
{
    'defects_found': True,
    'defect_count': 2,
    'severity': 'medium',
    'defects': [
        'Extra finger on left hand',
        'Unnatural skin texture on forearm'
    ],
    'confidence': 0.85
}
```

### 3. Quality Score Refinement

Claude's findings are combined with previous scores:

- **No defects**: Maintains or improves rating
- **Minor defects** (1-2, low severity): May maintain rating
- **Major defects** (3+, high severity): May reduce rating

The final score uses configurable weights:

**brisque-claude pipeline:**
- BRISQUE: 70%
- Claude: 30%

**brisque-sightengine-claude pipeline:**
- BRISQUE: 40%
- SightEngine: 30%
- Claude: 30%

### 4. Final Organization

Images are organized by their final star rating:

```
organized/2024-03-15/project-name/stablediffusion/
├── 5-star/       # Perfect images (passed all checks)
├── 4-star/       # High quality (minor issues acceptable)
├── 3-star/       # Good quality (not processed by Claude)
├── 2-star/       # Fair quality (BRISQUE only)
└── 1-star/       # Poor quality (BRISQUE only)
```

## Configuration

### Custom Weights

Adjust scoring weights in `settings.yaml`:

```yaml
pipeline:
  scoring_weights:
    brisque-claude:
      brisque: 0.7      # 70% weight
      claude: 0.3       # 30% weight
    
    brisque-sightengine-claude:
      brisque: 0.4      # 40% weight
      sightengine: 0.3  # 30% weight  
      claude: 0.3       # 30% weight
```

### Star Thresholds

Customize quality thresholds:

```yaml
pipeline:
  star_thresholds:
    5_star: 0.80  # Combined score >= 0.80
    4_star: 0.65  # Combined score >= 0.65
```

### Model Selection

Use different Claude models (in code):

```python
# In your custom script
from alicemultiverse.quality.claude import check_image_defects

# Use Sonnet for better accuracy
result = check_image_defects(
    "image.png",
    api_key,
    model="claude-3-sonnet-20240229"
)
```

## Troubleshooting

### Common Issues

1. **"No module named 'anthropic'"**
   ```bash
   pip install anthropic>=0.18.0
   ```

2. **"API rate limit exceeded"**
   - Claude has rate limits, especially for free tier
   - Use `--cost-limit` to control usage
   - Consider using Haiku model for higher limits

3. **"Incorrect API key"**
   - Verify key starts with `sk-ant-`
   - Check key permissions in Anthropic console
   - Try setting via environment variable

### Debug Mode

View detailed Claude responses:

```bash
# Enable verbose logging
alice --pipeline premium -v

# Check specific image
python -c "
from alicemultiverse.quality.claude import check_image_defects
result = check_image_defects('test.png', 'your-key')
print(result['raw_response'])
"
```

## Best Practices

1. **Start with dry run** to estimate costs before processing
2. **Use cost limits** to prevent unexpected charges
3. **Process in batches** to monitor quality distribution
4. **Cache results** - AliceMultiverse automatically caches Claude results
5. **Monitor API usage** in the Anthropic console

## Example Workflow

```bash
# 1. Setup API key
alice keys setup

# 2. Test on small batch
alice inbox --pipeline premium --dry-run

# 3. Process with cost limit
alice inbox --pipeline premium --cost-limit 5.0

# 4. Review results
ls organized/*/project-name/*/5-star/

# 5. Check for defects
alice inbox --pipeline premium -v | grep "defects_found"
```

## API Response Format

Claude returns structured defect analysis:

```json
{
  "defects_found": true,
  "defect_count": 3,
  "severity": "medium",
  "defects": [
    "Anatomical error: six fingers on right hand",
    "Texture inconsistency: skin appears plastic-like",
    "Perspective issue: chair legs don't align properly"
  ],
  "confidence": 0.85,
  "model": "claude-3-haiku-20240307",
  "tokens_used": 1245
}
```

This information is stored in the image metadata cache for future reference.