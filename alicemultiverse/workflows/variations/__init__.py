"""Smart content variation generation system."""

from .variation_generator import (
    ContentBase,
    VariationGenerator,
    VariationResult,
    VariationStrategy,
    VariationType,
)
from .variation_tracker import VariationMetrics, VariationTracker

__all__ = [
    "ContentBase",
    "VariationGenerator",
    "VariationMetrics",
    "VariationResult",
    "VariationStrategy",
    "VariationTracker",
    "VariationType",
]
