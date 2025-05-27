"""BRISQUE quality assessment implementation."""

import logging
from pathlib import Path

from PIL import Image

from ..core.constants import BRISQUE_MAX_DIMENSION

logger = logging.getLogger(__name__)

# Try to import BRISQUE implementation
BRISQUE_AVAILABLE = False
brisque_implementation = None
image_quality = None  # For test mocking
pybrisque = None  # For test mocking

try:
    # Prefer image-quality package (better for Apple Silicon)
    import imquality.brisque as brisque_module

    BRISQUE_AVAILABLE = True
    brisque_implementation = "image-quality"
    image_quality = brisque_module  # For test compatibility

    # Patch for scikit-image compatibility
    try:
        import inspect

        from skimage.transform import rescale

        sig = inspect.signature(rescale)
        if "channel_axis" in sig.parameters and "multichannel" not in sig.parameters:
            # Monkey patch for compatibility
            import skimage.transform

            _original_rescale = skimage.transform.rescale

            def patched_rescale(*args, **kwargs):
                if "multichannel" in kwargs:
                    kwargs["channel_axis"] = -1 if kwargs.pop("multichannel") else None
                return _original_rescale(*args, **kwargs)

            skimage.transform.rescale = patched_rescale
            logger.debug("Applied scikit-image compatibility patch")
    except Exception:
        pass

except ImportError:
    try:
        # Fallback to pybrisque
        import pybrisque as pybrisque_module
        from pybrisque import brisque as calculate_brisque_func

        BRISQUE_AVAILABLE = True
        brisque_implementation = "pybrisque"
        pybrisque = pybrisque_module  # For test compatibility
    except ImportError:
        logger.warning("No BRISQUE implementation available")


class BRISQUEAssessor:
    """BRISQUE-based image quality assessment."""

    def __init__(self, thresholds: dict):
        """Initialize BRISQUE assessor.

        Args:
            thresholds: Dictionary mapping star ratings to (min, max) score ranges
        """
        self.thresholds = thresholds

        if not BRISQUE_AVAILABLE:
            logger.warning("BRISQUE not available - quality assessment disabled")

    def assess_quality(self, image_path: Path) -> tuple[float | None, int | None]:
        """Assess image quality using BRISQUE.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (brisque_score, star_rating) or (None, None) if failed
        """
        if not is_available():
            return None, None

        try:
            score = self._calculate_score(image_path)
            if score is None:
                return None, None

            # Clamp score to valid range
            score = max(0, min(100, float(score)))

            # Convert to star rating
            stars = self._score_to_stars(score)

            return score, stars

        except Exception as e:
            logger.error(f"BRISQUE assessment failed for {image_path.name}: {e}")
            return None, None

    def _calculate_score(self, image_path: Path) -> float | None:
        """Calculate BRISQUE score for an image."""
        try:
            # Check which implementation is available dynamically
            if image_quality is not None:
                # Open and prepare image
                img = Image.open(image_path)

                # Convert grayscale/RGBA to RGB
                img = self._prepare_image(img)

                # Resize if too large
                if img.width > BRISQUE_MAX_DIMENSION or img.height > BRISQUE_MAX_DIMENSION:
                    img.thumbnail(
                        (BRISQUE_MAX_DIMENSION, BRISQUE_MAX_DIMENSION), Image.Resampling.LANCZOS
                    )

                return image_quality.score(img)

            elif pybrisque is not None:
                return pybrisque.brisque(str(image_path))

            return None

        except Exception as e:
            # Try fallback compression-based quality estimate
            if "channel_axis" in str(e) or "input array must have size 3" in str(e):
                return self._compression_quality_estimate(image_path)
            raise

    def _prepare_image(self, img: Image.Image) -> Image.Image:
        """Convert image to RGB format for BRISQUE."""
        if img.mode in ("L", "LA", "P"):
            # Convert grayscale/palette to RGB
            return img.convert("RGB")
        elif img.mode == "RGBA":
            # Convert RGBA to RGB with white background
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            return bg
        elif img.mode != "RGB":
            # Convert any other mode to RGB
            return img.convert("RGB")
        return img

    def _compression_quality_estimate(self, image_path: Path) -> float:
        """Estimate quality based on file compression ratio."""
        try:
            img = Image.open(image_path)
            file_size = image_path.stat().st_size
            pixels = img.width * img.height

            # Bits per pixel
            bits_per_pixel = (file_size * 8) / pixels

            # Map to BRISQUE-like score
            if bits_per_pixel > 24:
                return 10.0
            elif bits_per_pixel > 16:
                return 20.0
            elif bits_per_pixel > 8:
                return 35.0
            elif bits_per_pixel > 4:
                return 50.0
            elif bits_per_pixel > 2:
                return 70.0
            else:
                return 90.0

        except Exception as e:
            logger.warning(f"Compression estimate failed: {e}")
            return 50.0  # Default middle score

    def _score_to_stars(self, score: float) -> int:
        """Convert BRISQUE score to star rating."""
        for stars in sorted(self.thresholds.keys(), reverse=True):
            min_score, max_score = self.thresholds[stars]
            if min_score <= score < max_score:
                return stars
        return 1  # Default to 1 star


def is_available() -> bool:
    """Check if BRISQUE quality assessment is available."""
    # Check dynamically to support test mocking
    return (image_quality is not None) or (pybrisque is not None)


# Public convenience functions for testing/compatibility
def calculate_brisque_score(image_path: str) -> float | None:
    """Calculate BRISQUE score for an image.

    Args:
        image_path: Path to the image file

    Returns:
        BRISQUE score or None if assessment fails
    """
    assessor = BRISQUEAssessor({5: (0, 25), 4: (25, 45), 3: (45, 65), 2: (65, 80), 1: (80, 100)})
    score, _ = assessor.assess_quality(Path(image_path))
    return score


def get_quality_rating(score: float | None, config: dict) -> int | None:
    """Get quality rating from BRISQUE score.

    Args:
        score: BRISQUE score
        config: Configuration with quality thresholds

    Returns:
        Star rating (1-5) or None
    """
    if score is None:
        return None

    thresholds = config.get("quality", {}).get("thresholds", {})

    # Convert config format to assessor format
    assessor_thresholds = {}
    for star_key, bounds in thresholds.items():
        stars = int(star_key.split("_")[0])
        assessor_thresholds[stars] = (bounds["min"], bounds["max"])

    assessor = BRISQUEAssessor(assessor_thresholds)
    return assessor._score_to_stars(score)


def ensure_rgb_image(img: Image.Image) -> Image.Image:
    """Ensure image is in RGB format.

    Args:
        img: PIL Image

    Returns:
        RGB image
    """
    assessor = BRISQUEAssessor({})
    return assessor._prepare_image(img)
