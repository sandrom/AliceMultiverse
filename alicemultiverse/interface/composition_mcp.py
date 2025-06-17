"""MCP tools for visual composition and timeline flow analysis."""

from pathlib import Path
from typing import Any

from ..storage.unified_duckdb import DuckDBSearch
from ..workflows.composition import (
    CompositionAnalyzer,
    FlowAnalyzer,
    OptimizationStrategy,
    TimelineOptimizer,
)
from ..workflows.video_export import Timeline, TimelineClip


async def analyze_timeline_flow(
    timeline_data: dict[str, Any],
    target_mood: str | None = None,
    target_energy: str | None = None,
) -> dict[str, Any]:
    """Analyze timeline flow and detect issues.
    
    Args:
        timeline_data: Timeline data dictionary
        target_mood: Target mood (upbeat, dramatic, calm)
        target_energy: Target energy curve (rising_action, steady, etc.)
        
    Returns:
        Flow analysis with issues and suggestions
    """
    # Convert dictionary to Timeline object
    timeline = Timeline(
        name=timeline_data.get("name", "Timeline"),
        duration=timeline_data["duration"],
        frame_rate=timeline_data.get("frame_rate", 30),
        resolution=tuple(timeline_data.get("resolution", [1920, 1080])),
    )

    # Add clips
    for clip_data in timeline_data["clips"]:
        clip = TimelineClip(
            asset_path=Path(clip_data["path"]),
            start_time=clip_data["start_time"],
            duration=clip_data["duration"],
            transition_in=clip_data.get("transition_in"),
            transition_in_duration=clip_data.get("transition_in_duration", 0),
        )
        timeline.clips.append(clip)

    # Analyze flow
    analyzer = FlowAnalyzer()
    issues, suggestions = await analyzer.analyze_timeline_flow(
        timeline, target_mood, target_energy
    )

    # Generate report
    report = analyzer.generate_flow_report(issues, suggestions)

    # Format issues
    formatted_issues = []
    for issue in issues[:10]:  # Limit to top 10
        formatted_issues.append({
            "type": issue.issue_type.value,
            "severity": issue.severity,
            "time_range": [issue.start_time, issue.end_time],
            "affected_clips": issue.affected_clips,
            "description": issue.description,
        })

    # Format suggestions
    formatted_suggestions = []
    for suggestion in suggestions[:10]:  # Limit to top 10
        formatted_suggestions.append({
            "type": suggestion.suggestion_type.value,
            "priority": suggestion.priority,
            "target_clips": suggestion.target_clips,
            "description": suggestion.description,
            "expected_improvement": suggestion.expected_improvement,
        })

    return {
        "health_score": report["timeline_health_score"],
        "summary": report["summary"],
        "issues": formatted_issues,
        "suggestions": formatted_suggestions,
        "issue_breakdown": report["issues_by_type"],
    }


async def analyze_image_composition(
    image_path: str,
) -> dict[str, Any]:
    """Analyze visual composition of an image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Composition analysis with metrics and suggestions
    """
    analyzer = CompositionAnalyzer()

    # Analyze composition
    metrics = analyzer.analyze_image_composition(Path(image_path))

    # Get improvement suggestions
    suggestions = analyzer.suggest_composition_improvements(metrics)

    return {
        "metrics": {
            "rule_of_thirds": metrics.rule_of_thirds_score,
            "golden_ratio": metrics.golden_ratio_score,
            "symmetry": metrics.symmetry_score,
            "balance": metrics.balance_score,
            "leading_lines": metrics.leading_lines_score,
            "depth": metrics.depth_score,
            "focus_clarity": metrics.focus_clarity,
        },
        "composition_type": metrics.composition_type,
        "visual_weight": metrics.visual_weight_distribution,
        "interest_points": [
            {"x": p[0], "y": p[1]} for p in metrics.interest_points
        ],
        "suggestions": suggestions,
        "overall_score": (
            metrics.rule_of_thirds_score * 0.3 +
            metrics.balance_score * 0.3 +
            metrics.focus_clarity * 0.2 +
            metrics.leading_lines_score * 0.1 +
            metrics.depth_score * 0.1
        ),
    }


