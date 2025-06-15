"""
Portal effect detection for creative transitions.

Portal effects use shapes (circles, rectangles, doorways) as
transition points between shots, creating a "through the looking glass" effect.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

# ImagePath type removed - using str instead
from ..core.logging import get_logger

logger = get_logger(__name__)


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
        else:
            return self.size[0] * self.size[1]

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

    def _detect_circular_portals(
        self,
        gray: np.ndarray,
        img: np.ndarray
    ) -> list[Portal]:
        """Detect circular portal shapes."""
        h, w = gray.shape
        portals = []

        # Apply blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Detect circles using HoughCircles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=min(h, w) // 8,
            param1=50,
            param2=30,
            minRadius=int(min(h, w) * 0.05),
            maxRadius=int(min(h, w) * 0.4)
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))

            for circle in circles[0]:
                x, y, r = circle

                # Check if area is relatively dark
                mask = np.zeros(gray.shape, np.uint8)
                cv2.circle(mask, (x, y), r, 255, -1)
                mean_val = cv2.mean(gray, mask=mask)[0] / 255.0

                # Check edge strength
                edges = cv2.Canny(blurred, 50, 150)
                edge_mask = cv2.circle(mask.copy(), (x, y), r, 255, 3)
                edge_strength = np.sum(edges & edge_mask) / (2 * np.pi * r) / 255.0

                if mean_val < self.darkness_threshold or edge_strength > 0.3:
                    portal = Portal(
                        shape_type="circle",
                        center=(x / w, y / h),
                        size=(2 * r / w, 2 * r / h),
                        confidence=0.9,
                        darkness_ratio=1.0 - mean_val,
                        edge_strength=min(edge_strength * 2, 1.0)
                    )
                    portals.append(portal)

        return portals

    def _detect_rectangular_portals(
        self,
        gray: np.ndarray,
        img: np.ndarray
    ) -> list[Portal]:
        """Detect rectangular portal shapes (doors, windows, screens)."""
        h, w = gray.shape
        portals = []

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            # Approximate contour to polygon
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)

            # Check if it's a rectangle (4 vertices)
            if len(approx) == 4:
                x, y, w_rect, h_rect = cv2.boundingRect(approx)

                # Check size constraints
                area_ratio = (w_rect * h_rect) / (w * h)
                if self.min_portal_size < area_ratio < self.max_portal_size:
                    # Check darkness
                    roi = gray[y:y+h_rect, x:x+w_rect]
                    mean_val = np.mean(roi) / 255.0

                    # Check if it's roughly rectangular (not too skewed)
                    aspect_ratio = w_rect / h_rect
                    if 0.3 < aspect_ratio < 3.0:
                        # Calculate edge strength
                        edge_roi = edges[y:y+h_rect, x:x+w_rect]
                        edge_density = np.sum(edge_roi > 0) / (w_rect * h_rect)

                        portal = Portal(
                            shape_type="rectangle",
                            center=((x + w_rect/2) / w, (y + h_rect/2) / h),
                            size=(w_rect / w, h_rect / h),
                            confidence=0.8,
                            darkness_ratio=1.0 - mean_val,
                            edge_strength=min(edge_density * 10, 1.0)
                        )

                        if portal.quality_score > 0.3:
                            portals.append(portal)

        return portals

    def _detect_arch_portals(
        self,
        gray: np.ndarray,
        img: np.ndarray
    ) -> list[Portal]:
        """Detect arch-shaped portals."""
        h, w = gray.shape
        portals = []

        # Use ellipse detection for arches
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            if len(contour) >= 5:  # Need at least 5 points for ellipse
                try:
                    ellipse = cv2.fitEllipse(contour)
                    (x, y), (w_ellipse, h_ellipse), angle = ellipse

                    # Check if it's arch-like (wider than tall, not too angled)
                    if (w_ellipse > h_ellipse and
                        abs(angle - 90) < 45 and
                        self.min_portal_size < (w_ellipse * h_ellipse) / (w * h) < self.max_portal_size):

                        # Create mask for darkness check
                        mask = np.zeros(gray.shape, np.uint8)
                        cv2.ellipse(mask, ellipse, 255, -1)
                        mean_val = cv2.mean(gray, mask=mask)[0] / 255.0

                        portal = Portal(
                            shape_type="arch",
                            center=(x / w, y / h),
                            size=(w_ellipse / w, h_ellipse / h),
                            confidence=0.7,
                            darkness_ratio=1.0 - mean_val,
                            edge_strength=0.6  # Moderate edge strength for arches
                        )

                        if portal.quality_score > 0.3:
                            portals.append(portal)

                except cv2.error:
                    # Skip if ellipse fitting fails
                    continue

        return portals


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

    def _generate_transition_mask(
        self,
        portal: Portal,
        image_shape: tuple[int, int]
    ) -> np.ndarray:
        """Generate mask for portal transition."""
        h, w = image_shape
        mask = np.zeros((h, w), dtype=np.float32)

        center_x = int(portal.center[0] * w)
        center_y = int(portal.center[1] * h)

        if portal.shape_type == "circle":
            radius = int(portal.size[0] * w / 2)
            cv2.circle(mask, (center_x, center_y), radius, 1.0, -1)
            # Add gradient fade
            for r in range(radius, int(radius * 1.3)):
                alpha = 1.0 - (r - radius) / (radius * 0.3)
                cv2.circle(mask, (center_x, center_y), r, alpha, 1)

        elif portal.shape_type == "rectangle":
            width = int(portal.size[0] * w)
            height = int(portal.size[1] * h)
            x1 = center_x - width // 2
            y1 = center_y - height // 2
            x2 = x1 + width
            y2 = y1 + height
            cv2.rectangle(mask, (x1, y1), (x2, y2), 1.0, -1)

        elif portal.shape_type == "arch":
            # Approximate arch with ellipse
            width = int(portal.size[0] * w)
            height = int(portal.size[1] * h)
            cv2.ellipse(
                mask,
                (center_x, center_y),
                (width // 2, height // 2),
                0, 180, 360, 1.0, -1
            )

        # Apply Gaussian blur for smooth edges
        mask = cv2.GaussianBlur(mask, (21, 21), 10)

        return mask

    def _recommend_effect(self, match: PortalMatch) -> str:
        """Recommend transition effect based on portal match."""
        if match.alignment_score > 0.9 and match.size_compatibility > 0.8:
            return "direct_portal"  # Perfect alignment
        elif match.portal1.shape_type == "circle" and match.portal2.shape_type == "circle":
            return "zoom_spiral"  # Circular zoom with rotation
        elif match.transition_type == "zoom_through":
            return "zoom_blur"  # Fast zoom with motion blur
        else:
            return "portal_wipe"  # Masked wipe transition


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
