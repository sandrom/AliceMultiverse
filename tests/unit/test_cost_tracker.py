"""Tests for cost tracking functionality."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from alicemultiverse.core.cost_tracker import (
    CostTracker,
    CostCategory,
    ProviderPricing,
    CostEstimate,
    SpendingRecord,
    get_cost_tracker
)


class TestCostTracker:
    """Test the CostTracker class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cost_tracker(self, temp_dir):
        """Create a CostTracker instance with temp directory."""
        return CostTracker(data_dir=temp_dir)
    
    def test_initialization(self, cost_tracker, temp_dir):
        """Test CostTracker initialization."""
        assert cost_tracker.data_dir == temp_dir
        assert len(cost_tracker.pricing) > 0
        assert "openai" in cost_tracker.pricing
        assert "anthropic" in cost_tracker.pricing
        assert "runway" in cost_tracker.pricing
    
    def test_estimate_cost_understanding(self, cost_tracker):
        """Test cost estimation for understanding providers."""
        # Test token-based pricing
        estimate = cost_tracker.estimate_cost(
            provider="openai",
            operation="analyze",
            input_tokens=1000,
            output_tokens=500
        )
        
        assert isinstance(estimate, CostEstimate)
        assert estimate.provider == "openai"
        assert estimate.likely_cost > 0
        assert estimate.min_cost <= estimate.likely_cost <= estimate.max_cost
    
    def test_estimate_cost_generation(self, cost_tracker):
        """Test cost estimation for generation providers."""
        # Test per-request pricing
        estimate = cost_tracker.estimate_cost(
            provider="dall-e-3",
            operation="generate",
            count=5
        )
        
        assert estimate.provider == "dall-e-3"
        assert estimate.likely_cost == 0.04 * 5  # $0.04 per image
    
    def test_estimate_cost_video(self, cost_tracker):
        """Test cost estimation for video generation."""
        # Test per-second pricing
        estimate = cost_tracker.estimate_cost(
            provider="runway",
            operation="generate_video",
            duration=10
        )
        
        assert estimate.provider == "runway"
        assert estimate.likely_cost == 0.10 * 10  # $0.10 per second
    
    def test_record_cost(self, cost_tracker):
        """Test recording actual costs."""
        cost_tracker.record_cost(
            provider="openai",
            operation="analyze",
            cost=0.05,
            model="gpt-4o-mini",
            metadata={"images": 3}
        )
        
        # Check that cost was recorded
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in cost_tracker.spending_history
        assert len(cost_tracker.spending_history[today]) == 1
        
        record = cost_tracker.spending_history[today][0]
        assert record.provider == "openai"
        assert record.cost == 0.05
        assert record.model == "gpt-4o-mini"
    
    def test_get_total_cost(self, cost_tracker):
        """Test getting total cost for a date range."""
        now = datetime.now()
        
        # Record some costs
        cost_tracker.record_cost("openai", "analyze", 0.10)
        cost_tracker.record_cost("anthropic", "analyze", 0.20)
        cost_tracker.record_cost("runway", "generate", 0.50)
        
        # Get total for today
        total = cost_tracker.get_total_cost(
            now - timedelta(days=1),
            now + timedelta(days=1)
        )
        
        assert total == 0.80
    
    def test_get_cost_breakdown(self, cost_tracker):
        """Test getting cost breakdown by provider."""
        now = datetime.now()
        
        # Record costs from different providers
        cost_tracker.record_cost("openai", "analyze", 0.10)
        cost_tracker.record_cost("openai", "analyze", 0.05)
        cost_tracker.record_cost("anthropic", "analyze", 0.20)
        cost_tracker.record_cost("runway", "generate", 0.50)
        
        # Get breakdown by provider
        breakdown = cost_tracker.get_cost_breakdown(
            now - timedelta(days=1),
            now + timedelta(days=1),
            group_by="provider"
        )
        
        assert breakdown["openai"] == 0.15
        assert breakdown["anthropic"] == 0.20
        assert breakdown["runway"] == 0.50
    
    def test_budget_management(self, cost_tracker):
        """Test budget setting and checking."""
        # Set budgets
        cost_tracker.set_daily_limit(10.0)
        cost_tracker.set_monthly_limit(100.0)
        
        # Record some costs
        cost_tracker.record_cost("openai", "analyze", 5.0)
        
        # Check budget status
        status = cost_tracker.get_budget_status()
        
        assert status["daily_limit"] == 10.0
        assert status["monthly_limit"] == 100.0
        assert status["daily_used"] == 5.0
        assert status["monthly_used"] >= 5.0
    
    def test_budget_alerts(self, cost_tracker):
        """Test budget alert triggering."""
        # Set low budget
        cost_tracker.set_budget("daily", 1.0, alert_threshold=0.8)
        
        # Record cost that triggers alert
        cost_tracker.record_cost("openai", "analyze", 0.9)
        
        # Budget should be exceeded (90% of $1)
        assert cost_tracker.budgets["daily"] == 1.0
    
    def test_get_spending_summary(self, cost_tracker):
        """Test spending summary generation."""
        # Record various costs
        cost_tracker.record_cost("openai", "analyze", 0.10)
        cost_tracker.record_cost("anthropic", "analyze", 0.20)
        cost_tracker.record_cost("runway", "generate", 0.50)
        
        # Get summary
        summary = cost_tracker.get_spending_summary(days=30)
        
        assert "daily" in summary
        assert "weekly" in summary
        assert "monthly" in summary
        assert "providers" in summary
    
    def test_provider_comparison(self, cost_tracker):
        """Test provider comparison functionality."""
        comparison = cost_tracker.get_provider_comparison(
            category=CostCategory.UNDERSTANDING
        )
        
        # Should include understanding providers
        provider_names = [p["provider"] for p in comparison]
        assert "openai" in provider_names
        assert "anthropic" in provider_names
        assert "google" in provider_names
        
        # Should be sorted by cost
        costs = [p["cost_estimate"] for p in comparison if p["cost_estimate"] is not None]
        assert costs == sorted(costs)
    
    def test_free_tier_tracking(self, cost_tracker):
        """Test free tier usage tracking."""
        # Google has free tier
        remaining = cost_tracker._get_free_tier_remaining("google")
        assert remaining > 0
        
        # Use some free tier
        cost_tracker._increment_free_tier_usage("google")
        new_remaining = cost_tracker._get_free_tier_remaining("google")
        assert new_remaining == remaining - 1
    
    def test_format_cost_report(self, cost_tracker):
        """Test formatted cost report generation."""
        # Record some costs
        cost_tracker.record_cost("openai", "analyze", 0.10)
        cost_tracker.record_cost("runway", "generate", 0.50)
        
        # Generate report
        report = cost_tracker.format_cost_report()
        
        assert isinstance(report, str)
        assert "Cost Report" in report
        assert "openai" in report
        assert "runway" in report
    
    def test_estimate_batch_cost(self, cost_tracker):
        """Test batch cost estimation."""
        estimate = cost_tracker.estimate_batch_cost(
            file_count=100,
            providers=["openai", "anthropic"],
            operation="analyze"
        )
        
        assert "total_cost" in estimate
        assert "per_provider" in estimate
        assert len(estimate["per_provider"]) == 2
        assert estimate["cheapest_provider"] in ["openai", "anthropic"]
    
    def test_video_provider_pricing(self, cost_tracker):
        """Test that all video providers have pricing."""
        video_providers = ["runway", "pika", "luma", "minimax", "kling", "hedra", "veo3"]
        
        for provider in video_providers:
            assert provider in cost_tracker.pricing
            pricing = cost_tracker.pricing[provider]
            assert pricing.category == CostCategory.GENERATION
            assert pricing.per_second > 0 or pricing.per_request > 0


class TestGlobalCostTracker:
    """Test the global cost tracker instance."""
    
    def test_singleton_instance(self):
        """Test that get_cost_tracker returns the same instance."""
        tracker1 = get_cost_tracker()
        tracker2 = get_cost_tracker()
        
        assert tracker1 is tracker2
    
    def test_global_functions(self):
        """Test convenience functions."""
        from alicemultiverse.core.cost_tracker import estimate_cost, record_cost
        
        # Test estimate
        estimate = estimate_cost("openai", "analyze", input_tokens=1000)
        assert isinstance(estimate, CostEstimate)
        
        # Test record (doesn't return anything, just shouldn't error)
        record_cost("openai", "analyze", 0.05)