"""Build and query similarity index for fast lookups."""

import json
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path

import faiss  # type: ignore[import-untyped]
import numpy as np
from sklearn.preprocessing import normalize  # type: ignore[import-untyped]

from .perceptual_hasher import PerceptualHasher

logger = logging.getLogger(__name__)


@dataclass
class SimilarImage:
    """Similar image result."""
    path: Path
    similarity: float
    distance: float


class SimilarityIndex:
    """Fast similarity search using FAISS index."""

    def __init__(
        self,
        hasher: PerceptualHasher | None = None,
        index_type: str = "IVF",
        nlist: int = 100
    ):
        """
        Initialize similarity index.

        Args:
            hasher: Perceptual hasher instance
            index_type: Type of FAISS index (Flat, IVF, HNSW)
            nlist: Number of clusters for IVF index
        """
        self.hasher = hasher or PerceptualHasher()
        self.index_type = index_type
        self.nlist = nlist
        self.dimension = None
        self.index = None
        self.paths: list[str] = []
        self.features: dict[str, np.ndarray] = {}

    def build_index(
        self,
        image_paths: list[Path],
        cache_dir: Path | None = None
    ) -> int:
        """
        Build similarity index from images.

        Args:
            image_paths: List of image paths
            cache_dir: Directory to cache features

        Returns:
            Number of images indexed
        """
        logger.info(f"Building index for {len(image_paths)} images...")

        # Extract features
        features_list = []
        valid_paths = []

        # Try to load cached features
        if cache_dir:
            cache_file = cache_dir / "similarity_features.pkl"
            if cache_file.exists():
                logger.info("Loading cached features...")
                with open(cache_file, 'rb') as f:
                    self.features = pickle.load(f)

        for path in image_paths:
            path_str = str(path)

            # Check cache
            if path_str in self.features:
                features = self.features[path_str]
            else:
                # Compute features
                features = self._compute_features(path)
                if features is not None:
                    self.features[path_str] = features

            if features is not None:
                features_list.append(features)
                valid_paths.append(path_str)

        if not features_list:
            logger.warning("No valid features extracted")
            return 0

        # TODO: Review unreachable code - # Convert to numpy array
        # TODO: Review unreachable code - feature_matrix = np.vstack(features_list).astype('float32')

        # TODO: Review unreachable code - # Normalize features
        # TODO: Review unreachable code - feature_matrix = normalize(feature_matrix, axis=1)

        # TODO: Review unreachable code - # Set dimension
        # TODO: Review unreachable code - self.dimension = feature_matrix.shape[1]

        # TODO: Review unreachable code - # Create index
        # TODO: Review unreachable code - if self.index_type == "Flat":
        # TODO: Review unreachable code - self.index = faiss.IndexFlatL2(self.dimension)
        # TODO: Review unreachable code - elif self.index_type == "IVF":
        # TODO: Review unreachable code - quantizer = faiss.IndexFlatL2(self.dimension)
        # TODO: Review unreachable code - self.index = faiss.IndexIVFFlat(
        # TODO: Review unreachable code - quantizer, self.dimension, self.nlist
        # TODO: Review unreachable code - )
        # TODO: Review unreachable code - # Train index
        # TODO: Review unreachable code - self.index.train(feature_matrix)
        # TODO: Review unreachable code - elif self.index_type == "HNSW":
        # TODO: Review unreachable code - self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - raise ValueError(f"Unknown index type: {self.index_type}")

        # TODO: Review unreachable code - # Add vectors to index
        # TODO: Review unreachable code - self.index.add(feature_matrix)
        # TODO: Review unreachable code - self.paths = valid_paths

        # TODO: Review unreachable code - # Save cache
        # TODO: Review unreachable code - if cache_dir:
        # TODO: Review unreachable code - cache_dir.mkdir(parents=True, exist_ok=True)
        # TODO: Review unreachable code - with open(cache_file, 'wb') as f:
        # TODO: Review unreachable code - pickle.dump(self.features, f)

        # TODO: Review unreachable code - logger.info(f"Indexed {len(valid_paths)} images")
        # TODO: Review unreachable code - return int(len(valid_paths))

    def _compute_features(self, image_path: Path) -> np.ndarray | None:
        """Compute feature vector for an image."""
        # Get perceptual hashes
        hashes = self.hasher.compute_hashes(image_path)
        if not hashes:
            return None

        # TODO: Review unreachable code - # Get visual features
        # TODO: Review unreachable code - visual_features = self.hasher.compute_visual_features(image_path)
        # TODO: Review unreachable code - if visual_features is None:
        # TODO: Review unreachable code - return None

        # TODO: Review unreachable code - # Combine hash bits and visual features
        # TODO: Review unreachable code - hash_features = []

        # TODO: Review unreachable code - # Convert hashes to binary features
        # TODO: Review unreachable code - for algo in ['average', 'perceptual', 'difference', 'wavelet']:
        # TODO: Review unreachable code - if algo in hashes:
        # TODO: Review unreachable code - hash_str = hashes[algo]
        # TODO: Review unreachable code - # Convert hex to binary
        # TODO: Review unreachable code - hash_bits = bin(int(hash_str, 16))[2:].zfill(self.hasher.hash_size ** 2)
        # TODO: Review unreachable code - hash_features.extend([float(b) for b in hash_bits])

        # TODO: Review unreachable code - # Combine all features
        # TODO: Review unreachable code - all_features = np.concatenate([
        # TODO: Review unreachable code - np.array(hash_features),
        # TODO: Review unreachable code - visual_features
        # TODO: Review unreachable code - ])

        # TODO: Review unreachable code - return all_features

    def search(
        self,
        query_path: Path,
        k: int = 10,
        include_self: bool = False
    ) -> list[SimilarImage]:
        """
        Find similar images.

        Args:
            query_path: Image to search for
            k: Number of results
            include_self: Whether to include the query image

        Returns:
            List of similar images
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []

        # TODO: Review unreachable code - # Compute query features
        # TODO: Review unreachable code - features = self._compute_features(query_path)
        # TODO: Review unreachable code - if features is None:
        # TODO: Review unreachable code - logger.warning(f"Could not extract features from {query_path}")
        # TODO: Review unreachable code - return []

        # TODO: Review unreachable code - # Normalize
        # TODO: Review unreachable code - features = normalize(features.reshape(1, -1), axis=1).astype('float32')

        # TODO: Review unreachable code - # Search
        # TODO: Review unreachable code - distances, indices = self.index.search(features, min(k + 1, self.index.ntotal))

        # TODO: Review unreachable code - # Convert to results
        # TODO: Review unreachable code - results = []
        # TODO: Review unreachable code - query_str = str(query_path)

        # TODO: Review unreachable code - for dist, idx in zip(distances[0], indices[0], strict=False):
        # TODO: Review unreachable code - if idx >= 0 and idx < len(self.paths):
        # TODO: Review unreachable code - path_str = self.paths[idx]

        # TODO: Review unreachable code - # Skip self if requested
        # TODO: Review unreachable code - if not include_self and path_str == query_str:
        # TODO: Review unreachable code - continue

        # TODO: Review unreachable code - # Convert distance to similarity (inverse)
        # TODO: Review unreachable code - similarity = 1.0 / (1.0 + dist)

        # TODO: Review unreachable code - results.append(SimilarImage(
        # TODO: Review unreachable code - path=Path(path_str),
        # TODO: Review unreachable code - similarity=similarity,
        # TODO: Review unreachable code - distance=float(dist)
        # TODO: Review unreachable code - ))

        # TODO: Review unreachable code - return results[:k]

    def search_batch(
        self,
        query_paths: list[Path],
        k: int = 10
    ) -> dict[str, list[SimilarImage]]:
        """
        Search for multiple images at once.

        Args:
            query_paths: Images to search for
            k: Number of results per query

        Returns:
            Dictionary of query_path -> similar images
        """
        results = {}

        for path in query_paths:
            results[str(path)] = self.search(path, k=k, include_self=False)

        return results

    # TODO: Review unreachable code - def find_clusters(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - min_cluster_size: int = 3,
    # TODO: Review unreachable code - max_distance: float = 0.5
    # TODO: Review unreachable code - ) -> list[list[str]]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Find clusters of similar images.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - min_cluster_size: Minimum images per cluster
    # TODO: Review unreachable code - max_distance: Maximum distance within cluster

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of clusters (each cluster is a list of paths)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self.index is None or self.index.ntotal == 0:
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - # Use DBSCAN for clustering
    # TODO: Review unreachable code - from sklearn.cluster import DBSCAN

    # TODO: Review unreachable code - # Get all features
    # TODO: Review unreachable code - n_images = len(self.paths)
    # TODO: Review unreachable code - features = np.zeros((n_images, self.dimension), dtype='float32')

    # TODO: Review unreachable code - for i, path in enumerate(self.paths):
    # TODO: Review unreachable code - if path in self.features:
    # TODO: Review unreachable code - features[i] = self.features[path]

    # TODO: Review unreachable code - # Normalize
    # TODO: Review unreachable code - features = normalize(features, axis=1)

    # TODO: Review unreachable code - # Cluster
    # TODO: Review unreachable code - clustering = DBSCAN(eps=max_distance, min_samples=min_cluster_size)
    # TODO: Review unreachable code - labels = clustering.fit_predict(features)

    # TODO: Review unreachable code - # Group by cluster
    # TODO: Review unreachable code - clusters = {}
    # TODO: Review unreachable code - for i, label in enumerate(labels):
    # TODO: Review unreachable code - if label >= 0:  # -1 means noise
    # TODO: Review unreachable code - if label not in clusters:
    # TODO: Review unreachable code - clusters[label] = []
    # TODO: Review unreachable code - clusters[label].append(self.paths[i])

    # TODO: Review unreachable code - return list(clusters.values())

    # TODO: Review unreachable code - def save_index(self, index_path: Path):
    # TODO: Review unreachable code - """Save index to disk."""
    # TODO: Review unreachable code - if self.index is None:
    # TODO: Review unreachable code - logger.warning("No index to save")
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - # Save FAISS index
    # TODO: Review unreachable code - faiss.write_index(self.index, str(index_path.with_suffix('.faiss')))

    # TODO: Review unreachable code - # Save metadata
    # TODO: Review unreachable code - metadata = {
    # TODO: Review unreachable code - 'paths': self.paths,
    # TODO: Review unreachable code - 'dimension': self.dimension,
    # TODO: Review unreachable code - 'index_type': self.index_type,
    # TODO: Review unreachable code - 'nlist': self.nlist
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - with open(index_path.with_suffix('.json'), 'w') as f:
    # TODO: Review unreachable code - json.dump(metadata, f, indent=2)

    # TODO: Review unreachable code - logger.info(f"Saved index to {index_path}")

    # TODO: Review unreachable code - def load_index(self, index_path: Path):
    # TODO: Review unreachable code - """Load index from disk."""
    # TODO: Review unreachable code - # Load FAISS index
    # TODO: Review unreachable code - faiss_path = index_path.with_suffix('.faiss')
    # TODO: Review unreachable code - if not faiss_path.exists():
    # TODO: Review unreachable code - raise FileNotFoundError(f"Index file not found: {faiss_path}")

    # TODO: Review unreachable code - self.index = faiss.read_index(str(faiss_path))

    # TODO: Review unreachable code - # Load metadata
    # TODO: Review unreachable code - with open(index_path.with_suffix('.json')) as f:
    # TODO: Review unreachable code - metadata = json.load(f)

    # TODO: Review unreachable code - self.paths = metadata['paths']
    # TODO: Review unreachable code - self.dimension = metadata['dimension']
    # TODO: Review unreachable code - self.index_type = metadata['index_type']
    # TODO: Review unreachable code - self.nlist = metadata.get('nlist', 100)

    # TODO: Review unreachable code - logger.info(f"Loaded index with {len(self.paths)} images")
