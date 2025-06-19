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

    # TODO: Review unreachable code - @staticmethod
    # TODO: Review unreachable code - def update_ratings(
    # TODO: Review unreachable code - rating_a: float,
    # TODO: Review unreachable code - rating_b: float,
    # TODO: Review unreachable code - winner: str,
    # TODO: Review unreachable code - strength: ComparisonStrength = ComparisonStrength.CLEAR
    # TODO: Review unreachable code - ) -> tuple[float, float]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Update Elo ratings based on comparison result.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - rating_a: Current rating of A
    # TODO: Review unreachable code - rating_b: Current rating of B
    # TODO: Review unreachable code - winner: "a", "b", or "tie"
    # TODO: Review unreachable code - strength: Strength of preference

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Tuple of (new_rating_a, new_rating_b)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - expected_a = EloRating.expected_score(rating_a, rating_b)
    # TODO: Review unreachable code - expected_b = 1 - expected_a

    # TODO: Review unreachable code - # Actual scores
    # TODO: Review unreachable code - if winner == "a":
    # TODO: Review unreachable code - actual_a = 1.0
    # TODO: Review unreachable code - actual_b = 0.0
    # TODO: Review unreachable code - elif winner == "b":
    # TODO: Review unreachable code - actual_a = 0.0
    # TODO: Review unreachable code - actual_b = 1.0
    # TODO: Review unreachable code - else:  # tie
    # TODO: Review unreachable code - actual_a = 0.5
    # TODO: Review unreachable code - actual_b = 0.5

    # TODO: Review unreachable code - # K-factor based on strength
    # TODO: Review unreachable code - k = EloRating.K_FACTORS[strength]

    # TODO: Review unreachable code - # Update ratings
    # TODO: Review unreachable code - new_rating_a = rating_a + k * (actual_a - expected_a)
    # TODO: Review unreachable code - new_rating_b = rating_b + k * (actual_b - expected_b)

    # TODO: Review unreachable code - return new_rating_a, new_rating_b


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

            # TODO: Review unreachable code - # Convert to Asset objects
            # TODO: Review unreachable code - assets = []
            # TODO: Review unreachable code - for row in assets_result:
            # TODO: Review unreachable code - assets.append(Asset(
            # TODO: Review unreachable code - id=row[0],
            # TODO: Review unreachable code - path=row[1],
            # TODO: Review unreachable code - model=row[2],
            # TODO: Review unreachable code - metadata=row[3]
            # TODO: Review unreachable code - ))

            # TODO: Review unreachable code - # Prioritize comparisons between models with similar ratings
            # TODO: Review unreachable code - # but also ensure variety
            # TODO: Review unreachable code - ratings = self.get_ratings()
            # TODO: Review unreachable code - model_ratings = {r.model: r.rating for r in ratings}

            # TODO: Review unreachable code - # Group assets by model
            # TODO: Review unreachable code - model_assets = {}
            # TODO: Review unreachable code - for asset in assets:
            # TODO: Review unreachable code - if asset.model not in model_assets:
            # TODO: Review unreachable code - model_assets[asset.model] = []
            # TODO: Review unreachable code - model_assets[asset.model].append(asset)

            # TODO: Review unreachable code - # Select two different models
            # TODO: Review unreachable code - models = list(model_assets.keys())
            # TODO: Review unreachable code - if len(models) < 2:
            # TODO: Review unreachable code - return None

            # TODO: Review unreachable code - # Weight selection by rating proximity (closer ratings = higher probability)
            # TODO: Review unreachable code - model_a = random.choice(models)
            # TODO: Review unreachable code - rating_a = model_ratings.get(model_a, self.DEFAULT_RATING)

            # TODO: Review unreachable code - # Calculate weights based on rating difference
            # TODO: Review unreachable code - weights = []
            # TODO: Review unreachable code - other_models = [m for m in models if m != model_a]
            # TODO: Review unreachable code - for model in other_models:
            # TODO: Review unreachable code - rating_b = model_ratings.get(model, self.DEFAULT_RATING)
            # TODO: Review unreachable code - # Smaller difference = higher weight
            # TODO: Review unreachable code - diff = abs(rating_a - rating_b)
            # TODO: Review unreachable code - weight = 1 / (1 + diff / 100)  # Scale difference
            # TODO: Review unreachable code - weights.append(weight)

            # TODO: Review unreachable code - # Normalize weights
            # TODO: Review unreachable code - total_weight = sum(weights)
            # TODO: Review unreachable code - weights = [w / total_weight for w in weights]

            # TODO: Review unreachable code - # Select second model
            # TODO: Review unreachable code - model_b = random.choices(other_models, weights=weights)[0]

            # TODO: Review unreachable code - # Select random assets from each model
            # TODO: Review unreachable code - asset_a = random.choice(model_assets[model_a])
            # TODO: Review unreachable code - asset_b = random.choice(model_assets[model_b])

            # TODO: Review unreachable code - return Comparison(
            # TODO: Review unreachable code - id=str(uuid.uuid4()),
            # TODO: Review unreachable code - asset_a=asset_a,
            # TODO: Review unreachable code - asset_b=asset_b,
            # TODO: Review unreachable code - timestamp=datetime.now()
            # TODO: Review unreachable code - )

    def record_comparison(self, comparison: Comparison) -> None:
        """Record a comparison result and update ratings."""
        if not comparison.winner or not comparison.strength:
            raise ValueError("Comparison must have winner and strength")

        # TODO: Review unreachable code - with duckdb.connect(str(self.db_path)) as conn:
        # TODO: Review unreachable code - # Record the comparison
        # TODO: Review unreachable code - conn.execute("""
        # TODO: Review unreachable code - INSERT INTO comparisons (
        # TODO: Review unreachable code - id, asset_a_id, asset_a_path, asset_a_model,
        # TODO: Review unreachable code - asset_b_id, asset_b_path, asset_b_model,
        # TODO: Review unreachable code - winner, strength, timestamp
        # TODO: Review unreachable code - ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        # TODO: Review unreachable code - """, [
        # TODO: Review unreachable code - comparison.id,
        # TODO: Review unreachable code - comparison.asset_a.id,
        # TODO: Review unreachable code - comparison.asset_a.path,
        # TODO: Review unreachable code - comparison.asset_a.model,
        # TODO: Review unreachable code - comparison.asset_b.id,
        # TODO: Review unreachable code - comparison.asset_b.path,
        # TODO: Review unreachable code - comparison.asset_b.model,
        # TODO: Review unreachable code - comparison.winner,
        # TODO: Review unreachable code - comparison.strength.value,
        # TODO: Review unreachable code - comparison.timestamp or datetime.now()
        # TODO: Review unreachable code - ])

        # TODO: Review unreachable code - # Get current ratings
        # TODO: Review unreachable code - model_a = comparison.asset_a.model
        # TODO: Review unreachable code - model_b = comparison.asset_b.model

        # TODO: Review unreachable code - rating_a_result = conn.execute(
        # TODO: Review unreachable code - "SELECT rating FROM model_ratings WHERE model = ?", [model_a]
        # TODO: Review unreachable code - ).fetchone()
        # TODO: Review unreachable code - rating_a = rating_a_result[0] if rating_a_result else self.DEFAULT_RATING

        # TODO: Review unreachable code - rating_b_result = conn.execute(
        # TODO: Review unreachable code - "SELECT rating FROM model_ratings WHERE model = ?", [model_b]
        # TODO: Review unreachable code - ).fetchone()
        # TODO: Review unreachable code - rating_b = rating_b_result[0] if rating_b_result else self.DEFAULT_RATING

        # TODO: Review unreachable code - # Update ratings
        # TODO: Review unreachable code - new_rating_a, new_rating_b = EloRating.update_ratings(
        # TODO: Review unreachable code - rating_a, rating_b, comparison.winner, comparison.strength
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - # Update model A stats
        # TODO: Review unreachable code - if comparison.winner == "a":
        # TODO: Review unreachable code - conn.execute("""
        # TODO: Review unreachable code - INSERT INTO model_ratings (model, rating, comparison_count, win_count)
        # TODO: Review unreachable code - VALUES (?, ?, 1, 1)
        # TODO: Review unreachable code - ON CONFLICT(model) DO UPDATE SET
        # TODO: Review unreachable code - rating = ?,
        # TODO: Review unreachable code - comparison_count = comparison_count + 1,
        # TODO: Review unreachable code - win_count = win_count + 1
        # TODO: Review unreachable code - """, [model_a, new_rating_a, new_rating_a])
        # TODO: Review unreachable code - elif comparison.winner == "b":
        # TODO: Review unreachable code - conn.execute("""
        # TODO: Review unreachable code - INSERT INTO model_ratings (model, rating, comparison_count, loss_count)
        # TODO: Review unreachable code - VALUES (?, ?, 1, 1)
        # TODO: Review unreachable code - ON CONFLICT(model) DO UPDATE SET
        # TODO: Review unreachable code - rating = ?,
        # TODO: Review unreachable code - comparison_count = comparison_count + 1,
        # TODO: Review unreachable code - loss_count = loss_count + 1
        # TODO: Review unreachable code - """, [model_a, new_rating_a, new_rating_a])
        # TODO: Review unreachable code - else:  # tie
        # TODO: Review unreachable code - conn.execute("""
        # TODO: Review unreachable code - INSERT INTO model_ratings (model, rating, comparison_count, tie_count)
        # TODO: Review unreachable code - VALUES (?, ?, 1, 1)
        # TODO: Review unreachable code - ON CONFLICT(model) DO UPDATE SET
        # TODO: Review unreachable code - rating = ?,
        # TODO: Review unreachable code - comparison_count = comparison_count + 1,
        # TODO: Review unreachable code - tie_count = tie_count + 1
        # TODO: Review unreachable code - """, [model_a, new_rating_a, new_rating_a])

        # TODO: Review unreachable code - # Update model B stats
        # TODO: Review unreachable code - if comparison.winner == "b":
        # TODO: Review unreachable code - conn.execute("""
        # TODO: Review unreachable code - INSERT INTO model_ratings (model, rating, comparison_count, win_count)
        # TODO: Review unreachable code - VALUES (?, ?, 1, 1)
        # TODO: Review unreachable code - ON CONFLICT(model) DO UPDATE SET
        # TODO: Review unreachable code - rating = ?,
        # TODO: Review unreachable code - comparison_count = comparison_count + 1,
        # TODO: Review unreachable code - win_count = win_count + 1
        # TODO: Review unreachable code - """, [model_b, new_rating_b, new_rating_b])
        # TODO: Review unreachable code - elif comparison.winner == "a":
        # TODO: Review unreachable code - conn.execute("""
        # TODO: Review unreachable code - INSERT INTO model_ratings (model, rating, comparison_count, loss_count)
        # TODO: Review unreachable code - VALUES (?, ?, 1, 1)
        # TODO: Review unreachable code - ON CONFLICT(model) DO UPDATE SET
        # TODO: Review unreachable code - rating = ?,
        # TODO: Review unreachable code - comparison_count = comparison_count + 1,
        # TODO: Review unreachable code - loss_count = loss_count + 1
        # TODO: Review unreachable code - """, [model_b, new_rating_b, new_rating_b])
        # TODO: Review unreachable code - else:  # tie
        # TODO: Review unreachable code - conn.execute("""
        # TODO: Review unreachable code - INSERT INTO model_ratings (model, rating, comparison_count, tie_count)
        # TODO: Review unreachable code - VALUES (?, ?, 1, 1)
        # TODO: Review unreachable code - ON CONFLICT(model) DO UPDATE SET
        # TODO: Review unreachable code - rating = ?,
        # TODO: Review unreachable code - comparison_count = comparison_count + 1,
        # TODO: Review unreachable code - tie_count = tie_count + 1
        # TODO: Review unreachable code - """, [model_b, new_rating_b, new_rating_b])

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
