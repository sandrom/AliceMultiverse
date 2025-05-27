"""Test helper functions for quality assessment tests."""

from alicemultiverse.quality.brisque import is_available as brisque_available


def get_expected_quality_scores():
    """Get expected quality scores based on whether BRISQUE is available.

    Returns:
        dict: Mapping of image types to (score, stars) tuples
    """
    if brisque_available():
        # Real BRISQUE scores
        return {
            "high_quality": (20.0, 5),
            "medium_quality": (35.0, 4),
            "low_quality": (60.0, 3),
            "default": (90.0, 1),
        }
    else:
        # Compression-based fallback scores
        # Simple test images will have very low bits per pixel
        return {
            "high_quality": (90.0, 1),  # All simple images get same score
            "medium_quality": (90.0, 1),  # from compression fallback
            "low_quality": (90.0, 1),
            "default": (90.0, 1),
        }


def adjust_quality_expectations(test_func):
    """Decorator to adjust quality test expectations based on BRISQUE availability."""

    def wrapper(*args, **kwargs):
        # Inject expected scores into test
        kwargs["expected_scores"] = get_expected_quality_scores()
        return test_func(*args, **kwargs)

    return wrapper
