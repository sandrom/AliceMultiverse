"""
Metadata Capacity Demonstration for All Formats

This shows that JPEG, PNG, MP4, and MOV can all store sufficient
metadata for AliceMultiverse's needs.
"""

import json
from typing import Dict, Any


def create_comprehensive_metadata() -> Dict[str, Any]:
    """Create a comprehensive metadata example with all possible fields."""
    return {
        # Basic generation info
        'prompt': 'A very long and detailed prompt describing a cyberpunk city scene with neon lights, '
                 'flying cars, holographic advertisements, rain-slicked streets, and crowds of people '
                 'with cybernetic enhancements walking through narrow alleyways filled with steam '
                 'and colored lights from various shops and vendors selling futuristic goods',
        
        'negative_prompt': 'blurry, low quality, distorted, unrealistic, cartoon, anime style',
        
        'generation_params': {
            'model': 'stable-diffusion-xl-base-1.0',
            'vae': 'sdxl-vae-fp16-fix',
            'seed': 1234567890,
            'steps': 150,
            'cfg_scale': 7.5,
            'sampler': 'DPM++ 3M SDE Karras',
            'scheduler': 'karras',
            'width': 1024,
            'height': 1024,
            'clip_skip': 2,
            'lora_models': [
                {'name': 'cyberpunk_style_v2', 'weight': 0.8},
                {'name': 'neon_lights_v1', 'weight': 0.6}
            ],
            'controlnet': {
                'model': 'controlnet-depth',
                'weight': 0.7,
                'guidance_start': 0.0,
                'guidance_end': 1.0
            }
        },
        
        # Quality analysis results
        'brisque_score': 23.456789,
        'brisque_normalized': 0.76543211,
        
        'sightengine_quality': 0.8765,
        'sightengine_sharpness': 0.9234,
        'sightengine_contrast': 0.7891,
        'sightengine_brightness': 0.8123,
        'sightengine_exposure': 0.8456,
        'sightengine_ai_generated': True,
        'sightengine_ai_probability': 0.9876,
        'sightengine_ai_model_detected': 'stable_diffusion',
        
        'claude_defects_found': True,
        'claude_defect_count': 2,
        'claude_severity': 'low',
        'claude_confidence': 0.8765,
        'claude_quality_score': 0.8234,
        'claude_defects': [
            {
                'type': 'anatomical_inconsistency',
                'location': 'hand',
                'severity': 'minor',
                'description': 'Extra finger on left hand'
            },
            {
                'type': 'lighting_inconsistency',
                'location': 'background',
                'severity': 'minor',
                'description': 'Shadow direction mismatch'
            }
        ],
        'claude_positive_aspects': [
            'Excellent color composition',
            'Strong atmospheric perspective',
            'Detailed textures throughout'
        ],
        
        # Semantic tags (lots of them)
        'style_tags': ['cyberpunk', 'neon', 'futuristic', 'noir', 'atmospheric', 
                       'detailed', 'photorealistic', 'cinematic', 'moody'],
        'mood_tags': ['mysterious', 'energetic', 'tense', 'exciting', 'dark',
                      'vibrant', 'electric', 'urban', 'gritty'],
        'subject_tags': ['city', 'street', 'people', 'architecture', 'vehicles',
                        'signs', 'lights', 'rain', 'crowd', 'technology'],
        'color_tags': ['blue', 'purple', 'pink', 'neon', 'dark', 'contrast',
                       'saturated', 'cool_tones'],
        'technical_tags': ['high_resolution', 'detailed', 'sharp', 'well_composed',
                          'professional', 'portfolio_quality'],
        'custom_tags': ['client_approved', 'hero_shot', 'cover_image', 'featured',
                       'award_submission', 'print_ready'],
        
        # Relationships and lineage
        'relationships': {
            'parent': 'asset_base_001',
            'variations': ['asset_var_001', 'asset_var_002', 'asset_var_003'],
            'references': ['ref_001', 'ref_002'],
            'derivatives': ['asset_upscaled_001', 'asset_edited_001'],
            'similar': ['asset_789', 'asset_790', 'asset_791'],
            'collection': 'cyberpunk_heroes_2024'
        },
        
        # Project and workflow info
        'project_id': 'cyberpunk_music_video_2024_q1',
        'project_metadata': {
            'client': 'Neon Dreams Productions',
            'deadline': '2024-03-15',
            'budget_code': 'ND2024-001',
            'creative_director': 'Jane Doe',
            'art_direction': 'Dark, moody, high contrast'
        },
        
        'workflow_id': 'hero_shot_workflow_v3',
        'workflow_stage': 'final_selection',
        'approval_status': 'pending_client',
        'revision_number': 3,
        
        # Extended metadata
        'creation_context': {
            'session_id': 'sess_20240315_142350',
            'batch_id': 'batch_hero_shots_001',
            'experiment_id': 'exp_lighting_variations',
            'iteration': 47,
            'total_iterations': 150
        },
        
        # ComfyUI specific
        'comfyui_workflow': {
            'workflow_api': '... (large JSON workflow definition) ...',
            'custom_nodes': ['ComfyUI-Impact-Pack', 'ComfyUI-Manager'],
            'execution_time': 45.6,
            'vram_peak': 11.2
        },
        
        # Video-specific (for MP4/MOV)
        'video_metadata': {
            'duration': 10.5,
            'fps': 24,
            'codec': 'h264',
            'bitrate': 8000000,
            'resolution': '1920x1080',
            'aspect_ratio': '16:9',
            'color_space': 'rec709',
            'scene_changes': [1.0, 3.5, 5.0, 7.5],
            'motion_vectors': '... (motion data) ...'
        },
        
        # Usage rights and licensing
        'licensing': {
            'license': 'commercial_use',
            'restrictions': ['no_resale', 'attribution_required'],
            'expiry_date': '2025-03-15',
            'territory': 'worldwide',
            'usage_categories': ['digital', 'print', 'billboard']
        },
        
        # Analytics and performance
        'analytics': {
            'view_count': 1523,
            'download_count': 47,
            'usage_in_projects': 3,
            'client_rating': 4.8,
            'peer_reviews': [
                {'reviewer': 'john_doe', 'score': 5, 'comment': 'Excellent mood'},
                {'reviewer': 'jane_smith', 'score': 4, 'comment': 'Good but needs refinement'}
            ]
        },
        
        # Technical pipeline data
        'pipeline_data': {
            'stages_completed': ['generation', 'upscaling', 'color_grading', 'sharpening'],
            'processing_time_total': 127.5,
            'api_costs': {
                'generation': 0.023,
                'sightengine': 0.001,
                'claude': 0.018,
                'storage': 0.002
            },
            'carbon_footprint': 0.045  # kg CO2
        }
    }


