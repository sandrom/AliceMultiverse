"""DaVinci Resolve timeline export functionality."""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from .enums import TransitionType

logger = logging.getLogger(__name__)


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
