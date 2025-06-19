"""MCP tools for advanced deduplication with perceptual hashing."""

import json
from pathlib import Path
from typing import Any

from ..assets.deduplication.duplicate_finder import DuplicateFinder
from ..assets.deduplication.similarity_index import SimilarityIndex
from ..core.structured_logging import get_logger

logger = get_logger(__name__)


async def find_duplicates_advanced(
    paths: list[str] | None = None,
    exact_only: bool = False,
    similarity_threshold: float = 0.9,
    include_videos: bool = True,
    min_file_size: int = 0,
    recursive: bool = True,
    limit: int = 100
) -> dict[str, Any]:
    """Find duplicate and similar images using advanced perceptual hashing.

    Args:
        paths: Directories to search (defaults to configured paths)
        exact_only: Only find exact duplicates (MD5 hash)
        similarity_threshold: Similarity threshold (0.0-1.0) for perceptual matching
        include_videos: Include video files in search
        min_file_size: Minimum file size in bytes to consider
        recursive: Search directories recursively
        limit: Maximum number of duplicate groups to return

    Returns:
        Duplicate groups with similarity scores and recommendations
    """
    try:
        # Use DuplicateFinder for the heavy lifting
        finder = DuplicateFinder()

        # Get paths from config if not provided
        if not paths:
            from ..core.config import load_config
            config = load_config()
            paths = [str(config.paths.organized)]

        # Find duplicates
        if exact_only:
            duplicates = await finder.find_exact_duplicates(
                paths=[Path(p) for p in paths],
                recursive=recursive,
                min_size=min_file_size,
                include_videos=include_videos
            )
        else:
            duplicates = await finder.find_similar_images(
                paths=[Path(p) for p in paths],
                threshold=similarity_threshold,
                recursive=recursive,
                min_size=min_file_size
            )

        # Format results
        duplicate_groups = []
        total_duplicates = 0
        total_wasted_space = 0

        for master, dupes in list(duplicates.items())[:limit]:
            group_size = sum(d["size"] for d in dupes) + Path(master).stat().st_size
            wasted_space = sum(d["size"] for d in dupes)
            total_wasted_space += wasted_space
            total_duplicates += len(dupes)

            duplicate_groups.append({
                "master": str(master),
                "master_size": Path(master).stat().st_size,
                "duplicates": [
                    {
                        "path": d["path"],
                        "size": d["size"],
                        "similarity": d.get("similarity", 1.0)
                    }
                    for d in dupes
                ],
                "total_size": group_size,
                "wasted_space": wasted_space,
                "recommendation": _get_dedup_recommendation(master, dupes)
            })

        return {
            "success": True,
            "message": f"Found {len(duplicate_groups)} duplicate groups",
            "data": {
                "duplicate_groups": duplicate_groups,
                "summary": {
                    "total_groups": len(duplicates),
                    "total_duplicates": total_duplicates,
                    "total_wasted_space": total_wasted_space,
                    "total_wasted_space_mb": round(total_wasted_space / (1024 * 1024), 2),
                    "search_type": "exact" if exact_only else "perceptual",
                    "similarity_threshold": similarity_threshold if not exact_only else None
                }
            }
        }

    except Exception as e:
        logger.error(f"Failed to find duplicates: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to find duplicates"
        }


async def remove_duplicates(
    duplicate_groups: list[dict[str, Any]] | None = None,
    strategy: str = "keep_organized",
    backup: bool = True,
    dry_run: bool = True,
    use_hardlinks: bool = False
) -> dict[str, Any]:
    """Remove duplicate files with various strategies.

    Args:
        duplicate_groups: Groups from find_duplicates_advanced (if None, finds them first)
        strategy: Removal strategy - keep_organized, keep_largest, keep_newest, interactive
        backup: Create backup before removal
        dry_run: Preview what would be removed without actually removing
        use_hardlinks: Use hardlinks instead of deletion to save space

    Returns:
        Removal results with space saved
    """
    try:
        finder = DuplicateFinder()

        # If no groups provided, find them first
        if not duplicate_groups:
            result = await find_duplicates_advanced(exact_only=False)
            if not result["success"]:
                return result
            # TODO: Review unreachable code - duplicate_groups = result["data"]["duplicate_groups"]

        # Convert to format expected by DuplicateFinder
        duplicates_dict = {}
        for group in duplicate_groups:
            master = group["master"]
            dupes = [
                {
                    "path": d["path"],
                    "size": d["size"],
                    "similarity": d.get("similarity", 1.0)
                }
                for d in group["duplicates"]
            ]
            duplicates_dict[master] = dupes

        # Remove duplicates
        removed, saved_space = await finder.remove_duplicates(
            duplicates_dict,
            strategy=strategy,
            backup=backup,
            dry_run=dry_run,
            use_hardlinks=use_hardlinks
        )

        return {
            "success": True,
            "message": f"{'Would remove' if dry_run else 'Removed'} {len(removed)} duplicate files",
            "data": {
                "removed_files": removed,
                "space_saved": saved_space,
                "space_saved_mb": round(saved_space / (1024 * 1024), 2),
                "strategy": strategy,
                "dry_run": dry_run,
                "backup_created": backup and not dry_run
            }
        }

    except Exception as e:
        logger.error(f"Failed to remove duplicates: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to remove duplicates"
        }


