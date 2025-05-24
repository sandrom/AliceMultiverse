# AliceMultiverse Quick Reference

## What is this?
**AliceMultiverse** = AI Media Organizer that sorts your AI-generated images automatically

## Installation (2 minutes)
```bash
# Clone the repo
git clone https://github.com/yourusername/AliceMultiverse.git
cd AliceMultiverse

# Install
pip install -e .
```

## Basic Usage (30 seconds)
```bash
# Organize AI images from Downloads to Pictures
alice

# That's it! Check your organized folder
```

## Common Commands
```bash
alice --quality        # Sort by quality (5-star system)
alice --watch         # Keep running, organize new files
alice --dry-run       # Preview without moving files
alice --help          # See all options
```

## Default Folders
- **Input**: `~/Downloads` (where your AI images are)
- **Output**: `~/Pictures/AI-Organized` (where they go)

Change with: `alice --inbox ~/YourFolder --organized ~/OutputFolder`

## What It Organizes
✅ Images: PNG, JPG, WebP, HEIC
✅ Videos: MP4, MOV
✅ AI Tools: Midjourney, DALL-E, Stable Diffusion, + 12 more

## Folder Structure Created
```
organized/
├── 2024-03-15/              # Date
│   └── project-name/        # Project
│       └── midjourney/      # AI tool
│           ├── image1.png
│           └── image2.jpg
```

## Problems?
- Not organizing? Check file is from supported AI tool
- Wrong folders? Edit `settings.yaml` or use command line flags
- Need API keys? Only for advanced quality features (optional)

## Next Steps
- Enable quality sorting: `alice --quality`
- Read full docs: See [README.md](README.md)
- Configure: Copy `.env.example` to `.env`

---
**Remember**: AliceMultiverse = Your AI art's new best friend 🎨