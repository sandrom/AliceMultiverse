"""Mobile companion server for timeline control and preview."""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import json
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .token_manager import TokenManager
from ..interface.timeline_preview import Timeline, TimelineClip

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


class MobileServer:
    """Server for mobile companion app."""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        media_dir: Optional[Path] = None,
        token_manager: Optional[TokenManager] = None
    ):
        """
        Initialize mobile server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            media_dir: Directory containing media files
            token_manager: Token manager instance
        """
        self.host = host
        self.port = port
        self.media_dir = media_dir or Path.home() / "Pictures" / "AI"
        self.token_manager = token_manager or TokenManager()
        
        # Create FastAPI app
        self.app = FastAPI(title="Alice Mobile Companion")
        self._setup_routes()
        self._setup_middleware()
        
        # WebSocket connections
        self.active_connections: Set[WebSocket] = set()
        self.timelines: Dict[str, Timeline] = {}
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def _setup_middleware(self):
        """Configure middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure for your network
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def read_root():
            """Serve mobile web app."""
            return HTMLResponse(self._get_mobile_app_html())
        
        @self.app.get("/api/auth/validate")
        async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
            """Validate authentication token."""
            if self.token_manager.validate_token(credentials.credentials):
                session_id = str(uuid.uuid4())
                self.sessions[session_id] = {
                    "created": datetime.now(),
                    "token": credentials.credentials
                }
                return {"valid": True, "session_id": session_id}
            
            raise HTTPException(status_code=401, detail="Invalid token")
        
        @self.app.get("/api/timelines")
        async def list_timelines(credentials: HTTPAuthorizationCredentials = Depends(security)):
            """List available timelines."""
            if not self.token_manager.validate_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid token")
            
            return {
                "timelines": [
                    {
                        "id": tid,
                        "name": timeline.name,
                        "duration": timeline.duration,
                        "clip_count": len(timeline.clips)
                    }
                    for tid, timeline in self.timelines.items()
                ]
            }
        
        @self.app.get("/api/timeline/{timeline_id}")
        async def get_timeline(
            timeline_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """Get timeline details."""
            if not self.token_manager.validate_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid token")
            
            if timeline_id not in self.timelines:
                raise HTTPException(status_code=404, detail="Timeline not found")
            
            timeline = self.timelines[timeline_id]
            return {
                "id": timeline_id,
                "name": timeline.name,
                "duration": timeline.duration,
                "clips": [
                    {
                        "id": clip.id,
                        "file_path": str(clip.file_path),
                        "start_time": clip.start_time,
                        "duration": clip.duration,
                        "thumbnail": f"/api/thumbnail/{clip.id}"
                    }
                    for clip in timeline.clips
                ]
            }
        
        @self.app.post("/api/timeline/{timeline_id}/reorder")
        async def reorder_clips(
            timeline_id: str,
            clip_ids: List[str],
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """Reorder clips in timeline."""
            if not self.token_manager.validate_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid token")
            
            if timeline_id not in self.timelines:
                raise HTTPException(status_code=404, detail="Timeline not found")
            
            timeline = self.timelines[timeline_id]
            
            # Reorder clips based on provided IDs
            new_clips = []
            for clip_id in clip_ids:
                clip = next((c for c in timeline.clips if c.id == clip_id), None)
                if clip:
                    new_clips.append(clip)
            
            timeline.clips = new_clips
            timeline.recalculate_times()
            
            # Broadcast update
            await self._broadcast_timeline_update(timeline_id)
            
            return {"success": True}
        
        @self.app.get("/api/thumbnail/{clip_id}")
        async def get_thumbnail(
            clip_id: str,
            size: int = Query(200, ge=50, le=500)
        ):
            """Get clip thumbnail."""
            # Find clip across all timelines
            clip = None
            for timeline in self.timelines.values():
                clip = next((c for c in timeline.clips if c.id == clip_id), None)
                if clip:
                    break
            
            if not clip:
                raise HTTPException(status_code=404, detail="Clip not found")
            
            # Generate or serve cached thumbnail
            # For now, serve the original file
            return FileResponse(clip.file_path)
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.active_connections.add(websocket)
            
            try:
                while True:
                    # Keep connection alive and handle messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "auth":
                        token = message.get("token")
                        if not self.token_manager.validate_token(token):
                            await websocket.send_json({
                                "type": "error",
                                "message": "Invalid token"
                            })
                            break
                    
                    elif message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    async def _broadcast_timeline_update(self, timeline_id: str):
        """Broadcast timeline update to all connected clients."""
        if timeline_id not in self.timelines:
            return
        
        timeline = self.timelines[timeline_id]
        update = {
            "type": "timeline_update",
            "timeline_id": timeline_id,
            "timeline": {
                "name": timeline.name,
                "duration": timeline.duration,
                "clips": [
                    {
                        "id": clip.id,
                        "start_time": clip.start_time,
                        "duration": clip.duration
                    }
                    for clip in timeline.clips
                ]
            }
        }
        
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(update)
            except:
                disconnected.add(connection)
        
        # Remove disconnected clients
        self.active_connections -= disconnected
    
    def _get_mobile_app_html(self) -> str:
        """Return mobile web app HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>Alice Timeline Control</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #fff;
            overflow-x: hidden;
            touch-action: pan-y;
        }
        
        .header {
            background: #2a2a2a;
            padding: 15px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 20px;
            font-weight: 500;
        }
        
        .auth-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            padding: 20px;
        }
        
        .auth-container h2 {
            margin-bottom: 30px;
            font-size: 24px;
        }
        
        .token-input {
            width: 100%;
            max-width: 300px;
            padding: 15px;
            font-size: 16px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 8px;
            color: #fff;
            margin-bottom: 20px;
        }
        
        .btn {
            background: #007aff;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            touch-action: manipulation;
        }
        
        .btn:active {
            background: #0051d5;
        }
        
        .timeline-list {
            padding: 20px;
        }
        
        .timeline-item {
            background: #2a2a2a;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .timeline-item:active {
            transform: scale(0.98);
        }
        
        .timeline-item h3 {
            font-size: 18px;
            margin-bottom: 8px;
        }
        
        .timeline-item .info {
            color: #888;
            font-size: 14px;
        }
        
        .clips-container {
            padding: 20px;
            padding-bottom: 100px;
        }
        
        .clip {
            background: #2a2a2a;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            cursor: move;
            touch-action: none;
            user-select: none;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .clip.dragging {
            opacity: 0.5;
            transform: scale(1.05);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            z-index: 1000;
        }
        
        .clip-thumbnail {
            width: 80px;
            height: 80px;
            border-radius: 8px;
            margin-right: 15px;
            background: #444;
            object-fit: cover;
        }
        
        .clip-info h4 {
            font-size: 16px;
            margin-bottom: 5px;
        }
        
        .clip-info .duration {
            color: #888;
            font-size: 14px;
        }
        
        .drag-handle {
            margin-left: auto;
            font-size: 24px;
            color: #666;
            padding: 0 10px;
        }
        
        .bottom-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #2a2a2a;
            padding: 20px;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-around;
        }
        
        .status {
            position: fixed;
            top: 70px;
            right: 20px;
            background: #333;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 14px;
            display: none;
        }
        
        .status.connected {
            background: #2d7a2d;
            display: block;
        }
        
        .status.disconnected {
            background: #a22;
            display: block;
        }
        
        @media (max-width: 400px) {
            .clip {
                padding: 10px;
            }
            
            .clip-thumbnail {
                width: 60px;
                height: 60px;
            }
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="auth-container" id="authScreen">
            <h2>Alice Timeline Control</h2>
            <input 
                type="password" 
                class="token-input" 
                id="tokenInput" 
                placeholder="Enter access token"
                autocomplete="off"
            >
            <button class="btn" onclick="authenticate()">Connect</button>
        </div>
        
        <div id="mainScreen" style="display: none;">
            <div class="header">
                <h1>Timelines</h1>
            </div>
            
            <div class="status" id="connectionStatus">Disconnected</div>
            
            <div class="timeline-list" id="timelineList"></div>
            
            <div class="clips-container" id="clipsContainer" style="display: none;">
                <div class="header">
                    <h1 id="timelineName">Timeline</h1>
                </div>
                <div id="clipsList"></div>
                <div class="bottom-bar">
                    <button class="btn" onclick="showTimelines()">Back</button>
                    <button class="btn" onclick="saveOrder()">Save Order</button>
                </div>
            </div>
        </div>
    </div>
    
    <script src="/static/mobile-app.js"></script>
</body>
</html>
"""
    
    async def add_timeline(self, timeline_id: str, timeline: Timeline):
        """Add a timeline to the server."""
        self.timelines[timeline_id] = timeline
        await self._broadcast_timeline_update(timeline_id)
    
    def run(self):
        """Run the mobile server."""
        import uvicorn
        
        logger.info(f"Starting mobile server on {self.host}:{self.port}")
        logger.info(f"Access from mobile: http://{self.host}:{self.port}")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )