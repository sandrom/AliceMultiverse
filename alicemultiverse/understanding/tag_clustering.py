"""Tag clustering system for automatic grouping of similar concepts.

This module provides intelligent clustering of tags based on co-occurrence,
semantic similarity, and usage patterns.
"""

import json
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import numpy as np
from sklearn.cluster import DBSCAN

from .tag_hierarchy import TagHierarchy

logger = logging.getLogger(__name__)


@dataclass
class TagCluster:
    """A cluster of related tags."""
    
    id: str
    name: str
    tags: Set[str] = field(default_factory=set)
    centroid_tag: Optional[str] = None  # Most representative tag
    confidence: float = 1.0
    category: Optional[str] = None
    
    def add_tag(self, tag: str):
        """Add a tag to the cluster."""
        self.tags.add(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the cluster."""
        self.tags.discard(tag)
    
    @property
    def size(self) -> int:
        """Number of tags in cluster."""
        return len(self.tags)


class TagClusteringSystem:
    """Intelligent tag clustering based on usage patterns and semantics."""
    
    def __init__(self, hierarchy: Optional[TagHierarchy] = None):
        """Initialize clustering system.
        
        Args:
            hierarchy: Optional tag hierarchy for semantic information
        """
        self.hierarchy = hierarchy or TagHierarchy()
        self.clusters: Dict[str, TagCluster] = {}
        self.tag_to_cluster: Dict[str, str] = {}
        self.co_occurrence: Dict[Tuple[str, str], int] = defaultdict(int)
        self.tag_frequency: Counter = Counter()
        
        # Predefined conceptual clusters
        self._initialize_concept_clusters()
    
    def _initialize_concept_clusters(self):
        """Initialize with predefined conceptual clusters."""
        concepts = {
            "lighting_conditions": {
                "tags": {"sunset", "sunrise", "golden_hour", "blue_hour", 
                        "daylight", "night", "overcast", "backlit"},
                "category": "technical"
            },
            "artistic_medium": {
                "tags": {"oil_painting", "watercolor", "acrylic", "digital_art",
                        "pencil_drawing", "charcoal", "pastel", "ink"},
                "category": "style"
            },
            "photographic_style": {
                "tags": {"portrait", "landscape", "street", "macro", "aerial",
                        "documentary", "fashion", "architectural"},
                "category": "style"
            },
            "emotional_tone": {
                "tags": {"happy", "sad", "melancholic", "joyful", "peaceful",
                        "dramatic", "mysterious", "ethereal"},
                "category": "mood"
            },
            "color_temperature": {
                "tags": {"warm", "cool", "neutral", "vibrant", "muted",
                        "pastel", "monochrome", "colorful"},
                "category": "color"
            },
            "time_period": {
                "tags": {"modern", "vintage", "retro", "futuristic", "ancient",
                        "medieval", "renaissance", "contemporary"},
                "category": "style"
            },
            "composition": {
                "tags": {"centered", "rule_of_thirds", "symmetrical", "asymmetrical",
                        "minimalist", "busy", "layered", "geometric"},
                "category": "technical"
            }
        }
        
        for cluster_id, data in concepts.items():
            cluster = TagCluster(
                id=cluster_id,
                name=cluster_id.replace("_", " ").title(),
                tags=data["tags"],
                category=data["category"]
            )
            self.clusters[cluster_id] = cluster
            
            # Update tag-to-cluster mapping
            for tag in data["tags"]:
                self.tag_to_cluster[tag] = cluster_id
    
    def update_co_occurrence(self, tag_sets: List[Set[str]]):
        """Update co-occurrence matrix from tag sets.
        
        Args:
            tag_sets: List of tag sets from analyzed images
        """
        for tags in tag_sets:
            # Update frequency
            self.tag_frequency.update(tags)
            
            # Update co-occurrence
            tag_list = sorted(tags)  # Consistent ordering
            for i, tag1 in enumerate(tag_list):
                for tag2 in tag_list[i+1:]:
                    key = (tag1, tag2) if tag1 < tag2 else (tag2, tag1)
                    self.co_occurrence[key] += 1
    
    def compute_tag_similarity(self, tag1: str, tag2: str) -> float:
        """Compute similarity between two tags.
        
        Args:
            tag1: First tag
            tag2: Second tag
            
        Returns:
            Similarity score (0-1)
        """
        # Normalize tags
        tag1 = self.hierarchy.normalize_tag(tag1)
        tag2 = self.hierarchy.normalize_tag(tag2)
        
        if tag1 == tag2:
            return 1.0
        
        similarity = 0.0
        
        # Co-occurrence similarity
        key = (tag1, tag2) if tag1 < tag2 else (tag2, tag1)
        if key in self.co_occurrence:
            freq1 = self.tag_frequency.get(tag1, 1)
            freq2 = self.tag_frequency.get(tag2, 1)
            co_freq = self.co_occurrence[key]
            
            # Jaccard similarity
            similarity += 0.4 * (co_freq / (freq1 + freq2 - co_freq))
        
        # Hierarchical similarity
        if self.hierarchy:
            # Check if one is ancestor of other
            if tag2 in self.hierarchy.get_ancestors(tag1):
                similarity += 0.3
            elif tag1 in self.hierarchy.get_ancestors(tag2):
                similarity += 0.3
            
            # Check if they share ancestors
            ancestors1 = set(self.hierarchy.get_ancestors(tag1))
            ancestors2 = set(self.hierarchy.get_ancestors(tag2))
            if ancestors1 and ancestors2:
                shared = len(ancestors1 & ancestors2)
                total = len(ancestors1 | ancestors2)
                similarity += 0.2 * (shared / total)
            
            # Check if they're related
            related1 = self.hierarchy.get_related(tag1)
            if tag2 in related1:
                similarity += 0.1 * related1[tag2]
        
        return min(similarity, 1.0)
    
    def cluster_tags_by_similarity(self, tags: List[str], 
                                  min_similarity: float = 0.5) -> List[TagCluster]:
        """Cluster tags based on similarity.
        
        Args:
            tags: List of tags to cluster
            min_similarity: Minimum similarity for clustering
            
        Returns:
            List of tag clusters
        """
        if not tags:
            return []
        
        # Compute similarity matrix
        n_tags = len(tags)
        similarity_matrix = np.zeros((n_tags, n_tags))
        
        for i in range(n_tags):
            for j in range(i, n_tags):
                sim = self.compute_tag_similarity(tags[i], tags[j])
                similarity_matrix[i, j] = sim
                similarity_matrix[j, i] = sim
        
        # Convert to distance matrix
        distance_matrix = 1 - similarity_matrix
        
        # Cluster using DBSCAN
        clustering = DBSCAN(
            eps=1-min_similarity,
            min_samples=2,
            metric='precomputed'
        ).fit(distance_matrix)
        
        # Create clusters
        clusters = []
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:  # Noise points
                continue
            
            cluster_indices = np.where(clustering.labels_ == cluster_id)[0]
            cluster_tags = {tags[i] for i in cluster_indices}
            
            # Find centroid tag (most connected)
            centroid_idx = cluster_indices[0]
            max_sim = 0
            for idx in cluster_indices:
                total_sim = sum(similarity_matrix[idx, i] for i in cluster_indices)
                if total_sim > max_sim:
                    max_sim = total_sim
                    centroid_idx = idx
            
            cluster = TagCluster(
                id=f"auto_{cluster_id}",
                name=f"Cluster {cluster_id}",
                tags=cluster_tags,
                centroid_tag=tags[centroid_idx],
                confidence=float(np.mean([
                    similarity_matrix[i, j]
                    for i in cluster_indices
                    for j in cluster_indices
                    if i != j
                ]))
            )
            clusters.append(cluster)
        
        return clusters
    
    def suggest_cluster_names(self, cluster: TagCluster) -> List[str]:
        """Suggest names for a tag cluster.
        
        Args:
            cluster: Tag cluster
            
        Returns:
            List of suggested names
        """
        suggestions = []
        
        # Use hierarchy to find common ancestors
        if self.hierarchy:
            common_ancestors = self.hierarchy.find_common_ancestors(list(cluster.tags))
            for ancestor, count in common_ancestors[:3]:
                if count >= len(cluster.tags) * 0.5:
                    suggestions.append(ancestor.replace("_", " ").title())
        
        # Use centroid tag
        if cluster.centroid_tag:
            suggestions.append(f"{cluster.centroid_tag.replace('_', ' ').title()} Group")
        
        # Find common substrings
        if len(cluster.tags) > 2:
            common = self._find_common_substring(list(cluster.tags))
            if common and len(common) > 3:
                suggestions.append(common.title())
        
        return suggestions
    
    def _find_common_substring(self, strings: List[str]) -> str:
        """Find longest common substring in a list of strings."""
        if not strings:
            return ""
        
        shortest = min(strings, key=len)
        for length in range(len(shortest), 0, -1):
            for start in range(len(shortest) - length + 1):
                substr = shortest[start:start + length]
                if all(substr in s for s in strings):
                    return substr
        
        return ""
    
    def merge_clusters(self, cluster_ids: List[str], new_name: str) -> TagCluster:
        """Merge multiple clusters into one.
        
        Args:
            cluster_ids: IDs of clusters to merge
            new_name: Name for merged cluster
            
        Returns:
            Merged cluster
        """
        merged_tags = set()
        categories = []
        
        for cluster_id in cluster_ids:
            if cluster_id in self.clusters:
                cluster = self.clusters[cluster_id]
                merged_tags.update(cluster.tags)
                if cluster.category:
                    categories.append(cluster.category)
                
                # Remove old cluster
                del self.clusters[cluster_id]
        
        # Create new cluster
        new_id = f"merged_{len(self.clusters)}"
        merged_cluster = TagCluster(
            id=new_id,
            name=new_name,
            tags=merged_tags,
            category=Counter(categories).most_common(1)[0][0] if categories else None
        )
        
        self.clusters[new_id] = merged_cluster
        
        # Update tag mappings
        for tag in merged_tags:
            self.tag_to_cluster[tag] = new_id
        
        return merged_cluster
    
    def auto_cluster_new_tags(self, new_tags: Set[str]) -> Dict[str, str]:
        """Automatically assign new tags to existing clusters.
        
        Args:
            new_tags: Set of new tags
            
        Returns:
            Mapping of tag to cluster ID
        """
        assignments = {}
        
        for tag in new_tags:
            best_cluster = None
            best_score = 0.0
            
            # Check similarity to existing clusters
            for cluster_id, cluster in self.clusters.items():
                # Average similarity to cluster members
                similarities = [
                    self.compute_tag_similarity(tag, cluster_tag)
                    for cluster_tag in cluster.tags
                ]
                avg_similarity = np.mean(similarities) if similarities else 0
                
                if avg_similarity > best_score and avg_similarity > 0.5:
                    best_score = avg_similarity
                    best_cluster = cluster_id
            
            if best_cluster:
                assignments[tag] = best_cluster
                self.clusters[best_cluster].add_tag(tag)
                self.tag_to_cluster[tag] = best_cluster
        
        return assignments
    
    def get_cluster_statistics(self) -> Dict[str, Dict]:
        """Get statistics about current clusters.
        
        Returns:
            Dictionary of cluster statistics
        """
        stats = {}
        
        for cluster_id, cluster in self.clusters.items():
            stats[cluster_id] = {
                "name": cluster.name,
                "size": cluster.size,
                "tags": sorted(cluster.tags),
                "centroid": cluster.centroid_tag,
                "category": cluster.category,
                "confidence": cluster.confidence
            }
        
        return stats
    
    def export_clusters(self, path: Path):
        """Export clusters to JSON file.
        
        Args:
            path: Output file path
        """
        data = {
            "clusters": {
                cluster_id: {
                    "name": cluster.name,
                    "tags": sorted(cluster.tags),
                    "centroid_tag": cluster.centroid_tag,
                    "confidence": cluster.confidence,
                    "category": cluster.category
                }
                for cluster_id, cluster in self.clusters.items()
            },
            "tag_to_cluster": self.tag_to_cluster,
            "statistics": self.get_cluster_statistics()
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_clusters(self, path: Path):
        """Import clusters from JSON file.
        
        Args:
            path: Input file path
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Clear existing
        self.clusters.clear()
        self.tag_to_cluster.clear()
        
        # Import clusters
        for cluster_id, cluster_data in data.get("clusters", {}).items():
            cluster = TagCluster(
                id=cluster_id,
                name=cluster_data["name"],
                tags=set(cluster_data["tags"]),
                centroid_tag=cluster_data.get("centroid_tag"),
                confidence=cluster_data.get("confidence", 1.0),
                category=cluster_data.get("category")
            )
            self.clusters[cluster_id] = cluster
        
        # Import mappings
        self.tag_to_cluster = data.get("tag_to_cluster", {})