async def analyze_timeline_compositions(
    timeline_data: dict[str, Any],
    sample_rate: float = 0.2,
) -> dict[str, Any]:
    """Analyze composition of all clips in timeline.
    
    Args:
        timeline_data: Timeline data dictionary
        sample_rate: Fraction of clips to sample (0-1)
        
    Returns:
        Aggregated composition analysis
    """
    analyzer = CompositionAnalyzer()

    # Extract clip paths
    clip_paths = [Path(clip["path"]) for clip in timeline_data["clips"]]

    # Sample clips
    import random
    sample_size = max(1, int(len(clip_paths) * sample_rate))
    sampled_indices = sorted(random.sample(range(len(clip_paths)), sample_size))

    # Analyze sampled clips
    all_metrics = []
    composition_types = {}

    for idx in sampled_indices:
        path = clip_paths[idx]
        if path.suffix.lower() in [".jpg", ".png", ".webp"]:
            metrics = analyzer.analyze_image_composition(path)
            all_metrics.append(metrics)

            # Count composition types
            comp_type = metrics.composition_type
            composition_types[comp_type] = composition_types.get(comp_type, 0) + 1

    if not all_metrics:
        return {"error": "No valid images to analyze"}

    # Calculate averages
    avg_metrics = {
        "rule_of_thirds": sum(m.rule_of_thirds_score for m in all_metrics) / len(all_metrics),
        "golden_ratio": sum(m.golden_ratio_score for m in all_metrics) / len(all_metrics),
        "symmetry": sum(m.symmetry_score for m in all_metrics) / len(all_metrics),
        "balance": sum(m.balance_score for m in all_metrics) / len(all_metrics),
        "leading_lines": sum(m.leading_lines_score for m in all_metrics) / len(all_metrics),
        "depth": sum(m.depth_score for m in all_metrics) / len(all_metrics),
        "focus_clarity": sum(m.focus_clarity for m in all_metrics) / len(all_metrics),
    }

    # Find dominant composition type
    dominant_type = max(composition_types.items(), key=lambda x: x[1])[0] if composition_types else "unknown"

    return {
        "clips_analyzed": len(all_metrics),
        "total_clips": len(clip_paths),
        "average_metrics": avg_metrics,
        "composition_distribution": composition_types,
        "dominant_composition": dominant_type,
        "overall_quality": sum(avg_metrics.values()) / len(avg_metrics),
        "consistency_score": 1.0 - (len(composition_types) - 1) / max(1, len(all_metrics)),
    }


async def optimize_timeline(
    timeline_data: dict[str, Any],
    strategy: str = "balanced",
    preserve_clips: list[int] | None = None,
    target_duration: float | None = None,
) -> dict[str, Any]:
    """Optimize timeline based on flow analysis.
    
    Args:
        timeline_data: Timeline data dictionary
        strategy: Optimization strategy
        preserve_clips: Indices of clips to preserve
        target_duration: Target duration in seconds
        
    Returns:
        Optimized timeline with changes report
    """
    # Convert to Timeline object
    timeline = Timeline(
        name=timeline_data.get("name", "Timeline"),
        duration=timeline_data["duration"],
        frame_rate=timeline_data.get("frame_rate", 30),
        resolution=tuple(timeline_data.get("resolution", [1920, 1080])),
    )

    for clip_data in timeline_data["clips"]:
        clip = TimelineClip(
            asset_path=Path(clip_data["path"]),
            start_time=clip_data["start_time"],
            duration=clip_data["duration"],
            transition_in=clip_data.get("transition_in"),
            transition_in_duration=clip_data.get("transition_in_duration", 0),
        )
        timeline.clips.append(clip)

    # Optimize
    optimizer = TimelineOptimizer()
    result = await optimizer.optimize_timeline(
        timeline,
        strategy=OptimizationStrategy(strategy),
        preserve_clips=preserve_clips,
        target_duration=target_duration,
    )

    # Generate report
    report = optimizer.generate_optimization_report(result, timeline)

    # Format optimized timeline
    optimized_data = {
        "name": result.optimized_timeline.name,
        "duration": result.optimized_timeline.duration,
        "frame_rate": result.optimized_timeline.frame_rate,
        "resolution": list(result.optimized_timeline.resolution),
        "clips": []
    }

    for clip in result.optimized_timeline.clips:
        optimized_data["clips"].append({
            "path": str(clip.asset_path),
            "start_time": clip.start_time,
            "duration": clip.duration,
            "transition_in": clip.transition_in,
            "transition_in_duration": clip.transition_in_duration,
            "effects": clip.effects,
        })

    return {
        "optimized_timeline": optimized_data,
        "changes_made": result.changes_made,
        "improvement_score": result.improvement_score,
        "report": report,
        "warnings": result.warnings,
    }


