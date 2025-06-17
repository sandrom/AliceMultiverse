"""Timeline preview server implementation."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .html_generator import HTMLGeneratorMixin
from .routes import RouteHandlers
from .session import PreviewSession
from .timeline_operations import TimelineOperationsMixin

logger = logging.getLogger(__name__)


class TimelinePreviewServer(TimelineOperationsMixin, HTMLGeneratorMixin):
    """Web server for timeline preview interface."""

    def __init__(self, static_dir: Path | None = None):
        self.app = FastAPI(title="Alice Timeline Preview")
        self.sessions: dict[str, PreviewSession] = {}
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
        handlers = RouteHandlers(self)
        
        self.app.get("/", response_class=HTMLResponse)(handlers.index)
        self.app.get("/api/timeline/{session_id}")(handlers.get_timeline)
        self.app.get("/media/{file_path:path}")(handlers.serve_media)
        self.app.post("/session/create")(handlers.create_session)
        self.app.get("/session/{session_id}")(handlers.get_session)
        self.app.post("/session/{session_id}/update")(handlers.update_timeline)
        self.app.post("/session/{session_id}/undo")(handlers.undo)
        self.app.post("/session/{session_id}/redo")(handlers.redo)
        self.app.post("/session/{session_id}/export")(handlers.export_timeline)
        self.app.websocket("/ws/{session_id}")(handlers.websocket_endpoint)
        self.app.post("/api/preview/generate")(handlers.generate_preview)

    def run(self, host: str = "0.0.0.0", port: int = 8001):
        """Run the preview server."""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)


def create_preview_server(static_dir: Path | None = None) -> TimelinePreviewServer:
    """Create and return a timeline preview server instance."""
    return TimelinePreviewServer(static_dir)