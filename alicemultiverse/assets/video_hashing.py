"""Video content hashing using ffmpeg to extract keyframes."""

import hashlib
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def extract_video_info(video_path: Path) -> Optional[dict]:
    """Extract video information using ffprobe.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Video information dict or None if failed
    """
    try:
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
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe failed for {video_path}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ffprobe output: {e}")
        return None
    except FileNotFoundError:
        logger.error("ffprobe not found. Please install ffmpeg.")
        return None


def extract_keyframes(video_path: Path, max_frames: int = 10) -> List[bytes]:
    """Extract keyframes from video for hashing.
    
    Args:
        video_path: Path to video file
        max_frames: Maximum number of keyframes to extract
        
    Returns:
        List of keyframe data as bytes
    """
    keyframes = []
    
    try:
        # Get video duration
        info = extract_video_info(video_path)
        if not info:
            return keyframes
            
        # Find video stream
        video_stream = None
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break
                
        if not video_stream:
            logger.warning(f"No video stream found in {video_path}")
            return keyframes
            
        # Get duration
        duration = float(info["format"].get("duration", 0))
        if duration <= 0:
            return keyframes
            
        # Calculate intervals for keyframe extraction
        interval = duration / (max_frames + 1)
        
        # Extract frames at intervals
        for i in range(1, max_frames + 1):
            timestamp = i * interval
            
            # Use ffmpeg to extract frame at timestamp
            cmd = [
                "ffmpeg",
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-frames:v", "1",
                "-f", "image2pipe",
                "-vcodec", "mjpeg",
                "-loglevel", "error",
                "-"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, check=True)
                if result.stdout:
                    keyframes.append(result.stdout)
            except subprocess.CalledProcessError as e:
                logger.debug(f"Failed to extract frame at {timestamp}s: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error extracting keyframes from {video_path}: {e}")
        
    return keyframes


def hash_video_keyframes(video_path: Path, max_frames: int = 10) -> str:
    """Hash video content based on keyframes.
    
    Args:
        video_path: Path to video file
        max_frames: Maximum number of keyframes to extract
        
    Returns:
        SHA-256 hash of video keyframes
    """
    hasher = hashlib.sha256()
    
    # Extract keyframes
    keyframes = extract_keyframes(video_path, max_frames)
    
    if not keyframes:
        logger.warning(f"No keyframes extracted from {video_path}, using file hash")
        # Fall back to file hash
        with open(video_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    # Hash all keyframes in order
    for frame_data in keyframes:
        hasher.update(frame_data)
    
    # Include video metadata in hash
    info = extract_video_info(video_path)
    if info:
        # Add video dimensions and codec to hash
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                hasher.update(f"{stream.get('width', 0)}x{stream.get('height', 0)}".encode())
                hasher.update(stream.get("codec_name", "").encode())
                break
    
    logger.debug(f"Hashed {len(keyframes)} keyframes from {video_path.name}")
    return hasher.hexdigest()


def hash_video_stream_only(video_path: Path) -> str:
    """Hash only the video stream data, excluding container metadata.
    
    This is faster than keyframe extraction but still excludes metadata.
    
    Args:
        video_path: Path to video file
        
    Returns:
        SHA-256 hash of video stream
    """
    hasher = hashlib.sha256()
    
    try:
        # Use ffmpeg to extract raw video stream
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-c:v", "copy",  # Copy video codec, no re-encoding
            "-an",  # No audio
            "-f", "rawvideo",  # Raw video output
            "-loglevel", "error",
            "-"
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Hash the stream data in chunks
        while True:
            chunk = process.stdout.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
        
        process.wait()
        
        if process.returncode == 0:
            return hasher.hexdigest()
        else:
            logger.warning(f"ffmpeg failed with code {process.returncode}")
            
    except Exception as e:
        logger.error(f"Error hashing video stream: {e}")
    
    # Fall back to file hash
    with open(video_path, "rb") as f:
        hasher = hashlib.sha256()
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()