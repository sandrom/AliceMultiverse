"""
Motion and composition analyzer for images.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Union
from pathlib import Path
import logging
from PIL import Image
from .models import (
    MotionVector, 
    MotionDirection, 
    CompositionAnalysis,
    TransitionType
)


logger = logging.getLogger(__name__)


class MotionAnalyzer:
    """Analyzes motion and composition in images for transition planning."""
    
    def __init__(self):
        self.feature_detector = cv2.SIFT_create()
        self.edge_detector = cv2.Canny
        
    def analyze_image(self, image_path: Union[str, Path]) -> Dict[str, any]:
        """
        Comprehensive analysis of an image for transition planning.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing motion, composition, and color analysis
        """
        try:
            # Load image
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
                
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Perform analyses
            motion = self._analyze_motion_potential(img, gray)
            composition = self._analyze_composition(img, gray)
            colors = self._analyze_colors(img, hsv)
            
            return {
                'motion': motion,
                'composition': composition,
                'colors': colors,
                'path': str(image_path),
                'dimensions': (img.shape[1], img.shape[0])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return None
            
    def _analyze_motion_potential(self, img: np.ndarray, gray: np.ndarray) -> MotionVector:
        """Analyze potential motion in a static image."""
        h, w = gray.shape
        
        # Detect edges for motion lines
        edges = cv2.Canny(gray, 50, 150)
        
        # Find lines using HoughLinesP
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, 
                               minLineLength=min(w, h)//4, maxLineGap=10)
        
        motion_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # Normalize coordinates
                motion_lines.append((
                    (x1/w, y1/h),
                    (x2/w, y2/h)
                ))
        
        # Determine primary motion direction from lines
        direction = self._determine_motion_direction(motion_lines, (w, h))
        
        # Calculate visual flow using optical flow simulation
        flow_magnitude = self._calculate_flow_magnitude(gray)
        
        # Find focal point using feature detection
        keypoints = self.feature_detector.detect(gray, None)
        focal_point = self._calculate_focal_point(keypoints, (w, h))
        
        return MotionVector(
            direction=direction,
            speed=min(flow_magnitude, 1.0),
            focal_point=focal_point,
            motion_lines=motion_lines[:10],  # Keep top 10 lines
            confidence=0.8 if lines is not None and len(lines) > 5 else 0.5
        )
        
    def _analyze_composition(self, img: np.ndarray, gray: np.ndarray) -> CompositionAnalysis:
        """Analyze visual composition of the image."""
        h, w = gray.shape
        
        # Rule of thirds points
        thirds_points = [
            (w/3, h/3), (2*w/3, h/3),
            (w/3, 2*h/3), (2*w/3, 2*h/3)
        ]
        
        # Detect key points near rule of thirds
        keypoints = self.feature_detector.detect(gray, None)
        roi_points = []
        for kp in keypoints:
            for tp in thirds_points:
                if np.linalg.norm(np.array(kp.pt) - np.array(tp)) < min(w, h) * 0.1:
                    roi_points.append((kp.pt[0]/w, kp.pt[1]/h))
                    break
                    
        # Find leading lines
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50)
        leading_lines = []
        if lines is not None:
            # Sort by length and keep longest
            sorted_lines = sorted(lines, key=lambda l: np.linalg.norm(
                np.array([l[0][2]-l[0][0], l[0][3]-l[0][1]])), reverse=True)
            for line in sorted_lines[:5]:
                x1, y1, x2, y2 = line[0]
                leading_lines.append(((x1/w, y1/h), (x2/w, y2/h)))
        
        # Calculate visual weight center
        weight_center = self._calculate_visual_weight_center(gray)
        
        # Find empty space regions
        empty_regions = self._find_empty_regions(gray)
        
        # Analyze brightness by quadrant
        brightness_map = self._analyze_brightness_distribution(gray)
        
        # Get dominant colors
        dominant_colors = self._get_dominant_colors(img)
        
        return CompositionAnalysis(
            rule_of_thirds_points=roi_points,
            leading_lines=leading_lines,
            visual_weight_center=weight_center,
            empty_space_regions=empty_regions,
            dominant_colors=dominant_colors,
            brightness_map=brightness_map
        )
        
    def _analyze_colors(self, img: np.ndarray, hsv: np.ndarray) -> Dict[str, any]:
        """Analyze color properties of the image."""
        # Calculate color histogram
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # Determine color temperature (warm/cool)
        warm_mask = cv2.inRange(hsv, (0, 50, 50), (30, 255, 255))  # Reds/oranges
        cool_mask = cv2.inRange(hsv, (90, 50, 50), (130, 255, 255))  # Blues
        
        warm_ratio = np.sum(warm_mask > 0) / warm_mask.size
        cool_ratio = np.sum(cool_mask > 0) / cool_mask.size
        
        temperature = "warm" if warm_ratio > cool_ratio else "cool"
        
        return {
            'temperature': temperature,
            'warmth': warm_ratio,
            'coolness': cool_ratio,
            'saturation': float(np.mean(hist_s)),
            'brightness': float(np.mean(hist_v)),
            'contrast': float(np.std(hist_v))
        }
        
    def _determine_motion_direction(self, lines: List[Tuple], img_size: Tuple[int, int]) -> MotionDirection:
        """Determine primary motion direction from detected lines."""
        if not lines:
            return MotionDirection.STATIC
            
        # Calculate angle distribution
        angles = []
        for (start, end) in lines:
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            angle = np.arctan2(dy, dx) * 180 / np.pi
            angles.append(angle)
            
        # Determine dominant direction
        avg_angle = np.mean(angles)
        
        if -22.5 <= avg_angle <= 22.5:
            return MotionDirection.LEFT_TO_RIGHT
        elif 157.5 <= abs(avg_angle) <= 180:
            return MotionDirection.RIGHT_TO_LEFT
        elif 67.5 <= avg_angle <= 112.5:
            return MotionDirection.DOWN_TO_UP
        elif -112.5 <= avg_angle <= -67.5:
            return MotionDirection.UP_TO_DOWN
        else:
            return MotionDirection.DIAGONAL
            
    def _calculate_flow_magnitude(self, gray: np.ndarray) -> float:
        """Calculate simulated optical flow magnitude."""
        # Use gradient magnitude as proxy for motion potential
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Normalize to 0-1 range
        return float(np.mean(magnitude) / 255.0)
        
    def _calculate_focal_point(self, keypoints, img_size: Tuple[int, int]) -> Tuple[float, float]:
        """Calculate focal point from keypoints."""
        if not keypoints:
            return (0.5, 0.5)  # Center if no keypoints
            
        # Weight keypoints by response (strength)
        weighted_x = sum(kp.pt[0] * kp.response for kp in keypoints)
        weighted_y = sum(kp.pt[1] * kp.response for kp in keypoints)
        total_weight = sum(kp.response for kp in keypoints)
        
        if total_weight > 0:
            focal_x = weighted_x / total_weight / img_size[0]
            focal_y = weighted_y / total_weight / img_size[1]
            return (focal_x, focal_y)
        return (0.5, 0.5)
        
    def _calculate_visual_weight_center(self, gray: np.ndarray) -> Tuple[float, float]:
        """Calculate center of visual weight."""
        # Use intensity as weight
        h, w = gray.shape
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        
        total_weight = np.sum(gray)
        if total_weight > 0:
            center_x = np.sum(x_coords * gray) / total_weight / w
            center_y = np.sum(y_coords * gray) / total_weight / h
            return (float(center_x), float(center_y))
        return (0.5, 0.5)
        
    def _find_empty_regions(self, gray: np.ndarray) -> List[Tuple[float, float, float, float]]:
        """Find regions with low visual activity."""
        h, w = gray.shape
        
        # Divide into grid and find low-activity regions
        grid_size = 4
        regions = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                y1 = i * h // grid_size
                y2 = (i + 1) * h // grid_size
                x1 = j * w // grid_size
                x2 = (j + 1) * w // grid_size
                
                region = gray[y1:y2, x1:x2]
                if np.std(region) < 20:  # Low variance = empty
                    regions.append((
                        x1/w, y1/h,
                        (x2-x1)/w, (y2-y1)/h
                    ))
                    
        return regions
        
    def _analyze_brightness_distribution(self, gray: np.ndarray) -> Dict[str, float]:
        """Analyze brightness by quadrant."""
        h, w = gray.shape
        h2, w2 = h//2, w//2
        
        return {
            'top_left': float(np.mean(gray[:h2, :w2]) / 255),
            'top_right': float(np.mean(gray[:h2, w2:]) / 255),
            'bottom_left': float(np.mean(gray[h2:, :w2]) / 255),
            'bottom_right': float(np.mean(gray[h2:, w2:]) / 255)
        }
        
    def _get_dominant_colors(self, img: np.ndarray) -> List[Tuple[str, float]]:
        """Extract dominant colors using k-means clustering."""
        # Reshape image to list of pixels
        pixels = img.reshape(-1, 3)
        
        # Use simple quantization for speed
        # Round to nearest 32 for each channel
        quantized = (pixels // 32) * 32
        
        # Count unique colors
        unique, counts = np.unique(quantized, axis=0, return_counts=True)
        
        # Sort by frequency
        sorted_idx = np.argsort(counts)[::-1]
        
        # Return top 5 colors
        total_pixels = len(pixels)
        dominant = []
        for i in sorted_idx[:5]:
            color = unique[i]
            percentage = counts[i] / total_pixels
            # Convert BGR to hex
            hex_color = '#{:02x}{:02x}{:02x}'.format(color[2], color[1], color[0])
            dominant.append((hex_color, float(percentage)))
            
        return dominant