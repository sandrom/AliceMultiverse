# API Cost Optimization Guide

Master the art of managing AI service costs while maximizing creative output with AliceMultiverse's built-in optimization strategies.

## Overview

AI services can be expensive. This guide shows you how to:
- Track costs in real-time
- Choose the most cost-effective providers
- Batch operations efficiently
- Use local models as fallbacks
- Set and enforce budget limits

## Understanding Provider Costs

### Cost Comparison Table (as of December 2024)

```
Provider         | Image Analysis | Per 1K Images | Best For
-----------------|----------------|---------------|------------------
OpenAI GPT-4V    | $0.01-0.03    | $10-30       | Detailed analysis
Claude Vision    | $0.003-0.015  | $3-15        | Style & mood
Google Gemini    | $0.0025       | $2.50        | Cost-effective
DeepSeek         | $0.001        | $1.00        | Budget option
Ollama (local)   | $0.00         | $0.00        | Free, slower
```

### Hidden Costs to Consider

1. **Token Usage**: Longer prompts = higher costs
2. **Retries**: Failed requests still cost money
3. **Resolution**: Higher res images = more tokens
4. **Multi-pass**: Some analyses require multiple calls

## Cost Tracking Setup

### 1. Enable Cost Tracking

```yaml
# settings.yaml
cost_tracking:
  enabled: true
  currency: USD
  alert_threshold: 10.00  # Alert when daily spend exceeds $10
  monthly_budget: 100.00  # Hard limit per month
  
  # Per-provider limits
  provider_limits:
    openai: 50.00
    anthropic: 30.00
    google: 20.00
```

### 2. View Current Costs

```python
# Through Claude MCP
"Show my AI costs for today"
"What's my monthly API spend?"
"Which provider is most expensive?"

# CLI commands
alice costs --today
alice costs --month
alice costs --by-provider
```

### 3. Cost Reports

```bash
# Generate detailed report
alice costs report --output costs_report.json

# Example output:
{
  "period": "2024-01",
  "total": 45.67,
  "by_provider": {
    "openai": 25.40,
    "anthropic": 15.27,
    "google": 5.00
  },
  "by_feature": {
    "understanding": 30.50,
    "generation": 10.17,
    "analysis": 5.00
  }
}
```

## Optimization Strategies

### 1. Smart Provider Selection

#### Tiered Approach
```python
# Configure provider tiers
understanding:
  provider_tiers:
    # Tier 1: Fast, cheap screening
    screening:
      provider: google
      confidence_threshold: 0.8
      
    # Tier 2: Detailed analysis
    detailed:
      provider: anthropic
      trigger: "confidence < 0.8"
      
    # Tier 3: Specialized tasks
    specialized:
      provider: openai
      trigger: "complex_scene"
```

#### Task-Specific Providers
```python
# Match providers to their strengths
"Use Google for basic tagging"
"Use Claude for artistic analysis"
"Use OpenAI for text extraction"
```

### 2. Batch Processing

#### Optimal Batch Sizes
```python
# Configure batching
understanding:
  batch_config:
    min_batch_size: 10      # Wait for at least 10 images
    max_batch_size: 100     # Process at most 100 at once
    timeout: 300            # Process after 5 minutes regardless
    
# Manual batch control
"Analyze these 50 images in one batch"
```

#### Batch Timing
```python
# Schedule batch processing
alice schedule_analysis \
  --time "02:00" \          # Run at 2 AM
  --batch-size 500 \        # Large batches
  --provider google         # Cheapest provider
```

### 3. Caching Strategy

#### Smart Cache Usage
```yaml
# Cache configuration
cache:
  understanding:
    ttl: 2592000  # 30 days
    max_size: 10GB
    
  # Never re-analyze unless forced
  skip_if_cached: true
  
  # Cache similar images
  similarity_threshold: 0.95
```

#### Cache Warming
```python
# Pre-analyze during off-peak
"Pre-analyze all unprocessed images overnight"

# Use cached results
"Show analysis for this image (use cache)"
```

### 4. Local Model Fallbacks

#### Ollama Integration
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull vision model
ollama pull llava

# Configure as fallback
alice config set understanding.fallback_provider ollama
```

#### Hybrid Approach
```python
# Use local for screening
understanding:
  hybrid_mode:
    # Local first pass
    screening:
      provider: ollama
      model: llava
      
    # Cloud for uncertain cases  
    verification:
      provider: google
      trigger: "local_confidence < 0.7"
```

### 5. Budget Enforcement

#### Hard Limits
```python
# Stop when budget exceeded
cost_tracking:
  enforcement:
    daily_hard_limit: 20.00
    action: "stop"  # or "warn" or "switch_provider"
    
# Automatic provider switching
alice config set cost_tracking.over_budget_provider ollama
```

#### Soft Warnings
```python
# Progressive warnings
cost_tracking:
  warnings:
    - threshold: 50%
      message: "Half of daily budget used"
    - threshold: 80%
      message: "Approaching daily limit"
    - threshold: 90%
      message: "Consider using local models"
```

## Practical Examples

### Example 1: Portfolio Processing

```python
# Large portfolio, mixed approach
workflow = {
  "1_initial_screen": {
    "provider": "ollama",
    "cost": "$0",
    "purpose": "Filter obvious rejects"
  },
  "2_quality_check": {
    "provider": "google", 
    "cost": "$2.50/1k",
    "purpose": "Technical quality"
  },
  "3_artistic_analysis": {
    "provider": "anthropic",
    "cost": "$10/1k",
    "purpose": "Best 100 images only"
  }
}

