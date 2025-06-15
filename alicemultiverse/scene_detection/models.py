"""
Data models for scene detection.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SceneType(str, Enum):
    """Types of scenes that can be detected."""
    ESTABLISHING = "establishing"      # Wide shots that establish location
    CLOSEUP = "closeup"               # Close-up shots of subjects
    MEDIUM = "medium"                 # Medium shots
    WIDE = "wide"                     # Wide/landscape shots
    ACTION = "action"                 # Action sequences
    DIALOGUE = "dialogue"             # Conversation scenes
    TRANSITION = "transition"         # Transitional scenes
    MONTAGE = "montage"              # Montage sequences
    DETAIL = "detail"                 # Detail/insert shots
    POV = "pov"                      # Point of view shots


class DetectionMethod(str, Enum):
    """Methods for detecting scene boundaries."""
    CONTENT = "content"               # Content-based (histogram, edges)
    MOTION = "motion"                 # Motion-based detection
    AUDIO = "audio"                   # Audio-based detection
    AI_VISION = "ai_vision"          # AI vision model detection
    COMBINED = "combined"             # Combined methods


class TransitionType(str, Enum):
    """Types of transitions between scenes."""
    CUT = "cut"                      # Hard cut
    FADE = "fade"                    # Fade in/out
    DISSOLVE = "dissolve"            # Cross dissolve
    WIPE = "wipe"                    # Wipe transition
    MOTION = "motion"                # Motion-based transition


@dataclass
class SceneTransition:
    """Transition between two scenes."""
    type: TransitionType
    duration: float  # seconds
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scene:
    """A detected scene in a video or image sequence."""
    scene_id: str
    scene_type: SceneType
    start_time: float  # seconds (0 for images)
    end_time: float    # seconds (same as start for images)
    duration: float

    # For image sequences
    start_frame: int | None = None
    end_frame: int | None = None
    images: list[Path] = field(default_factory=list)

    # Scene characteristics
    dominant_subject: str | None = None
    location: str | None = None
    mood: str | None = None
    action: str | None = None
    camera_movement: str | None = None

    # Technical details
    average_brightness: float = 0.0
    dominant_colors: list[tuple[str, float]] = field(default_factory=list)
    motion_intensity: float = 0.0

    # Detection details
    detection_method: DetectionMethod = DetectionMethod.CONTENT
    confidence: float = 0.0

    # Relationships
    previous_scene: str | None = None
    next_scene: str | None = None
    transition_in: SceneTransition | None = None
    transition_out: SceneTransition | None = None

    # AI analysis
    ai_description: str | None = None
    ai_tags: list[str] = field(default_factory=list)
    ai_suggestions: list[str] = field(default_factory=list)

    @property
    def is_image(self) -> bool:
        """Check if this is a single image scene."""
        return self.start_time == self.end_time

    @property
    def frame_count(self) -> int:
        """Get number of frames in scene."""
        if self.start_frame is not None and self.end_frame is not None:
            return self.end_frame - self.start_frame + 1
        return len(self.images)


@dataclass
class Shot:
    """A shot in a shot list."""
    shot_number: int
    scene_id: str
    shot_type: str  # "Wide", "Medium", "Close-up", etc.
    duration: float
    description: str

    # Technical details
    camera_angle: str | None = None
    camera_movement: str | None = None
    lens: str | None = None

    # Production notes
    notes: list[str] = field(default_factory=list)
    vfx_required: bool = False
    audio_notes: str | None = None

    # References
    reference_images: list[Path] = field(default_factory=list)
    storyboard: Path | None = None


@dataclass
class ShotList:
    """Complete shot list for a video project."""
    project_name: str
    total_duration: float
    shots: list[Shot] = field(default_factory=list)
    scenes: list[Scene] = field(default_factory=list)

    # Metadata
    created_date: str | None = None
    director: str | None = None
    cinematographer: str | None = None
    notes: list[str] = field(default_factory=list)

    # Statistics
    shot_count: int = 0
    scene_count: int = 0
    average_shot_duration: float = 0.0

    def add_shot(self, shot: Shot):
        """Add a shot and update statistics."""
        self.shots.append(shot)
        self.shot_count = len(self.shots)
        self._update_statistics()

    def add_scene(self, scene: Scene):
        """Add a scene."""
        self.scenes.append(scene)
        self.scene_count = len(self.scenes)

    def _update_statistics(self):
        """Update shot list statistics."""
        if self.shots:
            total_duration = sum(shot.duration for shot in self.shots)
            self.average_shot_duration = total_duration / len(self.shots)

    def get_shots_for_scene(self, scene_id: str) -> list[Shot]:
        """Get all shots for a specific scene."""
        return [shot for shot in self.shots if shot.scene_id == scene_id]

    def export_to_dict(self) -> dict[str, Any]:
        """Export shot list to dictionary format."""
        return {
            "project_name": self.project_name,
            "total_duration": self.total_duration,
            "shot_count": self.shot_count,
            "scene_count": self.scene_count,
            "average_shot_duration": self.average_shot_duration,
            "shots": [
                {
                    "number": shot.shot_number,
                    "scene": shot.scene_id,
                    "type": shot.shot_type,
                    "duration": shot.duration,
                    "description": shot.description,
                    "camera_angle": shot.camera_angle,
                    "camera_movement": shot.camera_movement,
                    "notes": shot.notes,
                }
                for shot in self.shots
            ],
            "scenes": [
                {
                    "id": scene.scene_id,
                    "type": scene.scene_type.value,
                    "duration": scene.duration,
                    "description": scene.ai_description,
                    "mood": scene.mood,
                }
                for scene in self.scenes
            ],
        }
