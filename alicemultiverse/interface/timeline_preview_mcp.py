"""MCP tools for timeline preview functionality."""

import asyncio
import logging
import webbrowser
from pathlib import Path
from typing import Any

from ..workflows.video_export import Timeline, TimelineClip
from .timeline_preview import TimelinePreviewServer

logger = logging.getLogger(__name__)

# Global server instance
_preview_server: TimelinePreviewServer | None = None
_server_task: asyncio.Task | None = None


async def start_preview_server(port: int = 8001) -> bool:
    """Start the timeline preview server if not already running."""
    global _preview_server, _server_task

    if _preview_server is not None:
        logger.info("Preview server already running")
        return True

    try:
        _preview_server = TimelinePreviewServer()

        # Start server in background
        import uvicorn
        config = uvicorn.Config(
            app=_preview_server.app,
            host="127.0.0.1",
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        # Run server in background task
        _server_task = asyncio.create_task(server.serve())

        # Give server time to start
        await asyncio.sleep(1)

        logger.info(f"Timeline preview server started on port {port}")
        return True

    except Exception as e:
        logger.error(f"Failed to start preview server: {e}")
        _preview_server = None
        _server_task = None
        return False


async def preview_timeline(
    timeline_data: dict[str, Any],
    auto_open: bool = True,
    port: int = 8001
) -> dict[str, Any]:
    """
    Open a timeline in the web preview interface.

    Args:
        timeline_data: Timeline data dictionary
        auto_open: Whether to automatically open browser
        port: Server port

    Returns:
        Dict with preview URL and session ID
    """
    # Ensure server is running
    if not await start_preview_server(port):
        return {
            "success": False,
            "error": "Failed to start preview server"
        }

    try:
        # Create preview session
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://127.0.0.1:{port}/session/create",
                json=timeline_data,
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                session_id = result["session_id"]
                preview_url = f"http://127.0.0.1:{port}/?session={session_id}"

                # Open browser if requested
                if auto_open:
                    webbrowser.open(preview_url)
                    logger.info(f"Opened preview in browser: {preview_url}")

                return {
                    "success": True,
                    "session_id": session_id,
                    "preview_url": preview_url,
                    "message": "Timeline preview opened successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create session: {response.text}"
                }

    except Exception as e:
        logger.error(f"Error creating preview session: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def update_preview_timeline(
    session_id: str,
    operation: str,
    clips: list[dict[str, Any]],
    port: int = 8001
) -> dict[str, Any]:
    """
    Update a timeline in the preview interface.

    Args:
        session_id: Preview session ID
        operation: Operation type (reorder, trim, add_transition)
        clips: List of clip updates
        port: Server port

    Returns:
        Updated timeline data
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://127.0.0.1:{port}/session/{session_id}/update",
                json={
                    "timeline_id": session_id,
                    "operation": operation,
                    "clips": clips
                },
                timeout=10.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"Failed to update timeline: {response.text}"
                }

    except Exception as e:
        logger.error(f"Error updating timeline: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def export_preview_timeline(
    session_id: str,
    format: str = "json",
    output_path: Path | None = None,
    port: int = 8001
) -> dict[str, Any]:
    """
    Export a timeline from the preview interface.

    Args:
        session_id: Preview session ID
        format: Export format (json, edl, xml)
        output_path: Optional output file path
        port: Server port

    Returns:
        Export result
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://127.0.0.1:{port}/session/{session_id}/export",
                params={"format": format},
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()

                # Save to file if path provided
                if output_path:
                    output_path = Path(output_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    if format == "json":
                        import json
                        with open(output_path, 'w') as f:
                            json.dump(result, f, indent=2)
                    else:
                        # For EDL/XML, save the content string
                        with open(output_path, 'w') as f:
                            f.write(result.get("content", ""))

                    logger.info(f"Exported timeline to {output_path}")

                    return {
                        "success": True,
                        "format": format,
                        "output_path": str(output_path),
                        "message": f"Timeline exported to {output_path}"
                    }
                else:
                    return {
                        "success": True,
                        "format": format,
                        "data": result,
                        "message": "Timeline exported successfully"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Failed to export timeline: {response.text}"
                }

    except Exception as e:
        logger.error(f"Error exporting timeline: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_preview_status(port: int = 8001) -> dict[str, Any]:
    """
    Check if preview server is running and get status.

    Args:
        port: Server port

    Returns:
        Server status information
    """
    global _preview_server

    if _preview_server is None:
        return {
            "running": False,
            "message": "Preview server not started"
        }

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://127.0.0.1:{port}/",
                timeout=2.0
            )

            if response.status_code == 200:
                return {
                    "running": True,
                    "port": port,
                    "url": f"http://127.0.0.1:{port}/",
                    "sessions": len(_preview_server.sessions),
                    "message": "Preview server is running"
                }
            else:
                return {
                    "running": False,
                    "message": "Server not responding properly"
                }

    except Exception as e:
        return {
            "running": False,
            "message": f"Cannot connect to server: {e!s}"
        }


async def stop_preview_server() -> bool:
    """Stop the timeline preview server."""
    global _preview_server, _server_task

    if _server_task:
        _server_task.cancel()
        try:
            await _server_task
        except asyncio.CancelledError:
            pass
        _server_task = None

    _preview_server = None
    logger.info("Timeline preview server stopped")
    return True


# Example usage functions for testing
async def create_test_timeline() -> Timeline:
    """Create a test timeline for preview."""
    clips = [
        TimelineClip(
            asset_path=Path("/path/to/clip1.jpg"),
            start_time=0.0,
            duration=2.0,
            metadata={"title": "Clip 1"}
        ),
        TimelineClip(
            asset_path=Path("/path/to/clip2.jpg"),
            start_time=2.0,
            duration=3.0,
            metadata={"title": "Clip 2"}
        ),
        TimelineClip(
            asset_path=Path("/path/to/clip3.jpg"),
            start_time=5.0,
            duration=2.5,
            metadata={"title": "Clip 3"}
        ),
    ]

    return Timeline(
        name="Test Timeline",
        duration=7.5,
        clips=clips,
        markers=[
            {"time": 2.0, "type": "beat", "label": "Beat 1"},
            {"time": 4.0, "type": "beat", "label": "Beat 2"},
            {"time": 6.0, "type": "beat", "label": "Beat 3"},
        ]
    )


if __name__ == "__main__":
    # Test the preview server
    async def test():
        # Create test timeline
        timeline = await create_test_timeline()
        timeline_dict = {
            "name": timeline.name,
            "duration": timeline.duration,
            "frame_rate": timeline.frame_rate,
            "resolution": list(timeline.resolution),
            "clips": [
                {
                    "asset_path": str(clip.asset_path),
                    "start_time": clip.start_time,
                    "duration": clip.duration,
                    "in_point": clip.in_point,
                    "out_point": clip.out_point,
                    "metadata": clip.metadata
                }
                for clip in timeline.clips
            ],
            "markers": timeline.markers
        }

        # Preview timeline
        result = await preview_timeline(timeline_dict)
        print(f"Preview result: {result}")

        # Keep server running
        if result["success"]:
            print(f"Preview server running at: {result['preview_url']}")
            print("Press Ctrl+C to stop...")
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                await stop_preview_server()

    asyncio.run(test())
