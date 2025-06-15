"""
AI-powered shot list generation from detected scenes.
"""

import json
import logging
from pathlib import Path

from ..understanding.analyzer import ImageAnalyzer
from .models import Scene, SceneType, Shot, ShotList

logger = logging.getLogger(__name__)


class ShotListGenerator:
    """Generates professional shot lists from detected scenes."""

    # Shot type suggestions based on scene type
    SHOT_TYPE_TEMPLATES = {
        SceneType.ESTABLISHING: [
            ("Wide", 0.6, "Establish location and context"),
            ("Aerial/Drone", 0.3, "Show scale and geography"),
            ("Slow push in", 0.1, "Draw viewer into scene"),
        ],
        SceneType.DIALOGUE: [
            ("Over-shoulder", 0.3, "Show conversation perspective"),
            ("Medium close-up", 0.4, "Focus on speaker"),
            ("Two-shot", 0.2, "Show both participants"),
            ("Reaction shot", 0.1, "Capture listener response"),
        ],
        SceneType.ACTION: [
            ("Wide", 0.2, "Show full action"),
            ("Medium", 0.3, "Follow action"),
            ("Close-up", 0.3, "Detail shots"),
            ("Tracking", 0.2, "Dynamic movement"),
        ],
        SceneType.CLOSEUP: [
            ("Extreme close-up", 0.3, "Intimate detail"),
            ("Insert", 0.4, "Important object/detail"),
            ("Macro", 0.3, "Texture and detail"),
        ],
        SceneType.WIDE: [
            ("Wide", 0.5, "Full environment"),
            ("Extreme wide", 0.3, "Epic scale"),
            ("Pan", 0.2, "Reveal landscape"),
        ],
    }

    # Camera movement suggestions
    CAMERA_MOVEMENTS = {
        "static": "Locked off/tripod",
        "pan": "Horizontal pan",
        "tilt": "Vertical tilt",
        "dolly": "Dolly in/out",
        "track": "Tracking shot",
        "crane": "Crane/jib movement",
        "handheld": "Handheld for energy",
        "steadicam": "Smooth movement",
    }

    def __init__(
        self,
        style: str = "cinematic",
        shot_duration_range: tuple[float, float] = (2.0, 8.0),
        use_ai_suggestions: bool = True,
        ai_provider: str | None = None
    ):
        """
        Initialize shot list generator.
        
        Args:
            style: Visual style (cinematic, documentary, commercial, etc.)
            shot_duration_range: Min/max shot duration in seconds
            use_ai_suggestions: Whether to use AI for shot suggestions
            ai_provider: AI provider for analysis
        """
        self.style = style
        self.min_duration, self.max_duration = shot_duration_range
        self.use_ai_suggestions = use_ai_suggestions
        self.ai_provider = ai_provider

    def generate_shot_list(
        self,
        scenes: list[Scene],
        project_name: str = "Untitled Project",
        target_duration: float | None = None
    ) -> ShotList:
        """
        Generate a complete shot list from detected scenes.
        
        Args:
            scenes: List of detected scenes
            project_name: Name of the project
            target_duration: Target total duration (uses scene duration if None)
            
        Returns:
            Complete shot list
        """
        if not scenes:
            return ShotList(project_name=project_name, total_duration=0.0)

        # Calculate total duration
        total_duration = target_duration or sum(s.duration for s in scenes)

        # Create shot list
        shot_list = ShotList(
            project_name=project_name,
            total_duration=total_duration
        )

        # Add scenes
        for scene in scenes:
            shot_list.add_scene(scene)

        # Generate shots for each scene
        shot_number = 1
        for scene in scenes:
            shots = self._generate_shots_for_scene(
                scene,
                shot_number,
                target_duration
            )

            for shot in shots:
                shot_list.add_shot(shot)
                shot_number += 1

        # Add AI suggestions if enabled
        if self.use_ai_suggestions:
            shot_list = self._enhance_with_ai_suggestions(shot_list, scenes)

        return shot_list

    def _generate_shots_for_scene(
        self,
        scene: Scene,
        start_number: int,
        target_duration: float | None
    ) -> list[Shot]:
        """Generate shots for a single scene."""
        shots = []

        # Get shot templates for scene type
        templates = self.SHOT_TYPE_TEMPLATES.get(
            scene.scene_type,
            [("Medium", 1.0, "Standard coverage")]
        )

        # Calculate number of shots based on scene duration
        if scene.duration > 0:
            avg_shot_duration = (self.min_duration + self.max_duration) / 2
            num_shots = max(1, int(scene.duration / avg_shot_duration))
        else:
            # For image scenes
            num_shots = len(scene.images) if scene.images else 1

        # Distribute shot types
        shot_types = self._distribute_shot_types(templates, num_shots)

        # Create shots
        remaining_duration = scene.duration
        for i, (shot_type, description) in enumerate(shot_types):
            # Calculate shot duration
            if i < len(shot_types) - 1:
                duration = min(
                    self.max_duration,
                    max(self.min_duration, remaining_duration / (len(shot_types) - i))
                )
            else:
                duration = remaining_duration

            # Create shot
            shot = Shot(
                shot_number=start_number + i,
                scene_id=scene.scene_id,
                shot_type=shot_type,
                duration=duration,
                description=description
            )

            # Add technical details based on style
            self._add_technical_details(shot, scene, self.style)

            # Add reference image if available
            if scene.images and i < len(scene.images):
                shot.reference_images = [scene.images[i]]

            shots.append(shot)
            remaining_duration -= duration

        return shots

    def _distribute_shot_types(
        self,
        templates: list[tuple[str, float, str]],
        num_shots: int
    ) -> list[tuple[str, str]]:
        """Distribute shot types based on weights."""
        if num_shots <= 0:
            return []

        # Normalize weights
        total_weight = sum(t[1] for t in templates)

        distributed = []
        for shot_type, weight, description in templates:
            count = max(1, int(num_shots * weight / total_weight))
            distributed.extend([(shot_type, description)] * count)

        # Adjust to exact number
        if len(distributed) > num_shots:
            distributed = distributed[:num_shots]
        elif len(distributed) < num_shots:
            # Repeat pattern
            while len(distributed) < num_shots:
                distributed.append(distributed[len(distributed) % len(templates)])

        return distributed

    def _add_technical_details(self, shot: Shot, scene: Scene, style: str):
        """Add technical details based on style."""
        if style == "cinematic":
            # Cinematic style preferences
            shot.lens = self._suggest_lens_cinematic(shot.shot_type)
            shot.camera_movement = self._suggest_movement_cinematic(scene)
            shot.camera_angle = "Eye level" if "close" in shot.shot_type.lower() else "Slightly low"

        elif style == "documentary":
            # Documentary style
            shot.lens = "24-70mm zoom"
            shot.camera_movement = "Handheld" if scene.scene_type == SceneType.ACTION else "Tripod"
            shot.camera_angle = "Eye level"

        elif style == "commercial":
            # Commercial style
            shot.lens = self._suggest_lens_commercial(shot.shot_type)
            shot.camera_movement = "Steadicam" if scene.motion_intensity > 0.5 else "Dolly"
            shot.camera_angle = "Dynamic"

        # Add notes based on scene characteristics
        if scene.mood:
            shot.notes.append(f"Mood: {scene.mood}")
        if scene.dominant_colors:
            color_note = f"Key colors: {', '.join(c[0] for c in scene.dominant_colors[:3])}"
            shot.notes.append(color_note)

    def _suggest_lens_cinematic(self, shot_type: str) -> str:
        """Suggest lens for cinematic style."""
        lens_map = {
            "Wide": "18-24mm",
            "Extreme wide": "14-18mm",
            "Medium": "35-50mm",
            "Close-up": "85-135mm",
            "Extreme close-up": "100mm macro",
            "Two-shot": "50mm",
            "Over-shoulder": "85mm",
        }

        for key, lens in lens_map.items():
            if key.lower() in shot_type.lower():
                return lens

        return "50mm"  # Default

    def _suggest_lens_commercial(self, shot_type: str) -> str:
        """Suggest lens for commercial style."""
        if "wide" in shot_type.lower():
            return "24-35mm"
        elif "close" in shot_type.lower():
            return "85-105mm"
        else:
            return "50-85mm"

    def _suggest_movement_cinematic(self, scene: Scene) -> str:
        """Suggest camera movement for cinematic style."""
        if scene.scene_type == SceneType.ESTABLISHING:
            return "Slow dolly in"
        elif scene.scene_type == SceneType.ACTION:
            return "Tracking"
        elif scene.scene_type == SceneType.DIALOGUE:
            return "Static or subtle push"
        elif scene.motion_intensity > 0.7:
            return "Steadicam follow"
        else:
            return "Static with subtle movement"

    def _enhance_with_ai_suggestions(
        self,
        shot_list: ShotList,
        scenes: list[Scene]
    ) -> ShotList:
        """Enhance shot list with AI suggestions."""
        if not self.ai_provider:
            return shot_list

        try:
            analyzer = ImageAnalyzer()
            if self.ai_provider and self.ai_provider not in analyzer.analyzers:
                logger.warning(f"Provider {self.ai_provider} not available")
                return shot_list

            # Get overall project suggestions
            {
                "style": self.style,
                "scene_count": len(scenes),
                "total_duration": shot_list.total_duration,
                "scene_types": [s.scene_type.value for s in scenes],
            }

            # This would call the AI provider for suggestions
            # For now, add some generic notes
            shot_list.notes.extend([
                f"Visual style: {self.style}",
                f"Average shot duration: {shot_list.average_shot_duration:.1f}s",
                "Consider color grading for mood consistency",
            ])

            # Add scene-specific suggestions
            for scene in scenes:
                scene_shots = shot_list.get_shots_for_scene(scene.scene_id)
                if scene.ai_suggestions:
                    for shot in scene_shots:
                        shot.notes.extend(scene.ai_suggestions[:2])  # Add top suggestions

        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")

        return shot_list

    def export_shot_list(
        self,
        shot_list: ShotList,
        output_path: Path,
        format: str = "json"
    ):
        """
        Export shot list to file.
        
        Args:
            shot_list: Shot list to export
            output_path: Output file path
            format: Export format (json, csv, pdf)
        """
        output_path = Path(output_path)

        if format == "json":
            with open(output_path, 'w') as f:
                json.dump(shot_list.export_to_dict(), f, indent=2)

        elif format == "csv":
            import csv

            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Shot #", "Scene", "Type", "Duration",
                    "Description", "Camera", "Movement", "Notes"
                ])

                for shot in shot_list.shots:
                    writer.writerow([
                        shot.shot_number,
                        shot.scene_id,
                        shot.shot_type,
                        f"{shot.duration:.1f}s",
                        shot.description,
                        shot.camera_angle or "",
                        shot.camera_movement or "",
                        "; ".join(shot.notes)
                    ])

        elif format == "markdown":
            with open(output_path, 'w') as f:
                f.write(f"# Shot List: {shot_list.project_name}\n\n")
                f.write(f"**Total Duration**: {shot_list.total_duration:.1f}s\n")
                f.write(f"**Shot Count**: {shot_list.shot_count}\n")
                f.write(f"**Scene Count**: {shot_list.scene_count}\n\n")

                current_scene = None
                for shot in shot_list.shots:
                    if shot.scene_id != current_scene:
                        current_scene = shot.scene_id
                        # Find scene if it exists
                        scene = next((s for s in shot_list.scenes if s.scene_id == current_scene), None)
                        if scene:
                            f.write(f"\n## {current_scene} - {scene.scene_type.value}\n\n")
                            if scene.ai_description:
                                f.write(f"_{scene.ai_description}_\n\n")
                        else:
                            f.write(f"\n## {current_scene}\n\n")

                    f.write(f"**Shot {shot.shot_number}** - {shot.shot_type} ({shot.duration:.1f}s)\n")
                    f.write(f"- {shot.description}\n")
                    if shot.camera_movement:
                        f.write(f"- Camera: {shot.camera_movement}\n")
                    if shot.lens:
                        f.write(f"- Lens: {shot.lens}\n")
                    for note in shot.notes:
                        f.write(f"- {note}\n")
                    f.write("\n")

        logger.info(f"Exported shot list to {output_path} ({format})")
