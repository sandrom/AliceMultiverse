"""
Metadata Structure for Multi-Model Image Understanding

This module defines how we store both individual model outputs
and merged results in file metadata.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ModelOutput:
    """Individual model's analysis output."""
    provider: str
    model: str
    description: str
    tags: Dict[str, List[str]]
    generated_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    cost: float = 0.0
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    # Rating data (added after comparison)
    rating: Optional[float] = None
    rated_at: Optional[datetime] = None
    rating_session_id: Optional[str] = None


@dataclass 
class MergedMetadata:
    """
    Final metadata structure embedded in files.
    
    This contains:
    1. Merged tags from all models (no source attribution)
    2. Best description/prompt (based on ratings or rules)
    3. Individual model outputs for future reference
    4. Comparison/rating history
    """
    
    # Merged results (what users see/search)
    tags: Dict[str, List[str]]  # Deduplicated and merged
    description: str  # Best or consensus description
    generated_prompt: str  # Best or merged prompt
    
    # Individual model outputs (for comparison/updates)
    model_outputs: List[ModelOutput] = field(default_factory=list)
    
    # Which models contributed to final result
    contributing_models: List[str] = field(default_factory=list)
    
    # Comparison metadata
    comparison_session_id: Optional[str] = None
    comparison_completed: bool = False
    
    # Versioning
    metadata_version: str = "2.0"
    last_updated: datetime = field(default_factory=datetime.now)


# Example of how this looks in practice:
EXAMPLE_METADATA = {
    # What gets embedded in the file
    "alice:tags": {
        "style": ["cyberpunk", "neon", "futuristic"],  # Merged from all models
        "mood": ["dramatic", "mysterious"],
        "subject": ["woman", "portrait"]
        # No indication of which model provided which tag
    },
    
    "alice:understanding": {
        "description": "A dramatic cyberpunk portrait...",  # Best description
        "generated_prompt": "cyberpunk woman portrait...",  # Best prompt
        "metadata_version": "2.0"
    },
    
    # Preserved model outputs for comparison
    "alice:model_outputs": [
        {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet",
            "description": "A dramatic cyberpunk portrait of a woman with neon lighting",
            "tags": {
                "style": ["cyberpunk", "neon"],
                "mood": ["dramatic"],
                "subject": ["woman", "portrait"]
            },
            "generated_prompt": "cyberpunk woman portrait, neon lights...",
            "cost": 0.003,
            "rating": 8.5,
            "rated_at": "2024-01-15T10:30:00Z"
        },
        {
            "provider": "openai", 
            "model": "gpt-4o",
            "description": "Portrait of a woman in futuristic setting",
            "tags": {
                "style": ["futuristic", "cyberpunk"],
                "mood": ["mysterious"],
                "subject": ["woman", "portrait"]  
            },
            "generated_prompt": "futuristic woman portrait...",
            "cost": 0.001,
            "rating": 7.2,
            "rated_at": "2024-01-15T10:30:00Z"
        }
    ],
    
    "alice:comparison": {
        "session_id": "comp_123456",
        "completed": True,
        "contributing_models": ["anthropic:claude-3-5-sonnet", "openai:gpt-4o"]
    }
}


class MetadataMerger:
    """Merge outputs from multiple models into final metadata."""
    
    @staticmethod
    def merge_tags(model_outputs: List[ModelOutput]) -> Dict[str, List[str]]:
        """
        Merge tags from multiple models.
        
        Strategy:
        1. Collect all unique tags per category
        2. Optionally weight by model ratings
        3. Remove near-duplicates
        """
        merged = {}
        
        for output in model_outputs:
            for category, tags in output.tags.items():
                if category not in merged:
                    merged[category] = []
                merged[category].extend(tags)
        
        # Deduplicate
        for category in merged:
            merged[category] = list(set(merged[category]))
            
        return merged
    
    @staticmethod
    def select_best_description(model_outputs: List[ModelOutput]) -> str:
        """Select best description based on ratings or length."""
        # If we have ratings, use highest rated
        rated_outputs = [o for o in model_outputs if o.rating is not None]
        if rated_outputs:
            best = max(rated_outputs, key=lambda o: o.rating)
            return best.description
            
        # Otherwise, use most detailed (longest)
        return max(model_outputs, key=lambda o: len(o.description)).description
    
    @staticmethod
    def create_merged_metadata(
        model_outputs: List[ModelOutput],
        comparison_session_id: Optional[str] = None
    ) -> MergedMetadata:
        """Create final merged metadata from model outputs."""
        
        merger = MetadataMerger()
        
        return MergedMetadata(
            tags=merger.merge_tags(model_outputs),
            description=merger.select_best_description(model_outputs),
            generated_prompt=merger.select_best_prompt(model_outputs),
            model_outputs=model_outputs,
            contributing_models=[
                f"{o.provider}:{o.model}" for o in model_outputs
            ],
            comparison_session_id=comparison_session_id,
            comparison_completed=any(o.rating is not None for o in model_outputs)
        )