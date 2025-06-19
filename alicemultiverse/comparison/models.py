"""Data models for the comparison system."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal


class ComparisonStrength(str, Enum):
    """Strength of preference in a comparison."""
    SLIGHT = "slight"      # Small preference (16 point difference)
    CLEAR = "clear"        # Clear preference (32 point difference)
    STRONG = "strong"      # Strong preference (64 point difference)
    DECISIVE = "decisive"  # Decisive preference (128 point difference)


@dataclass
class Asset:
    """Represents an asset to be compared."""
    id: str
    path: str
    model: str
    metadata: dict | None = None


@dataclass
class Comparison:
    """Represents a comparison between two assets."""
    asset_a: Asset
    asset_b: Asset
    id: str | None = None
    winner: Literal["a", "b", "tie"] | None = None
    strength: ComparisonStrength | None = None
    timestamp: datetime | None = None


@dataclass
class ModelRating:
    """Represents a model's Elo rating."""
    model: str
    rating: float
    comparison_count: int
    win_count: int
    loss_count: int
    tie_count: int

    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        total = self.win_count + self.loss_count
        return float(self.win_count) / total if total > 0 else 0.5
