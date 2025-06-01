"""Test helper functions for understanding system tests."""


def get_expected_understanding_scores():
    """Get expected understanding scores for test images.

    Returns:
        dict: Mapping of image types to expected analysis results
    """
    return {
        "high_quality": {"aesthetic_score": 0.8, "technical_score": 0.9},
        "medium_quality": {"aesthetic_score": 0.6, "technical_score": 0.7},
        "low_quality": {"aesthetic_score": 0.4, "technical_score": 0.5},
        "default": {"aesthetic_score": 0.5, "technical_score": 0.5},
    }


def adjust_understanding_expectations(test_func):
    """Decorator to adjust understanding test expectations."""

    def wrapper(*args, **kwargs):
        # Inject expected scores into test
        kwargs["expected_scores"] = get_expected_understanding_scores()
        return test_func(*args, **kwargs)

    return wrapper
