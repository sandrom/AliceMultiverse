"""Similarity search functionality for DuckDB storage."""

from typing import Any

from .duckdb_base import DuckDBBase
from ..core.structured_logging import get_logger

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
        
        ref_hash = ref_result[0]
        
        # Find similar hashes
        # DuckDB doesn't have built-in hamming distance, so we use a workaround
        # This gets all hashes and we'll calculate similarity in Python
        query = f"""
            SELECT 
                p.content_hash,
                p.{hash_type} as hash_value,
                a.media_type,
                a.ai_source,
                a.prompt,
                a.created_at,
                a.locations
            FROM perceptual_hashes p
            INNER JOIN assets a ON p.content_hash = a.content_hash
            WHERE p.{hash_type} IS NOT NULL
            AND p.content_hash != ?
        """
        
        results = self.conn.execute(query, [content_hash]).fetchall()
        
        # Calculate similarities
        similar_assets = []
        for row in results:
            other_hash = row[1]
            if not other_hash:
                continue
            
            # Calculate hamming distance
            similarity = self._calculate_hash_similarity(ref_hash, other_hash)
            
            if similarity >= threshold:
                asset = {
                    "content_hash": row[0],
                    "similarity": similarity,
                    "media_type": row[2],
                    "ai_source": row[3],
                    "prompt": row[4],
                    "created_at": row[5],
                    "locations": row[6],
                }
                similar_assets.append(asset)
        
        # Sort by similarity and limit
        similar_assets.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_assets[:limit]

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

    def get_similarity_matrix(
        self,
        content_hashes: list[str],
        hash_type: str = "phash"
    ) -> dict[str, dict[str, float]]:
        """Calculate similarity matrix for a set of images.
        
        Args:
            content_hashes: List of content hashes to compare
            hash_type: Type of hash to use
            
        Returns:
            Dictionary mapping pairs of hashes to similarity scores
        """
        # Get hashes for all requested content
        placeholders = ",".join("?" * len(content_hashes))
        query = f"""
            SELECT content_hash, {hash_type}
            FROM perceptual_hashes
            WHERE content_hash IN ({placeholders})
            AND {hash_type} IS NOT NULL
        """
        
        results = self.conn.execute(query, content_hashes).fetchall()
        
        # Build hash lookup
        hash_lookup = {row[0]: row[1] for row in results}
        
        # Calculate similarities
        matrix = {}
        for i, hash1 in enumerate(content_hashes):
            if hash1 not in hash_lookup:
                continue
            
            matrix[hash1] = {}
            
            for j, hash2 in enumerate(content_hashes):
                if i == j:
                    matrix[hash1][hash2] = 1.0
                    continue
                
                if hash2 not in hash_lookup:
                    continue
                
                similarity = self._calculate_hash_similarity(
                    hash_lookup[hash1],
                    hash_lookup[hash2]
                )
                matrix[hash1][hash2] = similarity
        
        return matrix

    def _calculate_hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two perceptual hashes.
        
        Args:
            hash1: First hash
            hash2: Second hash
            
        Returns:
            Similarity score (0-1)
        """
        if len(hash1) != len(hash2):
            return 0.0
        
        # Convert hex to binary
        try:
            # Remove '0x' prefix if present
            hash1 = hash1.replace("0x", "")
            hash2 = hash2.replace("0x", "")
            
            # Convert to binary
            bin1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
            bin2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)
            
            # Calculate hamming distance
            distance = sum(b1 != b2 for b1, b2 in zip(bin1, bin2))
            
            # Convert to similarity (0-1)
            similarity = 1.0 - (distance / len(bin1))
            
            return similarity
            
        except (ValueError, TypeError):
            logger.warning(f"Invalid hash format: {hash1} or {hash2}")
            return 0.0