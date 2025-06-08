"""Improvement suggestion engine based on analytics."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass

from .performance_tracker import PerformanceTracker
from .export_analytics import ExportAnalytics
from ..core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class Improvement:
    """A suggested improvement."""
    id: str
    title: str
    description: str
    category: str  # workflow, performance, quality, efficiency
    priority: str  # high, medium, low
    impact: str  # time_saved, quality_improved, errors_reduced
    effort: str  # easy, medium, hard
    
    # Specific recommendations
    actions: List[str]
    metrics_before: Dict[str, Any]
    expected_improvement: Dict[str, Any]
    
    # Examples from data
    examples: List[Dict[str, Any]]
    
    # Implementation hints
    automation_possible: bool = False
    requires_user_input: bool = False
    affects_workflows: List[str] = None


class ImprovementEngine:
    """Generate actionable improvement suggestions."""
    
    def __init__(
        self,
        performance_tracker: Optional[PerformanceTracker] = None,
        export_analytics: Optional[ExportAnalytics] = None
    ):
        """Initialize improvement engine.
        
        Args:
            performance_tracker: Performance tracking instance
            export_analytics: Export analytics instance
        """
        self.performance = performance_tracker or PerformanceTracker()
        self.exports = export_analytics or ExportAnalytics()
        
        # Improvement templates
        self.improvement_templates = self._load_improvement_templates()
    
    def analyze_all(self) -> List[Improvement]:
        """Run all analysis and return improvements.
        
        Returns:
            List of suggested improvements
        """
        improvements = []
        
        # Analyze different aspects
        improvements.extend(self._analyze_workflow_efficiency())
        improvements.extend(self._analyze_export_patterns())
        improvements.extend(self._analyze_error_patterns())
        improvements.extend(self._analyze_user_behavior())
        improvements.extend(self._analyze_performance_bottlenecks())
        improvements.extend(self._analyze_quality_opportunities())
        
        # Sort by priority and impact
        improvements.sort(
            key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x.priority],
                {"time_saved": 0, "quality_improved": 1, "errors_reduced": 2}[x.impact]
            )
        )
        
        return improvements
    
    def _analyze_workflow_efficiency(self) -> List[Improvement]:
        """Analyze workflow efficiency patterns."""
        improvements = []
        
        # Get recent workflow stats
        stats = self.performance.get_performance_stats(time_range=timedelta(days=30))
        
        # Check for repetitive manual adjustments
        recent_workflows = [
            m for m in self.performance.historical_metrics[-50:]
            if m.get("manual_adjustments", 0) > 0
        ]
        
        if recent_workflows:
            # Find common adjustment patterns
            adjustment_patterns = defaultdict(int)
            for workflow in recent_workflows:
                metadata = workflow.get("metadata", {})
                for key, value in metadata.items():
                    if key.startswith("action_adjustment"):
                        adjustment_patterns[str(value)] += 1
            
            # If same adjustments appear frequently
            common_adjustments = [
                adj for adj, count in adjustment_patterns.items()
                if count > 5
            ]
            
            if common_adjustments:
                improvements.append(Improvement(
                    id="workflow_automation_001",
                    title="Automate Common Manual Adjustments",
                    description="Several manual adjustments are being repeated across workflows",
                    category="workflow",
                    priority="high",
                    impact="time_saved",
                    effort="medium",
                    actions=[
                        "Identify the most common manual adjustments",
                        "Create preset configurations for these adjustments",
                        "Add smart defaults based on content type",
                        "Implement one-click application of common settings"
                    ],
                    metrics_before={
                        "avg_adjustments_per_workflow": sum(
                            w.get("manual_adjustments", 0) for w in recent_workflows
                        ) / len(recent_workflows),
                        "time_per_adjustment": 30  # seconds estimate
                    },
                    expected_improvement={
                        "time_saved_per_workflow": "2-5 minutes",
                        "reduction_in_adjustments": "70%"
                    },
                    examples=common_adjustments[:3],
                    automation_possible=True,
                    affects_workflows=["video_creation", "timeline_export"]
                ))
        
        # Check for workflow abandonment
        abandoned_workflows = [
            m for m in self.performance.historical_metrics
            if m.get("status") == "failed" or (
                m.get("exports_created", 0) == 0 and m.get("status") == "completed"
            )
        ]
        
        abandonment_rate = len(abandoned_workflows) / len(self.performance.historical_metrics) * 100 if self.performance.historical_metrics else 0
        
        if abandonment_rate > 10:
            improvements.append(Improvement(
                id="workflow_completion_001",
                title="Reduce Workflow Abandonment",
                description=f"Workflow abandonment rate is {abandonment_rate:.1f}%",
                category="workflow",
                priority="medium",
                impact="errors_reduced",
                effort="medium",
                actions=[
                    "Add progress indicators for long operations",
                    "Implement auto-save for workflow state",
                    "Provide clearer error messages and recovery options",
                    "Add workflow resume capability"
                ],
                metrics_before={
                    "abandonment_rate": abandonment_rate,
                    "failed_workflows": len([w for w in abandoned_workflows if w.get("status") == "failed"])
                },
                expected_improvement={
                    "abandonment_reduction": "50%",
                    "user_satisfaction": "improved"
                },
                examples=[{
                    "workflow_type": w.get("workflow_type"),
                    "error": w.get("errors", ["Unknown"])[0] if w.get("errors") else "No export created"
                } for w in abandoned_workflows[:3]],
                requires_user_input=True,
                affects_workflows=["all"]
            ))
        
        return improvements
    
    def _analyze_export_patterns(self) -> List[Improvement]:
        """Analyze export usage patterns."""
        improvements = []
        
        # Get export insights
        insights = self.exports.get_workflow_insights()
        
        # Check iteration patterns
        if insights.get("exports_per_timeline", 0) > 3:
            improvements.append(Improvement(
                id="export_preview_001",
                title="Improve Export Preview Accuracy",
                description="Users are exporting multiple times per timeline",
                category="efficiency",
                priority="high",
                impact="time_saved",
                effort="medium",
                actions=[
                    "Enhance preview to show exact export output",
                    "Add platform-specific preview modes",
                    "Show potential issues before export",
                    "Implement 'confidence score' for exports"
                ],
                metrics_before={
                    "avg_exports_per_timeline": insights["exports_per_timeline"],
                    "time_per_export": 60  # seconds estimate
                },
                expected_improvement={
                    "export_reduction": "60%",
                    "time_saved": "3-5 minutes per project"
                },
                examples=[],
                automation_possible=True,
                affects_workflows=["timeline_export", "multi_version_export"]
            ))
        
        # Check format preferences
        format_prefs = insights.get("format_preferences", {})
        if format_prefs:
            top_format = list(format_prefs.keys())[0]
            
            improvements.append(Improvement(
                id="export_defaults_001",
                title=f"Optimize {top_format.upper()} Export Settings",
                description=f"{top_format} is your most used format",
                category="efficiency",
                priority="low",
                impact="time_saved",
                effort="easy",
                actions=[
                    f"Set {top_format} as default export format",
                    "Create quick export presets for common use cases",
                    "Optimize {top_format} export pipeline for speed",
                    "Add format-specific enhancements"
                ],
                metrics_before={
                    "format_usage": format_prefs,
                    "clicks_to_export": 3
                },
                expected_improvement={
                    "clicks_saved": 2,
                    "mental_overhead": "reduced"
                },
                examples=[],
                automation_possible=True,
                affects_workflows=["timeline_export"]
            ))
        
        # Check platform-specific issues
        for platform in ["instagram_reel", "tiktok", "youtube_shorts"]:
            platform_stats = self.exports.get_platform_performance(platform)
            
            if platform_stats["total_exports"] > 5:
                if platform_stats["compatibility_score"] < 0.8:
                    improvements.append(Improvement(
                        id=f"platform_optimization_{platform}",
                        title=f"Improve {platform.replace('_', ' ').title()} Compatibility",
                        description=f"Exports to {platform} have compatibility issues",
                        category="quality",
                        priority="medium",
                        impact="quality_improved",
                        effort="medium",
                        actions=[
                            f"Review {platform} platform requirements",
                            "Update default settings for better compatibility",
                            "Add automatic pre-flight checks",
                            "Implement platform-specific optimizations"
                        ],
                        metrics_before={
                            "compatibility_score": platform_stats["compatibility_score"],
                            "common_issues": platform_stats["common_optimizations"][:3]
                        },
                        expected_improvement={
                            "compatibility_increase": "95%+",
                            "manual_fixes_reduced": "80%"
                        },
                        examples=[],
                        automation_possible=True,
                        affects_workflows=["multi_version_export"]
                    ))
        
        return improvements
    
    def _analyze_error_patterns(self) -> List[Improvement]:
        """Analyze error patterns for improvements."""
        improvements = []
        
        # Get performance stats
        stats = self.performance.get_performance_stats(time_range=timedelta(days=30))
        
        # Check common errors
        common_errors = stats.get("common_errors", {})
        if common_errors:
            top_error = list(common_errors.keys())[0]
            error_count = common_errors[top_error]
            
            if error_count > 3:
                improvements.append(Improvement(
                    id="error_prevention_001",
                    title=f"Prevent '{top_error}' Errors",
                    description=f"This error occurred {error_count} times recently",
                    category="performance",
                    priority="high",
                    impact="errors_reduced",
                    effort="medium",
                    actions=[
                        "Add validation to prevent this error",
                        "Improve error recovery mechanisms",
                        "Provide clearer user guidance",
                        "Implement automatic retry with backoff"
                    ],
                    metrics_before={
                        "error_frequency": error_count,
                        "workflows_affected": error_count
                    },
                    expected_improvement={
                        "error_reduction": "90%",
                        "user_frustration": "eliminated"
                    },
                    examples=[{"error": top_error, "count": error_count}],
                    automation_possible=True,
                    affects_workflows=["all"]
                ))
        
        # Check API failures
        api_errors = [
            e for e, count in common_errors.items()
            if "API" in e or "api" in e
        ]
        
        if api_errors:
            improvements.append(Improvement(
                id="api_reliability_001",
                title="Improve API Error Handling",
                description="API errors are impacting workflows",
                category="performance",
                priority="medium",
                impact="errors_reduced",
                effort="medium",
                actions=[
                    "Implement exponential backoff for retries",
                    "Add fallback providers for critical operations",
                    "Cache API responses when possible",
                    "Provide offline mode for basic operations"
                ],
                metrics_before={
                    "api_errors": len(api_errors),
                    "affected_workflows": sum(common_errors[e] for e in api_errors)
                },
                expected_improvement={
                    "api_reliability": "99%+",
                    "user_experience": "seamless"
                },
                examples=api_errors[:3],
                automation_possible=True,
                affects_workflows=["video_creation", "style_analysis"]
            ))
        
        return improvements
    
    def _analyze_user_behavior(self) -> List[Improvement]:
        """Analyze user behavior patterns."""
        improvements = []
        
        # Check preview usage
        preview_workflows = [
            m for m in self.performance.historical_metrics
            if m.get("preview_views", 0) > 0
        ]
        
        if preview_workflows:
            avg_previews = sum(
                w.get("preview_views", 0) for w in preview_workflows
            ) / len(preview_workflows)
            
            if avg_previews > 5:
                improvements.append(Improvement(
                    id="preview_enhancement_001",
                    title="Enhance Preview System",
                    description="Users preview many times before committing",
                    category="efficiency",
                    priority="medium",
                    impact="time_saved",
                    effort="hard",
                    actions=[
                        "Add real-time preview updates",
                        "Implement side-by-side comparison views",
                        "Cache preview renders for faster viewing",
                        "Add preview quality settings"
                    ],
                    metrics_before={
                        "avg_previews_per_workflow": avg_previews,
                        "preview_time": 10  # seconds per preview
                    },
                    expected_improvement={
                        "preview_reduction": "50%",
                        "decision_confidence": "increased"
                    },
                    examples=[],
                    requires_user_input=True,
                    affects_workflows=["timeline_preview", "style_preview"]
                ))
        
        # Check redo patterns
        redo_workflows = [
            m for m in self.performance.historical_metrics
            if m.get("exports_redone", 0) > 0
        ]
        
        if len(redo_workflows) > len(self.performance.historical_metrics) * 0.2:
            improvements.append(Improvement(
                id="redo_reduction_001",
                title="Reduce Export Redos",
                description="Many exports are being redone",
                category="quality",
                priority="high",
                impact="time_saved",
                effort="medium",
                actions=[
                    "Add pre-export checklist",
                    "Implement export templates for common scenarios",
                    "Show common issues before export",
                    "Add 'confidence score' for export settings"
                ],
                metrics_before={
                    "redo_rate": len(redo_workflows) / len(self.performance.historical_metrics) * 100,
                    "time_wasted": len(redo_workflows) * 2  # minutes estimate
                },
                expected_improvement={
                    "redo_reduction": "70%",
                    "first_time_success": "increased"
                },
                examples=[],
                requires_user_input=True,
                affects_workflows=["timeline_export", "multi_version_export"]
            ))
        
        # Check time patterns
        export_patterns = self.exports.usage_patterns
        if export_patterns.get("hours"):
            peak_hours = sorted(
                export_patterns["hours"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            improvements.append(Improvement(
                id="performance_optimization_001",
                title="Optimize for Peak Usage Times",
                description=f"Most exports happen during {', '.join([h[0] + ':00' for h in peak_hours])}",
                category="performance",
                priority="low",
                impact="time_saved",
                effort="easy",
                actions=[
                    "Pre-warm caches before peak hours",
                    "Schedule maintenance during off-hours",
                    "Optimize resource allocation for peak times",
                    "Add queue priority for time-sensitive exports"
                ],
                metrics_before={
                    "peak_hours": peak_hours,
                    "peak_load": sum(h[1] for h in peak_hours)
                },
                expected_improvement={
                    "peak_performance": "20% faster",
                    "user_satisfaction": "improved"
                },
                examples=[],
                automation_possible=True,
                affects_workflows=["all"]
            ))
        
        return improvements
    
    def _analyze_performance_bottlenecks(self) -> List[Improvement]:
        """Analyze performance bottlenecks."""
        improvements = []
        
        # Check workflow durations
        recent_workflows = self.performance.historical_metrics[-50:]
        if recent_workflows:
            long_workflows = [
                w for w in recent_workflows
                if w.get("duration_seconds", 0) > 300  # 5 minutes
            ]
            
            if len(long_workflows) > len(recent_workflows) * 0.2:
                # Find common characteristics
                workflow_types = defaultdict(list)
                for w in long_workflows:
                    workflow_types[w.get("workflow_type", "unknown")].append(
                        w.get("duration_seconds", 0)
                    )
                
                slowest_type = max(
                    workflow_types.items(),
                    key=lambda x: sum(x[1]) / len(x[1])
                )[0]
                
                improvements.append(Improvement(
                    id="performance_workflow_001",
                    title=f"Optimize {slowest_type} Performance",
                    description=f"{slowest_type} workflows are taking too long",
                    category="performance",
                    priority="medium",
                    impact="time_saved",
                    effort="hard",
                    actions=[
                        "Profile the workflow to find bottlenecks",
                        "Implement parallel processing where possible",
                        "Add progress indicators for long operations",
                        "Consider background processing options"
                    ],
                    metrics_before={
                        "avg_duration": sum(workflow_types[slowest_type]) / len(workflow_types[slowest_type]),
                        "affected_workflows": len(workflow_types[slowest_type])
                    },
                    expected_improvement={
                        "speed_increase": "50%",
                        "user_experience": "more responsive"
                    },
                    examples=[],
                    automation_possible=True,
                    affects_workflows=[slowest_type]
                ))
        
        # Check memory usage
        memory_workflows = [
            w for w in recent_workflows
            if w.get("memory_mb", 0) > 1000  # 1GB
        ]
        
        if memory_workflows:
            improvements.append(Improvement(
                id="memory_optimization_001",
                title="Reduce Memory Usage",
                description="Some workflows use excessive memory",
                category="performance",
                priority="low",
                impact="errors_reduced",
                effort="medium",
                actions=[
                    "Implement streaming processing for large files",
                    "Add memory usage warnings",
                    "Optimize data structures",
                    "Implement garbage collection hints"
                ],
                metrics_before={
                    "high_memory_workflows": len(memory_workflows),
                    "peak_memory_mb": max(w.get("memory_mb", 0) for w in memory_workflows)
                },
                expected_improvement={
                    "memory_reduction": "40%",
                    "stability": "improved"
                },
                examples=[{
                    "workflow": w.get("workflow_type"),
                    "memory_mb": w.get("memory_mb")
                } for w in memory_workflows[:3]],
                automation_possible=True,
                affects_workflows=["video_processing", "batch_analysis"]
            ))
        
        return improvements
    
    def _analyze_quality_opportunities(self) -> List[Improvement]:
        """Analyze quality improvement opportunities."""
        improvements = []
        
        # Check export quality trends
        quality_trends = self.exports.get_quality_trends(time_range=timedelta(days=60))
        
        # Check if complexity is increasing but satisfaction isn't
        if quality_trends.get("complexity_trends") and quality_trends.get("user_satisfaction", 0) < 4:
            improvements.append(Improvement(
                id="quality_templates_001",
                title="Create Quality Templates",
                description="Complex exports could benefit from templates",
                category="quality",
                priority="medium",
                impact="quality_improved",
                effort="medium",
                actions=[
                    "Analyze successful complex exports",
                    "Create templates for common scenarios",
                    "Add quality presets (draft, final, master)",
                    "Implement smart suggestions based on content"
                ],
                metrics_before={
                    "user_satisfaction": quality_trends["user_satisfaction"],
                    "avg_complexity": sum(quality_trends["complexity_trends"].values()) / len(quality_trends["complexity_trends"])
                        if quality_trends["complexity_trends"] else 0
                },
                expected_improvement={
                    "satisfaction_increase": "4.5+ stars",
                    "setup_time_saved": "60%"
                },
                examples=[],
                requires_user_input=True,
                affects_workflows=["video_creation", "timeline_export"]
            ))
        
        # Check resolution trends
        if quality_trends.get("resolution_trends"):
            resolutions = list(quality_trends["resolution_trends"].values())
            if resolutions and resolutions[-1] < resolutions[0] * 0.8:
                improvements.append(Improvement(
                    id="quality_preservation_001",
                    title="Preserve Export Quality",
                    description="Export resolutions are decreasing over time",
                    category="quality",
                    priority="high",
                    impact="quality_improved",
                    effort="easy",
                    actions=[
                        "Review compression settings",
                        "Add quality warnings for low resolutions",
                        "Implement lossless intermediate formats",
                        "Educate about quality vs file size tradeoffs"
                    ],
                    metrics_before={
                        "resolution_decrease": f"{(1 - resolutions[-1] / resolutions[0]) * 100:.1f}%",
                        "current_avg_resolution": resolutions[-1]
                    },
                    expected_improvement={
                        "quality_preservation": "100%",
                        "user_awareness": "increased"
                    },
                    examples=[],
                    automation_possible=True,
                    affects_workflows=["timeline_export", "multi_version_export"]
                ))
        
        return improvements
    
    def _load_improvement_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load improvement templates."""
        return {
            "automation": {
                "description": "Automate repetitive tasks",
                "benefits": ["time_saved", "consistency"],
                "implementation": ["identify_patterns", "create_presets", "add_shortcuts"]
            },
            "optimization": {
                "description": "Improve performance",
                "benefits": ["speed", "resource_usage"],
                "implementation": ["profile", "parallelize", "cache"]
            },
            "quality": {
                "description": "Enhance output quality",
                "benefits": ["user_satisfaction", "professional_results"],
                "implementation": ["templates", "validation", "preview"]
            },
            "reliability": {
                "description": "Reduce errors and failures",
                "benefits": ["trust", "productivity"],
                "implementation": ["validation", "recovery", "monitoring"]
            }
        }