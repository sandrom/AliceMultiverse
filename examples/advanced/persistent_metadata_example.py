"""
Example: Persistent Metadata System

This demonstrates how AliceMultiverse stores analysis results directly
in image files, making them self-contained and portable.
"""

import logging
from pathlib import Path
from PIL import Image
import numpy as np

from alicemultiverse.metadata.persistent_metadata import PersistentMetadataManager
from alicemultiverse.metadata.embedder import MetadataEmbedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_image(path: Path, color=(100, 150, 200)):
    """Create a test image."""
    img = Image.new('RGB', (512, 512), color)
    img.save(path)
    logger.info(f"Created test image: {path}")


def demonstrate_metadata_embedding():
    """Show how metadata is embedded in images."""
    print("Metadata Embedding Demo")
    print("=" * 50)
    
    # Create test image
    test_dir = Path("test_metadata_demo")
    test_dir.mkdir(exist_ok=True)
    
    image_path = test_dir / "cyberpunk_portrait.png"
    create_test_image(image_path)
    
    # Initialize embedder
    embedder = MetadataEmbedder()
    
    # Simulate analysis results
    metadata = {
        'prompt': 'cyberpunk portrait with neon lighting, high detail',
        'generation_params': {
            'model': 'sdxl-turbo',
            'seed': 12345,
            'steps': 30,
            'cfg_scale': 7.5,
            'sampler': 'DPM++ 2M Karras'
        },
        
        # Raw analysis scores (what we embed)
        'brisque_score': 23.5,  # Raw BRISQUE score
        'sightengine_quality': 0.85,
        'sightengine_sharpness': 0.92,
        'sightengine_contrast': 0.78,
        'sightengine_brightness': 0.81,
        'sightengine_ai_generated': True,
        'sightengine_ai_probability': 0.98,
        
        'claude_defects_found': False,
        'claude_defect_count': 0,
        'claude_severity': 'none',
        'claude_confidence': 0.95,
        'claude_quality_score': 0.90,
        
        # Semantic tags
        'style_tags': ['cyberpunk', 'neon', 'futuristic'],
        'mood_tags': ['intense', 'mysterious'],
        'subject_tags': ['portrait', 'character'],
        'color_tags': ['blue', 'purple', 'pink'],
        
        # Relationships
        'relationships': {
            'variations': ['asset_123', 'asset_124'],
            'references': ['ref_001']
        },
        
        'role': 'hero',
        'project_id': 'cyberpunk_music_video_2024'
    }
    
    # Embed metadata
    print("\n1. Embedding metadata in image...")
    success = embedder.embed_metadata(image_path, metadata)
    print(f"   Embedding successful: {success}")
    
    # Extract to verify
    print("\n2. Extracting embedded metadata...")
    extracted = embedder.extract_metadata(image_path)
    
    print("\n   Extracted data:")
    print(f"   - Prompt: {extracted.get('prompt', 'Not found')[:50]}...")
    print(f"   - BRISQUE score: {extracted.get('brisque_score', 'Not found')}")
    print(f"   - SightEngine quality: {extracted.get('sightengine_quality', 'Not found')}")
    print(f"   - Claude defects: {extracted.get('claude_defects_found', 'Not found')}")
    print(f"   - Style tags: {extracted.get('style_tags', [])}")
    print(f"   - Role: {extracted.get('role', 'Not found')}")
    
    # Demonstrate portability
    print("\n3. Demonstrating portability...")
    moved_path = test_dir / "moved" / "renamed_image.png"
    moved_path.parent.mkdir(exist_ok=True)
    
    # Copy file (simulating moving to different location)
    import shutil
    shutil.copy2(image_path, moved_path)
    
    # Extract from moved file
    moved_metadata = embedder.extract_metadata(moved_path)
    print(f"   Metadata preserved after move: {bool(moved_metadata)}")
    print(f"   BRISQUE score still available: {moved_metadata.get('brisque_score', 'Lost')}")


