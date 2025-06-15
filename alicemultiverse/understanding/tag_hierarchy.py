"""Intelligent tag hierarchy system for semantic organization.

This module provides hierarchical tag organization with semantic relationships,
enabling better search and discovery through conceptual connections.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TagNode:
    """A node in the tag hierarchy."""

    name: str
    parent: str | None = None
    children: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)
    related: set[str] = field(default_factory=set)
    category: str | None = None
    weight: float = 1.0  # Importance weight


class TagHierarchy:
    """Manages hierarchical tag relationships and semantic groupings."""

    def __init__(self):
        """Initialize tag hierarchy."""
        self.nodes: dict[str, TagNode] = {}
        self.categories: dict[str, set[str]] = defaultdict(set)
        self.aliases: dict[str, str] = {}  # alias -> canonical
        self._initialize_default_hierarchy()

    def _initialize_default_hierarchy(self):
        """Initialize with default tag hierarchies."""
        # Art style hierarchy
        self._add_hierarchy([
            ("art_style", None, "style"),
            ("digital_art", "art_style", "style"),
            ("cyberpunk", "digital_art", "style"),
            ("vaporwave", "digital_art", "style"),
            ("glitch_art", "digital_art", "style"),
            ("synthwave", "digital_art", "style"),
            ("traditional_art", "art_style", "style"),
            ("oil_painting", "traditional_art", "style"),
            ("watercolor", "traditional_art", "style"),
            ("acrylic", "traditional_art", "style"),
            ("pencil_drawing", "traditional_art", "style"),
            ("photography", "art_style", "style"),
            ("portrait_photography", "photography", "style"),
            ("landscape_photography", "photography", "style"),
            ("street_photography", "photography", "style"),
            ("3d_art", "art_style", "style"),
            ("3d_render", "3d_art", "style"),
            ("cgi", "3d_art", "style"),
            ("digital_sculpture", "3d_art", "style"),
        ])

        # Subject hierarchy
        self._add_hierarchy([
            ("subject", None, "subject"),
            ("person", "subject", "subject"),
            ("portrait", "person", "subject"),
            ("face", "portrait", "subject"),
            ("full_body", "person", "subject"),
            ("group", "person", "subject"),
            ("nature", "subject", "subject"),
            ("landscape", "nature", "subject"),
            ("seascape", "nature", "subject"),
            ("mountain", "nature", "subject"),
            ("forest", "nature", "subject"),
            ("animal", "subject", "subject"),
            ("wildlife", "animal", "subject"),
            ("pet", "animal", "subject"),
            ("bird", "animal", "subject"),
            ("architecture", "subject", "subject"),
            ("building", "architecture", "subject"),
            ("interior", "architecture", "subject"),
            ("cityscape", "architecture", "subject"),
        ])

        # Mood/emotion hierarchy
        self._add_hierarchy([
            ("mood", None, "mood"),
            ("positive_mood", "mood", "mood"),
            ("happy", "positive_mood", "mood"),
            ("joyful", "positive_mood", "mood"),
            ("peaceful", "positive_mood", "mood"),
            ("serene", "positive_mood", "mood"),
            ("energetic", "positive_mood", "mood"),
            ("negative_mood", "mood", "mood"),
            ("sad", "negative_mood", "mood"),
            ("melancholic", "negative_mood", "mood"),
            ("dark", "negative_mood", "mood"),
            ("mysterious", "negative_mood", "mood"),
            ("neutral_mood", "mood", "mood"),
            ("contemplative", "neutral_mood", "mood"),
            ("dramatic", "neutral_mood", "mood"),
            ("ethereal", "neutral_mood", "mood"),
        ])

        # Lighting conditions
        self._add_hierarchy([
            ("lighting", None, "technical"),
            ("natural_light", "lighting", "technical"),
            ("golden_hour", "natural_light", "technical"),
            ("sunset", "natural_light", "technical"),
            ("sunrise", "natural_light", "technical"),
            ("daylight", "natural_light", "technical"),
            ("overcast", "natural_light", "technical"),
            ("artificial_light", "lighting", "technical"),
            ("neon", "artificial_light", "technical"),
            ("studio_lighting", "artificial_light", "technical"),
            ("candlelight", "artificial_light", "technical"),
            ("dramatic_lighting", "lighting", "technical"),
            ("backlit", "dramatic_lighting", "technical"),
            ("silhouette", "dramatic_lighting", "technical"),
            ("rim_lighting", "dramatic_lighting", "technical"),
        ])

        # Color schemes
        self._add_hierarchy([
            ("color_scheme", None, "color"),
            ("warm_colors", "color_scheme", "color"),
            ("red_tones", "warm_colors", "color"),
            ("orange_tones", "warm_colors", "color"),
            ("yellow_tones", "warm_colors", "color"),
            ("cool_colors", "color_scheme", "color"),
            ("blue_tones", "cool_colors", "color"),
            ("green_tones", "cool_colors", "color"),
            ("purple_tones", "cool_colors", "color"),
            ("monochrome", "color_scheme", "color"),
            ("black_and_white", "monochrome", "color"),
            ("sepia", "monochrome", "color"),
            ("vibrant", "color_scheme", "color"),
            ("pastel", "color_scheme", "color"),
            ("muted", "color_scheme", "color"),
        ])

        # Add common aliases
        self._add_aliases([
            ("b&w", "black_and_white"),
            ("bw", "black_and_white"),
            ("person", "people"),
            ("sci-fi", "science_fiction"),
            ("scifi", "science_fiction"),
            ("3d", "3d_art"),
            ("cg", "cgi"),
            ("sunset", "golden_hour"),
            ("sunrise", "golden_hour"),
        ])

        # Add related tags
        self._add_relations([
            ("cyberpunk", ["neon", "futuristic", "sci-fi", "night"]),
            ("vaporwave", ["retro", "aesthetic", "pink", "purple"]),
            ("portrait", ["face", "person", "headshot"]),
            ("golden_hour", ["warm_colors", "sunset", "sunrise"]),
            ("dramatic", ["high_contrast", "moody", "dark"]),
        ])

    def _add_hierarchy(self, hierarchy: list[tuple[str, str | None, str]]):
        """Add a hierarchy of tags.
        
        Args:
            hierarchy: List of (tag, parent, category) tuples
        """
        for tag, parent, category in hierarchy:
            self.add_tag(tag, parent, category)

    def _add_aliases(self, aliases: list[tuple[str, str]]):
        """Add tag aliases.
        
        Args:
            aliases: List of (alias, canonical) tuples
        """
        for alias, canonical in aliases:
            self.add_alias(alias, canonical)

    def _add_relations(self, relations: list[tuple[str, list[str]]]):
        """Add related tags.
        
        Args:
            relations: List of (tag, related_tags) tuples
        """
        for tag, related in relations:
            if tag in self.nodes:
                self.nodes[tag].related.update(related)

    def add_tag(self, tag: str, parent: str | None = None,
                category: str | None = None) -> TagNode:
        """Add a tag to the hierarchy.
        
        Args:
            tag: Tag name
            parent: Parent tag name
            category: Tag category
            
        Returns:
            Created or updated TagNode
        """
        # Normalize tag
        tag = tag.lower().replace(" ", "_")

        # Create node if doesn't exist
        if tag not in self.nodes:
            self.nodes[tag] = TagNode(tag, parent=parent, category=category)
        else:
            # Update existing node
            if parent:
                self.nodes[tag].parent = parent
            if category:
                self.nodes[tag].category = category

        # Update parent's children
        if parent and parent in self.nodes:
            self.nodes[parent].children.add(tag)

        # Update category index
        if category:
            self.categories[category].add(tag)

        return self.nodes[tag]

    def add_alias(self, alias: str, canonical: str):
        """Add an alias for a tag.
        
        Args:
            alias: Alias name
            canonical: Canonical tag name
        """
        alias = alias.lower().replace(" ", "_")
        canonical = canonical.lower().replace(" ", "_")

        self.aliases[alias] = canonical

        if canonical in self.nodes:
            self.nodes[canonical].aliases.add(alias)

    def normalize_tag(self, tag: str) -> str:
        """Normalize a tag to its canonical form.
        
        Args:
            tag: Tag to normalize
            
        Returns:
            Canonical tag name
        """
        tag = tag.lower().replace(" ", "_")
        return self.aliases.get(tag, tag)

    def get_ancestors(self, tag: str) -> list[str]:
        """Get all ancestors of a tag.
        
        Args:
            tag: Tag name
            
        Returns:
            List of ancestor tags from immediate parent to root
        """
        tag = self.normalize_tag(tag)
        ancestors = []

        current = tag
        while current in self.nodes and self.nodes[current].parent:
            parent = self.nodes[current].parent
            ancestors.append(parent)
            current = parent

        return ancestors

    def get_descendants(self, tag: str) -> set[str]:
        """Get all descendants of a tag.
        
        Args:
            tag: Tag name
            
        Returns:
            Set of all descendant tags
        """
        tag = self.normalize_tag(tag)
        if tag not in self.nodes:
            return set()

        descendants = set()
        to_visit = list(self.nodes[tag].children)

        while to_visit:
            child = to_visit.pop()
            descendants.add(child)
            if child in self.nodes:
                to_visit.extend(self.nodes[child].children)

        return descendants

    def get_related(self, tag: str, max_depth: int = 2) -> dict[str, float]:
        """Get related tags with relevance scores.
        
        Args:
            tag: Tag name
            max_depth: Maximum relation depth to explore
            
        Returns:
            Dict of related tags with relevance scores
        """
        tag = self.normalize_tag(tag)
        if tag not in self.nodes:
            return {}

        related = {}

        # Direct relations (highest score)
        for rel in self.nodes[tag].related:
            related[rel] = 1.0

        # Parent and siblings (high score)
        if self.nodes[tag].parent:
            parent = self.nodes[tag].parent
            related[parent] = 0.8

            # Siblings
            for sibling in self.nodes[parent].children:
                if sibling != tag:
                    related[sibling] = 0.7

        # Children (medium score)
        for child in self.nodes[tag].children:
            related[child] = 0.6

        # Category members (lower score)
        if self.nodes[tag].category:
            for member in self.categories[self.nodes[tag].category]:
                if member != tag and member not in related:
                    related[member] = 0.4

        return related

    def expand_tags(self, tags: list[str], include_ancestors: bool = True,
                   include_related: bool = False) -> set[str]:
        """Expand a list of tags to include hierarchical relations.
        
        Args:
            tags: List of tags to expand
            include_ancestors: Include ancestor tags
            include_related: Include related tags
            
        Returns:
            Expanded set of tags
        """
        expanded = set()

        for tag in tags:
            tag = self.normalize_tag(tag)
            expanded.add(tag)

            if include_ancestors:
                expanded.update(self.get_ancestors(tag))

            if include_related:
                related = self.get_related(tag, max_depth=1)
                expanded.update(r for r, score in related.items() if score >= 0.7)

        return expanded

    def group_by_category(self, tags: list[str]) -> dict[str, list[str]]:
        """Group tags by their categories.
        
        Args:
            tags: List of tags to group
            
        Returns:
            Dict mapping category to list of tags
        """
        grouped = defaultdict(list)

        for tag in tags:
            tag = self.normalize_tag(tag)
            if tag in self.nodes and self.nodes[tag].category:
                grouped[self.nodes[tag].category].append(tag)
            else:
                grouped["uncategorized"].append(tag)

        return dict(grouped)

    def find_common_ancestors(self, tags: list[str]) -> list[tuple[str, int]]:
        """Find common ancestors of multiple tags.
        
        Args:
            tags: List of tags
            
        Returns:
            List of (ancestor, count) tuples sorted by count
        """
        ancestor_counts = defaultdict(int)

        for tag in tags:
            ancestors = self.get_ancestors(tag)
            for ancestor in ancestors:
                ancestor_counts[ancestor] += 1

        return sorted(ancestor_counts.items(), key=lambda x: x[1], reverse=True)

    def suggest_parent_tags(self, tags: list[str], threshold: float = 0.5) -> list[str]:
        """Suggest parent tags based on children presence.
        
        Args:
            tags: Current tags
            threshold: Minimum ratio of children needed
            
        Returns:
            Suggested parent tags
        """
        suggestions = []
        tag_set = set(self.normalize_tag(t) for t in tags)

        # Check each potential parent
        for parent, node in self.nodes.items():
            if parent in tag_set or not node.children:
                continue

            # Count how many children are in tags
            children_present = sum(1 for child in node.children if child in tag_set)
            ratio = children_present / len(node.children)

            if ratio >= threshold:
                suggestions.append(parent)

        return suggestions

    def export_hierarchy(self, path: Path):
        """Export hierarchy to JSON file.
        
        Args:
            path: Output file path
        """
        data = {
            "nodes": {
                name: {
                    "parent": node.parent,
                    "children": list(node.children),
                    "aliases": list(node.aliases),
                    "related": list(node.related),
                    "category": node.category,
                    "weight": node.weight
                }
                for name, node in self.nodes.items()
            },
            "categories": {k: list(v) for k, v in self.categories.items()},
            "aliases": self.aliases
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_hierarchy(self, path: Path):
        """Import hierarchy from JSON file.
        
        Args:
            path: Input file path
        """
        with open(path) as f:
            data = json.load(f)

        # Clear existing
        self.nodes.clear()
        self.categories.clear()
        self.aliases.clear()

        # Import nodes
        for name, node_data in data.get("nodes", {}).items():
            node = TagNode(
                name=name,
                parent=node_data.get("parent"),
                children=set(node_data.get("children", [])),
                aliases=set(node_data.get("aliases", [])),
                related=set(node_data.get("related", [])),
                category=node_data.get("category"),
                weight=node_data.get("weight", 1.0)
            )
            self.nodes[name] = node

        # Import categories
        for cat, tags in data.get("categories", {}).items():
            self.categories[cat] = set(tags)

        # Import aliases
        self.aliases = data.get("aliases", {})
