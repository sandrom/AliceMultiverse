"""Asset analysis functionality."""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import re

from alice_utils import (
    compute_file_hash,
    detect_media_type,
    extract_image_metadata,
    get_file_info
)
from alice_models import MediaType, SourceType

from .models import AnalyzeResponse

logger = logging.getLogger(__name__)


class AssetAnalyzer:
    """Analyzes media assets to extract metadata and detect AI sources."""
    
    # AI source detection patterns
    AI_PATTERNS = {
        SourceType.STABLE_DIFFUSION: [
            r'Stable Diffusion',
            r'stable-diffusion',
            r'SD\s*v?\d+',
            r'Model: .*_v\d+',
            r'automatic1111',
            r'AUTOMATIC1111',
            r'Steps: \d+',
            r'Sampler: (?:DPM|Euler|DDIM|UniPC)',
            r'CFG scale: \d+',
        ],
        SourceType.MIDJOURNEY: [
            r'Midjourney',
            r'midjourney',
            r'MJ',
            r'mj_version',
            r'Job ID: [a-f0-9-]+',
        ],
        SourceType.DALLE: [
            r'DALL[·•]?E',
            r'dall-?e',
            r'OpenAI',
            r'dalle-\d+',
        ],
        SourceType.COMFYUI: [
            r'ComfyUI',
            r'comfyui',
            r'Workflow: ',
            r'prompt_id',
        ],
        SourceType.LEONARDO: [
            r'Leonardo\.AI',
            r'leonardo\.ai',
            r'Leonardo',
        ],
        SourceType.FLUX: [
            r'FLUX',
            r'flux',
            r'black-forest-labs',
        ],
        SourceType.IDEOGRAM: [
            r'Ideogram',
            r'ideogram\.ai',
        ],
        SourceType.PLAYGROUND: [
            r'Playground',
            r'playground\.ai',
        ],
    }
    
    def __init__(self):
        """Initialize analyzer."""
        self.logger = logger.getChild("analyzer")
    
    async def analyze(self, file_path: Path) -> AnalyzeResponse:
        """Analyze a media file."""
        start_time = time.time()
        
        # Get basic file info
        file_info = get_file_info(file_path)
        
        # Compute content hash
        content_hash = compute_file_hash(file_path)
        
        # Detect media type
        media_type = detect_media_type(file_path)
        
        # Initialize response data
        metadata = {
            "filename": file_info["name"],
            "created": file_info["created"].isoformat(),
            "modified": file_info["modified"].isoformat(),
        }
        
        extracted_metadata = {}
        generation_params = {}
        tags = []
        dimensions = None
        ai_source = None
        
        # Extract metadata based on media type
        if media_type == MediaType.IMAGE:
            img_metadata = extract_image_metadata(file_path)
            
            # Get dimensions
            if "width" in img_metadata and "height" in img_metadata:
                dimensions = {
                    "width": img_metadata["width"],
                    "height": img_metadata["height"]
                }
            
            # Extract EXIF
            if "exif" in img_metadata:
                extracted_metadata["exif"] = img_metadata["exif"]
            
            # Extract AI generation parameters
            if "info" in img_metadata:
                generation_params = self._extract_ai_params(img_metadata["info"])
                ai_source = self._detect_ai_source_from_metadata(img_metadata["info"])
            
            # Extract semantic tags
            tags = self._extract_semantic_tags(img_metadata, generation_params)
        
        # Detect AI source from filename if not found in metadata
        if not ai_source:
            ai_source = self._detect_ai_source_from_filename(file_path.name)
        
        # Processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return AnalyzeResponse(
            content_hash=content_hash,
            media_type=media_type,
            file_size=file_info["size"],
            ai_source=ai_source,
            metadata=metadata,
            extracted_metadata=extracted_metadata,
            generation_params=generation_params,
            tags=tags,
            dimensions=dimensions,
            processing_time_ms=processing_time_ms
        )
    
    def _extract_ai_params(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract AI generation parameters from image info."""
        params = {}
        
        # Look for common parameter fields
        param_fields = [
            "parameters", "params", "prompt", "negative_prompt",
            "steps", "cfg_scale", "sampler", "seed", "model",
            "model_hash", "width", "height", "denoising_strength"
        ]
        
        for field in param_fields:
            if field in info:
                params[field] = info[field]
        
        # Try to parse parameters string (common in SD)
        if "parameters" in info and isinstance(info["parameters"], str):
            parsed = self._parse_sd_parameters(info["parameters"])
            params.update(parsed)
        
        return params
    
    def _parse_sd_parameters(self, params_str: str) -> Dict[str, Any]:
        """Parse Stable Diffusion parameters string."""
        parsed = {}
        
        # Extract prompt (everything before "Negative prompt:" or first parameter)
        prompt_match = re.search(r'^(.*?)(?:Negative prompt:|Steps:|$)', params_str, re.DOTALL)
        if prompt_match:
            parsed["prompt"] = prompt_match.group(1).strip()
        
        # Extract negative prompt
        neg_prompt_match = re.search(r'Negative prompt:\s*([^,\n]+(?:,\s*[^,\n]+)*)', params_str)
        if neg_prompt_match:
            parsed["negative_prompt"] = neg_prompt_match.group(1).strip()
        
        # Extract other parameters
        param_patterns = {
            "steps": r'Steps:\s*(\d+)',
            "sampler": r'Sampler:\s*([^,\n]+)',
            "cfg_scale": r'CFG scale:\s*([\d.]+)',
            "seed": r'Seed:\s*(\d+)',
            "size": r'Size:\s*(\d+x\d+)',
            "model_hash": r'Model hash:\s*([a-f0-9]+)',
            "model": r'Model:\s*([^,\n]+)',
            "denoising_strength": r'Denoising strength:\s*([\d.]+)',
        }
        
        for param, pattern in param_patterns.items():
            match = re.search(pattern, params_str)
            if match:
                value = match.group(1)
                # Convert numeric values
                if param in ["steps", "seed"]:
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                elif param in ["cfg_scale", "denoising_strength"]:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                parsed[param] = value
        
        return parsed
    
    def _detect_ai_source_from_metadata(self, info: Dict[str, Any]) -> Optional[SourceType]:
        """Detect AI source from metadata."""
        # Convert all values to strings for pattern matching
        metadata_str = json.dumps(info, default=str).lower()
        
        for source, patterns in self.AI_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern.lower(), metadata_str):
                    return source
        
        return None
    
    def _detect_ai_source_from_filename(self, filename: str) -> Optional[SourceType]:
        """Detect AI source from filename patterns."""
        filename_lower = filename.lower()
        
        # Common filename patterns
        filename_patterns = {
            SourceType.STABLE_DIFFUSION: [
                r'sd_', r'stable_diffusion', r'_sd\d+', r'automatic1111'
            ],
            SourceType.MIDJOURNEY: [
                r'mj_', r'midjourney', r'_mj_', r'discord'
            ],
            SourceType.DALLE: [
                r'dalle', r'dall-e', r'openai'
            ],
            SourceType.COMFYUI: [
                r'comfyui', r'comfy_'
            ],
            SourceType.LEONARDO: [
                r'leonardo', r'leo_ai'
            ],
            SourceType.FLUX: [
                r'flux_', r'_flux'
            ],
        }
        
        for source, patterns in filename_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return source
        
        return None
    
    def _extract_semantic_tags(self, metadata: Dict[str, Any], 
                             gen_params: Dict[str, Any]) -> List[str]:
        """Extract semantic tags from metadata and prompts."""
        tags = set()
        
        # Extract from prompt
        prompt = gen_params.get("prompt", "")
        if prompt:
            # Common style tags
            style_tags = [
                "photorealistic", "anime", "cartoon", "abstract", "surreal",
                "minimalist", "vintage", "retro", "futuristic", "fantasy",
                "sci-fi", "horror", "romantic", "dramatic", "cinematic"
            ]
            
            prompt_lower = prompt.lower()
            for tag in style_tags:
                if tag in prompt_lower:
                    tags.add(tag)
            
            # Extract subject tags (simplified)
            if any(word in prompt_lower for word in ["portrait", "face", "person", "people"]):
                tags.add("portrait")
            if any(word in prompt_lower for word in ["landscape", "scenery", "nature"]):
                tags.add("landscape")
            if any(word in prompt_lower for word in ["architecture", "building", "interior"]):
                tags.add("architecture")
        
        # Add technical tags based on parameters
        if gen_params.get("steps", 0) > 50:
            tags.add("high-detail")
        if gen_params.get("cfg_scale", 0) > 10:
            tags.add("high-guidance")
        
        return sorted(list(tags))