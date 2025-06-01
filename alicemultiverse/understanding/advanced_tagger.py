"""Advanced hierarchical tagging system for image understanding."""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..database.models import Asset, Tag
from ..database.repository import AssetRepository
from .base import ImageAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class TagHierarchy:
    """Represents a hierarchical tag structure."""
    
    name: str
    category: str
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    confidence: float = 1.0
    source: str = "ai"  # 'ai', 'user', 'auto'
    metadata: Dict[str, Any] = field(default_factory=dict)


class TagVocabulary:
    """Manages custom tag vocabularies for projects."""
    
    def __init__(self):
        """Initialize with default vocabularies."""
        self.hierarchies: Dict[str, Dict[str, TagHierarchy]] = {}
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
    
    def add_hierarchy(self, category: str, relationships: List[Tuple[str, Optional[str]]]):
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
    
    def get_ancestors(self, category: str, tag: str) -> List[str]:
        """Get all ancestors of a tag in the hierarchy."""
        if category not in self.hierarchies or tag not in self.hierarchies[category]:
            return []
        
        ancestors = []
        current = tag
        hierarchy = self.hierarchies[category]
        
        while current and current in hierarchy:
            parent = hierarchy[current].parent
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors
    
    def get_descendants(self, category: str, tag: str) -> List[str]:
        """Get all descendants of a tag in the hierarchy."""
        if category not in self.hierarchies or tag not in self.hierarchies[category]:
            return []
        
        descendants = []
        to_process = [tag]
        hierarchy = self.hierarchies[category]
        
        while to_process:
            current = to_process.pop(0)
            if current in hierarchy:
                children = hierarchy[current].children
                descendants.extend(children)
                to_process.extend(children)
        
        return descendants
    
    def expand_tag(self, category: str, tag: str, include_ancestors: bool = True, 
                   include_descendants: bool = False) -> List[str]:
        """Expand a tag to include related tags in the hierarchy."""
        expanded = [tag]
        
        if include_ancestors:
            expanded.extend(self.get_ancestors(category, tag))
        
        if include_descendants:
            expanded.extend(self.get_descendants(category, tag))
        
        return list(set(expanded))  # Remove duplicates


