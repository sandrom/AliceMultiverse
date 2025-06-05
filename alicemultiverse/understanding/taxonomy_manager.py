"""Custom taxonomy manager for personal tag organization.

This module allows creating project-specific tag groups, mood boards as
tag collections, and import/export of custom tag schemes.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict, Counter

from .tag_hierarchy import TagHierarchy
from .tag_clustering import TagClusteringSystem, TagCluster

logger = logging.getLogger(__name__)


@dataclass
class TagCollection:
    """A collection of tags for a specific purpose."""
    
    id: str
    name: str
    description: str
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_tags(self, tags: List[str]):
        """Add tags to collection."""
        self.tags.update(tags)
        self.updated_at = datetime.now()
    
    def remove_tags(self, tags: List[str]):
        """Remove tags from collection."""
        self.tags.difference_update(tags)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": sorted(self.tags),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TagCollection':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            tags=set(data["tags"]),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class MoodBoard:
    """A mood board combining tags, colors, and style references."""
    
    id: str
    name: str
    description: str
    tags: Set[str] = field(default_factory=set)
    colors: List[str] = field(default_factory=list)  # Hex colors
    reference_images: List[str] = field(default_factory=list)  # Image paths
    style_notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class TaxonomyManager:
    """Manages custom taxonomies and tag organizations."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize taxonomy manager.
        
        Args:
            base_dir: Base directory for storing taxonomies
        """
        self.base_dir = base_dir or Path.home() / ".alice" / "taxonomies"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.hierarchy = TagHierarchy()
        self.clustering = TagClusteringSystem(self.hierarchy)
        
        # Collections
        self.project_tags: Dict[str, TagCollection] = {}
        self.mood_boards: Dict[str, MoodBoard] = {}
        self.tag_schemes: Dict[str, Dict] = {}
        
        self._load_saved_taxonomies()
    
    def _load_saved_taxonomies(self):
        """Load saved taxonomies from disk."""
        # Load project tags
        project_file = self.base_dir / "project_tags.json"
        if project_file.exists():
            with open(project_file, 'r') as f:
                data = json.load(f)
                for proj_id, proj_data in data.items():
                    self.project_tags[proj_id] = TagCollection.from_dict(proj_data)
        
        # Load mood boards
        mood_file = self.base_dir / "mood_boards.json"
        if mood_file.exists():
            with open(mood_file, 'r') as f:
                data = json.load(f)
                for board_id, board_data in data.items():
                    self.mood_boards[board_id] = MoodBoard(**board_data)
        
        # Load custom schemes
        schemes_dir = self.base_dir / "schemes"
        if schemes_dir.exists():
            for scheme_file in schemes_dir.glob("*.json"):
                scheme_name = scheme_file.stem
                with open(scheme_file, 'r') as f:
                    self.tag_schemes[scheme_name] = json.load(f)
    
    def save_taxonomies(self):
        """Save all taxonomies to disk."""
        # Save project tags
        project_data = {
            proj_id: collection.to_dict()
            for proj_id, collection in self.project_tags.items()
        }
        with open(self.base_dir / "project_tags.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Save mood boards
        mood_data = {
            board_id: board.to_dict()
            for board_id, board in self.mood_boards.items()
        }
        with open(self.base_dir / "mood_boards.json", 'w') as f:
            json.dump(mood_data, f, indent=2, default=str)
        
        # Save schemes
        schemes_dir = self.base_dir / "schemes"
        schemes_dir.mkdir(exist_ok=True)
        for scheme_name, scheme_data in self.tag_schemes.items():
            with open(schemes_dir / f"{scheme_name}.json", 'w') as f:
                json.dump(scheme_data, f, indent=2)
    
    # Project-specific tag management
    
    def create_project_tags(self, project_id: str, name: str, 
                          description: str = "") -> TagCollection:
        """Create a new project tag collection.
        
        Args:
            project_id: Unique project identifier
            name: Project name
            description: Project description
            
        Returns:
            Created tag collection
        """
        collection = TagCollection(
            id=project_id,
            name=name,
            description=description
        )
        self.project_tags[project_id] = collection
        self.save_taxonomies()
        return collection
    
    def add_project_tags(self, project_id: str, tags: List[str]):
        """Add tags to a project.
        
        Args:
            project_id: Project identifier
            tags: Tags to add
        """
        if project_id not in self.project_tags:
            self.create_project_tags(project_id, project_id)
        
        self.project_tags[project_id].add_tags(tags)
        self.save_taxonomies()
    
    def get_project_tags(self, project_id: str) -> Set[str]:
        """Get tags for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Set of project tags
        """
        if project_id in self.project_tags:
            return self.project_tags[project_id].tags
        return set()
    
    def suggest_project_tags(self, project_id: str, 
                           existing_tags: List[str]) -> List[str]:
        """Suggest additional tags for a project based on existing ones.
        
        Args:
            project_id: Project identifier
            existing_tags: Current tags in the project
            
        Returns:
            List of suggested tags
        """
        suggestions = []
        
        # Get related tags from hierarchy
        expanded = self.hierarchy.expand_tags(existing_tags, include_related=True)
        current = set(existing_tags)
        
        # Suggest parent tags
        parent_suggestions = self.hierarchy.suggest_parent_tags(existing_tags)
        suggestions.extend(parent_suggestions)
        
        # Suggest from related tags
        for tag in expanded - current:
            if tag not in suggestions:
                suggestions.append(tag)
        
        # Suggest from similar projects
        similar_tags = self._find_similar_project_tags(project_id, existing_tags)
        for tag in similar_tags:
            if tag not in current and tag not in suggestions:
                suggestions.append(tag)
        
        return suggestions[:10]  # Top 10 suggestions
    
    def _find_similar_project_tags(self, current_project: str, 
                                  current_tags: List[str]) -> List[str]:
        """Find tags from similar projects."""
        similar_tags = Counter()
        current_set = set(current_tags)
        
        for proj_id, collection in self.project_tags.items():
            if proj_id == current_project:
                continue
            
            # Calculate similarity
            overlap = len(current_set & collection.tags)
            if overlap >= len(current_set) * 0.3:  # 30% overlap
                # Add tags from similar project
                for tag in collection.tags - current_set:
                    similar_tags[tag] += overlap
        
        return [tag for tag, _ in similar_tags.most_common(10)]
    
    # Mood board management
    
    def create_mood_board(self, name: str, description: str = "") -> MoodBoard:
        """Create a new mood board.
        
        Args:
            name: Mood board name
            description: Description
            
        Returns:
            Created mood board
        """
        board_id = name.lower().replace(" ", "_")
        board = MoodBoard(
            id=board_id,
            name=name,
            description=description
        )
        self.mood_boards[board_id] = board
        self.save_taxonomies()
        return board
    
    def add_to_mood_board(self, board_id: str, tags: List[str] = None,
                         colors: List[str] = None, 
                         reference_images: List[str] = None):
        """Add elements to a mood board.
        
        Args:
            board_id: Mood board identifier
            tags: Tags to add
            colors: Hex colors to add
            reference_images: Image paths to add
        """
        if board_id not in self.mood_boards:
            return
        
        board = self.mood_boards[board_id]
        
        if tags:
            board.tags.update(tags)
        if colors:
            board.colors.extend(colors)
        if reference_images:
            board.reference_images.extend(reference_images)
        
        self.save_taxonomies()
    
    def analyze_mood_board(self, board_id: str) -> Dict[str, Any]:
        """Analyze a mood board for patterns and suggestions.
        
        Args:
            board_id: Mood board identifier
            
        Returns:
            Analysis results
        """
        if board_id not in self.mood_boards:
            return {}
        
        board = self.mood_boards[board_id]
        
        # Analyze tags
        tag_categories = self.hierarchy.group_by_category(list(board.tags))
        tag_clusters = self.clustering.cluster_tags_by_similarity(list(board.tags))
        
        # Find dominant themes
        dominant_categories = sorted(
            tag_categories.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:3]
        
        # Suggest additional tags
        suggested_tags = []
        for tag in board.tags:
            related = self.hierarchy.get_related(tag)
            for rel_tag, score in related.items():
                if rel_tag not in board.tags and score >= 0.7:
                    suggested_tags.append(rel_tag)
        
        return {
            "tag_count": len(board.tags),
            "color_count": len(board.colors),
            "reference_count": len(board.reference_images),
            "dominant_categories": dominant_categories,
            "tag_clusters": [
                {
                    "name": self.clustering.suggest_cluster_names(cluster)[0],
                    "tags": sorted(cluster.tags),
                    "confidence": cluster.confidence
                }
                for cluster in tag_clusters
            ],
            "suggested_tags": suggested_tags[:10],
            "coherence_score": self._calculate_coherence(board.tags)
        }
    
    def _calculate_coherence(self, tags: Set[str]) -> float:
        """Calculate coherence score for a set of tags."""
        if len(tags) < 2:
            return 1.0
        
        # Average pairwise similarity
        tag_list = list(tags)
        total_sim = 0
        count = 0
        
        for i in range(len(tag_list)):
            for j in range(i + 1, len(tag_list)):
                sim = self.clustering.compute_tag_similarity(tag_list[i], tag_list[j])
                total_sim += sim
                count += 1
        
        return total_sim / count if count > 0 else 0.0
    
    # Custom taxonomy schemes
    
    def create_taxonomy_scheme(self, name: str, description: str = "") -> Dict:
        """Create a custom taxonomy scheme.
        
        Args:
            name: Scheme name
            description: Scheme description
            
        Returns:
            Created scheme
        """
        scheme = {
            "name": name,
            "description": description,
            "hierarchies": {},
            "clusters": {},
            "rules": {},
            "created_at": datetime.now().isoformat()
        }
        self.tag_schemes[name] = scheme
        self.save_taxonomies()
        return scheme
    
    def export_taxonomy_scheme(self, scheme_name: str, output_path: Path):
        """Export a taxonomy scheme.
        
        Args:
            scheme_name: Name of scheme to export
            output_path: Output file path
        """
        if scheme_name not in self.tag_schemes:
            return
        
        scheme = self.tag_schemes[scheme_name].copy()
        
        # Add current hierarchy
        scheme["hierarchies"] = {
            name: {
                "parent": node.parent,
                "children": list(node.children),
                "category": node.category
            }
            for name, node in self.hierarchy.nodes.items()
        }
        
        # Add current clusters
        scheme["clusters"] = {
            cluster_id: {
                "name": cluster.name,
                "tags": sorted(cluster.tags),
                "category": cluster.category
            }
            for cluster_id, cluster in self.clustering.clusters.items()
        }
        
        with open(output_path, 'w') as f:
            json.dump(scheme, f, indent=2)
    
    def import_taxonomy_scheme(self, input_path: Path, merge: bool = False):
        """Import a taxonomy scheme.
        
        Args:
            input_path: Input file path
            merge: Whether to merge with existing or replace
        """
        with open(input_path, 'r') as f:
            scheme = json.load(f)
        
        scheme_name = scheme.get("name", input_path.stem)
        
        if not merge:
            # Clear existing
            self.hierarchy = TagHierarchy()
            self.clustering = TagClusteringSystem(self.hierarchy)
        
        # Import hierarchies
        for tag, node_data in scheme.get("hierarchies", {}).items():
            self.hierarchy.add_tag(
                tag,
                parent=node_data.get("parent"),
                category=node_data.get("category")
            )
        
        # Import clusters
        for cluster_id, cluster_data in scheme.get("clusters", {}).items():
            cluster = TagCluster(
                id=cluster_id,
                name=cluster_data["name"],
                tags=set(cluster_data["tags"]),
                category=cluster_data.get("category")
            )
            self.clustering.clusters[cluster_id] = cluster
            
            # Update mappings
            for tag in cluster.tags:
                self.clustering.tag_to_cluster[tag] = cluster_id
        
        # Save scheme
        self.tag_schemes[scheme_name] = scheme
        self.save_taxonomies()
    
    def get_taxonomy_summary(self) -> Dict[str, Any]:
        """Get summary of current taxonomy state.
        
        Returns:
            Summary statistics
        """
        return {
            "total_tags": len(self.hierarchy.nodes),
            "total_categories": len(self.hierarchy.categories),
            "total_clusters": len(self.clustering.clusters),
            "project_count": len(self.project_tags),
            "mood_board_count": len(self.mood_boards),
            "scheme_count": len(self.tag_schemes),
            "top_categories": [
                (cat, len(tags))
                for cat, tags in sorted(
                    self.hierarchy.categories.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )[:5]
            ],
            "largest_clusters": [
                (cluster.name, len(cluster.tags))
                for cluster in sorted(
                    self.clustering.clusters.values(),
                    key=lambda x: len(x.tags),
                    reverse=True
                )[:5]
            ]
        }