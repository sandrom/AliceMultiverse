"""Comprehensive tests for the model comparison and rating system."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from alicemultiverse.comparison import (
    Asset,
    Comparison,
    ComparisonManager,
    ComparisonStrength,
    EloRating,
    ModelRating,
)
from alicemultiverse.comparison.web_server import app, pending_comparisons


class TestEloRatingExtended:
    """Extended tests for the Elo rating algorithm edge cases."""

    def test_extreme_rating_differences(self):
        """Test behavior with extreme rating differences."""
        # Test very large rating difference (1000 points)
        high_rating = 2500
        low_rating = 1500

        # High rated player should have very high expected score
        expected = EloRating.expected_score(high_rating, low_rating)
        assert expected > 0.99

        # When underdog wins, they should gain significant points
        new_low, new_high = EloRating.update_ratings(
            high_rating, low_rating, "b", ComparisonStrength.DECISIVE
        )

        # Underdog should gain substantial rating
        assert new_low - low_rating > 100  # Big upset = big gain
        assert high_rating - new_high > 100  # Big upset = big loss

    def test_different_k_factors(self):
        """Test all K-factor variations."""
        rating_a = 1500
        rating_b = 1500

        strengths_and_k = [
            (ComparisonStrength.SLIGHT, 16),
            (ComparisonStrength.CLEAR, 32),
            (ComparisonStrength.STRONG, 64),
            (ComparisonStrength.DECISIVE, 128)
        ]

        changes = []
        for strength, expected_k in strengths_and_k:
            new_a, new_b = EloRating.update_ratings(
                rating_a, rating_b, "a", strength
            )
            change = new_a - rating_a
            changes.append(change)

            # With 50% expected score, change should be k/2
            assert abs(change - expected_k / 2) < 0.1

        # Verify changes are proportional to K factors
        assert changes[1] == changes[0] * 2  # CLEAR is 2x SLIGHT
        assert changes[2] == changes[0] * 4  # STRONG is 4x SLIGHT
        assert changes[3] == changes[0] * 8  # DECISIVE is 8x SLIGHT

    def test_rating_boundaries(self):
        """Test that ratings stay within reasonable bounds."""
        # Start with extreme ratings
        very_high = 3000
        very_low = 500

        # Even with decisive loss, ratings shouldn't go negative
        for _ in range(20):  # Multiple losses
            _, very_low = EloRating.update_ratings(
                very_high, very_low, "a", ComparisonStrength.DECISIVE
            )
            assert very_low > 0  # Should never go negative

        # Ratings shouldn't explode to infinity
        for _ in range(20):  # Multiple wins
            very_high, _ = EloRating.update_ratings(
                very_high, 1500, "a", ComparisonStrength.DECISIVE
            )
            assert very_high < 5000  # Reasonable upper bound


class TestComparisonManagerExtended:
    """Extended tests for ComparisonManager edge cases and advanced features."""

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

    def test_empty_database_operations(self, manager):
        """Test operations on empty database."""
        # Should return empty ratings
        ratings = manager.get_ratings()
        assert ratings == []

        # Should return None for next comparison
        comparison = manager.get_next_comparison()
        assert comparison is None

        # Should return empty history
        history = manager.get_comparison_history()
        assert history == []

    def test_populate_from_directory(self, manager):
        """Test populating assets from directory structure."""
        # Create mock directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some fake model directories
            models = ["stablediffusion", "midjourney", "dalle"]
            for model in models:
                model_dir = temp_path / model
                model_dir.mkdir()

                # Add some fake images
                for i in range(3):
                    image_path = model_dir / f"image_{i}.png"
                    image_path.write_text("fake image data")

            # Test population
            from alicemultiverse.comparison.populate import populate_from_directory
            count = populate_from_directory(temp_path, manager)

            assert count == 9  # 3 models * 3 images

            # Verify assets were added correctly
            ratings = manager.get_ratings()
            assert len(ratings) == 3
            assert set(r.model for r in ratings) == set(models)

    def test_smart_pairing_algorithm(self, manager):
        """Test the smart pairing algorithm prioritizes diverse comparisons."""
        # Add assets from multiple models with varying comparison counts
        models = ["model_a", "model_b", "model_c", "model_d"]
        assets = {}

        for model in models:
            for i in range(3):
                asset = Asset(
                    id=f"{model}_{i}",
                    path=f"{model}_{i}.png",
                    model=model
                )
                manager.add_asset(asset)
                if i == 0:  # Keep reference to first asset of each model
                    assets[model] = asset

        # Record some comparisons to create imbalance
        # model_a vs model_b: many comparisons
        for i in range(10):
            comparison = Comparison(
                id=f"comp_ab_{i}",
                asset_a=assets["model_a"],
                asset_b=assets["model_b"],
                winner="a",
                strength=ComparisonStrength.CLEAR,
                timestamp=datetime.now()
            )
            manager.record_comparison(comparison)

        # Now get next comparison - should avoid over-compared pairs
        seen_pairs = set()
        for _ in range(20):
            comparison = manager.get_next_comparison()
            if comparison:
                pair = tuple(sorted([comparison.asset_a.model, comparison.asset_b.model]))
                seen_pairs.add(pair)

        # Should see diverse pairings, not just model_a vs model_b
        assert len(seen_pairs) > 2

    def test_concurrent_comparison_handling(self, manager):
        """Test handling multiple concurrent comparisons."""
        # Add assets
        for i in range(4):
            asset = Asset(id=f"asset_{i}", path=f"{i}.png", model=f"model_{i%2}")
            manager.add_asset(asset)

        # Get multiple comparisons without recording them
        comparisons = []
        for _ in range(3):
            comp = manager.get_next_comparison()
            if comp:
                comparisons.append(comp)

        # All comparisons should have unique IDs
        ids = [c.id for c in comparisons]
        assert len(ids) == len(set(ids))

        # Record them all
        for comp in comparisons:
            comp.winner = "a"
            comp.strength = ComparisonStrength.CLEAR
            manager.record_comparison(comp)

        # Verify all were recorded
        history = manager.get_comparison_history(limit=10)
        assert len(history) >= len(comparisons)

    def test_invalid_vote_handling(self, manager):
        """Test handling of invalid votes."""
        # Add assets
        asset_a = Asset(id="a", path="a.png", model="model_a")
        asset_b = Asset(id="b", path="b.png", model="model_b")
        manager.add_asset(asset_a)
        manager.add_asset(asset_b)

        # Try invalid winner value
        comparison = Comparison(
            id="invalid_comp",
            asset_a=asset_a,
            asset_b=asset_b,
            winner="invalid",  # Invalid winner
            strength=ComparisonStrength.CLEAR,
            timestamp=datetime.now()
        )

        with pytest.raises(Exception):  # Could be ValueError or ConstraintException
            manager.record_comparison(comparison)

        # Try None strength for non-tie
        comparison.winner = "a"
        comparison.strength = None

        with pytest.raises(ValueError):
            manager.record_comparison(comparison)

    def test_model_statistics_accuracy(self, manager):
        """Test accuracy of model statistics calculations."""
        # Add assets from two models
        asset_a = Asset(id="a1", path="a1.png", model="model_a")
        asset_b = Asset(id="b1", path="b1.png", model="model_b")
        manager.add_asset(asset_a)
        manager.add_asset(asset_b)

        # Record specific pattern of comparisons
        results = [
            ("a", ComparisonStrength.DECISIVE),  # A wins decisively
            ("a", ComparisonStrength.CLEAR),     # A wins clearly
            ("b", ComparisonStrength.SLIGHT),    # B wins slightly
            ("tie", ComparisonStrength.SLIGHT),  # Tie (strength doesn't matter)
            ("a", ComparisonStrength.STRONG),    # A wins strongly
        ]

        for i, (winner, strength) in enumerate(results):
            comparison = Comparison(
                id=f"comp_{i}",
                asset_a=asset_a,
                asset_b=asset_b,
                winner=winner,
                strength=strength,
                timestamp=datetime.now()
            )
            manager.record_comparison(comparison)

        # Check statistics
        ratings = manager.get_ratings()
        model_a_stats = next(r for r in ratings if r.model == "model_a")
        model_b_stats = next(r for r in ratings if r.model == "model_b")

        # Model A: 3 wins, 1 loss, 1 tie
        assert model_a_stats.win_count == 3
        assert model_a_stats.loss_count == 1
        assert model_a_stats.tie_count == 1
        assert model_a_stats.comparison_count == 5
        assert abs(model_a_stats.win_rate - 0.75) < 0.01  # 3/4 = 0.75 (ties excluded)

        # Model B: 1 win, 3 losses, 1 tie
        assert model_b_stats.win_count == 1
        assert model_b_stats.loss_count == 3
        assert model_b_stats.tie_count == 1
        assert model_b_stats.comparison_count == 5
        assert abs(model_b_stats.win_rate - 0.25) < 0.01  # 1/4 = 0.25 (ties excluded)


class TestWebAPI:
    """Test the FastAPI web interface."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        # Clear any existing pending comparisons
        pending_comparisons.clear()

        # Mock the comparison manager
        with patch('alicemultiverse.comparison.web_server.comparison_manager') as mock_manager:
            # Set up mock manager
            self.mock_manager = mock_manager
            yield TestClient(app)

    def test_root_endpoint(self, client):
        """Test the root endpoint returns HTML."""
        # Mock the static file
        with patch('pathlib.Path.read_text', return_value="<html>Test</html>"):
            response = client.get("/")
            assert response.status_code == 200
            assert "html" in response.text.lower()

    def test_get_next_comparison_no_data(self, client):
        """Test getting comparison with no data."""
        self.mock_manager.get_next_comparison.return_value = None

        response = client.get("/comparison/next")
        assert response.status_code == 200
        assert response.json() is None

    def test_get_next_comparison_with_data(self, client):
        """Test getting comparison with available data."""
        # Create mock comparison
        mock_comparison = Comparison(
            id="test_comp_123",
            asset_a=Asset(id="a1", path="/path/to/a.png", model="model_a"),
            asset_b=Asset(id="b1", path="/path/to/b.png", model="model_b"),
            winner=None,
            strength=None,
            timestamp=datetime.now()
        )

        self.mock_manager.get_next_comparison.return_value = mock_comparison

        response = client.get("/comparison/next")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test_comp_123"
        assert data["asset_a"]["id"] == "a1"
        assert data["asset_b"]["id"] == "b1"

        # Verify it was added to pending comparisons
        assert "test_comp_123" in pending_comparisons

    def test_submit_vote_valid(self, client):
        """Test submitting a valid vote."""
        # Add a comparison to pending
        test_comparison = Comparison(
            id="vote_test_123",
            asset_a=Asset(id="a1", path="/a.png", model="model_a"),
            asset_b=Asset(id="b1", path="/b.png", model="model_b"),
            winner=None,
            strength=None,
            timestamp=datetime.now()
        )
        pending_comparisons["vote_test_123"] = test_comparison

        # Mock successful recording
        self.mock_manager.record_comparison.return_value = None

        # Submit vote
        vote_data = {
            "comparison_id": "vote_test_123",
            "winner": "a",
            "strength": "clear"
        }

        response = client.post("/comparison/vote", json=vote_data)
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

        # Verify comparison was updated and recorded
        self.mock_manager.record_comparison.assert_called_once()
        recorded_comp = self.mock_manager.record_comparison.call_args[0][0]
        assert recorded_comp.winner == "a"
        assert recorded_comp.strength == ComparisonStrength.CLEAR

        # Verify removed from pending
        assert "vote_test_123" not in pending_comparisons

    def test_submit_vote_invalid_winner(self, client):
        """Test submitting vote with invalid winner."""
        vote_data = {
            "comparison_id": "test_123",
            "winner": "invalid",
            "strength": "clear"
        }

        response = client.post("/comparison/vote", json=vote_data)
        assert response.status_code == 400
        assert "Invalid winner" in response.json()["detail"]

    def test_submit_vote_missing_strength(self, client):
        """Test submitting non-tie vote without strength."""
        # Add comparison to pending
        pending_comparisons["test_123"] = Mock()

        vote_data = {
            "comparison_id": "test_123",
            "winner": "a",
            # Missing strength
        }

        response = client.post("/comparison/vote", json=vote_data)
        assert response.status_code == 400
        assert "Strength required" in response.json()["detail"]

    def test_submit_vote_tie(self, client):
        """Test submitting a tie vote."""
        # Add comparison to pending
        test_comparison = Comparison(
            id="tie_test",
            asset_a=Asset(id="a1", path="/a.png", model="model_a"),
            asset_b=Asset(id="b1", path="/b.png", model="model_b"),
            winner=None,
            strength=None,
            timestamp=datetime.now()
        )
        pending_comparisons["tie_test"] = test_comparison

        self.mock_manager.record_comparison.return_value = None

        vote_data = {
            "comparison_id": "tie_test",
            "winner": "tie"
            # No strength needed for tie
        }

        response = client.post("/comparison/vote", json=vote_data)
        assert response.status_code == 200

        # Verify tie was recorded correctly
        recorded_comp = self.mock_manager.record_comparison.call_args[0][0]
        assert recorded_comp.winner == "tie"
        assert recorded_comp.strength is None

    def test_submit_vote_expired_comparison(self, client):
        """Test voting on expired/missing comparison."""
        vote_data = {
            "comparison_id": "nonexistent",
            "winner": "a",
            "strength": "clear"
        }

        response = client.post("/comparison/vote", json=vote_data)
        assert response.status_code == 404
        assert "not found or expired" in response.json()["detail"]

    def test_get_stats(self, client):
        """Test getting model statistics."""
        # Mock ratings data
        mock_ratings = [
            ModelRating(
                model="model_a",
                rating=1650.5,
                comparison_count=25,
                win_count=18,
                loss_count=5,
                tie_count=2
            ),
            ModelRating(
                model="model_b",
                rating=1450.3,
                comparison_count=25,
                win_count=5,
                loss_count=18,
                tie_count=2,
            )
        ]

        self.mock_manager.get_ratings.return_value = mock_ratings

        response = client.get("/comparison/stats")
        assert response.status_code == 200

        stats = response.json()
        assert len(stats) == 2

        # Verify first model stats
        assert stats[0]["model"] == "model_a"
        assert stats[0]["rating"] == 1650.5
        assert stats[0]["win_count"] == 18
        assert abs(stats[0]["win_rate"] - 0.783) < 0.01  # 18/23 = ~0.783

    def test_serve_image_not_found(self, client):
        """Test serving non-existent image."""
        response = client.get("/static/images/nonexistent.png")
        assert response.status_code == 404

    def test_pending_comparison_cleanup(self, client):
        """Test that old pending comparisons are cleaned up."""
        # Add many pending comparisons
        for i in range(150):
            pending_comparisons[f"comp_{i}"] = Mock()

        # Create a new comparison to trigger cleanup
        mock_comparison = Comparison(
            id="new_comp",
            asset_a=Asset(id="a", path="/a.png", model="model_a"),
            asset_b=Asset(id="b", path="/b.png", model="model_b"),
            winner=None,
            strength=None,
            timestamp=datetime.now()
        )

        self.mock_manager.get_next_comparison.return_value = mock_comparison

        response = client.get("/comparison/next")
        assert response.status_code == 200

        # Should keep only last 100 comparisons
        assert len(pending_comparisons) <= 100
        assert "new_comp" in pending_comparisons


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test.db"
        yield db_path
        shutil.rmtree(temp_dir)

    def test_complete_comparison_workflow(self, temp_db):
        """Test a complete comparison workflow from start to finish."""
        manager = ComparisonManager(db_path=temp_db)

        # 1. Add assets from multiple models
        models = ["flux", "stablediffusion", "midjourney", "dalle3"]
        for model in models:
            for i in range(5):
                asset = Asset(
                    id=f"{model}_{i}",
                    path=f"/images/{model}/image_{i}.png",
                    model=model
                )
                manager.add_asset(asset)

        # 2. Perform series of comparisons
        comparison_results = [
            ("flux", "stablediffusion", "a", ComparisonStrength.DECISIVE),
            ("flux", "midjourney", "a", ComparisonStrength.CLEAR),
            ("flux", "dalle3", "b", ComparisonStrength.SLIGHT),
            ("stablediffusion", "midjourney", "b", ComparisonStrength.CLEAR),
            ("stablediffusion", "dalle3", "b", ComparisonStrength.STRONG),
            ("midjourney", "dalle3", "b", ComparisonStrength.CLEAR),
        ]

        # Create map of model to assets
        model_assets = {}
        for model in models:
            # Just use the first asset for each model
            model_assets[model] = Asset(f"{model}_1", f"{model}/image_1.png", model)

        for model_a, model_b, winner, strength in comparison_results:
            # Get assets for these models
            asset_a = model_assets[model_a]
            asset_b = model_assets[model_b]

            comparison = Comparison(
                id=f"comp_{model_a}_{model_b}",
                asset_a=asset_a,
                asset_b=asset_b,
                winner=winner,
                strength=strength,
                timestamp=datetime.now()
            )
            manager.record_comparison(comparison)

        # 3. Check final rankings
        ratings = manager.get_ratings()
        sorted_ratings = sorted(ratings, key=lambda r: r.rating, reverse=True)

        # Expected rough order based on results:
        # dalle3 (won against flux, sd, midjourney)
        # flux (won against sd, midjourney, lost to dalle3)
        # midjourney (won against sd, lost to flux and dalle3)
        # stablediffusion (lost to everyone)

        model_order = [r.model for r in sorted_ratings]

        # Just verify we have all models ranked
        assert len(model_order) == 4
        assert set(model_order) == set(models)

        # Ratings should be spread out
        assert sorted_ratings[0].rating > 1550
        assert sorted_ratings[-1].rating < 1450
