"""
Intelligent transition matching between scenes.
"""

import logging

import numpy as np

from .models import (
    MotionDirection,
    SceneCompatibility,
    TransitionRule,
    TransitionSuggestion,
    TransitionType,
)
from .motion_analyzer import MotionAnalyzer

logger = logging.getLogger(__name__)


class TransitionMatcher:
    """Matches scenes and suggests optimal transitions."""

    def __init__(self):
        self.analyzer = MotionAnalyzer()
        self.rules = self._initialize_rules()

    def analyze_sequence(self, image_paths: list[str]) -> list[TransitionSuggestion]:
        """
        Analyze a sequence of images and suggest transitions.

        Args:
            image_paths: List of image file paths in sequence order

        Returns:
            List of transition suggestions between consecutive images
        """
        if len(image_paths) < 2:
            return []

        # Analyze all images
        analyses = []
        for path in image_paths:
            analysis = self.analyzer.analyze_image(path)
            if analysis:
                analyses.append(analysis)
            else:
                logger.warning(f"Could not analyze image: {path}")
                analyses.append(None)

        # Generate transition suggestions
        suggestions = []
        for i in range(len(analyses) - 1):
            if analyses[i] and analyses[i+1]:
                suggestion = self.suggest_transition(
                    analyses[i],
                    analyses[i+1],
                    image_paths[i],
                    image_paths[i+1]
                )
                suggestions.append(suggestion)

        return suggestions

    def suggest_transition(
        self,
        source_analysis: dict,
        target_analysis: dict,
        source_path: str,
        target_path: str
    ) -> TransitionSuggestion:
        """
        Suggest optimal transition between two analyzed images.

        Args:
            source_analysis: Analysis data for source image
            target_analysis: Analysis data for target image
            source_path: Path to source image
            target_path: Path to target image

        Returns:
            Transition suggestion with type, duration, and effects
        """
        # Calculate compatibility
        compatibility = self._calculate_compatibility(source_analysis, target_analysis)

        # Apply rules to determine transition type
        transition_type = self._apply_rules(source_analysis, target_analysis, compatibility)

        # Calculate optimal duration
        duration = self._calculate_duration(transition_type, compatibility)

        # Generate effect parameters
        effects = self._generate_effects(
            transition_type,
            source_analysis,
            target_analysis
        )

        return TransitionSuggestion(
            source_image=source_path,
            target_image=target_path,
            transition_type=transition_type,
            duration=duration,
            effects=effects,
            compatibility=compatibility,
            confidence=compatibility.overall_score
        )

    def _calculate_compatibility(
        self,
        source: dict,
        target: dict
    ) -> SceneCompatibility:
        """Calculate compatibility between two scenes."""
        # Motion continuity
        motion_score = self._calculate_motion_continuity(
            source['motion'],
            target['motion']
        )

        # Color harmony
        color_score = self._calculate_color_harmony(
            source['colors'],
            target['colors']
        )

        # Composition match
        comp_score = self._calculate_composition_match(
            source['composition'],
            target['composition']
        )

        # Overall score (weighted average)
        overall = (motion_score * 0.4 + color_score * 0.3 + comp_score * 0.3)

        # Determine best transition type
        if motion_score > 0.8:
            suggested = TransitionType.MOMENTUM
        elif color_score > 0.8:
            suggested = TransitionType.DISSOLVE
        elif overall < 0.3:
            suggested = TransitionType.CUT
        else:
            suggested = TransitionType.FADE

        # Generate notes
        notes = []
        if motion_score > 0.7:
            notes.append("Strong motion continuity - consider momentum-preserving transition")
        if color_score < 0.3:
            notes.append("High color contrast - use quick transition")
        if comp_score > 0.8:
            notes.append("Similar composition - smooth dissolve recommended")

        return SceneCompatibility(
            overall_score=overall,
            motion_continuity=motion_score,
            color_harmony=color_score,
            composition_match=comp_score,
            suggested_transition=suggested,
            transition_duration=self._suggest_duration(overall),
            notes=notes
        )

    def _calculate_motion_continuity(self, source_motion: dict, target_motion: dict) -> float:
        """Calculate how well motion flows between scenes."""
        # Check if directions are compatible
        direction_map = {
            MotionDirection.LEFT_TO_RIGHT: [MotionDirection.LEFT_TO_RIGHT, MotionDirection.STATIC],
            MotionDirection.RIGHT_TO_LEFT: [MotionDirection.RIGHT_TO_LEFT, MotionDirection.STATIC],
            MotionDirection.UP_TO_DOWN: [MotionDirection.UP_TO_DOWN, MotionDirection.STATIC],
            MotionDirection.DOWN_TO_UP: [MotionDirection.DOWN_TO_UP, MotionDirection.STATIC],
            MotionDirection.STATIC: list(MotionDirection),
        }

        source_dir = source_motion.direction
        target_dir = target_motion.direction

        # Direction compatibility
        if target_dir in direction_map.get(source_dir, []):
            direction_score = 1.0
        elif source_dir == target_dir:
            direction_score = 0.9
        else:
            direction_score = 0.3

        # Speed compatibility
        speed_diff = abs(source_motion.speed - target_motion.speed)
        speed_score = 1.0 - speed_diff

        # Focal point distance
        focal_dist = np.linalg.norm(
            np.array(source_motion.focal_point) - np.array(target_motion.focal_point)
        )
        focal_score = 1.0 - min(focal_dist, 1.0)

        return (direction_score * 0.5 + speed_score * 0.3 + focal_score * 0.2)

    def _calculate_color_harmony(self, source_colors: dict, target_colors: dict) -> float:
        """Calculate color compatibility between scenes."""
        # Temperature match
        temp_match = 1.0 if source_colors['temperature'] == target_colors['temperature'] else 0.5

        # Brightness difference
        brightness_diff = abs(source_colors['brightness'] - target_colors['brightness'])
        brightness_score = 1.0 - (brightness_diff / 255.0)

        # Saturation similarity
        sat_diff = abs(source_colors['saturation'] - target_colors['saturation'])
        sat_score = 1.0 - (sat_diff / 255.0)

        return (temp_match * 0.4 + brightness_score * 0.3 + sat_score * 0.3)

    def _calculate_composition_match(self, source_comp: dict, target_comp: dict) -> float:
        """Calculate composition compatibility."""
        # Visual weight center distance
        weight_dist = np.linalg.norm(
            np.array(source_comp.visual_weight_center) -
            np.array(target_comp.visual_weight_center)
        )
        weight_score = 1.0 - min(weight_dist, 1.0)

        # Empty space overlap
        # Check if empty regions in source align with content in target
        empty_score = self._calculate_empty_space_compatibility(
            source_comp.empty_space_regions,
            target_comp.empty_space_regions
        )

        # Rule of thirds alignment
        roi_score = self._calculate_roi_alignment(
            source_comp.rule_of_thirds_points,
            target_comp.rule_of_thirds_points
        )

        return (weight_score * 0.4 + empty_score * 0.3 + roi_score * 0.3)

    def _initialize_rules(self) -> list[TransitionRule]:
        """Initialize transition rules."""
        return [
            # High motion continuity
            TransitionRule(
                name="momentum_preserve",
                condition={"motion_continuity": (0.8, 1.0)},
                transition_type=TransitionType.MOMENTUM,
                priority=10
            ),
            # Similar composition
            TransitionRule(
                name="smooth_dissolve",
                condition={
                    "composition_match": (0.7, 1.0),
                    "color_harmony": (0.6, 1.0)
                },
                transition_type=TransitionType.DISSOLVE,
                priority=8
            ),
            # High contrast
            TransitionRule(
                name="quick_cut",
                condition={"color_harmony": (0.0, 0.3)},
                transition_type=TransitionType.CUT,
                duration_multiplier=0.5,
                priority=7
            ),
            # Zoom detection
            TransitionRule(
                name="zoom_transition",
                condition={"motion_type": ["zoom_in", "zoom_out"]},
                transition_type=TransitionType.ZOOM,
                priority=9
            ),
        ]

    def _apply_rules(
        self,
        source: dict,
        target: dict,
        compatibility: SceneCompatibility
    ) -> TransitionType:
        """Apply rules to determine transition type."""
        # Check each rule
        applicable_rules = []

        for rule in self.rules:
            if self._check_rule_conditions(rule, source, target, compatibility):
                applicable_rules.append(rule)

        # Sort by priority and take highest
        if applicable_rules:
            best_rule = max(applicable_rules, key=lambda r: r.priority)
            return best_rule.transition_type

        # Default based on compatibility
        return compatibility.suggested_transition

    def _check_rule_conditions(
        self,
        rule: TransitionRule,
        source: dict,
        target: dict,
        compatibility: SceneCompatibility
    ) -> bool:
        """Check if rule conditions are met."""
        for key, value in rule.condition.items():
            if key == "motion_continuity":
                score = compatibility.motion_continuity
                if not (value[0] <= score <= value[1]):
                    return False
            elif key == "composition_match":
                score = compatibility.composition_match
                if not (value[0] <= score <= value[1]):
                    return False
            elif key == "color_harmony":
                score = compatibility.color_harmony
                if not (value[0] <= score <= value[1]):
                    return False
            elif key == "motion_type":
                if source['motion'].direction not in value and target['motion'].direction not in value:
                    return False

        return True

    def _calculate_duration(
        self,
        transition_type: TransitionType,
        compatibility: SceneCompatibility
    ) -> float:
        """Calculate optimal transition duration."""
        # Base durations
        base_durations = {
            TransitionType.CUT: 0.0,
            TransitionType.DISSOLVE: 1.0,
            TransitionType.FADE: 0.5,
            TransitionType.WIPE: 0.7,
            TransitionType.ZOOM: 0.8,
            TransitionType.MORPH: 1.2,
            TransitionType.GLITCH: 0.3,
            TransitionType.MOMENTUM: 0.6
        }

        base = base_durations.get(transition_type, 0.5)

        # Adjust based on compatibility
        if compatibility.overall_score > 0.8:
            # High compatibility = longer transition
            multiplier = 1.2
        elif compatibility.overall_score < 0.3:
            # Low compatibility = quicker transition
            multiplier = 0.7
        else:
            multiplier = 1.0

        return base * multiplier

    def _suggest_duration(self, score: float) -> float:
        """Suggest duration based on compatibility score."""
        # Higher compatibility = longer transition
        return 0.5 + (score * 1.0)  # 0.5s to 1.5s range

    def _generate_effects(
        self,
        transition_type: TransitionType,
        source: dict,
        target: dict
    ) -> dict[str, any]:
        """Generate effect parameters for the transition."""
        effects = {}

        if transition_type == TransitionType.MOMENTUM:
            # Calculate momentum vector
            effects['direction'] = source['motion'].direction
            effects['speed'] = source['motion'].speed
            effects['preserve_motion'] = True

        elif transition_type == TransitionType.ZOOM:
            # Determine zoom direction
            source_focal = source['motion'].focal_point
            target_focal = target['motion'].focal_point
            effects['zoom_from'] = source_focal
            effects['zoom_to'] = target_focal

        elif transition_type == TransitionType.MORPH:
            # Morph between similar regions
            effects['morph_points'] = self._find_morph_points(source, target)

        elif transition_type == TransitionType.GLITCH:
            # Glitch parameters
            effects['intensity'] = 0.8
            effects['block_size'] = 16
            effects['color_shift'] = True

        return effects

    def _calculate_empty_space_compatibility(
        self,
        source_empty: list,
        target_empty: list
    ) -> float:
        """Calculate how well empty spaces align."""
        if not source_empty or not target_empty:
            return 0.5  # Neutral if no empty regions

        # Check for overlap
        overlap_score = 0.0
        for s_region in source_empty:
            for t_region in target_empty:
                overlap = self._calculate_region_overlap(s_region, t_region)
                overlap_score = max(overlap_score, overlap)

        return overlap_score

    def _calculate_region_overlap(
        self,
        region1: tuple[float, float, float, float],
        region2: tuple[float, float, float, float]
    ) -> float:
        """Calculate overlap between two regions."""
        x1, y1, w1, h1 = region1
        x2, y2, w2, h2 = region2

        # Calculate intersection
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))

        intersection = x_overlap * y_overlap
        union = w1 * h1 + w2 * h2 - intersection

        return intersection / union if union > 0 else 0

    def _calculate_roi_alignment(
        self,
        source_points: list[tuple[float, float]],
        target_points: list[tuple[float, float]]
    ) -> float:
        """Calculate rule of thirds alignment score."""
        if not source_points or not target_points:
            return 0.5

        # Find closest points
        min_distances = []
        for sp in source_points:
            distances = [np.linalg.norm(np.array(sp) - np.array(tp)) for tp in target_points]
            if distances:
                min_distances.append(min(distances))

        if min_distances:
            avg_distance = np.mean(min_distances)
            # Convert distance to score (closer = higher score)
            return max(0, 1.0 - avg_distance)
        return 0.5

    def _find_morph_points(self, source: dict, target: dict) -> list[tuple]:
        """Find corresponding points for morphing."""
        # Use rule of thirds points and focal points
        morph_points = []

        # Add focal points
        morph_points.append((
            source['motion'].focal_point,
            target['motion'].focal_point
        ))

        # Add matched rule of thirds points
        source_roi = source['composition'].rule_of_thirds_points
        target_roi = target['composition'].rule_of_thirds_points

        for sp in source_roi[:4]:  # Limit to 4 points
            if target_roi:
                # Find closest target point
                distances = [(tp, np.linalg.norm(np.array(sp) - np.array(tp))) for tp in target_roi]
                closest = min(distances, key=lambda x: x[1])
                morph_points.append((sp, closest[0]))

        return morph_points

    async def analyze_sequence_with_morphing(self, image_paths: list[str]) -> list[TransitionSuggestion]:
        """
        Analyze a sequence with enhanced morphing detection.

        This method integrates subject morphing analysis with traditional
        transition analysis for more sophisticated transitions.

        Args:
            image_paths: List of image file paths in sequence order

        Returns:
            List of transition suggestions including morphing opportunities
        """
        # Get basic transition analysis
        suggestions = self.analyze_sequence(image_paths)

        # Import morphing components
        from .morphing import SubjectMorpher

        morpher = SubjectMorpher()

        # Enhance with morphing analysis
        for i, suggestion in enumerate(suggestions):
            if i < len(image_paths) - 1:
                try:
                    # Detect subjects in both images
                    source_subjects = await morpher.detect_subjects(suggestion.source_image)
                    target_subjects = await morpher.detect_subjects(suggestion.target_image)

                    if source_subjects and target_subjects:
                        # Check for morphing opportunities
                        matches = morpher.find_similar_subjects(source_subjects, target_subjects)

                        if matches:
                            # Create morph transition
                            morph_transition = morpher.create_morph_transition(
                                suggestion.source_image,
                                suggestion.target_image,
                                source_subjects,
                                target_subjects
                            )

                            if morph_transition:
                                # Update suggestion to use morphing
                                suggestion.transition_type = TransitionType.MORPH
                                suggestion.duration = morph_transition.duration
                                suggestion.effects = {
                                    "morph_data": morph_transition.to_dict(),
                                    "subject_count": len(morph_transition.subject_pairs),
                                    "morph_type": morph_transition.morph_type
                                }
                                # Boost confidence if good match
                                match_ratio = len(matches) / max(len(source_subjects), len(target_subjects))
                                suggestion.confidence = max(suggestion.confidence, match_ratio)

                except Exception as e:
                    logger.warning(f"Morphing analysis failed for transition {i}: {e}")

        return suggestions
