"""Constants used throughout AliceMultiverse."""

# Version information
VERSION = "2.0.0"
CACHE_VERSION = "3.0"

# Directory names
METADATA_DIR_NAME = ".metadata"
DEFAULT_INBOX = "inbox"
DEFAULT_ORGANIZED = "organized"
UNCATEGORIZED_PROJECT = "uncategorized"

# Quality rating constants
MIN_QUALITY_STARS = 1
MAX_QUALITY_STARS = 5
QUALITY_STAR_RANGE = range(MIN_QUALITY_STARS, MAX_QUALITY_STARS + 1)

# File size limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MIN_FILE_SIZE = 1024  # 1 KB

# Quality assessment constants
BRISQUE_MAX_DIMENSION = 2048
HASH_CHUNK_SIZE = 4096

# API rate limits (requests per minute)
SIGHTENGINE_RATE_LIMIT = 60
CLAUDE_RATE_LIMIT = 10

# Cost per image (USD)
COSTS = {
    "brisque": 0.0,
    "sightengine": 0.001,
    "claude": 0.002,  # Haiku model default
    "gpt4v": 0.01,
}

# Date format for output folders
OUTPUT_DATE_FORMAT = "%Y-%m-%d"

# Number formatting
SEQUENCE_DIGITS = 5
SEQUENCE_FORMAT = "{:05d}"

# File extensions - AI-generated content focus
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}

# AI generator signatures
AI_IMAGE_GENERATORS = [
    "stablediffusion",
    "midjourney",
    "dalle",
    "comfyui",
    "flux",
    "leonardo",
    "firefly",
]

AI_VIDEO_GENERATORS = [
    "runway",
    "kling",
    "pika",
    "stable-video",
    "animatediff",
    "deforum",
    "modelscope",
    "zeroscope",
    "haiper",
    "genmo",
]

# Logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