class ProjectTagVocabulary:
    """Manages project-specific tag vocabularies."""
    
    def __init__(self, project_id: str, repository: AssetRepository):
        """Initialize project vocabulary.
        
        Args:
            project_id: The project ID
            repository: Asset repository for database access
        """
        self.project_id = project_id
        self.repository = repository
        self.base_vocabulary = TagVocabulary()
        self.custom_tags: Dict[str, Set[str]] = defaultdict(set)
        self._load_project_tags()
    
    def _load_project_tags(self):
        """Load existing tags from the project."""
        try:
            # Get all unique tags for this project
            with self.repository.get_session() as session:
                project_tags = (
                    session.query(Tag.tag_type, Tag.tag_value)
                    .join(Asset)
                    .filter(Asset.project_id == self.project_id)
                    .distinct()
                    .all()
                )
                
                for tag_type, tag_value in project_tags:
                    self.custom_tags[tag_type].add(tag_value)
                    
            logger.info(f"Loaded {sum(len(tags) for tags in self.custom_tags.values())} "
                       f"tags for project {self.project_id}")
                       
        except Exception as e:
            logger.warning(f"Failed to load project tags: {e}")
    
    def add_custom_tag(self, category: str, tag: str):
        """Add a custom tag to the project vocabulary."""
        self.custom_tags[category].add(tag)
    
    def get_all_tags(self, category: Optional[str] = None) -> Dict[str, Set[str]]:
        """Get all tags (base + custom) for the project."""
        result = {}
        
        # Start with base vocabulary
        for cat, hierarchy in self.base_vocabulary.hierarchies.items():
            if category is None or cat == category:
                result[cat] = set(hierarchy.keys())
        
        # Add custom tags
        for cat, tags in self.custom_tags.items():
            if category is None or cat == category:
                if cat in result:
                    result[cat].update(tags)
                else:
                    result[cat] = tags.copy()
        
        return result
    
    def suggest_tags(self, text: str, existing_tags: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Suggest additional tags based on text and existing tags."""
        suggestions = defaultdict(list)
        
        # Expand existing tags using hierarchy
        for category, tags in existing_tags.items():
            for tag in tags:
                # Add ancestors for better searchability
                ancestors = self.base_vocabulary.get_ancestors(category, tag)
                for ancestor in ancestors:
                    if ancestor not in tags and ancestor not in suggestions[category]:
                        suggestions[category].append(ancestor)
        
        # Add related tags based on common co-occurrences
        # This is a simplified version - in production, you'd use ML models
        tag_relations = {
            "golden_retriever": ["dog", "pet", "animal", "mammal"],
            "sunset": ["golden_hour", "warm_tones", "dramatic_light"],
            "portrait": ["close_up", "face", "person"],
            "landscape": ["wide_shot", "nature", "scenic"],
        }
        
        for category, tags in existing_tags.items():
            for tag in tags:
                if tag in tag_relations:
                    for related in tag_relations[tag]:
                        if related not in tags and related not in suggestions[category]:
                            suggestions[category].append(related)
        
        return dict(suggestions)


class AdvancedTagger:
    """Advanced tagging system with hierarchical and custom vocabularies."""
    
    def __init__(self, repository: AssetRepository):
        """Initialize the advanced tagger.
        
        Args:
            repository: Asset repository for database access
        """
        self.repository = repository
        self.project_vocabularies: Dict[str, ProjectTagVocabulary] = {}
    
    def get_project_vocabulary(self, project_id: str) -> ProjectTagVocabulary:
        """Get or create vocabulary for a project."""
        if project_id not in self.project_vocabularies:
            self.project_vocabularies[project_id] = ProjectTagVocabulary(
                project_id, self.repository
            )
        return self.project_vocabularies[project_id]
    
    def expand_tags(self, analysis_result: ImageAnalysisResult, 
                    project_id: Optional[str] = None) -> Dict[str, List[str]]:
        """Expand tags with hierarchical relationships.
        
        Args:
            analysis_result: The analysis result with initial tags
            project_id: Optional project ID for custom vocabulary
            
        Returns:
            Expanded tag dictionary with hierarchical tags added
        """
        expanded_tags = {}
        
        # Get vocabulary (project-specific or base)
        if project_id:
            vocabulary = self.get_project_vocabulary(project_id).base_vocabulary
        else:
            vocabulary = TagVocabulary()
        
        # Expand each tag with its hierarchy
        for category, tags in analysis_result.tags.items():
            expanded_set = set(tags)
            
            for tag in tags:
                # Add ancestors for better searchability
                ancestors = vocabulary.get_ancestors(category, tag)
                expanded_set.update(ancestors)
            
            expanded_tags[category] = sorted(list(expanded_set))
        
        return expanded_tags
    
    def add_specialized_categories(self, analysis_result: ImageAnalysisResult,
                                 image_path: Path) -> Dict[str, List[str]]:
        """Add specialized tag categories beyond basic ones.
        
        Args:
            analysis_result: The analysis result to enhance
            image_path: Path to the image file
            
        Returns:
            Dictionary of specialized tags
        """
        specialized = {
            "mood": [],
            "composition": [],
            "technical_quality": [],
            "artistic_style": [],
            "time_of_day": [],
            "weather": [],
            "season": [],
            "camera_angle": [],
            "depth_of_field": [],
            "color_palette": [],
            "texture": [],
            "pattern": [],
            "emotion": [],
            "activity": [],
            "fashion": [],
            "architecture": [],
            "nature": [],
            "urban": [],
            "cultural": [],
            "historical_period": [],
        }
        
        # Extract mood from description
        description_lower = analysis_result.description.lower()
        mood_indicators = {
            "dramatic": ["dramatic", "intense", "powerful", "striking"],
            "peaceful": ["peaceful", "calm", "serene", "tranquil"],
            "mysterious": ["mysterious", "enigmatic", "unclear", "shadowy"],
            "joyful": ["joyful", "happy", "cheerful", "bright"],
            "melancholic": ["sad", "melancholic", "gloomy", "somber"],
        }
        
        for mood, keywords in mood_indicators.items():
            if any(keyword in description_lower for keyword in keywords):
                specialized["mood"].append(mood)
        
        # Extract composition elements
        composition_indicators = {
            "rule_of_thirds": ["thirds", "off-center", "balanced"],
            "symmetrical": ["symmetrical", "symmetric", "mirrored"],
            "diagonal": ["diagonal", "angled", "tilted"],
            "leading_lines": ["lines leading", "guides the eye", "directional"],
            "framing": ["framed", "frame within", "natural frame"],
        }
        
        for comp, keywords in composition_indicators.items():
            if any(keyword in description_lower for keyword in keywords):
                specialized["composition"].append(comp)
        
        # Add technical quality tags based on existing analysis
        if hasattr(analysis_result, 'technical_details'):
            tech_details = analysis_result.technical_details
            if tech_details.get('sharpness') == 'good':
                specialized["technical_quality"].append("sharp")
            if tech_details.get('noise') == 'low':
                specialized["technical_quality"].append("clean")
            if tech_details.get('resolution') == 'high':
                specialized["technical_quality"].append("high_resolution")
        
        # Merge with existing tags
        for category, tags in specialized.items():
            if tags:  # Only add non-empty categories
                if category in analysis_result.tags:
                    # Merge without duplicates
                    existing = set(analysis_result.tags[category])
                    existing.update(tags)
                    analysis_result.tags[category] = sorted(list(existing))
                else:
                    analysis_result.tags[category] = sorted(tags)
        
        return specialized
    
    def apply_custom_vocabulary(self, analysis_result: ImageAnalysisResult,
                              project_id: str) -> None:
        """Apply project-specific custom vocabulary to tags.
        
        Args:
            analysis_result: The analysis result to enhance
            project_id: The project ID
        """
        vocabulary = self.get_project_vocabulary(project_id)
        
        # Suggest additional tags based on existing ones
        suggestions = vocabulary.suggest_tags(
            analysis_result.description,
            analysis_result.tags
        )
        
        # Add high-confidence suggestions
        for category, suggested_tags in suggestions.items():
            if category not in analysis_result.tags:
                analysis_result.tags[category] = []
            
            for tag in suggested_tags:
                if tag not in analysis_result.tags[category]:
                    analysis_result.tags[category].append(tag)
        
        # Sort tags for consistency
        for category in analysis_result.tags:
            analysis_result.tags[category] = sorted(analysis_result.tags[category])
    
    def save_tags_to_database(self, asset_hash: str, tags: Dict[str, List[str]], 
                            source: str = "ai", confidence: float = 1.0) -> None:
        """Save tags to the database.
        
        Args:
            asset_hash: The asset's content hash
            tags: Dictionary of tags by category
            source: Tag source ('ai', 'user', 'auto')
            confidence: Confidence score for AI-generated tags
        """
        with self.repository.get_session() as session:
            # Remove existing AI tags if we're updating
            if source == "ai":
                session.query(Tag).filter(
                    Tag.asset_id == asset_hash,
                    Tag.source == "ai"
                ).delete()
            
            # Add new tags
            for category, tag_list in tags.items():
                for tag_value in tag_list:
                    tag = Tag(
                        asset_id=asset_hash,
                        tag_type=category,
                        tag_value=tag_value,
                        confidence=confidence,
                        source=source
                    )
                    session.add(tag)
            
            session.commit()
            logger.info(f"Saved {sum(len(v) for v in tags.values())} tags for asset {asset_hash}")