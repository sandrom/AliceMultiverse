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

    # TODO: Review unreachable code - async def _identify_broll_opportunities(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - timeline: dict[str, Any]
    # TODO: Review unreachable code - ) -> dict[int, SceneContext]:
    # TODO: Review unreachable code - """Identify where b-roll would enhance the timeline."""
    # TODO: Review unreachable code - opportunities = {}

    # TODO: Review unreachable code - for idx, clip in enumerate(timeline['clips']):
    # TODO: Review unreachable code - # Analyze clip content
    # TODO: Review unreachable code - scene_info = await self._analyze_clip_scene(clip)

    # TODO: Review unreachable code - # Determine if b-roll would help
    # TODO: Review unreachable code - context = SceneContext(
    # TODO: Review unreachable code - start_time=clip['start_time'],
    # TODO: Review unreachable code - end_time=clip['start_time'] + clip['duration'],
    # TODO: Review unreachable code - scene_type=scene_info.get('type', 'unknown'),
    # TODO: Review unreachable code - primary_subject=scene_info.get('subject'),
    # TODO: Review unreachable code - mood=scene_info.get('mood'),
    # TODO: Review unreachable code - location=scene_info.get('location'),
    # TODO: Review unreachable code - dialogue='dialogue' in scene_info.get('tags', []),
    # TODO: Review unreachable code - energy_level=self._assess_energy_level(scene_info),
    # TODO: Review unreachable code - needs_visual_interest=self._needs_broll(clip, scene_info, idx, timeline)
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if context.needs_visual_interest:
    # TODO: Review unreachable code - opportunities[idx] = context

    # TODO: Review unreachable code - return opportunities

    # TODO: Review unreachable code - async def _analyze_clip_scene(self, clip: dict[str, Any]) -> dict[str, Any]:
    # TODO: Review unreachable code - """Analyze a clip's scene content."""
    # TODO: Review unreachable code - # Get asset metadata by searching for the file path
    # TODO: Review unreachable code - results, _ = self.db.search(
    # TODO: Review unreachable code - filters={'file_path': clip['asset_path']},
    # TODO: Review unreachable code - limit=1
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if not results:
    # TODO: Review unreachable code - return {}

    # TODO: Review unreachable code - asset_info = results[0]

    # TODO: Review unreachable code - # Extract tag values from structured format
    # TODO: Review unreachable code - tag_values = self._extract_tag_values(asset_info.get('tags', {}))

    # TODO: Review unreachable code - # Use existing metadata
    # TODO: Review unreachable code - scene_info = {
    # TODO: Review unreachable code - 'type': asset_info.get('scene_type', 'unknown'),
    # TODO: Review unreachable code - 'tags': tag_values,
    # TODO: Review unreachable code - 'mood': self._extract_mood_from_tags(tag_values),
    # TODO: Review unreachable code - 'subject': self._extract_subject_from_tags(tag_values),
    # TODO: Review unreachable code - 'location': self._extract_location_from_tags(tag_values)
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - return scene_info

    # TODO: Review unreachable code - def _assess_energy_level(self, scene_info: dict[str, Any]) -> str:
    # TODO: Review unreachable code - """Assess the energy level of a scene."""
    # TODO: Review unreachable code - tags = scene_info.get('tags', [])

    # TODO: Review unreachable code - # High energy indicators
    # TODO: Review unreachable code - high_energy = ['action', 'dynamic', 'fast', 'intense', 'exciting']
    # TODO: Review unreachable code - if any(tag in tags for tag in high_energy):
    # TODO: Review unreachable code - return 'high'

    # TODO: Review unreachable code - # Low energy indicators
    # TODO: Review unreachable code - low_energy = ['calm', 'peaceful', 'slow', 'quiet', 'serene']
    # TODO: Review unreachable code - if any(tag in tags for tag in low_energy):
    # TODO: Review unreachable code - return 'low'

    # TODO: Review unreachable code - return 'medium'

    # TODO: Review unreachable code - def _needs_broll(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - clip: dict[str, Any],
    # TODO: Review unreachable code - scene_info: dict[str, Any],
    # TODO: Review unreachable code - clip_idx: int,
    # TODO: Review unreachable code - timeline: dict[str, Any]
    # TODO: Review unreachable code - ) -> bool:
    # TODO: Review unreachable code - """Determine if a clip would benefit from b-roll."""
    # TODO: Review unreachable code - # Long clips often need visual variety
    # TODO: Review unreachable code - if clip['duration'] > 5.0:
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - # Dialogue scenes benefit from cutaways
    # TODO: Review unreachable code - if 'dialogue' in scene_info.get('tags', []):
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - # Static shots need movement
    # TODO: Review unreachable code - if scene_info.get('type') in ['establishing', 'wide', 'static']:
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - # Check for repetitive sequences
    # TODO: Review unreachable code - if clip_idx > 0:
    # TODO: Review unreachable code - prev_clip = timeline['clips'][clip_idx - 1]
    # TODO: Review unreachable code - if prev_clip.get('asset_path') == clip['asset_path']:
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - async def _get_suggestions_for_context(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - context: SceneContext,
    # TODO: Review unreachable code - clip: dict[str, Any],
    # TODO: Review unreachable code - project_context: dict[str, Any] | None,
    # TODO: Review unreachable code - max_suggestions: int
    # TODO: Review unreachable code - ) -> list[BRollSuggestion]:
    # TODO: Review unreachable code - """Get b-roll suggestions for a specific context."""
    # TODO: Review unreachable code - suggestions = []

    # TODO: Review unreachable code - # 1. Contextual suggestions (matching subject/location)
    # TODO: Review unreachable code - if context.primary_subject:
    # TODO: Review unreachable code - contextual = await self._find_contextual_broll(
    # TODO: Review unreachable code - context.primary_subject,
    # TODO: Review unreachable code - context.location,
    # TODO: Review unreachable code - exclude_path=clip['asset_path']
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - suggestions.extend(contextual[:max_suggestions // 3])

    # TODO: Review unreachable code - # 2. Mood-based suggestions
    # TODO: Review unreachable code - if context.mood:
    # TODO: Review unreachable code - mood_based = await self._find_mood_matching_broll(
    # TODO: Review unreachable code - context.mood,
    # TODO: Review unreachable code - context.energy_level,
    # TODO: Review unreachable code - exclude_path=clip['asset_path']
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - suggestions.extend(mood_based[:max_suggestions // 3])

    # TODO: Review unreachable code - # 3. Visual similarity suggestions
    # TODO: Review unreachable code - if self.similarity_index and clip.get('content_hash'):
    # TODO: Review unreachable code - visual_similar = await self._find_visually_similar_broll(
    # TODO: Review unreachable code - clip['content_hash'],
    # TODO: Review unreachable code - exclude_path=clip['asset_path']
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - suggestions.extend(visual_similar[:max_suggestions // 3])

    # TODO: Review unreachable code - # 4. Transition helpers (for scene changes)
    # TODO: Review unreachable code - if context.scene_type in ['establishing', 'transition']:
    # TODO: Review unreachable code - transition_helpers = await self._find_transition_broll(
    # TODO: Review unreachable code - context.energy_level,
    # TODO: Review unreachable code - project_context
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - suggestions.extend(transition_helpers[:max_suggestions // 4])

    # TODO: Review unreachable code - # Sort by relevance and deduplicate
    # TODO: Review unreachable code - suggestions = self._rank_and_deduplicate(suggestions)

    # TODO: Review unreachable code - return suggestions[:max_suggestions]

    # TODO: Review unreachable code - async def _find_contextual_broll(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - subject: str,
    # TODO: Review unreachable code - location: str | None,
    # TODO: Review unreachable code - exclude_path: str
    # TODO: Review unreachable code - ) -> list[BRollSuggestion]:
    # TODO: Review unreachable code - """Find b-roll matching subject/location context."""
    # TODO: Review unreachable code - # Build search query
    # TODO: Review unreachable code - tags = [subject]
    # TODO: Review unreachable code - if location:
    # TODO: Review unreachable code - tags.append(location)

    # TODO: Review unreachable code - # Search for matching assets
    # TODO: Review unreachable code - results, _ = self.metadata_search.search_by_tags(
    # TODO: Review unreachable code - tags=tags,
    # TODO: Review unreachable code - limit=10
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Also search for assets marked as b-roll
    # TODO: Review unreachable code - broll_results, _ = self.metadata_search.search(
    # TODO: Review unreachable code - filters={'asset_role': 'b-roll'},
    # TODO: Review unreachable code - limit=10
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Combine results, preferring b-roll assets
    # TODO: Review unreachable code - all_results = []
    # TODO: Review unreachable code - seen_hashes = set()

    # TODO: Review unreachable code - # Add b-roll results first
    # TODO: Review unreachable code - for result in broll_results:
    # TODO: Review unreachable code - if result['content_hash'] not in seen_hashes:
    # TODO: Review unreachable code - all_results.append(result)
    # TODO: Review unreachable code - seen_hashes.add(result['content_hash'])

    # TODO: Review unreachable code - # Add tag-based results
    # TODO: Review unreachable code - for result in results:
    # TODO: Review unreachable code - if result['content_hash'] not in seen_hashes:
    # TODO: Review unreachable code - all_results.append(result)
    # TODO: Review unreachable code - seen_hashes.add(result['content_hash'])

    # TODO: Review unreachable code - results = all_results[:10]  # Limit to 10 total

    # TODO: Review unreachable code - suggestions = []
    # TODO: Review unreachable code - for result in results:
    # TODO: Review unreachable code - if result['file_path'] != exclude_path:
    # TODO: Review unreachable code - suggestions.append(BRollSuggestion(
    # TODO: Review unreachable code - asset_path=result['file_path'],
    # TODO: Review unreachable code - content_hash=result['content_hash'],
    # TODO: Review unreachable code - relevance_score=result.get('score', 0.8),
    # TODO: Review unreachable code - suggestion_type='contextual',
    # TODO: Review unreachable code - reasoning=f"Matches subject: {subject}" + (f" and location: {location}" if location else ""),
    # TODO: Review unreachable code - tags=self._extract_tag_values(result.get('tags', {})),
    # TODO: Review unreachable code - placement_hint='cutaway'
    # TODO: Review unreachable code - ))

    # TODO: Review unreachable code - return suggestions

    # TODO: Review unreachable code - async def _find_mood_matching_broll(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - mood: str,
    # TODO: Review unreachable code - energy_level: str,
    # TODO: Review unreachable code - exclude_path: str
    # TODO: Review unreachable code - ) -> list[BRollSuggestion]:
    # TODO: Review unreachable code - """Find b-roll matching mood and energy."""
    # TODO: Review unreachable code - # Search for mood-matching assets
    # TODO: Review unreachable code - mood_tags = [mood, f"{energy_level}_energy"]

    # TODO: Review unreachable code - results, _ = self.metadata_search.search_by_tags(
    # TODO: Review unreachable code - tags=mood_tags,
    # TODO: Review unreachable code - limit=10
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - suggestions = []
    # TODO: Review unreachable code - for result in results:
    # TODO: Review unreachable code - if result['file_path'] != exclude_path:
    # TODO: Review unreachable code - suggestions.append(BRollSuggestion(
    # TODO: Review unreachable code - asset_path=result['file_path'],
    # TODO: Review unreachable code - content_hash=result['content_hash'],
    # TODO: Review unreachable code - relevance_score=result.get('score', 0.7),
    # TODO: Review unreachable code - suggestion_type='mood',
    # TODO: Review unreachable code - reasoning=f"Matches {mood} mood with {energy_level} energy",
    # TODO: Review unreachable code - tags=self._extract_tag_values(result.get('tags', {})),
    # TODO: Review unreachable code - placement_hint='overlay'
    # TODO: Review unreachable code - ))

    # TODO: Review unreachable code - return suggestions

    # TODO: Review unreachable code - async def _find_visually_similar_broll(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - content_hash: str,
    # TODO: Review unreachable code - exclude_path: str
    # TODO: Review unreachable code - ) -> list[BRollSuggestion]:
    # TODO: Review unreachable code - """Find visually similar b-roll."""
    # TODO: Review unreachable code - if not self.similarity_index:
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - # Find similar images
    # TODO: Review unreachable code - similar = self.similarity_index.find_similar(
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - k=10,
    # TODO: Review unreachable code - threshold=0.7
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - suggestions = []
    # TODO: Review unreachable code - for sim_hash, score in similar:
    # TODO: Review unreachable code - asset = self.db.get_asset_by_hash(sim_hash)
    # TODO: Review unreachable code - if asset and asset['file_path'] != exclude_path:
    # TODO: Review unreachable code - suggestions.append(BRollSuggestion(
    # TODO: Review unreachable code - asset_path=asset['file_path'],
    # TODO: Review unreachable code - content_hash=sim_hash,
    # TODO: Review unreachable code - relevance_score=score,
    # TODO: Review unreachable code - suggestion_type='visual',
    # TODO: Review unreachable code - reasoning=f"Visually similar (score: {score:.2f})",
    # TODO: Review unreachable code - tags=asset.get('tags', []),
    # TODO: Review unreachable code - placement_hint='transition'
    # TODO: Review unreachable code - ))

    # TODO: Review unreachable code - return suggestions

    # TODO: Review unreachable code - async def _find_transition_broll(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - energy_level: str,
    # TODO: Review unreachable code - project_context: dict[str, Any] | None
    # TODO: Review unreachable code - ) -> list[BRollSuggestion]:
    # TODO: Review unreachable code - """Find b-roll suitable for transitions."""
    # TODO: Review unreachable code - # Look for abstract or neutral content
    # TODO: Review unreachable code - transition_tags = ['abstract', 'texture', 'pattern', 'nature', 'neutral']

    # TODO: Review unreachable code - # Match energy level
    # TODO: Review unreachable code - if energy_level == 'high':
    # TODO: Review unreachable code - transition_tags.extend(['motion', 'dynamic', 'flowing'])
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - transition_tags.extend(['static', 'calm', 'minimal'])

    # TODO: Review unreachable code - results, _ = self.metadata_search.search_by_tags(
    # TODO: Review unreachable code - tags=transition_tags,
    # TODO: Review unreachable code - limit=5
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - suggestions = []
    # TODO: Review unreachable code - for result in results:
    # TODO: Review unreachable code - suggestions.append(BRollSuggestion(
    # TODO: Review unreachable code - asset_path=result['file_path'],
    # TODO: Review unreachable code - content_hash=result['content_hash'],
    # TODO: Review unreachable code - relevance_score=0.6,
    # TODO: Review unreachable code - suggestion_type='transition',
    # TODO: Review unreachable code - reasoning=f"Good for {energy_level} energy transitions",
    # TODO: Review unreachable code - tags=result.get('tags', []),
    # TODO: Review unreachable code - duration_suggestion=1.0,  # Short duration for transitions
    # TODO: Review unreachable code - placement_hint='transition'
    # TODO: Review unreachable code - ))

    # TODO: Review unreachable code - return suggestions

    # TODO: Review unreachable code - def _rank_and_deduplicate(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - suggestions: list[BRollSuggestion]
    # TODO: Review unreachable code - ) -> list[BRollSuggestion]:
    # TODO: Review unreachable code - """Rank suggestions by relevance and remove duplicates."""
    # TODO: Review unreachable code - # Remove duplicates by content hash
    # TODO: Review unreachable code - seen = set()
    # TODO: Review unreachable code - unique = []

    # TODO: Review unreachable code - for suggestion in suggestions:
    # TODO: Review unreachable code - if suggestion.content_hash not in seen:
    # TODO: Review unreachable code - seen.add(suggestion.content_hash)
    # TODO: Review unreachable code - unique.append(suggestion)

    # TODO: Review unreachable code - # Sort by relevance score
    # TODO: Review unreachable code - unique.sort(key=lambda x: x.relevance_score, reverse=True)

    # TODO: Review unreachable code - return unique

    # TODO: Review unreachable code - def _extract_mood_from_tags(self, tags: list[str]) -> str | None:
    # TODO: Review unreachable code - """Extract mood from tags."""
    # TODO: Review unreachable code - mood_tags = [
    # TODO: Review unreachable code - 'happy', 'sad', 'energetic', 'calm', 'dramatic',
    # TODO: Review unreachable code - 'mysterious', 'romantic', 'tense', 'peaceful', 'exciting'
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - for tag in tags:
    # TODO: Review unreachable code - if tag.lower() in mood_tags:
    # TODO: Review unreachable code - return tag.lower()

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def _extract_subject_from_tags(self, tags: list[str]) -> str | None:
    # TODO: Review unreachable code - """Extract primary subject from tags."""
    # TODO: Review unreachable code - # Common subject indicators
    # TODO: Review unreachable code - subject_prefixes = ['person', 'people', 'animal', 'object', 'landscape']

    # TODO: Review unreachable code - for tag in tags:
    # TODO: Review unreachable code - for prefix in subject_prefixes:
    # TODO: Review unreachable code - if tag.lower().startswith(prefix):
    # TODO: Review unreachable code - return tag

    # TODO: Review unreachable code - # Return first noun-like tag
    # TODO: Review unreachable code - return tags[0] if tags else None

    # TODO: Review unreachable code - def _extract_tag_values(self, tags_dict: dict[str, list[dict[str, Any]]]) -> list[str]:
    # TODO: Review unreachable code - """Extract tag values from the structured tags dictionary."""
    # TODO: Review unreachable code - tag_values = []
    # TODO: Review unreachable code - for tag_type, tag_list in tags_dict.items():
    # TODO: Review unreachable code - for tag_info in tag_list:
    # TODO: Review unreachable code - if isinstance(tag_info, dict) and 'value' in tag_info:
    # TODO: Review unreachable code - tag_values.append(tag_info['value'])
    # TODO: Review unreachable code - elif isinstance(tag_info, str):
    # TODO: Review unreachable code - tag_values.append(tag_info)
    # TODO: Review unreachable code - return tag_values

    # TODO: Review unreachable code - def _extract_location_from_tags(self, tags: list[str]) -> str | None:
    # TODO: Review unreachable code - """Extract location from tags."""
    # TODO: Review unreachable code - location_indicators = [
    # TODO: Review unreachable code - 'indoor', 'outdoor', 'city', 'nature', 'beach',
    # TODO: Review unreachable code - 'mountain', 'forest', 'desert', 'urban', 'rural'
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - for tag in tags:
    # TODO: Review unreachable code - if tag.lower() in location_indicators:
    # TODO: Review unreachable code - return tag.lower()

    # TODO: Review unreachable code - return None


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

        # TODO: Review unreachable code - # Auto-insert b-roll
        # TODO: Review unreachable code - enhanced_timeline = self._insert_broll_clips(
        # TODO: Review unreachable code - timeline,
        # TODO: Review unreachable code - suggestions,
        # TODO: Review unreachable code - max_broll_percentage
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - return enhanced_timeline

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
