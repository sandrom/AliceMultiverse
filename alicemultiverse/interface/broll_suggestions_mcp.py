"""MCP tools for automatic b-roll suggestions."""

from typing import Dict, List, Optional, Any

from ..workflows.broll_suggestions import BRollSuggestionEngine, BRollWorkflow
from ..storage.unified_duckdb import UnifiedDuckDBStorage
from ..deduplication.similarity_index import SimilarityIndex
from ..core.structured_logging import get_logger

logger = get_logger(__name__)


async def suggest_broll_for_timeline(
    timeline_data: Dict[str, Any],
    project_context: Optional[Dict[str, Any]] = None,
    max_suggestions_per_scene: int = 5,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Suggest relevant b-roll footage for a video timeline.
    
    Analyzes the timeline to identify opportunities where b-roll would enhance
    the narrative, then suggests appropriate footage based on:
    - Scene context (subject, location, mood)
    - Visual similarity to main footage
    - Energy levels and pacing
    - Transition needs
    
    Args:
        timeline_data: Timeline with clips to analyze
        project_context: Optional project info (genre, style, etc.)
        max_suggestions_per_scene: Max b-roll suggestions per scene
        db_path: Optional database path
        
    Returns:
        Dictionary with b-roll suggestions mapped to clip indices
    """
    try:
        # Initialize engine
        engine = BRollSuggestionEngine(db_path=db_path)
        
        # Get suggestions
        suggestions = await engine.suggest_broll_for_timeline(
            timeline_data,
            project_context,
            max_suggestions_per_scene
        )
        
        # Format response
        result = {
            "timeline_duration": timeline_data.get("duration", 0),
            "clips_analyzed": len(timeline_data.get("clips", [])),
            "scenes_needing_broll": len(suggestions),
            "suggestions": {}
        }
        
        # Convert suggestions to simple format
        for clip_idx, broll_list in suggestions.items():
            result["suggestions"][clip_idx] = [
                {
                    "asset_path": s.asset_path,
                    "relevance_score": s.relevance_score,
                    "type": s.suggestion_type,
                    "reasoning": s.reasoning,
                    "placement": s.placement_hint,
                    "duration": s.duration_suggestion
                }
                for s in broll_list
            ]
            
        return result
        
    except Exception as e:
        logger.error(f"Error suggesting b-roll: {e}")
        return {
            "error": str(e),
            "suggestions": {}
        }


async def auto_insert_broll(
    timeline_data: Dict[str, Any],
    max_broll_percentage: float = 0.3,
    prefer_types: Optional[List[str]] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Automatically insert b-roll clips into a timeline.
    
    Enhances the timeline by intelligently placing b-roll footage to:
    - Break up long shots
    - Add visual interest during dialogue
    - Smooth transitions between scenes
    - Maintain viewer engagement
    
    Args:
        timeline_data: Original timeline to enhance
        max_broll_percentage: Max percentage of timeline for b-roll (0.0-1.0)
        prefer_types: Preferred b-roll types ['contextual', 'mood', 'visual']
        db_path: Optional database path
        
    Returns:
        Enhanced timeline with b-roll clips inserted
    """
    try:
        # Initialize workflow
        workflow = BRollWorkflow()
        
        # Enhance timeline
        enhanced = await workflow.enhance_timeline_with_broll(
            timeline_data,
            auto_insert=True,
            max_broll_percentage=max_broll_percentage
        )
        
        # Calculate statistics
        original_clips = len(timeline_data.get("clips", []))
        enhanced_clips = len(enhanced.get("clips", []))
        broll_added = enhanced_clips - original_clips
        
        return {
            "timeline": enhanced,
            "statistics": {
                "original_clips": original_clips,
                "enhanced_clips": enhanced_clips,
                "broll_clips_added": broll_added,
                "broll_percentage": enhanced.get("broll_percentage", 0),
                "total_duration": enhanced.get("duration", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error auto-inserting b-roll: {e}")
        return {
            "error": str(e),
            "timeline": timeline_data
        }


async def analyze_scene_for_broll(
    asset_path: str,
    start_time: float,
    duration: float,
    scene_metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a single scene to determine b-roll needs.
    
    Evaluates a specific scene/clip to determine:
    - Whether b-roll would enhance the scene
    - What type of b-roll would work best
    - Suggested placement and duration
    
    Args:
        asset_path: Path to the main footage
        start_time: Scene start time in timeline
        duration: Scene duration
        scene_metadata: Optional pre-analyzed scene data
        db_path: Optional database path
        
    Returns:
        Analysis with b-roll recommendations
    """
    try:
        engine = BRollSuggestionEngine(db_path=db_path)
        
        # Create temporary clip for analysis
        clip = {
            "asset_path": asset_path,
            "start_time": start_time,
            "duration": duration
        }
        
        # Analyze scene
        scene_info = await engine._analyze_clip_scene(clip)
        
        # Assess needs
        energy = engine._assess_energy_level(scene_info)
        needs_broll = duration > 5.0 or 'dialogue' in scene_info.get('tags', [])
        
        analysis = {
            "scene_type": scene_info.get('type', 'unknown'),
            "energy_level": energy,
            "mood": scene_info.get('mood'),
            "subject": scene_info.get('subject'),
            "needs_broll": needs_broll,
            "reasoning": []
        }
        
        # Add reasoning
        if duration > 5.0:
            analysis["reasoning"].append("Long duration benefits from visual variety")
        if 'dialogue' in scene_info.get('tags', []):
            analysis["reasoning"].append("Dialogue scenes benefit from cutaways")
        if scene_info.get('type') in ['establishing', 'wide']:
            analysis["reasoning"].append("Wide shots can use detail inserts")
            
        # Suggest b-roll types
        analysis["suggested_broll_types"] = []
        if analysis["subject"]:
            analysis["suggested_broll_types"].append("contextual")
        if analysis["mood"]:
            analysis["suggested_broll_types"].append("mood")
        analysis["suggested_broll_types"].append("visual")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing scene: {e}")
        return {
            "error": str(e),
            "needs_broll": False
        }


async def find_broll_by_criteria(
    subject: Optional[str] = None,
    mood: Optional[str] = None,
    energy_level: Optional[str] = None,
    location: Optional[str] = None,
    exclude_paths: Optional[List[str]] = None,
    limit: int = 20,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find b-roll footage matching specific criteria.
    
    Search for b-roll assets based on various criteria:
    - Subject matter (people, objects, nature, etc.)
    - Mood (happy, dramatic, peaceful, etc.)
    - Energy level (high, medium, low)
    - Location (indoor, outdoor, urban, etc.)
    
    Args:
        subject: Subject to match
        mood: Mood to match
        energy_level: Energy level (high/medium/low)
        location: Location type
        exclude_paths: Paths to exclude from results
        limit: Maximum results
        db_path: Optional database path
        
    Returns:
        List of matching b-roll assets with metadata
    """
    try:
        db = UnifiedDuckDBStorage(db_path) if db_path else UnifiedDuckDBStorage()
        
        # Build search tags
        tags = []
        if subject:
            tags.append(subject)
        if mood:
            tags.append(mood)
        if energy_level:
            tags.append(f"{energy_level}_energy")
        if location:
            tags.append(location)
            
        # Add b-roll indicator
        tags.append("b-roll")
        
        # Search
        results = db.search_assets(
            tags=tags,
            limit=limit * 2  # Get extra to filter
        )
        
        # Filter exclusions
        if exclude_paths:
            results = [r for r in results if r['file_path'] not in exclude_paths]
            
        # Format results
        formatted = []
        for result in results[:limit]:
            formatted.append({
                "asset_path": result['file_path'],
                "content_hash": result['content_hash'],
                "tags": result.get('tags', []),
                "score": result.get('score', 0),
                "metadata": {
                    "subject": result.get('subject'),
                    "mood": result.get('mood'),
                    "scene_type": result.get('scene_type')
                }
            })
            
        return {
            "count": len(formatted),
            "criteria": {
                "subject": subject,
                "mood": mood,
                "energy_level": energy_level,
                "location": location
            },
            "results": formatted
        }
        
    except Exception as e:
        logger.error(f"Error finding b-roll: {e}")
        return {
            "error": str(e),
            "results": []
        }


async def generate_broll_shot_list(
    timeline_data: Dict[str, Any],
    style: str = "documentary",
    include_descriptions: bool = True,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a b-roll shot list for a project.
    
    Creates a detailed shot list of recommended b-roll footage based on:
    - Timeline analysis
    - Project style (documentary, narrative, music video, etc.)
    - Scene requirements
    
    Args:
        timeline_data: Timeline to analyze
        style: Project style for b-roll recommendations
        include_descriptions: Include detailed shot descriptions
        db_path: Optional database path
        
    Returns:
        Structured b-roll shot list with timing and descriptions
    """
    try:
        engine = BRollSuggestionEngine(db_path=db_path)
        
        # Get suggestions
        suggestions = await engine.suggest_broll_for_timeline(
            timeline_data,
            project_context={"style": style}
        )
        
        # Create shot list
        shot_list = {
            "project_style": style,
            "timeline_duration": timeline_data.get("duration", 0),
            "shots": []
        }
        
        # Style-specific guidelines
        style_guidelines = {
            "documentary": {
                "cutaway_frequency": "high",
                "preferred_types": ["contextual", "mood"],
                "average_duration": 2.0
            },
            "narrative": {
                "cutaway_frequency": "medium",
                "preferred_types": ["visual", "mood"],
                "average_duration": 1.5
            },
            "music_video": {
                "cutaway_frequency": "very_high",
                "preferred_types": ["visual", "transition"],
                "average_duration": 0.5
            }
        }
        
        guidelines = style_guidelines.get(style, style_guidelines["documentary"])
        
        # Generate shot list entries
        for clip_idx, broll_suggestions in suggestions.items():
            clip = timeline_data["clips"][int(clip_idx)]
            
            for idx, suggestion in enumerate(broll_suggestions[:3]):  # Top 3
                shot = {
                    "shot_number": f"B{int(clip_idx)+1}.{idx+1}",
                    "timeline_position": clip["start_time"],
                    "suggested_duration": suggestion.duration_suggestion or guidelines["average_duration"],
                    "type": suggestion.suggestion_type,
                    "placement": suggestion.placement_hint
                }
                
                if include_descriptions:
                    shot["description"] = _generate_shot_description(
                        suggestion,
                        clip,
                        style
                    )
                    
                shot["source"] = {
                    "asset_path": suggestion.asset_path,
                    "tags": suggestion.tags
                }
                
                shot_list["shots"].append(shot)
                
        # Add summary
        shot_list["summary"] = {
            "total_shots": len(shot_list["shots"]),
            "estimated_broll_duration": sum(s["suggested_duration"] for s in shot_list["shots"]),
            "guidelines": guidelines
        }
        
        return shot_list
        
    except Exception as e:
        logger.error(f"Error generating shot list: {e}")
        return {
            "error": str(e),
            "shots": []
        }


def _generate_shot_description(suggestion, main_clip, style):
    """Generate a descriptive shot description."""
    descriptions = {
        "contextual": f"Insert shot of {', '.join(suggestion.tags[:3])} to provide context",
        "mood": f"Atmospheric shot conveying {suggestion.reasoning}",
        "visual": f"Visually matching cutaway with similar composition",
        "transition": f"Transitional element to bridge scenes"
    }
    
    base = descriptions.get(suggestion.suggestion_type, "B-roll insert")
    
    # Add style-specific notes
    if style == "documentary":
        base += " - hold for viewer comprehension"
    elif style == "music_video":
        base += " - quick cut on beat"
        
    return base


def register_broll_tools(server) -> None:
    """Register b-roll suggestion tools with MCP server.
    
    Args:
        server: MCP server instance
    """
    # Register each b-roll function as a tool
    server.tool()(suggest_broll_for_timeline)
    server.tool()(auto_insert_broll)
    server.tool()(analyze_scene_for_broll)
    server.tool()(find_broll_by_criteria)
    server.tool()(generate_broll_shot_list)


# Export all MCP tools
__all__ = [
    'suggest_broll_for_timeline',
    'auto_insert_broll',
    'analyze_scene_for_broll',
    'find_broll_by_criteria',
    'generate_broll_shot_list',
    'register_broll_tools'
]