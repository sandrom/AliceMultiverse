"""Automatic B-roll suggestion system for video projects."""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ..core.structured_logging import get_logger
from ..scene_detection.scene_detector import SceneDetector
from ..metadata.search import AssetSearchEngine
from ..deduplication.similarity_index import SimilarityIndex
from ..understanding.analyzer import ImageAnalyzer
from ..storage.unified_duckdb import UnifiedDuckDBStorage

logger = get_logger(__name__)


@dataclass
class BRollSuggestion:
    """A single b-roll suggestion with context."""
    asset_path: str
    content_hash: str
    relevance_score: float
    suggestion_type: str  # 'contextual', 'visual', 'mood', 'transition'
    reasoning: str
    tags: List[str]
    duration_suggestion: Optional[float] = None
    placement_hint: Optional[str] = None  # 'cutaway', 'overlay', 'transition'
    

@dataclass
class SceneContext:
    """Context information for a scene needing b-roll."""
    start_time: float
    end_time: float
    scene_type: str
    primary_subject: Optional[str]
    mood: Optional[str]
    location: Optional[str]
    dialogue: bool
    energy_level: str  # 'low', 'medium', 'high'
    needs_visual_interest: bool
    

class BRollSuggestionEngine:
    """Engine for suggesting relevant b-roll footage."""
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        similarity_index: Optional[SimilarityIndex] = None,
        scene_detector: Optional[SceneDetector] = None
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
        self.metadata_search = AssetSearchEngine(self.db)
        
    async def suggest_broll_for_timeline(
        self,
        timeline: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None,
        max_suggestions_per_scene: int = 5
    ) -> Dict[str, List[BRollSuggestion]]:
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
        timeline: Dict[str, Any]
    ) -> Dict[int, SceneContext]:
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
        
    async def _analyze_clip_scene(self, clip: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a clip's scene content."""
        # Get asset metadata
        asset_info = self.db.get_asset_by_path(clip['asset_path'])
        if not asset_info:
            return {}
            
        # Use existing metadata
        scene_info = {
            'type': asset_info.get('scene_type', 'unknown'),
            'tags': asset_info.get('tags', []),
            'mood': self._extract_mood_from_tags(asset_info.get('tags', [])),
            'subject': self._extract_subject_from_tags(asset_info.get('tags', [])),
            'location': self._extract_location_from_tags(asset_info.get('tags', []))
        }
        
        return scene_info
        
    def _assess_energy_level(self, scene_info: Dict[str, Any]) -> str:
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
        clip: Dict[str, Any],
        scene_info: Dict[str, Any],
        clip_idx: int,
        timeline: Dict[str, Any]
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
        clip: Dict[str, Any],
        project_context: Optional[Dict[str, Any]],
        max_suggestions: int
    ) -> List[BRollSuggestion]:
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
        location: Optional[str],
        exclude_path: str
    ) -> List[BRollSuggestion]:
        """Find b-roll matching subject/location context."""
        # Build search query
        tags = [subject]
        if location:
            tags.append(location)
            
        # Search for matching assets
        results = self.metadata_search.search_by_tags(
            tags=tags,
            limit=10,
            role='b-roll'  # Prefer assets marked as b-roll
        )
        
        suggestions = []
        for result in results:
            if result['file_path'] != exclude_path:
                suggestions.append(BRollSuggestion(
                    asset_path=result['file_path'],
                    content_hash=result['content_hash'],
                    relevance_score=result.get('score', 0.8),
                    suggestion_type='contextual',
                    reasoning=f"Matches subject: {subject}" + (f" and location: {location}" if location else ""),
                    tags=result.get('tags', []),
                    placement_hint='cutaway'
                ))
                
        return suggestions
        
    async def _find_mood_matching_broll(
        self,
        mood: str,
        energy_level: str,
        exclude_path: str
    ) -> List[BRollSuggestion]:
        """Find b-roll matching mood and energy."""
        # Search for mood-matching assets
        mood_tags = [mood, f"{energy_level}_energy"]
        
        results = self.metadata_search.search_by_tags(
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
                    tags=result.get('tags', []),
                    placement_hint='overlay'
                ))
                
        return suggestions
        
    async def _find_visually_similar_broll(
        self,
        content_hash: str,
        exclude_path: str
    ) -> List[BRollSuggestion]:
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
        project_context: Optional[Dict[str, Any]]
    ) -> List[BRollSuggestion]:
        """Find b-roll suitable for transitions."""
        # Look for abstract or neutral content
        transition_tags = ['abstract', 'texture', 'pattern', 'nature', 'neutral']
        
        # Match energy level
        if energy_level == 'high':
            transition_tags.extend(['motion', 'dynamic', 'flowing'])
        else:
            transition_tags.extend(['static', 'calm', 'minimal'])
            
        results = self.metadata_search.search_by_tags(
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
        suggestions: List[BRollSuggestion]
    ) -> List[BRollSuggestion]:
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
        
    def _extract_mood_from_tags(self, tags: List[str]) -> Optional[str]:
        """Extract mood from tags."""
        mood_tags = [
            'happy', 'sad', 'energetic', 'calm', 'dramatic',
            'mysterious', 'romantic', 'tense', 'peaceful', 'exciting'
        ]
        
        for tag in tags:
            if tag.lower() in mood_tags:
                return tag.lower()
                
        return None
        
    def _extract_subject_from_tags(self, tags: List[str]) -> Optional[str]:
        """Extract primary subject from tags."""
        # Common subject indicators
        subject_prefixes = ['person', 'people', 'animal', 'object', 'landscape']
        
        for tag in tags:
            for prefix in subject_prefixes:
                if tag.lower().startswith(prefix):
                    return tag
                    
        # Return first noun-like tag
        return tags[0] if tags else None
        
    def _extract_location_from_tags(self, tags: List[str]) -> Optional[str]:
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
    
    def __init__(self, suggestion_engine: Optional[BRollSuggestionEngine] = None):
        """Initialize workflow."""
        self.engine = suggestion_engine or BRollSuggestionEngine()
        
    async def enhance_timeline_with_broll(
        self,
        timeline: Dict[str, Any],
        auto_insert: bool = False,
        max_broll_percentage: float = 0.3
    ) -> Dict[str, Any]:
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
        timeline: Dict[str, Any],
        suggestions: Dict[str, List[BRollSuggestion]],
        max_percentage: float
    ) -> Dict[str, Any]:
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