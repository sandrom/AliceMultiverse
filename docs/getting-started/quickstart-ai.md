# AI-Native Quick Start Guide

Get started with AliceMultiverse through AI assistants in just 5 minutes! This guide shows you how to use Alice through natural conversation instead of command-line interfaces.

## Prerequisites

- Python 3.12 or higher
- Claude Desktop or ChatGPT
- 500MB free disk space
- macOS, Linux, or Windows

## Installation

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/AliceMultiverse.git
cd AliceMultiverse
pip install -e .
```

### 2. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "alice": {
      "command": "alice",
      "args": ["mcp-server"]
    }
  }
}
```

### 3. Restart Claude Desktop

The Alice server will start automatically when Claude launches.

## Your First AI Conversation

### Basic Organization

Start a conversation with Claude:

```
You: Hi Claude, I have a folder full of AI-generated images in my Downloads folder. Can you help me organize them?

Claude: I'll help you organize your AI-generated images using Alice. Let me check what's in your Downloads folder and organize them by source and quality.

[Claude uses Alice to scan and organize your files]

Claude: I've organized 150 images from your Downloads folder:
- 80 Midjourney images (23 five-star, 45 four-star, 12 three-star)
- 45 Stable Diffusion images (15 five-star, 20 four-star, 10 three-star)
- 25 DALL-E images (8 five-star, 12 four-star, 5 three-star)

All files have been organized in ~/Pictures/AI-Organized/2024-03-15/
```

### Quality Assessment

```
You: Can you check the quality of the images in my latest project folder?

Claude: I'll assess the quality of images in your project folder using Alice's multi-stage pipeline.

[Claude runs quality assessment]

Claude: Quality assessment complete for 50 images:
- 5-star (Exceptional): 8 images (16%)
- 4-star (Great): 22 images (44%)
- 3-star (Good): 15 images (30%)
- 2-star (Fair): 4 images (8%)
- 1-star (Poor): 1 image (2%)

The best images have been identified and organized by quality rating.
```

### Smart Search

```
You: Find all my cyberpunk portraits from last week

Claude: I'll search for cyberpunk portraits from last week using Alice.

[Claude performs the search]

Claude: Found 15 cyberpunk portraits from last week:
- 8 from Midjourney (mostly neon-lit characters)
- 5 from Stable Diffusion XL (dark atmospheric portraits)
- 2 from DALL-E 3 (stylized cyberpunk faces)

Would you like me to show you the highest quality ones or organize them into a new collection?
```

## Common AI Workflows

### Continuous Monitoring

```
You: Can you watch my Downloads folder and organize new AI images as they arrive?

Claude: I'll set up Alice to monitor your Downloads folder continuously. Any new AI-generated images will be automatically organized by source and quality.
```

### Project-Based Organization

```
You: I'm working on a fantasy art project. Can you help me collect all relevant reference images?

Claude: I'll help you gather fantasy art references. Let me search through your organized images for fantasy-themed content and create a project folder for you.
```

### Batch Processing with Quality Filters

```
You: Process all images in my inbox but only keep the high-quality ones

Claude: I'll process your inbox images and filter for high quality only. This will help you focus on the best outputs from your AI generations.
```

## Understanding AI Responses

When Claude uses Alice, you'll see natural language summaries of:

- **Organization Results**: How many files were processed and where they went
- **Quality Distributions**: Star ratings and percentages
- **Source Detection**: Which AI tools generated your content
- **Search Results**: Matching assets with context
- **Cost Estimates**: For premium features like Claude vision analysis

## API Keys for Enhanced Features

Some features require API keys. You can set them up through conversation:

```
You: I want to use the advanced quality assessment features

Claude: To use advanced quality assessment, you'll need API keys for SightEngine and/or Claude vision. Would you like me to guide you through setting them up?

You: Yes, please help me set up the API keys

Claude: I'll help you configure your API keys securely. First, let me run the API key setup wizard...

[Claude runs: alice keys setup]
```

## Tips for AI Conversations

### Be Specific About Intent
- ✅ "Organize my AI images by quality and source"
- ✅ "Find all portraits with cyberpunk style from March"
- ❌ "Do something with my images"

### Provide Context
- ✅ "I'm working on a sci-fi project and need to find all my spaceship concepts"
- ✅ "Check the images I generated today for quality issues"
- ❌ "Find stuff"

### Ask for Explanations
- "What quality assessment methods are you using?"
- "How does Alice determine the AI source?"
- "What's the cost of running Claude vision on 100 images?"

### Use Natural Time References
- "Show me what I created yesterday"
- "Find images from last week's brainstorming session"
- "What did I generate in January?"

## Advanced AI Features

### Multi-Stage Pipelines

```
You: Use the most thorough quality assessment on my latest batch

Claude: I'll use the premium pipeline with BRISQUE, SightEngine, and Claude vision to thoroughly assess your latest batch. This will cost approximately $0.003 per image.
```

### Creative Memory

```
You: Remember this style for my cyberpunk project

Claude: I'll tag these images with your cyberpunk project reference. Alice will remember this style association for future searches and organizations.
```

### Workflow Automation

```
You: Every time I add images to my Downloads, organize them automatically

Claude: I'll help you set up an automated workflow that monitors your Downloads folder and organizes new AI-generated images by source and quality.
```

## What's Next?

- 🤖 [AI Conversation Examples](../user-guide/ai-conversations.md) - More conversation patterns
- 🔧 [Claude Desktop Setup](../integrations/claude-desktop.md) - Detailed configuration
- 📊 [Understanding Quality Metrics](../user-guide/pipeline-examples.md) - How assessment works
- 🎨 [Creative Workflows](../philosophy/creative-chaos.md) - Working with your creative process

## Troubleshooting

### Claude Can't Find Alice

```
You: Claude can't seem to access Alice

Solution: Make sure you've:
1. Installed Alice with `pip install -e .`
2. Added the configuration to claude_desktop_config.json
3. Restarted Claude Desktop
```

### Operations Seem Slow

```
You: Why is organizing taking so long?

Claude: First-time organization builds a metadata cache. Subsequent operations will be much faster. For large collections, I can process in batches to show progress.
```

### Quality Scores Seem Off

```
You: The quality ratings don't match my perception

Claude: Alice uses BRISQUE for technical quality, which may rate stylized art lower. Would you like me to:
1. Adjust the quality thresholds for your art style?
2. Use Claude vision for more subjective assessment?
3. Create custom quality criteria for your projects?
```

## Getting Help

When you need assistance:

```
You: I'm having trouble with Alice

Claude: I can help troubleshoot. Tell me:
1. What you were trying to do
2. What happened instead
3. Any error messages you saw

I'll help diagnose and fix the issue.
```

## The AI-Native Advantage

Using Alice through AI assistants provides:

- **Natural Language**: No need to remember command syntax
- **Contextual Help**: AI understands your creative goals
- **Smart Suggestions**: AI can recommend workflows
- **Error Translation**: Technical errors become friendly explanations
- **Workflow Memory**: AI remembers your preferences

Welcome to the future of creative workflow management! 🎨🤖