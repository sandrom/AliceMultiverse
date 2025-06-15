# Installation Guide

This guide provides detailed installation instructions for AliceMultiverse across different platforms and configurations.

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Memory**: 2GB RAM
- **Storage**: 500MB for installation + space for media
- **OS**: macOS 10.14+, Ubuntu 18.04+, Windows 10+

### Recommended Requirements
- **Python**: 3.10 or higher
- **Memory**: 8GB RAM
- **Storage**: SSD with 10GB+ free space
- **CPU**: Multi-core for faster processing

## Installation Methods

### Method 1: From Source (Recommended)

#### 1. Install Python

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Or download from python.org
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/) and ensure "Add to PATH" is checked.

#### 2. Clone Repository

```bash
git clone https://github.com/yourusername/AliceMultiverse.git
cd AliceMultiverse
```

#### 3. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Windows PowerShell:
venv\Scripts\Activate.ps1
```

#### 4. Install AliceMultiverse

```bash
# Upgrade pip first
pip install --upgrade pip

# Install in editable mode (recommended for development)
pip install -e .

# Or install with optional features
pip install -e ".[understanding]"  # With AI understanding system
pip install -e ".[full]"           # All features
pip install -e ".[dev]"            # Development dependencies
```

### Method 2: Using pip (Coming Soon)

```bash
pip install alicemultiverse
```

### Method 3: Using Docker

```bash
# Pull the image
docker pull alicemultiverse/alicemultiverse:latest

# Run with volume mount
docker run -v ~/inbox:/inbox -v ~/organized:/organized alicemultiverse
```

## Platform-Specific Setup

### macOS

#### Install System Dependencies

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install ffmpeg  # For video metadata
```

#### Keychain Access Setup

For secure API key storage:
1. Open Keychain Access
2. File → New Keychain Item
3. Keychain Item Name: `AliceMultiverse`
4. Account Name: Your API service (e.g., `sightengine`)
5. Password: Your API key

### Ubuntu/Debian

#### Install System Dependencies

```bash
# Update package list
sudo apt update

# Install system packages
sudo apt install -y \
    ffmpeg \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0
```

#### Install Python Dependencies

```bash
# Some packages need system libraries
sudo apt install -y \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev
```

### Windows

#### Install System Dependencies

1. **FFmpeg**:
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extract to `C:\ffmpeg`
   - Add `C:\ffmpeg\bin` to PATH

2. **Visual C++ Redistributable**:
   - Download from [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - Required for some Python packages

#### PowerShell Execution Policy

```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Understanding System Setup

### AI Provider Installation

AliceMultiverse uses AI providers for semantic understanding of images:

#### Core Providers
```bash
# Install AI provider SDKs
pip install openai          # OpenAI Vision
pip install anthropic       # Claude Vision
pip install google-generativeai  # Google AI
```

### Verify Understanding System

```python
# Test understanding availability
from alicemultiverse.understanding import UnderstandingManager

manager = UnderstandingManager()
if manager.available_providers:
    print(f"✓ Understanding available: {manager.available_providers}")
else:
    print("✗ No AI providers configured")
```

**Note**: The quality assessment system has been replaced with the AI understanding system which provides semantic tagging instead of quality ratings.

## API Services Setup

### SightEngine

1. Sign up at [sightengine.com](https://sightengine.com)
2. Get your API credentials
3. Set up keys:

```bash
# Using interactive setup
alice keys setup
# Follow prompts to enter SightEngine credentials

# Or use environment variables
export SIGHTENGINE_API_USER=your_user
export SIGHTENGINE_API_SECRET=your_secret
```

### Claude (Anthropic)

1. Get API key from [console.anthropic.com](https://console.anthropic.com)
2. Set up key:

```bash
# Using interactive setup
alice keys setup
# Follow prompts to enter Anthropic API key

# Or use environment variable
export ANTHROPIC_API_KEY=your_api_key
```

## Configuration

### Create Configuration File

```bash
# Copy default configuration
cp settings.yaml.example settings.yaml

# Edit with your preferences
nano settings.yaml  # or your preferred editor
```

### Essential Configuration

```yaml
paths:
  inbox: "~/Pictures/AI/inbox"
  organized: "~/Pictures/AI/organized"

processing:
  copy_mode: true  # Set to false to move files
  quality: false   # Set to true for quality assessment
  
quality:
  thresholds:
    5_star: {min: 0, max: 25}
    4_star: {min: 25, max: 45}
    3_star: {min: 45, max: 65}
    2_star: {min: 65, max: 80}
    1_star: {min: 80, max: 100}
```

## Verification

### 1. Check Installation

```bash
# Check CLI is available
alice --version

# Check dependencies
alice --check-deps
```

Expected output:
```
✓ ffprobe found (video metadata extraction)
✓ BRISQUE available (quality assessment)
AliceMultiverse v1.0.1 - All systems ready!
```

### 2. Run Test Organization

```bash
# Create test structure
mkdir -p test_inbox/test_project
echo "test" > test_inbox/test_project/test_image.jpg

# Run organization
alice organize test_inbox --output test_output --dry-run
```

### 3. Check Python API

```python
from alicemultiverse import MediaOrganizer
from alicemultiverse.core.config import load_config

config = load_config()
organizer = MediaOrganizer(config)
print("✓ Python API working")
```

## Troubleshooting

### Common Installation Issues

#### "pip: command not found"
```bash
# Ubuntu/Debian
sudo apt install python3-pip

# macOS
python -m ensurepip --upgrade
```

#### "error: Microsoft Visual C++ 14.0 is required"
- Windows: Install Visual Studio Build Tools
- Or use pre-compiled wheels: `pip install --only-binary :all: <package>`

#### "ImportError: libGL.so.1"
```bash
# Ubuntu/Debian
sudo apt install libgl1-mesa-glx

# In Docker
apt-get update && apt-get install -y libgl1-mesa-glx
```

#### Permission Errors
```bash
# Use --user flag
pip install --user -r requirements.txt

# Or fix permissions
sudo chown -R $USER:$USER ~/.cache/pip
```

### Dependency Conflicts

If you encounter dependency conflicts:

```bash
# Create fresh environment
deactivate
rm -rf venv
python -m venv venv --clear
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Platform-Specific Issues

**macOS Apple Silicon (M1/M2)**:
```bash
# Some packages need special handling
pip install --no-binary :all: pillow
```

**WSL2 (Windows Subsystem for Linux)**:
```bash
# GUI dependencies
sudo apt install python3-tk
```

## Advanced Installation

### Development Setup

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

### GPU Acceleration (Future)

For future GPU-accelerated quality assessment:

```bash
# NVIDIA GPU
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Apple Silicon
pip install torch torchvision
```

## Next Steps

- ✅ Installation complete!
- 📖 Continue to [Quick Start](quickstart.md)
- ⚙️ [Configure your settings](configuration.md)
- 🔑 [Set up API keys](../user-guide/api-keys.md)