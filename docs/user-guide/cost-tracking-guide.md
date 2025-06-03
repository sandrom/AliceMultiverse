# Cost Tracking Guide

AliceMultiverse includes comprehensive cost tracking to help you manage API spending. This is crucial since AI API costs can add up quickly when processing large image collections.

## Overview

The cost tracking system provides:
1. **Cost Estimation** - Preview costs before operations
2. **Real-time Tracking** - Record actual costs as they occur
3. **Budget Management** - Set limits and get alerts
4. **Spending Reports** - Analyze costs by provider and time
5. **Provider Comparison** - Find the most cost-effective options

## Using Cost Features Through Claude

### Preview Costs Before Operations

```
Me: I have 500 new images to organize. What would it cost to analyze them?

Claude: I'll estimate the cost for analyzing 500 images.

[Claude uses estimate_cost tool]

The cost estimate for analyzing 500 images:
- **Total cost: $3.75** (likely)
- Range: $3.00 - $4.50

Breakdown by provider:
- Anthropic Claude: $1.25 (500 × $0.0025)
- OpenAI GPT-4V: $2.50 (500 × $0.005)
- Google Gemini: Free (within daily limit)

Would you like to:
1. Proceed with all providers ($3.75)
2. Use only free providers (Google)
3. Process a smaller batch first
4. Skip analysis and organize by metadata only
```

### Set Budget Limits

```
Me: Set a daily budget of $10 for API calls

Claude: I'll set your daily budget to $10.

[Claude uses set_budget tool]

✅ Daily budget set to $10.00
- Alert threshold: 80% ($8.00)
- You'll be warned when spending reaches $8.00
- Operations will be blocked at $10.00

Current daily spending: $2.45 (24.5% of budget)
```

### View Spending Report

```
Me: Show me my spending this month

Claude: I'll generate your spending report.

[Claude uses get_spending_report tool]

=== AliceMultiverse Cost Report ===

📊 Spending Summary:
  Daily: $2.45 / $10.00 (24.5%)
  Weekly: $15.32
  Monthly: $47.89
  Total: $152.34

🏆 Top Providers by Spending:
  openai: $89.45
  anthropic: $42.30
  midjourney: $15.20
  elevenlabs: $5.39

📂 Spending by Category:
  understanding: $131.75
  generation: $15.20
  audio: $5.39

⚠️ Budget Status:
  🟢 Daily: $7.55 remaining (24.5% used)
  🟡 Monthly: $52.11 remaining (47.9% used)

💡 Cost Optimization Tips:
  • Consider anthropic instead of openai (save ~50%)
  • Use free tiers: google, deepseek
```

### Cost-Aware Workflows

```
Me: I want to organize my images but I'm near my daily budget

Claude: I see you have $2.30 remaining in your daily budget. Let me help you organize efficiently.

[Claude uses estimate_cost tool]

Options within your budget:
1. **Organize without AI analysis** - $0 
   - Uses existing metadata only
   - Still sorts by date/source

2. **Use free providers only** - $0
   - Google Gemini (50 images free/day)
   - Processes most important images first

3. **Partial analysis** - $2.00
   - Analyze 200 most recent images
   - Skip the rest for today

Which approach would you prefer?
```

## Cost Tracking Details

### Pricing Models

The system understands different pricing models:

1. **Per Request** - Fixed cost per operation (e.g., DALL-E)
2. **Per Token** - Based on input/output tokens (e.g., GPT-4, Claude)
3. **Per Second** - Duration-based (e.g., video generation)
4. **Per Megapixel** - Resolution-based (e.g., upscaling)

### Free Tier Tracking

Many providers offer free tiers:
- **Google Gemini**: 50 requests/day free
- **DeepSeek**: Very low cost alternative
- **Local models**: No cost if you run them

The system tracks free tier usage automatically.

### Budget Alerts

Set budgets at different levels:
- **Daily**: Prevent overspending in one day
- **Weekly**: Track weekly patterns
- **Monthly**: Match credit card cycles
- **Total**: Hard limit for projects

### Cost Categories

Spending is categorized for analysis:
- **Understanding**: Image analysis and tagging
- **Generation**: Creating new images/videos
- **Enhancement**: Upscaling and editing
- **Audio**: Sound effects and music

## Best Practices

### 1. Always Preview Costs