async def suggest_clip_order(
    clip_paths: list[str],
    target_flow: str = "rising_action",
) -> dict[str, Any]:
    """Suggest optimal clip order based on composition analysis.
    
    Args:
        clip_paths: List of clip paths
        target_flow: Target energy flow pattern
        
    Returns:
        Suggested clip order with reasoning
    """
    FlowAnalyzer()
    comp_analyzer = CompositionAnalyzer()

    # Analyze all clips
    clip_analyses = []
    for i, path in enumerate(clip_paths):
        path_obj = Path(path)
        if path_obj.suffix.lower() in [".jpg", ".png", ".webp"]:
            # Get composition metrics
            comp_metrics = comp_analyzer.analyze_image_composition(path_obj)

            # Estimate energy based on composition
            energy = (
                comp_metrics.leading_lines_score * 0.3 +
                comp_metrics.focus_clarity * 0.3 +
                (1 - comp_metrics.symmetry_score) * 0.2 +  # Asymmetry = energy
                comp_metrics.depth_score * 0.2
            )

            clip_analyses.append({
                "index": i,
                "path": path,
                "energy": energy,
                "composition_type": comp_metrics.composition_type,
                "balance": comp_metrics.balance_score,
            })

    if not clip_analyses:
        return {"error": "No valid clips to analyze"}

    # Sort based on target flow
    if target_flow == "rising_action":
        # Sort by increasing energy
        sorted_clips = sorted(clip_analyses, key=lambda x: x["energy"])
    elif target_flow == "falling_action":
        # Sort by decreasing energy
        sorted_clips = sorted(clip_analyses, key=lambda x: x["energy"], reverse=True)
    elif target_flow == "climactic":
        # Build to climax (save highest energy for 80% through)
        sorted_by_energy = sorted(clip_analyses, key=lambda x: x["energy"])
        climax_clip = sorted_by_energy.pop()  # Highest energy

        # Place climax at 80% position
        climax_position = int(len(clip_analyses) * 0.8)
        sorted_clips = sorted_by_energy[:climax_position]
        sorted_clips.append(climax_clip)
        sorted_clips.extend(sorted_by_energy[climax_position:])
    else:
        # Default: balance energy distribution
        sorted_clips = sorted(clip_analyses, key=lambda x: x["balance"], reverse=True)

    # Generate reasoning
    reasoning = []
    for i, clip in enumerate(sorted_clips):
        if i == 0:
            reasoning.append(f"Start with {clip['composition_type']} composition for strong opening")
        elif i == len(sorted_clips) - 1:
            reasoning.append(f"End with {clip['composition_type']} for closure")
        elif clip["energy"] > 0.7:
            reasoning.append(f"High-energy clip placed at position {i+1} for impact")

    return {
        "suggested_order": [clip["index"] for clip in sorted_clips],
        "ordered_paths": [clip["path"] for clip in sorted_clips],
        "energy_curve": [clip["energy"] for clip in sorted_clips],
        "reasoning": reasoning,
        "target_flow": target_flow,
    }


