"""Tests for performance analytics functionality."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from alicemultiverse.analytics import (
    ExportAnalytics,
    ExportMetrics,
    ImprovementEngine,
    PerformanceTracker,
)
from alicemultiverse.analytics.export_analytics import ExportFormat


class TestPerformanceTracker:
    """Test performance tracking functionality."""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create tracker with temp directory."""
        with patch('alicemultiverse.analytics.performance_tracker.Path.home') as mock_home:
            mock_home.return_value = tmp_path
            tracker = PerformanceTracker()
            yield tracker

    def test_session_lifecycle(self, tracker):
        """Test session start and end."""
        # Start session
        session = tracker.start_session("test-session-123")
        assert session.session_id == "test-session-123"
        assert session.start_time is not None
        assert tracker.current_session == session

        # End session
        ended_session = tracker.end_session()
        assert ended_session is not None
        assert ended_session.end_time is not None
        assert ended_session.total_duration_seconds > 0
        assert tracker.current_session is None

    def test_workflow_tracking(self, tracker):
        """Test workflow lifecycle tracking."""
        # Start workflow
        metrics = tracker.start_workflow(
            workflow_id="wf-123",
            workflow_type="video_creation",
            metadata={"project": "test"}
        )

        assert metrics.workflow_id == "wf-123"
        assert metrics.workflow_type == "video_creation"
        assert metrics.status == "in_progress"
        assert "wf-123" in tracker.active_workflows

        # Update workflow
        updated = tracker.update_workflow(
            "wf-123",
            {
                "clips_processed": 5,
                "api_calls_made": 2,
                "platform_metrics": {"instagram": {"success": True}}
            }
        )

        assert updated.clips_processed == 5
        assert updated.api_calls_made == 2
        assert "instagram" in updated.platform_metrics

        # End workflow
        completed = tracker.end_workflow("wf-123", "completed")
        assert completed.status == "completed"
        assert completed.duration_seconds is not None
        assert "wf-123" not in tracker.active_workflows

    def test_export_tracking(self, tracker):
        """Test export operation tracking."""
        # Start workflow first
        tracker.start_workflow("wf-123", "video_export")

        # Track export
        tracker.track_export(
            workflow_id="wf-123",
            platform="instagram_reel",
            success=True,
            duration=5.2,
            metadata={"resolution": "1080x1920"}
        )

        metrics = tracker.active_workflows["wf-123"]
        assert metrics.exports_created == 1
        assert "instagram_reel" in metrics.platforms_exported
        assert metrics.platform_metrics["instagram_reel"]["success"] is True

    def test_api_tracking(self, tracker):
        """Test API call tracking."""
        tracker.start_workflow("wf-123", "generation")

        tracker.track_api_call(
            workflow_id="wf-123",
            provider="openai",
            success=True,
            duration=1.5,
            cost=0.05
        )

        metrics = tracker.active_workflows["wf-123"]
        assert metrics.api_calls_made == 1
        assert metrics.metadata["api_openai_calls"] == 1
        assert metrics.metadata["api_openai_cost"] == 0.05

    def test_user_action_tracking(self, tracker):
        """Test user action tracking."""
        tracker.start_workflow("wf-123", "timeline_edit")

        tracker.track_user_action(
            workflow_id="wf-123",
            action="adjustment",
            metadata={"type": "color_correction"}
        )

        metrics = tracker.active_workflows["wf-123"]
        assert metrics.manual_adjustments == 1

    def test_performance_stats(self, tracker):
        """Test aggregated performance statistics."""
        # Create some historical data
        now = datetime.now()
        for i in range(5):
            workflow = {
                "workflow_id": f"wf-{i}",
                "workflow_type": "video_creation",
                "start_time": (now - timedelta(days=i)).isoformat(),
                "end_time": (now - timedelta(days=i) + timedelta(hours=1)).isoformat(),
                "duration_seconds": 3600,
                "status": "completed" if i < 4 else "failed",
                "errors": ["Network error"] if i == 4 else [],
                "platforms_exported": ["instagram", "tiktok"] if i < 4 else []
            }
            tracker.historical_metrics.append(workflow)

        # Get stats
        stats = tracker.get_performance_stats(time_range=timedelta(days=7))

        assert stats["total_workflows"] == 5
        assert stats["success_rate"] == 80.0  # 4/5
        assert stats["average_duration"] == 3600
        assert "Network error" in stats["common_errors"]
        assert stats["popular_platforms"]["instagram"] == 4

    def test_improvement_opportunities(self, tracker):
        """Test improvement opportunity detection."""
        # Add workflows with high redo count
        for i in range(10):
            workflow = {
                "workflow_id": f"wf-{i}",
                "workflow_type": "timeline_export",
                "start_time": datetime.now().isoformat(),
                "status": "completed",
                "exports_redone": 2,
                "manual_adjustments": 5
            }
            tracker.historical_metrics.append(workflow)

        opportunities = tracker.get_improvement_opportunities()

        # Should detect high manual adjustments
        assert any(opp["area"] == "automation" for opp in opportunities)
        assert any(opp["area"] == "efficiency" for opp in opportunities)


