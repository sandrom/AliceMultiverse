"""Main entry point for the Asset Processor service."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from alice_config import get_config
from alice_events import (
    AssetDiscoveredEvent,
    AssetProcessedEvent,
    QualityAssessedEvent,
    AssetOrganizedEvent,
    publish_event,
    EventSubscriber,
    global_event_bus
)

from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    QualityAssessRequest,
    QualityAssessResponse,
    OrganizePlanRequest,
    OrganizePlanResponse
)
from .analyzer import AssetAnalyzer
from .quality import QualityPipeline
from .organizer import AssetOrganizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Asset Processor Service",
    description="Media processing and organization service for AliceMultiverse",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
config = get_config()
analyzer = AssetAnalyzer()
quality_pipeline = QualityPipeline()
organizer = AssetOrganizer()


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info("Starting Asset Processor service")
    
    # Subscribe to relevant events
    class AssetEventHandler(EventSubscriber):
        @property
        def event_types(self) -> list[str]:
            return ["asset.discovered"]
        
        async def handle_event(self, event):
            if event.event_type == "asset.discovered":
                # Process discovered assets
                logger.info(f"Processing discovered asset: {event.file_path}")
                # TODO: Queue for processing
    
    handler = AssetEventHandler()
    global_event_bus.subscribe(handler)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "asset-processor",
        "version": "0.1.0"
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_asset(request: AnalyzeRequest):
    """Analyze a media file and extract all metadata."""
    try:
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Analyze the asset
        result = await analyzer.analyze(file_path)
        
        # Publish event
        await publish_event(AssetProcessedEvent(
            content_hash=result.content_hash,
            file_path=str(file_path),
            metadata=result.metadata,
            extracted_metadata=result.extracted_metadata,
            generation_params=result.generation_params
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quality/assess", response_model=QualityAssessResponse)
async def assess_quality(request: QualityAssessRequest):
    """Run quality assessment pipeline on an asset."""
    try:
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Run quality assessment
        result = await quality_pipeline.assess(
            file_path,
            content_hash=request.content_hash,
            pipeline_mode=request.pipeline_mode
        )
        
        # Publish event
        await publish_event(QualityAssessedEvent(
            content_hash=request.content_hash,
            file_path=str(file_path),
            star_rating=result.star_rating,
            combined_score=result.combined_score,
            brisque_score=result.brisque_score,
            pipeline_mode=request.pipeline_mode
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error assessing quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/organize/plan", response_model=OrganizePlanResponse)
async def plan_organization(request: OrganizePlanRequest):
    """Generate organization plan without moving files."""
    try:
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate organization plan
        result = await organizer.plan_organization(
            file_path,
            content_hash=request.content_hash,
            metadata=request.metadata,
            quality_rating=request.quality_rating
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error planning organization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/batch")
async def process_batch(file_paths: list[str]):
    """Process multiple files in batch."""
    results = []
    
    for file_path in file_paths:
        try:
            # Analyze
            analysis = await analyzer.analyze(Path(file_path))
            
            # Assess quality if image
            quality = None
            if analysis.media_type == "image":
                quality = await quality_pipeline.assess(
                    Path(file_path),
                    analysis.content_hash
                )
            
            # Plan organization
            organization = await organizer.plan_organization(
                Path(file_path),
                analysis.content_hash,
                analysis.metadata,
                quality.star_rating if quality else None
            )
            
            results.append({
                "file_path": file_path,
                "status": "success",
                "analysis": analysis,
                "quality": quality,
                "organization": organization
            })
            
        except Exception as e:
            results.append({
                "file_path": file_path,
                "status": "error",
                "error": str(e)
            })
    
    return {"results": results}


def main():
    """Run the service."""
    port = config.get("services.asset_processor.port", 8001)
    uvicorn.run(
        "asset_processor.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )


if __name__ == "__main__":
    main()