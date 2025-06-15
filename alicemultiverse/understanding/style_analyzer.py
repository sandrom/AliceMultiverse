"""Style similarity analyzer for extracting visual DNA from images.

This module extracts style fingerprints including color palettes, composition,
texture, and lighting characteristics for style-based clustering.
"""

import colorsys
import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


@dataclass
class ColorPalette:
    """Extracted color palette information."""

    dominant_colors: list[tuple[int, int, int]] = field(default_factory=list)
    color_names: list[str] = field(default_factory=list)
    color_percentages: list[float] = field(default_factory=list)
    temperature: str = "neutral"  # warm, cool, neutral
    saturation: str = "medium"    # vibrant, muted, monochrome
    brightness: str = "medium"    # bright, dark, medium
    harmony_type: str = "mixed"   # complementary, analogous, triadic, monochromatic


@dataclass
class CompositionAnalysis:
    """Image composition characteristics."""

    rule_of_thirds: float = 0.0  # 0-1 score
    symmetry_score: float = 0.0   # 0-1 score
    balance_type: str = "centered"  # centered, left-heavy, right-heavy
    focal_points: list[tuple[float, float]] = field(default_factory=list)  # Normalized coords
    depth_layers: int = 1  # Foreground/midground/background
    complexity: str = "medium"  # simple, medium, complex
    negative_space_ratio: float = 0.0


@dataclass
class TextureAnalysis:
    """Texture characteristics of the image."""

    overall_texture: str = "smooth"  # smooth, rough, mixed
    texture_variance: float = 0.0
    patterns_detected: list[str] = field(default_factory=list)
    grain_level: str = "none"  # none, fine, coarse
    detail_density: str = "medium"  # sparse, medium, dense


@dataclass
class LightingAnalysis:
    """Lighting characteristics."""

    light_direction: str = "frontal"  # frontal, side, back, ambient
    contrast_level: str = "medium"  # low, medium, high
    shadows: str = "soft"  # soft, hard, minimal
    highlights: str = "balanced"  # blown, balanced, subdued
    mood_lighting: str = "neutral"  # dramatic, soft, harsh, natural
    time_of_day: str | None = None  # golden_hour, blue_hour, midday, night


@dataclass
class StyleFingerprint:
    """Complete style fingerprint of an image."""

    image_path: str
    color_palette: ColorPalette
    composition: CompositionAnalysis
    texture: TextureAnalysis
    lighting: LightingAnalysis
    style_vector: np.ndarray = field(default_factory=lambda: np.array([]))
    style_tags: list[str] = field(default_factory=list)

    def similarity_score(self, other: 'StyleFingerprint') -> float:
        """Calculate similarity to another style fingerprint."""
        if len(self.style_vector) == 0 or len(other.style_vector) == 0:
            return 0.0

        # Cosine similarity of style vectors
        dot_product = np.dot(self.style_vector, other.style_vector)
        norm_product = np.linalg.norm(self.style_vector) * np.linalg.norm(other.style_vector)

        if norm_product == 0:
            return 0.0

        return float(dot_product / norm_product)


