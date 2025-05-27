"""Pipeline stages for quality assessment."""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path

from ..core.types import MediaType
from ..quality.brisque import BRISQUEAssessor
from ..quality.brisque import is_available as brisque_available

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    """Abstract base class for pipeline stages."""

    @abstractmethod
    def name(self) -> str:
        """Return the name of this stage."""
        pass

    @abstractmethod
    def process(self, image_path: Path, metadata: dict) -> dict:
        """Process an image through this stage.

        Args:
            image_path: Path to the image
            metadata: Current metadata for the image

        Returns:
            Updated metadata with stage results
        """
        pass

    @abstractmethod
    def should_process(self, metadata: dict) -> bool:
        """Check if this stage should process the image.

        Args:
            metadata: Current metadata for the image

        Returns:
            True if the stage should process this image
        """
        pass

    @abstractmethod
    def get_cost(self) -> float:
        """Get the cost per image for this stage."""
        pass


class BRISQUEStage(PipelineStage):
    """BRISQUE quality assessment stage."""

    def __init__(self, thresholds: dict[int, tuple[float, float]]):
        """Initialize BRISQUE stage.

        Args:
            thresholds: Quality thresholds mapping stars to score ranges
        """
        self.assessor = BRISQUEAssessor(thresholds) if brisque_available() else None
        self.thresholds = thresholds

    def name(self) -> str:
        return "brisque"

    def process(self, image_path: Path, metadata: dict) -> dict:
        """Process image through BRISQUE assessment."""
        if not self.assessor:
            logger.warning("BRISQUE not available, skipping assessment")
            return metadata

        try:
            score, stars = self.assessor.assess_quality(image_path)
            if score is not None:
                metadata["brisque_score"] = score
                metadata["brisque_stars"] = stars  # Store original BRISQUE rating
                metadata["quality_stars"] = stars  # This will be updated by later stages

                # Use dict to avoid duplicates when reprocessing
                if "pipeline_stages" not in metadata:
                    metadata["pipeline_stages"] = {}

                metadata["pipeline_stages"]["brisque"] = {
                    "score": score,
                    "stars": stars,
                    "passed": stars >= 3,  # Pass if 3+ stars
                    "timestamp": time.time(),
                }
            else:
                logger.warning(f"BRISQUE assessment failed for {image_path.name}")
        except Exception as e:
            logger.error(f"BRISQUE error for {image_path.name}: {e}")

        return metadata

    def should_process(self, metadata: dict) -> bool:
        """BRISQUE processes all images."""
        return metadata.get("media_type") == MediaType.IMAGE

    def get_cost(self) -> float:
        """BRISQUE is free (local processing)."""
        return 0.0


class SightEngineStage(PipelineStage):
    """SightEngine API quality assessment stage."""

    def __init__(
        self,
        api_user: str,
        api_secret: str,
        min_stars: int = 3,
        weights: dict[str, float] | None = None,
        star_thresholds: dict[str, float] | None = None,
    ):
        """Initialize SightEngine stage.

        Args:
            api_user: SightEngine API user
            api_secret: SightEngine API secret
            min_stars: Minimum BRISQUE stars required to process
            weights: Scoring weights for combining scores
            star_thresholds: Thresholds for star ratings
        """
        self.api_user = api_user
        self.api_secret = api_secret
        self.min_stars = min_stars
        self.weights = weights or {"brisque": 0.6, "sightengine": 0.4}
        self.star_thresholds = star_thresholds or {"5_star": 0.80, "4_star": 0.65}

    def name(self) -> str:
        return "sightengine"

    def process(self, image_path: Path, metadata: dict) -> dict:
        """Process image through SightEngine API to refine quality rating."""
        try:
            # Import here to avoid circular imports
            from ..quality.sightengine import check_image_quality

            result = check_image_quality(str(image_path), self.api_user, self.api_secret)

            if result:
                # Extract quality metrics (SightEngine returns 0-1, higher is better)
                sightengine_score = result.get("quality", {}).get("score", 0.5)

                # Store raw results
                metadata["sightengine_quality"] = sightengine_score
                metadata["sightengine_raw_result"] = result

                # Get original BRISQUE score and stars
                brisque_score = metadata.get("brisque_score", 50)  # 0-100, lower is better
                brisque_stars = metadata.get("brisque_stars", 3)

                # Normalize BRISQUE score to 0-1 range (higher is better)
                # BRISQUE: 0-25 = excellent, 25-45 = good, 45-65 = fair, 65-80 = poor, 80+ = bad
                brisque_normalized = max(0, min(1, (100 - brisque_score) / 100))

                # Combine scores with configurable weights
                brisque_weight = self.weights.get("brisque", 0.6)
                sightengine_weight = self.weights.get("sightengine", 0.4)
                combined_score = (brisque_weight * brisque_normalized) + (
                    sightengine_weight * sightengine_score
                )

                # Map combined score to star rating using configurable thresholds
                if combined_score >= self.star_thresholds.get("5_star", 0.80):
                    final_stars = 5
                elif combined_score >= self.star_thresholds.get("4_star", 0.65):
                    final_stars = 4
                else:
                    final_stars = 3

                # Update the quality stars
                metadata["quality_stars"] = final_stars
                metadata["combined_quality_score"] = combined_score

                # Log significant changes
                if final_stars != brisque_stars:
                    logger.info(
                        f"{image_path.name}: Quality adjusted from {brisque_stars}★ to {final_stars}★ "
                        f"(BRISQUE: {brisque_score:.1f}, SightEngine: {sightengine_score:.2f}, Combined: {combined_score:.2f})"
                    )

                # Use dict to avoid duplicates when reprocessing
                if "pipeline_stages" not in metadata:
                    metadata["pipeline_stages"] = {}

                metadata["pipeline_stages"]["sightengine"] = {
                    "quality_score": sightengine_score,
                    "brisque_stars": brisque_stars,
                    "final_stars": final_stars,
                    "combined_score": combined_score,
                    "passed": True,  # Always pass since we're just refining ratings
                    "timestamp": time.time(),
                }

        except Exception as e:
            logger.error(f"SightEngine error for {image_path.name}: {e}")

        return metadata

    def should_process(self, metadata: dict) -> bool:
        """Process if image has sufficient BRISQUE stars."""
        if metadata.get("media_type") != MediaType.IMAGE:
            return False

        stars = metadata.get("quality_stars", 0)
        return stars >= self.min_stars

    def get_cost(self) -> float:
        """SightEngine costs $0.001 per image."""
        return 0.001


