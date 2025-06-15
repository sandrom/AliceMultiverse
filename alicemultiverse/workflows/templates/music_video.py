"""Music video workflow template with beat synchronization.

Integrates music analysis, transition matching, and timeline generation.
"""

import logging
from pathlib import Path
from typing import Any

from alicemultiverse.transitions import TransitionMatcher
from alicemultiverse.workflows.base import WorkflowContext, WorkflowStep, WorkflowTemplate
from alicemultiverse.workflows.music_analyzer import MusicAnalyzer

logger = logging.getLogger(__name__)


class MusicVideoTemplate(WorkflowTemplate):
    """Template for creating music-driven videos with smart transitions.
    
    This workflow:
    1. Analyzes music for beats, tempo, and structure
    2. Selects and sequences images based on mood/energy
    3. Analyzes transitions between images
    4. Syncs cuts to music beats
    5. Exports timeline for editing software
    
    Parameters:
        music_file: Path to audio file (MP3, WAV, M4A)
        images: List of image paths or selection criteria
        sync_mode: How to sync ('beat', 'downbeat', 'section')
        transition_style: Transition preference ('smooth', 'energetic', 'auto')
        export_formats: List of export formats ('edl', 'xml', 'capcut')
        target_duration: Target video duration in seconds
        energy_matching: Match image energy to music energy
    """

    def __init__(self):
        super().__init__(name="MusicVideo")
        self.music_analyzer = MusicAnalyzer()
        self.transition_matcher = TransitionMatcher()

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define the music video workflow steps."""
        steps = []
        params = context.initial_params

        # Step 1: Analyze music
        steps.append(WorkflowStep(
            name="analyze_music",
            provider="local",
            operation="analyze_music",
            parameters={
                "music_file": params["music_file"],
                "detect_sections": True,
                "detect_beats": True,
                "analyze_mood": True,
            },
            cost_limit=0.0  # Local operation
        ))

        # Step 2: Select and sequence images
        steps.append(WorkflowStep(
            name="sequence_images",
            provider="local",
            operation="sequence_images",
            parameters={
                "images": params.get("images", []),
                "music_analysis_from": "analyze_music",
                "energy_matching": params.get("energy_matching", True),
                "target_duration": params.get("target_duration"),
                "selection_mode": params.get("selection_mode", "auto"),
            },
            condition="analyze_music.success",
            cost_limit=0.0
        ))

        # Step 3: Analyze transitions
        steps.append(WorkflowStep(
            name="analyze_transitions",
            provider="local",
            operation="analyze_transitions",
            parameters={
                "image_sequence_from": "sequence_images",
                "transition_style": params.get("transition_style", "auto"),
                "music_analysis_from": "analyze_music",
            },
            condition="sequence_images.success",
            cost_limit=0.0
        ))

        # Step 4: Create timeline
        steps.append(WorkflowStep(
            name="create_timeline",
            provider="local",
            operation="create_timeline",
            parameters={
                "sequence_from": "sequence_images",
                "transitions_from": "analyze_transitions",
                "music_from": "analyze_music",
                "sync_mode": params.get("sync_mode", "beat"),
                "min_shot_duration": params.get("min_shot_duration", 0.5),
                "max_shot_duration": params.get("max_shot_duration", 5.0),
            },
            condition="analyze_transitions.success",
            cost_limit=0.0
        ))

        # Step 5: Generate proxies (optional)
        if params.get("generate_proxies", True):
            steps.append(WorkflowStep(
                name="generate_proxies",
                provider="local",
                operation="generate_proxies",
                parameters={
                    "timeline_from": "create_timeline",
                    "proxy_resolution": params.get("proxy_resolution", "720p"),
                    "proxy_codec": params.get("proxy_codec", "h264"),
                },
                condition="create_timeline.success",
                cost_limit=0.0
            ))

        # Step 6: Export timeline
        export_formats = params.get("export_formats", ["xml"])
        for format_type in export_formats:
            steps.append(WorkflowStep(
                name=f"export_{format_type}",
                provider="local",
                operation=f"export_{format_type}",
                parameters={
                    "timeline_from": "create_timeline",
                    "proxies_from": "generate_proxies" if params.get("generate_proxies") else None,
                    "project_name": params.get("project_name", "Music Video"),
                    "frame_rate": params.get("frame_rate", 30),
                },
                condition="create_timeline.success",
                cost_limit=0.0
            ))

        return steps

    def execute_operation(self, step: WorkflowStep, context: WorkflowContext) -> dict[str, Any]:
        """Execute a specific operation in the workflow."""
        operation = step.operation
        params = step.parameters

        if operation == "analyze_music":
            return self._analyze_music(params)
        elif operation == "sequence_images":
            return self._sequence_images(params, context)
        elif operation == "analyze_transitions":
            return self._analyze_transitions(params, context)
        elif operation == "create_timeline":
            return self._create_timeline(params, context)
        elif operation == "generate_proxies":
            return self._generate_proxies(params, context)
        elif operation.startswith("export_"):
            return self._export_timeline(operation, params, context)
        else:
            return super().execute_operation(step, context)

    def _analyze_music(self, params: dict) -> dict[str, Any]:
        """Analyze music file for structure and beats."""
        music_file = params["music_file"]

        try:
            import asyncio
            analysis = asyncio.run(self.music_analyzer.analyze_audio(Path(music_file)))

            # Extract key information
            return {
                "success": True,
                "tempo": analysis["tempo"],
                "beats": analysis["beats"],
                "downbeats": analysis["downbeats"],
                "sections": analysis["sections"],
                "mood": analysis.get("mood", "neutral"),
                "energy_profile": analysis.get("energy_profile", []),
                "duration": analysis["duration"],
            }
        except Exception as e:
            logger.error(f"Music analysis failed: {e}")
            return {"success": False, "error": str(e)}

    def _sequence_images(self, params: dict, context: WorkflowContext) -> dict[str, Any]:
        """Select and sequence images based on music analysis."""
        images = params["images"]
        music_data = context.get_result(params["music_analysis_from"])

        if not music_data or not music_data.get("success"):
            return {"success": False, "error": "Music analysis not available"}

        try:
            # If energy matching is enabled, sort by energy levels
            if params.get("energy_matching"):
                sequenced = self._match_images_to_energy(
                    images,
                    music_data["energy_profile"],
                    music_data["sections"]
                )
            else:
                # Simple sequential ordering
                sequenced = images

            # Calculate shot count based on tempo and duration
            tempo = music_data["tempo"]
            duration = params.get("target_duration") or music_data["duration"]

            # Approximate shots based on tempo
            if tempo < 80:  # Slow
                avg_shot_duration = 3.0
            elif tempo < 120:  # Medium
                avg_shot_duration = 2.0
            else:  # Fast
                avg_shot_duration = 1.0

            shot_count = int(duration / avg_shot_duration)

            # Adjust sequence length
            if len(sequenced) > shot_count:
                sequenced = sequenced[:shot_count]
            elif len(sequenced) < shot_count:
                # Repeat images if needed
                import itertools
                sequenced = list(itertools.islice(
                    itertools.cycle(sequenced), shot_count
                ))

            return {
                "success": True,
                "sequence": sequenced,
                "shot_count": len(sequenced),
                "avg_shot_duration": avg_shot_duration,
            }
        except Exception as e:
            logger.error(f"Image sequencing failed: {e}")
            return {"success": False, "error": str(e)}

    def _match_images_to_energy(
        self,
        images: list[str],
        energy_profile: list[dict],
        sections: list[dict]
    ) -> list[str]:
        """Match images to music energy levels."""
        # This is a simplified implementation
        # In production, you'd analyze image characteristics

        # Sort images by assumed energy (for demo, use filename)
        # In reality, you'd analyze visual complexity, colors, etc.
        sorted_images = sorted(images)

        # Distribute images across sections
        sequenced = []
        for section in sections:
            section_energy = section.get("energy", 0.5)

            # High energy = later images (assumed more complex)
            if section_energy > 0.7:
                idx_start = int(len(sorted_images) * 0.7)
            elif section_energy > 0.4:
                idx_start = int(len(sorted_images) * 0.3)
            else:
                idx_start = 0

            # Add images for this section
            section_duration = section["end"] - section["start"]
            section_shots = max(1, int(section_duration / 2))  # 2 sec avg

            for i in range(section_shots):
                idx = (idx_start + i) % len(sorted_images)
                sequenced.append(sorted_images[idx])

        return sequenced

    def _analyze_transitions(self, params: dict, context: WorkflowContext) -> dict[str, Any]:
        """Analyze transitions between sequenced images."""
        sequence_data = context.get_result(params["image_sequence_from"])

        if not sequence_data or not sequence_data.get("success"):
            return {"success": False, "error": "Image sequence not available"}

        try:
            sequence = sequence_data["sequence"]
            music_data = context.get_result(params["music_analysis_from"])

            # Analyze transitions
            suggestions = self.transition_matcher.analyze_sequence(sequence)

            # Adjust based on music tempo
            tempo = music_data["tempo"]
            transition_style = params.get("transition_style", "auto")

            # Modify suggestions based on style
            if transition_style == "energetic" or tempo > 120:
                # Faster cuts, shorter transitions
                for s in suggestions:
                    s.duration *= 0.5
                    if s.transition_type.value == "dissolve":
                        s.transition_type = TransitionType.CUT
            elif transition_style == "smooth" or tempo < 80:
                # Longer transitions
                for s in suggestions:
                    s.duration *= 1.5

            return {
                "success": True,
                "transitions": [
                    {
                        "source": s.source_image,
                        "target": s.target_image,
                        "type": s.transition_type.value,
                        "duration": s.duration,
                        "confidence": s.confidence,
                    }
                    for s in suggestions
                ],
                "count": len(suggestions),
            }
        except Exception as e:
            logger.error(f"Transition analysis failed: {e}")
            return {"success": False, "error": str(e)}

    def _create_timeline(self, params: dict, context: WorkflowContext) -> dict[str, Any]:
        """Create timeline with beat-synced cuts."""
        sequence_data = context.get_result(params["sequence_from"])
        transitions_data = context.get_result(params["transitions_from"])
        music_data = context.get_result(params["music_from"])

        if not all([sequence_data, transitions_data, music_data]):
            return {"success": False, "error": "Required data not available"}

        try:
            sequence = sequence_data["sequence"]
            transitions = transitions_data["transitions"]
            sync_mode = params.get("sync_mode", "beat")

            # Get sync points based on mode
            if sync_mode == "beat":
                sync_points = music_data["beats"]
            elif sync_mode == "downbeat":
                sync_points = music_data["downbeats"]
            else:  # section
                sync_points = [s["start"] for s in music_data["sections"]]

            # Create timeline
            timeline = []
            current_time = 0.0

            for i, image in enumerate(sequence):
                # Find next sync point
                next_sync = next(
                    (sp for sp in sync_points if sp > current_time),
                    None
                )

                if next_sync is None:
                    # No more sync points, use average duration
                    duration = sequence_data["avg_shot_duration"]
                else:
                    duration = next_sync - current_time

                # Apply min/max constraints
                duration = max(params["min_shot_duration"], duration)
                duration = min(params["max_shot_duration"], duration)

                # Get transition info
                transition = None
                if i < len(transitions):
                    transition = transitions[i]

                timeline.append({
                    "clip_id": f"clip_{i}",
                    "source": image,
                    "start_time": current_time,
                    "duration": duration,
                    "transition": transition,
                    "beat_aligned": True,
                })

                current_time += duration

            return {
                "success": True,
                "timeline": timeline,
                "total_duration": current_time,
                "clip_count": len(timeline),
                "music_file": music_data.get("file_path"),
            }
        except Exception as e:
            logger.error(f"Timeline creation failed: {e}")
            return {"success": False, "error": str(e)}

    def _generate_proxies(self, params: dict, context: WorkflowContext) -> dict[str, Any]:
        """Generate proxy files for smooth editing."""
        timeline_data = context.get_result(params["timeline_from"])

        if not timeline_data or not timeline_data.get("success"):
            return {"success": False, "error": "Timeline not available"}

        try:
            # In a real implementation, this would generate actual proxy files
            # For now, we'll simulate the process
            timeline = timeline_data["timeline"]
            proxy_paths = {}

            for clip in timeline:
                source = clip["source"]
                proxy_path = f"/tmp/proxies/{Path(source).stem}_proxy.mp4"
                proxy_paths[source] = proxy_path

            return {
                "success": True,
                "proxy_paths": proxy_paths,
                "proxy_count": len(proxy_paths),
                "resolution": params["proxy_resolution"],
                "codec": params["proxy_codec"],
            }
        except Exception as e:
            logger.error(f"Proxy generation failed: {e}")
            return {"success": False, "error": str(e)}

    def _export_timeline(
        self,
        operation: str,
        params: dict,
        context: WorkflowContext
    ) -> dict[str, Any]:
        """Export timeline in requested format."""
        timeline_data = context.get_result(params["timeline_from"])

        if not timeline_data or not timeline_data.get("success"):
            return {"success": False, "error": "Timeline not available"}

        format_type = operation.replace("export_", "")

        try:
            timeline = timeline_data["timeline"]
            music_file = timeline_data.get("music_file")

            # Convert timeline data to Timeline object
            from alicemultiverse.workflows.video_export import (
                CapCutExporter,
                DaVinciResolveExporter,
                Timeline,
                TimelineClip,
            )

            # Create Timeline object
            timeline_obj = Timeline(
                name=params["project_name"],
                duration=timeline_data["total_duration"],
                frame_rate=params["frame_rate"]
            )

            # Add clips
            for clip_data in timeline:
                clip = TimelineClip(
                    asset_path=Path(clip_data["source"]),
                    start_time=clip_data["start_time"],
                    duration=clip_data["duration"],
                    beat_aligned=clip_data.get("beat_aligned", False)
                )
                if clip_data.get("transition"):
                    trans = clip_data["transition"]
                    clip.transition_in = trans.get("type")
                    clip.transition_in_duration = trans.get("duration", 0)
                timeline_obj.clips.append(clip)

            # Add audio track if available
            if music_file:
                timeline_obj.audio_tracks.append({
                    "path": music_file,
                    "start_time": 0,
                    "duration": timeline_data["total_duration"]
                })

            # Export based on format
            output_path = Path(f"{params['project_name']}_{format_type}.{format_type}")

            if format_type == "edl":
                success = DaVinciResolveExporter.export_edl(timeline_obj, output_path)
            elif format_type == "xml":
                success = DaVinciResolveExporter.export_xml(timeline_obj, output_path)
            elif format_type == "capcut":
                success = CapCutExporter.export_json(timeline_obj, output_path)
            else:
                return {"success": False, "error": f"Unknown format: {format_type}"}

            if not success:
                return {"success": False, "error": f"Failed to export {format_type}"}

            return {
                "success": True,
                "output_path": str(output_path),
                "format": format_type,
                "clip_count": len(timeline),
                "duration": timeline_data["total_duration"],
            }
        except Exception as e:
            logger.error(f"Timeline export failed: {e}")
            return {"success": False, "error": str(e)}

    def validate(self, context: WorkflowContext) -> list[str]:
        """Validate the workflow can execute."""
        errors = super().validate(context)
        params = context.initial_params

        # Check required parameters
        if not params.get("music_file"):
            errors.append("music_file is required")

        if not params.get("images"):
            errors.append("images list is required")

        # Check sync mode
        valid_sync_modes = ["beat", "downbeat", "section"]
        if params.get("sync_mode", "beat") not in valid_sync_modes:
            errors.append(f"Invalid sync_mode. Choose from: {valid_sync_modes}")

        # Check export formats
        valid_formats = ["edl", "xml", "capcut"]
        for fmt in params.get("export_formats", ["xml"]):
            if fmt not in valid_formats:
                errors.append(f"Invalid export format: {fmt}")

        return errors

    def estimate_cost(self, context: WorkflowContext) -> float:
        """Estimate total workflow cost."""
        # All operations are local, so no API costs
        return 0.0


class QuickMusicVideoTemplate(MusicVideoTemplate):
    """Quick music video template for fast results."""

    def __init__(self):
        super().__init__()
        self.name = "QuickMusicVideo"

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define quick music video steps."""
        # Override defaults for speed
        params = context.initial_params
        params.setdefault("sync_mode", "downbeat")  # Less cuts
        params.setdefault("transition_style", "energetic")  # Simple cuts
        params.setdefault("generate_proxies", False)  # Skip proxies
        params.setdefault("export_formats", ["edl"])  # Single format
        params.setdefault("min_shot_duration", 1.0)  # Longer shots

        return super().define_steps(context)


class CinematicMusicVideoTemplate(MusicVideoTemplate):
    """Cinematic music video template with advanced features."""

    def __init__(self):
        super().__init__()
        self.name = "CinematicMusicVideo"

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define cinematic music video steps."""
        # Override defaults for quality
        params = context.initial_params
        params.setdefault("sync_mode", "beat")  # Precise sync
        params.setdefault("transition_style", "smooth")  # Elegant transitions
        params.setdefault("generate_proxies", True)  # High-quality proxies
        params.setdefault("proxy_resolution", "1080p")
        params.setdefault("export_formats", ["xml", "edl"])  # Pro formats
        params.setdefault("energy_matching", True)  # Smart sequencing
        params.setdefault("min_shot_duration", 0.5)
        params.setdefault("max_shot_duration", 4.0)

        steps = super().define_steps(context)

        # Add color analysis step
        color_step = WorkflowStep(
            name="analyze_color_flow",
            provider="local",
            operation="analyze_color_flow",
            parameters={
                "sequence_from": "sequence_images",
                "smooth_transitions": True,
            },
            condition="sequence_images.success",
            cost_limit=0.0
        )

        # Insert after sequence_images
        steps.insert(2, color_step)

        return steps
