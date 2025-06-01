"""Tests for the Elo rating system."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from alicemultiverse.comparison import (
    EloRating, 
    ComparisonManager, 
    Asset, 
    Comparison, 
    ComparisonStrength,
    ModelRating
)


class TestEloRating:
    """Test the Elo rating algorithm."""
    
    def test_expected_score(self):
        """Test expected score calculation."""
        # Equal ratings should give 0.5
        assert EloRating.expected_score(1500, 1500) == 0.5
        
        # Higher rating should have higher expected score
        assert EloRating.expected_score(1600, 1400) > 0.5
        assert EloRating.expected_score(1400, 1600) < 0.5
        
        # 400 point difference should give ~0.91 expected score
        score = EloRating.expected_score(1900, 1500)
        assert 0.90 < score < 0.92
    
    def test_update_ratings_winner_a(self):
        """Test rating updates when A wins."""
        rating_a = 1500
        rating_b = 1500
        
        new_a, new_b = EloRating.update_ratings(
            rating_a, rating_b, "a", ComparisonStrength.CLEAR
        )
        
        # Winner should gain rating
        assert new_a > rating_a
        # Loser should lose rating
        assert new_b < rating_b
        # Total rating should be conserved
        assert (new_a + new_b) == (rating_a + rating_b)
    
    def test_update_ratings_winner_b(self):
        """Test rating updates when B wins."""
        rating_a = 1500
        rating_b = 1500
        
        new_a, new_b = EloRating.update_ratings(
            rating_a, rating_b, "b", ComparisonStrength.CLEAR
        )
        
        # Winner should gain rating
        assert new_b > rating_b
        # Loser should lose rating
        assert new_a < rating_a
        # Total rating should be conserved
        assert (new_a + new_b) == (rating_a + rating_b)
    
    def test_update_ratings_tie(self):
        """Test rating updates for a tie."""
        rating_a = 1600
        rating_b = 1400
        
        new_a, new_b = EloRating.update_ratings(
            rating_a, rating_b, "tie", ComparisonStrength.CLEAR
        )
        
        # Higher rated player should lose some rating in a tie
        assert new_a < rating_a
        # Lower rated player should gain some rating in a tie
        assert new_b > rating_b
        # Total rating should be conserved
        assert (new_a + new_b) == (rating_a + rating_b)
    
    def test_strength_affects_k_factor(self):
        """Test that comparison strength affects rating change magnitude."""
        rating_a = 1500
        rating_b = 1500
        
        # Test different strengths
        _, _ = EloRating.update_ratings(rating_a, rating_b, "a", ComparisonStrength.SLIGHT)
        slight_change = abs(1500 - _)
        
        _, _ = EloRating.update_ratings(rating_a, rating_b, "a", ComparisonStrength.DECISIVE)
        decisive_change = abs(1500 - _)
        
        # Decisive win should cause larger rating change
        assert decisive_change > slight_change
        assert decisive_change == slight_change * 8  # 128/16 = 8


class TestComparisonManager:
    """Test the comparison manager."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test.db"
        yield db_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_db):
        """Create a comparison manager with temporary database."""
        return ComparisonManager(db_path=temp_db)
    
    def test_add_asset(self, manager):
        """Test adding assets."""
        asset = Asset(
            id="test_1",
            path="test/image.png",
            model="test_model"
        )
        
        manager.add_asset(asset)
        
        # Should be able to get ratings for the model
        ratings = manager.get_ratings()
        assert len(ratings) == 1
        assert ratings[0].model == "test_model"
        assert ratings[0].rating == manager.DEFAULT_RATING
    
    def test_get_next_comparison_insufficient_assets(self, manager):
        """Test getting comparison with insufficient assets."""
        # Add only one asset
        asset = Asset(id="1", path="1.png", model="model1")
        manager.add_asset(asset)
        
        comparison = manager.get_next_comparison()
        assert comparison is None
    
    def test_get_next_comparison_single_model(self, manager):
        """Test getting comparison with single model."""
        # Add multiple assets from same model
        for i in range(3):
            asset = Asset(id=str(i), path=f"{i}.png", model="model1")
            manager.add_asset(asset)
        
        comparison = manager.get_next_comparison()
        assert comparison is None  # Need at least 2 different models
    
    def test_get_next_comparison_multiple_models(self, manager):
        """Test getting comparison with multiple models."""
        # Add assets from different models
        models = ["model1", "model2", "model3"]
        for model in models:
            for i in range(2):
                asset = Asset(
                    id=f"{model}_{i}",
                    path=f"{model}_{i}.png",
                    model=model
                )
                manager.add_asset(asset)
        
        comparison = manager.get_next_comparison()
        assert comparison is not None
        assert comparison.asset_a.model != comparison.asset_b.model
    
    def test_record_comparison(self, manager):
        """Test recording a comparison result."""
        # Add assets
        asset_a = Asset(id="a1", path="a1.png", model="modelA")
        asset_b = Asset(id="b1", path="b1.png", model="modelB")
        manager.add_asset(asset_a)
        manager.add_asset(asset_b)
        
        # Create and record comparison
        comparison = Comparison(
            id="comp1",
            asset_a=asset_a,
            asset_b=asset_b,
            winner="a",
            strength=ComparisonStrength.CLEAR,
            timestamp=datetime.now()
        )
        
        manager.record_comparison(comparison)
        
        # Check ratings were updated
        ratings = manager.get_ratings()
        assert len(ratings) == 2
        
        # Model A should have higher rating after winning
        model_a_rating = next(r for r in ratings if r.model == "modelA")
        model_b_rating = next(r for r in ratings if r.model == "modelB")
        
        assert model_a_rating.rating > manager.DEFAULT_RATING
        assert model_b_rating.rating < manager.DEFAULT_RATING
        assert model_a_rating.win_count == 1
        assert model_b_rating.loss_count == 1
    
    def test_record_comparison_tie(self, manager):
        """Test recording a tie."""
        # Add assets with different initial ratings
        asset_a = Asset(id="a1", path="a1.png", model="modelA")
        asset_b = Asset(id="b1", path="b1.png", model="modelB")
        manager.add_asset(asset_a)
        manager.add_asset(asset_b)
        
        # Record a tie
        comparison = Comparison(
            id="comp1",
            asset_a=asset_a,
            asset_b=asset_b,
            winner="tie",
            strength=ComparisonStrength.CLEAR,
            timestamp=datetime.now()
        )
        
        manager.record_comparison(comparison)
        
        # Check tie counts
        ratings = manager.get_ratings()
        for rating in ratings:
            assert rating.tie_count == 1
            assert rating.win_count == 0
            assert rating.loss_count == 0
    
    def test_get_comparison_history(self, manager):
        """Test getting comparison history."""
        # Add assets and record some comparisons
        models = ["modelA", "modelB"]
        assets = {}
        
        for model in models:
            asset = Asset(id=f"{model}_1", path=f"{model}.png", model=model)
            manager.add_asset(asset)
            assets[model] = asset
        
        # Record multiple comparisons
        for i in range(5):
            comparison = Comparison(
                id=f"comp_{i}",
                asset_a=assets["modelA"],
                asset_b=assets["modelB"],
                winner="a" if i % 2 == 0 else "b",
                strength=ComparisonStrength.CLEAR,
                timestamp=datetime.now()
            )
            manager.record_comparison(comparison)
        
        # Get history
        history = manager.get_comparison_history(limit=3)
        assert len(history) == 3
        
        # Check history structure
        for item in history:
            assert "id" in item
            assert "model_a" in item
            assert "model_b" in item
            assert "winner" in item
            assert "strength" in item
            assert "timestamp" in item
    
    def test_rating_convergence(self, manager):
        """Test that ratings converge to expected values."""
        # Add two models where A is clearly better
        asset_a = Asset(id="a", path="a.png", model="strong_model")
        asset_b = Asset(id="b", path="b.png", model="weak_model")
        manager.add_asset(asset_a)
        manager.add_asset(asset_b)
        
        # Simulate many comparisons where A wins 80% of the time
        import random
        random.seed(42)  # For reproducibility
        
        for i in range(100):
            winner = "a" if random.random() < 0.8 else "b"
            comparison = Comparison(
                id=f"comp_{i}",
                asset_a=asset_a,
                asset_b=asset_b,
                winner=winner,
                strength=ComparisonStrength.CLEAR,
                timestamp=datetime.now()
            )
            manager.record_comparison(comparison)
        
        # Check final ratings
        ratings = manager.get_ratings()
        strong_rating = next(r for r in ratings if r.model == "strong_model")
        weak_rating = next(r for r in ratings if r.model == "weak_model")
        
        # Strong model should have significantly higher rating
        assert strong_rating.rating > weak_rating.rating
        assert strong_rating.rating > 1580  # Should be well above default
        assert weak_rating.rating < 1420   # Should be well below default
        
        # Win rates should be approximately correct
        assert 0.75 < strong_rating.win_rate < 0.85
        assert 0.15 < weak_rating.win_rate < 0.25