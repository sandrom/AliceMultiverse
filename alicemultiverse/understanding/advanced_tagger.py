"""Advanced hierarchical tagging system for image understanding."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# PostgreSQL removed - Asset, Tag, and AssetRepository no longer available
from .base import ImageAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class TagHierarchy:
    """Represents a hierarchical tag structure."""

    name: str
    category: str
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    confidence: float = 1.0
    source: str = "ai"  # 'ai', 'user', 'auto'
    metadata: dict[str, Any] = field(default_factory=dict)


class TagVocabulary:
    """Manages custom tag vocabularies for projects."""

    def __init__(self):
        """Initialize with default vocabularies."""
        self.hierarchies: dict[str, dict[str, TagHierarchy]] = {}
        self._initialize_default_hierarchies()

    def _initialize_default_hierarchies(self):
        """Set up default tag hierarchies."""
        # Animal hierarchy
        self.add_hierarchy("animal", [
            ("animal", None),
            ("mammal", "animal"),
            ("bird", "animal"),
            ("reptile", "animal"),
            ("dog", "mammal"),
            ("cat", "mammal"),
            ("horse", "mammal"),
            ("golden_retriever", "dog"),
            ("labrador", "dog"),
            ("german_shepherd", "dog"),
            ("siamese", "cat"),
            ("persian", "cat"),
        ])

        # Mood hierarchy
        self.add_hierarchy("mood", [
            ("emotional", None),
            ("positive", "emotional"),
            ("negative", "emotional"),
            ("neutral", "emotional"),
            ("happy", "positive"),
            ("joyful", "positive"),
            ("excited", "positive"),
            ("peaceful", "positive"),
            ("sad", "negative"),
            ("melancholic", "negative"),
            ("anxious", "negative"),
            ("angry", "negative"),
            ("contemplative", "neutral"),
            ("mysterious", "neutral"),
        ])

        # Composition hierarchy
        self.add_hierarchy("composition", [
            ("framing", None),
            ("angle", None),
            ("balance", None),
            ("close_up", "framing"),
            ("medium_shot", "framing"),
            ("wide_shot", "framing"),
            ("extreme_close_up", "close_up"),
            ("low_angle", "angle"),
            ("high_angle", "angle"),
            ("eye_level", "angle"),
            ("dutch_angle", "angle"),
            ("symmetrical", "balance"),
            ("asymmetrical", "balance"),
            ("rule_of_thirds", "balance"),
            ("centered", "balance"),
        ])

        # Artistic style hierarchy
        self.add_hierarchy("style", [
            ("artistic_movement", None),
            ("modern", "artistic_movement"),
            ("classical", "artistic_movement"),
            ("contemporary", "modern"),
            ("abstract", "modern"),
            ("minimalist", "modern"),
            ("surrealist", "modern"),
            ("impressionist", "classical"),
            ("realist", "classical"),
            ("baroque", "classical"),
            ("photorealistic", None),
            ("stylized", None),
            ("cartoon", "stylized"),
            ("anime", "stylized"),
            ("watercolor", "stylized"),
            ("oil_painting", "stylized"),
        ])

        # Technical quality hierarchy
        self.add_hierarchy("technical", [
            ("focus", None),
            ("lighting", None),
            ("color", None),
            ("sharp", "focus"),
            ("soft_focus", "focus"),
            ("bokeh", "focus"),
            ("motion_blur", "focus"),
            ("natural_light", "lighting"),
            ("studio_light", "lighting"),
            ("dramatic_light", "lighting"),
            ("soft_light", "lighting"),
            ("hard_light", "lighting"),
            ("vibrant", "color"),
            ("muted", "color"),
            ("monochrome", "color"),
            ("warm_tones", "color"),
            ("cool_tones", "color"),
        ])

    def add_hierarchy(self, category: str, relationships: list[tuple[str, str | None]]):
        """Add a hierarchy of tags.

        Args:
            category: The category name
            relationships: List of (tag, parent) tuples
        """
        if category not in self.hierarchies:
            self.hierarchies[category] = {}

        hierarchy = self.hierarchies[category]

        # First pass: create all tags
        for tag_name, parent in relationships:
            if tag_name not in hierarchy:
                hierarchy[tag_name] = TagHierarchy(
                    name=tag_name,
                    category=category,
                    parent=parent
                )

        # Second pass: build children lists
        for tag_name, parent in relationships:
            if parent and parent in hierarchy:
                hierarchy[parent].children.append(tag_name)

    def get_ancestors(self, category: str, tag: str) -> list[str]:
        """Get all ancestors of a tag in the hierarchy."""
        if category not in self.hierarchies or tag not in self.hierarchies[category]:
            return []

        # TODO: Review unreachable code - ancestors = []
        # TODO: Review unreachable code - current = tag
        # TODO: Review unreachable code - hierarchy = self.hierarchies[category]

        # TODO: Review unreachable code - while current and current in hierarchy:
        # TODO: Review unreachable code - parent = hierarchy[current].parent
        # TODO: Review unreachable code - if parent:
        # TODO: Review unreachable code - ancestors.append(parent)
        # TODO: Review unreachable code - current = parent
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - break

        # TODO: Review unreachable code - return ancestors

    def get_descendants(self, category: str, tag: str) -> list[str]:
        """Get all descendants of a tag in the hierarchy."""
        if category not in self.hierarchies or tag not in self.hierarchies[category]:
            return []

        # TODO: Review unreachable code - descendants = []
        # TODO: Review unreachable code - to_process = [tag]
        # TODO: Review unreachable code - hierarchy = self.hierarchies[category]

        # TODO: Review unreachable code - while to_process:
        # TODO: Review unreachable code - current = to_process.pop(0)
        # TODO: Review unreachable code - if current in hierarchy:
        # TODO: Review unreachable code - children = hierarchy[current].children
        # TODO: Review unreachable code - descendants.extend(children)
        # TODO: Review unreachable code - to_process.extend(children)

        # TODO: Review unreachable code - return descendants

    def expand_tag(self, category: str, tag: str, include_ancestors: bool = True,
                   include_descendants: bool = False) -> list[str]:
        """Expand a tag to include related tags in the hierarchy."""
        expanded = [tag]

        if include_ancestors:
            expanded.extend(self.get_ancestors(category, tag))

        if include_descendants:
            expanded.extend(self.get_descendants(category, tag))

        return list(set(expanded))  # Remove duplicates


# TODO: Review unreachable code - class ProjectTagVocabulary:
# TODO: Review unreachable code - """Manages project-specific tag vocabularies."""

# TODO: Review unreachable code - def __init__(self, project_id: str, repository: Any):
# TODO: Review unreachable code - """Initialize project vocabulary.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - project_id: The project ID
# TODO: Review unreachable code - repository: Asset repository for database access
# TODO: Review unreachable code - """
# TODO: Review unreachable code - self.project_id = project_id
# TODO: Review unreachable code - self.repository = repository
# TODO: Review unreachable code - self.base_vocabulary = TagVocabulary()
# TODO: Review unreachable code - self.custom_tags: dict[str, set[str]] = defaultdict(set)
# TODO: Review unreachable code - self._load_project_tags()

