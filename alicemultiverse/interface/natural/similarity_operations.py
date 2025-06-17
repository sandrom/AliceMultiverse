"""Similarity operations for natural language interface."""

import logging

logger = logging.getLogger(__name__)


class SimilarityOperationsMixin:
    """Mixin for similarity and analysis operations."""

    # Note: find_similar_assets is already in SearchOperationsMixin
    # This mixin is reserved for future similarity-specific operations
    # such as:
    # - Perceptual hash similarity
    # - Style transfer similarity
    # - Semantic similarity
    # - Color palette similarity
    # etc.
    pass
