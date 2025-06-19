"""
Color Flow Transitions module for smooth color-based transitions between shots.

Analyzes color palettes, creates gradient transitions, and detects lighting
direction for seamless visual flow between consecutive shots.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2  # type: ignore
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
            # TODO: Review unreachable code - else:
            # TODO: Review unreachable code - raise ValueError(f"Could not read video: {path}")
        else:
            # Load image
            img = Image.open(path).convert('RGB')
            return np.array(img)

    # TODO: Review unreachable code - def _extract_color_palette(self, image: np.ndarray) -> ColorPalette:
    # TODO: Review unreachable code - """Extract dominant colors and color properties from image."""
    # TODO: Review unreachable code - # Reshape image to list of pixels
    # TODO: Review unreachable code - pixels = image.reshape(-1, 3)

    # TODO: Review unreachable code - # Use K-means to find dominant colors
    # TODO: Review unreachable code - kmeans = KMeans(n_clusters=self.n_colors, random_state=42)
    # TODO: Review unreachable code - kmeans.fit(pixels)

    # TODO: Review unreachable code - # Get colors and their weights
    # TODO: Review unreachable code - colors = kmeans.cluster_centers_.astype(int)
    # TODO: Review unreachable code - labels = kmeans.labels_
    # TODO: Review unreachable code - weights = [np.sum(labels == i) / len(labels) for i in range(self.n_colors)]

    # TODO: Review unreachable code - # Sort by weight
    # TODO: Review unreachable code - sorted_indices = np.argsort(weights)[::-1]
    # TODO: Review unreachable code - dominant_colors = [tuple(colors[i]) for i in sorted_indices]
    # TODO: Review unreachable code - color_weights = [weights[i] for i in sorted_indices]

    # TODO: Review unreachable code - # Calculate average properties
    # TODO: Review unreachable code - avg_brightness = self._calculate_average_brightness(image)
    # TODO: Review unreachable code - avg_saturation = self._calculate_average_saturation(image)
    # TODO: Review unreachable code - color_temp = self._calculate_color_temperature(dominant_colors, color_weights)

    # TODO: Review unreachable code - return ColorPalette(
    # TODO: Review unreachable code - dominant_colors=dominant_colors,
    # TODO: Review unreachable code - color_weights=color_weights,
    # TODO: Review unreachable code - average_brightness=avg_brightness,
    # TODO: Review unreachable code - average_saturation=avg_saturation,
    # TODO: Review unreachable code - color_temperature=color_temp
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _analyze_lighting(self, image: np.ndarray) -> LightingInfo:
    # TODO: Review unreachable code - """Analyze lighting direction and properties."""
    # TODO: Review unreachable code - # Convert to grayscale for lighting analysis
    # TODO: Review unreachable code - gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # TODO: Review unreachable code - # Apply Sobel filters to detect gradients
    # TODO: Review unreachable code - sobel_x = cv2.Sobel(gray, cv2.CV_64F  # type: ignore, 1, 0, ksize=5)
    # TODO: Review unreachable code - sobel_y = cv2.Sobel(gray, cv2.CV_64F  # type: ignore, 0, 1, ksize=5)

    # TODO: Review unreachable code - # Calculate average gradient direction
    # TODO: Review unreachable code - avg_grad_x = np.mean(sobel_x)
    # TODO: Review unreachable code - avg_grad_y = np.mean(sobel_y)

    # TODO: Review unreachable code - # Normalize direction vector
    # TODO: Review unreachable code - magnitude = np.sqrt(avg_grad_x**2 + avg_grad_y**2)
    # TODO: Review unreachable code - if magnitude > 0:
    # TODO: Review unreachable code - direction = (avg_grad_x / magnitude, avg_grad_y / magnitude)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - direction = (0.0, 0.0)

    # TODO: Review unreachable code - # Calculate intensity (average brightness of top 20% pixels)
    # TODO: Review unreachable code - bright_threshold = np.percentile(gray, 80)
    # TODO: Review unreachable code - intensity = np.mean(gray[gray > bright_threshold]) / 255.0

    # TODO: Review unreachable code - # Determine lighting type
    # TODO: Review unreachable code - std_dev = np.std(gray)
    # TODO: Review unreachable code - if std_dev < 30:
    # TODO: Review unreachable code - light_type = 'ambient'
    # TODO: Review unreachable code - elif std_dev > 70:
    # TODO: Review unreachable code - light_type = 'directional'
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - light_type = 'mixed'

    # TODO: Review unreachable code - # Calculate shadow density
    # TODO: Review unreachable code - dark_threshold = np.percentile(gray, 20)
    # TODO: Review unreachable code - shadow_pixels = gray[gray < dark_threshold]
    # TODO: Review unreachable code - shadow_density = len(shadow_pixels) / gray.size if gray.size > 0 else 0.0

    # TODO: Review unreachable code - return LightingInfo(
    # TODO: Review unreachable code - direction=direction,
    # TODO: Review unreachable code - intensity=intensity,
    # TODO: Review unreachable code - type=light_type,
    # TODO: Review unreachable code - shadow_density=shadow_density
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _create_gradient_transition(self, palette1: ColorPalette, palette2: ColorPalette,
    # TODO: Review unreachable code - lighting1: LightingInfo, lighting2: LightingInfo,
    # TODO: Review unreachable code - duration: int) -> GradientTransition:
    # TODO: Review unreachable code - """Create gradient transition based on color and lighting analysis."""
    # TODO: Review unreachable code - # Use top 3 colors from each palette
    # TODO: Review unreachable code - start_colors = palette1.dominant_colors[:3]
    # TODO: Review unreachable code - end_colors = palette2.dominant_colors[:3]

    # TODO: Review unreachable code - # Determine transition type based on lighting
    # TODO: Review unreachable code - if lighting1.type == 'directional' and lighting2.type == 'directional':
    # TODO: Review unreachable code - # Use diagonal transition aligned with average lighting direction
    # TODO: Review unreachable code - (
    # TODO: Review unreachable code - (lighting1.direction[0] + lighting2.direction[0]) / 2,
    # TODO: Review unreachable code - (lighting1.direction[1] + lighting2.direction[1]) / 2
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - transition_type = 'diagonal'
    # TODO: Review unreachable code - elif abs(palette1.average_brightness - palette2.average_brightness) > 0.3:
    # TODO: Review unreachable code - # Use radial transition for significant brightness changes
    # TODO: Review unreachable code - transition_type = 'radial'
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Default to linear transition
    # TODO: Review unreachable code - transition_type = 'linear'

    # TODO: Review unreachable code - # Determine blend curve based on color temperature difference
    # TODO: Review unreachable code - temp_diff = abs(palette1.color_temperature - palette2.color_temperature)
    # TODO: Review unreachable code - if temp_diff > 0.3:
    # TODO: Review unreachable code - blend_curve = 'ease-in-out'
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - blend_curve = 'linear'

    # TODO: Review unreachable code - # Create basic mask data (can be enhanced with actual masking)
    # TODO: Review unreachable code - mask_data = self._create_transition_mask(transition_type, (1920, 1080))

    # TODO: Review unreachable code - return GradientTransition(
    # TODO: Review unreachable code - start_colors=start_colors,
    # TODO: Review unreachable code - end_colors=end_colors,
    # TODO: Review unreachable code - duration_frames=duration,
    # TODO: Review unreachable code - transition_type=transition_type,
    # TODO: Review unreachable code - blend_curve=blend_curve,
    # TODO: Review unreachable code - mask_data=mask_data
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _create_transition_mask(self, transition_type: str,
    # TODO: Review unreachable code - size: tuple[int, int]) -> np.ndarray:
    # TODO: Review unreachable code - """Create transition mask for advanced effects."""
    # TODO: Review unreachable code - width, height = size
    # TODO: Review unreachable code - mask = np.zeros((height, width), dtype=np.float32)

    # TODO: Review unreachable code - if transition_type == 'linear':
    # TODO: Review unreachable code - # Horizontal gradient
    # TODO: Review unreachable code - for x in range(width):
    # TODO: Review unreachable code - mask[:, x] = x / width

    # TODO: Review unreachable code - elif transition_type == 'radial':
    # TODO: Review unreachable code - # Radial gradient from center
    # TODO: Review unreachable code - center_x, center_y = width // 2, height // 2
    # TODO: Review unreachable code - max_dist = np.sqrt(center_x**2 + center_y**2)

    # TODO: Review unreachable code - for y in range(height):
    # TODO: Review unreachable code - for x in range(width):
    # TODO: Review unreachable code - dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    # TODO: Review unreachable code - mask[y, x] = min(dist / max_dist, 1.0)

    # TODO: Review unreachable code - elif transition_type == 'diagonal':
    # TODO: Review unreachable code - # Diagonal gradient
    # TODO: Review unreachable code - for y in range(height):
    # TODO: Review unreachable code - for x in range(width):
    # TODO: Review unreachable code - mask[y, x] = (x + y) / (width + height)

    # TODO: Review unreachable code - return mask

    # TODO: Review unreachable code - def _calculate_compatibility(self, palette1: ColorPalette, palette2: ColorPalette,
    # TODO: Review unreachable code - lighting1: LightingInfo, lighting2: LightingInfo) -> float:
    # TODO: Review unreachable code - """Calculate compatibility score between two shots."""
    # TODO: Review unreachable code - # Color similarity
    # TODO: Review unreachable code - color_sim = self._calculate_color_similarity(palette1, palette2)

    # TODO: Review unreachable code - # Brightness compatibility
    # TODO: Review unreachable code - brightness_diff = abs(palette1.average_brightness - palette2.average_brightness)
    # TODO: Review unreachable code - brightness_score = 1.0 - brightness_diff

    # TODO: Review unreachable code - # Saturation compatibility
    # TODO: Review unreachable code - saturation_diff = abs(palette1.average_saturation - palette2.average_saturation)
    # TODO: Review unreachable code - saturation_score = 1.0 - saturation_diff

    # TODO: Review unreachable code - # Lighting compatibility
    # TODO: Review unreachable code - lighting_score = self._calculate_lighting_compatibility(lighting1, lighting2)

    # TODO: Review unreachable code - # Weighted average
    # TODO: Review unreachable code - weights = [0.4, 0.2, 0.2, 0.2]  # color, brightness, saturation, lighting
    # TODO: Review unreachable code - scores = [color_sim, brightness_score, saturation_score, lighting_score]

    # TODO: Review unreachable code - return sum(w * s for w, s in zip(weights, scores, strict=False))

    # TODO: Review unreachable code - def _calculate_color_similarity(self, palette1: ColorPalette,
    # TODO: Review unreachable code - palette2: ColorPalette) -> float:
    # TODO: Review unreachable code - """Calculate similarity between color palettes."""
    # TODO: Review unreachable code - similarities = []

    # TODO: Review unreachable code - # Compare each color in palette1 with closest in palette2
    # TODO: Review unreachable code - for i, color1 in enumerate(palette1.dominant_colors[:3]):
    # TODO: Review unreachable code - min_dist = float('inf')
    # TODO: Review unreachable code - for color2 in palette2.dominant_colors[:3]:
    # TODO: Review unreachable code - dist = self._color_distance(color1, color2)
    # TODO: Review unreachable code - min_dist = min(min_dist, dist)

    # TODO: Review unreachable code - # Weight by color prominence
    # TODO: Review unreachable code - weight = palette1.color_weights[i]
    # TODO: Review unreachable code - similarities.append((1.0 - min_dist / 441.67) * weight)  # 441.67 = max RGB distance

    # TODO: Review unreachable code - return sum(similarities) / sum(palette1.color_weights[:3])

    # TODO: Review unreachable code - def _color_distance(self, color1: tuple[int, int, int],
    # TODO: Review unreachable code - color2: tuple[int, int, int]) -> float:
    # TODO: Review unreachable code - """Calculate Euclidean distance between two RGB colors."""
    # TODO: Review unreachable code - return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2, strict=False)))

    # TODO: Review unreachable code - def _calculate_lighting_compatibility(self, lighting1: LightingInfo,
    # TODO: Review unreachable code - lighting2: LightingInfo) -> float:
    # TODO: Review unreachable code - """Calculate compatibility between lighting conditions."""
    # TODO: Review unreachable code - # Direction similarity (dot product of normalized vectors)
    # TODO: Review unreachable code - direction_sim = (lighting1.direction[0] * lighting2.direction[0] +
    # TODO: Review unreachable code - lighting1.direction[1] * lighting2.direction[1])
    # TODO: Review unreachable code - direction_score = (direction_sim + 1) / 2  # Normalize to 0-1

    # TODO: Review unreachable code - # Intensity compatibility
    # TODO: Review unreachable code - intensity_diff = abs(lighting1.intensity - lighting2.intensity)
    # TODO: Review unreachable code - intensity_score = 1.0 - intensity_diff

    # TODO: Review unreachable code - # Type compatibility
    # TODO: Review unreachable code - type_score = 1.0 if lighting1.type == lighting2.type else 0.5

    # TODO: Review unreachable code - # Shadow density compatibility
    # TODO: Review unreachable code - shadow_diff = abs(lighting1.shadow_density - lighting2.shadow_density)
    # TODO: Review unreachable code - shadow_score = 1.0 - shadow_diff

    # TODO: Review unreachable code - # Weighted average
    # TODO: Review unreachable code - return (direction_score * 0.3 + intensity_score * 0.3 +
    # TODO: Review unreachable code - type_score * 0.2 + shadow_score * 0.2)

    # TODO: Review unreachable code - def _suggest_effects(self, palette1: ColorPalette, palette2: ColorPalette,
    # TODO: Review unreachable code - lighting1: LightingInfo, lighting2: LightingInfo) -> list[str]:
    # TODO: Review unreachable code - """Suggest transition effects based on analysis."""
    # TODO: Review unreachable code - effects = []

    # TODO: Review unreachable code - # Color-based suggestions
    # TODO: Review unreachable code - temp_diff = abs(palette1.color_temperature - palette2.color_temperature)
    # TODO: Review unreachable code - if temp_diff > 0.5:
    # TODO: Review unreachable code - effects.append('color_temperature_shift')

    # TODO: Review unreachable code - brightness_diff = abs(palette1.average_brightness - palette2.average_brightness)
    # TODO: Review unreachable code - if brightness_diff > 0.3:
    # TODO: Review unreachable code - effects.append('exposure_ramp')

    # TODO: Review unreachable code - saturation_diff = abs(palette1.average_saturation - palette2.average_saturation)
    # TODO: Review unreachable code - if saturation_diff > 0.3:
    # TODO: Review unreachable code - effects.append('saturation_blend')

    # TODO: Review unreachable code - # Lighting-based suggestions
    # TODO: Review unreachable code - if lighting1.type != lighting2.type:
    # TODO: Review unreachable code - effects.append('lighting_transition')

    # TODO: Review unreachable code - if abs(lighting1.shadow_density - lighting2.shadow_density) > 0.3:
    # TODO: Review unreachable code - effects.append('shadow_morph')

    # TODO: Review unreachable code - # Direction-based suggestions
    # TODO: Review unreachable code - direction_diff = np.arccos(np.clip(
    # TODO: Review unreachable code - lighting1.direction[0] * lighting2.direction[0] +
    # TODO: Review unreachable code - lighting1.direction[1] * lighting2.direction[1], -1, 1
    # TODO: Review unreachable code - ))
    # TODO: Review unreachable code - if direction_diff > np.pi / 4:  # More than 45 degrees
    # TODO: Review unreachable code - effects.append('light_sweep')

    # TODO: Review unreachable code - # Always suggest these for smooth transitions
    # TODO: Review unreachable code - effects.extend(['gradient_wipe', 'color_match'])

    # TODO: Review unreachable code - return list(set(effects))  # Remove duplicates

    # TODO: Review unreachable code - def _calculate_average_brightness(self, image: np.ndarray) -> float:
    # TODO: Review unreachable code - """Calculate average brightness (0.0 to 1.0)."""
    # TODO: Review unreachable code - # Convert to HSV and get V channel
    # TODO: Review unreachable code - hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    # TODO: Review unreachable code - return np.mean(hsv[:, :, 2]) / 255.0

    # TODO: Review unreachable code - def _calculate_average_saturation(self, image: np.ndarray) -> float:
    # TODO: Review unreachable code - """Calculate average saturation (0.0 to 1.0)."""
    # TODO: Review unreachable code - # Convert to HSV and get S channel
    # TODO: Review unreachable code - hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    # TODO: Review unreachable code - return np.mean(hsv[:, :, 1]) / 255.0

    # TODO: Review unreachable code - def _calculate_color_temperature(self, colors: list[tuple[int, int, int]],
    # TODO: Review unreachable code - weights: list[float]) -> float:
    # TODO: Review unreachable code - """Calculate color temperature (0.0=cool to 1.0=warm)."""
    # TODO: Review unreachable code - warm_score = 0.0

    # TODO: Review unreachable code - for color, weight in zip(colors, weights, strict=False):
    # TODO: Review unreachable code - r, g, b = color
    # TODO: Review unreachable code - # Simple warm/cool calculation based on R-B difference
    # TODO: Review unreachable code - warmth = (r - b) / 255.0  # -1 to 1
    # TODO: Review unreachable code - warm_score += (warmth + 1) / 2 * weight  # Normalize to 0-1

    # TODO: Review unreachable code - return warm_score


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


# TODO: Review unreachable code - def _generate_color_match_lut(analysis: ColorFlowAnalysis, output_path: str) -> None:
# TODO: Review unreachable code - """Generate a color matching LUT file."""
# TODO: Review unreachable code - # Simple 3D LUT generation (17x17x17)
# TODO: Review unreachable code - size = 17
# TODO: Review unreachable code - lut = []

# TODO: Review unreachable code - # Header
# TODO: Review unreachable code - lut.append('TITLE "Color Flow Match"')
# TODO: Review unreachable code - lut.append(f'LUT_3D_SIZE {size}')
# TODO: Review unreachable code - lut.append('')

# TODO: Review unreachable code - # Generate LUT values
# TODO: Review unreachable code - for b in range(size):
# TODO: Review unreachable code - for g in range(size):
# TODO: Review unreachable code - for r in range(size):
# TODO: Review unreachable code - # Normalize to 0-1
# TODO: Review unreachable code - nr, ng, nb = r/(size-1), g/(size-1), b/(size-1)

# TODO: Review unreachable code - # Apply color shift based on palette analysis
# TODO: Review unreachable code - # This is a simplified version - real implementation would be more sophisticated
# TODO: Review unreachable code - shifted_r = nr * 0.9 + 0.1 * (analysis.shot2_palette.dominant_colors[0][0] / 255)
# TODO: Review unreachable code - shifted_g = ng * 0.9 + 0.1 * (analysis.shot2_palette.dominant_colors[0][1] / 255)
# TODO: Review unreachable code - shifted_b = nb * 0.9 + 0.1 * (analysis.shot2_palette.dominant_colors[0][2] / 255)

# TODO: Review unreachable code - # Clamp values
# TODO: Review unreachable code - shifted_r = max(0, min(1, shifted_r))
# TODO: Review unreachable code - shifted_g = max(0, min(1, shifted_g))
# TODO: Review unreachable code - shifted_b = max(0, min(1, shifted_b))

# TODO: Review unreachable code - lut.append(f'{shifted_r:.6f} {shifted_g:.6f} {shifted_b:.6f}')

# TODO: Review unreachable code - # Write LUT file
# TODO: Review unreachable code - with open(output_path, 'w') as f:
# TODO: Review unreachable code - f.write('\n'.join(lut))


# TODO: Review unreachable code - # Convenience function for batch processing
# TODO: Review unreachable code - def analyze_sequence(shot_paths: list[str], transition_duration: int = 30,
# TODO: Review unreachable code - export_path: str | None = None,
# TODO: Review unreachable code - editor: str = 'resolve') -> list[ColorFlowAnalysis]:
# TODO: Review unreachable code - """
# TODO: Review unreachable code - Analyze color flow for a sequence of shots.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - shot_paths: List of paths to shots in sequence
# TODO: Review unreachable code - transition_duration: Duration of each transition in frames
# TODO: Review unreachable code - export_path: Optional path to export analysis
# TODO: Review unreachable code - editor: Target editor for export

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - List of color flow analyses for each consecutive pair
# TODO: Review unreachable code - """
# TODO: Review unreachable code - analyzer = ColorFlowAnalyzer()
# TODO: Review unreachable code - analyses = []

