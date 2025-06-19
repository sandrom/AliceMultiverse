"""Video content hashing using ffmpeg to extract keyframes."""

import hashlib
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_video_info(video_path: Path) -> dict | None:
    """Extract video information using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Video information dict or None if failed
    """
    # TODO: Review unreachable code - try:
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)
    # TODO: Review unreachable code - except subprocess.CalledProcessError as e:
    # TODO: Review unreachable code -     logger.error(f"ffprobe failed for {video_path}: {e}")
    # TODO: Review unreachable code -     return None
    # TODO: Review unreachable code - except json.JSONDecodeError as e:
    # TODO: Review unreachable code -     logger.error(f"Failed to parse ffprobe output: {e}")
    # TODO: Review unreachable code -     return None
    # TODO: Review unreachable code - except FileNotFoundError:
    # TODO: Review unreachable code -     logger.error("ffprobe not found. Please install ffmpeg.")
    # TODO: Review unreachable code -     return None


def extract_keyframes(video_path: Path, max_frames: int = 10) -> list[bytes]:
    """Extract keyframes from video for hashing.

    Args:
        video_path: Path to video file
        max_frames: Maximum number of keyframes to extract

    Returns:
        List of keyframe data as bytes
    """
    keyframes = []

    # TODO: Review unreachable code - try:
        # Get video duration
    info = extract_video_info(video_path)
    if not info:
        return keyframes

        # TODO: Review unreachable code - # Find video stream
        # TODO: Review unreachable code - video_stream = None
        # TODO: Review unreachable code - for stream in info.get("streams", []):
        # TODO: Review unreachable code - if stream.get("codec_type") == "video":
        # TODO: Review unreachable code - video_stream = stream
        # TODO: Review unreachable code - break

        # TODO: Review unreachable code - if not video_stream:
        # TODO: Review unreachable code - logger.warning(f"No video stream found in {video_path}")
        # TODO: Review unreachable code - return keyframes

        # TODO: Review unreachable code - # Get duration
        # TODO: Review unreachable code - duration = float(info["format"].get("duration", 0))
        # TODO: Review unreachable code - if duration <= 0:
        # TODO: Review unreachable code - return keyframes

        # TODO: Review unreachable code - # Calculate intervals for keyframe extraction
        # TODO: Review unreachable code - interval = duration / (max_frames + 1)

        # TODO: Review unreachable code - # Extract frames at intervals
        # TODO: Review unreachable code - for i in range(1, max_frames + 1):
        # TODO: Review unreachable code - timestamp = i * interval

        # TODO: Review unreachable code - # Use ffmpeg to extract frame at timestamp
        # TODO: Review unreachable code - cmd = [
        # TODO: Review unreachable code - "ffmpeg",
        # TODO: Review unreachable code - "-ss", str(timestamp),
        # TODO: Review unreachable code - "-i", str(video_path),
        # TODO: Review unreachable code - "-frames:v", "1",
        # TODO: Review unreachable code - "-f", "image2pipe",
        # TODO: Review unreachable code - "-vcodec", "mjpeg",
        # TODO: Review unreachable code - "-loglevel", "error",
        # TODO: Review unreachable code - "-"
        # TODO: Review unreachable code - ]

        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - result = subprocess.run(cmd, capture_output=True, check=True)
        # TODO: Review unreachable code - if result.stdout:
        # TODO: Review unreachable code - keyframes.append(result.stdout)
        # TODO: Review unreachable code - except subprocess.CalledProcessError as e:
        # TODO: Review unreachable code - logger.debug(f"Failed to extract frame at {timestamp}s: {e}")
        # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - except Exception as e:
        logger.error(f"Error extracting keyframes from {video_path}: {e}")

    return keyframes


# TODO: Review unreachable code - def hash_video_keyframes(video_path: Path, max_frames: int = 10) -> str:
# TODO: Review unreachable code - """Hash video content based on keyframes.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - video_path: Path to video file
# TODO: Review unreachable code - max_frames: Maximum number of keyframes to extract

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - SHA-256 hash of video keyframes
# TODO: Review unreachable code - """
# TODO: Review unreachable code - hasher = hashlib.sha256()

