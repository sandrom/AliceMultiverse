#!/usr/bin/env python3
"""
Demonstration of subject morphing for smooth transitions.

This example shows how to:
1. Detect subjects in images
2. Find matching subjects across shots
3. Generate morph keyframes
4. Export After Effects compatible data
"""

import asyncio
import json
from pathlib import Path

from alicemultiverse.transitions.morphing import (
    MorphingTransitionMatcher,
    SubjectMorpher,
    SubjectRegion,
)


async def demo_subject_detection(image_path: str):
    """Demonstrate subject detection in a single image."""
    print(f"\n{'='*60}")
    print("Subject Detection Demo")
    print(f"{'='*60}")

    morpher = SubjectMorpher()

    print(f"\nAnalyzing: {Path(image_path).name}")
    subjects = await morpher.detect_subjects(image_path)

    if not subjects:
        print("No subjects detected.")
        return subjects

    print(f"Found {len(subjects)} subjects:")
    for i, subject in enumerate(subjects, 1):
        print(f"\n{i}. {subject.label}")
        print(f"   - Confidence: {subject.confidence:.2%}")
        print(f"   - Position: ({subject.center[0]:.2f}, {subject.center[1]:.2f})")
        print(f"   - Size: {subject.area:.2%} of image")
        print(f"   - Bounding box: {subject.bbox}")

    return subjects


async def demo_subject_matching(
    source_path: str,
    target_path: str,
    source_subjects: list[SubjectRegion],
    target_subjects: list[SubjectRegion]
):
    """Demonstrate subject matching between two images."""
    print(f"\n{'='*60}")
    print("Subject Matching Demo")
    print(f"{'='*60}")

    morpher = SubjectMorpher()

    print("\nMatching subjects:")
    print(f"  Source: {Path(source_path).name} ({len(source_subjects)} subjects)")
    print(f"  Target: {Path(target_path).name} ({len(target_subjects)} subjects)")

    # Find matches
    matches = morpher.find_similar_subjects(source_subjects, target_subjects)

    if not matches:
        print("\nNo matching subjects found.")
        return matches

    print(f"\nFound {len(matches)} matches:")
    for i, (source, target) in enumerate(matches, 1):
        similarity = morpher._calculate_subject_similarity(source, target)
        print(f"\n{i}. {source.label} → {target.label}")
        print(f"   - Similarity: {similarity:.2%}")
        print(f"   - Position shift: {abs(source.center[0] - target.center[0]):.2f}, "
              f"{abs(source.center[1] - target.center[1]):.2f}")
        print(f"   - Size change: {(target.area / source.area):.2%}")

    return matches


