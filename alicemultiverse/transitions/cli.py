"""
CLI commands for transition analysis.
"""

import click
import asyncio
import json
from pathlib import Path
from typing import List

from .transition_matcher import TransitionMatcher
from .morphing import MorphingTransitionMatcher, SubjectMorpher
from .color_flow import ColorFlowAnalyzer, analyze_sequence, export_analysis_for_editor
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


@transitions.command()
@click.argument('images', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), required=True, help='Output directory for morph data')
@click.option('--duration', '-d', type=float, default=1.2, help='Morph duration in seconds')
@click.option('--fps', type=float, default=30.0, help='Frames per second for export')
@click.option('--min-similarity', type=float, default=0.6, help='Minimum similarity threshold')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def morph(images: List[str], output: str, duration: float, fps: float, min_similarity: float, verbose: bool):
    """
    Analyze images for subject morphing opportunities.
    
    Creates After Effects compatible morph data for smooth transitions
    between similar subjects across shots.
    
    Example:
        alice transitions morph img1.jpg img2.jpg img3.jpg -o morph_data/
    """
    setup_logging(debug=verbose)
    
    if len(images) < 2:
        click.echo("Error: Need at least 2 images for morphing analysis", err=True)
        return
        
    async def run_analysis():
        click.echo(f"Analyzing {len(images)} images for morphing opportunities...")
        
        # Create output directory
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Analyze for morphing
        matcher = MorphingTransitionMatcher()
        transitions = await matcher.analyze_for_morphing(list(images), min_similarity)
        
        if not transitions:
            click.echo("No suitable morphing transitions found.")
            return
            
        click.echo(f"\nFound {len(transitions)} morphing opportunities:")
        
        # Process each transition
        morpher = SubjectMorpher()
        for i, morph_trans in enumerate(transitions):
            source_name = Path(morph_trans.source_image).name
            target_name = Path(morph_trans.target_image).name
            
            click.echo(f"\n{i+1}. {source_name} → {target_name}")
            click.echo(f"   Duration: {morph_trans.duration:.2f}s")
            click.echo(f"   Matched subjects: {len(morph_trans.subject_pairs)}")
            
            for j, (src_subj, tgt_subj) in enumerate(morph_trans.subject_pairs):
                click.echo(f"     - {src_subj.label} → {tgt_subj.label}")
                
            # Export After Effects data
            export_path = output_dir / f"morph_{i+1:02d}.json"
            export_result = morpher.export_for_after_effects(
                morph_trans, str(export_path), fps
            )
            
            click.echo(f"   Exported: {export_path.name}")
            click.echo(f"   JSX script: {Path(export_result['jsx_path']).name}")
            
        # Create summary
        summary_path = output_dir / "morph_summary.json"
        summary = {
            "total_transitions": len(transitions),
            "fps": fps,
            "default_duration": duration,
            "transitions": [
                {
                    "index": i + 1,
                    "source": Path(t.source_image).name,
                    "target": Path(t.target_image).name,
                    "duration": t.duration,
                    "subjects": len(t.subject_pairs),
                    "files": {
                        "data": f"morph_{i+1:02d}.json",
                        "script": f"morph_{i+1:02d}.jsx"
                    }
                }
                for i, t in enumerate(transitions)
            ]
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        click.echo(f"\nSummary saved to: {summary_path}")
        click.echo("\nTo use in After Effects:")
        click.echo("  1. Open your composition")
        click.echo("  2. File > Scripts > Run Script File...")
        click.echo("  3. Select a .jsx file from the output directory")
    
    asyncio.run(run_analysis())


@transitions.command()
@click.argument('image', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def subjects(image: str, verbose: bool):
    """
    Detect subjects in an image for morphing analysis.
    
    Example:
        alice transitions subjects portrait.jpg
    """
    setup_logging(debug=verbose)
    
    async def detect():
        morpher = SubjectMorpher()
        
        click.echo(f"Detecting subjects in: {image}")
        
        subjects = await morpher.detect_subjects(image)
        
        if not subjects:
            click.echo("No subjects detected in the image.")
            return
            
        click.echo(f"\nDetected {len(subjects)} subjects:")
        
        for i, subject in enumerate(subjects, 1):
            click.echo(f"\n{i}. {subject.label}")
            click.echo(f"   Confidence: {subject.confidence:.2%}")
            click.echo(f"   Position: ({subject.center[0]:.2f}, {subject.center[1]:.2f})")
            click.echo(f"   Area: {subject.area:.2%} of image")
            
            if verbose:
                x, y, w, h = subject.bbox
                click.echo(f"   Bounding box: x={x:.2f}, y={y:.2f}, w={w:.2f}, h={h:.2f}")
                if subject.features:
                    click.echo(f"   Features: {json.dumps(subject.features, indent=6)}")
    
    asyncio.run(detect())


@transitions.command()
@click.argument('images', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory for transition data')
@click.option('--duration', '-d', type=int, default=30, help='Transition duration in frames')
@click.option('--editor', '-e', type=click.Choice(['resolve', 'premiere', 'fcpx', 'fusion']), 
              default='resolve', help='Target video editor')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def colorflow(images: List[str], output: str, duration: int, editor: str, verbose: bool):
    """
    Analyze color flow between shots for smooth color-based transitions.
    
    This command analyzes color palettes, lighting direction, and creates
    gradient transitions with matching data for video editors.
    
    Example:
        alice transitions colorflow shot1.jpg shot2.jpg shot3.jpg -o color_data/
    """
    setup_logging(debug=verbose)
    
    if len(images) < 2:
        click.echo("Error: Need at least 2 images to analyze color flow", err=True)
        return
        
    click.echo(f"Analyzing color flow for {len(images)} images...")
    
    # Analyze sequence
    analyses = analyze_sequence(list(images), duration)
    
    # Display results
    for i, analysis in enumerate(analyses):
        source_name = Path(images[i]).name
        target_name = Path(images[i + 1]).name
        
        click.echo(f"\nTransition {i+1}: {source_name} → {target_name}")
        click.echo(f"  Compatibility: {analysis.compatibility_score:.2%}")
        click.echo(f"  Transition type: {analysis.gradient_transition.transition_type}")
        click.echo(f"  Duration: {analysis.gradient_transition.duration_frames} frames")
        
        # Color information
        click.echo(f"\n  Color Analysis:")
        click.echo(f"    Shot 1 dominant color: RGB{analysis.shot1_palette.dominant_colors[0]}")
        click.echo(f"    Shot 2 dominant color: RGB{analysis.shot2_palette.dominant_colors[0]}")
        click.echo(f"    Temperature shift: {abs(analysis.shot1_palette.color_temperature - analysis.shot2_palette.color_temperature):.2f}")
        click.echo(f"    Brightness change: {abs(analysis.shot1_palette.average_brightness - analysis.shot2_palette.average_brightness):.2f}")
        
        # Lighting information
        click.echo(f"\n  Lighting Analysis:")
        click.echo(f"    Shot 1: {analysis.shot1_lighting.type} (intensity: {analysis.shot1_lighting.intensity:.2f})")
        click.echo(f"    Shot 2: {analysis.shot2_lighting.type} (intensity: {analysis.shot2_lighting.intensity:.2f})")
        
        # Suggested effects
        click.echo(f"\n  Suggested effects:")
        for effect in analysis.suggested_effects[:5]:  # Top 5 effects
            click.echo(f"    - {effect}")
            
        if verbose:
            # Detailed color palette
            click.echo(f"\n  Detailed color palette (Shot 1):")
            for j, (color, weight) in enumerate(zip(analysis.shot1_palette.dominant_colors[:3], 
                                                   analysis.shot1_palette.color_weights[:3])):
                click.echo(f"    {j+1}. RGB{color} ({weight:.1%})")
                
            click.echo(f"\n  Detailed color palette (Shot 2):")
            for j, (color, weight) in enumerate(zip(analysis.shot2_palette.dominant_colors[:3], 
                                                   analysis.shot2_palette.color_weights[:3])):
                click.echo(f"    {j+1}. RGB{color} ({weight:.1%})")
    
    # Export if output directory specified
    if output:
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export individual transitions
        for i, analysis in enumerate(analyses):
            export_path = output_dir / f"colorflow_{i+1:02d}_{editor}.json"
            export_analysis_for_editor(analysis, str(export_path), editor)
            click.echo(f"\nExported transition {i+1} to: {export_path.name}")
            
            # For Resolve, also export LUT if needed
            if editor == 'resolve' and analysis.compatibility_score < 0.7:
                lut_name = export_path.with_suffix('.cube').name
                click.echo(f"  Generated color matching LUT: {lut_name}")
        
        # Create summary file
        summary_path = output_dir / "colorflow_summary.json"
        summary = {
            "shot_count": len(images),
            "transition_count": len(analyses),
            "total_duration_frames": sum(a.gradient_transition.duration_frames for a in analyses),
            "editor": editor,
            "transitions": [
                {
                    "index": i + 1,
                    "source": Path(images[i]).name,
                    "target": Path(images[i + 1]).name,
                    "compatibility": analysis.compatibility_score,
                    "type": analysis.gradient_transition.transition_type,
                    "duration": analysis.gradient_transition.duration_frames,
                    "effects": analysis.suggested_effects[:3]  # Top 3 effects
                }
                for i, analysis in enumerate(analyses)
            ]
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        click.echo(f"\nSummary saved to: {summary_path}")
        click.echo(f"\nTo use in {editor.upper()}:")
        
        if editor == 'resolve':
            click.echo("  1. Open your timeline in DaVinci Resolve")
            click.echo("  2. Import the JSON files into Fusion")
            click.echo("  3. Apply the color flow transitions between clips")
            click.echo("  4. Use generated LUTs for color matching if needed")
        elif editor == 'premiere':
            click.echo("  1. Open your sequence in Premiere Pro")
            click.echo("  2. Import the transition data")
            click.echo("  3. Apply color effects with keyframes from the JSON")
        elif editor == 'fcpx':
            click.echo("  1. Open your project in Final Cut Pro X")
            click.echo("  2. Use the Motion template data from the JSON files")
            click.echo("  3. Apply as generators between clips")
        elif editor == 'fusion':
            click.echo("  1. Open Fusion or Fusion page in Resolve")
            click.echo("  2. Import the JSON composition data")
            click.echo("  3. Connect the nodes as specified")


@transitions.command()
@click.argument('shot1', type=click.Path(exists=True))
@click.argument('shot2', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for analysis')
@click.option('--duration', '-d', type=int, default=30, help='Transition duration in frames')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def colorpair(shot1: str, shot2: str, output: str, duration: int, verbose: bool):
    """
    Analyze color flow between a single pair of shots.
    
    Example:
        alice transitions colorpair shot1.jpg shot2.jpg -o transition.json
    """
    setup_logging(debug=verbose)
    
    click.echo(f"Analyzing color flow: {Path(shot1).name} → {Path(shot2).name}")
    
    # Analyze the pair
    analyzer = ColorFlowAnalyzer()
    analysis = analyzer.analyze_shot_pair(shot1, shot2, duration)
    
    # Display detailed results
    click.echo(f"\nColor Flow Analysis:")
    click.echo(f"  Compatibility score: {analysis.compatibility_score:.2%}")
    click.echo(f"  Transition type: {analysis.gradient_transition.transition_type}")
    click.echo(f"  Blend curve: {analysis.gradient_transition.blend_curve}")
    click.echo(f"  Duration: {duration} frames")
    
    # Shot 1 details
    click.echo(f"\nShot 1 Analysis:")
    click.echo(f"  Dominant colors:")
    for i, (color, weight) in enumerate(zip(analysis.shot1_palette.dominant_colors[:3],
                                           analysis.shot1_palette.color_weights[:3])):
        click.echo(f"    {i+1}. RGB{color} ({weight:.1%})")
    click.echo(f"  Average brightness: {analysis.shot1_palette.average_brightness:.2f}")
    click.echo(f"  Average saturation: {analysis.shot1_palette.average_saturation:.2f}")
    click.echo(f"  Color temperature: {'Warm' if analysis.shot1_palette.color_temperature > 0.5 else 'Cool'} ({analysis.shot1_palette.color_temperature:.2f})")
    click.echo(f"  Lighting: {analysis.shot1_lighting.type} (intensity: {analysis.shot1_lighting.intensity:.2f})")
    
    # Shot 2 details
    click.echo(f"\nShot 2 Analysis:")
    click.echo(f"  Dominant colors:")
    for i, (color, weight) in enumerate(zip(analysis.shot2_palette.dominant_colors[:3],
                                           analysis.shot2_palette.color_weights[:3])):
        click.echo(f"    {i+1}. RGB{color} ({weight:.1%})")
    click.echo(f"  Average brightness: {analysis.shot2_palette.average_brightness:.2f}")
    click.echo(f"  Average saturation: {analysis.shot2_palette.average_saturation:.2f}")
    click.echo(f"  Color temperature: {'Warm' if analysis.shot2_palette.color_temperature > 0.5 else 'Cool'} ({analysis.shot2_palette.color_temperature:.2f})")
    click.echo(f"  Lighting: {analysis.shot2_lighting.type} (intensity: {analysis.shot2_lighting.intensity:.2f})")
    
    # Transition details
    click.echo(f"\nGradient Transition:")
    click.echo(f"  Start colors: {[f'RGB{c}' for c in analysis.gradient_transition.start_colors]}")
    click.echo(f"  End colors: {[f'RGB{c}' for c in analysis.gradient_transition.end_colors]}")
    click.echo(f"  Type: {analysis.gradient_transition.transition_type}")
    click.echo(f"  Blend curve: {analysis.gradient_transition.blend_curve}")
    
    # Suggested effects
    click.echo(f"\nSuggested effects:")
    for effect in analysis.suggested_effects:
        click.echo(f"  - {effect}")
    
    if verbose:
        # Lighting details
        click.echo(f"\nDetailed Lighting Analysis:")
        click.echo(f"  Shot 1 light direction: ({analysis.shot1_lighting.direction[0]:.2f}, {analysis.shot1_lighting.direction[1]:.2f})")
        click.echo(f"  Shot 2 light direction: ({analysis.shot2_lighting.direction[0]:.2f}, {analysis.shot2_lighting.direction[1]:.2f})")
        click.echo(f"  Shot 1 shadow density: {analysis.shot1_lighting.shadow_density:.2f}")
        click.echo(f"  Shot 2 shadow density: {analysis.shot2_lighting.shadow_density:.2f}")
    
    # Save if output specified
    if output:
        with open(output, 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)
        click.echo(f"\nAnalysis saved to: {output}")