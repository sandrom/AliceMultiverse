"""Example of using mmaudio for video-to-audio generation.

This example shows how to add synchronized audio to a video using mmaudio-v2.
"""

import asyncio
import logging
from pathlib import Path

from alicemultiverse.interface import AliceInterface
from alicemultiverse.interface.models import (
    GenerateRequest,
    GenerationType,
    AssetMetadata
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_audio_for_video():
    """Generate synchronized audio for a video using mmaudio."""
    
    alice = AliceInterface()
    
    # Example 1: Generate audio for a video with a specific prompt
    logger.info("Generating audio for video...")
    
    # Assume we have a video file or URL
    video_url = "https://example.com/my-video.mp4"  # Replace with actual video URL
    
    # You can also upload a local video first if needed
    # video_asset = await alice.upload_asset("path/to/local/video.mp4")
    # video_url = video_asset.url
    
    request = GenerateRequest(
        prompt="Upbeat electronic music with synthesizer sounds",
        model="mmaudio-v2",
        provider="fal",
        generation_type=GenerationType.AUDIO,  # Even though it returns video
        parameters={
            "video_url": video_url,
            "negative_prompt": "silence, noise, distortion",
            "num_steps": 25,
            "duration": 8,  # seconds
            "cfg_strength": 4.5,
            "mask_away_clip": False
        }
    )
    
    result = await alice.generate(request)
    logger.info(f"Generated video with audio saved to: {result.file_path}")
    logger.info(f"Generation cost: ${result.cost:.4f}")
    
    # Example 2: Generate nature sounds for a nature video
    nature_request = GenerateRequest(
        prompt="Natural forest ambience with birds chirping and wind through trees",
        model="mmaudio-v2", 
        provider="fal",
        generation_type=GenerationType.AUDIO,
        parameters={
            "video_url": "https://example.com/nature-scene.mp4",
            "negative_prompt": "music, human voices, artificial sounds",
            "duration": 10,
            "cfg_strength": 5.0  # Higher for more adherence to prompt
        }
    )
    
    nature_result = await alice.generate(nature_request)
    logger.info(f"Nature video with audio: {nature_result.file_path}")
    
    # Example 3: Generate dialogue/voice for a talking head video
    dialogue_request = GenerateRequest(
        prompt="Clear human speech, professional voiceover",
        model="mmaudio-v2",
        provider="fal", 
        generation_type=GenerationType.AUDIO,
        parameters={
            "video_url": "https://example.com/talking-head.mp4",
            "negative_prompt": "background music, echo, distortion",
            "cfg_strength": 6.0,  # Even higher for speech clarity
            "mask_away_clip": True  # May help with speech generation
        }
    )
    
    dialogue_result = await alice.generate(dialogue_request)
    logger.info(f"Video with dialogue: {dialogue_result.file_path}")
    
    # Example 4: Batch process multiple videos
    video_prompts = [
        ("video1.mp4", "Cinematic orchestral music, epic and dramatic"),
        ("video2.mp4", "Jazz piano with soft drums, relaxing mood"),
        ("video3.mp4", "Action movie sound effects, explosions and tension"),
    ]
    
    for video_url, prompt in video_prompts:
        batch_request = GenerateRequest(
            prompt=prompt,
            model="mmaudio-v2",
            provider="fal",
            generation_type=GenerationType.AUDIO,
            parameters={
                "video_url": f"https://example.com/{video_url}",
                "duration": 8
            }
        )
        
        try:
            result = await alice.generate(batch_request)
            logger.info(f"Generated audio for {video_url}: {result.file_path}")
        except Exception as e:
            logger.error(f"Failed to generate audio for {video_url}: {e}")


async def main():
    """Run the examples."""
    try:
        await generate_audio_for_video()
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())