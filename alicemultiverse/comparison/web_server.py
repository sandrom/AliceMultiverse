"""FastAPI web server for the comparison system."""

import os
from pathlib import Path
from typing import Optional, List, Dict
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

from .elo_system import ComparisonManager
from .models import Asset, Comparison, ComparisonStrength
from ..core.config import load_config

logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# API models
class VoteRequest(BaseModel):
    comparison_id: str
    winner: str  # "a", "b", or "tie"
    strength: Optional[str] = None  # ComparisonStrength value


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
pending_comparisons: Dict[str, Comparison] = {}

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main comparison interface."""
    index_path = static_dir / "index.html"
    return index_path.read_text()


@app.get("/comparison/next")
async def get_next_comparison() -> Optional[ComparisonResponse]:
    """Get the next pair of images to compare."""
    comparison = comparison_manager.get_next_comparison()
    
    if not comparison:
        return None
    
    # Store in pending comparisons
    pending_comparisons[comparison.id] = comparison
    
    # Clean up old pending comparisons (keep last 100)
    if len(pending_comparisons) > 100:
        oldest_ids = list(pending_comparisons.keys())[:-100]
        for old_id in oldest_ids:
            del pending_comparisons[old_id]
    
    return ComparisonResponse(
        id=comparison.id,
        asset_a={
            "id": comparison.asset_a.id,
            "path": comparison.asset_a.path,
        },
        asset_b={
            "id": comparison.asset_b.id,
            "path": comparison.asset_b.path,
        }
    )


@app.post("/comparison/vote")
async def submit_vote(vote: VoteRequest):
    """Submit a comparison vote."""
    # Validate winner
    if vote.winner not in ["a", "b", "tie"]:
        raise HTTPException(status_code=400, detail="Invalid winner")
    
    # Validate strength
    strength = None
    if vote.winner != "tie":
        if not vote.strength:
            raise HTTPException(status_code=400, detail="Strength required for non-tie votes")
        try:
            strength = ComparisonStrength(vote.strength)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid strength value")
    
    # Get the comparison from pending
    comparison = pending_comparisons.get(vote.comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found or expired")
    
    # Update with vote results
    comparison.winner = vote.winner
    comparison.strength = strength
    
    # Remove from pending
    del pending_comparisons[vote.comparison_id]
    
    try:
        comparison_manager.record_comparison(comparison)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error recording comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to record vote")


@app.get("/comparison/stats")
async def get_stats() -> List[StatsResponse]:
    """Get current model rankings."""
    ratings = comparison_manager.get_ratings()
    
    return [
        StatsResponse(
            model=r.model,
            rating=r.rating,
            comparison_count=r.comparison_count,
            win_count=r.win_count,
            loss_count=r.loss_count,
            tie_count=r.tie_count,
            win_rate=r.win_rate
        )
        for r in ratings
    ]


@app.get("/static/images/{path:path}")
async def serve_image(path: str):
    """Serve images from the organized directory."""
    # Try configured path first
    possible_dirs = []
    if hasattr(config, 'paths') and hasattr(config.paths, 'organized'):
        possible_dirs.append(Path(config.paths.organized))
    
    # Add fallback locations
    possible_dirs.extend([
        Path("organized"),
        Path.home() / "Pictures" / "AI" / "organized",
    ])
    
    # Also check if path is already absolute
    if Path(path).is_absolute() and Path(path).exists():
        return FileResponse(path)
    
    # Try each possible directory
    for base_dir in possible_dirs:
        image_path = base_dir / path
        if image_path.exists():
            return FileResponse(image_path)
    
    raise HTTPException(status_code=404, detail="Image not found")


def populate_test_data():
    """Populate test data from organized directories."""
    from .populate import populate_default_directories
    
    logger.info("Populating comparison system with assets...")
    count = populate_default_directories(comparison_manager, limit=1000, config=config)
    logger.info(f"Populated with {count} assets")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the web server."""
    # Populate test data in development
    if os.getenv("ALICE_ENV") == "development":
        populate_test_data()
    
    logger.info(f"Starting comparison server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()