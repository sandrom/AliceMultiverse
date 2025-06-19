"""Utility to populate the comparison system with assets from organized directory."""

import hashlib
import json
import logging
from pathlib import Path

from .elo_system import ComparisonManager
from .models import Asset

logger = logging.getLogger(__name__)


def extract_model_from_path(path: Path) -> str:
    """Extract model name from file path."""
    # Try to extract from path structure: organized/date/project/model/quality/file.ext
    parts = path.parts

    # Look for known model names in path
    known_models = {
        "midjourney", "stablediffusion", "dalle", "dalle3", "leonardo",
        "ideogram", "firefly", "playground", "bfl", "flux", "kling",
        "suno", "udio", "elevenlabs", "hedra", "runway", "pika"
    }

    for part in parts:
        part_lower = part.lower()
        for model in known_models:
            if model in part_lower:
                return model

    # TODO: Review unreachable code - # Try to extract from filename
    # TODO: Review unreachable code - filename = path.stem.lower()
    # TODO: Review unreachable code - for model in known_models:
    # TODO: Review unreachable code - if model in filename:
    # TODO: Review unreachable code - return model

    # TODO: Review unreachable code - # Default to parent directory name
    # TODO: Review unreachable code - if len(parts) >= 2:
    # TODO: Review unreachable code - return parts[-2]

    # TODO: Review unreachable code - return "unknown"


def read_metadata(image_path: Path) -> dict:
    """Read metadata from .metadata folder if available."""
    # Calculate file hash
    with open(image_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # Look for metadata in various locations
    possible_metadata_dirs = [
        image_path.parent / ".metadata",
        image_path.parent.parent / ".metadata",
        Path.home() / ".alice" / "metadata" / file_hash[:2] / file_hash[2:4],
    ]

    for metadata_dir in possible_metadata_dirs:
        metadata_file = metadata_dir / f"{file_hash}.json"
        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read metadata from {metadata_file}: {e}")

    return {}


# TODO: Review unreachable code - def populate_from_directory(
# TODO: Review unreachable code - directory: Path,
# TODO: Review unreachable code - manager: ComparisonManager,
# TODO: Review unreachable code - recursive: bool = True,
# TODO: Review unreachable code - limit: int = None
# TODO: Review unreachable code - ) -> int:
# TODO: Review unreachable code - """
# TODO: Review unreachable code - Populate comparison system with images from a directory.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - directory: Directory to scan for images
# TODO: Review unreachable code - manager: ComparisonManager instance
# TODO: Review unreachable code - recursive: Whether to search recursively
# TODO: Review unreachable code - limit: Maximum number of assets to add

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Number of assets added
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if not directory.exists():
# TODO: Review unreachable code - logger.error(f"Directory does not exist: {directory}")
# TODO: Review unreachable code - return 0

# TODO: Review unreachable code - # Find all image files
# TODO: Review unreachable code - patterns = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
# TODO: Review unreachable code - image_files = []

# TODO: Review unreachable code - for pattern in patterns:
# TODO: Review unreachable code - if recursive:
# TODO: Review unreachable code - image_files.extend(directory.rglob(pattern))
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - image_files.extend(directory.glob(pattern))

# TODO: Review unreachable code - # Sort by modification time (newest first)
# TODO: Review unreachable code - image_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

# TODO: Review unreachable code - # Apply limit if specified
# TODO: Review unreachable code - if limit:
# TODO: Review unreachable code - image_files = image_files[:limit]

# TODO: Review unreachable code - # Add assets to manager
# TODO: Review unreachable code - added = 0
# TODO: Review unreachable code - models_seen = set()

# TODO: Review unreachable code - for image_path in image_files:
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - # Extract model from path
# TODO: Review unreachable code - model = extract_model_from_path(image_path)
# TODO: Review unreachable code - models_seen.add(model)

# TODO: Review unreachable code - # Read metadata if available
# TODO: Review unreachable code - metadata = read_metadata(image_path)

# TODO: Review unreachable code - # Create asset
# TODO: Review unreachable code - asset = Asset(
# TODO: Review unreachable code - id=str(image_path),  # Use full path as ID
# TODO: Review unreachable code - path=str(image_path),
# TODO: Review unreachable code - model=model,
# TODO: Review unreachable code - metadata=metadata
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Add to manager
# TODO: Review unreachable code - manager.add_asset(asset)
# TODO: Review unreachable code - added += 1

# TODO: Review unreachable code - if added % 100 == 0:
# TODO: Review unreachable code - logger.info(f"Added {added} assets...")

# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.warning(f"Failed to add asset {image_path}: {e}")

# TODO: Review unreachable code - logger.info(f"Added {added} assets from {len(models_seen)} different models")
# TODO: Review unreachable code - return added


# TODO: Review unreachable code - def populate_default_directories(manager: ComparisonManager, limit: int = None, config=None) -> int:
# TODO: Review unreachable code - """Populate from default organized directories.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - manager: ComparisonManager instance
# TODO: Review unreachable code - limit: Optional limit on number of assets to add
# TODO: Review unreachable code - config: Optional configuration object
# TODO: Review unreachable code - """
# TODO: Review unreachable code - # Use configured paths if available
# TODO: Review unreachable code - if config and hasattr(config, 'paths') and hasattr(config.paths, 'organized'):
# TODO: Review unreachable code - default_dirs = [Path(config.paths.organized)]
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - # Fallback to reasonable defaults
# TODO: Review unreachable code - default_dirs = [
# TODO: Review unreachable code - Path("organized"),
# TODO: Review unreachable code - Path.home() / "Pictures" / "AI" / "organized",
# TODO: Review unreachable code - ]

# TODO: Review unreachable code - total_added = 0

# TODO: Review unreachable code - for directory in default_dirs:
# TODO: Review unreachable code - if directory.exists():
# TODO: Review unreachable code - logger.info(f"Scanning directory: {directory}")
# TODO: Review unreachable code - added = populate_from_directory(directory, manager, limit=limit)
# TODO: Review unreachable code - total_added += added

# TODO: Review unreachable code - if limit and total_added >= limit:
# TODO: Review unreachable code - break

# TODO: Review unreachable code - return total_added