async def demo_morph_generation(
    source_path: str,
    target_path: str,
    subject_pairs: list[tuple]
):
    """Demonstrate morph keyframe generation."""
    print(f"\n{'='*60}")
    print("Morph Generation Demo")
    print(f"{'='*60}")

    morpher = SubjectMorpher()

    # Generate keyframes
    print("\nGenerating morph keyframes...")
    keyframes = morpher.generate_morph_keyframes(
        subject_pairs,
        duration=1.2,
        morph_type="smooth",
        keyframe_count=10
    )

    print(f"Generated {len(keyframes)} keyframes")

    # Show sample keyframes
    print("\nSample keyframes:")
    for i in [0, len(keyframes)//2, len(keyframes)-1]:
        if i < len(keyframes):
            kf = keyframes[i]
            print(f"\n  Keyframe {i+1} (t={kf.time:.2f}s):")
            print(f"    - Position: ({kf.target_point[0]:.3f}, {kf.target_point[1]:.3f})")
            print(f"    - Scale: {kf.scale:.2f}")
            print(f"    - Rotation: {kf.rotation:.1f}°")
            print(f"    - Opacity: {kf.opacity:.2f}")

    return keyframes


async def demo_after_effects_export(morph_transition):
    """Demonstrate After Effects export."""
    print(f"\n{'='*60}")
    print("After Effects Export Demo")
    print(f"{'='*60}")

    morpher = SubjectMorpher()

    # Export to temporary directory
    output_dir = Path("output/morph_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    export_path = output_dir / "morph_demo.json"

    print(f"\nExporting to: {export_path}")
    result = morpher.export_for_after_effects(
        morph_transition,
        str(export_path),
        fps=30.0
    )

    print("\nExport complete:")
    print(f"  - JSON data: {result['json_path']}")
    print(f"  - JSX script: {result['jsx_path']}")
    print(f"  - Subjects: {result['subject_count']}")
    print(f"  - Keyframes: {result['keyframe_count']}")
    print(f"  - Duration: {result['duration']:.2f}s")

    # Show sample of exported data
    with open(result['json_path']) as f:
        data = json.load(f)

    print("\nExported data structure:")
    print(f"  - Version: {data['version']}")
    print(f"  - FPS: {data['project']['fps']}")
    print(f"  - Morph layers: {len(data['morph_data'])}")

    if data['morph_data']:
        layer = data['morph_data'][0]
        print(f"\n  Sample morph layer '{layer['name']}':")
        print(f"    - Keyframes: {len(layer['keyframes'])}")
        print(f"    - Source anchor: {layer['source_anchor']}")
        print(f"    - Target anchor: {layer['target_anchor']}")


async def demo_sequence_analysis(image_paths: list[str]):
    """Demonstrate full sequence morphing analysis."""
    print(f"\n{'='*60}")
    print("Sequence Morphing Analysis")
    print(f"{'='*60}")

    matcher = MorphingTransitionMatcher()

    print(f"\nAnalyzing {len(image_paths)} images for morphing opportunities...")

    transitions = await matcher.analyze_for_morphing(image_paths, min_similarity=0.5)

    if not transitions:
        print("No morphing opportunities found.")
        return

    print(f"\nFound {len(transitions)} morphing opportunities:")

    for i, trans in enumerate(transitions):
        print(f"\n{i+1}. {Path(trans.source_image).name} → {Path(trans.target_image).name}")
        print(f"   - Duration: {trans.duration:.2f}s")
        print(f"   - Type: {trans.morph_type}")
        print(f"   - Matched subjects: {len(trans.subject_pairs)}")

        for j, (src, tgt) in enumerate(trans.subject_pairs):
            print(f"     {j+1}. {src.label} → {tgt.label}")


async def main():
    """Run the morphing demonstration."""
    print("Subject Morphing Demonstration")
    print("==============================")

    # Example images (replace with actual image paths)
    test_images = [
        "test_data/portrait1.jpg",
        "test_data/portrait2.jpg",
        "test_data/portrait3.jpg"
    ]

    # Check if test images exist
    existing_images = [p for p in test_images if Path(p).exists()]

    if len(existing_images) < 2:
        print("\nNote: This demo requires at least 2 test images.")
        print("Please provide image paths or create test images in test_data/")

        # Create mock demo data
        print("\nRunning with mock data for demonstration...")

        # Mock subjects
        mock_subjects1 = [
            SubjectRegion(
                label="person",
                confidence=0.95,
                bbox=(0.3, 0.2, 0.4, 0.6),
                center=(0.5, 0.5),
                area=0.24
            ),
            SubjectRegion(
                label="face",
                confidence=0.98,
                bbox=(0.35, 0.25, 0.3, 0.3),
                center=(0.5, 0.4),
                area=0.09
            )
        ]

        mock_subjects2 = [
            SubjectRegion(
                label="person",
                confidence=0.92,
                bbox=(0.35, 0.22, 0.38, 0.58),
                center=(0.54, 0.51),
                area=0.22
            ),
            SubjectRegion(
                label="face",
                confidence=0.96,
                bbox=(0.38, 0.27, 0.28, 0.28),
                center=(0.52, 0.41),
                area=0.08
            )
        ]

        # Demo matching
        morpher = SubjectMorpher()
        matches = morpher.find_similar_subjects(mock_subjects1, mock_subjects2)

        print(f"\nMock matching results: {len(matches)} matches found")

        # Demo keyframe generation
        if matches:
            keyframes = morpher.generate_morph_keyframes(
                matches, duration=1.2, morph_type="elastic"
            )
            print(f"Generated {len(keyframes)} keyframes for morphing")

        return

    # Run with actual images
    # 1. Detect subjects in first image
    subjects1 = await demo_subject_detection(existing_images[0])

    # 2. Detect subjects in second image
    subjects2 = await demo_subject_detection(existing_images[1])

    # 3. Match subjects
    if subjects1 and subjects2:
        matches = await demo_subject_matching(
            existing_images[0], existing_images[1],
            subjects1, subjects2
        )

        # 4. Generate morph keyframes
        if matches:
            keyframes = await demo_morph_generation(
                existing_images[0], existing_images[1], matches
            )

            # 5. Create full morph transition
            morpher = SubjectMorpher()
            morph_transition = morpher.create_morph_transition(
                existing_images[0], existing_images[1],
                subjects1, subjects2,
                duration=1.2
            )

            # 6. Export for After Effects
            if morph_transition:
                await demo_after_effects_export(morph_transition)

    # 7. Analyze full sequence if more than 2 images
    if len(existing_images) > 2:
        await demo_sequence_analysis(existing_images)

    print("\n\nDemo complete!")


if __name__ == "__main__":
    asyncio.run(main())