# TODO: Review unreachable code - def _load_project_tags(self):
# TODO: Review unreachable code - """Load existing tags from the project."""
# TODO: Review unreachable code - # PostgreSQL removed - cannot load project tags from database
# TODO: Review unreachable code - logger.debug(f"Project tag loading skipped for {self.project_id} - PostgreSQL removed")
# TODO: Review unreachable code - return

# TODO: Review unreachable code - def add_custom_tag(self, category: str, tag: str):
# TODO: Review unreachable code - """Add a custom tag to the project vocabulary."""
# TODO: Review unreachable code - self.custom_tags[category].add(tag)

# TODO: Review unreachable code - def get_all_tags(self, category: str | None = None) -> dict[str, set[str]]:
# TODO: Review unreachable code - """Get all tags (base + custom) for the project."""
# TODO: Review unreachable code - result = {}

# TODO: Review unreachable code - # Start with base vocabulary
# TODO: Review unreachable code - for cat, hierarchy in self.base_vocabulary.hierarchies.items():
# TODO: Review unreachable code - if category is None or cat == category:
# TODO: Review unreachable code - result[cat] = set(hierarchy.keys())

# TODO: Review unreachable code - # Add custom tags
# TODO: Review unreachable code - for cat, tags in self.custom_tags.items():
# TODO: Review unreachable code - if category is None or cat == category:
# TODO: Review unreachable code - if cat in result:
# TODO: Review unreachable code - result[cat].update(tags)
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - result[cat] = tags.copy()

