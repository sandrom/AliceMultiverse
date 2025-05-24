"""Creative models for Alice orchestration.

These models represent creative concepts rather than technical details,
enabling AI assistants to work in natural, creative terms.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class CreativeRole(Enum):
    """Creative roles that assets can play in a project."""
    HERO = "hero"              # Main/featured content
    SUPPORTING = "supporting"   # Supporting elements
    BACKGROUND = "background"   # Background/atmosphere
    REFERENCE = "reference"     # Reference/inspiration
    EXPERIMENT = "experiment"   # Experimental/test
    OUTTAKE = "outtake"        # Didn't make the cut
    ARCHIVE = "archive"        # Historical/archived


class CreativeMood(Enum):
    """Mood categories for creative work."""
    ENERGETIC = "energetic"
    CALM = "calm"
    DARK = "dark"
    BRIGHT = "bright"
    MYSTERIOUS = "mysterious"
    PLAYFUL = "playful"
    SERIOUS = "serious"
    DREAMY = "dreamy"
    INTENSE = "intense"
    WHIMSICAL = "whimsical"


class WorkflowPhase(Enum):
    """Phases of creative workflow."""
    IDEATION = "ideation"
    EXPLORATION = "exploration"
    REFINEMENT = "refinement"
    PRODUCTION = "production"
    REVIEW = "review"
    FINAL = "final"


@dataclass
class CreativeContext:
    """Context for a creative project or session."""
    project_name: str
    description: Optional[str] = None
    phase: WorkflowPhase = WorkflowPhase.EXPLORATION
    
    # Creative preferences
    primary_style: Optional[str] = None
    mood: Optional[CreativeMood] = None
    color_palette: List[str] = field(default_factory=list)
    inspiration_sources: List[str] = field(default_factory=list)
    
    # Constraints and guidelines
    avoid_elements: List[str] = field(default_factory=list)
    must_include: List[str] = field(default_factory=list)
    technical_requirements: Dict[str, Any] = field(default_factory=dict)
    
    # History
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    iteration_count: int = 0
    
    def to_prompt_modifiers(self) -> str:
        """Convert context to prompt modifiers."""
        modifiers = []
        
        if self.primary_style:
            modifiers.append(self.primary_style)
            
        if self.mood:
            modifiers.append(f"{self.mood.value} mood")
            
        if self.color_palette:
            modifiers.append(f"colors: {', '.join(self.color_palette)}")
            
        if self.must_include:
            modifiers.append(f"including {', '.join(self.must_include)}")
            
        if self.avoid_elements:
            modifiers.append(f"avoiding {', '.join(self.avoid_elements)}")
            
        return ", ".join(modifiers)


@dataclass
class CreativeAsset:
    """Represents an asset in creative terms."""
    id: str
    name: str
    role: CreativeRole = CreativeRole.EXPERIMENT
    
    # Creative properties
    style_tags: List[str] = field(default_factory=list)
    mood_tags: List[str] = field(default_factory=list)
    subject_tags: List[str] = field(default_factory=list)
    
    # Relationships
    inspired_by: List[str] = field(default_factory=list)  # Asset IDs
    variations_of: Optional[str] = None  # Parent asset ID
    used_in: List[str] = field(default_factory=list)  # Project/scene IDs
    
    # Creative metadata
    prompt: Optional[str] = None
    notes: Optional[str] = None
    rating: Optional[int] = None  # 1-5 stars
    
    # Temporal
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    
    def matches_mood(self, mood: CreativeMood) -> bool:
        """Check if asset matches a mood."""
        return mood.value in self.mood_tags
    
    def has_style(self, style: str) -> bool:
        """Check if asset has a style."""
        return style.lower() in [s.lower() for s in self.style_tags]


@dataclass
class CreativeWorkflow:
    """Represents a creative workflow."""
    id: str
    name: str
    description: Optional[str] = None
    
    # Workflow definition
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    
    # Context and parameters
    context: Optional[CreativeContext] = None
    input_assets: List[str] = field(default_factory=list)
    output_assets: List[str] = field(default_factory=list)
    
    # Execution state
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    success_count: int = 0
    failure_count: int = 0
    cost_estimate: Optional[float] = None
    
    def add_step(self, step_type: str, parameters: Dict[str, Any]):
        """Add a step to the workflow."""
        self.steps.append({
            'type': step_type,
            'parameters': parameters,
            'status': 'pending'
        })
    
    def complete_step(self, success: bool = True):
        """Mark current step as complete."""
        if self.current_step < len(self.steps):
            self.steps[self.current_step]['status'] = 'completed' if success else 'failed'
            self.current_step += 1
            
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1


@dataclass
class StyleEvolution:
    """Tracks how a style evolves over time."""
    style_name: str
    base_elements: Dict[str, Any] = field(default_factory=dict)
    
    # Evolution history
    iterations: List[Dict[str, Any]] = field(default_factory=list)
    current_version: int = 1
    
    # Learned preferences
    successful_elements: List[str] = field(default_factory=list)
    avoided_elements: List[str] = field(default_factory=list)
    
    # Statistics
    usage_count: int = 0
    success_rate: float = 0.0
    
    def record_iteration(self, elements: Dict[str, Any], success: bool):
        """Record a style iteration."""
        self.iterations.append({
            'version': self.current_version,
            'elements': elements,
            'success': success,
            'timestamp': datetime.utcnow()
        })
        
        if success:
            # Learn from successful iterations
            for key, value in elements.items():
                if isinstance(value, str) and value not in self.successful_elements:
                    self.successful_elements.append(value)
        
        self.usage_count += 1
        self.current_version += 1
        
        # Update success rate
        successful = sum(1 for i in self.iterations if i['success'])
        self.success_rate = successful / len(self.iterations)
    
    def get_evolved_style(self) -> Dict[str, Any]:
        """Get the current evolved style."""
        evolved = self.base_elements.copy()
        
        # Add successful elements
        if self.successful_elements:
            evolved['proven_elements'] = self.successful_elements[:5]  # Top 5
            
        # Note avoided elements
        if self.avoided_elements:
            evolved['avoid'] = self.avoided_elements
            
        return evolved


@dataclass
class CreativeMemoryEntry:
    """An entry in creative memory."""
    id: str
    timestamp: datetime
    entry_type: str  # 'search', 'creation', 'feedback', 'discovery'
    
    # Content
    description: str
    tags: List[str] = field(default_factory=list)
    
    # Context
    project_id: Optional[str] = None
    workflow_id: Optional[str] = None
    related_assets: List[str] = field(default_factory=list)
    
    # Outcome
    success: bool = True
    impact_score: float = 0.0  # How important was this
    
    def age_days(self) -> int:
        """Get age of memory in days."""
        return (datetime.utcnow() - self.timestamp).days


@dataclass
class CreativePattern:
    """A pattern in creative work."""
    pattern_type: str  # 'style_combination', 'workflow_sequence', 'time_preference'
    elements: List[str]
    
    # Statistics
    occurrence_count: int = 1
    success_rate: float = 1.0
    last_seen: datetime = field(default_factory=datetime.utcnow)
    
    # Context
    common_contexts: List[str] = field(default_factory=list)
    
    def record_occurrence(self, success: bool, context: Optional[str] = None):
        """Record a pattern occurrence."""
        self.occurrence_count += 1
        self.last_seen = datetime.utcnow()
        
        # Update success rate
        if not success:
            self.success_rate = ((self.success_rate * (self.occurrence_count - 1)) + 
                               (1.0 if success else 0.0)) / self.occurrence_count
        
        # Track context
        if context and context not in self.common_contexts:
            self.common_contexts.append(context)
            if len(self.common_contexts) > 5:
                self.common_contexts.pop(0)
    
    def is_successful(self) -> bool:
        """Check if pattern is generally successful."""
        return self.success_rate > 0.7 and self.occurrence_count > 3