def demonstrate_persistent_manager():
    """Show the full persistent metadata system."""
    print("\n\nPersistent Metadata Manager Demo")
    print("=" * 50)
    
    test_dir = Path("test_metadata_demo")
    cache_dir = test_dir / ".alice_cache"
    
    # Initialize manager
    manager = PersistentMetadataManager(cache_dir)
    
    # Create images with different quality levels
    images = [
        ("high_quality.png", (50, 100, 150), 15.2),   # Low BRISQUE = good
        ("medium_quality.png", (150, 100, 50), 45.8), # Medium BRISQUE
        ("low_quality.png", (200, 50, 50), 78.3),     # High BRISQUE = poor
    ]
    
    print("\n1. Creating and analyzing images...")
    for filename, color, brisque in images:
        path = test_dir / filename
        create_test_image(path, color)
        
        # Simulate analysis
        metadata = {
            'content_hash': manager.cache.get_content_hash(path),
            'brisque_score': brisque,
            'style_tags': ['test', 'demo'],
        }
        
        # Save metadata (embeds in image and updates cache)
        manager.save_metadata(path, metadata)
        print(f"   Saved metadata for {filename}")
    
    # Load metadata (demonstrates precedence)
    print("\n2. Loading metadata...")
    for filename, _, _ in images:
        path = test_dir / filename
        metadata, from_cache = manager.load_metadata(path)
        
        print(f"\n   {filename}:")
        print(f"   - Loaded from: {'cache' if from_cache else 'embedded in image'}")
        print(f"   - BRISQUE score: {metadata.get('brisque_score')}")
        print(f"   - Quality stars: {metadata.get('quality_stars')}")
        print(f"   - Combined score: {metadata.get('combined_quality_score', 0):.2f}")
    
    # Clear cache to demonstrate recovery
    print("\n3. Clearing cache and rebuilding from images...")
    import shutil
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    
    # Rebuild from embedded metadata
    manager = PersistentMetadataManager(cache_dir)
    count = manager.rebuild_cache_from_images(test_dir)
    print(f"   Rebuilt cache from {count} images")
    
    # Verify data is still available
    print("\n4. Verifying data after cache rebuild...")
    path = test_dir / "high_quality.png"
    metadata, from_cache = manager.load_metadata(path)
    print(f"   high_quality.png BRISQUE score: {metadata.get('brisque_score')}")
    print(f"   Data successfully recovered from embedded metadata!")
    
    # Show metadata status
    print("\n5. Metadata coverage status:")
    status = manager.get_metadata_status(test_dir)
    for key, value in status.items():
        print(f"   {key}: {value}")


def demonstrate_score_recalculation():
    """Show how scores can be recalculated with new thresholds."""
    print("\n\nScore Recalculation Demo")
    print("=" * 50)
    
    test_dir = Path("test_metadata_demo")
    cache_dir = test_dir / ".alice_cache"
    
    # Initialize with original thresholds
    original_thresholds = {
        '5_star': {'min': 0, 'max': 25},
        '4_star': {'min': 25, 'max': 45},
        '3_star': {'min': 45, 'max': 65},
        '2_star': {'min': 65, 'max': 85},
        '1_star': {'min': 85, 'max': 100}
    }
    
    manager = PersistentMetadataManager(cache_dir, original_thresholds)
    
    print("\n1. Original thresholds:")
    path = test_dir / "medium_quality.png"
    metadata, _ = manager.load_metadata(path)
    print(f"   BRISQUE score: {metadata.get('brisque_score')}")
    print(f"   Quality stars: {metadata.get('quality_stars')}")
    
    # Change thresholds (stricter)
    stricter_thresholds = {
        '5_star': {'min': 0, 'max': 20},
        '4_star': {'min': 20, 'max': 35},
        '3_star': {'min': 35, 'max': 55},
        '2_star': {'min': 55, 'max': 75},
        '1_star': {'min': 75, 'max': 100}
    }
    
    manager = PersistentMetadataManager(cache_dir, stricter_thresholds)
    
    print("\n2. Stricter thresholds:")
    metadata, _ = manager.load_metadata(path)
    print(f"   BRISQUE score: {metadata.get('brisque_score')} (unchanged)")
    print(f"   Quality stars: {metadata.get('quality_stars')} (recalculated)")
    print("\n   Raw analysis data is preserved, only interpretation changes!")


if __name__ == "__main__":
    # Run all demonstrations
    demonstrate_metadata_embedding()
    demonstrate_persistent_manager()
    demonstrate_score_recalculation()
    
    print("\n\nKey Benefits:")
    print("- Images are self-contained with all analysis data")
    print("- Can move/rename files without losing metadata")
    print("- Cache can be rebuilt from images if needed")
    print("- Quality thresholds can be adjusted without re-analysis")
    print("- Raw scores preserved, final ratings recalculated")