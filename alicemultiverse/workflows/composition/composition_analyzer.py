"""Visual composition analyzer for individual frames and overall timeline."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CompositionMetrics:
    """Metrics for visual composition analysis."""
    rule_of_thirds_score: float = 0.0  # 0-1
    golden_ratio_score: float = 0.0  # 0-1
    symmetry_score: float = 0.0  # 0-1
    balance_score: float = 0.0  # 0-1
    leading_lines_score: float = 0.0  # 0-1
    depth_score: float = 0.0  # 0-1
    focus_clarity: float = 0.0  # 0-1
    visual_weight_distribution: dict[str, float] = field(default_factory=dict)
    interest_points: list[tuple[float, float]] = field(default_factory=list)
    composition_type: str = "unknown"


class CompositionAnalyzer:
    """Analyze visual composition of images and video frames."""

    # Grid divisions for analysis
    THIRDS_GRID = 3
    GOLDEN_RATIO = 1.618

    # Composition types
    COMPOSITION_TYPES = [
        "centered",
        "rule_of_thirds",
        "golden_ratio",
        "diagonal",
        "symmetrical",
        "asymmetrical",
        "radial",
        "frame_within_frame",
    ]

    def __init__(self):
        """Initialize the composition analyzer."""
        self.cache = {}

    def analyze_image_composition(
        self,
        image_path: Path,
        return_visualization: bool = False,
    ) -> CompositionMetrics:
        """Analyze composition of a single image.

        Args:
            image_path: Path to image
            return_visualization: Whether to return visualization

        Returns:
            Composition metrics
        """
        # Check cache
        cache_key = str(image_path)
        if cache_key in self.cache and not return_visualization:
            return self.cache[cache_key]

        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return CompositionMetrics()

        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Analyze composition
        metrics = CompositionMetrics()

        # Rule of thirds analysis
        metrics.rule_of_thirds_score = self._analyze_rule_of_thirds(img_rgb)

        # Golden ratio analysis
        metrics.golden_ratio_score = self._analyze_golden_ratio(img_rgb)

        # Symmetry analysis
        metrics.symmetry_score = self._analyze_symmetry(img_rgb)

        # Balance analysis
        metrics.balance_score = self._analyze_balance(img_rgb)

        # Leading lines detection
        metrics.leading_lines_score = self._detect_leading_lines(img_rgb)

        # Depth perception
        metrics.depth_score = self._analyze_depth(img_rgb)

        # Focus clarity (using Laplacian variance)
        metrics.focus_clarity = self._analyze_focus_clarity(img_rgb)

        # Visual weight distribution
        metrics.visual_weight_distribution = self._analyze_visual_weight(img_rgb)

        # Interest points detection
        metrics.interest_points = self._detect_interest_points(img_rgb)

        # Determine composition type
        metrics.composition_type = self._determine_composition_type(metrics)

        # Cache result
        self.cache[cache_key] = metrics

        return metrics

    def _analyze_rule_of_thirds(self, img: np.ndarray) -> float:
        """Analyze adherence to rule of thirds."""
        h, w = img.shape[:2]

        # Define thirds lines
        v_third1 = w // 3
        v_third2 = 2 * w // 3
        h_third1 = h // 3
        h_third2 = 2 * h // 3

        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Detect edges
        edges = cv2.Canny(gray, 50, 150)

        # Calculate edge density near thirds lines
        line_width = max(10, min(w, h) // 50)  # Adaptive line width

        # Vertical thirds
        v1_edges = edges[:, max(0, v_third1-line_width):min(w, v_third1+line_width)]
        v2_edges = edges[:, max(0, v_third2-line_width):min(w, v_third2+line_width)]

        # Horizontal thirds
        h1_edges = edges[max(0, h_third1-line_width):min(h, h_third1+line_width), :]
        h2_edges = edges[max(0, h_third2-line_width):min(h, h_third2+line_width), :]

        # Calculate scores
        v1_score = np.sum(v1_edges > 0) / v1_edges.size if v1_edges.size > 0 else 0
        v2_score = np.sum(v2_edges > 0) / v2_edges.size if v2_edges.size > 0 else 0
        h1_score = np.sum(h1_edges > 0) / h1_edges.size if h1_edges.size > 0 else 0
        h2_score = np.sum(h2_edges > 0) / h2_edges.size if h2_edges.size > 0 else 0

        # Check intersection points (power points)
        intersection_score = 0
        power_points = [
            (v_third1, h_third1),
            (v_third1, h_third2),
            (v_third2, h_third1),
            (v_third2, h_third2),
        ]

        # Use feature detection for interest points
        detector = cv2.goodFeaturesToTrack(
            gray, maxCorners=100, qualityLevel=0.01, minDistance=30
        )

        if detector is not None:
            for point in power_points:
                # Check if any detected feature is near this power point
                for feature in detector:
                    fx, fy = feature[0]
                    dist = np.sqrt((fx - point[0])**2 + (fy - point[1])**2)
                    if dist < line_width * 2:
                        intersection_score += 0.25
                        break

        # Combine scores
        line_score = (v1_score + v2_score + h1_score + h2_score) / 4
        total_score = line_score * 0.6 + intersection_score * 0.4

        return min(1.0, total_score * 2)  # Scale up as scores tend to be low

    def _analyze_golden_ratio(self, img: np.ndarray) -> float:
        """Analyze adherence to golden ratio."""
        h, w = img.shape[:2]

        # Define golden ratio lines
        golden_v1 = int(w / self.GOLDEN_RATIO)
        golden_v2 = w - golden_v1
        golden_h1 = int(h / self.GOLDEN_RATIO)
        golden_h2 = h - golden_h1

        # Similar analysis to rule of thirds
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        line_width = max(10, min(w, h) // 50)

        # Check golden lines
        scores = []
        for line_pos in [golden_v1, golden_v2]:
            line_edges = edges[:, max(0, line_pos-line_width):min(w, line_pos+line_width)]
            if line_edges.size > 0:
                scores.append(np.sum(line_edges > 0) / line_edges.size)

        for line_pos in [golden_h1, golden_h2]:
            line_edges = edges[max(0, line_pos-line_width):min(h, line_pos+line_width), :]
            if line_edges.size > 0:
                scores.append(np.sum(line_edges > 0) / line_edges.size)

        return min(1.0, np.mean(scores) * 2) if scores else 0.0

    def _analyze_symmetry(self, img: np.ndarray) -> float:
        """Analyze image symmetry."""
        h, w = img.shape[:2]

        # Check vertical symmetry
        left_half = img[:, :w//2]
        right_half = img[:, w//2:]
        right_flipped = cv2.flip(right_half, 1)

        # Resize if needed
        if left_half.shape != right_flipped.shape:
            min_w = min(left_half.shape[1], right_flipped.shape[1])
            left_half = left_half[:, :min_w]
            right_flipped = right_flipped[:, :min_w]

        # Calculate similarity
        v_symmetry = 1 - np.mean(np.abs(left_half - right_flipped)) / 255

        # Check horizontal symmetry
        top_half = img[:h//2, :]
        bottom_half = img[h//2:, :]
        bottom_flipped = cv2.flip(bottom_half, 0)

        if top_half.shape != bottom_flipped.shape:
            min_h = min(top_half.shape[0], bottom_flipped.shape[0])
            top_half = top_half[:min_h, :]
            bottom_flipped = bottom_flipped[:min_h, :]

        h_symmetry = 1 - np.mean(np.abs(top_half - bottom_flipped)) / 255

        # Return the higher symmetry score
        return max(v_symmetry, h_symmetry)

    def _analyze_balance(self, img: np.ndarray) -> float:
        """Analyze visual balance of the image."""
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Calculate visual weight using brightness
        # Divide image into quadrants
        quadrants = [
            gray[:h//2, :w//2],  # Top-left
            gray[:h//2, w//2:],  # Top-right
            gray[h//2:, :w//2],  # Bottom-left
            gray[h//2:, w//2:],  # Bottom-right
        ]

        # Calculate average brightness for each quadrant
        weights = [np.mean(q) for q in quadrants]

        # Check diagonal balance
        diag1_balance = 1 - abs(weights[0] + weights[3] - weights[1] - weights[2]) / (sum(weights) + 1e-6)
        diag2_balance = 1 - abs(weights[0] + weights[1] - weights[2] - weights[3]) / (sum(weights) + 1e-6)

        # Check horizontal and vertical balance
        h_balance = 1 - abs(weights[0] + weights[1] - weights[2] - weights[3]) / (sum(weights) + 1e-6)
        v_balance = 1 - abs(weights[0] + weights[2] - weights[1] - weights[3]) / (sum(weights) + 1e-6)

        # Combine balance scores
        balance_score = (diag1_balance + diag2_balance + h_balance + v_balance) / 4

        return max(0, min(1, balance_score))

    def _detect_leading_lines(self, img: np.ndarray) -> float:
        """Detect leading lines in the image."""
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=50,
            minLineLength=min(img.shape[:2]) // 4,
            maxLineGap=20
        )

        if lines is None:
            return 0.0

        # Analyze line directions
        h, w = img.shape[:2]
        center = (w // 2, h // 2)

        leading_score = 0
        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Calculate if line points toward center
            line_vec = np.array([x2 - x1, y2 - y1])
            to_center1 = np.array([center[0] - x1, center[1] - y1])
            to_center2 = np.array([center[0] - x2, center[1] - y2])

            # Check if line points toward center
            dot1 = np.dot(line_vec, to_center1)
            dot2 = np.dot(-line_vec, to_center2)

            if dot1 > 0 or dot2 > 0:
                # Line leads toward center
                line_length = np.sqrt(line_vec[0]**2 + line_vec[1]**2)
                leading_score += line_length / (w + h)

        # Normalize score
        return min(1.0, leading_score / 5)  # Expect ~5 good leading lines max

    def _analyze_depth(self, img: np.ndarray) -> float:
        """Analyze depth perception in the image."""
        h, w = img.shape[:2]

        # Simple depth analysis based on:
        # 1. Size gradient (objects get smaller with distance)
        # 2. Blur gradient (distant objects are less sharp)
        # 3. Color/contrast gradient

        # Divide image into horizontal bands
        bands = 5
        band_height = h // bands

        sharpness_scores = []
        brightness_scores = []

        for i in range(bands):
            band = img[i*band_height:(i+1)*band_height, :]

            # Calculate sharpness using Laplacian
            gray_band = cv2.cvtColor(band, cv2.COLOR_RGB2GRAY)
            laplacian = cv2.Laplacian(gray_band, cv2.CV_64F)
            sharpness = np.var(laplacian)
            sharpness_scores.append(sharpness)

            # Calculate average brightness
            brightness = np.mean(gray_band)
            brightness_scores.append(brightness)

        # Check if there's a gradient (indicating depth)
        sharpness_gradient = 0
        brightness_gradient = 0

        for i in range(1, bands):
            # Expect sharpness to decrease with height (distance)
            if sharpness_scores[i] < sharpness_scores[i-1]:
                sharpness_gradient += 1

            # Expect brightness to change consistently
            if abs(brightness_scores[i] - brightness_scores[i-1]) > 10:
                brightness_gradient += 1

        depth_score = (sharpness_gradient + brightness_gradient) / (2 * (bands - 1))

        return depth_score

    def _analyze_focus_clarity(self, img: np.ndarray) -> float:
        """Analyze focus clarity of the image."""
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Calculate Laplacian variance (measure of sharpness)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = np.var(laplacian)

        # Normalize (these values are empirical)
        # Sharp images typically have variance > 100
        # Blurry images typically have variance < 50
        normalized = min(1.0, variance / 200)

        return normalized

    def _analyze_visual_weight(self, img: np.ndarray) -> dict[str, float]:
        """Analyze distribution of visual weight."""
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Divide into 9 regions (3x3 grid)
        regions = {}
        region_names = [
            "top_left", "top_center", "top_right",
            "mid_left", "center", "mid_right",
            "bot_left", "bot_center", "bot_right"
        ]

        idx = 0
        for i in range(3):
            for j in range(3):
                y1 = i * h // 3
                y2 = (i + 1) * h // 3
                x1 = j * w // 3
                x2 = (j + 1) * w // 3

                region = gray[y1:y2, x1:x2]

                # Visual weight based on brightness and edge density
                brightness = np.mean(region)
                edges = cv2.Canny(region, 50, 150)
                edge_density = np.sum(edges > 0) / edges.size

                # Combine brightness and edge density
                weight = (brightness / 255) * 0.7 + edge_density * 0.3
                regions[region_names[idx]] = float(weight)
                idx += 1

        return regions

    def _detect_interest_points(self, img: np.ndarray) -> list[tuple[float, float]]:
        """Detect points of interest in the image."""
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        # Detect corners/features
        corners = cv2.goodFeaturesToTrack(
            gray,
            maxCorners=10,
            qualityLevel=0.01,
            minDistance=min(w, h) // 20
        )

        interest_points = []
        if corners is not None:
            for corner in corners:
                x, y = corner[0]
                # Normalize coordinates
                interest_points.append((float(x / w), float(y / h)))

        # Also detect high contrast regions
        # Use Sobel to find gradients
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

        # Find local maxima
        kernel_size = min(w, h) // 20
        kernel = np.ones((kernel_size, kernel_size)) / (kernel_size**2)
        local_mean = cv2.filter2D(gradient_magnitude, -1, kernel)

        # Points where gradient is significantly higher than local mean
        high_contrast = gradient_magnitude > local_mean * 2

        # Sample some high contrast points
        y_coords, x_coords = np.where(high_contrast)
        if len(y_coords) > 0:
            # Random sample to avoid too many points
            sample_size = min(5, len(y_coords))
            indices = np.random.choice(len(y_coords), sample_size, replace=False)

            for idx in indices:
                x, y = x_coords[idx], y_coords[idx]
                norm_point = (float(x / w), float(y / h))
                # Avoid duplicates
                if not any(abs(p[0] - norm_point[0]) < 0.05 and abs(p[1] - norm_point[1]) < 0.05
                          for p in interest_points):
                    interest_points.append(norm_point)

        return interest_points[:15]  # Limit to 15 points

    def _determine_composition_type(self, metrics: CompositionMetrics) -> str:
        """Determine the primary composition type based on metrics."""
        scores = {
            "rule_of_thirds": metrics.rule_of_thirds_score,
            "golden_ratio": metrics.golden_ratio_score,
            "symmetrical": metrics.symmetry_score,
        }

        # Check for centered composition
        if "center" in metrics.visual_weight_distribution:
            center_weight = metrics.visual_weight_distribution["center"]
            if center_weight > 0.4:  # Strong center weight
                scores["centered"] = center_weight

        # Check for diagonal composition
        if metrics.leading_lines_score > 0.5:
            scores["diagonal"] = metrics.leading_lines_score

        # Check for asymmetrical balance
        if metrics.balance_score > 0.7 and metrics.symmetry_score < 0.3:
            scores["asymmetrical"] = metrics.balance_score

        # Find the highest scoring type
        if scores:
            composition_type = max(scores.items(), key=lambda x: x[1])[0]
            if scores[composition_type] < 0.3:  # No strong composition
                return "unstructured"
            return composition_type

        return "unknown"

    def suggest_composition_improvements(
        self,
        metrics: CompositionMetrics,
    ) -> list[str]:
        """Suggest improvements based on composition analysis."""
        suggestions = []

        # Check overall composition strength
        overall_score = (
            metrics.rule_of_thirds_score * 0.3 +
            metrics.balance_score * 0.3 +
            metrics.focus_clarity * 0.2 +
            metrics.leading_lines_score * 0.1 +
            metrics.depth_score * 0.1
        )

        if overall_score < 0.3:
            suggestions.append("Consider stronger compositional structure")

        # Specific suggestions
        if metrics.rule_of_thirds_score < 0.3:
            suggestions.append("Try placing key elements along thirds lines or intersections")

        if metrics.balance_score < 0.4:
            suggestions.append("Image appears unbalanced - redistribute visual weight")

        if metrics.focus_clarity < 0.3:
            suggestions.append("Image lacks sharp focus - ensure main subject is clear")

        if metrics.leading_lines_score < 0.2:
            suggestions.append("Add leading lines to guide viewer's eye")

        if metrics.depth_score < 0.3:
            suggestions.append("Consider adding depth cues (size variation, overlap, blur)")

        # Check visual weight distribution
        if metrics.visual_weight_distribution:
            weights = list(metrics.visual_weight_distribution.values())
            if max(weights) > 0.5:
                heavy_region = max(
                    metrics.visual_weight_distribution.items(),
                    key=lambda x: x[1]
                )[0]
                suggestions.append(f"Heavy visual weight in {heavy_region} - consider rebalancing")

        return suggestions
