"""Style-based clustering system for finding visually similar images.

This module implements style similarity clustering, auto-collections,
and style transfer hint extraction.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .style_analyzer import StyleAnalyzer, StyleFingerprint

logger = logging.getLogger(__name__)


@dataclass
class StyleCluster:
    """A cluster of images with similar visual style."""
    
    id: str
    name: str
    images: List[str] = field(default_factory=list)
    fingerprints: List[StyleFingerprint] = field(default_factory=list)
    centroid_image: Optional[str] = None
    style_summary: Dict[str, Any] = field(default_factory=dict)
    coherence_score: float = 0.0
    
    def add_image(self, image_path: str, fingerprint: StyleFingerprint):
        """Add an image to the cluster."""
        self.images.append(image_path)
        self.fingerprints.append(fingerprint)
    
    @property
    def size(self) -> int:
        """Number of images in cluster."""
        return len(self.images)


@dataclass
class StyleTransferHint:
    """Hints for recreating a style in new images."""
    
    source_image: str
    style_elements: Dict[str, str] = field(default_factory=dict)
    prompt_fragments: List[str] = field(default_factory=list)
    color_palette: List[Tuple[int, int, int]] = field(default_factory=list)
    technical_params: Dict[str, Any] = field(default_factory=dict)
    success_rate: float = 0.0  # How well this style transfers


class StyleClusteringSystem:
    """System for clustering images by visual style similarity."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize style clustering system.
        
        Args:
            cache_dir: Directory for caching style fingerprints
        """
        self.analyzer = StyleAnalyzer()
        self.cache_dir = cache_dir or Path.home() / ".alice" / "style_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.fingerprints: Dict[str, StyleFingerprint] = {}
        self.clusters: Dict[str, StyleCluster] = {}
        self.style_transfer_hints: Dict[str, List[StyleTransferHint]] = defaultdict(list)
        
        self._load_cache()
    
    def _load_cache(self):
        """Load cached style fingerprints."""
        cache_file = self.cache_dir / "fingerprints.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    # Reconstruct fingerprints from JSON
                    # Note: This is simplified, full implementation would properly deserialize
                    logger.info(f"Loaded {len(data)} cached fingerprints")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save style fingerprints to cache."""
        cache_file = self.cache_dir / "fingerprints.json"
        try:
            # Simplified serialization
            data = {
                path: {
                    "style_tags": fp.style_tags,
                    "color_temperature": fp.color_palette.temperature,
                    "composition_complexity": fp.composition.complexity,
                    "lighting_mood": fp.lighting.mood_lighting
                }
                for path, fp in self.fingerprints.items()
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    async def analyze_image_style(self, image_path: Path) -> StyleFingerprint:
        """Analyze and cache image style.
        
        Args:
            image_path: Path to image
            
        Returns:
            Style fingerprint
        """
        path_str = str(image_path)
        
        # Check cache
        if path_str in self.fingerprints:
            return self.fingerprints[path_str]
        
        # Analyze
        fingerprint = self.analyzer.analyze_image(image_path)
        self.fingerprints[path_str] = fingerprint
        
        # Save to cache periodically
        if len(self.fingerprints) % 10 == 0:
            self._save_cache()
        
        return fingerprint
    
    async def find_similar_styles(self, image_path: Path, 
                                 similarity_threshold: float = 0.8,
                                 max_results: int = 10) -> List[Tuple[str, float]]:
        """Find images with similar visual style.
        
        Args:
            image_path: Reference image
            similarity_threshold: Minimum similarity score (0-1)
            max_results: Maximum number of results
            
        Returns:
            List of (image_path, similarity_score) tuples
        """
        # Get reference fingerprint
        reference = await self.analyze_image_style(image_path)
        
        # Compare with all other fingerprints
        similarities = []
        for path, fingerprint in self.fingerprints.items():
            if path == str(image_path):
                continue
            
            score = reference.similarity_score(fingerprint)
            if score >= similarity_threshold:
                similarities.append((path, score))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:max_results]
    
    async def cluster_by_style(self, image_paths: List[Path],
                              min_cluster_size: int = 3,
                              method: str = "dbscan") -> List[StyleCluster]:
        """Cluster images by visual style similarity.
        
        Args:
            image_paths: Images to cluster
            min_cluster_size: Minimum cluster size
            method: Clustering method ("dbscan" or "hierarchical")
            
        Returns:
            List of style clusters
        """
        if len(image_paths) < min_cluster_size:
            return []
        
        # Analyze all images
        fingerprints = []
        valid_paths = []
        
        for path in image_paths:
            try:
                fp = await self.analyze_image_style(path)
                fingerprints.append(fp)
                valid_paths.append(str(path))
            except Exception as e:
                logger.warning(f"Failed to analyze {path}: {e}")
        
        if len(fingerprints) < min_cluster_size:
            return []
        
        # Build feature matrix
        feature_matrix = np.array([fp.style_vector for fp in fingerprints])
        
        # Standardize features
        scaler = StandardScaler()
        feature_matrix_scaled = scaler.fit_transform(feature_matrix)
        
        # Apply PCA for dimensionality reduction if needed
        # Only use PCA if we have enough samples
        if feature_matrix.shape[1] > 10 and feature_matrix.shape[0] > 10:
            pca = PCA(n_components=10)
            feature_matrix_scaled = pca.fit_transform(feature_matrix_scaled)
        
        # Cluster
        if method == "dbscan":
            clustering = DBSCAN(eps=1.5, min_samples=min_cluster_size, metric='euclidean')
        else:  # hierarchical
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=2.0,
                linkage='ward'
            )
        
        labels = clustering.fit_predict(feature_matrix_scaled)
        
        # Create clusters
        clusters = []
        for cluster_id in set(labels):
            if cluster_id == -1:  # DBSCAN noise
                continue
            
            cluster_indices = np.where(labels == cluster_id)[0]
            if len(cluster_indices) < min_cluster_size:
                continue
            
            cluster = StyleCluster(
                id=f"style_cluster_{len(clusters)}",
                name=f"Style Group {len(clusters) + 1}"
            )
            
            # Add images to cluster
            for idx in cluster_indices:
                cluster.add_image(valid_paths[idx], fingerprints[idx])
            
            # Find centroid image
            cluster.centroid_image = self._find_centroid_image(cluster)
            
            # Generate style summary
            cluster.style_summary = self._summarize_cluster_style(cluster)
            
            # Calculate coherence
            cluster.coherence_score = self._calculate_cluster_coherence(cluster)
            
            # Generate name
            cluster.name = self._generate_cluster_name(cluster)
            
            clusters.append(cluster)
            self.clusters[cluster.id] = cluster
        
        return clusters
    
    def _find_centroid_image(self, cluster: StyleCluster) -> str:
        """Find most representative image in cluster."""
        if not cluster.fingerprints:
            return cluster.images[0] if cluster.images else ""
        
        # Calculate average style vector
        avg_vector = np.mean([fp.style_vector for fp in cluster.fingerprints], axis=0)
        
        # Find closest to average
        min_distance = float('inf')
        centroid_image = cluster.images[0]
        
        for i, fp in enumerate(cluster.fingerprints):
            distance = np.linalg.norm(fp.style_vector - avg_vector)
            if distance < min_distance:
                min_distance = distance
                centroid_image = cluster.images[i]
        
        return centroid_image
    
    def _summarize_cluster_style(self, cluster: StyleCluster) -> Dict[str, Any]:
        """Generate style summary for cluster."""
        summary = {
            "dominant_colors": [],
            "color_temperatures": [],
            "lighting_moods": [],
            "composition_types": [],
            "texture_types": [],
            "common_tags": []
        }
        
        # Aggregate properties
        color_temps = []
        lighting_moods = []
        compositions = []
        textures = []
        all_tags = []
        all_colors = []
        
        for fp in cluster.fingerprints:
            color_temps.append(fp.color_palette.temperature)
            lighting_moods.append(fp.lighting.mood_lighting)
            compositions.append(fp.composition.complexity)
            textures.append(fp.texture.overall_texture)
            all_tags.extend(fp.style_tags)
            all_colors.extend(fp.color_palette.dominant_colors[:2])
        
        # Find most common elements
        from collections import Counter
        
        summary["color_temperatures"] = [
            temp for temp, _ in Counter(color_temps).most_common(2)
        ]
        summary["lighting_moods"] = [
            mood for mood, _ in Counter(lighting_moods).most_common(2)
        ]
        summary["composition_types"] = [
            comp for comp, _ in Counter(compositions).most_common(2)
        ]
        summary["texture_types"] = [
            tex for tex, _ in Counter(textures).most_common(2)
        ]
        summary["common_tags"] = [
            tag for tag, count in Counter(all_tags).most_common(5)
            if count >= len(cluster.fingerprints) * 0.3
        ]
        
        # Average colors
        if all_colors:
            # Group similar colors
            color_clusters = self._cluster_colors(all_colors)
            summary["dominant_colors"] = color_clusters[:3]
        
        return summary
    
    def _cluster_colors(self, colors: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Cluster similar colors and return representatives."""
        if not colors:
            return []
        
        # Simple color clustering using KMeans
        from sklearn.cluster import KMeans
        
        color_array = np.array(colors)
        n_clusters = min(3, len(set(map(tuple, colors))))
        
        if n_clusters < 2:
            return [tuple(colors[0])]
        
        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        kmeans.fit(color_array)
        
        # Return cluster centers as representative colors
        return [tuple(map(int, center)) for center in kmeans.cluster_centers_]
    
    def _calculate_cluster_coherence(self, cluster: StyleCluster) -> float:
        """Calculate how coherent/similar images in cluster are."""
        if len(cluster.fingerprints) < 2:
            return 1.0
        
        # Calculate average pairwise similarity
        similarities = []
        for i in range(len(cluster.fingerprints)):
            for j in range(i + 1, len(cluster.fingerprints)):
                sim = cluster.fingerprints[i].similarity_score(cluster.fingerprints[j])
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _generate_cluster_name(self, cluster: StyleCluster) -> str:
        """Generate descriptive name for style cluster."""
        summary = cluster.style_summary
        
        # Build name from key characteristics
        parts = []
        
        # Add color temperature
        if summary.get("color_temperatures"):
            parts.append(summary["color_temperatures"][0].title())
        
        # Add lighting mood
        if summary.get("lighting_moods"):
            mood = summary["lighting_moods"][0]
            if mood != "neutral":
                parts.append(mood.title())
        
        # Add composition type
        if summary.get("composition_types"):
            comp = summary["composition_types"][0]
            if comp != "medium":
                parts.append(comp.title())
        
        if parts:
            return " ".join(parts[:2]) + " Style"
        else:
            return f"Style Group {cluster.id.split('_')[-1]}"
    
    def extract_style_transfer_hints(self, cluster: StyleCluster) -> List[StyleTransferHint]:
        """Extract hints for recreating the cluster's style.
        
        Args:
            cluster: Style cluster to analyze
            
        Returns:
            List of style transfer hints
        """
        hints = []
        
        # Analyze centroid image for main style
        if cluster.centroid_image and cluster.centroid_image in self.fingerprints:
            centroid_fp = self.fingerprints[cluster.centroid_image]
            
            hint = StyleTransferHint(source_image=cluster.centroid_image)
            
            # Extract style elements
            hint.style_elements = {
                "color_scheme": centroid_fp.color_palette.temperature,
                "lighting": centroid_fp.lighting.mood_lighting,
                "composition": centroid_fp.composition.complexity,
                "texture": centroid_fp.texture.overall_texture,
                "contrast": centroid_fp.lighting.contrast_level
            }
            
            # Generate prompt fragments
            fragments = []
            
            # Color prompts
            if centroid_fp.color_palette.temperature == "warm":
                fragments.append("warm color palette")
            elif centroid_fp.color_palette.temperature == "cool":
                fragments.append("cool tones")
            
            if centroid_fp.color_palette.saturation == "vibrant":
                fragments.append("vibrant colors")
            elif centroid_fp.color_palette.saturation == "muted":
                fragments.append("muted colors")
            
            # Lighting prompts
            if centroid_fp.lighting.mood_lighting == "dramatic":
                fragments.append("dramatic lighting")
            elif centroid_fp.lighting.mood_lighting == "soft":
                fragments.append("soft lighting")
            
            if centroid_fp.lighting.contrast_level == "high":
                fragments.append("high contrast")
            
            # Composition prompts
            if centroid_fp.composition.rule_of_thirds > 0.7:
                fragments.append("rule of thirds composition")
            
            if centroid_fp.composition.negative_space_ratio > 0.5:
                fragments.append("minimalist composition")
            
            hint.prompt_fragments = fragments
            
            # Extract color palette
            hint.color_palette = centroid_fp.color_palette.dominant_colors[:3]
            
            # Technical parameters
            hint.technical_params = {
                "suggested_aspect_ratio": self._suggest_aspect_ratio(cluster),
                "complexity_level": centroid_fp.composition.complexity,
                "detail_density": centroid_fp.texture.detail_density
            }
            
            # Calculate success rate based on cluster coherence
            hint.success_rate = cluster.coherence_score
            
            hints.append(hint)
        
        # Extract additional hints from highly coherent sub-groups
        sub_hints = self._extract_subgroup_hints(cluster)
        hints.extend(sub_hints)
        
        # Store hints
        for hint in hints:
            self.style_transfer_hints[cluster.id].append(hint)
        
        return hints
    
    def _suggest_aspect_ratio(self, cluster: StyleCluster) -> str:
        """Suggest aspect ratio based on cluster images."""
        # This would analyze actual image dimensions
        # Simplified for now
        return "16:9"  # Default
    
    def _extract_subgroup_hints(self, cluster: StyleCluster) -> List[StyleTransferHint]:
        """Extract hints from coherent subgroups within cluster."""
        hints = []
        
        # Find images with very similar specific elements
        # For example, all images with same color temperature AND lighting
        style_groups = defaultdict(list)
        
        for i, fp in enumerate(cluster.fingerprints):
            key = (
                fp.color_palette.temperature,
                fp.lighting.mood_lighting,
                fp.composition.complexity
            )
            style_groups[key].append(i)
        
        # Create hints for significant subgroups
        for style_key, indices in style_groups.items():
            if len(indices) >= 2:  # At least 2 images with same style
                # Use first image as example
                idx = indices[0]
                fp = cluster.fingerprints[idx]
                
                hint = StyleTransferHint(source_image=cluster.images[idx])
                
                # Very specific style elements
                temp, mood, comp = style_key
                hint.style_elements = {
                    "exact_temperature": temp,
                    "exact_mood": mood,
                    "exact_complexity": comp
                }
                
                # More specific prompts
                hint.prompt_fragments = [
                    f"{temp} color temperature",
                    f"{mood} lighting mood",
                    f"{comp} composition"
                ]
                
                hint.color_palette = fp.color_palette.dominant_colors[:3]
                hint.success_rate = 0.9  # High success for specific matches
                
                hints.append(hint)
        
        return hints[:3]  # Limit to top 3 subgroup hints
    
    def build_auto_collections(self, min_collection_size: int = 5) -> Dict[str, List[str]]:
        """Build automatic collections from style clusters.
        
        Args:
            min_collection_size: Minimum images for a collection
            
        Returns:
            Dict mapping collection names to image lists
        """
        collections = {}
        
        for cluster_id, cluster in self.clusters.items():
            if cluster.size >= min_collection_size and cluster.coherence_score > 0.7:
                collection_name = cluster.name
                collections[collection_name] = cluster.images
        
        # Also create collections based on specific style elements
        element_collections = self._build_element_collections()
        collections.update(element_collections)
        
        return collections
    
    def _build_element_collections(self) -> Dict[str, List[str]]:
        """Build collections based on specific style elements."""
        collections = defaultdict(list)
        
        # Group by specific characteristics
        for path, fp in self.fingerprints.items():
            # Color-based collections
            if fp.color_palette.temperature == "warm":
                collections["Warm Tones"].append(path)
            elif fp.color_palette.temperature == "cool":
                collections["Cool Tones"].append(path)
            
            # Mood-based collections
            if fp.lighting.mood_lighting == "dramatic":
                collections["Dramatic Lighting"].append(path)
            elif fp.lighting.mood_lighting == "soft":
                collections["Soft Light"].append(path)
            
            # Composition-based collections
            if fp.composition.negative_space_ratio > 0.6:
                collections["Minimalist"].append(path)
            elif fp.composition.complexity == "complex":
                collections["Complex Compositions"].append(path)
            
            # Time-based collections
            if fp.lighting.time_of_day == "golden_hour":
                collections["Golden Hour"].append(path)
            elif fp.lighting.time_of_day == "blue_hour":
                collections["Blue Hour"].append(path)
        
        # Filter out small collections
        return {
            name: images 
            for name, images in collections.items() 
            if len(images) >= 5
        }
    
    def get_style_compatibility(self, image_paths: List[Path]) -> float:
        """Calculate style compatibility score for a set of images.
        
        Args:
            image_paths: Images to check compatibility
            
        Returns:
            Compatibility score (0-1)
        """
        if len(image_paths) < 2:
            return 1.0
        
        # Get fingerprints
        fingerprints = []
        for path in image_paths:
            if str(path) in self.fingerprints:
                fingerprints.append(self.fingerprints[str(path)])
        
        if len(fingerprints) < 2:
            return 0.0
        
        # Calculate average pairwise similarity
        similarities = []
        for i in range(len(fingerprints)):
            for j in range(i + 1, len(fingerprints)):
                sim = fingerprints[i].similarity_score(fingerprints[j])
                similarities.append(sim)
        
        return np.mean(similarities)
    
    def suggest_style_combinations(self, base_image: Path, 
                                 candidates: List[Path]) -> List[Tuple[str, float]]:
        """Suggest which images work well with a base image style.
        
        Args:
            base_image: Reference image
            candidates: Candidate images to evaluate
            
        Returns:
            List of (image_path, compatibility_score) tuples
        """
        suggestions = []
        
        # Get base fingerprint
        base_fp = None
        if str(base_image) in self.fingerprints:
            base_fp = self.fingerprints[str(base_image)]
        
        if not base_fp:
            return []
        
        # Evaluate each candidate
        for candidate in candidates:
            if str(candidate) in self.fingerprints:
                candidate_fp = self.fingerprints[str(candidate)]
                
                # Calculate compatibility
                similarity = base_fp.similarity_score(candidate_fp)
                
                # Bonus for complementary elements
                if base_fp.color_palette.temperature != candidate_fp.color_palette.temperature:
                    # Complementary temperatures can work well
                    similarity *= 1.1
                
                suggestions.append((str(candidate), min(similarity, 1.0)))
        
        # Sort by compatibility
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions