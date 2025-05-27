"""Simplified pipeline stages for quality assessment."""

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..quality.brisque import BRISQUEAssessor
from ..quality.brisque import is_available as brisque_available

logger = logging.getLogger(__name__)


def create_brisque_stage(thresholds: dict[int, tuple]) -> Callable:
    """Create BRISQUE assessment stage function."""
    assessor = BRISQUEAssessor(thresholds) if brisque_available() else None

    def process_brisque(image_path: Path, metadata: dict) -> dict:
        """Process image through BRISQUE assessment."""
        if not assessor:
            logger.warning("BRISQUE not available, skipping assessment")
            return metadata

        try:
            score, stars = assessor.assess_quality(image_path)
            if score is not None:
                metadata["brisque_score"] = score
                metadata["brisque_stars"] = stars
                metadata["quality_stars"] = stars  # Initial quality rating

                # Initialize pipeline results dict
                if "pipeline_stages" not in metadata:
                    metadata["pipeline_stages"] = {}

                metadata["pipeline_stages"]["brisque"] = {
                    "score": score,
                    "stars": stars,
                    "passed": stars >= 3,
                    "timestamp": time.time(),
                }

                logger.debug(f"{image_path.name}: BRISQUE score={score:.1f}, stars={stars}")

        except Exception as e:
            logger.error(f"BRISQUE error for {image_path.name}: {e}")

        return metadata

    # Add metadata to the function
    process_brisque.stage_name = "brisque"
    process_brisque.min_stars = 0  # Process all images
    process_brisque.cost = 0.0

    return process_brisque


def create_sightengine_stage(
    api_user: str,
    api_secret: str,
    min_stars: int = 3,
    weights: dict[str, float] | None = None,
    star_thresholds: dict[str, float] | None = None,
) -> Callable:
    """Create SightEngine assessment stage function."""
    weights = weights or {"brisque": 0.6, "sightengine": 0.4}
    star_thresholds = star_thresholds or {"5_star": 0.80, "4_star": 0.65}

    def process_sightengine(image_path: Path, metadata: dict) -> dict:
        """Process image through SightEngine API."""
        # Check if should process
        current_stars = metadata.get("quality_stars", 0)
        if current_stars < min_stars:
            return metadata

        try:
            from ..quality.sightengine import check_image_quality

            result = check_image_quality(str(image_path), api_user, api_secret)

            if result:
                # Extract and store results
                sightengine_score = result.get("quality", {}).get("score", 0.5)
                metadata["sightengine_quality"] = sightengine_score
                metadata["sightengine_raw_result"] = result

                # Combine with BRISQUE score
                brisque_score = metadata.get("brisque_score", 50)
                brisque_normalized = max(0, min(1, (100 - brisque_score) / 100))

                combined_score = (
                    weights["brisque"] * brisque_normalized
                    + weights["sightengine"] * sightengine_score
                )

                # Update star rating
                if combined_score >= star_thresholds["5_star"]:
                    final_stars = 5
                elif combined_score >= star_thresholds["4_star"]:
                    final_stars = 4
                else:
                    final_stars = 3

                previous_stars = metadata.get("quality_stars", 3)
                metadata["quality_stars"] = final_stars
                metadata["combined_quality_score"] = combined_score

                if "pipeline_stages" not in metadata:
                    metadata["pipeline_stages"] = {}

                metadata["pipeline_stages"]["sightengine"] = {
                    "quality_score": sightengine_score,
                    "final_stars": final_stars,
                    "combined_score": combined_score,
                    "passed": True,
                    "timestamp": time.time(),
                }

                if final_stars != previous_stars:
                    logger.info(
                        f"{image_path.name}: Quality adjusted {previous_stars}★ → {final_stars}★"
                    )

        except Exception as e:
            logger.error(f"SightEngine error for {image_path.name}: {e}")

        return metadata

    process_sightengine.stage_name = "sightengine"
    process_sightengine.min_stars = min_stars
    process_sightengine.cost = 0.001

    return process_sightengine


