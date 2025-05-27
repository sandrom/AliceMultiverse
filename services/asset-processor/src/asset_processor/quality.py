"""Quality assessment pipeline."""

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

try:
    from image_quality import brisque

    BRISQUE_AVAILABLE = True
except ImportError:
    BRISQUE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("BRISQUE not available - install image-quality package")

from alice_config import get_config
from alice_models import QualityRating

from .models import QualityAssessResponse

logger = logging.getLogger(__name__)


class QualityPipeline:
    """Multi-stage quality assessment pipeline."""

    def __init__(self):
        """Initialize quality pipeline."""
        self.logger = logger.getChild("quality")
        self.config = get_config()

        # Get thresholds from config
        self.thresholds = {
            5: self.config.get("services.quality_analyzer.thresholds.5_star", 0.80),
            4: self.config.get("services.quality_analyzer.thresholds.4_star", 0.65),
            3: self.config.get("services.quality_analyzer.thresholds.3_star", 0.50),
            2: self.config.get("services.quality_analyzer.thresholds.2_star", 0.35),
            1: self.config.get("services.quality_analyzer.thresholds.1_star", 0.0),
        }

    async def assess(
        self, file_path: Path, content_hash: str, pipeline_mode: str = "basic"
    ) -> QualityAssessResponse:
        """Run quality assessment pipeline."""
        start_time = time.time()

        # Initialize scores
        brisque_score = None
        sightengine_score = None
        claude_assessment = None
        quality_issues = []
        stages_completed = []

        # Stage 1: BRISQUE (always run for basic mode)
        if BRISQUE_AVAILABLE:
            try:
                brisque_score = await self._assess_brisque(file_path)
                stages_completed.append("brisque")
            except Exception as e:
                self.logger.error(f"BRISQUE assessment failed: {e}")
                quality_issues.append("brisque_failed")

        # Stage 2: SightEngine (standard and premium modes)
        if pipeline_mode in ["standard", "premium"]:
            # Note: Actual API call would be made by main service
            # This is just a placeholder
            stages_completed.append("sightengine_requested")

        # Stage 3: Claude (premium mode only)
        if pipeline_mode == "premium":
            # Note: Actual API call would be made by main service
            # This is just a placeholder
            stages_completed.append("claude_requested")

        # Calculate combined score
        combined_score = self._calculate_combined_score(
            brisque_score=brisque_score,
            sightengine_score=sightengine_score,
            claude_assessment=claude_assessment,
            pipeline_mode=pipeline_mode,
        )

        # Determine star rating
        star_rating = self._determine_star_rating(combined_score)

        # Detect quality issues
        if brisque_score:
            issues = self._detect_quality_issues(brisque_score)
            quality_issues.extend(issues)

        # Calculate duration
        assessment_duration_ms = int((time.time() - start_time) * 1000)

        return QualityAssessResponse(
            star_rating=star_rating,
            combined_score=combined_score,
            brisque_score=brisque_score,
            sightengine_score=sightengine_score,
            claude_assessment=claude_assessment,
            quality_issues=quality_issues,
            pipeline_mode=pipeline_mode,
            stages_completed=stages_completed,
            assessment_duration_ms=assessment_duration_ms,
        )

    async def _assess_brisque(self, file_path: Path) -> float:
        """Run BRISQUE quality assessment."""
        if not BRISQUE_AVAILABLE:
            raise RuntimeError("BRISQUE not available")

        try:
            # Load image with PIL
            from PIL import Image

            img = Image.open(file_path)

            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Convert to numpy array
            img_array = np.array(img)

            # Calculate BRISQUE score
            score = brisque.score(img_array)

            # Clamp to reasonable range (0-100)
            score = max(0, min(100, score))

            return float(score)

        except Exception as e:
            self.logger.error(f"BRISQUE calculation failed: {e}")
            raise

    def _calculate_combined_score(
        self,
        brisque_score: float | None,
        sightengine_score: float | None,
        claude_assessment: dict[str, Any] | None,
        pipeline_mode: str,
    ) -> float:
        """Calculate combined quality score (0-1, higher is better)."""

        if pipeline_mode == "basic":
            # Only BRISQUE available
            if brisque_score is not None:
                # Convert BRISQUE (0-100, lower is better) to 0-1 (higher is better)
                return 1.0 - (brisque_score / 100.0)
            return 0.5  # Default if no score

        elif pipeline_mode == "standard":
            # BRISQUE + SightEngine
            scores = []
            weights = []

            if brisque_score is not None:
                scores.append(1.0 - (brisque_score / 100.0))
                weights.append(0.6)  # 60% weight

            if sightengine_score is not None:
                scores.append(sightengine_score)
                weights.append(0.4)  # 40% weight

            if scores:
                return sum(s * w for s, w in zip(scores, weights, strict=False)) / sum(weights)
            return 0.5

        elif pipeline_mode == "premium":
            # All three sources
            scores = []
            weights = []

            if brisque_score is not None:
                scores.append(1.0 - (brisque_score / 100.0))
                weights.append(0.4)  # 40% weight

            if sightengine_score is not None:
                scores.append(sightengine_score)
                weights.append(0.3)  # 30% weight

            if claude_assessment and "quality_score" in claude_assessment:
                scores.append(claude_assessment["quality_score"])
                weights.append(0.3)  # 30% weight

            if scores:
                return sum(s * w for s, w in zip(scores, weights, strict=False)) / sum(weights)
            return 0.5

        return 0.5  # Default

    def _determine_star_rating(self, combined_score: float) -> QualityRating:
        """Determine star rating from combined score."""
        for stars in [5, 4, 3, 2, 1]:
            if combined_score >= self.thresholds[stars]:
                return QualityRating(stars)
        return QualityRating.ONE_STAR

    def _detect_quality_issues(self, brisque_score: float) -> list[str]:
        """Detect specific quality issues from BRISQUE score."""
        issues = []

        if brisque_score > 80:
            issues.append("very_poor_quality")
        elif brisque_score > 65:
            issues.append("poor_quality")

        if brisque_score > 70:
            issues.extend(["possible_blur", "possible_compression_artifacts"])

        return issues
