"""MCP tools for video creation workflow."""

import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.models import Tool

from alicemultiverse.workflows.video_creation import (
    VideoCreationWorkflow,
    VideoStoryboard,
    CameraMotion,
    TransitionType
)
from alicemultiverse.storage.duckdb_search import DuckDBSearch
from alicemultiverse.providers import get_provider
from alicemultiverse.core.structured_logging import get_logger

logger = get_logger(__name__)


def register_video_creation_tools(server: Server, search_db: DuckDBSearch) -> None:
    """Register video creation tools with MCP server.
    
    Args:
        server: MCP server instance
        search_db: DuckDB search instance for asset lookup
    """
    
    # Create workflow instance
    workflow = VideoCreationWorkflow(search_db)
    
    @server.tool()
    async def analyze_for_video(
        image_hash: str
    ) -> Dict[str, Any]:
        """Analyze a single image for video generation potential.
        
        Args:
            image_hash: Hash of image to analyze
            
        Returns:
            Analysis including suggested camera motion and keywords
        """
        try:
            analysis = await workflow.analyze_image_for_video(image_hash)
            
            # Format for readable output
            return {
                "success": True,
                "image_hash": image_hash,
                "suggested_camera_motion": analysis["suggested_motion"].value,
                "motion_keywords": analysis["motion_keywords"],
                "composition": analysis["composition"],
                "tags": analysis["tags"][:10],  # Limit tags for readability
                "video_hints": {
                    "has_action": len(analysis["motion_keywords"]) > 0,
                    "suggested_duration": 5 if analysis["composition"]["has_action"] else 4,
                    "complexity": "high" if len(analysis["tags"]) > 15 else "medium"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @server.tool()
    async def generate_video_storyboard(
        image_hashes: List[str],
        style: str = "cinematic",
        target_duration: int = 30,
        project_name: Optional[str] = None,
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """Generate a complete video storyboard from selected images.
        
        Args:
            image_hashes: List of selected image hashes
            style: Video style - cinematic, documentary, music_video, narrative, abstract
            target_duration: Target video duration in seconds
            project_name: Optional project name (auto-generated if not provided)
            save_to_file: Whether to save storyboard to file
            
        Returns:
            Complete storyboard with shots and transitions
        """
        try:
            # Generate storyboard
            storyboard = await workflow.generate_video_prompts(
                image_hashes=image_hashes,
                style=style,
                target_duration=target_duration,
                enhance_with_ai=False  # Can be made configurable
            )
            
            # Override project name if provided
            if project_name:
                storyboard.project_name = project_name
            
            # Save if requested
            output_path = None
            if save_to_file:
                # Save to project directory if in a project context
                output_dir = Path.cwd() / "storyboards"
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"{storyboard.project_name}.json"
                storyboard.save(output_path)
            
            # Format response
            response = {
                "success": True,
                "project_name": storyboard.project_name,
                "total_duration": storyboard.total_duration,
                "shot_count": len(storyboard.shots),
                "style": style,
                "shots": []
            }
            
            # Add shot summaries
            for i, shot in enumerate(storyboard.shots):
                response["shots"].append({
                    "index": i + 1,
                    "image_hash": shot.image_hash[:12] + "...",
                    "duration": shot.duration,
                    "camera_motion": shot.camera_motion.value,
                    "prompt_preview": shot.prompt[:80] + "..." if len(shot.prompt) > 80 else shot.prompt
                })
            
            if output_path:
                response["saved_to"] = str(output_path)
            
            # Add usage instructions
            response["next_steps"] = [
                "Use 'create_kling_prompts' to generate video requests",
                "Or use 'prepare_flux_keyframes' for enhanced keyframes",
                "Review and edit the storyboard file if needed"
            ]
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate storyboard: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @server.tool()
    async def create_kling_prompts(
        storyboard_file: str,
        model: str = "kling-v2.1-pro-text",
        output_format: str = "list"
    ) -> Dict[str, Any]:
        """Create Kling-ready prompts from a storyboard.
        
        Args:
            storyboard_file: Path to storyboard JSON file
            model: Kling model to use (text or image variants)
            output_format: Format - 'list', 'script', or 'detailed'
            
        Returns:
            Kling prompts formatted for video generation
        """
        try:
            # Load storyboard
            storyboard_path = Path(storyboard_file)
            if not storyboard_path.exists():
                # Try in storyboards directory
                storyboard_path = Path.cwd() / "storyboards" / storyboard_file
                if not storyboard_path.exists():
                    raise FileNotFoundError(f"Storyboard not found: {storyboard_file}")
            
            storyboard = VideoStoryboard.load(storyboard_path)
            
            # Create Kling requests
            requests = workflow.create_kling_requests(storyboard, model)
            
            # Format response based on output format
            if output_format == "script":
                # Create a script format
                lines = [
                    f"# Kling Video Generation Script",
                    f"# Project: {storyboard.project_name}",
                    f"# Model: {model}",
                    ""
                ]
                
                for i, (shot, request) in enumerate(zip(storyboard.shots, requests)):
                    lines.extend([
                        f"## Shot {i+1}",
                        f"Prompt: {request.prompt}",
                        f"Duration: {request.parameters['duration']}s",
                        f"Camera: {request.parameters['camera_motion']}",
                        ""
                    ])
                
                return {
                    "success": True,
                    "format": "script",
                    "content": "\n".join(lines),
                    "shot_count": len(requests)
                }
                
            elif output_format == "detailed":
                # Detailed format with all parameters
                shots_data = []
                for i, (shot, request) in enumerate(zip(storyboard.shots, requests)):
                    shots_data.append({
                        "shot_number": i + 1,
                        "prompt": request.prompt,
                        "model": request.model,
                        "parameters": request.parameters,
                        "reference_image": shot.image_hash if request.reference_assets else None,
                        "transitions": {
                            "in": shot.transition_in.value,
                            "out": shot.transition_out.value
                        }
                    })
                
                return {
                    "success": True,
                    "format": "detailed",
                    "project": storyboard.project_name,
                    "total_duration": storyboard.total_duration,
                    "shots": shots_data
                }
                
            else:  # list format
                # Simple list of prompts
                prompts = []
                for i, request in enumerate(requests):
                    prompts.append({
                        "shot": i + 1,
                        "prompt": request.prompt,
                        "duration": request.parameters["duration"],
                        "camera": request.parameters["camera_motion"]
                    })
                
                return {
                    "success": True,
                    "format": "list",
                    "prompts": prompts,
                    "model": model,
                    "estimated_cost": len(prompts) * 0.35  # Rough estimate
                }
                
        except Exception as e:
            logger.error(f"Failed to create Kling prompts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @server.tool()
    async def prepare_flux_keyframes(
        storyboard_file: str,
        modifications: Optional[Dict[str, str]] = None,
        shots_to_process: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Prepare enhanced keyframes using Flux Kontext.
        
        Args:
            storyboard_file: Path to storyboard JSON file
            modifications: Optional modifications per shot (shot_number -> modification prompt)
            shots_to_process: Specific shots to process (1-indexed), or None for all
            
        Returns:
            Flux generation requests for keyframe preparation
        """
        try:
            # Load storyboard
            storyboard_path = Path(storyboard_file)
            if not storyboard_path.exists():
                storyboard_path = Path.cwd() / "storyboards" / storyboard_file
                if not storyboard_path.exists():
                    raise FileNotFoundError(f"Storyboard not found: {storyboard_file}")
            
            storyboard = VideoStoryboard.load(storyboard_path)
            
            # Convert shot numbers to indices if provided
            if modifications:
                # Convert 1-indexed shot numbers to 0-indexed
                mod_dict = {}
                for shot_num, mod in modifications.items():
                    idx = str(int(shot_num) - 1)
                    mod_dict[idx] = mod
                modifications = mod_dict
            
            # Prepare keyframes
            flux_requests = await workflow.prepare_keyframes_with_flux(
                storyboard, 
                modifications
            )
            
            # Filter shots if specified
            if shots_to_process:
                filtered = {}
                for shot_num in shots_to_process:
                    idx = str(shot_num - 1)
                    if idx in flux_requests:
                        filtered[idx] = flux_requests[idx]
                flux_requests = filtered
            
            # Format response
            response = {
                "success": True,
                "project": storyboard.project_name,
                "keyframe_sets": {}
            }
            
            for shot_idx, requests in flux_requests.items():
                shot_num = int(shot_idx) + 1
                shot = storyboard.shots[int(shot_idx)]
                
                keyframe_data = {
                    "shot_number": shot_num,
                    "original_prompt": shot.prompt,
                    "keyframes": []
                }
                
                for i, req in enumerate(requests):
                    keyframe_data["keyframes"].append({
                        "type": "base" if i == 0 else ("transition" if "Blend" in req.prompt else "modified"),
                        "prompt": req.prompt,
                        "model": req.model,
                        "reference_count": len(req.reference_assets) if req.reference_assets else 0
                    })
                
                response["keyframe_sets"][f"shot_{shot_num}"] = keyframe_data
            
            response["total_keyframes"] = sum(
                len(kf["keyframes"]) for kf in response["keyframe_sets"].values()
            )
            response["estimated_cost"] = response["total_keyframes"] * 0.07  # Flux cost estimate
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to prepare Flux keyframes: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @server.tool()
    async def create_transition_guide(
        storyboard_file: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a transition guide for video editing.
        
        Args:
            storyboard_file: Path to storyboard JSON file
            output_file: Optional output file path for the guide
            
        Returns:
            Formatted transition guide
        """
        try:
            # Load storyboard
            storyboard_path = Path(storyboard_file)
            if not storyboard_path.exists():
                storyboard_path = Path.cwd() / "storyboards" / storyboard_file
                if not storyboard_path.exists():
                    raise FileNotFoundError(f"Storyboard not found: {storyboard_file}")
            
            storyboard = VideoStoryboard.load(storyboard_path)
            
            # Create guide
            guide = workflow.create_transition_guide(storyboard)
            
            # Save if requested
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(guide)
                
                return {
                    "success": True,
                    "saved_to": str(output_path),
                    "preview": guide[:500] + "..." if len(guide) > 500 else guide
                }
            else:
                return {
                    "success": True,
                    "guide": guide,
                    "shot_count": len(storyboard.shots),
                    "total_duration": storyboard.total_duration
                }
                
        except Exception as e:
            logger.error(f"Failed to create transition guide: {e}")
            return {
                "success": False,
                "error": str(e)
            }