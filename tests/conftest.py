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
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from alicemultiverse.core.types import MediaType, QualityRating
from alicemultiverse.database.models import Base


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_config(temp_dir: Path) -> dict[str, Any]:
    """Create a sample configuration dictionary."""
    return {
        "paths": {"inbox": str(temp_dir / "inbox"), "organized": str(temp_dir / "organized")},
        "processing": {
            "copy_mode": True,
            "quality": False,
            "watch": False,
            "watch_interval": 5,
            "force_reindex": False,
            "dry_run": False,
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
        "ai_generators": {
            "image": ["stablediffusion", "midjourney", "dalle", "comfyui", "flux"],
            "video": ["runway", "kling", "pika", "stable-video", "animatediff"],
        },
        "metadata": {"cache_version": "3.0.0", "folder_name": ".metadata"},
        "file_types": {
            "image_extensions": [".jpg", ".jpeg", ".png"],
            "video_extensions": [".mp4", ".mov"],
        },
        "pipeline": {
            "mode": None,
            "stages": [],
            "configurations": {
                "basic": {"stages": ["brisque"]},
                "standard": {"stages": ["brisque", "sightengine"]},
                "premium": {"stages": ["brisque", "sightengine", "claude"]},
            },
            "thresholds": {
                "brisque_min_stars": 3,
                "sightengine_min_stars": 4,
                "sightengine_min_quality": 0.7,
            },
            "scoring_weights": {
                "standard": {"brisque": 0.6, "sightengine": 0.4},
                "premium": {"brisque": 0.4, "sightengine": 0.3, "claude": 0.3},
            },
            "star_thresholds": {"5_star": 0.80, "4_star": 0.65},
            "cost_limits": {"sightengine": 5.0, "claude": 10.0, "total": 20.0},
        },
    }


@pytest.fixture
def omega_config(sample_config: dict[str, Any]) -> OmegaConf:
    """Create an OmegaConf configuration object."""
    return OmegaConf.create(sample_config)


@pytest.fixture
def sample_media_files(temp_dir: Path) -> dict[str, Path]:
    """Create sample media files for testing."""
    inbox = temp_dir / "inbox"
    inbox.mkdir(exist_ok=True)

    # Create test project structure
    project_dir = inbox / "test-project"
    project_dir.mkdir(exist_ok=True)

    files = {}

    # Create test images
    for i in range(3):
        img_path = project_dir / f"test_image_{i}.png"
        img_path.write_bytes(b"fake png data")
        files[f"image_{i}"] = img_path

    # Create test video
    video_path = project_dir / "test_video.mp4"
    video_path.write_bytes(b"fake mp4 data")
    files["video"] = video_path

    return files


@pytest.fixture
def mock_metadata_cache() -> Mock:
    """Create a mock metadata cache."""
    cache = Mock()
    cache.get_metadata.return_value = None
    cache.set_metadata.return_value = None
    cache.has_metadata.return_value = False
    return cache


@pytest.fixture
def mock_brisque() -> Mock:
    """Create a mock BRISQUE quality assessor."""
    brisque = Mock()
    brisque.score.return_value = 30.0  # Good quality score
    return brisque


@pytest.fixture
def mock_api_manager() -> Mock:
    """Create a mock API key manager."""
    manager = Mock()
    manager.get_api_key.return_value = "test-api-key"
    manager.get_sightengine_credentials.return_value = "user,secret"
    return manager


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Store original environment
    original_env = os.environ.copy()

    # Remove any test-related env vars
    test_env_vars = [
        "SIGHTENGINE_API_USER",
        "SIGHTENGINE_API_SECRET",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "DATABASE_URL",
        "ALICEMULTIVERSE_DATABASE_URL",
    ]

    for var in test_env_vars:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Database test fixtures
# For tests only, we use SQLite in-memory for speed and isolation
# Production always uses PostgreSQL

@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine using SQLite in-memory."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Required for SQLite in-memory with multiple connections
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing command-line interface."""
    from click.testing import CliRunner

    return CliRunner()


# Parametrized fixtures for different test scenarios
@pytest.fixture(params=[MediaType.IMAGE, MediaType.VIDEO, MediaType.UNKNOWN])
def media_type(request):
    """Parametrized fixture for media types."""
    return request.param


@pytest.fixture(
    params=[
        QualityRating.FIVE_STAR,
        QualityRating.FOUR_STAR,
        QualityRating.THREE_STAR,
        QualityRating.TWO_STAR,
        QualityRating.ONE_STAR,
        QualityRating.UNRATED,
    ]
)
def quality_rating(request):
    """Parametrized fixture for quality ratings."""
    return request.param


# Markers for test organization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.requires_ffmpeg = pytest.mark.requires_ffmpeg
