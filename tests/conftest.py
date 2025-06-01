"""Shared pytest fixtures and configuration."""

import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from omegaconf import OmegaConf

from alicemultiverse.core.types import MediaType, QualityRating


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir: Path) -> OmegaConf:
    """Create a test configuration."""
    config = {
        "paths": {
            "inbox": str(temp_dir / "inbox"),
            "organized": str(temp_dir / "organized"),
            "metadata_dir": ".metadata",
        },
        "processing": {
            "move": False,
            "force": False,
            "dry_run": False,
            "watch": False,
            "quality": False,
        },
        "pipeline": {
            "mode": "basic",
            "stages": ["brisque"],
            "cost_limit": None,
            "dry_run": False,
            "resume": False,
        },
        "quality": {
            "thresholds": {
                "5_star": {"min": 0, "max": 25},
                "4_star": {"min": 25, "max": 45},
                "3_star": {"min": 45, "max": 65},
                "2_star": {"min": 65, "max": 80},
                "1_star": {"min": 80, "max": 100},
            }
        },
        "cache": {
            "enable_duckdb": True,
            "duckdb_path": str(temp_dir / "cache.db"),
            "redis": {
                "enabled": False,
                "host": "localhost",
                "port": 6379,
            }
        },
        "enhanced_metadata": True,
    }
    return OmegaConf.create(config)


@pytest.fixture
def mock_redis() -> Mock:
    """Create a mock Redis client."""
    redis_mock = Mock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.exists.return_value = False
    redis_mock.expire.return_value = True
    return redis_mock


@pytest.fixture
def sample_image_path(temp_dir: Path) -> Path:
    """Create a sample image file."""
    image_path = temp_dir / "test_image.png"
    # Create a minimal PNG file
    png_header = b'\x89PNG\r\n\x1a\n'
    png_data = png_header + b'\x00' * 100  # Minimal data
    image_path.write_bytes(png_data)
    return image_path


@pytest.fixture
def sample_video_path(temp_dir: Path) -> Path:
    """Create a sample video file."""
    video_path = temp_dir / "test_video.mp4"
    # Create a minimal MP4 file
    mp4_header = b'\x00\x00\x00\x20ftypisom'
    mp4_data = mp4_header + b'\x00' * 100  # Minimal data
    video_path.write_bytes(mp4_data)
    return video_path


@pytest.fixture
def sample_metadata() -> dict[str, Any]:
    """Create sample metadata for testing."""
    return {
        "content_hash": "test_hash_123",
        "file_path": "/test/path/image.png",
        "media_type": MediaType.IMAGE.value,
        "file_size": 1024,
        "width": 1920,
        "height": 1080,
        "source_type": "midjourney",
        "prompt": "a beautiful landscape",
        "model": "v6",
        "tags": ["landscape", "nature", "scenic"],
        "custom_tags": ["favorite", "portfolio"],
        "quality_stars": 5,
        "created_at": "2024-01-01T00:00:00",
        "modified_at": "2024-01-01T00:00:00",
    }


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up test environment variables."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    # Disable external API calls
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SIGHTENGINE_API_USER", "test-user")
    monkeypatch.setenv("SIGHTENGINE_API_SECRET", "test-secret")