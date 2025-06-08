"""Web-based timeline preview interface for video exports.

This module provides an interactive web interface for previewing video timelines
before exporting to editing software. Features include:
- Visual timeline with clips
- Drag-and-drop reordering
- Real-time playback preview
- Transition visualization
- Beat marker display
"""

import copy
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..workflows.video_export import Timeline, TimelineClip

logger = logging.getLogger(__name__)


class TimelinePreviewRequest(BaseModel):
    """Request to preview a timeline."""
    timeline_id: str
    format: str = "web"  # web, edl, xml, capcut


class TimelineUpdateRequest(BaseModel):
    """Request to update timeline."""
    timeline_id: str
    clips: List[dict]  # List of clip updates
    operation: str  # reorder, trim, add_transition, etc.


class PreviewSession:
    """Manages a timeline preview session."""
    
    def __init__(self, timeline: Timeline):
        self.id = str(uuid.uuid4())
        self.timeline = timeline
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.version = 1
        self.undo_stack: List[Timeline] = []
        self.redo_stack: List[Timeline] = []
    
    def update_timeline(self, new_timeline: Timeline):
        """Update timeline with undo support."""
        self.undo_stack.append(self.timeline)
        self.timeline = new_timeline
        self.last_modified = datetime.now()
        self.version += 1
        self.redo_stack.clear()
    
    def undo(self) -> bool:
        """Undo last change."""
        if self.undo_stack:
            self.redo_stack.append(self.timeline)
            self.timeline = self.undo_stack.pop()
            self.last_modified = datetime.now()
            return True
        return False
    
    def redo(self) -> bool:
        """Redo last undone change."""
        if self.redo_stack:
            self.undo_stack.append(self.timeline)
            self.timeline = self.redo_stack.pop()
            self.last_modified = datetime.now()
            return True
        return False


