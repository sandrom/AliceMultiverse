"""
Color Flow Transitions module for smooth color-based transitions between shots.

Analyzes color palettes, creates gradient transitions, and detects lighting
direction for seamless visual flow between consecutive shots.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans


@dataclass
class ColorPalette:
    """Represents the color palette of a shot."""
    dominant_colors: list[tuple[int, int, int]]  # RGB values
    color_weights: list[float]  # Weight/percentage of each color
    average_brightness: float
    average_saturation: float
    color_temperature: float  # Warm (high) to cool (low)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            'dominant_colors': [list(color) for color in self.dominant_colors],
            'color_weights': self.color_weights,
            'average_brightness': self.average_brightness,
            'average_saturation': self.average_saturation,
            'color_temperature': self.color_temperature
        }


@dataclass
class LightingInfo:
    """Represents lighting information in a shot."""
    direction: tuple[float, float]  # Normalized 2D vector (x, y)
    intensity: float  # 0.0 to 1.0
    type: str  # 'directional', 'ambient', 'mixed'
    shadow_density: float  # 0.0 to 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            'direction': list(self.direction),
            'intensity': self.intensity,
            'type': self.type,
            'shadow_density': self.shadow_density
        }


@dataclass
class GradientTransition:
    """Represents a gradient transition between two shots."""
    start_colors: list[tuple[int, int, int]]
    end_colors: list[tuple[int, int, int]]
    duration_frames: int
    transition_type: str  # 'linear', 'radial', 'diagonal'
    blend_curve: str  # 'linear', 'ease-in', 'ease-out', 'ease-in-out'
    mask_data: np.ndarray | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            'start_colors': [list(color) for color in self.start_colors],
            'end_colors': [list(color) for color in self.end_colors],
            'duration_frames': self.duration_frames,
            'transition_type': self.transition_type,
            'blend_curve': self.blend_curve,
            'has_mask': self.mask_data is not None
        }


@dataclass
class ColorFlowAnalysis:
    """Complete color flow analysis between two shots."""
    shot1_palette: ColorPalette
    shot2_palette: ColorPalette
    shot1_lighting: LightingInfo
    shot2_lighting: LightingInfo
    gradient_transition: GradientTransition
    compatibility_score: float  # 0.0 to 1.0
    suggested_effects: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            'shot1_palette': self.shot1_palette.to_dict(),
            'shot2_palette': self.shot2_palette.to_dict(),
            'shot1_lighting': self.shot1_lighting.to_dict(),
            'shot2_lighting': self.shot2_lighting.to_dict(),
            'gradient_transition': self.gradient_transition.to_dict(),
            'compatibility_score': self.compatibility_score,
            'suggested_effects': self.suggested_effects
        }


class ColorFlowAnalyzer:
    """Analyzes color flow between shots for smooth transitions."""

    def __init__(self, n_colors: int = 5):
        """
        Initialize the color flow analyzer.

        Args:
            n_colors: Number of dominant colors to extract from each shot
        """
        self.n_colors = n_colors

    def analyze_shot_pair(self, shot1_path: str, shot2_path: str,
                         transition_duration: int = 30) -> ColorFlowAnalysis:
        """
        Analyze color flow between two shots.

        Args:
            shot1_path: Path to first shot (image or first frame of video)
            shot2_path: Path to second shot (image or first frame of video)
            transition_duration: Duration of transition in frames

        Returns:
            Complete color flow analysis
        """
        # Load images
        img1 = self._load_image(shot1_path)
        img2 = self._load_image(shot2_path)

        # Extract color palettes
        palette1 = self._extract_color_palette(img1)
        palette2 = self._extract_color_palette(img2)

        # Analyze lighting
        lighting1 = self._analyze_lighting(img1)
        lighting2 = self._analyze_lighting(img2)

        # Create gradient transition
        gradient = self._create_gradient_transition(
            palette1, palette2, lighting1, lighting2, transition_duration
        )

        # Calculate compatibility
        compatibility = self._calculate_compatibility(
            palette1, palette2, lighting1, lighting2
        )

        # Suggest effects based on analysis
        effects = self._suggest_effects(palette1, palette2, lighting1, lighting2)

        return ColorFlowAnalysis(
            shot1_palette=palette1,
            shot2_palette=palette2,
            shot1_lighting=lighting1,
            shot2_lighting=lighting2,
            gradient_transition=gradient,
            compatibility_score=compatibility,
            suggested_effects=effects
        )

    def _load_image(self, path: str) -> np.ndarray:
        """Load image or extract first frame from video."""
        path_obj = Path(path)

        if path_obj.suffix.lower() in ['.mp4', '.mov', '.avi']:
            # Extract first frame from video
            cap = cv2.VideoCapture(str(path))
            ret, frame = cap.read()
            cap.release()
            if ret:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                raise ValueError(f"Could not read video: {path}")
        else:
            # Load image
            img = Image.open(path).convert('RGB')
            return np.array(img)

    def _extract_color_palette(self, image: np.ndarray) -> ColorPalette:
        """Extract dominant colors and color properties from image."""
        # Reshape image to list of pixels
        pixels = image.reshape(-1, 3)

        # Use K-means to find dominant colors
        kmeans = KMeans(n_clusters=self.n_colors, random_state=42)
        kmeans.fit(pixels)

        # Get colors and their weights
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        weights = [np.sum(labels == i) / len(labels) for i in range(self.n_colors)]

        # Sort by weight
        sorted_indices = np.argsort(weights)[::-1]
        dominant_colors = [tuple(colors[i]) for i in sorted_indices]
        color_weights = [weights[i] for i in sorted_indices]

        # Calculate average properties
        avg_brightness = self._calculate_average_brightness(image)
        avg_saturation = self._calculate_average_saturation(image)
        color_temp = self._calculate_color_temperature(dominant_colors, color_weights)

        return ColorPalette(
            dominant_colors=dominant_colors,
            color_weights=color_weights,
            average_brightness=avg_brightness,
            average_saturation=avg_saturation,
            color_temperature=color_temp
        )

    def _analyze_lighting(self, image: np.ndarray) -> LightingInfo:
        """Analyze lighting direction and properties."""
        # Convert to grayscale for lighting analysis
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Apply Sobel filters to detect gradients
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)

        # Calculate average gradient direction
        avg_grad_x = np.mean(sobel_x)
        avg_grad_y = np.mean(sobel_y)

        # Normalize direction vector
        magnitude = np.sqrt(avg_grad_x**2 + avg_grad_y**2)
        if magnitude > 0:
            direction = (avg_grad_x / magnitude, avg_grad_y / magnitude)
        else:
            direction = (0.0, 0.0)

        # Calculate intensity (average brightness of top 20% pixels)
        bright_threshold = np.percentile(gray, 80)
        intensity = np.mean(gray[gray > bright_threshold]) / 255.0

        # Determine lighting type
        std_dev = np.std(gray)
        if std_dev < 30:
            light_type = 'ambient'
        elif std_dev > 70:
            light_type = 'directional'
        else:
            light_type = 'mixed'

        # Calculate shadow density
        dark_threshold = np.percentile(gray, 20)
        shadow_pixels = gray[gray < dark_threshold]
        shadow_density = len(shadow_pixels) / gray.size if gray.size > 0 else 0.0

        return LightingInfo(
            direction=direction,
            intensity=intensity,
            type=light_type,
            shadow_density=shadow_density
        )

    def _create_gradient_transition(self, palette1: ColorPalette, palette2: ColorPalette,
                                  lighting1: LightingInfo, lighting2: LightingInfo,
                                  duration: int) -> GradientTransition:
        """Create gradient transition based on color and lighting analysis."""
        # Use top 3 colors from each palette
        start_colors = palette1.dominant_colors[:3]
        end_colors = palette2.dominant_colors[:3]

        # Determine transition type based on lighting
        if lighting1.type == 'directional' and lighting2.type == 'directional':
            # Use diagonal transition aligned with average lighting direction
            (
                (lighting1.direction[0] + lighting2.direction[0]) / 2,
                (lighting1.direction[1] + lighting2.direction[1]) / 2
            )
            transition_type = 'diagonal'
        elif abs(palette1.average_brightness - palette2.average_brightness) > 0.3:
            # Use radial transition for significant brightness changes
            transition_type = 'radial'
        else:
            # Default to linear transition
            transition_type = 'linear'

        # Determine blend curve based on color temperature difference
        temp_diff = abs(palette1.color_temperature - palette2.color_temperature)
        if temp_diff > 0.3:
            blend_curve = 'ease-in-out'
        else:
            blend_curve = 'linear'

        # Create basic mask data (can be enhanced with actual masking)
        mask_data = self._create_transition_mask(transition_type, (1920, 1080))

        return GradientTransition(
            start_colors=start_colors,
            end_colors=end_colors,
            duration_frames=duration,
            transition_type=transition_type,
            blend_curve=blend_curve,
            mask_data=mask_data
        )

    def _create_transition_mask(self, transition_type: str,
                               size: tuple[int, int]) -> np.ndarray:
        """Create transition mask for advanced effects."""
        width, height = size
        mask = np.zeros((height, width), dtype=np.float32)

        if transition_type == 'linear':
            # Horizontal gradient
            for x in range(width):
                mask[:, x] = x / width

        elif transition_type == 'radial':
            # Radial gradient from center
            center_x, center_y = width // 2, height // 2
            max_dist = np.sqrt(center_x**2 + center_y**2)

            for y in range(height):
                for x in range(width):
                    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    mask[y, x] = min(dist / max_dist, 1.0)

        elif transition_type == 'diagonal':
            # Diagonal gradient
            for y in range(height):
                for x in range(width):
                    mask[y, x] = (x + y) / (width + height)

        return mask

    def _calculate_compatibility(self, palette1: ColorPalette, palette2: ColorPalette,
                               lighting1: LightingInfo, lighting2: LightingInfo) -> float:
        """Calculate compatibility score between two shots."""
        # Color similarity
        color_sim = self._calculate_color_similarity(palette1, palette2)

        # Brightness compatibility
        brightness_diff = abs(palette1.average_brightness - palette2.average_brightness)
        brightness_score = 1.0 - brightness_diff

        # Saturation compatibility
        saturation_diff = abs(palette1.average_saturation - palette2.average_saturation)
        saturation_score = 1.0 - saturation_diff

        # Lighting compatibility
        lighting_score = self._calculate_lighting_compatibility(lighting1, lighting2)

        # Weighted average
        weights = [0.4, 0.2, 0.2, 0.2]  # color, brightness, saturation, lighting
        scores = [color_sim, brightness_score, saturation_score, lighting_score]

        return sum(w * s for w, s in zip(weights, scores, strict=False))

    def _calculate_color_similarity(self, palette1: ColorPalette,
                                  palette2: ColorPalette) -> float:
        """Calculate similarity between color palettes."""
        similarities = []

        # Compare each color in palette1 with closest in palette2
        for i, color1 in enumerate(palette1.dominant_colors[:3]):
            min_dist = float('inf')
            for color2 in palette2.dominant_colors[:3]:
                dist = self._color_distance(color1, color2)
                min_dist = min(min_dist, dist)

            # Weight by color prominence
            weight = palette1.color_weights[i]
            similarities.append((1.0 - min_dist / 441.67) * weight)  # 441.67 = max RGB distance

        return sum(similarities) / sum(palette1.color_weights[:3])

    def _color_distance(self, color1: tuple[int, int, int],
                       color2: tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two RGB colors."""
        return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2, strict=False)))

    def _calculate_lighting_compatibility(self, lighting1: LightingInfo,
                                        lighting2: LightingInfo) -> float:
        """Calculate compatibility between lighting conditions."""
        # Direction similarity (dot product of normalized vectors)
        direction_sim = (lighting1.direction[0] * lighting2.direction[0] +
                        lighting1.direction[1] * lighting2.direction[1])
        direction_score = (direction_sim + 1) / 2  # Normalize to 0-1

        # Intensity compatibility
        intensity_diff = abs(lighting1.intensity - lighting2.intensity)
        intensity_score = 1.0 - intensity_diff

        # Type compatibility
        type_score = 1.0 if lighting1.type == lighting2.type else 0.5

        # Shadow density compatibility
        shadow_diff = abs(lighting1.shadow_density - lighting2.shadow_density)
        shadow_score = 1.0 - shadow_diff

        # Weighted average
        return (direction_score * 0.3 + intensity_score * 0.3 +
                type_score * 0.2 + shadow_score * 0.2)

    def _suggest_effects(self, palette1: ColorPalette, palette2: ColorPalette,
                        lighting1: LightingInfo, lighting2: LightingInfo) -> list[str]:
        """Suggest transition effects based on analysis."""
        effects = []

        # Color-based suggestions
        temp_diff = abs(palette1.color_temperature - palette2.color_temperature)
        if temp_diff > 0.5:
            effects.append('color_temperature_shift')

        brightness_diff = abs(palette1.average_brightness - palette2.average_brightness)
        if brightness_diff > 0.3:
            effects.append('exposure_ramp')

        saturation_diff = abs(palette1.average_saturation - palette2.average_saturation)
        if saturation_diff > 0.3:
            effects.append('saturation_blend')

        # Lighting-based suggestions
        if lighting1.type != lighting2.type:
            effects.append('lighting_transition')

        if abs(lighting1.shadow_density - lighting2.shadow_density) > 0.3:
            effects.append('shadow_morph')

        # Direction-based suggestions
        direction_diff = np.arccos(np.clip(
            lighting1.direction[0] * lighting2.direction[0] +
            lighting1.direction[1] * lighting2.direction[1], -1, 1
        ))
        if direction_diff > np.pi / 4:  # More than 45 degrees
            effects.append('light_sweep')

        # Always suggest these for smooth transitions
        effects.extend(['gradient_wipe', 'color_match'])

        return list(set(effects))  # Remove duplicates

    def _calculate_average_brightness(self, image: np.ndarray) -> float:
        """Calculate average brightness (0.0 to 1.0)."""
        # Convert to HSV and get V channel
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        return np.mean(hsv[:, :, 2]) / 255.0

    def _calculate_average_saturation(self, image: np.ndarray) -> float:
        """Calculate average saturation (0.0 to 1.0)."""
        # Convert to HSV and get S channel
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        return np.mean(hsv[:, :, 1]) / 255.0

    def _calculate_color_temperature(self, colors: list[tuple[int, int, int]],
                                   weights: list[float]) -> float:
        """Calculate color temperature (0.0=cool to 1.0=warm)."""
        warm_score = 0.0

        for color, weight in zip(colors, weights, strict=False):
            r, g, b = color
            # Simple warm/cool calculation based on R-B difference
            warmth = (r - b) / 255.0  # -1 to 1
            warm_score += (warmth + 1) / 2 * weight  # Normalize to 0-1

        return warm_score


