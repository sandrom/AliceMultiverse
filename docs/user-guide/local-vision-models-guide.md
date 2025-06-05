# Local Vision Models Guide

Use free, private local vision models with AliceMultiverse to analyze images without API costs.

## Overview

AliceMultiverse now supports Ollama for local image analysis:
- **Free**: No API costs
- **Private**: Images never leave your machine
- **Fast**: Local inference with GPU acceleration
- **Hybrid**: Fallback to cloud for complex analysis

## Quick Start

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai
```

### 2. Pull a Vision Model

```bash
# Basic model (7B, fast)
ollama pull llava:latest

# Better quality (13B, slower)
ollama pull llava:13b

# Alternative models
ollama pull bakllava:latest
ollama pull llava-phi3:latest
```

### 3. Check Status in Alice

```
You: Check if local vision models are available
Alice: Checking Ollama status...

Ollama is running with vision models available:
- llava:latest (recommended for general use)
- llava:13b (better quality, slower)
```

## Using Local Analysis

### Basic Local Analysis

```
You: Analyze these images using local models
- /inbox/project/image1.png
- /inbox/project/image2.png

Alice: Analyzing 2 images locally...

✓ Analyzed image1.png (local, free)
  Tags: portrait, woman, cyberpunk, neon lighting
  
✓ Analyzed image2.png (local, free)
  Tags: landscape, futuristic city, night scene

Total cost: $0.00 (saved ~$0.002)
```

### Hybrid Analysis (Local + Cloud)

```
You: Analyze images with local first, cloud for complex ones
- Simple portraits: use local
- Complex scenes: use cloud

Alice: Using hybrid approach...

Local (free): 15 images analyzed
Cloud ($0.03): 5 complex scenes analyzed
Total saved: $0.015
```

## Model Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llava:latest | 4.7GB | Fast | Good | General use, quick tags |
| llava:13b | 8.0GB | Medium | Better | Detailed analysis |
| bakllava:latest | 4.7GB | Fast | Good | Alternative option |
| llava-phi3:latest | 3.8GB | Very Fast | Good | Speed priority |

## Use Cases

### 1. Initial Screening (Free)
Use local models to quickly tag and categorize:
```
You: Screen my latest downloads with local models
Alice: Analyzing 50 images locally...

Categories found:
- Portraits: 20 images
- Landscapes: 15 images  
- Abstract: 10 images
- UI/Screenshots: 5 images

No API costs incurred.
```

### 2. Bulk Tagging (Hybrid)
Combine local and cloud for comprehensive tagging:
```
You: Tag everything, use cloud only for artistic style analysis

Alice: Hybrid analysis plan:
- Local: Basic tags (objects, scenes, colors)
- Cloud: Style analysis for 10 best images

Estimated cost: $0.01 (vs $0.05 all-cloud)
```

### 3. Privacy-First Workflow
Keep sensitive content completely local:
```
You: Analyze personal photos locally only
Alice: Using local-only mode (no cloud fallback)

✓ All 25 images analyzed privately
✓ No data sent to external services
✓ Tags saved locally in metadata
```

## Advanced Configuration

### Provider Priority
```yaml
# settings.yaml
understanding:
  provider_priority:
    - ollama      # Try local first
    - google      # Then free tier
    - deepseek    # Then cheapest
    - anthropic   # Premium last
```

### Model Selection
```
You: Use llava:13b for portraits, llava:latest for others

Alice: Custom model selection configured:
- Portraits → llava:13b (better face details)
- Other → llava:latest (faster general use)
```

### Performance Tuning
```
You: Analyze in batches of 10 for memory efficiency

Alice: Batch processing configured:
- Batch size: 10 images
- Memory limit respected
- Progress shown per batch
```

## Troubleshooting

### Ollama Not Running
```
Error: Ollama not available

Solution:
1. Start Ollama: ollama serve
2. Check status: curl http://localhost:11434/api/tags
3. Retry analysis
```

### Model Not Found
```
Error: Model llava:latest not found

Solution:
ollama pull llava:latest
```

### Slow Performance
- Use smaller model (llava-phi3)
- Enable GPU acceleration
- Reduce batch size
- Upgrade to M2/M3 Mac or NVIDIA GPU

## Cost Comparison

| Workflow | Images | Local Only | Hybrid | Cloud Only |
|----------|--------|------------|--------|------------|
| Quick tags | 100 | $0.00 | $0.00 | $0.10 |
| Detailed | 100 | $0.00 | $0.02 | $0.20 |
| Artistic | 100 | N/A | $0.05 | $0.30 |

## Best Practices

1. **Start Local**: Always try local models first
2. **Selective Cloud**: Use cloud for complex artistic analysis
3. **Model Choice**: Pick model based on speed/quality needs
4. **Batch Smart**: Group similar images for efficiency
5. **Cache Results**: Reuse analysis for duplicates

## Integration with Workflows

### With Batch Optimization
```
You: Optimize analysis of 500 images using all available methods

Alice: Multi-optimization strategy:
1. Perceptual hashing: Group similar images
2. Local models: Analyze representatives 
3. Cloud selective: Complex images only

Results:
- 100 groups identified
- 80 analyzed locally (free)
- 20 analyzed with cloud ($0.02)
- Applied to all 500 images
- Total saved: $0.48
```

### With Quick Selection
```
You: Mark favorites while analyzing locally

Alice: Combined workflow:
1. Local analysis for tags
2. Present results
3. You mark favorites
4. Cloud analysis only for marked

Efficient and cost-effective!
```

## Future Features

- [ ] Custom fine-tuned models
- [ ] Multi-model consensus
- [ ] Specialized models (fashion, architecture)
- [ ] Offline model packs
- [ ] Edge device support