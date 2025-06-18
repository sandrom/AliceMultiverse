"""Story arc workflow template for narrative-driven video creation.

Creates videos following classic narrative structures.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any

from alicemultiverse.workflows.base import WorkflowContext, WorkflowStep, WorkflowTemplate

logger = logging.getLogger(__name__)


class StoryStructure(Enum):
    """Classic story structures."""
    THREE_ACT = "three_act"  # Setup, Confrontation, Resolution
    FIVE_ACT = "five_act"  # Exposition, Rising Action, Climax, Falling Action, Resolution
    HEROS_JOURNEY = "heros_journey"  # Call to Adventure, Trials, Return
    KISHOTEN = "kishoten"  # Introduction, Development, Twist, Conclusion
    CIRCULAR = "circular"  # End where you began with transformation


class StoryArcTemplate(WorkflowTemplate):
    """Template for creating narrative-driven videos with story structure.

    This workflow:
    1. Defines narrative structure and pacing
    2. Maps images to story beats
    3. Applies appropriate transitions for narrative flow
    4. Adjusts pacing for emotional impact
    5. Adds narrative markers for post-production

    Parameters:
        images: List of image paths or selection criteria
        structure: Story structure type (three_act, five_act, etc.)
        duration: Target video duration in seconds
        narrative_tags: Tags describing story elements per image
        emotion_curve: Desired emotional progression
        music_file: Optional music for pacing
        voiceover_markers: Add markers for voiceover timing
    """

    def __init__(self):
        super().__init__(name="StoryArc")
        self.story_beats = {
            StoryStructure.THREE_ACT: [
                ("setup", 0.25),  # 25% for setup
                ("confrontation", 0.50),  # 50% for confrontation
                ("resolution", 0.25)  # 25% for resolution
            ],
            StoryStructure.FIVE_ACT: [
                ("exposition", 0.15),
                ("rising_action", 0.25),
                ("climax", 0.20),
                ("falling_action", 0.25),
                ("resolution", 0.15)
            ],
            StoryStructure.HEROS_JOURNEY: [
                ("ordinary_world", 0.10),
                ("call_to_adventure", 0.10),
                ("trials", 0.50),
                ("revelation", 0.15),
                ("return", 0.15)
            ],
            StoryStructure.KISHOTEN: [
                ("ki_introduction", 0.20),
                ("sho_development", 0.30),
                ("ten_twist", 0.20),
                ("ketsu_conclusion", 0.30)
            ],
            StoryStructure.CIRCULAR: [
                ("beginning", 0.20),
                ("journey_out", 0.30),
                ("transformation", 0.30),
                ("return_changed", 0.20)
            ]
        }

        # Transition styles for different narrative moments
        self.narrative_transitions = {
            "setup": ["fade_in", "gentle_cut"],
            "rising_tension": ["quick_cut", "match_cut"],
            "climax": ["impact_cut", "flash"],
            "resolution": ["slow_fade", "dissolve"],
            "twist": ["whip_pan", "glitch"],
            "reflection": ["cross_dissolve", "fade_through_black"]
        }

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define the story arc workflow steps."""
        steps = []
        params = context.initial_params

        # Step 1: Analyze narrative content
        steps.append(WorkflowStep(
            name="analyze_narrative",
            provider="local",
            operation="analyze_narrative_content",
            parameters={
                "images": params["images"],
                "narrative_tags": params.get("narrative_tags", {}),
                "structure": params.get("structure", "three_act"),
                "detect_emotions": True,
                "detect_subjects": True,
                "detect_settings": True,
            },
            cost_limit=0.0  # Local analysis
        ))

        # Step 2: Map to story structure
        steps.append(WorkflowStep(
            name="map_story_beats",
            provider="local",
            operation="map_to_story_structure",
            parameters={
                "narrative_analysis_from": "analyze_narrative",
                "structure": params.get("structure", "three_act"),
                "duration": params["duration"],
                "emotion_curve": params.get("emotion_curve", "standard"),
                "preserve_chronology": params.get("preserve_chronology", True),
            },
            condition="analyze_narrative.success",
            cost_limit=0.0
        ))

        # Step 3: Design narrative transitions
        steps.append(WorkflowStep(
            name="design_transitions",
            provider="local",
            operation="design_narrative_transitions",
            parameters={
                "story_beats_from": "map_story_beats",
                "transition_style": "narrative_appropriate",
                "emphasis_moments": params.get("emphasis_moments", []),
                "pacing_variation": params.get("pacing_variation", "dynamic"),
            },
            condition="map_story_beats.success",
            cost_limit=0.0
        ))

        # Step 4: Apply pacing
        steps.append(WorkflowStep(
            name="apply_pacing",
            provider="local",
            operation="apply_narrative_pacing",
            parameters={
                "story_beats_from": "map_story_beats",
                "transitions_from": "design_transitions",
                "music_file": params.get("music_file"),
                "voiceover_space": params.get("voiceover_markers", False),
                "emotional_pacing": True,
            },
            condition="design_transitions.success",
            cost_limit=0.0
        ))

        # Step 5: Generate timeline
        steps.append(WorkflowStep(
            name="generate_timeline",
            provider="local",
            operation="generate_story_timeline",
            parameters={
                "pacing_from": "apply_pacing",
                "add_chapter_markers": True,
                "add_emotion_markers": True,
                "add_voiceover_markers": params.get("voiceover_markers", False),
                "export_formats": params.get("export_formats", ["edl", "xml"]),
            },
            condition="apply_pacing.success",
            cost_limit=0.0
        ))

        return steps

    def analyze_narrative_content(self, context: WorkflowContext) -> dict[str, Any]:
        """Analyze images for narrative content."""
        params = context.get_step_params("analyze_narrative")
        images = params["images"]
        narrative_tags = params.get("narrative_tags", {})

        analyzed_content = []
        for i, image_path in enumerate(images):
            # Extract narrative elements
            content = {
                "path": str(image_path),
                "index": i,
                "tags": narrative_tags.get(str(image_path), []),
                "emotion": self._detect_emotion(image_path),
                "subject": self._detect_subject(image_path),
                "setting": self._detect_setting(image_path),
                "narrative_weight": 1.0,  # Can be adjusted based on importance
            }
            analyzed_content.append(content)

        return {
            "content": analyzed_content,
            "total_images": len(images),
            "detected_themes": self._extract_themes(analyzed_content),
            "emotional_range": self._calculate_emotional_range(analyzed_content),
        }

    def map_to_story_structure(self, context: WorkflowContext) -> dict[str, Any]:
        """Map images to story beats."""
        params = context.get_step_params("map_story_beats")
        narrative_analysis = context.get_result("analyze_narrative")

        structure = StoryStructure(params["structure"])
        duration = params["duration"]

        # Get story beats for chosen structure
        beats = self.story_beats[structure]

        # Distribute images across beats
        content = narrative_analysis["content"]
        mapped_beats = []

        current_index = 0
        for beat_name, beat_proportion in beats:
            beat_duration = duration * beat_proportion
            beat_image_count = int(len(content) * beat_proportion)

            beat_images = content[current_index:current_index + beat_image_count]

            mapped_beats.append({
                "name": beat_name,
                "duration": beat_duration,
                "images": beat_images,
                "emotional_tone": self._get_beat_emotion(beat_name, structure),
                "pacing": self._get_beat_pacing(beat_name, structure),
                "transition_style": self._get_beat_transitions(beat_name),
            })

            current_index += beat_image_count

        return {
            "structure": structure.value,
            "beats": mapped_beats,
            "total_duration": duration,
            "beat_count": len(beats),
        }

    def design_narrative_transitions(self, context: WorkflowContext) -> dict[str, Any]:
        """Design transitions appropriate for narrative flow."""
        context.get_step_params("design_transitions")
        story_beats = context.get_result("map_story_beats")

        transitions = []

        for i, beat in enumerate(story_beats["beats"]):
            beat_transitions = []

            # Transitions within beat
            for j in range(len(beat["images"]) - 1):
                transition = {
                    "from": beat["images"][j]["path"],
                    "to": beat["images"][j + 1]["path"],
                    "type": self._select_transition(beat["transition_style"]),
                    "duration": self._get_transition_duration(beat["pacing"]),
                    "narrative_purpose": beat["name"],
                }
                beat_transitions.append(transition)

            # Transition to next beat
            if i < len(story_beats["beats"]) - 1:
                next_beat = story_beats["beats"][i + 1]
                if beat["images"] and next_beat["images"]:
                    transition = {
                        "from": beat["images"][-1]["path"],
                        "to": next_beat["images"][0]["path"],
                        "type": self._select_beat_transition(beat["name"], next_beat["name"]),
                        "duration": 1.0,  # Longer for beat changes
                        "narrative_purpose": f"{beat['name']}_to_{next_beat['name']}",
                    }
                    beat_transitions.append(transition)

            transitions.extend(beat_transitions)

        return {
            "transitions": transitions,
            "total_transitions": len(transitions),
            "transition_types": list(set(t["type"] for t in transitions)),
        }

    def apply_narrative_pacing(self, context: WorkflowContext) -> dict[str, Any]:
        """Apply pacing based on narrative needs."""
        params = context.get_step_params("apply_pacing")
        story_beats = context.get_result("map_story_beats")
        context.get_result("design_transitions")

        timeline = []
        current_time = 0.0

        for beat in story_beats["beats"]:
            beat_timeline = []

            # Calculate time per image in beat
            image_count = len(beat["images"])
            if image_count > 0:
                base_duration = beat["duration"] / image_count

                for i, image in enumerate(beat["images"]):
                    # Adjust duration based on narrative importance
                    duration = base_duration * self._get_pacing_multiplier(
                        beat["name"],
                        beat["pacing"],
                        i / image_count  # Position within beat
                    )

                    # Add voiceover space if requested
                    if params.get("voiceover_space") and self._needs_voiceover_space(beat["name"]):
                        duration *= 1.2  # 20% more time for voiceover

                    beat_timeline.append({
                        "image": image["path"],
                        "start": current_time,
                        "duration": duration,
                        "beat": beat["name"],
                        "emotion": image.get("emotion", "neutral"),
                    })

                    current_time += duration

            timeline.extend(beat_timeline)

        return {
            "timeline": timeline,
            "total_duration": current_time,
            "average_shot_duration": current_time / len(timeline) if timeline else 0,
            "pacing_profile": self._analyze_pacing_profile(timeline),
        }

    def generate_story_timeline(self, context: WorkflowContext) -> dict[str, Any]:
        """Generate final timeline with narrative markers."""
        params = context.get_step_params("generate_timeline")
        pacing = context.get_result("apply_pacing")
        story_beats = context.get_result("map_story_beats")
        transitions = context.get_result("design_transitions")

        # Create timeline with all elements
        timeline_data = {
            "clips": pacing["timeline"],
            "transitions": transitions["transitions"],
            "markers": self._generate_markers(story_beats, params),
            "metadata": {
                "structure": story_beats["structure"],
                "total_duration": pacing["total_duration"],
                "beat_count": story_beats["beat_count"],
                "created_by": "StoryArcTemplate",
            }
        }

        # Export in requested formats
        exports = {}
        for format in params.get("export_formats", ["edl"]):
            if format == "edl":
                exports["edl"] = self._export_edl(timeline_data)
            elif format == "xml":
                exports["xml"] = self._export_xml(timeline_data)
            elif format == "json":
                exports["json"] = timeline_data

        return {
            "timeline": timeline_data,
            "exports": exports,
            "summary": {
                "total_clips": len(timeline_data["clips"]),
                "total_duration": pacing["total_duration"],
                "structure": story_beats["structure"],
                "markers": len(timeline_data["markers"]),
            }
        }

    # Helper methods
    def _detect_emotion(self, image_path: Path) -> str:
        """Detect emotional tone of image."""
        # Placeholder - would use actual image analysis
        return "neutral"

    def _detect_subject(self, image_path: Path) -> str:
        """Detect main subject of image."""
        # Placeholder - would use actual image analysis
        return "unknown"

    def _detect_setting(self, image_path: Path) -> str:
        """Detect setting/location of image."""
        # Placeholder - would use actual image analysis
        return "unknown"

    def _extract_themes(self, content: list[dict]) -> list[str]:
        """Extract common themes from content."""
        # Analyze tags and detected elements for themes
        themes = []
        # Placeholder implementation
        return themes

    def _calculate_emotional_range(self, content: list[dict]) -> dict[str, Any]:
        """Calculate emotional range across content."""
        emotions = [c.get("emotion", "neutral") for c in content]
        return {
            "primary_emotion": max(set(emotions), key=emotions.count),
            "emotion_variety": len(set(emotions)),
        }

    def _get_beat_emotion(self, beat_name: str, structure: StoryStructure) -> str:
        """Get typical emotion for story beat."""
        emotion_map = {
            "setup": "curious",
            "exposition": "calm",
            "rising_action": "tense",
            "climax": "intense",
            "confrontation": "conflict",
            "resolution": "peaceful",
            "return": "satisfied",
        }
        return emotion_map.get(beat_name, "neutral")

    def _get_beat_pacing(self, beat_name: str, structure: StoryStructure) -> str:
        """Get typical pacing for story beat."""
        pacing_map = {
            "setup": "moderate",
            "exposition": "slow",
            "rising_action": "accelerating",
            "climax": "fast",
            "confrontation": "variable",
            "resolution": "slow",
            "twist": "sudden",
        }
        return pacing_map.get(beat_name, "moderate")

    def _get_beat_transitions(self, beat_name: str) -> str:
        """Get appropriate transition style for beat."""
        for category, beat_list in [
            ("setup", ["setup", "exposition", "ordinary_world", "ki_introduction"]),
            ("rising_tension", ["rising_action", "confrontation", "trials", "sho_development"]),
            ("climax", ["climax", "revelation", "ten_twist"]),
            ("resolution", ["resolution", "return", "ketsu_conclusion", "return_changed"]),
        ]:
            if beat_name in beat_list:
                return category
        return "gentle_cut"

    def _select_transition(self, style: str) -> str:
        """Select specific transition from style category."""
        if style in self.narrative_transitions:
            import random
            return random.choice(self.narrative_transitions[style])
        return "cut"

    def _get_transition_duration(self, pacing: str) -> float:
        """Get transition duration based on pacing."""
        duration_map = {
            "slow": 1.5,
            "moderate": 1.0,
            "fast": 0.5,
            "accelerating": 0.75,
            "variable": 1.0,
            "sudden": 0.25,
        }
        return duration_map.get(pacing, 1.0)

    def _select_beat_transition(self, from_beat: str, to_beat: str) -> str:
        """Select transition between story beats."""
        # Major transitions between acts
        major_transitions = {
            ("setup", "confrontation"): "impact_cut",
            ("confrontation", "resolution"): "slow_fade",
            ("rising_action", "climax"): "build_up",
            ("climax", "falling_action"): "release",
            ("ten_twist", "ketsu_conclusion"): "reveal",
        }

        key = (from_beat, to_beat)
        if key in major_transitions:
            return major_transitions[key]

        # Default to cross dissolve for beat changes
        return "cross_dissolve"

    def _get_pacing_multiplier(self, beat_name: str, pacing: str, position: float) -> float:
        """Get duration multiplier based on narrative position."""
        # Climax gets shorter shots
        if beat_name == "climax":
            return 0.8

        # Resolution gets longer shots
        if beat_name in ["resolution", "ketsu_conclusion"]:
            return 1.3

        # Accelerating pacing speeds up over time
        if pacing == "accelerating":
            return 1.0 - (position * 0.3)  # 30% faster by end

        return 1.0

    def _needs_voiceover_space(self, beat_name: str) -> bool:
        """Check if beat typically needs voiceover space."""
        voiceover_beats = ["setup", "exposition", "resolution", "return"]
        return beat_name in voiceover_beats

    def _analyze_pacing_profile(self, timeline: list[dict]) -> dict[str, Any]:
        """Analyze pacing characteristics."""
        durations = [clip["duration"] for clip in timeline]

        if not durations:
            return {}

        return {
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "variation": max(durations) - min(durations),
        }

    def _generate_markers(self, story_beats: dict, params: dict) -> list[dict]:
        """Generate timeline markers."""
        markers = []

        # Chapter markers for beats
        current_time = 0.0
        for beat in story_beats["beats"]:
            markers.append({
                "time": current_time,
                "type": "chapter",
                "name": beat["name"].replace("_", " ").title(),
                "color": self._get_beat_color(beat["name"]),
            })
            current_time += beat["duration"]

        # Emotion markers if requested
        if params.get("add_emotion_markers"):
            # Add emotion change markers
            pass

        # Voiceover markers if requested
        if params.get("add_voiceover_markers"):
            # Add voiceover space markers
            pass

        return markers

    def _get_beat_color(self, beat_name: str) -> str:
        """Get color for beat marker."""
        color_map = {
            "setup": "blue",
            "rising_action": "yellow",
            "climax": "red",
            "falling_action": "orange",
            "resolution": "green",
        }
        return color_map.get(beat_name, "gray")

    def _export_edl(self, timeline_data: dict) -> str:
        """Export timeline as EDL."""
        # Simplified EDL export
        edl_lines = ["TITLE: Story Arc Timeline", "FCM: NON-DROP FRAME", ""]

        # Add clips
        for i, clip in enumerate(timeline_data["clips"]):
            edl_lines.append(f"{i+1:03d}  001      V     C        ")
            edl_lines.append(f"* FROM CLIP NAME: {Path(clip['image']).name}")
            edl_lines.append(f"* BEAT: {clip['beat']}")
            edl_lines.append("")

        return "\n".join(edl_lines)

    def _export_xml(self, timeline_data: dict) -> str:
        """Export timeline as XML."""
        # Placeholder for XML export
        return "<timeline>...</timeline>"


class DocumentaryStoryTemplate(StoryArcTemplate):
    """Specialized story arc for documentary-style narratives.

    Focuses on:
    - Information delivery
    - Evidence presentation
    - Interview/testimony pacing
    - B-roll integration
    """

    def __init__(self):
        super().__init__()
        self.name = "DocumentaryStory"

        # Documentary-specific story beats
        self.story_beats[StoryStructure.THREE_ACT] = [
            ("introduction", 0.15),  # Brief intro
            ("exploration", 0.65),   # Main content
            ("conclusion", 0.20)     # Takeaways
        ]


class EmotionalJourneyTemplate(StoryArcTemplate):
    """Story arc focused on emotional progression.

    Maps images to emotional journey rather than plot points.
    """

    def __init__(self):
        super().__init__()
        self.name = "EmotionalJourney"

        # Emotion-based structure
        self.emotion_arc = [
            ("baseline", 0.15),
            ("disruption", 0.20),
            ("struggle", 0.25),
            ("breakthrough", 0.20),
            ("new_normal", 0.20)
        ]
