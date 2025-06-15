#!/usr/bin/env python3
"""
DaVinci Resolve Export Validation Test Suite

Tests EDL and XML export formats with real-world scenarios.
"""

import json
import random
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alicemultiverse.interface.models import Clip, TimelineRequest
from alicemultiverse.video_export import DaVinciExporter


class DaVinciValidationSuite:
    """Comprehensive validation for DaVinci Resolve exports."""

    def __init__(self, test_media_path: Path):
        self.test_media_path = Path(test_media_path)
        self.exporter = DaVinciExporter()
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": []
        }

    def run_all_tests(self):
        """Run complete validation suite."""
        print("🎬 DaVinci Resolve Export Validation Suite")
        print("=" * 50)

        # Test 1: Large timeline (100+ clips)
        self.test_large_timeline()

        # Test 2: Metadata preservation
        self.test_metadata_preservation()

        # Test 3: Beat markers
        self.test_beat_markers()

        # Test 4: Proxy paths
        self.test_proxy_paths()

        # Test 5: Complex transitions
        self.test_complex_transitions()

        # Test 6: Multi-track timeline
        self.test_multi_track()

        # Summary
        self.print_summary()

    def test_large_timeline(self):
        """Test export with 100+ clips."""
        print("\n📋 Test 1: Large Timeline (150 clips)")
        print("-" * 40)

        try:
            # Create 150 test clips
            clips = []
            current_time = 0.0

            for i in range(150):
                duration = random.uniform(1.0, 5.0)
                clip = Clip(
                    id=f"clip_{i:03d}",
                    source_path=str(self.test_media_path / f"image_{i:03d}.jpg"),
                    start_time=current_time,
                    duration=duration,
                    metadata={
                        "original_name": f"test_image_{i:03d}.jpg",
                        "clip_number": i,
                        "test_category": "large_timeline"
                    }
                )
                clips.append(clip)
                current_time += duration

            # Create timeline request
            timeline = TimelineRequest(
                project_name="Large Timeline Test",
                clips=clips,
                fps=30.0,
                resolution=(1920, 1080),
                audio_path="/tmp/test_audio.mp3"
            )

            # Export EDL
            print("  - Exporting EDL...")
            edl_path = Path("/tmp/large_timeline_test.edl")
            self.exporter.export_edl(timeline, edl_path)

            # Verify EDL
            with open(edl_path) as f:
                edl_content = f.read()

            assert "TITLE: Large Timeline Test" in edl_content
            assert edl_content.count("CLIP NAME:") == 150
            print("  ✅ EDL export successful")

            # Export XML
            print("  - Exporting XML...")
            xml_path = Path("/tmp/large_timeline_test.xml")
            self.exporter.export_xml(timeline, xml_path)

            # Verify XML
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Count clips in XML
            video_clips = root.findall(".//video/track/clipitem")
            assert len(video_clips) == 150
            print("  ✅ XML export successful")

            # Check file sizes
            edl_size = edl_path.stat().st_size / 1024  # KB
            xml_size = xml_path.stat().st_size / 1024  # KB
            print(f"  - EDL size: {edl_size:.1f} KB")
            print(f"  - XML size: {xml_size:.1f} KB")

            self._record_success("large_timeline", {
                "clip_count": 150,
                "edl_size_kb": edl_size,
                "xml_size_kb": xml_size
            })

        except Exception as e:
            self._record_failure("large_timeline", str(e))
            print(f"  ❌ Test failed: {e}")

    def test_metadata_preservation(self):
        """Test that all metadata is preserved in exports."""
        print("\n📋 Test 2: Metadata Preservation")
        print("-" * 40)

        try:
            # Create clips with rich metadata
            test_metadata = {
                "ai_provider": "midjourney",
                "prompt": "cyberpunk city at night",
                "seed": "12345",
                "quality_score": 0.95,
                "tags": ["cyberpunk", "night", "city"],
                "color_grade": "cool_blue",
                "custom_field": "test_value"
            }

            clips = [
                Clip(
                    id="metadata_test_1",
                    source_path=str(self.test_media_path / "test1.jpg"),
                    start_time=0.0,
                    duration=3.0,
                    metadata=test_metadata
                ),
                Clip(
                    id="metadata_test_2",
                    source_path=str(self.test_media_path / "test2.jpg"),
                    start_time=3.0,
                    duration=3.0,
                    metadata=test_metadata
                )
            ]

            timeline = TimelineRequest(
                project_name="Metadata Test",
                clips=clips,
                fps=24.0,
                metadata={
                    "export_date": "2024-01-15",
                    "exported_by": "validation_suite"
                }
            )

            # Export and check XML metadata
            xml_path = Path("/tmp/metadata_test.xml")
            self.exporter.export_xml(timeline, xml_path)

            # Parse and verify
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Check clip metadata
            first_clip = root.find(".//video/track/clipitem")
            comments = first_clip.findall(".//comments")

            metadata_found = False
            for comment in comments:
                comment_text = comment.find("mastercomment1").text
                if "midjourney" in comment_text:
                    metadata_found = True

            assert metadata_found, "Metadata not found in XML comments"
            print("  ✅ Metadata preserved in XML")

            self._record_success("metadata_preservation", {
                "metadata_fields": len(test_metadata)
            })

        except Exception as e:
            self._record_failure("metadata_preservation", str(e))
            print(f"  ❌ Test failed: {e}")

    def test_beat_markers(self):
        """Test beat marker export."""
        print("\n📋 Test 3: Beat Markers")
        print("-" * 40)

        try:
            # Create timeline with beat markers
            beat_times = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

            clips = [
                Clip(
                    id="beat_test",
                    source_path=str(self.test_media_path / "beat_test.jpg"),
                    start_time=0.0,
                    duration=5.0
                )
            ]

            timeline = TimelineRequest(
                project_name="Beat Marker Test",
                clips=clips,
                fps=30.0,
                metadata={
                    "beat_markers": beat_times,
                    "bpm": 120
                }
            )

            # Export with beat markers
            xml_path = Path("/tmp/beat_marker_test.xml")
            self.exporter.export_xml(timeline, xml_path)

            # Verify markers in XML
            tree = ET.parse(xml_path)
            root = tree.getroot()

            markers = root.findall(".//marker")
            assert len(markers) >= len(beat_times), f"Expected {len(beat_times)} markers, found {len(markers)}"

            print(f"  ✅ {len(markers)} beat markers exported")

            self._record_success("beat_markers", {
                "marker_count": len(markers),
                "expected_count": len(beat_times)
            })

        except Exception as e:
            self._record_failure("beat_markers", str(e))
            print(f"  ❌ Test failed: {e}")

    def test_proxy_paths(self):
        """Test proxy file path handling."""
        print("\n📋 Test 4: Proxy Paths")
        print("-" * 40)

        try:
            # Create clips with proxy paths
            clips = []
            for i in range(5):
                clip = Clip(
                    id=f"proxy_test_{i}",
                    source_path=str(self.test_media_path / f"original_{i}.jpg"),
                    start_time=i * 2.0,
                    duration=2.0,
                    metadata={
                        "proxy_path": str(self.test_media_path / "proxies" / f"proxy_{i}.jpg"),
                        "has_proxy": True
                    }
                )
                clips.append(clip)

            timeline = TimelineRequest(
                project_name="Proxy Path Test",
                clips=clips,
                fps=30.0,
                use_proxies=True
            )

            # Export XML with proxy support
            xml_path = Path("/tmp/proxy_test.xml")
            self.exporter.export_xml(timeline, xml_path)

            # Verify proxy paths in XML
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Check for proxy references
            files = root.findall(".//file")
            proxy_count = 0

            for file_elem in files:
                pathurl = file_elem.find("pathurl")
                if pathurl is not None and "proxy" in pathurl.text:
                    proxy_count += 1

            print(f"  ✅ {proxy_count} proxy paths configured")

            self._record_success("proxy_paths", {
                "proxy_count": proxy_count,
                "total_clips": len(clips)
            })

        except Exception as e:
            self._record_failure("proxy_paths", str(e))
            print(f"  ❌ Test failed: {e}")

    def test_complex_transitions(self):
        """Test complex transition scenarios."""
        print("\n📋 Test 5: Complex Transitions")
        print("-" * 40)

        try:
            # Create clips with various transitions
            clips = []
            transition_types = ["cut", "dissolve", "wipe", "fade", "slide"]

            for i in range(10):
                clip = Clip(
                    id=f"transition_test_{i}",
                    source_path=str(self.test_media_path / f"trans_{i}.jpg"),
                    start_time=i * 3.0,
                    duration=3.0,
                    transition_in={
                        "type": random.choice(transition_types),
                        "duration": 0.5
                    } if i > 0 else None,
                    transition_out={
                        "type": random.choice(transition_types),
                        "duration": 0.5
                    } if i < 9 else None
                )
                clips.append(clip)

            timeline = TimelineRequest(
                project_name="Transition Test",
                clips=clips,
                fps=24.0
            )

            # Export both formats
            edl_path = Path("/tmp/transition_test.edl")
            xml_path = Path("/tmp/transition_test.xml")

            self.exporter.export_edl(timeline, edl_path)
            self.exporter.export_xml(timeline, xml_path)

            # Verify transitions in EDL
            with open(edl_path) as f:
                edl_content = f.read()

            # Count transition markers
            dissolve_count = edl_content.count("DISSOLVE")
            wipe_count = edl_content.count("WIPE")

            print(f"  ✅ Transitions exported: {dissolve_count} dissolves, {wipe_count} wipes")

            self._record_success("complex_transitions", {
                "transition_types": len(set(transition_types)),
                "dissolve_count": dissolve_count,
                "wipe_count": wipe_count
            })

        except Exception as e:
            self._record_failure("complex_transitions", str(e))
            print(f"  ❌ Test failed: {e}")

    def test_multi_track(self):
        """Test multi-track timeline export."""
        print("\n📋 Test 6: Multi-Track Timeline")
        print("-" * 40)

        try:
            # Create main video track
            main_clips = []
            for i in range(5):
                main_clips.append(Clip(
                    id=f"main_{i}",
                    source_path=str(self.test_media_path / f"main_{i}.jpg"),
                    start_time=i * 4.0,
                    duration=4.0,
                    track=1
                ))

            # Create overlay track
            overlay_clips = []
            for i in range(3):
                overlay_clips.append(Clip(
                    id=f"overlay_{i}",
                    source_path=str(self.test_media_path / f"overlay_{i}.png"),
                    start_time=i * 6.0 + 2.0,
                    duration=2.0,
                    track=2,
                    opacity=0.7
                ))

            # Combine all clips
            all_clips = main_clips + overlay_clips

            timeline = TimelineRequest(
                project_name="Multi-Track Test",
                clips=all_clips,
                fps=30.0,
                tracks=2
            )

            # Export XML (EDL doesn't support multi-track well)
            xml_path = Path("/tmp/multitrack_test.xml")
            self.exporter.export_xml(timeline, xml_path)

            # Verify tracks in XML
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Count tracks
            tracks = root.findall(".//video/track")
            assert len(tracks) >= 2, f"Expected at least 2 tracks, found {len(tracks)}"

            print(f"  ✅ {len(tracks)} video tracks exported")

            self._record_success("multi_track", {
                "track_count": len(tracks),
                "main_clips": len(main_clips),
                "overlay_clips": len(overlay_clips)
            })

        except Exception as e:
            self._record_failure("multi_track", str(e))
            print(f"  ❌ Test failed: {e}")

    def _record_success(self, test_name: str, details: dict[str, Any]):
        """Record successful test."""
        self.results["tests_run"] += 1
        self.results["tests_passed"] += 1
        self.results["details"].append({
            "test": test_name,
            "status": "passed",
            "details": details
        })

    def _record_failure(self, test_name: str, error: str):
        """Record failed test."""
        self.results["tests_run"] += 1
        self.results["tests_failed"] += 1
        self.results["details"].append({
            "test": test_name,
            "status": "failed",
            "error": error
        })

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        print(f"Tests Run: {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']} ✅")
        print(f"Tests Failed: {self.results['tests_failed']} ❌")
        print(f"Success Rate: {(self.results['tests_passed'] / self.results['tests_run'] * 100):.1f}%")

        # Save detailed results
        results_path = Path("/tmp/davinci_validation_results.json")
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: {results_path}")

        # Print recommendations
        print("\n📝 RECOMMENDATIONS:")
        if self.results["tests_failed"] == 0:
            print("  ✅ All tests passed! Export formats are ready for production use.")
        else:
            print("  ⚠️  Some tests failed. Review the detailed results and fix issues before use.")

        print("\n💡 NEXT STEPS:")
        print("  1. Import test files into DaVinci Resolve")
        print("  2. Verify timeline structure matches expectations")
        print("  3. Check that all metadata is accessible")
        print("  4. Test with real project files")


if __name__ == "__main__":
    # Check if test media path provided
    if len(sys.argv) < 2:
        print("Usage: python davinci_resolve_validation.py <test_media_path>")
        print("Example: python davinci_resolve_validation.py ~/Pictures/test_images")
        sys.exit(1)

    test_media_path = Path(sys.argv[1])
    if not test_media_path.exists():
        print(f"Error: Test media path does not exist: {test_media_path}")
        sys.exit(1)

    # Run validation suite
    validator = DaVinciValidationSuite(test_media_path)
    validator.run_all_tests()
