"""Helper to create test images."""

from pathlib import Path
from PIL import Image


def create_test_png(path: Path):
    """Create a minimal valid PNG file."""
    img = Image.new('RGB', (1, 1), color='red')
    img.save(path, 'PNG')


def create_test_jpeg(path: Path):
    """Create a minimal valid JPEG file."""
    img = Image.new('RGB', (1, 1), color='blue')
    img.save(path, 'JPEG')