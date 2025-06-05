"""Video export templates for various editing software.

This module provides export functionality for:
- DaVinci Resolve (EDL/XML format)
- CapCut (JSON format)
- Generic timeline formats
"""

import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class TimelineClip:
    """A single clip in the timeline."""
    
    asset_path: Path
    start_time: float  # Timeline position in seconds
    duration: float    # Clip duration in seconds
    in_point: float = 0.0  # Source in point
    out_point: Optional[float] = None  # Source out point (None = use duration)
    
    # Transitions
    transition_in: Optional[str] = None  # Transition type
    transition_in_duration: float = 0.0
    transition_out: Optional[str] = None
    transition_out_duration: float = 0.0
    
    # Effects and metadata
    effects: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Sync info
    beat_aligned: bool = False
    sync_point: Optional[float] = None  # Beat/marker time
    
    @property
    def end_time(self) -> float:
        """Get the end time of this clip on the timeline."""
        return self.start_time + self.duration
    
    @property
    def source_duration(self) -> float:
        """Get the source clip duration."""
        if self.out_point is not None:
            return self.out_point - self.in_point
        return self.duration


@dataclass 
class Timeline:
    """Video timeline with clips and metadata."""
    
    name: str
    duration: float
    frame_rate: float = 30.0
    resolution: Tuple[int, int] = (1920, 1080)
    
    clips: List[TimelineClip] = field(default_factory=list)
    audio_tracks: List[Dict[str, Any]] = field(default_factory=list)
    markers: List[Dict[str, Any]] = field(default_factory=list)  # Beat markers, etc.
    
    metadata: Dict[str, Any] = field(default_factory=dict)


