"""Style consistency analyzer plugin for checking visual coherence."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import cv2
from sklearn.metrics.pairwise import cosine_similarity
import imagehash
from PIL import Image

from ..base import AnalyzerPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class StyleConsistencyAnalyzerPlugin(AnalyzerPlugin):
    """Analyze style consistency across a set of images."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="style_consistency_analyzer",
            version="1.0.0",
            type=PluginType.ANALYZER,
            description="Analyze visual style consistency across multiple images",
            author="AliceMultiverse",
            dependencies=["opencv-python", "pillow", "numpy", "scikit-learn", "imagehash"],
            config_schema={
                "threshold": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7,
                    "description": "Similarity threshold for consistency"
                },
                "color_weight": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3
                },
                "texture_weight": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3
                },
                "composition_weight": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.4
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the analyzer."""
        self.threshold = self.config.get("threshold", 0.7)
        self.color_weight = self.config.get("color_weight", 0.3)
        self.texture_weight = self.config.get("texture_weight", 0.3)
        self.composition_weight = self.config.get("composition_weight", 0.4)
        
        # Normalize weights
        total_weight = self.color_weight + self.texture_weight + self.composition_weight
        if total_weight > 0:
            self.color_weight /= total_weight
            self.texture_weight /= total_weight
            self.composition_weight /= total_weight
        
        self._initialized = True
        return True
    
    async def cleanup(self):
        """Clean up resources."""
        self._initialized = False
    
    async def analyze(self, inputs: List[Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze style consistency across images.
        
        Args:
            inputs: List of image paths to analyze
            parameters: Analysis parameters
            
        Returns:
            Analysis results including consistency score and recommendations
        """
        if len(inputs) < 2:
            return {
                "error": "At least 2 images required for consistency analysis",
                "success": False
            }
        
        # Extract features from all images
        features = []
        for img_path in inputs:
            try:
                feature = await self._extract_features(img_path)
                features.append(feature)
            except Exception as e:
                logger.error(f"Error extracting features from {img_path}: {e}")
                continue
        
        if len(features) < 2:
            return {
                "error": "Could not extract features from enough images",
                "success": False
            }
        
        # Calculate pairwise similarities
        similarities = []
        detailed_scores = []
        
        for i in range(len(features)):
            for j in range(i + 1, len(features)):
                sim = self._calculate_similarity(features[i], features[j])
                similarities.append(sim["overall"])
                detailed_scores.append({
                    "images": [str(inputs[i].name), str(inputs[j].name)],
                    "scores": sim
                })
        
        # Calculate overall consistency
        overall_consistency = np.mean(similarities) if similarities else 0
        
        # Identify outliers
        outliers = []
        if len(features) > 2:
            for i, img_path in enumerate(inputs):
                # Calculate average similarity to all other images
                sims = []
                for j in range(len(features)):
                    if i != j:
                        sim = self._calculate_similarity(features[i], features[j])
                        sims.append(sim["overall"])
                
                avg_sim = np.mean(sims)
                if avg_sim < self.threshold:
                    outliers.append({
                        "image": str(img_path.name),
                        "average_similarity": float(avg_sim)
                    })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_consistency, detailed_scores, outliers
        )
        
        return {
            "success": True,
            "overall_consistency": float(overall_consistency),
            "is_consistent": overall_consistency >= self.threshold,
            "detailed_scores": detailed_scores,
            "outliers": outliers,
            "recommendations": recommendations,
            "statistics": {
                "mean_similarity": float(np.mean(similarities)),
                "std_similarity": float(np.std(similarities)),
                "min_similarity": float(np.min(similarities)),
                "max_similarity": float(np.max(similarities))
            }
        }
    
    async def _extract_features(self, image_path: Path) -> Dict[str, Any]:
        """Extract style features from an image."""
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        pil_image = Image.open(image_path)
        
        features = {}
        
        # Color features
        features["color"] = self._extract_color_features(image)
        
        # Texture features
        features["texture"] = self._extract_texture_features(image)
        
        # Composition features
        features["composition"] = self._extract_composition_features(image, pil_image)
        
        return features
    
    def _extract_color_features(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract color distribution features."""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Calculate color histograms
        h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        v_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # Normalize histograms
        h_hist = cv2.normalize(h_hist, h_hist).flatten()
        s_hist = cv2.normalize(s_hist, s_hist).flatten()
        v_hist = cv2.normalize(v_hist, v_hist).flatten()
        
        # Calculate dominant colors
        pixels = image.reshape(-1, 3)
        # Simple k-means clustering for dominant colors
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        kmeans.fit(pixels)
        dominant_colors = kmeans.cluster_centers_
        
        return {
            "hue_hist": h_hist,
            "saturation_hist": s_hist,
            "value_hist": v_hist,
            "dominant_colors": dominant_colors
        }
    
    def _extract_texture_features(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract texture features using gradients."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate gradient magnitude and orientation
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        orientation = np.arctan2(grad_y, grad_x)
        
        # Create histograms
        mag_hist = cv2.calcHist([magnitude.astype(np.float32)], [0], None, [256], [0, 256])
        orient_hist = cv2.calcHist([orientation.astype(np.float32)], [0], None, [36], [-np.pi, np.pi])
        
        # Normalize
        mag_hist = cv2.normalize(mag_hist, mag_hist).flatten()
        orient_hist = cv2.normalize(orient_hist, orient_hist).flatten()
        
        return {
            "magnitude_hist": mag_hist,
            "orientation_hist": orient_hist,
            "texture_energy": float(np.mean(magnitude))
        }
    
    def _extract_composition_features(self, image: np.ndarray, pil_image: Image.Image) -> Dict[str, Any]:
        """Extract composition features."""
        h, w = image.shape[:2]
        
        # Calculate center of mass of brightness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        moments = cv2.moments(gray)
        if moments["m00"] != 0:
            cx = moments["m10"] / moments["m00"] / w
            cy = moments["m01"] / moments["m00"] / h
        else:
            cx, cy = 0.5, 0.5
        
        # Calculate image hash for structure
        dhash = imagehash.dhash(pil_image, hash_size=16)
        
        # Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)
        
        return {
            "center_of_mass": (cx, cy),
            "structure_hash": str(dhash),
            "edge_density": float(edge_density),
            "aspect_ratio": w / h
        }
    
    def _calculate_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> Dict[str, float]:
        """Calculate similarity between two feature sets."""
        # Color similarity
        color_sim = 0.0
        
        # Compare color histograms
        h_sim = cv2.compareHist(features1["color"]["hue_hist"], features2["color"]["hue_hist"], cv2.HISTCMP_CORREL)
        s_sim = cv2.compareHist(features1["color"]["saturation_hist"], features2["color"]["saturation_hist"], cv2.HISTCMP_CORREL)
        v_sim = cv2.compareHist(features1["color"]["value_hist"], features2["color"]["value_hist"], cv2.HISTCMP_CORREL)
        
        color_sim = (h_sim + s_sim + v_sim) / 3
        
        # Texture similarity
        mag_sim = cv2.compareHist(features1["texture"]["magnitude_hist"], features2["texture"]["magnitude_hist"], cv2.HISTCMP_CORREL)
        orient_sim = cv2.compareHist(features1["texture"]["orientation_hist"], features2["texture"]["orientation_hist"], cv2.HISTCMP_CORREL)
        energy_sim = 1 - abs(features1["texture"]["texture_energy"] - features2["texture"]["texture_energy"]) / max(features1["texture"]["texture_energy"], features2["texture"]["texture_energy"])
        
        texture_sim = (mag_sim + orient_sim + energy_sim) / 3
        
        # Composition similarity
        cx1, cy1 = features1["composition"]["center_of_mass"]
        cx2, cy2 = features2["composition"]["center_of_mass"]
        center_dist = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
        center_sim = 1 - min(center_dist, 1.0)
        
        # Structure similarity using hash
        hash1 = imagehash.hex_to_hash(features1["composition"]["structure_hash"])
        hash2 = imagehash.hex_to_hash(features2["composition"]["structure_hash"])
        structure_sim = 1 - (hash1 - hash2) / len(hash1.hash) ** 2
        
        edge_sim = 1 - abs(features1["composition"]["edge_density"] - features2["composition"]["edge_density"])
        
        composition_sim = (center_sim + structure_sim + edge_sim) / 3
        
        # Overall similarity
        overall = (
            self.color_weight * color_sim +
            self.texture_weight * texture_sim +
            self.composition_weight * composition_sim
        )
        
        return {
            "overall": float(overall),
            "color": float(color_sim),
            "texture": float(texture_sim),
            "composition": float(composition_sim)
        }
    
    def _generate_recommendations(
        self, 
        overall_consistency: float,
        detailed_scores: List[Dict],
        outliers: List[Dict]
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if overall_consistency < 0.5:
            recommendations.append("Low consistency detected. Consider establishing a clearer visual style guide.")
        elif overall_consistency < self.threshold:
            recommendations.append("Moderate consistency. Some images deviate from the common style.")
        else:
            recommendations.append("Good style consistency across the image set.")
        
        # Analyze which aspect has lowest consistency
        if detailed_scores:
            color_scores = [s["scores"]["color"] for s in detailed_scores]
            texture_scores = [s["scores"]["texture"] for s in detailed_scores]
            composition_scores = [s["scores"]["composition"] for s in detailed_scores]
            
            avg_color = np.mean(color_scores)
            avg_texture = np.mean(texture_scores)
            avg_composition = np.mean(composition_scores)
            
            min_aspect = min(
                ("color", avg_color),
                ("texture", avg_texture),
                ("composition", avg_composition),
                key=lambda x: x[1]
            )
            
            if min_aspect[1] < self.threshold:
                aspect_recommendations = {
                    "color": "Consider using a consistent color palette or color grading.",
                    "texture": "Try to maintain similar texture styles (smooth, detailed, etc.).",
                    "composition": "Aim for consistent composition and framing across images."
                }
                recommendations.append(aspect_recommendations[min_aspect[0]])
        
        # Outlier recommendations
        if outliers:
            outlier_names = [o["image"] for o in outliers]
            recommendations.append(f"Consider reviewing or regenerating these outliers: {', '.join(outlier_names)}")
        
        return recommendations