# Total cost: ~$3 vs $30 for all-Claude approach
```

### Example 2: Daily Imports

```python
# Optimize daily workflow
daily_import_config = {
  "morning": {
    "provider": "google",
    "batch_size": 50,
    "estimated_cost": "$0.125"
  },
  "afternoon": {
    "provider": "cached_only",
    "cost": "$0"
  },
  "evening_review": {
    "provider": "anthropic",
    "only_favorites": true,
    "estimated_cost": "$0.50"
  }
}
```

### Example 3: Event Coverage

```python
# High-volume event optimization
event_optimization = {
  "during_event": {
    "provider": "none",  # Just organize
    "cost": "$0"
  },
  "post_event_screen": {
    "provider": "ollama",  # Local, fast
    "batch_size": 500,
    "cost": "$0"
  },
  "client_selects": {
    "provider": "openai",  # Best quality
    "count": 50,
    "cost": "$1.50"
  }
}
```

## Advanced Cost Optimization

### 1. Prompt Engineering

```python
# Shorter prompts = lower costs
expensive_prompt = """
Analyze this image in great detail. Describe every element,
color, mood, style, composition, technical aspects, and provide
suggestions for improvement with specific recommendations.
"""  # ~100 tokens

optimized_prompt = """
List: main subject, style, mood, 3 colors, quality score
"""  # ~15 tokens

# 85% cost reduction, similar results
```

### 2. Resolution Optimization

```python
# Reduce image size before analysis
understanding:
  preprocessing:
    max_dimension: 1024  # Resize large images
    jpeg_quality: 85     # Compress slightly
    
# Saves 50-70% on token costs
```

### 3. Selective Analysis

```python
# Only analyze what matters
selective_rules:
  skip_if:
    - "already_tagged"
    - "quality_score < 60"
    - "duplicate_of_analyzed"
    
  priority_for:
    - "five_star_rated"
    - "client_selects"
    - "hero_shots"
```

### 4. Provider Arbitrage

```python
# Use price differences
arbitrage_strategy:
  # New providers often cheaper
  experimental:
    provider: "new_provider"
    test_percentage: 10
    
  # Regional pricing
  regional:
    us_east: "google"
    europe: "anthropic"
    asia: "deepseek"
```

## Monitoring and Alerts

### Real-time Monitoring

```python
# Enable cost dashboard
alice costs monitor --dashboard

# Displays:
# - Current spend rate
# - Provider distribution  
# - Projection to end of day
# - Budget remaining
```

### Alert Configuration

```yaml
# alerts.yaml
cost_alerts:
  - name: "Unusual spike"
    condition: "hourly_spend > 5 * average_hourly"
    action: "email"
    
  - name: "Provider down"
    condition: "error_rate > 50%"
    action: "switch_provider"
    
  - name: "Budget warning"
    condition: "daily_spend > 0.8 * daily_budget"
    action: "notify"
```

### Cost Analytics

```python
# Analyze spending patterns
"Show cost trends this month"
"Which features cost the most?"
"Compare provider efficiency"

# Optimize based on data
"Suggest cost optimizations based on my usage"
```

## Quick Reference

### Cost Reduction Checklist

- [ ] Enable caching (save 90%+ on re-analysis)
- [ ] Use batch processing (save 20-30%)
- [ ] Implement provider tiers (save 50-70%)
- [ ] Optimize prompts (save 60-80%)
- [ ] Reduce image resolution (save 40-60%)
- [ ] Schedule off-peak processing (save 10-20%)
- [ ] Use local models for screening (save 80-90%)

### Budget Planning

```python
# Monthly budget calculator
images_per_month = 5000
analysis_percentage = 20  # Analyze 20%

# Costs by strategy
strategies = {
  "premium": 5000 * 0.20 * 0.03,     # $30
  "balanced": 5000 * 0.20 * 0.005,   # $5
  "budget": 5000 * 0.20 * 0.001,     # $1
  "hybrid": 5000 * 0.05 * 0.01,      # $2.50
}
```

## Troubleshooting

### High Costs Issues

**Problem**: Costs exceeding budget
- Check for analysis loops
- Verify cache is working
- Review provider selection
- Check image resolutions

**Problem**: Slow batch processing
- Increase batch sizes
- Use async processing
- Enable parallel requests
- Check rate limits

**Problem**: Provider errors costing money
- Implement retry limits
- Add circuit breakers
- Monitor error rates
- Have fallback providers

## Best Practices

1. **Start Conservative**
   - Begin with strict limits
   - Gradually increase as needed
   - Monitor patterns first

2. **Measure Everything**
   - Track cost per feature
   - Monitor provider efficiency
   - Analyze usage patterns

3. **Automate Optimization**
   - Let system choose providers
   - Auto-switch on budget limits
   - Schedule heavy processing

4. **Regular Reviews**
   - Weekly cost analysis
   - Monthly optimization
   - Quarterly strategy review

## Next Steps

1. Set up cost tracking in settings.yaml
2. Configure provider tiers for your workflow
3. Enable caching and batch processing
4. Monitor first week's costs
5. Adjust strategies based on data

## Additional Resources

- [Understanding System Guide](./local-vision-models-guide.md) - Local model setup
- [Batch Analysis Guide](./batch-analysis-optimization.md) - Detailed batching
- [Provider Comparison](./provider-comparison.md) - Detailed provider analysis

---

**Remember**: The goal isn't to minimize costs at all expense—it's to maximize value per dollar spent. Sometimes paying more for better analysis on key images is worth it.