"""Video creation workflow for generating prompts and managing video projects.

This module helps create engaging video content by:
1. Analyzing selected images to generate video prompts
2. Suggesting camera movements and transitions
3. Managing storyboards and shot lists
4. Integrating with Kling for video generation
5. Using Flux Kontext for keyframe preparation
6. Exporting to DaVinci Resolve with timeline
"""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from xml.dom import minidom

import logging

from ..providers.provider_types import GenerationRequest, GenerationType
from ..storage.unified_duckdb import DuckDBSearch

logger = logging.getLogger(__name__)


class CameraMotion(Enum):
    """Camera motion types for video generation."""
    STATIC = "static"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    AUTO = "auto"
    TRACK_FORWARD = "track_forward"
    TRACK_BACKWARD = "track_backward"
    ORBIT_LEFT = "orbit_left"
    ORBIT_RIGHT = "orbit_right"


class TransitionType(Enum):
    """Transition types between shots."""
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    MOTION_BLUR = "motion_blur"
    MORPH = "morph"


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
        with open(file_path) as f:
            data = json.load(f)

        # Convert back to objects
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


class VideoCreationWorkflow:
    """Workflow for creating videos from selected images."""

    # Prompt templates for different video styles
    STYLE_TEMPLATES = {
        "cinematic": {
            "prefix": "Cinematic shot:",
            "camera_hints": ["dramatic angle", "film grain", "wide composition"],
            "motion_bias": [CameraMotion.TRACK_FORWARD, CameraMotion.ORBIT_LEFT, CameraMotion.ZOOM_IN],
            "duration": 5
        },
        "documentary": {
            "prefix": "Documentary footage:",
            "camera_hints": ["steady shot", "natural lighting", "observational"],
            "motion_bias": [CameraMotion.PAN_LEFT, CameraMotion.PAN_RIGHT, CameraMotion.STATIC],
            "duration": 4
        },
        "music_video": {
            "prefix": "Dynamic music video shot:",
            "camera_hints": ["rhythmic movement", "stylized", "high energy"],
            "motion_bias": [CameraMotion.ZOOM_IN, CameraMotion.ZOOM_OUT, CameraMotion.ORBIT_RIGHT],
            "duration": 3
        },
        "narrative": {
            "prefix": "Story scene:",
            "camera_hints": ["character focus", "emotional", "purposeful movement"],
            "motion_bias": [CameraMotion.TRACK_FORWARD, CameraMotion.TILT_UP, CameraMotion.STATIC],
            "duration": 5
        },
        "abstract": {
            "prefix": "Abstract visual:",
            "camera_hints": ["experimental", "fluid motion", "dreamlike"],
            "motion_bias": [CameraMotion.AUTO, CameraMotion.ORBIT_LEFT, CameraMotion.ZOOM_OUT],
            "duration": 4
        }
    }

    # Motion keywords that suggest camera movements
    MOTION_INDICATORS = {
        CameraMotion.ZOOM_IN: ["close-up", "detail", "intimate", "focus", "reveal"],
        CameraMotion.ZOOM_OUT: ["wide", "landscape", "establish", "context", "expand"],
        CameraMotion.PAN_LEFT: ["scan", "survey", "follow", "explore left"],
        CameraMotion.PAN_RIGHT: ["scan", "survey", "follow", "explore right"],
        CameraMotion.TILT_UP: ["rise", "ascend", "lookup", "tower", "sky"],
        CameraMotion.TILT_DOWN: ["descend", "ground", "drop", "fall"],
        CameraMotion.TRACK_FORWARD: ["approach", "enter", "advance", "push in"],
        CameraMotion.TRACK_BACKWARD: ["retreat", "exit", "pull back", "withdraw"],
        CameraMotion.ORBIT_LEFT: ["circle", "rotate", "around left"],
        CameraMotion.ORBIT_RIGHT: ["circle", "rotate", "around right"],
        CameraMotion.STATIC: ["still", "fixed", "stationary", "stable"]
    }

    def __init__(self, search_db: DuckDBSearch, understanding_provider: Any | None = None):
        """Initialize video creation workflow.
        
        Args:
            search_db: Database for searching assets
            understanding_provider: Optional AI provider for enhanced analysis
        """
        self.search_db = search_db
        self.understanding_provider = understanding_provider

    async def analyze_image_for_video(self, image_hash: str) -> dict[str, Any]:
        """Analyze a single image to extract video-relevant information.
        
        Args:
            image_hash: Hash of image to analyze
            
        Returns:
            Dictionary with motion suggestions and video metadata
        """
        # Get image metadata
        results, _ = self.search_db.search({"content_hash": image_hash}, limit=1)
        if not results:
            raise ValueError(f"Image not found: {image_hash}")

        metadata = results[0]
        tags = metadata.get("tags", [])

        # Analyze composition for camera motion
        composition_hints = self._analyze_composition(tags)

        # Determine suggested camera motion
        suggested_motion = self._suggest_camera_motion(tags, composition_hints)

        # Extract motion keywords
        motion_keywords = self._extract_motion_keywords(tags)

        return {
            "image_hash": image_hash,
            "file_path": metadata.get("file_path"),
            "tags": tags,
            "composition": composition_hints,
            "suggested_motion": suggested_motion,
            "motion_keywords": motion_keywords,
            "original_prompt": metadata.get("prompt", "")
        }

    def _analyze_composition(self, tags: list[str]) -> dict[str, Any]:
        """Analyze image composition from tags."""
        composition = {
            "has_character": any(tag in ["portrait", "person", "character", "face"] for tag in tags),
            "is_landscape": any(tag in ["landscape", "scenery", "environment", "vista"] for tag in tags),
            "has_architecture": any(tag in ["building", "architecture", "city", "interior"] for tag in tags),
            "is_abstract": any(tag in ["abstract", "pattern", "texture", "geometric"] for tag in tags),
            "has_action": any(tag in ["motion", "action", "movement", "dynamic"] for tag in tags),
            "depth": "deep" if any(tag in ["perspective", "depth", "layers"] for tag in tags) else "shallow"
        }
        return composition

    def _suggest_camera_motion(self, tags: list[str], composition: dict[str, Any]) -> CameraMotion:
        """Suggest camera motion based on image analysis."""
        # Check for explicit motion indicators in tags
        for motion, keywords in self.MOTION_INDICATORS.items():
            if any(keyword in tag.lower() for tag in tags for keyword in keywords):
                return motion

        # Rule-based suggestions
        if composition["has_character"] and not composition["is_landscape"]:
            return CameraMotion.ZOOM_IN  # Focus on character
        elif composition["is_landscape"] and composition["depth"] == "deep":
            return CameraMotion.TRACK_FORWARD  # Explore the landscape
        elif composition["has_architecture"]:
            return CameraMotion.ORBIT_LEFT  # Reveal architecture
        elif composition["is_abstract"]:
            return CameraMotion.AUTO  # Let AI decide
        elif composition["has_action"]:
            return CameraMotion.PAN_RIGHT  # Follow action
        else:
            return CameraMotion.STATIC  # Default to static

    def _extract_motion_keywords(self, tags: list[str]) -> list[str]:
        """Extract keywords that suggest motion or dynamism."""
        motion_words = [
            "flying", "running", "flowing", "spinning", "floating",
            "falling", "rising", "moving", "dancing", "jumping",
            "wind", "wave", "storm", "fire", "explosion",
            "speed", "velocity", "energy", "dynamic", "kinetic"
        ]

        return [tag for tag in tags if any(word in tag.lower() for word in motion_words)]

    async def generate_video_prompts(
        self,
        image_hashes: list[str],
        style: str = "cinematic",
        target_duration: int = 30,
        enhance_with_ai: bool = False
    ) -> VideoStoryboard:
        """Generate video prompts from selected images.
        
        Args:
            image_hashes: List of selected image hashes
            style: Video style (cinematic, documentary, etc.)
            target_duration: Target video duration in seconds
            enhance_with_ai: Use AI to enhance prompts
            
        Returns:
            Complete video storyboard
        """
        if style not in self.STYLE_TEMPLATES:
            style = "cinematic"

        style_template = self.STYLE_TEMPLATES[style]
        shots = []

        # Calculate duration per shot
        shot_duration = min(
            style_template["duration"],
            max(3, target_duration // len(image_hashes))
        )

        for i, image_hash in enumerate(image_hashes):
            # Analyze image
            analysis = await self.analyze_image_for_video(image_hash)

            # Generate base prompt
            prompt = self._generate_shot_prompt(analysis, style_template)

            # Enhance with AI if requested
            if enhance_with_ai and self.understanding_provider:
                prompt = await self._enhance_prompt_with_ai(
                    prompt,
                    analysis,
                    style_template
                )

            # Determine transitions
            transition_in = TransitionType.FADE if i == 0 else TransitionType.CUT
            transition_out = TransitionType.FADE if i == len(image_hashes) - 1 else TransitionType.CUT

            # Create shot description
            shot = ShotDescription(
                image_hash=image_hash,
                prompt=prompt,
                camera_motion=analysis["suggested_motion"],
                duration=shot_duration,
                transition_in=transition_in,
                transition_out=transition_out,
                motion_keywords=analysis["motion_keywords"],
                style_notes=style_template["camera_hints"]
            )

            shots.append(shot)

        # Create storyboard
        storyboard = VideoStoryboard(
            project_name=f"{style}_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            shots=shots,
            total_duration=sum(shot.duration for shot in shots),
            style_guide={
                "style": style,
                "template": style_template,
                "image_count": len(image_hashes)
            }
        )

        return storyboard

    def _generate_shot_prompt(self, analysis: dict[str, Any], style_template: dict[str, Any]) -> str:
        """Generate a video prompt for a single shot."""
        # Start with style prefix
        prompt_parts = [style_template["prefix"]]

        # Add descriptive elements from tags
        key_tags = analysis["tags"][:5]  # Use top 5 tags
        if key_tags:
            prompt_parts.append(", ".join(key_tags))

        # Add composition hints
        comp = analysis["composition"]
        if comp["has_character"]:
            prompt_parts.append("with character in focus")
        elif comp["is_landscape"]:
            prompt_parts.append("sweeping landscape view")

        # Add motion description
        motion = analysis["suggested_motion"]
        if motion != CameraMotion.STATIC:
            motion_desc = motion.value.replace("_", " ")
            prompt_parts.append(f"camera {motion_desc}")

        # Add style-specific camera hints
        if style_template["camera_hints"]:
            prompt_parts.append(style_template["camera_hints"][0])

        # Add motion keywords if present
        if analysis["motion_keywords"]:
            prompt_parts.append(f"featuring {', '.join(analysis['motion_keywords'][:2])}")

        return ", ".join(prompt_parts)

    async def _enhance_prompt_with_ai(
        self,
        base_prompt: str,
        analysis: dict[str, Any],
        style_template: dict[str, Any]
    ) -> str:
        """Use AI to enhance the video prompt."""
        if not self.understanding_provider:
            return base_prompt

        # Create enhancement prompt
        enhancement_prompt = f"""
        Enhance this video generation prompt for Kling AI:
        
        Base prompt: {base_prompt}
        Style: {style_template.get('prefix', 'cinematic')}
        Camera motion: {analysis['suggested_motion'].value}
        
        Make it more cinematic and specific for video generation.
        Keep it under 100 words. Focus on movement and atmosphere.
        """

        try:
            # Use understanding provider to enhance
            # This is a simplified version - you might want to add proper API integration
            enhanced = await self.understanding_provider.analyze_with_prompt(
                analysis["file_path"],
                enhancement_prompt
            )
            return enhanced.get("description", base_prompt)
        except Exception as e:
            logger.warning(f"Failed to enhance prompt with AI: {e}")
            return base_prompt

    def create_kling_requests(
        self,
        storyboard: VideoStoryboard,
        model: str = "kling-v2.1-pro-text",
        output_dir: Path | None = None
    ) -> list[GenerationRequest]:
        """Create Kling generation requests from storyboard.
        
        Args:
            storyboard: Video storyboard
            model: Kling model to use
            output_dir: Output directory for videos
            
        Returns:
            List of generation requests ready for Kling
        """
        requests = []

        for i, shot in enumerate(storyboard.shots):
            # Determine if this is image-to-video
            is_image_based = "image" in model

            # Create output path
            if output_dir:
                output_path = output_dir / f"shot_{i+1:02d}_{shot.image_hash[:8]}.mp4"
            else:
                output_path = None

            # Build parameters
            parameters = {
                "duration": shot.duration,
                "camera_motion": shot.camera_motion.value,
                "aspect_ratio": "16:9",  # Could be customized
            }

            # Add mode for pro/master models
            if "pro" in model:
                parameters["mode"] = "professional"
            elif "master" in model:
                parameters["mode"] = "master"

            # Create request
            request = GenerationRequest(
                prompt=shot.prompt,
                generation_type=GenerationType.VIDEO,
                model=model,
                reference_assets=[shot.image_hash] if is_image_based else None,
                parameters=parameters,
                output_path=output_path
            )

            requests.append(request)

        return requests

    def create_transition_guide(self, storyboard: VideoStoryboard) -> str:
        """Create a text guide for video editing with transitions.
        
        Args:
            storyboard: Video storyboard
            
        Returns:
            Formatted transition guide
        """
        lines = [
            f"# Transition Guide for {storyboard.project_name}",
            f"Total Duration: {storyboard.total_duration} seconds",
            f"Number of Shots: {len(storyboard.shots)}",
            "",
            "## Shot List with Transitions:",
            ""
        ]

        for i, shot in enumerate(storyboard.shots):
            lines.extend([
                f"### Shot {i+1}",
                f"- Duration: {shot.duration}s",
                f"- Camera: {shot.camera_motion.value}",
                f"- Transition In: {shot.transition_in.value}",
                f"- Transition Out: {shot.transition_out.value}",
                f"- Prompt: {shot.prompt}",
                ""
            ])

        lines.extend([
            "## Editing Notes:",
            "- Use 0.5s overlap for dissolve transitions",
            "- Match motion blur transitions with camera movement",
            "- Adjust timing based on music/rhythm if applicable",
            ""
        ])

        return "\n".join(lines)

    async def prepare_keyframes_with_flux(
        self,
        storyboard: VideoStoryboard,
        modifications: dict[str, str] | None = None
    ) -> dict[str, list[GenerationRequest]]:
        """Prepare keyframes using Flux Kontext for smoother video generation.
        
        Args:
            storyboard: Video storyboard
            modifications: Optional modifications per shot (shot_index -> modification prompt)
            
        Returns:
            Dictionary mapping shot indices to Flux generation requests
        """
        flux_requests = {}

        for i, shot in enumerate(storyboard.shots):
            requests = []

            # Base keyframe (original image)
            base_request = GenerationRequest(
                prompt=f"Prepare for video: {shot.prompt}",
                generation_type=GenerationType.IMAGE,
                model="flux-kontext-pro",
                reference_assets=[shot.image_hash],
                parameters={
                    "guidance_scale": 3.5,
                    "num_inference_steps": 28
                }
            )
            requests.append(base_request)

            # If modifications requested for this shot
            if modifications and str(i) in modifications:
                mod_request = GenerationRequest(
                    prompt=modifications[str(i)],
                    generation_type=GenerationType.IMAGE,
                    model="flux-kontext-pro",
                    reference_assets=[shot.image_hash],
                    parameters={
                        "guidance_scale": 4.0,
                        "num_inference_steps": 35
                    }
                )
                requests.append(mod_request)

            # Create transition frames if needed
            if i < len(storyboard.shots) - 1:
                next_shot = storyboard.shots[i + 1]
                if shot.transition_out in [TransitionType.MORPH, TransitionType.DISSOLVE]:
                    # Create intermediate frame for smooth transition
                    transition_request = GenerationRequest(
                        prompt=f"Blend between: {shot.prompt} and {next_shot.prompt}",
                        generation_type=GenerationType.IMAGE,
                        model="flux-kontext-pro-multi",
                        reference_assets=[shot.image_hash, next_shot.image_hash],
                        reference_weights=[1.5, 0.5],  # Favor current shot
                        parameters={
                            "guidance_scale": 3.0,
                            "num_inference_steps": 40
                        }
                    )
                    requests.append(transition_request)

            flux_requests[str(i)] = requests

        return flux_requests

    def export_to_davinci_resolve(
        self,
        storyboard: VideoStoryboard,
        video_files: dict[int, Path],
        project_name: str | None = None,
        frame_rate: float = 30.0,
        resolution: tuple[int, int] = (1920, 1080)
    ) -> Path:
        """Export storyboard and videos to DaVinci Resolve timeline format.
        
        Args:
            storyboard: Video storyboard
            video_files: Dict mapping shot index to video file paths
            project_name: Optional project name (uses storyboard name if not provided)
            frame_rate: Timeline frame rate (default: 30 fps)
            resolution: Timeline resolution (default: 1920x1080)
            
        Returns:
            Path to the exported .fcpxml file
        """
        project_name = project_name or storyboard.project_name

        # Create timeline XML
        timeline = DaVinciResolveTimeline(
            project_name=project_name,
            frame_rate=frame_rate,
            resolution=resolution
        )

        # Add shots to timeline
        current_time = 0
        for i, shot in enumerate(storyboard.shots):
            if i not in video_files:
                logger.warning(f"No video file for shot {i+1}, skipping")
                continue

            video_path = video_files[i]

            # Add clip to timeline
            timeline.add_clip(
                file_path=video_path,
                start_time=current_time,
                duration=shot.duration,
                shot_name=f"Shot_{i+1:02d}",
                notes=shot.prompt
            )

            # Add transitions
            if i > 0 and shot.transition_in != TransitionType.CUT:
                timeline.add_transition(
                    transition_type=shot.transition_in,
                    start_time=current_time,
                    duration=0.5  # Default 0.5s transition
                )

            current_time += shot.duration

        # Export timeline
        output_path = Path(f"{project_name}_timeline.fcpxml")
        timeline.export(output_path)

        return output_path


class DaVinciResolveTimeline:
    """Helper class to create DaVinci Resolve compatible timeline files."""

    def __init__(
        self,
        project_name: str,
        frame_rate: float = 30.0,
        resolution: tuple[int, int] = (1920, 1080)
    ):
        """Initialize timeline.
        
        Args:
            project_name: Name of the project
            frame_rate: Timeline frame rate
            resolution: Timeline resolution (width, height)
        """
        self.project_name = project_name
        self.frame_rate = frame_rate
        self.resolution = resolution
        self.clips = []
        self.transitions = []

        # Frame duration in seconds
        self.frame_duration = 1.0 / frame_rate

    def add_clip(
        self,
        file_path: Path,
        start_time: float,
        duration: float,
        shot_name: str,
        notes: str | None = None
    ):
        """Add a clip to the timeline.
        
        Args:
            file_path: Path to video file
            start_time: Start time in seconds
            duration: Duration in seconds
            shot_name: Name of the shot
            notes: Optional notes/comments
        """
        self.clips.append({
            "file_path": str(file_path),
            "start_time": start_time,
            "duration": duration,
            "shot_name": shot_name,
            "notes": notes or "",
            "start_frame": int(start_time * self.frame_rate),
            "duration_frames": int(duration * self.frame_rate)
        })

    def add_transition(
        self,
        transition_type: TransitionType,
        start_time: float,
        duration: float = 0.5
    ):
        """Add a transition between clips.
        
        Args:
            transition_type: Type of transition
            start_time: Start time of transition
            duration: Duration of transition
        """
        self.transitions.append({
            "type": transition_type.value,
            "start_time": start_time,
            "duration": duration,
            "start_frame": int(start_time * self.frame_rate),
            "duration_frames": int(duration * self.frame_rate)
        })

    def export(self, output_path: Path) -> None:
        """Export timeline to FCPXML format.
        
        Args:
            output_path: Path to save the .fcpxml file
        """
        # Create root element
        fcpxml = ET.Element("fcpxml", version="1.8")

        # Add resources
        resources = ET.SubElement(fcpxml, "resources")

        # Add format resource
        ET.SubElement(
            resources,
            "format",
            id="r1",
            name=f"{self.resolution[0]}x{self.resolution[1]} {self.frame_rate}p",
            frameDuration=f"{int(1000/self.frame_rate)}/1000s",
            width=str(self.resolution[0]),
            height=str(self.resolution[1])
        )

        # Add asset resources for each clip
        for i, clip in enumerate(self.clips):
            ET.SubElement(
                resources,
                "asset",
                id=f"r{i+2}",
                name=clip["shot_name"],
                src=f"file://{clip['file_path']}",
                start="0s",
                duration=f"{clip['duration']}s",
                hasVideo="1",
                hasAudio="1"
            )

        # Create project
        project = ET.SubElement(fcpxml, "project", name=self.project_name)

        # Create sequence
        sequence = ET.SubElement(
            project,
            "sequence",
            duration=f"{sum(c['duration'] for c in self.clips)}s",
            format="r1"
        )

        # Create spine (main timeline)
        spine = ET.SubElement(sequence, "spine")

        # Add clips to spine
        for i, clip in enumerate(self.clips):
            # Add clip
            clip_elem = ET.SubElement(
                spine,
                "clip",
                name=clip["shot_name"],
                offset=f"{clip['start_time']}s",
                duration=f"{clip['duration']}s",
                format="r1"
            )

            # Add asset reference
            ET.SubElement(
                clip_elem,
                "asset-clip",
                ref=f"r{i+2}",
                offset="0s",
                duration=f"{clip['duration']}s",
                format="r1"
            )

            # Add notes if present
            if clip["notes"]:
                note = ET.SubElement(clip_elem, "note")
                note.text = clip["notes"]

        # Add transitions
        for trans in self.transitions:
            # Find the clip at this time
            for i, clip in enumerate(self.clips):
                if abs(clip["start_time"] - trans["start_time"]) < 0.01:
                    # Add transition element
                    if trans["type"] == "fade":
                        ET.SubElement(
                            spine,
                            "transition",
                            name="Fade to Black",
                            offset=f"{trans['start_time']}s",
                            duration=f"{trans['duration']}s"
                        )
                    elif trans["type"] == "dissolve":
                        ET.SubElement(
                            spine,
                            "transition",
                            name="Cross Dissolve",
                            offset=f"{trans['start_time']}s",
                            duration=f"{trans['duration']}s"
                        )
                    break

        # Pretty print the XML
        xml_str = minidom.parseString(ET.tostring(fcpxml)).toprettyxml(indent="  ")

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(xml_str)

        logger.info(f"Exported DaVinci Resolve timeline to: {output_path}")
