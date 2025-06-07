"""Utility to populate the comparison system with assets from organized directory."""

import logging
from pathlib import Path
from typing import Dict
import hashlib
import json

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
    
    # Try to extract from filename
    filename = path.stem.lower()
    for model in known_models:
        if model in filename:
            return model
    
    # Default to parent directory name
    if len(parts) >= 2:
        return parts[-2]
    
    return "unknown"


def read_metadata(image_path: Path) -> Dict:
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


def populate_from_directory(
    directory: Path, 
    manager: ComparisonManager,
    recursive: bool = True,
    limit: int = None
) -> int:
    """
    Populate comparison system with images from a directory.
    
    Args:
        directory: Directory to scan for images
        manager: ComparisonManager instance
        recursive: Whether to search recursively
        limit: Maximum number of assets to add
        
    Returns:
        Number of assets added
    """
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        return 0
    
    # Find all image files
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
    image_files = []
    
    for pattern in patterns:
        if recursive:
            image_files.extend(directory.rglob(pattern))
        else:
            image_files.extend(directory.glob(pattern))
    
    # Sort by modification time (newest first)
    image_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Apply limit if specified
    if limit:
        image_files = image_files[:limit]
    
    # Add assets to manager
    added = 0
    models_seen = set()
    
    for image_path in image_files:
        try:
            # Extract model from path
            model = extract_model_from_path(image_path)
            models_seen.add(model)
            
            # Read metadata if available
            metadata = read_metadata(image_path)
            
            # Create asset
            asset = Asset(
                id=str(image_path),  # Use full path as ID
                path=str(image_path),
                model=model,
                metadata=metadata
            )
            
            # Add to manager
            manager.add_asset(asset)
            added += 1
            
            if added % 100 == 0:
                logger.info(f"Added {added} assets...")
                
        except Exception as e:
            logger.warning(f"Failed to add asset {image_path}: {e}")
    
    logger.info(f"Added {added} assets from {len(models_seen)} different models")
    return added


def populate_default_directories(manager: ComparisonManager, limit: int = None, config=None) -> int:
    """Populate from default organized directories.
    
    Args:
        manager: ComparisonManager instance
        limit: Optional limit on number of assets to add
        config: Optional configuration object
    """
    # Use configured paths if available
    if config and hasattr(config, 'paths') and hasattr(config.paths, 'organized'):
        default_dirs = [Path(config.paths.organized)]
    else:
        # Fallback to reasonable defaults
        default_dirs = [
            Path("organized"),
            Path.home() / "Pictures" / "AI" / "organized",
        ]
    
    total_added = 0
    
    for directory in default_dirs:
        if directory.exists():
            logger.info(f"Scanning directory: {directory}")
            added = populate_from_directory(directory, manager, limit=limit)
            total_added += added
            
            if limit and total_added >= limit:
                break
    
    return total_added