async def detect_composition_patterns(
    project_name: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Detect composition patterns in a project or collection.
    
    Args:
        project_name: Optional project filter
        limit: Maximum images to analyze
        
    Returns:
        Composition patterns and insights
    """
    # Get images from database
    db = DuckDBSearch()

    # Build query
    conditions = []
    if project_name:
        conditions.append(f"project_name = '{project_name}'")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT file_path
        FROM media_files
        {where_clause}
        AND media_type = 'image'
        ORDER BY created_at DESC
        LIMIT {limit}
    """

    results = db.execute_query(query)
    if not results:
        return {"error": "No images found"}

    # Analyze compositions
    analyzer = CompositionAnalyzer()
    patterns = {
        "composition_types": {},
        "quality_distribution": {"high": 0, "medium": 0, "low": 0},
        "common_issues": {},
        "strengths": {},
    }

    for row in results:
        path = Path(row[0])
        if path.exists() and path.suffix.lower() in [".jpg", ".png", ".webp"]:
            metrics = analyzer.analyze_image_composition(path)

            # Track composition types
            comp_type = metrics.composition_type
            patterns["composition_types"][comp_type] = patterns["composition_types"].get(comp_type, 0) + 1

            # Calculate quality
            quality_score = (
                metrics.rule_of_thirds_score * 0.3 +
                metrics.balance_score * 0.3 +
                metrics.focus_clarity * 0.2 +
                metrics.leading_lines_score * 0.1 +
                metrics.depth_score * 0.1
            )

            if quality_score > 0.7:
                patterns["quality_distribution"]["high"] += 1
            elif quality_score > 0.4:
                patterns["quality_distribution"]["medium"] += 1
            else:
                patterns["quality_distribution"]["low"] += 1

            # Track issues
            if metrics.focus_clarity < 0.3:
                patterns["common_issues"]["poor_focus"] = patterns["common_issues"].get("poor_focus", 0) + 1
            if metrics.balance_score < 0.4:
                patterns["common_issues"]["unbalanced"] = patterns["common_issues"].get("unbalanced", 0) + 1

            # Track strengths
            if metrics.rule_of_thirds_score > 0.7:
                patterns["strengths"]["rule_of_thirds"] = patterns["strengths"].get("rule_of_thirds", 0) + 1
            if metrics.symmetry_score > 0.8:
                patterns["strengths"]["symmetry"] = patterns["strengths"].get("symmetry", 0) + 1

    # Calculate insights
    total_analyzed = sum(patterns["quality_distribution"].values())

    return {
        "images_analyzed": total_analyzed,
        "composition_patterns": patterns["composition_types"],
        "quality_distribution": patterns["quality_distribution"],
        "average_quality": (
            patterns["quality_distribution"]["high"] * 1.0 +
            patterns["quality_distribution"]["medium"] * 0.5 +
            patterns["quality_distribution"]["low"] * 0.0
        ) / max(1, total_analyzed),
        "common_issues": patterns["common_issues"],
        "strengths": patterns["strengths"],
        "recommendations": _generate_composition_recommendations(patterns),
    }


def _generate_composition_recommendations(patterns: dict[str, Any]) -> list[str]:
    """Generate recommendations based on patterns."""
    recommendations = []

    # Check quality distribution
    total = sum(patterns["quality_distribution"].values())
    if total > 0:
        high_quality_ratio = patterns["quality_distribution"]["high"] / total
        if high_quality_ratio < 0.3:
            recommendations.append("Focus on improving overall composition quality")

    # Check common issues
    if patterns["common_issues"].get("poor_focus", 0) > total * 0.3:
        recommendations.append("Many images have focus issues - check camera settings or AI model")

    if patterns["common_issues"].get("unbalanced", 0) > total * 0.3:
        recommendations.append("Work on visual balance - distribute elements more evenly")

    # Check composition variety
    comp_types = patterns["composition_types"]
    if comp_types and max(comp_types.values()) > total * 0.6:
        dominant = max(comp_types.items(), key=lambda x: x[1])[0]
        recommendations.append(f"Try varying composition beyond {dominant}")

    # Positive reinforcement
    if patterns["strengths"].get("rule_of_thirds", 0) > total * 0.4:
        recommendations.append("Good use of rule of thirds - keep it up!")

    return recommendations


# MCP tool definitions
COMPOSITION_TOOLS = [
    {
        "name": "analyze_timeline_flow",
        "description": "Analyze timeline flow and detect pacing/rhythm issues",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeline_data": {
                    "type": "object",
                    "description": "Timeline data with clips",
                    "required": ["duration", "clips"],
                },
                "target_mood": {
                    "type": "string",
                    "description": "Target mood (upbeat, dramatic, calm)",
                },
                "target_energy": {
                    "type": "string",
                    "description": "Target energy curve",
                    "enum": ["rising_action", "falling_action", "wave", "steady", "climactic"],
                },
            },
            "required": ["timeline_data"],
        },
    },
    {
        "name": "analyze_image_composition",
        "description": "Analyze visual composition of an image",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to image file",
                },
            },
            "required": ["image_path"],
        },
    },
    {
        "name": "analyze_timeline_compositions",
        "description": "Analyze composition of all clips in timeline",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeline_data": {
                    "type": "object",
                    "description": "Timeline data with clips",
                },
                "sample_rate": {
                    "type": "number",
                    "description": "Fraction of clips to sample",
                    "default": 0.2,
                },
            },
            "required": ["timeline_data"],
        },
    },
    {
        "name": "optimize_timeline",
        "description": "Optimize timeline based on flow analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeline_data": {
                    "type": "object",
                    "description": "Timeline data to optimize",
                },
                "strategy": {
                    "type": "string",
                    "description": "Optimization strategy",
                    "enum": ["minimal", "balanced", "aggressive", "preserve_intent", "energy_focused", "narrative_focused"],
                    "default": "balanced",
                },
                "preserve_clips": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Clip indices to preserve",
                },
                "target_duration": {
                    "type": "number",
                    "description": "Target duration in seconds",
                },
            },
            "required": ["timeline_data"],
        },
    },
    {
        "name": "suggest_clip_order",
        "description": "Suggest optimal clip order based on composition",
        "input_schema": {
            "type": "object",
            "properties": {
                "clip_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of clip paths",
                },
                "target_flow": {
                    "type": "string",
                    "description": "Target energy flow",
                    "enum": ["rising_action", "falling_action", "climactic", "balanced"],
                    "default": "rising_action",
                },
            },
            "required": ["clip_paths"],
        },
    },
    {
        "name": "detect_composition_patterns",
        "description": "Detect composition patterns in collection",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Optional project filter",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum images to analyze",
                    "default": 100,
                },
            },
        },
    },
]