def export_analysis_for_editor(analysis: ColorFlowAnalysis, output_path: str,
                              editor: str = 'resolve') -> None:
    """
    Export color flow analysis for video editors.

    Args:
        analysis: Color flow analysis results
        output_path: Path to save export file
        editor: Target editor ('resolve', 'premiere', 'fcpx', 'fusion')
    """
    if editor == 'resolve':
        _export_for_resolve(analysis, output_path)
    elif editor == 'premiere':
        _export_for_premiere(analysis, output_path)
    elif editor == 'fcpx':
        _export_for_fcpx(analysis, output_path)
    elif editor == 'fusion':
        _export_for_fusion(analysis, output_path)
    else:
        # Default JSON export
        with open(output_path, 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)


def _export_for_resolve(analysis: ColorFlowAnalysis, output_path: str) -> None:
    """Export for DaVinci Resolve."""
    resolve_data = {
        'ColorFlowTransition': {
            'SourceColors': [
                {'R': c[0]/255, 'G': c[1]/255, 'B': c[2]/255}
                for c in analysis.gradient_transition.start_colors
            ],
            'TargetColors': [
                {'R': c[0]/255, 'G': c[1]/255, 'B': c[2]/255}
                for c in analysis.gradient_transition.end_colors
            ],
            'Duration': analysis.gradient_transition.duration_frames,
            'TransitionType': analysis.gradient_transition.transition_type,
            'BlendCurve': analysis.gradient_transition.blend_curve,
            'LightingMatch': {
                'SourceDirection': list(analysis.shot1_lighting.direction),
                'TargetDirection': list(analysis.shot2_lighting.direction),
                'IntensityRamp': [
                    analysis.shot1_lighting.intensity,
                    analysis.shot2_lighting.intensity
                ]
            },
            'SuggestedNodes': analysis.suggested_effects,
            'CompatibilityScore': analysis.compatibility_score
        }
    }

    # Save as Resolve-compatible JSON
    with open(output_path, 'w') as f:
        json.dump(resolve_data, f, indent=2)

    # Also save LUT if significant color shift
    if analysis.compatibility_score < 0.7:
        lut_path = Path(output_path).with_suffix('.cube')
        _generate_color_match_lut(analysis, str(lut_path))