# TODO: Review unreachable code - return result

# TODO: Review unreachable code - def suggest_tags(self, text: str, existing_tags: dict[str, list[str]]) -> dict[str, list[str]]:
# TODO: Review unreachable code - """Suggest additional tags based on text and existing tags."""
# TODO: Review unreachable code - suggestions = defaultdict(list)

# TODO: Review unreachable code - # Expand existing tags using hierarchy
# TODO: Review unreachable code - for category, tags in existing_tags.items():
# TODO: Review unreachable code - for tag in tags:
# TODO: Review unreachable code - # Add ancestors for better searchability
# TODO: Review unreachable code - ancestors = self.base_vocabulary.get_ancestors(category, tag)
# TODO: Review unreachable code - for ancestor in ancestors:
# TODO: Review unreachable code - if ancestor not in tags and ancestor not in suggestions[category]:
# TODO: Review unreachable code - suggestions[category].append(ancestor)

# TODO: Review unreachable code - # Add related tags based on common co-occurrences
# TODO: Review unreachable code - # This is a simplified version - in production, you'd use ML models
# TODO: Review unreachable code - tag_relations = {
# TODO: Review unreachable code - "golden_retriever": ["dog", "pet", "animal", "mammal"],
# TODO: Review unreachable code - "sunset": ["golden_hour", "warm_tones", "dramatic_light"],
# TODO: Review unreachable code - "portrait": ["close_up", "face", "person"],
# TODO: Review unreachable code - "landscape": ["wide_shot", "nature", "scenic"],
# TODO: Review unreachable code - }

# TODO: Review unreachable code - for category, tags in existing_tags.items():
# TODO: Review unreachable code - for tag in tags:
# TODO: Review unreachable code - if tag in tag_relations:
# TODO: Review unreachable code - for related in tag_relations[tag]:
# TODO: Review unreachable code - if related not in tags and related not in suggestions[category]:
# TODO: Review unreachable code - suggestions[category].append(related)

# TODO: Review unreachable code - return dict(suggestions)


# TODO: Review unreachable code - class AdvancedTagger:
# TODO: Review unreachable code - """Advanced tagging system with hierarchical and custom vocabularies."""

# TODO: Review unreachable code - def __init__(self, repository: Any):
# TODO: Review unreachable code - """Initialize the advanced tagger.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - repository: Asset repository for database access
# TODO: Review unreachable code - """
# TODO: Review unreachable code - self.repository = repository
# TODO: Review unreachable code - self.project_vocabularies: dict[str, ProjectTagVocabulary] = {}

# TODO: Review unreachable code - def get_project_vocabulary(self, project_id: str) -> ProjectTagVocabulary:
# TODO: Review unreachable code - """Get or create vocabulary for a project."""
# TODO: Review unreachable code - if project_id not in self.project_vocabularies:
# TODO: Review unreachable code - self.project_vocabularies[project_id] = ProjectTagVocabulary(
# TODO: Review unreachable code - project_id, self.repository
# TODO: Review unreachable code - )
# TODO: Review unreachable code - return self.project_vocabularies[project_id]

# TODO: Review unreachable code - def expand_tags(self, analysis_result: ImageAnalysisResult,
# TODO: Review unreachable code - project_id: str | None = None) -> dict[str, list[str]]:
# TODO: Review unreachable code - """Expand tags with hierarchical relationships.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - analysis_result: The analysis result with initial tags
# TODO: Review unreachable code - project_id: Optional project ID for custom vocabulary

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Expanded tag dictionary with hierarchical tags added
# TODO: Review unreachable code - """
# TODO: Review unreachable code - expanded_tags = {}