class TimelinePreviewServer:
    """Web server for timeline preview interface."""
    
    def __init__(self, static_dir: Optional[Path] = None):
        self.app = FastAPI(title="Alice Timeline Preview")
        self.sessions: Dict[str, PreviewSession] = {}
        self.static_dir = static_dir or Path(__file__).parent / "static" / "timeline_preview"
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Mount static files
        if self.static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        # Set media directory for serving video/image files
        self.media_dir = Path.home() / "Documents" / "AliceMultiverse"
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """Serve the timeline preview interface."""
            index_path = self.static_dir / "index.html"
            if index_path.exists():
                return index_path.read_text()
            else:
                return self._generate_default_html()
        
        @self.app.get("/api/timeline/{session_id}")
        async def get_timeline(session_id: str):
            """Get timeline data for a session."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return {
                "timeline": self._timeline_to_dict(session.timeline),
                "version": session.version
            }
        
        @self.app.get("/media/{file_path:path}")
        async def serve_media(file_path: str):
            """Serve media files (videos/images) from the media directory."""
            try:
                media_path = self.media_dir / file_path
                
                # Security check - ensure path doesn't escape media directory
                media_path = media_path.resolve()
                if not str(media_path).startswith(str(self.media_dir)):
                    raise HTTPException(status_code=403, detail="Access denied")
                
                if not media_path.exists():
                    raise HTTPException(status_code=404, detail="File not found")
                
                # Determine content type
                content_type = "application/octet-stream"
                suffix = media_path.suffix.lower()
                if suffix in [".mp4", ".mov", ".avi"]:
                    content_type = "video/mp4"
                elif suffix in [".jpg", ".jpeg"]:
                    content_type = "image/jpeg"
                elif suffix in [".png"]:
                    content_type = "image/png"
                elif suffix in [".webp"]:
                    content_type = "image/webp"
                elif suffix in [".webm"]:
                    content_type = "video/webm"
                
                return FileResponse(
                    media_path,
                    media_type=content_type,
                    headers={
                        "Accept-Ranges": "bytes",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
            except Exception as e:
                logger.error(f"Error serving media: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.post("/session/create")
        async def create_session(timeline_data: dict):
            """Create a new preview session from timeline data."""
            try:
                # Convert dict to Timeline object
                clips = [TimelineClip(**clip) for clip in timeline_data.get("clips", [])]
                timeline = Timeline(
                    name=timeline_data.get("name", "Untitled"),
                    duration=timeline_data.get("duration", 0),
                    frame_rate=timeline_data.get("frame_rate", 30),
                    resolution=tuple(timeline_data.get("resolution", [1920, 1080])),
                    clips=clips,
                    audio_tracks=timeline_data.get("audio_tracks", []),
                    markers=timeline_data.get("markers", []),
                    metadata=timeline_data.get("metadata", {})
                )
                
                session = PreviewSession(timeline)
                self.sessions[session.id] = session
                
                return {
                    "session_id": session.id,
                    "timeline": self._timeline_to_dict(timeline)
                }
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/session/{session_id}")
        async def get_session(session_id: str):
            """Get session details."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return {
                "session_id": session.id,
                "timeline": self._timeline_to_dict(session.timeline),
                "version": session.version,
                "created_at": session.created_at.isoformat(),
                "last_modified": session.last_modified.isoformat(),
                "can_undo": len(session.undo_stack) > 0,
                "can_redo": len(session.redo_stack) > 0
            }
        
        @self.app.post("/session/{session_id}/update")
        async def update_timeline(session_id: str, request: TimelineUpdateRequest):
            """Update timeline in session."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            try:
                # Apply the requested operation
                new_timeline = self._apply_timeline_operation(
                    session.timeline,
                    request.operation,
                    request.clips
                )
                
                session.update_timeline(new_timeline)
                
                return {
                    "success": True,
                    "timeline": self._timeline_to_dict(session.timeline),
                    "version": session.version
                }
            except Exception as e:
                logger.error(f"Failed to update timeline: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/session/{session_id}/undo")
        async def undo(session_id: str):
            """Undo last change."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if session.undo():
                return {
                    "success": True,
                    "timeline": self._timeline_to_dict(session.timeline),
                    "version": session.version
                }
            else:
                return {"success": False, "message": "Nothing to undo"}
        
        @self.app.post("/session/{session_id}/redo")
        async def redo(session_id: str):
            """Redo last undone change."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if session.redo():
                return {
                    "success": True,
                    "timeline": self._timeline_to_dict(session.timeline),
                    "version": session.version
                }
            else:
                return {"success": False, "message": "Nothing to redo"}
        
        @self.app.post("/session/{session_id}/export")
        async def export_timeline(session_id: str, format: str = "json"):
            """Export timeline in requested format."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if format == "json":
                return self._timeline_to_dict(session.timeline)
            elif format == "edl":
                # TODO: Implement EDL export
                return {"format": "edl", "content": "EDL export not yet implemented"}
            elif format == "xml":
                # TODO: Implement XML export
                return {"format": "xml", "content": "XML export not yet implemented"}
            else:
                raise HTTPException(status_code=400, detail=f"Unknown format: {format}")
        
        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket for real-time updates."""
            await websocket.accept()
            
            session = self.sessions.get(session_id)
            if not session:
                await websocket.close(code=1008, reason="Session not found")
                return
            
            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    if message["type"] == "ping":
                        await websocket.send_json({"type": "pong"})
                    
                    elif message["type"] == "update_timeline":
                        # Update timeline based on client changes
                        updates = message.get("updates", {})
                        if "clips" in updates:
                            # Update clip arrangement
                            new_timeline = copy.deepcopy(session.timeline)
                            new_timeline.clips = [TimelineClip(**clip) for clip in updates["clips"]]
                            new_timeline.duration = max((c.start_time + c.duration) for c in new_timeline.clips) if new_timeline.clips else 0
                            session.update_timeline(new_timeline)
                            
                            # Send update confirmation
                            await websocket.send_json({
                                "type": "timeline_update",
                                "timeline": self._timeline_to_dict(session.timeline)
                            })
                    
                    elif message["type"] == "undo":
                        if session.undo():
                            await websocket.send_json({
                                "type": "timeline_update",
                                "timeline": self._timeline_to_dict(session.timeline)
                            })
                    
                    elif message["type"] == "redo":
                        if session.redo():
                            await websocket.send_json({
                                "type": "timeline_update",
                                "timeline": self._timeline_to_dict(session.timeline)
                            })
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await websocket.close()
        
        @self.app.post("/api/preview/generate")
        async def generate_preview(request: dict):
            """Generate a preview video file from timeline."""
            try:
                timeline_data = request.get("timeline", {})
                format = request.get("format", "mp4")
                resolution = request.get("resolution", [1280, 720])
                include_audio = request.get("includeAudio", True)
                
                # Create temporary output file
                import tempfile
                temp_dir = Path(tempfile.mkdtemp())
                output_path = temp_dir / f"preview.{format}"
                
                # Import video export functionality
                from ..workflows.video_export import VideoExportManager
                
                # Convert timeline data to Timeline object
                timeline = Timeline(
                    name=timeline_data.get("name", "Preview"),
                    duration=timeline_data.get("duration", 0),
                    frame_rate=timeline_data.get("frame_rate", 30),
                    resolution=tuple(resolution),
                    clips=[TimelineClip(**clip) for clip in timeline_data.get("clips", [])]
                )
                
                # Generate preview (simplified version - in production would use ffmpeg)
                export_manager = VideoExportManager()
                
                # For now, return a placeholder response
                # Full implementation would use ffmpeg to create actual preview
                preview_url = f"/preview/{session_id}/{output_path.name}"
                
                return {
                    "preview_url": preview_url,
                    "duration": timeline.duration,
                    "format": format
                }
                
            except Exception as e:
                logger.error(f"Preview generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/asset/{asset_path:path}")
        async def get_asset(asset_path: str):
            """Serve asset files (images/videos)."""
            asset_file = Path(asset_path)
            if asset_file.exists() and asset_file.is_file():
                return FileResponse(asset_file)
            else:
                raise HTTPException(status_code=404, detail="Asset not found")
    
    def _timeline_to_dict(self, timeline: Timeline) -> dict:
        """Convert Timeline object to dictionary."""
        result = asdict(timeline)
        # Convert Path objects to strings
        for clip in result.get("clips", []):
            if "asset_path" in clip:
                clip["asset_path"] = str(clip["asset_path"])
        return result
    
    def _apply_timeline_operation(self, timeline: Timeline, operation: str, clip_updates: List[dict]) -> Timeline:
        """Apply an operation to the timeline."""
        # Create a copy of the timeline
        import copy
        new_timeline = copy.deepcopy(timeline)
        
        if operation == "reorder":
            # Reorder clips based on new positions
            clip_map = {i: clip for i, clip in enumerate(new_timeline.clips)}
            new_clips = []
            
            for update in clip_updates:
                old_index = update.get("old_index")
                new_index = update.get("new_index")
                if old_index is not None and old_index in clip_map:
                    clip = clip_map[old_index]
                    # Update start time based on new position
                    if new_index > 0 and new_index <= len(new_clips):
                        prev_clip = new_clips[new_index - 1]
                        clip.start_time = prev_clip.end_time
                    else:
                        clip.start_time = 0
                    new_clips.insert(new_index, clip)
            
            new_timeline.clips = new_clips
            
        elif operation == "trim":
            # Trim clip durations
            for update in clip_updates:
                clip_index = update.get("index")
                if 0 <= clip_index < len(new_timeline.clips):
                    clip = new_timeline.clips[clip_index]
                    if "in_point" in update:
                        clip.in_point = update["in_point"]
                    if "out_point" in update:
                        clip.out_point = update["out_point"]
                    if "duration" in update:
                        clip.duration = update["duration"]
        
        elif operation == "add_transition":
            # Add transitions between clips
            for update in clip_updates:
                clip_index = update.get("index")
                if 0 <= clip_index < len(new_timeline.clips):
                    clip = new_timeline.clips[clip_index]
                    if "transition_in" in update:
                        clip.transition_in = update["transition_in"]
                        clip.transition_in_duration = update.get("transition_in_duration", 1.0)
                    if "transition_out" in update:
                        clip.transition_out = update["transition_out"]
                        clip.transition_out_duration = update.get("transition_out_duration", 1.0)
        
        # Recalculate timeline duration
        if new_timeline.clips:
            new_timeline.duration = max(clip.end_time for clip in new_timeline.clips)
        
        return new_timeline
    
    def _generate_default_html(self) -> str:
        """Generate default HTML for timeline preview."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alice Timeline Preview</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #1a1a1a;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1 {
            color: #fff;
            margin-bottom: 30px;
        }
        
        .preview-container {
            background: #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .timeline-container {
            background: #333;
            border-radius: 4px;
            padding: 10px;
            min-height: 200px;
            overflow-x: auto;
        }
        
        .timeline-track {
            display: flex;
            gap: 2px;
            min-height: 80px;
            align-items: center;
        }
        
        .timeline-clip {
            background: #4a90e2;
            border-radius: 4px;
            padding: 8px;
            min-width: 100px;
            cursor: move;
            transition: transform 0.2s;
        }
        
        .timeline-clip:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .controls {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        
        button {
            background: #4a90e2;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        button:hover {
            background: #357abd;
        }
        
        button:disabled {
            background: #666;
            cursor: not-allowed;
        }
        
        .status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            padding: 10px 20px;
            border-radius: 4px;
            display: none;
        }
        
        .status.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Timeline Preview</h1>
        
        <div class="preview-container">
            <h3>Video Preview</h3>
            <div id="video-preview" style="background: #000; height: 400px; display: flex; align-items: center; justify-content: center;">
                <p style="color: #666;">Video preview will appear here</p>
            </div>
        </div>
        
        <div class="preview-container">
            <h3>Timeline</h3>
            <div class="timeline-container">
                <div class="timeline-track" id="timeline-track">
                    <!-- Clips will be added here -->
                </div>
            </div>
            
            <div class="controls">
                <button onclick="playPreview()">Play</button>
                <button onclick="pausePreview()">Pause</button>
                <button onclick="undoChange()" id="undo-btn">Undo</button>
                <button onclick="redoChange()" id="redo-btn">Redo</button>
                <button onclick="exportTimeline('edl')">Export EDL</button>
                <button onclick="exportTimeline('xml')">Export XML</button>
                <button onclick="exportTimeline('json')">Export JSON</button>
            </div>
        </div>
        
        <div class="status" id="status"></div>
    </div>
    
    <script>
        let sessionId = null;
        let timeline = null;
        let ws = null;
        
        // Initialize
        async function init() {
            // Check if we have a session ID in URL
            const urlParams = new URLSearchParams(window.location.search);
            sessionId = urlParams.get('session');
            
            if (sessionId) {
                await loadSession(sessionId);
            } else {
                showStatus('No session ID provided', 'error');
            }
        }
        
        async function loadSession(id) {
            try {
                const response = await fetch(`/session/${id}`);
                const data = await response.json();
                
                if (response.ok) {
                    timeline = data.timeline;
                    renderTimeline();
                    updateControls(data.can_undo, data.can_redo);
                    connectWebSocket(id);
                } else {
                    showStatus('Failed to load session', 'error');
                }
            } catch (error) {
                console.error('Error loading session:', error);
                showStatus('Error loading session', 'error');
            }
        }
        
        function renderTimeline() {
            const track = document.getElementById('timeline-track');
            track.innerHTML = '';
            
            if (!timeline || !timeline.clips) return;
            
            timeline.clips.forEach((clip, index) => {
                const clipEl = document.createElement('div');
                clipEl.className = 'timeline-clip';
                clipEl.draggable = true;
                clipEl.dataset.index = index;
                clipEl.innerHTML = `
                    <div style="font-size: 12px; font-weight: bold;">Clip ${index + 1}</div>
                    <div style="font-size: 10px; opacity: 0.8;">${clip.duration.toFixed(1)}s</div>
                `;
                
                // Add drag handlers
                clipEl.addEventListener('dragstart', handleDragStart);
                clipEl.addEventListener('dragover', handleDragOver);
                clipEl.addEventListener('drop', handleDrop);
                clipEl.addEventListener('dragend', handleDragEnd);
                
                track.appendChild(clipEl);
            });
        }
        
        function connectWebSocket(id) {
            ws = new WebSocket(`ws://localhost:8000/ws/${id}`);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                ws.send(JSON.stringify({ type: 'get_timeline' }));
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'timeline_update') {
                    timeline = data.timeline;
                    renderTimeline();
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                showStatus('Connection error', 'error');
            };
        }
        
        // Drag and drop handlers
        let draggedElement = null;
        
        function handleDragStart(e) {
            draggedElement = e.target;
            e.target.style.opacity = '0.5';
        }
        
        function handleDragOver(e) {
            if (e.preventDefault) {
                e.preventDefault();
            }
            e.dataTransfer.dropEffect = 'move';
            return false;
        }
        
        function handleDrop(e) {
            if (e.stopPropagation) {
                e.stopPropagation();
            }
            
            if (draggedElement !== e.target) {
                const oldIndex = parseInt(draggedElement.dataset.index);
                const newIndex = parseInt(e.target.dataset.index);
                
                reorderClips(oldIndex, newIndex);
            }
            
            return false;
        }
        
        function handleDragEnd(e) {
            e.target.style.opacity = '';
        }
        
        // Timeline operations
        async function reorderClips(oldIndex, newIndex) {
            try {
                const response = await fetch(`/session/${sessionId}/update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        timeline_id: sessionId,
                        operation: 'reorder',
                        clips: [{ old_index: oldIndex, new_index: newIndex }]
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    timeline = data.timeline;
                    renderTimeline();
                    showStatus('Timeline updated', 'success');
                }
            } catch (error) {
                console.error('Error reordering clips:', error);
                showStatus('Failed to reorder clips', 'error');
            }
        }
        
        async function undoChange() {
            try {
                const response = await fetch(`/session/${sessionId}/undo`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                if (data.success) {
                    timeline = data.timeline;
                    renderTimeline();
                    showStatus('Undone', 'success');
                }
            } catch (error) {
                console.error('Error undoing:', error);
                showStatus('Failed to undo', 'error');
            }
        }
        
        async function redoChange() {
            try {
                const response = await fetch(`/session/${sessionId}/redo`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                if (data.success) {
                    timeline = data.timeline;
                    renderTimeline();
                    showStatus('Redone', 'success');
                }
            } catch (error) {
                console.error('Error redoing:', error);
                showStatus('Failed to redo', 'error');
            }
        }
        
        async function exportTimeline(format) {
            try {
                const response = await fetch(`/session/${sessionId}/export?format=${format}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                // For now, just log the export
                console.log('Export result:', data);
                showStatus(`Exported as ${format.toUpperCase()}`, 'success');
                
                // TODO: Implement actual file download
            } catch (error) {
                console.error('Error exporting:', error);
                showStatus('Failed to export', 'error');
            }
        }
        
        function playPreview() {
            showStatus('Playback not yet implemented', 'info');
        }
        
        function pausePreview() {
            showStatus('Playback not yet implemented', 'info');
        }
        
        function updateControls(canUndo, canRedo) {
            document.getElementById('undo-btn').disabled = !canUndo;
            document.getElementById('redo-btn').disabled = !canRedo;
        }
        
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status show ${type}`;
            
            setTimeout(() => {
                status.classList.remove('show');
            }, 3000);
        }
        
        // Initialize on load
        window.addEventListener('load', init);
    </script>
</body>
</html>
        """
    
    def run(self, host: str = "0.0.0.0", port: int = 8001):
        """Run the preview server."""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)


def create_preview_server(static_dir: Optional[Path] = None) -> TimelinePreviewServer:
    """Create a timeline preview server instance."""
    return TimelinePreviewServer(static_dir)


if __name__ == "__main__":
    # Run the server
    server = create_preview_server()
    server.run()