def _export_for_premiere(analysis: ColorFlowAnalysis, output_path: str) -> None:
    """Export for Adobe Premiere Pro."""
    # Create XML structure for Premiere
    premiere_data = {
        'ColorFlowEffect': {
            'name': 'Color Flow Transition',
            'duration': analysis.gradient_transition.duration_frames,
            'parameters': {
                'startColors': [
                    f'#{r:02x}{g:02x}{b:02x}'
                    for r, g, b in analysis.gradient_transition.start_colors
                ],
                'endColors': [
                    f'#{r:02x}{g:02x}{b:02x}'
                    for r, g, b in analysis.gradient_transition.end_colors
                ],
                'transitionType': analysis.gradient_transition.transition_type,
                'lightingAdjustment': {
                    'enabled': True,
                    'startIntensity': analysis.shot1_lighting.intensity,
                    'endIntensity': analysis.shot2_lighting.intensity
                }
            },
            'keyframes': _generate_keyframes(analysis)
        }
    }

    with open(output_path, 'w') as f:
        json.dump(premiere_data, f, indent=2)


def _export_for_fcpx(analysis: ColorFlowAnalysis, output_path: str) -> None:
    """Export for Final Cut Pro X."""
    # FCPX Motion template data
    fcpx_data = {
        'generator': {
            'name': 'Color Flow Transition',
            'duration': analysis.gradient_transition.duration_frames / 30.0,  # seconds
            'parameters': [
                {
                    'name': 'Source Color 1',
                    'type': 'color',
                    'value': analysis.gradient_transition.start_colors[0]
                },
                {
                    'name': 'Target Color 1',
                    'type': 'color',
                    'value': analysis.gradient_transition.end_colors[0]
                },
                {
                    'name': 'Transition Style',
                    'type': 'popup',
                    'value': analysis.gradient_transition.transition_type
                },
                {
                    'name': 'Match Lighting',
                    'type': 'checkbox',
                    'value': True
                }
            ],
            'compatibilityScore': analysis.compatibility_score
        }
    }

    with open(output_path, 'w') as f:
        json.dump(fcpx_data, f, indent=2)


