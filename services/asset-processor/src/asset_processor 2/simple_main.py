"""Simplified main for testing Kubernetes deployment."""
from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="Asset Processor Service", version="0.1.0")

class HealthResponse(BaseModel):
    status: str
    service: str
    database_connected: bool = False

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="asset-processor",
        database_connected=bool(os.getenv("DATABASE_URL"))
    )

@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    return {"ready": True}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Asset Processor",
        "version": "0.1.0",
        "endpoints": ["/health", "/ready", "/docs"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)