async def build_similarity_index(
    paths: list[str] | None = None,
    index_type: str = "flat",
    force_rebuild: bool = False,
    include_videos: bool = False
) -> dict[str, Any]:
    """Build a similarity search index for fast duplicate/similar image detection.

    Args:
        paths: Directories to index (defaults to configured paths)
        index_type: Index type - flat, ivf, hnsw
        force_rebuild: Force rebuild even if index exists
        include_videos: Include video keyframes in index

    Returns:
        Index build results with statistics
    """
    try:
        # Initialize similarity index
        index = SimilarityIndex(index_type=index_type)

        # Get paths from config if not provided
        if not paths:
            from ..core.config import load_config
            config = load_config()
            paths = [str(config.paths.organized)]

        # Check if index exists and force_rebuild not set
        if index.index_exists() and not force_rebuild:
            return {
                "success": True,
                "message": "Similarity index already exists",
                "data": {
                    "index_path": str(index.index_path),
                    "index_type": index_type,
                    "status": "exists",
                    "recommendation": "Use force_rebuild=True to rebuild"
                }
            }

        # Build index
        image_paths = []
        for path in paths:
            p = Path(path)
            if p.is_dir():
                patterns = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.heic", "*.heif"]
                if include_videos:
                    patterns.extend(["*.mp4", "*.mov", "*.avi"])

                for pattern in patterns:
                    image_paths.extend(p.rglob(pattern))

        logger.info(f"Building similarity index for {len(image_paths)} files")

        # Add images to index
        for img_path in image_paths:
            try:
                await index.add_image(img_path)
            except Exception as e:
                logger.warning(f"Failed to index {img_path}: {e}")

        # Save index
        index.save_index()

        return {
            "success": True,
            "message": f"Built similarity index for {len(image_paths)} files",
            "data": {
                "index_path": str(index.index_path),
                "index_type": index_type,
                "total_files": len(image_paths),
                "index_size": index.index.ntotal if hasattr(index.index, 'ntotal') else 0,
                "status": "built"
            }
        }

    except Exception as e:
        logger.error(f"Failed to build similarity index: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to build similarity index"
        }


async def find_similar_images(
    image_path: str,
    count: int = 10,
    similarity_threshold: float = 0.8,
    use_index: bool = True
) -> dict[str, Any]:
    """Find images similar to a given image using perceptual hashing.

    Args:
        image_path: Path to the query image
        count: Number of similar images to return
        similarity_threshold: Minimum similarity score (0.0-1.0)
        use_index: Use similarity index if available

    Returns:
        Similar images with similarity scores
    """
    try:
        query_path = Path(image_path)
        if not query_path.exists():
            return {
                "success": False,
                "error": "Image not found",
                "message": f"Image not found: {image_path}"
            }

        if use_index:
            # Try to use similarity index
            index = SimilarityIndex()
            if index.index_exists():
                index.load_index()
                similar = await index.find_similar(query_path, k=count)

                # Filter by threshold
                filtered = [
                    {
                        "path": str(s["path"]),
                        "similarity": s["similarity"],
                        "distance": s["distance"]
                    }
                    for s in similar
                    if s is not None and s["similarity"] >= similarity_threshold
                ]

                return {
                    "success": True,
                    "message": f"Found {len(filtered)} similar images",
                    "data": {
                        "query_image": str(query_path),
                        "similar_images": filtered,
                        "method": "index_search",
                        "threshold": similarity_threshold
                    }
                }

        # Fallback to direct search
        from ..assets.deduplication.perceptual_hasher import PerceptualHasher
        hasher = PerceptualHasher()

        # Get query image hashes
        await hasher.compute_all_hashes(query_path)
        hasher.extract_visual_features(query_path)

        # Search through all images
        from ..core.config import load_config
        config = load_config()
        search_path = Path(config.paths.organized)

        results = []
        for img_path in search_path.rglob("*.jpg"):
            if img_path == query_path:
                continue

            try:
                # Compute similarity
                similarity = await hasher.compute_similarity(query_path, img_path)
                if similarity >= similarity_threshold:
                    results.append({
                        "path": str(img_path),
                        "similarity": similarity
                    })
            except Exception as e:
                logger.debug(f"Failed to compare with {img_path}: {e}")

        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "success": True,
            "message": f"Found {len(results[:count])} similar images",
            "data": {
                "query_image": str(query_path),
                "similar_images": results[:count],
                "method": "direct_search",
                "threshold": similarity_threshold
            }
        }

    except Exception as e:
        logger.error(f"Failed to find similar images: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to find similar images"
        }