def _export_for_fusion(analysis: ColorFlowAnalysis, output_path: str) -> None:
    """Export for Blackmagic Fusion."""
    # Fusion comp setup
    fusion_comp = {
        'Tools': {
            'ColorFlowGradient': {
                'type': 'Background',
                'inputs': {
                    'Width': 1920,
                    'Height': 1080,
                    'Type': 'Gradient',
                    'GradientType': analysis.gradient_transition.transition_type,
                    'Start': list(analysis.gradient_transition.start_colors[0]),
                    'End': list(analysis.gradient_transition.end_colors[0])
                }
            },
            'ColorCorrector': {
                'type': 'ColorCorrector',
                'inputs': {
                    'MasterRGBGain': analysis.shot2_lighting.intensity,
                    'ColorTemperature': analysis.shot2_palette.color_temperature
                }
            },
            'Merge': {
                'type': 'Merge',
                'inputs': {
                    'BlendMode': 'Normal',
                    'Mix': {'expression': f'time/{analysis.gradient_transition.duration_frames}'}
                }
            }
        },
        'exportInfo': analysis.to_dict()
    }

    with open(output_path, 'w') as f:
        json.dump(fusion_comp, f, indent=2)


def _generate_keyframes(analysis: ColorFlowAnalysis) -> list[dict[str, Any]]:
    """Generate keyframe data for animation."""
    keyframes = []
    duration = analysis.gradient_transition.duration_frames

    # Color keyframes
    for i in range(0, duration + 1, duration // 4):  # 5 keyframes
        t = i / duration
        keyframes.append({
            'time': i,
            'values': {
                'colorBlend': t,
                'brightness': (1 - t) * analysis.shot1_palette.average_brightness +
                             t * analysis.shot2_palette.average_brightness,
                'saturation': (1 - t) * analysis.shot1_palette.average_saturation +
                             t * analysis.shot2_palette.average_saturation
            }
        })

    return keyframes


def _generate_color_match_lut(analysis: ColorFlowAnalysis, output_path: str) -> None:
    """Generate a color matching LUT file."""
    # Simple 3D LUT generation (17x17x17)
    size = 17
    lut = []

    # Header
    lut.append('TITLE "Color Flow Match"')
    lut.append(f'LUT_3D_SIZE {size}')
    lut.append('')

    # Generate LUT values
    for b in range(size):
        for g in range(size):
            for r in range(size):
                # Normalize to 0-1
                nr, ng, nb = r/(size-1), g/(size-1), b/(size-1)

                # Apply color shift based on palette analysis
                # This is a simplified version - real implementation would be more sophisticated
                shifted_r = nr * 0.9 + 0.1 * (analysis.shot2_palette.dominant_colors[0][0] / 255)
                shifted_g = ng * 0.9 + 0.1 * (analysis.shot2_palette.dominant_colors[0][1] / 255)
                shifted_b = nb * 0.9 + 0.1 * (analysis.shot2_palette.dominant_colors[0][2] / 255)

                # Clamp values
                shifted_r = max(0, min(1, shifted_r))
                shifted_g = max(0, min(1, shifted_g))
                shifted_b = max(0, min(1, shifted_b))

                lut.append(f'{shifted_r:.6f} {shifted_g:.6f} {shifted_b:.6f}')

    # Write LUT file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lut))


# Convenience function for batch processing
def analyze_sequence(shot_paths: list[str], transition_duration: int = 30,
                    export_path: str | None = None,
                    editor: str = 'resolve') -> list[ColorFlowAnalysis]:
    """
    Analyze color flow for a sequence of shots.

    Args:
        shot_paths: List of paths to shots in sequence
        transition_duration: Duration of each transition in frames
        export_path: Optional path to export analysis
        editor: Target editor for export

    Returns:
        List of color flow analyses for each consecutive pair
    """
    analyzer = ColorFlowAnalyzer()
    analyses = []

    for i in range(len(shot_paths) - 1):
        analysis = analyzer.analyze_shot_pair(
            shot_paths[i],
            shot_paths[i + 1],
            transition_duration
        )
        analyses.append(analysis)

    if export_path:
        # Export all analyses
        export_data = {
            'sequence': [a.to_dict() for a in analyses],
            'metadata': {
                'shot_count': len(shot_paths),
                'transition_count': len(analyses),
                'total_duration': sum(a.gradient_transition.duration_frames for a in analyses)
            }
        }

        if editor == 'resolve':
            # Special handling for Resolve
            base_path = Path(export_path).with_suffix('')
            for i, analysis in enumerate(analyses):
                export_analysis_for_editor(
                    analysis,
                    f'{base_path}_transition_{i+1}.json',
                    editor
                )
        else:
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)

    return analyses
