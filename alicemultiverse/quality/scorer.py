"""Quality scoring functionality extracted from cache implementations."""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class QualityScorer:
    """Handle quality score calculations and star ratings.

    This class centralizes the quality scoring logic that was previously
    duplicated across multiple cache implementations.
    """

    # Default quality thresholds for star ratings
    DEFAULT_THRESHOLDS = {
        "5_star": {"min": 0, "max": 25},
        "4_star": {"min": 25, "max": 45},
        "3_star": {"min": 45, "max": 65},
        "2_star": {"min": 65, "max": 80},
        "1_star": {"min": 80, "max": 100},
    }

    def __init__(self, thresholds: dict[str, dict[str, float]] | None = None):
        """Initialize with quality thresholds.

        Args:
            thresholds: Quality thresholds for star ratings
        """
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS

    def calculate_star_rating(self, quality_score: float) -> int:
        """Calculate star rating from quality score.

        Args:
            quality_score: Quality score (0-100, lower is better)

        Returns:
            Star rating (1-5)
        """
        for stars in [5, 4, 3, 2, 1]:
            key = f"{stars}_star"
            if key in self.thresholds:
                threshold = self.thresholds[key]
                if threshold["min"] <= quality_score <= threshold["max"]:
                    return stars
        return 1  # Default to 1 star if no match

    def recalculate_scores(self, raw_analysis: dict[str, Any]) -> dict[str, Any]:
        """Recalculate scores based on current thresholds.

        This allows scores to be updated when thresholds change without
        re-running expensive analysis.

        Args:
            raw_analysis: Raw analysis results containing scores

        Returns:
            Updated analysis with recalculated ratings
        """
        analysis = raw_analysis.copy()

        # Recalculate star rating if quality score exists
        if "quality_score" in analysis:
            analysis["star_rating"] = self.calculate_star_rating(analysis["quality_score"])

        # Update timestamp
        analysis["score_calculated_at"] = datetime.now().isoformat()

        return analysis

    def merge_pipeline_results(
        self,
        brisque_score: float | None = None,
        sightengine_results: dict[str, Any] | None = None,
        claude_results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Merge results from different pipeline stages.

        Args:
            brisque_score: BRISQUE quality score
            sightengine_results: SightEngine API results
            claude_results: Claude API results

        Returns:
            Merged analysis results
        """
        # Start with BRISQUE as base quality score
        quality_score = brisque_score if brisque_score is not None else 50.0

        # Adjust based on SightEngine results
        if sightengine_results:
            # Apply penalties for quality issues
            if sightengine_results.get("quality", {}).get("score", 1.0) < 0.7:
                quality_score += 10
            if not sightengine_results.get("ai_generated", {}).get("ai_generated", True):
                quality_score += 20

        # Adjust based on Claude results
        if claude_results:
            defects = claude_results.get("defects", [])
            quality_score += len(defects) * 5  # Penalty per defect

        # Ensure score stays in valid range
        quality_score = max(0, min(100, quality_score))

        return {
            "quality_score": quality_score,
            "star_rating": self.calculate_star_rating(quality_score),
            "brisque_score": brisque_score,
            "sightengine_results": sightengine_results,
            "claude_results": claude_results,
            "pipeline_complete": True,
            "analyzed_at": datetime.now().isoformat(),
        }