class ClaudeStage(PipelineStage):
    """Claude API stage for AI defect detection and final quality refinement."""

    def __init__(
        self,
        api_key: str,
        min_stars: int = 4,
        model: str = "claude-3-haiku-20240307",
        weights: dict[str, float] | None = None,
        star_thresholds: dict[str, float] | None = None,
    ):
        """Initialize Claude stage.

        Args:
            api_key: Anthropic API key
            min_stars: Minimum stars required to process through Claude
            model: Claude model to use (haiku is most cost-effective)
            weights: Scoring weights for combining scores
            star_thresholds: Thresholds for star ratings
        """
        self.api_key = api_key
        self.min_stars = min_stars
        self.model = model
        self.weights = weights or {"brisque": 0.4, "sightengine": 0.3, "claude": 0.3}
        self.star_thresholds = star_thresholds or {"5_star": 0.80, "4_star": 0.65}

    def name(self) -> str:
        return "claude"

    def process(self, image_path: Path, metadata: dict) -> dict:
        """Process image through Claude for defect detection and final quality refinement."""
        try:
            # Import here to avoid circular imports
            from ..quality.claude import check_image_defects

            result = check_image_defects(str(image_path), self.api_key, self.model)

            if result:
                # Store defect analysis results
                metadata["claude_defects_found"] = result.get("defects_found", False)
                metadata["claude_defect_count"] = result.get("defect_count", 0)
                metadata["claude_severity"] = result.get("severity", "low")
                metadata["claude_confidence"] = result.get("confidence", 0.0)

                # Calculate Claude quality score (0-1, higher is better)
                # Based on defect count and severity
                defect_count = result.get("defect_count", 0)
                severity = result.get("severity", "low")

                if defect_count == 0:
                    claude_score = 1.0
                elif severity == "low":
                    claude_score = max(0.7, 1.0 - (defect_count * 0.1))
                elif severity == "medium":
                    claude_score = max(0.4, 0.7 - (defect_count * 0.1))
                else:  # high severity
                    claude_score = max(0.2, 0.4 - (defect_count * 0.1))

                # Get all previous scores
                brisque_score = metadata.get("brisque_score", 50)
                brisque_normalized = max(0, min(1, (100 - brisque_score) / 100))
                sightengine_score = metadata.get("sightengine_quality", 0.7)

                # Calculate final combined score with configurable weights
                brisque_weight = self.weights.get("brisque", 0.4)
                sightengine_weight = self.weights.get("sightengine", 0.3)
                claude_weight = self.weights.get("claude", 0.3)

                final_combined_score = (
                    brisque_weight * brisque_normalized
                    + sightengine_weight * sightengine_score
                    + claude_weight * claude_score
                )

                # Map to final star rating using configurable thresholds
                if final_combined_score >= self.star_thresholds.get("5_star", 0.80):
                    final_stars = 5
                elif final_combined_score >= self.star_thresholds.get("4_star", 0.65):
                    final_stars = 4
                else:
                    final_stars = 3

                # Get previous star rating for comparison
                previous_stars = metadata.get("quality_stars", 3)

                # Update final quality rating
                metadata["quality_stars"] = final_stars
                metadata["final_combined_score"] = final_combined_score
                metadata["claude_quality_score"] = claude_score

                # Log if rating changed
                if final_stars != previous_stars:
                    logger.info(
                        f"{image_path.name}: Final quality: {final_stars}★ "
                        f"(BRISQUE: {brisque_score:.1f}, SightEngine: {sightengine_score:.2f}, "
                        f"Claude: {claude_score:.2f}, Combined: {final_combined_score:.2f})"
                    )

                # Use dict to avoid duplicates when reprocessing
                if "pipeline_stages" not in metadata:
                    metadata["pipeline_stages"] = {}

                metadata["pipeline_stages"]["claude"] = {
                    "defects_found": result.get("defects_found", False),
                    "defect_count": result.get("defect_count", 0),
                    "severity": result.get("severity", "low"),
                    "confidence": result.get("confidence", 0.0),
                    "defects": result.get("defects", []),
                    "claude_score": claude_score,
                    "final_stars": final_stars,
                    "final_combined_score": final_combined_score,
                    "passed": True,  # Always pass since we're refining
                    "tokens_used": result.get("tokens_used", 0),
                    "timestamp": time.time(),
                }

        except Exception as e:
            logger.error(f"Claude error for {image_path.name}: {e}")

        return metadata

    def should_process(self, metadata: dict) -> bool:
        """Process if image has sufficient quality stars."""
        if metadata.get("media_type") != MediaType.IMAGE:
            return False

        # Process images with sufficient star rating
        stars = metadata.get("quality_stars", 0)
        if stars is None:
            return False
        return stars >= self.min_stars

    def get_cost(self) -> float:
        """Get estimated cost for Claude analysis."""
        from ..quality.claude import estimate_cost

        return estimate_cost(self.model)