# TODO: Review unreachable code - # Get vocabulary (project-specific or base)
# TODO: Review unreachable code - if project_id:
# TODO: Review unreachable code - vocabulary = self.get_project_vocabulary(project_id).base_vocabulary
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - vocabulary = TagVocabulary()

# TODO: Review unreachable code - # Expand each tag with its hierarchy
# TODO: Review unreachable code - for category, tags in analysis_result.tags.items():
# TODO: Review unreachable code - expanded_set = set(tags)

# TODO: Review unreachable code - for tag in tags:
# TODO: Review unreachable code - # Add ancestors for better searchability
# TODO: Review unreachable code - ancestors = vocabulary.get_ancestors(category, tag)
# TODO: Review unreachable code - expanded_set.update(ancestors)

# TODO: Review unreachable code - expanded_tags[category] = sorted(list(expanded_set))

# TODO: Review unreachable code - return expanded_tags

# TODO: Review unreachable code - def add_specialized_categories(self, analysis_result: ImageAnalysisResult,
# TODO: Review unreachable code - image_path: Path) -> dict[str, list[str]]:
# TODO: Review unreachable code - """Add specialized tag categories beyond basic ones.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - analysis_result: The analysis result to enhance
# TODO: Review unreachable code - image_path: Path to the image file

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Dictionary of specialized tags
# TODO: Review unreachable code - """
# TODO: Review unreachable code - specialized = {
# TODO: Review unreachable code - "mood": [],
# TODO: Review unreachable code - "composition": [],
# TODO: Review unreachable code - "technical_quality": [],
# TODO: Review unreachable code - "artistic_style": [],
# TODO: Review unreachable code - "time_of_day": [],
# TODO: Review unreachable code - "weather": [],
# TODO: Review unreachable code - "season": [],
# TODO: Review unreachable code - "camera_angle": [],
# TODO: Review unreachable code - "depth_of_field": [],
# TODO: Review unreachable code - "color_palette": [],
# TODO: Review unreachable code - "texture": [],
# TODO: Review unreachable code - "pattern": [],
# TODO: Review unreachable code - "emotion": [],
# TODO: Review unreachable code - "activity": [],
# TODO: Review unreachable code - "fashion": [],
# TODO: Review unreachable code - "architecture": [],
# TODO: Review unreachable code - "nature": [],
# TODO: Review unreachable code - "urban": [],
# TODO: Review unreachable code - "cultural": [],
# TODO: Review unreachable code - "historical_period": [],
# TODO: Review unreachable code - }

# TODO: Review unreachable code - # Extract mood from description
# TODO: Review unreachable code - description_lower = analysis_result.description.lower()
# TODO: Review unreachable code - mood_indicators = {
# TODO: Review unreachable code - "dramatic": ["dramatic", "intense", "powerful", "striking"],
# TODO: Review unreachable code - "peaceful": ["peaceful", "calm", "serene", "tranquil"],
# TODO: Review unreachable code - "mysterious": ["mysterious", "enigmatic", "unclear", "shadowy"],
# TODO: Review unreachable code - "joyful": ["joyful", "happy", "cheerful", "bright"],
# TODO: Review unreachable code - "melancholic": ["sad", "melancholic", "gloomy", "somber"],
# TODO: Review unreachable code - }

# TODO: Review unreachable code - for mood, keywords in mood_indicators.items():
# TODO: Review unreachable code - if any(keyword in description_lower for keyword in keywords):
# TODO: Review unreachable code - specialized["mood"].append(mood)

# TODO: Review unreachable code - # Extract composition elements
# TODO: Review unreachable code - composition_indicators = {
# TODO: Review unreachable code - "rule_of_thirds": ["thirds", "off-center", "balanced"],
# TODO: Review unreachable code - "symmetrical": ["symmetrical", "symmetric", "mirrored"],
# TODO: Review unreachable code - "diagonal": ["diagonal", "angled", "tilted"],
# TODO: Review unreachable code - "leading_lines": ["lines leading", "guides the eye", "directional"],
# TODO: Review unreachable code - "framing": ["framed", "frame within", "natural frame"],
# TODO: Review unreachable code - }

