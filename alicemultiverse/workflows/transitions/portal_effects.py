"""
Portal effect detection for creative transitions.

Portal effects use shapes (circles, rectangles, doorways) as
transition points between shots, creating a "through the looking glass" effect.
"""

import json

# ImagePath type removed - using str instead
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Portal:
    """Represents a portal shape in an image."""
    shape_type: str  # "circle", "rectangle", "arch", "irregular"
    center: tuple[float, float]  # Normalized position (0-1)
    size: tuple[float, float]  # Normalized width, height
    confidence: float  # Detection confidence
    darkness_ratio: float  # How dark/empty the portal area is
    edge_strength: float  # How well-defined the edges are

    @property
    def area(self) -> float:
        """Calculate normalized area of portal."""
        if self.shape_type == "circle":
            return np.pi * (self.size[0] / 2) * (self.size[1] / 2)
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - return self.size[0] * self.size[1]

    @property
    def quality_score(self) -> float:
        """Overall quality score for portal use."""
        # Good portals are well-defined, reasonably sized, and somewhat dark
        size_score = min(self.area * 4, 1.0)  # Prefer 25% of image
        darkness_score = self.darkness_ratio
        edge_score = self.edge_strength

        return (size_score * 0.3 + darkness_score * 0.4 +
                edge_score * 0.3) * self.confidence


@dataclass
class PortalMatch:
    """Represents a matched portal pair for transition."""
    portal1: Portal
    portal2: Portal
    alignment_score: float  # How well portals align
    size_compatibility: float  # How similar in size
    transition_type: str  # "zoom_through", "cross_fade", "spiral"

    @property
    def overall_score(self) -> float:
        """Calculate overall match quality."""
        return (
            self.portal1.quality_score * 0.3 +
            self.portal2.quality_score * 0.3 +
            self.alignment_score * 0.2 +
            self.size_compatibility * 0.2
        )


@dataclass
class PortalEffectAnalysis:
    """Complete portal effect analysis between shots."""
    portals_shot1: list[Portal]
    portals_shot2: list[Portal]
    best_match: PortalMatch | None
    all_matches: list[PortalMatch]
    recommended_effect: str
    mask_data: np.ndarray | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "shot1_portals": [
                {
                    "type": p.shape_type,
                    "center": p.center,
                    "size": p.size,
                    "quality": p.quality_score
                }
                for p in self.portals_shot1
            ],
            "shot2_portals": [
                {
                    "type": p.shape_type,
                    "center": p.center,
                    "size": p.size,
                    "quality": p.quality_score
                }
                for p in self.portals_shot2
            ],
            "best_match": {
                "portal1_index": self.portals_shot1.index(self.best_match.portal1),
                "portal2_index": self.portals_shot2.index(self.best_match.portal2),
                "score": self.best_match.overall_score,
                "transition": self.best_match.transition_type
            } if self.best_match else None,
            "recommended_effect": self.recommended_effect,
            "total_matches": len(self.all_matches)
        }


