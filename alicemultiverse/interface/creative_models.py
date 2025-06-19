"""Creative models for Alice orchestration.

These models represent creative concepts rather than technical details,
enabling AI assistants to work in natural, creative terms.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class CreativeRole(Enum):
    """Creative roles that assets can play in a project."""

    HERO = "hero"  # Main/featured content
    SUPPORTING = "supporting"  # Supporting elements
    BACKGROUND = "background"  # Background/atmosphere
    REFERENCE = "reference"  # Reference/inspiration
    EXPERIMENT = "experiment"  # Experimental/test
    OUTTAKE = "outtake"  # Didn't make the cut
    ARCHIVE = "archive"  # Historical/archived


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
    description: str | None = None
    phase: WorkflowPhase = WorkflowPhase.EXPLORATION

    # Creative preferences
    primary_style: str | None = None
    mood: CreativeMood | None = None
    color_palette: list[str] = field(default_factory=list)
    inspiration_sources: list[str] = field(default_factory=list)

    # Constraints and guidelines
    avoid_elements: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    technical_requirements: dict[str, Any] = field(default_factory=dict)

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


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class CreativeAsset:
# TODO: Review unreachable code - """Represents an asset in creative terms."""

# TODO: Review unreachable code - id: str
# TODO: Review unreachable code - name: str
# TODO: Review unreachable code - role: CreativeRole = CreativeRole.EXPERIMENT

# TODO: Review unreachable code - # Creative properties
# TODO: Review unreachable code - style_tags: list[str] = field(default_factory=list)
# TODO: Review unreachable code - mood_tags: list[str] = field(default_factory=list)
# TODO: Review unreachable code - subject_tags: list[str] = field(default_factory=list)

# TODO: Review unreachable code - # Relationships
# TODO: Review unreachable code - inspired_by: list[str] = field(default_factory=list)  # Asset IDs
# TODO: Review unreachable code - variations_of: str | None = None  # Parent asset ID
# TODO: Review unreachable code - used_in: list[str] = field(default_factory=list)  # Project/scene IDs

# TODO: Review unreachable code - # Creative metadata
# TODO: Review unreachable code - prompt: str | None = None
# TODO: Review unreachable code - notes: str | None = None
# TODO: Review unreachable code - rating: int | None = None  # 1-5 stars

# TODO: Review unreachable code - # Temporal
# TODO: Review unreachable code - created_at: datetime = field(default_factory=datetime.utcnow)
# TODO: Review unreachable code - last_used: datetime | None = None

# TODO: Review unreachable code - def matches_mood(self, mood: CreativeMood) -> bool:
# TODO: Review unreachable code - """Check if asset matches a mood."""
# TODO: Review unreachable code - return mood.value in self.mood_tags

# TODO: Review unreachable code - def has_style(self, style: str) -> bool:
# TODO: Review unreachable code - """Check if asset has a style."""
# TODO: Review unreachable code - return style.lower() in [s.lower() for s in self.style_tags]


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class CreativeWorkflow:
# TODO: Review unreachable code - """Represents a creative workflow."""

# TODO: Review unreachable code - id: str
# TODO: Review unreachable code - name: str
# TODO: Review unreachable code - description: str | None = None

# TODO: Review unreachable code - # Workflow definition
# TODO: Review unreachable code - steps: list[dict[str, Any]] = field(default_factory=list)
# TODO: Review unreachable code - current_step: int = 0

# TODO: Review unreachable code - # Context and parameters
# TODO: Review unreachable code - context: CreativeContext | None = None
# TODO: Review unreachable code - input_assets: list[str] = field(default_factory=list)
# TODO: Review unreachable code - output_assets: list[str] = field(default_factory=list)

# TODO: Review unreachable code - # Execution state
# TODO: Review unreachable code - status: str = "pending"  # pending, running, completed, failed
# TODO: Review unreachable code - started_at: datetime | None = None
# TODO: Review unreachable code - completed_at: datetime | None = None

# TODO: Review unreachable code - # Results
# TODO: Review unreachable code - success_count: int = 0
# TODO: Review unreachable code - failure_count: int = 0
# TODO: Review unreachable code - cost_estimate: float | None = None

# TODO: Review unreachable code - def add_step(self, step_type: str, parameters: dict[str, Any]) -> None:
# TODO: Review unreachable code - """Add a step to the workflow."""
# TODO: Review unreachable code - self.steps.append({"type": step_type, "parameters": parameters, "status": "pending"})

# TODO: Review unreachable code - def complete_step(self, success: bool = True) -> None:
# TODO: Review unreachable code - """Mark current step as complete."""
# TODO: Review unreachable code - if self.current_step < len(self.steps):
# TODO: Review unreachable code - self.steps[self.current_step]["status"] = "completed" if success else "failed"
# TODO: Review unreachable code - self.current_step += 1

# TODO: Review unreachable code - if success:
# TODO: Review unreachable code - self.success_count += 1
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - self.failure_count += 1


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class StyleEvolution:
# TODO: Review unreachable code - """Tracks how a style evolves over time."""

# TODO: Review unreachable code - style_name: str
# TODO: Review unreachable code - base_elements: dict[str, Any] = field(default_factory=dict)

# TODO: Review unreachable code - # Evolution history
# TODO: Review unreachable code - iterations: list[dict[str, Any]] = field(default_factory=list)
# TODO: Review unreachable code - current_version: int = 1

# TODO: Review unreachable code - # Learned preferences
# TODO: Review unreachable code - successful_elements: list[str] = field(default_factory=list)
# TODO: Review unreachable code - avoided_elements: list[str] = field(default_factory=list)

# TODO: Review unreachable code - # Statistics
# TODO: Review unreachable code - usage_count: int = 0
# TODO: Review unreachable code - success_rate: float = 0.0

# TODO: Review unreachable code - def record_iteration(self, elements: dict[str, Any], success: bool) -> None:
# TODO: Review unreachable code - """Record a style iteration."""
# TODO: Review unreachable code - self.iterations.append(
# TODO: Review unreachable code - {
# TODO: Review unreachable code - "version": self.current_version,
# TODO: Review unreachable code - "elements": elements,
# TODO: Review unreachable code - "success": success,
# TODO: Review unreachable code - "timestamp": datetime.now(UTC),
# TODO: Review unreachable code - }
# TODO: Review unreachable code - )

# TODO: Review unreachable code - if success:
# TODO: Review unreachable code - # Learn from successful iterations
# TODO: Review unreachable code - for key, value in elements.items():
# TODO: Review unreachable code - if isinstance(value, str) and value not in self.successful_elements:
# TODO: Review unreachable code - self.successful_elements.append(value)

# TODO: Review unreachable code - self.usage_count += 1
# TODO: Review unreachable code - self.current_version += 1

# TODO: Review unreachable code - # Update success rate
# TODO: Review unreachable code - successful = sum(1 for i in self.iterations if i is not None and i["success"])
# TODO: Review unreachable code - self.success_rate = successful / len(self.iterations)

# TODO: Review unreachable code - def get_evolved_style(self) -> dict[str, Any]:
# TODO: Review unreachable code - """Get the current evolved style."""
# TODO: Review unreachable code - evolved = self.base_elements.copy()

# TODO: Review unreachable code - # Add successful elements
# TODO: Review unreachable code - if self.successful_elements:
# TODO: Review unreachable code - evolved["proven_elements"] = self.successful_elements[:5]  # Top 5

# TODO: Review unreachable code - # Note avoided elements
# TODO: Review unreachable code - if self.avoided_elements:
# TODO: Review unreachable code - evolved["avoid"] = self.avoided_elements

# TODO: Review unreachable code - return evolved


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class CreativeMemoryEntry:
# TODO: Review unreachable code - """An entry in creative memory."""

# TODO: Review unreachable code - id: str
# TODO: Review unreachable code - timestamp: datetime
# TODO: Review unreachable code - entry_type: str  # 'search', 'creation', 'feedback', 'discovery'

# TODO: Review unreachable code - # Content
# TODO: Review unreachable code - description: str
# TODO: Review unreachable code - tags: list[str] = field(default_factory=list)

# TODO: Review unreachable code - # Context
# TODO: Review unreachable code - project_id: str | None = None
# TODO: Review unreachable code - workflow_id: str | None = None
# TODO: Review unreachable code - related_assets: list[str] = field(default_factory=list)

# TODO: Review unreachable code - # Outcome
# TODO: Review unreachable code - success: bool = True
# TODO: Review unreachable code - impact_score: float = 0.0  # How important was this

# TODO: Review unreachable code - def age_days(self) -> int:
# TODO: Review unreachable code - """Get age of memory in days."""
# TODO: Review unreachable code - return (datetime.now(UTC) - self.timestamp).days


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class CreativePattern:
# TODO: Review unreachable code - """A pattern in creative work."""

# TODO: Review unreachable code - pattern_type: str  # 'style_combination', 'workflow_sequence', 'time_preference'
# TODO: Review unreachable code - elements: list[str]

# TODO: Review unreachable code - # Statistics
# TODO: Review unreachable code - occurrence_count: int = 1
# TODO: Review unreachable code - success_rate: float = 1.0
# TODO: Review unreachable code - last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))

# TODO: Review unreachable code - # Context
# TODO: Review unreachable code - common_contexts: list[str] = field(default_factory=list)

# TODO: Review unreachable code - def record_occurrence(self, success: bool, context: str | None = None) -> None:
# TODO: Review unreachable code - """Record a pattern occurrence."""
# TODO: Review unreachable code - self.occurrence_count += 1
# TODO: Review unreachable code - self.last_seen = datetime.now(UTC)

# TODO: Review unreachable code - # Update success rate
# TODO: Review unreachable code - if not success:
# TODO: Review unreachable code - self.success_rate = (
# TODO: Review unreachable code - (self.success_rate * (self.occurrence_count - 1)) + (1.0 if success else 0.0)
# TODO: Review unreachable code - ) / self.occurrence_count

# TODO: Review unreachable code - # Track context
# TODO: Review unreachable code - if context and context not in self.common_contexts:
# TODO: Review unreachable code - self.common_contexts.append(context)
# TODO: Review unreachable code - if len(self.common_contexts) > 5:
# TODO: Review unreachable code - self.common_contexts.pop(0)

# TODO: Review unreachable code - def is_successful(self) -> bool:
# TODO: Review unreachable code - """Check if pattern is generally successful."""
# TODO: Review unreachable code - return self.success_rate > 0.7 and self.occurrence_count > 3
