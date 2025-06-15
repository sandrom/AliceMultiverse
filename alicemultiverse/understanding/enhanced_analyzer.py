"""Enhanced image analyzer with intelligent tag hierarchies.

This module integrates tag hierarchy, clustering, and taxonomy management
into the image analysis pipeline for better organization and discovery.
"""

import logging
from collections import defaultdict
from pathlib import Path

from .analyzer import ImageAnalyzer
from .taxonomy_manager import TaxonomyManager

logger = logging.getLogger(__name__)


class EnhancedImageAnalyzer:
    """Image analyzer with intelligent tag management."""

    def __init__(self, taxonomy_dir: Path | None = None):
        """Initialize enhanced analyzer.
        
        Args:
            taxonomy_dir: Directory for storing taxonomies
        """
        self.analyzer = ImageAnalyzer()
        self.taxonomy = TaxonomyManager(taxonomy_dir)
        self.tag_history: list[set[str]] = []  # For co-occurrence learning

    async def analyze_with_hierarchy(
        self,
        image_path: Path | str,
        provider: str | None = None,
        project_id: str | None = None,
        expand_tags: bool = True,
        cluster_tags: bool = True
    ) -> dict[str, any]:
        """Analyze image with hierarchical tag enhancement.
        
        Args:
            image_path: Path to image
            provider: Specific provider to use
            project_id: Optional project ID for project-specific tags
            expand_tags: Whether to expand tags with hierarchy
            cluster_tags: Whether to cluster similar tags
            
        Returns:
            Enhanced analysis result
        """
        # Get base analysis
        result = await self.analyzer.analyze(
            image_path,
            provider=provider,
            extract_tags=True,
            generate_prompt=True
        )

        # Extract all tags from categories
        all_tags = []
        if isinstance(result.tags, dict):
            for category, tags in result.tags.items():
                all_tags.extend(tags)
        elif isinstance(result.tags, list):
            all_tags = result.tags

        # Normalize tags
        normalized_tags = [
            self.taxonomy.hierarchy.normalize_tag(tag)
            for tag in all_tags
        ]

        # Build enhanced result
        enhanced = {
            "original_analysis": result,
            "normalized_tags": normalized_tags,
            "hierarchical_tags": {},
            "tag_clusters": [],
            "suggested_tags": [],
            "tag_statistics": {}
        }

        # Expand tags with hierarchy
        if expand_tags:
            expanded = self.taxonomy.hierarchy.expand_tags(
                normalized_tags,
                include_ancestors=True,
                include_related=True
            )
            enhanced["expanded_tags"] = sorted(expanded)

            # Group by hierarchy
            for tag in normalized_tags:
                ancestors = self.taxonomy.hierarchy.get_ancestors(tag)
                if ancestors:
                    enhanced["hierarchical_tags"][tag] = ancestors

        # Cluster tags
        if cluster_tags and len(normalized_tags) > 3:
            clusters = self.taxonomy.clustering.cluster_tags_by_similarity(
                normalized_tags,
                min_similarity=0.5
            )
            enhanced["tag_clusters"] = [
                {
                    "name": self.taxonomy.clustering.suggest_cluster_names(cluster)[0]
                            if self.taxonomy.clustering.suggest_cluster_names(cluster)
                            else f"Cluster {i}",
                    "tags": sorted(cluster.tags),
                    "centroid": cluster.centroid_tag,
                    "confidence": cluster.confidence
                }
                for i, cluster in enumerate(clusters)
            ]

        # Add to project if specified
        if project_id:
            self.taxonomy.add_project_tags(project_id, normalized_tags)

            # Get project-specific suggestions
            suggestions = self.taxonomy.suggest_project_tags(
                project_id,
                normalized_tags
            )
            enhanced["suggested_tags"] = suggestions

        # Update co-occurrence data
        self.tag_history.append(set(normalized_tags))
        if len(self.tag_history) > 100:  # Keep last 100 for memory
            self.tag_history.pop(0)

        # Update clustering system with co-occurrence
        self.taxonomy.clustering.update_co_occurrence([set(normalized_tags)])

        # Calculate tag statistics
        enhanced["tag_statistics"] = {
            "total_tags": len(normalized_tags),
            "unique_categories": len(set(
                self.taxonomy.hierarchy.nodes[tag].category
                for tag in normalized_tags
                if tag in self.taxonomy.hierarchy.nodes and
                self.taxonomy.hierarchy.nodes[tag].category
            )),
            "hierarchy_depth": max(
                len(self.taxonomy.hierarchy.get_ancestors(tag))
                for tag in normalized_tags
            ) if normalized_tags else 0,
            "coherence_score": self.taxonomy._calculate_coherence(set(normalized_tags))
        }

        return enhanced

    async def analyze_batch_with_clustering(
        self,
        image_paths: list[Path | str],
        provider: str | None = None,
        auto_cluster: bool = True,
        min_cluster_size: int = 3
    ) -> dict[str, any]:
        """Analyze batch of images and auto-cluster by tags.
        
        Args:
            image_paths: List of image paths
            provider: Provider to use
            auto_cluster: Whether to auto-cluster results
            min_cluster_size: Minimum images per cluster
            
        Returns:
            Batch analysis with clustering
        """
        # Analyze all images
        results = []
        all_tag_sets = []

        for path in image_paths:
            try:
                enhanced = await self.analyze_with_hierarchy(
                    path,
                    provider=provider,
                    expand_tags=False,  # Don't expand for clustering
                    cluster_tags=False  # We'll cluster across images
                )
                results.append({
                    "path": str(path),
                    "tags": enhanced["normalized_tags"],
                    "analysis": enhanced
                })
                all_tag_sets.append(set(enhanced["normalized_tags"]))
            except Exception as e:
                logger.error(f"Failed to analyze {path}: {e}")
                results.append({
                    "path": str(path),
                    "error": str(e)
                })

        # Update co-occurrence from batch
        if all_tag_sets:
            self.taxonomy.clustering.update_co_occurrence(all_tag_sets)

        # Build result
        batch_result = {
            "images_analyzed": len([r for r in results if "tags" in r]),
            "images_failed": len([r for r in results if "error" in r]),
            "results": results,
            "image_clusters": [],
            "tag_frequency": defaultdict(int),
            "common_themes": []
        }

        # Calculate tag frequency
        for result in results:
            if "tags" in result:
                for tag in result["tags"]:
                    batch_result["tag_frequency"][tag] += 1

        # Auto-cluster images by tag similarity
        if auto_cluster and len([r for r in results if "tags" in r]) >= min_cluster_size:
            image_clusters = self._cluster_images_by_tags(
                [(r["path"], set(r["tags"])) for r in results if "tags" in r],
                min_cluster_size
            )
            batch_result["image_clusters"] = image_clusters

        # Find common themes
        common_tags = [
            tag for tag, count in batch_result["tag_frequency"].items()
            if count >= len(results) * 0.3  # Present in 30%+ of images
        ]
        if common_tags:
            # Group common tags by category
            categorized = self.taxonomy.hierarchy.group_by_category(common_tags)
            batch_result["common_themes"] = categorized

        return batch_result

    def _cluster_images_by_tags(
        self,
        image_tags: list[tuple[str, set[str]]],
        min_cluster_size: int
    ) -> list[dict]:
        """Cluster images based on tag similarity.
        
        Args:
            image_tags: List of (image_path, tag_set) tuples
            min_cluster_size: Minimum cluster size
            
        Returns:
            List of image clusters
        """
        if len(image_tags) < min_cluster_size:
            return []

        # Build similarity matrix
        n_images = len(image_tags)
        similarity_matrix = [[0.0] * n_images for _ in range(n_images)]

        for i in range(n_images):
            for j in range(i, n_images):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                else:
                    # Jaccard similarity
                    tags_i = image_tags[i][1]
                    tags_j = image_tags[j][1]
                    if tags_i or tags_j:
                        intersection = len(tags_i & tags_j)
                        union = len(tags_i | tags_j)
                        sim = intersection / union if union > 0 else 0
                        similarity_matrix[i][j] = sim
                        similarity_matrix[j][i] = sim

        # Find clusters (simple greedy approach)
        clusters = []
        assigned = set()

        for i in range(n_images):
            if i in assigned:
                continue

            # Start new cluster
            cluster_members = [i]
            assigned.add(i)

            # Find similar images
            for j in range(n_images):
                if j in assigned:
                    continue

                # Check similarity to cluster members
                avg_sim = sum(
                    similarity_matrix[j][member]
                    for member in cluster_members
                ) / len(cluster_members)

                if avg_sim >= 0.5:  # 50% average similarity
                    cluster_members.append(j)
                    assigned.add(j)

            if len(cluster_members) >= min_cluster_size:
                # Get cluster info
                cluster_paths = [image_tags[i][0] for i in cluster_members]
                cluster_tags = set()
                for i in cluster_members:
                    cluster_tags.update(image_tags[i][1])

                # Find most common tags
                tag_counts = defaultdict(int)
                for i in cluster_members:
                    for tag in image_tags[i][1]:
                        tag_counts[tag] += 1

                common_tags = [
                    tag for tag, count in tag_counts.items()
                    if count >= len(cluster_members) * 0.5
                ]

                clusters.append({
                    "id": f"cluster_{len(clusters)}",
                    "size": len(cluster_members),
                    "images": cluster_paths,
                    "common_tags": sorted(common_tags),
                    "all_tags": sorted(cluster_tags),
                    "suggested_name": self._suggest_cluster_name(common_tags)
                })

        return clusters

    def _suggest_cluster_name(self, tags: list[str]) -> str:
        """Suggest a name for an image cluster based on tags."""
        if not tags:
            return "Unnamed Cluster"

        # Find common ancestors
        common_ancestors = self.taxonomy.hierarchy.find_common_ancestors(tags)
        if common_ancestors:
            ancestor, count = common_ancestors[0]
            if count >= len(tags) * 0.5:
                return ancestor.replace("_", " ").title()

        # Use most important tag
        tag_weights = []
        for tag in tags:
            if tag in self.taxonomy.hierarchy.nodes:
                weight = self.taxonomy.hierarchy.nodes[tag].weight
                ancestors = len(self.taxonomy.hierarchy.get_ancestors(tag))
                tag_weights.append((tag, weight * (1 + ancestors * 0.1)))
            else:
                tag_weights.append((tag, 1.0))

        if tag_weights:
            tag_weights.sort(key=lambda x: x[1], reverse=True)
            return tag_weights[0][0].replace("_", " ").title() + " Collection"

        return "Mixed Collection"

    def create_mood_board_from_analysis(
        self,
        name: str,
        image_analyses: list[dict],
        description: str = ""
    ) -> str:
        """Create a mood board from analyzed images.
        
        Args:
            name: Mood board name
            image_analyses: List of enhanced analysis results
            description: Mood board description
            
        Returns:
            Mood board ID
        """
        board = self.taxonomy.create_mood_board(name, description)

        # Collect all tags
        all_tags = set()
        reference_images = []

        for analysis in image_analyses:
            if "normalized_tags" in analysis:
                all_tags.update(analysis["normalized_tags"])
            if "path" in analysis.get("original_analysis", {}):
                reference_images.append(analysis["original_analysis"]["path"])

        # Add to mood board
        self.taxonomy.add_to_mood_board(
            board.id,
            tags=list(all_tags),
            reference_images=reference_images
        )

        return board.id

    def get_tag_insights(self) -> dict[str, any]:
        """Get insights about tag usage and patterns.
        
        Returns:
            Dictionary of tag insights
        """
        insights = {
            "taxonomy_summary": self.taxonomy.get_taxonomy_summary(),
            "co_occurrence_patterns": [],
            "tag_evolution": [],
            "clustering_quality": 0.0
        }

        # Top co-occurring tag pairs
        top_pairs = sorted(
            self.taxonomy.clustering.co_occurrence.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        insights["co_occurrence_patterns"] = [
            {
                "tags": list(pair),
                "count": count,
                "similarity": self.taxonomy.clustering.compute_tag_similarity(
                    pair[0], pair[1]
                )
            }
            for pair, count in top_pairs
        ]

        # Tag frequency over time (simplified)
        if self.tag_history:
            recent_tags = defaultdict(list)
            for i, tag_set in enumerate(self.tag_history[-20:]):  # Last 20
                for tag in tag_set:
                    recent_tags[tag].append(i)

            # Find trending tags
            trending = []
            for tag, positions in recent_tags.items():
                if len(positions) >= 3:  # Appears in at least 3 recent sets
                    # Simple trend: more recent = higher score
                    trend_score = sum(pos for pos in positions) / len(positions)
                    trending.append((tag, trend_score))

            insights["tag_evolution"] = [
                {"tag": tag, "trend_score": score}
                for tag, score in sorted(trending, key=lambda x: x[1], reverse=True)[:10]
            ]

        # Overall clustering quality
        if self.taxonomy.clustering.clusters:
            qualities = [
                cluster.confidence
                for cluster in self.taxonomy.clustering.clusters.values()
            ]
            insights["clustering_quality"] = sum(qualities) / len(qualities)

        return insights
