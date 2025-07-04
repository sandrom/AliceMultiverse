"""New unified DuckDB implementation composed of modular components.

This module provides the same interface as the original unified_duckdb.py
but uses the new modular architecture for better maintainability.
"""

from pathlib import Path
from typing import Any

from .duckdb_analytics import DuckDBAnalytics
from .duckdb_maintenance import DuckDBMaintenance
from .duckdb_search import DuckDBSearch
from .duckdb_similarity import DuckDBSimilarity
from .duckdb_storage import DuckDBStorage


class UnifiedDuckDBStorage(
    DuckDBStorage,
    DuckDBSearch,
    DuckDBAnalytics,
    DuckDBSimilarity,
    DuckDBMaintenance
):
    """Unified DuckDB storage combining all functionality.

    This class inherits from all the modular components to provide
    the complete unified interface while keeping the code organized.
    """

    def __init__(self, db_path: Path | None = None, read_only: bool = False):
        """Initialize unified DuckDB storage.

        Args:
            db_path: Path to DuckDB database file. If None, uses in-memory database.
            read_only: Open database in read-only mode (better for concurrent reads)
        """
        # Initialize base class which handles connection and schema
        super().__init__(db_path, read_only)

    def clear_index(self) -> None:
        """Clear all data from the index (backward compatibility)."""
        self.rebuild_from_scratch()


class DuckDBSearchCache(UnifiedDuckDBStorage):
    """Backward compatibility class for DuckDBSearchCache.

    This is now just an alias for UnifiedDuckDBStorage.
    """

    def get_connection(self):
        """Get the database connection (backward compatibility)."""
        return self.conn


# TODO: Review unreachable code - class DuckDBSearch(UnifiedDuckDBStorage):
# TODO: Review unreachable code - """Backward compatibility class for standalone DuckDBSearch.

# TODO: Review unreachable code - This is now just an alias for UnifiedDuckDBStorage.
# TODO: Review unreachable code - """

# TODO: Review unreachable code - def index_asset(self, metadata: dict[str, Any]) -> None:
# TODO: Review unreachable code - """Index an asset (backward compatibility method).

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - metadata: Asset metadata including content_hash and file_path
# TODO: Review unreachable code - """
# TODO: Review unreachable code - content_hash = metadata.get("content_hash")
# TODO: Review unreachable code - file_path = metadata.get("file_path")

# TODO: Review unreachable code - if not content_hash or not file_path:
# TODO: Review unreachable code - raise ValueError("content_hash and file_path are required")

# TODO: Review unreachable code - self.upsert_asset(content_hash, file_path, metadata)