def analyze_metadata_size():
    """Analyze the size of comprehensive metadata."""
    metadata = create_comprehensive_metadata()
    
    # Convert to JSON to measure size
    json_str = json.dumps(metadata, indent=2)
    json_compact = json.dumps(metadata, separators=(',', ':'))
    
    print("Metadata Size Analysis")
    print("=" * 50)
    print(f"Number of top-level fields: {len(metadata)}")
    print(f"Total nested fields: ~{sum(len(v) if isinstance(v, dict) else 1 for v in metadata.values())}")
    print(f"\nJSON size (formatted): {len(json_str):,} bytes ({len(json_str)/1024:.1f} KB)")
    print(f"JSON size (compact): {len(json_compact):,} bytes ({len(json_compact)/1024:.1f} KB)")
    
    # Test compression (what PNG uses internally)
    import zlib
    compressed = zlib.compress(json_compact.encode())
    print(f"Compressed size: {len(compressed):,} bytes ({len(compressed)/1024:.1f} KB)")
    print(f"Compression ratio: {len(compressed)/len(json_compact)*100:.1f}%")
    
    print("\n" + "=" * 50)
    print("Format Capacity Comparison:")
    print("=" * 50)
    
    formats = {
        'PNG tEXt chunks': {
            'limit': 'No practical limit (2GB per chunk)',
            'can_fit': True,
            'notes': 'Can split across multiple chunks if needed'
        },
        'JPEG EXIF': {
            'limit': '64KB per EXIF tag',
            'can_fit': len(json_compact) < 65536,
            'notes': 'Can use multiple tags or XMP for larger data'
        },
        'JPEG XMP': {
            'limit': 'No practical limit',
            'can_fit': True,
            'notes': 'RDF/XML format, very flexible'
        },
        'MP4/MOV atoms': {
            'limit': '4GB theoretical (practically unlimited)',
            'can_fit': True,
            'notes': 'Custom atoms + XMP support'
        }
    }
    
    for format_name, info in formats.items():
        status = "✅" if info['can_fit'] else "⚠️"
        print(f"\n{format_name}:")
        print(f"  Limit: {info['limit']}")
        print(f"  Can fit our metadata: {status}")
        print(f"  Notes: {info['notes']}")
    
    print("\n" + "=" * 50)
    print("Conclusion:")
    print("=" * 50)
    print("✅ All formats (JPEG, PNG, MP4, MOV) can store our metadata")
    print("✅ PNG is ideal - unlimited capacity, native support")
    print("✅ JPEG works well with EXIF + XMP combination")
    print("✅ MP4/MOV have excellent support via atoms and XMP")
    print("\nEven with comprehensive metadata (~10-20KB), we're well within")
    print("the capacity limits of all formats!")


def show_practical_examples():
    """Show practical examples of metadata in each format."""
    print("\n\nPractical Implementation Examples")
    print("=" * 50)
    
    print("\n1. PNG Implementation:")
    print("   - Use PIL to add tEXt chunks")
    print("   - Each chunk: key=value pair")
    print("   - Our data: alice-multiverse:metadata = {JSON}")
    print("   - Completely lossless, no re-encoding")
    
    print("\n2. JPEG Implementation:")
    print("   - Primary: EXIF ImageDescription (0x010e) = {JSON}")
    print("   - Fallback: XMP packet with custom namespace")
    print("   - Preserve existing EXIF data")
    print("   - No quality loss if done correctly")
    
    print("\n3. MP4/MOV Implementation:")
    print("   - Use ffmpeg: -metadata alice_multiverse='{JSON}'")
    print("   - Or custom atom: 'udta.meta.alice'")
    print("   - No re-encoding needed (-c copy)")
    print("   - Supports streaming metadata")
    
    print("\n4. Cross-Format Compatibility:")
    print("   - Same JSON structure across all formats")
    print("   - Graceful degradation if moved between formats")
    print("   - Can always extract and re-embed")


if __name__ == "__main__":
    analyze_metadata_size()
    show_practical_examples()
    
    print("\n\nKey Takeaways:")
    print("- All formats support more than enough metadata")
    print("- Our ~10-20KB of analysis data fits easily")
    print("- Images and videos become self-contained")
    print("- No external database required for core data")
    print("- Cache becomes pure performance optimization")