class PortalDetector:
    """Detects portal shapes suitable for transitions."""

    def __init__(self):
        """Initialize portal detector."""
        self.min_portal_size = 0.05  # 5% of image
        self.max_portal_size = 0.5   # 50% of image
        self.darkness_threshold = 0.3
        self.edge_threshold = 100

    def detect_portals(self, image_path: str) -> list[Portal]:
        """
        Detect portal shapes in an image.

        Args:
            image_path: Path to image

        Returns:
            List of detected portals
        """
        img = cv2.imread(str(image_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = img.shape[:2]

        portals = []

        # Detect circles
        circles = self._detect_circular_portals(gray, img_rgb)
        portals.extend(circles)

        # Detect rectangles/doorways
        rectangles = self._detect_rectangular_portals(gray, img_rgb)
        portals.extend(rectangles)

        # Detect arches
        arches = self._detect_arch_portals(gray, img_rgb)
        portals.extend(arches)

        # Sort by quality score
        portals.sort(key=lambda p: p.quality_score, reverse=True)

        return portals[:5]  # Return top 5 portals

    # TODO: Review unreachable code - def _detect_circular_portals(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - gray: np.ndarray,
    # TODO: Review unreachable code - img: np.ndarray
    # TODO: Review unreachable code - ) -> list[Portal]:
    # TODO: Review unreachable code - """Detect circular portal shapes."""
    # TODO: Review unreachable code - h, w = gray.shape
    # TODO: Review unreachable code - portals = []

    # TODO: Review unreachable code - # Apply blur to reduce noise
    # TODO: Review unreachable code - blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    # TODO: Review unreachable code - # Detect circles using HoughCircles
    # TODO: Review unreachable code - circles = cv2.HoughCircles(
    # TODO: Review unreachable code - blurred,
    # TODO: Review unreachable code - cv2.HOUGH_GRADIENT,
    # TODO: Review unreachable code - dp=1,
    # TODO: Review unreachable code - minDist=min(h, w) // 8,
    # TODO: Review unreachable code - param1=50,
    # TODO: Review unreachable code - param2=30,
    # TODO: Review unreachable code - minRadius=int(min(h, w) * 0.05),
    # TODO: Review unreachable code - maxRadius=int(min(h, w) * 0.4)
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if circles is not None:
    # TODO: Review unreachable code - circles = np.uint16(np.around(circles))

    # TODO: Review unreachable code - for circle in circles[0]:
    # TODO: Review unreachable code - x, y, r = circle

    # TODO: Review unreachable code - # Check if area is relatively dark
    # TODO: Review unreachable code - mask = np.zeros(gray.shape, np.uint8)
    # TODO: Review unreachable code - cv2.circle(mask, (x, y), r, 255, -1)
    # TODO: Review unreachable code - mean_val = cv2.mean(gray, mask=mask)[0] / 255.0

    # TODO: Review unreachable code - # Check edge strength
    # TODO: Review unreachable code - edges = cv2.Canny(blurred, 50, 150)
    # TODO: Review unreachable code - edge_mask = cv2.circle(mask.copy(), (x, y), r, 255, 3)
    # TODO: Review unreachable code - edge_strength = np.sum(edges & edge_mask) / (2 * np.pi * r) / 255.0

    # TODO: Review unreachable code - if mean_val < self.darkness_threshold or edge_strength > 0.3:
    # TODO: Review unreachable code - portal = Portal(
    # TODO: Review unreachable code - shape_type="circle",
    # TODO: Review unreachable code - center=(x / w, y / h),
    # TODO: Review unreachable code - size=(2 * r / w, 2 * r / h),
    # TODO: Review unreachable code - confidence=0.9,
    # TODO: Review unreachable code - darkness_ratio=1.0 - mean_val,
    # TODO: Review unreachable code - edge_strength=min(edge_strength * 2, 1.0)
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - portals.append(portal)

    # TODO: Review unreachable code - return portals

    # TODO: Review unreachable code - def _detect_rectangular_portals(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - gray: np.ndarray,
    # TODO: Review unreachable code - img: np.ndarray
    # TODO: Review unreachable code - ) -> list[Portal]:
    # TODO: Review unreachable code - """Detect rectangular portal shapes (doors, windows, screens)."""
    # TODO: Review unreachable code - h, w = gray.shape
    # TODO: Review unreachable code - portals = []

    # TODO: Review unreachable code - # Edge detection
    # TODO: Review unreachable code - edges = cv2.Canny(gray, 50, 150)

    # TODO: Review unreachable code - # Find contours
    # TODO: Review unreachable code - contours, _ = cv2.findContours(
    # TODO: Review unreachable code - edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - for contour in contours:
    # TODO: Review unreachable code - # Approximate contour to polygon
    # TODO: Review unreachable code - perimeter = cv2.arcLength(contour, True)
    # TODO: Review unreachable code - approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)

    # TODO: Review unreachable code - # Check if it's a rectangle (4 vertices)
    # TODO: Review unreachable code - if len(approx) == 4:
    # TODO: Review unreachable code - x, y, w_rect, h_rect = cv2.boundingRect(approx)

    # TODO: Review unreachable code - # Check size constraints
    # TODO: Review unreachable code - area_ratio = (w_rect * h_rect) / (w * h)
    # TODO: Review unreachable code - if self.min_portal_size < area_ratio < self.max_portal_size:
    # TODO: Review unreachable code - # Check darkness
    # TODO: Review unreachable code - roi = gray[y:y+h_rect, x:x+w_rect]
    # TODO: Review unreachable code - mean_val = np.mean(roi) / 255.0

    # TODO: Review unreachable code - # Check if it's roughly rectangular (not too skewed)
    # TODO: Review unreachable code - aspect_ratio = w_rect / h_rect
    # TODO: Review unreachable code - if 0.3 < aspect_ratio < 3.0:
    # TODO: Review unreachable code - # Calculate edge strength
    # TODO: Review unreachable code - edge_roi = edges[y:y+h_rect, x:x+w_rect]
    # TODO: Review unreachable code - edge_density = np.sum(edge_roi > 0) / (w_rect * h_rect)

    # TODO: Review unreachable code - portal = Portal(
    # TODO: Review unreachable code - shape_type="rectangle",
    # TODO: Review unreachable code - center=((x + w_rect/2) / w, (y + h_rect/2) / h),
    # TODO: Review unreachable code - size=(w_rect / w, h_rect / h),
    # TODO: Review unreachable code - confidence=0.8,
    # TODO: Review unreachable code - darkness_ratio=1.0 - mean_val,
    # TODO: Review unreachable code - edge_strength=min(edge_density * 10, 1.0)
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if portal.quality_score > 0.3:
    # TODO: Review unreachable code - portals.append(portal)

    # TODO: Review unreachable code - return portals

    # TODO: Review unreachable code - def _detect_arch_portals(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - gray: np.ndarray,
    # TODO: Review unreachable code - img: np.ndarray
    # TODO: Review unreachable code - ) -> list[Portal]:
    # TODO: Review unreachable code - """Detect arch-shaped portals."""
    # TODO: Review unreachable code - h, w = gray.shape
    # TODO: Review unreachable code - portals = []

    # TODO: Review unreachable code - # Use ellipse detection for arches
    # TODO: Review unreachable code - edges = cv2.Canny(gray, 50, 150)
    # TODO: Review unreachable code - contours, _ = cv2.findContours(
    # TODO: Review unreachable code - edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - for contour in contours:
    # TODO: Review unreachable code - if len(contour) >= 5:  # Need at least 5 points for ellipse
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - ellipse = cv2.fitEllipse(contour)
    # TODO: Review unreachable code - (x, y), (w_ellipse, h_ellipse), angle = ellipse

    # TODO: Review unreachable code - # Check if it's arch-like (wider than tall, not too angled)
    # TODO: Review unreachable code - if (w_ellipse > h_ellipse and
    # TODO: Review unreachable code - abs(angle - 90) < 45 and
    # TODO: Review unreachable code - self.min_portal_size < (w_ellipse * h_ellipse) / (w * h) < self.max_portal_size):

    # TODO: Review unreachable code - # Create mask for darkness check
    # TODO: Review unreachable code - mask = np.zeros(gray.shape, np.uint8)
    # TODO: Review unreachable code - cv2.ellipse(mask, ellipse, 255, -1)
    # TODO: Review unreachable code - mean_val = cv2.mean(gray, mask=mask)[0] / 255.0

    # TODO: Review unreachable code - portal = Portal(
    # TODO: Review unreachable code - shape_type="arch",
    # TODO: Review unreachable code - center=(x / w, y / h),
    # TODO: Review unreachable code - size=(w_ellipse / w, h_ellipse / h),
    # TODO: Review unreachable code - confidence=0.7,
    # TODO: Review unreachable code - darkness_ratio=1.0 - mean_val,
    # TODO: Review unreachable code - edge_strength=0.6  # Moderate edge strength for arches
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if portal.quality_score > 0.3:
    # TODO: Review unreachable code - portals.append(portal)

    # TODO: Review unreachable code - except cv2.error:
    # TODO: Review unreachable code - # Skip if ellipse fitting fails
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - return portals


class PortalEffectGenerator:
    """Generates portal transition effects between shots."""

    def __init__(self):
        """Initialize effect generator."""
        self.detector = PortalDetector()

    def analyze_portal_transition(
        self,
        image1_path: str,
        image2_path: str
    ) -> PortalEffectAnalysis:
        """
        Analyze potential portal transition between images.

        Args:
            image1_path: Path to first image
            image2_path: Path to second image

        Returns:
            PortalEffectAnalysis with matches and recommendations
        """
        # Detect portals in both images
        portals1 = self.detector.detect_portals(image1_path)
        portals2 = self.detector.detect_portals(image2_path)

        # Match portals
        matches = self._match_portals(portals1, portals2)

        # Find best match
        best_match = max(matches, key=lambda m: m.overall_score) if matches else None

        # Generate mask for best match
        mask_data = None
        if best_match:
            mask_data = self._generate_transition_mask(
                best_match.portal1,
                cv2.imread(str(image1_path)).shape[:2]
            )

        # Determine recommended effect
        effect = self._recommend_effect(best_match) if best_match else "cross_fade"

        return PortalEffectAnalysis(
            portals_shot1=portals1,
            portals_shot2=portals2,
            best_match=best_match,
            all_matches=matches,
            recommended_effect=effect,
            mask_data=mask_data
        )

    def _match_portals(
        self,
        portals1: list[Portal],
        portals2: list[Portal]
    ) -> list[PortalMatch]:
        """Match portals between two shots."""
        matches = []

        for p1 in portals1:
            for p2 in portals2:
                # Calculate alignment score
                center_dist = np.sqrt(
                    (p1.center[0] - p2.center[0])**2 +
                    (p1.center[1] - p2.center[1])**2
                )
                alignment = 1.0 - min(center_dist, 1.0)

                # Calculate size compatibility
                size_ratio = min(p1.area, p2.area) / max(p1.area, p2.area)

                # Determine transition type based on portals
                if p1.shape_type == "circle" and p2.shape_type == "circle":
                    transition = "zoom_through"
                elif alignment > 0.8:
                    transition = "cross_fade"
                else:
                    transition = "spiral"

                match = PortalMatch(
                    portal1=p1,
                    portal2=p2,
                    alignment_score=alignment,
                    size_compatibility=size_ratio,
                    transition_type=transition
                )

                if match.overall_score > 0.5:
                    matches.append(match)

        return sorted(matches, key=lambda m: m.overall_score, reverse=True)

    # TODO: Review unreachable code - def _generate_transition_mask(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - portal: Portal,
    # TODO: Review unreachable code - image_shape: tuple[int, int]
    # TODO: Review unreachable code - ) -> np.ndarray:
    # TODO: Review unreachable code - """Generate mask for portal transition."""
    # TODO: Review unreachable code - h, w = image_shape
    # TODO: Review unreachable code - mask = np.zeros((h, w), dtype=np.float32)

    # TODO: Review unreachable code - center_x = int(portal.center[0] * w)
    # TODO: Review unreachable code - center_y = int(portal.center[1] * h)

    # TODO: Review unreachable code - if portal.shape_type == "circle":
    # TODO: Review unreachable code - radius = int(portal.size[0] * w / 2)
    # TODO: Review unreachable code - cv2.circle(mask, (center_x, center_y), radius, 1.0, -1)
    # TODO: Review unreachable code - # Add gradient fade
    # TODO: Review unreachable code - for r in range(radius, int(radius * 1.3)):
    # TODO: Review unreachable code - alpha = 1.0 - (r - radius) / (radius * 0.3)
    # TODO: Review unreachable code - cv2.circle(mask, (center_x, center_y), r, alpha, 1)

    # TODO: Review unreachable code - elif portal.shape_type == "rectangle":
    # TODO: Review unreachable code - width = int(portal.size[0] * w)
    # TODO: Review unreachable code - height = int(portal.size[1] * h)
    # TODO: Review unreachable code - x1 = center_x - width // 2
    # TODO: Review unreachable code - y1 = center_y - height // 2
    # TODO: Review unreachable code - x2 = x1 + width
    # TODO: Review unreachable code - y2 = y1 + height
    # TODO: Review unreachable code - cv2.rectangle(mask, (x1, y1), (x2, y2), 1.0, -1)

    # TODO: Review unreachable code - elif portal.shape_type == "arch":
    # TODO: Review unreachable code - # Approximate arch with ellipse
    # TODO: Review unreachable code - width = int(portal.size[0] * w)
    # TODO: Review unreachable code - height = int(portal.size[1] * h)
    # TODO: Review unreachable code - cv2.ellipse(
    # TODO: Review unreachable code - mask,
    # TODO: Review unreachable code - (center_x, center_y),
    # TODO: Review unreachable code - (width // 2, height // 2),
    # TODO: Review unreachable code - 0, 180, 360, 1.0, -1
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Apply Gaussian blur for smooth edges
    # TODO: Review unreachable code - mask = cv2.GaussianBlur(mask, (21, 21), 10)

    # TODO: Review unreachable code - return mask

    # TODO: Review unreachable code - def _recommend_effect(self, match: PortalMatch) -> str:
    # TODO: Review unreachable code - """Recommend transition effect based on portal match."""
    # TODO: Review unreachable code - if match.alignment_score > 0.9 and match.size_compatibility > 0.8:
    # TODO: Review unreachable code - return "direct_portal"  # Perfect alignment
    # TODO: Review unreachable code - elif match.portal1.shape_type == "circle" and match.portal2.shape_type == "circle":
    # TODO: Review unreachable code - return "zoom_spiral"  # Circular zoom with rotation
    # TODO: Review unreachable code - elif match.transition_type == "zoom_through":
    # TODO: Review unreachable code - return "zoom_blur"  # Fast zoom with motion blur
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - return "portal_wipe"  # Masked wipe transition


def export_portal_effect(
    analysis: PortalEffectAnalysis,
    output_path: Path,
    format: str = "after_effects"
) -> None:
    """Export portal effect data for video editors."""

    if format == "after_effects":
        # Export as After Effects script
        with open(output_path, 'w') as f:
            f.write("// Portal Effect Transition\n")
            f.write("// Generated by AliceMultiverse\n\n")

            if analysis.best_match:
                p1 = analysis.best_match.portal1
                p2 = analysis.best_match.portal2

                f.write("// Portal 1 (Source)\n")
                f.write(f"var portal1_center = [{p1.center[0]}, {p1.center[1]}];\n")
                f.write(f"var portal1_size = [{p1.size[0]}, {p1.size[1]}];\n")
                f.write(f"var portal1_type = '{p1.shape_type}';\n\n")

                f.write("// Portal 2 (Destination)\n")
                f.write(f"var portal2_center = [{p2.center[0]}, {p2.center[1]}];\n")
                f.write(f"var portal2_size = [{p2.size[0]}, {p2.size[1]}];\n")
                f.write(f"var portal2_type = '{p2.shape_type}';\n\n")

                f.write("// Transition parameters\n")
                f.write(f"var effect_type = '{analysis.recommended_effect}';\n")
                f.write("var duration = 1.0; // seconds\n\n")

                f.write("// Apply effect\n")
                f.write("// 1. Create mask from portal1\n")
                f.write("// 2. Animate scale and position\n")
                f.write("// 3. Transition to portal2\n")

    elif format == "json":
        # Export as JSON for custom implementations
        with open(output_path, 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)