class DaVinciResolveExporter:
    """Export timelines for DaVinci Resolve."""
    
    @staticmethod
    def export_edl(timeline: Timeline, output_path: Path) -> bool:
        """Export timeline as EDL (Edit Decision List).
        
        EDL is a simple text format supported by most NLEs.
        """
        try:
            with open(output_path, 'w') as f:
                # EDL Header
                f.write(f"TITLE: {timeline.name}\n")
                f.write(f"FCM: NON-DROP FRAME\n\n")
                
                # Write clips
                for i, clip in enumerate(timeline.clips, 1):
                    # EDL format: edit_number reel_name channel operation
                    # Source and record timecodes
                    edit_num = f"{i:03d}"
                    reel_name = clip.asset_path.stem[:7].upper()  # Max 8 chars
                    
                    # Convert times to timecode
                    src_in = DaVinciResolveExporter._seconds_to_timecode(
                        clip.in_point, timeline.frame_rate
                    )
                    src_out = DaVinciResolveExporter._seconds_to_timecode(
                        clip.source_duration, timeline.frame_rate
                    )
                    rec_in = DaVinciResolveExporter._seconds_to_timecode(
                        clip.start_time, timeline.frame_rate
                    )
                    rec_out = DaVinciResolveExporter._seconds_to_timecode(
                        clip.end_time, timeline.frame_rate
                    )
                    
                    # Write edit
                    f.write(f"{edit_num}  {reel_name} V     C        ")
                    f.write(f"{src_in} {src_out} {rec_in} {rec_out}\n")
                    
                    # Add file path as comment
                    f.write(f"* FROM CLIP NAME: {clip.asset_path.name}\n")
                    f.write(f"* SOURCE FILE: {clip.asset_path}\n")
                    
                    # Add transition if present
                    if clip.transition_in:
                        trans_duration = int(clip.transition_in_duration * timeline.frame_rate)
                        f.write(f"* EFFECT NAME: {clip.transition_in.upper()}\n")
                        f.write(f"* EFFECT DURATION: {trans_duration}\n")
                    
                    f.write("\n")
                
            logger.info(f"Exported EDL to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export EDL: {e}")
            return False
    
    @staticmethod
    def export_xml(timeline: Timeline, output_path: Path) -> bool:
        """Export timeline as DaVinci Resolve XML (FCPXML-like format)."""
        try:
            # Create root element
            root = ET.Element("fcpxml", version="1.8")
            
            # Add resources
            resources = ET.SubElement(root, "resources")
            
            # Create format resource
            format_elem = ET.SubElement(
                resources, "format",
                id="r1",
                name=f"{timeline.resolution[0]}x{timeline.resolution[1]}",
                frameDuration=f"1/{int(timeline.frame_rate)}s",
                width=str(timeline.resolution[0]),
                height=str(timeline.resolution[1])
            )
            
            # Add assets
            for i, clip in enumerate(timeline.clips):
                asset = ET.SubElement(
                    resources, "asset",
                    id=f"r{i+2}",
                    name=clip.asset_path.stem,
                    src=str(clip.asset_path),
                    hasVideo="1"
                )
                if clip.metadata.get("duration"):
                    asset.set("duration", f"{clip.metadata['duration']}s")
            
            # Create project
            library = ET.SubElement(root, "library")
            event = ET.SubElement(library, "event", name=timeline.name)
            project = ET.SubElement(event, "project", name=timeline.name)
            
            # Create sequence
            sequence = ET.SubElement(
                project, "sequence",
                format="r1",
                duration=f"{timeline.duration}s"
            )
            
            # Create spine (main timeline)
            spine = ET.SubElement(sequence, "spine")
            
            # Add clips to spine
            for i, clip in enumerate(timeline.clips):
                # Create clip element
                clip_elem = ET.SubElement(
                    spine, "clip",
                    name=clip.asset_path.stem,
                    ref=f"r{i+2}",
                    offset=f"{clip.start_time}s",
                    duration=f"{clip.duration}s"
                )
                
                # Add transitions
                if clip.transition_in:
                    trans = ET.SubElement(
                        clip_elem, "transition",
                        name=clip.transition_in,
                        duration=f"{clip.transition_in_duration}s"
                    )
                
                # Add markers for beat sync
                if clip.beat_aligned and clip.sync_point:
                    marker = ET.SubElement(
                        clip_elem, "marker",
                        start=f"{clip.sync_point}s",
                        value="Beat Sync"
                    )
            
            # Add timeline markers
            for marker in timeline.markers:
                marker_elem = ET.SubElement(
                    sequence, "marker",
                    start=f"{marker['time']}s",
                    value=marker.get('name', 'Marker'),
                    note=marker.get('note', '')
                )
            
            # Write XML
            tree = ET.ElementTree(root)
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            logger.info(f"Exported DaVinci Resolve XML to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export XML: {e}")
            return False
    
    @staticmethod
    def _seconds_to_timecode(seconds: float, fps: float) -> str:
        """Convert seconds to timecode format HH:MM:SS:FF."""
        total_frames = int(seconds * fps)
        hours = total_frames // (3600 * int(fps))
        minutes = (total_frames % (3600 * int(fps))) // (60 * int(fps))
        secs = (total_frames % (60 * int(fps))) // int(fps)
        frames = total_frames % int(fps)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"


