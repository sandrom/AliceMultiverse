"""Perceptual hashing for finding visually similar images."""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
import imagehash

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
        self.cache: Dict[str, Dict[str, str]] = {}
    
    def compute_hashes(self, image_path: Path) -> Dict[str, str]:
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
            
            # Open image
            pil_image = Image.open(image_path)
            
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Compute different hash types
            hashes = {
                'average': str(imagehash.average_hash(pil_image, hash_size=self.hash_size)),
                'perceptual': str(imagehash.phash(pil_image, hash_size=self.hash_size)),
                'difference': str(imagehash.dhash(pil_image, hash_size=self.hash_size)),
                'wavelet': str(imagehash.whash(pil_image, hash_size=self.hash_size)),
                'color': str(imagehash.colorhash(pil_image, binbits=3))
            }
            
            # Compute MD5 for exact duplicates
            with open(image_path, 'rb') as f:
                hashes['md5'] = hashlib.md5(f.read()).hexdigest()
            
            # Cache results
            self.cache[path_str] = hashes
            
            return hashes
            
        except Exception as e:
            logger.error(f"Error computing hashes for {image_path}: {e}")
            return {}
    
    def compute_similarity(self, hash1: Dict[str, str], hash2: Dict[str, str]) -> float:
        """
        Compute similarity score between two hash sets.
        
        Args:
            hash1: First set of hashes
            hash2: Second set of hashes
            
        Returns:
            Similarity score (0-1, higher = more similar)
        """
        if not hash1 or not hash2:
            return 0.0
        
        # Check for exact match
        if hash1.get('md5') == hash2.get('md5'):
            return 1.0
        
        scores = []
        weights = {
            'average': 0.2,
            'perceptual': 0.3,
            'difference': 0.2,
            'wavelet': 0.2,
            'color': 0.1
        }
        
        for algo, weight in weights.items():
            if algo in hash1 and algo in hash2:
                # Convert back to hash objects for comparison
                h1 = imagehash.hex_to_hash(hash1[algo])
                h2 = imagehash.hex_to_hash(hash2[algo])
                
                # Calculate normalized distance
                distance = h1 - h2
                max_distance = len(h1.hash) ** 2 * 4  # Maximum possible distance
                similarity = 1.0 - (distance / max_distance)
                
                scores.append(similarity * weight)
        
        return sum(scores) / sum(weights.values()) if scores else 0.0
    
    def find_similar_groups(
        self, 
        hashes: Dict[str, Dict[str, str]], 
        threshold: float = 0.85
    ) -> List[List[str]]:
        """
        Group images by similarity.
        
        Args:
            hashes: Dictionary of image_path -> hashes
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of groups, each containing similar image paths
        """
        # Convert to list for easier processing
        paths = list(hashes.keys())
        n = len(paths)
        
        # Track which images have been grouped
        grouped = set()
        groups = []
        
        for i in range(n):
            if paths[i] in grouped:
                continue
                
            # Start new group
            group = [paths[i]]
            grouped.add(paths[i])
            
            # Find similar images
            for j in range(i + 1, n):
                if paths[j] in grouped:
                    continue
                    
                similarity = self.compute_similarity(
                    hashes[paths[i]], 
                    hashes[paths[j]]
                )
                
                if similarity >= threshold:
                    group.append(paths[j])
                    grouped.add(paths[j])
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def compute_visual_features(self, image_path: Path) -> Optional[np.ndarray]:
        """
        Compute additional visual features for similarity.
        
        Args:
            image_path: Path to image
            
        Returns:
            Feature vector or None if error
        """
        try:
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                return None
            
            # Resize to standard size
            img = cv2.resize(img, (256, 256))
            
            features = []
            
            # Color histogram
            for i in range(3):  # BGR channels
                hist = cv2.calcHist([img], [i], None, [32], [0, 256])
                hist = hist.flatten() / hist.sum()  # Normalize
                features.extend(hist)
            
            # Edge density
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size
            features.append(edge_density)
            
            # Texture features (using Laplacian variance)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            texture_score = laplacian.var()
            features.append(texture_score / 1000)  # Normalize
            
            # Brightness and contrast
            brightness = np.mean(gray) / 255
            contrast = np.std(gray) / 255
            features.extend([brightness, contrast])
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error computing visual features for {image_path}: {e}")
            return None
    
    def save_cache(self, cache_path: Path):
        """Save hash cache to file."""
        import json
        
        with open(cache_path, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def load_cache(self, cache_path: Path):
        """Load hash cache from file."""
        import json
        
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached hashes")