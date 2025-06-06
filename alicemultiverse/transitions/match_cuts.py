"""
Match cut detection and analysis for seamless transitions.

Match cuts are edits where two shots share similar:
- Movement patterns
- Object shapes
- Action continuity
- Visual composition
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import cv2
from PIL import Image
import json

from ..core.types import ImagePath
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MotionVector:
    """Represents motion in an image."""
    direction: Tuple[float, float]  # Normalized direction vector
    magnitude: float  # 0-1 strength
    center: Tuple[float, float]  # Normalized position (0-1)
    
    def similarity_to(self, other: 'MotionVector') -> float:
        """Calculate similarity to another motion vector."""
        # Direction similarity (dot product)
        dir_sim = abs(
            self.direction[0] * other.direction[0] + 
            self.direction[1] * other.direction[1]
        )
        
        # Magnitude similarity
        mag_sim = 1.0 - abs(self.magnitude - other.magnitude)
        
        # Position similarity
        pos_dist = np.sqrt(
            (self.center[0] - other.center[0])**2 + 
            (self.center[1] - other.center[1])**2
        )
        pos_sim = 1.0 - min(pos_dist, 1.0)
        
        # Weighted combination
        return 0.5 * dir_sim + 0.3 * mag_sim + 0.2 * pos_sim


@dataclass
class ShapeMatch:
    """Represents a matching shape between images."""
    shape_type: str  # "circle", "rectangle", "line", "curve"
    position1: Tuple[float, float]  # Normalized position in image 1
    position2: Tuple[float, float]  # Normalized position in image 2
    size1: float  # Relative size in image 1
    size2: float  # Relative size in image 2
    confidence: float  # 0-1 match confidence


@dataclass
class MatchCutAnalysis:
    """Results of match cut analysis between two shots."""
    motion_matches: List[Tuple[MotionVector, MotionVector]]
    shape_matches: List[ShapeMatch]
    action_continuity: float  # 0-1 score
    cut_point_suggestion: Optional[int]  # Frame number if applicable
    match_type: str  # "motion", "shape", "action", "composite"
    confidence: float  # Overall match confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "motion_matches": [
                {
                    "vector1": {
                        "direction": m1.direction,
                        "magnitude": m1.magnitude,
                        "center": m1.center
                    },
                    "vector2": {
                        "direction": m2.direction,
                        "magnitude": m2.magnitude,
                        "center": m2.center
                    },
                    "similarity": m1.similarity_to(m2)
                }
                for m1, m2 in self.motion_matches
            ],
            "shape_matches": [
                {
                    "type": s.shape_type,
                    "position1": s.position1,
                    "position2": s.position2,
                    "size1": s.size1,
                    "size2": s.size2,
                    "confidence": s.confidence
                }
                for s in self.shape_matches
            ],
            "action_continuity": self.action_continuity,
            "cut_point_suggestion": self.cut_point_suggestion,
            "match_type": self.match_type,
            "confidence": self.confidence
        }


class MatchCutDetector:
    """Detects and analyzes match cuts between shots."""
    
    def __init__(self):
        """Initialize match cut detector."""
        self.motion_threshold = 0.7
        self.shape_threshold = 0.8
        
    def analyze_match_cut(
        self,
        image1_path: ImagePath,
        image2_path: ImagePath
    ) -> MatchCutAnalysis:
        """
        Analyze potential match cut between two images.
        
        Args:
            image1_path: Path to first image
            image2_path: Path to second image
            
        Returns:
            MatchCutAnalysis with detected matches
        """
        # Load images
        img1 = self._load_image(image1_path)
        img2 = self._load_image(image2_path)
        
        # Detect motion patterns
        motion1 = self._detect_motion(img1)
        motion2 = self._detect_motion(img2)
        motion_matches = self._match_motions(motion1, motion2)
        
        # Detect shapes
        shapes1 = self._detect_shapes(img1)
        shapes2 = self._detect_shapes(img2)
        shape_matches = self._match_shapes(shapes1, shapes2)
        
        # Analyze action continuity
        action_score = self._analyze_action_continuity(
            img1, img2, motion_matches, shape_matches
        )
        
        # Determine match type and confidence
        match_type, confidence = self._determine_match_type(
            motion_matches, shape_matches, action_score
        )
        
        return MatchCutAnalysis(
            motion_matches=motion_matches,
            shape_matches=shape_matches,
            action_continuity=action_score,
            cut_point_suggestion=None,  # Would need video for frame-specific
            match_type=match_type,
            confidence=confidence
        )
    
    def _load_image(self, path: ImagePath) -> np.ndarray:
        """Load and preprocess image."""
        img = cv2.imread(str(path))
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    def _detect_motion(self, image: np.ndarray) -> List[MotionVector]:
        """Detect motion patterns in image using optical flow simulation."""
        vectors = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Detect edges for motion cues
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours (potential moving objects)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        h, w = image.shape[:2]
        
        for contour in contours[:10]:  # Top 10 largest
            if cv2.contourArea(contour) < 100:
                continue
                
            # Get contour properties
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
                
            cx = M["m10"] / M["m00"] / w
            cy = M["m01"] / M["m00"] / h
            
            # Estimate motion direction from contour shape
            rect = cv2.minAreaRect(contour)
            angle = rect[2] * np.pi / 180
            
            # Create motion vector
            vector = MotionVector(
                direction=(np.cos(angle), np.sin(angle)),
                magnitude=min(cv2.contourArea(contour) / (w * h) * 10, 1.0),
                center=(cx, cy)
            )
            vectors.append(vector)
        
        return vectors
    
    def _detect_shapes(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect geometric shapes in image."""
        shapes = []
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        h, w = image.shape[:2]
        
        # Detect circles
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=min(h, w) // 3
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for circle in circles[0, :5]:  # Top 5 circles
                shapes.append({
                    "type": "circle",
                    "center": (circle[0] / w, circle[1] / h),
                    "radius": circle[2] / min(h, w),
                    "area": np.pi * (circle[2] / min(h, w))**2
                })
        
        # Detect lines
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )
        
        if lines is not None:
            for line in lines[:5]:  # Top 5 lines
                x1, y1, x2, y2 = line[0]
                shapes.append({
                    "type": "line",
                    "start": (x1 / w, y1 / h),
                    "end": (x2 / w, y2 / h),
                    "length": np.sqrt((x2-x1)**2 + (y2-y1)**2) / np.sqrt(h**2 + w**2)
                })
        
        # Detect rectangles
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        for contour in contours[:5]:  # Top 5 contours
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            
            if len(approx) == 4:  # Rectangle
                x, y, w_rect, h_rect = cv2.boundingRect(approx)
                shapes.append({
                    "type": "rectangle",
                    "center": ((x + w_rect/2) / w, (y + h_rect/2) / h),
                    "width": w_rect / w,
                    "height": h_rect / h,
                    "area": (w_rect / w) * (h_rect / h)
                })
        
        return shapes
    
    def _match_motions(
        self,
        motions1: List[MotionVector],
        motions2: List[MotionVector]
    ) -> List[Tuple[MotionVector, MotionVector]]:
        """Match motion vectors between images."""
        matches = []
        
        for m1 in motions1:
            best_match = None
            best_score = 0
            
            for m2 in motions2:
                score = m1.similarity_to(m2)
                if score > best_score and score > self.motion_threshold:
                    best_score = score
                    best_match = m2
            
            if best_match:
                matches.append((m1, best_match))
        
        return matches
    
    def _match_shapes(
        self,
        shapes1: List[Dict[str, Any]],
        shapes2: List[Dict[str, Any]]
    ) -> List[ShapeMatch]:
        """Match shapes between images."""
        matches = []
        
        for s1 in shapes1:
            for s2 in shapes2:
                if s1["type"] != s2["type"]:
                    continue
                
                confidence = 0
                
                if s1["type"] == "circle":
                    # Match circles by position and size
                    pos_dist = np.sqrt(
                        (s1["center"][0] - s2["center"][0])**2 +
                        (s1["center"][1] - s2["center"][1])**2
                    )
                    size_ratio = min(s1["radius"], s2["radius"]) / max(s1["radius"], s2["radius"])
                    confidence = (1 - min(pos_dist, 1)) * 0.5 + size_ratio * 0.5
                    
                elif s1["type"] == "line":
                    # Match lines by angle and position
                    angle1 = np.arctan2(
                        s1["end"][1] - s1["start"][1],
                        s1["end"][0] - s1["start"][0]
                    )
                    angle2 = np.arctan2(
                        s2["end"][1] - s2["start"][1],
                        s2["end"][0] - s2["start"][0]
                    )
                    angle_diff = abs(angle1 - angle2)
                    angle_sim = 1 - min(angle_diff / np.pi, 1)
                    
                    # Average position
                    center1 = (
                        (s1["start"][0] + s1["end"][0]) / 2,
                        (s1["start"][1] + s1["end"][1]) / 2
                    )
                    center2 = (
                        (s2["start"][0] + s2["end"][0]) / 2,
                        (s2["start"][1] + s2["end"][1]) / 2
                    )
                    pos_dist = np.sqrt(
                        (center1[0] - center2[0])**2 +
                        (center1[1] - center2[1])**2
                    )
                    pos_sim = 1 - min(pos_dist, 1)
                    
                    confidence = angle_sim * 0.6 + pos_sim * 0.4
                    
                elif s1["type"] == "rectangle":
                    # Match rectangles by position and aspect ratio
                    pos_dist = np.sqrt(
                        (s1["center"][0] - s2["center"][0])**2 +
                        (s1["center"][1] - s2["center"][1])**2
                    )
                    aspect1 = s1["width"] / s1["height"]
                    aspect2 = s2["width"] / s2["height"]
                    aspect_sim = min(aspect1, aspect2) / max(aspect1, aspect2)
                    confidence = (1 - min(pos_dist, 1)) * 0.5 + aspect_sim * 0.5
                
                if confidence > self.shape_threshold:
                    match = ShapeMatch(
                        shape_type=s1["type"],
                        position1=s1.get("center", s1.get("start", (0, 0))),
                        position2=s2.get("center", s2.get("start", (0, 0))),
                        size1=s1.get("radius", s1.get("area", s1.get("length", 0))),
                        size2=s2.get("radius", s2.get("area", s2.get("length", 0))),
                        confidence=confidence
                    )
                    matches.append(match)
        
        return matches
    
    def _analyze_action_continuity(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        motion_matches: List[Tuple[MotionVector, MotionVector]],
        shape_matches: List[ShapeMatch]
    ) -> float:
        """Analyze how well action continues between shots."""
        score = 0.0
        
        # Motion continuity
        if motion_matches:
            motion_scores = [
                m1.similarity_to(m2) for m1, m2 in motion_matches
            ]
            score += np.mean(motion_scores) * 0.5
        
        # Shape alignment
        if shape_matches:
            shape_scores = [s.confidence for s in shape_matches]
            score += np.mean(shape_scores) * 0.3
        
        # Edge alignment (for compositional continuity)
        edges1 = cv2.Canny(cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY), 50, 150)
        edges2 = cv2.Canny(cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY), 50, 150)
        
        # Compare edge distributions
        hist1 = cv2.calcHist([edges1], [0], None, [2], [0, 256])
        hist2 = cv2.calcHist([edges2], [0], None, [2], [0, 256])
        
        edge_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        score += max(0, edge_similarity) * 0.2
        
        return min(score, 1.0)
    
    def _determine_match_type(
        self,
        motion_matches: List[Tuple[MotionVector, MotionVector]],
        shape_matches: List[ShapeMatch],
        action_score: float
    ) -> Tuple[str, float]:
        """Determine the type and confidence of match cut."""
        motion_weight = len(motion_matches) * 0.3
        shape_weight = len(shape_matches) * 0.3
        action_weight = action_score * 0.4
        
        total_score = min(motion_weight + shape_weight + action_weight, 1.0)
        
        if motion_weight > shape_weight and motion_weight > 0.3:
            match_type = "motion"
        elif shape_weight > motion_weight and shape_weight > 0.3:
            match_type = "shape"
        elif action_score > 0.6:
            match_type = "action"
        else:
            match_type = "composite"
        
        return match_type, total_score


