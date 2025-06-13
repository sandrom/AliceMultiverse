"""MCP tools for enhanced video generation with multiple providers."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..providers.simple_registry import get_provider
from ..providers.types import GenerationRequest, GenerationType

logger = logging.getLogger(__name__)

# MCP decorators will be added by the server when importing these functions


async def generate_video_runway(
    prompt: str,
    model: str = "gen3-alpha",
    duration: int = 5,
    camera_motion: str | None = None,
    motion_amount: float | None = None,
    seed: int | None = None,
    output_path: str | None = None,
    input_image: str | None = None
) -> dict[str, Any]:
    """Generate professional video using Runway Gen-3 Alpha.

    Args:
        prompt: Text description for video generation
        model: Model to use (gen3-alpha, gen3-alpha-turbo)
        duration: Video duration in seconds (5-10)
        camera_motion: Camera movement (static, zoom_in, zoom_out, pan_left, pan_right)
        motion_amount: Amount of motion (0.0-1.0)
        seed: Random seed for reproducibility
        output_path: Where to save the video
        input_image: Optional image for image-to-video

    Returns:
        Generation result with video path and metadata
    """
    try:
        provider = get_provider("runway")

        # Build parameters
        parameters = {
            "duration": duration
        }

        if camera_motion:
            parameters["camera_motion"] = camera_motion

        if motion_amount is not None:
            parameters["motion_amount"] = motion_amount

        if seed is not None:
            parameters["seed"] = seed

        # Create request
        request = GenerationRequest(
            prompt=prompt,
            model=model,
            generation_type=GenerationType.VIDEO,
            parameters=parameters,
            output_path=Path(output_path) if output_path else None,
            reference_assets=[input_image] if input_image else None
        )

        # Generate
        result = await provider.generate(request)

        return {
            "success": result.success,
            "video_path": str(result.file_path) if result.file_path else None,
            "cost": result.cost,
            "provider": "runway",
            "model": model,
            "duration": duration,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Runway generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": "runway"
        }


async def generate_video_pika(
    prompt: str,
    model: str = "pika-2.1-hd",
    duration: int = 3,
    aspect_ratio: str = "16:9",
    camera_control: dict[str, Any] | None = None,
    ingredients: list[str] | None = None,
    lip_sync_audio: str | None = None,
    output_path: str | None = None,
    input_image: str | None = None
) -> dict[str, Any]:
    """Generate HD video using Pika 2.1 with ingredient control.

    Args:
        prompt: Text description for video generation
        model: Model to use (pika-2.1, pika-2.1-hd)
        duration: Video duration in seconds (3-10)
        aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4)
        camera_control: Camera movement parameters
        ingredients: List of elements to control in the video
        lip_sync_audio: Audio file for lip sync
        output_path: Where to save the video
        input_image: Optional image for image-to-video

    Returns:
        Generation result with video path and metadata
    """
    try:
        provider = get_provider("pika")

        # Build parameters
        parameters = {
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }

        if camera_control:
            parameters["camera_control"] = camera_control

        if ingredients:
            parameters["ingredients"] = ingredients

        if lip_sync_audio:
            parameters["lip_sync_audio"] = lip_sync_audio
            model = "pika-lip-sync"  # Use lip sync model

        # Create request
        request = GenerationRequest(
            prompt=prompt,
            model=model,
            generation_type=GenerationType.VIDEO,
            parameters=parameters,
            output_path=Path(output_path) if output_path else None,
            reference_assets=[input_image] if input_image else None
        )

        # Generate
        result = await provider.generate(request)

        return {
            "success": result.success,
            "video_path": str(result.file_path) if result.file_path else None,
            "cost": result.cost,
            "provider": "pika",
            "model": model,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Pika generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": "pika"
        }


async def generate_video_luma(
    prompt: str,
    enhance_prompt: bool = True,
    aspect_ratio: str = "16:9",
    loop: bool = False,
    keyframes: dict[str, Any] | None = None,
    output_path: str | None = None,
    start_image: str | None = None,
    end_image: str | None = None
) -> dict[str, Any]:
    """Generate video using Luma Dream Machine with advanced controls.

    Args:
        prompt: Text description for video generation
        enhance_prompt: Whether to enhance prompt with AI
        aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4, 21:9)
        loop: Whether to create a seamless loop
        keyframes: Keyframe specifications for control
        output_path: Where to save the video
        start_image: Optional starting image
        end_image: Optional ending image for interpolation

    Returns:
        Generation result with video path and metadata
    """
    try:
        provider = get_provider("luma")

        # Build parameters
        parameters = {
            "enhance_prompt": enhance_prompt,
            "aspect_ratio": aspect_ratio,
            "loop": loop
        }

        if keyframes:
            parameters["keyframes"] = keyframes

        if end_image:
            parameters["end_image"] = end_image

        # Create request
        request = GenerationRequest(
            prompt=prompt,
            model="dream-machine",
            generation_type=GenerationType.VIDEO,
            parameters=parameters,
            output_path=Path(output_path) if output_path else None,
            reference_assets=[start_image] if start_image else None
        )

        # Generate
        result = await provider.generate(request)

        return {
            "success": result.success,
            "video_path": str(result.file_path) if result.file_path else None,
            "cost": result.cost,
            "provider": "luma",
            "model": "dream-machine",
            "aspect_ratio": aspect_ratio,
            "loop": loop,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Luma generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": "luma"
        }


async def generate_video_minimax(
    prompt: str,
    prompt_optimizer: bool = True,
    duration: int = 6,
    resolution: str = "1280x720",
    camera_mode: str | None = None,
    output_path: str | None = None,
    input_image: str | None = None
) -> dict[str, Any]:
    """Generate video using MiniMax Hailuo with competitive quality.

    Args:
        prompt: Text description for video generation
        prompt_optimizer: Whether to optimize prompt automatically
        duration: Video duration in seconds (5-10)
        resolution: Video resolution (1280x720, 1080x1080, 720x1280)
        camera_mode: Camera movement preset
        output_path: Where to save the video
        input_image: Optional image for image-to-video

    Returns:
        Generation result with video path and metadata
    """
    try:
        provider = get_provider("minimax")

        # Build parameters
        parameters = {
            "prompt_optimizer": prompt_optimizer,
            "duration": duration,
            "resolution": resolution
        }

        if camera_mode:
            parameters["camera_mode"] = camera_mode

        # Create request
        request = GenerationRequest(
            prompt=prompt,
            model="hailuo-video",
            generation_type=GenerationType.VIDEO,
            parameters=parameters,
            output_path=Path(output_path) if output_path else None,
            reference_assets=[input_image] if input_image else None
        )

        # Generate
        result = await provider.generate(request)

        return {
            "success": result.success,
            "video_path": str(result.file_path) if result.file_path else None,
            "cost": result.cost,
            "provider": "minimax",
            "model": "hailuo-video",
            "duration": duration,
            "resolution": resolution,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"MiniMax generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": "minimax"
        }


async def generate_video_kling(
    prompt: str,
    model: str = "kling-v1.5",
    duration: int = 5,
    aspect_ratio: str = "16:9",
    quality: str = "professional",
    motion_strength: float = 0.5,
    camera_movement: str | None = None,
    output_path: str | None = None,
    input_image: str | None = None
) -> dict[str, Any]:
    """Generate cinematic video using Kling AI with professional quality.

    Args:
        prompt: Text description for video generation
        model: Model to use (kling-v1, kling-v1.5, kling-v2)
        duration: Video duration in seconds (5-10)
        aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1, 4:3)
        quality: Quality preset (standard, professional, cinematic)
        motion_strength: Motion intensity (0.0-1.0)
        camera_movement: Camera motion (static, pan, zoom, orbit)
        output_path: Where to save the video
        input_image: Optional image for image-to-video

    Returns:
        Generation result with video path and metadata
    """
    try:
        provider = get_provider("kling")

        # Build parameters
        parameters = {
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "quality": quality,
            "motion_strength": motion_strength
        }

        if camera_movement:
            parameters["camera_movement"] = camera_movement

        # Create request
        request = GenerationRequest(
            prompt=prompt,
            model=model,
            generation_type=GenerationType.VIDEO,
            parameters=parameters,
            output_path=Path(output_path) if output_path else None,
            reference_assets=[input_image] if input_image else None
        )

        # Generate
        result = await provider.generate(request)

        return {
            "success": result.success,
            "video_path": str(result.file_path) if result.file_path else None,
            "cost": result.cost,
            "provider": "kling",
            "model": model,
            "duration": duration,
            "quality": quality,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Kling generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": "kling"
        }


async def generate_video_hedra(
    prompt: str,
    audio_input: str,
    avatar_image: str | None = None,
    voice_id: str | None = None,
    aspect_ratio: str = "1:1",
    output_path: str | None = None
) -> dict[str, Any]:
    """Generate AI avatar video using Hedra Character API.

    Args:
        prompt: Text for the avatar to speak
        audio_input: Path to audio file or text for TTS
        avatar_image: Optional avatar image (will use default if not provided)
        voice_id: Voice ID for text-to-speech (if audio_input is text)
        aspect_ratio: Video aspect ratio (1:1, 16:9, 9:16)
        output_path: Where to save the video

    Returns:
        Generation result with video path and metadata
    """
    try:
        provider = get_provider("hedra")

        # Build parameters
        parameters = {
            "aspect_ratio": aspect_ratio
        }

        if voice_id:
            parameters["voice_id"] = voice_id

        # Determine if audio_input is a file path or text
        if Path(audio_input).exists():
            parameters["audio_file"] = audio_input
        else:
            parameters["text"] = audio_input

        # Create request
        request = GenerationRequest(
            prompt=prompt,  # For Hedra, prompt is the text to speak
            model="character-2",
            generation_type=GenerationType.VIDEO,
            parameters=parameters,
            output_path=Path(output_path) if output_path else None,
            reference_assets=[avatar_image] if avatar_image else None
        )

        # Generate
        result = await provider.generate(request)

        return {
            "success": result.success,
            "video_path": str(result.file_path) if result.file_path else None,
            "cost": result.cost,
            "provider": "hedra",
            "model": "character-2",
            "aspect_ratio": aspect_ratio,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Hedra generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": "hedra"
        }


async def compare_video_providers(
    prompt: str,
    providers: list[str] | None = None,
    output_dir: str | None = None,
    compare_quality: bool = True,
    compare_cost: bool = True,
    compare_speed: bool = True
) -> dict[str, Any]:
    """Generate videos with multiple providers for comparison.

    Args:
        prompt: Text description for video generation
        providers: List of providers to compare (default: all)
        output_dir: Directory to save comparison videos
        compare_quality: Include quality metrics
        compare_cost: Include cost comparison
        compare_speed: Include generation time

    Returns:
        Comparison results with videos and metrics
    """
    if not providers:
        providers = ["runway", "pika", "luma", "minimax", "veo3"]

    output_dir = Path(output_dir) if output_dir else Path("comparisons") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    tasks = []

    # Create generation tasks for each provider
    for provider_name in providers:
        if provider_name == "runway":
            task = generate_video_runway(
                prompt=prompt,
                output_path=str(output_dir / "runway_gen3.mp4")
            )
        elif provider_name == "pika":
            task = generate_video_pika(
                prompt=prompt,
                output_path=str(output_dir / "pika_hd.mp4")
            )
        elif provider_name == "luma":
            task = generate_video_luma(
                prompt=prompt,
                output_path=str(output_dir / "luma_dream.mp4")
            )
        elif provider_name == "minimax":
            task = generate_video_minimax(
                prompt=prompt,
                output_path=str(output_dir / "minimax_hailuo.mp4")
            )
        elif provider_name == "veo3":
            # Import Veo3 function
            from .video_creation_mcp import generate_video_veo3
            task = generate_video_veo3(
                prompt=prompt,
                output_path=str(output_dir / "google_veo3.mp4")
            )
        elif provider_name == "kling":
            task = generate_video_kling(
                prompt=prompt,
                output_path=str(output_dir / "kling_cinematic.mp4")
            )
        else:
            continue

        tasks.append((provider_name, task))

    # Run all generations in parallel
    start_times = {}
    for provider_name, task in tasks:
        start_times[provider_name] = datetime.now()

    task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

    # Process results
    for (provider_name, _), result in zip(tasks, task_results, strict=False):
        if isinstance(result, Exception):
            results[provider_name] = {
                "success": False,
                "error": str(result)
            }
        else:
            end_time = datetime.now()
            generation_time = (end_time - start_times[provider_name]).total_seconds()

            results[provider_name] = {
                **result,
                "generation_time": generation_time
            }

    # Build comparison summary
    comparison = {
        "prompt": prompt,
        "output_directory": str(output_dir),
        "providers": results,
        "summary": {
            "total_providers": len(providers),
            "successful": sum(1 for r in results.values() if r.get("success", False)),
            "failed": sum(1 for r in results.values() if not r.get("success", False))
        }
    }

    if compare_cost:
        comparison["cost_analysis"] = {
            provider: result.get("cost", 0)
            for provider, result in results.items()
            if result.get("success", False)
        }
        comparison["summary"]["total_cost"] = sum(comparison["cost_analysis"].values())
        comparison["summary"]["cheapest"] = min(
            comparison["cost_analysis"].items(),
            key=lambda x: x[1]
        )[0] if comparison["cost_analysis"] else None

    if compare_speed:
        comparison["speed_analysis"] = {
            provider: result.get("generation_time", 0)
            for provider, result in results.items()
            if result.get("success", False)
        }
        comparison["summary"]["fastest"] = min(
            comparison["speed_analysis"].items(),
            key=lambda x: x[1]
        )[0] if comparison["speed_analysis"] else None

    if compare_quality:
        # Note: Quality comparison would require additional analysis
        comparison["quality_notes"] = {
            "runway": "Professional cinematic quality, excellent motion",
            "pika": "HD quality with precise control, good for specific shots",
            "luma": "Strong prompt adherence, good for creative concepts",
            "minimax": "Competitive quality, cost-effective option",
            "veo3": "State-of-the-art with native audio support",
            "kling": "Cinematic quality with natural motion, professional presets"
        }

    return comparison


async def estimate_video_costs(
    prompt: str,
    providers: list[str] | None = None,
    duration: int = 5,
    include_details: bool = True
) -> dict[str, Any]:
    """Estimate costs for video generation across providers.

    Args:
        prompt: Text description for estimation
        providers: List of providers to estimate (default: all)
        duration: Video duration in seconds
        include_details: Include detailed breakdown

    Returns:
        Cost estimates for each provider
    """
    if not providers:
        providers = ["runway", "pika", "luma", "minimax", "veo3", "kling"]
        # Note: Hedra is excluded by default as it requires audio input

    estimates = {}

    for provider_name in providers:
        try:
            provider = get_provider(provider_name)

            # Create sample request for estimation
            request = GenerationRequest(
                prompt=prompt,
                generation_type=GenerationType.VIDEO,
                parameters={"duration": duration}
            )

            cost = provider.estimate_cost(request)

            estimates[provider_name] = {
                "estimated_cost": cost,
                "duration": duration,
                "cost_per_second": cost / duration if duration > 0 else 0
            }

            if include_details:
                capabilities = provider.get_capabilities()
                estimates[provider_name]["details"] = {
                    "models": capabilities.models,
                    "max_duration": getattr(provider, "max_duration", 10),
                    "features": capabilities.features,
                    "resolution": capabilities.max_resolution
                }

        except Exception as e:
            estimates[provider_name] = {
                "error": str(e),
                "available": False
            }

    # Summary
    available_estimates = {
        k: v for k, v in estimates.items()
        if "estimated_cost" in v
    }

    summary = {
        "prompt": prompt,
        "duration": duration,
        "providers": estimates,
        "summary": {
            "cheapest": min(
                available_estimates.items(),
                key=lambda x: x[1]["estimated_cost"]
            )[0] if available_estimates else None,
            "most_expensive": max(
                available_estimates.items(),
                key=lambda x: x[1]["estimated_cost"]
            )[0] if available_estimates else None,
            "average_cost": sum(
                v["estimated_cost"] for v in available_estimates.values()
            ) / len(available_estimates) if available_estimates else 0
        }
    }

    return summary


def register_video_providers_tools(server) -> None:
    """Register video provider tools with MCP server.

    Args:
        server: MCP server instance
    """

    # Register each video generation function as a tool
    server.tool()(generate_video_runway)
    server.tool()(generate_video_pika)
    server.tool()(generate_video_luma)
    server.tool()(generate_video_minimax)
    server.tool()(generate_video_kling)
    server.tool()(generate_video_hedra)
    server.tool()(compare_video_providers)
    server.tool()(estimate_video_costs)