# TODO: Review unreachable code - for i in range(len(shot_paths) - 1):
# TODO: Review unreachable code - analysis = analyzer.analyze_shot_pair(
# TODO: Review unreachable code - shot_paths[i],
# TODO: Review unreachable code - shot_paths[i + 1],
# TODO: Review unreachable code - transition_duration
# TODO: Review unreachable code - )
# TODO: Review unreachable code - analyses.append(analysis)

# TODO: Review unreachable code - if export_path:
# TODO: Review unreachable code - # Export all analyses
# TODO: Review unreachable code - export_data = {
# TODO: Review unreachable code - 'sequence': [a.to_dict() for a in analyses],
# TODO: Review unreachable code - 'metadata': {
# TODO: Review unreachable code - 'shot_count': len(shot_paths),
# TODO: Review unreachable code - 'transition_count': len(analyses),
# TODO: Review unreachable code - 'total_duration': sum(a.gradient_transition.duration_frames for a in analyses)
# TODO: Review unreachable code - }
# TODO: Review unreachable code - }

# TODO: Review unreachable code - if editor == 'resolve':
# TODO: Review unreachable code - # Special handling for Resolve
# TODO: Review unreachable code - base_path = Path(export_path).with_suffix('')
# TODO: Review unreachable code - for i, analysis in enumerate(analyses):
# TODO: Review unreachable code - export_analysis_for_editor(
# TODO: Review unreachable code - analysis,
# TODO: Review unreachable code - f'{base_path}_transition_{i+1}.json',
# TODO: Review unreachable code - editor
# TODO: Review unreachable code - )
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - with open(export_path, 'w') as f:
# TODO: Review unreachable code - json.dump(export_data, f, indent=2)

# TODO: Review unreachable code - return analyses