class CapCutExporter:
    """Export timelines for CapCut mobile editor."""
    
    @staticmethod
    def export_json(timeline: Timeline, output_path: Path) -> bool:
        """Export timeline as CapCut-compatible JSON."""
        try:
            # CapCut project structure
            project = {
                "version": "1.0",
                "project_name": timeline.name,
                "create_time": datetime.now().isoformat(),
                "duration": int(timeline.duration * 1000),  # milliseconds
                "resolution": {
                    "width": timeline.resolution[0],
                    "height": timeline.resolution[1]
                },
                "fps": timeline.frame_rate,
                "tracks": {
                    "video": [],
                    "audio": [],
                    "effect": [],
                    "text": []
                },
                "materials": [],
                "markers": []
            }
            
            # Add materials (assets)
            material_map = {}
            for i, clip in enumerate(timeline.clips):
                material_id = hashlib.md5(str(clip.asset_path).encode()).hexdigest()[:8]
                if material_id not in material_map:
                    material = {
                        "id": material_id,
                        "type": "video",
                        "path": str(clip.asset_path),
                        "name": clip.asset_path.name,
                        "duration": int(clip.duration * 1000)
                    }
                    project["materials"].append(material)
                    material_map[material_id] = material
            
            # Add clips to video track
            for i, clip in enumerate(timeline.clips):
                material_id = hashlib.md5(str(clip.asset_path).encode()).hexdigest()[:8]
                
                clip_data = {
                    "id": f"clip_{i}",
                    "material_id": material_id,
                    "in_point": int(clip.in_point * 1000),
                    "out_point": int((clip.out_point or clip.duration) * 1000),
                    "start_time": int(clip.start_time * 1000),
                    "duration": int(clip.duration * 1000),
                    "speed": 1.0,
                    "volume": 1.0
                }
                
                # Add transition
                if clip.transition_in:
                    clip_data["transition_in"] = {
                        "type": CapCutExporter._map_transition(clip.transition_in),
                        "duration": int(clip.transition_in_duration * 1000)
                    }
                
                # Add effects
                if clip.effects:
                    clip_data["effects"] = []
                    for effect in clip.effects:
                        clip_data["effects"].append({
                            "type": effect.get("type", "unknown"),
                            "params": effect.get("params", {})
                        })
                
                # Add beat sync flag
                if clip.beat_aligned:
                    clip_data["beat_sync"] = True
                    if clip.sync_point:
                        clip_data["sync_point"] = int(clip.sync_point * 1000)
                
                project["tracks"]["video"].append(clip_data)
            
            # Add markers
            for marker in timeline.markers:
                project["markers"].append({
                    "time": int(marker["time"] * 1000),
                    "name": marker.get("name", ""),
                    "color": marker.get("color", "#FF0000"),
                    "type": marker.get("type", "beat")
                })
            
            # Add audio tracks
            for audio in timeline.audio_tracks:
                project["tracks"]["audio"].append({
                    "id": audio.get("id", f"audio_{len(project['tracks']['audio'])}"),
                    "path": audio.get("path", ""),
                    "start_time": int(audio.get("start_time", 0) * 1000),
                    "duration": int(audio.get("duration", timeline.duration) * 1000),
                    "volume": audio.get("volume", 1.0)
                })
            
            # Add suggested transitions based on mood
            if timeline.metadata.get("mood"):
                project["suggestions"] = CapCutExporter._get_mood_suggestions(
                    timeline.metadata["mood"]
                )
            
            # Write JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(project, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported CapCut JSON to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CapCut JSON: {e}")
            return False
    
    @staticmethod
    def _map_transition(transition_name: str) -> str:
        """Map generic transition names to CapCut types."""
        mapping = {
            "crossfade": "fade",
            "dissolve": "fade",
            "wipe": "wipe_right",
            "slide": "slide_right",
            "zoom": "zoom_in",
            "fade": "fade"
        }
        return mapping.get(transition_name.lower(), "fade")
    
    @staticmethod
    def _get_mood_suggestions(mood: str) -> Dict[str, Any]:
        """Get editing suggestions based on mood."""
        suggestions = {
            "energetic": {
                "transitions": ["zoom_in", "slide_right", "glitch"],
                "effects": ["shake", "flash", "speed_ramp"],
                "pace": "fast"
            },
            "calm": {
                "transitions": ["fade", "dissolve"],
                "effects": ["blur", "glow"],
                "pace": "slow"
            },
            "dramatic": {
                "transitions": ["fade_to_black", "cross_blur"],
                "effects": ["vignette", "contrast_boost"],
                "pace": "medium"
            },
            "upbeat": {
                "transitions": ["bounce", "spin", "slide"],
                "effects": ["color_pop", "light_leak"],
                "pace": "fast"
            }
        }
        return suggestions.get(mood, suggestions["calm"])


