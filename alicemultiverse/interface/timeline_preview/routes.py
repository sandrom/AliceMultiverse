"""API route handlers for timeline preview interface."""

import copy
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, WebSocket
from fastapi.responses import FileResponse, HTMLResponse

from ...workflows.video_export import Timeline, TimelineClip
from .models import TimelineUpdateRequest
from .session import PreviewSession

logger = logging.getLogger(__name__)


class RouteHandlers:
    """Route handlers for timeline preview server."""
    
    def __init__(self, server):
        """Initialize route handlers with server reference."""
        self.server = server
        self.sessions = server.sessions
        self.static_dir = server.static_dir
        self.media_dir = server.media_dir
    
    async def index(self):
        """Serve the timeline preview interface."""
        index_path = self.static_dir / "index.html"
        if index_path.exists():
            return index_path.read_text()
        else:
            return self.server._generate_default_html()
    
    async def get_timeline(self, session_id: str):
        """Get timeline data for a session."""
        session = self.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "timeline": self.server._timeline_to_dict(session.timeline),
            "version": session.version
        }
    
    async def serve_media(self, file_path: str):
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
    
    async def create_session(self, timeline_data: dict):
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
                "timeline": self.server._timeline_to_dict(timeline)
            }
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_session(self, session_id: str):
        """Get session details."""
        session = self.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session.id,
            "timeline": self.server._timeline_to_dict(session.timeline),
            "version": session.version,
            "created_at": session.created_at.isoformat(),
            "last_modified": session.last_modified.isoformat(),
            "can_undo": len(session.undo_stack) > 0,
            "can_redo": len(session.redo_stack) > 0
        }
    
    async def update_timeline(self, session_id: str, request: TimelineUpdateRequest):
        """Update timeline in session."""
        session = self.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            # Apply the requested operation
            new_timeline = self.server._apply_timeline_operation(
                session.timeline,
                request.operation,
                request.clips
            )
            
            session.update_timeline(new_timeline)
            
            return {
                "success": True,
                "timeline": self.server._timeline_to_dict(session.timeline),
                "version": session.version
            }
        except Exception as e:
            logger.error(f"Failed to update timeline: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def undo(self, session_id: str):
        """Undo last change."""
        session = self.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.undo():
            return {
                "success": True,
                "timeline": self.server._timeline_to_dict(session.timeline),
                "version": session.version
            }
        else:
            return {"success": False, "message": "Nothing to undo"}
    
    async def redo(self, session_id: str):
        """Redo last undone change."""
        session = self.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.redo():
            return {
                "success": True,
                "timeline": self.server._timeline_to_dict(session.timeline),
                "version": session.version
            }
        else:
            return {"success": False, "message": "Nothing to redo"}
    
    async def export_timeline(self, session_id: str, format: str = "json"):
        """Export timeline in requested format."""
        session = self.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if format == "json":
            return self.server._timeline_to_dict(session.timeline)
        elif format == "edl":
            # TODO: Implement EDL export
            return {"format": "edl", "content": "EDL export not yet implemented"}
        elif format == "xml":
            # TODO: Implement XML export
            return {"format": "xml", "content": "XML export not yet implemented"}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {format}")
    
    async def websocket_endpoint(self, websocket: WebSocket, session_id: str):
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
                            "timeline": self.server._timeline_to_dict(session.timeline)
                        })
                
                elif message["type"] == "undo":
                    if session.undo():
                        await websocket.send_json({
                            "type": "timeline_update",
                            "timeline": self.server._timeline_to_dict(session.timeline)
                        })
                
                elif message["type"] == "redo":
                    if session.redo():
                        await websocket.send_json({
                            "type": "timeline_update",
                            "timeline": self.server._timeline_to_dict(session.timeline)
                        })
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await websocket.close()
    
    async def generate_preview(self, request: dict):
        """Generate a preview video file from timeline."""
        try:
            timeline_data = request.get("timeline", {})
            format = request.get("format", "mp4")
            resolution = request.get("resolution", [1280, 720])
            request.get("includeAudio", True)
            
            # Create temporary output file
            temp_dir = Path(tempfile.mkdtemp())
            output_path = temp_dir / f"preview.{format}"
            
            # Import video export functionality
            from ...workflows.video_export import VideoExportManager
            
            # Convert timeline data to Timeline object
            timeline = Timeline(
                name=timeline_data.get("name", "Preview"),
                duration=timeline_data.get("duration", 0),
                frame_rate=timeline_data.get("frame_rate", 30),
                resolution=tuple(resolution),
                clips=[TimelineClip(**clip) for clip in timeline_data.get("clips", [])]
            )
            
            # Generate preview (simplified version - in production would use ffmpeg)
            VideoExportManager()
            
            # For now, return a placeholder response
            # Full implementation would use ffmpeg to create actual preview
            # Generate a unique preview ID
            import hashlib
            # Generate preview ID from timeline + timestamp
            preview_source = f"{timeline.id}:{datetime.now().isoformat()}"
            preview_id = hashlib.sha256(preview_source.encode()).hexdigest()[:16]
            preview_url = f"/preview/{preview_id}/{output_path.name}"
            
            return {
                "preview_url": preview_url,
                "duration": timeline.duration,
                "format": format
            }
        
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))