# TODO: Review unreachable code - for comp, keywords in composition_indicators.items():
# TODO: Review unreachable code - if any(keyword in description_lower for keyword in keywords):
# TODO: Review unreachable code - specialized["composition"].append(comp)

# TODO: Review unreachable code - # Add technical quality tags based on existing analysis
# TODO: Review unreachable code - if hasattr(analysis_result, 'technical_details'):
# TODO: Review unreachable code - tech_details = analysis_result.technical_details
# TODO: Review unreachable code - if tech_details.get('sharpness') == 'good':
# TODO: Review unreachable code - specialized["technical_quality"].append("sharp")
# TODO: Review unreachable code - if tech_details.get('noise') == 'low':
# TODO: Review unreachable code - specialized["technical_quality"].append("clean")
# TODO: Review unreachable code - if tech_details.get('resolution') == 'high':
# TODO: Review unreachable code - specialized["technical_quality"].append("high_resolution")

# TODO: Review unreachable code - # Merge with existing tags
# TODO: Review unreachable code - for category, tags in specialized.items():
# TODO: Review unreachable code - if tags:  # Only add non-empty categories
# TODO: Review unreachable code - if category in analysis_result.tags:
# TODO: Review unreachable code - # Merge without duplicates
# TODO: Review unreachable code - existing = set(analysis_result.tags[category])
# TODO: Review unreachable code - existing.update(tags)
# TODO: Review unreachable code - analysis_result.tags[category] = sorted(list(existing))
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - analysis_result.tags[category] = sorted(tags)

# TODO: Review unreachable code - return specialized

# TODO: Review unreachable code - def apply_custom_vocabulary(self, analysis_result: ImageAnalysisResult,
# TODO: Review unreachable code - project_id: str) -> None:
# TODO: Review unreachable code - """Apply project-specific custom vocabulary to tags.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - analysis_result: The analysis result to enhance
# TODO: Review unreachable code - project_id: The project ID
# TODO: Review unreachable code - """
# TODO: Review unreachable code - vocabulary = self.get_project_vocabulary(project_id)

# TODO: Review unreachable code - # Suggest additional tags based on existing ones
# TODO: Review unreachable code - suggestions = vocabulary.suggest_tags(
# TODO: Review unreachable code - analysis_result.description,
# TODO: Review unreachable code - analysis_result.tags
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Add high-confidence suggestions
# TODO: Review unreachable code - for category, suggested_tags in suggestions.items():
# TODO: Review unreachable code - if category not in analysis_result.tags:
# TODO: Review unreachable code - analysis_result.tags[category] = []

# TODO: Review unreachable code - for tag in suggested_tags:
# TODO: Review unreachable code - if tag not in analysis_result.tags[category]:
# TODO: Review unreachable code - analysis_result.tags[category].append(tag)

# TODO: Review unreachable code - # Sort tags for consistency
# TODO: Review unreachable code - for category in analysis_result.tags:
# TODO: Review unreachable code - analysis_result.tags[category] = sorted(analysis_result.tags[category])

# TODO: Review unreachable code - # NOTE: Database storage has been removed. Tags are now stored in file metadata.
# TODO: Review unreachable code - # def save_tags_to_database(self, asset_hash: str, tags: dict[str, list[str]],
# TODO: Review unreachable code - #                         source: str = "ai", confidence: float = 1.0) -> None:
# TODO: Review unreachable code - #     """Save tags to the database.
# TODO: Review unreachable code - #
# TODO: Review unreachable code - #     Args:
# TODO: Review unreachable code - #         asset_hash: The asset's content hash
# TODO: Review unreachable code - #         tags: Dictionary of tags by category
# TODO: Review unreachable code - #         source: Tag source ('ai', 'user', 'auto')
# TODO: Review unreachable code - #         confidence: Confidence score for AI-generated tags
# TODO: Review unreachable code - #     """
# TODO: Review unreachable code - #     # This method is deprecated - tags are now stored in file metadata
# TODO: Review unreachable code - #     pass
