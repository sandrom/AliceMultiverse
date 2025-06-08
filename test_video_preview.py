#!/usr/bin/env python3
"""Test script for video playback in web preview interface."""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

import uvicorn
from alicemultiverse.interface.timeline_preview import TimelinePreviewServer
from alicemultiverse.workflows.video_export import Timeline, TimelineClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_video_preview():
    """Test the video preview functionality."""
    # Create server instance
    server = TimelinePreviewServer()
    
    # Create test timeline with sample video clips
    test_clips = [
        TimelineClip(
            path="test_videos/clip1.mp4",
            start_time=0.0,
            duration=5.0,
            transition_in="fade",
            transition_in_duration=0.5
        ),
        TimelineClip(
            path="test_videos/clip2.mp4",
            start_time=5.0,
            duration=7.0,
            transition_in="dissolve",
            transition_in_duration=1.0
        ),
        TimelineClip(
            path="test_videos/clip3.mp4",
            start_time=12.0,
            duration=4.0,
            transition_out="fade",
            transition_out_duration=0.5
        )
    ]
    
    test_timeline = Timeline(
        name="Test Video Timeline",
        duration=16.0,
        frame_rate=30,
        resolution=(1920, 1080),
        clips=test_clips,
        audio_tracks=[],
        markers=[
            {"time": 2.0, "type": "beat", "strong": True},
            {"time": 4.0, "type": "beat", "strong": False},
            {"time": 6.0, "type": "beat", "strong": True},
            {"time": 8.0, "type": "beat", "strong": False},
            {"time": 10.0, "type": "beat", "strong": True},
            {"time": 12.0, "type": "beat", "strong": False},
            {"time": 14.0, "type": "beat", "strong": True}
        ],
        metadata={"created": datetime.now().isoformat()}
    )
    
    # Create session
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        # Create session
        response = await client.post("/session/create", json={
            "name": test_timeline.name,
            "duration": test_timeline.duration,
            "frame_rate": test_timeline.frame_rate,
            "resolution": list(test_timeline.resolution),
            "clips": [
                {
                    "path": clip.path,
                    "start_time": clip.start_time,
                    "duration": clip.duration,
                    "transition_in": clip.transition_in,
                    "transition_in_duration": clip.transition_in_duration,
                    "transition_out": clip.transition_out,
                    "transition_out_duration": clip.transition_out_duration
                }
                for clip in test_timeline.clips
            ],
            "markers": test_timeline.markers,
            "metadata": test_timeline.metadata
        })
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            logger.info(f"Created session: {session_id}")
            
            # Print URL for browser access
            print(f"\nOpen your browser to: http://localhost:8001/?session={session_id}")
            print("Features to test:")
            print("- Video playback with Play/Pause buttons")
            print("- Timeline scrubbing by clicking on ruler")
            print("- Drag and drop clip reordering")
            print("- Double-click clips to edit properties")
            print("- Export to various formats")
            print("- Keyboard shortcuts (Space, Arrow keys, Home/End)")
            print("\nPress Ctrl+C to stop the server")
        else:
            logger.error(f"Failed to create session: {response.status_code}")


async def create_test_videos():
    """Create simple test videos using ffmpeg."""
    test_dir = Path("test_videos")
    test_dir.mkdir(exist_ok=True)
    
    # Create 3 test videos with different colors
    colors = ["red", "green", "blue"]
    durations = [5, 7, 4]
    
    for i, (color, duration) in enumerate(zip(colors, durations)):
        output_path = test_dir / f"clip{i+1}.mp4"
        if not output_path.exists():
            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"color=c={color}:s=1920x1080:d={duration}",
                "-vf", f"drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='Clip {i+1}':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264",
                "-t", str(duration),
                str(output_path),
                "-y"
            ]
            
            import subprocess
            logger.info(f"Creating test video: {output_path}")
            subprocess.run(cmd, check=True)


async def main():
    """Main test function."""
    # Create test videos if needed
    await create_test_videos()
    
    # Import httpx here to avoid top-level import
    global httpx
    import httpx
    
    # Start the server
    server = TimelinePreviewServer()
    
    # Run test in background
    asyncio.create_task(test_video_preview())
    
    # Start server
    config = uvicorn.Config(
        app=server.app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())