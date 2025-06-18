"""Automatic B-roll suggestion system for video projects."""

import logging
from dataclasses import dataclass
from typing import Any

from ..assets.deduplication.similarity_index import SimilarityIndex
from ..scene_detection.scene_detector import SceneDetector
from ..storage.unified_duckdb import UnifiedDuckDBStorage

logger = logging.getLogger(__name__)


@dataclass
class BRollSuggestion:
    """A single b-roll suggestion with context."""
    asset_path: str
    content_hash: str
    relevance_score: float
    suggestion_type: str  # 'contextual', 'visual', 'mood', 'transition'
    reasoning: str
    tags: list[str]
    duration_suggestion: float | None = None
    placement_hint: str | None = None  # 'cutaway', 'overlay', 'transition'


@dataclass
class SceneContext:
    """Context information for a scene needing b-roll."""
    start_time: float
    end_time: float
    scene_type: str
    primary_subject: str | None
    mood: str | None
    location: str | None
    dialogue: bool
    energy_level: str  # 'low', 'medium', 'high'
    needs_visual_interest: bool


class BRollSuggestionEngine:
    """Engine for suggesting relevant b-roll footage."""

    def __init__(
        self,
        db_path: str | None = None,
        similarity_index: SimilarityIndex | None = None,
        scene_detector: SceneDetector | None = None
    ):
        """
        Initialize b-roll suggestion engine.

        Args:
            db_path: Path to DuckDB database
            similarity_index: Pre-built similarity index
            scene_detector: Scene detection instance
        """
        self.db = UnifiedDuckDBStorage(db_path) if db_path else UnifiedDuckDBStorage()
        self.similarity_index = similarity_index
        self.scene_detector = scene_detector or SceneDetector()
        # Use DuckDB's search functionality directly
        self.metadata_search = self.db

    async def suggest_broll_for_timeline(
        self,
        timeline: dict[str, Any],
        project_context: dict[str, Any] | None = None,
        max_suggestions_per_scene: int = 5
    ) -> dict[str, list[BRollSuggestion]]:
        """
        Suggest b-roll for an entire timeline.

        Args:
            timeline: Timeline data with clips
            project_context: Project information (style, genre, etc.)
            max_suggestions_per_scene: Maximum suggestions per scene

        Returns:
            Dictionary mapping clip indices to b-roll suggestions
        """
        suggestions = {}

        # Analyze timeline for b-roll opportunities
        opportunities = await self._identify_broll_opportunities(timeline)

        for clip_idx, context in opportunities.items():
            clip = timeline['clips'][clip_idx]

            # Get suggestions for this specific context
            clip_suggestions = await self._get_suggestions_for_context(
                context,
                clip,
                project_context,
                max_suggestions_per_scene
            )

            if clip_suggestions:
                suggestions[str(clip_idx)] = clip_suggestions

        return suggestions

    async def _identify_broll_opportunities(
        self,
        timeline: dict[str, Any]
    ) -> dict[int, SceneContext]:
        """Identify where b-roll would enhance the timeline."""
        opportunities = {}

        for idx, clip in enumerate(timeline['clips']):
            # Analyze clip content
            scene_info = await self._analyze_clip_scene(clip)

            # Determine if b-roll would help
            context = SceneContext(
                start_time=clip['start_time'],
                end_time=clip['start_time'] + clip['duration'],
                scene_type=scene_info.get('type', 'unknown'),
                primary_subject=scene_info.get('subject'),
                mood=scene_info.get('mood'),
                location=scene_info.get('location'),
                dialogue='dialogue' in scene_info.get('tags', []),
                energy_level=self._assess_energy_level(scene_info),
                needs_visual_interest=self._needs_broll(clip, scene_info, idx, timeline)
            )

            if context.needs_visual_interest:
                opportunities[idx] = context

        return opportunities

    async def _analyze_clip_scene(self, clip: dict[str, Any]) -> dict[str, Any]:
        """Analyze a clip's scene content."""
        # Get asset metadata by searching for the file path
        results, _ = self.db.search(
            filters={'file_path': clip['asset_path']},
            limit=1
        )

        if not results:
            return {}

        asset_info = results[0]

        # Extract tag values from structured format
        tag_values = self._extract_tag_values(asset_info.get('tags', {}))

        # Use existing metadata
        scene_info = {
            'type': asset_info.get('scene_type', 'unknown'),
            'tags': tag_values,
            'mood': self._extract_mood_from_tags(tag_values),
            'subject': self._extract_subject_from_tags(tag_values),
            'location': self._extract_location_from_tags(tag_values)
        }

        return scene_info

    def _assess_energy_level(self, scene_info: dict[str, Any]) -> str:
        """Assess the energy level of a scene."""
        tags = scene_info.get('tags', [])

        # High energy indicators
        high_energy = ['action', 'dynamic', 'fast', 'intense', 'exciting']
        if any(tag in tags for tag in high_energy):
            return 'high'

        # Low energy indicators
        low_energy = ['calm', 'peaceful', 'slow', 'quiet', 'serene']
        if any(tag in tags for tag in low_energy):
            return 'low'

        return 'medium'

    def _needs_broll(
        self,
        clip: dict[str, Any],
        scene_info: dict[str, Any],
        clip_idx: int,
        timeline: dict[str, Any]
    ) -> bool:
        """Determine if a clip would benefit from b-roll."""
        # Long clips often need visual variety
        if clip['duration'] > 5.0:
            return True

        # Dialogue scenes benefit from cutaways
        if 'dialogue' in scene_info.get('tags', []):
            return True

        # Static shots need movement
        if scene_info.get('type') in ['establishing', 'wide', 'static']:
            return True

        # Check for repetitive sequences
        if clip_idx > 0:
            prev_clip = timeline['clips'][clip_idx - 1]
            if prev_clip.get('asset_path') == clip['asset_path']:
                return True

        return False

    async def _get_suggestions_for_context(
        self,
        context: SceneContext,
        clip: dict[str, Any],
        project_context: dict[str, Any] | None,
        max_suggestions: int
    ) -> list[BRollSuggestion]:
        """Get b-roll suggestions for a specific context."""
        suggestions = []

        # 1. Contextual suggestions (matching subject/location)
        if context.primary_subject:
            contextual = await self._find_contextual_broll(
                context.primary_subject,
                context.location,
                exclude_path=clip['asset_path']
            )
            suggestions.extend(contextual[:max_suggestions // 3])

        # 2. Mood-based suggestions
        if context.mood:
            mood_based = await self._find_mood_matching_broll(
                context.mood,
                context.energy_level,
                exclude_path=clip['asset_path']
            )
            suggestions.extend(mood_based[:max_suggestions // 3])

        # 3. Visual similarity suggestions
        if self.similarity_index and clip.get('content_hash'):
            visual_similar = await self._find_visually_similar_broll(
                clip['content_hash'],
                exclude_path=clip['asset_path']
            )
            suggestions.extend(visual_similar[:max_suggestions // 3])

        # 4. Transition helpers (for scene changes)
        if context.scene_type in ['establishing', 'transition']:
            transition_helpers = await self._find_transition_broll(
                context.energy_level,
                project_context
            )
            suggestions.extend(transition_helpers[:max_suggestions // 4])

        # Sort by relevance and deduplicate
        suggestions = self._rank_and_deduplicate(suggestions)

        return suggestions[:max_suggestions]

    async def _find_contextual_broll(
        self,
        subject: str,
        location: str | None,
        exclude_path: str
    ) -> list[BRollSuggestion]:
        """Find b-roll matching subject/location context."""
        # Build search query
        tags = [subject]
        if location:
            tags.append(location)

        # Search for matching assets
        results, _ = self.metadata_search.search_by_tags(
            tags=tags,
            limit=10
        )

        # Also search for assets marked as b-roll
        broll_results, _ = self.metadata_search.search(
            filters={'asset_role': 'b-roll'},
            limit=10
        )

        # Combine results, preferring b-roll assets
        all_results = []
        seen_hashes = set()

        # Add b-roll results first
        for result in broll_results:
            if result['content_hash'] not in seen_hashes:
                all_results.append(result)
                seen_hashes.add(result['content_hash'])

        # Add tag-based results
        for result in results:
            if result['content_hash'] not in seen_hashes:
                all_results.append(result)
                seen_hashes.add(result['content_hash'])

        results = all_results[:10]  # Limit to 10 total

        suggestions = []
        for result in results:
            if result['file_path'] != exclude_path:
                suggestions.append(BRollSuggestion(
                    asset_path=result['file_path'],
                    content_hash=result['content_hash'],
                    relevance_score=result.get('score', 0.8),
                    suggestion_type='contextual',
                    reasoning=f"Matches subject: {subject}" + (f" and location: {location}" if location else ""),
                    tags=self._extract_tag_values(result.get('tags', {})),
                    placement_hint='cutaway'
                ))

        return suggestions

    async def _find_mood_matching_broll(
        self,
        mood: str,
        energy_level: str,
        exclude_path: str
    ) -> list[BRollSuggestion]:
        """Find b-roll matching mood and energy."""
        # Search for mood-matching assets
        mood_tags = [mood, f"{energy_level}_energy"]

        results, _ = self.metadata_search.search_by_tags(
            tags=mood_tags,
            limit=10
        )

        suggestions = []
        for result in results:
            if result['file_path'] != exclude_path:
                suggestions.append(BRollSuggestion(
                    asset_path=result['file_path'],
                    content_hash=result['content_hash'],
                    relevance_score=result.get('score', 0.7),
                    suggestion_type='mood',
                    reasoning=f"Matches {mood} mood with {energy_level} energy",
                    tags=self._extract_tag_values(result.get('tags', {})),
                    placement_hint='overlay'
                ))

        return suggestions

    async def _find_visually_similar_broll(
        self,
        content_hash: str,
        exclude_path: str
    ) -> list[BRollSuggestion]:
        """Find visually similar b-roll."""
        if not self.similarity_index:
            return []

        # Find similar images
        similar = self.similarity_index.find_similar(
            content_hash,
            k=10,
            threshold=0.7
        )

        suggestions = []
        for sim_hash, score in similar:
            asset = self.db.get_asset_by_hash(sim_hash)
            if asset and asset['file_path'] != exclude_path:
                suggestions.append(BRollSuggestion(
                    asset_path=asset['file_path'],
                    content_hash=sim_hash,
                    relevance_score=score,
                    suggestion_type='visual',
                    reasoning=f"Visually similar (score: {score:.2f})",
                    tags=asset.get('tags', []),
                    placement_hint='transition'
                ))

        return suggestions

    async def _find_transition_broll(
        self,
        energy_level: str,
        project_context: dict[str, Any] | None
    ) -> list[BRollSuggestion]:
        """Find b-roll suitable for transitions."""
        # Look for abstract or neutral content
        transition_tags = ['abstract', 'texture', 'pattern', 'nature', 'neutral']

        # Match energy level
        if energy_level == 'high':
            transition_tags.extend(['motion', 'dynamic', 'flowing'])
        else:
            transition_tags.extend(['static', 'calm', 'minimal'])

        results, _ = self.metadata_search.search_by_tags(
            tags=transition_tags,
            limit=5
        )

        suggestions = []
        for result in results:
            suggestions.append(BRollSuggestion(
                asset_path=result['file_path'],
                content_hash=result['content_hash'],
                relevance_score=0.6,
                suggestion_type='transition',
                reasoning=f"Good for {energy_level} energy transitions",
                tags=result.get('tags', []),
                duration_suggestion=1.0,  # Short duration for transitions
                placement_hint='transition'
            ))

        return suggestions

    def _rank_and_deduplicate(
        self,
        suggestions: list[BRollSuggestion]
    ) -> list[BRollSuggestion]:
        """Rank suggestions by relevance and remove duplicates."""
        # Remove duplicates by content hash
        seen = set()
        unique = []

        for suggestion in suggestions:
            if suggestion.content_hash not in seen:
                seen.add(suggestion.content_hash)
                unique.append(suggestion)

        # Sort by relevance score
        unique.sort(key=lambda x: x.relevance_score, reverse=True)

        return unique

    def _extract_mood_from_tags(self, tags: list[str]) -> str | None:
        """Extract mood from tags."""
        mood_tags = [
            'happy', 'sad', 'energetic', 'calm', 'dramatic',
            'mysterious', 'romantic', 'tense', 'peaceful', 'exciting'
        ]

        for tag in tags:
            if tag.lower() in mood_tags:
                return tag.lower()

        return None

    def _extract_subject_from_tags(self, tags: list[str]) -> str | None:
        """Extract primary subject from tags."""
        # Common subject indicators
        subject_prefixes = ['person', 'people', 'animal', 'object', 'landscape']

        for tag in tags:
            for prefix in subject_prefixes:
                if tag.lower().startswith(prefix):
                    return tag

        # Return first noun-like tag
        return tags[0] if tags else None

    def _extract_tag_values(self, tags_dict: dict[str, list[dict[str, Any]]]) -> list[str]:
        """Extract tag values from the structured tags dictionary."""
        tag_values = []
        for tag_type, tag_list in tags_dict.items():
            for tag_info in tag_list:
                if isinstance(tag_info, dict) and 'value' in tag_info:
                    tag_values.append(tag_info['value'])
                elif isinstance(tag_info, str):
                    tag_values.append(tag_info)
        return tag_values

    def _extract_location_from_tags(self, tags: list[str]) -> str | None:
        """Extract location from tags."""
        location_indicators = [
            'indoor', 'outdoor', 'city', 'nature', 'beach',
            'mountain', 'forest', 'desert', 'urban', 'rural'
        ]

        for tag in tags:
            if tag.lower() in location_indicators:
                return tag.lower()

        return None


class BRollWorkflow:
    """High-level workflow for b-roll suggestions."""

    def __init__(self, suggestion_engine: BRollSuggestionEngine | None = None):
        """Initialize workflow."""
        self.engine = suggestion_engine or BRollSuggestionEngine()

    async def enhance_timeline_with_broll(
        self,
        timeline: dict[str, Any],
        auto_insert: bool = False,
        max_broll_percentage: float = 0.3
    ) -> dict[str, Any]:
        """
        Enhance a timeline with b-roll suggestions.

        Args:
            timeline: Original timeline
            auto_insert: Whether to automatically insert b-roll
            max_broll_percentage: Maximum percentage of timeline for b-roll

        Returns:
            Enhanced timeline with b-roll
        """
        # Get suggestions
        suggestions = await self.engine.suggest_broll_for_timeline(timeline)

        if not auto_insert:
            # Just return timeline with suggestions attached
            timeline['broll_suggestions'] = suggestions
            return timeline

        # Auto-insert b-roll
        enhanced_timeline = self._insert_broll_clips(
            timeline,
            suggestions,
            max_broll_percentage
        )

        return enhanced_timeline

    def _insert_broll_clips(
        self,
        timeline: dict[str, Any],
        suggestions: dict[str, list[BRollSuggestion]],
        max_percentage: float
    ) -> dict[str, Any]:
        """Insert b-roll clips into timeline."""
        # Calculate maximum b-roll duration
        total_duration = timeline.get('duration', 0)
        max_broll_duration = total_duration * max_percentage
        current_broll_duration = 0

        # Sort clips by time
        clips = sorted(timeline['clips'], key=lambda x: x['start_time'])
        new_clips = []

        for idx, clip in enumerate(clips):
            new_clips.append(clip)

            # Check if we have suggestions for this clip
            if str(idx) in suggestions and current_broll_duration < max_broll_duration:
                # Get best suggestion
                best_suggestion = suggestions[str(idx)][0]

                # Determine b-roll duration
                broll_duration = min(
                    best_suggestion.duration_suggestion or 2.0,
                    max_broll_duration - current_broll_duration
                )

                # Create b-roll clip
                broll_clip = {
                    'asset_path': best_suggestion.asset_path,
                    'start_time': clip['start_time'] + clip['duration'],
                    'duration': broll_duration,
                    'role': 'b-roll',
                    'transition_in': 'cut',
                    'transition_out': 'cut',
                    'metadata': {
                        'suggestion_type': best_suggestion.suggestion_type,
                        'reasoning': best_suggestion.reasoning
                    }
                }

                new_clips.append(broll_clip)
                current_broll_duration += broll_duration

        # Update timeline
        timeline['clips'] = new_clips
        timeline['has_broll'] = True
        timeline['broll_percentage'] = current_broll_duration / total_duration

        return timeline
