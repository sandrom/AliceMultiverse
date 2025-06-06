"""
CLI commands for transition analysis.
"""

import click
import json
from pathlib import Path
from typing import List

from .transition_matcher import TransitionMatcher
from ..core.logging import setup_logging


@click.group()
def transitions():
    """Analyze and suggest transitions between images."""
    pass


@transitions.command()
@click.argument('images', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(images: List[str], output: str, verbose: bool):
    """
    Analyze transitions between a sequence of images.
    
    Example:
        alice transitions analyze img1.jpg img2.jpg img3.jpg -o transitions.json
    """
    setup_logging(debug=verbose)
    
    if len(images) < 2:
        click.echo("Error: Need at least 2 images to analyze transitions", err=True)
        return
        
    click.echo(f"Analyzing transitions for {len(images)} images...")
    
    # Create matcher and analyze
    matcher = TransitionMatcher()
    suggestions = matcher.analyze_sequence(list(images))
    
    # Display results
    for i, suggestion in enumerate(suggestions):
        click.echo(f"\nTransition {i+1}: {Path(suggestion.source_image).name} → {Path(suggestion.target_image).name}")
        click.echo(f"  Type: {suggestion.transition_type.value}")
        click.echo(f"  Duration: {suggestion.duration:.2f}s")
        click.echo(f"  Confidence: {suggestion.confidence:.2%}")
        
        if suggestion.compatibility:
            comp = suggestion.compatibility
            click.echo(f"  Compatibility:")
            click.echo(f"    - Motion continuity: {comp.motion_continuity:.2%}")
            click.echo(f"    - Color harmony: {comp.color_harmony:.2%}")
            click.echo(f"    - Composition match: {comp.composition_match:.2%}")
            
            if comp.notes:
                click.echo(f"  Notes:")
                for note in comp.notes:
                    click.echo(f"    - {note}")
                    
        if verbose and suggestion.effects:
            click.echo(f"  Effects: {json.dumps(suggestion.effects, indent=4)}")
            
    # Save to file if requested
    if output:
        output_data = []
        for suggestion in suggestions:
            data = {
                'source': suggestion.source_image,
                'target': suggestion.target_image,
                'transition': suggestion.transition_type.value,
                'duration': suggestion.duration,
                'confidence': suggestion.confidence,
                'effects': suggestion.effects or {}
            }
            if suggestion.compatibility:
                data['compatibility'] = {
                    'overall': suggestion.compatibility.overall_score,
                    'motion': suggestion.compatibility.motion_continuity,
                    'color': suggestion.compatibility.color_harmony,
                    'composition': suggestion.compatibility.composition_match,
                    'notes': suggestion.compatibility.notes
                }
            output_data.append(data)
            
        with open(output, 'w') as f:
            json.dump(output_data, f, indent=2)
        click.echo(f"\nResults saved to: {output}")


@transitions.command()
@click.argument('image', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def motion(image: str, verbose: bool):
    """
    Analyze motion characteristics of a single image.
    
    Example:
        alice transitions motion image.jpg
    """
    setup_logging(debug=verbose)
    
    from .motion_analyzer import MotionAnalyzer
    
    click.echo(f"Analyzing motion in: {image}")
    
    analyzer = MotionAnalyzer()
    result = analyzer.analyze_image(image)
    
    if not result:
        click.echo("Error: Could not analyze image", err=True)
        return
        
    # Display motion analysis
    motion = result['motion']
    click.echo(f"\nMotion Analysis:")
    click.echo(f"  Direction: {motion.direction.value}")
    click.echo(f"  Speed: {motion.speed:.2%}")
    click.echo(f"  Focal point: ({motion.focal_point[0]:.2f}, {motion.focal_point[1]:.2f})")
    click.echo(f"  Confidence: {motion.confidence:.2%}")
    click.echo(f"  Motion lines detected: {len(motion.motion_lines)}")
    
    # Display composition
    comp = result['composition']
    click.echo(f"\nComposition Analysis:")
    click.echo(f"  Rule of thirds points: {len(comp.rule_of_thirds_points)}")
    click.echo(f"  Leading lines: {len(comp.leading_lines)}")
    click.echo(f"  Visual weight center: ({comp.visual_weight_center[0]:.2f}, {comp.visual_weight_center[1]:.2f})")
    click.echo(f"  Empty regions: {len(comp.empty_space_regions)}")
    
    # Display colors
    colors = result['colors']
    click.echo(f"\nColor Analysis:")
    click.echo(f"  Temperature: {colors['temperature']}")
    click.echo(f"  Brightness: {colors['brightness']:.0f}")
    click.echo(f"  Saturation: {colors['saturation']:.0f}")
    click.echo(f"  Contrast: {colors['contrast']:.0f}")
    
    if verbose:
        click.echo(f"\nDominant colors:")
        for color, pct in comp.dominant_colors[:5]:
            click.echo(f"  {color}: {pct:.1%}")
            
        click.echo(f"\nBrightness distribution:")
        for quad, brightness in comp.brightness_map.items():
            click.echo(f"  {quad}: {brightness:.2%}")