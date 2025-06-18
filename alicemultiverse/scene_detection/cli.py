"""
CLI commands for scene detection and shot list generation.
"""

import json
from pathlib import Path

import click

from ..core.logging import setup_logging
from .scene_detector import SceneDetector
from .shot_list_generator import ShotListGenerator


@click.group()
def scenes():
    """Detect scenes and generate shot lists."""


@scenes.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
@click.option('--threshold', '-t', type=float, default=0.3, help='Detection threshold (0-1)')
@click.option('--min-duration', type=float, default=1.0, help='Minimum scene duration (seconds)')
@click.option('--use-ai/--no-ai', default=True, help='Use AI for scene analysis')
@click.option('--ai-provider', type=str, help='AI provider for analysis')
@click.option('--group-similar/--individual', default=True, help='Group similar images (for image sequences)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def detect(
    input_path: str,
    output: str | None,
    threshold: float,
    min_duration: float,
    use_ai: bool,
    ai_provider: str | None,
    group_similar: bool,
    verbose: bool
):
    """
    Detect scenes in a video or image sequence.

    Examples:
        alice scenes detect video.mp4 -o scenes.json
        alice scenes detect ./images/ --group-similar
    """
    setup_logging(debug=verbose)

    input_path = Path(input_path)
    detector = SceneDetector(
        threshold=threshold,
        min_scene_duration=min_duration,
        use_ai=use_ai,
        ai_provider=ai_provider
    )

    # Check if input is video or directory
    if input_path.is_file():
        # Video file
        click.echo(f"Detecting scenes in video: {input_path}")
        scenes = detector.detect_video_scenes(input_path)

    elif input_path.is_dir():
        # Image directory
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        images = sorted([
            f for f in input_path.iterdir()
            if f.suffix.lower() in image_extensions
        ])

        if not images:
            click.echo("No images found in directory", err=True)
            return

        click.echo(f"Detecting scenes in {len(images)} images...")
        scenes = detector.detect_image_sequence_scenes(images, group_similar)

    else:
        click.echo("Input must be a video file or directory", err=True)
        return

    # Display results
    click.echo(f"\nDetected {len(scenes)} scenes:")

    for scene in scenes:
        if scene.duration > 0:
            click.echo(
                f"\n{scene.scene_id}: {scene.scene_type.value} "
                f"({scene.start_time:.1f}s - {scene.end_time:.1f}s)"
            )
        else:
            click.echo(
                f"\n{scene.scene_id}: {scene.scene_type.value} "
                f"({len(scene.images)} images)"
            )

        if scene.ai_description:
            click.echo(f"  Description: {scene.ai_description}")
        if scene.dominant_subject:
            click.echo(f"  Subject: {scene.dominant_subject}")
        if scene.mood:
            click.echo(f"  Mood: {scene.mood}")
        if scene.ai_tags:
            click.echo(f"  Tags: {', '.join(scene.ai_tags[:5])}")

    # Save results
    if output:
        detector.export_scenes(scenes, output)
        click.echo(f"\nSaved scene data to: {output}")