# TODO: Review unreachable code - # Extract keyframes
# TODO: Review unreachable code - keyframes = extract_keyframes(video_path, max_frames)

# TODO: Review unreachable code - if not keyframes:
# TODO: Review unreachable code - logger.warning(f"No keyframes extracted from {video_path}, using file hash")
# TODO: Review unreachable code - # Fall back to file hash
# TODO: Review unreachable code - with open(video_path, "rb") as f:
# TODO: Review unreachable code - while chunk := f.read(8192):
# TODO: Review unreachable code - hasher.update(chunk)
# TODO: Review unreachable code - return hasher.hexdigest()

# TODO: Review unreachable code - # Hash all keyframes in order
# TODO: Review unreachable code - for frame_data in keyframes:
# TODO: Review unreachable code - hasher.update(frame_data)

# TODO: Review unreachable code - # Include video metadata in hash
# TODO: Review unreachable code - info = extract_video_info(video_path)
# TODO: Review unreachable code - if info:
# TODO: Review unreachable code - # Add video dimensions and codec to hash
# TODO: Review unreachable code - for stream in info.get("streams", []):
# TODO: Review unreachable code - if stream.get("codec_type") == "video":
# TODO: Review unreachable code - hasher.update(f"{stream.get('width', 0)}x{stream.get('height', 0)}".encode())
# TODO: Review unreachable code - hasher.update(stream.get("codec_name", "").encode())
# TODO: Review unreachable code - break

# TODO: Review unreachable code - logger.debug(f"Hashed {len(keyframes)} keyframes from {video_path.name}")
# TODO: Review unreachable code - return hasher.hexdigest()


# TODO: Review unreachable code - def hash_video_stream_only(video_path: Path) -> str:
# TODO: Review unreachable code - """Hash only the video stream data, excluding container metadata.

# TODO: Review unreachable code - This is faster than keyframe extraction but still excludes metadata.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - video_path: Path to video file

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - SHA-256 hash of video stream
# TODO: Review unreachable code - """
# TODO: Review unreachable code - hasher = hashlib.sha256()

# TODO: Review unreachable code - try:
# TODO: Review unreachable code - # Use ffmpeg to extract raw video stream
# TODO: Review unreachable code - cmd = [
# TODO: Review unreachable code - "ffmpeg",
# TODO: Review unreachable code - "-i", str(video_path),
# TODO: Review unreachable code - "-c:v", "copy",  # Copy video codec, no re-encoding
# TODO: Review unreachable code - "-an",  # No audio
# TODO: Review unreachable code - "-f", "rawvideo",  # Raw video output
# TODO: Review unreachable code - "-loglevel", "error",
# TODO: Review unreachable code - "-"
# TODO: Review unreachable code - ]

# TODO: Review unreachable code - process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# TODO: Review unreachable code - # Hash the stream data in chunks
# TODO: Review unreachable code - while True:
# TODO: Review unreachable code - chunk = process.stdout.read(8192)
# TODO: Review unreachable code - if not chunk:
# TODO: Review unreachable code - break
# TODO: Review unreachable code - hasher.update(chunk)

# TODO: Review unreachable code - process.wait()

# TODO: Review unreachable code - if process.returncode == 0:
# TODO: Review unreachable code - return hasher.hexdigest()
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - logger.warning(f"ffmpeg failed with code {process.returncode}")

# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.error(f"Error hashing video stream: {e}")

# TODO: Review unreachable code - # Fall back to file hash
# TODO: Review unreachable code - with open(video_path, "rb") as f:
# TODO: Review unreachable code - hasher = hashlib.sha256()
# TODO: Review unreachable code - while chunk := f.read(8192):
# TODO: Review unreachable code - hasher.update(chunk)
# TODO: Review unreachable code - return hasher.hexdigest()
