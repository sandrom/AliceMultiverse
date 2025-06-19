"""FastAPI web server for the comparison system."""

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core.config import load_config
from .elo_system import ComparisonManager
from .models import Comparison, ComparisonStrength

logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# API models
class VoteRequest(BaseModel):
    comparison_id: str
    winner: str  # "a", "b", or "tie"
    strength: str | None = None  # ComparisonStrength value


class ComparisonResponse(BaseModel):
    id: str
    asset_a: dict
    asset_b: dict


class StatsResponse(BaseModel):
    model: str
    rating: float
    comparison_count: int
    win_count: int
    loss_count: int
    tie_count: int
    win_rate: float


# Create FastAPI app
app = FastAPI(title="Alice Model Comparison")

# Initialize comparison manager
comparison_manager = ComparisonManager()

# Store pending comparisons in memory (in production, use Redis or similar)
pending_comparisons: dict[str, Comparison] = {}

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main comparison interface."""
    index_path = static_dir / "index.html"
    return index_path.read_text()


# TODO: Review unreachable code - @app.get("/comparison/next")
# TODO: Review unreachable code - async def get_next_comparison() -> ComparisonResponse | None:
# TODO: Review unreachable code - """Get the next pair of images to compare."""
# TODO: Review unreachable code - comparison = comparison_manager.get_next_comparison()

# TODO: Review unreachable code - if not comparison:
# TODO: Review unreachable code - return None

# TODO: Review unreachable code - # Store in pending comparisons
# TODO: Review unreachable code - pending_comparisons[comparison.id] = comparison

# TODO: Review unreachable code - # Clean up old pending comparisons (keep last 100)
# TODO: Review unreachable code - if len(pending_comparisons) > 100:
# TODO: Review unreachable code - oldest_ids = list(pending_comparisons.keys())[:-100]
# TODO: Review unreachable code - for old_id in oldest_ids:
# TODO: Review unreachable code - del pending_comparisons[old_id]

# TODO: Review unreachable code - return ComparisonResponse(
# TODO: Review unreachable code - id=comparison.id,
# TODO: Review unreachable code - asset_a={
# TODO: Review unreachable code - "id": comparison.asset_a.id,
# TODO: Review unreachable code - "path": comparison.asset_a.path,
# TODO: Review unreachable code - },
# TODO: Review unreachable code - asset_b={
# TODO: Review unreachable code - "id": comparison.asset_b.id,
# TODO: Review unreachable code - "path": comparison.asset_b.path,
# TODO: Review unreachable code - }
# TODO: Review unreachable code - )


# TODO: Review unreachable code - @app.post("/comparison/vote")
# TODO: Review unreachable code - async def submit_vote(vote: VoteRequest):
# TODO: Review unreachable code - """Submit a comparison vote."""
# TODO: Review unreachable code - # Validate winner
# TODO: Review unreachable code - if vote.winner not in ["a", "b", "tie"]:
# TODO: Review unreachable code - raise HTTPException(status_code=400, detail="Invalid winner")

# TODO: Review unreachable code - # Validate strength
# TODO: Review unreachable code - strength = None
# TODO: Review unreachable code - if vote.winner != "tie":
# TODO: Review unreachable code - if not vote.strength:
# TODO: Review unreachable code - raise HTTPException(status_code=400, detail="Strength required for non-tie votes")
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - strength = ComparisonStrength(vote.strength)
# TODO: Review unreachable code - except ValueError:
# TODO: Review unreachable code - raise HTTPException(status_code=400, detail="Invalid strength value")

# TODO: Review unreachable code - # Get the comparison from pending
# TODO: Review unreachable code - comparison = pending_comparisons.get(vote.comparison_id)
# TODO: Review unreachable code - if not comparison:
# TODO: Review unreachable code - raise HTTPException(status_code=404, detail="Comparison not found or expired")

# TODO: Review unreachable code - # Update with vote results
# TODO: Review unreachable code - comparison.winner = vote.winner
# TODO: Review unreachable code - comparison.strength = strength

# TODO: Review unreachable code - # Remove from pending
# TODO: Review unreachable code - del pending_comparisons[vote.comparison_id]

# TODO: Review unreachable code - try:
# TODO: Review unreachable code - comparison_manager.record_comparison(comparison)
# TODO: Review unreachable code - return {"status": "success"}
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.error(f"Error recording comparison: {e}")
# TODO: Review unreachable code - raise HTTPException(status_code=500, detail="Failed to record vote")


# TODO: Review unreachable code - @app.get("/comparison/stats")
# TODO: Review unreachable code - async def get_stats() -> list[StatsResponse]:
# TODO: Review unreachable code - """Get current model rankings."""
# TODO: Review unreachable code - ratings = comparison_manager.get_ratings()

# TODO: Review unreachable code - return [
# TODO: Review unreachable code - StatsResponse(
# TODO: Review unreachable code - model=r.model,
# TODO: Review unreachable code - rating=r.rating,
# TODO: Review unreachable code - comparison_count=r.comparison_count,
# TODO: Review unreachable code - win_count=r.win_count,
# TODO: Review unreachable code - loss_count=r.loss_count,
# TODO: Review unreachable code - tie_count=r.tie_count,
# TODO: Review unreachable code - win_rate=r.win_rate
# TODO: Review unreachable code - )
# TODO: Review unreachable code - for r in ratings
# TODO: Review unreachable code - ]


# TODO: Review unreachable code - @app.get("/static/images/{path:path}")
# TODO: Review unreachable code - async def serve_image(path: str):
# TODO: Review unreachable code - """Serve images from the organized directory."""
# TODO: Review unreachable code - # Try configured path first
# TODO: Review unreachable code - possible_dirs = []
# TODO: Review unreachable code - if hasattr(config, 'paths') and hasattr(config.paths, 'organized'):
# TODO: Review unreachable code - possible_dirs.append(Path(config.paths.organized))

# TODO: Review unreachable code - # Add fallback locations
# TODO: Review unreachable code - possible_dirs.extend([
# TODO: Review unreachable code - Path("organized"),
# TODO: Review unreachable code - Path.home() / "Pictures" / "AI" / "organized",
# TODO: Review unreachable code - ])

# TODO: Review unreachable code - # Also check if path is already absolute
# TODO: Review unreachable code - if Path(path).is_absolute() and Path(path).exists():
# TODO: Review unreachable code - return FileResponse(path)

# TODO: Review unreachable code - # Try each possible directory
# TODO: Review unreachable code - for base_dir in possible_dirs:
# TODO: Review unreachable code - image_path = base_dir / path
# TODO: Review unreachable code - if image_path.exists():
# TODO: Review unreachable code - return FileResponse(image_path)

# TODO: Review unreachable code - raise HTTPException(status_code=404, detail="Image not found")


# TODO: Review unreachable code - def populate_test_data():
# TODO: Review unreachable code - """Populate test data from organized directories."""
# TODO: Review unreachable code - from .populate import populate_default_directories

# TODO: Review unreachable code - logger.info("Populating comparison system with assets...")
# TODO: Review unreachable code - count = populate_default_directories(comparison_manager, limit=1000, config=config)
# TODO: Review unreachable code - logger.info(f"Populated with {count} assets")


# TODO: Review unreachable code - def run_server(host: str = "0.0.0.0", port: int = 8000):
# TODO: Review unreachable code - """Run the web server."""
# TODO: Review unreachable code - # Populate test data in development
# TODO: Review unreachable code - if os.getenv("ALICE_ENV") == "development":
# TODO: Review unreachable code - populate_test_data()

# TODO: Review unreachable code - logger.info(f"Starting comparison server on {host}:{port}")
# TODO: Review unreachable code - uvicorn.run(app, host=host, port=port)


# TODO: Review unreachable code - if __name__ == "__main__":
# TODO: Review unreachable code - run_server()