@scenes.command()
@click.argument('scenes_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), required=True, help='Output file')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'markdown']), default='json')
@click.option('--project-name', '-p', default='Untitled Project', help='Project name')
@click.option('--style', '-s', type=click.Choice(['cinematic', 'documentary', 'commercial']), default='cinematic')
@click.option('--shot-duration', type=(float, float), default=(2.0, 8.0), help='Min/max shot duration')
@click.option('--use-ai/--no-ai', default=True, help='Use AI for suggestions')
@click.option('--ai-provider', type=str, help='AI provider')
@click.option('--target-duration', type=float, help='Target total duration')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def shotlist(
    scenes_file: str,
    output: str,
    format: str,
    project_name: str,
    style: str,
    shot_duration: tuple,
    use_ai: bool,
    ai_provider: str | None,
    target_duration: float | None,
    verbose: bool
):
    """
    Generate a shot list from detected scenes.

    Example:
        alice scenes shotlist scenes.json -o shotlist.md --format markdown
    """
    setup_logging(debug=verbose)

    # Load scenes
    with open(scenes_file) as f:
        data = json.load(f)

    # Reconstruct scene objects
    from .models import DetectionMethod, Scene, SceneType

    scenes = []
    for scene_data in data['scenes']:
        scene = Scene(
            scene_id=scene_data['id'],
            scene_type=SceneType(scene_data['type']),
            start_time=scene_data['start_time'],
            end_time=scene_data['end_time'],
            duration=scene_data['duration'],
            ai_description=scene_data.get('description'),
            ai_tags=scene_data.get('tags', []),
            dominant_subject=scene_data.get('subject'),
            mood=scene_data.get('mood'),
            confidence=scene_data.get('confidence', 1.0),
            detection_method=DetectionMethod.CONTENT
        )

        if scene_data.get('frames'):
            scene.start_frame = scene_data['frames'][0]
            scene.end_frame = scene_data['frames'][1]

        if scene_data.get('images'):
            scene.images = [Path(p) for p in scene_data['images']]

        scenes.append(scene)

    # Generate shot list
    click.echo(f"Generating {style} shot list for {len(scenes)} scenes...")

    generator = ShotListGenerator(
        style=style,
        shot_duration_range=shot_duration,
        use_ai_suggestions=use_ai,
        ai_provider=ai_provider
    )

    shot_list = generator.generate_shot_list(
        scenes,
        project_name=project_name,
        target_duration=target_duration
    )

    # Display summary
    click.echo("\nGenerated shot list:")
    click.echo(f"  Project: {shot_list.project_name}")
    click.echo(f"  Total duration: {shot_list.total_duration:.1f}s")
    click.echo(f"  Scenes: {shot_list.scene_count}")
    click.echo(f"  Shots: {shot_list.shot_count}")
    click.echo(f"  Average shot: {shot_list.average_shot_duration:.1f}s")

    # Export
    generator.export_shot_list(shot_list, Path(output), format)
    click.echo(f"\nExported to: {output}")


@scenes.command()
@click.argument('video', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory for shots')
@click.option('--format', '-f', type=click.Choice(['jpg', 'png']), default='jpg')
@click.option('--scenes-file', type=click.Path(exists=True), help='Use existing scenes JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def extract(
    video: str,
    output: str | None,
    format: str,
    scenes_file: str | None,
    verbose: bool
):
    """
    Extract representative frames from video scenes.

    Example:
        alice scenes extract video.mp4 -o ./shots/
    """
    setup_logging(debug=verbose)

    import cv2

    video_path = Path(video)
    output_dir = Path(output) if output else video_path.parent / f"{video_path.stem}_shots"
    output_dir.mkdir(exist_ok=True)

    # Load or detect scenes
    if scenes_file:
        with open(scenes_file) as f:
            data = json.load(f)
        scenes_data = data['scenes']
    else:
        click.echo("Detecting scenes first...")
        detector = SceneDetector()
        scenes = detector.detect_video_scenes(video_path)
        scenes_data = [
            {
                'id': s.scene_id,
                'frames': [s.start_frame, s.end_frame]
            }
            for s in scenes
        ]

    # Extract frames
    cap = cv2.VideoCapture(str(video_path))

    try:
        click.echo(f"Extracting frames to {output_dir}...")

        for scene_data in scenes_data:
            scene_id = scene_data['id']

            if scene_data.get('frames'):
                # Get middle frame
                start_frame = scene_data['frames'][0]
                end_frame = scene_data['frames'][1]
                middle_frame = (start_frame + end_frame) // 2

                # Extract frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
                ret, frame = cap.read()

                if ret:
                    output_path = output_dir / f"{scene_id}.{format}"
                    cv2.imwrite(str(output_path), frame)
                    click.echo(f"  Extracted {scene_id}")

    finally:
        cap.release()

    click.echo(f"\nExtracted {len(scenes_data)} frames")


# Add to main CLI
def add_to_cli(cli):
    """Add scenes commands to main CLI."""
    cli.add_command(scenes)