async def get_deduplication_report(
    paths: list[str] | None = None,
    include_recommendations: bool = True,
    export_path: str | None = None
) -> dict[str, Any]:
    """Generate a comprehensive deduplication report.

    Args:
        paths: Directories to analyze (defaults to configured paths)
        include_recommendations: Include removal recommendations
        export_path: Export report to JSON file

    Returns:
        Comprehensive deduplication analysis
    """
    try:
        # Find all duplicates
        exact_result = await find_duplicates_advanced(
            paths=paths,
            exact_only=True,
            limit=1000
        )

        similar_result = await find_duplicates_advanced(
            paths=paths,
            exact_only=False,
            similarity_threshold=0.95,
            limit=1000
        )

        # Build report
        report = {
            "exact_duplicates": {
                "total_groups": exact_result["data"]["summary"]["total_groups"],
                "total_files": exact_result["data"]["summary"]["total_duplicates"],
                "wasted_space_mb": exact_result["data"]["summary"]["total_wasted_space_mb"]
            },
            "similar_images": {
                "total_groups": similar_result["data"]["summary"]["total_groups"],
                "total_files": similar_result["data"]["summary"]["total_duplicates"],
                "wasted_space_mb": similar_result["data"]["summary"]["total_wasted_space_mb"],
                "threshold": similar_result["data"]["summary"]["similarity_threshold"]
            },
            "total_potential_savings_mb": (
                exact_result["data"]["summary"]["total_wasted_space_mb"] +
                similar_result["data"]["summary"]["total_wasted_space_mb"]
            )
        }

        if include_recommendations:
            if report is not None:
                report["recommendations"] = _get_deduplication_recommendations(
                exact_result["data"]["duplicate_groups"],
                similar_result["data"]["duplicate_groups"]
            )

        # Export if requested
        if export_path:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            full_report = {
                "summary": report,
                "exact_duplicates": exact_result["data"]["duplicate_groups"][:50],
                "similar_images": similar_result["data"]["duplicate_groups"][:50]
            }

            with open(export_file, 'w') as f:
                json.dump(full_report, f, indent=2)

            if report is not None:
                report["export_path"] = str(export_file)

        return {
            "success": True,
            "message": "Deduplication report generated",
            "data": report
        }

    except Exception as e:
        logger.error(f"Failed to generate deduplication report: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate deduplication report"
        }


def _get_dedup_recommendation(master: str, duplicates: list[dict[str, Any]]) -> str:
    """Get deduplication recommendation for a group."""
    if all(d.get("similarity", 1.0) == 1.0 for d in duplicates):
        return "Safe to remove - exact duplicates"

    # TODO: Review unreachable code - avg_similarity = sum(d.get("similarity", 1.0) for d in duplicates) / len(duplicates)
    # TODO: Review unreachable code - if avg_similarity > 0.98:
    # TODO: Review unreachable code - return "Likely safe to remove - nearly identical"
    # TODO: Review unreachable code - elif avg_similarity > 0.95:
    # TODO: Review unreachable code - return "Review recommended - very similar but not identical"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - return "Manual review required - moderately similar"


def _get_deduplication_recommendations(
    exact_groups: list[dict[str, Any]],
    similar_groups: list[dict[str, Any]]
) -> dict[str, Any]:
    """Generate deduplication recommendations."""
    return {
        "immediate_action": {
            "description": "Exact duplicates safe to remove",
            "count": len(exact_groups),
            "space_savings_mb": sum(g["wasted_space"] for g in exact_groups) / (1024 * 1024)
        },
        "review_recommended": {
            "description": "Very similar images that may be duplicates",
            "count": sum(1 for g in similar_groups if any(
                d["similarity"] > 0.95 for d in g["duplicates"]
            )),
            "space_savings_mb": sum(
                g["wasted_space"] for g in similar_groups
                if any(d["similarity"] > 0.95 for d in g["duplicates"])
            ) / (1024 * 1024)
        },
        "strategy": {
            "recommended": "keep_organized",
            "reason": "Preserves your organized structure while removing duplicates from inbox"
        }
    }


def register_deduplication_tools(server) -> None:
    """Register deduplication tools with MCP server.

    Args:
        server: MCP server instance
    """

    # Register each deduplication function as a tool
    server.tool()(find_duplicates_advanced)
    server.tool()(remove_duplicates)
    server.tool()(build_similarity_index)
    server.tool()(find_similar_images)
    server.tool()(get_deduplication_report)
