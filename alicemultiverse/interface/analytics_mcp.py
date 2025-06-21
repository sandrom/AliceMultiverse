"""MCP tools for performance analytics and improvements."""

from datetime import datetime, timedelta
from typing import Any

from ..analytics import ExportAnalytics, ExportMetrics, ImprovementEngine, PerformanceTracker
from ..analytics.export_analytics import ExportFormat
from ..core.structured_logging import get_logger

logger = get_logger(__name__)

# Global instances
_performance_tracker: PerformanceTracker | None = None
_export_analytics: ExportAnalytics | None = None
_improvement_engine: ImprovementEngine | None = None
_active_session_id: str | None = None


def get_performance_tracker() -> PerformanceTracker:
    """Get or create performance tracker instance."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker


def get_export_analytics() -> ExportAnalytics:
    """Get or create export analytics instance."""
    global _export_analytics
    if _export_analytics is None:
        _export_analytics = ExportAnalytics()
    return _export_analytics


def get_improvement_engine() -> ImprovementEngine:
    """Get or create improvement engine instance."""
    global _improvement_engine
    if _improvement_engine is None:
        _improvement_engine = ImprovementEngine(
            performance_tracker=get_performance_tracker(),
            export_analytics=get_export_analytics()
        )
    return _improvement_engine


async def start_analytics_session() -> dict[str, Any]:
    """Start a new analytics session.

    Begins tracking performance metrics for the current session.

    Returns:
        Session information
    """
    global _active_session_id

    try:
        tracker = get_performance_tracker()

        # Generate session ID
        # Use timestamp-based session ID for easy sorting/identification
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
        _active_session_id = session_id

        # Start session
        session = tracker.start_session(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "started_at": session.start_time.isoformat(),
            "message": "Analytics session started. All workflows will be tracked."
        }

    except Exception as e:
        logger.error(f"Failed to start analytics session: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def end_analytics_session() -> dict[str, Any]:
    """End the current analytics session.

    Stops tracking and provides session summary.

    Returns:
        Session summary and metrics
    """
    global _active_session_id

    try:
        tracker = get_performance_tracker()

        if not _active_session_id:
            return {
                "success": False,
                "error": "No active session"
            }

        # End session
        session = tracker.end_session()
        _active_session_id = None

        if not session:
            return {
                "success": False,
                "error": "Failed to end session"
            }

        duration = (session.end_time - session.start_time).total_seconds()

        return {
            "success": True,
            "session_id": session.session_id,
            "duration_seconds": duration,
            "metrics": {
                "workflows_completed": session.workflows_completed,
                "workflows_failed": session.workflows_failed,
                "total_exports": session.total_exports,
                "total_api_calls": session.total_api_calls,
                "popular_features": dict(sorted(
                    session.popular_features.items(),
                    key=lambda x: x[1],
                    reverse=True
                )),
                "common_errors": dict(sorted(
                    session.common_errors.items(),
                    key=lambda x: x[1],
                    reverse=True
                ))
            }
        }

    except Exception as e:
        logger.error(f"Failed to end analytics session: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def track_workflow_event(
    workflow_id: str,
    event_type: str,
    data: dict[str, Any]
) -> dict[str, Any]:
    """Track a workflow event.

    Records performance data for workflow analysis.

    Args:
        workflow_id: Workflow identifier
        event_type: Type of event (start, update, complete, fail)
        data: Event data

    Returns:
        Tracking result
    """
    try:
        tracker = get_performance_tracker()

        if event_type == "start":
            workflow_type = data.get("workflow_type", "unknown")
            metadata = data.get("metadata", {})

            metrics = tracker.start_workflow(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                metadata=metadata
            )

            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": "tracking_started"
            }

        elif event_type == "update":
            metrics = tracker.update_workflow(workflow_id, data)

            if not metrics:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }

            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": "updated"
            }

        elif event_type in ["complete", "fail"]:
            status = "completed" if event_type == "complete" else "failed"
            metrics = tracker.end_workflow(workflow_id, status)

            if not metrics:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }

            summary = tracker.get_workflow_summary(workflow_id)

            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": status,
                "summary": summary
            }

        else:
            return {
                "success": False,
                "error": f"Unknown event type: {event_type}"
            }

    except Exception as e:
        logger.error(f"Failed to track workflow event: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def track_export_event(
    export_id: str,
    timeline_id: str,
    format: str,
    platform: str | None = None,
    metrics: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Track an export operation.

    Records detailed export metrics for analysis.

    Args:
        export_id: Unique export identifier
        timeline_id: Associated timeline
        format: Export format (edl, xml, json, capcut)
        platform: Target platform if applicable
        metrics: Export metrics

    Returns:
        Tracking result
    """
    try:
        analytics = get_export_analytics()

        # Create export metrics
        export_metrics = ExportMetrics(
            export_id=export_id,
            timeline_id=timeline_id,
            format=ExportFormat(format.lower()),
            platform=platform
        )

        # Update with provided metrics
        if metrics:
            for key, value in metrics.items():
                if hasattr(export_metrics, key):
                    setattr(export_metrics, key, value)

        # Track export
        analytics.track_export(export_metrics)

        # Also track in workflow if active
        if _active_session_id:
            tracker = get_performance_tracker()
            active_workflows = list(tracker.active_workflows.keys())

            if active_workflows:
                # Track in most recent workflow
                workflow_id = active_workflows[-1]
                tracker.track_export(
                    workflow_id=workflow_id,
                    platform=platform or format,
                    success=export_metrics.successful,
                    duration=export_metrics.duration_seconds or 0,
                    metadata={"export_id": export_id}
                )

        return {
            "success": True,
            "export_id": export_id,
            "tracked": True
        }

    except Exception as e:
        logger.error(f"Failed to track export event: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_performance_insights(
    time_range_days: int | None = 30,
    workflow_type: str | None = None
) -> dict[str, Any]:
    """Get performance insights and statistics.

    Analyzes workflow performance over time.

    Args:
        time_range_days: Days to analyze (default 30)
        workflow_type: Filter by workflow type

    Returns:
        Performance insights and statistics
    """
    try:
        tracker = get_performance_tracker()

        # Get performance stats
        time_range = timedelta(days=time_range_days) if time_range_days else None
        stats = tracker.get_performance_stats(
            time_range=time_range,
            workflow_type=workflow_type
        )

        # Get improvement opportunities
        opportunities = tracker.get_improvement_opportunities()

        # Format response
        return {
            "success": True,
            "time_range_days": time_range_days,
            "workflow_type": workflow_type,
            "statistics": {
                "total_workflows": stats["total_workflows"],
                "success_rate": f"{stats['success_rate']:.1f}%",
                "average_duration_seconds": stats["average_duration"],
                "common_errors": stats["common_errors"],
                "popular_platforms": stats["popular_platforms"],
                "resource_usage": stats["resource_usage"]
            },
            "opportunities": [
                {
                    "area": opp["area"],
                    "issue": opp["issue"],
                    "suggestion": opp["suggestion"],
                    "impact": opp["impact"]
                }
                for opp in opportunities
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get performance insights: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_export_analytics(
    format: str | None = None,
    platform: str | None = None,
    time_range_days: int | None = 30
) -> dict[str, Any]:
    """Get export analytics and patterns.

    Analyzes export usage and success patterns.

    Args:
        format: Filter by export format
        platform: Filter by platform
        time_range_days: Days to analyze

    Returns:
        Export analytics and insights
    """
    try:
        analytics = get_export_analytics()

        # Get format statistics
        export_format = ExportFormat(format.lower()) if format else None
        time_range = timedelta(days=time_range_days) if time_range_days else None

        format_stats = analytics.get_format_statistics(
            format=export_format,
            time_range=time_range
        )

        # Get platform performance if specified
        platform_stats = None
        if platform:
            platform_stats = analytics.get_platform_performance(
                platform=platform,
                time_range=time_range
            )

        # Get workflow insights
        workflow_insights = analytics.get_workflow_insights()

        # Get quality trends
        quality_trends = analytics.get_quality_trends(time_range=time_range)

        return {
            "success": True,
            "filters": {
                "format": format,
                "platform": platform,
                "time_range_days": time_range_days
            },
            "format_statistics": format_stats,
            "platform_performance": platform_stats,
            "workflow_patterns": {
                "exports_per_timeline": workflow_insights["exports_per_timeline"],
                "format_preferences": workflow_insights["format_preferences"],
                "iteration_patterns": workflow_insights["iteration_patterns"]
            },
            "quality_trends": {
                "user_satisfaction": quality_trends["user_satisfaction"],
                "recent_resolutions": list(quality_trends["resolution_trends"].items())[-5:]
                if quality_trends is not None and quality_trends["resolution_trends"] else [],
                "complexity_trend": "increasing" if len(quality_trends["complexity_trends"]) > 1
                and list(quality_trends["complexity_trends"].values())[-1] >
                list(quality_trends["complexity_trends"].values())[0] else "stable"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get export analytics: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_improvement_suggestions(
    max_suggestions: int = 10
) -> dict[str, Any]:
    """Get improvement suggestions based on analytics.

    Analyzes usage patterns and suggests optimizations.

    Args:
        max_suggestions: Maximum suggestions to return

    Returns:
        Prioritized improvement suggestions
    """
    try:
        engine = get_improvement_engine()

        # Get all improvements
        improvements = engine.analyze_all()

        # Limit to max suggestions
        improvements = improvements[:max_suggestions]

        # Format response
        suggestions = []
        for imp in improvements:
            suggestions.append({
                "id": imp.id,
                "title": imp.title,
                "description": imp.description,
                "category": imp.category,
                "priority": imp.priority,
                "impact": imp.impact,
                "effort": imp.effort,
                "actions": imp.actions,
                "expected_improvement": imp.expected_improvement,
                "automation_possible": imp.automation_possible
            })

        # Get export-specific suggestions
        export_analytics = get_export_analytics()
        export_suggestions = export_analytics.suggest_improvements()

        # Merge suggestions
        for exp_sug in export_suggestions[:3]:  # Add top 3 export suggestions
            suggestions.append({
                "id": f"export_{exp_sug['category']}",
                "title": exp_sug["issue"],
                "description": exp_sug["suggestion"],
                "category": exp_sug["category"],
                "priority": exp_sug["priority"],
                "impact": "varies",
                "effort": "medium",
                "actions": [exp_sug["suggestion"]],
                "expected_improvement": {},
                "automation_possible": True
            })

        return {
            "success": True,
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
            "categories": {
                "workflow": len([s for s in suggestions if s is not None and s["category"] == "workflow"]),
                "performance": len([s for s in suggestions if s is not None and s["category"] == "performance"]),
                "quality": len([s for s in suggestions if s is not None and s["category"] == "quality"]),
                "efficiency": len([s for s in suggestions if s is not None and s["category"] == "efficiency"])
            }
        }

    except Exception as e:
        logger.error(f"Failed to get improvement suggestions: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def apply_improvement(
    improvement_id: str,
    parameters: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Apply an improvement suggestion.

    Implements the suggested improvement automatically where possible.

    Args:
        improvement_id: Improvement to apply
        parameters: Implementation parameters

    Returns:
        Application result
    """
    try:
        # This would implement actual improvements
        # For now, we'll return a placeholder

        return {
            "success": True,
            "improvement_id": improvement_id,
            "status": "manual_implementation_required",
            "message": "Review the suggested actions and implement manually",
            "documentation_url": f"/docs/improvements/{improvement_id}"
        }

    except Exception as e:
        logger.error(f"Failed to apply improvement: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Helper function for tracking user actions
async def track_user_action(
    action: str,
    metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Track a user action for analytics.

    Records user interactions for behavior analysis.

    Args:
        action: Action type (adjustment, preview, redo, etc.)
        metadata: Additional context

    Returns:
        Tracking result
    """
    try:
        tracker = get_performance_tracker()

        # Find active workflow
        if not tracker.active_workflows:
            return {
                "success": False,
                "error": "No active workflow to track action"
            }

        # Track in most recent workflow
        workflow_id = list(tracker.active_workflows.keys())[-1]

        tracker.track_user_action(
            workflow_id=workflow_id,
            action=action,
            metadata=metadata
        )

        return {
            "success": True,
            "action": action,
            "tracked_in": workflow_id
        }

    except Exception as e:
        logger.error(f"Failed to track user action: {e}")
        return {
            "success": False,
            "error": str(e)
        }