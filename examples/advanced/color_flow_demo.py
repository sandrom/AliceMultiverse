#!/usr/bin/env python3
"""
Color Flow Transitions Demo

This script demonstrates the Color Flow Transitions feature that analyzes
color palettes and lighting between shots to create smooth, visually
pleasing transitions for video editing.
"""

import sys
from pathlib import Path
from alicemultiverse.transitions import (
    ColorFlowAnalyzer,
    analyze_sequence,
    export_analysis_for_editor
)


def main():
    """Run color flow analysis demo."""
    print("=== Color Flow Transitions Demo ===\n")
    
    # Example 1: Analyze a single pair of shots
    print("1. Analyzing a single transition between two shots:")
    
    # You would replace these with actual image paths
    shot1 = "path/to/shot1.jpg"  # e.g., warm sunset shot
    shot2 = "path/to/shot2.jpg"  # e.g., cool night shot
    
    # Check if files exist (demo mode if not)
    if not Path(shot1).exists() or not Path(shot2).exists():
        print("   [Demo mode - using example analysis]\n")
        print_demo_analysis()
    else:
        analyzer = ColorFlowAnalyzer()
        analysis = analyzer.analyze_shot_pair(shot1, shot2, transition_duration=30)
        
        print(f"   Compatibility Score: {analysis.compatibility_score:.2%}")
        print(f"   Transition Type: {analysis.gradient_transition.transition_type}")
        print(f"   Duration: {analysis.gradient_transition.duration_frames} frames")
        
        print("\n   Color Analysis:")
        print(f"   - Shot 1 dominant: RGB{analysis.shot1_palette.dominant_colors[0]}")
        print(f"   - Shot 2 dominant: RGB{analysis.shot2_palette.dominant_colors[0]}")
        
        print("\n   Lighting Analysis:")
        print(f"   - Shot 1: {analysis.shot1_lighting.type} lighting")
        print(f"   - Shot 2: {analysis.shot2_lighting.type} lighting")
        
        print("\n   Suggested Effects:")
        for effect in analysis.suggested_effects[:5]:
            print(f"   - {effect}")
        
        # Export for video editor
        export_analysis_for_editor(analysis, "color_transition.json", "resolve")
        print("\n   Exported to: color_transition.json")
    
    # Example 2: Analyze a sequence of shots
    print("\n\n2. Analyzing a sequence of multiple shots:")
    
    sequence = [
        "path/to/shot1.jpg",
        "path/to/shot2.jpg", 
        "path/to/shot3.jpg",
        "path/to/shot4.jpg"
    ]
    
    if not all(Path(s).exists() for s in sequence):
        print("   [Demo mode - showing example sequence analysis]\n")
        print_demo_sequence()
    else:
        analyses = analyze_sequence(sequence, transition_duration=24)
        
        for i, analysis in enumerate(analyses):
            print(f"\n   Transition {i+1}:")
            print(f"   - Compatibility: {analysis.compatibility_score:.2%}")
            print(f"   - Type: {analysis.gradient_transition.transition_type}")
            print(f"   - Effects: {', '.join(analysis.suggested_effects[:3])}")
    
    print("\n\n=== How to Use Color Flow Transitions ===")
    print("\n1. Command Line:")
    print("   alice transitions colorflow shot1.jpg shot2.jpg shot3.jpg -o output/")
    print("   alice transitions colorpair shot1.jpg shot2.jpg -v")
    
    print("\n2. In Python:")
    print("   from alicemultiverse.transitions import ColorFlowAnalyzer")
    print("   analyzer = ColorFlowAnalyzer()")
    print("   analysis = analyzer.analyze_shot_pair('shot1.jpg', 'shot2.jpg')")
    
    print("\n3. Export for Editors:")
    print("   - DaVinci Resolve: JSON + LUT files")
    print("   - Premiere Pro: JSON with keyframe data")
    print("   - Final Cut Pro X: Motion template data")
    print("   - Fusion: Node-based composition")
    
    print("\n=== Key Features ===")
    print("- Analyzes dominant colors and palettes")
    print("- Detects lighting direction and intensity")
    print("- Suggests transition types (linear, radial, diagonal)")
    print("- Generates gradient masks for effects")
    print("- Creates color matching LUTs")
    print("- Exports editor-specific formats")


def print_demo_analysis():
    """Print example analysis for demo mode."""
    print("   Compatibility Score: 72%")
    print("   Transition Type: diagonal")
    print("   Duration: 30 frames")
    
    print("\n   Color Analysis:")
    print("   - Shot 1 dominant: RGB(255, 147, 41) [Warm orange]")
    print("   - Shot 2 dominant: RGB(41, 128, 185) [Cool blue]")
    print("   - Temperature shift: 0.68 (warm to cool)")
    print("   - Brightness change: 0.34")
    
    print("\n   Lighting Analysis:")
    print("   - Shot 1: directional lighting (intensity: 0.85)")
    print("   - Shot 2: ambient lighting (intensity: 0.45)")
    print("   - Light direction change: 47°")
    
    print("\n   Suggested Effects:")
    print("   - color_temperature_shift")
    print("   - exposure_ramp")
    print("   - light_sweep")
    print("   - gradient_wipe")
    print("   - color_match")


def print_demo_sequence():
    """Print example sequence analysis for demo mode."""
    transitions = [
        ("warm sunset", "cool twilight", 68, "diagonal"),
        ("cool twilight", "night scene", 85, "radial"),
        ("night scene", "dawn light", 52, "linear")
    ]
    
    for i, (from_desc, to_desc, compat, trans_type) in enumerate(transitions):
        print(f"\n   Transition {i+1}: {from_desc} → {to_desc}")
        print(f"   - Compatibility: {compat}%")
        print(f"   - Type: {trans_type}")
        print(f"   - Key effects: color_temperature_shift, exposure_ramp, gradient_wipe")


if __name__ == "__main__":
    main()