def find_match_cuts(
    images: List[ImagePath],
    threshold: float = 0.7
) -> List[Tuple[int, int, MatchCutAnalysis]]:
    """
    Find potential match cuts in a sequence of images.
    
    Args:
        images: List of image paths
        threshold: Minimum confidence for match cut
        
    Returns:
        List of (index1, index2, analysis) tuples
    """
    detector = MatchCutDetector()
    matches = []
    
    for i in range(len(images) - 1):
        for j in range(i + 1, min(i + 5, len(images))):  # Check next 5 images
            analysis = detector.analyze_match_cut(images[i], images[j])
            
            if analysis.confidence >= threshold:
                matches.append((i, j, analysis))
                logger.info(
                    f"Found {analysis.match_type} match cut between "
                    f"images {i} and {j} (confidence: {analysis.confidence:.2f})"
                )
    
    return matches


def export_match_cuts(
    matches: List[Tuple[int, int, MatchCutAnalysis]],
    output_path: Path,
    format: str = "json"
) -> None:
    """Export match cut analysis to file."""
    if format == "json":
        data = {
            "match_cuts": [
                {
                    "from_index": i,
                    "to_index": j,
                    "analysis": analysis.to_dict()
                }
                for i, j, analysis in matches
            ],
            "total_matches": len(matches)
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    elif format == "edl":
        # Export as EDL with match cut annotations
        with open(output_path, 'w') as f:
            f.write("TITLE: Match Cuts\n\n")
            
            for idx, (i, j, analysis) in enumerate(matches):
                f.write(f"{idx+1:03d}  001      V     C        ")
                f.write(f"00:00:{i:02d}:00 00:00:{j:02d}:00 ")
                f.write(f"00:00:{i:02d}:00 00:00:{j:02d}:00\n")
                f.write(f"* MATCH CUT: {analysis.match_type.upper()}\n")
                f.write(f"* CONFIDENCE: {analysis.confidence:.2%}\n")
                f.write("\n")