class ProxyGenerator:
    """Generate proxy files for smooth editing."""
    
    @staticmethod
    async def generate_proxies(
        timeline: Timeline,
        output_dir: Path,
        proxy_resolution: Tuple[int, int] = (1280, 720),
        codec: str = "h264"
    ) -> Dict[str, Path]:
        """Generate proxy files for all clips in timeline.
        
        Returns mapping of original path to proxy path.
        """
        import asyncio
        import aiofiles
        
        proxy_map = {}
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for clip in timeline.clips:
            if clip.asset_path.suffix.lower() in ['.jpg', '.png', '.webp']:
                # For images, just copy or resize
                proxy_path = output_dir / f"{clip.asset_path.stem}_proxy.jpg"
                
                # Use PIL to resize
                from PIL import Image
                img = Image.open(clip.asset_path)
                img.thumbnail(proxy_resolution, Image.Resampling.LANCZOS)
                img.save(proxy_path, "JPEG", quality=85)
                
                proxy_map[str(clip.asset_path)] = proxy_path
                logger.info(f"Created image proxy: {proxy_path}")
                
            elif clip.asset_path.suffix.lower() in ['.mp4', '.mov', '.avi']:
                # For video, use ffmpeg to create proxy
                proxy_path = output_dir / f"{clip.asset_path.stem}_proxy.mp4"
                
                cmd = [
                    'ffmpeg', '-i', str(clip.asset_path),
                    '-vf', f'scale={proxy_resolution[0]}:{proxy_resolution[1]}',
                    '-c:v', codec,
                    '-preset', 'fast',
                    '-crf', '23',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-y',  # Overwrite
                    str(proxy_path)
                ]
                
                try:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.PIPE
                    )
                    _, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        proxy_map[str(clip.asset_path)] = proxy_path
                        logger.info(f"Created video proxy: {proxy_path}")
                    else:
                        logger.error(f"Failed to create proxy: {stderr.decode()}")
                        
                except Exception as e:
                    logger.error(f"Proxy generation failed for {clip.asset_path}: {e}")
        
        return proxy_map


class VideoExportManager:
    """Main class for managing video exports."""
    
    def __init__(self):
        """Initialize export manager."""
        self.davinci_exporter = DaVinciResolveExporter()
        self.capcut_exporter = CapCutExporter()
        self.proxy_generator = ProxyGenerator()
    
    async def export_timeline(
        self,
        timeline: Timeline,
        output_dir: Path,
        formats: List[str] = ["edl", "xml", "capcut"],
        generate_proxies: bool = False,
        proxy_resolution: Tuple[int, int] = (1280, 720)
    ) -> Dict[str, Any]:
        """Export timeline in multiple formats.
        
        Args:
            timeline: Timeline to export
            output_dir: Directory for output files
            formats: List of formats to export ("edl", "xml", "capcut")
            generate_proxies: Whether to generate proxy files
            proxy_resolution: Resolution for proxy files
            
        Returns:
            Dictionary with export results and paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = {
            "success": True,
            "exports": {},
            "proxies": {}
        }
        
        # Export in requested formats
        if "edl" in formats:
            edl_path = output_dir / f"{timeline.name}.edl"
            if self.davinci_exporter.export_edl(timeline, edl_path):
                results["exports"]["edl"] = edl_path
            else:
                results["success"] = False
        
        if "xml" in formats:
            xml_path = output_dir / f"{timeline.name}.xml"
            if self.davinci_exporter.export_xml(timeline, xml_path):
                results["exports"]["xml"] = xml_path
            else:
                results["success"] = False
        
        if "capcut" in formats:
            json_path = output_dir / f"{timeline.name}_capcut.json"
            if self.capcut_exporter.export_json(timeline, json_path):
                results["exports"]["capcut"] = json_path
            else:
                results["success"] = False
        
        # Generate proxies if requested
        if generate_proxies:
            proxy_dir = output_dir / "proxies"
            proxy_map = await self.proxy_generator.generate_proxies(
                timeline, proxy_dir, proxy_resolution
            )
            results["proxies"] = proxy_map
        
        return results