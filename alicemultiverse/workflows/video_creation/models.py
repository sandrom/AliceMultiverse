"""Data models for video creation workflow."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .enums import CameraMotion, TransitionType


@dataclass
class ShotDescription:
    """Description of a single video shot."""
    image_hash: str
    prompt: str
    camera_motion: CameraMotion
    duration: int  # seconds
    transition_in: TransitionType
    transition_out: TransitionType
    motion_keywords: list[str] = field(default_factory=list)
    style_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "image_hash": self.image_hash,
            "prompt": self.prompt,
            "camera_motion": self.camera_motion.value,
            "duration": self.duration,
            "transition_in": self.transition_in.value,
            "transition_out": self.transition_out.value,
            "motion_keywords": self.motion_keywords,
            "style_notes": self.style_notes
        }


@dataclass
class VideoStoryboard:
    """Complete storyboard for a video project."""
    project_name: str
    shots: list[ShotDescription]
    total_duration: int
    style_guide: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_name": self.project_name,
            "shots": [shot.to_dict() for shot in self.shots],
            "total_duration": self.total_duration,
            "style_guide": self.style_guide,
            "created_at": self.created_at.isoformat()
        }

    def save(self, output_path: Path) -> None:
        """Save storyboard to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> "VideoStoryboard":
        """Load storyboard from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert shots back to ShotDescription objects
        shots = []
        for shot_data in data["shots"]:
            shot = ShotDescription(
                image_hash=shot_data["image_hash"],
                prompt=shot_data["prompt"],
                camera_motion=CameraMotion(shot_data["camera_motion"]),
                duration=shot_data["duration"],
                transition_in=TransitionType(shot_data["transition_in"]),
                transition_out=TransitionType(shot_data["transition_out"]),
                motion_keywords=shot_data.get("motion_keywords", []),
                style_notes=shot_data.get("style_notes", [])
            )
            shots.append(shot)
        
        return cls(
            project_name=data["project_name"],
            shots=shots,
            total_duration=data["total_duration"],
            style_guide=data["style_guide"],
            created_at=datetime.fromisoformat(data["created_at"])
        )