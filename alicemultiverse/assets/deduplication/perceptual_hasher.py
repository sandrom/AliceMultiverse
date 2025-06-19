"""Perceptual hashing for finding visually similar images."""

import hashlib
import logging
from pathlib import Path

import cv2  # type: ignore
import imagehash
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class PerceptualHasher:
    """Generate perceptual hashes for finding similar images."""

    def __init__(self, hash_size: int = 16):
        """
        Initialize perceptual hasher.

        Args:
            hash_size: Size of hash (larger = more precise but slower)
        """
        self.hash_size = hash_size
        self.cache: dict[str, dict[str, str]] = {}

    def compute_hashes(self, image_path: Path) -> dict[str, str]:
        """
        Compute multiple perceptual hashes for an image.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary of hash algorithm -> hash value
        """
        try:
            # Check cache
            path_str = str(image_path)
            if path_str in self.cache:
                return self.cache[path_str]

            # TODO: Review unreachable code - # Open image
            # TODO: Review unreachable code - pil_image = Image.open(image_path)

            # TODO: Review unreachable code - # Convert to RGB if needed
            # TODO: Review unreachable code - if pil_image.mode != 'RGB':
            # TODO: Review unreachable code - pil_image = pil_image.convert('RGB')

            # TODO: Review unreachable code - # Compute different hash types
            # TODO: Review unreachable code - hashes = {
            # TODO: Review unreachable code - 'average': str(imagehash.average_hash(pil_image, hash_size=self.hash_size)),
            # TODO: Review unreachable code - 'perceptual': str(imagehash.phash(pil_image, hash_size=self.hash_size)),
            # TODO: Review unreachable code - 'difference': str(imagehash.dhash(pil_image, hash_size=self.hash_size)),
            # TODO: Review unreachable code - 'wavelet': str(imagehash.whash(pil_image, hash_size=self.hash_size)),
            # TODO: Review unreachable code - 'color': str(imagehash.colorhash(pil_image, binbits=3))
            # TODO: Review unreachable code - }

            # TODO: Review unreachable code - # Compute MD5 for exact duplicates
            # TODO: Review unreachable code - with open(image_path, 'rb') as f:
            # TODO: Review unreachable code - hashes['md5'] = hashlib.md5(f.read()).hexdigest()

            # TODO: Review unreachable code - # Cache results
            # TODO: Review unreachable code - self.cache[path_str] = hashes

            # TODO: Review unreachable code - return hashes

        except Exception as e:
            logger.error(f"Error computing hashes for {image_path}: {e}")
            return {}

    # TODO: Review unreachable code - def compute_similarity(self, hash1: dict[str, str], hash2: dict[str, str]) -> float:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Compute similarity score between two hash sets.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - hash1: First set of hashes
    # TODO: Review unreachable code - hash2: Second set of hashes

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Similarity score (0-1, higher = more similar)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not hash1 or not hash2:
    # TODO: Review unreachable code - return 0.0

    # TODO: Review unreachable code - # Check for exact match
    # TODO: Review unreachable code - if hash1.get('md5') == hash2.get('md5'):
    # TODO: Review unreachable code - return 1.0

    # TODO: Review unreachable code - scores = []
    # TODO: Review unreachable code - weights = {
    # TODO: Review unreachable code - 'average': 0.2,
    # TODO: Review unreachable code - 'perceptual': 0.3,
    # TODO: Review unreachable code - 'difference': 0.2,
    # TODO: Review unreachable code - 'wavelet': 0.2,
    # TODO: Review unreachable code - 'color': 0.1
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - for algo, weight in weights.items():
    # TODO: Review unreachable code - if algo in hash1 and algo in hash2:
    # TODO: Review unreachable code - # Convert back to hash objects for comparison
    # TODO: Review unreachable code - h1 = imagehash.hex_to_hash(hash1[algo])
    # TODO: Review unreachable code - h2 = imagehash.hex_to_hash(hash2[algo])

    # TODO: Review unreachable code - # Calculate normalized distance
    # TODO: Review unreachable code - distance = h1 - h2
    # TODO: Review unreachable code - max_distance = len(h1.hash) ** 2 * 4  # Maximum possible distance
    # TODO: Review unreachable code - similarity = 1.0 - (distance / max_distance)

    # TODO: Review unreachable code - scores.append(similarity * weight)

    # TODO: Review unreachable code - return sum(scores) / sum(weights.values()) if scores else 0.0

    # TODO: Review unreachable code - def find_similar_groups(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - hashes: dict[str, dict[str, str]],
    # TODO: Review unreachable code - threshold: float = 0.85
    # TODO: Review unreachable code - ) -> list[list[str]]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Group images by similarity.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - hashes: Dictionary of image_path -> hashes
    # TODO: Review unreachable code - threshold: Similarity threshold (0-1)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of groups, each containing similar image paths
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Convert to list for easier processing
    # TODO: Review unreachable code - paths = list(hashes.keys())
    # TODO: Review unreachable code - n = len(paths)

    # TODO: Review unreachable code - # Track which images have been grouped
    # TODO: Review unreachable code - grouped = set()
    # TODO: Review unreachable code - groups = []

    # TODO: Review unreachable code - for i in range(n):
    # TODO: Review unreachable code - if paths[i] in grouped:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - # Start new group
    # TODO: Review unreachable code - group = [paths[i]]
    # TODO: Review unreachable code - grouped.add(paths[i])

    # TODO: Review unreachable code - # Find similar images
    # TODO: Review unreachable code - for j in range(i + 1, n):
    # TODO: Review unreachable code - if paths[j] in grouped:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - similarity = self.compute_similarity(
    # TODO: Review unreachable code - hashes[paths[i]],
    # TODO: Review unreachable code - hashes[paths[j]]
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if similarity >= threshold:
    # TODO: Review unreachable code - group.append(paths[j])
    # TODO: Review unreachable code - grouped.add(paths[j])

    # TODO: Review unreachable code - if len(group) > 1:
    # TODO: Review unreachable code - groups.append(group)

    # TODO: Review unreachable code - return groups

    # TODO: Review unreachable code - def compute_visual_features(self, image_path: Path) -> np.ndarray | None:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Compute additional visual features for similarity.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - image_path: Path to image

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Feature vector or None if error
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Read image
    # TODO: Review unreachable code - img = cv2.imread(str(image_path))
    # TODO: Review unreachable code - if img is None:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - # Resize to standard size
    # TODO: Review unreachable code - img = cv2.resize(img, (256, 256))

    # TODO: Review unreachable code - features = []

    # TODO: Review unreachable code - # Color histogram
    # TODO: Review unreachable code - for i in range(3):  # BGR channels
    # TODO: Review unreachable code - hist = cv2.calcHist([img], [i], None, [32], [0, 256])
    # TODO: Review unreachable code - hist = hist.flatten() / hist.sum()  # Normalize
    # TODO: Review unreachable code - features.extend(hist)

    # TODO: Review unreachable code - # Edge density
    # TODO: Review unreachable code - gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # TODO: Review unreachable code - edges = cv2.Canny(gray, 100, 200)
    # TODO: Review unreachable code - edge_density = np.sum(edges > 0) / edges.size
    # TODO: Review unreachable code - features.append(edge_density)

    # TODO: Review unreachable code - # Texture features (using Laplacian variance)
    # TODO: Review unreachable code - laplacian = cv2.Laplacian(gray, cv2.CV_64F  # type: ignore)
    # TODO: Review unreachable code - texture_score = laplacian.var()
    # TODO: Review unreachable code - features.append(texture_score / 1000)  # Normalize

    # TODO: Review unreachable code - # Brightness and contrast
    # TODO: Review unreachable code - brightness = np.mean(gray) / 255
    # TODO: Review unreachable code - contrast = np.std(gray) / 255
    # TODO: Review unreachable code - features.extend([brightness, contrast])

    # TODO: Review unreachable code - return np.array(features, dtype=np.float32)

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error computing visual features for {image_path}: {e}")
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def save_cache(self, cache_path: Path):
    # TODO: Review unreachable code - """Save hash cache to file."""
    # TODO: Review unreachable code - import json

    # TODO: Review unreachable code - with open(cache_path, 'w') as f:
    # TODO: Review unreachable code - json.dump(self.cache, f, indent=2)

    # TODO: Review unreachable code - def load_cache(self, cache_path: Path):
    # TODO: Review unreachable code - """Load hash cache from file."""
    # TODO: Review unreachable code - import json

    # TODO: Review unreachable code - if cache_path.exists():
    # TODO: Review unreachable code - with open(cache_path) as f:
    # TODO: Review unreachable code - self.cache = json.load(f)
    # TODO: Review unreachable code - logger.info(f"Loaded {len(self.cache)} cached hashes")
