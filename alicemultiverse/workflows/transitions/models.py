"""
Data models for transition analysis.
"""

from dataclasses import dataclass
from enum import Enum


class TransitionType(str, Enum):
    """Types of transitions between scenes."""
    CUT = "cut"
    DISSOLVE = "dissolve"
    FADE = "fade"
    WIPE = "wipe"
    ZOOM = "zoom"
    MORPH = "morph"
    GLITCH = "glitch"
    MOMENTUM = "momentum_preserve"


class MotionDirection(str, Enum):
    """Primary motion directions in a scene."""
    STATIC = "static"
    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"
    UP_TO_DOWN = "up_to_down"
    DOWN_TO_UP = "down_to_up"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    CIRCULAR = "circular"
    DIAGONAL = "diagonal"


@dataclass
class MotionVector:
    """Represents motion characteristics of an image/scene."""
    direction: MotionDirection
    speed: float  # 0.0 (static) to 1.0 (fast motion)
    focal_point: tuple[float, float]  # Normalized coordinates (0-1)
    motion_lines: list[tuple[tuple[float, float], tuple[float, float]]]  # Start/end points
    confidence: float  # 0.0 to 1.0


@dataclass
class CompositionAnalysis:
    """Visual composition analysis of an image."""
    rule_of_thirds_points: list[tuple[float, float]]  # Key subject positions
    leading_lines: list[tuple[tuple[float, float], tuple[float, float]]]
    visual_weight_center: tuple[float, float]  # Center of visual mass
    empty_space_regions: list[tuple[float, float, float, float]]  # x, y, w, h
    dominant_colors: list[tuple[str, float]]  # Color hex and percentage
    brightness_map: dict[str, float]  # quadrant -> brightness (0-1)


@dataclass
class SceneCompatibility:
    """Compatibility score between two scenes."""
    overall_score: float  # 0.0 to 1.0
    motion_continuity: float  # How well motion flows
    color_harmony: float  # Color compatibility
    composition_match: float  # Visual balance compatibility
    suggested_transition: TransitionType
    transition_duration: float  # Suggested duration in seconds
    notes: list[str]  # Specific recommendations


@dataclass
class TransitionSuggestion:
    """Suggested transition between two images/scenes."""
    source_image: str
    target_image: str
    transition_type: TransitionType
    duration: float  # seconds
    timing: str | None = None  # e.g., "on_beat", "between_beats"
    effects: dict[str, any] | None = None  # Additional effect parameters
    compatibility: SceneCompatibility | None = None
    confidence: float = 0.0


@dataclass
class TransitionRule:
    """Rule for automatic transition selection."""
    name: str
    condition: dict[str, any]  # Conditions to match
    transition_type: TransitionType
    duration_multiplier: float = 1.0
    priority: int = 0  # Higher priority rules override lower ones