class StyleAnalyzer:
    """Analyzes images to extract style fingerprints."""

    def __init__(self):
        """Initialize style analyzer."""
        self.color_names = {
            "red": (255, 0, 0),
            "orange": (255, 165, 0),
            "yellow": (255, 255, 0),
            "green": (0, 255, 0),
            "cyan": (0, 255, 255),
            "blue": (0, 0, 255),
            "purple": (128, 0, 128),
            "pink": (255, 192, 203),
            "brown": (165, 42, 42),
            "black": (0, 0, 0),
            "white": (255, 255, 255),
            "gray": (128, 128, 128)
        }

    def analyze_image(self, image_path: Path) -> StyleFingerprint:
        """Extract complete style fingerprint from an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            StyleFingerprint with all style characteristics
        """
        try:
            # Load image
            pil_image = Image.open(image_path).convert('RGB')
            cv_image = cv2.imread(str(image_path))
            cv_image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

            # Extract components
            color_palette = self._analyze_colors(pil_image)
            composition = self._analyze_composition(cv_image)
            texture = self._analyze_texture(cv_image)
            lighting = self._analyze_lighting(cv_image_rgb)

            # Build style vector
            style_vector = self._build_style_vector(
                color_palette, composition, texture, lighting
            )

            # Generate style tags
            style_tags = self._generate_style_tags(
                color_palette, composition, texture, lighting
            )

            return StyleFingerprint(
                image_path=str(image_path),
                color_palette=color_palette,
                composition=composition,
                texture=texture,
                lighting=lighting,
                style_vector=style_vector,
                style_tags=style_tags
            )

        except Exception as e:
            logger.error(f"Failed to analyze style for {image_path}: {e}")
            # Return empty fingerprint on error
            return StyleFingerprint(
                image_path=str(image_path),
                color_palette=ColorPalette(),
                composition=CompositionAnalysis(),
                texture=TextureAnalysis(),
                lighting=LightingAnalysis()
            )

    def _analyze_colors(self, image: Image.Image, n_colors: int = 5) -> ColorPalette:
        """Extract color palette from image."""
        # Resize for faster processing
        thumb = image.copy()
        thumb.thumbnail((200, 200))

        # Convert to numpy array
        pixels = np.array(thumb).reshape(-1, 3)

        # Extract dominant colors using KMeans
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)

        # Get colors and their percentages
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        color_counts = Counter(labels)
        total_pixels = len(labels)

        dominant_colors = []
        color_names = []
        color_percentages = []

        for i, color in enumerate(colors):
            rgb = tuple(color)
            dominant_colors.append(rgb)
            color_names.append(self._get_color_name(rgb))
            color_percentages.append(color_counts[i] / total_pixels)

        # Sort by percentage
        sorted_indices = np.argsort(color_percentages)[::-1]
        dominant_colors = [dominant_colors[i] for i in sorted_indices]
        color_names = [color_names[i] for i in sorted_indices]
        color_percentages = [color_percentages[i] for i in sorted_indices]

        # Analyze color properties
        temperature = self._analyze_color_temperature(dominant_colors, color_percentages)
        saturation = self._analyze_saturation(dominant_colors, color_percentages)
        brightness = self._analyze_brightness(dominant_colors, color_percentages)
        harmony = self._analyze_color_harmony(dominant_colors)

        return ColorPalette(
            dominant_colors=dominant_colors,
            color_names=color_names,
            color_percentages=color_percentages,
            temperature=temperature,
            saturation=saturation,
            brightness=brightness,
            harmony_type=harmony
        )

    def _get_color_name(self, rgb: tuple[int, int, int]) -> str:
        """Get nearest color name for RGB value."""
        min_distance = float('inf')
        closest_name = "unknown"

        for name, reference_rgb in self.color_names.items():
            distance = sum((a - b) ** 2 for a, b in zip(rgb, reference_rgb, strict=False)) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_name = name

        return closest_name

    def _analyze_color_temperature(self, colors: list[tuple[int, int, int]],
                                 percentages: list[float]) -> str:
        """Determine overall color temperature."""
        warm_score = 0.0
        cool_score = 0.0

        for color, pct in zip(colors, percentages, strict=False):
            r, g, b = color
            # Warm colors have more red/yellow
            if r > b:
                warm_score += pct * (r - b) / 255
            # Cool colors have more blue/green
            elif b > r:
                cool_score += pct * (b - r) / 255

        if warm_score > cool_score * 1.3:
            return "warm"
        elif cool_score > warm_score * 1.3:
            return "cool"
        else:
            return "neutral"

    def _analyze_saturation(self, colors: list[tuple[int, int, int]],
                          percentages: list[float]) -> str:
        """Determine overall saturation level."""
        avg_saturation = 0.0

        for color, pct in zip(colors, percentages, strict=False):
            # Convert to HSV
            r, g, b = [x / 255.0 for x in color]
            _, s, _ = colorsys.rgb_to_hsv(r, g, b)
            avg_saturation += s * pct

        if avg_saturation < 0.2:
            return "monochrome"
        elif avg_saturation < 0.5:
            return "muted"
        else:
            return "vibrant"

    def _analyze_brightness(self, colors: list[tuple[int, int, int]],
                          percentages: list[float]) -> str:
        """Determine overall brightness."""
        avg_brightness = 0.0

        for color, pct in zip(colors, percentages, strict=False):
            # Simple luminance calculation
            r, g, b = color
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            avg_brightness += luminance * pct

        if avg_brightness < 0.3:
            return "dark"
        elif avg_brightness > 0.7:
            return "bright"
        else:
            return "medium"

    def _analyze_color_harmony(self, colors: list[tuple[int, int, int]]) -> str:
        """Determine color harmony type."""
        if len(colors) < 2:
            return "monochromatic"

        # Convert to HSV for harmony analysis
        hsv_colors = []
        for color in colors[:3]:  # Use top 3 colors
            r, g, b = [x / 255.0 for x in color]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            hsv_colors.append((h * 360, s, v))

        # Check for monochromatic (similar hues)
        hues = [h for h, _, _ in hsv_colors]
        hue_variance = np.std(hues)

        if hue_variance < 30:
            return "monochromatic"

        # Check for complementary (opposite hues)
        if len(hues) >= 2:
            hue_diff = abs(hues[0] - hues[1])
            if 150 < hue_diff < 210:
                return "complementary"

        # Check for analogous (adjacent hues)
        if hue_variance < 60:
            return "analogous"

        return "mixed"

    def _analyze_composition(self, image: np.ndarray) -> CompositionAnalysis:
        """Analyze image composition."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Rule of thirds analysis
        thirds_score = self._check_rule_of_thirds(gray)

        # Symmetry analysis
        symmetry_score = self._check_symmetry(gray)

        # Balance analysis
        balance = self._analyze_balance(gray)

        # Find focal points using corner detection
        focal_points = self._find_focal_points(gray)

        # Complexity analysis
        complexity = self._analyze_complexity(gray)

        # Negative space
        negative_space = self._analyze_negative_space(gray)

        return CompositionAnalysis(
            rule_of_thirds=thirds_score,
            symmetry_score=symmetry_score,
            balance_type=balance,
            focal_points=focal_points,
            complexity=complexity,
            negative_space_ratio=negative_space
        )

    def _check_rule_of_thirds(self, gray: np.ndarray) -> float:
        """Check adherence to rule of thirds."""
        h, w = gray.shape

        # Define thirds lines
        v_third1 = w // 3
        v_third2 = 2 * w // 3
        h_third1 = h // 3
        h_third2 = 2 * h // 3

        # Use edge detection to find strong features
        edges = cv2.Canny(gray, 50, 150)

        # Check edge density near thirds lines
        score = 0.0
        margin = max(w, h) // 20  # 5% margin

        # Vertical lines
        score += np.sum(edges[:, v_third1-margin:v_third1+margin]) / (h * margin * 2)
        score += np.sum(edges[:, v_third2-margin:v_third2+margin]) / (h * margin * 2)

        # Horizontal lines
        score += np.sum(edges[h_third1-margin:h_third1+margin, :]) / (w * margin * 2)
        score += np.sum(edges[h_third2-margin:h_third2+margin, :]) / (w * margin * 2)

        return min(score / 1000, 1.0)  # Normalize to 0-1

    def _check_symmetry(self, gray: np.ndarray) -> float:
        """Check image symmetry."""
        h, w = gray.shape

        # Vertical symmetry
        left_half = gray[:, :w//2]
        right_half = cv2.flip(gray[:, w//2:], 1)

        # Resize to same size if needed
        min_w = min(left_half.shape[1], right_half.shape[1])
        left_half = left_half[:, :min_w]
        right_half = right_half[:, :min_w]

        # Calculate similarity
        diff = np.abs(left_half.astype(float) - right_half.astype(float))
        symmetry_score = 1.0 - (np.mean(diff) / 255.0)

        return symmetry_score

    def _analyze_balance(self, gray: np.ndarray) -> str:
        """Analyze visual balance."""
        h, w = gray.shape

        # Calculate visual weight for each half
        left_weight = np.mean(gray[:, :w//2])
        right_weight = np.mean(gray[:, w//2:])

        ratio = left_weight / (right_weight + 1e-6)

        if 0.9 < ratio < 1.1:
            return "centered"
        elif ratio > 1.1:
            return "left-heavy"
        else:
            return "right-heavy"

    def _find_focal_points(self, gray: np.ndarray) -> list[tuple[float, float]]:
        """Find focal points using corner detection."""
        h, w = gray.shape

        # Use Harris corner detection
        corners = cv2.cornerHarris(gray, 2, 3, 0.04)

        # Find top corners
        threshold = 0.01 * corners.max()
        corner_coords = np.where(corners > threshold)

        # Cluster nearby corners
        focal_points = []
        if len(corner_coords[0]) > 0:
            points = list(zip(corner_coords[1] / w, corner_coords[0] / h, strict=False))

            # Simple clustering - take top 3 spread out points
            selected = []
            for point in points:
                if not selected:
                    selected.append(point)
                else:
                    # Check if far enough from existing points
                    min_dist = min(
                        ((p[0] - point[0])**2 + (p[1] - point[1])**2)**0.5
                        for p in selected
                    )
                    if min_dist > 0.2 and len(selected) < 3:
                        selected.append(point)

            focal_points = selected

        return focal_points

    def _analyze_complexity(self, gray: np.ndarray) -> str:
        """Analyze visual complexity."""
        # Use edge density as complexity measure
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges) / (edges.shape[0] * edges.shape[1] * 255)

        if edge_density < 0.05:
            return "simple"
        elif edge_density < 0.15:
            return "medium"
        else:
            return "complex"

    def _analyze_negative_space(self, gray: np.ndarray) -> float:
        """Analyze negative space ratio."""
        # Use thresholding to separate subject from background
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Count background pixels
        background_pixels = np.sum(binary == 0)
        total_pixels = binary.shape[0] * binary.shape[1]

        return background_pixels / total_pixels

    def _analyze_texture(self, image: np.ndarray) -> TextureAnalysis:
        """Analyze image texture."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Calculate texture variance using Laplacian
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_variance = laplacian.var()

        # Determine texture type
        if texture_variance < 100:
            overall_texture = "smooth"
        elif texture_variance < 500:
            overall_texture = "medium"
        else:
            overall_texture = "rough"

        # Detect patterns using FFT
        patterns = self._detect_patterns(gray)

        # Analyze grain
        grain_level = "none"
        if texture_variance > 50:
            # Use high-pass filter to detect grain
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            grain = cv2.filter2D(gray, -1, kernel)
            grain_std = np.std(grain)

            if grain_std > 30:
                grain_level = "coarse"
            elif grain_std > 15:
                grain_level = "fine"

        # Detail density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges) / (edges.shape[0] * edges.shape[1] * 255)

        if edge_density < 0.05:
            detail_density = "sparse"
        elif edge_density < 0.15:
            detail_density = "medium"
        else:
            detail_density = "dense"

        return TextureAnalysis(
            overall_texture=overall_texture,
            texture_variance=texture_variance,
            patterns_detected=patterns,
            grain_level=grain_level,
            detail_density=detail_density
        )

    def _detect_patterns(self, gray: np.ndarray) -> list[str]:
        """Detect repeating patterns in image."""
        patterns = []

        # Use FFT to find periodic patterns
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.abs(f_shift)

        # Look for peaks in frequency domain
        threshold = np.percentile(magnitude, 99)
        peaks = magnitude > threshold

        # Analyze peak patterns
        peak_count = np.sum(peaks)
        if peak_count > 100:
            patterns.append("repetitive")

        # Check for specific patterns
        # Stripes: strong horizontal or vertical frequencies
        h, w = gray.shape
        h_freq = np.sum(magnitude[h//2-5:h//2+5, :])
        v_freq = np.sum(magnitude[:, w//2-5:w//2+5])

        if h_freq > magnitude.sum() * 0.1:
            patterns.append("horizontal_stripes")
        if v_freq > magnitude.sum() * 0.1:
            patterns.append("vertical_stripes")

        return patterns

    def _analyze_lighting(self, image: np.ndarray) -> LightingAnalysis:
        """Analyze lighting characteristics."""
        # Convert to LAB for better lighting analysis
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l_channel = lab[:, :, 0]

        # Analyze contrast
        contrast_level = self._analyze_contrast(l_channel)

        # Analyze light direction
        light_direction = self._analyze_light_direction(l_channel)

        # Analyze shadows and highlights
        shadows, highlights = self._analyze_shadows_highlights(l_channel)

        # Determine mood lighting
        mood = self._determine_lighting_mood(l_channel, contrast_level)

        # Guess time of day from color temperature and brightness
        time_of_day = self._guess_time_of_day(image, l_channel)

        return LightingAnalysis(
            light_direction=light_direction,
            contrast_level=contrast_level,
            shadows=shadows,
            highlights=highlights,
            mood_lighting=mood,
            time_of_day=time_of_day
        )

    def _analyze_contrast(self, l_channel: np.ndarray) -> str:
        """Analyze contrast level."""
        std_dev = np.std(l_channel)

        if std_dev < 20:
            return "low"
        elif std_dev < 40:
            return "medium"
        else:
            return "high"

    def _analyze_light_direction(self, l_channel: np.ndarray) -> str:
        """Analyze primary light direction."""
        h, w = l_channel.shape

        # Divide image into quadrants
        top_half = np.mean(l_channel[:h//2, :])
        bottom_half = np.mean(l_channel[h//2:, :])
        left_half = np.mean(l_channel[:, :w//2])
        right_half = np.mean(l_channel[:, w//2:])

        # Determine direction based on brightness distribution
        vertical_ratio = top_half / (bottom_half + 1e-6)
        horizontal_ratio = left_half / (right_half + 1e-6)

        if abs(vertical_ratio - 1.0) < 0.1 and abs(horizontal_ratio - 1.0) < 0.1:
            return "ambient"
        elif vertical_ratio > 1.2:
            return "top"
        elif vertical_ratio < 0.8:
            return "bottom"
        elif horizontal_ratio > 1.2:
            return "left"
        elif horizontal_ratio < 0.8:
            return "right"
        else:
            return "frontal"

    def _analyze_shadows_highlights(self, l_channel: np.ndarray) -> tuple[str, str]:
        """Analyze shadow and highlight characteristics."""
        # Shadow analysis
        shadow_threshold = np.percentile(l_channel, 20)
        shadow_pixels = l_channel < shadow_threshold
        shadow_contrast = np.std(l_channel[shadow_pixels]) if np.any(shadow_pixels) else 0

        if shadow_contrast < 10:
            shadows = "soft"
        elif shadow_contrast < 20:
            shadows = "medium"
        else:
            shadows = "hard"

        # Highlight analysis
        highlight_threshold = np.percentile(l_channel, 95)
        highlight_pixels = l_channel > highlight_threshold
        highlight_ratio = np.sum(highlight_pixels) / l_channel.size

        if highlight_ratio > 0.1:
            highlights = "blown"
        elif highlight_ratio < 0.01:
            highlights = "subdued"
        else:
            highlights = "balanced"

        return shadows, highlights

    def _determine_lighting_mood(self, l_channel: np.ndarray, contrast: str) -> str:
        """Determine mood based on lighting."""
        mean_brightness = np.mean(l_channel)

        if contrast == "high" and mean_brightness < 100:
            return "dramatic"
        elif contrast == "low" and mean_brightness > 150:
            return "soft"
        elif contrast == "high" and mean_brightness > 150:
            return "harsh"
        else:
            return "natural"

    def _guess_time_of_day(self, image: np.ndarray, l_channel: np.ndarray) -> str | None:
        """Guess time of day from image characteristics."""
        # Analyze color channels
        r_mean = np.mean(image[:, :, 0])
        np.mean(image[:, :, 1])
        b_mean = np.mean(image[:, :, 2])
        brightness = np.mean(l_channel)

        # Golden hour: warm tones, medium brightness
        if r_mean > b_mean * 1.3 and 80 < brightness < 180:
            return "golden_hour"

        # Blue hour: cool tones, low brightness
        elif b_mean > r_mean * 1.2 and brightness < 100:
            return "blue_hour"

        # Night: very low brightness
        elif brightness < 50:
            return "night"

        # Midday: high brightness, neutral colors
        elif brightness > 180 and abs(r_mean - b_mean) < 20:
            return "midday"

        return None

    def _build_style_vector(self, color: ColorPalette, comp: CompositionAnalysis,
                          texture: TextureAnalysis, lighting: LightingAnalysis) -> np.ndarray:
        """Build numerical style vector for similarity comparison."""
        vector = []

        # Color features (normalized RGB values of top 3 colors)
        for i in range(3):
            if i < len(color.dominant_colors):
                r, g, b = color.dominant_colors[i]
                vector.extend([r/255, g/255, b/255])
            else:
                vector.extend([0, 0, 0])

        # Color properties
        vector.append(1.0 if color.temperature == "warm" else (0.0 if color.temperature == "cool" else 0.5))
        vector.append(1.0 if color.saturation == "vibrant" else (0.0 if color.saturation == "monochrome" else 0.5))
        vector.append(1.0 if color.brightness == "bright" else (0.0 if color.brightness == "dark" else 0.5))

        # Composition features
        vector.append(comp.rule_of_thirds)
        vector.append(comp.symmetry_score)
        vector.append(1.0 if comp.balance_type == "centered" else 0.5)
        vector.append(comp.negative_space_ratio)
        vector.append(1.0 if comp.complexity == "complex" else (0.0 if comp.complexity == "simple" else 0.5))

        # Texture features
        vector.append(min(texture.texture_variance / 1000, 1.0))  # Normalize
        vector.append(1.0 if texture.overall_texture == "rough" else (0.0 if texture.overall_texture == "smooth" else 0.5))
        vector.append(1.0 if texture.grain_level != "none" else 0.0)

        # Lighting features
        vector.append(1.0 if lighting.contrast_level == "high" else (0.0 if lighting.contrast_level == "low" else 0.5))
        vector.append(1.0 if lighting.shadows == "hard" else (0.0 if lighting.shadows == "soft" else 0.5))
        vector.append(1.0 if lighting.mood_lighting == "dramatic" else 0.5)

        return np.array(vector)

    def _generate_style_tags(self, color: ColorPalette, comp: CompositionAnalysis,
                           texture: TextureAnalysis, lighting: LightingAnalysis) -> list[str]:
        """Generate descriptive style tags."""
        tags = []

        # Color tags
        tags.append(f"{color.temperature}_tones")
        tags.append(f"{color.saturation}_colors")
        tags.append(f"{color.brightness}_overall")
        if color.harmony_type != "mixed":
            tags.append(f"{color.harmony_type}_harmony")

        # Add dominant color
        if color.color_names:
            tags.append(f"{color.color_names[0]}_dominant")

        # Composition tags
        if comp.rule_of_thirds > 0.7:
            tags.append("rule_of_thirds")
        if comp.symmetry_score > 0.8:
            tags.append("symmetrical")
        tags.append(f"{comp.complexity}_composition")
        if comp.negative_space_ratio > 0.5:
            tags.append("minimalist")

        # Texture tags
        tags.append(f"{texture.overall_texture}_texture")
        if texture.grain_level != "none":
            tags.append(f"{texture.grain_level}_grain")
        tags.append(f"{texture.detail_density}_detail")

        # Lighting tags
        tags.append(f"{lighting.contrast_level}_contrast")
        tags.append(f"{lighting.mood_lighting}_lighting")
        if lighting.time_of_day:
            tags.append(lighting.time_of_day)

        return tags
