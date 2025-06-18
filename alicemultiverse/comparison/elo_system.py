"""Elo rating system implementation for model comparison."""

import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import ClassVar

import duckdb

from .models import Asset, Comparison, ComparisonStrength, ModelRating


class EloRating:
    """Implements the Elo rating algorithm."""

    # K-factor determines how much ratings change per comparison
    # Higher K = more volatile ratings
    K_FACTORS: ClassVar[dict[ComparisonStrength, int]] = {
        ComparisonStrength.SLIGHT: 16,
        ComparisonStrength.CLEAR: 32,
        ComparisonStrength.STRONG: 64,
        ComparisonStrength.DECISIVE: 128,
    }

    @staticmethod
    def expected_score(rating_a: float, rating_b: float) -> float:
        """Calculate expected score for player A against player B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    @staticmethod
    def update_ratings(
        rating_a: float,
        rating_b: float,
        winner: str,
        strength: ComparisonStrength = ComparisonStrength.CLEAR
    ) -> tuple[float, float]:
        """
        Update Elo ratings based on comparison result.

        Args:
            rating_a: Current rating of A
            rating_b: Current rating of B
            winner: "a", "b", or "tie"
            strength: Strength of preference

        Returns:
            Tuple of (new_rating_a, new_rating_b)
        """
        expected_a = EloRating.expected_score(rating_a, rating_b)
        expected_b = 1 - expected_a

        # Actual scores
        if winner == "a":
            actual_a = 1.0
            actual_b = 0.0
        elif winner == "b":
            actual_a = 0.0
            actual_b = 1.0
        else:  # tie
            actual_a = 0.5
            actual_b = 0.5

        # K-factor based on strength
        k = EloRating.K_FACTORS[strength]

        # Update ratings
        new_rating_a = rating_a + k * (actual_a - expected_a)
        new_rating_b = rating_b + k * (actual_b - expected_b)

        return new_rating_a, new_rating_b


class ComparisonManager:
    """Manages comparisons and ratings using DuckDB."""

    DEFAULT_RATING = 1500.0

    def __init__(self, db_path: Path | None = None):
        """Initialize the comparison manager."""
        self.db_path = db_path or Path.home() / ".alice" / "comparisons.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with duckdb.connect(str(self.db_path)) as conn:
            # Comparisons table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS comparisons (
                    id VARCHAR PRIMARY KEY,
                    asset_a_id VARCHAR NOT NULL,
                    asset_a_path VARCHAR NOT NULL,
                    asset_a_model VARCHAR NOT NULL,
                    asset_b_id VARCHAR NOT NULL,
                    asset_b_path VARCHAR NOT NULL,
                    asset_b_model VARCHAR NOT NULL,
                    winner VARCHAR CHECK (winner IN ('a', 'b', 'tie')),
                    strength VARCHAR,
                    timestamp TIMESTAMP NOT NULL
                )
            """)

            # Model ratings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_ratings (
                    model VARCHAR PRIMARY KEY,
                    rating DOUBLE NOT NULL DEFAULT 1500.0,
                    comparison_count INTEGER NOT NULL DEFAULT 0,
                    win_count INTEGER NOT NULL DEFAULT 0,
                    loss_count INTEGER NOT NULL DEFAULT 0,
                    tie_count INTEGER NOT NULL DEFAULT 0
                )
            """)

            # Assets table for tracking available assets
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id VARCHAR PRIMARY KEY,
                    path VARCHAR NOT NULL,
                    model VARCHAR NOT NULL,
                    metadata JSON
                )
            """)

    def add_asset(self, asset: Asset) -> None:
        """Add an asset to the pool."""
        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO assets (id, path, model, metadata)
                VALUES (?, ?, ?, ?)
            """, [asset.id, asset.path, asset.model, asset.metadata])

            # Ensure model has a rating entry
            conn.execute("""
                INSERT OR IGNORE INTO model_ratings (model)
                VALUES (?)
            """, [asset.model])

    def get_next_comparison(self) -> Comparison | None:
        """Get the next pair of assets to compare."""
        with duckdb.connect(str(self.db_path)) as conn:
            # Get all assets
            assets_result = conn.execute("""
                SELECT id, path, model, metadata FROM assets
            """).fetchall()

            if len(assets_result) < 2:
                return None

            # Convert to Asset objects
            assets = []
            for row in assets_result:
                assets.append(Asset(
                    id=row[0],
                    path=row[1],
                    model=row[2],
                    metadata=row[3]
                ))

            # Prioritize comparisons between models with similar ratings
            # but also ensure variety
            ratings = self.get_ratings()
            model_ratings = {r.model: r.rating for r in ratings}

            # Group assets by model
            model_assets = {}
            for asset in assets:
                if asset.model not in model_assets:
                    model_assets[asset.model] = []
                model_assets[asset.model].append(asset)

            # Select two different models
            models = list(model_assets.keys())
            if len(models) < 2:
                return None

            # Weight selection by rating proximity (closer ratings = higher probability)
            model_a = random.choice(models)
            rating_a = model_ratings.get(model_a, self.DEFAULT_RATING)

            # Calculate weights based on rating difference
            weights = []
            other_models = [m for m in models if m != model_a]
            for model in other_models:
                rating_b = model_ratings.get(model, self.DEFAULT_RATING)
                # Smaller difference = higher weight
                diff = abs(rating_a - rating_b)
                weight = 1 / (1 + diff / 100)  # Scale difference
                weights.append(weight)

            # Normalize weights
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]

            # Select second model
            model_b = random.choices(other_models, weights=weights)[0]

            # Select random assets from each model
            asset_a = random.choice(model_assets[model_a])
            asset_b = random.choice(model_assets[model_b])

            return Comparison(
                id=str(uuid.uuid4()),
                asset_a=asset_a,
                asset_b=asset_b,
                timestamp=datetime.now()
            )

    def record_comparison(self, comparison: Comparison) -> None:
        """Record a comparison result and update ratings."""
        if not comparison.winner or not comparison.strength:
            raise ValueError("Comparison must have winner and strength")

        with duckdb.connect(str(self.db_path)) as conn:
            # Record the comparison
            conn.execute("""
                INSERT INTO comparisons (
                    id, asset_a_id, asset_a_path, asset_a_model,
                    asset_b_id, asset_b_path, asset_b_model,
                    winner, strength, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                comparison.id,
                comparison.asset_a.id,
                comparison.asset_a.path,
                comparison.asset_a.model,
                comparison.asset_b.id,
                comparison.asset_b.path,
                comparison.asset_b.model,
                comparison.winner,
                comparison.strength.value,
                comparison.timestamp or datetime.now()
            ])

            # Get current ratings
            model_a = comparison.asset_a.model
            model_b = comparison.asset_b.model

            rating_a_result = conn.execute(
                "SELECT rating FROM model_ratings WHERE model = ?", [model_a]
            ).fetchone()
            rating_a = rating_a_result[0] if rating_a_result else self.DEFAULT_RATING

            rating_b_result = conn.execute(
                "SELECT rating FROM model_ratings WHERE model = ?", [model_b]
            ).fetchone()
            rating_b = rating_b_result[0] if rating_b_result else self.DEFAULT_RATING

            # Update ratings
            new_rating_a, new_rating_b = EloRating.update_ratings(
                rating_a, rating_b, comparison.winner, comparison.strength
            )

            # Update model A stats
            if comparison.winner == "a":
                conn.execute("""
                    INSERT INTO model_ratings (model, rating, comparison_count, win_count)
                    VALUES (?, ?, 1, 1)
                    ON CONFLICT(model) DO UPDATE SET
                        rating = ?,
                        comparison_count = comparison_count + 1,
                        win_count = win_count + 1
                """, [model_a, new_rating_a, new_rating_a])
            elif comparison.winner == "b":
                conn.execute("""
                    INSERT INTO model_ratings (model, rating, comparison_count, loss_count)
                    VALUES (?, ?, 1, 1)
                    ON CONFLICT(model) DO UPDATE SET
                        rating = ?,
                        comparison_count = comparison_count + 1,
                        loss_count = loss_count + 1
                """, [model_a, new_rating_a, new_rating_a])
            else:  # tie
                conn.execute("""
                    INSERT INTO model_ratings (model, rating, comparison_count, tie_count)
                    VALUES (?, ?, 1, 1)
                    ON CONFLICT(model) DO UPDATE SET
                        rating = ?,
                        comparison_count = comparison_count + 1,
                        tie_count = tie_count + 1
                """, [model_a, new_rating_a, new_rating_a])

            # Update model B stats
            if comparison.winner == "b":
                conn.execute("""
                    INSERT INTO model_ratings (model, rating, comparison_count, win_count)
                    VALUES (?, ?, 1, 1)
                    ON CONFLICT(model) DO UPDATE SET
                        rating = ?,
                        comparison_count = comparison_count + 1,
                        win_count = win_count + 1
                """, [model_b, new_rating_b, new_rating_b])
            elif comparison.winner == "a":
                conn.execute("""
                    INSERT INTO model_ratings (model, rating, comparison_count, loss_count)
                    VALUES (?, ?, 1, 1)
                    ON CONFLICT(model) DO UPDATE SET
                        rating = ?,
                        comparison_count = comparison_count + 1,
                        loss_count = loss_count + 1
                """, [model_b, new_rating_b, new_rating_b])
            else:  # tie
                conn.execute("""
                    INSERT INTO model_ratings (model, rating, comparison_count, tie_count)
                    VALUES (?, ?, 1, 1)
                    ON CONFLICT(model) DO UPDATE SET
                        rating = ?,
                        comparison_count = comparison_count + 1,
                        tie_count = tie_count + 1
                """, [model_b, new_rating_b, new_rating_b])

    def get_ratings(self) -> list[ModelRating]:
        """Get current ratings for all models."""
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT model, rating, comparison_count, win_count, loss_count, tie_count
                FROM model_ratings
                ORDER BY rating DESC
            """).fetchall()

            return [
                ModelRating(
                    model=row[0],
                    rating=row[1],
                    comparison_count=row[2],
                    win_count=row[3],
                    loss_count=row[4],
                    tie_count=row[5]
                )
                for row in result
            ]

    def get_comparison_history(self, limit: int = 100) -> list[dict]:
        """Get recent comparison history."""
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT
                    id, asset_a_model, asset_b_model,
                    winner, strength, timestamp
                FROM comparisons
                ORDER BY timestamp DESC
                LIMIT ?
            """, [limit]).fetchall()

            return [
                {
                    "id": row[0],
                    "model_a": row[1],
                    "model_b": row[2],
                    "winner": row[3],
                    "strength": row[4],
                    "timestamp": row[5]
                }
                for row in result
            ]