def create_claude_stage(
    api_key: str,
    min_stars: int = 4,
    model: str = "claude-3-haiku-20240307",
    weights: dict[str, float] | None = None,
    star_thresholds: dict[str, float] | None = None,
) -> Callable:
    """Create Claude assessment stage function."""
    weights = weights or {"brisque": 0.4, "sightengine": 0.3, "claude": 0.3}
    star_thresholds = star_thresholds or {"5_star": 0.80, "4_star": 0.65}

    def process_claude(image_path: Path, metadata: dict) -> dict:
        """Process image through Claude for defect detection."""
        # Check if should process
        current_stars = metadata.get("quality_stars", 0)
        if current_stars < min_stars:
            return metadata

        try:
            from ..quality.claude import check_image_defects

            result = check_image_defects(str(image_path), api_key, model)

            if result:
                # Store defect analysis
                metadata["claude_defects_found"] = result.get("defects_found", False)
                metadata["claude_defect_count"] = result.get("defect_count", 0)
                metadata["claude_severity"] = result.get("severity", "low")

                # Calculate Claude score based on defects
                defect_count = result.get("defect_count", 0)
                severity = result.get("severity", "low")

                if defect_count == 0:
                    claude_score = 1.0
                elif severity == "low":
                    claude_score = max(0.7, 1.0 - (defect_count * 0.1))
                elif severity == "medium":
                    claude_score = max(0.4, 0.7 - (defect_count * 0.1))
                else:
                    claude_score = max(0.2, 0.4 - (defect_count * 0.1))

                # Calculate final combined score
                brisque_score = metadata.get("brisque_score", 50)
                brisque_normalized = max(0, min(1, (100 - brisque_score) / 100))
                sightengine_score = metadata.get("sightengine_quality", 0.7)

                final_combined_score = (
                    weights["brisque"] * brisque_normalized
                    + weights["sightengine"] * sightengine_score
                    + weights["claude"] * claude_score
                )

                # Update final star rating
                if final_combined_score >= star_thresholds["5_star"]:
                    final_stars = 5
                elif final_combined_score >= star_thresholds["4_star"]:
                    final_stars = 4
                else:
                    final_stars = 3

                previous_stars = metadata.get("quality_stars", 3)
                metadata["quality_stars"] = final_stars
                metadata["final_combined_score"] = final_combined_score
                metadata["claude_quality_score"] = claude_score

                if "pipeline_stages" not in metadata:
                    metadata["pipeline_stages"] = {}

                metadata["pipeline_stages"]["claude"] = {
                    "defects_found": result.get("defects_found", False),
                    "defect_count": result.get("defect_count", 0),
                    "severity": result.get("severity", "low"),
                    "defects": result.get("defects", []),
                    "claude_score": claude_score,
                    "final_stars": final_stars,
                    "final_combined_score": final_combined_score,
                    "passed": True,
                    "timestamp": time.time(),
                }

                if final_stars != previous_stars:
                    logger.info(
                        f"{image_path.name}: Final quality {previous_stars}★ → {final_stars}★"
                    )

        except Exception as e:
            logger.error(f"Claude error for {image_path.name}: {e}")

        return metadata

    process_claude.stage_name = "claude"
    process_claude.min_stars = min_stars

    # Calculate cost
    from ..quality.claude import estimate_cost

    process_claude.cost = estimate_cost(model)

    return process_claude


def create_pipeline_stages(config: Any) -> list[Callable]:
    """Create pipeline stages based on configuration.

    Args:
        config: Configuration object with pipeline settings

    Returns:
        List of stage processing functions
    """
    stages = []

    # Check if pipeline mode is set in processing config
    pipeline_mode = getattr(config.processing, "pipeline", None)
    if not pipeline_mode or pipeline_mode == "none":
        return stages

    # Get quality thresholds
    thresholds = {}
    if hasattr(config, "quality") and hasattr(config.quality, "thresholds"):
        thresholds = dict(config.quality.thresholds)

    # Always add BRISQUE if quality is enabled or pipeline is active
    if pipeline_mode or (hasattr(config.processing, "quality") and config.processing.quality):
        stages.append(create_brisque_stage(thresholds))

    # For standard or premium pipeline, add SightEngine
    if pipeline_mode in ["standard", "premium"]:
        # Get API keys from config or key manager
        from ..core.keys.manager import APIKeyManager

        key_manager = APIKeyManager()

        se_user = getattr(config.processing, "sightengine_user", None) or key_manager.get_key(
            "sightengine", "user"
        )
        se_secret = getattr(config.processing, "sightengine_secret", None) or key_manager.get_key(
            "sightengine", "secret"
        )

        if se_user and se_secret:
            stages.append(
                create_sightengine_stage(api_user=se_user, api_secret=se_secret, min_stars=3)
            )
        else:
            logger.warning("SightEngine API keys not found for pipeline")

    # For premium pipeline, add Claude
    if pipeline_mode == "premium":
        from ..core.keys.manager import APIKeyManager

        key_manager = APIKeyManager()

        claude_key = getattr(config.processing, "claude_api_key", None) or key_manager.get_key(
            "claude"
        )

        if claude_key:
            stages.append(
                create_claude_stage(
                    api_key=claude_key, min_stars=4, model="claude-3-haiku-20240307"
                )
            )
        else:
            logger.warning("Claude API key not found for pipeline")

    return stages
