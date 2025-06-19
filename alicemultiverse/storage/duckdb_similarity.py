"""Similarity search functionality for DuckDB storage."""

from typing import Any

from ..core.structured_logging import get_logger
from .duckdb_base import DuckDBBase

logger = get_logger(__name__)


class DuckDBSimilarity(DuckDBBase):
    """Similarity search operations using perceptual hashes."""

    def index_perceptual_hashes(
        self,
        content_hash: str,
        phash: str | None = None,
        dhash: str | None = None,
        ahash: str | None = None,
        whash: str | None = None,
        colorhash: str | None = None,
    ) -> None:
        """Index perceptual hashes for an asset.

        Args:
            content_hash: Content hash of the asset
            phash: Perceptual hash
            dhash: Difference hash
            ahash: Average hash
            whash: Wavelet hash
            colorhash: Color hash
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO perceptual_hashes
            (content_hash, phash, dhash, ahash, whash, colorhash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [content_hash, phash, dhash, ahash, whash, colorhash])

        logger.debug(f"Indexed perceptual hashes for {content_hash}")

    def find_similar(
        self,
        content_hash: str,
        threshold: float = 0.9,
        limit: int = 20,
        hash_type: str = "phash"
    ) -> list[dict[str, Any]]:
        """Find similar images using perceptual hashes.

        Args:
            content_hash: Reference image hash
            threshold: Similarity threshold (0-1)
            limit: Maximum results
            hash_type: Type of hash to use (phash, dhash, ahash, whash)

        Returns:
            List of similar assets with similarity scores
        """
        # Get reference hash
        ref_result = self.conn.execute(
            f"SELECT {hash_type} FROM perceptual_hashes WHERE content_hash = ?",
            [content_hash]
        ).fetchone()

        if not ref_result or not ref_result[0]:
            logger.warning(f"No {hash_type} found for {content_hash}")
            return []

        # TODO: Review unreachable code - ref_hash = ref_result[0]

        # TODO: Review unreachable code - # Find similar hashes
        # TODO: Review unreachable code - # DuckDB doesn't have built-in hamming distance, so we use a workaround
        # TODO: Review unreachable code - # This gets all hashes and we'll calculate similarity in Python
        # TODO: Review unreachable code - query = f"""
        # TODO: Review unreachable code - SELECT
        # TODO: Review unreachable code - p.content_hash,
        # TODO: Review unreachable code - p.{hash_type} as hash_value,
        # TODO: Review unreachable code - a.media_type,
        # TODO: Review unreachable code - a.ai_source,
        # TODO: Review unreachable code - a.prompt,
        # TODO: Review unreachable code - a.created_at,
        # TODO: Review unreachable code - a.locations
        # TODO: Review unreachable code - FROM perceptual_hashes p
        # TODO: Review unreachable code - INNER JOIN assets a ON p.content_hash = a.content_hash
        # TODO: Review unreachable code - WHERE p.{hash_type} IS NOT NULL
        # TODO: Review unreachable code - AND p.content_hash != ?
        # TODO: Review unreachable code - """

        # TODO: Review unreachable code - results = self.conn.execute(query, [content_hash]).fetchall()

        # TODO: Review unreachable code - # Calculate similarities
        # TODO: Review unreachable code - similar_assets = []
        # TODO: Review unreachable code - for row in results:
        # TODO: Review unreachable code - other_hash = row[1]
        # TODO: Review unreachable code - if not other_hash:
        # TODO: Review unreachable code - continue

        # TODO: Review unreachable code - # Calculate hamming distance
        # TODO: Review unreachable code - similarity = self._calculate_hash_similarity(ref_hash, other_hash)

        # TODO: Review unreachable code - if similarity >= threshold:
        # TODO: Review unreachable code - asset = {
        # TODO: Review unreachable code - "content_hash": row[0],
        # TODO: Review unreachable code - "similarity": similarity,
        # TODO: Review unreachable code - "media_type": row[2],
        # TODO: Review unreachable code - "ai_source": row[3],
        # TODO: Review unreachable code - "prompt": row[4],
        # TODO: Review unreachable code - "created_at": row[5],
        # TODO: Review unreachable code - "locations": row[6],
        # TODO: Review unreachable code - }
        # TODO: Review unreachable code - similar_assets.append(asset)

        # TODO: Review unreachable code - # Sort by similarity and limit
        # TODO: Review unreachable code - similar_assets.sort(key=lambda x: x["similarity"], reverse=True)
        # TODO: Review unreachable code - return similar_assets[:limit]

    def find_duplicates(
        self,
        hash_types: list[str] | None = None,
        exact_only: bool = False
    ) -> list[list[str]]:
        """Find duplicate images.

        Args:
            hash_types: Hash types to check (default: all)
            exact_only: Only find exact matches

        Returns:
            List of duplicate groups (list of content hashes)
        """
        if not hash_types:
            hash_types = ["phash", "dhash", "ahash"]

        duplicate_groups = []
        processed = set()

        for hash_type in hash_types:
            # Find hashes that appear multiple times
            query = f"""
                SELECT {hash_type}, GROUP_CONCAT(content_hash) as hashes
                FROM perceptual_hashes
                WHERE {hash_type} IS NOT NULL
                GROUP BY {hash_type}
                HAVING COUNT(*) > 1
            """

            duplicates = self.conn.execute(query).fetchall()

            for hash_value, content_hashes in duplicates:
                hashes = content_hashes.split(",")

                # Skip if already processed
                if any(h in processed for h in hashes):
                    continue

                duplicate_groups.append(hashes)
                processed.update(hashes)

        return duplicate_groups

    # TODO: Review unreachable code - def get_similarity_matrix(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - content_hashes: list[str],
    # TODO: Review unreachable code - hash_type: str = "phash"
    # TODO: Review unreachable code - ) -> dict[str, dict[str, float]]:
    # TODO: Review unreachable code - """Calculate similarity matrix for a set of images.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - content_hashes: List of content hashes to compare
    # TODO: Review unreachable code - hash_type: Type of hash to use

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary mapping pairs of hashes to similarity scores
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Get hashes for all requested content
    # TODO: Review unreachable code - placeholders = ",".join("?" * len(content_hashes))
    # TODO: Review unreachable code - query = f"""
    # TODO: Review unreachable code - SELECT content_hash, {hash_type}
    # TODO: Review unreachable code - FROM perceptual_hashes
    # TODO: Review unreachable code - WHERE content_hash IN ({placeholders})
    # TODO: Review unreachable code - AND {hash_type} IS NOT NULL
    # TODO: Review unreachable code - """

    # TODO: Review unreachable code - results = self.conn.execute(query, content_hashes).fetchall()

    # TODO: Review unreachable code - # Build hash lookup
    # TODO: Review unreachable code - hash_lookup = {row[0]: row[1] for row in results}

    # TODO: Review unreachable code - # Calculate similarities
    # TODO: Review unreachable code - matrix = {}
    # TODO: Review unreachable code - for i, hash1 in enumerate(content_hashes):
    # TODO: Review unreachable code - if hash1 not in hash_lookup:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - matrix[hash1] = {}

    # TODO: Review unreachable code - for j, hash2 in enumerate(content_hashes):
    # TODO: Review unreachable code - if i == j:
    # TODO: Review unreachable code - matrix[hash1][hash2] = 1.0
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - if hash2 not in hash_lookup:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - similarity = self._calculate_hash_similarity(
    # TODO: Review unreachable code - hash_lookup[hash1],
    # TODO: Review unreachable code - hash_lookup[hash2]
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - matrix[hash1][hash2] = similarity

    # TODO: Review unreachable code - return matrix

    # TODO: Review unreachable code - def _calculate_hash_similarity(self, hash1: str, hash2: str) -> float:
    # TODO: Review unreachable code - """Calculate similarity between two perceptual hashes.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - hash1: First hash
    # TODO: Review unreachable code - hash2: Second hash

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Similarity score (0-1)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if len(hash1) != len(hash2):
    # TODO: Review unreachable code - return 0.0

    # TODO: Review unreachable code - # Convert hex to binary
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Remove '0x' prefix if present
    # TODO: Review unreachable code - hash1 = hash1.replace("0x", "")
    # TODO: Review unreachable code - hash2 = hash2.replace("0x", "")

    # TODO: Review unreachable code - # Convert to binary
    # TODO: Review unreachable code - bin1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
    # TODO: Review unreachable code - bin2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)

    # TODO: Review unreachable code - # Calculate hamming distance
    # TODO: Review unreachable code - distance = sum(b1 != b2 for b1, b2 in zip(bin1, bin2))

    # TODO: Review unreachable code - # Convert to similarity (0-1)
    # TODO: Review unreachable code - similarity = 1.0 - (distance / len(bin1))

    # TODO: Review unreachable code - return similarity

    # TODO: Review unreachable code - except (ValueError, TypeError):
    # TODO: Review unreachable code - logger.warning(f"Invalid hash format: {hash1} or {hash2}")
    # TODO: Review unreachable code - return 0.0