class TestExportAnalytics:
    """Test export analytics functionality."""

    @pytest.fixture
    def analytics(self, tmp_path):
        """Create analytics with temp directory."""
        return ExportAnalytics(data_dir=tmp_path)

    def test_track_export(self, analytics):
        """Test export metric tracking."""
        metrics = ExportMetrics(
            export_id="exp-123",
            timeline_id="tl-456",
            format=ExportFormat.EDL,
            platform="instagram_reel",
            clip_count=10,
            total_duration=30.0,
            successful=True
        )

        analytics.track_export(metrics)

        assert len(analytics.export_history) == 1
        assert analytics.export_history[0]["export_id"] == "exp-123"
        assert analytics.usage_patterns["formats"]["edl"] == 1
        assert analytics.usage_patterns["platforms"]["instagram_reel"] == 1

    def test_format_statistics(self, analytics):
        """Test format-specific statistics."""
        # Add some exports
        for i, fmt in enumerate([ExportFormat.EDL, ExportFormat.EDL, ExportFormat.XML]):
            metrics = ExportMetrics(
                export_id=f"exp-{i}",
                timeline_id="tl-1",
                format=fmt,
                clip_count=10 + i,
                successful=True,
                duration_seconds=5.0
            )
            analytics.track_export(metrics)

        stats = analytics.get_format_statistics(format=ExportFormat.EDL)

        assert stats["total_exports"] == 2
        assert stats["success_rate"] == 100.0
        assert stats["average_clip_count"] == 10.5  # (10+11)/2

    def test_platform_performance(self, analytics):
        """Test platform-specific analysis."""
        # Add platform exports
        for i in range(5):
            metrics = ExportMetrics(
                export_id=f"exp-{i}",
                timeline_id=f"tl-{i}",
                format=ExportFormat.JSON,
                platform="tiktok",
                compatibility_score=0.9 if i < 3 else 0.6,
                edit_count=i,
                published=i < 3
            )
            analytics.track_export(metrics)

        perf = analytics.get_platform_performance("tiktok")

        assert perf["total_exports"] == 5
        assert perf["average_edit_count"] == 2.0  # (0+1+2+3+4)/5
        assert perf["adoption_rate"] == 60.0  # 3/5 published

    def test_workflow_insights(self, analytics):
        """Test workflow pattern analysis."""
        # Multiple exports per timeline
        for timeline in ["tl-1", "tl-2"]:
            for i in range(3):
                metrics = ExportMetrics(
                    export_id=f"{timeline}-exp-{i}",
                    timeline_id=timeline,
                    format=ExportFormat.XML,
                    start_time=datetime.now() + timedelta(minutes=i*10)
                )
                analytics.track_export(metrics)

        insights = analytics.get_workflow_insights()

        assert insights["total_timelines"] == 2
        assert insights["exports_per_timeline"] == 3.0
        assert "3 exports" in insights["iteration_patterns"]

    def test_quality_trends(self, analytics):
        """Test quality trend analysis."""
        # Add exports with varying quality
        base_time = datetime.now() - timedelta(days=30)

        for week in range(4):
            for day in range(7):
                timestamp = base_time + timedelta(weeks=week, days=day)

                metrics = ExportMetrics(
                    export_id=f"exp-w{week}-d{day}",
                    timeline_id="tl-1",
                    format=ExportFormat.EDL,
                    start_time=timestamp,
                    resolution=(1920, 1080) if week < 2 else (1280, 720),
                    total_duration=30.0 + week * 10,
                    clip_count=10 + week * 2,
                    user_rating=5 if week < 2 else 3
                )
                analytics.track_export(metrics)

        trends = analytics.get_quality_trends(time_range=timedelta(days=35))

        assert len(trends["resolution_trends"]) > 0
        assert len(trends["duration_trends"]) > 0
        assert trends["user_satisfaction"] == 4.0  # Average of 5 and 3

    def test_improvement_suggestions(self, analytics):
        """Test export improvement suggestions."""
        # Add exports with issues
        for i in range(10):
            metrics = ExportMetrics(
                export_id=f"exp-{i}",
                timeline_id=f"tl-{i//3}",  # Multiple per timeline
                format=ExportFormat.JSON,
                successful=i > 2,  # 30% failure rate
                edit_count=8 if i < 5 else 2,
                export_speed_mbps=5.0 if i < 3 else 50.0
            )
            analytics.track_export(metrics)

        suggestions = analytics.suggest_improvements()

        # Should suggest reliability improvements
        assert any(s["category"] == "reliability" for s in suggestions)
        # Should suggest efficiency improvements
        assert any(s["category"] == "efficiency" for s in suggestions)
        # Should suggest usability improvements
        assert any(s["category"] == "usability" for s in suggestions)


