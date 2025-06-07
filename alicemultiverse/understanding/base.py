"""Base classes for image understanding."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ImageAnalysisResult:
    """Result from image analysis."""
    
    # Core description
    description: str
    detailed_description: Optional[str] = None
    
    # Extracted tags with semantic meaning
    tags: Dict[str, List[str]] = field(default_factory=dict)
    # Example tags structure:
    # {
    #     "style": ["photorealistic", "cinematic", "moody"],
    #     "mood": ["dramatic", "mysterious", "contemplative"],
    #     "subject": ["woman", "portrait", "close-up"],
    #     "color": ["blue-toned", "high-contrast", "dark"],
    #     "technical": ["shallow-dof", "studio-lighting", "high-resolution"],
    #     "fashion": ["leather-jacket", "casual-wear"],
    #     "hair": ["long", "wavy", "brunette"],
    #     "pose": ["profile", "looking-away"],
    #     "setting": ["urban", "night", "street"],
    #     "camera": ["85mm", "bokeh", "professional"],
    #     "art_movement": ["contemporary", "fashion-photography"],
    #     "emotion": ["pensive", "confident"],
    #     "composition": ["rule-of-thirds", "centered", "tight-crop"],
    #     "texture": ["smooth-skin", "leather-texture"],
    #     "weather": ["overcast", "evening"],
    #     "action": ["standing", "posing"],
    #     "gender": ["female"],
    #     "age_group": ["young-adult"],
    #     "ethnicity": ["diverse"],  # Be respectful and general
    #     "accessories": ["earrings", "necklace"],
    #     "time_period": ["contemporary", "2020s"],
    #     "genre": ["fashion", "portrait", "editorial"]
    # }
    
    # Prompt generation (reverse engineering)
    generated_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    
    # Technical details
    detected_objects: List[Dict[str, Any]] = field(default_factory=list)
    dominant_colors: List[str] = field(default_factory=list)
    
    # Quality/technical assessment (different from subjective quality)
    technical_details: Dict[str, Any] = field(default_factory=dict)
    # Example: {"resolution": "high", "sharpness": "good", "noise": "low"}
    
    # Provider-specific raw response
    raw_response: Optional[Dict[str, Any]] = None
    
    # Cost tracking
    cost: float = 0.0
    tokens_used: Optional[int] = None
    
    # Provider info
    provider: Optional[str] = None
    model: Optional[str] = None
    
    def get_all_tags(self) -> List[str]:
        """Get all tags as a flat list."""
        all_tags = []
        for tag_list in self.tags.values():
            all_tags.extend(tag_list)
        return list(set(all_tags))  # Remove duplicates
    
    def get_tags_by_category(self, category: str) -> List[str]:
        """Get tags for a specific category."""
        return self.tags.get(category, [])


class ImageAnalyzer(ABC):
    """Abstract base class for image analyzers."""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        """Initialize analyzer.
        
        Args:
            api_key: API key for the service
            model: Specific model to use (provider-dependent)
        """
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    async def analyze(
        self, 
        image_path: Path,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        detailed: bool = False,
        custom_instructions: Optional[str] = None
    ) -> ImageAnalysisResult:
        """Analyze an image.
        
        Args:
            image_path: Path to the image file
            generate_prompt: Whether to generate a prompt from the image
            extract_tags: Whether to extract semantic tags
            detailed: Whether to include detailed descriptions
            custom_instructions: Additional instructions for analysis
            
        Returns:
            ImageAnalysisResult with extracted information
        """
    
    @abstractmethod
    def estimate_cost(self, detailed: bool = False) -> float:
        """Estimate cost per image analysis.
        
        Args:
            detailed: Whether using detailed analysis
            
        Returns:
            Estimated cost in USD
        """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
    
    @property
    @abstractmethod
    def supports_batch(self) -> bool:
        """Whether this analyzer supports batch processing."""
    
    def _extract_tags_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract tags from descriptive text.
        
        This is a helper method that can be overridden by specific providers.
        """
        # Basic implementation - providers can override with better extraction
        tags = {
            "style": [],
            "mood": [],
            "subject": [],
            "color": [],
            "technical": [],
            "setting": [],
        }
        
        # Simple keyword matching - providers should use AI for better extraction
        style_keywords = ["photorealistic", "artistic", "abstract", "minimalist", "cinematic"]
        mood_keywords = ["happy", "sad", "dramatic", "peaceful", "energetic", "mysterious"]
        
        text_lower = text.lower()
        for keyword in style_keywords:
            if keyword in text_lower:
                tags["style"].append(keyword)
                
        for keyword in mood_keywords:
            if keyword in text_lower:
                tags["mood"].append(keyword)
        
        return tags