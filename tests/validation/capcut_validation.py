#!/usr/bin/env python3
"""
CapCut Mobile Export Validation Test Suite

Tests JSON export format for CapCut mobile compatibility.
"""

import sys
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alicemultiverse.video_export import CapCutExporter
from alicemultiverse.interface.models import TimelineRequest, Clip


class CapCutValidationSuite:
    """Comprehensive validation for CapCut mobile exports."""
    
    def __init__(self, test_media_path: Path):
        self.test_media_path = Path(test_media_path)
        self.exporter = CapCutExporter()
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": []
        }
        
    def run_all_tests(self):
        """Run complete validation suite."""
        print("📱 CapCut Mobile Export Validation Suite")
        print("=" * 50)
        
        # Test 1: JSON structure validation
        self.test_json_structure()
        
        # Test 2: Asset path resolution
        self.test_asset_paths()
        
        # Test 3: Effect compatibility
        self.test_effects()
        
        # Test 4: Mobile performance (file size)
        self.test_mobile_performance()
        
        # Test 5: Audio sync
        self.test_audio_sync()
        
        # Test 6: Aspect ratios
        self.test_aspect_ratios()
        
        # Summary
        self.print_summary()
        
    def test_json_structure(self):
        """Test that JSON follows CapCut's expected structure."""
        print("\n📋 Test 1: JSON Structure Validation")
        print("-" * 40)
        
        try:
            # Create simple timeline
            clips = [
                Clip(
                    id="test_1",
                    source_path=str(self.test_media_path / "test1.jpg"),
                    start_time=0.0,
                    duration=3.0
                ),
                Clip(
                    id="test_2",
                    source_path=str(self.test_media_path / "test2.jpg"),
                    start_time=3.0,
                    duration=3.0
                )
            ]
            
            timeline = TimelineRequest(
                project_name="Structure Test",
                clips=clips,
                fps=30.0,
                resolution=(1080, 1920),  # Vertical for mobile
                audio_path="/tmp/test_audio.mp3"
            )
            
            # Export JSON
            json_path = Path("/tmp/capcut_structure_test.json")
            self.exporter.export_json(timeline, json_path)
            
            # Load and validate structure
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check required fields
            required_fields = [
                "version",
                "project_name",
                "duration",
                "fps",
                "resolution",
                "tracks",
                "materials"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
                
            # Check tracks structure
            assert "video" in data["tracks"], "Missing video track"
            assert isinstance(data["tracks"]["video"], list), "Video track must be array"
            
            # Check materials structure
            assert "videos" in data["materials"], "Missing video materials"
            assert isinstance(data["materials"]["videos"], list), "Video materials must be array"
            
            print("  ✅ JSON structure valid")
            print(f"  - Version: {data['version']}")
            print(f"  - Duration: {data['duration']}s")
            print(f"  - Clips: {len(data['tracks']['video'][0]['segments'])}")
            
            self._record_success("json_structure", {
                "version": data["version"],
                "clip_count": len(clips)
            })
            
        except Exception as e:
            self._record_failure("json_structure", str(e))
            print(f"  ❌ Test failed: {e}")
            
    def test_asset_paths(self):
        """Test asset path resolution for mobile."""
        print("\n📋 Test 2: Asset Path Resolution")
        print("-" * 40)
        
        try:
            # Create clips with various path formats
            test_paths = [
                "/Users/test/image.jpg",
                "~/Pictures/image.png",
                "./relative/path/image.jpg",
                "C:\\Windows\\path\\image.jpg"  # Windows path
            ]
            
            clips = []
            for i, path in enumerate(test_paths):
                clips.append(Clip(
                    id=f"path_test_{i}",
                    source_path=path,
                    start_time=i * 2.0,
                    duration=2.0
                ))
                
            timeline = TimelineRequest(
                project_name="Path Test",
                clips=clips,
                fps=30.0
            )
            
            # Export with mobile paths
            json_path = Path("/tmp/capcut_path_test.json")
            self.exporter.export_json(timeline, json_path, mobile_paths=True)
            
            # Check path handling
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            materials = data["materials"]["videos"]
            
            # Verify paths are properly formatted
            for material in materials:
                path = material["path"]
                
                # Check for mobile-friendly paths
                assert not path.startswith("~"), "Tilde paths not expanded"
                assert not path.startswith("C:"), "Windows paths not converted"
                assert "/" in path or "\\" in path, "Path separator missing"
                
                # Check for material IDs (required for CapCut)
                assert "id" in material, "Material missing ID"
                assert "md5" in material or "hash" in material, "Material missing hash"
                
            print(f"  ✅ {len(materials)} asset paths validated")
            print("  - All paths mobile-compatible")
            print("  - Material IDs generated")
            
            self._record_success("asset_paths", {
                "path_count": len(materials),
                "mobile_compatible": True
            })
            
        except Exception as e:
            self._record_failure("asset_paths", str(e))
            print(f"  ❌ Test failed: {e}")
            
    def test_effects(self):
        """Test effect compatibility."""
        print("\n📋 Test 3: Effect Compatibility")
        print("-" * 40)
        
        try:
            # Create clips with various effects
            effects = [
                {"type": "fade_in", "duration": 0.5},
                {"type": "fade_out", "duration": 0.5},
                {"type": "blur", "intensity": 0.5},
                {"type": "brightness", "value": 1.2},
                {"type": "contrast", "value": 1.1},
                {"type": "saturation", "value": 0.8},
                {"type": "speed", "value": 2.0}
            ]
            
            clips = []
            for i, effect in enumerate(effects):
                clip = Clip(
                    id=f"effect_test_{i}",
                    source_path=str(self.test_media_path / f"effect_{i}.jpg"),
                    start_time=i * 3.0,
                    duration=3.0,
                    effects=[effect]
                )
                clips.append(clip)
                
            timeline = TimelineRequest(
                project_name="Effects Test",
                clips=clips,
                fps=30.0,
                resolution=(1080, 1920)
            )
            
            # Export with effects
            json_path = Path("/tmp/capcut_effects_test.json")
            self.exporter.export_json(timeline, json_path)
            
            # Verify effects in JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            segments = data["tracks"]["video"][0]["segments"]
            
            effect_count = 0
            supported_effects = []
            
            for segment in segments:
                if "effects" in segment:
                    for effect in segment["effects"]:
                        effect_count += 1
                        if effect["type"] not in supported_effects:
                            supported_effects.append(effect["type"])
                            
            print(f"  ✅ {effect_count} effects exported")
            print(f"  - Supported types: {', '.join(supported_effects)}")
            
            # Check for CapCut-specific effect format
            sample_effect = segments[0]["effects"][0] if segments and "effects" in segments[0] else None
            if sample_effect:
                assert "type" in sample_effect, "Effect missing type"
                assert "parameters" in sample_effect or any(k in sample_effect for k in ["duration", "value", "intensity"]), "Effect missing parameters"
                
            self._record_success("effects", {
                "effect_count": effect_count,
                "effect_types": len(supported_effects)
            })
            
        except Exception as e:
            self._record_failure("effects", str(e))
            print(f"  ❌ Test failed: {e}")
            
    def test_mobile_performance(self):
        """Test file size and performance characteristics."""
        print("\n📋 Test 4: Mobile Performance")
        print("-" * 40)
        
        try:
            # Create large timeline to test file size
            clips = []
            for i in range(100):
                clip = Clip(
                    id=f"perf_test_{i}",
                    source_path=str(self.test_media_path / f"perf_{i}.jpg"),
                    start_time=i * 1.5,
                    duration=1.5,
                    metadata={
                        "quality": random.uniform(0.7, 1.0),
                        "tags": ["test", "performance", f"clip_{i}"]
                    }
                )
                clips.append(clip)
                
            timeline = TimelineRequest(
                project_name="Performance Test",
                clips=clips,
                fps=30.0,
                resolution=(1080, 1920)
            )
            
            # Export with optimization
            json_path = Path("/tmp/capcut_performance_test.json")
            start_time = time.time()
            self.exporter.export_json(timeline, json_path, optimize_mobile=True)
            export_time = time.time() - start_time
            
            # Check file size
            file_size = json_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # Load and check structure
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Performance checks
            assert file_size_mb < 10, f"File too large for mobile: {file_size_mb:.2f} MB"
            assert export_time < 5, f"Export too slow: {export_time:.2f}s"
            
            # Check optimization
            # Optimized export should minimize metadata
            segment = data["tracks"]["video"][0]["segments"][0]
            assert "metadata" not in segment or len(str(segment.get("metadata", {}))) < 200, "Metadata not optimized"
            
            print(f"  ✅ Performance validated")
            print(f"  - File size: {file_size_mb:.2f} MB")
            print(f"  - Export time: {export_time:.2f}s")
            print(f"  - 100 clips processed")
            
            self._record_success("mobile_performance", {
                "file_size_mb": file_size_mb,
                "export_time_s": export_time,
                "clip_count": 100
            })
            
        except Exception as e:
            self._record_failure("mobile_performance", str(e))
            print(f"  ❌ Test failed: {e}")
            
    def test_audio_sync(self):
        """Test audio synchronization data."""
        print("\n📋 Test 5: Audio Sync")
        print("-" * 40)
        
        try:
            # Create beat-synced timeline
            beat_times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
            
            clips = []
            for i, beat_time in enumerate(beat_times[:-1]):
                duration = beat_times[i + 1] - beat_time
                clip = Clip(
                    id=f"beat_sync_{i}",
                    source_path=str(self.test_media_path / f"beat_{i}.jpg"),
                    start_time=beat_time,
                    duration=duration
                )
                clips.append(clip)
                
            timeline = TimelineRequest(
                project_name="Audio Sync Test",
                clips=clips,
                fps=30.0,
                audio_path="/tmp/beat_track.mp3",
                metadata={
                    "bpm": 120,
                    "beat_markers": beat_times,
                    "audio_offset": 0.0
                }
            )
            
            # Export with audio
            json_path = Path("/tmp/capcut_audio_test.json")
            self.exporter.export_json(timeline, json_path)
            
            # Verify audio in JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check audio track
            assert "audio" in data["tracks"], "Missing audio track"
            audio_track = data["tracks"]["audio"][0]
            
            assert "segments" in audio_track, "Missing audio segments"
            audio_segment = audio_track["segments"][0]
            
            assert "path" in audio_segment or "material_id" in audio_segment, "Audio missing reference"
            assert "duration" in audio_segment, "Audio missing duration"
            
            # Check beat sync data
            if "metadata" in data:
                assert data["metadata"].get("bpm") == 120, "BPM not preserved"
                
            print("  ✅ Audio sync validated")
            print(f"  - BPM: {data.get('metadata', {}).get('bpm', 'N/A')}")
            print(f"  - Beat count: {len(beat_times)}")
            
            self._record_success("audio_sync", {
                "has_audio": True,
                "bpm": 120,
                "beat_count": len(beat_times)
            })
            
        except Exception as e:
            self._record_failure("audio_sync", str(e))
            print(f"  ❌ Test failed: {e}")
            
    def test_aspect_ratios(self):
        """Test various aspect ratios for mobile."""
        print("\n📋 Test 6: Aspect Ratios")
        print("-" * 40)
        
        try:
            aspect_ratios = [
                (1080, 1920, "9:16 Vertical"),
                (1080, 1080, "1:1 Square"),
                (1920, 1080, "16:9 Horizontal"),
                (720, 1280, "9:16 HD"),
                (1080, 1350, "4:5 Instagram")
            ]
            
            results = []
            
            for width, height, name in aspect_ratios:
                # Create simple timeline
                clips = [Clip(
                    id=f"aspect_test",
                    source_path=str(self.test_media_path / "aspect_test.jpg"),
                    start_time=0.0,
                    duration=3.0
                )]
                
                timeline = TimelineRequest(
                    project_name=f"Aspect Test {name}",
                    clips=clips,
                    fps=30.0,
                    resolution=(width, height)
                )
                
                # Export
                json_path = Path(f"/tmp/capcut_aspect_{width}x{height}.json")
                self.exporter.export_json(timeline, json_path)
                
                # Verify
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                assert data["resolution"]["width"] == width
                assert data["resolution"]["height"] == height
                
                results.append(f"{name} ({width}x{height})")
                
            print("  ✅ All aspect ratios validated")
            for result in results:
                print(f"  - {result}")
                
            self._record_success("aspect_ratios", {
                "tested_ratios": len(aspect_ratios),
                "all_valid": True
            })
            
        except Exception as e:
            self._record_failure("aspect_ratios", str(e))
            print(f"  ❌ Test failed: {e}")
            
    def _record_success(self, test_name: str, details: Dict[str, Any]):
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
        results_path = Path("/tmp/capcut_validation_results.json")
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: {results_path}")
        
        # Print recommendations
        print("\n📝 RECOMMENDATIONS:")
        if self.results["tests_failed"] == 0:
            print("  ✅ All tests passed! JSON format is ready for CapCut mobile.")
        else:
            print("  ⚠️  Some tests failed. Review the detailed results and fix issues before use.")
            
        print("\n💡 NEXT STEPS:")
        print("  1. Transfer test JSON files to mobile device")
        print("  2. Import into CapCut and verify timeline")
        print("  3. Check that all clips load correctly")
        print("  4. Test effects and transitions")
        print("  5. Verify audio synchronization")
        
        print("\n📱 MOBILE IMPORT GUIDE:")
        print("  1. Save JSON to phone's Documents folder")
        print("  2. Open CapCut → New Project → Import")
        print("  3. Select 'Import Project' (not media)")
        print("  4. Navigate to JSON file")
        print("  5. CapCut will reconstruct the timeline")


if __name__ == "__main__":
    # Check if test media path provided
    if len(sys.argv) < 2:
        print("Usage: python capcut_validation.py <test_media_path>")
        print("Example: python capcut_validation.py ~/Pictures/test_images")
        sys.exit(1)
        
    test_media_path = Path(sys.argv[1])
    if not test_media_path.exists():
        print(f"Error: Test media path does not exist: {test_media_path}")
        sys.exit(1)
        
    # Run validation suite
    validator = CapCutValidationSuite(test_media_path)
    validator.run_all_tests()