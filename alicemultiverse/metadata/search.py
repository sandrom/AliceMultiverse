"""Search functionality for AI-driven asset discovery."""

import logging
from datetime import datetime

from .models import AssetMetadata, AssetRole, SearchQuery

logger = logging.getLogger(__name__)


class AssetSearchEngine:
    """Search engine for finding assets through metadata."""

    def __init__(self, metadata_store: dict[str, AssetMetadata]):
        """Initialize search engine.

        Args:
            metadata_store: Dictionary mapping asset IDs to metadata
        """
        self.metadata_store = metadata_store
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Build search indexes for efficient querying."""
        # Tag indexes
        self.style_index: dict[str, set[str]] = {}
        self.mood_index: dict[str, set[str]] = {}
        self.subject_index: dict[str, set[str]] = {}
        self.role_index: dict[AssetRole, set[str]] = {}
        self.project_index: dict[str, set[str]] = {}

        # Relationship indexes
        self.parent_index: dict[str, set[str]] = {}
        self.group_index: dict[str, set[str]] = {}

        # Build indexes
        for asset_id, metadata in self.metadata_store.items():
            # Tag indexes
            for tag in metadata.get("style_tags", []):
                self.style_index.setdefault(tag, set()).add(asset_id)

            for tag in metadata.get("mood_tags", []):
                self.mood_index.setdefault(tag, set()).add(asset_id)

            for tag in metadata.get("subject_tags", []):
                self.subject_index.setdefault(tag, set()).add(asset_id)

            # Role index
            role = metadata.get("role")
            if role:
                self.role_index.setdefault(role, set()).add(asset_id)

            # Project index
            project_id = metadata.get("project_id")
            if project_id:
                self.project_index.setdefault(project_id, set()).add(asset_id)

            # Relationship indexes
            parent_id = metadata.get("parent_id")
            if parent_id:
                self.parent_index.setdefault(parent_id, set()).add(asset_id)

    def search_assets(self, query: SearchQuery) -> list[AssetMetadata]:
        """Search for assets matching the query.

        Args:
            query: Search query parameters

        Returns:
            List of matching asset metadata, sorted by relevance
        """
        # Start with all assets
        candidate_ids = set(self.metadata_store.keys())

        # Apply filters progressively
        candidate_ids = self._filter_by_time(candidate_ids, query)
        candidate_ids = self._filter_by_tags(candidate_ids, query)
        candidate_ids = self._filter_by_relationships(candidate_ids, query)
        candidate_ids = self._filter_by_quality(candidate_ids, query)
        candidate_ids = self._filter_by_role_status(candidate_ids, query)
        candidate_ids = self._filter_by_technical(candidate_ids, query)

        # Get metadata for candidates
        results = [self.metadata_store[asset_id] for asset_id in candidate_ids]

        # Sort results
        results = self._sort_results(results, query)

        # Apply limit
        if query.get("limit"):
            results = results[: query["limit"]]

        return results

    def find_similar_assets(
        self, reference_id: str, similarity_threshold: float = 0.7, limit: int = 10
    ) -> list[AssetMetadata]:
        """Find assets similar to a reference asset.

        Args:
            reference_id: ID of reference asset
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum results to return

        Returns:
            List of similar assets sorted by similarity
        """
        if reference_id not in self.metadata_store:
            return []

        reference = self.metadata_store[reference_id]
        similarities = []

        for asset_id, metadata in self.metadata_store.items():
            if asset_id == reference_id:
                continue

            # Calculate similarity score
            score = self._calculate_similarity(reference, metadata)

            if score >= similarity_threshold:
                similarities.append((score, metadata))

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [metadata for _, metadata in similarities[:limit]]

    def search_by_description(self, description: str, limit: int = 20) -> list[AssetMetadata]:
        """Search assets by natural language description.

        Args:
            description: Natural language search query
            limit: Maximum results to return

        Returns:
            List of matching assets
        """
        # Extract keywords from description
        keywords = set(description.lower().split())

        # Remove common words
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "about",
        }
        keywords = keywords - stopwords

        # Score each asset by keyword matches
        scores = []

        for asset_id, metadata in self.metadata_store.items():
            score = 0

            # Check prompt
            prompt = (metadata.get("prompt") or "").lower()
            for keyword in keywords:
                if keyword in prompt:
                    score += 2  # Prompt matches are weighted higher

            # Check tags
            all_tags = (
                metadata.get("style_tags", [])
                + metadata.get("mood_tags", [])
                + metadata.get("subject_tags", [])
                + metadata.get("custom_tags", [])
            )

            for tag in all_tags:
                if tag.lower() in keywords:
                    score += 1

            # Check description and notes
            desc = (metadata.get("description") or "").lower()
            notes = (metadata.get("notes") or "").lower()

            for keyword in keywords:
                if keyword in desc:
                    score += 1
                if keyword in notes:
                    score += 0.5

            if score > 0:
                scores.append((score, metadata))

        # Sort by score and return top results
        scores.sort(key=lambda x: x[0], reverse=True)
        return [metadata for _, metadata in scores[:limit]]

    def _filter_by_time(self, candidates: set[str], query: SearchQuery) -> set[str]:
        """Filter candidates by time constraints."""
        if not any(
            [
                query.get("timeframe_start"),
                query.get("timeframe_end"),
                query.get("created_in_phase"),
            ]
        ):
            return candidates

        filtered = set()

        for asset_id in candidates:
            metadata = self.metadata_store[asset_id]
            created_at = metadata.get("created_at")

            if not created_at:
                continue

            # Check timeframe
            if query.get("timeframe_start") and created_at < query["timeframe_start"]:
                continue

            if query.get("timeframe_end") and created_at > query["timeframe_end"]:
                continue

            # Check phase
            if query.get("created_in_phase"):
                if metadata.get("project_phase") != query["created_in_phase"]:
                    continue

            filtered.add(asset_id)

        return filtered

    def _filter_by_tags(self, candidates: set[str], query: SearchQuery) -> set[str]:
        """Filter candidates by tag constraints."""
        # Get assets matching specific tag types
        tag_sets = []

        if query.get("style_tags"):
            style_matches = set()
            for tag in query["style_tags"]:
                style_matches.update(self.style_index.get(tag, set()))
            tag_sets.append(style_matches)

        if query.get("mood_tags"):
            mood_matches = set()
            for tag in query["mood_tags"]:
                mood_matches.update(self.mood_index.get(tag, set()))
            tag_sets.append(mood_matches)

        if query.get("subject_tags"):
            subject_matches = set()
            for tag in query["subject_tags"]:
                subject_matches.update(self.subject_index.get(tag, set()))
            tag_sets.append(subject_matches)

        # Intersect with candidates
        if tag_sets:
            # Assets must match at least one tag from each category
            filtered = candidates
            for tag_set in tag_sets:
                filtered = filtered.intersection(tag_set)
            candidates = filtered

        # Handle any_tags (OR logic)
        if query.get("any_tags"):
            any_matches = set()
            for asset_id in candidates:
                metadata = self.metadata_store[asset_id]
                all_tags = (
                    metadata.get("style_tags", [])
                    + metadata.get("mood_tags", [])
                    + metadata.get("subject_tags", [])
                    + metadata.get("custom_tags", [])
                )
                if any(tag in all_tags for tag in query["any_tags"]):
                    any_matches.add(asset_id)
            candidates = candidates.intersection(any_matches)

        # Handle all_tags (AND logic)
        if query.get("all_tags"):
            all_matches = set()
            for asset_id in candidates:
                metadata = self.metadata_store[asset_id]
                all_tags = set(
                    metadata.get("style_tags", [])
                    + metadata.get("mood_tags", [])
                    + metadata.get("subject_tags", [])
                    + metadata.get("custom_tags", [])
                )
                if all(tag in all_tags for tag in query["all_tags"]):
                    all_matches.add(asset_id)
            candidates = candidates.intersection(all_matches)

        return candidates

    def _filter_by_relationships(self, candidates: set[str], query: SearchQuery) -> set[str]:
        """Filter by relationship constraints."""
        if query.get("variations_of"):
            # Get all variations of the specified asset
            parent_id = query["variations_of"]
            variations = self.parent_index.get(parent_id, set())
            candidates = candidates.intersection(variations)

        if query.get("similar_to"):
            # Get similar assets
            reference_id = query["similar_to"]
            if reference_id in self.metadata_store:
                reference = self.metadata_store[reference_id]
                similar_ids = set(reference.get("similar_to", []))
                candidates = candidates.intersection(similar_ids)

        if query.get("in_group"):
            # Get assets in the same group
            group_match = set()
            for asset_id in candidates:
                metadata = self.metadata_store[asset_id]
                if query["in_group"] in metadata.get("grouped_with", []):
                    group_match.add(asset_id)
            candidates = candidates.intersection(group_match)

        return candidates

    def _filter_by_quality(self, candidates: set[str], query: SearchQuery) -> set[str]:
        """Filter by quality constraints."""
        filtered = set()

        for asset_id in candidates:
            metadata = self.metadata_store[asset_id]

            # Check quality score
            if query.get("min_quality_score") is not None:
                score = metadata.get("quality_score")
                if score is None or score < query["min_quality_score"]:
                    continue

            # Check star rating
            if query.get("min_stars") is not None:
                stars = metadata.get("quality_stars")
                if stars is None or stars < query["min_stars"]:
                    continue

            # Check defects
            if query.get("exclude_defects"):
                if metadata.get("ai_defects"):
                    continue

            filtered.add(asset_id)

        return filtered

    def _filter_by_role_status(self, candidates: set[str], query: SearchQuery) -> set[str]:
        """Filter by role and status constraints."""
        # Filter by roles
        if query.get("roles"):
            role_matches = set()
            for role in query["roles"]:
                role_matches.update(self.role_index.get(role, set()))
            candidates = candidates.intersection(role_matches)

        # Filter by approval status
        if query.get("approved_only"):
            approved = set()
            for asset_id in candidates:
                if self.metadata_store[asset_id].get("approved"):
                    approved.add(asset_id)
            candidates = approved

        # Exclude archived
        if query.get("exclude_archived", True):
            active = set()
            for asset_id in candidates:
                if self.metadata_store[asset_id].get("role") != AssetRole.ARCHIVED:
                    active.add(asset_id)
            candidates = active

        return candidates

    def _filter_by_technical(self, candidates: set[str], query: SearchQuery) -> set[str]:
        """Filter by technical constraints."""
        filtered = set()

        for asset_id in candidates:
            metadata = self.metadata_store[asset_id]

            # Check source types
            if query.get("source_types"):
                if metadata.get("source_type") not in query["source_types"]:
                    continue

            # Check mime types
            if query.get("mime_types"):
                if metadata.get("mime_type") not in query["mime_types"]:
                    continue

            filtered.add(asset_id)

        return filtered

    def _calculate_similarity(self, ref: AssetMetadata, other: AssetMetadata) -> float:
        """Calculate similarity score between two assets."""
        score = 0.0
        weights = {
            "style": 0.3,
            "mood": 0.2,
            "subject": 0.2,
            "source": 0.1,
            "quality": 0.1,
            "project": 0.1,
        }

        # Style similarity
        ref_styles = set(ref.get("style_tags", []))
        other_styles = set(other.get("style_tags", []))
        if ref_styles and other_styles:
            style_sim = len(ref_styles & other_styles) / len(ref_styles | other_styles)
            score += weights["style"] * style_sim

        # Mood similarity
        ref_moods = set(ref.get("mood_tags", []))
        other_moods = set(other.get("mood_tags", []))
        if ref_moods and other_moods:
            mood_sim = len(ref_moods & other_moods) / len(ref_moods | other_moods)
            score += weights["mood"] * mood_sim

        # Subject similarity
        ref_subjects = set(ref.get("subject_tags", []))
        other_subjects = set(other.get("subject_tags", []))
        if ref_subjects and other_subjects:
            subject_sim = len(ref_subjects & other_subjects) / len(ref_subjects | other_subjects)
            score += weights["subject"] * subject_sim

        # Same source type
        if ref.get("source_type") == other.get("source_type"):
            score += weights["source"]

        # Similar quality
        ref_quality = ref.get("quality_stars", 0)
        other_quality = other.get("quality_stars", 0)
        if ref_quality and other_quality:
            quality_diff = abs(ref_quality - other_quality)
            quality_sim = 1.0 - (quality_diff / 5.0)
            score += weights["quality"] * quality_sim

        # Same project
        if ref.get("project_id") == other.get("project_id"):
            score += weights["project"]

        return score

    def _sort_results(
        self, results: list[AssetMetadata], query: SearchQuery
    ) -> list[AssetMetadata]:
        """Sort results based on query preferences."""
        sort_by = query.get("sort_by", "relevance")

        if sort_by == "created":
            results.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        elif sort_by == "quality":
            results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        # For 'relevance', maintain the order from filtering/scoring

        return results