class TestImprovementEngine:
    """Test improvement suggestion engine."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create improvement engine with mocked dependencies."""
        with patch('alicemultiverse.analytics.performance_tracker.Path.home') as mock_home:
            mock_home.return_value = tmp_path
            performance = PerformanceTracker()
            exports = ExportAnalytics(data_dir=tmp_path)
            engine = ImprovementEngine(performance, exports)
            yield engine

    def test_analyze_all(self, engine):
        """Test comprehensive analysis."""
        # Add some data to analyze
        engine.performance.historical_metrics = [
            {
                "workflow_id": "wf-1",
                "workflow_type": "video_creation",
                "status": "completed",
                "manual_adjustments": 10,
                "duration_seconds": 300,
                "errors": []
            }
        ]

        improvements = engine.analyze_all()

        assert isinstance(improvements, list)
        # Should be sorted by priority
        if len(improvements) > 1:
            assert improvements[0].priority in ["high", "medium", "low"]

    def test_workflow_efficiency_analysis(self, engine):
        """Test workflow efficiency improvement detection."""
        # Add workflows with repetitive adjustments
        for i in range(10):
            engine.performance.historical_metrics.append({
                "workflow_id": f"wf-{i}",
                "workflow_type": "timeline_edit",
                "manual_adjustments": 5,
                "status": "completed",
                "metadata": {
                    "action_adjustment": {"type": "color_correction", "value": 0.5}
                }
            })

        improvements = engine._analyze_workflow_efficiency()

        assert len(improvements) > 0
        assert any(imp.category == "workflow" for imp in improvements)
        assert any("automate" in imp.title.lower() for imp in improvements)

    def test_export_pattern_analysis(self, engine):
        """Test export pattern improvement detection."""
        # Add export data
        for i in range(5):
            metrics = ExportMetrics(
                export_id=f"exp-{i}",
                timeline_id="tl-1",
                format=ExportFormat.EDL,
                start_time=datetime.now() + timedelta(minutes=i*10)
            )
            engine.exports.track_export(metrics)

        # Add workflow insights
        engine.exports.export_history = [
            {"timeline_id": "tl-1", "format": "edl"} for _ in range(5)
        ]

        improvements = engine._analyze_export_patterns()

        assert any(imp.category == "efficiency" for imp in improvements)

    def test_error_pattern_analysis(self, engine):
        """Test error pattern improvement detection."""
        # Add workflows with errors
        common_error = "API rate limit exceeded"
        for i in range(5):
            engine.performance.historical_metrics.append({
                "workflow_id": f"wf-{i}",
                "status": "failed",
                "errors": [common_error]
            })

        improvements = engine._analyze_error_patterns()

        assert len(improvements) > 0
        assert any(common_error in imp.title for imp in improvements)
        assert any(imp.priority == "high" for imp in improvements)

    def test_performance_bottleneck_analysis(self, engine):
        """Test performance bottleneck detection."""
        # Add slow workflows
        for i in range(10):
            engine.performance.historical_metrics.append({
                "workflow_id": f"wf-{i}",
                "workflow_type": "video_processing",
                "duration_seconds": 600,  # 10 minutes
                "memory_mb": 2000  # 2GB
            })

        improvements = engine._analyze_performance_bottlenecks()

        assert any(imp.category == "performance" for imp in improvements)
        assert any("memory" in imp.title.lower() for imp in improvements)


class TestAnalyticsMCPIntegration:
    """Test MCP tool integration for analytics."""

    @pytest.mark.asyncio
    async def test_start_session_mcp(self):
        """Test start analytics session MCP tool."""
        from alicemultiverse.interface.analytics_mcp import start_analytics_session

        result = await start_analytics_session()

        assert result["success"] is True
        assert "session_id" in result
        assert "started_at" in result

    @pytest.mark.asyncio
    async def test_end_session_mcp(self):
        """Test end analytics session MCP tool."""
        from alicemultiverse.interface.analytics_mcp import (
            end_analytics_session,
            start_analytics_session,
        )

        # Start session first
        start_result = await start_analytics_session()
        assert start_result["success"] is True

        # End session
        end_result = await end_analytics_session()

        assert end_result["success"] is True
        assert "metrics" in end_result
        assert "duration_seconds" in end_result

    @pytest.mark.asyncio
    async def test_performance_insights_mcp(self):
        """Test get performance insights MCP tool."""
        from alicemultiverse.interface.analytics_mcp import get_performance_insights

        result = await get_performance_insights(time_range_days=7)

        assert result["success"] is True
        assert "statistics" in result
        assert "opportunities" in result

    @pytest.mark.asyncio
    async def test_export_analytics_mcp(self):
        """Test get export analytics MCP tool."""
        from alicemultiverse.interface.analytics_mcp import get_export_analytics

        result = await get_export_analytics(
            format="edl",
            time_range_days=30
        )

        assert result["success"] is True
        assert "format_statistics" in result
        assert "workflow_patterns" in result
        assert "quality_trends" in result

    @pytest.mark.asyncio
    async def test_improvement_suggestions_mcp(self):
        """Test get improvement suggestions MCP tool."""
        from alicemultiverse.interface.analytics_mcp import get_improvement_suggestions

        result = await get_improvement_suggestions(max_suggestions=5)

        assert result["success"] is True
        assert "suggestions" in result
        assert "categories" in result
        assert len(result["suggestions"]) <= 5