```
Me: Analyze these 1000 images with detailed understanding

Claude: Let me check the cost first...

⚠️ Cost Warning: $25.00 for detailed analysis of 1000 images

This exceeds your daily budget ($10.00). Would you like to:
- Process in batches over several days
- Use basic analysis instead ($5.00)
- Use free providers only
```

### 2. Use Provider Comparison

```
Me: What's the cheapest way to analyze images?

Claude: Here's a cost comparison for image analysis:

1. **Google Gemini** - Free (50/day limit)
   - Good for general understanding
   - Supports up to 50 free daily

2. **DeepSeek** - $0.0002/image
   - Very cost effective
   - Good quality for basic analysis

3. **Anthropic Claude** - $0.0025/image
   - Excellent for nuanced understanding
   - Best style/mood detection

4. **OpenAI GPT-4V** - $0.005/image
   - Highest quality
   - Best for complex scenes
```

### 3. Batch Operations Wisely

```
Me: I have 5000 images to process

Claude: For 5000 images, I recommend:

1. **Test batch first** (50 images)
   - Cost: $0.25
   - Verify quality meets needs

2. **Process in daily batches**
   - 500 images/day = $2.50/day
   - Stays within budget
   - Complete in 10 days

3. **Prioritize important images**
   - Recent uploads first
   - Skip sorted-out folders
   - Focus on untagged items
```

### 4. Monitor Spending Trends

```
Me: Am I spending more than usual?

Claude: Looking at your spending trends:

📈 This Month vs Last Month:
- Total: $47.89 vs $35.20 (+36%)
- Daily average: $3.99 vs $2.93
- Provider shift: More OpenAI usage

Observations:
- Spending increased after enabling detailed analysis
- Consider switching back to basic analysis
- Your current pace will hit $120 this month
```

## Configuration

### Custom Pricing

If you have special pricing, update it:

```yaml
# ~/.alice/costs/custom_pricing.json
{
  "openai": {
    "category": "understanding",
    "per_token_input": 0.005,
    "per_token_output": 0.015,
    "notes": "Enterprise pricing"
  }
}
```

### Export Cost Data

Cost data is stored in:
- `~/.alice/costs/spending_YYYY-MM.jsonl` - Monthly spending logs
- `~/.alice/costs/budgets.json` - Budget configuration
- `~/.alice/costs/free_tier_usage.json` - Free tier tracking

## Common Scenarios

### Scenario 1: First-Time Setup

```
Me: I just got API keys. Help me set reasonable budgets.

Claude: Based on typical usage, I recommend:

For casual use (100-500 images/month):
- Daily budget: $5
- Monthly budget: $50

For heavy use (1000-5000 images/month):  
- Daily budget: $20
- Monthly budget: $200

I'll set conservative limits to start:
- Daily: $5 (alert at $4)
- Monthly: $50 (alert at $40)

You can always increase these later.
```

### Scenario 2: Budget Exceeded

```
Me: Organize my new downloads

Claude: ⚠️ Budget Alert: You've reached your daily limit ($10.00)

Today's spending:
- Morning: $6.50 (analyzed 1300 images)
- Afternoon: $3.50 (generated 35 images)

Options:
1. Wait until tomorrow (resets at midnight)
2. Increase daily budget
3. Organize without AI analysis (free)
4. Override for this operation only
```

### Scenario 3: Cost Optimization

```
Me: My costs are too high. How can I reduce them?

Claude: Based on your usage, here's how to reduce costs by ~60%:

1. **Switch primary provider** 
   - Current: OpenAI ($0.005/image)
   - Suggested: Anthropic ($0.0025/image)
   - Savings: $112/month

2. **Use free tiers**
   - Process first 50 daily with Google (free)
   - Savings: $30/month

3. **Reduce analysis frequency**
   - Only analyze new files, not moved ones
   - Skip already-tagged images
   - Savings: $45/month

Total potential savings: $187/month (62%)
```

## CLI Cost Commands (Debug Only)

For developers debugging cost tracking:

```bash
# Preview costs
alice cost estimate --operation understand --count 100

# View spending
alice cost report --period monthly

# Set budgets
alice cost budget --daily 10 --monthly 100

# Export cost data
alice cost export --format csv --output costs.csv
```

Remember: Normal users should interact through Claude Desktop, not the CLI.