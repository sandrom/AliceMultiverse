"""Build and query similarity index for fast lookups."""

import json
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from sklearn.preprocessing import normalize

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

        # Convert to numpy array
        feature_matrix = np.vstack(features_list).astype('float32')

        # Normalize features
        feature_matrix = normalize(feature_matrix, axis=1)

        # Set dimension
        self.dimension = feature_matrix.shape[1]

        # Create index
        if self.index_type == "Flat":
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IVF":
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(
                quantizer, self.dimension, self.nlist
            )
            # Train index
            self.index.train(feature_matrix)
        elif self.index_type == "HNSW":
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")

        # Add vectors to index
        self.index.add(feature_matrix)
        self.paths = valid_paths

        # Save cache
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(self.features, f)

        logger.info(f"Indexed {len(valid_paths)} images")
        return len(valid_paths)

    def _compute_features(self, image_path: Path) -> np.ndarray | None:
        """Compute feature vector for an image."""
        # Get perceptual hashes
        hashes = self.hasher.compute_hashes(image_path)
        if not hashes:
            return None

        # Get visual features
        visual_features = self.hasher.compute_visual_features(image_path)
        if visual_features is None:
            return None

        # Combine hash bits and visual features
        hash_features = []

        # Convert hashes to binary features
        for algo in ['average', 'perceptual', 'difference', 'wavelet']:
            if algo in hashes:
                hash_str = hashes[algo]
                # Convert hex to binary
                hash_bits = bin(int(hash_str, 16))[2:].zfill(self.hasher.hash_size ** 2)
                hash_features.extend([float(b) for b in hash_bits])

        # Combine all features
        all_features = np.concatenate([
            np.array(hash_features),
            visual_features
        ])

        return all_features

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

        # Compute query features
        features = self._compute_features(query_path)
        if features is None:
            logger.warning(f"Could not extract features from {query_path}")
            return []

        # Normalize
        features = normalize(features.reshape(1, -1), axis=1).astype('float32')

        # Search
        distances, indices = self.index.search(features, min(k + 1, self.index.ntotal))

        # Convert to results
        results = []
        query_str = str(query_path)

        for dist, idx in zip(distances[0], indices[0], strict=False):
            if idx >= 0 and idx < len(self.paths):
                path_str = self.paths[idx]

                # Skip self if requested
                if not include_self and path_str == query_str:
                    continue

                # Convert distance to similarity (inverse)
                similarity = 1.0 / (1.0 + dist)

                results.append(SimilarImage(
                    path=Path(path_str),
                    similarity=similarity,
                    distance=float(dist)
                ))

        return results[:k]

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

    def find_clusters(
        self,
        min_cluster_size: int = 3,
        max_distance: float = 0.5
    ) -> list[list[str]]:
        """
        Find clusters of similar images.

        Args:
            min_cluster_size: Minimum images per cluster
            max_distance: Maximum distance within cluster

        Returns:
            List of clusters (each cluster is a list of paths)
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Use DBSCAN for clustering
        from sklearn.cluster import DBSCAN

        # Get all features
        n_images = len(self.paths)
        features = np.zeros((n_images, self.dimension), dtype='float32')

        for i, path in enumerate(self.paths):
            if path in self.features:
                features[i] = self.features[path]

        # Normalize
        features = normalize(features, axis=1)

        # Cluster
        clustering = DBSCAN(eps=max_distance, min_samples=min_cluster_size)
        labels = clustering.fit_predict(features)

        # Group by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label >= 0:  # -1 means noise
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(self.paths[i])

        return list(clusters.values())

    def save_index(self, index_path: Path):
        """Save index to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return

        # Save FAISS index
        faiss.write_index(self.index, str(index_path.with_suffix('.faiss')))

        # Save metadata
        metadata = {
            'paths': self.paths,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'nlist': self.nlist
        }

        with open(index_path.with_suffix('.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved index to {index_path}")

    def load_index(self, index_path: Path):
        """Load index from disk."""
        # Load FAISS index
        faiss_path = index_path.with_suffix('.faiss')
        if not faiss_path.exists():
            raise FileNotFoundError(f"Index file not found: {faiss_path}")

        self.index = faiss.read_index(str(faiss_path))

        # Load metadata
        with open(index_path.with_suffix('.json')) as f:
            metadata = json.load(f)

        self.paths = metadata['paths']
        self.dimension = metadata['dimension']
        self.index_type = metadata['index_type']
        self.nlist = metadata.get('nlist', 100)

        logger.info(f"Loaded index with {len(self.paths)} images")
