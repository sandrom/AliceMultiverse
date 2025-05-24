# AliceMultiverse - AI Media Organizer

<div align="center">

**Automatically organize your AI-generated images by source, date, and quality**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

## 🎯 What does it do?

AliceMultiverse automatically organizes your AI-generated images and videos into a clean folder structure, detecting which AI tool created them and optionally assessing their quality.

### Before AliceMultiverse:
```
Downloads/
├── 00123.png                    # What AI made this?
├── _9f7d8a6b-4c2e-11ee.png     # Midjourney? 
├── ComfyUI_00456_.png           # Another tool...
├── dalle-3-image.jpg            # Mixed together
└── 1234567890.webp              # No organization
```

### After AliceMultiverse:
```
organized/
├── 2024-03-15/
│   ├── project-cyberpunk/
│   │   ├── midjourney/
│   │   │   ├── 5-star/         # Best quality
│   │   │   ├── 4-star/         # Good quality
│   │   │   └── 3-star/         # Average
│   │   └── dalle/
│   │       └── 5-star/
│   └── project-nature/
│       └── stablediffusion/
└── 2024-03-16/
    └── project-portraits/
```

## 🚀 Quick Start

### 1. Install
```bash
pip install -e .
```

### 2. Run
```bash
# Basic organization
alice

# With quality assessment (sorts into star ratings)
alice --quality

# Watch for new files continuously
alice --watch
```

That's it! Your AI images are now organized.

## ✨ Features

- **🤖 AI Detection** - Recognizes images from Midjourney, DALL-E, Stable Diffusion, and 12+ other AI tools
- **📁 Smart Organization** - Groups by date, project, and AI source automatically
- **⭐ Quality Assessment** - Optional sorting into 5-star rating folders
- **🔄 Watch Mode** - Continuously monitors for new images
- **💾 Fast Processing** - Intelligent caching for large collections

## 📋 Configuration

AliceMultiverse works out of the box with sensible defaults. To customize:

### Option 1: Command Line
```bash
alice --inbox ~/Downloads/AI --organized ~/Pictures/AI-Sorted
```

### Option 2: Settings File
Create `settings.yaml`:
```yaml
paths:
  inbox: ~/Downloads/AI-Images
  organized: ~/Pictures/AI-Organized

processing:
  quality: true        # Enable quality assessment
  watch: false         # Enable watch mode
```

### Option 3: Environment Variables
See `.env.example` for all options.

## 🎨 Quality Assessment

Enable quality sorting to automatically organize images by visual quality:

```bash
alice --quality
```

This creates star-rating folders (5-star, 4-star, etc.) based on technical image quality.

### Advanced Quality Options

For more accurate assessments, you can enable additional quality checks:

```bash
# Technical quality check (requires SightEngine API key)
alice --pipeline standard

# Full artistic evaluation (requires Anthropic API key)  
alice --pipeline premium
```

See [API Setup Guide](docs/development/API_KEYS.md) for details.

## 📖 Documentation

- [Installation Guide](docs/getting-started/installation.md)
- [Configuration Options](docs/getting-started/configuration.md)
- [API Documentation](docs/api/reference/)

### For Developers
- [Architecture Overview](docs/development/ARCHITECTURE.md)
- [Database Features](docs/development/README_DATABASE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Future Roadmap](docs/development/ROADMAP.md)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
<strong>AliceMultiverse</strong> - Because your AI art deserves better than a messy Downloads folder
</div>